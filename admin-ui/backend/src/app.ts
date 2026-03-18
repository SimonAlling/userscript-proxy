import Fastify from "fastify";

export async function buildApp() {
  const app = Fastify({
    logger: true,
  });

  app.get("/api/health", () => {
    return { ok: true };
  });

  return app;
}
