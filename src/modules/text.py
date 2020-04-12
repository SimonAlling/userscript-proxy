import modules.constants as C

description = "Inject userscripts using mitmproxy."

def stringifyVersion(version: str) -> str:
    return C.VERSION_PREFIX + version

INFO_MESSAGE: str = C.APP_NAME + " " + stringifyVersion(C.VERSION)

WELCOME_MESSAGE: str = "\n".join([
    "",
    "╔═" + "═" * len(INFO_MESSAGE) + "═╗",
    "║ " +           INFO_MESSAGE  + " ║",
    "╚═" + "═" * len(INFO_MESSAGE) + "═╝",
    "",
])
