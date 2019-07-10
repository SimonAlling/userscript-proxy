from modules.constants import DEFAULT_PORT, APP_NAME, VERSION, VERSION_PREFIX, DEFAULT_QUERY_PARAM_TO_DISABLE

metavar_file = "FILE"
metavar_dir = "DIR"
metavar_param = "PARAM"
matching = f"matching any of the rules specified in {metavar_file} (file name or glob pattern)"

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

option_recursive_short = "r"
option_recursive = "recursive"
help_recursive = f"""Recurse into directories when looking for userscripts"""

option_transparent_short = "t"
option_transparent = "transparent"
help_transparent = "Transparent mode"

option_userscripts_short = "u"
option_userscripts = "userscripts"
help_userscripts = f"Load userscripts from directory {metavar_dir}"

option_list_injected_short = "l"
option_list_injected = "list-injected"
help_list_injected = "Insert an HTML comment with a list of injected userscripts"

def stringifyVersion(version: str) -> str:
    return VERSION_PREFIX + version

INFO_MESSAGE: str = APP_NAME + " " + stringifyVersion(VERSION)
