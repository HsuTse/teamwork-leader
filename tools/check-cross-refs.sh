#!/usr/bin/env bash
# check-cross-refs.sh — I-033 mitigation: validate hook→lib cross-references
#
# For each hook script in hooks/, extract every "lib/<name>.py" reference and
# verify the referenced file exists in lib/ relative to the plugin root.
# Exits non-zero if any reference is broken.
#
# Usage:
#   bash tools/check-cross-refs.sh [--help]
#
# Environment:
#   CLAUDE_PLUGIN_ROOT — plugin root (default: parent of this script's dir)
#
# I-033 mitigation: cross-script-file drift detection; SOURCE-OF-TRUTH for
#   hook→lib consistency validation per T-3-9 acceptance criterion (e).

set -euo pipefail

# ── help ──────────────────────────────────────────────────────────────────────

if [[ "${1:-}" == "--help" ]]; then
  cat <<'EOF'
check-cross-refs.sh — Validate hook→lib cross-references (I-033 mitigation)

USAGE
  bash tools/check-cross-refs.sh [--help]

DESCRIPTION
  Greps all 3 hook scripts (hooks/pre-compact.py, hooks/session-start.py,
  hooks/stop.py) for "lib/<name>.py" references and verifies each referenced
  file exists at lib/<name>.py relative to CLAUDE_PLUGIN_ROOT.

  Exits 0 if all references resolve. Exits non-zero if any are broken.
  Prints a summary of all checked references and their status.

ENVIRONMENT
  CLAUDE_PLUGIN_ROOT  Plugin root directory (default: parent of this script)

EXIT CODES
  0   All references resolve correctly
  1   One or more broken references detected
  2   Script usage error
EOF
  exit 0
fi

# ── resolve plugin root ───────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$SCRIPT_DIR")}"

HOOKS_DIR="$PLUGIN_ROOT/hooks"
LIB_DIR="$PLUGIN_ROOT/lib"

# ── validate dirs exist ───────────────────────────────────────────────────────

if [[ ! -d "$HOOKS_DIR" ]]; then
  echo "ERROR: hooks/ directory not found at $HOOKS_DIR" >&2
  exit 1
fi

if [[ ! -d "$LIB_DIR" ]]; then
  echo "ERROR: lib/ directory not found at $LIB_DIR" >&2
  exit 1
fi

# ── check each hook script ────────────────────────────────────────────────────

HOOK_SCRIPTS=("pre-compact.py" "session-start.py" "stop.py")
exit_code=0
total_refs=0
broken_refs=0

echo "check-cross-refs: scanning hooks/ → lib/ references"
echo "  PLUGIN_ROOT=$PLUGIN_ROOT"
echo ""

for hook in "${HOOK_SCRIPTS[@]}"; do
  hook_path="$HOOKS_DIR/$hook"

  if [[ ! -f "$hook_path" ]]; then
    echo "ERROR: hook script missing: $hook_path" >&2
    exit_code=1
    continue
  fi

  # Extract all lib/<name>.py references (deduplicated, sorted).
  # Regex covers: lowercase letters, uppercase letters, digits, hyphens, underscores
  # for forward-compatibility with lib script names that may use those characters.
  refs=$(grep -oE 'lib/[a-zA-Z0-9_-]+\.py' "$hook_path" | sort -u || true)

  if [[ -z "$refs" ]]; then
    echo "  [$hook] — no lib/ references found"
    continue
  fi

  while IFS= read -r ref; do
    lib_name="${ref#lib/}"
    lib_path="$LIB_DIR/$lib_name"
    total_refs=$((total_refs + 1))

    if [[ -f "$lib_path" ]]; then
      echo "  [$hook] $ref → OK ($lib_path)"
    else
      echo "  [$hook] $ref → BROKEN (expected: $lib_path)" >&2
      exit_code=1
      broken_refs=$((broken_refs + 1))
    fi
  done <<< "$refs"
done

echo ""
echo "check-cross-refs: $total_refs references checked; $broken_refs broken"

exit "$exit_code"
