from argparse import ArgumentParser

import modules.arguments as A
import modules.text as T
from modules.utilities import flag, shortFlag

def getArgparser():
    argparser = ArgumentParser(description=T.description)
    eitherIgnoreOrIntercept = argparser.add_mutually_exclusive_group()
    eitherIgnoreOrIntercept.add_argument(
        flag(A.ignore),
        type=str,
        metavar=A.metavar_file,
        help=A.ignore_help,
    )
    eitherIgnoreOrIntercept.add_argument(
        flag(A.intercept),
        type=str,
        metavar=A.metavar_file,
        help=A.intercept_help,
    )
    argparser.add_argument(
        flag(A.no_default_rules),
        action="store_true",
        help=A.no_default_rules_help,
    )
    argparser.add_argument(
        flag(A.no_default_userscripts),
        action="store_true",
        help=A.no_default_userscripts_help,
    )
    argparser.add_argument(
        flag(A.inline), shortFlag(A.inline_short),
        action="store_true",
        help=A.inline_help,
    )
    argparser.add_argument(
        flag(A.list_injected),
        action="store_true",
        help=A.list_injected_help,
    )
    argparser.add_argument(
        flag(A.port), shortFlag(A.port_short),
        type=int,
        default=A.port_default,
        help=A.port_help,
    )
    argparser.add_argument(
        flag(A.query_param_to_disable), shortFlag(A.query_param_to_disable_short),
        type=str,
        metavar=A.metavar_param,
        default=A.query_param_to_disable_default,
        help=A.query_param_to_disable_help,
    )
    argparser.add_argument(
        flag(A.transparent), shortFlag(A.transparent_short),
        action="store_true",
        help=A.transparent_help,
    )
    argparser.add_argument(
        flag(A.userscripts_dir), shortFlag(A.userscripts_dir_short),
        type=str,
        metavar=A.metavar_dir,
        default=A.userscripts_dir_default,
        help=A.userscripts_dir_help,
    )
    return argparser
