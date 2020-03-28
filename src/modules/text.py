from modules.constants import DEFAULT_PORT, APP_NAME, VERSION, VERSION_PREFIX, DEFAULT_QUERY_PARAM_TO_DISABLE, DEFAULT_RULES_DIR, DEFAULT_USERSCRIPTS_DIR
from modules.utilities import flag

metavar_file = "FILE"
metavar_dir = "DIR"
metavar_param = "PARAM"
RULES_DIR = "rules-dir"
matching = f"matching any of the rules specified in {metavar_file} (file name or glob pattern, relative to {flag(RULES_DIR)})"

description = "Inject userscripts using mitmproxy."

option_ignore = "ignore"
help_ignore = "Intercept all traffic except from hosts " + matching

option_intercept = "intercept"
help_intercept = "Intercept only traffic from hosts " + matching

option_inline_short = "i"
option_inline = "inline"
help_inline = "Always insert userscripts inline, never linked"

option_port_short = "p"
option_port = "port"
help_port = f"""mitmproxy port (default: {DEFAULT_PORT})"""

option_query_param_to_disable_short = "q"
option_query_param_to_disable = "query-param-to-disable"
help_query_param_to_disable = f"""Disable userscripts when the request URL contains a PARAM query parameter, for example "foo" to disable userscripts for http://example.com?foo (default: {DEFAULT_QUERY_PARAM_TO_DISABLE})"""

option_transparent_short = "t"
option_transparent = "transparent"
help_transparent = "Transparent mode"

option_rules_dir_short = "r"
option_rules_dir = RULES_DIR
help_rules_dir = f"Load ignore/intercept rules from directory {metavar_dir} (default: {DEFAULT_RULES_DIR})"

option_userscripts_dir_short = "u"
option_userscripts_dir = "userscripts-dir"
help_userscripts_dir = f"Load userscripts from directory {metavar_dir} (default: {DEFAULT_USERSCRIPTS_DIR})"

option_list_injected_short = "l"
option_list_injected = "list-injected"
help_list_injected = "Insert an HTML comment with a list of injected userscripts"

def stringifyVersion(version: str) -> str:
    return VERSION_PREFIX + version

INFO_MESSAGE: str = APP_NAME + " " + stringifyVersion(VERSION)
