export type ScriptSummary = {
  id: string;
  enabled: boolean;
  name: string;
  version: string | null;
};

export type ScriptDetails = {
  id: string;
  enabled: boolean;
  source: string;
  name: string;
  version: string | null;
};

type ErrorResponse = {
  error: string;
};

const API_BASE_URL = "http://localhost:3000";

async function readJsonOrThrow<T>(response: Response): Promise<T> {
  if (response.ok) {
    return (await response.json()) as T;
  }

  let errorMessage = `Request failed with status ${response.status}`;

  try {
    const errorBody = (await response.json()) as Partial<ErrorResponse>;
    if (typeof errorBody.error === "string") {
      errorMessage = errorBody.error;
    }
  } catch {
    // Ignore parse failure and keep default message.
  }

  throw new Error(errorMessage);
}

export async function listScripts(): Promise<ReadonlyArray<ScriptSummary>> {
  const response = await fetch(`${API_BASE_URL}/api/scripts`);
  const body = await readJsonOrThrow<{ scripts: ReadonlyArray<ScriptSummary> }>(
    response,
  );
  return body.scripts;
}

export async function getScript(id: string): Promise<ScriptDetails> {
  const response = await fetch(
    `${API_BASE_URL}/api/scripts/${encodeURIComponent(id)}`,
  );
  const body = await readJsonOrThrow<{ script: ScriptDetails }>(response);
  return body.script;
}

export async function saveScriptSource(
  id: string,
  source: string,
): Promise<ScriptDetails> {
  const response = await fetch(
    `${API_BASE_URL}/api/scripts/${encodeURIComponent(id)}/source`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ source }),
    },
  );

  const body = await readJsonOrThrow<{ script: ScriptDetails }>(response);
  return body.script;
}

export async function setScriptEnabled(
  id: string,
  enabled: boolean,
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/scripts/${encodeURIComponent(id)}/enabled`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ enabled }),
    },
  );

  if (!response.ok) {
    await readJsonOrThrow(response);
  }
}
