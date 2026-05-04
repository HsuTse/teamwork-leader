# Real-Session Integration Test
# Stage 3 — Auto-Resume Daemon (v0.1.7)
# RAID: I-032 (RD I-032 + Opus PLAN_AUDIT missing-element 5)
# Design ref: design.md §1 T2→T3→T4→T8 (PreCompact + Stop + SessionStart chain)
# Per I-014/I-015: --print mode does NOT fire hooks; this test uses real interactive session ONLY.

## Purpose

Verify that the PreCompact → Stop → SessionStart hook chain fires correctly in
a real interactive Claude session. This test is OUT-of-CI (hooks do not fire in
`--print` mode per I-014/I-015) and IN-of-Stage-3-DoD.

## Prerequisites

- Plugin installed and registered: `hooks/hooks.json` references all 3 hooks
- `$CLAUDE_PROJECT_DIR` and `$CLAUDE_PLUGIN_ROOT` set in the claude session env
- `.teamlead/` directory writable at `$CLAUDE_PROJECT_DIR/.teamlead/`
- Interactive `claude` binary available (NOT `claude -p` / `claude --print`)

## Test Procedure

### Step 1 — Verify hook registration

Before starting the interactive session, confirm hooks are registered:

```bash
# From project root
cat hooks/hooks.json | python3 -c "
import json, sys
d = json.load(sys.stdin)
h = d.get('hooks', {})
print('PreCompact registered:', 'PreCompact' in h)
print('Stop registered:', 'Stop' in h)
print('SessionStart registered:', 'SessionStart' in h)
"
```

Expected output:
```
PreCompact registered: True
Stop registered: True
SessionStart registered: True
```

### Step 2 — Set environment variables

```bash
export CLAUDE_PLUGIN_ROOT="$(pwd)"
export CLAUDE_PROJECT_DIR="$(pwd)"
```

Verify `.teamlead/` is writable:

```bash
mkdir -p .teamlead && touch .teamlead/.write-test && rm .teamlead/.write-test
echo "writable: OK"
```

### Step 3 — Start interactive Claude session

```bash
claude
```

Do NOT use `claude -p` or `claude --print`. The hooks must fire in interactive mode.

### Step 4 — Trigger AutoCompact (PreCompact hook test)

Inside the interactive session, trigger compaction by either:
- Running a long conversation until AutoCompact fires naturally, OR
- Using the `/compact` command explicitly

Expected: PreCompact hook fires BEFORE compaction completes.

**Observe**:
- `$CLAUDE_PROJECT_DIR/.teamlead/baton.json` is created
- `baton.json` contains `"gate_state": "BATON_WRITTEN"`
- `baton.json` has 0600 permissions
- No `.teamlead/gate.lock` remains (released after atomic write)

Verification commands (run in a second terminal):
```bash
ls -la .teamlead/
python3 -c "
import json
d = json.load(open('.teamlead/baton.json'))
print('gate_state:', d.get('gate_state'))
print('session_id:', d.get('session_id', 'MISSING')[:8], '...')
print('prior_pause_commit:', d.get('prior_pause_commit', 'MISSING')[:8], '...')
print('branch:', d.get('branch'))
"
```

### Step 5 — End session (Stop hook test)

Exit the interactive Claude session (Ctrl+D or `/exit`).

Expected: Stop hook fires on session end.

**Observe**:
- macOS notification appears (if osascript available): "TeamLead Auto-Resume armed"
- No errors in terminal output from stop hook
- If `.teamlead/last-resume-failure.txt` exists from a prior failed test, a
  banner appears in the session output warning the operator

### Step 6 — Start new interactive session (SessionStart hook test)

```bash
claude
```

Expected: SessionStart hook fires at session start.

**Two possible paths depending on baton state**:

**Path A — Fresh baton present (gate_state=BATON_WRITTEN)**:
- Session output shows RESUME CONTEXT READY banner
- Banner includes prior session_id, prior_pause_commit, restore_prompt
- Session is in Auto-Mode-OFF (manual ack required before execution)
- Operator runs: `python3 hooks/session-start.py --ack-resume` to consume baton

**Path B — No baton (ARMED state)**:
- Session proceeds normally (no banner)
- `.teamlead/` directory confirmed to exist

### Step 7 — Verify baton consumed (Path A only)

After `--ack-resume`:
```bash
ls -la .teamlead/
# Expected: baton.json renamed to baton.consumed-<ISO>.json
# Expected: no gate.lock present
```

## Evidence Section

*This section is to be filled in by the operator after running the procedure above.*

**Date/Time tested**: `<placeholder>`

**Operator**: `<placeholder>`

**Step 1 — Hook registration output**:
```
<placeholder>
```

**Step 4 — Baton written (PreCompact fired)**:
- baton.json exists: `<placeholder: YES/NO>`
- gate_state value: `<placeholder>`
- permissions (ls -la): `<placeholder>`
- gate.lock absent after write: `<placeholder: YES/NO>`

**Step 5 — Stop hook fired**:
- macOS notification appeared: `<placeholder: YES/NO/N/A>`
- Stop hook exit code: `<placeholder>`
- Unexpected output: `<placeholder: none/describe>`

**Step 6 — SessionStart hook fired**:
- Path taken: `<placeholder: A (resume banner) or B (ARMED no-banner)>`
- RESUME banner appeared: `<placeholder: YES/NO>`
- Auto-Mode-OFF confirmed: `<placeholder: YES/NO>`

**Step 7 — Baton consumed (if Path A)**:
- baton.consumed-*.json present: `<placeholder: YES/NO/N/A>`
- gate.lock absent: `<placeholder: YES/NO>`

**Overall result**: `<placeholder: PASS/FAIL/PARTIAL>`

**Notes/deviations from procedure**:
```
<placeholder>
```

## Known constraints

- Per I-014/I-015: hooks NEVER fire in `--print` / `-p` mode. Do NOT attempt
  to verify hook firing via `claude -p` — it will not work by design.
- Per I-015: Stop hook does NOT fire in `--print` mode. This is why the real-
  session test is manually operated, not automated.
- The `.teamlead/` workspace artifacts (baton.json, gate.lock, last-resume-
  failure.txt) are not committed to git (gitignored per Stage 3 scope).
- `last-resume-failure.txt` from prior failed tests should be cleared before
  running Step 6 if you want a clean ARMED path test.

## Relationship to CI verifications

The automated verify clauses in T-3-9 (`check-cross-refs.sh`, evidence file
presence checks) do NOT cover hook-fire verification — that is exclusively
this manual real-session test. The automated tools verify the measurement
infrastructure and cross-reference consistency only.

## RAID references

- I-032: RD RAID — this real-session test is the I-032 mitigation artifact
- I-014/I-015: hooks do not fire in --print mode (constraint documented here)
- I-023: Metric 2 (T-S-4 fault→awareness) and this test complement each other;
  the automated Metric 2 script tests the detection mechanism in test-mode;
  this manual test verifies the full live chain
