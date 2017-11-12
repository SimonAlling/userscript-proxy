import re
from utilities import first

REGEX_MATCH_ALL = r"<all_urls>"
REGEX_MATCH_SCHEME = r"\*|https?"
REGEX_MATCH_HOST = r"(\*\.)*[^\/\*]+|\*"
REGEX_MATCH_PATH = r"\/.*"

# Outer parentheses necessary to enclose `|`:
REGEX_MATCH_PATTERN = re.compile(
	r"^(?:" + REGEX_MATCH_ALL + r"|(" + REGEX_MATCH_SCHEME + r"):\/\/(" + REGEX_MATCH_HOST + r")(" + REGEX_MATCH_PATH + r"))$"
)

REGEX_INCLUDE_REGULAR = r"^(.+)$"
REGEX_INCLUDE_REGEX = r"^\/(.+)\/$"

REGEX_INCLUDE_PATTERN = re.compile(
	REGEX_INCLUDE_REGEX + "|" + REGEX_INCLUDE_REGULAR
)


def isMatchPattern(pattern):
	return REGEX_MATCH_PATTERN.match(pattern) != None

def isIncludePattern(pattern):
	return REGEX_INCLUDE_PATTERN.match(pattern) != None

def isIncludePattern_regex(pattern):
	return re.compile(REGEX_INCLUDE_REGEX).match(pattern) != None

def withoutSurroundingSlashes(s):
	return first(re.subn(re.compile(r"^\/|\/$"), "", s))

def regexFromIncludePattern(pattern): # raises re.error
	return (
		re.compile(withoutSurroundingSlashes(pattern), re.IGNORECASE)
        if isIncludePattern_regex(pattern)
		else re.compile(r"^" + re.escape(pattern).replace(r"\*", ".*") + r"$", re.IGNORECASE)
	)
