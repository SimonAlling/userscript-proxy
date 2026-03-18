import { Err, Ok, type Result } from "./util/results";

const PREFIX_NAME = "// @name";
const PREFIX_VERSION = "// @version";

export type Metadata = {
  name: string;
  version: string | null;
};

export function extractMetadata(source: string): Result<Metadata, string> {
  const metadataLines = extractMetadataLines(source);

  type ParsedMetadata = {
    name: string | null;
    version: string | null;
  };

  const initialMetadata: ParsedMetadata = {
    name: null,
    version: null,
  };

  const parsedMetadata = metadataLines.reduce((acc, line) => {
    switch (true) {
      case line.startsWith(PREFIX_NAME):
        return { ...acc, name: line.slice(PREFIX_NAME.length).trim() };

      case line.startsWith(PREFIX_VERSION):
        return { ...acc, version: line.slice(PREFIX_VERSION.length).trim() };

      default:
        return acc;
    }
  }, initialMetadata);

  if (parsedMetadata.name === null || parsedMetadata.name === "") {
    return Err(`Userscript must have a name.`);
  }

  return Ok({
    name: parsedMetadata.name,
    version: parsedMetadata.version,
  });
}

function extractMetadataLines(sourceCode: string): Array<string> {
  const lines = sourceCode.split(/\r?\n/);

  const startIndex = lines.findIndex((x) => x.trim() === "// ==UserScript==");
  const endIndex = lines.findIndex((x) => x.trim() === "// ==/UserScript==");

  return lines.slice(startIndex + 1, endIndex);
}
