# PROGRESS.md — Schema Reference

> **Source of truth**: design doc v3 §5.3, §11.1, §11.2, §11.6, §11.10. This file consolidates the schema.

## Required sections

PROGRESS.md is owned by TeamLead (sole writer). Sections appear in this order.

> **Ordering note**: design doc §5.3 specifies that `## Active Stage` / `## State` / `## Last Action` exist as state-machine fields, but does not constrain their relative position to `## Charter` / `## Budget Baseline`. The ordering below is canonical to this schema doc; cite this file when authoring or migrating PROGRESS.md.

```markdown
# Project: <name>

## Schema decision: <migrate|coexist|side-file> at YYYY-MM-DD
(per design doc §5.6; only present if existed before TeamLead)

## Charter
<from CEO_Gate_0 — Goal, success criteria, constraints>

## Budget Baseline
<from BudgetProposal at CEO_Gate_0 — knobs + per-stage kT baseline>

## Active Stage: <name>
## State: PLANNING | PLAN_AUDIT | EXECUTING | GATING | REPORTING | AWAITING_CEO | ESCALATED | COMPLETED | ABORTED
## Last Action: <ISO-8601 timestamp> [TRUSTED|CLAIMED] — <one-line Insight>

## RAID Register
- [R] ...
- [A] ...
- [I] ...
- [D] ...
- [V] ...

## Stage History
### Stage 1 (closed YYYY-MM-DD)
<full StageReport for Stage 1>
### Stage 2 (closed YYYY-MM-DD)
<full StageReport for Stage 2>
...

## CCB Activity
<rolling list of CCB-Light entries this stage; reset at stage close, PO appends each row to <project>/docs/decisions/ccb-log.md per pmp-ccb.md §Audit log file>

## CCB-Heavy Pending
(only present if pending; cleared when CEO decides)

## Self-Audit
<TeamLead's stage-by-stage record of verified vs unverified PM claims>

## Exception
(only present when active exception; cleared when escalation resolved)

## Lessons Learned
(only present at ProjectClose)
```

## Field semantics

### `## State`

Valid values:

| State | Meaning |
|---|---|
| `PLANNING` | PMs drafting plans for current Stage |
| `PLAN_AUDIT` | Opus reviewing PMs' plans |
| `EXECUTING` | Per-task dispatch + step-review loop |
| `GATING` | Running Gate_Forward / Human / Requirement |
| `REPORTING` | Drafting StageReport + WaveRefinement |
| `AWAITING_CEO` | At CEO_Gate (any) — waiting for response |
| `ESCALATED` | Retry exhausted or INCONCLUSIVE — CEO must respond |
| `COMPLETED` | Project closed (set at ProjectClose CEO_Gate_Final) |
| `ABORTED` | CEO chose `abort` verb |

### `## Last Action`

Single line, OVERWRITTEN on each TeamLead write (not append).

Format:
```
## Last Action: 2026-05-02T14:30:15+08:00 [TRUSTED] — RD PM completed T-1-3 (validateOrderPayload), QA cross-verified 1 of 3 RD test claims passed
```

Prefix:
- `[TRUSTED]` — TeamLead verified PM's claim against artifact (per anti-rubber-stamp §3.3)
- `[CLAIMED]` — PM reported but TeamLead has not yet verified (allowed mid-stage; must be `[TRUSTED]` before Stage close)

### `## RAID Register`

Per design doc §11.2 (with status fields per Round 2 PMP MED-3):

```markdown
- [R] <risk> | likelihood: low/med/high | impact: low/med/high | mitigation: <plan> | status: open/mitigating/closed | owner: <PM> | review_date: YYYY-MM-DD
- [A] <assumption> | validates if: <criterion> | validation_status: pending/validated/invalidated | validated_at: YYYY-MM-DD
- [I] <issue> | severity: low/med/high | owner: <PM> | next action: <step> | status: open/closed
- [D] <dependency> | external: y/n | blockedBy: <thing> | status: open/resolved
- [V] <value-criterion> | hypothesis: <expected outcome> | realized: pending/yes/partial/no | measured_by: <evidence>
```

### `## CCB Activity`

Per design doc §5.2 (StageReport sub-section) + value-driven.md `## Value Realized vs Hypothesis` cross-reference.

Rolling list of CCB-Light entries opened during the current stage. Format:

```markdown
## CCB Activity

- <YYYY-MM-DDThh:mm> | section: <PROGRESS.md anchor> | requested-by: <PM> | spec-impact: <one-line> | resolution: open/applied/rejected
- ...
```

**Lifecycle**:
- New CCB-Light entries appended as PMs surface them (see `pmp-ccb.md`)
- At stage close, this section's contents are migrated to `<project>/docs/decisions/ccb-log.md` (per `pmp-ccb.md` §Audit log file) and the section reset for next stage
- Cap rule per `pmp-ccb.md`: ≥3 same section / ≥5 stage total → auto-escalate to CCB-Heavy

### `## Stage History`

Append-only. Each stage gets a `### Stage N (closed YYYY-MM-DD)` header followed by the stage's StageReport content (per `templates/stage-report.md.tpl`).

When PROGRESS.md hits 2000-line ceiling (§11.6):
- Oldest stage's content moved to `<project>/docs/stage-archives/stage-N.md`
- Replaced in PROGRESS.md with one-line `<!-- archived to docs/stage-archives/stage-N.md -->`

### `## Self-Audit`

Per design doc §3.3 + Round 2 PMP NM1.

**Phase 2 RSS update**: structured per-dispatch records now live in `<project>/docs/audit-trail.jsonl` (see `## Audit-trail sidecar (Phase 2 T3)` below). PROGRESS.md `## Self-Audit` is reduced to a **per-stage human-readable summary**. Legacy in-flight projects (predating Phase 2 RSS) may retain the verbose format — see Migration note below.

Format (Phase 2 short form + Phase 3 trust_tier snapshot):

```markdown
## Self-Audit

### Stage 1
- I verified 8 of 12 PM claims this stage. Per-dispatch detail in `docs/audit-trail.jsonl`.
- divergence_flag distribution: aligned 9, watch 2, escalate 1, legacy_no_meta 0
- High-divergence dispatches surfaced (≥10): [list — PM/dispatch_id/divergence_score/divergence_flag]
- Sampling-rotation distribution: QA→RD (1), PO→Gate_Requirement (1), UX→RD (0)
- trust_tier snapshot (Phase 3 N1): PO=standard, RD=trusted, QA=trusted, UX=standard (changes since last stage: RD standard→trusted, UX trusted→standard — anti-gaming trigger §3 fired on UX divergence_mean 7.2)
```

The trust_tier line MUST list every activated PM. The "(changes since last stage: ...)" parenthetical is REQUIRED if any tier transitioned this stage; if no changes, write "(no changes since last stage)".

Format (legacy verbose — kept for projects predating Phase 2 RSS):

```markdown
## Self-Audit

### Stage 1
- I verified 8 of 12 PM claims this stage.
- Unverified items: [list with reason — typically time-bounded sampling]
- Highest-risk claim selected for verification: <claim> by <PM>
- Lowest-confidence claim selected: <claim> by <PM>
- Sampling rotation: QA cross-verified RD; PO cross-verified Gate_Requirement findings; UX cross-verified RD's Mezzanine claims
```

**Migration note**: For projects whose PROGRESS.md predates Phase 2 RSS, retain the verbose format until next stage close. From the next stage onward, emit short form + jsonl sidecar. Do NOT mid-stage convert (would break Resumption protocol §5.3 reconciliation).

### `## Exception`

Per design doc §11.10 (Round 2 PMP LOW-2). Only present when active. Format:

```markdown
## Exception (active)

- Type: budget_breach | gate_fail | raid_escalation | ccb_heavy_raised | cross_pm_dispute
- Stage: <N>
- Detail: <one paragraph>
- TeamLead action: surfaced to CEO at <ISO timestamp>
- CEO response pending
```

Cleared when CEO responds and TeamLead returns to normal flow.

## Size discipline (per design doc §11.6)

- **Hard ceiling**: 2000 lines
- **Trigger**: TeamLead checks line count after EVERY write
- **StageReport archival**: oldest stage → `<project>/docs/stage-archives/stage-N.md`; replaced with one-line back-reference
- **RAID archival**: closed/validated/resolved entries older than 2 stages → `<project>/docs/stage-archives/raid-archive.md`
- **Calibration warning**: if projection (current + projected next-stage delta) > 2000, TeamLead warns CEO at CEO_Gate_(N-1) to consider archival cadence increase OR re-baseline
- **Default PM intake**: TeamLead embeds excerpt only (current stage state + active RAID), not full PROGRESS.md
- **On-demand full read**: PM may explicitly request full PROGRESS.md via dispatch return field

## Stale guard (per design doc §11.3)

Before any TeamLead write to PROGRESS.md:
1. Snapshot mtime + sha256
2. Compare immediately before write
3. Mismatch → bail; surface diff to CEO
4. Backup `PROGRESS.md.bak.<timestamp>` before write

PMs do NOT write PROGRESS.md directly (per §3 authority matrix). They return payloads; TeamLead serializes.

## Audit-trail sidecar (Phase 2 T3)

Per `anti-rubber-stamp.md` Rule 0 (Phase 2 RSS), TeamLead persists structured per-dispatch verification records to `<project>/docs/audit-trail.jsonl` — append-only, one JSON object per line.

### Schema

Each line is a self-contained JSON object:

```json
{
  "ts": "<ISO-8601 timestamp>",
  "stage": 1,
  "pm_role": "rd-pm",
  "dispatch_id": "S1-D3",
  "dod_status": "met",
  "dod_confidence": 8,
  "scope_confidence": 9,
  "risk_class": "impl",
  "would_repeat_choice": true,
  "surprise_count": 1,
  "verification_self_redundancy": 5,
  "novelty_class": "routine",
  "deferred_decisions": 0,
  "observed_PASS": 1.0,
  "actual_diff_outside_scope": false,
  "divergence_score": 1.0,
  "divergence_flag": "aligned",
  "sampling_applied": "default",
  "verdict": "TRUSTED",
  "notes": "all 3 verify_evidence re-runs PASS",
  "kmr_proxy": 1.0,
  "kmr_fired": false,
  "kmr_verdict": null,
  "kmr_root_cause": null,
  "schema_validation_status": "pass"
}
```

Field constraints:
- `ts` — ISO-8601 with timezone offset
- `stage` — integer
- `pm_role` — `"po-pm" | "rd-pm" | "qa-pm" | "ux-pm" | "<ad-hoc-role>"`
- `dispatch_id` — TeamLead-assigned, format `S<stage>-D<seq>` (monotonic within stage)
- `dod_status` — `"met" | "partial" | "missed"`
- All 8 `meta` fields from `dispatch-header.md` are persisted: `dod_confidence`, `scope_confidence`, `risk_class`, `would_repeat_choice`, `surprise_count`, `verification_self_redundancy`, `novelty_class`, `deferred_decisions`. Numeric fields are integer `0..9`; enum values per `dispatch-header.md` §`meta` block field semantics; all become `null` for legacy dispatches without `meta`.
- `observed_PASS` — float `[0,1]` or `null` (read-only dispatch)
- `actual_diff_outside_scope` — boolean
- `divergence_score` — float (computed per Rule 0); `null` for legacy
- `divergence_flag` — `"aligned" | "watch" | "escalate" | "legacy_no_meta"`
- `sampling_applied` — reflects the **effective** sampling used (per `references/anti-rubber-stamp.md` Rule 2 precedence table); enum: `"minimal-per-dispatch" | "default" | "broad" | "escalated_broad" | "tier_forced_broad" | "tier_and_escalate_broad"`:
  - `minimal-per-dispatch` / `default` / `broad` — match `verify_policy` knob value (no escalation, no tier override)
  - `escalated_broad` — Rule 0 escalate forced broad on a non-`restricted` PM
  - `tier_forced_broad` — trust_tier `restricted` forced broad without per-dispatch escalate (Phase 3 N1)
  - `tier_and_escalate_broad` — both fire (Rule 0 escalate AND trust_tier `restricted`); preserves dual-cause provenance for dogfood analytics
- `verdict` — `"TRUSTED" | "CLAIMED"` matching the `## Last Action` prefix
- `notes` — optional, ≤200 chars (free-text only — do NOT pipe-delimit structured KMR data here; use the structured fields below)
- `kmr_proxy` (Phase 3 T10) — float `0..9` or `null` if KMR not run on this dispatch (e.g., legacy in-flight before Phase 3)
- `kmr_fired` (Phase 3 T10) — boolean: `true` if `kmr_proxy ≥ 4` triggered Mini Gate_Forward; `false` otherwise; `null` if KMR not run
- `kmr_verdict` (Phase 3 T12) — `"PASS" | "PARTIAL" | "FAIL" | "INCONCLUSIVE"` (Mini Gate_Forward classifier verdict) or `null` if not fired
- `kmr_root_cause` (Phase 3 T12) — `"code_bug" | "spec_ambiguity" | "spec_gap" | "environmental" | "inconclusive"` from Mini Gate classifier when verdict ≠ PASS; `null` otherwise
- `kmr_skipped` (Phase 3 migration) — boolean: `true` if dispatch lacked a `pre-task-estimates.jsonl` entry (legacy pre-rollout dispatch carried into a post-rollout stage); `false` for normal dispatches; `null` if KMR mode is disabled per `kmr_mode` knob
- `schema_validation_status` (v0.1.3) — enum `"pass" | "rejected_and_retried" | "rejected_and_escalated" | null`: persists the outcome of TeamLead's parse-time validation against the 11 mandatory fields (per `anti-rubber-stamp.md` §Mandatory rejection criteria):
  - `pass` — first attempt parsed cleanly with all 11 fields present
  - `rejected_and_retried` — first attempt INCOMPLETE → re-dispatched with schema reminder → second attempt PASS (this final row records the successful retry; the failed attempt is not separately persisted to keep audit-trail per-task 1:1 with `pre-task-estimates.jsonl`)
  - `rejected_and_escalated` — both attempts INCOMPLETE → ESCALATED (this row records the second failed attempt for diagnostic completeness; ESCALATED state separately captured in PROGRESS.md `## Exception`)
  - `null` — legacy in-flight dispatches predating v0.1.3 (no validation status recorded retroactively); also `null` if `schema_enforcement_mode == off` knob disables v0.1.3 enforcement
  - **Retry budget invariant**: schema validation re-dispatch (INCOMPLETE → second attempt) does **NOT** consume the §EXECUTING step 7 step-review retry slot. Schema validation has its own 1-retry pool (separate from step-review retry pool and Mini Gate retry pool). This separation is intentional: schema correctness fix is not a content-quality fix.

### Single-writer invariant (NOT stale-guard)

PROGRESS.md uses stale-guard (§Stale guard above) because it is **overwrite-edited**. `audit-trail.jsonl` is **append-only** with TeamLead as the sole writer (per design doc §3 authority matrix) — concurrent-write collision is structurally impossible in single-process orchestration.

DO NOT apply stale-guard semantics to jsonl: `mtime + sha256 → bail` is the wrong discipline for append-only files (every writer would see mtime mismatch trivially after a prior append). Stale-guard exists to prevent concurrent overwrites; append-only files have no overwrite-collision surface.

If concurrent writers ever become possible (e.g., parallel Phase 3 cron-driven analytics writing to the same file): use POSIX `flock(2)` advisory lock before append. Reject any design that adds a second writer without lock discipline.

### Migration / rollout

- **New projects (post-Phase 2 RSS)**: TeamLead creates `<project>/docs/audit-trail.jsonl` at project init (CEO_Gate_0); appends one record per PM dispatch from then on.
- **In-flight projects (predating Phase 2 RSS)**: TeamLead creates the file **lazily** on first dispatch after RSS rollout. Pre-rollout dispatches are not retroactively backfilled (their record lives only in PROGRESS.md verbose Self-Audit). Dispatches without `meta` log `divergence_flag: legacy_no_meta` so rollout completion is observable.
- **Resumption** (per §Resumption protocol): TeamLead reads PROGRESS.md `## Self-Audit` short summary first; queries `audit-trail.jsonl` only if cross-stage analysis is needed (e.g., for trust-tiering in Phase 3).

### Rotation / archival

- No 2000-line ceiling on `audit-trail.jsonl` (structured, queryable; does not compete with PROGRESS.md context budget)
- At project close, kept in `<project>/docs/audit-trail.jsonl` permanently as a project artifact
- For analytics or troubleshooting: query with `jq` or `python -m json.tool`

### Cross-references

- Schema operands: `anti-rubber-stamp.md` §Computed signals (`observed_PASS`, `actual_diff_outside_scope`)
- Routing producer: `anti-rubber-stamp.md` Rule 0
- `meta` block source: `dispatch-header.md` §`meta` block field semantics

## Pre-task estimates sidecar (Phase 3 T11)

Per `references/stage-runbook.md` §EXECUTING step 3 (Phase 3 KMR), TeamLead writes one record per **task pick** to `<project>/docs/pre-task-estimates.jsonl` BEFORE dispatching the PM. This file is the input side of KMR's per-task divergence proxy (per `references/stage-runbook.md` §EXECUTING KMR step + `references/three-gates.md` §Mini Gate_Forward).

Pairs with `audit-trail.jsonl`: pre-task-estimates.jsonl is the **pre-dispatch** record; audit-trail.jsonl is the **post-dispatch** record. KMR joins the two by `dispatch_id`.

### Schema

Each line is a self-contained JSON object:

```json
{
  "ts": "<ISO-8601 timestamp at task pick>",
  "stage": 1,
  "dispatch_id": "S1-D3",
  "task_id": "T-1-3",
  "expected_cost_kT": 12,
  "expected_scope_files": ["apps/api/src/order/validate.ts", "apps/api/src/order/types.ts"],
  "expected_raid_delta": 1
}
```

Field constraints:
- `ts` — ISO-8601 with timezone offset
- `stage` — integer (must match the corresponding audit-trail.jsonl `stage` for the same dispatch_id)
- `dispatch_id` — TeamLead-assigned (per `## Audit-trail sidecar` schema); SAME value as the post-dispatch audit-trail.jsonl line for this task
- `task_id` — RD PM's task list ID (e.g., `T-1-3` per `agents/rd-pm.md` §Workflow); identifies which task in the plan this estimate is for
- `expected_cost_kT` — integer kT estimate or `null`; **sourced from RD PM's selected `plan_candidate.cost_estimate_kT`** at PLAN_AUDIT close (per Phase 2 T5 `dispatch-header.md` §`plan_candidates` block); if single-plan mode, sourced from a tasks.md cost annotation in the form `T-N-X: <description> — verify: <command>; expected_cost_kT: <integer>`. If tasks.md has no cost annotation for this task, write `null` (KMR's `budget_surprise` term skips this dispatch). TeamLead does NOT independently estimate.
- `expected_scope_files` — list of file paths RD PM declared in their plan for this task (relative or absolute — match RD's own format)
- `expected_raid_delta` — integer count of new RAID entries TeamLead expects this task to surface (typically 0 for routine, 1–2 for novel work; sourced from RD plan's risk annotations)

### Single-writer invariant

Same as `audit-trail.jsonl` (per `## Audit-trail sidecar` §Single-writer invariant): TeamLead is the sole writer; append-only; NO stale-guard discipline. If concurrent-write features are added in Phase 4+, use `flock(2)`.

### Migration / rollout

- **New projects (post-Phase 3 KMR)**: TeamLead creates `pre-task-estimates.jsonl` lazily on first task pick.
- **In-flight projects (predating Phase 3 KMR)**: TeamLead creates the file lazily on first task pick after KMR rollout. Pre-rollout dispatches don't have pre-task records — KMR's proxy computation skips dispatches missing the pre-task entry (logs `kmr_skipped: true` as a structured top-level boolean in audit-trail.jsonl per the schema field above; do NOT pipe-delimit into `notes`).

### Cross-references

- KMR proxy formula: `references/stage-runbook.md` §EXECUTING KMR step
- Source of `expected_cost_kT`: `references/dispatch-header.md` §`plan_candidates` block (Phase 2 T5)
- Mini Gate_Forward triggered by KMR: `references/three-gates.md` §Mini Gate_Forward (Phase 3 T12)

## Resumption protocol (per design doc §5.3)

On `/teamwork-leader` invocation:
1. Read PROGRESS.md
2. Check `## State` field
3. Reconcile with `tasks.md` actual status:
   - If `## State: EXECUTING` but no tasks marked completed since last `## Last Action` → downgrade state to last verifiable checkpoint
4. If most recent `## Stage History` entry timestamp > `## Last Action` timestamp → trust `## Last Action` (was written after Stage History per atomic write rule)
5. Surface to CEO: "Resume Stage <X> from State <Y>?"

## In-flight dispatch loss on /clear

Task tool dispatches do NOT survive `/clear`. On resume:
- If state ∈ {`PLAN_AUDIT`, `GATING`, mid-step-review}, TeamLead must re-dispatch
- Cannot resume mid-flight; previous dispatch's work is lost (artifacts may persist if PM wrote to disk before /clear)
