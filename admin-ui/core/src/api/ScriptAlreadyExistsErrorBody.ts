import * as td from "tiny-decoders";

export type ScriptAlreadyExistsErrorBody = {
  existingScriptName: string;
};

export const ScriptAlreadyExistsErrorBodyCodec: td.Codec<ScriptAlreadyExistsErrorBody> =
  td.fields({
    existingScriptName: td.string,
  });
