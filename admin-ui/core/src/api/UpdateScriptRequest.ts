import * as td from "tiny-decoders";

export type UpdateScriptRequest = {
  newScriptContent: string;
};

export const UpdateScriptRequestCodec: td.Codec<UpdateScriptRequest> =
  td.fields({
    newScriptContent: td.string,
  });
