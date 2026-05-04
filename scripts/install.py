#!/usr/bin/env python3
"""
install.py — TeamLead auto-resume-daemon installer (Layer 1 + 2 + 3)

Layer 1: Render plist template → ~/Library/LaunchAgents/ + launchctl bootstrap
Layer 2: On launchctl failure → write install-state.json + manual instructions
Layer 3: After successful Layer 1 → write install-probe + poll for pong (10s)
"""

import argparse
import json
import os
import string
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path


LABEL = "com.teamwork-leader.auto-resume-daemon"
PLIST_FILENAME = f"{LABEL}.plist"
TEMPLATE_FILENAME = f"{LABEL}.plist.in"
LAUNCH_AGENTS_DIR = Path.home() / "Library" / "LaunchAgents"
MANUAL_INSTALL_DOC = "docs/install/manual-install.md"
PROBE_POLL_INTERVAL = 1  # seconds
PROBE_TIMEOUT = 10  # seconds


def resolve_env() -> dict[str, str]:
    """Resolve CLAUDE_PLUGIN_ROOT and CLAUDE_PROJECT_DIR from environment."""
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    return {
        "CLAUDE_PLUGIN_ROOT": plugin_root,
        "CLAUDE_PROJECT_DIR": project_dir,
    }


def render_plist(plugin_root: str, project_dir: str) -> str:
    """Render plist template using Python string.Template.safe_substitute()."""
    # Locate template relative to this script's directory
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    template_path = repo_root / "templates" / TEMPLATE_FILENAME

    if not template_path.exists():
        print(f"ERROR: plist template not found: {template_path}", file=sys.stderr)
        sys.exit(1)

    template_text = template_path.read_text()
    env_vars = {
        "CLAUDE_PLUGIN_ROOT": plugin_root,
        "CLAUDE_PROJECT_DIR": project_dir,
    }
    rendered = string.Template(template_text).safe_substitute(env_vars)
    return rendered


def write_install_state(project_dir: str, reason: str) -> None:
    """Layer 2: write install-state.json for manual-pending state."""
    teamlead_dir = Path(project_dir) / ".teamlead" if project_dir else Path(".teamlead")
    teamlead_dir.mkdir(parents=True, exist_ok=True)
    state_path = teamlead_dir / "install-state.json"
    state = {
        "status": "manual-pending",
        "reason": reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    state_path.write_text(json.dumps(state, indent=2))
    print(f"[install] Wrote install state: {state_path}")


def print_manual_instructions(plist_dest: Path) -> None:
    """Print manual installation instructions for degraded-mode fallback."""
    print()
    print("=" * 60)
    print("MANUAL INSTALLATION REQUIRED")
    print("=" * 60)
    print()
    print("launchctl bootstrap could not complete automatically.")
    print("To complete installation manually, run:")
    print()
    print(f"  launchctl bootstrap gui/$(id -u) {plist_dest}")
    print()
    print(f"For detailed instructions, see: {MANUAL_INSTALL_DOC}")
    print()
    print("[install] Daemon installer exiting in degraded mode (exit 0).")
    print()


def write_probe_and_poll(project_dir: str) -> None:
    """Layer 3: write install-probe.json + poll for install-probe.pong.json (10s)."""
    teamlead_dir = Path(project_dir) / ".teamlead" if project_dir else Path(".teamlead")
    teamlead_dir.mkdir(parents=True, exist_ok=True)

    probe_id = str(uuid.uuid4())
    probe_path = teamlead_dir / "install-probe.json"
    pong_path = teamlead_dir / "install-probe.pong.json"

    probe_data = {
        "probe_id": probe_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    probe_path.write_text(json.dumps(probe_data, indent=2))
    print(f"[install] Wrote install probe: {probe_path} (probe_id={probe_id})")
    print(f"[install] Polling for pong at {pong_path} (timeout={PROBE_TIMEOUT}s)...")

    deadline = time.monotonic() + PROBE_TIMEOUT
    while time.monotonic() < deadline:
        if pong_path.exists():
            print("[install] Install probe pong received — daemon is responsive.")
            return
        time.sleep(PROBE_POLL_INTERVAL)

    # Timeout — degraded-mode warning, still exit 0
    print()
    print("[install] WARNING: Daemon installed but install-probe pong not received within 10s.")
    print("[install] The daemon may take a moment to start. Installation is considered complete.")
    print()


def cmd_dry_run(args: argparse.Namespace) -> None:
    """--dry-run: render plist to stdout + print intended launchctl bootstrap command."""
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "/path/to/plugin")
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "/path/to/project")

    rendered = render_plist(plugin_root, project_dir)
    plist_dest = LAUNCH_AGENTS_DIR / PLIST_FILENAME

    print("=" * 60)
    print("DRY RUN — Rendered plist (would be written to):")
    print(f"  {plist_dest}")
    print("=" * 60)
    print(rendered)
    print("=" * 60)
    print("DRY RUN — Intended launchctl bootstrap command (NOT executed):")
    print(f"  launchctl bootstrap gui/{os.getuid()} {plist_dest}")
    print("=" * 60)
    print("[install] Dry-run complete. No files written, no launchctl invoked.")


def cmd_uninstall(args: argparse.Namespace) -> None:
    """--uninstall: bootout + plist removal; idempotent."""
    plist_dest = LAUNCH_AGENTS_DIR / PLIST_FILENAME
    uid = os.getuid()

    # Attempt launchctl bootout (idempotent — ignore non-zero if already unloaded)
    print(f"[uninstall] Running: launchctl bootout gui/{uid} {plist_dest}")
    result = subprocess.run(
        ["launchctl", "bootout", f"gui/{uid}", str(plist_dest)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        # Common idempotent errors: service not found / not loaded
        print(f"[uninstall] launchctl bootout returned non-zero (idempotent): {stderr}")
    else:
        print("[uninstall] launchctl bootout succeeded.")

    # Remove plist file (idempotent — no error if already absent)
    if plist_dest.exists():
        plist_dest.unlink()
        print(f"[uninstall] Removed: {plist_dest}")
    else:
        print(f"[uninstall] Plist not present (already removed): {plist_dest}")

    print("[uninstall] Uninstall complete.")


def cmd_install(args: argparse.Namespace) -> None:
    """Default install: Layer 1 → Layer 2 fallback → Layer 3 probe."""
    env = resolve_env()
    plugin_root = env["CLAUDE_PLUGIN_ROOT"]
    project_dir = env["CLAUDE_PROJECT_DIR"]

    # Layer 1: Render plist + write to LaunchAgents
    rendered = render_plist(plugin_root, project_dir)
    LAUNCH_AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    plist_dest = LAUNCH_AGENTS_DIR / PLIST_FILENAME
    plist_dest.write_text(rendered)
    print(f"[install] Rendered plist written: {plist_dest}")

    # Layer 1: launchctl bootstrap
    uid = os.getuid()
    bootstrap_cmd = ["launchctl", "bootstrap", f"gui/{uid}", str(plist_dest)]
    print(f"[install] Running: {' '.join(bootstrap_cmd)}")
    result = subprocess.run(bootstrap_cmd, capture_output=True, text=True)

    if result.returncode != 0:
        stderr = result.stderr.strip()
        print(f"[install] launchctl bootstrap failed (code={result.returncode}): {stderr}", file=sys.stderr)

        # Layer 2: write install-state.json + print manual instructions
        write_install_state(project_dir, stderr or f"launchctl exit {result.returncode}")
        print_manual_instructions(plist_dest)
        # Degraded mode — exit 0 per I-019 guard-tolerance
        sys.exit(0)

    print("[install] launchctl bootstrap succeeded.")

    # Layer 3: write probe + poll for pong
    write_probe_and_poll(project_dir)

    print("[install] Installation complete.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="TeamLead auto-resume-daemon installer"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--dry-run",
        action="store_true",
        help="Render plist to stdout and print intended launchctl command without executing",
    )
    group.add_argument(
        "--uninstall",
        action="store_true",
        help="Unload daemon and remove plist; idempotent",
    )
    args = parser.parse_args()

    if args.dry_run:
        cmd_dry_run(args)
    elif args.uninstall:
        cmd_uninstall(args)
    else:
        cmd_install(args)


if __name__ == "__main__":
    main()
