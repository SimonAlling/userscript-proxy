import { useEffect, useState } from "react";
import * as td from "tiny-decoders";

import "./ScriptListView.css";

import {
  ScriptSummaryCodec,
  type ScriptSummary,
} from "@userscript-proxy/core/api/ScriptSummary";
import { assertExhausted } from "@userscript-proxy/core/assertions";

import { AddScriptView } from "./AddScriptView";

type ScriptListState =
  | { tag: "Loading" }
  | { tag: "HaveScripts"; scripts: ReadonlyArray<ScriptSummary> }
  | { tag: "CouldNotGetScripts"; error: string };

type ScriptListMode = { tag: "ViewingScripts" } | { tag: "AddingScript" };

export function ScriptListView() {
  const [scriptListState, setScriptListState] = useState<ScriptListState>({
    tag: "Loading",
  });
  const [mode, setMode] = useState<ScriptListMode>({ tag: "ViewingScripts" });

  useEffect(() => {
    fetch("/api/scripts")
      .then((r) => r.json())
      .then(td.array(ScriptSummaryCodec).decoder)
      .then(interpretResponse)
      .then(maybeLogError)
      .then(setScriptListState)
      .catch(console.error);
  }, []);

  const scripts =
    scriptListState.tag === "HaveScripts" ? scriptListState.scripts : null;

  return (
    <section id="script-list-section">
      <div className="script-list-header">
        <h2>Installed scripts</h2>
        {scripts !== null && mode.tag === "ViewingScripts" && (
          <button
            onClick={() => {
              setMode({ tag: "AddingScript" });
            }}
          >
            Add script
          </button>
        )}
      </div>
      {scripts !== null && mode.tag === "AddingScript" && (
        <AddScriptView
          existingFilenames={scripts.map((s) => s.filename)}
          onSaved={(script) => {
            setScriptListState({
              tag: "HaveScripts",
              scripts: [...scripts, script],
            });
            setMode({ tag: "ViewingScripts" });
          }}
          onCancelled={() => {
            setMode({ tag: "ViewingScripts" });
          }}
        />
      )}
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
