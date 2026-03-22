import "./App.css";
import { HealthCheckView } from "./health-check/HealthCheckView";
import { ScriptListView } from "./scripts/ScriptListView";

function App() {
  return (
    <div className="the-app">
      <HealthCheckView />
      <ScriptListView />
    </div>
  );
}

export default App;
