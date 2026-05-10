#!/usr/bin/env python3
"""
tools/measure-write-baton.py — Write synthetic measurement baton for T-1-c.

Writes a valid 7-field baton.json with gate_state=BATON_WRITTEN.
Prints the file's mtime as a float epoch timestamp to stdout.

Used by .github/workflows/measure-execution.yml for both cold-start and
warm-start measurement loops. The mtime printed is used as T0 (baton-write
start anchor) for latency computation.

Usage:
    python3 tools/measure-write-baton.py <baton_path> [--session-id <uuid>]

--session-id <uuid>
    Real session UUID from a prior claude session.  When provided the baton
    carries that UUID so real claude --resume can locate the session.

    If omitted, the tool tries to discover the most-recently-modified .jsonl
    file under ~/.claude/projects/<project_hash>/ and uses its stem (the
    UUID filename without extension) as the session_id.  Falls back to the
    legacy synthetic literal "measurement-run-synthetic-session" only when no
    .jsonl files are found, which retains backward compatibility with
    environments that pre-exist v0.1.11.
"""

import argparse
import glob
import json
import os
import sys


def _discover_local_session_id() -> str:
    """Return the most-recently-modified session UUID from the Claude projects dir.

    Searches ~/.claude/projects/<any_hash>/*.jsonl under the teamwork-leader
    project directory hash (resolved from CLAUDE_PROJECT_DIR if set, otherwise
    from the script's own parent).  Returns the stem (UUID) of the .jsonl with
    the largest mtime, or the legacy synthetic literal as a fallback.
    """
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not project_dir:
        # Resolve from the script's parent (tools/ → repo root)
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Claude encodes the project path as a hash directory name under ~/.claude/projects/
    # by replacing path separators with "-".  e.g. /Users/X/foo → -Users-X-foo
    encoded = project_dir.replace(os.sep, "-")
    claude_projects_dir = os.path.join(os.path.expanduser("~"), ".claude", "projects", encoded)

    pattern = os.path.join(claude_projects_dir, "*.jsonl")
    candidates = glob.glob(pattern)
    if not candidates:
        # Fallback: legacy synthetic literal (backward compat)
        return "measurement-run-synthetic-session"

    # Most recently modified .jsonl = the session UUID for the latest claude run
    latest = max(candidates, key=os.path.getmtime)
    return os.path.splitext(os.path.basename(latest))[0]


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="measure-write-baton.py",
        description="Write synthetic measurement baton for T-1-c latency measurement.",
    )
    parser.add_argument("baton_path", help="Path to write baton.json")
    parser.add_argument(
        "--session-id",
        metavar="UUID",
        default=None,
        help=(
            "Real session UUID from a prior claude session.  "
            "When omitted, the tool auto-discovers from ~/.claude/projects/<hash>/*.jsonl."
        ),
    )
    return parser.parse_args(argv)


def main() -> None:
    args = _parse_args(sys.argv[1:])
    baton_path = args.baton_path

    if args.session_id is not None:
        session_id = args.session_id
    else:
        session_id = _discover_local_session_id()

    baton = {
        "session_id": session_id,
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
