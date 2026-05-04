#!/usr/bin/env python3
"""
lib/baton-writer.py — Atomic baton write (transparent transport).

Purpose: Reads JSON payload from stdin, validates all 7 required keys are
present and non-null, enforces ≤ 1 MB size cap, then atomically writes the
baton via os.open(O_WRONLY|O_CREAT|O_EXCL, 0o600) + os.replace().
Sets 0600 permissions immediately after rename.

This script is a transparent atomic-write transport only.
Field assembly is the responsibility of the pre-compact orchestrator
(hooks/pre-compact.py) and handoff-builder (lib/handoff-builder.py).

Required keys: session_id, prior_pause_commit, branch, last_action_iso,
               progress_md_anchor, restore_prompt, auto_mode_resumed.

Spec reference: design.md §2 lines 155-157, 165-172, 183-185.
Implementation task: T-3-2.

CLI signature:
  python3 lib/baton-writer.py < payload.json
      Production mode: read from stdin, write to $CLAUDE_PROJECT_DIR/.teamlead/baton.json

  python3 lib/baton-writer.py --test-write /tmp/path.json < payload.json
      Test mode: read from stdin, write to specified path

  python3 lib/baton-writer.py --self-test
      Self-test mode: synthesize valid 7-key fixture payload and write to
      /tmp/baton-self-test.json; exits 0 on success.
"""
import json
import os
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from typing import Any

# 7 required keys per design.md §2 lines 165-172
REQUIRED_KEYS: list[str] = [
    "session_id",
    "prior_pause_commit",
    "branch",
    "last_action_iso",
    "progress_md_anchor",
    "restore_prompt",
    "auto_mode_resumed",
]

# Chosen design cap: 1 MB (design.md §2 lines 183-185, FV-T-1-7 line 587)
MAX_PAYLOAD_BYTES: int = 1 * 1024 * 1024  # 1 MB

# Self-test output path
SELF_TEST_OUTPUT: str = "/tmp/baton-self-test.json"


def _validate_keys(payload: dict[str, Any]) -> None:
    """Assert all 7 required keys are present and non-null.

    Raises SystemExit(1) with a descriptive message if any key is missing
    or has a null value. Key-presence-only validation per Q8 resolution
    (no type coercion).
    """
    missing: list[str] = []
    null_valued: list[str] = []
    for key in REQUIRED_KEYS:
        if key not in payload:
            missing.append(key)
        elif payload[key] is None:
            null_valued.append(key)

    if missing or null_valued:
        errors: list[str] = []
        if missing:
            errors.append(f"missing keys: {missing}")
        if null_valued:
            errors.append(f"null-valued keys: {null_valued}")
        print(
            f"[baton-writer] ERROR: payload validation failed — {'; '.join(errors)}",
            file=sys.stderr,
        )
        sys.exit(1)


def _atomic_write(payload_bytes: bytes, dest_path: str) -> None:
    """Atomically write payload_bytes to dest_path.

    Protocol (design.md §2 lines 155-157):
    1. Write to dest_path + '.tmp' via os.open(O_WRONLY|O_CREAT|O_EXCL, 0o600)
       to avoid TOCTOU window.
    2. os.replace(tmp, dest) — POSIX atomic rename on same filesystem.
    3. os.chmod(dest, 0o600) immediately after rename (before gate.lock release).

    Raises SystemExit(1) on any OS error; does NOT leave .tmp behind on failure
    (unlinks on error path).
    """
    dest_dir = os.path.dirname(os.path.abspath(dest_path))
    os.makedirs(dest_dir, exist_ok=True)

    tmp_path = dest_path + ".tmp"

    # Open with O_EXCL to detect pre-existing torn tmp; unlink it first if stale.
    # The reaper (T11 / gate-lock.py) handles quarantine; here we simply replace.
    try:
        fd = os.open(
            tmp_path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
    except FileExistsError:
        # Stale .tmp from a prior torn write; remove and retry once.
        try:
            os.unlink(tmp_path)
        except OSError as exc:
            print(
                f"[baton-writer] ERROR: could not remove stale tmp {tmp_path!r}: {exc}",
                file=sys.stderr,
            )
            sys.exit(1)
        try:
            fd = os.open(
                tmp_path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
        except OSError as exc:
            print(
                f"[baton-writer] ERROR: could not open tmp {tmp_path!r}: {exc}",
                file=sys.stderr,
            )
            sys.exit(1)
    except OSError as exc:
        print(
            f"[baton-writer] ERROR: could not open tmp {tmp_path!r}: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Write payload bytes to tmp file; unlink on any write error.
    try:
        os.write(fd, payload_bytes)
    except OSError as exc:
        os.close(fd)
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        print(
            f"[baton-writer] ERROR: write to tmp failed: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)
    finally:
        try:
            os.close(fd)
        except OSError:
            pass

    # Atomic rename: tmp → dest (design.md line 157)
    try:
        os.replace(tmp_path, dest_path)
    except OSError as exc:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        print(
            f"[baton-writer] ERROR: atomic rename failed: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Set 0600 immediately after rename (design.md line 156)
    try:
        os.chmod(dest_path, 0o600)
    except OSError as exc:
        print(
            f"[baton-writer] WARNING: chmod 0600 on {dest_path!r} failed: {exc}",
            file=sys.stderr,
        )
        # Non-fatal warning; write already committed atomically.


def write_baton(payload: dict[str, Any], dest_path: str) -> None:
    """Validate payload and atomically write to dest_path.

    Steps:
    1. Validate 7 required keys present + non-null (exits 1 on failure).
    2. Serialize to JSON bytes.
    3. Enforce ≤ 1 MB size cap (exits 1 if exceeded).
    4. Atomic write via _atomic_write().
    """
    # Step 1: key-presence + non-null validation
    _validate_keys(payload)

    # Step 2: serialize
    try:
        payload_bytes = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    except (TypeError, ValueError) as exc:
        print(
            f"[baton-writer] ERROR: JSON serialization failed: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Step 3: size cap enforcement (design.md lines 183-185)
    if len(payload_bytes) > MAX_PAYLOAD_BYTES:
        print(
            f"[baton-writer] ERROR: payload size {len(payload_bytes)} bytes exceeds "
            f"1 MB cap ({MAX_PAYLOAD_BYTES} bytes); aborting write.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Step 4: atomic write
    _atomic_write(payload_bytes, dest_path)
    print(
        f"[baton-writer] baton written to {dest_path!r} "
        f"({len(payload_bytes)} bytes, 0600)",
        file=sys.stderr,
    )


def _default_dest_path() -> str:
    """Resolve default production baton path from $CLAUDE_PROJECT_DIR."""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not project_dir:
        print(
            "[baton-writer] ERROR: $CLAUDE_PROJECT_DIR not set; "
            "use --test-write <path> for test mode.",
            file=sys.stderr,
        )
        sys.exit(1)
    return os.path.join(project_dir, ".teamlead", "baton.json")


def _fixture_payload() -> dict[str, Any]:
    """Build a valid 7-key fixture payload for --self-test mode.

    auto_mode_resumed is always false per design.md §2 frozen decision.
    """
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "session_id": str(uuid.uuid4()),
        "prior_pause_commit": "0" * 40,  # placeholder SHA-1
        "branch": "feat/v0.1.7-auto-resume-daemon",
        "last_action_iso": now_iso,
        "progress_md_anchor": "a" * 64,  # placeholder sha256 hex
        "restore_prompt": "TeamLead: resume from last saved state.",
        "auto_mode_resumed": False,  # FROZEN default per design.md §2 line 171
    }


def main() -> None:
    args = sys.argv[1:]

    # --self-test mode: synthesize fixture payload, write to /tmp/baton-self-test.json
    if args == ["--self-test"]:
        payload = _fixture_payload()
        write_baton(payload, SELF_TEST_OUTPUT)
        sys.exit(0)

    # --test-write <path> mode: read payload from stdin, write to specified path
    if len(args) == 2 and args[0] == "--test-write":
        dest_path = args[1]
        try:
            raw = sys.stdin.read()
        except OSError as exc:
            print(
                f"[baton-writer] ERROR: reading stdin failed: {exc}",
                file=sys.stderr,
            )
            sys.exit(1)
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            print(
                f"[baton-writer] ERROR: stdin is not valid JSON: {exc}",
                file=sys.stderr,
            )
            sys.exit(1)
        write_baton(payload, dest_path)
        sys.exit(0)

    # Production mode (no args): read from stdin, write to default path
    if not args:
        dest_path = _default_dest_path()
        try:
            raw = sys.stdin.read()
        except OSError as exc:
            print(
                f"[baton-writer] ERROR: reading stdin failed: {exc}",
                file=sys.stderr,
            )
            sys.exit(1)
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            print(
                f"[baton-writer] ERROR: stdin is not valid JSON: {exc}",
                file=sys.stderr,
            )
            sys.exit(1)
        write_baton(payload, dest_path)
        sys.exit(0)

    # Unknown invocation
    print(
        "Usage:\n"
        "  python3 lib/baton-writer.py                  # production: stdin → $CLAUDE_PROJECT_DIR/.teamlead/baton.json\n"
        "  python3 lib/baton-writer.py --test-write <path>  # test: stdin → <path>\n"
        "  python3 lib/baton-writer.py --self-test          # self-test: fixture → /tmp/baton-self-test.json",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
