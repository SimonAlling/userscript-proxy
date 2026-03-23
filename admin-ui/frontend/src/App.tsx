import "./App.css";
import { HealthCheckView } from "./health-check/HealthCheckView";
import { RestartButton } from "./proxy/RestartButton";
import { ScriptListView } from "./scripts/ScriptListView";

function App() {
  return (
    <div className="the-app">
      <HealthCheckView />
      <RestartButton />
      <ScriptListView />
    </div>
  );
}

export default App;
