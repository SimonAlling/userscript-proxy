# Helpers/utilities:
metavar_file = "FILE"
metavar_dir = "DIR"
metavar_param = "PARAM"
matching = f"matching any of the rules specified in {metavar_file} (file name or glob pattern)"


ignore = "ignore"
ignore_help = "Intercept all traffic except from hosts " + matching

inline = "inline"
inline_short = "i"
inline_help = "Always insert userscripts inline, never linked"

intercept = "intercept"
intercept_help = "Intercept only traffic from hosts " + matching

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

transparent = "transparent"
transparent_short = "t"
transparent_help = "Transparent mode"

userscripts_dir = "userscripts-dir"
userscripts_dir_short = "u"
userscripts_dir_default = None
userscripts_dir_help = f"Load userscripts from directory {metavar_dir}"
