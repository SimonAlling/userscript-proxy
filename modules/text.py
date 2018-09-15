from modules.constants import DEFAULT_PORT

description = "Inject userscripts using mitmproxy."
option_inline = "inline"
help_inline = "Always insert userscripts inline, never linked"
option_verbose = "verbose"
help_verbose = "Insert an HTML comment with a list of injected userscripts"
option_transparent = "transparent"
help_transparent = "Transparent mode"
option_port = "port"
help_port = f"""mitmproxy port (default: {DEFAULT_PORT})"""
