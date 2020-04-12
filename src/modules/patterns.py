import re
from typing import Match, Optional, Pattern

from modules.utilities import first, isSomething

REGEX_MATCH_ALL = r"<all_urls>"
REGEX_MATCH_SCHEME = r"\*|https?"
REGEXGROUP_MATCH_SCHEME = r"scheme"
REGEX_MATCH_HOST = r"(\*\.)*[^\/\*]+|\*"
REGEXGROUP_MATCH_HOST = r"host"
REGEX_MATCH_PATH = r"\/.*"
REGEXGROUP_MATCH_PATH = r"path"
MATCH_PATTERN_ALL_NORMALIZED = "*://*/*"

# Outer parentheses necessary to enclose `|`:
REGEX_MATCH_PATTERN = re.compile(
      r"^(?:" + REGEX_MATCH_ALL + r"|"
    + r"(?P<" + REGEXGROUP_MATCH_SCHEME + r">" + REGEX_MATCH_SCHEME + r"):\/\/"
    + r"(?P<" + REGEXGROUP_MATCH_HOST   + r">" + REGEX_MATCH_HOST   + r")"
    + r"(?P<" + REGEXGROUP_MATCH_PATH   + r">" + REGEX_MATCH_PATH   + r")"
    + r")$"
)

REGEX_INCLUDE_REGULAR = r"^(.+)$"
REGEX_INCLUDE_REGEX = r"^\/(.+)\/$"

REGEX_INCLUDE_PATTERN = re.compile(
    REGEX_INCLUDE_REGEX + "|" + REGEX_INCLUDE_REGULAR
)


def normalizeMatchPattern(pattern: str) -> str:
    return MATCH_PATTERN_ALL_NORMALIZED if pattern == REGEX_MATCH_ALL else pattern


def isMatchPattern(pattern: str) -> bool:
    return isSomething(REGEX_MATCH_PATTERN.match(pattern))


def isIncludePattern(pattern: str) -> bool:
    return isSomething(REGEX_INCLUDE_PATTERN.match(pattern))


def isIncludePattern_regex(pattern: str) -> bool:
    return isSomething(re.compile(REGEX_INCLUDE_REGEX).match(pattern))


def withoutSurroundingSlashes(s: str) -> str:
    return first(re.subn(re.compile(r"^\/|\/$"), "", s))


def regexFromIncludePattern(pattern: str) -> Pattern: # raises re.error
    return (
        re.compile(withoutSurroundingSlashes(pattern), re.IGNORECASE)
        if isIncludePattern_regex(pattern)
        else re.compile(r"^" + regexify(pattern) + r"$", re.IGNORECASE)
    )


def regexify(segment: str) -> str:
    return re.escape(segment).replace(r"\*", ".*")


# Returns None if the pattern is invalid:
def extractGroup(group: str, matchPattern: str) -> Optional[str]:
    try:
        match: Optional[Match] = REGEX_MATCH_PATTERN.search(normalizeMatchPattern(matchPattern))
        return None if match is None else match.group(group)
    except:
        return None


def schemeIn(matchPattern: str) -> Optional[str]:
    return extractGroup(REGEXGROUP_MATCH_SCHEME, matchPattern)


def hostIn(matchPattern: str) -> Optional[str]:
    return extractGroup(REGEXGROUP_MATCH_HOST, matchPattern)


def pathIn(matchPattern: str) -> Optional[str]:
    return extractGroup(REGEXGROUP_MATCH_PATH, matchPattern)
