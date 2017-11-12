import re
import metadata
import warnings
from string import Template
from utilities import first, second, isSomething
from metadata import tag_name, tag_type, tag_unique, tag_default, tag_required, tag_predicate, PREFIX_TAG
from urlmatch import urlmatch
from patterns import isMatchPattern, isIncludePattern, regexFromIncludePattern

class UserscriptError(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)

directive_name = "name"
directive_version = "version"
directive_run_at = "run-at"
directive_match = "match"
directive_include = "include"
directive_exclude = "exclude"
directive_noframes = "noframes"

document_end = "document-end"
document_start = "document-start"
document_idle = "document-idle"

METADATA_TAGS = [
    {
        tag_name: directive_name,
        tag_type: str,
        tag_unique: True,
        tag_default: None,
        tag_required: True,
        tag_predicate: lambda val: val != "",
    },
    {
        tag_name: directive_version,
        tag_type: str,
        tag_unique: True,
        tag_default: "0.0.0",
        tag_required: False,
        tag_predicate: None,
    },
    {
        tag_name: directive_run_at,
        tag_type: str,
        tag_unique: True,
        tag_default: document_end,
        tag_required: False,
        tag_predicate: lambda val: val in [ document_end, document_start, document_idle ],
    },
    {
        tag_name: directive_match,
        tag_type: str,
        tag_unique: False,
        tag_default: None,
        tag_required: False,
        tag_predicate: isMatchPattern,
    },
    {
        tag_name: directive_include,
        tag_type: str,
        tag_unique: False,
        tag_default: None,
        tag_required: False,
        tag_predicate: isIncludePattern,
    },
    {
        tag_name: directive_exclude,
        tag_type: str,
        tag_unique: False,
        tag_default: None,
        tag_required: False,
        tag_predicate: isIncludePattern,
    },
    {
        tag_name: directive_noframes,
        tag_type: bool,
        tag_unique: True,
        tag_default: False,
        tag_required: False,
        tag_predicate: None,
    },
]

Metadata = metadata.Metadata(METADATA_TAGS)


def f(s):
    # Instead of f"bar" which requires Python 3.6.
    # Uses globals() in a possibly confusing or dangerous way; be careful!
    return s.format(**globals())

STRING_WARNING_INVALID_REGEX = Template(f("""{PREFIX_TAG}{directive_include}/{PREFIX_TAG}{directive_exclude} patterns starting and ending with `/` are interpreted as regular expressions, and this pattern is not a valid regex:

    $pattern

The regex engine reported this error:

    $error

"""))


def regexFromIncludePattern_safe(pattern):
    try:
        return regexFromIncludePattern(pattern)
    except re.error as error:
        # warnings.warn(STRING_WARNING_INVALID_REGEX.substitute(pattern=pattern, error=error)) # TODO: uncomment when we can handle warnings
        return None

class Userscript:
    def __init__(self, filename: str, content: str):
        self.filename = filename
        self.content = content
        self.metadata = Metadata.validate(Metadata.parse(Metadata.extract(content)))
        self.name = self.valueOf(directive_name)
        self.runAt = self.valueOf(directive_run_at)
        self.noframes = self.valueOf(directive_noframes)
        self.matchPatterns = self.allValuesFor(directive_match)
        self.includePatternRegexes = list(filter(
            isSomething,
            list(map(
                regexFromIncludePattern_safe,
                self.allValuesFor(directive_include)
            ))
        ))
        self.excludePatternRegexes = list(filter(
            isSomething,
            list(map(
                regexFromIncludePattern_safe,
                self.allValuesFor(directive_exclude)
            ))
        ))

    def __str__(self):
        return "%s; matches: %s" % (self.name, self.matches)

    def allValuesFor(self, directive):
        return [second(pair) for pair in self.metadata if first(pair) == directive]

    def valueOf(self, directive):
        return self.allValuesFor(directive)[0]

    def isApplicable(self, url):
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

    def getName(self):
        return self.name

    def getContent(self):
        return self.content

    def getRunAt(self):
        return self.runAt

    def wrapInEventListener(event, scriptContent):
        return """window.addEventListener("{e}", function() {{\n{s}\n}});""".format(e=event, s=scriptContent)
