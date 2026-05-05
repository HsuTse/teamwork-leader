#!/usr/bin/env python3
"""
tools/measure-poll-resumed.py — Poll baton.json until SESSION_RESUMED for T-1-c.

Polls the baton file at 500ms intervals until gate_state transitions to
SESSION_RESUMED or the timeout expires. Prints a JSON record to stdout.

Exit code 0: SESSION_RESUMED observed (latency recorded).
Exit code 1: timeout or ABORTED state reached (measurement failed).

Usage:
    python3 tools/measure-poll-resumed.py \
        <baton_path> <baton_write_ts> <run_id> <run_type> <timeout_s>

    baton_path    — path to baton.json
    baton_write_ts — T0 float epoch timestamp (from measure-write-baton.py)
    run_id        — string identifier, e.g. "cold-001"
    run_type      — "cold" or "warm"
    timeout_s     — max seconds to poll
"""

import datetime
import json
import sys
import time


def main() -> None:
    if len(sys.argv) != 6:
        print(
            "Usage: measure-poll-resumed.py "
            "<baton_path> <baton_write_ts> <run_id> <run_type> <timeout_s>",
            file=sys.stderr,
        )
        sys.exit(1)

    baton_path = sys.argv[1]
    baton_write_ts = float(sys.argv[2])
    run_id = sys.argv[3]
    run_type = sys.argv[4]
    timeout_s = float(sys.argv[5])

    deadline = time.time() + timeout_s
    poll_interval = 0.5  # 500ms granularity for low-latency detection

    session_resumed_ts = None
    gate_state_seen = "BATON_WRITTEN"

    while time.time() < deadline:
        try:
            with open(baton_path, encoding="utf-8") as f:
                baton = json.load(f)
            gs = baton.get("gate_state", "")
            gate_state_seen = gs
            if gs == "SESSION_RESUMED":
                session_resumed_ts = time.time()
                break
            elif gs in ("ABORTED", "UNKNOWN"):
                # Daemon failed (T6 exhausted) — this run is invalid
                break
        except (json.JSONDecodeError, FileNotFoundError):
            pass
        time.sleep(poll_interval)

    if session_resumed_ts is None:
        result = {
            "run_id": run_id,
            "type": run_type,
            "status": "TIMEOUT_OR_ABORTED",
            "gate_state_final": gate_state_seen,
            "baton_write_ts": baton_write_ts,
            "session_resumed_ts": None,
            "latency_s": None,
        }
        print(json.dumps(result))
        sys.exit(1)

    latency_s = session_resumed_ts - baton_write_ts
    result = {
        "run_id": run_id,
        "type": run_type,
        "status": "OK",
        "latency_s": round(latency_s, 3),
        "baton_write_ts": round(baton_write_ts, 3),
        "session_resumed_ts": round(session_resumed_ts, 3),
        "timestamp_iso": datetime.datetime.utcfromtimestamp(session_resumed_ts).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "runner_info": {
            "os": "macOS 14",
            "arch": "arm64",
            "gha_runner_label": "macos-14",
            "gha_runner_arch": "ARM64",
        },
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
