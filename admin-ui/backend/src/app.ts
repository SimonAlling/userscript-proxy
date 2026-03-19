import cors from "@fastify/cors";
import Fastify from "fastify";
import { registerScriptRoutes } from "./routes/scripts";
import { FileSystemScriptStore } from "./services/script-store";

export async function buildApp() {
  const app = Fastify({
    logger: true,
  });

  await app.register(cors, {
    origin: true,
    methods: ["GET", "PUT"],
  });

  app.get("/api/health", () => {
    return { ok: true };
  });

  const dataDir = process.env["DATA_DIR"] ?? "/tmp/userscript-proxy/data";
  const scriptStore = new FileSystemScriptStore(dataDir);

  registerScriptRoutes(app, scriptStore);

  return app;
}
