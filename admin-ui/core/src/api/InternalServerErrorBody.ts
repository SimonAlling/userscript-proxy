import * as td from "tiny-decoders";

export type InternalServerErrorBody = {
  serverErrorReason: string;
};

export const InternalServerErrorBodyCodec: td.Codec<InternalServerErrorBody> =
  td.fields({
    serverErrorReason: td.string,
  });
