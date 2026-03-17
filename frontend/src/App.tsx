import { useState } from "react";
import "./App.css";

type Script = {
  id: string;
  name: string;
  version: string;
  enabled: boolean;
  matches: string[];
  source: string;
};

const initialScripts: ReadonlyArray<Script> = [
  {
    id: "1",
    name: "Dark mode helper",
    version: "0.1.0",
    enabled: true,
    matches: ["*://example.com/*"],
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
    matches: ["*://www.youtube.com/*"],
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

  const selectedScript = scripts.find((script) => script.id === selectedId);

  function updateSelectedScript(changes: Partial<Script>) {
    setScripts((currentScripts) =>
      currentScripts.map((script) =>
        script.id === selectedId ? { ...script, ...changes } : script,
      ),
    );
  }

  function addScript() {
    const newScript: Script = {
      id: crypto.randomUUID(),
      name: "New script",
      version: "0.1.0",
      enabled: true,
      matches: ["*://*/*"],
      source: `// ==UserScript==
// @name        New script
// @version     0.1.0
// @match       *://*/*
// ==/UserScript==
`,
    };

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

  if (!selectedScript) {
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
                    v{script.version} ·{" "}
                    {script.enabled ? "Enabled" : "Disabled"}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <section className="editor">
          <div className="formRow">
            <label htmlFor="name">Name</label>
            <input
              id="name"
              type="text"
              value={selectedScript.name}
              onChange={(e) => {
                updateSelectedScript({ name: e.target.value });
              }}
            />
          </div>

          <div className="formRow">
            <label htmlFor="version">Version</label>
            <input
              id="version"
              type="text"
              value={selectedScript.version}
              onChange={(e) => {
                updateSelectedScript({ version: e.target.value });
              }}
            />
          </div>

          <div className="formRow checkboxRow">
            <label htmlFor="enabled">Enabled</label>
            <input
              id="enabled"
              type="checkbox"
              checked={selectedScript.enabled}
              onChange={(e) => {
                updateSelectedScript({ enabled: e.target.checked });
              }}
            />
          </div>

          <div className="formRow">
            <label htmlFor="matches">Match patterns</label>
            <textarea
              id="matches"
              rows={4}
              value={selectedScript.matches.join("\n")}
              onChange={(e) => {
                updateSelectedScript({
                  matches: e.target.value
                    .split("\n")
                    .map((line) => line.trim())
                    .filter(Boolean),
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
                updateSelectedScript({ source: e.target.value });
              }}
            />
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
