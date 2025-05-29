import re
from string import Template
from typing import Callable, List, NamedTuple, Optional, Pattern
import warnings

from urlmatch import urlmatch

import modules.inline as inline
import modules.metadata as metadata
from modules.metadata import Metadata, Tag, Tag_boolean, Tag_string
from modules.patterns import isIncludePattern, isMatchPattern, regexFromIncludePattern
from modules.utilities import compose2, stripIndentation, strs

class UserscriptError(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)

REGEX_URL: Pattern = re.compile(r"^https?://")

directive_name     : str = "name"
directive_version  : str = "version"
directive_run_at   : str = "run-at"
directive_match    : str = "match"
directive_include  : str = "include"
directive_exclude  : str = "exclude"
directive_noframes : str = "noframes"
directive_downloadURL : str = "downloadURL"

document_end   : str = "document-end"
document_start : str = "document-start"
document_idle  : str = "document-idle"

tag_name: Tag_string = Tag_string(
    name = directive_name,
    unique = True,
    default = None,
    required = True,
    predicate = lambda val: val != "",
)
tag_run_at: Tag_string = Tag_string(
    name = directive_run_at,
    unique = True,
    default = document_end,
    required = False,
    predicate = lambda val: val in [ document_end, document_start, document_idle ],
)
tag_match: Tag_string = Tag_string(
    name = directive_match,
    unique = False,
    default = None,
    required = False,
    predicate = isMatchPattern,
)
tag_include: Tag_string = Tag_string(
    name = directive_include,
    unique = False,
    default = None,
    required = False,
    predicate = isIncludePattern,
)
tag_exclude: Tag_string = Tag_string(
    name = directive_exclude,
    unique = False,
    default = None,
    required = False,
    predicate = isIncludePattern,
)
tag_noframes: Tag_boolean = Tag_boolean(
    name = directive_noframes,
    unique = True,
    default = False,
    required = False,
    predicate = None,
)
tag_version: Tag_string = Tag_string(
    name = directive_version,
    unique = True,
    default = None,
    required = False,
    predicate = None,
)
tag_downloadURL: Tag_string = Tag_string(
    name = directive_downloadURL,
    unique = True,
    default = None,
    required = False,
    predicate = lambda val: REGEX_URL.match(val) is not None,
)

METADATA_TAGS: List[Tag] = [
    tag_name,
    tag_run_at,
    tag_match,
    tag_noframes,
    tag_include,
    tag_exclude,
    tag_version,
    tag_downloadURL,
]

validateMetadata: Callable[[Metadata], Metadata] = metadata.validator(METADATA_TAGS)


STRING_WARNING_INVALID_REGEX: Template = Template(f"""{metadata.tag(directive_include)}/{metadata.tag(directive_exclude)} patterns starting and ending with `/` are interpreted as regular expressions, and this pattern is not a valid regex:

    $pattern

The regex engine reported this error:

    $error

""")


class Userscript(NamedTuple):
    name: str
    version: Optional[str]
    content: str
    runAt: str
    noframes: bool
    matchPatterns: List[str]
    includePatternRegexes: List[Pattern]
    excludePatternRegexes: List[Pattern]
    downloadURL: Optional[str]
    unsafeSequences: List[str] # in <script> tag

    def __str__(self) -> str:
        return self.name


def create(content: str) -> Userscript:
    validMetadata: Metadata = validateMetadata(metadata.parse(metadata.extract(content)))
    valueOf = metadata.valueGetter_one(validMetadata)
    allValuesOf = metadata.valueGetter_all(validMetadata)
    includePatternRegexes: List[Pattern] = list(filter(
        lambda x: x is not None,
        map(
            compose2(regexFromIncludePattern_safe, str),
            allValuesOf(tag_include)
        )
    ))
    excludePatternRegexes: List[Pattern] = list(filter(
        lambda x: x is not None,
        map(
            compose2(regexFromIncludePattern_safe, str),
            allValuesOf(tag_exclude)
        )
    ))
    return Userscript(
        name = str(valueOf(tag_name)),
        version = None if valueOf(tag_version) is None else str(valueOf(tag_version)),
        content = content,
        runAt = str(valueOf(tag_run_at)),
        noframes = bool(valueOf(tag_noframes)),
        matchPatterns = strs(allValuesOf(tag_match)),
        includePatternRegexes = includePatternRegexes,
        excludePatternRegexes = excludePatternRegexes,
        downloadURL = None if valueOf(tag_downloadURL) is None else str(valueOf(tag_downloadURL)),
        unsafeSequences = inline.unsafeSequencesIn(content),
    )


def applicableChecker(url: str) -> Callable[[Userscript], bool]:
    def isApplicable(userscript: Userscript) -> bool:
        for regex in userscript.excludePatternRegexes:
            if regex.search(url) is not None:
                return False
        for regex in userscript.includePatternRegexes:
            if regex.search(url) is not None:
                return True
        for pattern in userscript.matchPatterns:
            if urlmatch(pattern, url):
                return True
        return False
    return isApplicable


def withEventListener(event: str) -> Callable[[str], str]:
    return lambda scriptContent: f"""window.addEventListener("{event}", function() {{\n{scriptContent}\n}});"""


def withNoframes(scriptContent: str) -> str:
    return stripIndentation(f"""
        if (window.top === window) {{ // {metadata.tag(directive_noframes)}
        {scriptContent}
        }}
    """)


def withVersionSuffix(url: str, version: Optional[str]) -> str:
    return url + ("" if version is None else "?v=" + version)


def regexFromIncludePattern_safe(pattern: str) -> Optional[Pattern]:
    try:
        return regexFromIncludePattern(pattern)
    except re.error as error:
        # warnings.warn(STRING_WARNING_INVALID_REGEX.substitute(pattern=pattern, error=error)) # TODO: uncomment when we can handle warnings
        return None
