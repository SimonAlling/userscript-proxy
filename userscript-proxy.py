import glob, os, fnmatch, re
from bs4 import BeautifulSoup
from mitmproxy import ctx, http
from metadata import MetadataError
from userscript import Userscript, UserscriptError, document_end, document_start, document_idle
from warnings import warn
import shlex
import warnings

def stringifyVersion(version):
    return VERSION_PREFIX + str(version)

VERSION = "0.0.1"
VERSION_PREFIX = "v"
WELCOME_MESSAGE = "Userscript Proxy " + stringifyVersion(VERSION)
DIRS_USERSCRIPTS = ["userscripts"]
PATTERN_USERSCRIPT = "*.user.js"
RELEVANT_CONTENT_TYPES = ["text/html"]
REGEX_TEXT_HTML = re.compile(r"text/html")
TAB = "    "

def logInfo(s):
    ctx.log.info(s)

def logWarning(s):
    ctx.log.warn(s)

def logError(s):
    ctx.log.error(s)

class UserscriptInjector:
    def __init__(self):
        self.userscripts = []
        logInfo("")
        logInfo("╔═" + "═" * len(WELCOME_MESSAGE) + "═╗")
        logInfo("║ " + WELCOME_MESSAGE            + " ║")
        logInfo("╚═" + "═" * len(WELCOME_MESSAGE) + "═╝")
        logInfo("")
        logInfo("Loading userscripts ...")
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
                logInfo(TAB + "• "+filename)
                try:
                    content = open(filename).read()
                except PermissionError:
                    logError("Could not read file `"+filename+"`: Permission denied.")
                    continue
                except Exception as e:
                    logError("Could not read file `"+filename+"`: " + str(e))
                    continue
                try:
                    self.userscripts.append(Userscript(filename, content))
                except MetadataError as err:
                    logError("Metadata error:")
                    logError(err.str())
                    continue
                except UserscriptError as err:
                    logError("There was an error with a userscript:")
                    logError(err.str())
                    continue

        logInfo("")
        logInfo(str(len(self.userscripts)) + " userscript(s) loaded:")
        for s in self.userscripts:
            logInfo(TAB + "• "+s.getName()+" ("+s.filename+")")
        logInfo("")


    def response(self, flow: http.HTTPFlow):
        if "Content-Type" in flow.response.headers:
            if REGEX_TEXT_HTML.match(flow.response.headers["Content-Type"]):
                soup = BeautifulSoup(flow.response.content, "html.parser") # TODO: maybe change parser
                for script in self.userscripts:
                    if script.isApplicable(flow.request.url):
                        logInfo("Injecting %s into %s" % (script.getName(), flow.request.url))
                        tag = soup.new_tag("script")
                        scriptContent = script.getContent()
                        if script.runAt == document_start:
                            tag.string = scriptContent
                            soup.head.append(tag)
                        elif script.runAt == document_idle:
                            tag.string = Userscript.wrapInEventListener("load", scriptContent)
                            soup.head.append(tag)
                        elif script.runAt == document_end:
                            tag.string = scriptContent
                            soup.body.append(tag)
                flow.response.content = str(soup).encode("utf8")


def start():
    return UserscriptInjector()
