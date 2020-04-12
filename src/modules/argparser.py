from argparse import ArgumentParser
import modules.text as T
from modules.utilities import flag, shortFlag

def getArgparser():
    argparser = ArgumentParser(description=T.description)
    eitherIgnoreOrIntercept = argparser.add_mutually_exclusive_group()
    eitherIgnoreOrIntercept.add_argument(
        flag(T.option_ignore),
        type=str,
        metavar=T.metavar_file,
        help=T.help_ignore,
    )
    eitherIgnoreOrIntercept.add_argument(
        flag(T.option_intercept),
        type=str,
        metavar=T.metavar_file,
        help=T.help_intercept,
    )
    argparser.add_argument(
        flag(T.option_no_default_rules),
        action="store_true",
        help=T.help_no_default_rules,
    )
    argparser.add_argument(
        flag(T.option_no_default_userscripts),
        action="store_true",
        help=T.help_no_default_userscripts,
    )
    argparser.add_argument(
        flag(T.option_inline), shortFlag(T.option_inline_short),
        action="store_true",
        help=T.help_inline,
    )
    argparser.add_argument(
        flag(T.option_list_injected),
        action="store_true",
        help=T.help_list_injected,
    )
    argparser.add_argument(
        flag(T.option_port), shortFlag(T.option_port_short),
        type=int,
        default=T.option_port_default,
        help=T.help_port,
    )
    argparser.add_argument(
        flag(T.option_query_param_to_disable), shortFlag(T.option_query_param_to_disable_short),
        type=str,
        metavar=T.metavar_param,
        default=T.option_query_param_to_disable_default,
        help=T.help_query_param_to_disable,
    )
    argparser.add_argument(
        flag(T.option_transparent), shortFlag(T.option_transparent_short),
        action="store_true",
        help=T.help_transparent,
    )
    argparser.add_argument(
        flag(T.option_userscripts_dir), shortFlag(T.option_userscripts_dir_short),
        type=str,
        metavar=T.metavar_dir,
        default=T.option_userscripts_dir_default,
        help=T.help_userscripts_dir,
    )
    return argparser
