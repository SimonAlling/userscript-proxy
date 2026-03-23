import { useState } from "react";

import { assertExhausted } from "@userscript-proxy/core/assertions";

type RestartState =
  | { tag: "Idle" }
  | { tag: "Restarting" }
  | { tag: "Done"; ok: boolean };

export function RestartButton() {
  const [restartState, setRestartState] = useState<RestartState>({
    tag: "Idle",
  });

  function handleClick() {
    setRestartState({ tag: "Restarting" });
    fetch("/api/proxy/restart", { method: "POST" })
      .then((r) => {
        setRestartState({ tag: "Done", ok: r.ok });
      })
      .catch(() => {
        setRestartState({ tag: "Done", ok: false });
      });
  }

  return (
    <div>
      <button
        disabled={restartState.tag === "Restarting"}
        onClick={handleClick}
      >
        Restart proxy
      </button>
      {renderRestartState(restartState)}
    </div>
  );
}

function renderRestartState(restartState: RestartState) {
  switch (restartState.tag) {
    case "Idle":
      return null;

    case "Restarting":
      return " ⏳";

    case "Done":
      return restartState.ok ? " ✅" : " ❌";

    default:
      assertExhausted(restartState, "restart state");
  }
}
