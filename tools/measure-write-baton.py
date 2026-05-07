#!/usr/bin/env python3
"""
tools/measure-write-baton.py — Write synthetic measurement baton for T-1-c.

Writes a valid 7-field baton.json with gate_state=BATON_WRITTEN.
Prints the file's mtime as a float epoch timestamp to stdout.

Used by .github/workflows/measure-execution.yml for both cold-start and
warm-start measurement loops. The mtime printed is used as T0 (baton-write
start anchor) for latency computation.

Usage:
    python3 tools/measure-write-baton.py <baton_path>
"""

import json
import os
import sys


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: measure-write-baton.py <baton_path>", file=sys.stderr)
        sys.exit(1)

    baton_path = sys.argv[1]

    baton = {
        "session_id": "measurement-run-synthetic-session",
        "prior_pause_commit": "0000000000000000000000000000000000000000",
        "branch": "feat/v0.1.9-measurement",
        "last_action_iso": "2026-05-05T00:00:00Z",
        "progress_md_anchor": "T-1-c measurement run",
        "restore_prompt": "Measurement run synthetic resume prompt.",
        "auto_mode_resumed": False,
        "gate_state": "BATON_WRITTEN",
    }

    with open(baton_path, "w", encoding="utf-8") as f:
        json.dump(baton, f, indent=2)

    # Get mtime immediately after write — this is T0 for latency measurement.
    mtime = os.stat(baton_path).st_mtime
    print(f"{mtime:.6f}")


if __name__ == "__main__":
    main()
