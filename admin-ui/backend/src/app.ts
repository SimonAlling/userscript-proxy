import fastifyStatic from "@fastify/static";
import Fastify from "fastify";

import type { HealthStatus } from "@userscript-proxy/core/api/HealthStatus";
import type { ScriptSummary } from "@userscript-proxy/core/api/ScriptSummary";

import { listScripts } from "./storage";

const NO_FRONTEND_DIR = "";

export async function buildApp(frontendDir: string, scriptsDir: string) {
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

  app.get<{ Reply: Array<ScriptSummary> }>("/api/scripts", async () =>
    listScripts(scriptsDir),
  );

  return app;
}
