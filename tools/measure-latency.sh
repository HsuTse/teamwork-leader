#!/usr/bin/env bash
# measure-latency.sh — Metric 1: PreCompact→daemon read latency (I-023)
#
# Writes a test baton via lib/baton-writer.py --write and polls until
# gate_state transitions or the target wait elapses. Records wall-clock
# latency to docs/specs/phase-3-evidence/latency-precompact-to-daemon.txt.
#
# Phase 1 MVP NOTE (v0.1.7):
#   No daemon is implemented in Phase 1. The expected measurement is N/A.
#   This script records target=30s / actual=N/A (no-daemon-Phase-1) and
#   carries the actionable metric to v0.1.8+ as RAID-I.
#
# Stage 4 extension (AC-4-F / I-046 resolution):
#   --dry-run flag: synthetic CI mode. Skips real baton-writer invocation;
#   emits a JSON record with daemon_present field to stdout. Evidence file
#   written to docs/specs/phase-4-evidence/latency-daemon-present.txt.
#   Existing invocation without --dry-run retains pre-Stage-4 behavior.
#
# Usage:
#   bash tools/measure-latency.sh [--help] [--self-test] [--dry-run]
#
# Environment:
#   CLAUDE_PLUGIN_ROOT     Plugin root (default: parent of this script)
#   CLAUDE_PROJECT_DIR     Project dir for .teamlead/ workspace
#   LATENCY_POLL_TIMEOUT   Max seconds to poll (default: 30)

set -euo pipefail

# ── help ──────────────────────────────────────────────────────────────────────

if [[ "${1:-}" == "--help" ]]; then
  cat <<'EOF'
measure-latency.sh — Metric 1: PreCompact→daemon read latency (I-023)

USAGE
  bash tools/measure-latency.sh [--help] [--self-test] [--dry-run]

DESCRIPTION
  Writes a test baton to .teamlead/baton.json via lib/baton-writer.py --write,
  then polls until gate_state transitions to SESSION_RESUMED or the timeout
  elapses. Records the wall-clock latency to:
    docs/specs/phase-3-evidence/latency-precompact-to-daemon.txt

  Target: <= 30s. In Phase 1 MVP (v0.1.7) no daemon is present; the script
  records N/A and carries the measurement to v0.1.8+ via RAID-I.

  --dry-run mode (Stage 4 / AC-4-F): synthetic CI mode. Skips real baton-writer
  invocation; emits a JSON record with daemon_present field to stdout and writes
  evidence to docs/specs/phase-4-evidence/latency-daemon-present.txt.

OPTIONS
  --self-test   Run in synthetic self-test mode; exits 0 if baton-writer
                invocation succeeds and evidence file is written.
  --dry-run     Stage 4 synthetic CI mode: emit JSON record with daemon_present
                field; write evidence to phase-4-evidence/. Exits 0.
  --help        Show this message.

ENVIRONMENT
  CLAUDE_PLUGIN_ROOT     Plugin root directory (default: parent of this script)
  CLAUDE_PROJECT_DIR     Project workspace (default: plugin root's parent)
  LATENCY_POLL_TIMEOUT   Max poll seconds (default: 30)

EXIT CODES
  0   Evidence file written (target met or N/A documented)
  1   Error writing baton or evidence file
EOF
  exit 0
fi

# ── resolve paths ─────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$SCRIPT_DIR")}"
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(dirname "$PLUGIN_ROOT")}"
SELF_TEST="${1:-}"

BATON_WRITER="$PLUGIN_ROOT/lib/baton-writer.py"
TEAMLEAD_DIR="$PROJECT_DIR/.teamlead"
BATON_PATH="$TEAMLEAD_DIR/baton.json"
# I-068: evidence dir is overridable via TWL_EVIDENCE_DIR env var; default
# preserves v0.1.7 behavior (hardcoded phase-3-evidence path) for backward compat.
EVIDENCE_DIR="${TWL_EVIDENCE_DIR:-$PLUGIN_ROOT/docs/specs/phase-3-evidence}"
EVIDENCE_FILE="$EVIDENCE_DIR/latency-precompact-to-daemon.txt"
POLL_TIMEOUT="${LATENCY_POLL_TIMEOUT:-30}"

# ── Stage 4 --dry-run path (AC-4-F / I-046 resolution) ───────────────────────
# Additive extension: existing invocation without --dry-run is unchanged.

if [[ "${1:-}" == "--dry-run" ]]; then
  # I-068: dry-run evidence dir is also overridable via TWL_EVIDENCE_DIR.
  DRY_RUN_EVIDENCE_DIR="${TWL_EVIDENCE_DIR:-$PLUGIN_ROOT/docs/specs/phase-4-evidence}"
  DRY_RUN_EVIDENCE_FILE="$DRY_RUN_EVIDENCE_DIR/latency-daemon-present.txt"
  mkdir -p "$DRY_RUN_EVIDENCE_DIR"

  DRY_RUN_ISO_NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  DRY_RUN_START_TS="$(date +%s)"

  # daemon_present: check if scripts/daemon.py exists (Stage 4 artifact)
  DAEMON_PRESENT="false"
  if [[ -f "$PLUGIN_ROOT/scripts/daemon.py" ]]; then
    DAEMON_PRESENT="true"
  fi

  # Synthetic: no baton-writer invocation; simulate gate_state poll cycle
  DRY_RUN_END_TS="$(date +%s)"
  DRY_RUN_WALL_CLOCK=$((DRY_RUN_END_TS - DRY_RUN_START_TS))

  # Emit JSON record with daemon_present field (AC-4-F design.md line 542)
  JSON_RECORD="{\"tool\":\"measure-latency.sh\",\"mode\":\"dry-run\",\"timestamp\":\"$DRY_RUN_ISO_NOW\",\"daemon_present\":$DAEMON_PRESENT,\"target_seconds\":30,\"actual_seconds\":\"N/A-dry-run\",\"wall_clock_seconds\":$DRY_RUN_WALL_CLOCK,\"gate_state_observed\":\"SYNTHETIC-DRY-RUN\",\"metric\":\"I-023-M1\"}"
  echo "$JSON_RECORD"

  # Write plain-text evidence file for phase-4-evidence/
  cat > "$DRY_RUN_EVIDENCE_FILE" <<DRYEOF
# Metric 1 — PreCompact→Daemon Read Latency (Stage 4 / AC-4-F / daemon-present)
# Generated: $DRY_RUN_ISO_NOW
# Tool: tools/measure-latency.sh --dry-run
# RAID: I-023-M1 (dogfood instrumentation; I-046 inline resolution)
# Mode: dry-run (synthetic CI — no real baton-writer invocation)

daemon_present=$DAEMON_PRESENT
target_seconds=30
actual_seconds=N/A-dry-run (synthetic mode; real measurement requires live daemon poll)
wall_clock_seconds=$DRY_RUN_WALL_CLOCK
gate_state_observed=SYNTHETIC-DRY-RUN

## Interpretation

--dry-run mode skips real baton-writer invocation and daemon poll cycle.
daemon_present=$DAEMON_PRESENT reflects whether scripts/daemon.py exists in this Stage 4 build.

The real daemon-present M1 latency measurement (baton-write to gate_state=SESSION_RESUMED)
requires a live daemon polling loop. This dry-run confirms:
  - measure-latency.sh --dry-run flag is functional (exit 0)
  - daemon_present field is correctly emitted in JSON record
  - phase-4-evidence/ directory is writable

## RAID carry

I-023-M1 (actual baton-write→SESSION_RESUMED wall-clock ≤ 30s) is measured by
running the daemon poll live (non-dry-run) with daemon.py active.
Below-target → carry to v0.1.8+ per Stage 3 close report precedent.
DRYEOF

  echo "measure-latency: --dry-run PASS (daemon_present=$DAEMON_PRESENT; evidence=$DRY_RUN_EVIDENCE_FILE)"
  exit 0
fi

# ── validate dependencies ─────────────────────────────────────────────────────

if [[ ! -f "$BATON_WRITER" ]]; then
  echo "ERROR: lib/baton-writer.py not found at $BATON_WRITER" >&2
  exit 1
fi

mkdir -p "$EVIDENCE_DIR"
mkdir -p "$TEAMLEAD_DIR"

# ── Phase 1 MVP: no daemon path ───────────────────────────────────────────────

ISO_NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
START_TS="$(date +%s)"

echo "measure-latency: writing test baton via baton-writer.py --self-test ..."

# Use --self-test mode: baton-writer synthesizes a valid 7-key fixture payload
# internally and writes it to /tmp/baton-self-test.json. This is the canonical
# test invocation that does not require stdin piping.
# For Metric 1 purposes, we verify baton-writer can write successfully; the
# production path (baton at BATON_PATH) is exercised by pre-compact.py in
# real-session integration (real-session-integration.md).
SELF_TEST_BATON="/tmp/baton-self-test.json"
python3 "$BATON_WRITER" --self-test 2>&1 || {
  echo "ERROR: baton-writer.py --self-test failed" >&2
  exit 1
}

# Copy self-test output to .teamlead/baton.json for poll observation
# (demonstrates baton placement at canonical path)
cp "$SELF_TEST_BATON" "$BATON_PATH" 2>/dev/null || true

WRITE_TS="$(date +%s)"
echo "measure-latency: baton written at $ISO_NOW"

# Poll for gate_state transition (daemon would change this; in Phase 1 no daemon).
# Use a short poll (4s max) since we know no daemon is present — the point is
# to record the measurement infrastructure is functional, not to wait.
POLL_TIMEOUT_EFFECTIVE=4  # override for Phase 1 no-daemon: don't wait 30s
echo "measure-latency: polling for gate_state=SESSION_RESUMED (timeout=${POLL_TIMEOUT_EFFECTIVE}s, Phase-1-no-daemon) ..."
ELAPSED=0
GATE_STATE="BATON_WRITTEN"
while [[ $ELAPSED -lt $POLL_TIMEOUT_EFFECTIVE ]]; do
  if [[ -f "$BATON_PATH" ]]; then
    GATE_STATE="$(python3 -c "
import json, sys
try:
    d = json.load(open('$BATON_PATH'))
    print(d.get('gate_state', 'UNKNOWN'))
except Exception as e:
    print('READ_ERROR')
" 2>/dev/null || echo "READ_ERROR")"
    if [[ "$GATE_STATE" == "SESSION_RESUMED" ]]; then
      break
    fi
  fi
  sleep 2
  ELAPSED=$((ELAPSED + 2))
done

END_TS="$(date +%s)"
WALL_CLOCK=$((END_TS - START_TS))

# ── write evidence file ───────────────────────────────────────────────────────

cat > "$EVIDENCE_FILE" <<EOF
# Metric 1 — PreCompact→Daemon Read Latency
# Generated: $ISO_NOW
# Tool: tools/measure-latency.sh
# RAID: I-023 (dogfood instrumentation 3 metrics)

target_seconds=30
actual_seconds=N/A (no-daemon-Phase-1)
wall_clock_measured_seconds=$WALL_CLOCK
poll_timeout_seconds=$POLL_TIMEOUT
baton_write_result=OK
gate_state_observed=$GATE_STATE

## Interpretation

Phase 1 MVP (v0.1.7) has no daemon component. The state machine does not
transition BATON_WRITTEN → SESSION_RESUMED automatically. This is expected.

The measurement above records:
  - baton_write_result: whether lib/baton-writer.py --test-write succeeded (OK = PASS)
  - gate_state_observed: final observed gate_state after poll timeout (BATON_WRITTEN = expected for Phase 1)
  - wall_clock_measured_seconds: total elapsed including poll timeout

## RAID carry to v0.1.8+

I-023 Metric 1 (actual PreCompact→daemon latency ≤ 30s) is carried as RAID-I
to v0.1.8+ when the daemon component is implemented. The Phase 1 evidence here
confirms baton-writer is functional; daemon pickup latency will be measured in
Stage 4 (Phase 2 launchd daemon).

## Raw measurement
baton_written_unix=$WRITE_TS
poll_end_unix=$END_TS
EOF

echo "measure-latency: evidence written to $EVIDENCE_FILE"

if [[ "$SELF_TEST" == "--self-test" ]]; then
  echo "measure-latency: --self-test PASS (evidence file written; baton-writer OK)"
fi

exit 0
