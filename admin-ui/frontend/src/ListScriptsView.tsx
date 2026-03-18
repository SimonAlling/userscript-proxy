import type { Script } from "./userscript";

type ListScriptsViewProps = {
  scripts: ReadonlyArray<Script>;
  onAddScript: () => void;
  onDeleteScript: (scriptId: string) => void;
  onToggleEnabled: (scriptId: string, enabled: boolean) => void;
  onEditScript: (scriptId: string) => void;
};

export function ListScriptsView(props: ListScriptsViewProps) {
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
