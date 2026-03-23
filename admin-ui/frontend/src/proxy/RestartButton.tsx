import { useState } from "react";

import { assertExhausted } from "@userscript-proxy/core/assertions";

import "./RestartButton.css";

type RestartState =
  | { tag: "Idle" }
  | { tag: "Restarting" }
  | { tag: "Done"; ok: boolean };

const FEEDBACK_DURATION_MS = 1000;

export function RestartButton() {
  const [restartState, setRestartState] = useState<RestartState>({
    tag: "Idle",
  });

  function handleClick() {
    setRestartState({ tag: "Restarting" });
    fetch("/api/proxy/restart", { method: "POST" })
      .then((r) => {
        setRestartState({ tag: "Done", ok: r.ok });
        setTimeout(() => {
          setRestartState({ tag: "Idle" });
        }, FEEDBACK_DURATION_MS);
      })
      .catch(() => {
        setRestartState({ tag: "Done", ok: false });
        setTimeout(() => {
          setRestartState({ tag: "Idle" });
        }, FEEDBACK_DURATION_MS);
      });
  }

  return (
    <button
      className="restart-button"
      disabled={shouldBeDisabled(restartState)}
      onClick={handleClick}
    >
      {makeButtonLabel(restartState)}
    </button>
  );
}

function makeButtonLabel(restartState: RestartState) {
  switch (restartState.tag) {
    case "Idle":
      return "Restart proxy";

    case "Restarting":
      return "Restarting …";

    case "Done":
      return restartState.ok ? "✅ Restarted" : "❌ Failed";

    default:
      assertExhausted(restartState, "restart state");
  }
}

function shouldBeDisabled(restartState: RestartState): boolean {
  switch (restartState.tag) {
    case "Idle":
      return false;

    case "Restarting":
    case "Done":
      return true;
  }
}
