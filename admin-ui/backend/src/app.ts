import Fastify from "fastify";
import { registerScriptRoutes } from "./routes/scripts";
import { InMemoryScriptStore } from "./services/script-store";

export async function buildApp() {
  const app = Fastify({
    logger: true,
  });

  app.get("/api/health", () => {
    return { ok: true };
  });

  const scriptStore = new InMemoryScriptStore();

  registerScriptRoutes(app, scriptStore);

  return app;
}
