import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";
import { throwIfNullOrUndefined } from "./util/assertions.ts";

createRoot(
  throwIfNullOrUndefined(document.getElementById("root"), "root element"),
).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
