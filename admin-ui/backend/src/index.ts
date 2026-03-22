import { errorMessageFromCaught } from "@userscript-proxy/core/errors";

import { buildApp } from "./app";
import { getEnvVarOrThrow } from "./environment";

const host = getEnvVarOrThrow("BACKEND_HOST");
const port = Number.parseInt(getEnvVarOrThrow("BACKEND_PORT"));

async function main(): Promise<void> {
  try {
    const app = await buildApp();
    await app.listen({ host, port });
  } catch (error) {
    console.error(errorMessageFromCaught(error));
    process.exit(1);
  }
}

void main();
