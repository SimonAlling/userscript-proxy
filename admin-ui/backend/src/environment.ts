export function getEnvVarOrThrow(envVarName: string): string {
  const value = process.env[envVarName];

  if (value === undefined) {
    throw new Error(`Environment variable '${envVarName}' not specified.`);
  }

  return value;
}
