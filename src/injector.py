from typing import Optional, Iterable, List, Callable, Pattern, Match, Tuple
import glob, os
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
from modules.utilities import first, second, itemList, fromOptional, flag, idem
from modules.constants import VERSION, VERSION_PREFIX, DEFAULT_USERSCRIPTS_DIR
from modules.inject import Options, inject
from modules.misc import sanitize
from modules.requests import CONTENT_TYPE, inferEncoding, requestContainsQueryParam

PATTERN_USERSCRIPT: str = "*.user.js"
RELEVANT_CONTENT_TYPES: List[str] = ["text/html", "application/xhtml+xml"]
CHARSET_DEFAULT: str = "utf-8"
TAB: str = "    "
LIST_ITEM_PREFIX: str = TAB + "• "
HTML_PARSER: str = "lxml"
# lxml handles non-uppercase DOCTYPE correctly; html.parser does not: It emits
# <!DOCTYPE doctype html> if the original source code contained <!doctype html>.
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


# Because ctx.options is not subscriptable and we want to be able to use
# expressions as keys:
def option(key: str):
    return ctx.options.__getattr__(sanitize(key))


def loadUserscripts(directory: str) -> List[Userscript]:
    loadedUserscripts: List[Tuple[Userscript, str]] = []
    workingDirectory = os.getcwd()
    logInfo(f"""Looking recursively for userscripts ({PATTERN_USERSCRIPT}) in directory `{directory}` ...""")
    os.chdir(directory)
    pattern = "**/" + PATTERN_USERSCRIPT
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
    os.chdir(workingDirectory) # so mitmproxy does not unload the script
    logInfo("")
    logInfo(str(len(loadedUserscripts)) + " userscript(s) loaded:")
    logInfo(bulletList(map(
        lambda s: f"{first(s).name} ({second(s)})",
        loadedUserscripts
    )))
    logInfo("")
    return list(map(first, loadedUserscripts))


class UserscriptInjector:
    def __init__(self):
        self.userscripts: List[Userscript] = []


    def load(self, loader):
        loader.add_option(sanitize(T.option_inline), bool, False, T.help_inline)
        loader.add_option(sanitize(T.option_no_default_userscripts), bool, False, T.help_no_default_userscripts)
        loader.add_option(sanitize(T.option_list_injected), bool, False, T.help_list_injected)
        loader.add_option(sanitize(T.option_userscripts_dir), str, T.option_userscripts_dir_default, T.help_userscripts_dir)
        loader.add_option(sanitize(T.option_query_param_to_disable), str, T.option_query_param_to_disable_default, T.help_query_param_to_disable)


    def configure(self, updates):
        useDefaultUserscripts = True
        if sanitize(T.option_no_default_userscripts) in updates and option(T.option_no_default_userscripts):
            logInfo(f"""Built-in default userscripts will be skipped due to {flag(T.option_no_default_userscripts)} flag.""")
            useDefaultUserscripts = False
        if sanitize(T.option_inline) in updates and option(T.option_inline):
            logWarning(f"""Only inline injection will be used due to {flag(T.option_inline)} flag.""")
        if sanitize(T.option_query_param_to_disable) in updates:
            logInfo(f"""Userscripts will not be injected when the request URL contains a `{option(T.option_query_param_to_disable)}` query parameter.""")
        if sanitize(T.option_userscripts_dir) in updates:
            userscripts = loadUserscripts(DEFAULT_USERSCRIPTS_DIR) if useDefaultUserscripts else []
            userscripts.append(loadUserscripts(option(T.option_userscripts_dir)))
            self.userscripts = userscripts


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
                if requestContainsQueryParam(option(T.option_query_param_to_disable), flow.request):
                    logInfo(f"""Not injecting any userscripts into {requestURL} because it contains a `{option(T.option_query_param_to_disable)}` query parameter.""")
                    return
                isApplicable: Callable[[Userscript], bool] = userscript.applicableChecker(requestURL)
                for script in self.userscripts:
                    if isApplicable(script):
                        useInline = option(T.option_inline) or script.downloadURL is None
                        if useInline and len(script.unsafeSequences) > 0:
                            logError(unsafeSequencesMessage(script))
                            continue
                        logInfo(f"""Injecting {script.name}{"" if script.version is None else " " + VERSION_PREFIX + script.version} into {requestURL} ({"inline" if useInline else "linked"}) ...""")
                        result = inject(script, soup, Options(
                            inline = option(T.option_inline),
                        ))
                        if type(result) is BeautifulSoup:
                            soup = result
                            insertedScripts.append(script.name + ("" if script.version is None else " " + T.stringifyVersion(script.version)))
                        else:
                            logError("Injection failed due to the following error:")
                            logError(str(result))

                index_DTD: Optional[int] = indexOfDTD(soup)
                # Insert information comment:
                if option(T.option_list_injected):
                    soup.insert(0 if index_DTD is None else 1+index_DTD, Comment(
                        HTML_INFO_COMMENT_PREFIX + (
                            "No matching userscripts for this URL." if insertedScripts == []
                            else "These scripts were inserted:\n" + bulletList(insertedScripts)
                        ) + "\n"
                    ))
                # Serialize and encode:
                response.content = str(soup).encode(
                    fromOptional(soup.original_encoding, CHARSET_DEFAULT),
                    "replace"
                )


addons = [ UserscriptInjector() ]
