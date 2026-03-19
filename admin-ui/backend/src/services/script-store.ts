import { promises as fs } from "node:fs";
import path from "node:path";
import { extractMetadata } from "@userscript-proxy/core/metadata";

export type ScriptRecord = {
  id: string;
  enabled: boolean;
  source: string;
};

export type ScriptSummary = {
  id: string;
  enabled: boolean;
  name: string;
  version: string | null;
};

export type ScriptDetails = {
  id: string;
  enabled: boolean;
  source: string;
  name: string;
  version: string | null;
};

export type ScriptStore = {
  listScripts(): Promise<ReadonlyArray<ScriptSummary>>;
  getScript(id: string): Promise<ScriptDetails | null>;
  saveSource(id: string, source: string): Promise<ScriptDetails>;
  setEnabled(id: string, enabled: boolean): Promise<void>;
};

type ScriptStateFile = {
  scripts: Record<string, { enabled: boolean }>;
};

export class InMemoryScriptStore implements ScriptStore {
  private scripts: Array<ScriptRecord>;

  public constructor() {
    this.scripts = [
      {
        id: "example-script",
        enabled: true,
        source: `// ==UserScript==
// @name        Example script
// @version     0.1.0
// @match       *://*/*
// ==/UserScript==

console.log("hello");
`,
      },
    ];
  }

  public async listScripts(): Promise<ReadonlyArray<ScriptSummary>> {
    await Promise.resolve();
    return this.scripts.map((script) => this.toSummary(script));
  }

  public async getScript(id: string): Promise<ScriptDetails | null> {
    await Promise.resolve();
    const script = this.scripts.find((candidate) => candidate.id === id);

    if (script === undefined) {
      return null;
    }

    return this.toDetails(script);
  }

  public async saveSource(id: string, source: string): Promise<ScriptDetails> {
    await Promise.resolve();
    const parseResult = extractMetadata(source);

    if (parseResult.tag === "Err") {
      throw new InvalidScriptSourceError(parseResult.error);
    }

    const existingIndex = this.scripts.findIndex(
      (candidate) => candidate.id === id,
    );

    if (existingIndex === -1) {
      throw new ScriptNotFoundError(id);
    }

    const current = this.scripts[existingIndex];
    if (current === undefined) {
      throw new ScriptNotFoundError(id);
    }

    const updated: ScriptRecord = {
      ...current,
      source,
    };

    this.scripts[existingIndex] = updated;

    return this.toDetails(updated);
  }

  public async setEnabled(id: string, enabled: boolean): Promise<void> {
    await Promise.resolve();
    const existingIndex = this.scripts.findIndex(
      (candidate) => candidate.id === id,
    );

    if (existingIndex === -1) {
      throw new ScriptNotFoundError(id);
    }

    const current = this.scripts[existingIndex];
    if (current === undefined) {
      throw new ScriptNotFoundError(id);
    }

    this.scripts[existingIndex] = {
      ...current,
      enabled,
    };
  }

  private toSummary(script: ScriptRecord): ScriptSummary {
    const parseResult = extractMetadata(script.source);

    if (parseResult.tag === "Err") {
      return {
        id: script.id,
        enabled: script.enabled,
        name: "(invalid script)",
        version: null,
      };
    }

    return {
      id: script.id,
      enabled: script.enabled,
      name: parseResult.value.name,
      version: parseResult.value.version,
    };
  }

  private toDetails(script: ScriptRecord): ScriptDetails {
    const parseResult = extractMetadata(script.source);

    if (parseResult.tag === "Err") {
      throw new InvalidScriptSourceError(parseResult.error);
    }

    return {
      id: script.id,
      enabled: script.enabled,
      source: script.source,
      name: parseResult.value.name,
      version: parseResult.value.version,
    };
  }
}

export class FileSystemScriptStore implements ScriptStore {
  private readonly userscriptsDir: string;
  private readonly stateDir: string;
  private readonly stateFilePath: string;

  public constructor(dataDir: string) {
    this.userscriptsDir = path.join(dataDir, "userscripts");
    this.stateDir = path.join(dataDir, "state");
    this.stateFilePath = path.join(this.stateDir, "scripts.json");
  }

  public async listScripts(): Promise<ReadonlyArray<ScriptSummary>> {
    await this.ensureLayout();

    const [entries, state] = await Promise.all([
      fs.readdir(this.userscriptsDir, { withFileTypes: true }),
      this.readState(),
    ]);

    const fileNames = entries
      .filter((entry) => entry.isFile() && entry.name.endsWith(".user.js"))
      .map((entry) => entry.name)
      .sort((a, b) => a.localeCompare(b));

    const summaries = await Promise.all(
      fileNames.map(async (fileName) => {
        const id = scriptIdFromFileName(fileName);
        const source = await fs.readFile(
          path.join(this.userscriptsDir, fileName),
          "utf8",
        );

        const parseResult = extractMetadata(source);

        if (parseResult.tag === "Err") {
          return {
            id,
            enabled: state.scripts[id]?.enabled ?? true,
            name: "(invalid script)",
            version: null,
          } satisfies ScriptSummary;
        }

        return {
          id,
          enabled: state.scripts[id]?.enabled ?? true,
          name: parseResult.value.name,
          version: parseResult.value.version,
        } satisfies ScriptSummary;
      }),
    );

    return summaries;
  }

  public async getScript(id: string): Promise<ScriptDetails | null> {
    await this.ensureLayout();

    const source = await this.readScriptSourceIfExists(id);
    if (source === null) {
      return null;
    }

    const parseResult = extractMetadata(source);
    if (parseResult.tag === "Err") {
      throw new InvalidScriptSourceError(parseResult.error);
    }

    const state = await this.readState();

    return {
      id,
      enabled: state.scripts[id]?.enabled ?? true,
      source,
      name: parseResult.value.name,
      version: parseResult.value.version,
    };
  }

  public async saveSource(id: string, source: string): Promise<ScriptDetails> {
    await this.ensureLayout();

    const parseResult = extractMetadata(source);
    if (parseResult.tag === "Err") {
      throw new InvalidScriptSourceError(parseResult.error);
    }

    const filePath = this.filePathForId(id);

    try {
      await fs.access(filePath);
    } catch (error: unknown) {
      if (isNotFoundError(error)) {
        throw new ScriptNotFoundError(id);
      }
      throw error;
    }

    await fs.writeFile(filePath, source, "utf8");

    const state = await this.readState();

    return {
      id,
      enabled: state.scripts[id]?.enabled ?? true,
      source,
      name: parseResult.value.name,
      version: parseResult.value.version,
    };
  }

  public async setEnabled(id: string, enabled: boolean): Promise<void> {
    await this.ensureLayout();

    const filePath = this.filePathForId(id);

    try {
      await fs.access(filePath);
    } catch (error: unknown) {
      if (isNotFoundError(error)) {
        throw new ScriptNotFoundError(id);
      }
      throw error;
    }

    const state = await this.readState();
    state.scripts[id] = { enabled };
    await this.writeState(state);
  }

  private async ensureLayout(): Promise<void> {
    await fs.mkdir(this.userscriptsDir, { recursive: true });
    await fs.mkdir(this.stateDir, { recursive: true });

    try {
      await fs.access(this.stateFilePath);
    } catch (error: unknown) {
      if (isNotFoundError(error)) {
        await this.writeState({ scripts: {} });
        return;
      }
      throw error;
    }
  }

  private async readScriptSourceIfExists(id: string): Promise<string | null> {
    const filePath = this.filePathForId(id);

    try {
      return await fs.readFile(filePath, "utf8");
    } catch (error: unknown) {
      if (isNotFoundError(error)) {
        return null;
      }
      throw error;
    }
  }

  private filePathForId(id: string): string {
    if (!isSafeScriptId(id)) {
      throw new Error(`Unsafe script id: ${id}`);
    }

    return path.join(this.userscriptsDir, `${id}.user.js`);
  }

  private async readState(): Promise<ScriptStateFile> {
    const raw = await fs.readFile(this.stateFilePath, "utf8");
    const parsed = JSON.parse(raw) as Partial<ScriptStateFile>;

    return {
      scripts: parsed.scripts ?? {},
    };
  }

  private async writeState(state: ScriptStateFile): Promise<void> {
    const json = JSON.stringify(state, null, 2) + "\n";
    await fs.writeFile(this.stateFilePath, json, "utf8");
  }
}

export class ScriptNotFoundError extends Error {
  public constructor(id: string) {
    super(`Script not found: ${id}`);
    this.name = "ScriptNotFoundError";
  }
}

export class InvalidScriptSourceError extends Error {
  public constructor(message: string) {
    super(message);
    this.name = "InvalidScriptSourceError";
  }
}

function scriptIdFromFileName(fileName: string): string {
  return fileName.replace(/\.user\.js$/, "");
}

function isSafeScriptId(id: string): boolean {
  return /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(id);
}

function isNotFoundError(error: unknown): boolean {
  return (
    typeof error === "object" &&
    error !== null &&
    "code" in error &&
    error.code === "ENOENT"
  );
}
