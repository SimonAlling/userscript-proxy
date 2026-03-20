import { useEffect, useState } from "react";
import { assertExhausted } from "@userscript-proxy/core/assertions";
import { extractMetadata } from "@userscript-proxy/core/metadata";
import "./App.css";
import { EditScriptView, type WhatIsBeingEdited } from "./EditScriptView";
import { ListScriptsView } from "./ListScriptsView";
import { NewScriptFormView } from "./NewScriptFormView";
import {
  createScript,
  deleteScript,
  getScript,
  listScripts,
  saveScriptSource,
  setScriptEnabled,
  type ScriptDetails,
} from "./api";
import { makeNewScriptSource, type Script } from "./userscript";

type UiState =
  | {
      tag: "Loading";
    }
  | {
      tag: "LoadFailed";
      error: string;
    }
  | {
      tag: "ListScripts";
      scripts: ReadonlyArray<Script>;
      saving: boolean;
    }
  | {
      tag: "NewScriptForm";
      scripts: ReadonlyArray<Script>;
      idDraft: string;
    }
  | {
      tag: "EditScript";
      scripts: ReadonlyArray<Script>;
      whatIsBeingEdited: WhatIsBeingEdited;
      draftSource: string;
      metadataError: string | null;
      isDirty: boolean;
      saving: boolean;
      saveError: string | null;
    };

function App() {
  const [uiState, setUiState] = useState<UiState>({ tag: "Loading" });

  useEffect(() => {
    let cancelled = false;

    async function load(): Promise<void> {
      try {
        const summaries = await listScripts();

        const scripts: ReadonlyArray<Script> = summaries.map((script) => ({
          id: script.id,
          name: script.name,
          version: script.version,
          enabled: script.enabled,
          source: "",
        }));

        if (cancelled) {
          return;
        }

        setUiState({
          tag: "ListScripts",
          scripts,
          saving: false,
        });
      } catch (error) {
        if (cancelled) {
          return;
        }

        setUiState({
          tag: "LoadFailed",
          error:
            error instanceof Error ? error.message : "Failed to load scripts.",
        });
      }
    }

    void load();

    return () => {
      cancelled = true;
    };
  }, []);

  switch (uiState.tag) {
    case "Loading":
      return <div className="app">Loading scripts...</div>;

    case "LoadFailed":
      return (
        <div className="app">
          <div className="errorBox">{uiState.error}</div>
        </div>
      );

    case "ListScripts":
      return (
        <ListScriptsView
          scripts={uiState.scripts}
          onAddScript={() => {
            setUiState({
              tag: "NewScriptForm",
              scripts: uiState.scripts,
              idDraft: "new-script",
            });
          }}
          onDeleteScript={(scriptId) => {
            const shouldDelete = window.confirm("Are you sure?");

            if (!shouldDelete) {
              return;
            }

            setUiState({
              ...uiState,
              saving: true,
            });

            deleteScript(scriptId).then(
              () => {
                setUiState({
                  tag: "ListScripts",
                  scripts: uiState.scripts.filter(
                    (script) => script.id !== scriptId,
                  ),
                  saving: false,
                });
              },
              (error: unknown) => {
                setUiState({
                  tag: "LoadFailed",
                  error:
                    error instanceof Error
                      ? error.message
                      : "Failed to delete script.",
                });
              },
            );
          }}
          onToggleEnabled={async (scriptId, enabled) => {
            setUiState({
              ...uiState,
              saving: true,
            });

            try {
              await setScriptEnabled(scriptId, enabled);

              setUiState({
                tag: "ListScripts",
                scripts: uiState.scripts.map((script) =>
                  script.id === scriptId ? { ...script, enabled } : script,
                ),
                saving: false,
              });
            } catch (error) {
              setUiState({
                tag: "LoadFailed",
                error:
                  error instanceof Error
                    ? error.message
                    : "Failed to update enabled state.",
              });
            }
          }}
          onEditScript={async (scriptId) => {
            setUiState({
              ...uiState,
              saving: true,
            });

            try {
              const script = await getScript(scriptId);

              const parseResult = extractMetadata(script.source);

              setUiState({
                tag: "EditScript",
                scripts: uiState.scripts.map((candidate) =>
                  // TODO: WHY???
                  candidate.id === script.id
                    ? toFrontendScript(script)
                    : candidate,
                ),
                whatIsBeingEdited: { tag: "ExistingScript", script: script },
                draftSource: script.source,
                metadataError:
                  parseResult.tag === "Err" ? parseResult.error : null,
                isDirty: false,
                saving: false,
                saveError: null,
              });
            } catch (error) {
              setUiState({
                tag: "LoadFailed",
                error:
                  error instanceof Error
                    ? error.message
                    : "Failed to load script details.",
              });
            }
          }}
        />
      );

    case "NewScriptForm":
      return (
        <NewScriptFormView
          idDraft={uiState.idDraft}
          existingIds={uiState.scripts.map((s) => s.id)}
          onIdDraftChange={(idDraft) => {
            setUiState({ ...uiState, idDraft });
          }}
          onCreate={() => {
            setUiState({
              tag: "EditScript",
              scripts: uiState.scripts,
              whatIsBeingEdited: { tag: "NewScript", id: uiState.idDraft },
              draftSource: makeNewScriptSource(),
              metadataError: null,
              isDirty: false,
              saving: false,
              saveError: null,
            });
          }}
          onCancel={() => {
            setUiState({
              tag: "ListScripts",
              scripts: uiState.scripts,
              saving: false,
            });
          }}
        />
      );

    case "EditScript": {
      return (
        <EditScriptView
          whatIsBeingEdited={uiState.whatIsBeingEdited}
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
                isDirty: deriveDirtiness(
                  draftSource,
                  uiState.whatIsBeingEdited,
                ),
              });
              return;
            }

            setUiState({
              ...uiState,
              draftSource,
              metadataError: null,
              isDirty: deriveDirtiness(draftSource, uiState.whatIsBeingEdited),
            });
          }}
          onSave={async () => {
            const parseResult = extractMetadata(uiState.draftSource);

            if (parseResult.tag === "Err") {
              setUiState({
                ...uiState,
                metadataError: parseResult.error,
                saveError: null,
              });
              return;
            }

            setUiState({
              ...uiState,
              saving: true,
              saveError: null,
            });

            try {
              let savedScript: ScriptDetails;

              if (uiState.whatIsBeingEdited.tag === "NewScript") {
                savedScript = await createScript(
                  uiState.whatIsBeingEdited.id,
                  uiState.draftSource,
                );
              } else {
                savedScript = await saveScriptSource(
                  uiState.whatIsBeingEdited.script.id,
                  uiState.draftSource,
                );
              }

              const updatedScripts =
                uiState.whatIsBeingEdited.tag === "NewScript"
                  ? [...uiState.scripts, toFrontendScript(savedScript)]
                  : uiState.scripts.map((script) =>
                      script.id === savedScript.id
                        ? toFrontendScript(savedScript)
                        : script,
                    );

              setUiState({
                tag: "EditScript",
                scripts: updatedScripts,
                whatIsBeingEdited: {
                  tag: "ExistingScript",
                  script: savedScript,
                },
                draftSource: savedScript.source,
                metadataError: null,
                isDirty: false,
                saving: false,
                saveError: null,
              });
            } catch (error) {
              setUiState({
                ...uiState,
                saving: false,
                saveError:
                  error instanceof Error
                    ? error.message
                    : "Failed to save script.",
              });
            }
          }}
          onSaveAndClose={async () => {
            const parseResult = extractMetadata(uiState.draftSource);

            if (parseResult.tag === "Err") {
              setUiState({
                ...uiState,
                metadataError: parseResult.error,
                saveError: null,
              });
              return;
            }

            setUiState({
              ...uiState,
              saving: true,
              saveError: null,
            });

            try {
              let savedScript: ScriptDetails;

              if (uiState.whatIsBeingEdited.tag === "NewScript") {
                savedScript = await createScript(
                  uiState.whatIsBeingEdited.id,
                  uiState.draftSource,
                );
              } else {
                savedScript = await saveScriptSource(
                  uiState.whatIsBeingEdited.script.id,
                  uiState.draftSource,
                );
              }

              const updatedScripts =
                uiState.whatIsBeingEdited.tag === "NewScript"
                  ? [...uiState.scripts, toFrontendScript(savedScript)]
                  : uiState.scripts.map((script) =>
                      script.id === savedScript.id
                        ? toFrontendScript(savedScript)
                        : script,
                    );

              setUiState({
                tag: "ListScripts",
                scripts: updatedScripts,
                saving: false,
              });
            } catch (error) {
              setUiState({
                ...uiState,
                saving: false,
                saveError:
                  error instanceof Error
                    ? error.message
                    : "Failed to save script.",
              });
            }
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
              saving: false,
            });
          }}
          saving={uiState.saving}
          saveError={uiState.saveError}
        />
      );
    }

    default:
      assertExhausted(uiState, "ui state");
  }
}

export default App;

function toFrontendScript(script: ScriptDetails): Script {
  return {
    id: script.id,
    name: script.name,
    version: script.version,
    enabled: script.enabled,
    source: script.source,
  };
}

function deriveDirtiness(
  draftSource: string,
  whatIsBeingEdited: WhatIsBeingEdited,
): boolean {
  switch (whatIsBeingEdited.tag) {
    case "NewScript":
      return draftSource !== makeNewScriptSource();

    case "ExistingScript":
      return draftSource !== whatIsBeingEdited.script.source;
  }
}
