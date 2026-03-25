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

  app.get<{ Reply: HealthStatus }>("/api/health", async (_request, reply) => {
    return reply.code(200).send({ ok: true });
  });

  app.get<{ Reply: Array<ScriptSummary> }>(
    "/api/scripts",
    async (_request, reply) =>
      reply.code(200).send(await listScripts(scriptsDir)),
  );

  app.post<{
    Body: CreateScriptRequest;
    Reply: undefined;
  }>("/api/scripts", async (request, reply) => {
    const body: unknown = request.body;

    const decodingResult = decodeWith(CreateScriptRequestCodec, body, false);

    if (decodingResult.tag === "Err") {
      return reply
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
      return reply.code(201).send();
    }

    switch (creationResult.error.tag) {
      case "InvalidName":
        return reply.code(400).send(creationResult.error.reason);

      case "AlreadyExists":
        return reply.code(409).send(withExtension(filenameWithoutExtension));

      case "CouldNotWrite":
        return reply.code(500).send(creationResult.error.reason);

      default:
        assertExhausted(creationResult.error, "script-creation error");
    }
  });

  app.post<{ Reply: HealthStatus }>(
    "/api/proxy/restart",
    async (_request, reply) => {
      const response = await fetch(proxyRestartUrl, { method: "POST" });
      return reply.code(200).send({ ok: response.ok });
    },
  );

  return app;
}
