import * as td from "tiny-decoders";

export type ScriptDetails = {
  scriptContent: string;
};

export const ScriptDetailsCodec: td.Codec<ScriptDetails> = td.fields({
  scriptContent: td.string,
});
