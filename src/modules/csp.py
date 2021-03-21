import secrets
from typing import List, NamedTuple, Optional

from modules.userscript import Userscript
from modules.utilities import isSomething

# Reference: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy


class Injection(NamedTuple):
    userscript: Userscript
    nonce: Optional[str]


def headerWithScriptsAllowed(cspHeaderValue: str, injections: List[Injection]) -> str:
    # Example CSP header:
    #
    #     Content-Security-Policy: default-src 'self'; frame-src 'self'; img-src https:; connect-src 'self'
    #
    cspKeyValuePairs = [ directive.strip().split(" ", 1) for directive in cspHeaderValue.split(';') ]
    cspDict = { key: value for key, value in cspKeyValuePairs }
    if "script-src" not in cspDict:
        # Browsers fall back to default-src if there is no script-src.
        # Since there was no script-src directive and we are adding one, we include the default-src (if present) in it to avoid breaking the site's effective CSP.
        cspDict["script-src"] = cspDict["default-src"] if "default-src" in cspDict else ""
    sourcesToAllow = [ source(i) for i in injections ]
    cspDict["script-src"] += " " + " ".join(sourcesToAllow)
    return '; '.join([ f'{key} {value}' for key, value in cspDict.items() ])


def source(injection: Injection) -> str:
    if isSomething(injection.nonce):
        return f"'nonce-{injection.nonce}'"
    else:
        # MDN about host (i.e. download URL) sources: "Unlike other values below, single quotes shouldn't be used."
        return injection.userscript.downloadURL


def generateNonce():
    return secrets.token_hex() # If no argument is passed, "a reasonable default is used" for the number of bytes.
