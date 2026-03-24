import fs from "node:fs/promises";

import type { ScriptSummary } from "@userscript-proxy/core/api/ScriptSummary";
import { isUserscriptFilename } from "@userscript-proxy/core/files";

export async function listScripts(
  scriptsDir: string,
): Promise<Array<ScriptSummary>> {
  const files = await fs.readdir(scriptsDir, { recursive: true });
  return files.filter(isUserscriptFilename).map((f) => ({ filename: f }));
}
