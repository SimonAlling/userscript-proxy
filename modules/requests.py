# Due to its mitmproxy dependency, this module can only be imported by files run
# "in" mitm[dump|proxy], e.g. not in the launcher script.

from typing import Callable
from mitmproxy import http
from modules.utilities import equals

def requestContainsQueryParam(param: str, request: http.HTTPRequest) -> bool:
    return any(map(equals(param), request.query))
