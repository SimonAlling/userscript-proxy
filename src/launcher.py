#!/usr/bin/env python3

import glob
import os
import shlex
import subprocess
from typing import List

from modules.argparser import getArgparser
import modules.arguments as A
import modules.constants as C
import modules.ignore as ignore
from modules.misc import sanitize
import modules.text as T
from modules.utilities import flag, idem, isSomething, itemList

FILENAME_INJECTOR: str = "injector.py"
MATCH_NO_HOSTS = r"^$"


def printInfo(
    useFiltering: bool,
    useIntercept: bool,
    useTransparent: bool,
    filterRules: List[str],
):
    print()
    print("mitmproxy will be run in " + ("TRANSPARENT" if useTransparent else "REGULAR") + " mode.")
    print()
    if useFiltering:
        print(f"Traffic from hosts matching any of these rules will be {'INTERCEPTED' if useIntercept else 'IGNORED'} by mitmproxy:")
        print()
        print(itemList("    ", filterRules))
        print()
        if useTransparent:
            print(f"Please note that ignore/intercept rules based on hostnames may not work in transparent mode; it may be necessary to use IP addresses instead.")
    else:
        print(f"Since {flag(A.no_default_rules)} was given and {flag(A.rules)} was not, ALL traffic will be intercepted.")
    print()


def checkThatUserscriptsDirectoryExistsIfSpecified(directory: str):
    if directory is not None and not os.path.isdir(directory):
        print(f"Directory `{directory}` does not exist. If you're using Docker, you need to use -v to mount a directory from the host inside the container. Exiting.")
        exit(1)


try:
    workingDirectory = os.getcwd()
    args = getArgparser().parse_args()
    print(T.WELCOME_MESSAGE)
    globPattern = args.rules
    useCustomFiltering = globPattern is not None
    useDefaultRules = not args.no_default_rules
    useTransparent = args.transparent
    useFiltering = useCustomFiltering or useDefaultRules
    useIntercept = args.intercept is True
    userscriptsDirectory = args.userscripts_dir
    checkThatUserscriptsDirectoryExistsIfSpecified(userscriptsDirectory)
    def ruleFilesContent_default():
        if useDefaultRules:
            print(f"Reading default {'intercept' if useIntercept else 'ignore'} rules ...")
            globPatternForDefaultRules = C.DEFAULT_INTERCEPT_RULES if useIntercept else C.DEFAULT_IGNORE_RULES
            filenames: List[str] = [ shlex.quote(unsafeFilename) for unsafeFilename in glob.glob(globPatternForDefaultRules) ]
            acc = ""
            for filename in filenames:
                print("Reading " + filename + " ...")
                acc += open(filename).read()
            return acc
        else:
            return ""
    def ruleFilesContent_custom():
        if useCustomFiltering:
            print(f"Reading custom {'intercept' if useIntercept else 'ignore'} rules ({globPattern}) ...")
            filenames: List[str] = [ shlex.quote(unsafeFilename) for unsafeFilename in glob.glob(globPattern) ]
            acc = ""
            for filename in filenames:
                print("Reading " + filename + " ...")
                acc += open(filename).read()
            os.chdir(workingDirectory)
            return acc
        else:
            return ""
    ruleFilesContent = ruleFilesContent_default() + "\n" + ruleFilesContent_custom()
    filterRules = ignore.rulesIn(ruleFilesContent)
    printInfo(
        useFiltering=useFiltering,
        useIntercept=useIntercept,
        useTransparent=useTransparent,
        filterRules=filterRules,
    )
    maybeNegate = ignore.negate if useIntercept else idem
    regex = maybeNegate(ignore.entireIgnoreRegex(ruleFilesContent)) if useFiltering else MATCH_NO_HOSTS
    script = os.path.join(os.path.dirname(__file__), FILENAME_INJECTOR)
    subprocess.run([
        "mitmdump", "--ignore-hosts", regex,
        "--listen-port", str(args.port),
        "--mode", "transparent" if useTransparent else "regular",
        "--showhost", # use Host header for URL display
        "-s", script,
        "--set", f"""{sanitize(A.inline)}={str(args.inline).lower()}""",
        "--set", f"""{sanitize(A.list_injected)}={str(args.list_injected).lower()}""",
        "--set", f"""{sanitize(A.no_default_userscripts)}={str(args.no_default_userscripts).lower()}""",
        "--set", "" if userscriptsDirectory is None else f"""{sanitize(A.userscripts_dir)}={userscriptsDirectory}""",
        "--set", f"""{sanitize(A.query_param_to_disable)}={args.query_param_to_disable}""",
        # Empty string breaks the argument chain:
        "--rawtcp" if useTransparent else "", # for apps like Facebook Messenger
    ])
except KeyboardInterrupt:
    print("")
    print("Interrupted by user.")
except Exception as e:
    print(e)
    exit(1)
