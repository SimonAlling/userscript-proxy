from modules.constants import DEFAULT_PORT

metavar_file = "FILE"
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

option_verbose = "verbose"
help_verbose = "Insert an HTML comment with a list of injected userscripts"
