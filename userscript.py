import re
import metadata
from metadata import first, second, tag_name, tag_type, tag_unique, tag_default, tag_required, tag_predicate
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


class Userscript:
    def __init__(self, filename: str, content: str):
        self.filename = filename
        self.content = content
        self.metadata = Metadata.validate(Metadata.parse(Metadata.extract(content)))
        self.name = self.valueOf(directive_name)
        self.runAt = self.valueOf(directive_run_at)
        self.noframes = self.valueOf(directive_noframes)
        self.matchPatterns = self.allValuesFor(directive_match)
        self.includePatternRegexes = map(regexFromIncludePattern, self.allValuesFor(directive_include))
        self.excludePatternRegexes = map(regexFromIncludePattern, self.allValuesFor(directive_exclude))

    def __str__(self):
        return "%s; matches: %s" % (self.name, self.matches)

    def allValuesFor(self, directive):
        return [second(pair) for pair in self.metadata if first(pair) == directive]

    def valueOf(self, directive):
        return self.allValuesFor(directive)[0]

    def isApplicable(self, url):
        for regex in self.excludePatternRegexes:
            if regex.match(url):
                return False
        for regex in self.includePatternRegexes:
            if regex.match(url):
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
        return ("window.addEventListener(\""+event+"\", function() {"
            + "\n"
            + scriptContent
            + "\n"
            + "});")
