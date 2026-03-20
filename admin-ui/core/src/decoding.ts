import * as td from "tiny-decoders";

export class DecodingError extends Error {
  public constructor(error: td.DecoderError, context: string, dataIsSensitive: boolean) {
    super(`Unexpected data in ${context}: ${td.format(error, { sensitive: dataIsSensitive })}`);
    this.name = "DecodingError";
  }
}

export function decodeOrThrow<T>(namedParameters: {
  codec: td.Codec<T>,
  data: unknown,
  context: string,
  dataIsSensitive: boolean,
}): T {
  const result = namedParameters.codec.decoder(namedParameters.data);

  if (result.tag === "DecoderError") {
    throw new DecodingError(result.error, namedParameters.context, namedParameters.dataIsSensitive);
  }

  return result.value;
}
