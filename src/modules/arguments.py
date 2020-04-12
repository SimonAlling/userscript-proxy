from modules.utilities import flag

# Helpers/utilities:
metavar_file = "FILE"
metavar_dir = "DIR"
metavar_param = "PARAM"

RULES = "rules"

inline = "inline"
inline_short = "i"
inline_help = "Always insert userscripts inline, never linked"

intercept = "intercept"
intercept_help = f"Invert the meaning of {flag(RULES)} so that traffic from matched hosts is intercepted instead of ignored"

list_injected = "list-injected"
list_injected_short = "l"
list_injected_help = "Insert an HTML comment with a list of injected userscripts"

no_default_rules = "no-default-rules"
no_default_rules_help = f"Skip built-in default ignore/intercept rules"

no_default_userscripts = "no-default-userscripts"
no_default_userscripts_help = f"""Skip built-in default userscripts"""

port = "port"
port_short = "p"
port_default = 8080
port_help = f"""mitmproxy port (default: {port_default})"""

query_param_to_disable = "query-param-to-disable"
query_param_to_disable_short = "q"
query_param_to_disable_default = "nouserscripts"
query_param_to_disable_help = f"""Disable userscripts when the request URL contains a PARAM query parameter, for example "foo" to disable userscripts for http://example.com?foo (default: {query_param_to_disable_default})"""

rules = RULES
rules_short = "r"
rules_help = f"Ignore (or, with {flag(intercept)}, intercept) traffic from hosts matching any of the rules specified in {metavar_file} (file name or glob pattern)"

transparent = "transparent"
transparent_short = "t"
transparent_help = "Transparent mode"

userscripts_dir = "userscripts-dir"
userscripts_dir_short = "u"
userscripts_dir_default = None
userscripts_dir_help = f"Load userscripts from directory {metavar_dir}"
