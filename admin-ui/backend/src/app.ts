import fastifyStatic from "@fastify/static";
import Fastify from "fastify";

import {
  type CreateScriptRequest,
  CreateScriptRequestCodec,
} from "@userscript-proxy/core/api/CreateScriptRequest";
import type { HealthStatus } from "@userscript-proxy/core/api/HealthStatus";
import type { ScriptDetails } from "@userscript-proxy/core/api/ScriptDetails";
import type { ScriptSummary } from "@userscript-proxy/core/api/ScriptSummary";
import {
  type UpdateScriptRequest,
  UpdateScriptRequestCodec,
} from "@userscript-proxy/core/api/UpdateScriptRequest";
import { assertExhausted } from "@userscript-proxy/core/assertions";
import { decodeWith } from "@userscript-proxy/core/decoding";
import {
  isUserscriptFilename,
  withExtension,
} from "@userscript-proxy/core/files";
import { quote } from "@userscript-proxy/core/strings";

import { createScript, listScripts, readScript, updateScript } from "./storage";

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
    Reply: undefined | string;
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
      return reply.code(201).send(undefined);
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

  app.get<{ Params: { filename: string }; Reply: ScriptDetails | string }>(
    "/api/scripts/:filename",
    async (request, reply) => {
      const { filename } = request.params;

      if (!isUserscriptFilename(filename)) {
        // If nothing else, this should prevent us from accidentally serving a non-userscript file.
        return reply
          .code(400)
          .send(`Invalid userscript filename: ${quote(filename)}`);
      }

      const result = await readScript(scriptsDir, filename);

      if (result.tag === "Ok") {
        return reply.code(200).send({ scriptContent: result.value });
      }

      switch (result.error.tag) {
        case "NotFound":
          return reply.code(404).send(filename);

        case "CouldNotRead":
          return reply.code(500).send(result.error.reason);

        default:
          assertExhausted(result.error, "script-read error");
      }
    },
  );

  app.put<{
    Params: { filename: string };
    Body: UpdateScriptRequest;
    Reply: undefined | string;
  }>("/api/scripts/:filename", async (request, reply) => {
    const { filename } = request.params;

    if (!isUserscriptFilename(filename)) {
      return reply
        .code(400)
        .send(`Invalid userscript filename: ${quote(filename)}`);
    }

    const body: unknown = request.body;
    const decodingResult = decodeWith(UpdateScriptRequestCodec, body, false);

    if (decodingResult.tag === "Err") {
      return reply
        .code(400)
        .send(`Invalid request payload: ${decodingResult.error}`);
    }

    const { newScriptContent } = decodingResult.value;
    const result = await updateScript(scriptsDir, filename, newScriptContent);

    if (result.tag === "Ok") {
      return reply.code(200).send(undefined);
    }

    switch (result.error.tag) {
      case "NotFound":
        return reply.code(404).send(filename);

      case "CouldNotWrite":
        return reply.code(500).send(result.error.reason);

      default:
        assertExhausted(result.error, "script-update error");
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
