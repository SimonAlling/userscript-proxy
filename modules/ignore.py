from typing import List, Pattern
import re
from modules.patterns import isIncludePattern_regex, regexify, withoutSurroundingSlashes

COMMENT_PREFIX: str = "#"
PORT_PREFIX: str = ":"
PIPE: str = "|"
REGEX_COMMENT: Pattern = re.compile(r"\#.*$")

def rulesIn(text: str) -> List[str]:
    return list(filter(
        lambda s: s != "",
        map(withoutCommentAndTrimmed, text.splitlines())
    ))


def withoutCommentAndTrimmed(line: str) -> str:
    return re.sub(REGEX_COMMENT, "", line).strip()


def withPortSuffix(regex: str) -> str:
    return regex if PORT_PREFIX in regex else regex + r"\:\d+"


def ignoreRegex(ignoreRule: str) -> str:
    return (
        withoutSurroundingSlashes(ignoreRule)
        if isIncludePattern_regex(ignoreRule)
        else r"^(?:.+\.)?" + withPortSuffix(regexify(ignoreRule)) + r"$"
    )


def entireIgnoreRegex(ignoreFileContent: str) -> str:
    return PIPE.join(map(
        ignoreRegex,
        rulesIn(ignoreFileContent)
    ))


# https://stackoverflow.com/a/2637899
def negate(regex: str) -> str:
    return "^(?!(?:" + regex + ")$).*$"
