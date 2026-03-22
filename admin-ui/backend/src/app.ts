import fastifyStatic from "@fastify/static";
import Fastify from "fastify";

import type { HealthStatus } from "@userscript-proxy/core/api/HealthStatus";

const NO_FRONTEND_DIR = "";

export async function buildApp(frontendDir: string) {
  const app = Fastify({
    logger: true,
  });

  if (frontendDir !== NO_FRONTEND_DIR) {
    await app.register(fastifyStatic, {
      root: frontendDir,
      wildcard: false,
    });
  }

  app.get<{ Reply: HealthStatus }>("/api/health", () => {
    return { ok: true };
  });

  return app;
}
