import type { Script } from "./userscript";

type EditScriptViewProps = {
  script: Script;
  draftSource: string;
  metadataError: string | null;
  isDirty: boolean;
  onDraftSourceChange: (draftSource: string) => void;
  onSave: () => Promise<void>;
  onSaveAndClose: () => Promise<void>;
  onClose: () => void;
  saving: boolean;
  saveError: string | null;
};

export function EditScriptView(props: EditScriptViewProps) {
  const {
    script,
    draftSource,
    metadataError,
    isDirty,
    onDraftSourceChange,
    onSave,
    onSaveAndClose,
    onClose,
    saving,
    saveError,
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
          <button
            onClick={() => void onSave().catch(console.error)}
            disabled={saving}
          >
            {saving ? "Saving..." : "Save"}
          </button>
          <button
            onClick={() => void onSaveAndClose().catch(console.error)}
            disabled={saving}
          >
            {saving ? "Saving..." : "Save & Close"}
          </button>
          <button onClick={onClose} disabled={saving}>
            Close
          </button>
        </div>

        {saveError !== null && <div className="errorBox">{saveError}</div>}
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
