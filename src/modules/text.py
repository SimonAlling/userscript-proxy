from modules.constants import APP_NAME, VERSION, VERSION_PREFIX
from modules.utilities import flag

description = "Inject userscripts using mitmproxy."

def stringifyVersion(version: str) -> str:
    return VERSION_PREFIX + version

INFO_MESSAGE: str = APP_NAME + " " + stringifyVersion(VERSION)

WELCOME_MESSAGE: str = "\n".join([
    "",
    "╔═" + "═" * len(INFO_MESSAGE) + "═╗",
    "║ " +           INFO_MESSAGE  + " ║",
    "╚═" + "═" * len(INFO_MESSAGE) + "═╝",
    "",
])
