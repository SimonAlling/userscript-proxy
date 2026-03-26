import fs from "node:fs/promises";
import path from "node:path";

import type { ScriptSummary } from "@userscript-proxy/core/api/ScriptSummary";
import { errorMessageFromCaught } from "@userscript-proxy/core/errors";
import {
  isUserscriptFilename,
  howToSortFilenames,
  validateFilename,
  withExtension,
} from "@userscript-proxy/core/files";
import { Err, Ok, type Result } from "@userscript-proxy/core/results";

export async function listScripts(
  scriptsDir: string,
): Promise<Array<ScriptSummary>> {
  const files = await fs.readdir(scriptsDir, { recursive: true });
  return files
    .filter(isUserscriptFilename)
    .toSorted(howToSortFilenames)
    .map((f) => ({ filename: f }));
}

type ScriptCreationError =
  | { tag: "InvalidName"; reason: string }
  | { tag: "AlreadyExists" }
  | { tag: "CouldNotWrite"; reason: string };

export async function createScript(
  scriptsDir: string,
  filenameWithoutExtension: string,
  content: string,
): Promise<Result<void, ScriptCreationError>> {
  const filenameValidationResult = validateFilename(filenameWithoutExtension);

  if (filenameValidationResult.tag === "Err") {
    return Err({ tag: "InvalidName", reason: filenameValidationResult.error });
  }

  const filename = withExtension(filenameWithoutExtension);
  const filePath = path.join(scriptsDir, filename);
  try {
    await fs.writeFile(filePath, content, { flag: "wx" });
    return Ok(undefined);
  } catch (caught) {
    if (isErrnoException(caught) && caught.code === "EEXIST") {
      return Err({ tag: "AlreadyExists" });
    }

    return Err({
      tag: "CouldNotWrite",
      reason: errorMessageFromCaught(caught),
    });
  }
}

type ScriptReadError =
  | { tag: "NotFound" }
  | { tag: "CouldNotRead"; reason: string };

export async function readScript(
  scriptsDir: string,
  filename: string,
): Promise<Result<string, ScriptReadError>> {
  const filePath = path.join(scriptsDir, filename);
  try {
    const content = await fs.readFile(filePath, "utf-8");
    return Ok(content);
  } catch (caught) {
    if (isErrnoException(caught) && caught.code === "ENOENT") {
      return Err({ tag: "NotFound" });
    }
    return Err({ tag: "CouldNotRead", reason: errorMessageFromCaught(caught) });
  }
}

type ScriptUpdateError =
  | { tag: "NotFound" }
  | { tag: "CouldNotWrite"; reason: string };

export async function updateScript(
  scriptsDir: string,
  filename: string,
  content: string,
): Promise<Result<void, ScriptUpdateError>> {
  const filePath = path.join(scriptsDir, filename);
  try {
    await fs.stat(filePath);
  } catch (caught) {
    if (isErrnoException(caught) && caught.code === "ENOENT") {
      return Err({ tag: "NotFound" });
    }
    return Err({
      tag: "CouldNotWrite",
      reason: errorMessageFromCaught(caught),
    });
  }

  try {
    await fs.writeFile(filePath, content);
    return Ok(undefined);
  } catch (caught) {
    return Err({
      tag: "CouldNotWrite",
      reason: errorMessageFromCaught(caught),
    });
  }
}

type ScriptDeleteError =
  | { tag: "NotFound" }
  | { tag: "CouldNotDelete"; reason: string };

export async function deleteScript(
  scriptsDir: string,
  filename: string,
): Promise<Result<void, ScriptDeleteError>> {
  const filePath = path.join(scriptsDir, filename);
  try {
    await fs.unlink(filePath);
    return Ok(undefined);
  } catch (caught) {
    if (isErrnoException(caught) && caught.code === "ENOENT") {
      return Err({ tag: "NotFound" });
    }
    return Err({
      tag: "CouldNotDelete",
      reason: errorMessageFromCaught(caught),
    });
  }
}

function isErrnoException(e: unknown): e is NodeJS.ErrnoException {
  return e instanceof Error && "code" in e;
}
