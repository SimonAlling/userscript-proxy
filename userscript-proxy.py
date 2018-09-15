from typing import List
import subprocess
from modules.utilities import itemList, flag
import modules.ignore as ignore
import modules.text as T
from argparse import ArgumentParser

FILENAME_INJECTOR: str = "injector.py"
FILENAME_IGNORE: str = "ignore.txt"

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

try:
    args = argparser.parse_args()
    print("Reading ignore rules ...")
    ignoreFileContent: str = open(FILENAME_IGNORE).read()
    rules: List[str] = ignore.rulesIn(ignoreFileContent)
    print("Traffic from hosts matching any of these rules will be ignored by mitmproxy:")
    print()
    print(itemList("    ", rules))
    print()
    regex: str = ignore.entireIgnoreRegex(ignoreFileContent)
    subprocess.run([
        "mitmdump", "--ignore-hosts", regex,
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
except PermissionError:
    print("Could not read file `"+FILENAME_IGNORE+"`: Permission denied.")
