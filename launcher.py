from typing import List
import glob
import subprocess
from modules.utilities import itemList, flag, idem, isSomething
from modules.constants import DEFAULT_PORT
import modules.ignore as ignore
import modules.text as T
import shlex
from argparse import ArgumentParser
from functools import reduce

FILENAME_INJECTOR: str = "injector.py"
MATCH_NO_HOSTS = r"^$"

argparser = ArgumentParser(description=T.description)
argparser.add_argument(
    flag(T.option_inline),
    action="store_true",
    help=T.help_inline,
)
argparser.add_argument(
    flag(T.option_verbose),
    action="store_true",
    help=T.help_verbose,
)
argparser.add_argument(
    flag(T.option_transparent),
    action="store_true",
    help=T.help_transparent,
)
group = argparser.add_mutually_exclusive_group()
group.add_argument(
    flag(T.option_ignore),
    type=str,
    metavar=T.metavar_file,
    help=T.help_ignore,
)
group.add_argument(
    flag(T.option_intercept),
    type=str,
    metavar=T.metavar_file,
    help=T.help_intercept,
)
argparser.add_argument(
    flag(T.option_port),
    type=int,
    default=DEFAULT_PORT,
    help=T.help_port,
)

def readRuleFile(accumulatedContent: str, filename: str) -> str:
    print("Reading " + filename + " ...")
    try:
        fileContent: str = open(filename).read()
        return accumulatedContent + fileContent
    except Exception as e:
        print("Could not read file `"+filename+"`: " + str(e))
        return accumulatedContent

try:
    args = argparser.parse_args()
    glob_ignore = args.ignore
    glob_intercept = args.intercept
    globPattern = (
        glob_intercept if isSomething(glob_intercept)
        else glob_ignore if isSomething(glob_ignore)
        else None
    )
    useFiltering = globPattern is not None
    regex: str = MATCH_NO_HOSTS
    if useFiltering:
        useIntercept = isSomething(glob_intercept)
        print(f"Reading {'intercept' if useIntercept else 'ignore'} rules ...")
        filenames: List[str] = [ shlex.quote(unsafeFilename) for unsafeFilename in glob.glob(globPattern) ]
        ruleFilesContent: str = reduce(readRuleFile, filenames, "")
        maybeNegate = ignore.negate if useIntercept else idem
        regex = maybeNegate(ignore.entireIgnoreRegex(ruleFilesContent))
        print(f"Traffic from hosts matching any of these rules will be {'INTERCEPTED' if useIntercept else 'IGNORED'} by mitmproxy:")
        print()
        print(itemList("    ", ignore.rulesIn(ruleFilesContent)))
        print()
    useTransparent = args.transparent
    print("mitmproxy will be run in " + ("TRANSPARENT" if useTransparent else "REGULAR") + " mode.")
    print()
    if not useFiltering:
        print(f"Since neither {flag(T.option_ignore)} nor {flag(T.option_intercept)} was given, ALL traffic will be intercepted.")
    if useFiltering and useTransparent:
        print(f"Please note that ignore/intercept rules based on hostnames may not work in transparent mode; it may be necessary to use IP addresses instead.")
    print()
    subprocess.run([
        "mitmdump", "--ignore-hosts", regex,
        "--listen-port", str(args.port),
        "--mode", "transparent" if useTransparent else "regular",
        "--showhost", # use Host header for URL display
        "-s", FILENAME_INJECTOR,
        "--set", f"""{T.option_inline}={str(args.inline).lower()}""",
        "--set", f"""{T.option_verbose}={str(args.verbose).lower()}""",
        # Empty string breaks the argument chain:
        "--rawtcp" if useTransparent else "", # for apps like Facebook Messenger
    ])
except KeyboardInterrupt:
    print("")
    print("Interrupted by user.")
