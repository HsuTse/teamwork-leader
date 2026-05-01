# Phase 3 Dogfood Plan

> **Source of truth**: this file. Phase 3 ships N1 trust-tiering + KMR mid-stage re-gate + audit-trail.jsonl persistence; their thresholds and weights are SEED values that need empirical calibration. This doc defines how that calibration runs.

## §1 Project selection criteria

The Phase 3 dogfood project must meet **all** of these:

- **≥ 3 stages** (so trust_tier rolling 3-stage window can fully populate at least once)
- **≥ 10 PM dispatches per stage** (so per-PM divergence_mean has statistical signal, not single-sample noise)
- **≥ 2 distinct PM roles activated** (PO + RD minimum; QA / UX optional but ideal)
- **At least 1 stage with `plan_candidates: [A, B, C]`** (Phase 2 T5 selector mode coverage)
- **Real work, not synthetic** — fabricated dispatches do not surface honest meta-block self-assessment patterns
- **Non-trivial DoD criteria** — toy projects don't reveal Mini Gate vs step-review disagreement patterns

Recommended dogfood candidates (CEO selects):

- A small backend feature behind real spec (e.g., 3-stage validation framework with PO/RD/QA + plan_candidates choice)
- A frontend page reorganization with UX activated
- Documentation refactor (PO-heavy, lower-risk validation of trust_tier promotion path)

## §2 Metrics collected

All from `<project>/docs/audit-trail.jsonl` and `<project>/docs/pre-task-estimates.jsonl` (joined on `dispatch_id`). Query via `jq` per `progress-md-schema.md` §Audit-trail sidecar.

### Phase 2 RSS metrics (validation prereq for Phase 3)

These MUST be confirmed before Phase 3 N1 (trust-tiering) operationalizes — see §6 Validation prerequisites:

- **`meta` block emission rate** = `count(records with meta != null) / count(total)`. Target ≥ 95% post-RSS rollout.
- **`verification_self_redundancy` distribution per PM** — must show variance (NOT a constant value across all dispatches). If a PM emits `5` on every dispatch, the field is dead and T9 anti-gaming Trigger 1 (`redundancy_mean ≥ 7 AND observed_PASS_mean < 0.5`) is structurally unfireable.
- **`divergence_score` distribution** — should approximate the τ=10% trigger analog (~10% of dispatches in `escalate` band, ≥ 10).

### Phase 3 N1 trust-tiering metrics

- **`trust_tier` distribution per PM per stage** — count of (`restricted` / `standard` / `trusted`) over time. Target steady state at Stage 5+: ≥ 1 PM at `trusted`, no PM stuck at `restricted` >2 stages.
- **Tier transition log** — each promotion/demotion + trigger reason (extract from `## Self-Audit` per stage).
- **Anti-gaming trigger fire rate** — count of forced-restricted firings per Trigger {1, 2, 3}. Target: triggers fire ≤ 5% of stage closes (false-positive guard).
- **Recovery time from `restricted` to `standard`** — count of stages from forced-restricted to recovery (per Rule 0.5 §Tier promotion / demotion table). Target: ≤ 4 stages average.

### Phase 3 KMR metrics

- **KMR fire rate** = `count(records with kmr_fired=true) / count(total)`. **Target ~30% per stage** (per stage-runbook.md §EXECUTING step 7a threshold rationale: useful but not noise).
- **Mini Gate verdict distribution** — `count(kmr_verdict = PASS) / count(kmr_fired)`. Expect 60–80% PASS (Mini Gate fires on divergence but most divergence is benign).
- **Mini-Gate-vs-step-review agreement rate** — joint count of (`step_review_verdict`, `kmr_verdict`) cross-tab. **Critical metric**: Mini Gate FAIL rate when step-review PASSed = "Mini Gate caught what step-review missed" rate. Target ≥ 5% (low enough that Mini Gate isn't a duplicate, high enough that it's a real signal).
- **Mini Gate trigger source distribution** — which `per_task_divergence_proxy` term dominated (budget_surprise / scope_surprise / ambient_instability / step_review_signal). If 90%+ of fires are step_review_signal, the other terms are dead and the formula needs re-balancing.

### Phase 3 selector_score metrics (Phase 2 T5 calibration carry-over)

- **selector_score selection vs CEO override rate** — count of times CEO `revise_next` after PLAN_AUDIT picked candidate A but CEO disagrees / count of total selector decisions. Target ≤ 10%.
- **K=2 vs K=3 candidate count distribution** — does RD PM use the cap?

## §3 Calibration triggers

When dogfood metrics breach these thresholds, calibrate via §4 governance:

### Rule 0 (Phase 2) thresholds (5, 10)

| Metric | Action |
|---|---|
| `escalate` rate > 20% steady state | Tighten thresholds (raise the 10 threshold to 12); CCB-Light if within ±2 |
| `escalate` rate < 3% steady state | Loosen thresholds (lower 10 to 8); CCB-Light |
| `watch` rate > 50% steady state | Either raise 5 threshold (less Watch noise) OR lower 10 (more escalation) — judgment call requiring CEO at next CEO_Gate |

### KMR proxy threshold (4)

| Metric | Action |
|---|---|
| KMR fire rate < 10% | Lower threshold to 3; CCB-Light |
| KMR fire rate > 50% | Raise threshold to 5; CCB-Light |
| step_review_signal dominates 90%+ fires | **Re-balance proxy formula**: increase weight on other terms or use weighted-sum instead of `max`. CCB-Heavy (formula structure change). |

### Trust_tier promotion/demotion thresholds (per Rule 0.5)

| Metric | Action |
|---|---|
| No PM ever reaches `trusted` after 3 stages | Loosen `trusted` criterion — drop `cross_pm_dispute_count == 0` to `≤ 1`; CCB-Light |
| Anti-gaming triggers fire > 10% per stage close | Raise trigger thresholds (e.g., `divergence_mean ≥ 7` → `≥ 8`); CCB-Light |
| `restricted` PM never recovers in ≤ 4 stages | Loosen recovery — `divergence_mean < 5` → `< 6`; CCB-Light |

### selector_score coefficients

| Metric | Action |
|---|---|
| Selection vs CEO-override rate > 20% | Re-balance coefficients (e.g., reduce `0.5 × cost_estimate_kT` weight if CEO consistently picks more expensive but better candidates); CCB-Light per coefficient adjusted |
| `novelty_bonus` always 1 (every candidate has non-`none` risk) | Reduce bonus or remove (it provides no signal); CCB-Light |

## §4 Calibration governance

**Detector**: TeamLead at stage close runs the metrics queries (jq-based, against audit-trail.jsonl + pre-task-estimates.jsonl). Surfaces breaches in `## Self-Audit` per stage as a one-line `calibration drift: <metric> = <value> (threshold: <range>)`.

**Surface to CEO**: at the next CEO_Gate AskUserQuestion, TeamLead includes a one-line summary: `Calibration drift candidates this stage: <list of metrics breaching thresholds>; recommend: <CCB-Light or CCB-Heavy proposal>`.

**CEO decision routing**:
- **CCB-Light** triggers (per `pmp-ccb.md` §CCB-Light triggers — Phase 2 T4 already added "Rule 0 threshold adjustment within ±2"): single-threshold adjustment within ±2 of current value. CEO approves at gate; PO logs entry in `<project>/docs/decisions/ccb-log.md`.
- **CCB-Heavy** triggers: cross-tier threshold change (e.g., adding new tier), formula structure change (e.g., switching `max` to weighted sum), threshold change beyond ±2. Requires `templates/ccb-heavy.md.tpl` CR + budget recalc.

**Logging**: All threshold changes logged in `PROGRESS.md ## Budget Baseline` with rationale citing the dogfood metric that motivated the change. No silent threshold edits.

## §5 Kill-switch (disable Phase 3 features)

If Phase 3 dogfood reveals N1 / KMR harms throughput more than it adds verification value, CEO may disable per-feature without rolling back the code.

### Disable trust-tiering (N1)

- Set CEO_Gate_0 budget knob: `trust_tier_mode: disabled` (knob defined in `templates/budget-proposal.md.tpl` §Budget knobs)
- TeamLead skips Rule 0.5 computation; defaults all PMs to `standard`
- Rule 2 sampling reverts to pure verify_policy knob (no tier override)
- `audit-trail.jsonl` `sampling_applied` will not produce `tier_forced_broad` / `tier_and_escalate_broad` values

### Disable KMR

- Set CEO_Gate_0 budget knob: `kmr_mode: disabled`
- TeamLead skips step 7a entirely (proceed step 7 → step 8)
- `pre-task-estimates.jsonl` is no longer written (saves ~5 lines/dispatch I/O)
- `audit-trail.jsonl` `kmr_*` fields write `null`
- Rolling-back-to-Phase-2: this is the path

### Disable Phase 3 entirely (full Phase 2 mode)

Both knobs above set to `disabled`. System functionally identical to Phase 2 closure state.

## §6 Validation prerequisites

Before Phase 3 N1 / KMR ship to a real project, these MUST be confirmed:

1. **`meta` block emission rate ≥ 95%** in Phase 2 dogfood data (synthetic or real). If lower, fix PM agent intake before activating Rule 0.5.
2. **`verification_self_redundancy` shows variance** — NOT a constant value across PMs/dispatches. If a PM systematically emits the same value, that PM's anti-gaming Trigger 1 is structurally unfireable; either redesign Trigger 1 or accept the gap explicitly.
3. **`expected_cost_kT` source path validated** — RD PM's selected `plan_candidate.cost_estimate_kT` is populated when candidate-set mode is used; tasks.md cost annotation format adopted in single-plan mode (per `progress-md-schema.md` §Pre-task estimates sidecar example).
4. **`expected_scope_files` and `expected_raid_delta` populated by RD PM** — KMR's `scope_surprise` and `ambient_instability` terms depend on these. Validate Phase 2 dogfood data: RD PM's plan output (in candidate-set mode `plan_candidates[].dod` text or single-plan mode tasks.md) consistently surfaces both fields. If RD systematically omits them, the corresponding KMR proxy terms are structurally dead and KMR's effective signal degrades to budget_surprise + step_review_signal only — document the gap explicitly OR redesign RD PM intake to require these fields before activating KMR.

If any prerequisite fails, **delay Phase 3 N1 / KMR activation** for that project; document the gap in PROGRESS.md `## Self-Audit` and remain in Phase 2 mode for the affected stages.

## §7 Test fixtures (synthetic verification)

Before dogfood on real project, hand-walk synthetic fixtures to verify rule firing:

### Fixture A — Rule 0.5 trust_tier promotion

Synthetic `audit-trail.jsonl` 3-stage window for one PM:
- Stage 1: 3 dispatches, all `divergence_score < 3`, no escalate, no cross-PM dispute
- Stage 2: same
- Stage 3 close → expected: tier = `trusted`

### Fixture B — Rule 0.5 anti-gaming Trigger 2 (direct divergence)

Synthetic 3-stage window:
- Stage 1: 3 dispatches, `divergence_score: [9, 8, 7]`, `divergence_flag: [escalate, escalate, watch]`
- divergence_mean ≈ 8 ≥ 7 → expected: tier forced `restricted` + RAID-I logged

### Fixture C — Rule 0.5 anti-gaming Trigger 3 (consecutive escalate)

Synthetic 3 dispatches in a row, all `divergence_flag: escalate` (across stages OK)
- Expected: tier forced `restricted` regardless of rolling-mean math

### Fixture D — KMR proxy budget_surprise fires

`pre-task-estimates.jsonl`: `expected_cost_kT: 12`
`audit-trail.jsonl` post-dispatch: `meta.token_estimate_kT: 24`
- ratio = 2.0; budget_surprise = min(9, round((2.0 - 1) × 10)) = 9 ≥ 4 → expected: Mini Gate fires

### Fixture E — KMR proxy step_review_signal fires + retry FAILed

step-review verdict: FAIL → step 7 retry dispatched → retry FAILed → step 7a runs:
- step_review_signal = 9; proxy = 9 ≥ 4
- Mini Gate fires (evidence-only, NOT consuming retry slot)
- If Mini Gate verdict = FAIL → expected: evidence appended to `## Exception` Detail; task ESCALATES

### Fixture F — KMR proxy step_review_signal fires + retry PASSed

Same as E but retry PASSed → step 7a runs:
- step_review_signal = 9 (the original verdict that triggered retry was FAIL; signal stays 9)
- Mini Gate fires (evidence-only)
- If Mini Gate verdict = FAIL → expected: RAID-I entry created with `severity: med` (or `high` if Mini Gate `non_functional_findings` includes high item); task remains complete

These fixtures should be checked into `<project>/docs/test-fixtures/phase-3-*.jsonl` at first dogfood project init; TeamLead walks each by hand and logs result in `## Self-Audit` before Phase 3 features are trusted on real dispatches.

## §8 CGR (Phase 4) deferral

CGR (Capacity-Gap-Aware Opus Routing) is **deferred** until N1 + KMR have ≥ 3 stages of clean dogfood data showing:

- Trust_tier signal is meaningful (some PMs reach `trusted`; some fall to `restricted`; transitions correlate with observable PM behavior)
- KMR fire rate stabilizes within 20–40% range (not 5% or 80%)
- selector_score selection rate aligns with CEO override rate < 15%

When all three are met, propose Phase 4 CGR plan with capacity-gap heuristic weights informed by the collected metrics.

## §9 Reporting cadence

- **Per-stage**: TeamLead writes calibration drift line in `## Self-Audit` (per §4 Detector)
- **Per CEO_Gate**: AskUserQuestion summary includes one-line calibration breaches (per §4 Surface)
- **At project close (ProjectClose)**: Phase 3 metrics aggregate per `pmp-lessons-learned.md` §Step 3 Value Realization summary; recommend Phase 4 readiness based on §8 CGR criteria.
