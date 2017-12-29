from typing import Optional, Iterable, List, Callable, Pattern, Match
import glob, os, re
from bs4 import BeautifulSoup, Comment, Doctype
from mitmproxy import ctx, http
from functools import partial
import shlex
import warnings
from lib.metadata import MetadataError
import lib.userscript as userscript
from lib.userscript import Userscript, UserscriptError, document_end, document_start, document_idle
from lib.utilities import first, second, itemList, fromOptional

def stringifyVersion(version: str) -> str:
    return VERSION_PREFIX + version

VERSION: str = "0.4.0"
VERSION_PREFIX: str = "v"
APP_NAME: str = "Userscript Proxy"
WELCOME_MESSAGE: str = APP_NAME + " " + stringifyVersion(VERSION)
DIRS_USERSCRIPTS: List[str] = ["userscripts"]
PATTERN_USERSCRIPT: str = "*.user.js"
CONTENT_TYPE: str = "Content-Type"
RELEVANT_CONTENT_TYPES: List[str] = ["text/html", "application/xhtml+xml"]
CHARSET_DEFAULT: str = "utf-8"
REGEX_CHARSET: Pattern = re.compile(r"charset=([^;\s]+)")
TAB: str = "    "
LIST_ITEM_PREFIX: str = TAB + "• "
HTML_PARSER: str = "html.parser"
REGEX_DOCTYPE: Pattern = re.compile(r"doctype\s+", re.I)
ATTRIBUTE_UP_VERSION: str = "data-userscript-proxy-version"
INFO_COMMENT_PREFIX: str = f"""
[{WELCOME_MESSAGE}]
"""

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

def indexOfDTD(soup: BeautifulSoup) -> Optional[int]:
    index: int = 0
    for item in soup.contents:
        if isinstance(item, Doctype):
            return index
        index += 1
    return None

bulletList: Callable[[Iterable[str]], str] = partial(itemList, LIST_ITEM_PREFIX)

def inferEncoding(response: http.HTTPResponse) -> Optional[str]:
    httpHeaderValue = response.headers.get(CONTENT_TYPE, "").lower()
    match = REGEX_CHARSET.search(httpHeaderValue)
    return match.group(1) if match else None

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
        logInfo(bulletList(map(
            lambda s: f"{first(s).name} ({second(s)})",
            loadedUserscripts
        )))
        logInfo("")
        self.userscripts = list(map(first, loadedUserscripts))


    def response(self, flow: http.HTTPFlow):
        response = flow.response
        if CONTENT_TYPE in response.headers:
            if any(map(lambda t: t in response.headers[CONTENT_TYPE], RELEVANT_CONTENT_TYPES)):
                # Response is a web page; proceed.
                insertedScripts: List[str] = []
                soup = BeautifulSoup(
                    response.content,
                    HTML_PARSER,
                    from_encoding=inferEncoding(response)
                )
                isApplicable: Callable[[Userscript], bool] = userscript.applicableChecker(flow.request.url)
                for script in self.userscripts:
                    if isApplicable(script):
                        logInfo(f"Injecting {script.name} into {flow.request.url} ...")
                        insertedScripts.append(script.name + ("" if script.version is None else " " + stringifyVersion(script.version)))
                        tag = soup.new_tag("script")
                        tag[ATTRIBUTE_UP_VERSION] = VERSION
                        scriptContent: str = (
                            "\n" +
                            (userscript.withNoframes(script.content) if script.noframes else script.content) +
                            "\n"
                        )
                        try:
                            if script.runAt == document_end:
                                tag.string = scriptContent
                                fromOptional(soup.body, soup).append(tag)
                            else:
                                tag.string = scriptContent if script.runAt == document_start else userscript.wrapInEventListener("load", scriptContent)
                                if soup.head is not None:
                                    soup.head.append(tag)
                                elif soup.title is not None:
                                    soup.title.insert_after(tag)
                                elif soup.find() is not None:
                                    soup.find().insert_before(tag) # before first element
                                else:
                                    soup.append(tag)
                        except Exception as e:
                            logError("Injection failed due to the following error:")
                            logError(str(e))
                # Insert information comment:
                index_DTD: Optional[int] = indexOfDTD(soup)
                soup.insert(0 if index_DTD is None else 1+index_DTD, Comment(
                    INFO_COMMENT_PREFIX + (
                        "No matching userscripts for this URL." if insertedScripts == []
                        else "These scripts were inserted:\n" + bulletList(insertedScripts)
                    ) + "\n"
                ))
                # Prevent BS/html.parser from emitting `<!DOCTYPE doctype html>` or similar if "DOCTYPE" is not all uppercase in source HTML:
                if index_DTD is not None and REGEX_DOCTYPE.match(soup.contents[index_DTD]):
                    # There is a DTD and it is invalid, so replace it.
                    soup.contents[index_DTD] = Doctype(re.sub(REGEX_DOCTYPE, "", soup.contents[index_DTD]))
                # Serialize and encode:
                response.content = str(soup).encode(
                    fromOptional(soup.original_encoding, CHARSET_DEFAULT),
                    "replace"
                )


def start():
    return UserscriptInjector()
