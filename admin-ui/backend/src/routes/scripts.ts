import type { FastifyInstance } from "fastify";
import {
  InvalidScriptSourceError,
  ScriptNotFoundError,
  type ScriptStore,
} from "../services/script-store.js";

type ScriptIdParams = {
  id: string;
};

type SaveSourceBody = {
  source: string;
};

type SetEnabledBody = {
  enabled: boolean;
};

export function registerScriptRoutes(
  app: FastifyInstance,
  scriptStore: ScriptStore,
): void {
  app.get("/api/scripts", async (_request, reply) => {
    const scripts = await scriptStore.listScripts();
    return reply.send({ scripts });
  });

  app.get<{ Params: ScriptIdParams }>(
    "/api/scripts/:id",
    async (request, reply) => {
      const script = await scriptStore.getScript(request.params.id);

      if (script === null) {
        return reply.code(404).send({
          error: `Script not found: ${request.params.id}`,
        });
      }

      return reply.send({ script });
    },
  );

  app.put<{ Params: ScriptIdParams; Body: SaveSourceBody }>(
    "/api/scripts/:id/source",
    async (request, reply) => {
      try {
        const script = await scriptStore.saveSource(
          request.params.id,
          request.body.source,
        );

        return await reply.send({ script });
      } catch (error) {
        if (error instanceof ScriptNotFoundError) {
          return reply.code(404).send({ error: error.message });
        }

        if (error instanceof InvalidScriptSourceError) {
          return reply.code(400).send({ error: error.message });
        }

        throw error;
      }
    },
  );

  app.put<{ Params: ScriptIdParams; Body: SetEnabledBody }>(
    "/api/scripts/:id/enabled",
    async (request, reply) => {
      try {
        await scriptStore.setEnabled(request.params.id, request.body.enabled);
        return await reply.code(204).send();
      } catch (error) {
        if (error instanceof ScriptNotFoundError) {
          return reply.code(404).send({ error: error.message });
        }

        throw error;
      }
    },
  );
}
