export function boilerplate(filenameWithoutExtension: string): string {
  return `\
// ==UserScript==
// @name         ${filenameWithoutExtension}
// @namespace    http://me.example.com
// @match        *://example.com/*
// @version      1.0
// @description  A cool userscript.
// ==/UserScript==

`;
}
