from modules.utilities import flag

# Helpers/utilities:
metavar_file = "FILE"
metavar_dir = "DIR"
metavar_param = "PARAM"
metavar_allow = "ALLOW"

RULES = "rules"

bypass_csp = "bypass-csp"
bypass_csp_nothing = "nothing"
bypass_csp_script = "script"
bypass_csp_everything = "everything"
bypass_csp_default = bypass_csp_nothing
bypass_csp_values = { bypass_csp_nothing, bypass_csp_script, bypass_csp_everything }
bypass_csp_help = f"Bypass host site's Content Security Policy to allow userscripts to run properly. If {metavar_allow} is '{bypass_csp_script}', the CSP is bypassed only for the userscript itself. Use '{bypass_csp_everything}' to allow everything, which may be necessary if the userscript injects CSS, images etc. Note that the latter completely disables any CSP from every host site into which a userscript is injected. Default: '{bypass_csp_default}'."

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
