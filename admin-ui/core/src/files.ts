const USERSCRIPT_EXT = ".user.js";

export function isUserscriptFilename(
  filename: string,
): filename is `${string}${typeof USERSCRIPT_EXT}` {
  return filename.endsWith(USERSCRIPT_EXT);
}
