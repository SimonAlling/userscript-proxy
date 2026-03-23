import { useEffect, useState } from "react";

import "./HealthCheckView.css";

import {
  showHealthCheckFailure,
  showHealthCheckResponse,
} from "./show-backend-status";

export function HealthCheckView() {
  const [backendStatus, setBackendStatus] = useState<string>("⏳ Loading …");

  useEffect(() => {
    fetch("/api/health")
      .then((response) => {
        setBackendStatus(showHealthCheckResponse(response));
      })
      .catch((caught: unknown) => {
        setBackendStatus(showHealthCheckFailure(caught));
      });
  }, []);

  return (
    <aside className="health-check">Backend status: {backendStatus}</aside>
  );
}
