#!/usr/bin/env python3
"""
hooks/stop.py — Stop hook handler stub.

Purpose: Fired by Claude Code's Stop event when a session ends.
Invokes lib/notifier.py to emit macOS notification and surfaces
last-resume-failure.txt banner if present.

Spec reference: design.md §1 T7, lines 537-551.
Implementation task: T-3-7.

This file is a STUB. Full implementation pending T-3-7.
"""
import sys


def main() -> None:
    print("[STUB] hooks/stop.py — implementation pending T-3-7", file=sys.stderr)
    # Hooks must exit 0 to avoid breaking Claude Code sessions.
    sys.exit(0)


if __name__ == "__main__":
    main()
