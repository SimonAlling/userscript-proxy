import { useEffect, useState } from "react";
import * as td from "tiny-decoders";

import "./ScriptListView.css";

import {
  ScriptSummaryCodec,
  type ScriptSummary,
} from "@userscript-proxy/core/api/ScriptSummary";
import { assertExhausted } from "@userscript-proxy/core/assertions";

type ScriptListState =
  | { tag: "Loading" }
  | { tag: "HaveScripts"; scripts: ReadonlyArray<ScriptSummary> }
  | { tag: "CouldNotGetScripts"; error: string };

export function ScriptListView() {
  const [scriptListState, setScriptListState] = useState<ScriptListState>({
    tag: "Loading",
  });

  useEffect(() => {
    fetch("/api/scripts")
      .then((r) => r.json())
      .then(td.array(ScriptSummaryCodec).decoder)
      .then(interpretResponse)
      .then(maybeLogError)
      .then(setScriptListState)
      .catch(console.error);
  }, []);

  return (
    <section id="script-list-section">
      <h2>Installed scripts</h2>
      {renderScriptListState(scriptListState)}
    </section>
  );
}

function renderScriptListState(scriptListState: ScriptListState) {
  switch (scriptListState.tag) {
    case "Loading":
      return "⏳ Loading …";

    case "HaveScripts":
      return (
        <ul className="script-list">
          {scriptListState.scripts.map((s) => (
            <li key={s.filename}>{s.filename}</li>
          ))}
        </ul>
      );

    case "CouldNotGetScripts":
      return `❌ Could not get scripts.`;
  }
}

function interpretResponse(
  decodingResult: td.DecoderResult<Array<ScriptSummary>>,
): ScriptListState {
  if (decodingResult.tag === "DecoderError") {
    return {
      tag: "CouldNotGetScripts",
      error: td.format(decodingResult.error, { sensitive: false }),
    };
  }

  return { tag: "HaveScripts", scripts: decodingResult.value };
}

function maybeLogError(scriptListState: ScriptListState): ScriptListState {
  switch (scriptListState.tag) {
    case "Loading":
    case "HaveScripts":
      break;

    case "CouldNotGetScripts":
      console.error(`Could not get scripts. Reason:`, scriptListState.error);
      break;

    default:
      assertExhausted(scriptListState, "script list state");
  }

  return scriptListState;
}
