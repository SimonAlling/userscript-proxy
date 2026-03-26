import { useEffect, useState } from "react";

import { BadRequestErrorBodyCodec } from "@userscript-proxy/core/api/BadRequestErrorBody";
import { InternalServerErrorBodyCodec } from "@userscript-proxy/core/api/InternalServerErrorBody";
import {
  ScriptDetailsCodec,
  type ScriptDetails,
} from "@userscript-proxy/core/api/ScriptDetails";
import { ScriptNotFoundErrorBodyCodec } from "@userscript-proxy/core/api/ScriptNotFoundErrorBody";
import type { UpdateScriptRequest } from "@userscript-proxy/core/api/UpdateScriptRequest";
import { assertExhausted } from "@userscript-proxy/core/assertions";
import {
  errorMessageFromCaught,
  type ErrorInfo,
} from "@userscript-proxy/core/errors";
import { decodeJsonBody_NoReject } from "@userscript-proxy/core/fetching";
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
      .then((response) => interpretLoadResponse_NoReject(response))
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
          onSave_NoReject={(content) => update_NoReject(filename, content)}
          onClose={onCancelled}
        />
      );

    default:
      assertExhausted(state, "edit-script state");
  }

  async function update_NoReject(
    filenameToSave: string,
    content: string,
  ): NoRejectPromise<null, ErrorInfo> {
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
      const result = await interpretUpdateResponse_NoReject(response);
      if (result.tag === "Ok") {
        onSaved();
      }
      return result;
    } catch (caught: unknown) {
      const errorMsg = errorMessageFromCaught(caught);
      return Err({
        uiError: "Unexpected error.",
        logError: `Unexpected error when updating script: ${errorMsg}`,
      });
    }
  }
}

async function interpretLoadResponse_NoReject(
  response: Response,
): Promise<Result<ScriptDetails, ErrorInfo>> {
  if (response.ok) {
    const decoded = await decodeJsonBody_NoReject(response, ScriptDetailsCodec);

    if (decoded.tag === "Err") {
      return Err({
        uiError: "Could not load script.",
        logError: `Could not load script. Reason: ${decoded.error}`,
      });
    }

    return Ok(decoded.value);
  }

  const logMessagePrefix =
    `Could not load script. Response status: ${response.status}.` as const;

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

    case 404: {
      const bodyResult = await decodeJsonBody_NoReject(
        response,
        ScriptNotFoundErrorBodyCodec,
      );
      return Err({
        uiError:
          bodyResult.tag === "Ok"
            ? `Script ${quote(bodyResult.value.missingScriptName)} not found.`
            : "Script not found.",
        logError:
          bodyResult.tag === "Ok"
            ? `${logMessagePrefix} Script ${quote(bodyResult.value.missingScriptName)} not found.`
            : `${logMessagePrefix} ${bodyResult.error}`,
      });
    }

    case 500: {
      const bodyResult = await decodeJsonBody_NoReject(
        response,
        InternalServerErrorBodyCodec,
      );
      return Err({
        uiError: "Server failed to load script.",
        logError:
          bodyResult.tag === "Ok"
            ? `${logMessagePrefix} Reason: ${bodyResult.value.serverErrorReason}`
            : `${logMessagePrefix} ${bodyResult.error}`,
      });
    }

    default:
      return Err({
        uiError: "Could not load script.",
        logError: `${logMessagePrefix} Server responded with ${response.status} ${response.statusText}.`,
      });
  }
}

async function interpretUpdateResponse_NoReject(
  response: Response,
): NoRejectPromise<null, ErrorInfo> {
  if (response.ok) {
    return Ok(null);
  }

  const logMessagePrefix =
    `Could not update script. Response status: ${response.status}.` as const;

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

    case 404: {
      const bodyResult = await decodeJsonBody_NoReject(
        response,
        ScriptNotFoundErrorBodyCodec,
      );
      return Err({
        uiError:
          bodyResult.tag === "Ok"
            ? `Script ${quote(bodyResult.value.missingScriptName)} not found on server.`
            : "Script not found on server.",
        logError:
          bodyResult.tag === "Ok"
            ? `${logMessagePrefix} Filename: ${quote(bodyResult.value.missingScriptName)}`
            : `${logMessagePrefix} ${bodyResult.error}`,
      });
    }

    case 500: {
      const bodyResult = await decodeJsonBody_NoReject(
        response,
        InternalServerErrorBodyCodec,
      );
      return Err({
        uiError: "Server failed to update script.",
        logError:
          bodyResult.tag === "Ok"
            ? `${logMessagePrefix} Reason: ${bodyResult.value.serverErrorReason}`
            : `${logMessagePrefix} ${bodyResult.error}`,
      });
    }

    default:
      return Err({
        uiError: "Could not update script.",
        logError: `${logMessagePrefix} Server responded with ${response.status} ${response.statusText}.`,
      });
  }
}
