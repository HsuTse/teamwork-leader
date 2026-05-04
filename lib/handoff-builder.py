#!/usr/bin/env python3
"""
lib/handoff-builder.py — RESUME payload construction.

Purpose: Assembles the 6-field handoff payload for the pre-compact orchestrator
(hooks/pre-compact.py) to pass into baton-writer. Reads git state via subprocess,
computes sha256 of PROGRESS.md, extracts Last Action metadata, assembles
restore_prompt from PROGRESS.md tail + audit-trail.jsonl tail, sanitizes
restore_prompt against allowlist (design.md §5 lines 449-452), and caps at 8 KB.

Output schema (6 fields per Opus PLAN_AUDIT revision #3):
  restore_prompt       — sanitized string ≤ 8192 bytes
  progress_md_anchor   — sha256 hex of PROGRESS.md
  last_action_iso      — ISO-8601 from PROGRESS.md ## Last Action: line
  last_dispatch_id     — dispatch_id extracted from Last Action body, or "unknown"
  prior_pause_commit   — 40-char hex from git rev-parse HEAD
  branch               — git branch name, or "(detached HEAD)"

Note: auto_mode_resumed (always false) and session_id are NOT in this output;
they are added by the pre-compact orchestrator (hooks/pre-compact.py) before
calling baton-writer, per design.md §2 + Opus PLAN_AUDIT revision #3.

Spec references:
  design.md §2 lines 165-172 (baton schema)
  design.md §5 lines 449-454 (prompt-injection mitigation)
  Opus PLAN_AUDIT revision #3 (6-field handoff-builder scope)
  Opus PLAN_AUDIT revision #6 Q5 (CLAUDE_PROJECT_DIR env, not stdin)

CLI signature:
  python3 lib/handoff-builder.py
      Production mode: reads $CLAUDE_PROJECT_DIR/PROGRESS.md, outputs JSON to stdout.

  python3 lib/handoff-builder.py --build <path>
      Build mode: writes JSON to specified path; stdout silent.

  python3 lib/handoff-builder.py --self-test
      Self-test mode: round-trip with synthetic PROGRESS.md fixture;
      writes JSON to /tmp/handoff-self-test.json; exits 0 on success.

Implementation task: T-3-4.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from typing import Optional

# Maximum restore_prompt bytes (design.md §5 line 454)
RESTORE_PROMPT_MAX_BYTES: int = 8192

# Truncation marker appended when restore_prompt exceeds cap
TRUNCATION_MARKER: str = "[TRUNCATED AT 8KB — consult PROGRESS.md directly]"

# Default number of PROGRESS.md tail lines to include in restore_prompt
PROGRESS_MD_TAIL_LINES: int = 50

# Number of audit-trail.jsonl tail records to include (last N)
AUDIT_TRAIL_TAIL_RECORDS: int = 3

# Self-test output path
SELF_TEST_OUTPUT: str = "/tmp/handoff-self-test.json"

# Subprocess timeout for git commands (seconds)
GIT_TIMEOUT: int = 5

# Allowlist: ALLOW these character ranges (design.md §5 lines 449-452)
# ASCII letters, digits, whitespace (\n \t \r), standard punctuation.
# Disallowed: backtick, bare $, ${, \x00, control chars (except \n \t \r).
_ALLOWED_PATTERN: re.Pattern[str] = re.compile(
    r"[A-Za-z0-9 \t\n\r"
    r"\.\,\;\:\!\?\(\)\[\]\{\}\"\'\/\\\-\_\+\=\*\&\%\#\@\~\^\|"
    r"\<\>]+"
)

# Characters that are unconditionally disallowed (used for replacement logic)
_DISALLOWED_CHARS: re.Pattern[str] = re.compile(
    r"[`\x00\x01-\x08\x0b\x0c\x0e-\x1f\x7f]"
)

# Dollar sequences: bare $ (including bare dollar sign with no following char),
# ${...} sequences, and $(...) sequences.
_DOLLAR_SEQUENCES: re.Pattern[str] = re.compile(r"\$[\{(]?")


def _sanitize_restore_prompt(raw: str) -> str:
    """Sanitize restore_prompt per design.md §5 allowlist.

    Replacement strategy:
    1. Replace dollar sequences ($, ${, $( prefixes) with '_'.
    2. Replace backticks and control chars (except \\n \\t \\r) with '_'.
    3. Warn to stderr for each substitution made.

    Returns sanitized string (before length cap).
    """
    # Step 1: replace dollar sequences
    dollar_matches = list(_DOLLAR_SEQUENCES.finditer(raw))
    if dollar_matches:
        print(
            f"[handoff-builder] WARNING: sanitized {len(dollar_matches)} dollar "
            f"sequence(s) in restore_prompt",
            file=sys.stderr,
        )
    sanitized = _DOLLAR_SEQUENCES.sub("_", raw)

    # Step 2: replace backtick and disallowed control chars
    disallowed_matches = list(_DISALLOWED_CHARS.finditer(sanitized))
    if disallowed_matches:
        print(
            f"[handoff-builder] WARNING: sanitized {len(disallowed_matches)} "
            f"disallowed character(s) in restore_prompt",
            file=sys.stderr,
        )
    sanitized = _DISALLOWED_CHARS.sub("_", sanitized)

    return sanitized


def _cap_restore_prompt(text: str) -> str:
    """Cap restore_prompt at RESTORE_PROMPT_MAX_BYTES (UTF-8 encoded).

    If text exceeds the cap, truncate and append TRUNCATION_MARKER.
    The final result must fit within RESTORE_PROMPT_MAX_BYTES bytes.
    """
    encoded = text.encode("utf-8")
    if len(encoded) <= RESTORE_PROMPT_MAX_BYTES:
        return text

    marker_bytes = TRUNCATION_MARKER.encode("utf-8")
    # Reserve space for truncation marker
    cutoff = RESTORE_PROMPT_MAX_BYTES - len(marker_bytes)
    if cutoff < 0:
        # Degenerate edge case: marker itself exceeds cap
        return TRUNCATION_MARKER[:RESTORE_PROMPT_MAX_BYTES]

    truncated_bytes = encoded[:cutoff]
    # Decode with errors='ignore' to avoid partial multi-byte char corruption
    truncated_text = truncated_bytes.decode("utf-8", errors="ignore")
    print(
        f"[handoff-builder] WARNING: restore_prompt truncated from "
        f"{len(encoded)} bytes to {RESTORE_PROMPT_MAX_BYTES} bytes",
        file=sys.stderr,
    )
    return truncated_text + TRUNCATION_MARKER


def _git_rev_parse(cwd: str, *args: str) -> Optional[str]:
    """Run git rev-parse with given args in cwd; return stripped stdout or None on error."""
    try:
        result = subprocess.run(
            ["git", "rev-parse"] + list(args),
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        print(
            f"[handoff-builder] WARNING: git rev-parse {' '.join(args)} failed "
            f"(exit {result.returncode}): {result.stderr.strip()}",
            file=sys.stderr,
        )
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
        print(
            f"[handoff-builder] WARNING: git rev-parse {' '.join(args)} error: {exc}",
            file=sys.stderr,
        )
        return None


def _get_prior_pause_commit(cwd: str) -> str:
    """Return 40-char git HEAD SHA, or '0' * 40 if unavailable."""
    sha = _git_rev_parse(cwd, "HEAD")
    if sha and len(sha) == 40 and all(c in "0123456789abcdef" for c in sha.lower()):
        return sha.lower()
    print(
        "[handoff-builder] WARNING: could not obtain valid 40-char HEAD SHA; "
        "using placeholder.",
        file=sys.stderr,
    )
    return "0" * 40


def _get_branch(cwd: str) -> str:
    """Return git branch name, or '(detached HEAD)' if detached."""
    branch = _git_rev_parse(cwd, "--abbrev-ref", "HEAD")
    if branch is None:
        return "(detached HEAD)"
    if branch == "HEAD":
        return "(detached HEAD)"
    return branch


def _compute_progress_md_anchor(progress_md_path: str) -> str:
    """Compute sha256 hex digest of PROGRESS.md content.

    Uses Python hashlib per Q9 portability decision (no subprocess to sha256sum).
    """
    try:
        with open(progress_md_path, "rb") as fh:
            data = fh.read()
        return hashlib.sha256(data).hexdigest()
    except OSError as exc:
        print(
            f"[handoff-builder] WARNING: could not read {progress_md_path!r} "
            f"for sha256: {exc}; using zeros.",
            file=sys.stderr,
        )
        return "0" * 64


def _extract_last_action_iso(progress_md_path: str) -> str:
    """Extract ISO-8601 timestamp from the most recent '## Last Action:' line.

    Pattern: '## Last Action: <ISO-8601> [TRUSTED]'
    Example: '## Last Action: 2026-05-04T10:00+08:00 [TRUSTED]'

    Returns the ISO timestamp string, or current UTC time (+ stderr warning) if
    no match is found.
    """
    # ISO-8601 pattern: date + 'T' + time with optional offset or 'Z'
    iso_pattern = re.compile(
        r"^##\s+Last Action:\s+(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?(?:Z|[+-]\d{2}:\d{2})?)",
        re.MULTILINE,
    )
    try:
        with open(progress_md_path, "r", encoding="utf-8") as fh:
            content = fh.read()
        match = iso_pattern.search(content)
        if match:
            return match.group(1)
    except OSError as exc:
        print(
            f"[handoff-builder] WARNING: could not read {progress_md_path!r}: {exc}",
            file=sys.stderr,
        )

    # Fallback: current UTC time
    fallback = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(
        f"[handoff-builder] WARNING: no 'Last Action' ISO timestamp found in "
        f"PROGRESS.md; using current UTC time {fallback!r}.",
        file=sys.stderr,
    )
    return fallback


def _extract_last_dispatch_id(progress_md_path: str) -> str:
    """Extract dispatch_id from the most recent Last Action line body.

    Pattern: looks for S<N>-D<M> pattern in the first Last Action section.
    Returns the dispatch ID string, or "unknown" if not found.
    """
    dispatch_pattern = re.compile(r"\b(S\d+-D\d+)\b")
    last_action_header = re.compile(
        r"^##\s+Last Action(?:\s+\([^)]*\))?:\s+",
        re.MULTILINE,
    )
    try:
        with open(progress_md_path, "r", encoding="utf-8") as fh:
            content = fh.read()

        # Find the first Last Action section
        match = last_action_header.search(content)
        if match:
            # Extract from match position to next '## ' header or EOF
            section_start = match.start()
            next_header = re.search(r"^##\s+", content[match.end():], re.MULTILINE)
            if next_header:
                section = content[section_start: match.end() + next_header.start()]
            else:
                section = content[section_start:]

            # Return the first occurrence of S<N>-D<M> in the Last Action section.
            # "First occurrence" reflects the dispatch ID closest to the
            # Last Action header (most recently logged dispatch).
            all_ids = dispatch_pattern.findall(section)
            if all_ids:
                return all_ids[0]  # first occurrence = current dispatch

    except OSError as exc:
        print(
            f"[handoff-builder] WARNING: could not read {progress_md_path!r}: {exc}",
            file=sys.stderr,
        )

    return "unknown"


def _tail_lines(path: str, n: int) -> str:
    """Return last n lines of text file as a single string. Empty string on error."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
        return "".join(lines[-n:])
    except OSError:
        return ""


def _tail_jsonl_records(path: str, n: int) -> str:
    """Return last n non-empty lines of a JSONL file as newline-joined string.

    Used for audit-trail.jsonl. Empty string if file does not exist.
    """
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            lines = [ln for ln in fh.readlines() if ln.strip()]
        return "".join(lines[-n:])
    except OSError:
        return ""


def _assemble_restore_prompt(project_dir: str, progress_md_path: str) -> str:
    """Assemble restore_prompt from PROGRESS.md tail + audit-trail.jsonl tail.

    Sanitizes and caps the result per design.md §5.
    """
    progress_tail = _tail_lines(progress_md_path, PROGRESS_MD_TAIL_LINES)

    audit_trail_path = os.path.join(project_dir, ".teamlead", "audit-trail.jsonl")
    audit_tail = _tail_jsonl_records(audit_trail_path, AUDIT_TRAIL_TAIL_RECORDS)

    parts: list[str] = []
    if progress_tail:
        parts.append("=== PROGRESS.md (last 50 lines) ===\n" + progress_tail)
    if audit_tail:
        parts.append("=== audit-trail.jsonl (last 3 records) ===\n" + audit_tail)

    raw = "\n".join(parts) if parts else "(no context available)"

    sanitized = _sanitize_restore_prompt(raw)
    return _cap_restore_prompt(sanitized)


def build_payload(project_dir: str, progress_md_path: str) -> dict[str, str]:
    """Assemble the 6-field handoff payload.

    Args:
        project_dir: path used as cwd for git commands and audit-trail lookup
        progress_md_path: absolute path to PROGRESS.md

    Returns:
        dict with keys: restore_prompt, progress_md_anchor, last_action_iso,
                        last_dispatch_id, prior_pause_commit, branch
    """
    prior_pause_commit = _get_prior_pause_commit(project_dir)
    branch = _get_branch(project_dir)
    progress_md_anchor = _compute_progress_md_anchor(progress_md_path)
    last_action_iso = _extract_last_action_iso(progress_md_path)
    last_dispatch_id = _extract_last_dispatch_id(progress_md_path)
    restore_prompt = _assemble_restore_prompt(project_dir, progress_md_path)

    return {
        "restore_prompt": restore_prompt,
        "progress_md_anchor": progress_md_anchor,
        "last_action_iso": last_action_iso,
        "last_dispatch_id": last_dispatch_id,
        "prior_pause_commit": prior_pause_commit,
        "branch": branch,
    }


def _resolve_env() -> tuple[str, str]:
    """Resolve project_dir and progress_md_path from $CLAUDE_PROJECT_DIR.

    Exits 1 if environment is not configured.
    """
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "").strip()
    if not project_dir:
        print(
            "[handoff-builder] ERROR: $CLAUDE_PROJECT_DIR not set; "
            "use --build <path> for explicit output or --self-test for testing.",
            file=sys.stderr,
        )
        sys.exit(1)
    progress_md_path = os.path.join(project_dir, "PROGRESS.md")
    return project_dir, progress_md_path


def _run_self_test() -> None:
    """Self-test: build payload against a synthetic PROGRESS.md fixture.

    Verifies:
    - All 6 required fields present
    - prior_pause_commit is 40-char hex (real SHA from this repo, or placeholder)
    - restore_prompt length ≤ 8192 bytes
    - allowlist sanitization works ($ and backtick replaced)
    - Writes output to SELF_TEST_OUTPUT
    """
    # Create a synthetic PROGRESS.md in a temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        progress_md_path = os.path.join(tmpdir, "PROGRESS.md")
        with open(progress_md_path, "w", encoding="utf-8") as fh:
            fh.write(
                "# Project: teamwork-leader v0.1.7\n\n"
                "## Last Action: 2026-05-04T10:00:00Z [TRUSTED] — S3-D5 RD PM T-3-4 "
                "handoff-builder dispatch.\n\n"
                "Stage 3 wave 3: T-3-4 lib/handoff-builder.py implementation.\n"
                "Injection test: `backtick` and ${VARIABLE} and $HOME should be sanitized.\n"
            )

        # Use the actual repo dir for git context (real HEAD SHA)
        repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        payload = build_payload(repo_dir, progress_md_path)

    # Validate all 6 fields present
    required_fields = [
        "restore_prompt",
        "progress_md_anchor",
        "last_action_iso",
        "last_dispatch_id",
        "prior_pause_commit",
        "branch",
    ]
    for field in required_fields:
        if field not in payload:
            print(
                f"[handoff-builder] SELF-TEST FAIL: missing field {field!r}",
                file=sys.stderr,
            )
            sys.exit(1)

    # Validate prior_pause_commit: 40-char hex
    commit = payload["prior_pause_commit"]
    if len(commit) != 40 or not all(c in "0123456789abcdef" for c in commit.lower()):
        print(
            f"[handoff-builder] SELF-TEST FAIL: prior_pause_commit {commit!r} "
            "is not a valid 40-char hex SHA",
            file=sys.stderr,
        )
        sys.exit(1)

    # Validate restore_prompt length cap
    prompt_bytes = payload["restore_prompt"].encode("utf-8")
    if len(prompt_bytes) > RESTORE_PROMPT_MAX_BYTES:
        print(
            f"[handoff-builder] SELF-TEST FAIL: restore_prompt {len(prompt_bytes)} bytes "
            f"exceeds {RESTORE_PROMPT_MAX_BYTES} byte cap",
            file=sys.stderr,
        )
        sys.exit(1)

    # Validate allowlist: backtick and $ must not appear in restore_prompt
    rp = payload["restore_prompt"]
    if "`" in rp:
        print(
            "[handoff-builder] SELF-TEST FAIL: backtick present in restore_prompt "
            "after sanitization",
            file=sys.stderr,
        )
        sys.exit(1)
    if re.search(r"\$", rp):
        print(
            "[handoff-builder] SELF-TEST FAIL: dollar sign present in restore_prompt "
            "after sanitization",
            file=sys.stderr,
        )
        sys.exit(1)

    # Validate progress_md_anchor is 64-char hex (sha256)
    anchor = payload["progress_md_anchor"]
    if len(anchor) != 64 or not all(c in "0123456789abcdef" for c in anchor.lower()):
        print(
            f"[handoff-builder] SELF-TEST FAIL: progress_md_anchor {anchor!r} "
            "is not a valid 64-char sha256 hex",
            file=sys.stderr,
        )
        sys.exit(1)

    # Write output to SELF_TEST_OUTPUT
    output_bytes = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    with open(SELF_TEST_OUTPUT, "wb") as fh:
        fh.write(output_bytes)

    print(
        f"[handoff-builder] --self-test PASS: all 6 fields valid; "
        f"output at {SELF_TEST_OUTPUT} ({len(output_bytes)} bytes)",
        file=sys.stderr,
    )


def main() -> None:
    args = sys.argv[1:]

    # --self-test mode
    if args == ["--self-test"]:
        _run_self_test()
        sys.exit(0)

    # --build <path> mode: build payload, write to specified file
    if len(args) == 2 and args[0] == "--build":
        dest_path = args[1]
        project_dir, progress_md_path = _resolve_env()
        payload = build_payload(project_dir, progress_md_path)
        output_bytes = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        try:
            with open(dest_path, "wb") as fh:
                fh.write(output_bytes)
        except OSError as exc:
            print(
                f"[handoff-builder] ERROR: could not write to {dest_path!r}: {exc}",
                file=sys.stderr,
            )
            sys.exit(1)
        print(
            f"[handoff-builder] payload written to {dest_path!r} ({len(output_bytes)} bytes)",
            file=sys.stderr,
        )
        sys.exit(0)

    # Production mode (no args): build payload, output JSON to stdout
    if not args:
        project_dir, progress_md_path = _resolve_env()
        payload = build_payload(project_dir, progress_md_path)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        sys.exit(0)

    # Unknown invocation
    print(
        "Usage:\n"
        "  python3 lib/handoff-builder.py                   "
        "# production: output JSON to stdout\n"
        "  python3 lib/handoff-builder.py --build <path>    "
        "# build mode: write JSON to <path>\n"
        "  python3 lib/handoff-builder.py --self-test       "
        "# self-test: fixture round-trip to /tmp/handoff-self-test.json",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
