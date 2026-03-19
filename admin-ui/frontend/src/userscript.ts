export type Script = {
  id: string;
  name: string;
  version: string | null;
  enabled: boolean;
  source: string;
};

export function makeNewScriptSource(): string {
  return `// ==UserScript==
// @name        New script
// @version     0.1.0
// @match       *://*/*
// ==/UserScript==
`;
}
