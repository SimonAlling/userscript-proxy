import functools
import glob
import os
import shlex
from typing import Any, Callable, Iterable, Optional

from bs4 import BeautifulSoup, Comment, Doctype
from mitmproxy import ctx, http

import modules.arguments as A
import modules.constants as C
import modules.csp as csp
import modules.inject as inject
import modules.inline as inline
import modules.metadata as metadata
from modules.misc import sanitize
from modules.requests import CONTENT_TYPE, containsQueryParam, inferEncoding
import modules.text as T
import modules.userscript as userscript
from modules.userscript import Userscript
from modules.utilities import first, flag, fromOptional, itemList, second

PATTERN_USERSCRIPT: str = "*.user.js"
RELEVANT_CONTENT_TYPES: list[str] = ["text/html", "application/xhtml+xml"]
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

bulletList: Callable[[Iterable[str]], str] = functools.partial(itemList, LIST_ITEM_PREFIX)

def unsafeSequencesMessage(script: Userscript) -> str:
    sequences = script.unsafeSequences
    return f"""{script.name} cannot be injected because it contains {"these unsafe sequences" if len(sequences) > 1 else "this unsafe sequence"}:

{itemList(TAB, sequences)}

<script> tags cannot contain any of these sequences (case-insensitive):

{itemList(TAB, inline.DANGEROUS_SEQUENCES)}

Possible solutions:
""" + bulletList([
    f"Make sure the userscript does not contain any of the sequences listed above.",
    f"Make the userscript available online and give it a {metadata.tag(userscript.directive_downloadURL)}",
    f"Remove the {flag(A.inline)} flag.",
])


# Because ctx.options is not subscriptable and we want to be able to use
# expressions as keys:
def option(key: str) -> Any:
    return ctx.options.__getattr__(sanitize(key))


def loadUserscripts(directory: str) -> list[Userscript]:
    loadedUserscripts: list[tuple[Userscript, str]] = []
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
            if script.downloadURL is None:
                logWarning(f"""{script.name} will be injected inline because it does not have a {metadata.tag(userscript.directive_downloadURL)}.""")
            loadedUserscripts.append((script, filename))
            if script.downloadURL is None and len(script.unsafeSequences) > 0:
                logError(unsafeSequencesMessage(script))
        except metadata.MetadataError as err:
            logError("Metadata error:")
            logError(str(err))
            continue
    os.chdir(workingDirectory) # so mitmproxy does not unload the script
    logInfo("")
    logInfo(str(len(loadedUserscripts)) + " userscript(s) loaded:")
    logInfo("")
    logInfo(bulletList(map(
        lambda s: f"{first(s).name} ({second(s)})",
        loadedUserscripts
    )))
    logInfo("")
    return list(map(first, loadedUserscripts))


class UserscriptInjector:
    def __init__(self) -> None:
        self.userscripts: list[Userscript] = []


    def load(self, loader: Any) -> None:
        loader.add_option(sanitize(A.inline), bool, False, A.inline_help)
        loader.add_option(sanitize(A.no_default_userscripts), bool, False, A.no_default_userscripts_help)
        loader.add_option(sanitize(A.list_injected), bool, False, A.list_injected_help)
        loader.add_option(sanitize(A.bypass_csp), Optional[str], A.bypass_csp_default, A.bypass_csp_help)
        loader.add_option(sanitize(A.userscripts_dir), Optional[str], A.userscripts_dir_default, A.userscripts_dir_help)
        loader.add_option(sanitize(A.query_param_to_disable), str, A.query_param_to_disable_default, A.query_param_to_disable_help)


    def configure(self, updates: Any) -> None:
        useDefaultUserscripts = True
        if sanitize(A.no_default_userscripts) in updates and option(A.no_default_userscripts):
            logInfo(f"""Built-in default userscripts will be skipped due to {flag(A.no_default_userscripts)} flag.""")
            useDefaultUserscripts = False
        if sanitize(A.inline) in updates and option(A.inline):
            logWarning(f"""Only inline injection will be used due to {flag(A.inline)} flag.""")
        if sanitize(A.query_param_to_disable) in updates:
            logInfo(f"""Userscripts will not be injected when the request URL contains a `{option(A.query_param_to_disable)}` query parameter.""")
        if sanitize(A.userscripts_dir) in updates:
            userscripts = loadUserscripts(C.DEFAULT_USERSCRIPTS_DIR) if useDefaultUserscripts else []
            userscriptsDirectory = option(A.userscripts_dir)
            if userscriptsDirectory is None:
                logWarning(f"No custom userscripts will be loaded, because {flag(A.userscripts_dir)} was not provided.")
            else:
                userscripts.extend(loadUserscripts(userscriptsDirectory))
            self.userscripts = userscripts


    def response(self, flow: http.HTTPFlow) -> None:
        response = flow.response
        if CONTENT_TYPE in response.headers:
            if any(map(lambda t: t in response.headers[CONTENT_TYPE], RELEVANT_CONTENT_TYPES)):
                # Response is a web page; proceed.
                injections: list[csp.Injection] = []
                soup = BeautifulSoup(
                    response.content,
                    HTML_PARSER,
                    from_encoding=inferEncoding(response)
                )
                requestURL = flow.request.pretty_url # should work in transparent mode too, unless the Host header is spoofed
                if containsQueryParam(option(A.query_param_to_disable), flow.request):
                    logInfo(f"""Not injecting any userscripts into {requestURL} because it contains a `{option(A.query_param_to_disable)}` query parameter.""")
                    return
                isApplicable: Callable[[Userscript], bool] = userscript.applicableChecker(requestURL)
                for script in self.userscripts:
                    if isApplicable(script):
                        useInline = option(A.inline) or script.downloadURL is None
                        if useInline and len(script.unsafeSequences) > 0:
                            logError(unsafeSequencesMessage(script))
                            continue
                        logInfo(f"""Injecting {script.name}{"" if script.version is None else " " + C.VERSION_PREFIX + script.version} into {requestURL} ({"inline" if useInline else "linked"}) ...""")
                        shouldUseNonce = useInline and option(A.bypass_csp) == A.bypass_csp_script # If not inline, then URL is used for bypassing; if bypass for nothing or everything, then the nonce would have no effect anyway.
                        nonce = csp.generateNonce() if shouldUseNonce else None
                        result = inject.inject(script, soup, inject.Options(
                            inline = option(A.inline),
                            nonce = nonce
                        ))
                        if type(result) is BeautifulSoup:
                            soup = result
                            injections.append(csp.Injection(
                                userscript = script,
                                nonce = nonce,
                            ))
                        else:
                            logError("Injection failed due to the following error:")
                            logError(str(result))

                handleContentSecurityPolicy(response, injections)
                index_DTD: Optional[int] = indexOfDTD(soup)
                # Insert information comment:
                if option(A.list_injected):
                    namesOfInjectedScripts = [ i.userscript.name + ("" if i.userscript.version is None else " " + T.stringifyVersion(i.userscript.version)) for i in injections ]
                    soup.insert(0 if index_DTD is None else 1+index_DTD, Comment(
                        HTML_INFO_COMMENT_PREFIX + (
                            "No matching userscripts for this URL." if namesOfInjectedScripts == []
                            else "These scripts were inserted:\n" + bulletList(namesOfInjectedScripts)
                        ) + "\n"
                    ))
                # Serialize and encode:
                response.content = str(soup).encode(
                    fromOptional(soup.original_encoding, CHARSET_DEFAULT),
                    "replace"
                )


def handleContentSecurityPolicy(response: http.HTTPFlow.response, injections: list[csp.Injection]) -> None:
    # If there is a CSP header, we may need to modify it for the userscript(s) to work.
    ContentSecurityPolicy = "Content-Security-Policy"
    if ContentSecurityPolicy in response.headers:
        bypassCspValue = option(A.bypass_csp)
        if bypassCspValue == A.bypass_csp_script:
            logInfo(f"Bypassing host site's Content Security Policy for userscripts only (not any resources injected _by_ userscripts, such as stylesheets and images). Try `{flag(A.bypass_csp)} {A.bypass_csp_everything}` if something does not work properly.")
            response.headers[ContentSecurityPolicy] = csp.headerWithScriptsAllowed(response.headers[ContentSecurityPolicy], injections)
        elif bypassCspValue == A.bypass_csp_everything:
            logInfo(f"Bypassing host site's Content Security Policy altogether due to `{flag(A.bypass_csp)} {A.bypass_csp_everything}`.")
            del response.headers[ContentSecurityPolicy]
        else:
            logWarning(f"Host site has a Content Security Policy. Try the {flag(A.bypass_csp)} flag if userscripts don't work properly.")


addons = [ UserscriptInjector() ]
