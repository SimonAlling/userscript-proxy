import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

import { getEnvVarOrThrow } from "@userscript-proxy/backend/src/environment";

const backendHost = getEnvVarOrThrow("BACKEND_HOST");
const backendPort = getEnvVarOrThrow("BACKEND_PORT");

const backendBaseUrl = `http://${backendHost}:${backendPort}`;

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "dist",
  },
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": backendBaseUrl,
    },
  },
});
