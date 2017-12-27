import subprocess

FILENAME_INJECTOR: str = "injector.py"

try:
    subprocess.run(["mitmdump", "-s", FILENAME_INJECTOR])
except KeyboardInterrupt:
    print("")
    print("Interrupted by user.")
