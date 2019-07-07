from modules.constants import DEFAULT_PORT, APP_NAME, VERSION, VERSION_PREFIX

metavar_file = "FILE"
metavar_dir = "DIR"
matching = f"matching any of the rules specified in {metavar_file} (file name or glob pattern)"

description = "Inject userscripts using mitmproxy."

option_ignore = "ignore"
help_ignore = "Intercept all traffic except from hosts " + matching

option_intercept = "intercept"
help_intercept = "Intercept only traffic from hosts " + matching

option_inline = "inline"
help_inline = "Always insert userscripts inline, never linked"

option_port = "port"
help_port = f"""mitmproxy port (default: {DEFAULT_PORT})"""

option_transparent = "transparent"
help_transparent = "Transparent mode"

option_userscripts = "userscripts"
help_userscripts = f"Load userscripts from directory {metavar_dir}"

option_verbose = "verbose"
help_verbose = "Insert an HTML comment with a list of injected userscripts"

def stringifyVersion(version: str) -> str:
    return VERSION_PREFIX + version

INFO_MESSAGE: str = APP_NAME + " " + stringifyVersion(VERSION)
