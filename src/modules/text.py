from modules.constants import APP_NAME, VERSION, VERSION_PREFIX
from modules.utilities import flag

ROOT_DIR: str = "/usr/share/userscript-proxy/"

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

option_no_default_rules = "no-default-rules"
help_no_default_rules = f"Skip built-in default ignore/intercept rules"

option_no_default_userscripts = "no-default-userscripts"
help_no_default_userscripts = f"""Skip built-in default userscripts"""

option_port_short = "p"
option_port = "port"
option_port_default = 8080
help_port = f"""mitmproxy port (default: {option_port_default})"""

option_query_param_to_disable_short = "q"
option_query_param_to_disable = "query-param-to-disable"
option_query_param_to_disable_default = "nouserscripts"
help_query_param_to_disable = f"""Disable userscripts when the request URL contains a PARAM query parameter, for example "foo" to disable userscripts for http://example.com?foo (default: {option_query_param_to_disable_default})"""

option_transparent_short = "t"
option_transparent = "transparent"
help_transparent = "Transparent mode"

option_rules_dir_short = "r"
option_rules_dir = RULES_DIR
option_rules_dir_default = ROOT_DIR + "rules"
help_rules_dir = f"Load ignore/intercept rules from directory {metavar_dir} (default: {option_rules_dir_default})"

option_userscripts_dir_short = "u"
option_userscripts_dir = "userscripts-dir"
option_userscripts_dir_default = None
help_userscripts_dir = f"Load userscripts from directory {metavar_dir}"

option_list_injected_short = "l"
option_list_injected = "list-injected"
help_list_injected = "Insert an HTML comment with a list of injected userscripts"

def stringifyVersion(version: str) -> str:
    return VERSION_PREFIX + version

INFO_MESSAGE: str = APP_NAME + " " + stringifyVersion(VERSION)
