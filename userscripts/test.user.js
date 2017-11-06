// ==UserScript==
// @name         Example Userscript
// @version      0.1.0
// @description  A basic example userscript.
// @author       John Smith
// @match        *://example.com/*
// @match        *://www.example.com/*
// @namespace    mywebsite.example
// @run-at       document-start
// ==/UserScript==

var styleElement = document.createElement("style");
styleElement.textContent = "body { color: red !important; }";
document.head.appendChild(styleElement);
