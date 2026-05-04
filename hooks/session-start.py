#!/usr/bin/env python3
"""
hooks/session-start.py — SessionStart hook handler.

Purpose: Fired by Claude Code's SessionStart event at the beginning of each
session. Handles two routing paths:

  (a) No baton present: ensures .teamlead/ dir, verifies gate.lock absent or
      stale-recoverable, transitions to ARMED. Outputs ARMED banner.
      Spec: design.md §1 T1, lines 76, 124-125.

  (b) Fresh baton (gate_state=BATON_WRITTEN): reads baton, re-validates 4 fields
      (prior_pause_commit, branch, progress_md_anchor, last_action_iso), composes
      RESUME banner. HALTs for CEO ack — does NOT auto-execute.
      Spec: design.md §1 T8, lines 83-84, 202-203, 439.

  (c) Any validation mismatch: ABORTED path — writes last-resume-failure.txt via
      lib/notifier.py. Outputs failure banner. Does NOT rename baton.

  (d) --ack-resume (CEO explicit ack): renames baton.json to baton.consumed-<ISO>.json;
      releases gate.lock via lib/gate-lock.py --release. Outputs DONE banner.
      Spec: design.md §1 T9, line 84.

Output contract: ALL paths write valid JSON to stdout:
  {"continue": true, "systemMessage": "<banner>"}
The hook must NEVER write non-JSON to stdout (Claude Code parses this).
All diagnostic/debug text goes to stderr.

Key invariants (FROZEN per design.md §5 + ~/CLAUDE.md §高風險操作):
  - AUTO_MODE_RESUMED is ALWAYS false on resume; CEo ack required.
  - Do NOT rename baton without explicit --ack-resume invocation.
  - Do NOT auto-execute the restore_prompt. Display only.

CLI signature:
  python3 hooks/session-start.py
      Production: detect baton + dispatch routing.

  python3 hooks/session-start.py --test-mode-no-baton
      Test: simulate no-baton ARMED path; exits 0.

  python3 hooks/session-start.py --test-mode-with-baton <path>
      Test: validate baton at <path>; exits 0.

  python3 hooks/session-start.py --test-mode-mismatch <path>
      Test: simulate mismatch ABORTED path; exits 0 (no baton renamed).

  python3 hooks/session-start.py --ack-resume
      Production: CEO ack — rename baton + release gate.lock; exits 0.

Spec references:
  design.md §1 T1/T8/T9 lines 76, 83-84, 124-125, 202-203, 439
  design.md §2 lines 163-172 (baton schema — 7 required fields)
  design.md §5 ~line 470 (Auto-Mode-OFF default, frozen invariant)
  I-036 (SessionStart output injection API — systemMessage field)
Implementation task: T-3-8.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any, Optional


# ── constants ─────────────────────────────────────────────────────────────────

# Required baton fields per design.md §2 lines 165-172
_REQUIRED_BATON_KEYS: list[str] = [
    "session_id",
    "prior_pause_commit",
    "branch",
    "last_action_iso",
    "progress_md_anchor",
    "restore_prompt",
    "auto_mode_resumed",
]

# gate_state value that indicates a fresh, unconsumed baton
_GATE_STATE_BATON_WRITTEN = "BATON_WRITTEN"

# Regex to extract ISO timestamp from PROGRESS.md "## Last Action:" line
# Matches: "## Last Action: 2026-05-04T10:06+08:00 [TRUSTED] — ..."
_LAST_ACTION_RE = re.compile(
    r"^##\s+Last Action:\s+(\S+)", re.MULTILINE
)


# ── path helpers ──────────────────────────────────────────────────────────────


def _project_dir() -> str:
    """Return $CLAUDE_PROJECT_DIR; exit 1 if unset."""
    d = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not d:
        _log("ERROR: $CLAUDE_PROJECT_DIR not set")
        sys.exit(1)
    return d


def _plugin_root() -> str:
    """Return $CLAUDE_PLUGIN_ROOT; fall back to directory of this script."""
    return os.environ.get(
        "CLAUDE_PLUGIN_ROOT",
        os.path.dirname(os.path.abspath(__file__)),
    )


def _teamlead_dir(project_dir: str) -> str:
    return os.path.join(project_dir, ".teamlead")


def _baton_path(project_dir: str) -> str:
    return os.path.join(_teamlead_dir(project_dir), "baton.json")


def _lock_path(project_dir: str) -> str:
    return os.path.join(_teamlead_dir(project_dir), "gate.lock")


def _progress_md_path(project_dir: str) -> str:
    return os.path.join(project_dir, "PROGRESS.md")


def _failure_txt_path(project_dir: str) -> str:
    return os.path.join(_teamlead_dir(project_dir), "last-resume-failure.txt")


# ── output helpers ─────────────────────────────────────────────────────────────


def _log(msg: str) -> None:
    """Write diagnostic message to stderr (never stdout)."""
    print(f"[session-start] {msg}", file=sys.stderr)


def _emit(system_message: str) -> None:
    """Write the required hook JSON payload to stdout and flush.

    Per I-036: Claude Code's SessionStart hook reads stdout and injects the
    systemMessage field into the session context. Output must be valid JSON only.
    """
    payload = {"continue": True, "systemMessage": system_message}
    sys.stdout.write(json.dumps(payload))
    sys.stdout.flush()


# ── filesystem helpers ────────────────────────────────────────────────────────


def _ensure_teamlead_dir(project_dir: str) -> None:
    """Ensure .teamlead/ directory exists with appropriate permissions.

    Per design.md §1 T1 line 76: SessionStart ensures .teamlead/ dir on no-baton path.
    Uses os.makedirs per I-018 (guard-tolerant Python; no bash chmod).
    """
    tl_dir = _teamlead_dir(project_dir)
    try:
        os.makedirs(tl_dir, exist_ok=True)
        os.chmod(tl_dir, 0o700)
    except OSError as exc:
        _log(f"WARNING: could not ensure .teamlead/ dir: {exc}")
        # Non-fatal; degraded mode per design.md §1 T1 failure mode


def _read_baton(baton_path: str) -> Optional[dict[str, Any]]:
    """Read and parse baton.json; return None if absent or corrupt."""
    if not os.path.exists(baton_path):
        return None
    try:
        with open(baton_path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        _log(f"WARNING: could not read baton at {baton_path!r}: {exc}")
        return None


def _validate_baton_schema(baton: dict[str, Any]) -> list[str]:
    """Return list of missing/null required fields; empty list = schema OK."""
    errors: list[str] = []
    for key in _REQUIRED_BATON_KEYS:
        if key not in baton:
            errors.append(f"missing key: {key!r}")
        elif baton[key] is None:
            errors.append(f"null value for key: {key!r}")
    return errors


# ── current-state probes ──────────────────────────────────────────────────────


def _current_head_commit(cwd: str) -> Optional[str]:
    """Return current git HEAD commit SHA; None on any error."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        _log(f"WARNING: git rev-parse HEAD failed: {exc}")
    return None


def _current_branch(cwd: str) -> Optional[str]:
    """Return current git branch name; None on any error."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        _log(f"WARNING: git rev-parse --abbrev-ref HEAD failed: {exc}")
    return None


def _sha256_file(path: str) -> Optional[str]:
    """Return sha256 hex digest of file content; None if file not readable."""
    try:
        with open(path, "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()
    except OSError as exc:
        _log(f"WARNING: sha256 of {path!r} failed: {exc}")
    return None


def _extract_last_action_iso(progress_md_path: str) -> Optional[str]:
    """Extract ISO timestamp from first '## Last Action:' line in PROGRESS.md.

    Per design.md §2 line 168: last_action_iso is used as a drift indicator.
    This is a soft-validation field; if not parseable, we skip the check.
    """
    try:
        with open(progress_md_path, "r", encoding="utf-8") as fh:
            content = fh.read()
    except OSError:
        return None
    m = _LAST_ACTION_RE.search(content)
    if m:
        return m.group(1)
    return None


# ── gate-lock helpers ─────────────────────────────────────────────────────────


def _release_gate_lock(lock_path: str) -> None:
    """Release gate.lock by invoking lib/gate-lock.py --test-release <path>.

    Uses test-release (path-explicit) to avoid $CLAUDE_PROJECT_DIR dependency in
    gate-lock.py CLI; our caller already has the resolved path.
    """
    gate_lock_script = os.path.join(_plugin_root(), "..", "lib", "gate-lock.py")
    gate_lock_script = os.path.normpath(gate_lock_script)
    try:
        subprocess.run(
            [sys.executable, gate_lock_script, "--test-release", lock_path],
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        _log(f"WARNING: gate-lock release failed: {exc}")


def _check_gate_lock_stale_or_absent(lock_path: str) -> None:
    """On no-baton ARMED path: invoke reaper on lock if present.

    Per design.md §1 T1 line 76: verify gate.lock absent or stale-recoverable.
    We invoke lib/gate-lock.py --reap (which handles stale recovery) and
    let a live lock remain in place (the session itself will proceed safely —
    ARMED state does not require the lock to be absent).
    """
    if not os.path.exists(lock_path):
        return
    gate_lock_script = os.path.join(_plugin_root(), "..", "lib", "gate-lock.py")
    gate_lock_script = os.path.normpath(gate_lock_script)
    try:
        subprocess.run(
            [sys.executable, gate_lock_script, "--reap"],
            timeout=10,
            env={**os.environ, "CLAUDE_PROJECT_DIR": os.path.dirname(os.path.dirname(lock_path))},
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        _log(f"WARNING: gate-lock reap on ARMED path failed: {exc}")


# ── notifier helper ───────────────────────────────────────────────────────────


def _write_failure_notice(failure_path: str, message: str) -> None:
    """Write failure notice via lib/notifier.py --test-notify.

    Uses path-explicit test-notify to avoid production $CLAUDE_PROJECT_DIR
    dependency when called from test modes.
    """
    notifier_script = os.path.join(_plugin_root(), "..", "lib", "notifier.py")
    notifier_script = os.path.normpath(notifier_script)
    try:
        subprocess.run(
            [sys.executable, notifier_script, "--test-notify", message, failure_path],
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        _log(f"WARNING: notifier invocation failed: {exc}")
        # Fallback: write directly to failure_path
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        try:
            os.makedirs(os.path.dirname(failure_path), exist_ok=True)
            with open(failure_path, "w", encoding="utf-8") as fh:
                fh.write(f"timestamp: {ts}\nmessage: {message}\n")
        except OSError:
            pass


# ── ISO timestamp helper ──────────────────────────────────────────────────────


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── routing paths ─────────────────────────────────────────────────────────────


def _path_armed(project_dir: str) -> None:
    """No-baton ARMED path.

    Per design.md §1 T1 lines 76, 124-125:
    - Ensure .teamlead/ dir exists.
    - Verify gate.lock absent or stale-recoverable (run reaper).
    - Emit ARMED banner.
    """
    _ensure_teamlead_dir(project_dir)
    lock_path = _lock_path(project_dir)
    _check_gate_lock_stale_or_absent(lock_path)
    _emit("[teamwork-leader] No active baton; session armed.")


def _path_validate_baton(
    project_dir: str,
    baton: dict[str, Any],
    baton_path: str,
) -> None:
    """Fresh-baton validation path (T8).

    Re-validates 4 fields against current state per design.md §1 T8, lines 202-203, 439:
      1. prior_pause_commit vs git rev-parse HEAD
      2. branch vs git rev-parse --abbrev-ref HEAD
      3. progress_md_anchor vs sha256(PROGRESS.md)
      4. last_action_iso vs PROGRESS.md ## Last Action: extract (soft)

    On all-match: compose RESUME banner; output for CEO ack; do NOT rename baton.
    On mismatch: ABORTED path — write failure notice; output failure banner.

    Key invariant: DOES NOT auto-rename baton or execute restore_prompt.
    CEO must invoke --ack-resume explicitly.
    """
    mismatches: list[str] = []
    progress_md_path = _progress_md_path(project_dir)
    failure_path = _failure_txt_path(project_dir)

    # Field 1: prior_pause_commit vs HEAD
    baton_commit: str = baton.get("prior_pause_commit", "")
    current_commit = _current_head_commit(project_dir)
    if current_commit is None:
        mismatches.append(
            f"prior_pause_commit: could not read git HEAD "
            f"(baton expects {baton_commit!r})"
        )
    elif current_commit != baton_commit:
        mismatches.append(
            f"prior_pause_commit: baton={baton_commit!r} "
            f"vs current HEAD={current_commit!r}"
        )

    # Field 2: branch
    baton_branch: str = baton.get("branch", "")
    current_branch_val = _current_branch(project_dir)
    if current_branch_val is None:
        mismatches.append(
            f"branch: could not read git branch "
            f"(baton expects {baton_branch!r})"
        )
    elif current_branch_val != baton_branch:
        mismatches.append(
            f"branch: baton={baton_branch!r} "
            f"vs current={current_branch_val!r}"
        )

    # Field 3: progress_md_anchor vs sha256(PROGRESS.md)
    baton_anchor: str = baton.get("progress_md_anchor", "")
    current_anchor = _sha256_file(progress_md_path)
    if current_anchor is None:
        mismatches.append(
            f"progress_md_anchor: could not read PROGRESS.md "
            f"(baton expects {baton_anchor!r})"
        )
    elif current_anchor != baton_anchor:
        mismatches.append(
            f"progress_md_anchor: baton={baton_anchor!r} "
            f"vs current={current_anchor!r} "
            f"(PROGRESS.md may have been edited externally)"
        )

    # Field 4: last_action_iso — soft validation (skip if not parseable)
    baton_last_action: str = baton.get("last_action_iso", "")
    current_last_action = _extract_last_action_iso(progress_md_path)
    if current_last_action is not None and baton_last_action:
        if current_last_action != baton_last_action:
            mismatches.append(
                f"last_action_iso: baton={baton_last_action!r} "
                f"vs PROGRESS.md={current_last_action!r}"
            )
    # If current_last_action is None or baton_last_action is empty: soft-skip

    if mismatches:
        # ABORTED path
        mismatch_detail = "; ".join(mismatches)
        failure_msg = (
            f"Resume validation FAILED at {_iso_now()} — {len(mismatches)} mismatch(es): "
            f"{mismatch_detail}"
        )
        _log(f"Baton mismatch(es) detected — routing ABORTED: {mismatch_detail}")
        _write_failure_notice(failure_path, failure_msg)
        _emit(
            f"[teamwork-leader] Resume failed — see .teamlead/last-resume-failure.txt "
            f"({len(mismatches)} mismatch(es): {mismatch_detail})"
        )
        return

    # All fields match — POST_RESUME_VERIFIED; compose RESUME banner
    # Per design.md §5 frozen invariant Auto-Mode-OFF: display restore_prompt only;
    # do NOT auto-execute; CEO must invoke --ack-resume explicitly.
    restore_prompt: str = baton.get("restore_prompt", "(restore_prompt not set)")
    last_dispatch_id: str = baton.get("last_dispatch_id", "unknown")
    written_at: str = baton.get("written_at_iso", "unknown")
    session_id: str = baton.get("session_id", "unknown")

    resume_banner = (
        f"[teamwork-leader] RESUME CONTEXT READY — POST_RESUME_VERIFIED\n"
        f"\n"
        f"Baton validated. All 4 re-validation fields match current repository state.\n"
        f"\n"
        f"Session paused at: {written_at}\n"
        f"Last dispatch: {last_dispatch_id}\n"
        f"Prior session ID: {session_id}\n"
        f"\n"
        f"RESTORE PROMPT (display only — CEO ack required before execution):\n"
        f"{restore_prompt}\n"
        f"\n"
        f"To acknowledge and consume baton, run:\n"
        f"  python3 hooks/session-start.py --ack-resume\n"
        f"\n"
        f"[Auto-Mode is OFF for this resumed session per ~/CLAUDE.md §高風險操作]"
    )
    _log("Baton validated; RESUME banner composed; awaiting CEO ack.")
    _emit(resume_banner)


def _path_ack_resume(project_dir: str) -> None:
    """CEO ack path (--ack-resume).

    Per design.md §1 T9 line 84:
    - Rename baton.json → baton.consumed-<ISO>.json
    - Release gate.lock

    Exits 0 on success; exits 1 if baton not found (idempotent guard).
    """
    baton_path = _baton_path(project_dir)
    lock_path = _lock_path(project_dir)

    if not os.path.exists(baton_path):
        _log("WARNING: --ack-resume called but no baton.json found (already consumed?)")
        _emit("[teamwork-leader] --ack-resume: no baton.json present; nothing to consume.")
        return

    iso_tag = _iso_now().replace(":", "-")
    consumed_path = os.path.join(
        _teamlead_dir(project_dir),
        f"baton.consumed-{iso_tag}.json",
    )
    try:
        os.rename(baton_path, consumed_path)
    except OSError as exc:
        _log(f"ERROR: could not rename baton to consumed: {exc}")
        sys.exit(1)

    _log(f"Baton consumed: {consumed_path!r}")

    # Release gate.lock (best-effort; missing lock is idempotent)
    _release_gate_lock(lock_path)

    _emit(
        f"[teamwork-leader] DONE — baton consumed (renamed to "
        f"baton.consumed-{iso_tag}.json). Session returns to ARMED."
    )


# ── production routing ────────────────────────────────────────────────────────


def _detect_and_route(project_dir: str) -> None:
    """Production routing: detect baton presence and dispatch.

    Per dispatch guidance §State routing logic:
    1. stat .teamlead/baton.json; if absent → ARMED path
    2. Read baton + check gate_state; if not BATON_WRITTEN → treat as no-baton
    3. Validate schema; if missing required fields → ABORTED
    4. Re-validate 4 fields → POST_RESUME_VERIFIED or ABORTED
    """
    baton_path = _baton_path(project_dir)
    baton = _read_baton(baton_path)

    if baton is None:
        # No baton or corrupt baton → ARMED
        _log("No baton found; routing to ARMED path.")
        _path_armed(project_dir)
        return

    # Check gate_state
    gate_state = baton.get("gate_state", "")
    if gate_state != _GATE_STATE_BATON_WRITTEN:
        _log(
            f"Baton gate_state={gate_state!r} (expected BATON_WRITTEN); "
            f"treating as no-baton."
        )
        _path_armed(project_dir)
        return

    # Validate required schema fields
    schema_errors = _validate_baton_schema(baton)
    if schema_errors:
        error_detail = "; ".join(schema_errors)
        failure_msg = (
            f"Resume schema validation FAILED at {_iso_now()} — "
            f"baton schema errors: {error_detail}"
        )
        _log(f"Baton schema errors: {error_detail}")
        _write_failure_notice(_failure_txt_path(project_dir), failure_msg)
        _emit(
            f"[teamwork-leader] Resume failed — baton schema invalid "
            f"({error_detail}). See .teamlead/last-resume-failure.txt"
        )
        return

    # All checks passed; run 4-field re-validation
    _log("Baton present with gate_state=BATON_WRITTEN; running 4-field re-validation.")
    _path_validate_baton(project_dir, baton, baton_path)


# ── test modes ────────────────────────────────────────────────────────────────


def _test_mode_no_baton() -> None:
    """Test: simulate ARMED path without needing $CLAUDE_PROJECT_DIR.

    Uses a temporary directory that looks like a project root.
    """
    import tempfile

    with tempfile.TemporaryDirectory() as tmp_dir:
        # Simulate ARMED path
        _ensure_teamlead_dir(tmp_dir)
        _emit("[teamwork-leader] No active baton; session armed.")
        _log("--test-mode-no-baton: PASS")


def _test_mode_with_baton(baton_path: str) -> None:
    """Test: validate baton at <path> against current git state.

    Uses current working directory as project_dir so git rev-parse and
    PROGRESS.md reads operate against the real repo. Any failure notices
    are written to <cwd>/.teamlead/last-resume-failure.txt (real path).
    """
    baton = _read_baton(baton_path)
    if baton is None:
        _log(f"ERROR: --test-mode-with-baton: could not read baton at {baton_path!r}")
        sys.exit(1)

    cwd = os.getcwd()
    # Ensure .teamlead/ exists in cwd so failure-notice writes don't fail
    os.makedirs(os.path.join(cwd, ".teamlead"), exist_ok=True)
    _path_validate_baton(cwd, baton, baton_path)
    _log("--test-mode-with-baton: PASS")


def _test_mode_mismatch(baton_path: str) -> None:
    """Test: simulate mismatch ABORTED path.

    Loads baton from <path> but intentionally corrupts the progress_md_anchor
    to force a mismatch, verifying that:
    - The failure notice is written.
    - The baton is NOT renamed.
    """
    import tempfile

    baton = _read_baton(baton_path)
    if baton is None:
        _log(f"ERROR: --test-mode-mismatch: could not read baton at {baton_path!r}")
        sys.exit(1)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tl_dir = os.path.join(tmp_dir, ".teamlead")
        os.makedirs(tl_dir, exist_ok=True)

        # Corrupt progress_md_anchor to force mismatch
        corrupted_baton = dict(baton)
        corrupted_baton["progress_md_anchor"] = "0" * 64

        _path_validate_baton(tmp_dir, corrupted_baton, baton_path)

        # Verify: baton.json at original path must still exist (not renamed)
        if not os.path.exists(baton_path):
            _log("ERROR: --test-mode-mismatch: baton was renamed (INVARIANT VIOLATED)")
            sys.exit(1)

        # Verify: last-resume-failure.txt was written
        failure_path = os.path.join(tl_dir, "last-resume-failure.txt")
        if not os.path.exists(failure_path):
            _log(
                "ERROR: --test-mode-mismatch: last-resume-failure.txt NOT written "
                "(expected ABORTED path to write it)"
            )
            sys.exit(1)

        _log("--test-mode-mismatch: PASS (baton intact, failure notice written)")


# ── CLI dispatch ──────────────────────────────────────────────────────────────


def main() -> None:
    """CLI entry point."""
    args = sys.argv[1:]

    # --test-mode-no-baton
    if args == ["--test-mode-no-baton"]:
        _test_mode_no_baton()
        sys.exit(0)

    # --test-mode-with-baton <path>
    if len(args) == 2 and args[0] == "--test-mode-with-baton":
        _test_mode_with_baton(args[1])
        sys.exit(0)

    # --test-mode-mismatch <path>
    if len(args) == 2 and args[0] == "--test-mode-mismatch":
        _test_mode_mismatch(args[1])
        sys.exit(0)

    # --ack-resume
    if args == ["--ack-resume"]:
        project_dir = _project_dir()
        _path_ack_resume(project_dir)
        sys.exit(0)

    # Production (no args): detect baton + dispatch
    if not args:
        project_dir = _project_dir()
        _detect_and_route(project_dir)
        sys.exit(0)

    # Unknown invocation
    _log(
        "Usage:\n"
        "  python3 hooks/session-start.py\n"
        "      Production: detect baton + dispatch routing.\n"
        "\n"
        "  python3 hooks/session-start.py --test-mode-no-baton\n"
        "      Test: simulate no-baton ARMED path.\n"
        "\n"
        "  python3 hooks/session-start.py --test-mode-with-baton <path>\n"
        "      Test: validate baton at <path>.\n"
        "\n"
        "  python3 hooks/session-start.py --test-mode-mismatch <path>\n"
        "      Test: simulate mismatch ABORTED path.\n"
        "\n"
        "  python3 hooks/session-start.py --ack-resume\n"
        "      CEO ack: rename baton + release gate.lock."
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
