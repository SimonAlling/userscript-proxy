import { throwIfNullOrUndefined } from "@userscript-proxy/core/assertions";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";

createRoot(
  throwIfNullOrUndefined(document.getElementById("root"), "root element"),
).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
