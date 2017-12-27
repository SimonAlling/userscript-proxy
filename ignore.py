from typing import List
import re
from utilities import compose2, not_, beginsWith
from patterns import isIncludePattern_regex, regexify, withoutSurroundingSlashes

PREFIX_COMMENT: str = "#"
PIPE: str = "|"

def rulesIn(text: str) -> List[str]:
    return list(filter(
        compose2(not_, beginsWith(PREFIX_COMMENT)),
        filter(lambda s: s != "", text.splitlines())
    ))


def withPortSuffix(regex: str) -> str:
    return regex + r"\:\d+" if re.compile(r":").search(regex) == None else regex


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
