import { useEffect, useRef, useState } from "react";

import { assertExhausted } from "@userscript-proxy/core/assertions";
import type { ErrorInfo } from "@userscript-proxy/core/errors";
import type { NoRejectPromise } from "@userscript-proxy/core/promises";

import "./ScriptEditorView.css";

type ScriptEditorState =
  | { tag: "Editing"; content: string; error: string | null }
  | { tag: "Saving"; content: string };

type Props = {
  filename: string;
  initialContent: string;
  onSave_NoReject: (content: string) => NoRejectPromise<null, ErrorInfo>;
  onClose: () => void;
};

export function ScriptEditorView({
  filename,
  initialContent,
  onSave_NoReject,
  onClose,
}: Props) {
  const [state, setState] = useState<ScriptEditorState>({
    tag: "Editing",
    content: initialContent,
    error: null,
  });

  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea !== null) {
      textarea.focus();
      textarea.setSelectionRange(textarea.value.length, textarea.value.length);
    }
  }, []);

  const isSaving = state.tag === "Saving";
  const content = state.content;
  const error = state.tag === "Editing" ? state.error : null;

  return (
    <div className="modal-panel">
      <div className="script-editor-header">
        <p className="script-editor-filename">{filename}</p>
        {error !== null && <p className="script-editor-error">{error}</p>}
        <div className="script-editor-actions">
          <button
            disabled={isSaving}
            onClick={() => {
              save(content);
            }}
          >
            Save
          </button>
          <button
            className="button-secondary"
            disabled={isSaving}
            onClick={() => {
              if (
                content === initialContent ||
                window.confirm("Are you sure?")
              ) {
                onClose();
              }
            }}
          >
            Cancel
          </button>
        </div>
      </div>
      <textarea
        ref={textareaRef}
        className="script-editor-textarea"
        disabled={isSaving}
        value={content}
        onChange={(e) => {
          setState({ tag: "Editing", content: e.target.value, error: null });
        }}
      />
    </div>
  );

  function save(contentToSave: string) {
    setState({ tag: "Saving", content: contentToSave });
    void onSave_NoReject(contentToSave).then((result) => {
      switch (result.tag) {
        case "Ok":
          // Parent handles navigation; nothing to do here.
          break;

        case "Err":
          console.error(result.error.logError);
          setState({
            tag: "Editing",
            content: contentToSave,
            error: result.error.uiError,
          });
          break;

        default:
          assertExhausted(result, "script-editor save result");
      }
    });
  }
}
