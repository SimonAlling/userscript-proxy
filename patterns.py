import re

REGEX_MATCH_ALL = r"<all_urls>"
REGEX_MATCH_SCHEME = r"\*|https?"
REGEX_MATCH_HOST = r"(\*\.)*[^\/\*]+|\*"
REGEX_MATCH_PATH = r"\/.*"

# Outer parentheses necessary to enclose `|`:
REGEX_MATCH_PATTERN = re.compile(
	r"^(?:" + REGEX_MATCH_ALL + r"|(" + REGEX_MATCH_SCHEME + r"):\/\/(" + REGEX_MATCH_HOST + r")(" + REGEX_MATCH_PATH + r"))$"
)

REGEX_INCLUDE_REGULAR = r"(.+)"
REGEX_INCLUDE_REGEX = r"\/(.+)\/"

# Outer parentheses necessary to enclose `|`:
REGEX_INCLUDE_PATTERN = re.compile(
	r"^(?:"+REGEX_INCLUDE_REGEX+r"|"+REGEX_INCLUDE_REGULAR+r")$"
)


def isMatchPattern(pattern):
	return REGEX_MATCH_PATTERN.match(pattern) != None

def isIncludePattern(pattern):
	return REGEX_INCLUDE_PATTERN.match(pattern) != None

def regexFromIncludePattern(pattern):
	# TODO: should support regex patterns as well
	return re.compile(r"^" + re.escape(pattern).replace(r"\*", ".*") + r"$")
