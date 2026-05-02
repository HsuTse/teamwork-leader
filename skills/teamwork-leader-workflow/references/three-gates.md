# Three Gates — Operational Mechanics

> **Source of truth**: design doc v3 §7. This file is the operational reference for QA PM (and TeamLead for Gate_Requirement).

## Common classifier schema (all 3 gates)

Every gate executor outputs structured classifier as a fenced ` ```json ` block:

```json
{
  "verdict": "PASS | PARTIAL | FAIL | INCONCLUSIVE",
  "root_cause": "code_bug | spec_ambiguity | spec_gap | environmental | inconclusive",
  "evidence": "<spec section anchor + code line + observed behavior>",
  "suggested_owner": "<PM name>",
  "dod_status": "met | partial | missed",
  "non_functional_findings": [
    {"type": "perf|security|a11y|reliability", "severity": "high|med|low", "note": "..."}
  ]
}
```

### Why structured classifier (not prose)

TeamLead routes failures based on `root_cause` → matching PM. **Prose interpretation is forbidden** — it leads to vibes routing (the very thing anti-rubber-stamp is meant to prevent).

### JSON parse failure (per design doc §7.0)

- **Parse exception** → TeamLead returns INCOMPLETE to gate executor with raw output + parse error message embedded
- **Re-dispatch ONCE** with corrected schema reminder
- **Second malformed** → escalate CEO with both raw outputs preserved verbatim
- **No prose fallback. No best-effort interpretation.**

This unifies with `dispatch-header.md` §Return contract (same INCOMPLETE → re-dispatch → escalate pattern).

## Sequencing under failure

Gates run sequentially: Forward → Human → Requirement. **No skipping**.

If Gate_Forward fails:
- Retry only Gate_Forward after fix
- Do NOT re-run Gate_Human / Gate_Requirement until prior gates pass

If Gate_Forward passes but Gate_Human fails:
- Retry only Gate_Human after fix
- Do NOT re-run Gate_Requirement until Gate_Human passes

Retry cap per gate: **2 rounds**. Still failing → escalate CEO.

## Gate_Forward — code logic trace

**Question**: 「程式跑起來符不符合我們以為它會做的事？」

**Executor**: QA PM dispatches Sonnet sub-agent with task:

```
Trace the execution path of <feature> from <entry point file:line> to <exit point file:line>.
Verify each branch matches spec section <anchor>.
Output structured classifier per three-gates.md schema as fenced ```json block.
```

**Tools allowed**: Read, Grep, Bash (for unit-test runs)

**Pass criteria**: Sonnet returns step-by-step trace ending in **observed correctness** (not "looks fine"). Each branch covered. `verdict: PASS`. `dod_status: met`.

**Fail handling per `root_cause`**:
- `code_bug` → bounce to RD PM (TeamLead schedules fix dispatch)
- `spec_ambiguity` → trigger CCB-Light (PO clarifies inline)
- `spec_gap` → CCB-Heavy
- `environmental` → bounce to RD or Ad-hoc DevOps PM
- `inconclusive` → escalate CEO immediately

## Mini Gate_Forward — content-conditioned, scoped (Phase 3 T12)

**When fires**: KMR per-task divergence proxy `≥ 4` per `references/stage-runbook.md` §EXECUTING step 7a (Phase 3 T10). NOT a stage-scheduled gate — fires per-task based on content signals.

**Distinction from full Gate_Forward**:

| | Full Gate_Forward | Mini Gate_Forward |
|---|---|---|
| **Scope** | Full stage scope (cross-cutting concerns, all features) | **Single task's `artifacts_touched` only** |
| **When** | At GATING state, sequentially before Gate_Human | Mid-EXECUTING, between step 7 and step 8 |
| **Trigger** | Stage end (scheduled) | KMR proxy ≥ 4 (content-conditioned) |
| **Cost** | Full Sonnet sub-agent trace + cross-cutting checks (~80 kT typical, estimated) | Subset trace ~20–40 kT (estimated; calibrate from Phase 3 dogfood data) |
| **Rubric** | Full §Gate_Forward criteria | Subset: trace within scope only; cross-cutting concerns skipped (deferred to full gate) |

**Procedure**:

1. QA PM dispatches Sonnet sub-agent (counted toward `parallel_pm_limit` knob) with task:

   ```
   Trace the execution path of the changes in the following files:
   <list of artifacts_touched paths from PM return>

   Verify each branch matches the relevant spec section.
   DO NOT trace cross-cutting concerns outside these files (those are deferred to full Gate_Forward at stage end).

   Output structured classifier per three-gates.md §Common classifier schema as fenced ```json block.
   ```

2. Sonnet returns common classifier (SAME schema as full Gate_Forward — `verdict` / `root_cause` / `evidence` / `suggested_owner` / `dod_status` / `non_functional_findings`).

3. **Fail handling** — depends on which branch fired Mini Gate (per `references/stage-runbook.md` §EXECUTING step 7a Decision block):

   **Branch A — Fired from PASS / PASS_WITH_MINOR step-review path** (proxy ≥ 4; step 7's retry slot still available):
   - `code_bug` / `spec_ambiguity` / `spec_gap` → bounce to `stage-runbook.md` §EXECUTING step 7's auto-fix path with Mini Gate's evidence as fix rationale. Same retry cap (1 per `auto-review-cadence.md`); second FAIL → ESCALATED.
   - `environmental` → bounce to RD or Ad-hoc DevOps PM.
   - `inconclusive` → escalate CEO per §JSON parse failure pattern.

   **Branch B — Fired from FAIL step-review path** (step 7's 1-retry already consumed synchronously; Mini Gate runs evidence-only):
   - Mini Gate verdict does **NOT** trigger re-dispatch (retry slot already consumed). Routing per `stage-runbook.md` §EXECUTING step 7a FAIL-branch:
     - `PASS` → log `kmr_verdict: PASS`; continue.
     - `PARTIAL` / `FAIL` + step 7's retry also FAILed → evidence appended to `## Exception` Detail field (task heading to ESCALATED).
     - `PARTIAL` / `FAIL` + step 7's retry PASSed → RAID-`[I]` entry with `severity: med` (or `high` if `non_functional_findings` includes high item); task remains complete.
     - `INCONCLUSIVE` → log only; do NOT double-escalate CEO (FAIL path already escalating or completing).

4. **Audit-trail logging**: write structured top-level fields to the dispatch's `audit-trail.jsonl` line per `references/progress-md-schema.md` §Audit-trail sidecar — `kmr_fired: true`, `kmr_verdict: <verdict>`, `kmr_root_cause: <root_cause if non-PASS>`. These are queryable via `jq` for Phase 3 dogfood metrics.

### Does NOT replace full Gate_Forward

Full Gate_Forward STILL runs at GATING. Mini Gate is **additional, not substitute** — mid-stage early warning catching ~30% of issues before they compound across tasks. Cross-cutting concerns (multi-file integration paths) STILL require full Gate_Forward at stage end.

### Why content-conditioned beats schedule-coarse

Triggering on **per-instance divergence** (rather than on a fixed schedule) catches problems where they actually surface. Full Gate_Forward at stage end catches errors AT MOST 4–7 tasks late. Mini Gate_Forward catches them **≥ 1 task earlier** on the dispatches that ACTUALLY exhibit divergence — surgical cost (subset scope), surgical timing (per-task trigger). (Approach inspired by KL-divergence-based triggering principles.)

### Threshold tuning

KMR firing threshold (`per_task_divergence_proxy ≥ 4`) lives in `references/stage-runbook.md` §EXECUTING step 7a. Calibrate per Phase 3 dogfood; threshold change per `references/pmp-ccb.md` §CCB-Light triggers (Rule 0 threshold ±2 = Light; beyond ±2 = Heavy).

## Gate_Human — UI operational verification

**Question**: 「真人操作介面，行為是不是預期的？」

**Executor**: QA PM, using executors listed in `dispatch-header.md` §Allowed tools for QA PM:
- `playwright-cli` (primary)
- `chrome-devtools-batch-scraper` (batch capture mode)

MCP variants (`mcp__plugin_playwright_*`, `mcp__claude-in-chrome__*`) are usable when those plugins are loaded; verify availability per `dispatch-header.md` §Skill availability check before invoking. Do NOT invoke MCP variants if not on the dispatch-header allow-list — surface to TeamLead for allow-list extension first.

**Procedure**:

1. Build scenarios per stage scope (golden path + error paths + edge cases)
2. For each scenario:
   - Run browser action (navigate, click, fill, etc.)
   - Capture screenshot/recording/state-check
   - Assert against expected outcome
3. **Subjective items** (UX feel, visual aesthetic):
   - Capture evidence
   - Mark `[SUBJECTIVE]` in output
   - QA returns to TeamLead — does NOT auto-pass
   - TeamLead surfaces to CEO via AskUserQuestion: "Subjective verification needed: <item>. Pass or revise?"

**Fail handling**:
- Code-side defect → RD PM
- UX/copy issue → UX PM (often + RD)
- Environmental (browser version, network) → Ad-hoc DevOps PM

## Gate_Requirement — external expert alignment

**Question**: 「實作是否符合需求文件 + 專案標準？」

**Default**: Final Stage only (cost mitigation). Mid-stage opt-in via CEO approval at CEO_Gate_(N-1).

**Executor**: TeamLead self-runs `bash ~/.claude/plugins/teamwork-leader/scripts/gate-requirement-runner.sh <manifest>` (claude -p shell-out). Use the absolute path — relative paths break from arbitrary project CWDs. Invocation via `bash` avoids requiring an execute bit on the script (PreToolUse hook blocks `chmod +x`); operator may `chmod +x` once manually if preferred.

### Manifest-based handoff contract (per design doc §7.3)

`claude -p` is a **fresh Claude session** that does NOT inherit context. Inputs must be passed via temp manifest file:

1. TeamLead writes `/tmp/teamlead-gate-req-<timestamp>.json`:
   ```json
   {
     "stage_name": "Stage 2",
     "stage_scope": "Backend validation framework",
     "docs_paths": ["<abs/path>/docs/spec.md"],
     "code_diff": "<git diff output, or file listing if non-repo>",
     "rules_paths": [
       "<plugin>/skills/teamwork-leader-workflow/references/discipline/surgical-change.md",
       "<plugin>/skills/teamwork-leader-workflow/references/discipline/simplicity.md",
       "<plugin>/skills/teamwork-leader-workflow/references/discipline/testing-discipline.md"
     ],
     "prompt": "Does this implementation satisfy the documented requirements and project conventions? Output classifier per three-gates.md schema."
   }
   ```

   **Path resolution requirement**: TeamLead MUST expand `~` to the absolute home path
   (`$HOME/...`) before writing the manifest. The runner does NOT auto-expand `~` —
   it uses `[[ -f "$path" ]]` directly, which treats `~` as a literal character. The
   tilde form above is shown for portability/readability in this example only.
2. `bash ~/.claude/plugins/teamwork-leader/scripts/gate-requirement-runner.sh /tmp/teamlead-gate-req-<timestamp>.json` reads manifest
3. Script builds full prompt (embedding all referenced files), pipes to `claude -p`
4. Captures `claude -p` stdout
5. TeamLead extracts ` ```json ``` block per §JSON parse failure
6. Manifest file deleted on success (plugin's cleanup discipline; project CLAUDE.md may override)

**Cost note**: each Gate_Requirement run = full Claude session (~50-100kT). Surfaced in StageReport token tally.

**Fail handling**:
- Gap in code → RD PM
- Gap in spec coverage → PO PM + CCB-Heavy
- Project convention violation → relevant PM (RD if styling/naming, PO if doc structure)

## Per-gate retry handling

Retry cap = 2 rounds (matches `auto-review-cadence.md`).

After fix, the SAME gate re-runs (not all gates). If 2 rounds exhausted → escalate CEO with all gate outputs preserved.

## Anti-rubber-stamp coupling

QA PM must use [TRUSTED]/[CLAIMED] discipline within gate output:
- `[TRUSTED]` evidence — QA personally executed the verify command and observed
- `[CLAIMED]` evidence — Sonnet sub-agent reported (QA must re-run sample per cross-PM verification rule)

TeamLead in turn re-runs ≥1 of QA's verify commands (anti-rubber-stamp sampling per design doc §3.3).
