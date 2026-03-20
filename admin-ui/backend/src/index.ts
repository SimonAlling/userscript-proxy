import { errorMessageFromCaught } from "@userscript-proxy/core/errors";

import { buildApp } from "./app";

const host = "127.0.0.1";
const port = 3000;

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
