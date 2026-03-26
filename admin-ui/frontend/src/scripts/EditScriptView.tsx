import { useEffect, useState } from "react";

import {
  ScriptDetailsCodec,
  type ScriptDetails,
} from "@userscript-proxy/core/api/ScriptDetails";
import type { UpdateScriptRequest } from "@userscript-proxy/core/api/UpdateScriptRequest";
import { assertExhausted } from "@userscript-proxy/core/assertions";
import { decodeWith } from "@userscript-proxy/core/decoding";
import {
  errorMessageFromCaught,
  type ErrorInfo,
} from "@userscript-proxy/core/errors";
import type { NoRejectPromise } from "@userscript-proxy/core/promises";
import { Err, Ok, type Result } from "@userscript-proxy/core/results";
import { quote } from "@userscript-proxy/core/strings";

import { ScriptEditorView } from "./ScriptEditorView";

type EditScriptState =
  | { tag: "Loading" }
  | { tag: "Loaded"; content: string }
  | { tag: "CouldNotLoad"; error: string };

type Props = {
  filename: string;
  onSaved: () => void;
  onCancelled: () => void;
};

export function EditScriptView({ filename, onSaved, onCancelled }: Props) {
  const [state, setState] = useState<EditScriptState>({ tag: "Loading" });

  useEffect(() => {
    void fetch(`/api/scripts/${encodeURIComponent(filename)}`)
      .then((response) => interpretLoadResponse(response))
      .then((result) => {
        switch (result.tag) {
          case "Ok":
            setState({ tag: "Loaded", content: result.value.scriptContent });
            break;

          case "Err":
            console.error(result.error.logError);
            setState({ tag: "CouldNotLoad", error: result.error.uiError });
            break;

          default:
            assertExhausted(result, "load-script response interpretation");
        }
      })
      .catch((caught: unknown) => {
        setState({
          tag: "CouldNotLoad",
          error: `Unexpected error: ${errorMessageFromCaught(caught)}`,
        });
      });
  }, [filename]);

  switch (state.tag) {
    case "Loading":
      return (
        <div className="modal-panel">
          <p>Loading {filename} …</p>
        </div>
      );

    case "CouldNotLoad":
      return (
        <div className="modal-panel">
          <p>
            Could not load <code>{filename}</code>. Reason:
            <pre>{state.error}</pre>
          </p>
          <button className="button-secondary" onClick={onCancelled}>
            Close
          </button>
        </div>
      );

    case "Loaded":
      return (
        <ScriptEditorView
          filename={filename}
          initialContent={state.content}
          onSave_NoReject={(content) => save_NoReject(filename, content)}
          onClose={onCancelled}
        />
      );

    default:
      assertExhausted(state, "edit-script state");
  }

  async function save_NoReject(
    filenameToSave: string,
    content: string,
  ): NoRejectPromise<null> {
    try {
      const response = await fetch(
        `/api/scripts/${encodeURIComponent(filenameToSave)}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            newScriptContent: content,
          } satisfies UpdateScriptRequest),
        },
      );
      const result = await interpretSaveResponse(response);
      if (result.tag === "Ok") {
        onSaved();
      }
      return result;
    } catch (caught: unknown) {
      const errorMsg = errorMessageFromCaught(caught);
      return Err({
        uiError: "Unexpected error.",
        logError: `Unexpected error when saving script: ${errorMsg}`,
      });
    }
  }
}

async function interpretLoadResponse(
  response: Response,
): Promise<Result<ScriptDetails, ErrorInfo>> {
  if (response.ok) {
    const body: unknown = await response.json();
    const decoded = decodeWith(ScriptDetailsCodec, body, false);

    if (decoded.tag === "Err") {
      return Err({
        uiError: "Could not load script.",
        logError: `Could not load script. Reason: Unexpected response shape: ${decoded.error}`,
      });
    }

    return Ok(decoded.value);
  }

  const bodyText = await response.text();
  const logMessagePrefix = `Could not load script. Response status: ${response.status}.`;

  switch (response.status) {
    case 400:
      return Err({
        uiError: "Invalid request.",
        logError: `${logMessagePrefix} Reason: ${bodyText}`,
      });

    case 404:
      return Err({
        uiError: `Script ${quote(bodyText)} not found.`,
        logError: `${logMessagePrefix} Script ${quote(bodyText)} not found.`,
      });

    case 500:
      return Err({
        uiError: "Server failed to load script.",
        logError: `${logMessagePrefix} Reason: ${bodyText}`,
      });

    default:
      return Err({
        uiError: "Could not load script.",
        logError: `${logMessagePrefix} Server responded with ${response.status} ${response.statusText}.`,
      });
  }
}

async function interpretSaveResponse(
  response: Response,
): Promise<Result<null, ErrorInfo>> {
  if (response.ok) {
    return Ok(null);
  }

  const bodyText = await response.text();
  const logMessagePrefix = `Could not update script. Response status: ${response.status}.`;

  switch (response.status) {
    case 400:
      return Err({
        uiError: "Invalid request.",
        logError: `${logMessagePrefix} Reason: ${bodyText}`,
      });

    case 404:
      return Err({
        uiError: `Script ${quote(bodyText)} not found on server.`,
        logError: `${logMessagePrefix} Filename: ${bodyText}`,
      });

    case 500:
      return Err({
        uiError: "Server failed to update script.",
        logError: `${logMessagePrefix} Reason: ${bodyText}`,
      });

    default:
      return Err({
        uiError: "Could not update script.",
        logError: `${logMessagePrefix} Server responded with ${response.status} ${response.statusText}.`,
      });
  }
}
