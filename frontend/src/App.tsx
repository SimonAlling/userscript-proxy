import { useState } from "react";
import "./App.css";
import { extractMetadata } from "./metadata";
import { assertExhausted } from "./util/assertions";

type Script = {
  id: string;
  name: string;
  version: string | null;
  enabled: boolean;
  source: string;
};

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

type ListScriptsViewProps = {
  scripts: ReadonlyArray<Script>;
  onAddScript: () => void;
  onDeleteScript: (scriptId: string) => void;
  onToggleEnabled: (scriptId: string, enabled: boolean) => void;
  onEditScript: (scriptId: string) => void;
};

function ListScriptsView(props: ListScriptsViewProps) {
  const {
    scripts,
    onAddScript,
    onDeleteScript,
    onToggleEnabled,
    onEditScript,
  } = props;

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <h1>Userscript Proxy</h1>
          <p>Manage your installed userscripts</p>
        </div>
        <button onClick={onAddScript}>Add script</button>
      </header>

      <main className="listMode">
        {scripts.length === 0 ? (
          <div className="emptyState">No scripts installed.</div>
        ) : (
          <ul className="scriptCards">
            {scripts.map((script) => (
              <li key={script.id} className="scriptCard">
                <div className="scriptCardHeader">
                  <div>
                    <div className="scriptCardTitle">{script.name}</div>
                    <div className="scriptCardMeta">
                      {script.version === null
                        ? "No version"
                        : `v${script.version}`}{" "}
                      · {script.enabled ? "Enabled" : "Disabled"}
                    </div>
                  </div>

                  <label className="inlineCheckbox">
                    <input
                      type="checkbox"
                      checked={script.enabled}
                      onChange={(e) => {
                        onToggleEnabled(script.id, e.target.checked);
                      }}
                    />
                    Enabled
                  </label>
                </div>

                <div className="scriptCardActions">
                  <button
                    onClick={() => {
                      onEditScript(script.id);
                    }}
                  >
                    Edit
                  </button>
                  <button
                    className="dangerButton"
                    onClick={() => {
                      onDeleteScript(script.id);
                    }}
                  >
                    Delete
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </main>
    </div>
  );
}

type EditScriptViewProps = {
  script: Script;
  draftSource: string;
  metadataError: string | null;
  isDirty: boolean;
  onDraftSourceChange: (draftSource: string) => void;
  onSave: () => void;
  onSaveAndClose: () => void;
  onClose: () => void;
};

function EditScriptView(props: EditScriptViewProps) {
  const {
    script,
    draftSource,
    metadataError,
    isDirty,
    onDraftSourceChange,
    onSave,
    onSaveAndClose,
    onClose,
  } = props;

  return (
    <div className="app editModeApp">
      <header className="topbar">
        <div>
          <h1>Edit script</h1>
          <p>
            {script.name}
            {isDirty ? " · Unsaved changes" : ""}
          </p>
        </div>

        <div className="buttonGroup">
          <button onClick={onSave} disabled={metadataError !== null}>
            Save
          </button>
          <button onClick={onSaveAndClose} disabled={metadataError !== null}>
            Save &amp; Close
          </button>
          <button onClick={onClose}>Close</button>
        </div>
      </header>

      <main className="editMode">
        <section className="editorPanel">
          <div className="formRow">
            <label htmlFor="source">Source</label>
            <textarea
              id="source"
              rows={24}
              value={draftSource}
              onChange={(e) => {
                onDraftSourceChange(e.target.value);
              }}
            />
          </div>
        </section>

        <aside className="diagnosticsPanel">
          <h2>Diagnostics</h2>

          {metadataError !== null && (
            <div className="errorBox">{metadataError}</div>
          )}

          {metadataError === null && (
            <div className="okBox">No problems found.</div>
          )}
        </aside>
      </main>
    </div>
  );
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
