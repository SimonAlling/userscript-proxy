import * as td from "tiny-decoders";

export type BadRequestErrorBody = {
  badRequestReason: string;
};

export const BadRequestErrorBodyCodec: td.Codec<BadRequestErrorBody> =
  td.fields({
    badRequestReason: td.string,
  });
