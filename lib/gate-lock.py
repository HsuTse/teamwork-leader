#!/usr/bin/env python3
"""
lib/gate-lock.py — Gate lock acquire/release.

Purpose: Manages exclusive gate.lock file to serialize baton write operations.
Acquire uses Python os.open(O_CREAT|O_EXCL|O_WRONLY, 0o600) for kernel-level
atomic create-or-fail (avoids flock shell-quoting bugs; per I-009).
Lock-file JSON: { pid, acquired_at, holder_role } (3 required fields).
Release calls os.unlink(gate.lock) AFTER baton atomic rename.
Liveness probe: os.kill(pid, 0) raises ProcessLookupError -> stale-lock recovery.
Stale-lock reaper quarantines baton.json.tmp to baton.json.tmp.quarantined-<ISO>.
Default TTL: 90 seconds (per design.md §3 line 290).

Spec references:
  design.md §3 lines 260-267  — lock-file JSON 3 required fields
  design.md §3 lines 272-279  — O_CREAT|O_EXCL atomic acquire
  design.md §3 line 281       — release ordering (unlink AFTER baton rename)
  design.md §3 lines 283-290  — stale-lock recovery + TTL + 3 criteria
  design.md §3 line 291       — daemon.pid sidecar (daemon.py self-write)
  Stage 1 I-009               — Python O_EXCL > shell flock
  Opus PLAN_AUDIT Q9          — T11 reaper quarantines baton.json.tmp
Implementation task: T-3-3.
"""

import json
import os
import sys
from datetime import datetime, timezone
from typing import Optional

DEFAULT_TTL_SECONDS: int = 90
REQUIRED_FIELDS: set = {"pid", "acquired_at", "holder_role"}


def _iso_now() -> str:
    """Return current UTC time as ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _write_lock(fd: int, holder_role: str) -> None:
    """Write JSON lock content to an already-open file descriptor."""
    payload = {
        "pid": os.getpid(),
        "acquired_at": _iso_now(),
        "holder_role": holder_role,
        "ttl_seconds": DEFAULT_TTL_SECONDS,
    }
    data = json.dumps(payload, indent=2).encode()
    os.write(fd, data)
    os.fsync(fd)
    os.close(fd)


def _read_lock(lock_path: str) -> Optional[dict]:
    """Read and parse lock file; return None if missing/corrupt."""
    try:
        with open(lock_path, "r") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _is_stale(lock_data: dict, lock_dir: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> tuple[bool, str]:
    """
    Evaluate the 3 staleness criteria from design.md §3 lines 283-291.
    Returns (is_stale, reason).
    """
    pid = lock_data.get("pid")
    acquired_at_str = lock_data.get("acquired_at")
    holder_role = lock_data.get("holder_role")

    # Validate required fields; corrupt lock treated as stale.
    if not REQUIRED_FIELDS.issubset(lock_data.keys()):
        return True, "corrupt_lock"

    # Criterion 1: TTL expiry
    try:
        acquired_at = datetime.fromisoformat(acquired_at_str)
        now = datetime.now(timezone.utc)
        if acquired_at.tzinfo is None:
            # Treat naive timestamps as UTC
            acquired_at = acquired_at.replace(tzinfo=timezone.utc)
        age_seconds = (now - acquired_at).total_seconds()
        if age_seconds > ttl_seconds:
            return True, "ttl_expired"
    except (ValueError, TypeError):
        return True, "corrupt_lock"

    # Criterion 2: Dead holder — signal 0 probe
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True, "dead_holder"
    except PermissionError:
        # EPERM: holder alive, owned by another UID; treat as alive per design.md
        pass

    # Criterion 3: Role/process mismatch for Daemon role
    if holder_role == "Daemon":
        daemon_pid_path = os.path.join(lock_dir, "daemon.pid")
        try:
            with open(daemon_pid_path, "r") as f:
                daemon_pid = int(f.read().strip())
            if daemon_pid != pid:
                return True, "role_mismatch"
        except (OSError, ValueError):
            # daemon.pid not yet written (Stage 4); skip criterion in that case
            pass

    return False, ""


def _quarantine_torn_tmp(lock_dir: str) -> None:
    """
    Quarantine baton.json.tmp if present (Opus PLAN_AUDIT Q9 / T11 reaper).
    Renames to baton.json.tmp.quarantined-<ISO> instead of unlinking,
    preserving forensic evidence for operator review.
    """
    tmp_path = os.path.join(lock_dir, "baton.json.tmp")
    if os.path.exists(tmp_path):
        iso = _iso_now().replace(":", "-")
        quarantine_path = f"{tmp_path}.quarantined-{iso}"
        os.rename(tmp_path, quarantine_path)


def _log_reaper_action(
    lock_dir: str,
    prior_lock: dict,
    reason: str,
    new_holder_pid: Optional[int],
) -> None:
    """Write single-record reaper log to last-reaper-action.json."""
    log = {
        "reaper_at": _iso_now(),
        "prior_holder": {
            "pid": prior_lock.get("pid"),
            "holder_role": prior_lock.get("holder_role"),
            "acquired_at": prior_lock.get("acquired_at"),
        },
        "reason": reason,
        "new_holder_pid": new_holder_pid,
    }
    log_path = os.path.join(lock_dir, "last-reaper-action.json")
    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)


def acquire(lock_path: str, holder_role: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> bool:
    """
    Acquire gate.lock at lock_path with holder_role.
    Uses O_CREAT|O_EXCL for kernel-level atomic create-or-fail (I-009).
    On FileExistsError: probe liveness + invoke stale-lock recovery if stale.
    Returns True on successful acquire; False if lock is held by live holder.
    """
    lock_dir = os.path.dirname(lock_path) or "."
    os.makedirs(lock_dir, exist_ok=True)

    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        _write_lock(fd, holder_role)
        return True
    except FileExistsError:
        pass

    # Lock file exists; check staleness
    lock_data = _read_lock(lock_path)
    if lock_data is None:
        # Corrupt / empty file: attempt unlink + retry
        try:
            os.unlink(lock_path)
        except OSError:
            pass
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            _write_lock(fd, holder_role)
            return True
        except FileExistsError:
            return False

    stale, reason = _is_stale(lock_data, lock_dir, ttl_seconds)
    if stale:
        _log_reaper_action(lock_dir, lock_data, reason, os.getpid())
        try:
            os.unlink(lock_path)
        except OSError:
            pass
        _quarantine_torn_tmp(lock_dir)
        # Retry acquire after stale recovery
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            _write_lock(fd, holder_role)
            return True
        except FileExistsError:
            return False

    return False


def release(lock_path: str) -> None:
    """
    Release gate.lock at lock_path.
    Per design.md line 281: caller MUST have already completed the baton
    atomic rename before calling this. Unlink is best-effort; missing lock
    on release is not an error (idempotent).
    """
    try:
        os.unlink(lock_path)
    except FileNotFoundError:
        pass


def reap(lock_path: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> bool:
    """
    T11 reaper: scan lock_path; if stale, unlink + quarantine baton.json.tmp.
    Returns True if reaping occurred; False if lock is absent or live.
    """
    if not os.path.exists(lock_path):
        return False

    lock_dir = os.path.dirname(lock_path) or "."
    lock_data = _read_lock(lock_path)
    if lock_data is None:
        # Corrupt lock; unlink
        try:
            os.unlink(lock_path)
        except OSError:
            pass
        _quarantine_torn_tmp(lock_dir)
        return True

    stale, reason = _is_stale(lock_data, lock_dir, ttl_seconds)
    if stale:
        _log_reaper_action(lock_dir, lock_data, reason, None)
        try:
            os.unlink(lock_path)
        except OSError:
            pass
        _quarantine_torn_tmp(lock_dir)
        return True

    return False


def _resolve_production_lock_path() -> str:
    """Resolve production gate.lock path from CLAUDE_PROJECT_DIR env var."""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not project_dir:
        print("ERROR: CLAUDE_PROJECT_DIR not set", file=sys.stderr)
        sys.exit(1)
    return os.path.join(project_dir, ".teamlead", "gate.lock")


def _self_test() -> None:
    """
    Self-test: round-trip acquire + verify JSON + O_EXCL conflict + release.
    Exits 0 on success; non-zero on any failure.
    """
    import tempfile

    with tempfile.TemporaryDirectory() as tmp_dir:
        lock_path = os.path.join(tmp_dir, "gate.lock")

        # --- Test 1: Basic acquire ---
        ok = acquire(lock_path, "PreCompact")
        assert ok, "Self-test FAIL: acquire returned False on fresh lock"

        # --- Test 2: JSON fields ---
        lock_data = _read_lock(lock_path)
        assert lock_data is not None, "Self-test FAIL: lock file unreadable"
        assert REQUIRED_FIELDS.issubset(lock_data.keys()), (
            f"Self-test FAIL: missing required fields; got {set(lock_data.keys())}"
        )
        assert lock_data["holder_role"] == "PreCompact", "Self-test FAIL: wrong holder_role"
        assert lock_data["pid"] == os.getpid(), "Self-test FAIL: wrong pid"

        # --- Test 3: O_EXCL conflict — second acquire must fail ---
        ok2 = acquire(lock_path, "Daemon")
        assert not ok2, "Self-test FAIL: second acquire succeeded (O_EXCL not enforced)"

        # --- Test 4: Release ---
        release(lock_path)
        assert not os.path.exists(lock_path), "Self-test FAIL: lock still present after release"

        # --- Test 5: TTL expiry triggers reap ---
        # Write a lock with an old acquired_at
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        stale_payload = {
            "pid": os.getpid(),
            "acquired_at": "2000-01-01T00:00:00+00:00",
            "holder_role": "PreCompact",
        }
        os.write(fd, json.dumps(stale_payload).encode())
        os.fsync(fd)
        os.close(fd)

        reaped = reap(lock_path)
        assert reaped, "Self-test FAIL: reap returned False on TTL-expired lock"
        assert not os.path.exists(lock_path), "Self-test FAIL: stale lock not removed by reap"

        # --- Test 6: Quarantine of baton.json.tmp ---
        # Pre-create a torn tmp artifact
        tmp_baton = os.path.join(tmp_dir, "baton.json.tmp")
        with open(tmp_baton, "w") as f:
            f.write('{"partial": true}')

        # Write stale lock again
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.write(fd, json.dumps(stale_payload).encode())
        os.fsync(fd)
        os.close(fd)

        reap(lock_path)

        # baton.json.tmp must be renamed to quarantined-*, NOT deleted
        assert not os.path.exists(tmp_baton), (
            "Self-test FAIL: baton.json.tmp still present (should be renamed)"
        )
        quarantine_files = [
            f for f in os.listdir(tmp_dir) if f.startswith("baton.json.tmp.quarantined-")
        ]
        assert len(quarantine_files) == 1, (
            f"Self-test FAIL: expected 1 quarantine file, found {quarantine_files}"
        )

    print("Self-test PASS", file=sys.stderr)


def main() -> None:
    """CLI entry point for gate-lock.py."""
    args = sys.argv[1:]

    if not args:
        print(
            "Usage:\n"
            "  gate-lock.py --acquire <holder_role>              # production acquire\n"
            "  gate-lock.py --release                            # production release\n"
            "  gate-lock.py --test-acquire <path> <holder_role>  # test acquire at path\n"
            "  gate-lock.py --test-release <path>                # test release at path\n"
            "  gate-lock.py --reap [<lock_path>]                 # reap stale lock (path optional; default: env-var)\n"
            "  gate-lock.py --self-test                          # self-test suite",
            file=sys.stderr,
        )
        sys.exit(1)

    cmd = args[0]

    if cmd == "--acquire":
        if len(args) < 2:
            print("ERROR: --acquire requires <holder_role>", file=sys.stderr)
            sys.exit(1)
        lock_path = _resolve_production_lock_path()
        ok = acquire(lock_path, args[1])
        if not ok:
            print(f"ERROR: gate.lock held by live process; cannot acquire", file=sys.stderr)
            sys.exit(1)

    elif cmd == "--release":
        lock_path = _resolve_production_lock_path()
        release(lock_path)

    elif cmd == "--test-acquire":
        if len(args) < 3:
            print("ERROR: --test-acquire requires <path> <holder_role>", file=sys.stderr)
            sys.exit(1)
        ok = acquire(args[1], args[2])
        if not ok:
            print(f"ERROR: gate.lock at {args[1]} held by live process", file=sys.stderr)
            sys.exit(1)

    elif cmd == "--test-release":
        if len(args) < 2:
            print("ERROR: --test-release requires <path>", file=sys.stderr)
            sys.exit(1)
        release(args[1])

    elif cmd == "--reap":
        # Accept optional explicit lock_path arg (design.md line 304; T-4-6 / I-049).
        # Falls back to env-var production path when no arg supplied (existing behaviour).
        if len(args) >= 2:
            lock_path = args[1]
        else:
            lock_path = _resolve_production_lock_path()
        reaped = reap(lock_path)
        if reaped:
            print("Reaper: stale lock removed", file=sys.stderr)
        else:
            print("Reaper: no stale lock found", file=sys.stderr)

    elif cmd == "--self-test":
        _self_test()

    else:
        print(f"ERROR: unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
