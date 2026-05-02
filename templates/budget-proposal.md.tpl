# Budget Proposal — <PROJECT_NAME>

<!--
Authority: TeamLead drafts; CEO approves at CEO_Gate_0.
After approval, this content is serialized into PROGRESS.md ## Budget Baseline section.
Per design doc §9 + references/progress-md-schema.md §Budget Baseline.
-->

## Stage decomposition (rolling-wave)

<!-- Per references/pmp-wbs.md: rolling-wave. Stage 1 fully decomposed; later stages refined at each CEO_Gate_(N-1). -->

| Stage | Name | Scope summary | Decomposition depth |
|---|---|---|---|
| 1 | <name> | <one paragraph> | full WBS to task level |
| 2 | <name> | <one paragraph> | milestone level only (refined at CEO_Gate_1) |
| 3 | <name> | <one paragraph> | milestone level only |
| ... | ... | ... | ... |

## Per-stage kT baseline

<!-- Token budgets are estimates from TeamLead's BudgetProposal phase.
     PMs report `token_estimate_kT` per dispatch (per dispatch-header.md §Return contract).
     TeamLead aggregates and compares against this baseline. -->

| Stage | PO | RD | QA | UX | Ad-hoc | Gate_Req | **Stage total** |
|---|---|---|---|---|---|---|---|
| 1 | <X> | <X> | <X> | <X> | <X> | <X if mid-stage> | <sum> |
| 2 | <X> | <X> | <X> | <X> | <X> | <X if mid-stage> | <sum> |
| ... | ... | ... | ... | ... | ... | ... | ... |
| **Project total** | | | | | | <X final-stage> | <sum> |

## Circuit breaker thresholds (per design doc §9.1)

| Trigger | Threshold | Action |
|---|---|---|
| 80% per-stage warning | <0.8 * stage_total> kT | warn CEO at next CEO_Gate; PMs continue |
| 100% per-stage hard breach | <stage_total> kT | halt; surface to CEO immediately; cannot proceed without CCB-Light or budget extension |
| 2× cumulative project | <2 * project_total> kT | halt; CCB-Heavy required; project may be aborted |

## Risk-adjusted contingency

**Contingency reserve**: <X% of project total> kT — held by TeamLead, allocated only via CEO approval at CEO_Gate.

**High-risk stages flagged**: <list of stages with elevated risk; e.g., Stage 3 due to external API integration>

## Knobs (decided at CEO_Gate_0)

### Budget knobs (per design doc §9.1)

| Knob | Default | Project setting |
|---|---|---|
| `pms` | PO + RD + QA + UX (+ ad-hoc activated as needed) | <list activated PMs for this project> |
| `retry_cap_per_gate` | 2 | <override only with CEO consent> |
| `retry_cap_per_step` | 1 | <override only with CEO consent> |
| `parallel_pm_limit` | 2 (hard limit 4) | <override only if Auto Mode disabled> |
| `gate_requirement_mode` | final stage only | <final | mid-stage opt-in per stage> |
| `milestones` | derived from stage decomposition | <list per-stage milestones> |
| `verify_policy` (Phase 2 RSS) | `default` | <`minimal-per-dispatch` \| `default` \| `broad`> — see §`verify_policy` tier explanation below |
| `trust_tier_mode` (Phase 3 N1) | `enabled` | <`enabled` \| `disabled`> — `disabled` defaults all PMs to `standard`, skipping Rule 0.5 computation. Disable activation requires CCB-Heavy per `references/pmp-ccb.md` (rollback of deployed verification mechanism). |
| `kmr_mode` (Phase 3 KMR) | `enabled` | <`enabled` \| `disabled`> — `disabled` skips `stage-runbook.md` §EXECUTING step 7a entirely (no per-task divergence proxy, no Mini Gate firing); `pre-task-estimates.jsonl` is no longer written; `kmr_*` fields write `null` in audit-trail.jsonl. Disable activation requires CCB-Heavy. |
| `schema_enforcement_mode` (v0.1.3) | `strict` | <`strict` \| `warn` \| `off`> — `strict` (default) runs `stage-runbook.md` §EXECUTING step 5 schema validation per v0.1.3 with INCOMPLETE → re-dispatch (separate retry pool) → second INCOMPLETE → ESCALATED. `warn` runs validation but only logs `schema_validation_status` to audit-trail without rejecting (legacy v0.1.2 silent-acceptance behavior preserved). `off` skips validation entirely; `schema_validation_status: null`. **Any non-`strict` value requires CCB-Heavy ratification** — both (a) mid-flight transitions `strict → warn / off` AND (b) **initial-baseline declarations of `warn` or `off` in Stage 1 BudgetProposal at CEO_Gate_0** (i.e., the CCB-Heavy gate is not just for state transitions; it ensures CEO consciously waives the enforcement mechanism). See `docs/v0.1.3-rollback.md` §Mid-stage upgrade guidance §Initial-baseline rule. |
| `plan_audit_anti_self_skip_mode` (v0.1.6) | `strict` | <`strict` \| `warn` \| `off`> — Controls Rule 7 enforcement during PLAN_AUDIT-phase Opus reviewer dispatches (see `references/anti-rubber-stamp.md` §Rule 7 and `references/plan-audit-rubric.md`). `strict` (default): full enforcement — dispatch prompt blacklist injected + `suggested_fix` structured-field validation + 1-retry on detection + escalate CEO on persistence. `warn`: validate and log `plan_audit_self_skip_detected: true` in audit-trail when detection fires, but do NOT re-dispatch or escalate (preserves dispatch flow while retaining observability). `off`: skip Rule 7 entirely; `plan_audit_self_skip_detected` logged as `null`. **Both `warn` and `off` require CCB-Heavy** — these values roll back a deployed enforcement mechanism. |

### `verify_policy` tier explanation (Phase 2 T4)

Sets the **default sampling depth** that anti-rubber-stamp Rule 2 applies per PM dispatch. Rule 0 (Phase 2 RSS) can override per-dispatch — `divergence_score ≥ 10` forces `broad` regardless of this knob (logged as `sampling_applied: escalated_broad` in `<project>/docs/audit-trail.jsonl`).

| Tier | Sampling behavior | Cost | When to choose |
|---|---|---|---|
| `minimal-per-dispatch` | **highest-risk claim only** per dispatch (drops lowest-confidence sampling from current Rule 2) | cheapest | Mature codebase + experienced PM trust profile + low-stakes project. **Weakens Rule 2** — drops the lowest-confidence anti-rubber-stamp signal. |
| `default` | **highest-risk + lowest-confidence** per dispatch (current Rule 2 behavior — baseline) | medium | New projects; first dogfood; default for unknowns |
| `broad` | **100% verify_evidence re-run** per dispatch (every entry sampled) | expensive (saturation-tier verification) | High-stakes work; CEO wants maximum verification; security/compliance projects |

#### Choosing a tier — CEO_Gate_0 consent

- Selecting `minimal-per-dispatch` requires **explicit CEO consent at CEO_Gate_0** with rationale logged to `## Budget Baseline` notes (e.g., "trusted PM team, low project risk per RAID assessment"). It weakens anti-rubber-stamp Rule 2 — the lowest-confidence claim is no longer sampled, so blind spots can persist longer before being caught.
- Selecting `broad` is conservative and always allowed; cost trades off vs verification depth. Expect 2–3× per-dispatch verification token spend vs `default`.
- Selecting `default` (recommended baseline) is the current Rule 2 behavior; no special consent needed.

CEO can adjust between gates via CCB-Light per `references/pmp-ccb.md` (single-tier change is light; cross-tier jump such as `broad → minimal-per-dispatch` is heavy and requires CCB-Heavy).

### Session knobs (decided per /teamwork-leader invocation)

- **Auto Mode**: <enabled | disabled>
- **Worktree decision**: <isolation required | optional | none> per references/reuse-map.md row "Worktree Decision"
- **Final review**: <`/opus-review final` if git repo | inline review | skip with consent>
- **Schema decision**: <fresh PROGRESS.md | migrate | coexist | side-file> per references/schema-migration.md

## CEO sign-off

<!-- After CEO_Gate_0 approve verb, TeamLead writes timestamp + serializes to PROGRESS.md ## Budget Baseline. -->

- Approved at: <ISO-8601 timestamp>
- Verb: approve
- Notes: <any caveats from CEO>
