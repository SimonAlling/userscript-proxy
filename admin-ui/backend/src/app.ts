import Fastify from "fastify";

import type { HealthStatus } from "@userscript-proxy/core/api/HealthStatus";

export async function buildApp() {
  const app = Fastify({
    logger: true,
  });

  app.get<{ Reply: HealthStatus }>("/api/health", () => {
    return { ok: true };
  });

  return app;
}
