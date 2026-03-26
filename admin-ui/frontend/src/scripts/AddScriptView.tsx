import { useState } from "react";

import type { CreateScriptRequest } from "@userscript-proxy/core/api/CreateScriptRequest";
import type { ScriptSummary } from "@userscript-proxy/core/api/ScriptSummary";
import { assertExhausted } from "@userscript-proxy/core/assertions";
import {
  errorMessageFromCaught,
  type ErrorInfo,
} from "@userscript-proxy/core/errors";
import { validateFilename, withExtension } from "@userscript-proxy/core/files";
import type { NoRejectPromise } from "@userscript-proxy/core/promises";
import { Err, Ok, type Result } from "@userscript-proxy/core/results";
import { quote } from "@userscript-proxy/core/strings";
import { boilerplate } from "@userscript-proxy/core/userscripts";

import "./AddScriptView.css";
import { ScriptEditorView } from "./ScriptEditorView";

type AddScriptState =
  | {
      tag: "EnteringFilename";
      filenameWithoutExtension: string;
      error: string | null;
    }
  | { tag: "Editor"; filenameWithoutExtension: string };

type Props = {
  existingFilenames: ReadonlyArray<string>;
  onSaved: (script: ScriptSummary) => void;
  onCancelled: () => void;
};

export function AddScriptView({
  existingFilenames,
  onSaved,
  onCancelled,
}: Props) {
  const [state, setState] = useState<AddScriptState>({
    tag: "EnteringFilename",
    filenameWithoutExtension: "",
    error: null,
  });

  switch (state.tag) {
    case "EnteringFilename":
      return (
        <div className="modal-overlay">
          <div className="modal-dialog">
            <div className="add-script-filename-row">
              <input
                autoFocus
                className="add-script-input"
                placeholder="my-script"
                type="text"
                value={state.filenameWithoutExtension}
                onChange={(e) => {
                  setState({
                    tag: "EnteringFilename",
                    filenameWithoutExtension: e.target.value,
                    error: null,
                  });
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault(); // Otherwise the Enter press is also interpreted as typing a newline in the edit-mode textarea.
                    proceedToEditor(state.filenameWithoutExtension);
                  }
                }}
              />
              <span className="add-script-ext">{withExtension("")}</span>
            </div>
            <p className="add-script-error">{state.error}</p>
            <div className="add-script-actions">
              <button
                onClick={() => {
                  proceedToEditor(state.filenameWithoutExtension);
                }}
              >
                Create
              </button>
              <button className="button-secondary" onClick={onCancelled}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      );

    case "Editor":
      return (
        <ScriptEditorView
          filename={withExtension(state.filenameWithoutExtension)}
          initialContent={boilerplate(state.filenameWithoutExtension)}
          onSave_NoReject={(content) =>
            saveScript_NoReject(state.filenameWithoutExtension, content)
          }
          onClose={onCancelled}
        />
      );

    default:
      assertExhausted(state, "add script state");
  }

  function proceedToEditor(filenameWithoutExtension: string) {
    const validationResult = validateFilename(filenameWithoutExtension);
    if (validationResult.tag === "Err") {
      setState({
        tag: "EnteringFilename",
        filenameWithoutExtension,
        error: validationResult.error,
      });
      return;
    }

    if (existingFilenames.includes(withExtension(filenameWithoutExtension))) {
      setState({
        tag: "EnteringFilename",
        filenameWithoutExtension,
        error: "A script with this name already exists.",
      });
      return;
    }

    setState({ tag: "Editor", filenameWithoutExtension });
  }

  async function saveScript_NoReject(
    filenameWithoutExtension: string,
    content: string,
  ): NoRejectPromise<null, ErrorInfo> {
    try {
      const response = await fetch("/api/scripts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content,
          filenameWithoutExtension,
        } satisfies CreateScriptRequest),
      });

      const result = await interpretSaveResponse(response);

      if (result.tag === "Ok") {
        onSaved({ filename: withExtension(filenameWithoutExtension) });
      }

      return result;
    } catch (caught: unknown) {
      return Err({
        uiError: "Unexpected error.",
        logError: `Unexpected error when saving script: ${errorMessageFromCaught(caught)}`,
      });
    }
  }
}

async function interpretSaveResponse(
  response: Response,
): Promise<Result<null, ErrorInfo>> {
  if (response.ok) {
    return Ok(null);
  }

  const bodyText = await response.text();

  const logMessagePrefix = `Could not save script. Response status: ${response.status}.`;

  switch (response.status) {
    case 400:
      return Err({
        uiError: "Invalid request.",
        logError: `${logMessagePrefix} Reason: ${bodyText}`,
      });

    case 409:
      return Err({
        uiError: "A script with that name already exists.",
        logError: `${logMessagePrefix} A script named ${quote(bodyText)} already exists.`,
      });

    case 500:
      return Err({
        uiError: "Server failed to save script.",
        logError: `${logMessagePrefix} Reason: ${bodyText}`,
      });

    default:
      return Err({
        uiError: "Could not save script.",
        logError: `${logMessagePrefix} Server responded with ${response.status} ${response.statusText}.`,
      });
  }
}
