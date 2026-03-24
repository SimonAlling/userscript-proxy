import * as td from "tiny-decoders";

export type CreateScriptRequest = {
  filenameWithoutExtension: string;
  content: string;
};

export const CreateScriptRequestCodec: td.Codec<CreateScriptRequest> =
  td.fields({
    filenameWithoutExtension: td.string,
    content: td.string,
  });
