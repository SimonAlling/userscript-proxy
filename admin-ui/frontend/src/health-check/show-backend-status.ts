import { errorMessageFromCaught } from "@userscript-proxy/core/errors";

export function showHealthCheckResponse(response: Response): string {
  if (!response.ok) {
    return `❌ ${response.status} ${response.statusText}`;
  }

  return `✅ OK`;
}

export function showHealthCheckFailure(caught: unknown): string {
  return `❌ ${errorMessageFromCaught(caught)}`;
}
