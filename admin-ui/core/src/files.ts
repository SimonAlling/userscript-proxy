import { Err, Ok, type Result } from "./results";

const USERSCRIPT_EXT = ".user.js";

const FILENAME_WITHOUT_EXTENSION_PATTERN = /^[A-Za-z0-9-_]+$/;

export function isUserscriptFilename(
  filename: string,
): filename is `${string}${typeof USERSCRIPT_EXT}` {
  return filename.endsWith(USERSCRIPT_EXT);
}

export function withExtension<T extends string>(
  filenameWithoutExtension: T,
): `${T}${typeof USERSCRIPT_EXT}` {
  return `${filenameWithoutExtension}${USERSCRIPT_EXT}`;
}

export function validateFilename(
  filenameWithoutExtension: string,
): Result<void, string> {
  if (filenameWithoutExtension.trim() === "") {
    return Err("Name cannot be empty.");
  }

  if (!FILENAME_WITHOUT_EXTENSION_PATTERN.test(filenameWithoutExtension)) {
    return Err(`Name must match ${FILENAME_WITHOUT_EXTENSION_PATTERN}.`);
  }

  return Ok(undefined);
}

export function howToSortFilenames(a: string, b: string) {
  return a.localeCompare(b);
}
