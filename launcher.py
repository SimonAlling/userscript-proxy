from typing import List
import glob
import subprocess
from modules.utilities import itemList, flag
from modules.constants import DEFAULT_PORT
import modules.ignore as ignore
import modules.text as T
import shlex
from argparse import ArgumentParser
from functools import reduce

FILENAME_INJECTOR: str = "injector.py"
FILENAME_IGNORE_PREFIX: str = "ignore"
FILENAME_IGNORE_SUFFIX: str = ".txt"

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
argparser.add_argument(
    flag(T.option_port),
    type=int,
    default=DEFAULT_PORT,
    help=T.help_port,
)

try:
    args = argparser.parse_args()
    print("Reading ignore rules ...")
    PATTERN_IGNORE: str = FILENAME_IGNORE_PREFIX + "*" + FILENAME_IGNORE_SUFFIX
    filenames: List[str] = [ shlex.quote(unsafe_filename) for unsafe_filename in glob.glob(PATTERN_IGNORE) ]
    def readIgnoreFile(accumulatedContent: str, filename: str) -> str:
        print("Loading " + filename + " ...")
        try:
            ignoreFileContent: str = open(filename).read()
            return accumulatedContent + ignoreFileContent
        except Exception as e:
            print("Could not read file `"+filename+"`: " + str(e))
            return accumulatedContent
    ignoreFilesContent: str = reduce(readIgnoreFile, filenames, "")
    rules: List[str] = ignore.rulesIn(ignoreFilesContent)
    regex: str = ignore.entireIgnoreRegex(ignoreFilesContent)
    print("Traffic from hosts matching any of these rules will be ignored by mitmproxy:")
    print()
    print(itemList("    ", rules))
    print()
    print("mitmproxy will be run in " + ("transparent" if args.transparent else "regular") + " mode")
    print()
    subprocess.run([
        "mitmdump", "--ignore-hosts", regex,
        "--listen-port", str(args.port),
        "--mode", "transparent" if args.transparent else "regular",
        "--showhost", # use Host header for URL display
        "-s", FILENAME_INJECTOR,
        "--set", f"""{T.option_inline}={str(args.inline).lower()}""",
        "--set", f"""{T.option_verbose}={str(args.verbose).lower()}""",
        # Empty string breaks the argument chain:
        "--rawtcp" if args.transparent else "", # for apps like Facebook Messenger
    ])
except KeyboardInterrupt:
    print("")
    print("Interrupted by user.")
