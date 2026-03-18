import { buildApp } from "./app";

const port = Number(process.env["USERSCRIPT_PROXY_ADMIN_BACKEND_PORT"] ?? "3000");
const host = process.env["USERSCRIPT_PROXY_ADMIN_BACKEND_HOST"] ?? "0.0.0.0";

async function main(): Promise<void> {
  const app = await buildApp();

  try {
    await app.listen({ port, host });
    app.log.info(`Backend listening on http://${host}:${port}`);
  } catch (error) {
    app.log.error(error);
    process.exit(1);
  }
}

void main();
