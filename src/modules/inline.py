import re
from typing import Pattern

# https://www.w3.org/TR/html/semantics-scripting.html#script-content-restrictions

DANGEROUS_SEQUENCES: list[str] = [
    r"<!--",
    r"<script",
    r"</script",
]

REGEX: Pattern = re.compile(
    "|".join(DANGEROUS_SEQUENCES),
    re.IGNORECASE, # to match e.g. <SCRIPT as well
)

def unsafeSequencesIn(source: str) -> list[str]:
    return re.findall(REGEX, source)
