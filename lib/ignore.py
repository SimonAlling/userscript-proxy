from typing import List
import re
from lib.utilities import compose2, not_, beginsWith
from lib.patterns import isIncludePattern_regex, regexify, withoutSurroundingSlashes

COMMENT_PREFIX: str = "#"
PORT_PREFIX: str = ":"
PIPE: str = "|"

def rulesIn(text: str) -> List[str]:
    return list(filter(
        compose2(not_, beginsWith(COMMENT_PREFIX)),
        filter(lambda s: s != "", text.splitlines())
    ))


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
