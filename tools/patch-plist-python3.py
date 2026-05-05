#!/usr/bin/env python3
"""
tools/patch-plist-python3.py — Patch launchd plist to use absolute python3 path.

On GHA macOS 14 runners, launchd uses a restricted PATH (/usr/bin:/bin:/usr/sbin:/sbin)
which resolves python3 to the system Python 3.9. daemon.py uses list[str]|None union
syntax (PEP 604, requires Python 3.10+) causing a TypeError at import time.

This script patches the installed plist file to replace the '/usr/bin/env python3'
invocation with the absolute path of the GHA-installed python3 (3.11+), ensuring
daemon.py runs under the correct interpreter.

Usage:
    python3 tools/patch-plist-python3.py <plist_path> <python3_path>

Exit code 0: plist patched successfully.
Exit code 1: plist not found or ProgramArguments in unexpected format.
"""

import plistlib
import sys


def main() -> None:
    if len(sys.argv) != 3:
        print(
            "Usage: patch-plist-python3.py <plist_path> <python3_path>",
            file=sys.stderr,
        )
        sys.exit(1)

    plist_path = sys.argv[1]
    py3_path = sys.argv[2]

    try:
        with open(plist_path, "rb") as f:
            plist = plistlib.load(f)
    except FileNotFoundError:
        print(f"ERROR: plist not found: {plist_path}", file=sys.stderr)
        sys.exit(1)

    args = plist.get("ProgramArguments", [])

    # Expected pattern from template: ["/usr/bin/env", "python3", "<daemon.py>", ...]
    if args and args[0] == "/usr/bin/env" and len(args) > 1 and args[1] == "python3":
        patched_args = [py3_path] + args[2:]
        plist["ProgramArguments"] = patched_args
        print(f"Patched ProgramArguments: {patched_args}")
    else:
        print(
            f"WARNING: ProgramArguments not in expected '/usr/bin/env python3 ...' "
            f"format; no patch applied. Got: {args}",
            file=sys.stderr,
        )
        sys.exit(1)

    with open(plist_path, "wb") as f:
        plistlib.dump(plist, f)
    print(f"Plist written: {plist_path}")


if __name__ == "__main__":
    main()
