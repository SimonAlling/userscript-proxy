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

const initialScripts: ReadonlyArray<Script> = [
  {
    id: "1",
    name: "Dark mode helper",
    version: "0.1.0",
    enabled: true,
    source: `// ==UserScript==
// @name        Dark mode helper
// @version     0.1.0
// @match       *://example.com/*
// ==/UserScript==

console.log("hello");
`,
  },
  {
    id: "2",
    name: "YouTube cleanup",
    version: "1.0.0",
    enabled: false,
    source: `// ==UserScript==
// @name        YouTube cleanup
// @version     1.0.0
// @match       *://www.youtube.com/*
// ==/UserScript==
`,
  },
];

function App() {
  const [scripts, setScripts] = useState<ReadonlyArray<Script>>(initialScripts);
  const [selectedId, setSelectedId] = useState<string>(initialScripts[0].id);

  const [metadataError, setMetadataError] = useState<string | null>(null);

  const selectedScript = scripts.find((script) => script.id === selectedId);

  function updateSelectedScript(update: ScriptUpdate) {
    switch (update.tag) {
      case "EnabledChanged": {
        setMetadataError(null);

        setScripts((currentScripts) =>
          currentScripts.map((script) =>
            script.id === selectedId
              ? { ...script, enabled: update.enabled }
              : script,
          ),
        );

        break;
      }

      case "SourceChanged": {
        const result = extractMetadata(update.source);

        if (result.tag === "Err") {
          setMetadataError(result.error);
          return;
        }

        setMetadataError(null);

        setScripts((currentScripts) =>
          currentScripts.map((script) =>
            script.id === selectedId
              ? {
                  ...script,
                  source: update.source,
                  name: result.value.name,
                  version: result.value.version,
                }
              : script,
          ),
        );
        break;
      }

      default:
        assertExhausted(update, "script update action");
    }
  }

  function addScript() {
    const newScript = makeNewScript(crypto.randomUUID());

    setScripts((currentScripts) => [newScript, ...currentScripts]);
    setSelectedId(newScript.id);
  }

  function deleteSelectedScript() {
    const remainingScripts = scripts.filter(
      (script) => script.id !== selectedId,
    );
    setScripts(remainingScripts);

    if (remainingScripts.length > 0) {
      setSelectedId(remainingScripts[0].id);
    }
  }

  if (selectedScript === undefined) {
    return <div className="app">No script selected.</div>;
  }

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <h1>Userscript Proxy</h1>
          <p>Simple React prototype for managing userscripts</p>
        </div>
        <button onClick={addScript}>Add script</button>
      </header>

      <main className="layout">
        <aside className="sidebar">
          <h2>Scripts</h2>
          <ul className="scriptList">
            {scripts.map((script) => (
              <li key={script.id}>
                <button
                  className={
                    script.id === selectedId
                      ? "scriptListItem selected"
                      : "scriptListItem"
                  }
                  onClick={() => {
                    setSelectedId(script.id);
                  }}
                >
                  <div className="scriptListTitle">{script.name}</div>
                  <div className="scriptListMeta">
                    {script.version === null
                      ? ""
                      : "v" + script.version + " · "}
                    {script.enabled ? "Enabled" : "Disabled"}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <section className="editor">
          <div className="formRow checkboxRow">
            <label htmlFor="enabled">Enabled</label>
            <input
              id="enabled"
              type="checkbox"
              checked={selectedScript.enabled}
              onChange={(e) => {
                updateSelectedScript({
                  tag: "EnabledChanged",
                  enabled: e.target.checked,
                });
              }}
            />
          </div>

          <div className="formRow">
            <label htmlFor="source">Source</label>
            <textarea
              id="source"
              rows={16}
              value={selectedScript.source}
              onChange={(e) => {
                updateSelectedScript({
                  tag: "SourceChanged",
                  source: e.target.value,
                });
              }}
            />

            {metadataError !== null && (
              <div className="errorBox">{metadataError}</div>
            )}
          </div>

          <div className="buttonRow">
            <button className="dangerButton" onClick={deleteSelectedScript}>
              Delete script
            </button>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;

function makeNewScript(id: string): Script {
  return {
    id: id,
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

type ScriptUpdate =
  | { tag: "EnabledChanged"; enabled: boolean }
  | { tag: "SourceChanged"; source: string };
