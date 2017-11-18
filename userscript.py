from typing import Optional, Tuple, List, Pattern
import re
import metadata
import warnings
from string import Template
from utilities import first, second, isSomething, strs, compose2
from metadata import Metadata, TagValue, PREFIX_TAG, Tag, Tag_string, Tag_boolean
from urlmatch import urlmatch
from patterns import isMatchPattern, isIncludePattern, regexFromIncludePattern

class UserscriptError(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)

directive_name: str = "name"
directive_version: str = "version"
directive_run_at: str = "run-at"
directive_match: str = "match"
directive_include: str = "include"
directive_exclude: str = "exclude"
directive_noframes: str = "noframes"

document_end: str = "document-end"
document_start: str = "document-start"
document_idle: str = "document-idle"

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

METADATA_TAGS: List[Tag] = [
    tag_name,
    tag_run_at,
    tag_match,
    tag_noframes,
    tag_include,
    tag_exclude,
    Tag_string(
        name = directive_version,
        unique = True,
        default = "0.0.0",
        required = False,
        predicate = None,
    ),
]


def f(s: str) -> str:
    # Instead of f"bar" which requires Python 3.6.
    # Uses globals() in a possibly confusing or dangerous way; be careful!
    return s.format(**globals())

STRING_WARNING_INVALID_REGEX: Template = Template(f("""{PREFIX_TAG}{directive_include}/{PREFIX_TAG}{directive_exclude} patterns starting and ending with `/` are interpreted as regular expressions, and this pattern is not a valid regex:

    $pattern

The regex engine reported this error:

    $error

"""))


def regexFromIncludePattern_safe(pattern: str) -> Optional[Pattern]:
    try:
        return regexFromIncludePattern(pattern)
    except re.error as error:
        # warnings.warn(STRING_WARNING_INVALID_REGEX.substitute(pattern=pattern, error=error)) # TODO: uncomment when we can handle warnings
        return None

class Userscript:
    def __init__(self, filename: str, content: str) -> None:
        self.filename: str = filename
        self.content: str = content
        self.metadata: Metadata = metadata.validate(METADATA_TAGS, metadata.parse(metadata.extract(content)))
        self.name: str = str(self.valueOf(tag_name))
        self.runAt: str = str(self.valueOf(tag_run_at))
        self.noframes: bool = bool(self.valueOf(tag_noframes))
        self.matchPatterns: List[str] = strs(self.allValuesOf(tag_match))
        self.includePatternRegexes: List[Pattern] = list(filter(
            isSomething,
            map(
                compose2(regexFromIncludePattern_safe, str),
                self.allValuesOf(tag_include)
            )
        ))
        self.excludePatternRegexes: List[Pattern] = list(filter(
            isSomething,
            map(
                compose2(regexFromIncludePattern_safe, str),
                self.allValuesOf(tag_exclude)
            )
        ))

    def __str__(self) -> str:
        return self.name

    def allValuesOf(self, tag: Tag) -> List[TagValue]:
        return [second(pair) for pair in self.metadata if first(pair) == tag.name]

    def valueOf(self, tag: Tag) -> Optional[TagValue]:
        values = self.allValuesOf(tag)
        return None if len(values) == 0 else values[0]

    def isApplicable(self, url: str) -> bool:
        for regex in self.excludePatternRegexes:
            if isSomething(regex.search(url)):
                return False
        for regex in self.includePatternRegexes:
            if isSomething(regex.search(url)):
                return True
        for pattern in self.matchPatterns:
            if urlmatch(pattern, url):
                return True
        return False

    def getName(self) -> str:
        return self.name

    def getContent(self) -> str:
        return self.content

    def getRunAt(self) -> str:
        return self.runAt

    def wrapInEventListener(self, event: str, scriptContent: str) -> str:
        return """window.addEventListener("{e}", function() {{\n{s}\n}});""".format(e=event, s=scriptContent)
