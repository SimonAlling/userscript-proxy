import * as td from "tiny-decoders";

export type ScriptSummary = {
  filename: string;
};

export const ScriptSummaryCodec: td.Codec<ScriptSummary> = td.fields({
  filename: td.string,
});
