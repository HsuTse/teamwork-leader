#!/usr/bin/env python3
"""
tools/patch-plist-python3.py — Patch launchd plist for GHA measurement environment.

Two problems solved by this script:

1. Python version: GHA macOS 14 system python3 is Python 3.9. daemon.py uses
   list[str]|None union syntax (PEP 604, Python 3.10+). launchd's restricted PATH
   (/usr/bin:/bin:/usr/sbin:/sbin) resolves /usr/bin/env python3 to the system Python,
   crashing at import time. Fix: replace /usr/bin/env+python3 in ProgramArguments with
   the absolute GHA python3 path.

2. claude stub visibility: The stub claude binary (tools/claude-stub.sh) is installed
   in $HOME/.local/bin and added to the shell PATH via $GITHUB_PATH. But launchd
   daemons do not inherit the shell PATH. Fix: inject a PATH entry into the plist's
   EnvironmentVariables that includes the stub directory ahead of the default PATH.

Usage:
    python3 tools/patch-plist-python3.py <plist_path> <python3_path> <stub_dir>

    plist_path   — absolute path to the installed plist file
    python3_path — absolute path of the GHA-installed python3 (from `which python3`)
    stub_dir     — directory containing the stub claude binary (e.g. $HOME/.local/bin)

Exit code 0: plist patched successfully.
Exit code 1: plist not found or ProgramArguments in unexpected format.

Note (v0.1.11): This script supports the GHA install-syntax verification context
only — it is NOT involved in measurement. Per v0.1.11 Charter §AC-3 reframe
(CCBL-Stage3-v0.1.11-AC3-LOCAL-REFRAME), measurement runs on the user's local
macOS deployment host where launchd's PATH inheritance is not a problem
(user-installed python3 >=3.10 is on the standard PATH).
"""

import plistlib
import sys


def main() -> None:
    if len(sys.argv) != 4:
        print(
            "Usage: patch-plist-python3.py <plist_path> <python3_path> <stub_dir>",
            file=sys.stderr,
        )
        sys.exit(1)

    plist_path = sys.argv[1]
    py3_path = sys.argv[2]
    stub_dir = sys.argv[3]

    try:
        with open(plist_path, "rb") as f:
            plist = plistlib.load(f)
    except FileNotFoundError:
        print(f"ERROR: plist not found: {plist_path}", file=sys.stderr)
        sys.exit(1)

    # Fix 1: Replace /usr/bin/env+python3 with absolute python3 path.
    # Expected ProgramArguments from template:
    #   ["/usr/bin/env", "python3", "<daemon.py>", "--watch", "<dir>"]
    args = plist.get("ProgramArguments", [])
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

    # Fix 2: Inject PATH into EnvironmentVariables so the stub claude is findable.
    # Default launchd PATH is /usr/bin:/bin:/usr/sbin:/sbin — stub_dir is not in it.
    env_vars = plist.get("EnvironmentVariables", {})
    default_path = "/usr/bin:/bin:/usr/sbin:/sbin"
    injected_path = f"{stub_dir}:{default_path}"
    env_vars["PATH"] = injected_path
    plist["EnvironmentVariables"] = env_vars
    print(f"Injected PATH: {injected_path}")

    with open(plist_path, "wb") as f:
        plistlib.dump(plist, f)
    print(f"Plist written: {plist_path}")


if __name__ == "__main__":
    main()
