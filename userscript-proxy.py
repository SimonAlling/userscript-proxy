from typing import List, Callable, Pattern
import glob, os, re
from bs4 import BeautifulSoup
from mitmproxy import ctx, http
from metadata import MetadataError
import userscript
from userscript import Userscript, UserscriptError, document_end, document_start, document_idle
from utilities import first, second
import shlex
import warnings

def stringifyVersion(version: str) -> str:
    return VERSION_PREFIX + version

VERSION: str = "0.2.0"
VERSION_PREFIX: str = "v"
WELCOME_MESSAGE: str = "Userscript Proxy " + stringifyVersion(VERSION)
DIRS_USERSCRIPTS: List[str] = ["userscripts"]
PATTERN_USERSCRIPT: str = "*.user.js"
RELEVANT_CONTENT_TYPES: List[str] = ["text/html"]
REGEX_TEXT_HTML: Pattern = re.compile(r"text/html")
TAB: str = "    "

def logInfo(s: str) -> None:
    try:
        ctx.log.info(s)
    except Exception:
        print(s)

def logWarning(s: str) -> None:
    try:
        ctx.log.warn(s)
    except Exception:
        print(s)

def logError(s: str) -> None:
    try:
        ctx.log.error(s)
    except Exception:
        print(s)

class UserscriptInjector:
    def __init__(self):
        self.userscripts: List[Userscript] = []
        logInfo("")
        logInfo("╔═" + "═" * len(WELCOME_MESSAGE) + "═╗")
        logInfo("║ " +           WELCOME_MESSAGE  + " ║")
        logInfo("╚═" + "═" * len(WELCOME_MESSAGE) + "═╝")
        logInfo("")
        logInfo("Loading userscripts ...")
        loadedUserscripts: List[Tuple[Userscript, str]] = []
        for directory in DIRS_USERSCRIPTS:
            logInfo("Looking for userscripts (`"+PATTERN_USERSCRIPT+"`) in directory `"+directory+"` ...")
            try:
                os.chdir(directory)
            except FileNotFoundError:
                logWarning("Directory `"+directory+"` does not exist.")
                continue
            except PermissionError:
                logError("Permission was denied when trying to read directory `"+DIR_USERSCRIPTS+"`.")
                continue

            for unsafe_filename in glob.glob(PATTERN_USERSCRIPT):
                filename = shlex.quote(unsafe_filename)
                logInfo("Loading " + filename + " ...")
                try:
                    content = open(filename).read()
                except PermissionError:
                    logError("Could not read file `"+filename+"`: Permission denied.")
                    continue
                except Exception as e:
                    logError("Could not read file `"+filename+"`: " + str(e))
                    continue
                try:
                    loadedUserscripts.append((userscript.create(content), filename))
                except MetadataError as err:
                    logError("Metadata error:")
                    logError(str(err))
                    continue
                except UserscriptError as err:
                    logError("Userscript error:")
                    logError(str(err))
                    continue

        logInfo("")
        logInfo(str(len(loadedUserscripts)) + " userscript(s) loaded:")
        for s in loadedUserscripts:
            logInfo(TAB + "• "+first(s).name+" ("+second(s)+")")
        logInfo("")
        self.userscripts = list(map(first, loadedUserscripts))


    def response(self, flow: http.HTTPFlow):
        if "Content-Type" in flow.response.headers:
            if REGEX_TEXT_HTML.match(flow.response.headers["Content-Type"]):
                soup = BeautifulSoup(flow.response.content, "html.parser") # TODO: maybe change parser
                isApplicable: Callable[[Userscript], bool] = userscript.applicableChecker(flow.request.url)
                for script in self.userscripts:
                    if isApplicable(script):
                        logInfo(f"Injecting {script.name} into {flow.request.url} ...")
                        tag = soup.new_tag("script")
                        if script.runAt == document_start:
                            tag.string = script.content
                            soup.head.append(tag)
                        elif script.runAt == document_idle:
                            tag.string = userscript.wrapInEventListener("load", script.content)
                            soup.head.append(tag)
                        else:
                            tag.string = script.content
                            soup.body.append(tag)
                flow.response.content = str(soup).encode("utf8")


def start():
    return UserscriptInjector()
