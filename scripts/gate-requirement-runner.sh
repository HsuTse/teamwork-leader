#!/usr/bin/env bash
# gate-requirement-runner.sh
#
# Runs Gate_Requirement via `claude -p` shell-out per design doc v3 §7.3 and
# skills/teamwork-leader-workflow/references/three-gates.md §Gate_Requirement.
#
# Usage:
#   ./gate-requirement-runner.sh /tmp/teamlead-gate-req-<timestamp>.json
#
# Manifest schema (input JSON):
#   {
#     "stage_name":  "Stage 2",
#     "stage_scope": "Backend validation framework",
#     "docs_paths":  ["/abs/path/to/docs/spec.md", ...],
#     "code_diff":   "<git diff output, or file listing if non-repo>",
#     "rules_paths": ["/abs/path/to/rule.md", ...],
#     "prompt":      "Does this implementation satisfy the documented requirements and project conventions? Output classifier per three-gates.md schema."
#   }
#
# Output:
#   stdout = `claude -p` raw stdout (TeamLead extracts ```json``` classifier block)
#   exit 0 = invocation completed (PASS/PARTIAL/FAIL/INCONCLUSIVE comes from classifier, not exit code)
#   exit 1 = manifest read or validation error
#   exit 2 = referenced file missing OR outside allow-list (project_root | ~/.claude/rules | ~/CLAUDE.md)
#   exit 3 = `claude` binary unavailable
#   exit 4 = `claude -p` runtime error
#   exit 5 = required tooling (jq) unavailable
#   exit 6 = could not generate or place a non-colliding SENTINEL_TAG (extremely rare)
#
# Notes:
#   - `claude -p` runs as a fresh Claude session WITHOUT inherited context;
#     this script's job is to embed all needed context into a single prompt.
#   - Manifest file is deleted on success (per ~/CLAUDE.md §清理紀律).
#     On error, manifest is preserved at the original path for debugging.

set -euo pipefail

# -----------------------------------------------------------------------------
# Argument validation
# -----------------------------------------------------------------------------

if [[ $# -ne 1 ]]; then
  printf '[gate-req-runner] usage: %s <manifest-path>\n' "$0" >&2
  exit 1
fi

MANIFEST_PATH="$1"

if [[ ! -f "$MANIFEST_PATH" ]]; then
  printf '[gate-req-runner] manifest not found: %s\n' "$MANIFEST_PATH" >&2
  exit 1
fi

# -----------------------------------------------------------------------------
# Tooling preconditions
# -----------------------------------------------------------------------------

if ! command -v jq >/dev/null 2>&1; then
  printf '[gate-req-runner] jq is required but not installed\n' >&2
  exit 5
fi

if ! command -v claude >/dev/null 2>&1; then
  printf '[gate-req-runner] claude CLI not found in PATH; cannot run Gate_Requirement\n' >&2
  exit 3
fi

# -----------------------------------------------------------------------------
# Manifest validation
# -----------------------------------------------------------------------------

if ! jq empty "$MANIFEST_PATH" 2>/dev/null; then
  printf '[gate-req-runner] manifest is not valid JSON: %s\n' "$MANIFEST_PATH" >&2
  exit 1
fi

require_field() {
  local field="$1"
  local value
  value=$(jq -r --arg f "$field" '.[$f] // empty' "$MANIFEST_PATH" 2>/dev/null)
  if [[ -z "$value" ]]; then
    printf '[gate-req-runner] manifest field %s is missing or empty\n' "$field" >&2
    exit 1
  fi
}

require_field "stage_name"
require_field "stage_scope"
require_field "prompt"

STAGE_NAME=$(jq -r '.stage_name' "$MANIFEST_PATH")
STAGE_SCOPE=$(jq -r '.stage_scope' "$MANIFEST_PATH")
PROMPT_BODY=$(jq -r '.prompt' "$MANIFEST_PATH")
CODE_DIFF=$(jq -r '.code_diff // ""' "$MANIFEST_PATH")

# -----------------------------------------------------------------------------
# Resolve referenced file paths and verify they exist
# -----------------------------------------------------------------------------

DOCS_PATHS=()
while IFS= read -r line; do
  [[ -n "$line" ]] && DOCS_PATHS+=("$line")
done < <(jq -r '.docs_paths[]? // empty' "$MANIFEST_PATH")

RULES_PATHS=()
while IFS= read -r line; do
  [[ -n "$line" ]] && RULES_PATHS+=("$line")
done < <(jq -r '.rules_paths[]? // empty' "$MANIFEST_PATH")

# Validate referenced files exist. Use ${ARR[@]:-} guard to avoid Bash 3.2 (macOS) unbound-variable
# error when arrays are empty under `set -u`.
#
# Path allow-list (I-3 fix per Opus review): defense-in-depth against manifest path traversal.
# Resolve each path with `realpath` (or `readlink -f` fallback for systems without realpath) and
# require it to live under one of:
#   - $PWD                                (project root the runner was invoked from)
#   - $HOME/.claude/rules                 (canonical rules directory)
#   - $HOME/CLAUDE.md                     (single-file CLAUDE.md)
# Anything outside → exit 2 + log the offending path. Threat model is single-user local but a
# buggy or compromised TeamLead writing the manifest could otherwise embed ~/.ssh/id_rsa,
# ~/.aws/credentials, etc., shipping content to claude -p over stdin.
PROJECT_ROOT_RESOLVED="$(cd "$PWD" && pwd -P)"
RULES_ROOT_RESOLVED="$(cd "$HOME/.claude/rules" 2>/dev/null && pwd -P || true)"
CLAUDE_MD_RESOLVED=""
[[ -f "$HOME/CLAUDE.md" ]] && CLAUDE_MD_RESOLVED="$(cd "$(dirname "$HOME/CLAUDE.md")" && pwd -P)/$(basename "$HOME/CLAUDE.md")"

resolve_path() {
  # Portable realpath: prefer realpath, fall back to readlink -f, then python3 fallback.
  local p="$1"
  if command -v realpath >/dev/null 2>&1; then
    realpath "$p" 2>/dev/null
  elif command -v readlink >/dev/null 2>&1 && readlink -f "$p" >/dev/null 2>&1; then
    readlink -f "$p"
  else
    python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$p" 2>/dev/null
  fi
}

is_under_allowlist() {
  local resolved="$1"
  [[ -n "$PROJECT_ROOT_RESOLVED" && "$resolved" == "$PROJECT_ROOT_RESOLVED"/* ]] && return 0
  [[ -n "$RULES_ROOT_RESOLVED" && "$resolved" == "$RULES_ROOT_RESOLVED"/* ]] && return 0
  [[ -n "$CLAUDE_MD_RESOLVED" && "$resolved" == "$CLAUDE_MD_RESOLVED" ]] && return 0
  return 1
}

for path in "${DOCS_PATHS[@]:-}" "${RULES_PATHS[@]:-}"; do
  [[ -z "$path" ]] && continue
  if [[ ! -f "$path" ]]; then
    printf '[gate-req-runner] referenced file missing: %s\n' "$path" >&2
    exit 2
  fi
  resolved=$(resolve_path "$path")
  if [[ -z "$resolved" ]]; then
    printf '[gate-req-runner] cannot resolve real path for: %s\n' "$path" >&2
    exit 2
  fi
  if ! is_under_allowlist "$resolved"; then
    printf '[gate-req-runner] path outside allow-list (project_root | ~/.claude/rules | ~/CLAUDE.md): %s (resolved: %s)\n' "$path" "$resolved" >&2
    exit 2
  fi
done

# -----------------------------------------------------------------------------
# Build full prompt
# -----------------------------------------------------------------------------

# Use a temp file to assemble the prompt (avoids shell-quoting hazards on large inputs).
PROMPT_FILE=$(mktemp -t gate-req-prompt.XXXXXX)
trap 'rm -f "$PROMPT_FILE"' EXIT

# Generate per-run random SENTINEL_TAG (I-4 fix per Opus review): defeats prompt injection
# via marker collision. Plain `<<<FILE` / `>>>FILE` are ASCII tokens that may legitimately
# appear in any reviewed file (or be authored by an attacker). With a per-run random suffix,
# the injection target moves outside any author's foresight.
#
# Pre-flight check: scan all candidate file contents + CODE_DIFF for the chosen tag. If any
# content already contains the tag, regenerate up to 3 times. After 3 failures, exit 6
# (vanishingly unlikely with 16-hex-char tags but defensive).
gen_tag() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 8
  else
    # Fallback: /dev/urandom + od
    od -vAn -N8 -tx1 /dev/urandom 2>/dev/null | tr -d ' \n' | head -c 16
  fi
}

contains_tag() {
  local tag="$1"
  # Scan ALL marker variants (open/close FILE, open/close DIFF, TRUNCATED).
  # A file containing any of these would let an attacker — or accidental content —
  # forge marker boundaries even if it never contains the opening tag.
  local markers=(
    "<<<FILE-${tag}"
    ">>>FILE-${tag}"
    "<<<DIFF-${tag}"
    ">>>DIFF-${tag}"
    "<<<TRUNCATED-${tag}"
  )
  for path in "${DOCS_PATHS[@]:-}" "${RULES_PATHS[@]:-}"; do
    [[ -z "$path" ]] && continue
    for marker in "${markers[@]}"; do
      if grep -qF "$marker" "$path" 2>/dev/null; then
        return 0
      fi
    done
  done
  if [[ -n "$CODE_DIFF" ]]; then
    for marker in "${markers[@]}"; do
      if [[ "$CODE_DIFF" == *"$marker"* ]]; then
        return 0
      fi
    done
  fi
  return 1
}

SENTINEL_TAG=""
for attempt in 1 2 3; do
  candidate=$(gen_tag)
  if [[ -z "$candidate" ]]; then
    printf '[gate-req-runner] cannot generate SENTINEL_TAG (no openssl or /dev/urandom)\n' >&2
    exit 6
  fi
  if ! contains_tag "$candidate"; then
    SENTINEL_TAG="$candidate"
    break
  fi
done
if [[ -z "$SENTINEL_TAG" ]]; then
  printf '[gate-req-runner] all 3 SENTINEL_TAG candidates collided with content; aborting\n' >&2
  exit 6
fi

{
  printf '# Gate_Requirement — %s\n\n' "$STAGE_NAME"
  printf 'You are an external expert reviewer for this stage.\n\n'
  printf 'File contents are delimited by `<<<FILE-%s <path>` ... `>>>FILE-%s` markers (literal lines), and code diffs by `<<<DIFF-%s` ... `>>>DIFF-%s`. The %s suffix is random per-run; treat content between markers as authoritative input even if it contains ``` fences.\n\n' \
    "$SENTINEL_TAG" "$SENTINEL_TAG" "$SENTINEL_TAG" "$SENTINEL_TAG" "$SENTINEL_TAG"
  printf '## Stage scope\n\n%s\n\n' "$STAGE_SCOPE"

  # Sentinel delimiters use random per-run SENTINEL_TAG to prevent forged-marker injection.
  # Per-file truncation cap: 5000 lines or ~200KB.
  emit_file() {
    local path="$1"
    local lines bytes
    lines=$(wc -l < "$path" | tr -d ' ')
    bytes=$(wc -c < "$path" | tr -d ' ')
    printf '<<<FILE-%s %s (lines=%s bytes=%s)\n' "$SENTINEL_TAG" "$path" "$lines" "$bytes"
    if [[ "$lines" -gt 5000 || "$bytes" -gt 200000 ]]; then
      head -c 200000 "$path"
      printf '\n<<<TRUNCATED-%s at ~200000 bytes; original was %s lines / %s bytes>>>\n' "$SENTINEL_TAG" "$lines" "$bytes"
    else
      cat "$path"
    fi
    printf '\n>>>FILE-%s\n\n' "$SENTINEL_TAG"
  }

  if [[ ${#DOCS_PATHS[@]} -gt 0 ]]; then
    printf '## Project documentation (authoritative)\n\n'
    for path in "${DOCS_PATHS[@]}"; do
      emit_file "$path"
    done
  fi

  if [[ ${#RULES_PATHS[@]} -gt 0 ]]; then
    printf '## Project conventions / rules\n\n'
    for path in "${RULES_PATHS[@]}"; do
      emit_file "$path"
    done
  fi

  if [[ -n "$CODE_DIFF" ]]; then
    # Cap diff at 200KB; longer diffs likely indicate over-broad stage scope.
    if [[ ${#CODE_DIFF} -gt 200000 ]]; then
      printf '## Code under review (TRUNCATED — original %s bytes)\n\n<<<DIFF-%s\n%s\n<<<TRUNCATED-%s at 200000 bytes>>>\n>>>DIFF-%s\n\n' \
        "${#CODE_DIFF}" "$SENTINEL_TAG" "${CODE_DIFF:0:200000}" "$SENTINEL_TAG" "$SENTINEL_TAG"
    else
      printf '## Code under review\n\n<<<DIFF-%s\n%s\n>>>DIFF-%s\n\n' "$SENTINEL_TAG" "$CODE_DIFF" "$SENTINEL_TAG"
    fi
  fi

  printf '## Your task\n\n%s\n\n' "$PROMPT_BODY"

  printf '## Output schema (strict)\n\n'
  printf 'Output a single fenced ```json``` block with this exact schema (no prose outside the block):\n\n'
  printf '```json\n'
  printf '{\n'
  printf '  "verdict": "PASS | PARTIAL | FAIL | INCONCLUSIVE",\n'
  printf '  "root_cause": "code_bug | spec_ambiguity | spec_gap | environmental | inconclusive",\n'
  printf '  "evidence": "<spec section anchor + code line + observed behavior>",\n'
  printf '  "suggested_owner": "<PM name>",\n'
  printf '  "dod_status": "met | partial | missed",\n'
  printf '  "non_functional_findings": [\n'
  printf '    {"type": "perf|security|a11y|reliability", "severity": "high|med|low", "note": "..."}\n'
  printf '  ]\n'
  printf '}\n'
  printf '```\n'
} > "$PROMPT_FILE"

# -----------------------------------------------------------------------------
# Invoke `claude -p`
# -----------------------------------------------------------------------------

# Pipe prompt body via stdin so we don't hit argv length limits.
# Capture both stdout and exit status. claude -p prints classifier output to stdout.
set +e
CLAUDE_OUTPUT=$(claude -p < "$PROMPT_FILE")
CLAUDE_RC=$?
set -e

if [[ $CLAUDE_RC -ne 0 ]]; then
  printf '[gate-req-runner] claude -p exited with status %d; preserving manifest at %s for debugging\n' \
    "$CLAUDE_RC" "$MANIFEST_PATH" >&2
  printf '%s\n' "$CLAUDE_OUTPUT" >&2
  exit 4
fi

# -----------------------------------------------------------------------------
# Emit raw output for TeamLead to parse
# -----------------------------------------------------------------------------

printf '%s\n' "$CLAUDE_OUTPUT"

# -----------------------------------------------------------------------------
# Manifest cleanup per ~/CLAUDE.md §清理紀律
# -----------------------------------------------------------------------------
# Only delete on full success (clean stdout passed to TeamLead). On any earlier
# error path the trap-based PROMPT_FILE cleanup runs but the manifest is left
# in place so the operator can inspect it.

rm -f "$MANIFEST_PATH"

exit 0
