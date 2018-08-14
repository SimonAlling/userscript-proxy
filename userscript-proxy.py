from typing import List
import subprocess
from modules.utilities import itemList
import modules.ignore as ignore
import modules.text as T
from argparse import ArgumentParser

FILENAME_INJECTOR: str = "injector.py"
FILENAME_IGNORE: str = "ignore.txt"

argparser = ArgumentParser(description=T.description)
argparser.add_argument(
    T.flag_inline,
    action="store_true",
    help=T.help_inline,
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
    subprocess.run(["mitmdump", "--ignore", regex, "-s", FILENAME_INJECTOR, "--set", f"""inline={str(args.inline).lower()}"""])
except KeyboardInterrupt:
    print("")
    print("Interrupted by user.")
except PermissionError:
    print("Could not read file `"+FILENAME_IGNORE+"`: Permission denied.")
