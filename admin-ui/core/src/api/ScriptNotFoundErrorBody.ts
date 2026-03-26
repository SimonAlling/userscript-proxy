import * as td from "tiny-decoders";

export type ScriptNotFoundErrorBody = {
  missingScriptName: string;
};

export const ScriptNotFoundErrorBodyCodec: td.Codec<ScriptNotFoundErrorBody> =
  td.fields({
    missingScriptName: td.string,
  });
