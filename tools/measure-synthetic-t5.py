#!/usr/bin/env python3
"""Phase C synthetic --self-test-t5 measurement (AC-3 CCBL-Stage3-v0.1.11-AC3-LOCAL-REFRAME).

Measures daemon.py --test-mode --self-test-t5 (BATON_WRITTEN → SESSION_RESUMED).
Deviation: test_mode skips claude spawn + §7(g-1) timeout/poll loop (plumbing only).
Usage: python3 tools/measure-synthetic-t5.py [--self-test]
       MEASURE_N=10 python3 tools/measure-synthetic-t5.py
"""

import argparse
import json
import math
import os
import platform
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAEMON = os.path.join(ROOT, "scripts", "daemon.py")
WRITER = os.path.join(ROOT, "tools", "write-synthetic-baton.py")
JSONL_OUT = os.path.join(ROOT, ".teamlead", "synthetic-t5-measurement.jsonl")
SUMMARY_OUT = os.path.join(ROOT, "docs", "specs", "v0.1.11-evidence", "synthetic-t5-summary.json")


def _pct(sorted_vals: list[float], p: float) -> float:
    # _pct: assumes sorted_vals is already sorted (caller responsibility; see _stats)
    return sorted_vals[max(0, math.ceil(p / 100.0 * len(sorted_vals)) - 1)]


def _stats(vals: list[float]) -> dict:
    if not vals:
        return {"p50": None, "p95": None, "max": None, "n": 0}
    s = sorted(vals)
    return {"p50": round(_pct(s, 50), 3), "p95": round(_pct(s, 95), 3), "max": round(s[-1], 3), "n": len(s)}


def _write_baton(watch_dir: str) -> str:
    baton_path = os.path.join(watch_dir, "baton.json")
    if os.path.exists(baton_path):
        os.unlink(baton_path)
    r = subprocess.run(
        [sys.executable, WRITER, "--project-dir", ROOT, "--scenario", "same-commit",
         "--mismatch-field", "none", "--output", baton_path],
        capture_output=True, text=True, timeout=30,
    )
    if r.returncode != 0:
        raise RuntimeError(f"write-synthetic-baton failed: {r.stderr.strip()}")
    return baton_path


def _run_iter(watch_dir: str, idx: int, cold: bool) -> dict:
    label = "cold" if cold else "warm"
    baton_path = _write_baton(watch_dir)
    with open(baton_path, encoding="utf-8") as fh:
        pre = json.load(fh)
    if pre.get("gate_state") != "BATON_WRITTEN":
        return {"iteration": idx, "label": label, "wall_clock_s": None, "exit_code": None,
                "gate_state_post": pre.get("gate_state"), "status": "FAIL",
                "error": f"pre gate_state={pre.get('gate_state')!r}"}
    t0 = time.monotonic()
    r = subprocess.run(
        [sys.executable, DAEMON, "--watch", watch_dir, "--test-mode", "--self-test-t5"],
        capture_output=True, text=True, timeout=60,
        env={**os.environ, "CLAUDE_PLUGIN_ROOT": ROOT},
    )
    wall = round(time.monotonic() - t0, 3)
    try:
        with open(baton_path, encoding="utf-8") as fh:
            gate_post = json.load(fh).get("gate_state")
    except (OSError, json.JSONDecodeError) as e:
        gate_post = f"READ_ERROR:{e}"
    status = "PASS" if r.returncode == 0 and gate_post == "SESSION_RESUMED" else "FAIL"
    return {"iteration": idx, "label": label, "wall_clock_s": wall, "exit_code": r.returncode,
            "gate_state_post": gate_post, "status": status,
            "stderr_tail": r.stderr.strip()[-200:] if r.stderr else ""}


def run_measurement(n: int) -> int:
    print(f"[measure-synthetic-t5] N={n}", file=sys.stderr)
    os.makedirs(os.path.dirname(JSONL_OUT), exist_ok=True)
    os.makedirs(os.path.dirname(SUMMARY_OUT), exist_ok=True)
    results: list[dict] = []
    all_pass = True
    with tempfile.TemporaryDirectory(prefix="tl-synth-t5-") as wd:
        os.makedirs(os.path.join(wd, ".teamlead"), exist_ok=True)
        for i in range(n):
            rec = _run_iter(wd, i + 1, cold=(i == 0))
            results.append(rec)
            print(f"[measure-synthetic-t5] iter={i+1}/{n} label={rec['label']} "
                  f"wall={rec.get('wall_clock_s')}s gate={rec.get('gate_state_post')} status={rec['status']}",
                  file=sys.stderr)
            if rec["status"] != "PASS":
                all_pass = False
                print(f"[measure-synthetic-t5] FAIL: {rec.get('error', rec.get('stderr_tail'))}", file=sys.stderr)
    with open(JSONL_OUT, "w", encoding="utf-8") as fh:
        for r in results:
            fh.write(json.dumps(r) + "\n")
    cold_t = [r["wall_clock_s"] for r in results if r["label"] == "cold" and r["wall_clock_s"] is not None]
    warm_t = [r["wall_clock_s"] for r in results if r["label"] == "warm" and r["wall_clock_s"] is not None]
    sha = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"],
                         capture_output=True, text=True).stdout.strip()
    summary = {
        "iterations": n, "cold": _stats(cold_t), "warm": _stats(warm_t),
        "all_pass": all_pass, "test_mode": "synthetic_self_test_t5",
        "deviation_from_real_e2e": (
            "test_mode=True skips real claude spawn, git stash, and §7(g-1) 30s primary wait "
            "+ 28s poll loop. Validates allowlist + baton-update plumbing only. "
            "See measurement-protocol.v0.1.9.md deviation-1 pattern."
        ),
        "host": f"{platform.uname().system} {platform.uname().machine}",
        "daemon_commit_sha": sha,
        "timestamp_iso": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    with open(SUMMARY_OUT, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
        fh.write("\n")
    print(json.dumps(summary, indent=2))
    return 0 if all_pass else 1


def run_self_test() -> int:
    print("[measure-synthetic-t5 --self-test] N=2 schema verification", file=sys.stderr)
    if run_measurement(2) != 0:
        print("[measure-synthetic-t5 --self-test] FAIL: measurement returned non-zero", file=sys.stderr)
        return 1
    with open(SUMMARY_OUT, encoding="utf-8") as fh:
        s = json.load(fh)
    required = ["iterations", "cold", "warm", "all_pass", "test_mode",
                "deviation_from_real_e2e", "host", "daemon_commit_sha", "timestamp_iso"]
    missing = [k for k in required if k not in s]
    if missing:
        print(f"[measure-synthetic-t5 --self-test] FAIL: missing keys {missing}", file=sys.stderr)
        return 1
    if s["iterations"] != 2 or not s["all_pass"]:
        print(f"[measure-synthetic-t5 --self-test] FAIL: iterations={s['iterations']} all_pass={s['all_pass']}", file=sys.stderr)
        return 1
    print("[measure-synthetic-t5 --self-test] PASS: schema valid, all_pass=true, iterations=2")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Phase C synthetic --self-test-t5 measurement for AC-3")
    p.add_argument("--self-test", action="store_true", help="Run N=2 and verify output schema")
    args = p.parse_args()
    return run_self_test() if args.self_test else run_measurement(int(os.environ.get("MEASURE_N", "10")))


if __name__ == "__main__":
    sys.exit(main())
