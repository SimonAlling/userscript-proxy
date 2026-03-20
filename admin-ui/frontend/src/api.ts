import * as td from "tiny-decoders";

import { decodeOrThrow } from "@userscript-proxy/core/decoding";

export type ScriptSummary = {
  id: string;
  enabled: boolean;
  name: string;
  version: string | null;
};

const ScriptSummary: td.Codec<ScriptSummary> = td.fields({
  id: td.string,
  enabled: td.boolean,
  name: td.string,
  version: td.nullOr(td.string),
});

export type ScriptDetails = {
  id: string;
  enabled: boolean;
  source: string;
  name: string;
  version: string | null;
};

const ScriptDetails: td.Codec<ScriptDetails> = td.fields({
  id: td.string,
  enabled: td.boolean,
  source: td.string,
  name: td.string,
  version: td.nullOr(td.string),
});

type ErrorResponse = {
  error: string;
};

const ErrorResponse: td.Codec<ErrorResponse> = td.fields({
  error: td.string,
});

const API_BASE_URL = "http://localhost:3000";

async function readJsonOrThrow<T>(
  response: Response,
  codec: td.Codec<T>,
): Promise<T> {
  const data: unknown = await response.json();

  if (response.ok) {
    return decodeOrThrow({
      codec: codec,
      data: data,
      context: "API response",
      dataIsSensitive: false,
    });
  }

  let errorMessage = `Request failed with status ${response.status}`;

  try {
    const decodingResult = decodeOrThrow({
      codec: ErrorResponse,
      data: data,
      context: "API response",
      dataIsSensitive: false,
    });

    errorMessage = decodingResult.error;
  } catch {
    // Ignore parse failure and keep default message.
  }

  throw new Error(errorMessage);
}

export async function listScripts(): Promise<ReadonlyArray<ScriptSummary>> {
  const response = await fetch(`${API_BASE_URL}/api/scripts`);
  const body = await readJsonOrThrow(
    response,
    td.fields({
      scripts: td.array(ScriptSummary),
    }),
  );
  return body.scripts;
}

export async function getScript(id: string): Promise<ScriptDetails> {
  const response = await fetch(
    `${API_BASE_URL}/api/scripts/${encodeURIComponent(id)}`,
  );
  const body = await readJsonOrThrow(
    response,
    td.fields({ script: ScriptDetails }),
  );
  return body.script;
}

export async function createScript(
  id: string,
  source: string,
): Promise<ScriptDetails> {
  const response = await fetch(`${API_BASE_URL}/api/scripts`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ id, source }),
  });
  const body = await readJsonOrThrow(
    response,
    td.fields({ script: ScriptDetails }),
  );
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

  const body = await readJsonOrThrow(
    response,
    td.fields({ script: ScriptDetails }),
  );
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

  await readJsonOrThrow(response, td.number);
}
