import { fooish } from "@userscript-proxy/core";

console.warn(fooish.decoder(5));

export type Script = {
  id: string;
  name: string;
  version: string | null;
  enabled: boolean;
  source: string;
};

export function makeNewScript(id: string): Script {
  return {
    id,
    name: "New script",
    version: "0.1.0",
    enabled: true,
    source: `// ==UserScript==
// @name        New script
// @version     0.1.0
// @match       *://*/*
// ==/UserScript==
`,
  };
}
