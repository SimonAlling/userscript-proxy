# Due to its mitmproxy dependency, this module can only be imported by files run
# "in" mitm[dump|proxy], e.g. not in the launcher script.

import re
from typing import Callable, Optional, Pattern
from mitmproxy import http
from modules.utilities import equals

CONTENT_TYPE: str = "Content-Type"
REGEX_CHARSET: Pattern = re.compile(r"charset=([^;\s]+)")

def inferEncoding(response: http.HTTPResponse) -> Optional[str]:
    httpHeaderValue = response.headers.get(CONTENT_TYPE, "").lower()
    match = REGEX_CHARSET.search(httpHeaderValue)
    return match.group(1) if match else None

def requestContainsQueryParam(param: str, request: http.HTTPRequest) -> bool:
    return any(map(equals(param), request.query))
