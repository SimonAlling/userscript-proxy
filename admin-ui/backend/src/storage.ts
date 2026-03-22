import fs from "node:fs/promises";

import type { ScriptSummary } from "@userscript-proxy/core/api/ScriptSummary";

const USERSCRIPT_EXT = ".user.js";

export async function listScripts(
  scriptsDir: string,
): Promise<Array<ScriptSummary>> {
  const files = await fs.readdir(scriptsDir, { recursive: true });
  return files
    .filter((f) => f.endsWith(USERSCRIPT_EXT))
    .map((f) => ({ filename: f }));
}
