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
  createScript(id: string, source: string): Promise<ScriptDetails>;
  saveSource(id: string, source: string): Promise<ScriptDetails>;
  setEnabled(id: string, enabled: boolean): Promise<void>;
  deleteScript(id: string): Promise<void>;
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

  public async createScript(id: string, source: string): Promise<ScriptDetails> {
    await Promise.resolve();
    const parseResult = extractMetadata(source);

    if (parseResult.tag === "Err") {
      throw new InvalidScriptSourceError(parseResult.error);
    }

    const exists = this.scripts.some((candidate) => candidate.id === id);

    if (exists) {
      throw new ScriptAlreadyExistsError(id);
    }

    const record: ScriptRecord = { id, enabled: true, source };
    this.scripts.push(record);
    return this.toDetails(record);
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

  public async deleteScript(id: string): Promise<void> {
    await Promise.resolve();
    const existingIndex = this.scripts.findIndex(
      (candidate) => candidate.id === id,
    );

    if (existingIndex === -1) {
      throw new ScriptNotFoundError(id);
    }

    this.scripts.splice(existingIndex, 1);
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

export class ScriptNotFoundError extends Error {
  public constructor(id: string) {
    super(`Script not found: ${id}`);
    this.name = "ScriptNotFoundError";
  }
}

export class ScriptAlreadyExistsError extends Error {
  public constructor(id: string) {
    super(`Script already exists: ${id}`);
    this.name = "ScriptAlreadyExistsError";
  }
}

export class InvalidScriptSourceError extends Error {
  public constructor(message: string) {
    super(message);
    this.name = "InvalidScriptSourceError";
  }
}
