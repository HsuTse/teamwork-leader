#!/usr/bin/env python3
"""
hooks/stop.py — Stop hook handler for Claude Code session end.

Purpose: Fired by Claude Code's Stop event when a session ends.
  1. Invokes lib/notifier.py (subprocess) to emit macOS notification
     (best-effort courtesy only; silent no-op on osascript unavailable).
  2. Reads ${CLAUDE_PROJECT_DIR:-$(pwd)}/.teamlead/last-resume-failure.txt
     if present and surfaces its content via stderr (operator-visible).
     Does NOT delete the banner file; it is consumed by SessionStart per
     T-S-4 mitigation chain (design.md lines 544-551).
  3. Always emits valid JSON {"decision": "approve"} on stdout so Claude
     Code's Stop hook contract is satisfied (hook-development SKILL).

Flags:
  (no flags)     Production: invoke notifier + banner check + JSON output.
  --test-mode    Skip actual notification (no system popup during CI/tests);
                 still read/surface banner if present; emit JSON output; exit 0.
  --self-test    Internal sanity: synthetic banner read + JSON output
                 validation; no external side effects; exit 0 on PASS.

Spec reference: design.md §5 lines 537-551 (notification + banner surface);
               design.md §5 lines 544-551 + §1 T-S-4 row line 565 (banner consumption chain).
Implementation task: T-3-7.
"""

import json
import os
import subprocess
import sys


# ── constants ──────────────────────────────────────────────────────────────────

_BANNER_FILENAME = "last-resume-failure.txt"
_NOTIFICATION_MESSAGE = "TeamLead session ended — check .teamlead/last-resume-failure.txt if auto-resume failed"
_NOTIFIER_TIMEOUT_SECONDS = 10


# ── helpers ────────────────────────────────────────────────────────────────────


def _resolve_plugin_root() -> str:
    """Resolve CLAUDE_PLUGIN_ROOT or fall back to parent of this script's directory."""
    root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if root:
        return root
    # hooks/stop.py → parent is the plugin root
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _resolve_banner_path() -> str:
    """Resolve the last-resume-failure.txt path from $CLAUDE_PROJECT_DIR.

    Falls back to pwd if $CLAUDE_PROJECT_DIR is unset (per dispatch constraint).
    """
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    return os.path.join(project_dir, ".teamlead", _BANNER_FILENAME)


def _invoke_notifier(plugin_root: str, test_mode: bool) -> None:
    """Invoke lib/notifier.py via subprocess.run; silent no-op on any failure.

    Uses canonical --notify flag (not --test-notify) per S3-D8 constraint.
    In test mode, skips actual invocation entirely to avoid system popups
    during automated tests.  The notifier itself implements layered fallback
    (osascript → silent no-op on unavailable); if we invoke it in production
    mode it may pop a real notification — which is desired.
    """
    if test_mode:
        # Explicit skip: no system notification in test/CI context.
        print("[stop] test-mode: skipping notifier invocation", file=sys.stderr)
        return

    notifier_path = os.path.join(plugin_root, "lib", "notifier.py")
    cmd = [sys.executable, notifier_path, "--notify", _NOTIFICATION_MESSAGE]

    try:
        subprocess.run(
            cmd,
            timeout=_NOTIFIER_TIMEOUT_SECONDS,
            # Capture output to avoid polluting Stop hook's stdout (JSON only).
            capture_output=True,
        )
        # Ignore return code: notifier exits 0 on success or 1 on internal
        # write error; Stop hook must not fail either way per design.md line 540.
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        # Silent no-op: per design.md line 540, notification is COURTESY only.
        pass


def _surface_banner(banner_path: str) -> None:
    """Read last-resume-failure.txt and emit to stderr if present.

    Design.md lines 544-551: banner is surfaced at session-end for operator
    awareness.  This hook does NOT delete the file; that is operator-driven.
    FileNotFoundError → silent skip (the normal case when no failure occurred).
    """
    try:
        with open(banner_path, "r", encoding="utf-8") as fh:
            content = fh.read()
    except FileNotFoundError:
        # Normal path: no prior auto-resume failure.
        return
    except OSError as exc:
        # Other read errors (permissions, etc.) → log but do not raise.
        print(f"[stop] WARNING: could not read banner {banner_path!r}: {exc}", file=sys.stderr)
        return

    print(
        f"[stop] NOTICE: prior auto-resume failure detected in {banner_path!r}:\n"
        f"{content.strip()}\n"
        f"Run /teamwork-leader doctor or inspect the file above.",
        file=sys.stderr,
    )


def _emit_json_decision() -> None:
    """Write Stop hook JSON return value to stdout.

    Claude Code Stop hook contract: {"decision": "approve"} signals
    the session may proceed to exit normally.
    Reference: hook-development SKILL canonical return contract.
    """
    print(json.dumps({"decision": "approve"}))


def _run_self_test() -> None:
    """Internal sanity check; exits 0 on PASS, 1 on FAIL.

    Tests:
    1. Banner read path: write synthetic banner to /tmp, confirm _surface_banner
       emits content to stderr (no actual OS interaction).
    2. JSON output: capture _emit_json_decision output, parse and validate
       "decision" field presence and value.
    """
    import io
    import tempfile

    all_pass = True
    # Capture original streams once at function start so each sub-test's
    # finally block restores to the true original, not a sub-test-local ref.
    original_stderr = sys.stderr
    original_stdout = sys.stdout

    # ── sub-test 1: banner read ───────────────────────────────────────────────
    tmp_dir = tempfile.mkdtemp()
    teamlead_dir = os.path.join(tmp_dir, ".teamlead")
    os.makedirs(teamlead_dir, exist_ok=True)
    synthetic_banner = os.path.join(teamlead_dir, _BANNER_FILENAME)
    synthetic_content = (
        "timestamp: 2026-05-04T00:00:00Z\n"
        "message: self-test synthetic failure\n"
    )
    with open(synthetic_banner, "w", encoding="utf-8") as fh:
        fh.write(synthetic_content)

    # Redirect stderr to capture output from _surface_banner.
    captured_stderr = io.StringIO()
    sys.stderr = captured_stderr
    try:
        _surface_banner(synthetic_banner)
    finally:
        sys.stderr = original_stderr

    banner_output = captured_stderr.getvalue()
    if "self-test synthetic failure" not in banner_output:
        print(
            f"[stop] SELF-TEST FAIL: expected synthetic failure message in banner output; "
            f"got: {banner_output!r}",
            file=sys.stderr,
        )
        all_pass = False
    else:
        print("[stop] self-test sub-1 (banner read): PASS", file=sys.stderr)

    # ── sub-test 2: absent banner → silent skip ───────────────────────────────
    absent_path = os.path.join(tmp_dir, "nonexistent", _BANNER_FILENAME)
    captured_stderr2 = io.StringIO()
    sys.stderr = captured_stderr2
    try:
        _surface_banner(absent_path)
    finally:
        sys.stderr = original_stderr

    absent_output = captured_stderr2.getvalue()
    if absent_output.strip():
        print(
            f"[stop] SELF-TEST FAIL: expected silent skip for absent banner; "
            f"got: {absent_output!r}",
            file=sys.stderr,
        )
        all_pass = False
    else:
        print("[stop] self-test sub-2 (absent banner silent): PASS", file=sys.stderr)

    # ── sub-test 3: JSON output validation ───────────────────────────────────
    captured_stdout = io.StringIO()
    sys.stdout = captured_stdout
    try:
        _emit_json_decision()
    finally:
        sys.stdout = original_stdout

    json_output = captured_stdout.getvalue().strip()
    try:
        parsed = json.loads(json_output)
    except json.JSONDecodeError as exc:
        print(
            f"[stop] SELF-TEST FAIL: JSON output not parseable: {exc}; got: {json_output!r}",
            file=sys.stderr,
        )
        all_pass = False
        parsed = {}

    if parsed.get("decision") != "approve":
        print(
            f"[stop] SELF-TEST FAIL: expected decision='approve'; got: {parsed!r}",
            file=sys.stderr,
        )
        all_pass = False
    else:
        print("[stop] self-test sub-3 (JSON decision field): PASS", file=sys.stderr)

    # ── result ────────────────────────────────────────────────────────────────
    if all_pass:
        print("[stop] self-test PASS", file=sys.stderr)
        sys.exit(0)
    else:
        print("[stop] self-test FAIL", file=sys.stderr)
        sys.exit(1)


# ── main ───────────────────────────────────────────────────────────────────────


def main() -> None:
    """Entry point for Stop hook.

    Execution order (production):
      1. Invoke lib/notifier.py for macOS courtesy notification.
      2. Read + surface last-resume-failure.txt banner if present.
      3. Emit {"decision": "approve"} JSON to stdout.
      Exit 0 always (Stop hook MUST exit 0 to not break Claude Code session).

    In --test-mode, step 1 is skipped (no system popup).
    In --self-test, runs internal sanity and exits without reaching step 1-3.
    """
    args = sys.argv[1:]

    # --self-test: internal sanity; exits inside.
    if args == ["--self-test"]:
        _run_self_test()
        # _run_self_test always calls sys.exit; unreachable:
        return

    test_mode = "--test-mode" in args

    plugin_root = _resolve_plugin_root()
    banner_path = _resolve_banner_path()

    # Step 1: macOS courtesy notification (skipped in test mode).
    _invoke_notifier(plugin_root, test_mode)

    # Step 2: surface last-resume-failure.txt banner if present.
    _surface_banner(banner_path)

    # Step 3: emit Stop hook JSON return value.
    _emit_json_decision()

    sys.exit(0)


if __name__ == "__main__":
    main()
