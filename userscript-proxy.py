from typing import List
import subprocess
from lib.utilities import itemList
import lib.ignore as ignore

FILENAME_INJECTOR: str = "injector.py"
FILENAME_IGNORE: str = "ignore.txt"

try:
    print("Reading ignore rules ...")
    ignoreFileContent: str = open(FILENAME_IGNORE).read()
    rules: List[str] = ignore.rulesIn(ignoreFileContent)
    print("Traffic from hosts matching any of these rules will be ignored by mitmproxy:")
    print()
    print(itemList("    ", rules))
    print()
    regex: str = ignore.entireIgnoreRegex(ignoreFileContent)
    subprocess.run(["mitmdump", "--ignore", regex, "-s", FILENAME_INJECTOR])
except KeyboardInterrupt:
    print("")
    print("Interrupted by user.")
except PermissionError:
    print("Could not read file `"+FILENAME_IGNORE+"`: Permission denied.")
except Exception as e:
    print("Could not read file `"+FILENAME_IGNORE+"`: " + str(e))
