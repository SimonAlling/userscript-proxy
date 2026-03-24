import fastifyStatic from "@fastify/static";
import Fastify from "fastify";

import {
  type CreateScriptRequest,
  CreateScriptRequestCodec,
} from "@userscript-proxy/core/api/CreateScriptRequest";
import type { HealthStatus } from "@userscript-proxy/core/api/HealthStatus";
import type { ScriptSummary } from "@userscript-proxy/core/api/ScriptSummary";
import { assertExhausted } from "@userscript-proxy/core/assertions";
import { decodeWith } from "@userscript-proxy/core/decoding";
import { withExtension } from "@userscript-proxy/core/files";

import { createScript, listScripts } from "./storage";

const NO_FRONTEND_DIR = "";

export async function buildApp(
  frontendDir: string,
  scriptsDir: string,
  proxyRestartUrl: string,
) {
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

  app.post<{
    Body: CreateScriptRequest;
    Reply: undefined;
  }>("/api/scripts", async (request, reply) => {
    const body: unknown = request.body;

    const decodingResult = decodeWith(CreateScriptRequestCodec, body, false);

    if (decodingResult.tag === "Err") {
      return await reply
        .code(400)
        .send(`Invalid request payload: ${decodingResult.error}`);
    }

    const { filenameWithoutExtension, content } = decodingResult.value;

    const creationResult = await createScript(
      scriptsDir,
      filenameWithoutExtension,
      content,
    );

    if (creationResult.tag === "Ok") {
      return await reply.code(201).send();
    }

    switch (creationResult.error.tag) {
      case "InvalidName":
        return await reply.code(400).send(creationResult.error.reason);

      case "AlreadyExists":
        return await reply
          .code(409)
          .send(withExtension(filenameWithoutExtension));

      case "CouldNotWrite":
        return await reply.code(500).send(creationResult.error.reason);

      default:
        assertExhausted(creationResult.error, "script-creation error");
    }
  });

  app.post<{ Reply: HealthStatus }>("/api/proxy/restart", async () => {
    const response = await fetch(proxyRestartUrl, { method: "POST" });
    return { ok: response.ok };
  });

  return app;
}
