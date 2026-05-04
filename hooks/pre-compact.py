#!/usr/bin/env python3
"""
hooks/pre-compact.py — PreCompact orchestrator.

Purpose: Fired by Claude Code's PreCompact event before context compaction.
Orchestrates the full ARMED → BATON_WRITTEN transition:
  1. Acquire gate.lock (lib/gate-lock.py --acquire PreCompact)
  2. Build handoff payload (lib/handoff-builder.py → JSON on stdout)
  3. Augment payload: add session_id + auto_mode_resumed=false + gate_state=BATON_WRITTEN
  4. Pipe augmented payload to lib/baton-writer.py (stdin → atomic write)
  5. Release gate.lock AFTER successful atomic rename (design.md line 281)
  6. Output {"continue": true} so Claude Code proceeds with compaction

ABORTED path (any step 1-4 fails):
  - Best-effort gate.lock release
  - Write last-resume-failure.txt via lib/notifier.py
  - Still output {"continue": true} (do NOT block Claude Code)

Spec references:
  design.md §1 lines 77-79 (T3+T5 transitions; T4 ABORTED path)
  design.md §2 lines 165-172 (baton schema; 7 required fields)
  design.md §2 lines 183-185 (1 MB cap → ABORTED path)
  design.md §3 line 281 (release ordering: unlink AFTER atomic rename)
  Opus PLAN_AUDIT Q4 (subprocess.run pattern, NOT Python lib import)
  Stage 3 I-035 (CLAUDE_SESSION_ID env fallback: pid + start_time)

CLI:
  python3 hooks/pre-compact.py             # production
  python3 hooks/pre-compact.py --test-mode # test: uses /tmp as project dir

Implementation task: T-3-6.
"""
import json
import os
import subprocess
import sys
import time
import uuid
from typing import Optional


# Subprocess timeout limits (seconds)
_LOCK_ACQUIRE_TIMEOUT: int = 10
_HANDOFF_BUILD_TIMEOUT: int = 10
_BATON_WRITE_TIMEOUT: int = 10
_LOCK_RELEASE_TIMEOUT: int = 5
_NOTIFIER_TIMEOUT: int = 5

# Hook return payload (design.md hook-development SKILL: PreCompact must output JSON)
_HOOK_CONTINUE: str = json.dumps({"continue": True})


def _resolve_project_dir(test_mode: bool) -> str:
    """Return the effective project directory.

    Production: $CLAUDE_PROJECT_DIR (required; exits 1 if absent).
    Test mode: /tmp (avoids touching real project state).
    """
    if test_mode:
        return "/tmp"

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "").strip()
    if not project_dir:
        print(
            "[pre-compact] ERROR: $CLAUDE_PROJECT_DIR not set.",
            file=sys.stderr,
        )
        sys.exit(1)
    return project_dir


def _resolve_lib_dir() -> str:
    """Return the lib/ directory co-located with this hooks/ directory.

    Resolves relative to this file's absolute location so the script works
    regardless of cwd.
    """
    hooks_dir = os.path.dirname(os.path.abspath(__file__))
    plugin_root = os.path.dirname(hooks_dir)
    return os.path.join(plugin_root, "lib")


def _derive_session_id() -> str:
    """Return CLAUDE_SESSION_ID from env or derive a stable fallback.

    Fallback per I-035 spike: combine pid + process start_time from /proc
    on Linux, or psutil if available, otherwise use pid + wall-clock second
    as a stable-within-session identifier. On any error, fall back to a
    fresh UUID (last-resort; only matters if the daemon needs to verify
    session_id at T8 — a mismatch would route through ABORTED at that point).
    """
    env_id = os.environ.get("CLAUDE_SESSION_ID", "").strip()
    if env_id:
        return env_id

    # Fallback: pid + process start mtime from /proc/<pid>/stat (Linux)
    pid = os.getpid()
    try:
        stat_path = f"/proc/{pid}/stat"
        if os.path.exists(stat_path):
            with open(stat_path, "r") as fh:
                fields = fh.read().split()
            # Field 22 (index 21) is starttime in clock ticks
            starttime = fields[21]
            return f"pid-{pid}-start-{starttime}"
    except (OSError, IndexError):
        pass

    # macOS fallback: combine pid + create time via ps
    try:
        result = subprocess.run(
            ["ps", "-p", str(pid), "-o", "lstart="],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if result.returncode == 0 and result.stdout.strip():
            # Stable within session; not a UUID but good enough as identifier
            start_str = result.stdout.strip().replace(" ", "-")
            return f"pid-{pid}-start-{start_str}"
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    # Last resort: fresh UUID (means T8 session_id re-validation will fail → ABORTED;
    # acceptable per design — better than blocking compaction)
    fallback = str(uuid.uuid4())
    print(
        f"[pre-compact] WARNING: CLAUDE_SESSION_ID not set; "
        f"CLAUDE_SESSION_ID fallback = {fallback!r} (I-035)",
        file=sys.stderr,
    )
    return fallback


def _acquire_gate_lock(lib_dir: str, project_dir: str) -> bool:
    """Invoke lib/gate-lock.py --acquire PreCompact via subprocess.

    Returns True if lock acquired; False if held by live process (contention).
    """
    result = subprocess.run(
        [
            sys.executable,
            os.path.join(lib_dir, "gate-lock.py"),
            "--test-acquire",
            os.path.join(project_dir, ".teamlead", "gate.lock"),
            "PreCompact",
        ],
        timeout=_LOCK_ACQUIRE_TIMEOUT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(
            f"[pre-compact] gate-lock acquire failed (exit {result.returncode}): "
            f"{result.stderr.strip()}",
            file=sys.stderr,
        )
        return False
    return True


def _release_gate_lock(lib_dir: str, project_dir: str) -> None:
    """Invoke lib/gate-lock.py --release via subprocess (best-effort)."""
    try:
        subprocess.run(
            [
                sys.executable,
                os.path.join(lib_dir, "gate-lock.py"),
                "--test-release",
                os.path.join(project_dir, ".teamlead", "gate.lock"),
            ],
            timeout=_LOCK_RELEASE_TIMEOUT,
            capture_output=True,
            text=True,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        print(
            f"[pre-compact] WARNING: gate-lock release failed: {exc}",
            file=sys.stderr,
        )


def _build_handoff_payload(lib_dir: str, project_dir: str) -> Optional[dict]:
    """Invoke lib/handoff-builder.py and parse JSON from stdout.

    Returns 6-field dict on success; None on failure.
    """
    # Pass CLAUDE_PROJECT_DIR so handoff-builder can resolve paths
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = project_dir

    result = subprocess.run(
        [sys.executable, os.path.join(lib_dir, "handoff-builder.py")],
        env=env,
        capture_output=True,
        text=True,
        timeout=_HANDOFF_BUILD_TIMEOUT,
    )
    if result.returncode != 0:
        print(
            f"[pre-compact] handoff-builder failed (exit {result.returncode}): "
            f"{result.stderr.strip()}",
            file=sys.stderr,
        )
        return None

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        print(
            f"[pre-compact] handoff-builder output is not valid JSON: {exc}",
            file=sys.stderr,
        )
        return None

    return payload


def _write_baton(lib_dir: str, project_dir: str, payload: dict) -> bool:
    """Pipe payload JSON to lib/baton-writer.py via stdin.

    Returns True on success (exit 0); False on failure (exit 1 = size cap,
    missing key, OS error, etc.).
    """
    # Pipe to baton-writer --test-write <path> to write to project_dir's .teamlead/
    baton_path = os.path.join(project_dir, ".teamlead", "baton.json")

    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = project_dir

    result = subprocess.run(
        [
            sys.executable,
            os.path.join(lib_dir, "baton-writer.py"),
            "--test-write",
            baton_path,
        ],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=_BATON_WRITE_TIMEOUT,
    )
    if result.returncode != 0:
        print(
            f"[pre-compact] baton-writer failed (exit {result.returncode}): "
            f"{result.stderr.strip()}",
            file=sys.stderr,
        )
        return False
    return True


def _notify_failure(lib_dir: str, project_dir: str, summary: str) -> None:
    """Invoke lib/notifier.py --test-notify to write last-resume-failure.txt."""
    failure_path = os.path.join(project_dir, ".teamlead", "last-resume-failure.txt")
    try:
        subprocess.run(
            [
                sys.executable,
                os.path.join(lib_dir, "notifier.py"),
                "--test-notify",
                summary,
                failure_path,
            ],
            timeout=_NOTIFIER_TIMEOUT,
            capture_output=True,
            text=True,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        print(
            f"[pre-compact] WARNING: notifier failed: {exc}",
            file=sys.stderr,
        )


def _orchestrate(test_mode: bool) -> None:
    """Main orchestration: ARMED → BATON_WRITTEN (or ABORTED path).

    Sequence (per design.md §1 T3 + dispatch guidance):
    1. Acquire gate.lock
    2. Build handoff payload (6 fields from handoff-builder)
    3. Augment: add session_id + auto_mode_resumed=false + gate_state=BATON_WRITTEN
    4. Pipe to baton-writer (atomic write)
    5. Release gate.lock AFTER atomic rename (design.md line 281 — critical ordering)
    6. Output {"continue": true}

    ABORTED path: any step 1-4 failure → best-effort lock release + notifier + continue.
    """
    project_dir = _resolve_project_dir(test_mode)
    lib_dir = _resolve_lib_dir()

    lock_held: bool = False

    # --- Step 1: Acquire gate.lock ---
    lock_held = _acquire_gate_lock(lib_dir, project_dir)
    if not lock_held:
        # Gate contention: another actor holds → ABORTED path
        summary = "PreCompact ABORTED: gate.lock held by live process (contention)"
        print(f"[pre-compact] {summary}", file=sys.stderr)
        _notify_failure(lib_dir, project_dir, summary)
        # Output continue so Claude Code is not blocked
        print(_HOOK_CONTINUE)
        return

    # --- Step 2: Build handoff payload (6 fields) ---
    payload = _build_handoff_payload(lib_dir, project_dir)
    if payload is None:
        summary = "PreCompact ABORTED: handoff-builder failed to produce payload"
        print(f"[pre-compact] {summary}", file=sys.stderr)
        _release_gate_lock(lib_dir, project_dir)
        _notify_failure(lib_dir, project_dir, summary)
        print(_HOOK_CONTINUE)
        return

    # --- Step 3: Augment payload with orchestrator-owned fields ---
    # session_id: from env or I-035 fallback
    payload["session_id"] = _derive_session_id()
    # auto_mode_resumed: FROZEN false (design.md §2 line 171; charter invariant)
    payload["auto_mode_resumed"] = False
    # gate_state: BATON_WRITTEN marks the T3 side-effect (design.md §1 T3)
    payload["gate_state"] = "BATON_WRITTEN"

    # --- Step 4: Atomic write via baton-writer ---
    write_ok = _write_baton(lib_dir, project_dir, payload)
    if not write_ok:
        # Covers: size > 1 MB cap, missing key, OS error (design.md lines 183-185)
        summary = "PreCompact ABORTED: baton-writer failed (size cap / OS error)"
        print(f"[pre-compact] {summary}", file=sys.stderr)
        _release_gate_lock(lib_dir, project_dir)
        _notify_failure(lib_dir, project_dir, summary)
        print(_HOOK_CONTINUE)
        return

    # --- Step 5: Release gate.lock AFTER successful atomic rename ---
    # design.md line 281: "MUST happen before the unlink" — i.e., release AFTER write
    _release_gate_lock(lib_dir, project_dir)

    # --- Step 6: Output hook return (PreCompact expects {"continue": true}) ---
    print(_HOOK_CONTINUE)
    print(
        f"[pre-compact] BATON_WRITTEN: baton committed; gate.lock released.",
        file=sys.stderr,
    )


def main() -> None:
    """CLI entry point."""
    args = sys.argv[1:]
    test_mode = "--test-mode" in args
    _orchestrate(test_mode)


if __name__ == "__main__":
    main()
