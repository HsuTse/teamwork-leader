#!/usr/bin/env python3
"""
tools/write-synthetic-baton.py — I-018 compliant Python helper for writing
synthetic test batons in measure-checkout-fp.sh trials.

This script writes a baton.json file with fields derived from the current
git state (for same-commit scenarios) or deliberately mismatched (for
divergent scenarios).

Called by: tools/measure-checkout-fp.sh
Usage:
  python3 tools/write-synthetic-baton.py \\
    --project-dir <dir> \\
    --scenario same-commit|divergent \\
    --mismatch-field none|prior_pause_commit|branch|progress_md_anchor|last_action_iso \\
    --output <path>

Per I-018: state-changing writes MUST be in Python. This script is the
Python actor for baton creation in the checkout false-positive measurement.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import uuid
from datetime import datetime, timezone


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _current_head(project_dir: str) -> str:
    """Return current HEAD commit SHA (40 hex chars), or a fallback on error."""
    try:
        result = subprocess.run(
            ["git", "-C", project_dir, "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return "0" * 40


def _current_branch(project_dir: str) -> str:
    """Return current branch name, or 'DETACHED' on error."""
    try:
        result = subprocess.run(
            ["git", "-C", project_dir, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return "DETACHED"


def _sha256_file(path: str) -> str:
    """Return sha256 hex digest of file, or a fallback string if unreadable."""
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return "a" * 64


def _progress_md_path(project_dir: str) -> str:
    return os.path.join(project_dir, "PROGRESS.md")


def _extract_last_action_iso(progress_md_path: str) -> str:
    """Extract ISO timestamp from first matching ## Last Action: line."""
    pattern = re.compile(r"^##\s+Last Action:\s+(\S+)", re.MULTILINE)
    try:
        content = open(progress_md_path, encoding="utf-8").read()
        m = pattern.search(content)
        if m:
            return m.group(1)
    except OSError:
        pass
    return "2026-01-01T00:00:00Z"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Write a synthetic baton for T-S-3 false-positive measurement (I-023 Metric 3)"
    )
    parser.add_argument(
        "--project-dir",
        required=True,
        help="Project directory (for git state + PROGRESS.md reads)",
    )
    parser.add_argument(
        "--scenario",
        choices=["same-commit", "divergent"],
        required=True,
        help="same-commit: fields match current HEAD; divergent: one field mismatched",
    )
    parser.add_argument(
        "--mismatch-field",
        default="none",
        choices=["none", "prior_pause_commit", "branch", "progress_md_anchor", "last_action_iso"],
        help="Which field to mismatch in divergent scenario (ignored for same-commit)",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output path for baton.json",
    )
    args = parser.parse_args()

    project_dir = os.path.abspath(args.project_dir)
    progress_md = _progress_md_path(project_dir)

    # Derive real current state
    real_commit = _current_head(project_dir)
    real_branch = _current_branch(project_dir)
    real_anchor = _sha256_file(progress_md)
    real_last_action = _extract_last_action_iso(progress_md)

    # Start with all-match baton
    baton: dict = {
        "session_id": str(uuid.uuid4()),
        "prior_pause_commit": real_commit,
        "branch": real_branch,
        "last_action_iso": real_last_action,
        "progress_md_anchor": real_anchor,
        "restore_prompt": "Synthetic test baton from measure-checkout-fp.sh (I-023 Metric 3)",
        "auto_mode_resumed": False,
        "gate_state": "BATON_WRITTEN",
        "written_at_iso": _iso_now(),
        "last_dispatch_id": "S3-D9-SYNTHETIC",
        "payload_size_bytes": 0,  # updated below
    }

    # Apply mismatch for divergent scenario
    if args.scenario == "divergent" and args.mismatch_field != "none":
        field = args.mismatch_field
        if field == "prior_pause_commit":
            # Use a clearly fake SHA that won't match any real commit
            baton["prior_pause_commit"] = "deadbeef" * 5
        elif field == "branch":
            baton["branch"] = "synthetic-nonexistent-branch-fp-test"
        elif field == "progress_md_anchor":
            # Flip all bits of the anchor (clearly wrong SHA)
            baton["progress_md_anchor"] = "f" * 64
        elif field == "last_action_iso":
            # Use a clearly wrong timestamp
            baton["last_action_iso"] = "1970-01-01T00:00:00Z"

    # NOTE: This synthetic baton has 11 keys (7 production keys + 4 test-only
    # extras: gate_state, written_at_iso, last_dispatch_id, payload_size_bytes).
    # Production baton-writer validates exactly 7 required keys and would reject
    # a baton written via baton-writer.py --self-test because of extra keys.
    # The test scaffold writes directly (bypassing baton-writer) specifically to
    # allow session-start.py's --test-mode-with-baton path to see extra fields.
    # TODO(v0.1.8): evaluate whether test extras should be stripped or baton-writer
    # updated to permit extra keys with an explicit allowlist (schema drift risk).
    _SYNTHETIC_KEYS = [
        "session_id", "prior_pause_commit", "branch", "last_action_iso",
        "progress_md_anchor", "restore_prompt", "auto_mode_resumed",
        # Test-only extras (not in production 7-key schema):
        "gate_state", "written_at_iso", "last_dispatch_id", "payload_size_bytes",
    ]
    assert set(baton.keys()) == set(_SYNTHETIC_KEYS), (
        f"Synthetic baton key drift: expected {sorted(_SYNTHETIC_KEYS)}, "
        f"got {sorted(baton.keys())}"
    )

    # Compute payload size (approximate; baton-writer does the precise check)
    payload_bytes = json.dumps(baton, ensure_ascii=False, indent=2).encode("utf-8")
    baton["payload_size_bytes"] = len(payload_bytes)
    # Re-serialize with updated size
    payload_bytes = json.dumps(baton, ensure_ascii=False, indent=2).encode("utf-8")

    # Write to output path (simple write; not going through baton-writer.py
    # because this is a test scaffold that may have non-7-field structure;
    # baton-writer would reject the extra gate_state / written_at_iso fields
    # failing the 7-key assertion — this is intentional: we write directly
    # for the test-mode-with-baton path which reads the baton raw)
    output_dir = os.path.dirname(os.path.abspath(args.output))
    os.makedirs(output_dir, exist_ok=True)

    tmp_path = args.output + ".tmp"
    try:
        fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        os.unlink(tmp_path)
        fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)

    try:
        os.write(fd, payload_bytes)
    finally:
        os.close(fd)

    os.replace(tmp_path, args.output)
    os.chmod(args.output, 0o600)

    print(
        f"[write-synthetic-baton] wrote {args.scenario}/{args.mismatch_field} "
        f"baton to {args.output} ({len(payload_bytes)} bytes)"
    )


if __name__ == "__main__":
    main()
