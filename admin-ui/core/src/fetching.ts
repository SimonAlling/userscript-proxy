import * as td from "tiny-decoders";

import { decodeWith } from "@userscript-proxy/core/decoding";
import { errorMessageFromCaught } from "@userscript-proxy/core/errors";
import { Err, Ok } from "@userscript-proxy/core/results";
import type { NoRejectPromise } from "@userscript-proxy/core/promises";

export async function decodeJsonBody_NoReject<T>(
  response: Response,
  codec: td.Codec<T>,
): NoRejectPromise<
  T,
  | `Could not parse response body as JSON: ${string}`
  | `Unexpected response body shape: ${string}`
> {
  let body: unknown;
  try {
    body = await response.json();
  } catch (caught) {
    return Err(
      `Could not parse response body as JSON: ${errorMessageFromCaught(caught)}` as const,
    );
  }
  const decoded = decodeWith(codec, body, false);
  if (decoded.tag === "Ok") {
    return Ok(decoded.value);
  }
  return Err(`Unexpected response body shape: ${decoded.error}` as const);
}
