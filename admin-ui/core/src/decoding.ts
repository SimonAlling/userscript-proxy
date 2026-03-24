import * as td from "tiny-decoders";

import { Err, Ok, type Result } from "./results";

export function decodeWith<T>(
  codec: td.Codec<T>,
  input: unknown,
  isSensitive: boolean,
): Result<T, string> {
  return toResult(codec.decoder(input), isSensitive);
}

function toResult<T>(
  decoderResult: td.DecoderResult<T>,
  isSensitive: boolean,
): Result<T, string> {
  switch (decoderResult.tag) {
    case "DecoderError":
      return Err(td.format(decoderResult.error, { sensitive: isSensitive }));

    case "Valid":
      return Ok(decoderResult.value);
  }
}
