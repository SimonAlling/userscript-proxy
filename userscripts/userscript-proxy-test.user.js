// ==UserScript==
// @name         Userscript Proxy Test
// @version      1.0.0
// @match        *://example.com/*
// @match        *://www.example.com/*
// @run-at       document-start
// ==/UserScript==

(d => {
  "use strict";
  const CSS = "html body { color: green; background-color: #9E9; }";
  const T = "Userscript Proxy working!";
  d.head.appendChild(d.createElement("style")).textContent = CSS;
  d.addEventListener("DOMContentLoaded", _ => (d.querySelector("h1") || d.body).textContent = T);
})(document);
