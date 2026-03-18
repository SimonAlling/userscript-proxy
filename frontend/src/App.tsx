import { useState } from "react";
import "./App.css";
import { EditScriptView } from "./EditScriptView";
import { ListScriptsView } from "./ListScriptsView";
import { extractMetadata } from "./metadata";
import type { Script } from "./userscript";
import { assertExhausted } from "./util/assertions";

type UiState =
  | {
      tag: "ListScripts";
      scripts: ReadonlyArray<Script>;
    }
  | {
      tag: "EditScript";
      scripts: ReadonlyArray<Script>;
      scriptId: string;
      draftSource: string;
      metadataError: string | null;
      isDirty: boolean;
    };

const initialScripts: ReadonlyArray<Script> = [
  makeNewScript(crypto.randomUUID()),
];

function App() {
  const [uiState, setUiState] = useState<UiState>({
    tag: "ListScripts",
    scripts: initialScripts,
  });

  switch (uiState.tag) {
    case "ListScripts":
      return (
        <ListScriptsView
          scripts={uiState.scripts}
          onAddScript={() => {
            const newScript = makeNewScript(crypto.randomUUID());

            setUiState({
              tag: "ListScripts",
              scripts: [newScript, ...uiState.scripts],
            });
          }}
          onDeleteScript={(scriptId) => {
            setUiState({
              tag: "ListScripts",
              scripts: uiState.scripts.filter(
                (script) => script.id !== scriptId,
              ),
            });
          }}
          onToggleEnabled={(scriptId, enabled) => {
            setUiState({
              tag: "ListScripts",
              scripts: uiState.scripts.map((script) =>
                script.id === scriptId ? { ...script, enabled } : script,
              ),
            });
          }}
          onEditScript={(scriptId) => {
            const script = uiState.scripts.find((s) => s.id === scriptId);

            if (script === undefined) {
              return;
            }

            const parseResult = extractMetadata(script.source);

            setUiState({
              tag: "EditScript",
              scripts: uiState.scripts,
              scriptId: script.id,
              draftSource: script.source,
              metadataError:
                parseResult.tag === "Err" ? parseResult.error : null,
              isDirty: false,
            });
          }}
        />
      );

    case "EditScript": {
      const script = uiState.scripts.find((s) => s.id === uiState.scriptId);

      if (script === undefined) {
        return (
          <div className="app">
            <p>Script not found.</p>
          </div>
        );
      }

      return (
        <EditScriptView
          script={script}
          draftSource={uiState.draftSource}
          metadataError={uiState.metadataError}
          isDirty={uiState.isDirty}
          onDraftSourceChange={(draftSource) => {
            const result = extractMetadata(draftSource);

            if (result.tag === "Err") {
              setUiState({
                ...uiState,
                draftSource,
                metadataError: result.error,
                isDirty: draftSource !== script.source,
              });
              return;
            }

            setUiState({
              ...uiState,
              draftSource,
              metadataError: null,
              isDirty: draftSource !== script.source,
            });
          }}
          onSave={() => {
            const result = extractMetadata(uiState.draftSource);

            if (result.tag === "Err") {
              setUiState({
                ...uiState,
                metadataError: result.error,
              });
              return;
            }

            const updatedScripts = uiState.scripts.map((currentScript) =>
              currentScript.id === uiState.scriptId
                ? {
                    ...currentScript,
                    source: uiState.draftSource,
                    name: result.value.name,
                    version: result.value.version,
                  }
                : currentScript,
            );

            setUiState({
              tag: "EditScript",
              scripts: updatedScripts,
              scriptId: uiState.scriptId,
              draftSource: uiState.draftSource,
              metadataError: null,
              isDirty: false,
            });
          }}
          onSaveAndClose={() => {
            const result = extractMetadata(uiState.draftSource);

            if (result.tag === "Err") {
              setUiState({
                ...uiState,
                metadataError: result.error,
              });
              return;
            }

            const updatedScripts = uiState.scripts.map((currentScript) =>
              currentScript.id === uiState.scriptId
                ? {
                    ...currentScript,
                    source: uiState.draftSource,
                    name: result.value.name,
                    version: result.value.version,
                  }
                : currentScript,
            );

            setUiState({
              tag: "ListScripts",
              scripts: updatedScripts,
            });
          }}
          onClose={() => {
            if (uiState.isDirty) {
              const shouldDiscard = window.confirm("Discard unsaved changes?");

              if (!shouldDiscard) {
                return;
              }
            }

            setUiState({
              tag: "ListScripts",
              scripts: uiState.scripts,
            });
          }}
        />
      );
    }

    default:
      assertExhausted(uiState, "ui state");
  }
}

export default App;

function makeNewScript(id: string): Script {
  return {
    id,
    name: "New script",
    version: "0.1.0",
    enabled: true,
    source: `// ==UserScript==
// @name        New script
// @version     0.1.0
// @match       *://*/*
// ==/UserScript==
`,
  };
}
