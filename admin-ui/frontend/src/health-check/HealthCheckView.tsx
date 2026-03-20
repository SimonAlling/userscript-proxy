import { useEffect, useState } from "react";

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

  return <aside>Backend status: {backendStatus}</aside>;
}
