export function isSafeScriptId(id: string): boolean {
  return /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(id);
}

export function slugifyScriptName(name: string): string {
  return name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}
