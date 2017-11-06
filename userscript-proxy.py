import glob, os, fnmatch, re
from bs4 import BeautifulSoup
from mitmproxy import ctx, http
from metadata import MetadataError
from userscript import Userscript, UserscriptError, document_end, document_start, document_idle
from warnings import warn
import shlex
import warnings

DIR_USERSCRIPTS = "userscripts"
PATTERN_USERSCRIPT = "*.user.js"
RELEVANT_CONTENT_TYPES = ["text/html"]
REGEX_TEXT_HTML = re.compile(r"text/html")

def logInfo(s):
    ctx.log.info(s)

def logWarning(s):
    ctx.log.warn(s)

def logError(s):
    ctx.log.error(s)

class UserscriptInjector:
    def __init__(self):
        self.userscripts = []
        logInfo("Loading userscripts ...")
        try:
            os.chdir(DIR_USERSCRIPTS)
        except FileNotFoundError:
            logError("Cannot load userscripts. Directory `"+DIR_USERSCRIPTS+"` does not exist.")
        except PermissionError:
            logError("Cannot load userscripts. Permission was denied when trying to read directory `"+DIR_USERSCRIPTS+"`.")

        numberOfUserscripts = 0
        for unsafe_filename in glob.glob(PATTERN_USERSCRIPT):
            filename = shlex.quote(unsafe_filename)
            logInfo("    • "+filename)
            try:
                content = open(filename).read()
            except PermissionError:
                logError("Could not read file `"+filename+"`: Permission denied.")
                continue
            except Exception as e:
                logError("Could not read file `"+filename+"`: " + str(e))
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
            numberOfUserscripts = numberOfUserscripts + 1

        logInfo(str(numberOfUserscripts) + " userscript(s) loaded.")

    def getApplicableScripts(self, url):
        matchingScripts = []
        for script in self.userscripts:
            if script.isApplicable(url):
                matchingScripts.append(script)
        return matchingScripts

    def response(self, flow: http.HTTPFlow):
        if "Content-Type" in flow.response.headers:
            if REGEX_TEXT_HTML.match(flow.response.headers["Content-Type"]):
                applicableScripts = self.getApplicableScripts(flow.request.url)
                soup = BeautifulSoup(flow.response.content, "html.parser") # TODO: maybe change parser
                for script in self.userscripts:
                    if script.isApplicable(flow.request.url):
                        logInfo("Injecting %s into %s" % (script.getName(), flow.request.url))
                        tag = soup.new_tag("script")
                        tag.string = script.getContent()
                        if script.runAt == document_start:
                            soup.head.append(tag)
                        elif script.runAt == document_end:
                            soup.body.append(tag)
                        else:
                            logError(document_idle + " not supported.") # TODO: should be supported
                flow.response.content = str(soup).encode("utf8")


def start():
    return UserscriptInjector()
