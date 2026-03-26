import { useEffect, useState } from "react";
import * as td from "tiny-decoders";

import "./ScriptListView.css";

import { BadRequestErrorBodyCodec } from "@userscript-proxy/core/api/BadRequestErrorBody";
import { InternalServerErrorBodyCodec } from "@userscript-proxy/core/api/InternalServerErrorBody";
import {
  ScriptSummaryCodec,
  type ScriptSummary,
} from "@userscript-proxy/core/api/ScriptSummary";
import { assertExhausted } from "@userscript-proxy/core/assertions";
import {
  errorMessageFromCaught,
  type ErrorInfo,
} from "@userscript-proxy/core/errors";
import { decodeJsonBody_NoReject } from "@userscript-proxy/core/fetching";
import { howToSortFilenames } from "@userscript-proxy/core/files";
import type { NoRejectPromise } from "@userscript-proxy/core/promises";
import { Err, Ok } from "@userscript-proxy/core/results";

import { AddScriptView } from "./AddScriptView";
import { EditScriptView } from "./EditScriptView";

type ScriptListState =
  | { tag: "Loading" }
  | { tag: "HaveScripts"; scripts: ReadonlyArray<ScriptSummary> }
  | { tag: "CouldNotGetScripts"; error: string };

type ScriptListMode =
  | { tag: "ViewingScripts" }
  | { tag: "AddingScript" }
  | { tag: "EditingScript"; filename: string };

export function ScriptListView() {
  const [scriptListState, setScriptListState] = useState<ScriptListState>({
    tag: "Loading",
  });
  const [mode, setMode] = useState<ScriptListMode>({ tag: "ViewingScripts" });
  const [deleteError, setDeleteError] = useState<string | null>(null);

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
      {deleteError !== null && (
        <p className="script-list-delete-error">{deleteError}</p>
      )}
      {scripts !== null && mode.tag === "AddingScript" && (
        <AddScriptView
          existingFilenames={scripts.map((s) => s.filename)}
          onSaved={(script) => {
            setScriptListState({
              tag: "HaveScripts",
              scripts: [...scripts, script].toSorted((a, b) =>
                howToSortFilenames(a.filename, b.filename),
              ),
            });
            setMode({ tag: "ViewingScripts" });
          }}
          onCancelled={() => {
            setMode({ tag: "ViewingScripts" });
          }}
        />
      )}
      {mode.tag === "EditingScript" && (
        <EditScriptView
          filename={mode.filename}
          onSaved={() => {
            setMode({ tag: "ViewingScripts" });
          }}
          onCancelled={() => {
            setMode({ tag: "ViewingScripts" });
          }}
        />
      )}
      {renderScriptListState(
        scriptListState,
        (filename) => {
          setMode({ tag: "EditingScript", filename });
        },
        (filename) => {
          void handleDelete_NoReject(filename).then((result) => {
            if (result.tag === "Err") {
              console.error(result.error.logError);
              setDeleteError(result.error.uiError);
            }
          });
        },
      )}
    </section>
  );

  async function handleDelete_NoReject(
    filename: string,
  ): NoRejectPromise<null, ErrorInfo> {
    if (!window.confirm(`Delete ${filename}?`)) {
      return Ok(null);
    }

    setDeleteError(null);

    try {
      const response = await fetch(
        `/api/scripts/${encodeURIComponent(filename)}`,
        { method: "DELETE" },
      );
      const result = await interpretDeleteResponse_NoReject(response);

      if (result.tag === "Ok") {
        if (scripts !== null) {
          setScriptListState({
            tag: "HaveScripts",
            scripts: scripts.filter((s) => s.filename !== filename),
          });
        }

        return Ok(null);
      } else {
        return Err(result.error);
      }
    } catch (caught: unknown) {
      const msg = errorMessageFromCaught(caught);
      return Err({
        logError: `Unexpected error when deleting script: ${msg}`,
        uiError: "Unexpected error.",
      });
    }
  }
}

function renderScriptListState(
  scriptListState: ScriptListState,
  onEdit: (filename: string) => void,
  onDelete: (filename: string) => void,
) {
  switch (scriptListState.tag) {
    case "Loading":
      return "⏳ Loading …";

    case "HaveScripts":
      if (scriptListState.scripts.length === 0) {
        return <p className="script-list-empty">No scripts installed.</p>;
      }
      return (
        <ul className="script-list">
          {scriptListState.scripts.map((s) => (
            <li key={s.filename}>
              <span className="script-list-item-filename">{s.filename}</span>
              <div className="script-list-item-actions">
                <button
                  className="button-secondary"
                  onClick={() => {
                    onEdit(s.filename);
                  }}
                >
                  Edit
                </button>
                <button
                  className="button-danger"
                  onClick={() => {
                    onDelete(s.filename);
                  }}
                >
                  Delete
                </button>
              </div>
            </li>
          ))}
        </ul>
      );

    case "CouldNotGetScripts":
      return `❌ Could not get scripts.`;
  }
}

async function interpretDeleteResponse_NoReject(
  response: Response,
): NoRejectPromise<null, ErrorInfo> {
  if (response.ok || response.status === 404) {
    // Already gone; treat as success.
    return Ok(null);
  }

  const logMessagePrefix = `Could not delete script. Response status: ${response.status}.`;

  switch (response.status) {
    case 400: {
      const bodyResult = await decodeJsonBody_NoReject(
        response,
        BadRequestErrorBodyCodec,
      );
      return Err({
        uiError: "Invalid request.",
        logError:
          bodyResult.tag === "Ok"
            ? `${logMessagePrefix} Reason: ${bodyResult.value.badRequestReason}`
            : `${logMessagePrefix} ${bodyResult.error}`,
      });
    }

    case 500: {
      const bodyResult = await decodeJsonBody_NoReject(
        response,
        InternalServerErrorBodyCodec,
      );
      return Err({
        uiError: "Server failed to delete script.",
        logError:
          bodyResult.tag === "Ok"
            ? `${logMessagePrefix} Reason: ${bodyResult.value.serverErrorReason}`
            : `${logMessagePrefix} ${bodyResult.error}`,
      });
    }

    default:
      return Err({
        uiError: "Could not delete script.",
        logError: `${logMessagePrefix} Server responded with ${response.status} ${response.statusText}.`,
      });
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
