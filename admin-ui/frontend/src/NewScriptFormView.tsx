import { isSafeScriptId } from "@userscript-proxy/core/script-id";

type NewScriptFormViewProps = {
  idDraft: string;
  onIdDraftChange: (id: string) => void;
  onCreate: () => void;
  onCancel: () => void;
};

export function NewScriptFormView(props: NewScriptFormViewProps) {
  const { idDraft, onIdDraftChange, onCreate, onCancel } = props;

  const isValid = isSafeScriptId(idDraft);

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <h1>New script</h1>
        </div>
        <div className="buttonGroup">
          <button onClick={onCreate} disabled={!isValid}>
            Create
          </button>
          <button onClick={onCancel}>Cancel</button>
        </div>
      </header>

      <main>
        <div className="formRow">
          <label htmlFor="scriptId">Script ID</label>
          <input
            id="scriptId"
            type="text"
            value={idDraft}
            onChange={(e) => {
              onIdDraftChange(e.target.value);
            }}
          />
        </div>
        {idDraft.length > 0 && !isValid && (
          <div className="errorBox">
            ID must be lowercase letters, numbers, and hyphens (e.g. my-script)
          </div>
        )}
        {isValid && <p>Will be saved as {idDraft}.user.js</p>}
      </main>
    </div>
  );
}
