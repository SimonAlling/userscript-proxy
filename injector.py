from typing import Optional, Iterable, List, Callable, Pattern, Match
import glob, os, re
from bs4 import BeautifulSoup, Comment, Doctype, Tag
from mitmproxy import ctx, http
from functools import partial
import shlex
import warnings
from modules.metadata import MetadataError
import modules.userscript as userscript
import modules.text as T
from modules.userscript import Userscript, UserscriptError, document_end, document_start, document_idle
from modules.utilities import idem, first, second, itemList, fromOptional, stripIndendation

def stringifyVersion(version: str) -> str:
    return VERSION_PREFIX + version

VERSION: str = "0.6.0"
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

inline = "inline"
verbose = "verbose"

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

def insertEarlyIn(soup: BeautifulSoup, tag: Tag):
    if soup.body is not None and soup.body.find() is not None:
        soup.body.find().insert_before(tag)
    elif soup.title is not None:
        soup.title.insert_after(tag)
    elif soup.find() is not None:
        soup.find().insert_after(tag) # after first element
    else:
        soup.append(tag)

def insertLateIn(soup: BeautifulSoup, tag: Tag):
    fromOptional(soup.body, soup).append(tag)

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
            logInfo("Looking for userscripts ("+PATTERN_USERSCRIPT+") in directory `"+directory+"` ...")
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
            os.chdir("..") # so mitmproxy does not unload the script

        logInfo("")
        logInfo(str(len(loadedUserscripts)) + " userscript(s) loaded:")
        logInfo(bulletList(map(
            lambda s: f"{first(s).name} ({second(s)})",
            loadedUserscripts
        )))
        logInfo("")
        self.userscripts = list(map(first, loadedUserscripts))


    def load(self, loader):
        loader.add_option(inline, bool, False, T.help_inline)
        loader.add_option(verbose, bool, False, T.help_verbose)


    def configure(self, updates):
        if inline in updates and ctx.options.inline:
            logWarning(f"""Only inline injection will be used due to {T.flag_inline} flag.""")


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
                        useInline = ctx.options.inline or script.downloadURL is None
                        logInfo(f"""Injecting {script.name} into {flow.request.url} ({"inline" if useInline else "linked"}) ...""")
                        insertedScripts.append(script.name + ("" if script.version is None else " " + stringifyVersion(script.version)))
                        tag = soup.new_tag("script")
                        tag[ATTRIBUTE_UP_VERSION] = VERSION
                        withLoadListenerIfRunAtIdle = userscript.withEventListener("load") if script.runAt == document_idle else idem
                        withNoframesIfNoframes = userscript.withNoframes if script.noframes else idem
                        try:
                            if useInline:
                                tag.string = withNoframesIfNoframes(withLoadListenerIfRunAtIdle(script.content))
                                if script.runAt == document_end:
                                    insertLateIn(soup, tag)
                                else:
                                    insertEarlyIn(soup, tag)
                            else:
                                s = "s" # JS variable name
                                src = userscript.withVersionSuffix(script.downloadURL, script.version)
                                JS_insertScriptTag = f"""document.head.appendChild({s});"""
                                JS_insertionCode = (stripIndendation(f"""
                                    const {s} = document.createElement("script");
                                    {s}.setAttribute("{ATTRIBUTE_UP_VERSION}", "{VERSION}");
                                    {s}.src = "{src}";
                                    {withLoadListenerIfRunAtIdle(JS_insertScriptTag)}
                                """))
                                if script.runAt == document_idle or script.noframes:
                                    tag.string = withNoframesIfNoframes(JS_insertionCode)
                                else:
                                    tag["src"] = src
                                # Tag prepared. Insert it:
                                if script.runAt == document_end:
                                    insertLateIn(soup, tag)
                                else:
                                    insertEarlyIn(soup, tag)
                        except Exception as e:
                            logError("Injection failed due to the following error:")
                            logError(str(e))
                index_DTD: Optional[int] = indexOfDTD(soup)
                # Insert information comment:
                if ctx.options.verbose:
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


addons = [ UserscriptInjector() ]
