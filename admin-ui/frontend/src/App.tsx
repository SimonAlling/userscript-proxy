import "./App.css";
import { HealthCheckView } from "./health-check/HealthCheckView";
import { RestartButton } from "./proxy/RestartButton";
import { ScriptListView } from "./scripts/ScriptListView";

function App() {
  return (
    <div className="the-app">
      <header id="app-header">
        <h1>Userscript Proxy</h1>
        <div id="app-header-actions">
          <HealthCheckView />
          <RestartButton />
        </div>
      </header>
      <main>
        <ScriptListView />
      </main>
    </div>
  );
}

export default App;
