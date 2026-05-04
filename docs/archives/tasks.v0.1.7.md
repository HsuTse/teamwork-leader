# tasks.md — teamwork-leader v0.1.7 Auto-Resume Daemon

## ⏸ RESUME BRIEF (paused 2026-05-03 mid-Stage-1)

**Status**: Stage 1 EXECUTING paused after 2/7 tasks complete (T-1-7 + T-1-1 both `confirmed`). 5 tasks remain (T-1-2 / T-1-3 / T-1-4 / T-1-5 / T-1-6) + Stage 1 close INTEGRITY check. Branch: `feat/v0.1.7-auto-resume-daemon` (committed at pause).

**Why paused**: Stage 1 budget hit ~83/100 kT (80% calibration warning); parent session approaching its own AutoCompact threshold. Per Opus advisor, pausing here is **dogfood of charter goal** — measuring manual resume cost is Stage 2 spec input.

**Resume command**: `/teamwork-leader` (TeamLead will detect existing PROGRESS.md → Resume mode → reconcile state).

**Next dispatch on resume**: **S1-D5 = T-1-2** (PreCompact stdout capture under near-limit ctx).

### Carry-forward findings ONLY relevant to T-1-2 (parked: rest)

| Tag | Status | Implication for T-1-2 |
|---|---|---|
| **T-1-7 confirmed** (S1-D2) | done | Hook timeout = HARD KILL (sleep 12s + timeout=5 → killed); payload no observable upper bound up to 16MB. T-1-2 PreCompact baton can use any sensible payload size |
| **A-001 validated** (S1-D4) | closed | `claude --resume <id> --print '<prompt>'` works (claude 2.1.112): both prior context + new prompt turn surface. Stage 2 design may use `--resume + -p` model |
| **I-002 open** (PLANNING) | open | T-1-2 PreCompact synthetic-trigger feasibility unclear — plan candidate C has explicit synthetic-first-then-real-fallback rule (45min synthetic time-box → inconclusive escalates) |
| **I-005-T1-7 RESOLVED** (S1-D3) | closed | tasks.md hooks.json wrapper-format applied at lines 32/136/232/289/373; T-1-2 hooks.json snippet now uses canonical `{"description":..., "hooks":{...}}` format (loadable on first attempt) |
| **I-006-T1-7 open** | open | T-1-2 marker file ~5KB; bash string-concat O(N²) NOT a concern at this size — proceed |

### Parked findings (re-load when their task fires)

- I-008/I-009/I-010 — T-1-3 prep (init step / flock bug / gdate fallback)
- I-007 — Stage 1 dod_status aggregation rule (need at stage close)
- A-004/A-005 — backup candidates A and B (only if C fails)
- I-001 — silent-misroute risk (mitigated charter-wide)
- I-011 — meta enum drift (Phase 4 calibration)
- R-001 — Anthropic native resume risk (validates at T-1-6 — PO PM owner)

### Resume cost measurement (Stage 2 spec input)

When resuming this charter in a new Claude Code session, **time and record**:
- Wall clock from `/teamwork-leader` invocation → first PM dispatch ready
- Tool calls consumed before first dispatch (Read SKILL.md / runbook / dispatch-header / PROGRESS.md / tasks.md / etc.)
- kT consumed before first dispatch
- Whether Resume mode auto-detected correctly OR manual reconciliation needed

Append measurement to `docs/specs/phase-0-evidence/resume-cost-baseline.txt` — this becomes the **manual baseline the Stage 4 daemon must beat**.

---

## Stage 1 — Phase 0 Fact Validation

Each task is a **reproduce-based** validation. Every task MUST emit:
- `command` — exact shell command(s) executed
- `actual_output` — captured stdout/stderr (excerpt acceptable but include enough to support verdict)
- `verdict` — `confirmed | refuted | inconclusive`
- `implications` — if refuted/inconclusive, what design assumption breaks

| ID | Title | Owner | Acceptance |
|---|---|---|---|
| T-1-1 | Verify `claude --resume <id> -p "<prompt>"` CLI behavior | RD | `claude --help` shows `--resume`; minimal repro session-A → resume session-B with `-p` proves prompt is consumed as new user turn |
| T-1-2 | Verify PreCompact hook stdout capture under near-limit ctx | RD | Synthetic ctx-saturation test triggers PreCompact; hook writes 5KB+ payload and Claude's PreCompact stdout matches what was written |
| T-1-3 | Verify PreCompact + Stop hook race ordering | RD | Trigger compact at session end; observe execution order via timestamped log lines from each hook |
| T-1-4 | Verify plugin hook can write outside `${CLAUDE_PLUGIN_ROOT}` | RD | Hook attempts `echo > $PROJECT_ROOT/.teamlead/probe.txt` → file exists post-hook |
| T-1-5 | Evaluate launchd plist install UX (plugin-driven vs manual) | DevOps-via-RD | `launchctl bootstrap gui/$UID <plist>` runs without sudo; document permission dialog UX cost |
| T-1-6 | Survey Anthropic native resume roadmap | PO | Search Claude Code public changelog + docs + GitHub issues for "resume" / "compact" / "session continuity"; verdict on whether self-build is competitive vs ETA |
| T-1-7 | Verify hook timeout + payload size limits | RD | Read official hook docs; force a hook to take >timeout and emit >large-payload; observe truncation/kill behavior |

### Execution plan (drafted 2026-05-03 by RD PM, pending PLAN_AUDIT)

**Global execution conventions**

- Evidence root: `docs/specs/phase-0-evidence/` — created at start of EXECUTING stage; one file per task `<task-id>.txt`
- Evidence capture template: `<command_block> 2>&1 | tee docs/specs/phase-0-evidence/<task-id>.txt` (interactive sessions wrap with `script -q`)
- Each evidence file MUST start with header lines: `# task: <id>`, `# date: <ISO-8601>`, `# claude_version: $(claude --version)`, `# branch: $(git rev-parse --abbrev-ref HEAD)`
- Time-box exceeded → write `verdict: inconclusive` + last captured snapshot, do NOT keep retrying
- Each task ends by writing a verdict block to its evidence file: `verdict: <confirmed|refuted|inconclusive>`, `implications: <text>`
- No `git commit` from this stage — commits happen at stage close after all gates pass
- Branch precondition (re-checked at start of EXECUTING): `git rev-parse --abbrev-ref HEAD` returns `feat/v0.1.7-auto-resume-daemon`
- **Hooks.json format**: Plugin hooks.json MUST use wrapper format `{"description":..., "hooks":{...}}` (per hook-development SKILL.md line 119). Bare-event format `{"PreCompact":[...]}` does NOT load.

### Evidence header helper

Every task's first command MUST initialize its evidence file with a standard header via the helper script below. Subsequent task commands then `tee -a` to append.

```bash
cat > docs/specs/phase-0-evidence/_write_header.sh <<'SH'
#!/bin/bash
TASK_ID="$1"
[ -z "$TASK_ID" ] && { echo "usage: _write_header.sh <task-id>" >&2; exit 1; }
cat <<HDR
# task: ${TASK_ID}
# date: $(date -Iseconds)
# claude_version: $(claude --version 2>/dev/null || echo "unknown")
# branch: $(git rev-parse --abbrev-ref HEAD)
HDR
SH
chmod +x docs/specs/phase-0-evidence/_write_header.sh
```

Per-task usage convention: every task begins with
`bash docs/specs/phase-0-evidence/_write_header.sh <task-id> > docs/specs/phase-0-evidence/<task-id>.txt`
and all subsequent capture commands use `tee -a` to append (NOT overwrite).

---

#### T-1-1 — Verify `claude --resume <id> -p "<prompt>"` CLI behavior

**Time-box**: 25 min. **Dependencies**: none (entry point).

**Commands**:

```bash
# 0. Initialize evidence file with standard header (mandatory per Evidence header helper convention)
bash docs/specs/phase-0-evidence/_write_header.sh t-1-1 \
  > docs/specs/phase-0-evidence/t-1-1.txt

# 1. Confirm flag presence
claude --help 2>&1 | grep -E '\-\-resume|\-p, --print' \
  | tee -a docs/specs/phase-0-evidence/t-1-1.txt

# 1.5 Pre-check --output-format support
claude --help 2>&1 | grep -qE '\-\-output-format' && FLAG_SUPPORTED=1 || FLAG_SUPPORTED=0
echo "output_format_supported=$FLAG_SUPPORTED" | tee -a docs/specs/phase-0-evidence/t-1-1.txt

# 2. Create session-A: write a known sentinel into transcript via -p mode
SENTINEL_A="T1-1-SENTINEL-$(date +%s)"
if [ "$FLAG_SUPPORTED" = "1" ]; then
  # json-extract path — preferred when --output-format is supported
  SESSION_A=$(claude --print --output-format=json \
    "Remember this sentinel: $SENTINEL_A. Just acknowledge." \
    | tee -a docs/specs/phase-0-evidence/t-1-1.txt \
    | jq -r '.session_id')
else
  # Fallback path — pre-generate UUID and pass via --session-id
  SESSION_A=$(uuidgen)
  claude --session-id "$SESSION_A" --print \
    "Remember this sentinel: $SENTINEL_A. Just acknowledge." \
    2>&1 | tee -a docs/specs/phase-0-evidence/t-1-1.txt
fi
echo "session_a=$SESSION_A sentinel=$SENTINEL_A" \
  | tee -a docs/specs/phase-0-evidence/t-1-1.txt

# 3. Resume session-A with -p (the critical claim under test)
SENTINEL_B="T1-1-RESUME-PROBE-$(date +%s)"
claude --resume "$SESSION_A" --print \
  "What was the sentinel I asked you to remember? Also confirm you received this new turn: $SENTINEL_B" \
  2>&1 | tee -a docs/specs/phase-0-evidence/t-1-1.txt
```

**Verdict criteria**:

- **confirmed**: Step 3 stdout contains BOTH `$SENTINEL_A` (proves resume loaded prior context) AND echo/acknowledgement of `$SENTINEL_B` (proves prompt was consumed as new turn). Exit code 0.
- **refuted**: Step 3 errors with "cannot resume in -p mode" / similar, OR output shows only one of the sentinels (resume loaded but prompt not injected, or prompt injected but no prior context).
- **inconclusive**: Step 3 hangs past time-box, OR `--output-format=json` not supported and we cannot extract session_id (fallback: try `--session-id <pre-generated-uuid>` to bypass discovery).

**Per-task rollback**: Two synthetic sessions are created in `~/.claude/sessions/` (or wherever Claude Code persists). Cleanup: `rm -f ~/.claude/sessions/*${SENTINEL_A}*` if a path is identifiable; otherwise note session IDs in evidence file and let natural session-pruning handle it (NOT manually deleting unknown session files — see CLEANUP discipline). Acceptable: leave sessions, document IDs.

**Implications if refuted**: A-001 invalidated → design pivots to `claude -p "<context-bundle>"` new-session model; baton schema must include full context restitching (not just delta).

---

#### T-1-7 — Verify hook timeout + payload size limits (RUN BEFORE T-1-2/T-1-3)

**Time-box**: 30 min. **Dependencies**: none.

**Rationale for ordering**: T-1-2 and T-1-3 both depend on knowing the timeout / payload behaviour to design their fixtures. Running T-1-7 first lets T-1-2/T-1-3 size their probes correctly.

**Commands**:

```bash
# 1. Capture authoritative hook docs locally (already verified during PLANNING)
#    Source: ~/.claude/plugins/marketplaces/claude-plugins-official/plugins/plugin-dev/skills/hook-development/SKILL.md
#    Defaults observed: command 60s, prompt 30s. Recorded in evidence header.
cp ~/.claude/plugins/marketplaces/claude-plugins-official/plugins/plugin-dev/skills/hook-development/SKILL.md \
   docs/specs/phase-0-evidence/t-1-7-hook-docs-snapshot.md

# 2. Build a sandbox plugin scaffold under /tmp/teamlead-probe-plugin/
#    Note: PreCompact entry retained to verify event-name acceptance; SessionStart entry produces
#    actual timeout/payload evidence (synchronous trigger).
mkdir -p /tmp/teamlead-probe-plugin/{hooks,scripts}
cat > /tmp/teamlead-probe-plugin/hooks/hooks.json <<'JSON'
{
  "description": "T-1-7 hook timeout + payload size probe",
  "hooks": {
    "PreCompact": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "bash ${CLAUDE_PLUGIN_ROOT}/scripts/timeout-probe.sh",
        "timeout": 5
      }]
    }],
    "SessionStart": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "bash ${CLAUDE_PLUGIN_ROOT}/scripts/timeout-probe.sh",
        "timeout": 5
      }]
    }]
  }
}
JSON

# 3. Slow probe: deliberately exceed timeout=5
cat > /tmp/teamlead-probe-plugin/scripts/timeout-probe.sh <<'SH'
#!/bin/bash
echo "T-1-7 timeout-probe START $(date -Iseconds)" >> /tmp/t-1-7-hook.log
sleep 12
echo "T-1-7 timeout-probe END $(date -Iseconds)" >> /tmp/t-1-7-hook.log
echo '{"continue": true, "systemMessage": "should-be-killed"}'
SH
chmod +x /tmp/teamlead-probe-plugin/scripts/timeout-probe.sh

# 4. Large payload probe: emit increasing payload sizes
cat > /tmp/teamlead-probe-plugin/scripts/payload-probe.sh <<'SH'
#!/bin/bash
SIZE_KB="${PROBE_SIZE_KB:-10}"
PAYLOAD=$(head -c $((SIZE_KB * 1024)) /dev/urandom | base64)
printf '{"continue":true,"systemMessage":"size=%sKB:%s"}' "$SIZE_KB" "$PAYLOAD"
SH
chmod +x /tmp/teamlead-probe-plugin/scripts/payload-probe.sh

# 5. Trigger via test harness (claude --plugin-dir /tmp/teamlead-probe-plugin --debug -p "<trigger>")
#    PreCompact only fires on actual compact; for timeout/payload mechanics we substitute SessionStart
#    (hook runtime is shared) by adding SessionStart matcher pointing to same scripts.
#    Run with --debug and tee debug log:
claude --plugin-dir /tmp/teamlead-probe-plugin --debug -p "ping" \
  2>&1 | tee docs/specs/phase-0-evidence/t-1-7.txt

# 6. Inspect /tmp/t-1-7-hook.log to see if "END" was reached (timeout did NOT kill) or absent (kill confirmed)
cat /tmp/t-1-7-hook.log >> docs/specs/phase-0-evidence/t-1-7.txt

# 7. Repeat step 5 with PROBE_SIZE_KB=10, 100, 1024, 4096 to find truncation boundary
for s in 10 100 1024 4096; do
  PROBE_SIZE_KB=$s claude --plugin-dir /tmp/teamlead-probe-plugin --debug -p "ping-$s" \
    2>&1 | tee -a docs/specs/phase-0-evidence/t-1-7.txt
done
```

**Verdict criteria**:

- **confirmed (with limits documented)**: Evidence file records (a) timeout kill behavior — script's `END` line absent from /tmp/t-1-7-hook.log when sleep > timeout, AND (b) payload size at which `systemMessage` is truncated or hook is rejected. Both numbers feed Stage 2 design.
- **refuted**: Hook never fires under `--plugin-dir` (means plugin dev API broken — escalate immediately, blocks all subsequent T-1-X).
- **inconclusive**: Cannot trigger PreCompact synthetically AND SessionStart substitution rejected by Claude Code; document attempt and proceed to T-1-2 with explicit assumption "timeout=60s, payload=unknown".

**Per-task rollback**: `rm -rf /tmp/teamlead-probe-plugin /tmp/t-1-7-hook.log` at task end. No state outside `/tmp` and `docs/specs/phase-0-evidence/`.

**Implications if refuted**: All hook-based design assumptions invalid — Stage 2 must pivot to non-hook mechanism (e.g., external file-watcher daemon).

---

#### T-1-2 — Verify PreCompact hook stdout capture under near-limit ctx

**Time-box**: 45 min. **Dependencies**: T-1-7 (timeout/payload limits known).

**Approach**: see plan candidates A/B/C below. Default = candidate **C (hybrid)**.

**Commands (candidate C)**:

```bash
# 1. Reuse /tmp/teamlead-probe-plugin from T-1-7. Replace PreCompact hook with marker writer:
cat > /tmp/teamlead-probe-plugin/scripts/precompact-marker.sh <<'SH'
#!/bin/bash
MARKER="T1-2-PRECOMPACT-$(date +%s)-$$"
SIZE_KB=5
PAYLOAD=$(head -c $((SIZE_KB * 1024)) /dev/urandom | base64 | tr -d '\n' | head -c 5120)
# Write to disk as primary evidence (Claude output is secondary)
echo "marker=$MARKER size=${SIZE_KB}KB ts=$(date -Iseconds)" \
  >> /tmp/t-1-2-precompact.log
# Emit on stdout — this is the claim under test
printf '{"continue":true,"systemMessage":"%s|%s"}' "$MARKER" "$PAYLOAD"
SH
chmod +x /tmp/teamlead-probe-plugin/scripts/precompact-marker.sh

# Update hooks.json to PreCompact:
cat > /tmp/teamlead-probe-plugin/hooks/hooks.json <<'JSON'
{
  "description": "T-1-2 PreCompact stdout capture probe",
  "hooks": {
    "PreCompact": [{
      "matcher": "*",
      "hooks": [{ "type": "command",
                  "command": "bash ${CLAUDE_PLUGIN_ROOT}/scripts/precompact-marker.sh",
                  "timeout": 30 }]
    }]
  }
}
JSON

# 2. Drive ctx toward AutoCompact threshold via --print stream-json with large input file:
#    Build a 500K-token context flood (synthetic JSON-array of fake transcripts)
python3 -c "
import json,sys
# Approximate: 500K tokens ~= 2MB text
chunks = ['Lorem ipsum dolor sit amet, consectetur adipiscing elit. ' * 50] * 8000
print(json.dumps({'flood': chunks}))
" > /tmp/t-1-2-flood.json

# 3. Start a session with the flood pre-loaded, then issue a turn that should trigger AutoCompact:
claude --plugin-dir /tmp/teamlead-probe-plugin --debug \
  --print "Read /tmp/t-1-2-flood.json fully and summarize each chunk individually with full quotes" \
  2>&1 | tee docs/specs/phase-0-evidence/t-1-2.txt

# 4. After session ends, cross-reference:
#    (a) /tmp/t-1-2-precompact.log — disk evidence of hook firing
#    (b) docs/specs/phase-0-evidence/t-1-2.txt — search for MARKER substring (proves stdout captured)
grep -E "T1-2-PRECOMPACT-[0-9]+" docs/specs/phase-0-evidence/t-1-2.txt \
  >> docs/specs/phase-0-evidence/t-1-2.txt
cat /tmp/t-1-2-precompact.log >> docs/specs/phase-0-evidence/t-1-2.txt
```

**Verdict criteria**:

- **confirmed**: `/tmp/t-1-2-precompact.log` has marker line AND debug log shows the hook output (marker substring present). Both 5KB+ payload chunks visible in debug stream.
- **partial-confirmed (= confirmed but with caveat)**: disk log fires, but stdout substring absent / truncated → A-003 partially refuted, design implication: "trust disk-write, don't trust stdout" (this is actually the safer design anyway).
- **refuted**: Hook never fires (no disk log line) — A-003 fully refuted, escalate.
- **inconclusive**: Cannot trigger AutoCompact in <45 min wall time → record attempt, recommend candidate B (real-session dogfood) as follow-up.

**Per-task rollback**: `rm /tmp/t-1-2-flood.json /tmp/t-1-2-precompact.log` at task end. Plugin scaffold reused by T-1-3, leave in place until T-1-3 completes.

**Implications if refuted**: A-003 invalidated → design must NOT route handoff via Claude's output channel; must write directly to disk in hook script.

---

#### T-1-3 — Verify PreCompact + Stop hook race ordering

**Time-box**: 30 min. **Dependencies**: T-1-7 (timeout knowledge), T-1-2 (plugin scaffold reused).

**Commands**:

```bash
# 1. Add Stop hook to existing /tmp/teamlead-probe-plugin/hooks/hooks.json:
cat > /tmp/teamlead-probe-plugin/hooks/hooks.json <<'JSON'
{
  "description": "T-1-3 PreCompact + Stop race ordering probe",
  "hooks": {
    "PreCompact": [{
      "matcher": "*",
      "hooks": [{ "type": "command",
                  "command": "bash ${CLAUDE_PLUGIN_ROOT}/scripts/timestamp-precompact.sh",
                  "timeout": 30 }]
    }],
    "Stop": [{
      "matcher": "*",
      "hooks": [{ "type": "command",
                  "command": "bash ${CLAUDE_PLUGIN_ROOT}/scripts/timestamp-stop.sh",
                  "timeout": 30 }]
    }]
  }
}
JSON

# 2. Both scripts log nanosecond-resolution timestamp + hook name to a shared log:
cat > /tmp/teamlead-probe-plugin/scripts/timestamp-precompact.sh <<'SH'
#!/bin/bash
flock /tmp/t-1-3-race.lock -c "echo precompact|$(gdate +%s%N || date +%s%N) >> /tmp/t-1-3-race.log"
echo '{"continue":true}'
SH
cat > /tmp/teamlead-probe-plugin/scripts/timestamp-stop.sh <<'SH'
#!/bin/bash
flock /tmp/t-1-3-race.lock -c "echo stop|$(gdate +%s%N || date +%s%N) >> /tmp/t-1-3-race.log"
echo '{"decision":"approve"}'
SH
chmod +x /tmp/teamlead-probe-plugin/scripts/*.sh

# 3. Trigger session 3 times to detect non-determinism in race ordering.
#    Each run: reset /tmp/t-1-3-race.log, append a "# run=N" header to evidence, capture session output,
#    then snapshot race log to /tmp/t-1-3-race.log.run$run before next iteration.
for run in 1 2 3; do
  rm -f /tmp/t-1-3-race.log /tmp/t-1-3-race.lock
  echo "# run=$run" >> docs/specs/phase-0-evidence/t-1-3.txt
  claude --plugin-dir /tmp/teamlead-probe-plugin --debug \
    --print "Summarize /tmp/t-1-2-flood.json briefly then stop" \
    2>&1 | tee -a docs/specs/phase-0-evidence/t-1-3.txt
  # Inspect race log for this run, then preserve it
  sort -t'|' -k2 -n /tmp/t-1-3-race.log >> docs/specs/phase-0-evidence/t-1-3.txt
  mv /tmp/t-1-3-race.log /tmp/t-1-3-race.log.run$run
done
```

**Verdict criteria** (cross-reference per-run race-log files `/tmp/t-1-3-race.log.run1`, `.run2`, `.run3`):

- **confirmed (deterministic ordering)**: All three of `/tmp/t-1-3-race.log.run1`..`.run3` show identical ordering (e.g., precompact always before stop, or vice versa).
- **confirmed (parallel/non-deterministic)**: Ordering varies across `/tmp/t-1-3-race.log.run{1,2,3}` → matches hook-development SKILL "All matching hooks run in parallel" doc statement. Design implication: must NOT depend on ordering; use file locks or sequential coordinator script.
- **inconclusive**: Compact does not trigger within session → only Stop fires in all three runs; document and treat ordering question as moot (re-validate in Stage 3 dogfood).
- **refuted**: Either hook fails to fire in any run → escalate (overlaps with T-1-7 finding).

**Per-task rollback**: `rm /tmp/t-1-3-race.log /tmp/t-1-3-race.lock /tmp/t-1-3-race.log.run{1,2,3}` at task end. Loop runs 3 times in step 3; results consolidated into single evidence file plus three preserved per-run snapshots.

**Implications if non-deterministic**: Stage 2 baton-writer design must be idempotent + use file lock; cannot rely on PreCompact-then-Stop sequence.

---

#### T-1-4 — Verify plugin hook can write outside `${CLAUDE_PLUGIN_ROOT}`

**Time-box**: 15 min. **Dependencies**: T-1-7 (plugin scaffold pattern).

**Commands**:

```bash
# 1. Create a probe directory inside this project (NOT /tmp — claim is about $CLAUDE_PROJECT_DIR access)
mkdir -p /Users/HsuTse/ClaudeProject/teamwork-leader/.teamlead-probe
PROBE_FILE="/Users/HsuTse/ClaudeProject/teamwork-leader/.teamlead-probe/probe.txt"
rm -f "$PROBE_FILE"

# 2. Add SessionStart hook that writes outside plugin root:
cat > /tmp/teamlead-probe-plugin/scripts/cross-write.sh <<'SH'
#!/bin/bash
PROBE_FILE="$CLAUDE_PROJECT_DIR/.teamlead-probe/probe.txt"
mkdir -p "$(dirname "$PROBE_FILE")"
echo "wrote-from-hook ts=$(date -Iseconds) cwd=$(pwd) plugin_root=$CLAUDE_PLUGIN_ROOT project_dir=$CLAUDE_PROJECT_DIR" \
  > "$PROBE_FILE"
echo "{\"continue\":true,\"systemMessage\":\"probe-written:$PROBE_FILE\"}"
SH
chmod +x /tmp/teamlead-probe-plugin/scripts/cross-write.sh

cat > /tmp/teamlead-probe-plugin/hooks/hooks.json <<'JSON'
{
  "description": "T-1-4 cross-project-root write probe",
  "hooks": {
    "SessionStart": [{
      "matcher": "*",
      "hooks": [{ "type": "command",
                  "command": "bash ${CLAUDE_PLUGIN_ROOT}/scripts/cross-write.sh",
                  "timeout": 10 }]
    }]
  }
}
JSON

# 3. Trigger SessionStart from this project's cwd:
cd /Users/HsuTse/ClaudeProject/teamwork-leader
claude --plugin-dir /tmp/teamlead-probe-plugin --debug --print "say hi" \
  2>&1 | tee docs/specs/phase-0-evidence/t-1-4.txt

# 4. Verify file exists and content:
ls -la "$PROBE_FILE" >> docs/specs/phase-0-evidence/t-1-4.txt
cat "$PROBE_FILE" >> docs/specs/phase-0-evidence/t-1-4.txt
```

**Verdict criteria**:

- **confirmed**: `$PROBE_FILE` exists post-hook with timestamp + correct `$CLAUDE_PROJECT_DIR` value.
- **refuted**: File missing OR hook errors with permission denied. Implication: baton must live inside plugin root (requires symlink/state-server design).
- **inconclusive**: Hook fires (debug log shows it) but file missing for non-permission reason (e.g., cwd mismatch).

**Per-task rollback**: `rm -rf /Users/HsuTse/ClaudeProject/teamwork-leader/.teamlead-probe` at task end. The dir is gitignored-by-pattern (`.teamlead-*`) — verify with `git check-ignore` before rollback to avoid surprising commit. If NOT ignored, add `.teamlead-probe/` to `.gitignore` first OR use a different probe location like `$TMPDIR/teamlead-probe-${PROJECT_BASENAME}` (still outside `${CLAUDE_PLUGIN_ROOT}` and outside repo, satisfying the claim).

**Implications if refuted**: A-002 invalidated → Stage 2 design must place baton/gate.lock inside `${CLAUDE_PLUGIN_ROOT}`, requiring per-project symlink convention or file-server side-channel.

---

#### T-1-5 — Evaluate launchd plist install UX (plugin-driven vs manual)

**Time-box**: 35 min. **Dependencies**: none. **Owner**: DevOps-via-RD.

**Commands**:

```bash
# PRE-EXECUTION GATE — STOP HERE on first run
# launchctl bootstrap mutates user-system state outside repo (per CLAUDE.md §高風險操作).
# Probe label: com.teamlead.probe (no RunAtLoad; bootout in same task).
# Required: CEO acknowledgment before proceeding. If not granted, write `verdict: inconclusive`
# with implications "T-1-5 skipped per CEO declination" and exit.

# 1. Author a no-op plist (launches /usr/bin/true on demand, not on schedule):
cat > /tmp/com.teamlead.probe.plist <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTD/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.teamlead.probe</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/true</string>
  </array>
  <key>RunAtLoad</key><false/>
  <key>StandardOutPath</key><string>/tmp/teamlead-probe-stdout.log</string>
  <key>StandardErrorPath</key><string>/tmp/teamlead-probe-stderr.log</string>
</dict>
</plist>
PLIST

# 2. Bootstrap (install) without sudo:
launchctl bootstrap "gui/$UID" /tmp/com.teamlead.probe.plist \
  2>&1 | tee docs/specs/phase-0-evidence/t-1-5.txt
echo "exit=$?" >> docs/specs/phase-0-evidence/t-1-5.txt

# 3. Verify it loaded:
launchctl print "gui/$UID/com.teamlead.probe" 2>&1 \
  | head -50 >> docs/specs/phase-0-evidence/t-1-5.txt

# 4. Document any TCC / Full-Disk-Access / Notification permission dialogs encountered (manual observation):
echo "## UX dialogs observed" >> docs/specs/phase-0-evidence/t-1-5.txt
echo "(human-recorded: list every system permission prompt that appeared during step 2)" \
  >> docs/specs/phase-0-evidence/t-1-5.txt

# 5. Test on-demand kickstart:
launchctl kickstart -k "gui/$UID/com.teamlead.probe" \
  2>&1 | tee -a docs/specs/phase-0-evidence/t-1-5.txt

# 6. Bootout (uninstall) — same path as future uninstall script:
launchctl bootout "gui/$UID/com.teamlead.probe" \
  2>&1 | tee -a docs/specs/phase-0-evidence/t-1-5.txt
```

**Verdict criteria**:

- **confirmed**: bootstrap exits 0 without sudo prompt; launchctl print shows the agent loaded; bootout cleanly removes it. Number of TCC dialogs documented.
- **refuted**: bootstrap requires sudo OR bootstrap fails with permissions error → escalate; Phase 2 daemon design must use alternative (cron user crontab, or in-process /loop-only).
- **inconclusive**: bootstrap succeeds but kickstart fails for environment-specific reasons → record details.

**Per-task rollback**: `launchctl bootout gui/$UID/com.teamlead.probe 2>/dev/null; rm -f /tmp/com.teamlead.probe.plist /tmp/teamlead-probe-stdout.log /tmp/teamlead-probe-stderr.log`. Run rollback even if test passed — don't leave a probe agent loaded.

**Implications if refuted**: Phase 2 launchd design ditched; pivot to in-Claude `/loop` skill (limits cross-session resumption capability — escalate to CEO).

---

#### T-1-6 — Survey Anthropic native resume roadmap

**Time-box**: 45 min. **Dependencies**: none. **Owner**: PO (this dispatch is RD-PM; T-1-6 will be re-dispatched to PO at EXECUTING).

```text
# OWNERSHIP TRANSITION — T-1-6 owner is PO, not RD
# RD-PM executes step 1 (cli-version snapshot) only, then STOPS.
# TeamLead re-dispatches PO-PM with prompt template embedded below for steps 2-3 + verdict.
```

**PO re-dispatch prompt template** (TeamLead fills `{{...}}` placeholders at dispatch time):

```text
You are dispatched as PO PM by TeamLead (dispatch_id {{S1-D2}}) for project teamwork-leader v0.1.7,
task T-1-6: Survey Anthropic native resume roadmap. RD-PM has already completed step 1
(cli-version snapshot at docs/specs/phase-0-evidence/t-1-6.txt). Your scope is steps 2–3 + verdict.

Read first:
- docs/specs/phase-0-evidence/t-1-6.txt — RD's step-1 snapshot
- tasks.md §T-1-6 — task definition + verdict criteria

Tools: WebFetch + WebSearch (PO-tier).
Sources to survey:
- https://docs.anthropic.com/en/docs/claude-code/changelog
- https://github.com/anthropics/claude-code/issues?q=resume+OR+compact+OR+continuity
- WebSearch query: "claude code session resume" date>=2026-01-01

Required output:
- Append top-3 hits per source (URL + title + status + ETA-if-stated) to t-1-6.txt
- Apply the decision matrix in tasks.md §T-1-6 step 3
- Write verdict block (confirmed-proceed | confirmed-pause | inconclusive) + implications

Constraints: read-only research; no repo file changes outside docs/specs/phase-0-evidence/t-1-6.txt.
Return contract: 11-field schema per dispatch-header.md.
```

**Commands**:

```bash
# 1. [RD-PM] Snapshot Claude Code public changelog (local cache if available):
claude --version | tee docs/specs/phase-0-evidence/t-1-6.txt
ls ~/.claude/plugins/marketplaces/ 2>&1 \
  >> docs/specs/phase-0-evidence/t-1-6.txt
# RD-PM STOPS HERE. Steps 2-3 below are PO-PM scope after re-dispatch.
# WebFetch (PO will use): https://docs.anthropic.com/en/docs/claude-code/changelog
# WebFetch: https://github.com/anthropics/claude-code/issues?q=resume+OR+compact+OR+continuity
# WebSearch: "claude code session resume" date>=2026-01-01

# 2. Capture top-3 currently-open/recent items per source:
echo "## changelog hits" >> docs/specs/phase-0-evidence/t-1-6.txt
echo "(PO records URL + title + status + ETA-if-stated for each)" \
  >> docs/specs/phase-0-evidence/t-1-6.txt

# 3. Decision matrix:
#    - If any hit shows "shipping <90d" with strong scope match → recommend pause/redirect
#    - If hits show "exploring/RFC" only → proceed (build remains valuable)
#    - If no hits → proceed (we're charting new territory)
```

**Verdict criteria**:

- **confirmed (proceed)**: No Anthropic-shipped or imminent (<90d) feature covers cross-AutoCompact resume + plugin hooks orchestration.
- **confirmed (pause)**: Anthropic announced shipping <90d → CEO redirect needed.
- **inconclusive**: Conflicting signals → record both, escalate to CEO.

**Per-task rollback**: None — read-only research.

**Implications if `confirmed (pause)`**: R-001 realized; charter pivot.

---

### Stage 1 close — evidence integrity

After all T-1-X tasks reach a verdict (confirmed | refuted | inconclusive), Stage 1 close requires generating an evidence integrity manifest AND validating that the fact-validation document's JSONL blocks parse cleanly. **Both commands must succeed before stage close commit.**

```bash
# 1. Generate SHA-256 manifest of all evidence text files
find docs/specs/phase-0-evidence -type f -name '*.txt' -print0 | \
  xargs -0 shasum -a 256 > docs/specs/phase-0-evidence/INTEGRITY.sha256

# 2. Validate every JSONL block in phase-0-fact-validation.md parses as JSON
grep -A1 '^```jsonl' docs/specs/phase-0-fact-validation.md | grep -E '^\{' | jq -c .
```

If either command exits non-zero, do NOT commit Stage 1 close — fix the offending evidence first (corrupted file → re-run task; malformed JSONL → fix `phase-0-fact-validation.md`). The `INTEGRITY.sha256` file is committed as part of stage close.

---

### Plan execution sequence summary

| Order | Task | Time-box | Why this order |
|---|---|---|---|
| 1 | T-1-7 | 30m | Provides hook timeout/payload facts for T-1-2/T-1-3 |
| 2 | T-1-1 | 25m | Independent CLI claim; quick high-signal answer on A-001 |
| 3 | T-1-4 | 15m | Reuses plugin scaffold from T-1-7; quick A-002 answer |
| 4 | T-1-2 | 45m | Needs T-1-7 limits; reuses scaffold |
| 5 | T-1-3 | 30m | Reuses T-1-2 scaffold + flood file |
| 6 | T-1-5 | 35m | Independent; DevOps-flavoured launchd test |
| 7 | T-1-6 | 45m | PO-owned roadmap survey; can run in parallel with any of above |
| **Total** | — | **~225m wall time** | Within Stage 1 EXECUTING budget envelope |

## Stage 2 — Spec + Design Doc

**Goal**: produce `docs/specs/auto-resume-daemon-design.md` covering state machine + baton + gate.lock + launchd plist + security model + environment portability. Must pass plugin-internal Opus PlanAudit at PLAN_AUDIT.

**Stage 2 baseline budget**: 150 kT (PO=60 / RD=30 / QA=30 / Gate_Req=30).

**Decomposition strategy**: by-domain parallelism with skeleton-first anchor (Plan B selected — see plan_candidates in PLANNING return). T-2-1 establishes section skeleton + cross-reference graph FIRST so section drafters work against fixed anchors; T-2-2 through T-2-6 then run in two parallel batches; T-2-7 integrates and runs internal QA review.

| ID | Title | Owner | Acceptance | blockedBy | parallel |
|---|---|---|---|---|---|
| T-2-1 | Skeleton + cross-reference graph + frozen-decisions for `auto-resume-daemon-design.md` (STRENGTHENED per advisor) | PO | File created with: (a) 6 numbered section headers; (b) **per-section sub-skeleton** containing main data structure 簽名 (e.g., baton.json field list) + 接點清單 (which sections this depends on / depended-by) + open-question list; (c) Stage 1 finding cross-reference table (A-001 / A-002 / I-014 / I-015 / I-018 / V-001 + Wave Refinement note 1); (d) **Frozen design decisions** explicitly listed: **baton size limit = ≤ 1 MB chosen cap** (NOT 16 MB — that's observed ceiling per FV-T-1-7 line 587), disk-write hook payload default (per CCBL-001), `$CLAUDE_PROJECT_DIR/.teamlead/` location for baton + gate.lock (per A-002 validated); (e) open-question list extracted from Stage 1 RAID-A (A-004/A-005, I-005/I-006/I-007, I-016/I-017); (f) ADR-link to CCBL-003 (Opus selection override rationale) | none (entry) | no |
| T-2-2 | Section §1: State machine (ARMED → PRE_COMPACT_TRIGGERED → BATON_WRITTEN → SESSION_RESUMED → POST_RESUME_VERIFIED → DONE/ABORTED) | RD | Section §1 contains state-list with transition table (event → from_state → to_state → side_effect), failure-mode column (timeout / hard-kill / abort path); explicitly references I-018 hook-script-language constraint and I-014/I-015 hook-free-zone (`-p` mode no-PreCompact-fire) | T-2-1 | yes (with T-2-3, T-2-4) |
| T-2-3 | Section §2: Baton schema (JSON, lives in `$CLAUDE_PROJECT_DIR/.teamlead/baton.json`) | RD | Section §2 contains JSON schema fragment with field list (session_id, prior_pause_commit, last_dispatch_id, RAID hash digest, gate_state, schema_version, written_at_iso, payload_size_bytes); references A-002 (write-outside-CLAUDE_PLUGIN_ROOT validated) and T-1-7 size budget; **must state chosen design cap = ≤ 1 MB (per FV-T-1-7 line 587 design recommendation)** with explicit note that 16 MB is observed-no-truncation upper bound only (line 580) — NOT the chosen cap. T-2-1 skeleton freezes this decision; T-2-3 elaborates rationale | T-2-1 | yes (with T-2-2, T-2-4) |
| T-2-4 | Section §3: gate.lock schema (cross-process coordination, lives in `$CLAUDE_PROJECT_DIR/.teamlead/gate.lock`) | RD | Section §3 contains lock-file format (PID + acquired_at + holder_role) + acquire/release semantics + stale-lock recovery (TTL ≥ baton write timeout); references I-009 flock-bug Stage 1 finding (parked) | T-2-1 | yes (with T-2-2, T-2-3) |
| T-2-5 | Section §4: launchd plist template + §6 environment portability (cross-cutting) | PO | Section §4 contains plist XML template with `${CLAUDE_PLUGIN_ROOT}`-aware path placeholders; Section §6 contains guard-tolerant probe-and-fall-back install procedure (per R-002 deployment-env signal); both sections reference T-1-5 launchd UX evidence | T-2-1 | yes (with T-2-6) |
| T-2-6 | Section §5: Security model (prompt-injection + git stash + non-Auto-Mode default) | PO | Section §5 explicitly addresses (a) prompt-injection mitigation: how baton-injected `-p` payload is sanitized vs A-001 validated mechanism; (b) git stash safety: never auto-resume across uncommitted changes without explicit baton hash match; (c) non-Auto-Mode default: resumed sessions default to interactive Auto-Mode-OFF per ~/CLAUDE.md §高風險操作; references I-001 silent-misroute Reviewer B concern | T-2-1 | yes (with T-2-5) |
| T-2-7 | Integration pass + internal QA review of full design doc | QA | Run `wc -l docs/specs/auto-resume-daemon-design.md` ≥ 200; `grep -c "TBD\|TODO\|<placeholder>"` returns 0; all 6 sections present; cross-references intact (Stage 1 RAID IDs resolve); sign-off note appended at doc end with QA timestamp | T-2-2, T-2-3, T-2-4, T-2-5, T-2-6 | no (final gate) |

### Verify clauses (per task — Goal-Driven Execution)

```bash
# T-2-1 verify
test -f docs/specs/auto-resume-daemon-design.md \
  && grep -cE '^## §[1-6]' docs/specs/auto-resume-daemon-design.md
# expected: file exists; section header count == 6

# T-2-2 verify
grep -A20 '^## §1' docs/specs/auto-resume-daemon-design.md \
  | grep -cE 'ARMED|PRE_COMPACT_TRIGGERED|BATON_WRITTEN|SESSION_RESUMED|POST_RESUME_VERIFIED|DONE|ABORTED'
# expected: ≥ 6 (every state name appears in §1)

# T-2-3 verify
grep -A30 '^## §2' docs/specs/auto-resume-daemon-design.md \
  | grep -cE 'session_id|prior_pause_commit|last_dispatch_id|gate_state|schema_version'
# expected: ≥ 5 (every required field appears)

# T-2-4 verify
grep -A20 '^## §3' docs/specs/auto-resume-daemon-design.md \
  | grep -cE 'PID|acquired_at|holder_role|TTL|stale'
# expected: ≥ 5

# T-2-5 verify
grep -A40 '^## §4' docs/specs/auto-resume-daemon-design.md \
  | grep -cE 'launchctl|bootstrap|\$\{CLAUDE_PLUGIN_ROOT\}|plist'
# expected: ≥ 4

# T-2-6 verify
grep -A40 '^## §5' docs/specs/auto-resume-daemon-design.md \
  | grep -cE 'prompt.injection|git stash|non-Auto-Mode|Auto-Mode-OFF'
# expected: ≥ 4

# T-2-7 verify (final integration)
test $(grep -c "TBD\|TODO\|<placeholder>" docs/specs/auto-resume-daemon-design.md) -eq 0 \
  && test $(wc -l < docs/specs/auto-resume-daemon-design.md) -ge 500 \
  && grep -cE '^## §[1-6]' docs/specs/auto-resume-daemon-design.md
# expected: 0 placeholders; ≥500 lines (tightened from 200 per Opus PlanAudit revision; aligns with PO §4 length estimate 580-810 lines lower bound); 6 section headers
```

### kT estimates per task (Stage 2 baseline 150 kT total)

| Task | Owner | kT | Rationale |
|---|---|---|---|
| T-2-1 | PO | 15 | Skeleton + cross-ref table; small write but high cognitive load (extracts from Stage 1 RAID) |
| T-2-2 | RD | 12 | State machine; technical density |
| T-2-3 | RD | 10 | Baton schema; JSON field-list |
| T-2-4 | RD | 8 | gate.lock; smaller schema |
| T-2-5 | PO | 20 | launchd plist + env portability; XML template + install procedure |
| T-2-6 | PO | 25 | Security model; 3 distinct subdomains, narrative-heavy |
| T-2-7 | QA | 20 | Integration pass + cross-ref validation + sign-off note |
| Sub-total | — | **110** | — |
| Reserve (Gate_Req + buffer) | — | **40** | PlanAudit mid-stage step-review + CCB-Light contingency + final integration |
| **Total** | — | **150** | Within Stage 2 baseline |

### Plan execution sequence summary

| Order | Task(s) | Why this order |
|---|---|---|
| 1 | T-2-1 | Establishes skeleton + cross-ref anchors so parallel section drafters share consistent structure |
| 2 (parallel batch) | T-2-2 / T-2-3 / T-2-4 (RD batch) ‖ T-2-5 / T-2-6 (PO batch) | Sections independent once skeleton fixed; RD owns 3 schema sections, PO owns 2 narrative sections — both batches dispatched in parallel |
| 3 | T-2-7 | QA integration pass after all 5 section drafts return; final placeholder/cross-ref/sign-off check |
| **Total dispatches** | **3 waves** (1 + parallel + 1) | Maximizes parallelism while keeping skeleton coherent |

### Stage 2 close — DoD

Before Stage 2 close commit:

1. T-2-7 verify command returns 0 placeholders + ≥500 lines + 6 section headers
2. PlanAudit verdict at PLAN_AUDIT == APPROVED or APPROVED_WITH_REVISIONS (per Charter Success Criteria) — **CONFIRMED 2026-05-03**: Opus PlanAudit verdict APPROVED_WITH_REVISIONS / selected_id=A; CEO override to B via CCBL-003 (advisor-recommended)
3. CEO_Gate_2_PLAN_PRE_EXEC passes before Stage 2 EXECUTING begins — **CONFIRMED 2026-05-03T15:14+08:00**: CEO accepted Opus advisor B-recommendation
4. Stage 2 actual cost ≤ 100% of 150 kT baseline (post-hoc validation; carry to Stage 3 budget calibration if exceeded). Updated estimate: ~163 kT (PLANNING 30 + PLAN_AUDIT 10 + advisor 5 + revisions 3 + EXECUTING 110 + integration 5) — slight overspend acceptable; contingency 70 kT absorbs.

### Rollback plan for partial Stage 2 close (per Opus PlanAudit revision)

If T-2-2..T-2-6 parallel batch returns mixed APPROVED + FAIL status at GATING:

1. **Gate-blocking failures (any FAIL on cross-section interface)**: halt T-2-7 integration; re-dispatch failing PM with corrected expectations; if 2nd attempt also FAIL → ESCALATED. Do NOT merge partial Stage 2 doc.
2. **Non-blocking failures (1 section FAIL but does not break cross-section interface)**: write partial design doc with the failing section marked `## §N — DEFERRED` with explicit RAID-I tracker; CCB-Light to defer that section's content to Stage 3 dogfood; CEO approval at CEO_Gate_2_partial.
3. **Mid-stage step-review FAIL on T-2-1 (skeleton)**: critical — halt parallel batch dispatch; re-dispatch T-2-1 with reviewer feedback; do NOT proceed to T-2-2..T-2-6 until T-2-1 step-review PASS (per advisor I-020 recommendation).
4. **Cost overrun (>200 kT actual cost)**: trigger CCB-Heavy mid-stage; CEO arbitrates extend-budget vs descope.

### Acceptance-criteria-stub to verify-clause map (per Opus PlanAudit revision)

| Outline ac stub | T-2-X verify clause | Maps fully? |
|---|---|---|
| §2.1 "Every state listed has at least one entry transition" | T-2-2 grep state-name keywords (≥6) | Partial — verifies state mention, not transition arrow |
| §2.1 "State diagram renders the full lifecycle with no orphan nodes" | T-2-2 (no diagram-rendering verify) | NOT covered — T-2-2 EXECUTING must add `grep -c '^### Transition' §1 ≥ 7` AND visual review attestation in EXECUTING return |
| §2.2 "JSON schema lists every field with type + required/optional + one-line meaning" | T-2-3 grep field name list | Partial — verifies fields exist, not type/required annotations |
| §2.2 "Required fields cover prior_session_id, prior_pause_commit, branch, last_action_iso, progress_md_anchor, restore_prompt, auto_mode_resumed (default false)" | T-2-3 grep ≥5 (7 needed) | Partial — must update T-2-3 verify to ≥7 AND grep `auto_mode_resumed.*false` literal |
| §2.3 "Lock file format defined" | T-2-4 grep ≥5 keywords | Adequate |
| §2.4 "plist XML template with `${CLAUDE_PLUGIN_ROOT}` placeholders" | T-2-5 grep launchctl + ${CLAUDE_PLUGIN_ROOT} ≥4 | Adequate |
| §2.5 "Prompt-injection mitigation explicit" | T-2-6 grep keywords ≥4 | Partial — keyword grep doesn't validate substantive coverage |
| §2.6 (env-portability cross-cutting) | T-2-5 (combined with §4) | Adequate |
| **Action**: PMs in EXECUTING MUST address per-section "Partial" or "NOT covered" gaps via additional return evidence (not just verify-clause keyword grep) | — | — |

## Stage 3 — Phase 1 MVP Self-contained Hooks

**Goal**: 3 hook scripts + 4 lib scripts (7 total) as plugin-self-contained MVP. All scripts live in `hooks/` + `lib/` under `${CLAUDE_PLUGIN_ROOT}` and are implemented in **Python** per design.md §1 line 56 I-018 mandate. No host-skill dependencies other than Claude Code built-ins. Each script passes Sonnet step-review per CEO knob `step_review_mandatory=true`.

**Design spec**: `docs/specs/auto-resume-daemon-design.md` (frozen, 732 lines, 6 sections). All acceptance criteria below cite line numbers from this frozen spec. Do NOT modify design.md without CCB-Light.

**Stage 3 baseline budget**: 235 kT (PO 15 / RD 120 / QA 70 / Gate_Req 30).

**I-018 language constraint** (design.md line 56): All state-changing actors that interact with the filesystem are implemented in **Python** (not bash). **I-031 spec-gap arbitration** (Opus PLAN_AUDIT verdict APPROVED_WITH_REVISIONS / Option B): Charter line 14 names `*.sh` extensions; design.md §1 line 56 (FROZEN spec) mandates Python; reconciliation = Charter wording is plan-tracking and reconciles toward FROZEN spec via TeamLead routine update (NOT CCB-Light). All 7 scripts are `*.py` files with Python shebangs `#!/usr/bin/env python3` and are directly executable via `chmod +x`. hooks.json wrapper (`{"description":...,"hooks":{...}}`) points to `.py` executables. CCBL-Stage3-001 closed-resolved by this arbitration.

**I-023 dogfood instrumentation**: T-3-9 owns latency/frequency probes. Metric targets with explicit pass/fail thresholds: (1) PreCompact→daemon read latency ≤ 30s; (2) T-S-4 fault→awareness latency ≤ 5min; (3) T-S-3 mid-pause checkout false-positive rate ≤ 5%. Below-target metrics → RAID-I carry-forward to v0.1.8+, NOT Stage 3 close blocker. Evidence written to `docs/specs/phase-3-evidence/`.

### Stage 3 deferred-question resolutions (Opus PLAN_AUDIT inline)

Per Opus PLAN_AUDIT shared revision #6, PO outline §6 deferred questions Q4/Q5/Q8/Q9 resolved before EXECUTING:

- **Q4 (gate-lock library vs subprocess invocation)**: **subprocess** — preserves all-libs-are-independent-scripts invariant; modest subprocess overhead acceptable; aligns with Q8 minimal-validation answer
- **Q5 (baton-writer stdin vs named-file)**: **stdin** — avoids tempfile proliferation; matches PO outline preference; T-3-2 verify clauses use stdin pattern
- **Q8 (baton-writer schema validation depth)**: **key-presence-only validation** — no type coercion; baton-writer rejects payload missing any of 7 required keys (per T-3-2 acceptance (e) realignment); deeper validation belongs in handoff-builder + pre-compact orchestrator
- **Q9 (T11 reaper torn-tmp quarantine scope)**: **YES** — `lib/gate-lock.py` reaper quarantines `baton.json.tmp` artifact (renames to `baton.json.tmp.quarantined-<ISO>`) on stale-lock recovery; design.md §2 says T11 reaper handles torn writes, and `gate-lock.py` IS the T11 implementer; T-3-3 acceptance to be expanded by RD during EXECUTING dispatch

### Task list

| ID | Title | Owner | Acceptance | blockedBy | parallel-safe | kT estimate |
|---|---|---|---|---|---|---|
| T-3-1 | Scaffold `hooks/` + `lib/` dirs + plugin manifest registration | RD | (a) `hooks/` and `lib/` dirs exist under `${CLAUDE_PLUGIN_ROOT}`; (b) `hooks/hooks.json` uses canonical wrapper format `{"description":...,"hooks":{...}}` (per hooks.json format note in Stage 1 execution conventions, tasks.md line 73); (c) all 7 script files stubbed as non-empty executables (`chmod +x`); (d) `grep -cE '"PreCompact"\|"Stop"\|"SessionStart"' ${CLAUDE_PLUGIN_ROOT}/hooks/hooks.json` returns ≥ 3; (e) no design.md modification | none | no (entry point) | 5 |
| T-3-2 | `lib/baton-writer.py` — atomic baton write (transparent transport) | RD | **[DONE — S3-D2 PASS]** (a) Python script with `#!/usr/bin/env python3` shebang (per I-018; design.md lines 56, 155-157); (b) writes `baton.json.tmp` then atomically renames to `baton.json` via `os.replace()` (design.md line 157); (c) sets `0600` perms immediately after rename (design.md line 156); (d) enforces ≤ 1 MB payload size cap with abort path (design.md lines 183-185); (e) **asserts payload contains all 7 required keys (key-presence + non-null) before atomic write; rejects with exit 1 if missing** — baton-writer is transparent atomic-write transport per PO outline §lib/baton-writer; field assembly is responsibility of pre-compact orchestrator + handoff-builder, NOT baton-writer (Opus PLAN_AUDIT cross-PM scope alignment); required key set: `session_id`, `prior_pause_commit`, `branch`, `last_action_iso`, `progress_md_anchor`, `restore_prompt`, `auto_mode_resumed` (design.md lines 165-172); (f) verify: `python3 ${CLAUDE_PLUGIN_ROOT}/lib/baton-writer.py --test-write /tmp/test-baton.json` exits 0 AND `python3 -c "import json,sys; d=json.load(open('/tmp/test-baton.json')); assert all(k in d for k in ['session_id','prior_pause_commit','branch','last_action_iso','progress_md_anchor','restore_prompt','auto_mode_resumed']); sys.exit(0)"` exits 0 — verify_evidence: ALL PASS (--self-test exit 0; 7-key assert exit 0; size-cap 1.1MB reject exit 1; missing-key reject exit 1; null-value reject exit 1; no-.tmp-on-failure PASS; perms 600 PASS; os.replace confirmed; auto_mode_resumed=False literal PASS) | T-3-1 | yes (with T-3-3) | 12 |
| T-3-3 | `lib/gate-lock.py` — gate.lock acquire/release | RD | (a) Acquire uses Python `os.open(O_CREAT\|O_EXCL\|O_WRONLY, 0o600)` (design.md lines 272-279); (b) lock-file JSON has 3 required fields: `pid`, `acquired_at`, `holder_role` (design.md lines 260-267); (c) release path: `os.unlink(gate.lock)` AFTER baton atomic rename (design.md line 281 — "MUST happen before the unlink"); (d) liveness probe: `os.kill(pid, 0)` raises `ProcessLookupError` → invoke stale-lock recovery; (e) default `ttl_seconds=90` (design.md line 290); (f) verify: `bash lib/gate-lock.py --test-acquire /tmp/test-gate.lock PreCompact && cat /tmp/test-gate.lock | python3 -c "import json,sys; d=json.load(sys.stdin); assert {'pid','acquired_at','holder_role'}.issubset(d); sys.exit(0)"` exits 0 | T-3-1 | yes (with T-3-2) | 10 |
| T-3-4 | `lib/handoff-builder.py` — RESUME payload construction | RD | (a) Reads `git rev-parse HEAD` (prior_pause_commit) and `git rev-parse --abbrev-ref HEAD` (branch) via subprocess; (b) computes `sha256sum PROGRESS.md` for `progress_md_anchor` (design.md line 169); (c) extracts most recent PROGRESS.md `Last Action` line for `last_action_iso` (design.md line 168); (d) sanitizes `restore_prompt` against allowlist: ASCII letters+digits+whitespace+punctuation set, disallows backtick/bare-dollar/`${...}` (design.md lines 449-452); (e) caps `restore_prompt` at 8 KB (design.md line 454); (f) verify: `bash lib/handoff-builder.py --build /tmp/test-payload.json && python3 -c "import json,sys; d=json.load(open('/tmp/test-payload.json')); assert 'restore_prompt' in d and 'prior_pause_commit' in d and 'progress_md_anchor' in d; sys.exit(0)"` exits 0 | T-3-2, T-3-3 | no | 10 |
| T-3-5 | `lib/notifier.py` — osascript wrapper with layered fallback | RD | (a) Attempts `osascript -e 'display notification ...'` as primary channel (design.md lines 539-542); (b) on any failure (osascript missing, exit non-zero, platform not macOS) → silent no-op (design.md line 542: "COURTESY, NOT SOURCE OF TRUTH"); (c) also writes `last-resume-failure.txt` as SOURCE OF TRUTH (design.md lines 526-536); (d) verify: `bash lib/notifier.py --test-notify "test message" /tmp/test-failure.txt && cat /tmp/test-failure.txt | grep -qE "test message"` exits 0 regardless of osascript availability | T-3-1 | yes (with T-3-2, T-3-3) | 6 |
| T-3-6 | `hooks/pre-compact.py` — PreCompact handler | RD | (a) On fire: acquires gate.lock via lib/gate-lock.py with `holder_role=PreCompact` (design.md lines 77, 283); (b) invokes lib/handoff-builder.py to construct baton payload; (c) invokes lib/baton-writer.py to perform atomic write; (d) releases gate.lock AFTER successful atomic rename (design.md line 281); (e) on write failure or size > 1 MB: transitions to ABORTED path — releases lock, writes `last-resume-failure.txt` (design.md lines 79, 183-184); (f) outputs valid JSON `{"continue": true}` (hook return per hook-development SKILL); (g) verify: `bash hooks/pre-compact.py --test-mode && python3 -c "import json,os; d=json.load(open('$CLAUDE_PROJECT_DIR/.teamlead/baton.json')); assert d['gate_state']=='BATON_WRITTEN'; sys.exit(0)"` exits 0 | T-3-2, T-3-3, T-3-4 | no | 15 |
| T-3-7 | `hooks/stop.py` — Stop handler with macOS notification | RD | (a) On fire: invokes lib/notifier.py to emit macOS notification (design.md lines 537-542); (b) checks for `last-resume-failure.txt` and surfaces banner if present (design.md lines 544-551); (c) outputs valid JSON `{"decision": "approve"}` (Stop hook return per hook-development SKILL); (d) verify: `bash hooks/stop.py --test-mode` exits 0 AND outputs JSON with `decision` field | T-3-5 | yes (with T-3-8) | 6 |
| T-3-8 | `hooks/session-start.py` — SessionStart handler, auto-inject RESUME context | RD | (a) On fire with no baton present: ensures `.teamlead/` dir, verifies gate.lock absent or stale-recoverable → transitions to ARMED (design.md lines 76, 124-125); (b) on fire with fresh baton (gate_state=BATON_WRITTEN): reads baton, recomputes `progress_md_anchor` (sha256 PROGRESS.md), re-validates `git rev-parse HEAD` == `prior_pause_commit` AND `branch` AND `last_action_iso` (design.md lines 202-203, 439); (c) mismatch on any field → ABORTED path + writes `last-resume-failure.txt`; (d) on all fields match: HALTs for CEO ack (Auto-Mode-OFF; does NOT auto-execute); composes RESUME banner for display (design.md lines 83-84); (e) on DONE (CEO ack): renames `baton.json` → `baton.consumed-<ISO>.json`, resets gate.lock (design.md line 84); (f) outputs valid JSON `{"continue": true, "systemMessage": "<RESUME banner or status>"}` (design.md §1 T8 side-effect); (g) verify: `bash hooks/session-start.py --test-mode-no-baton` exits 0 AND JSON output has `continue: true`; `bash hooks/session-start.py --test-mode-with-baton /tmp/test-baton.json` exits 0 AND output contains RESUME context | T-3-3, T-3-4, T-3-5 | yes (with T-3-7) | 20 |
| T-3-9 | Integration tests + dogfood instrumentation (I-023) | RD | (a) `docs/specs/phase-3-evidence/` directory created with at least 3 evidence files; (b) Metric 1 (PreCompact→daemon read latency): `tools/measure-latency.sh` writes test baton + polls `gate_state=SESSION_RESUMED`; records wall-clock to `phase-3-evidence/latency-precompact-to-daemon.txt`; **target ≤ 30s; below-target = RAID-I carry to v0.1.8+, NOT Stage 3 close blocker**; (c) Metric 2 (T-S-4 fault→awareness latency): `tools/measure-fault-awareness.sh` injects failure baton + polls `last-resume-failure.txt` mtime; records to `phase-3-evidence/latency-fault-to-awareness.txt`; **target ≤ 5min; below-target = RAID-I carry**; (d) Metric 3 (T-S-3 mid-pause checkout false-positive rate): `tools/measure-checkout-fp.sh` with synthetic HEAD-match scenarios (≥10 trials); records to `phase-3-evidence/false-positive-checkout.txt`; **target ≤ 5% false-positive rate; above-target = RAID-I carry**; (e) cross-ref consistency check: `tools/check-cross-refs.sh` greps all 3 hook scripts for references to lib scripts and validates the referenced file exists (`$CLAUDE_PLUGIN_ROOT/lib/<name>.py`); exits non-zero if any reference is broken; (f) **real-session integration test** (per RD I-032 + Opus PLAN_AUDIT missing-element 5): T-3-9 must include at minimum 1 manual-step test in `phase-3-evidence/real-session-integration.md` documenting interactive session test outcome (PreCompact + Stop + SessionStart fires verified); since `--print` mode does NOT fire hooks per I-014/I-015, this test is OUT-of-CI but IN-of-Stage-3-DoD; (g) verify: `bash tools/check-cross-refs.sh` exits 0 AND `test -f docs/specs/phase-3-evidence/latency-precompact-to-daemon.txt` exits 0 AND `test -f docs/specs/phase-3-evidence/real-session-integration.md` exits 0 | T-3-6, T-3-7, T-3-8 | no | 18 |
| T-3-10 | QA integration sweep + Stage 3 close report | QA | (a) All 7 hook + lib scripts are executable (`ls -l hooks/*.py lib/*.py \| grep -v '^-rwx'` returns empty); (b) hooks.json static-validation: `python3 -c "import json; json.load(open('${CLAUDE_PLUGIN_ROOT}/hooks/hooks.json'))"` exits 0 AND each `command` entry resolves to existing `.py` file with shebang `#!/usr/bin/env python3` (NOTE: per I-014/I-015 `--print` mode does NOT fire hooks; deferred runtime registration check to Stage 3 dogfood real-session validation in T-3-9); (c) cross-refs between hooks and lib scripts verified via `tools/check-cross-refs.sh` exits 0; (d) `grep -rE "os.replace|os.open|O_CREAT|O_EXCL" lib/ hooks/` returns ≥ 3 matches (Python actors present); (e) `grep -rE "#.*TODO\|#.*TBD\|#.*FIXME" hooks/ lib/` returns 0 (no debug artifacts); (f) Stage 3 close report written to `docs/specs/phase-3-evidence/stage-3-close-report.txt` with: total lines per script, step-review verdict per script, I-023 metric observations | T-3-9 | no | 15 |

### Verify clauses (per task — runnable post-EXECUTING)

```bash
# T-3-1 scaffold verify
grep -cE '"PreCompact"|"Stop"|"SessionStart"' ${CLAUDE_PLUGIN_ROOT}/hooks/hooks.json
# expected: >= 3

# T-3-2 baton-writer verify
python3 ${CLAUDE_PLUGIN_ROOT}/lib/baton-writer.py --test-write /tmp/test-baton.json \
  && python3 -c "import json,sys; d=json.load(open('/tmp/test-baton.json')); assert all(k in d for k in ['session_id','prior_pause_commit','branch','last_action_iso','progress_md_anchor','restore_prompt','auto_mode_resumed']); sys.exit(0)"
# expected: exit 0

# T-3-3 gate-lock verify
python3 ${CLAUDE_PLUGIN_ROOT}/lib/gate-lock.py --test-acquire /tmp/test-gate.lock PreCompact \
  && cat /tmp/test-gate.lock | python3 -c "import json,sys; d=json.load(sys.stdin); assert {'pid','acquired_at','holder_role'}.issubset(d); sys.exit(0)"
# expected: exit 0; cleanup: rm -f /tmp/test-gate.lock

# T-3-4 handoff-builder verify
python3 ${CLAUDE_PLUGIN_ROOT}/lib/handoff-builder.py --build /tmp/test-payload.json \
  && python3 -c "import json,sys; d=json.load(open('/tmp/test-payload.json')); assert 'restore_prompt' in d and 'prior_pause_commit' in d and 'progress_md_anchor' in d; sys.exit(0)"
# expected: exit 0

# T-3-5 notifier verify
python3 ${CLAUDE_PLUGIN_ROOT}/lib/notifier.py --test-notify "test message" /tmp/test-failure.txt \
  && grep -q "test message" /tmp/test-failure.txt
# expected: exit 0; silent no-op on osascript failure is acceptable

# T-3-6 pre-compact verify
python3 ${CLAUDE_PLUGIN_ROOT}/hooks/pre-compact.py --test-mode \
  && python3 -c "import json,os; d=json.load(open(os.environ.get('CLAUDE_PROJECT_DIR','.') + '/.teamlead/baton.json')); assert d.get('gate_state')=='BATON_WRITTEN'; sys.exit(0)"
# expected: exit 0

# T-3-7 stop verify
python3 ${CLAUDE_PLUGIN_ROOT}/hooks/stop.py --test-mode \
  | python3 -c "import json,sys; d=json.load(sys.stdin); assert 'decision' in d; sys.exit(0)"
# expected: exit 0

# T-3-8 session-start verify (no-baton path)
python3 ${CLAUDE_PLUGIN_ROOT}/hooks/session-start.py --test-mode-no-baton \
  | python3 -c "import json,sys; d=json.load(sys.stdin); assert d.get('continue')==True; sys.exit(0)"
# expected: exit 0

# T-3-9 cross-ref check + evidence dirs
bash ${CLAUDE_PLUGIN_ROOT}/tools/check-cross-refs.sh \
  && test -f docs/specs/phase-3-evidence/latency-precompact-to-daemon.txt
# expected: exit 0 (cross-refs intact; at least one evidence file present)

# T-3-10 QA sweep verify
ls ${CLAUDE_PLUGIN_ROOT}/hooks/*.py ${CLAUDE_PLUGIN_ROOT}/lib/*.py | xargs -I{} test -x {} \
  && grep -rE "os\.replace|os\.open|O_CREAT|O_EXCL" ${CLAUDE_PLUGIN_ROOT}/lib/ ${CLAUDE_PLUGIN_ROOT}/hooks/ | grep -c "." | awk '{exit ($1 >= 3) ? 0 : 1}'
# expected: exit 0 (all scripts executable + Python actors present)
```

### kT estimates per task (Stage 3 baseline 235 kT total)

| Task | Owner | kT | Rationale |
|---|---|---|---|
| T-3-1 | RD | 5 | Scaffold only; dirs + stub scripts + hooks.json registration |
| T-3-2 | RD | 12 | Atomic write + 7-field baton + size cap + Python subprocess pattern |
| T-3-3 | RD | 10 | O_CREAT\|O_EXCL semantics + liveness probe + stale-lock TTL |
| T-3-4 | RD | 10 | SHA-256 anchor + allowlist sanitizer + git subprocess calls |
| T-3-5 | RD | 6 | osascript wrapper + fallback + file write; small surface |
| T-3-6 | RD | 15 | PreCompact integrates lib/gate-lock + lib/baton-writer + lib/handoff-builder; most complex hook |
| T-3-7 | RD | 6 | Stop handler; straightforward — invokes lib/notifier + outputs JSON |
| T-3-8 | RD | 20 | SessionStart; highest complexity: no-baton path + baton re-validation + CEO-ack halt + rename + stale-baton fallback |
| T-3-9 | RD | 18 | Integration tests + I-023 3 latency metrics + check-cross-refs.sh |
| T-3-10 | QA | 15 | Integration sweep + stage close report + step-review evidence |
| Sub-total | — | **117** | — |
| Step-review overhead (10 scripts × ~2 kT Sonnet) | — | **20** | CEO knob step_review_mandatory=true |
| Gate_Req + CCB-Light + governance overhead (per Wave Refinement +10-15%) | — | **28** | PlanAudit + advisor + Wave Refinement +10-15% margin per Stage 2 close note; Wave Refinement baseline proposed ~30 kT via CCB-Light at PLAN_AUDIT |
| Reserve (buffer) | — | **10** | — |
| **Total projected** | — | **175** | Under 235 kT baseline by ~60 kT; Wave Refinement margin CCB-Light at PLAN_AUDIT may adjust |

### Plan execution sequence summary

| Order | Task(s) | Rationale |
|---|---|---|
| 1 | T-3-1 | Entry-point: scaffold; all others blocked on dirs + hooks.json |
| 2 (parallel batch A) | T-3-2 / T-3-3 / T-3-5 | Lib primitives independent of each other once scaffold exists |
| 3 | T-3-4 | Depends on T-3-2 (baton fields) + T-3-3 (lock semantics for write sequencing) |
| 4 (parallel batch B) | T-3-6 / T-3-7 / T-3-8 | Hooks integrate libs; T-3-6 depends on T-3-2/T-3-3/T-3-4; T-3-7 depends on T-3-5; T-3-8 depends on T-3-3/T-3-4/T-3-5; T-3-7 and T-3-8 are parallel |
| 5 | T-3-9 | Integration tests + I-023 instrumentation; requires all hooks complete |
| 6 | T-3-10 | QA sweep + close report; final gate |
| **Total waves** | **6 waves** (1 + parallel + 1 + parallel + 1 + 1) | — |

### Stage 3 close — DoD

Before Stage 3 close commit:
1. T-3-10 QA sweep verify passes (all scripts executable + Python actors present + cross-refs clean + stage close report written)
2. `tools/check-cross-refs.sh` exits 0
3. All T-3-X step-reviews (Sonnet) return PASS or PASS_WITH_MINOR (per CEO knob `step_review_mandatory=true`)
4. I-023 evidence files present in `docs/specs/phase-3-evidence/` (≥ 3 metric files)
5. No `.py` scripts contain `#.*TODO`, `#.*TBD`, or debug artifacts

### Stage 3 partial-close rollback plan (Opus PLAN_AUDIT shared revision #4 — parallels Stage 2 close rollback)

Four scenarios for partial Stage 3 close (mixed PASS+FAIL across 7 scripts):

- **(a) All 7 scripts PASS step-review** → standard close path; T-3-9 + T-3-10 → CEO_Gate_3 → Stage 4
- **(b) 1-2 scripts FAIL step-review with surgical retry available** → 1 retry per script per `retry_cap_per_step=1`; if retry PASSes, treat as Stage 2's I-029/I-030 retry-fix-success precedent (RAID-I closed-by-retry; Stage 3 close proceeds)
- **(c) ≥3 scripts FAIL OR T-3-9 integration test fails OR retry exhausted** → escalate ESCALATED state; CEO arbitration required; options include (i) reset to PLAN_AUDIT for plan revision (CCB-Heavy if structural rebaseline needed), (ii) close Stage 3 partial with explicit RAID-D for unfinished scripts (deferred to Stage 4 rebaseline), (iii) abort charter
- **(d) I-023 dogfood metrics fail target thresholds (Metric 1 > 30s, Metric 2 > 5min, Metric 3 > 5%)** → carry as RAID-I to v0.1.8+, NOT Stage 3 close blocker per T-3-9 design; scripts close with metric_status="below-target-but-functional" annotation in stage-3-close-report.txt

### Plan candidates (K=3) — see return contract

## Stage 4 — Phase 2 Full Daemon (FINAL)

**Goal**: Ship `scripts/daemon.py` (launchd-supervised Python daemon) that advances the state machine from `BATON_WRITTEN` → `SESSION_RESUMED` via `claude --resume <session_id>` (interactive, NOT `-p`). Integrates cleanly with existing 3 hooks + 4 libs shipped in Stage 3. Includes launchd plist install script, install-probe verification, daemon-present I-023-M1 latency measurement, and first real-session interactive dogfood.

**Design spec authority**: `docs/specs/auto-resume-daemon-design.md` (FROZEN, 732 lines). Line citations below are authoritative. DO NOT modify design.md without CCB-Light.

**Stage 4 baseline budget**: 250 kT (PO 20 / RD 150 / QA 60 / Gate_Req 20).

**I-018 language constraint** (design.md line 56): daemon.py is a state-changing actor → Python only. subprocess for lib invocation (NOT import). Install script similarly Python per I-018 (bash heredocs with `launchctl` literal risk guard-intercept per I-019).

**I-014/I-015 carry**: real-session integration tests OUT-of-CI but IN-of-Stage-4-DoD (daemon.py must also support `--test-mode` for synthetic CI testing).

**I-023-M1 carry from Stage 3**: Metric 1 (PreCompact→Daemon read latency ≤ 30s) could not be measured in Stage 3 (no daemon). T-4-9 re-runs `tools/measure-latency.sh` with daemon present. Below-target → RAID-I carry to v0.1.8+, NOT Stage 4 close blocker.

**New RAID IDs** (avoid collision with I-001..I-045): use I-046+.

### Task list

| ID | Title | Owner | blockedBy | parallel-safe | kT est |
|---|---|---|---|---|---|
| T-4-1 | Scaffold daemon.py stub + .teamlead/daemon.pid contract + plist .in template update | RD | none | no (entry) | 8 |
| T-4-2 | daemon.py main loop — poll baton.json mtime + read/validate baton schema | RD | T-4-1 | no | 12 |
| T-4-3 | daemon.py T5 actor — `BATON_WRITTEN→SESSION_RESUMED` (gate.lock acquire + git stash + claude --resume spawn + success path) | RD | T-4-2 | no | 20 |
| T-4-4 | daemon.py T6 retry within BATON_WRITTEN — exponential backoff 1s/4s/16s + daemon-retries counter | RD | T-4-3 | no | 8 |
| T-4-5 | daemon.py T7 retry-exhausted → ABORTED — write last-resume-failure.txt + osascript notification + exit 0 | RD | T-4-4 | no | 6 |
| T-4-6 | daemon.py daemon-side T11 stale-lock reaper sweep — subprocess lib/gate-lock.py --reap on each poll cycle | RD | T-4-2 | yes (logically; implemented inline T-4-2 loop) | 6 |
| T-4-7 | daemon.py crash recovery + daemon.pid lifecycle — write pid on startup, cleanup on exit, handle RunAtLoad vs WatchPaths wakeup | RD | T-4-3 | no | 8 |
| T-4-8 | plist install script — Python install.py: render .plist.in → ~/Library/LaunchAgents, launchctl bootstrap, Layer 3 install-probe pong | RD | T-4-1 | yes (after T-4-1) | 10 |
| T-4-9 | Integration tests — daemon-present I-023-M1 latency measurement + tools/measure-latency.sh re-run + --test-mode synthetic CI | RD | T-4-5, T-4-6, T-4-7, T-4-8 | no | 14 |
| T-4-10 | Real-session manual-step dogfood (I-032 Stage 4 interactive test) — first interactive dogfood with daemon loaded | RD | T-4-9 | no | 10 |
| T-4-11 | QA close — acceptance criteria sweep + Stage 4 close report + cosmetic batch + commit | QA | T-4-10 | no | 18 |
| T-4-12 | Stage 4 GATING + REPORTING preparation (Gate_Forward + Gate_Requirement evidence + audit-trail rows) | QA | T-4-11 | no | 10 |

### Task acceptance criteria (with design.md line citations)

---

#### T-4-1 — Scaffold daemon.py stub + .teamlead/daemon.pid contract + plist .in template update

**Acceptance**:
- (a) `scripts/daemon.py` exists as non-empty Python file with `#!/usr/bin/env python3` shebang; executable (`chmod +x`); (design.md line 325 — `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/daemon.py --watch`)
- (b) Stub accepts `--watch <dir>` CLI arg and `--test-mode` flag (no-op in stub; wired for T-4-2 impl); exits 0 cleanly
- (c) Stub writes `${CLAUDE_PROJECT_DIR}/.teamlead/daemon.pid` with `str(os.getpid())` on startup using **0600 permissions** via `os.open(O_WRONLY|O_CREAT|O_TRUNC, 0o600)` + `os.replace` for atomic write (design.md §5 T-S-1 line 517); pid file is **NOT removed on clean exit** — next launchd respawn overwrites atomically (design.md §3.12 line 519). `_remove_pid` helper retained for T-4-8 uninstall but NOT registered to atexit. (Reconciles original tasks.md T-4-1(c) wording with design.md FROZEN spec at S4-D1 step-review FAIL → fix-and-retry; logged as I-055 for T-4-12 cosmetic batch.)
- (d) `docs/specs/auto-resume-daemon-design.md` NOT modified (constraint)
- (e) `hooks/`, `lib/`, `tools/` NOT modified (constraint)
- (f) Plist template at `templates/com.teamwork-leader.auto-resume-daemon.plist.in` exists (may already exist from Stage 3 scaffold; if absent, create from design.md lines 331-384 XML; if present, verify `${CLAUDE_PLUGIN_ROOT}/scripts/daemon.py` is the ProgramArguments entry)

**Verify clause**:
```bash
# (a) shebang + executable
head -1 /Users/HsuTse/ClaudeProject/teamwork-leader/scripts/daemon.py | grep -q '#!/usr/bin/env python3' && test -x /Users/HsuTse/ClaudeProject/teamwork-leader/scripts/daemon.py
# expected: exit 0

# (b) stub --watch + --test-mode
python3 /Users/HsuTse/ClaudeProject/teamwork-leader/scripts/daemon.py --watch /tmp/test-teamlead --test-mode
# expected: exits 0 within 5s

# (c) daemon.pid written
ls /Users/HsuTse/ClaudeProject/teamwork-leader/.teamlead/daemon.pid 2>/dev/null || echo "pid-file-absent-in-stub-acceptable"
# expected: file present OR "no daemon running" state documented

# (f) plist template
grep -q 'scripts/daemon.py' /Users/HsuTse/ClaudeProject/teamwork-leader/templates/com.teamwork-leader.auto-resume-daemon.plist.in
# expected: exit 0
```

---

#### T-4-2 — daemon.py main loop — poll baton.json mtime + read/validate baton schema

**Acceptance**:
- (a) Main loop polls `${CLAUDE_PROJECT_DIR}/.teamlead/baton.json` mtime every 5 s (design.md line 276 — "daemon polls every 5 s")
- (b) On mtime change: reads baton; validates 7 required fields present + non-null (`session_id`, `prior_pause_commit`, `branch`, `last_action_iso`, `progress_md_anchor`, `restore_prompt`, `auto_mode_resumed`) — design.md lines 164-172
- (c) Checks `gate_state == "BATON_WRITTEN"` before acting (design.md line 64 — `BATON_WRITTEN` is the trigger state); ignores other gate_state values
- (d) In `--test-mode`: reads a test baton at `--watch <dir>/baton.json`, validates fields, prints `gate_state=<value>` to stdout, exits 0 without spawning claude
- (e) Loop includes T11 stale-lock reaper call (design.md line 304 — "daemon polls every 5 s and runs the reaper inline before its own acquire attempt") — delegated to T-4-6 impl but wired in loop

**Verify clause**:
```bash
# Write a valid test baton, run daemon in test-mode, verify it reads correctly
TEAMLEAD_DIR=/tmp/test-teamlead-$(date +%s)
mkdir -p "$TEAMLEAD_DIR"
python3 /Users/HsuTse/ClaudeProject/teamwork-leader/tools/write-synthetic-baton.py \
  --output "$TEAMLEAD_DIR/baton.json" \
  --gate-state BATON_WRITTEN
python3 /Users/HsuTse/ClaudeProject/teamwork-leader/scripts/daemon.py \
  --watch "$TEAMLEAD_DIR" --test-mode 2>&1 | grep -E "gate_state=BATON_WRITTEN|schema=valid"
# expected: output contains gate_state or schema validation confirmation; exit 0
rm -rf "$TEAMLEAD_DIR"
```

---

#### T-4-3 — daemon.py T5 actor — `BATON_WRITTEN→SESSION_RESUMED` transition

**Acceptance**:
- (a) Acquires gate.lock via subprocess `python3 lib/gate-lock.py --acquire <path> Daemon` BEFORE spawning claude (design.md lines 201-202, 283 — "Daemon acquires with holder_role=Daemon before spawning claude --resume")
- (b) Executes git stash safety net BEFORE spawning (design.md lines 468-480): `git -C ${CLAUDE_PROJECT_DIR} status --porcelain`; if dirty, `git -C ${CLAUDE_PROJECT_DIR} stash push -u -m "teamlead-resume-<session_id>-<iso>"`; writes stash ref to `.teamlead/last-stash.txt`
- (c) Validates `restore_prompt` allowlist (design.md lines 453-454 — "daemon re-runs the same allowlist check") before spawn; on rejection → T7 ABORTED path
- (d) Spawns `claude --resume <session_id> -p <restore_prompt>` via `subprocess.Popen` (NOT `subprocess.run`, so daemon.py does not block on resumed session; design.md lines 497-510 §4 daemon contract — A-001 VALIDATED primitive: `cmd = ["claude", "--resume", session_id, "-p", restore_prompt]`; Q4 resolution: `--resume` omits `--print`, the resumed session is interactive but the `-p` flag carries the new-turn restore_prompt input). Reconciles spec drift between §1 transition table (lines 55, 135) and §4 contract: §4 is authoritative.
- (e) On spawn success: updates `gate_state=SESSION_RESUMED` in baton via in-place edit under gate.lock (design.md line 201); releases gate.lock via subprocess `lib/gate-lock.py --release`
- (f) In `--test-mode`: simulates T5 without actually launching claude; writes `gate_state=SESSION_RESUMED` to test baton; exits 0

**Verify clause**:
```bash
# Synthetic T5 test-mode: writes SESSION_RESUMED to baton
TEAMLEAD_DIR=/tmp/test-t5-$(date +%s)
mkdir -p "$TEAMLEAD_DIR"
python3 /Users/HsuTse/ClaudeProject/teamwork-leader/tools/write-synthetic-baton.py \
  --output "$TEAMLEAD_DIR/baton.json" --gate-state BATON_WRITTEN
python3 /Users/HsuTse/ClaudeProject/teamwork-leader/scripts/daemon.py \
  --watch "$TEAMLEAD_DIR" --test-mode --self-test-t5 2>&1
python3 -c "
import json, os
d = json.load(open('$TEAMLEAD_DIR/baton.json'))
assert d.get('gate_state') == 'SESSION_RESUMED', f'Expected SESSION_RESUMED, got {d.get(\"gate_state\")}'
print('T-4-3 PASS: gate_state=SESSION_RESUMED')
"
rm -rf "$TEAMLEAD_DIR"
# expected: "T-4-3 PASS: gate_state=SESSION_RESUMED"
```

---

#### T-4-4 — daemon.py T6 retry within BATON_WRITTEN — exponential backoff

**Acceptance**:
- (a) On spawn failure (subprocess non-zero exit / FileNotFoundError for `claude` binary): increments retry counter in `.teamlead/daemon-retries` file (design.md line 81 — "Increment retry counter in `.teamlead/daemon-retries`")
- (b) Backoff sequence: 1 s, 4 s, 16 s before each retry attempt (design.md lines 135, 398 — "N=3 with exponential backoff (1 s, 4 s, 16 s)"; plist ThrottleInterval=10 s external complement)
- (c) After N=3 retries exhausted → invokes T7 ABORTED path (T-4-5) (design.md line 81 — "After N=3 retries → escalate to ABORTED")
- (d) In `--test-mode`: simulates 3 failed spawns with truncated backoff (1 ms instead of 1s/4s/16s), verifies counter reaches 3, transitions to ABORTED without side effects

**Verify clause**:
```bash
# Verify retry counter logic in test-mode (fast backoff)
TEAMLEAD_DIR=/tmp/test-t6-$(date +%s)
mkdir -p "$TEAMLEAD_DIR"
python3 /Users/HsuTse/ClaudeProject/teamwork-leader/tools/write-synthetic-baton.py \
  --output "$TEAMLEAD_DIR/baton.json" --gate-state BATON_WRITTEN
python3 /Users/HsuTse/ClaudeProject/teamwork-leader/scripts/daemon.py \
  --watch "$TEAMLEAD_DIR" --test-mode --self-test-t6-exhaust 2>&1 | tee /tmp/t4-t6-verify.txt
grep -q "retry.*3\|retries_exhausted\|ABORTED" /tmp/t4-t6-verify.txt && echo "T-4-4 PASS" || echo "T-4-4 FAIL"
test -f "$TEAMLEAD_DIR/daemon-retries" && cat "$TEAMLEAD_DIR/daemon-retries"
rm -rf "$TEAMLEAD_DIR" /tmp/t4-t6-verify.txt
# expected: "T-4-4 PASS"; daemon-retries file shows count=3
```

---

#### T-4-5 — daemon.py T7 retry-exhausted → ABORTED

**Acceptance**:
- (a) Writes `last-resume-failure.txt` at `${CLAUDE_PROJECT_DIR}/.teamlead/last-resume-failure.txt` with: ISO-8601 UTC timestamp, failing transition ID (T7), specific failure reason, suggested operator action, cross-ref to stash ref if `.teamlead/last-stash.txt` present (design.md lines 526-536)
- (b) Invokes `lib/notifier.py` subprocess for osascript best-effort notification (design.md lines 539-542 — "daemon invokes osascript … on any platform where osascript is absent or fails, this step is a silent no-op")
- (c) Updates `gate_state=ABORTED` in baton under gate.lock; releases gate.lock
- (d) Calls `os._exit(0)` (or `sys.exit(0)`) so launchd interprets as clean exit and does NOT respawn (design.md line 395 — "`KeepAlive: SuccessfulExit: false` → intentional T7 normal exits are NOT respawned")
- (e) In `--test-mode`: writes failure file to test dir; exits 0; does NOT fire osascript

**Verify clause**:
```bash
TEAMLEAD_DIR=/tmp/test-t7-$(date +%s)
mkdir -p "$TEAMLEAD_DIR"
python3 /Users/HsuTse/ClaudeProject/teamwork-leader/tools/write-synthetic-baton.py \
  --output "$TEAMLEAD_DIR/baton.json" --gate-state BATON_WRITTEN
python3 /Users/HsuTse/ClaudeProject/teamwork-leader/scripts/daemon.py \
  --watch "$TEAMLEAD_DIR" --test-mode --self-test-t7-abort 2>&1
test -f "$TEAMLEAD_DIR/last-resume-failure.txt" && grep -q "T7\|retry" "$TEAMLEAD_DIR/last-resume-failure.txt" && echo "T-4-5 PASS"
python3 -c "
import json
d = json.load(open('$TEAMLEAD_DIR/baton.json'))
assert d.get('gate_state') == 'ABORTED', f'Expected ABORTED, got {d.get(\"gate_state\")}'
print('gate_state=ABORTED confirmed')
"
rm -rf "$TEAMLEAD_DIR"
# expected: "T-4-5 PASS"; gate_state=ABORTED confirmed
```

---

#### T-4-6 — daemon.py daemon-side T11 stale-lock reaper sweep

**RAID-I I-049 inline resolution**: `lib/gate-lock.py` currently exposes `--acquire`/`--release`/`--test-acquire` only; **`--reap` subcommand is missing**. T-4-6 MUST extend `lib/gate-lock.py` with `--reap <lock_path>` subcommand as a surgical CCB-Light extension. This is the documented exception to CI-6 "hooks remain FROZEN" — CI-6 covers `hooks/` only; `lib/` extensions for daemon integration are within Stage 4 scope per design.md §3 stale-lock reaper contract (lines 287-293). Append CCBL-Stage4-T-4-6 entry to `docs/decisions/ccb-log.md` when applied. Bound: `--reap` is read-only inspect + conditional unlink; MUST NOT change `--acquire`/`--release`/`--test-acquire` behavior (verified by re-running existing `lib/gate-lock.py --self-test`).

**Acceptance**:
- (a) `lib/gate-lock.py --reap <lock_path>` subcommand added (CCB-Light); on stale lock (dead holder PID via `os.kill(pid, 0)` → `ProcessLookupError`, OR TTL expired per §3) → `os.unlink` + exit 0; on live holder → no-op + exit 0; on missing lock file → exit 0; existing `--self-test` still passes
- (b) On each poll cycle (before gate.lock acquire attempt), daemon calls subprocess `python3 lib/gate-lock.py --reap ${CLAUDE_PROJECT_DIR}/.teamlead/gate.lock` (design.md line 304 — "daemon polls every 5 s and runs the reaper inline before its own acquire attempt")
- (c) Reaper subprocess handles dead-holder detection + TTL expiry per §3 (design.md lines 287-293); daemon main loop does NOT re-implement reaper logic (subprocess delegation per I-018 / design.md line 291 — symmetric Python actors)
- (d) Logs reaper action to debug channel (stdout or `.teamlead/daemon.err` which is the plist StandardErrorPath, design.md line 397)
- (e) Reaper failure (subprocess non-zero) → log warning; continue poll loop; do NOT abort episode

**Verify clause**:
```bash
# Verify --reap subcommand exists in gate-lock.py and exits cleanly with no stale lock
python3 /Users/HsuTse/ClaudeProject/teamwork-leader/lib/gate-lock.py --reap /tmp/test-no-lock.lock 2>&1; echo "exit=$?"
# expected: exit=0 (no lock to reap → clean exit)

# Verify daemon --test-mode calls reaper per cycle
python3 /Users/HsuTse/ClaudeProject/teamwork-leader/scripts/daemon.py \
  --watch /tmp/test-empty-dir-$$ --test-mode --self-test-reaper 2>&1 | grep -qi "reap"
# expected: output contains "reap" confirming reaper call
```

---

#### T-4-7 — daemon.py crash recovery + daemon.pid lifecycle

**Acceptance**:
- (a) daemon.py writes `.teamlead/daemon.pid` with `str(os.getpid())` immediately after arg-parse / before poll loop (design.md line 291)
- (b) On clean exit (T7 exhausted, `--test-mode` done, SIGTERM): pid file is **NOT removed** by daemon.py — next launchd respawn overwrites atomically via `os.replace` (design.md §3.12 line 519 FROZEN spec authority). `_remove_pid` helper from T-4-1 retained for T-4-8 uninstall only; **NOT registered to atexit**. (Reconciles tasks.md T-4-7(b) wording with design.md FROZEN spec at S4-D5 wave 2 close → pre-T-4-7-dispatch resolution; logged as I-066 cosmetic batch entry for T-4-12; same spec-precedence rule as I-055 from T-4-1.)
- (c) On crash (unhandled exception): PID file left for reaper; launchd `KeepAlive: SuccessfulExit: false` + non-zero exit → respawn; next instance re-writes PID; prior stale PID file detected by `os.kill(pid, 0)` → `ProcessLookupError` → reaper removes (design.md line 291)
- (d) RunAtLoad behavior: daemon starts even if baton absent; polls and finds nothing; does not error; daemon.pid written immediately
- (e) WatchPaths wakeup behavior: launchd wakes daemon on `.teamlead/` directory change; daemon handles being woken with no fresh baton (polls, finds same mtime as last seen, no-ops)

**Verify clause**:
```bash
# PID file lifecycle test
TEAMLEAD_DIR=/tmp/test-t7pid-$(date +%s)
mkdir -p "$TEAMLEAD_DIR"
python3 /Users/HsuTse/ClaudeProject/teamwork-leader/scripts/daemon.py \
  --watch "$TEAMLEAD_DIR" --test-mode --self-test-pid 2>&1
# After clean exit, pid file should be removed
test ! -f "$TEAMLEAD_DIR/daemon.pid" && echo "T-4-7 PASS: pid cleaned up" || echo "T-4-7 FAIL: pid file still present"
rm -rf "$TEAMLEAD_DIR"
# expected: "T-4-7 PASS: pid cleaned up"
```

---

#### T-4-8 — plist install script (Python install.py)

**Acceptance**:
- (a) `scripts/install.py` exists; Python shebang; executable (per I-018 — Python not bash for filesystem ops; design.md line 602 — "uses python string substitution, not shell envsubst, to avoid bash-heredoc guard friction")
- (b) Layer 1: renders `templates/com.teamwork-leader.auto-resume-daemon.plist.in` → `~/Library/LaunchAgents/com.teamwork-leader.auto-resume-daemon.plist` via Python `str.format_map()` or `string.Template`; interpolates `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_PROJECT_DIR}` (design.md line 603)
- (c) Layer 1: invokes `launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.teamwork-leader.auto-resume-daemon.plist` via `subprocess.run`; on exit-0 → Layer 3 verification (design.md lines 601-607)
- (d) Layer 2: on non-zero exit or guard-block detection → writes `.teamlead/install-state.json` with `{"status":"manual-pending"}`; prints manual-install instructions pointing to `docs/install/manual-install.md` (design.md lines 612-624)
- (e) Layer 3: writes `${CLAUDE_PROJECT_DIR}/.teamlead/install-probe.json`; polls for `install-probe.pong.json` for 10 s; on timeout → prints degraded-mode warning; daemon still considered installed (design.md lines 629-641)
- (f) `--dry-run` flag: renders plist to stdout, prints launchctl command, skips actual bootstrap; safe on guard-blocked hosts
- (g) `--uninstall` flag: `launchctl bootout gui/$UID/com.teamwork-leader.auto-resume-daemon` + removes plist file

**Verify clause**:
```bash
# Dry-run test (safe; no launchctl invocation)
python3 /Users/HsuTse/ClaudeProject/teamwork-leader/scripts/install.py --dry-run 2>&1 | \
  grep -E "launchctl|bootstrap|com.teamwork-leader"
# expected: output shows rendered launchctl command; exit 0

# Plist template renders correctly
python3 -c "
import string, os
tpl = open('/Users/HsuTse/ClaudeProject/teamwork-leader/templates/com.teamwork-leader.auto-resume-daemon.plist.in').read()
env = {'CLAUDE_PLUGIN_ROOT': '/test/plugin', 'CLAUDE_PROJECT_DIR': '/test/project'}
rendered = string.Template(tpl).safe_substitute(env)
assert 'scripts/daemon.py' in rendered
assert '/test/plugin' in rendered
print('plist template render PASS')
"
# expected: "plist template render PASS"
```

---

#### T-4-9 — Integration tests + daemon-present I-023-M1 latency measurement

**RAID-I I-046 inline resolution**: `tools/measure-latency.sh` currently lacks `--dry-run` flag and `daemon_present` field. T-4-9 MUST extend the tool with both, as a surgical extension (NOT new tool). Bound: extension is additive — existing invocation without `--dry-run` retains pre-Stage-4 behavior. AC-4-F is satisfied via the extended tool.

**Acceptance**:
- (a) `tools/measure-latency.sh` extended with `--dry-run` flag and `daemon_present` field in emitted record (per AC-4-F design.md line 542); re-runs with daemon present; records wall-clock from baton-write to `gate_state=SESSION_RESUMED` in `docs/specs/phase-4-evidence/latency-daemon-present.txt`; target ≤ 30 s; below-target → RAID-I to v0.1.8+, NOT Stage 4 close blocker (design.md line 398 — ThrottleInterval=10 + backoff; I-023-M1 carry from Stage 3 close report)
- (b) `docs/specs/phase-4-evidence/` directory created; at least 2 evidence files present (latency + self-test results)
- (c) `--test-mode` synthetic CI test: `python3 scripts/daemon.py --watch /tmp/test-dir --test-mode` cycle covers T5+T6+T7 paths without launching real claude; evidence written to `phase-4-evidence/daemon-test-mode-results.txt`
- (d) `tools/check-cross-refs.sh` still exits 0 after daemon.py + install.py added (existing cross-ref tool extends to `scripts/` dir)
- (e) `tools/measure-fault-awareness.sh` re-run with daemon in-loop confirms T-S-4 latency still ≤ 5 min (validates daemon does not regress Metric 2; evidence appended)

**Verify clause**:
```bash
# Cross-refs still intact after Stage 4 additions
/Users/HsuTse/ClaudeProject/teamwork-leader/tools/check-cross-refs.sh; echo "exit=$?"
# expected: exit=0

# Evidence directory created
test -d /Users/HsuTse/ClaudeProject/teamwork-leader/docs/specs/phase-4-evidence && echo "dir PASS"
# expected: "dir PASS"

# daemon.py --test-mode self-test passes
python3 /Users/HsuTse/ClaudeProject/teamwork-leader/scripts/daemon.py \
  --watch /tmp/test-daemon-ci-$$ --test-mode --self-test 2>&1 | tail -5
# expected: output indicates PASS on T5+T6+T7 synthetic paths; exit 0
```

---

#### T-4-10 — Real-session manual-step dogfood (I-032 Stage 4 interactive test)

**Acceptance**:
- (a) At least 1 manual interactive session test documented in `docs/specs/phase-4-evidence/real-session-integration-s4.md`; records: daemon PID visible via `launchctl print gui/$UID/com.teamwork-leader.auto-resume-daemon`, baton-write triggered (observed in `.teamlead/baton.json`), daemon-wakeup observed (`.teamlead/daemon.out` shows poll cycle), `gate_state` progression visible (BATON_WRITTEN → SESSION_RESUMED sequence observed or simulated) (design.md line 80, I-032)
- (b) Out-of-CI per I-014/I-015 (`--print` mode does NOT fire hooks); manual-step test with real interactive Claude Code session
- (c) Evidence file includes: ISO timestamp, Claude version, daemon version env var (`TEAMLEAD_DAEMON_VERSION=v0.1.7`), observed latency measurement (baton mtime vs `gate_state=SESSION_RESUMED` write mtime), any anomalies or deviations from spec
- (d) If launchd install was blocked by I-019 guard on this host: document degraded-mode evidence path instead (manual fallback per §1 `BATON_WRITTEN` reaper note, design.md line 125); still closes as PASS_WITH_MINOR

**Verify clause**:
```bash
test -f /Users/HsuTse/ClaudeProject/teamwork-leader/docs/specs/phase-4-evidence/real-session-integration-s4.md \
  && grep -q "gate_state\|daemon" /Users/HsuTse/ClaudeProject/teamwork-leader/docs/specs/phase-4-evidence/real-session-integration-s4.md \
  && echo "T-4-10 evidence PASS"
# expected: "T-4-10 evidence PASS"
```

---

#### T-4-11 — QA close — acceptance criteria sweep + Stage 4 close report + cosmetic batch + commit

**Acceptance**:
- (a) `scripts/daemon.py` and `scripts/install.py` executable + Python shebang; `ls -l scripts/*.py | grep -v '^-rwx'` returns empty
- (b) No debug artifacts: `grep -rE "#.*TODO|#.*TBD|#.*FIXME" scripts/` returns 0 lines
- (c) Python actors present: `grep -rE "os\.replace|os\.open|O_CREAT|O_EXCL|subprocess" scripts/` returns ≥ 3 matches
- (d) `python3 -c "import py_compile; py_compile.compile('scripts/daemon.py'); py_compile.compile('scripts/install.py')"` exits 0 (syntax-clean)
- (e) `tools/check-cross-refs.sh` exits 0 (all lib references across hooks + daemon intact)
- (f) Stage 4 close report written to `docs/specs/phase-4-evidence/stage-4-close-report.txt` with: lines per new script, step-review verdict per task, I-023-M1 daemon-present latency result, real-session dogfood evidence pointer
- (g) Stage 4 cosmetic batch applied (any PASS_WITH_MINOR items from step-reviews); all deferred items logged as RAID-I to v0.1.8+

**Verify clause**:
```bash
# Syntax check
python3 -c "import py_compile; py_compile.compile('/Users/HsuTse/ClaudeProject/teamwork-leader/scripts/daemon.py'); py_compile.compile('/Users/HsuTse/ClaudeProject/teamwork-leader/scripts/install.py')" && echo "syntax PASS"

# No debug artifacts
grep -rE "#.*TODO|#.*TBD|#.*FIXME" /Users/HsuTse/ClaudeProject/teamwork-leader/scripts/ | wc -l
# expected: 0

# Stage 4 close report present
test -f /Users/HsuTse/ClaudeProject/teamwork-leader/docs/specs/phase-4-evidence/stage-4-close-report.txt && echo "report PASS"
```

---

#### T-4-12 — Stage 4 GATING + REPORTING preparation

**Acceptance**:
- (a) Gate_Forward evidence recorded in `docs/specs/phase-4-evidence/stage-4-close-report.txt` (same file as T-4-11 close report; gates are documented sections within)
- (b) Gate_Requirement (knob `gate_requirement_mode=final_only`; Stage 4 IS final stage): requirement-gate runner invoked per `tools/gate-requirement-runner.sh` or equivalent; evidence recorded
- (c) Charter budget tally updated: Stage 4 actual kT + project total ≤ 900 kT (currently 497/900 at Stage 4 entry; 250 kT baseline headroom = 153 kT positive variance)
- (d) `audit-trail.jsonl` rows for S4-GATE-FORWARD, S4-GATE-HUMAN (N/A — no UI artifacts), S4-GATE-REQUIREMENT, S4-CLOSE-REPORTING present (TeamLead-owned append, not RD)
- (e) `PROGRESS.md` Stage 4 → REPORTING transition noted (TeamLead-owned)

**Verify clause**:
```bash
# Final stage gate check — confirm this IS the final stage
python3 -c "print('Stage 4 is final stage per Charter: Phase 2 daemon implementation')"
# expected: prints confirmation; no code action by RD needed (TeamLead-owned gate artifacts)

# Budget headroom sanity check
python3 -c "
actual_entry = 497
stage4_baseline = 250
total_cap = 900
headroom = total_cap - actual_entry
print(f'Stage 4 headroom: {headroom} kT (baseline {stage4_baseline} kT → {headroom - stage4_baseline} kT positive variance)')
assert headroom >= stage4_baseline, 'Budget overrun at Stage 4 entry'
print('Budget PASS')
"
# expected: "Budget PASS"; headroom = 403 kT at entry
```

---

### Verify clauses (per task — runnable post-EXECUTING)

```bash
# T-4-1 scaffold verify
head -1 /Users/HsuTse/ClaudeProject/teamwork-leader/scripts/daemon.py | grep -q '#!/usr/bin/env python3' \
  && test -x /Users/HsuTse/ClaudeProject/teamwork-leader/scripts/daemon.py \
  && grep -q 'scripts/daemon.py' /Users/HsuTse/ClaudeProject/teamwork-leader/templates/com.teamwork-leader.auto-resume-daemon.plist.in
# expected: exit 0

# T-4-2 main loop verify
TDIR=/tmp/t42-$$; mkdir -p "$TDIR"
python3 /Users/HsuTse/ClaudeProject/teamwork-leader/tools/write-synthetic-baton.py --output "$TDIR/baton.json" --gate-state BATON_WRITTEN
python3 /Users/HsuTse/ClaudeProject/teamwork-leader/scripts/daemon.py --watch "$TDIR" --test-mode 2>&1 | grep -E "gate_state|schema"
rm -rf "$TDIR"
# expected: gate_state or schema mention in output; exit 0

# T-4-3 T5 actor verify
TDIR=/tmp/t43-$$; mkdir -p "$TDIR"
python3 /Users/HsuTse/ClaudeProject/teamwork-leader/tools/write-synthetic-baton.py --output "$TDIR/baton.json" --gate-state BATON_WRITTEN
python3 /Users/HsuTse/ClaudeProject/teamwork-leader/scripts/daemon.py --watch "$TDIR" --test-mode --self-test-t5
python3 -c "import json; d=json.load(open('$TDIR/baton.json')); assert d['gate_state']=='SESSION_RESUMED'; print('T5 PASS')"
rm -rf "$TDIR"
# expected: "T5 PASS"

# T-4-4 retry logic verify
python3 /Users/HsuTse/ClaudeProject/teamwork-leader/scripts/daemon.py --watch /tmp/t44-$$ --test-mode --self-test-t6-exhaust 2>&1 | grep -qE "retry.*3|retries_exhausted" && echo "T6 PASS"
# expected: "T6 PASS"

# T-4-5 ABORTED path verify
TDIR=/tmp/t45-$$; mkdir -p "$TDIR"
python3 /Users/HsuTse/ClaudeProject/teamwork-leader/tools/write-synthetic-baton.py --output "$TDIR/baton.json" --gate-state BATON_WRITTEN
python3 /Users/HsuTse/ClaudeProject/teamwork-leader/scripts/daemon.py --watch "$TDIR" --test-mode --self-test-t7-abort
test -f "$TDIR/last-resume-failure.txt" && grep -q "T7" "$TDIR/last-resume-failure.txt" && echo "T7 PASS"
rm -rf "$TDIR"
# expected: "T7 PASS"

# T-4-6 reaper verify
python3 /Users/HsuTse/ClaudeProject/teamwork-leader/lib/gate-lock.py --reap /tmp/no-lock-$$.lock; echo "reap exit=$?"
# expected: exit=0

# T-4-7 pid lifecycle verify
TDIR=/tmp/t47-$$; mkdir -p "$TDIR"
python3 /Users/HsuTse/ClaudeProject/teamwork-leader/scripts/daemon.py --watch "$TDIR" --test-mode --self-test-pid
test ! -f "$TDIR/daemon.pid" && echo "pid cleanup PASS" || echo "pid cleanup FAIL"
rm -rf "$TDIR"

# T-4-8 install script dry-run verify
python3 /Users/HsuTse/ClaudeProject/teamwork-leader/scripts/install.py --dry-run 2>&1 | grep -qE "launchctl|bootstrap" && echo "install dry-run PASS"
# expected: "install dry-run PASS"

# T-4-9 integration verify
/Users/HsuTse/ClaudeProject/teamwork-leader/tools/check-cross-refs.sh && echo "cross-refs PASS"
test -d /Users/HsuTse/ClaudeProject/teamwork-leader/docs/specs/phase-4-evidence && echo "evidence dir PASS"
# expected: both PASS

# T-4-10 real-session evidence verify
test -f /Users/HsuTse/ClaudeProject/teamwork-leader/docs/specs/phase-4-evidence/real-session-integration-s4.md && echo "dogfood evidence PASS"
# expected: "dogfood evidence PASS"

# T-4-11 QA sweep verify
python3 -c "import py_compile; py_compile.compile('/Users/HsuTse/ClaudeProject/teamwork-leader/scripts/daemon.py'); py_compile.compile('/Users/HsuTse/ClaudeProject/teamwork-leader/scripts/install.py')" && echo "syntax PASS"
grep -rE "#.*TODO|#.*TBD|#.*FIXME" /Users/HsuTse/ClaudeProject/teamwork-leader/scripts/ | wc -l
# expected: "syntax PASS"; 0 debug artifacts

# T-4-12 budget sanity verify
python3 -c "assert (900 - 497) >= 250; print('budget PASS')"
# expected: "budget PASS"
```

### kT estimates per task (Stage 4 baseline 250 kT total)

| Task | Owner | kT | Rationale |
|---|---|---|---|
| T-4-1 | RD | 8 | Scaffold + stub + pid contract + plist template check; straightforward but sets integration surface |
| T-4-2 | RD | 12 | Main poll loop + baton schema validation + gate_state filtering; medium complexity |
| T-4-3 | RD | 20 | T5 actor: gate.lock acquire + git stash probe + allowlist re-check + claude spawn + baton update + gate.lock release; highest complexity single task |
| T-4-4 | RD | 8 | Retry counter + backoff timing + N=3 exhaustion logic; mechanical but must be exact per spec |
| T-4-5 | RD | 6 | ABORTED path: failure file write + notifier subprocess + gate_state update + clean exit; spec-prescriptive |
| T-4-6 | RD | 6 | Reaper subprocess wiring in poll loop; implementation is delegation to existing lib/gate-lock.py |
| T-4-7 | RD | 8 | PID lifecycle + crash-recovery pattern + signal handler; cross-cuts all prior tasks |
| T-4-8 | RD | 10 | install.py: Layer 1+2+3 + dry-run + uninstall + I-019 guard-tolerance; env-portability concern elevates cost |
| T-4-9 | RD | 14 | Integration tests + M1 latency measurement + phase-4-evidence dir + check-cross-refs re-run; I-023-M1 re-measurement is the highest-value item |
| T-4-10 | RD | 10 | Real-session manual dogfood + evidence documentation; OUT-of-CI but IN-of-DoD |
| T-4-11 | QA | 18 | Sweep all scripts + cosmetic batch + close report + deferred RAID-I logging |
| T-4-12 | QA | 10 | Gate_Forward + Gate_Requirement + budget tally; final gate artifacts |
| Sub-total | — | **130** | — |
| Step-review overhead (2 new scripts × ~3 kT Sonnet) | — | **6** | CEO knob step_review_mandatory=true; 2 scripts (daemon.py + install.py); T-4-9+T-4-10 evidence is manual-step |
| Wave overhead (Gate_Req + CCB-Light + governance) | — | **20** | PlanAudit + advisor + final stage governance; Wave Refinement +10-15% margin per Stage 3 precedent |
| Reserve (buffer) | — | **14** | Daemon-first integration surprises; env-install unknowns (I-019 guard behavior with scripts/install.py) |
| **Total projected** | — | **170** | Under 250 kT baseline by ~80 kT; positive variance absorbed by reserve if env-install surprises surface |

### Plan execution sequence summary (Stage 4)

| Order | Task(s) | Rationale |
|---|---|---|
| 1 | T-4-1 | Entry-point: scaffold stub + pid contract + plist template check |
| 2 | T-4-2 | Main loop; blocked on T-4-1 stub |
| 3 (sequential) | T-4-3 → T-4-4 → T-4-5 | T5/T6/T7 state-machine chain; each depends on prior; sequential by state-machine causality |
| 4 (parallel) | T-4-6 + T-4-7 | Reaper wiring (inline in loop) + pid lifecycle (cross-cutting); both can be integrated simultaneously with T-4-2..5 body complete |
| 5 | T-4-8 | Install script; depends on T-4-1 (plist template exists); can start after T-4-1 but delayed here to allow daemon.py stabilization before wiring install-probe pong |
| 6 | T-4-9 | Integration tests; requires T-4-5 + T-4-6 + T-4-7 + T-4-8 all complete |
| 7 | T-4-10 | Real-session dogfood; requires T-4-9 (daemon installed + synthetic tests pass) |
| 8 | T-4-11 | QA sweep; all implementation complete |
| 9 | T-4-12 | Gate artifacts; final stage close |

### Stage 4 close — DoD

Before Stage 4 close commit:

1. All T-4-1 through T-4-11 tasks PASS or PASS_WITH_MINOR (step-review per CEO knob `step_review_mandatory=true`)
2. `scripts/daemon.py` exists + is executable + syntax-clean; implements T5/T6/T7/T11 per design.md §1 transition table (lines 80-87)
3. `scripts/install.py` exists + is executable + renders plist from template + Layer 1/2/3 install-probe logic present
4. `launchctl print gui/$UID/com.teamwork-leader.auto-resume-daemon` shows daemon loaded (on hosts where install succeeded per Layer 1); OR `.teamlead/install-state.json` shows `"status":"manual-pending"` with degraded-mode documented (hosts blocked by I-019)
5. I-023-M1 daemon-present latency MEASURED + result recorded in `phase-4-evidence/latency-daemon-present.txt`; below-target (> 30 s) → RAID-I carry to v0.1.8+, NOT close blocker
6. Real-session manual-step evidence present in `phase-4-evidence/real-session-integration-s4.md` (T-4-10 PASS or PASS_WITH_MINOR)
7. `tools/check-cross-refs.sh` exits 0 (Stage 3 + Stage 4 scripts all cross-reference intact)
8. Charter total budget ≤ 900 kT (497 entry + Stage 4 actual ≤ 403 kT; Stage 4 projected ~170 kT → ~667 kT total, well within 900 kT)
9. `docs/specs/phase-4-evidence/stage-4-close-report.txt` written with all task verdicts + metric observations

### Stage 4 partial-close rollback plan

- **(a) T-4-3 (T5 actor) FAILS step-review**: critical path — T-4-4/T-4-5 blocked; 1 retry per `retry_cap_per_step=1`; if 2nd attempt also FAIL → escalate ESCALATED; CEO arbitration (options: (i) descope T5 daemon spawn to v0.1.8+, ship daemon as monitor-only stub, (ii) extend budget via CCB-Heavy)
- **(b) T-4-8 (install script) FAILS on guard-blocked host**: NOT close blocker per I-019 precedent; document degraded-mode path; T-4-10 real-session test uses manual launchctl bootstrap (operator-run); close as PASS_WITH_MINOR
- **(c) T-4-10 (real-session dogfood) returns FAIL**: 1 retry; if 2nd FAIL → document specific failure in evidence file + carry to RAID-I; close Stage 4 as PASS_WITH_MINOR (real-session test is IN-of-DoD but not charter-blocking per I-032 precedent from Stage 3)
- **(d) T-4-9 I-023-M1 latency above 30 s target**: carry RAID-I to v0.1.8+; NOT Stage 4 close blocker per I-023-M1 carry-forward design (Stage 3 close report metric_status="below-target-but-functional" precedent)
- **(e) Budget overrun >250 kT Stage 4 actual**: trigger CCB-Heavy mid-stage; CEO arbitrates extend vs descope
