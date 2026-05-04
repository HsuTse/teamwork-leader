#!/usr/bin/env python3
"""
lib/notifier.py — macOS notification wrapper with layered fallback.

Purpose:
  1. Attempts osascript -e 'display notification ...' as PRIMARY CHANNEL (courtesy only).
     On any failure (FileNotFoundError, CalledProcessError, TimeoutExpired, non-macOS)
     → silent no-op.  Rationale: "COURTESY, NOT SOURCE OF TRUTH" (design.md line 542).
  2. ALWAYS writes last-resume-failure.txt regardless of osascript outcome — this is
     the SOURCE OF TRUTH (design.md §5 lines 526-536).

Atomic write: tmp + os.replace + 0600 chmod (same pattern as baton-writer.py).

Spec reference: design.md §5 lines 526-542; design.md §6 lines 539-542.
Implementation task: T-3-5.

CLI signature:
  python3 lib/notifier.py --notify "<message>"
      Production: osascript + write to $CLAUDE_PROJECT_DIR/.teamlead/last-resume-failure.txt

  python3 lib/notifier.py --test-notify "<message>" <output-path>
      Test mode: osascript + write to specified path

  python3 lib/notifier.py --self-test
      Self-test: round-trip verify file write exits 0 on success
"""
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone


# Production last-resume-failure.txt relative to $CLAUDE_PROJECT_DIR/.teamlead/
_FAILURE_FILENAME = "last-resume-failure.txt"


# ── internal helpers ──────────────────────────────────────────────────────────


def _try_osascript(message: str) -> None:
    """Attempt macOS display notification; silently no-op on any failure.

    Per design.md §6 lines 539-542 and §5 line 540:
    - FileNotFoundError  → osascript not available (non-macOS or stripped install)
    - CalledProcessError → osascript returned non-zero
    - TimeoutExpired     → osascript hung (5 s hard limit)
    All three → silent no-op; no stdout/stderr noise from this function.
    """
    # Escape double-quotes in message to keep the AppleScript literal safe.
    safe_msg = message.replace('"', '\\"')
    script = f'display notification "{safe_msg}" with title "TeamLead"'
    try:
        subprocess.run(
            ["osascript", "-e", script],
            timeout=5,
            check=True,
            capture_output=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        pass  # silent no-op per spec


def _build_record(message: str) -> str:
    """Build the last-resume-failure.txt content per design.md §5 lines 526-536.

    Single-record overwrite; fields separated by newlines for grep-ability.
    """
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return (
        f"timestamp: {ts}\n"
        f"message: {message}\n"
    )


def _atomic_write(content: str, dest_path: str) -> None:
    """Atomically write content to dest_path with 0600 permissions.

    Protocol (mirrors baton-writer.py):
    1. Write to dest_path + '.tmp' via os.open(O_WRONLY|O_CREAT|O_TRUNC, 0o600).
       Uses O_TRUNC (not O_EXCL) since single-record overwrite is the desired semantic
       — previous failure record is replaced on each invocation.
    2. os.replace(tmp, dest) — POSIX atomic rename on same filesystem.
    3. os.chmod(dest, 0o600) immediately after rename.

    Raises SystemExit(1) on any OS error; does NOT leave .tmp behind on failure.
    """
    dest_path = os.path.abspath(dest_path)
    dest_dir = os.path.dirname(dest_path)
    os.makedirs(dest_dir, exist_ok=True)

    tmp_path = dest_path + ".tmp"
    payload_bytes = content.encode("utf-8")

    # Open with O_TRUNC to overwrite any stale .tmp from prior torn write.
    try:
        fd = os.open(
            tmp_path,
            os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
            0o600,
        )
    except OSError as exc:
        print(
            f"[notifier] ERROR: could not open tmp {tmp_path!r}: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Write bytes; unlink on error.
    try:
        os.write(fd, payload_bytes)
    except OSError as exc:
        os.close(fd)
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        print(
            f"[notifier] ERROR: write to tmp failed: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)
    finally:
        try:
            os.close(fd)
        except OSError:
            pass

    # Atomic rename: tmp → dest
    try:
        os.replace(tmp_path, dest_path)
    except OSError as exc:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        print(
            f"[notifier] ERROR: atomic rename failed: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Set 0600 after rename
    try:
        os.chmod(dest_path, 0o600)
    except OSError as exc:
        # Non-fatal; write already committed atomically.
        print(
            f"[notifier] WARNING: chmod 0600 on {dest_path!r} failed: {exc}",
            file=sys.stderr,
        )


def _default_dest_path() -> str:
    """Resolve production path from $CLAUDE_PROJECT_DIR."""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not project_dir:
        print(
            "[notifier] ERROR: $CLAUDE_PROJECT_DIR not set; "
            "use --test-notify <message> <path> for test mode.",
            file=sys.stderr,
        )
        sys.exit(1)
    return os.path.join(project_dir, ".teamlead", _FAILURE_FILENAME)


# ── public entry point ────────────────────────────────────────────────────────


def notify(message: str, dest_path: str) -> None:
    """Best-effort osascript + authoritative file write.

    Always writes dest_path regardless of osascript outcome.
    """
    _try_osascript(message)
    record = _build_record(message)
    _atomic_write(record, dest_path)
    print(
        f"[notifier] failure record written to {dest_path!r}",
        file=sys.stderr,
    )


# ── CLI dispatch ──────────────────────────────────────────────────────────────


def main() -> None:
    args = sys.argv[1:]

    # --notify "<message>"  (production mode)
    if len(args) == 2 and args[0] == "--notify":
        message = args[1]
        dest_path = _default_dest_path()
        notify(message, dest_path)
        sys.exit(0)

    # --test-notify "<message>" <output-path>
    if len(args) == 3 and args[0] == "--test-notify":
        message = args[1]
        dest_path = args[2]
        notify(message, dest_path)
        sys.exit(0)

    # --self-test  (round-trip: write to /tmp, read back, verify content)
    if args == ["--self-test"]:
        import tempfile as _tmp

        tmp_dir = _tmp.mkdtemp()
        out_path = os.path.join(tmp_dir, _FAILURE_FILENAME)
        test_msg = "self-test probe"
        notify(test_msg, out_path)

        # Verify round-trip
        try:
            with open(out_path, "r", encoding="utf-8") as fh:
                content = fh.read()
        except OSError as exc:
            print(f"[notifier] SELF-TEST FAIL: could not read {out_path!r}: {exc}", file=sys.stderr)
            sys.exit(1)

        if test_msg not in content:
            print(
                f"[notifier] SELF-TEST FAIL: expected {test_msg!r} in output; got:\n{content}",
                file=sys.stderr,
            )
            sys.exit(1)

        # Verify 0600 permissions
        mode = oct(os.stat(out_path).st_mode & 0o777)
        if mode != "0o600":
            print(
                f"[notifier] SELF-TEST FAIL: expected permissions 0600, got {mode}",
                file=sys.stderr,
            )
            sys.exit(1)

        print("[notifier] self-test PASS", file=sys.stderr)
        sys.exit(0)

    # Unknown invocation
    print(
        "Usage:\n"
        "  python3 lib/notifier.py --notify \"<message>\"\n"
        "      Production: osascript + write to $CLAUDE_PROJECT_DIR/.teamlead/last-resume-failure.txt\n"
        "\n"
        "  python3 lib/notifier.py --test-notify \"<message>\" <output-path>\n"
        "      Test: osascript + write to specified path\n"
        "\n"
        "  python3 lib/notifier.py --self-test\n"
        "      Self-test: round-trip verify file write",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
