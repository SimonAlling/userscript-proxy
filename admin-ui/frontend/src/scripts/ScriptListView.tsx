import { useEffect, useState } from "react";

export function ScriptListView() {
  const [apiResponse, setApiResponse] = useState<unknown>(undefined);

  useEffect(() => {
    fetch("/api/scripts")
      .then((r) => r.json())
      .then(setApiResponse)
      .catch(console.error);
  }, []);

  return <pre>{JSON.stringify(apiResponse)}</pre>;
}
