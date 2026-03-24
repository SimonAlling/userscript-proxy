export function errorMessageFromCaught(caught: unknown): string {
  return caught instanceof Error
    ? `${caught.name}: ${caught.message}`
    : typeof caught === "string"
      ? caught
      : String(caught);
}

export type ErrorInfo = {
  uiError: string;
  logError: string;
};
