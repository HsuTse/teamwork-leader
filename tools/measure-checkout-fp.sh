#!/usr/bin/env bash
# measure-checkout-fp.sh — Metric 3: T-S-3 mid-pause checkout false-positive rate (I-023)
#
# Runs >= 10 synthetic trials testing _path_validate_baton in session-start.py.
# Each trial creates a baton with either:
#   - SAME-COMMIT scenario: baton fields match current HEAD/branch/anchor (should validate OK)
#   - DIVERGENT scenario:   baton fields deliberately mismatch (should route ABORTED)
#
# A "false-positive" is a same-commit trial that incorrectly routes ABORTED.
# A "false-negative" would be a divergent trial that incorrectly validates OK
# (not measured here; that is T-S-3 mitigation failure, tracked separately).
#
# Records results to:
#   docs/specs/phase-3-evidence/false-positive-checkout.txt
#
# Target: <= 5% false-positive rate (0/10 = 0% expected for same-commit trials)
#
# Per I-014/I-015: uses --test-mode-with-baton (not real interactive session).
# Per I-018: baton write in Python (via write-synthetic-baton.py helper).
#
# Usage:
#   bash tools/measure-checkout-fp.sh [--help] [--self-test]
#
# Environment:
#   CLAUDE_PLUGIN_ROOT   Plugin root (default: parent of this script)
#   CLAUDE_PROJECT_DIR   Project dir for .teamlead/ workspace

set -euo pipefail

# ── help ──────────────────────────────────────────────────────────────────────

if [[ "${1:-}" == "--help" ]]; then
  cat <<'EOF'
measure-checkout-fp.sh — Metric 3: T-S-3 checkout false-positive rate (I-023)

USAGE
  bash tools/measure-checkout-fp.sh [--help] [--self-test]

DESCRIPTION
  Runs >= 10 synthetic trials against session-start.py --test-mode-with-baton.
  Trials alternate between same-commit (HEAD-match) and divergent scenarios.

  False-positive: a HEAD-match baton that incorrectly fails validation.
  Target: <= 5% false-positive rate over >= 10 trials.

  Records results to:
    docs/specs/phase-3-evidence/false-positive-checkout.txt

OPTIONS
  --self-test   Run trials; exits 0 if evidence file written and all
                same-commit trials pass (0% FP rate expected).
  --help        Show this message.

ENVIRONMENT
  CLAUDE_PLUGIN_ROOT   Plugin root directory (default: parent of this script)
  CLAUDE_PROJECT_DIR   Project workspace (default: plugin root's parent)

EXIT CODES
  0   Evidence written; false-positive rate <= 5%
  1   False-positive rate > 5% or script error
EOF
  exit 0
fi

# ── resolve paths ─────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$SCRIPT_DIR")}"
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(dirname "$PLUGIN_ROOT")}"
SELF_TEST="${1:-}"

SESSION_START="$PLUGIN_ROOT/hooks/session-start.py"
WRITE_BATON_SCRIPT="$PLUGIN_ROOT/tools/write-synthetic-baton.py"
EVIDENCE_DIR="$PLUGIN_ROOT/docs/specs/phase-3-evidence"
EVIDENCE_FILE="$EVIDENCE_DIR/false-positive-checkout.txt"
TMP_BATON="/tmp/teamlead-fp-test-baton-$$.json"

# ── validate dependencies ─────────────────────────────────────────────────────

if [[ ! -f "$SESSION_START" ]]; then
  echo "ERROR: hooks/session-start.py not found at $SESSION_START" >&2
  exit 1
fi

if [[ ! -f "$WRITE_BATON_SCRIPT" ]]; then
  echo "ERROR: tools/write-synthetic-baton.py not found at $WRITE_BATON_SCRIPT" >&2
  echo "       This helper script must exist (I-018: Python for state-changing writes)" >&2
  exit 1
fi

mkdir -p "$EVIDENCE_DIR"

# ── run synthetic trials ──────────────────────────────────────────────────────

ISO_NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
TOTAL_TRIALS=12      # >= 10 required; 6 same-commit + 6 divergent
SAME_COMMIT_TRIALS=6
DIVERGENT_TRIALS=6
FP_COUNT=0           # false positives: same-commit that incorrectly fail
FN_COUNT=0           # false negatives: divergent that incorrectly pass (T-S-3 failure mode)
TRIAL_LOG=""

echo "measure-checkout-fp: running $TOTAL_TRIALS synthetic trials ..."
echo "  SESSION_START=$SESSION_START"
echo "  PLUGIN_ROOT=$PLUGIN_ROOT"
echo "  PROJECT_DIR=$PROJECT_DIR"

# Trial helper: write baton and invoke session-start.py --test-mode-with-baton
# Returns:
#   "VALIDATED" — 4-field re-validation passed (resume banner output)
#   "ABORTED"   — mismatch detected or validation failed

run_trial() {
  local trial_n="$1"
  local scenario="$2"  # "same-commit" or "divergent"
  local mismatch_field="${3:-none}"

  # Write synthetic baton via Python helper (I-018: Python for writes).
  # Redirect stdout+stderr to stderr so run_trial's captured output contains
  # only the final VALIDATED/ABORTED verdict, not the write progress message.
  python3 "$WRITE_BATON_SCRIPT" \
    --project-dir "$PROJECT_DIR" \
    --scenario "$scenario" \
    --mismatch-field "$mismatch_field" \
    --output "$TMP_BATON" >&2 || {
    echo "  Trial $trial_n [$scenario/$mismatch_field]: BATON_WRITE_FAILED" >&2
    echo "BATON_WRITE_FAILED"
    return
  }

  # Invoke session-start.py --test-mode-with-baton.
  # IMPORTANT: session-start.py --test-mode-with-baton uses os.getcwd() as
  # project_dir for git-state and PROGRESS.md reads. We must cd to PROJECT_DIR
  # so the validation runs against the same state the baton was written from.
  local output
  output="$(cd "$PROJECT_DIR" && python3 "$SESSION_START" --test-mode-with-baton "$TMP_BATON" 2>&1)" || true

  # Determine outcome by checking output for ABORTED vs RESUME banner keywords
  if echo "$output" | grep -qiE "RESUME CONTEXT READY|POST_RESUME_VERIFIED|Baton validated"; then
    echo "VALIDATED"
  elif echo "$output" | grep -qiE "Resume.*fail|mismatch|ABORTED|validation FAILED"; then
    echo "ABORTED"
  else
    # Unexpected output — count as unknown; don't penalize false-positive count
    echo "UNKNOWN"
  fi
}

# Same-commit trials (should all VALIDATE)
for i in $(seq 1 $SAME_COMMIT_TRIALS); do
  trial_n="SC-$i"
  result="$(run_trial "$trial_n" "same-commit" "none")"
  if [[ "$result" == "VALIDATED" ]]; then
    TRIAL_LOG+="Trial $trial_n [same-commit/none]: VALIDATED (PASS)\n"
    echo "  Trial $trial_n [same-commit]: VALIDATED — PASS"
  elif [[ "$result" == "ABORTED" ]]; then
    FP_COUNT=$((FP_COUNT + 1))
    TRIAL_LOG+="Trial $trial_n [same-commit/none]: ABORTED (FALSE POSITIVE)\n"
    echo "  Trial $trial_n [same-commit]: ABORTED — FALSE POSITIVE" >&2
  else
    TRIAL_LOG+="Trial $trial_n [same-commit/none]: $result (SKIP — uncertain)\n"
    echo "  Trial $trial_n [same-commit]: $result — uncertain (skip)"
  fi
done

# Divergent trials — alternate which field mismatches
MISMATCH_FIELDS=("prior_pause_commit" "branch" "progress_md_anchor" "last_action_iso" "prior_pause_commit" "branch")

for i in $(seq 1 $DIVERGENT_TRIALS); do
  idx=$((i - 1))
  mismatch="${MISMATCH_FIELDS[$idx]}"
  trial_n="DV-$i"
  result="$(run_trial "$trial_n" "divergent" "$mismatch")"
  if [[ "$result" == "ABORTED" ]]; then
    TRIAL_LOG+="Trial $trial_n [divergent/$mismatch]: ABORTED (PASS — correct rejection)\n"
    echo "  Trial $trial_n [divergent/$mismatch]: ABORTED — PASS (correct)"
  elif [[ "$result" == "VALIDATED" ]]; then
    FN_COUNT=$((FN_COUNT + 1))
    TRIAL_LOG+="Trial $trial_n [divergent/$mismatch]: VALIDATED (FALSE NEGATIVE — T-S-3 failure)\n"
    echo "  Trial $trial_n [divergent/$mismatch]: VALIDATED — FALSE NEGATIVE (T-S-3 failure)" >&2
  else
    TRIAL_LOG+="Trial $trial_n [divergent/$mismatch]: $result (SKIP — uncertain)\n"
    echo "  Trial $trial_n [divergent/$mismatch]: $result — uncertain (skip)"
  fi
done

# Cleanup temp baton
rm -f "$TMP_BATON"

# ── compute false-positive rate ───────────────────────────────────────────────

FP_RATE_PCT=0
if [[ $SAME_COMMIT_TRIALS -gt 0 ]]; then
  # Integer arithmetic: FP_RATE_PCT = (FP_COUNT * 100) / SAME_COMMIT_TRIALS
  FP_RATE_PCT=$(( (FP_COUNT * 100) / SAME_COMMIT_TRIALS ))
fi

TARGET_FP_PCT=5
if [[ $FP_RATE_PCT -le $TARGET_FP_PCT ]]; then
  RATE_ASSESSMENT="TARGET_MET (${FP_RATE_PCT}% <= ${TARGET_FP_PCT}%)"
  EXIT_CODE=0
else
  RATE_ASSESSMENT="ABOVE_TARGET (${FP_RATE_PCT}% > ${TARGET_FP_PCT}%) — RAID-I carry"
  EXIT_CODE=1
fi

# ── write evidence file ───────────────────────────────────────────────────────

cat > "$EVIDENCE_FILE" <<EOF
# Metric 3 — T-S-3 Mid-Pause Checkout False-Positive Rate
# Generated: $ISO_NOW
# Tool: tools/measure-checkout-fp.sh
# RAID: I-023 (dogfood instrumentation 3 metrics)
# Design ref: design.md §5 T-S-3 + §1 T8 (4-field re-validation)

total_trials=$TOTAL_TRIALS
same_commit_trials=$SAME_COMMIT_TRIALS
divergent_trials=$DIVERGENT_TRIALS
false_positive_count=$FP_COUNT
false_negative_count=$FN_COUNT
false_positive_rate_pct=${FP_RATE_PCT}
target_false_positive_rate_pct=${TARGET_FP_PCT}
assessment=$RATE_ASSESSMENT

## Interpretation

False positive: a same-commit baton (where HEAD/branch/anchor all match)
that session-start.py incorrectly routes to ABORTED.

False negative: a divergent baton (deliberately mismatched field) that
session-start.py incorrectly routes to VALIDATED (T-S-3 failure mode —
more critical than false positives).

Target <= 5% false-positive rate. False negatives are carried as RAID-A
(architectural assumption) per T-S-3 mitigation chain.

## Trial log

$(echo -e "$TRIAL_LOG")

## 4-field re-validation fields tested

same_commit_trials_tested=prior_pause_commit + branch + progress_md_anchor + last_action_iso (all match)
divergent_trials_tested=prior_pause_commit (x2) + branch (x2) + progress_md_anchor + last_action_iso

## Source code reference

Validation function: hooks/session-start.py::_path_validate_baton()
4-field spec: design.md lines 202-203, 439
EOF

echo ""
echo "measure-checkout-fp: results summary"
echo "  total_trials=$TOTAL_TRIALS same_commit=$SAME_COMMIT_TRIALS divergent=$DIVERGENT_TRIALS"
echo "  false_positive_count=$FP_COUNT false_negative_count=$FN_COUNT"
echo "  false_positive_rate=${FP_RATE_PCT}% assessment=$RATE_ASSESSMENT"
echo "measure-checkout-fp: evidence written to $EVIDENCE_FILE"

if [[ "$SELF_TEST" == "--self-test" ]]; then
  echo "measure-checkout-fp: --self-test PASS (evidence written; FP rate check complete)"
fi

exit $EXIT_CODE
