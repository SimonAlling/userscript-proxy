from typing import Optional, Iterable, List, Callable, Pattern, Match
import glob, os, re
from bs4 import BeautifulSoup, Comment, Doctype
from mitmproxy import ctx, http
from functools import partial
import shlex
import warnings
from modules.metadata import MetadataError, PREFIX_TAG
import modules.userscript as userscript
import modules.inline as inline
import modules.text as T
from modules.userscript import Userscript, UserscriptError, document_end, document_start, document_idle
from modules.utilities import first, second, itemList, fromOptional, flag
from modules.constants import VERSION, VERSION_PREFIX, APP_NAME, DEFAULT_USERSCRIPTS_DIR
from modules.inject import Options, inject

PATTERN_USERSCRIPT: str = "*.user.js"
CONTENT_TYPE: str = "Content-Type"
RELEVANT_CONTENT_TYPES: List[str] = ["text/html", "application/xhtml+xml"]
CHARSET_DEFAULT: str = "utf-8"
REGEX_CHARSET: Pattern = re.compile(r"charset=([^;\s]+)")
TAB: str = "    "
LIST_ITEM_PREFIX: str = TAB + "• "
HTML_PARSER: str = "lxml"
REGEX_DOCTYPE: Pattern = re.compile(r"doctype\s+", re.I)
HTML_INFO_COMMENT_PREFIX: str = f"""
[{T.INFO_MESSAGE}]
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

def unsafeSequencesMessage(script: Userscript) -> str:
    sequences = script.unsafeSequences
    return f"""{script.name} cannot be injected because it contains {"these unsafe sequences" if len(sequences) > 1 else "this unsafe sequence"}:

{itemList(TAB, sequences)}

<script> tags cannot contain any of these sequences (case-insensitive):

{itemList(TAB, inline.DANGEROUS_SEQUENCES)}

Possible solutions:
""" + bulletList([
    f"Make sure the userscript does not contain any of the sequences listed above.",
    f"Make the userscript available online and give it a {PREFIX_TAG}{userscript.directive_downloadURL}",
    f"Remove the {flag(T.option_inline)} flag.",
])

def inferEncoding(response: http.HTTPResponse) -> Optional[str]:
    httpHeaderValue = response.headers.get(CONTENT_TYPE, "").lower()
    match = REGEX_CHARSET.search(httpHeaderValue)
    return match.group(1) if match else None


def sanitize(optionName: str) -> str:
    return optionName.replace("-", "_")


class UserscriptInjector:
    def __init__(self):
        self.userscripts: List[Userscript] = []


    def load(self, loader):
        loader.add_option(sanitize(T.option_inline), bool, False, T.help_inline)
        loader.add_option(sanitize(T.option_recursive), bool, False, T.help_recursive)
        loader.add_option(sanitize(T.option_list_injected), bool, False, T.help_list_injected)
        loader.add_option(sanitize(T.option_userscripts), str, DEFAULT_USERSCRIPTS_DIR, T.help_userscripts)


    def configure(self, updates):
        if T.option_inline in updates and ctx.options.inline:
            logWarning(f"""Only inline injection will be used due to {flag(T.option_inline)} flag.""")
        if T.option_userscripts in updates:
            self.loadUserscripts()


    def loadUserscripts(self):
        logInfo("Loading userscripts ...")
        loadedUserscripts: List[Tuple[Userscript, str]] = []
        DIRS_USERSCRIPTS = [ ctx.options.userscripts ]
        useRecursive = ctx.options.recursive
        for directory in DIRS_USERSCRIPTS:
            logInfo(f"""Looking{" recursively" if useRecursive else ""} for userscripts ({PATTERN_USERSCRIPT}) in directory `{directory}` ...""")
            if not useRecursive:
                logInfo(f"{TAB}(use {flag(T.option_recursive)} to look recursively)")
            try:
                os.chdir(directory)
            except FileNotFoundError:
                logWarning("Directory `"+directory+"` does not exist.")
                continue
            except PermissionError:
                logError("Permission was denied when trying to read directory `"+DIR_USERSCRIPTS+"`.")
                continue
            pattern = ("**/" if useRecursive else "") + PATTERN_USERSCRIPT
            # recursive=True only affects the meaning of "**".
            # https://docs.python.org/3/library/glob.html#glob.glob
            for unsafe_filename in glob.glob(pattern, recursive=True):
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
                    script = userscript.create(content)
                    loadedUserscripts.append((script, filename))
                    if script.downloadURL is None and len(script.unsafeSequences) > 0:
                        logError(unsafeSequencesMessage(script))
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
        self.userscripts = self.userscripts + list(map(first, loadedUserscripts))


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
                requestURL = flow.request.pretty_url # should work in transparent mode too, unless the Host header is spoofed
                isApplicable: Callable[[Userscript], bool] = userscript.applicableChecker(requestURL)
                for script in self.userscripts:
                    if isApplicable(script):
                        useInline = ctx.options.inline or script.downloadURL is None
                        if useInline and len(script.unsafeSequences) > 0:
                            logError(unsafeSequencesMessage(script))
                            continue
                        logInfo(f"""Injecting {script.name}{"" if script.version is None else " " + VERSION_PREFIX + script.version} into {requestURL} ({"inline" if useInline else "linked"}) ...""")
                        result = inject(script, soup, Options(
                            inline = ctx.options.inline,
                        ))
                        if type(result) is BeautifulSoup:
                            soup = result
                            insertedScripts.append(script.name + ("" if script.version is None else " " + T.stringifyVersion(script.version)))
                        else:
                            logError("Injection failed due to the following error:")
                            logError(str(result))

                index_DTD: Optional[int] = indexOfDTD(soup)
                # Insert information comment:
                if ctx.options.list_injected:
                    soup.insert(0 if index_DTD is None else 1+index_DTD, Comment(
                        HTML_INFO_COMMENT_PREFIX + (
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
