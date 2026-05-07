#!/usr/bin/env python3
"""
tools/measure-compute-stats.py — Compute p50/p95/max from measurement JSONL.

Reads a JSONL file of run records (each line is a JSON object from
measure-poll-resumed.py), computes p50/p95/max per §statistics-computation
in measurement-protocol.v0.1.9.md, and prints a JSON summary to stdout.

At N=10, p95 == max by sample definition (PO-2 degeneracy clause).
AC-2 gate: p50 <= 30s AND p95 <= 30s AND max <= 30s.

Exit code 0: statistics computed (regardless of AC-2 verdict).
Exit code 1: no valid runs found.

Usage:
    python3 tools/measure-compute-stats.py <runs.jsonl>
"""

import json
import math
import sys


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: measure-compute-stats.py <runs.jsonl>", file=sys.stderr)
        sys.exit(1)

    jsonl_path = sys.argv[1]
    runs = []

    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                r = json.loads(line)
                if r.get("status") == "OK" and r.get("latency_s") is not None:
                    runs.append(r["latency_s"])

    n = len(runs)
    if n == 0:
        print(json.dumps({"error": "no valid runs", "n": 0}))
        sys.exit(1)

    runs_sorted = sorted(runs)

    # p50: value at index ceil(N/2) - 1 (0-indexed)
    p50 = runs_sorted[math.ceil(n / 2) - 1]

    # p95: value at index ceil(0.95 * N) - 1 (nearest-rank method)
    # At N=10: ceil(9.5) = 10, index 9 = max (PO-2 degeneracy clause)
    p95 = runs_sorted[math.ceil(0.95 * n) - 1]

    max_val = runs_sorted[-1]

    ac2_pass = (p50 <= 30.0) and (p95 <= 30.0) and (max_val <= 30.0)

    result = {
        "n": n,
        "p50_s": round(p50, 3),
        "p95_s": round(p95, 3),
        "max_s": round(max_val, 3),
        "ac2_verdict": "PASS" if ac2_pass else "FAIL",
        "note_n10_degeneracy": (
            "p95 == max at N=10 by sample definition "
            "(see measurement-protocol.v0.1.9.md §statistics-computation PO-2)"
        ),
        "raw_sorted": [round(v, 3) for v in runs_sorted],
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
