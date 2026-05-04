#!/usr/bin/env python3
"""
teamwork-leader auto-resume daemon (T-4-2 main loop)

Polls baton.json mtime every 5 s. On mtime change, reads and validates the
baton schema (7 required fields), checks gate_state == BATON_WRITTEN, then
hands off to the T5 actor (T-4-3).  T5 includes T6 retry-within-BATON_WRITTEN
(T-4-4): exponential backoff 1/4/16s, up to 3 attempts.  On T6 exhaustion,
_enter_aborted() (T-4-5) writes last-resume-failure.txt, sets gate_state=ABORTED,
and exits cleanly so launchd does NOT respawn (SuccessfulExit:false guard).

Per design.md §3.12 line 519, daemon.py does NOT remove its pid file on
clean exit — launchd respawns and the next instance overwrites it atomically
via os.replace.

Usage:
    daemon.py --watch <dir> [--test-mode]
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

POLL_INTERVAL_SECONDS: float = 5.0  # design.md line 276

# T6 retry constants (design.md lines 135 Q3 resolution, line 398)
T6_MAX_RETRIES: int = 3
# Backoff delays BEFORE each retry attempt (index = attempt number 0,1,2).
# I-061: T6_BACKOFF_SECONDS[0] (1.0s) is structurally dead — the loop guard
# "if attempt > 0" means the first attempt (attempt=0) never sleeps.
# The value is retained for index-symmetry clarity; refactor deferred to v0.1.8+.
T6_BACKOFF_SECONDS: list[float] = [1.0, 4.0, 16.0]
T6_BACKOFF_SECONDS_TEST: list[float] = [0.001, 0.001, 0.001]  # truncated for --self-test-t6-exhaust

# Required baton fields per design.md lines 164-172
BATON_REQUIRED_FIELDS: list[str] = [
    "session_id",
    "prior_pause_commit",
    "branch",
    "last_action_iso",
    "progress_md_anchor",
    "restore_prompt",
    "auto_mode_resumed",
]

GATE_STATE_TRIGGER = "BATON_WRITTEN"  # design.md line 64
GATE_STATE_RESUMED = "SESSION_RESUMED"  # design.md line 65

# restore_prompt allowlist per design.md §5 T-S-2 lines 628-630:
# ASCII letters, digits, whitespace (space/tab/\n), common punctuation.
# Disallowed: backtick, bare $, ${, NUL, control chars other than \n/\t.
_RESTORE_PROMPT_ALLOWLIST_RE = re.compile(
    r"^[\w\s.,;:\-_/()\[\]{}<>#@!?'\"]*$",
    re.UNICODE,
)
_RESTORE_PROMPT_MAX_BYTES = 8 * 1024  # design.md §5 lines 632: 8 KB cap


# ---------------------------------------------------------------------------
# PID file helpers
# ---------------------------------------------------------------------------

def _pid_path() -> str:
    """Return absolute path for daemon.pid based on CLAUDE_PROJECT_DIR or
    directory containing this script's parent (.teamlead sibling)."""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not project_dir:
        # Fall back: resolve relative to this file → scripts/../.teamlead/
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_dir, ".teamlead", "daemon.pid")


def _write_pid(pid_path: str) -> None:
    """Write current PID to pid_path with 0600 permissions per §5 T-S-1.
    Atomic via temp+replace so concurrent launchd respawns don't tear (design.md §3.12 line 519)."""
    os.makedirs(os.path.dirname(pid_path), exist_ok=True)
    tmp_path = pid_path + ".tmp"
    fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, (str(os.getpid()) + "\n").encode("utf-8"))
    finally:
        os.close(fd)
    os.replace(tmp_path, pid_path)


def _remove_pid(pid_path: str) -> None:
    """Remove pid_path if it exists. Reserved for uninstall (T-4-8) — NOT
    invoked from daemon.py main loop or exit path.  Per design.md §3.12
    line 519, the pid file is intentionally NOT removed on clean exit;
    launchd respawns and the new instance overwrites it atomically."""
    try:
        os.unlink(pid_path)
    except FileNotFoundError:
        pass


# ---------------------------------------------------------------------------
# T6 retry counter helpers (design.md line 81)
# ---------------------------------------------------------------------------

def _retry_counter_path() -> str:
    """Return absolute path for daemon-retries per design.md line 81.

    Uses CLAUDE_PROJECT_DIR env if set; otherwise resolves from script parent.
    """
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not project_dir:
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_dir, ".teamlead", "daemon-retries")


def _write_retry_counter(retry_path: str, count: int) -> None:
    """Atomically write retry count to retry_path (atomic via tmp+replace,
    matching daemon.pid pattern)."""
    os.makedirs(os.path.dirname(retry_path), exist_ok=True)
    tmp_path = retry_path + ".tmp"
    fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, (str(count) + "\n").encode("utf-8"))
    finally:
        os.close(fd)
    os.replace(tmp_path, retry_path)


def _read_retry_counter(retry_path: str) -> int:
    """Read current retry count from retry_path; returns 0 if file absent or unreadable."""
    try:
        with open(retry_path, encoding="utf-8") as fh:
            return int(fh.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


# ---------------------------------------------------------------------------
# T7 ABORTED real implementation (T-4-5)
# ---------------------------------------------------------------------------

def _enter_aborted(
    reason: str,
    watch_dir: str,
    *,
    test_mode: bool = False,
) -> None:
    """T7 retry-exhausted → ABORTED transition (design.md lines 526-542, 395).

    Steps:
      (a) Write last-resume-failure.txt atomically (0600) via lib/notifier.py
          subprocess call.  In test_mode: write to test dir, skip osascript.
          In production: write to $CLAUDE_PROJECT_DIR/.teamlead/ + fire osascript.
      (b) Update gate_state=ABORTED in baton.json under gate.lock — re-uses
          _update_baton_gate_state (T-4-3).  Release gate.lock via subprocess.
      (c) Log T7 marker so callers can grep "T7" in stderr.
      (d) Clean exit via sys.exit(0) — launchd KeepAlive SuccessfulExit:false
          prevents respawn (design.md line 395).

    In --test-mode: notifier uses --test-notify <msg> <path> so osascript is
    not invoked.  gate.lock ops use --test-acquire/--test-release with the
    lock path from watch_dir directly.
    """
    # Resolve paths
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    baton_path = os.path.join(watch_dir, "baton.json")
    lock_path = os.path.join(watch_dir, "gate.lock")

    # Resolve lib/ paths
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if not plugin_root:
        plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gate_lock_script = os.path.join(plugin_root, "lib", "gate-lock.py")
    lib_notifier_path = os.path.join(plugin_root, "lib", "notifier.py")

    # Build failure message content (design.md lines 526-536):
    # - ISO-8601 UTC timestamp (handled inside notifier._build_record)
    # - failing transition ID (T7)
    # - specific failure reason
    # - suggested operator action
    # - cross-ref to stash ref if last-stash.txt present
    last_stash_path = os.path.join(watch_dir, ".teamlead", "last-stash.txt")
    stash_ref_line = ""
    try:
        with open(last_stash_path, encoding="utf-8") as fh:
            stash_ref = fh.read().strip()
        if stash_ref:
            stash_ref_line = f"\nstash_ref: {stash_ref}"
    except FileNotFoundError:
        pass

    failure_message = (
        f"transition: T7\n"
        f"reason: {reason}\n"
        f"suggested_action: Check daemon logs; re-trigger by re-writing baton.json with gate_state=BATON_WRITTEN"
        f"{stash_ref_line}"
    )

    print(
        f"[daemon T7] ERROR: retries_exhausted — entering ABORTED: {reason}",
        file=sys.stderr,
    )

    # (a) Write last-resume-failure.txt via lib/notifier.py subprocess.
    # I-064: design.md top-level (line 526) describes a single-line key=value format;
    # this implementation emits a multi-line "transition: T7\nreason: ...\n..." format
    # per design.md §lines 526-536 detail spec.  The discrepancy is cosmetic (operators
    # can parse either); aligning to strict single-line is deferred to v0.1.8+ refactor.
    if test_mode:
        # test-mode: write to watch_dir/.teamlead/ (not production CLAUDE_PROJECT_DIR)
        # use --test-notify to skip osascript
        failure_file_path = os.path.join(watch_dir, ".teamlead", "last-resume-failure.txt")
        subprocess.run(
            ["python3", lib_notifier_path, "--test-notify", failure_message, failure_file_path],
            capture_output=True,
            check=False,
        )
    else:
        # production: notifier resolves path from $CLAUDE_PROJECT_DIR + fires osascript
        subprocess.run(
            ["python3", lib_notifier_path, "--notify", failure_message],
            capture_output=True,
            check=False,
        )

    # (b) Update gate_state=ABORTED in baton under gate.lock
    if test_mode:
        result = subprocess.run(
            ["python3", gate_lock_script, "--test-acquire", lock_path, "Daemon"],
            capture_output=True,
        )
    else:
        result = subprocess.run(
            ["python3", gate_lock_script, "--acquire", "Daemon"],
            capture_output=True,
        )
    lock_acquired = result.returncode == 0
    if not lock_acquired:
        print(
            f"[daemon T7] WARNING: gate.lock acquire failed — writing ABORTED without lock: "
            f"{result.stderr.decode(errors='replace').strip()}",
            file=sys.stderr,
        )

    try:
        _update_baton_gate_state(baton_path, "ABORTED")
        print("[daemon T7] INFO: gate_state updated to ABORTED", file=sys.stderr)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[daemon T7] WARNING: could not update baton gate_state: {exc}", file=sys.stderr)
    finally:
        if lock_acquired:
            if test_mode:
                subprocess.run(
                    ["python3", gate_lock_script, "--test-release", lock_path],
                    capture_output=True,
                )
            else:
                subprocess.run(
                    ["python3", gate_lock_script, "--release"],
                    capture_output=True,
                )

    # (d) Clean exit — launchd KeepAlive SuccessfulExit:false → NOT respawn
    print("[daemon T7] INFO: clean exit after ABORTED", file=sys.stderr)
    sys.exit(0)


# ---------------------------------------------------------------------------
# Baton validation
# ---------------------------------------------------------------------------

class BatonSchemaError(Exception):
    """Raised when baton JSON fails required-field validation."""


def _read_baton(baton_path: str) -> dict:
    """Read and parse baton.json. Raises OSError or json.JSONDecodeError on failure."""
    with open(baton_path, encoding="utf-8") as fh:
        return json.load(fh)


def _validate_baton(baton: dict) -> None:
    """Validate 7 required fields are present and non-null.

    Raises BatonSchemaError listing all missing/null fields.
    """
    bad: list[str] = []
    for field in BATON_REQUIRED_FIELDS:
        if field not in baton:
            bad.append(f"{field} (missing)")
        elif baton[field] is None:
            bad.append(f"{field} (null)")
    if bad:
        raise BatonSchemaError(f"baton schema invalid — bad fields: {', '.join(bad)}")


# ---------------------------------------------------------------------------
# T11 stale-lock reaper (placeholder — real impl in T-4-6)
# ---------------------------------------------------------------------------

def _run_stale_lock_reaper(watch_dir: str) -> None:
    """Invoke stale-lock reaper per design.md line 304.

    Delegates to lib/gate-lock.py --reap <lock_path> via subprocess
    per I-018 (symmetric Python actors, no inline reimplementation).
    Failure is non-fatal: log warning and continue so the daemon loop
    is not blocked by a reaper error.
    """
    lib_gate_lock = os.path.join(
        os.environ.get("CLAUDE_PLUGIN_ROOT")
        or os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "lib",
        "gate-lock.py",
    )
    gate_lock_path = os.path.join(watch_dir, ".teamlead", "gate.lock")
    try:
        result = subprocess.run(
            ["python3", lib_gate_lock, "--reap", gate_lock_path],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            print(
                f"[daemon reaper] WARNING: reap subprocess returned {result.returncode}:"
                f" {result.stderr.strip()}",
                file=sys.stderr,
            )
        elif "stale lock removed" in result.stderr.lower() or "reaped" in result.stdout.lower():
            print(
                f"[daemon reaper] INFO: stale lock removed at {gate_lock_path}",
                file=sys.stderr,
            )
    except (subprocess.TimeoutExpired, OSError) as exc:
        print(
            f"[daemon reaper] WARNING: reap subprocess failed (will retry next cycle): {exc}",
            file=sys.stderr,
        )


# ---------------------------------------------------------------------------
# restore_prompt allowlist validator (design.md §5 T-S-2)
# ---------------------------------------------------------------------------

def _validate_restore_prompt(prompt: str) -> bool:
    """Return True if restore_prompt passes the §5 T-S-2 allowlist check.

    Disallowed: backtick, bare '$', '${', NUL, control chars other than \\n/\\t,
    and content exceeding 8 KB.  Allowed: ASCII letters, digits, whitespace,
    common punctuation as listed in design.md §5 lines 628-630.
    """
    if len(prompt.encode("utf-8")) > _RESTORE_PROMPT_MAX_BYTES:
        return False
    # Reject shell-injection gadgets not caught by the char-class RE
    for banned in ("`", "${", "\x00"):
        if banned in prompt:
            return False
    # Bare dollar sign (covers $VAR and $(cmd))
    if "$" in prompt:
        return False
    # Reject control chars other than \n and \t
    for ch in prompt:
        cp = ord(ch)
        if cp < 0x20 and ch not in ("\n", "\t"):
            return False
    # Apply BMP allowlist regex (ASCII path + Unicode letters/punctuation)
    if not _RESTORE_PROMPT_ALLOWLIST_RE.match(prompt):
        return False
    return True


# ---------------------------------------------------------------------------
# T5 actor: BATON_WRITTEN → SESSION_RESUMED (design.md §1 T5, §4 step 7)
# ---------------------------------------------------------------------------

def _update_baton_gate_state(baton_path: str, new_state: str) -> None:
    """In-place update of gate_state in baton.json under gate.lock.

    Reads current baton, sets gate_state, writes atomically via tmp+replace.
    Per design.md §2 T5 cross-reference: daemon writes gate_state only.
    """
    with open(baton_path, encoding="utf-8") as fh:
        baton = json.load(fh)
    baton["gate_state"] = new_state
    tmp_path = baton_path + ".daemon_tmp"
    with open(tmp_path, "w", encoding="utf-8") as fh:
        json.dump(baton, fh, indent=2, ensure_ascii=False)
    os.replace(tmp_path, baton_path)


def _run_t5_actor(
    watch_dir: str,
    baton: dict,
    *,
    test_mode: bool = False,
) -> None:
    """Execute §1 T5: BATON_WRITTEN → SESSION_RESUMED.

    Steps (design.md §4 internal state machine step 7a-g):
      (a) Acquire gate.lock (subprocess lib/gate-lock.py --acquire Daemon)
      (b) Re-read baton to confirm gate_state == BATON_WRITTEN (double-check)
      (c) git stash safety net — probe + stash if dirty
      (d) Validate restore_prompt allowlist (§5 T-S-2)
      (e) Spawn claude --resume <session_id> -p <restore_prompt>  [test_mode: skip]
      (f) Update gate_state=SESSION_RESUMED in baton
      (g) Release gate.lock

    In --self-test-t5 mode (test_mode=True):
      - Skips actual subprocess.Popen spawn (no real claude invocation)
      - Skips gate.lock subprocess calls (uses direct --test-acquire/--test-release)
      - Still exercises allowlist + baton-update logic
    """
    baton_path = os.path.join(watch_dir, "baton.json")
    lock_path = os.path.join(watch_dir, "gate.lock")
    last_stash_path = os.path.join(watch_dir, "last-stash.txt")

    # Resolve lib/gate-lock.py path from CLAUDE_PLUGIN_ROOT or script parent
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if not plugin_root:
        plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gate_lock_script = os.path.join(plugin_root, "lib", "gate-lock.py")

    # (a) Acquire gate.lock — per design.md §4 step 7a / §3 lines 201-202
    if test_mode:
        # Use --test-acquire so no CLAUDE_PROJECT_DIR env is required
        result = subprocess.run(
            ["python3", gate_lock_script, "--test-acquire", lock_path, "Daemon"],
            capture_output=True,
        )
    else:
        result = subprocess.run(
            ["python3", gate_lock_script, "--acquire", "Daemon"],
            capture_output=True,
        )
    if result.returncode != 0:
        print(
            f"[daemon T5] WARNING: gate.lock acquire failed — skipping T5 (will retry): "
            f"{result.stderr.decode(errors='replace').strip()}",
            file=sys.stderr,
        )
        return

    lock_acquired = True
    try:
        # (b) Re-read baton under lock (double-check per §4 step 7b)
        try:
            with open(baton_path, encoding="utf-8") as fh:
                current_baton = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"[daemon T5] ERROR: re-read baton failed: {exc}", file=sys.stderr)
            return

        if current_baton.get("gate_state") != GATE_STATE_TRIGGER:
            print(
                f"[daemon T5] INFO: gate_state changed to "
                f"{current_baton.get('gate_state')!r} under lock — aborting T5",
                file=sys.stderr,
            )
            return

        session_id: str = current_baton["session_id"]
        restore_prompt: str = current_baton["restore_prompt"]

        # (c) git stash safety net (design.md §5 lines 642-671, §4 step 7c)
        project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
        if not project_dir and not test_mode:
            print(
                "[daemon T5] WARNING: CLAUDE_PROJECT_DIR not set — skipping git stash check",
                file=sys.stderr,
            )
        elif project_dir and not test_mode:
            # production-only: git stash has real side effects, skip in --self-test-t5
            try:
                status_result = subprocess.run(
                    ["git", "-C", project_dir, "status", "--porcelain"],
                    capture_output=True,
                    text=True,
                )
                if status_result.returncode == 0 and status_result.stdout.strip():
                    # Working tree is dirty — stash it
                    iso_now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                    stash_msg = f"teamlead-resume-{session_id}-{iso_now}"
                    stash_result = subprocess.run(
                        [
                            "git",
                            "-C",
                            project_dir,
                            "stash",
                            "push",
                            "-u",
                            "-m",
                            stash_msg,
                        ],
                        capture_output=True,
                        text=True,
                    )
                    if stash_result.returncode == 0:
                        # Record stash ref for recovery audit (design.md §5 line 654)
                        stash_ref = "stash@{0}"
                        try:
                            os.makedirs(os.path.dirname(last_stash_path), exist_ok=True)
                            with open(last_stash_path, "w", encoding="utf-8") as fh:
                                fh.write(stash_ref + "\n")
                        except OSError as exc:
                            print(
                                f"[daemon T5] WARNING: could not write last-stash.txt: {exc}",
                                file=sys.stderr,
                            )
                        print(
                            f"[daemon T5] INFO: git stash pushed: {stash_msg}",
                            file=sys.stderr,
                        )
                    else:
                        print(
                            f"[daemon T5] WARNING: git stash failed: "
                            f"{stash_result.stderr.strip()}",
                            file=sys.stderr,
                        )
            except OSError as exc:
                print(f"[daemon T5] WARNING: git stash probe failed: {exc}", file=sys.stderr)

        # (d) Validate restore_prompt allowlist (design.md §5 T-S-2, §4 step 7d)
        if not _validate_restore_prompt(restore_prompt):
            print(
                "[daemon T5] ERROR: restore_prompt failed allowlist check — T7 abort path",
                file=sys.stderr,
            )
            # Stub abort callback (T7 abort path belongs to T-4-5)
            return

        # (e) Spawn claude --resume <session_id> -p <restore_prompt>
        #     Per design.md §4 lines 497-510 — non-blocking Popen.
        #     In test_mode (--self-test-t5 or --self-test-t6-exhaust): no actual spawn.
        #     T6 retry (design.md lines 135 Q3 / line 81): up to T6_MAX_RETRIES attempts
        #     with exponential backoff 1s/4s/16s (test: 1ms each).
        if not test_mode:
            cmd = ["claude", "--resume", session_id, "-p", restore_prompt]
            project_dir_for_spawn = project_dir or os.path.expanduser("~")
            retry_path = _retry_counter_path()
            backoff_sequence = T6_BACKOFF_SECONDS
            spawn_succeeded = False

            for attempt in range(T6_MAX_RETRIES):
                if attempt > 0:
                    delay = backoff_sequence[attempt]
                    print(
                        f"[daemon T6] INFO: retry {attempt}/{T6_MAX_RETRIES - 1} "
                        f"— sleeping {delay}s before spawn",
                        file=sys.stderr,
                    )
                    time.sleep(delay)
                try:
                    proc = subprocess.Popen(cmd, cwd=project_dir_for_spawn)
                    # Wait briefly to detect immediate non-zero exit
                    try:
                        exit_code = proc.wait(timeout=2.0)
                    except subprocess.TimeoutExpired:
                        # Process still running — treat as success (expected long-lived)
                        exit_code = 0
                    if exit_code != 0:
                        raise subprocess.CalledProcessError(exit_code, cmd)
                    spawn_succeeded = True
                    print(
                        f"[daemon T5] INFO: spawned claude --resume {session_id} (pid={proc.pid})",
                        file=sys.stderr,
                    )
                    # Clear retry counter on success
                    _write_retry_counter(retry_path, 0)
                    break
                except (FileNotFoundError, subprocess.CalledProcessError, OSError) as exc:
                    current_count = attempt + 1
                    _write_retry_counter(retry_path, current_count)
                    print(
                        f"[daemon T6] WARNING: spawn attempt {current_count}/{T6_MAX_RETRIES} "
                        f"failed: {exc}",
                        file=sys.stderr,
                    )

            if not spawn_succeeded:
                print(
                    f"[daemon T6] ERROR: retry {T6_MAX_RETRIES} exhausted",
                    file=sys.stderr,
                )
                _enter_aborted(
                    f"claude spawn failed after {T6_MAX_RETRIES} retries",
                    watch_dir,
                    test_mode=False,
                )
                return  # unreachable; _enter_aborted calls sys.exit(0)
        else:
            print(
                f"[daemon T5] INFO: --self-test-t5: skip spawn, simulating SESSION_RESUMED",
                file=sys.stderr,
            )

        # (f) Update gate_state=SESSION_RESUMED in baton
        _update_baton_gate_state(baton_path, GATE_STATE_RESUMED)
        print(
            "[daemon T5] INFO: gate_state updated to SESSION_RESUMED",
            file=sys.stderr,
        )

    finally:
        # (g) Release gate.lock — always, even on error paths above
        if lock_acquired:
            if test_mode:
                subprocess.run(
                    ["python3", gate_lock_script, "--test-release", lock_path],
                    capture_output=True,
                )
            else:
                subprocess.run(
                    ["python3", gate_lock_script, "--release"],
                    capture_output=True,
                )


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="daemon.py",
        description="teamwork-leader auto-resume daemon",
    )
    # I-065: --self-test-* flags (t5, t6-exhaust, t7-abort, pid, reaper) are independent
    # single-shot test paths; combining two simultaneously is undefined behavior.
    # argparse mutually_exclusive_group was considered but omitted because _run_test_mode()
    # resolves priority via early-return ordering (reaper > pid > t6 > t5 > t7), making
    # mutual-exclusion enforcement redundant in practice.  Formalizing via
    # add_mutually_exclusive_group is deferred to v0.1.8+ for cleaner operator UX.
    parser.add_argument(
        "--watch",
        metavar="DIR",
        required=True,
        help="Directory to watch for baton.json changes",
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help=(
            "Read baton at --watch <dir>/baton.json, validate fields, "
            "print gate_state=<value> or schema=valid, then exit 0 "
            "without spawning claude"
        ),
    )
    parser.add_argument(
        "--self-test-t5",
        action="store_true",
        help=(
            "Simulate T5 (BATON_WRITTEN → SESSION_RESUMED) without actual claude spawn. "
            "Requires --test-mode. Writes gate_state=SESSION_RESUMED to baton. "
            "Downstream: --self-test-t6-exhaust, --self-test-t7 follow same sub-flag naming pattern."
        ),
    )
    parser.add_argument(
        "--self-test-t6-exhaust",
        action="store_true",
        help=(
            "Simulate T6 retry exhaustion: 3 failed spawn attempts with truncated backoff "
            "(1ms per attempt instead of 1s/4s/16s). "
            "Requires --test-mode. Increments daemon-retries counter to 3 then enters real T7 ABORTED path. "
            "Writes last-resume-failure.txt + sets gate_state=ABORTED + exits 0."
        ),
    )
    parser.add_argument(
        "--self-test-t7-abort",
        action="store_true",
        help=(
            "Simulate T7 ABORTED path directly: write last-resume-failure.txt to test dir, "
            "set gate_state=ABORTED in baton, exit 0. "
            "Requires --test-mode. Does NOT fire osascript. "
            "Per I-051: dash-connected naming convention."
        ),
    )
    parser.add_argument(
        "--self-test-pid",
        action="store_true",
        help=(
            "Verify PID file lifecycle: write pid (already done by main before this flag is "
            "checked), verify file exists, verify content == os.getpid(), verify 0600 perms, "
            "print pid-file=<path> and perms=0600, then exit 0. "
            "Pid file is NOT removed on exit (design.md §3.12 line 519). "
            "Requires --test-mode. Does NOT require baton.json. "
            "Per I-051: dash-connected naming convention."
        ),
    )
    parser.add_argument(
        "--self-test-reaper",
        action="store_true",
        help=(
            "Invoke _run_stale_lock_reaper() against --watch dir and exit 0. "
            "Emits a grep-able signal line to stderr. "
            "Requires --test-mode. Does NOT require baton.json. "
            "Per I-051: dash-connected naming convention."
        ),
    )
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# Test-mode path
# ---------------------------------------------------------------------------

def _run_test_mode(
    watch_dir: str,
    *,
    self_test_t5: bool = False,
    self_test_t6_exhaust: bool = False,
    self_test_t7_abort: bool = False,
    self_test_pid: bool = False,
    self_test_reaper: bool = False,
) -> int:
    """--test-mode: single-shot read + validate + print, no spawn.

    Prints gate_state=<value> if gate_state field present.
    Prints schema=valid if all 7 required fields pass.
    If --self-test-reaper: invoke _run_stale_lock_reaper(watch_dir), print verify
    signal, exit 0. Does NOT require baton.json.
    If --self-test-pid: verify pid file written by main() — file exists, content ==
    os.getpid(), perms 0600, print pid-file=<path> and perms=0600, exit 0.
    Pid file is NOT removed on exit (design.md §3.12 line 519). Does NOT require baton.
    If --self-test-t5: additionally runs T5 actor in simulation mode
    (gate acquire/release via --test-acquire/--test-release, no claude spawn).
    If --self-test-t6-exhaust: simulates 3 failed spawn attempts with truncated
    backoff (1ms each), increments daemon-retries counter to T6_MAX_RETRIES,
    then enters real T7 ABORTED path (writes failure file + sets gate_state=ABORTED + exits 0).
    If --self-test-t7-abort: directly exercises T7 ABORTED path (write failure file,
    set gate_state=ABORTED, exit 0) without going through T5/T6 first.
    Exits 0 on success, 1 on read/parse/schema error.
    """
    # --self-test-reaper: invoke stale-lock reaper and exit; no baton required.
    if self_test_reaper:
        _run_stale_lock_reaper(watch_dir)
        print(
            f"[daemon --self-test-reaper] reaper invoked for {watch_dir}",
            file=sys.stderr,
        )
        return 0

    # --self-test-pid: verify pid file written by main(); no baton required.
    if self_test_pid:
        pid_path = _pid_path()
        # Verify file exists
        if not os.path.exists(pid_path):
            print(
                f"[daemon --self-test-pid] FAIL: pid file not found at {pid_path}",
                file=sys.stderr,
            )
            return 1
        # Verify content == os.getpid()
        with open(pid_path, encoding="utf-8") as fh:
            content = fh.read().strip()
        expected_pid = str(os.getpid())
        if content != expected_pid:
            print(
                f"[daemon --self-test-pid] FAIL: pid file content {content!r} != {expected_pid!r}",
                file=sys.stderr,
            )
            return 1
        # Verify 0600 perms
        mode = oct(os.stat(pid_path).st_mode & 0o777)
        if mode != "0o600":
            print(
                f"[daemon --self-test-pid] FAIL: perms {mode} != 0o600",
                file=sys.stderr,
            )
            return 1
        # All checks passed; pid file left in place (NOT removed — design.md §3.12 line 519)
        print(f"pid-file={pid_path}")
        print("perms=0600")
        print(f"[daemon --self-test-pid] PASS: pid={expected_pid} file={pid_path} perms=0600")
        return 0

    baton_path = os.path.join(watch_dir, "baton.json")
    try:
        baton = _read_baton(baton_path)
    except FileNotFoundError:
        print(f"[daemon --test-mode] ERROR: baton not found at {baton_path}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"[daemon --test-mode] ERROR: baton JSON parse error: {exc}", file=sys.stderr)
        return 1

    # Print gate_state first (verify clause expects this in output)
    gate_state = baton.get("gate_state")
    if gate_state is not None:
        print(f"gate_state={gate_state}")

    # Validate required fields
    try:
        _validate_baton(baton)
    except BatonSchemaError as exc:
        print(f"[daemon --test-mode] schema=invalid: {exc}", file=sys.stderr)
        return 1

    print("schema=valid")

    if self_test_t6_exhaust:
        # Simulate T6 retry exhaustion: 3 failed spawns with truncated backoff.
        # gate_state must be BATON_WRITTEN to exercise the correct code path.
        if gate_state != GATE_STATE_TRIGGER:
            print(
                f"[daemon --self-test-t6-exhaust] ERROR: gate_state must be {GATE_STATE_TRIGGER!r}, "
                f"got {gate_state!r}",
                file=sys.stderr,
            )
            return 1
        retry_path = _retry_counter_path()
        for attempt in range(T6_MAX_RETRIES):
            delay = T6_BACKOFF_SECONDS_TEST[attempt]
            if attempt > 0:
                print(
                    f"[daemon T6] INFO: retry {attempt}/{T6_MAX_RETRIES - 1} "
                    f"— sleeping {delay}s before spawn",
                    file=sys.stderr,
                )
                time.sleep(delay)
            current_count = attempt + 1
            _write_retry_counter(retry_path, current_count)
            print(
                f"[daemon T6] WARNING: spawn attempt {current_count}/{T6_MAX_RETRIES} "
                f"failed: simulated failure (--self-test-t6-exhaust)",
                file=sys.stderr,
            )
        print(
            f"[daemon T6] ERROR: retry {T6_MAX_RETRIES} exhausted",
            file=sys.stderr,
        )
        # Print retry_counter before entering T7 (which calls sys.exit(0))
        final_count = _read_retry_counter(retry_path)
        print(f"[daemon --self-test-t6-exhaust] retry_counter={final_count}")
        _enter_aborted(
            f"claude spawn failed after {T6_MAX_RETRIES} retries",
            watch_dir,
            test_mode=True,
        )
        return 0  # unreachable; _enter_aborted calls sys.exit(0)

    if self_test_t5:
        # Run T5 actor in simulation mode (no actual claude spawn)
        if gate_state != GATE_STATE_TRIGGER:
            print(
                f"[daemon --self-test-t5] ERROR: gate_state must be {GATE_STATE_TRIGGER!r} "
                f"for T5 simulation, got {gate_state!r}",
                file=sys.stderr,
            )
            return 1
        _run_t5_actor(watch_dir, baton, test_mode=True)
        # Verify the baton was updated
        try:
            updated = _read_baton(baton_path)
        except (OSError, json.JSONDecodeError) as exc:
            print(
                f"[daemon --self-test-t5] ERROR: could not re-read baton after T5: {exc}",
                file=sys.stderr,
            )
            return 1
        if updated.get("gate_state") != GATE_STATE_RESUMED:
            print(
                f"[daemon --self-test-t5] ERROR: expected gate_state={GATE_STATE_RESUMED!r}, "
                f"got {updated.get('gate_state')!r}",
                file=sys.stderr,
            )
            return 1
        print(f"[daemon --self-test-t5] gate_state={GATE_STATE_RESUMED}")

    if self_test_t7_abort:
        # Directly exercise T7 ABORTED path without going through T5/T6 first.
        # Writes failure file to watch_dir/.teamlead/, sets gate_state=ABORTED.
        # Per spec (e): --test-mode --self-test-t7-abort
        _enter_aborted(
            "self-test-t7-abort: direct T7 exercise",
            watch_dir,
            test_mode=True,
        )
        return 0  # unreachable; _enter_aborted calls sys.exit(0)

    return 0


# ---------------------------------------------------------------------------
# Main daemon loop
# ---------------------------------------------------------------------------

def _daemon_loop(watch_dir: str) -> int:
    """Infinite poll loop: check baton.json mtime every 5 s.

    On mtime change:
    1. Run stale-lock reaper (T-4-6 placeholder).
    2. Read + validate baton schema.
    3. Check gate_state == BATON_WRITTEN.
    4. Hand off to T5 actor (T-4-3, not implemented here).
    """
    baton_path = os.path.join(watch_dir, "baton.json")
    last_mtime: float | None = None

    while True:
        # T11 stale-lock reaper — runs before each acquire attempt per design.md line 304
        _run_stale_lock_reaper(watch_dir)

        try:
            current_mtime = os.stat(baton_path).st_mtime
        except FileNotFoundError:
            # baton.json not yet written; reset last_mtime so we catch first write
            last_mtime = None
            time.sleep(POLL_INTERVAL_SECONDS)
            continue

        if current_mtime == last_mtime:
            time.sleep(POLL_INTERVAL_SECONDS)
            continue

        # mtime changed — baton was written or updated. Defer last_mtime
        # update until after successful read+validate so a mid-write
        # JSONDecodeError leaves last_mtime unchanged and the next poll
        # retries (S4-D2 step-review major fix; design.md mid-write recovery).

        try:
            baton = _read_baton(baton_path)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"[daemon] WARNING: baton read error (will retry): {exc}", file=sys.stderr)
            time.sleep(POLL_INTERVAL_SECONDS)
            continue

        try:
            _validate_baton(baton)
        except BatonSchemaError as exc:
            print(f"[daemon] WARNING: {exc} (ignoring baton)", file=sys.stderr)
            # Schema-invalid baton is NOT retriable via mtime; advance last_mtime
            # to prevent re-validating the same bad baton on every poll.
            last_mtime = current_mtime
            time.sleep(POLL_INTERVAL_SECONDS)
            continue

        # Read + validate succeeded; commit last_mtime so we don't reprocess.
        last_mtime = current_mtime

        gate_state = baton.get("gate_state")
        if gate_state != GATE_STATE_TRIGGER:
            # Ignore non-BATON_WRITTEN states per design.md line 64
            print(
                f"[daemon] INFO: gate_state={gate_state!r} — not BATON_WRITTEN, ignoring",
                file=sys.stderr,
            )
            time.sleep(POLL_INTERVAL_SECONDS)
            continue

        # gate_state == BATON_WRITTEN — hand off to T5 actor (T-4-3)
        print(
            f"[daemon] INFO: gate_state=BATON_WRITTEN detected — running T5 actor",
            file=sys.stderr,
        )
        _run_t5_actor(watch_dir, baton)
        time.sleep(POLL_INTERVAL_SECONDS)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    args = _parse_args(argv)

    pid_path = _pid_path()
    _write_pid(pid_path)

    if args.test_mode:
        return _run_test_mode(
            args.watch,
            self_test_t5=args.self_test_t5,
            self_test_t6_exhaust=args.self_test_t6_exhaust,
            self_test_t7_abort=args.self_test_t7_abort,
            self_test_pid=args.self_test_pid,
            self_test_reaper=args.self_test_reaper,
        )

    return _daemon_loop(args.watch)


if __name__ == "__main__":
    sys.exit(main())
