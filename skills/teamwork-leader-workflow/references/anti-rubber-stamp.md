# Anti-Rubber-Stamp — TeamLead Verification Discipline

> **Source of truth**: design doc v3 §3.2, §3.3, §3.4. This file is the operational reference.

User's explicit concern: TeamLead **不能被 PM 唬弄**. The line between PMP-style management and "AI summarizing AI" theater.

## Computed signals (operands for Rule 0 divergence routing)

Rule 0 (defined below) routes verification depth based on **divergence_score** — computed from the PM-emitted `meta` block (per `dispatch-header.md` §Return contract `meta`) plus these two signals derived from existing Rule 2 / Rule 3 outputs:

### `observed_PASS` ∈ [0, 1]

Derived from **Rule 2** execution (verify command re-run sampling):

```
observed_PASS = (verify_evidence entries TeamLead re-ran AND saw PASS)
              / (verify_evidence entries TeamLead sampled this dispatch)
```

Edge case: TeamLead sampled 0 entries (read-only dispatch, empty `verify_evidence` array) → `observed_PASS = N/A`; the corresponding divergence_score term is skipped (does not contribute to the sum).

### `actual_diff_outside_scope` ∈ {true, false}

Derived from **Rule 3** execution (sample diff inspection):

- Inspect git diff (or direct Read) of paths listed in `artifacts_touched`
- Compare those paths against the dispatch's declared scope (frozen PROGRESS.md excerpt + dispatch scope description from `dispatch-header.md`)
- `true` if **any** touched path falls outside declared scope; `false` otherwise

Edge case: empty `artifacts_touched` (read-only dispatch) → `actual_diff_outside_scope = false` by definition.

Both signals are **by-products of existing Rule 2 + Rule 3 execution** — no new tooling required. TeamLead persists these values per-dispatch in `audit-trail.jsonl` (per `progress-md-schema.md` §Audit-trail sidecar).

## The 5 mandatory verification rules (per §3.3)

For every PM dispatch return, TeamLead MUST run Rules 1–5 below. Phase 2 RSS adds **Rule 0** which fires first when the PM return includes a `meta` block — Rule 0 routes the *depth* of Rules 1–5 sampling, but does NOT replace any of them.

### Rule 0 — Parse `meta` first, route by `divergence_score` (Phase 2 RSS — additional)

For PM returns containing the `meta` block (per `dispatch-header.md` §`meta` block field semantics):

1. **Parse `meta`** before any other rule. Valid field types and ranges are defined in `dispatch-header.md` §`meta` block field semantics — quick reference: `dod_confidence` / `scope_confidence` / `surprise_count` / `verification_self_redundancy` / `deferred_decisions` are integers in `[0, 9]`; `risk_class` ∈ `{env, spec, impl, verifier, none}`; `novelty_class` ∈ `{routine, edge, first_seen}`; `would_repeat_choice` is boolean. If JSON parse of `meta` fails (malformed types, out-of-range values, unknown enum) → INCOMPLETE per §Mandatory rejection criteria.
2. **Compute `divergence_score`** using the operands defined in §Computed signals:

```
divergence_score = |dod_confidence - 9 * observed_PASS|
                 + |scope_confidence - scope_observed|
                 + (surprise_count > 3 ? 2 : 0)

where:
  dod_confidence   ∈ [0, 9]  (from PM meta)
  scope_confidence ∈ [0, 9]  (from PM meta)
  surprise_count   ∈ [0, 9]  (from PM meta)
  observed_PASS    ∈ [0, 1]  (computed signal; if N/A — read-only dispatch — drop term 1)
  scope_observed   = 9 if actual_diff_outside_scope == false else 0
```

**N/A case (read-only dispatch, `verify_evidence` empty)** — formula collapses to:

```
divergence_score = |scope_confidence - scope_observed|
                 + (surprise_count > 3 ? 2 : 0)
```

(theoretical range: 0–11)

3. **Route by `divergence_score`** (theoretical range: 0–20):

| `divergence_score` | Route |
|---|---|
| < 5 | **Aligned** — apply default sampling per `verify_policy` knob (Phase 2 T4); log `divergence_flag: aligned` |
| ≥ 5 AND < 10 | **Watch** — apply default sampling but log `divergence_flag: watch` in `audit-trail.jsonl`; persistent watch across 3+ stages → escalate in `## Self-Audit` |
| ≥ 10 | **Escalate** — force `verify_policy: broad` for THIS dispatch (re-run ALL `verify_evidence` entries) regardless of stage-level knob; mark `divergence_flag: escalate`; CEO sees count at next gate |

4. **Legacy in-flight dispatch (no `meta`)**: degrade to existing 5-rule sampling path. Log `divergence_flag: legacy_no_meta` in `audit-trail.jsonl` so the rollout completion is observable.

#### Worked examples

**Example A — Aligned (low divergence)**:
- PM emits `meta: { dod_confidence: 8, scope_confidence: 9, surprise_count: 1, ... }`
- TeamLead Rule 2 samples 3 verify_evidence, all 3 PASS → `observed_PASS = 1.0`
- TeamLead Rule 3 inspection: no diff outside scope → `actual_diff_outside_scope = false` → `scope_observed = 9`
- divergence_score = |8 − 9·1.0| + |9 − 9| + (1 > 3 ? 2 : 0) = 1 + 0 + 0 = **1**
- Route: < 5 → **Aligned**. Default sampling per knob.

**Example B — Escalate (high divergence)**:
- PM emits `meta: { dod_confidence: 9, scope_confidence: 7, surprise_count: 5, ... }`
- TeamLead Rule 2 samples 4 verify_evidence, only 1 PASS → `observed_PASS = 0.25`
- TeamLead Rule 3 inspection: 2 paths outside scope → `actual_diff_outside_scope = true` → `scope_observed = 0`
- divergence_score = |9 − 9·0.25| + |7 − 0| + (5 > 3 ? 2 : 0) = 6.75 + 7 + 2 = **15.75**
- Route: ≥ 10 → **Escalate**. Force `verify_policy: broad` for this dispatch; flag in `## Self-Audit`.

**Example C — Watch (mid-band divergence)**:
- PM emits `meta: { dod_confidence: 8, scope_confidence: 6, surprise_count: 2, ... }`
- TeamLead Rule 2 samples 2 verify_evidence, 1 PASS → `observed_PASS = 0.5`
- TeamLead Rule 3 inspection: no diff outside scope → `actual_diff_outside_scope = false` → `scope_observed = 9`
- divergence_score = |8 − 9·0.5| + |6 − 9| + (2 > 3 ? 2 : 0) = 3.5 + 3 + 0 = **6.5**
- Route: ≥ 5 AND < 10 → **Watch**. Default sampling per `verify_policy` knob applies, but `divergence_flag: watch` is logged to `audit-trail.jsonl`. Persistent watch across 3+ stages → `## Self-Audit` flags pattern.

#### Threshold rationale

- 0–4: honest calibration noise (PM self-assessment within ±1 of observed; 0 surprises)
- 5–9: accumulating drift on one dimension OR small drift on multiple; logged but action-deferred
- ≥10: significant divergence (one dimension fully misaligned, e.g., PM `dod_confidence=9` but `observed_PASS=0`) OR three dimensions all moderately off

Initial thresholds chosen so that escalate fires on roughly ~10% of dispatches in steady state — a target trigger frequency analog (inspired by KL-divergence-based triggering literature). **Tune empirically after Phase 2 dogfood**; thresholds live in this file (no separate config). CEO log destination depends on timing:

- **Initial setup at CEO_Gate_0** → log rationale to `PROGRESS.md ## Budget Baseline` (per `templates/budget-proposal.md.tpl` §`verify_policy` tier explanation; one-time decision serialized at project start)
- **Mid-project adjustment via CCB** → log to `PROGRESS.md ## CCB Activity` per `references/pmp-ccb.md` (single-tier change is CCB-Light; cross-tier jump or threshold change beyond ±2 is CCB-Heavy)

#### Phase 2 cross-references (all landed)

- `verify_policy` knob — landed at **Phase 2 T4** in `templates/budget-proposal.md.tpl` §`verify_policy` tier explanation
- `audit-trail.jsonl` — landed at **Phase 2 T3** in `progress-md-schema.md` §Audit-trail sidecar
- `meta` block source — landed at **Phase 2 T1** in `dispatch-header.md` §`meta` block field semantics

### Rule 0.5 — Per-PM trust_tier (Phase 3 N1)

`trust_tier` is a **per-PM rolling-window assessment** computed from `audit-trail.jsonl` history. It modifies how Rule 2 samples (per Rule 2 table below). Computed at **stage close** (REPORTING state, before AWAITING_CEO writes Self-Audit) and snapshotted in PROGRESS.md `## Self-Audit`.

#### Computation

**Source**: last 3 stages of dispatches in `<project>/docs/audit-trail.jsonl` filtered by `pm_role`.

**Inputs** (over the rolling 3-stage window):

- `divergence_mean` — mean of `divergence_score` across the PM's dispatches in the window
- `redundancy_mean` — mean of `verification_self_redundancy` across the window (first operational use of this field — see `dispatch-header.md` §`meta` block field semantics)
- `observed_PASS_mean` — mean of `observed_PASS` across the window (skip dispatches with `null` observed_PASS)
- `escalate_count` — count of dispatches with `divergence_flag: escalate` in the window
- `cross_pm_dispute_count` — count of times this PM's claim was refuted by sibling-PM cross-verification (per §Cross-PM verification below — sibling PM emits BLOCKED with refutation; TeamLead reverts `[TRUSTED]` to `[CLAIMED]` and logs in audit-trail.jsonl `notes` field; scheduling per `references/stage-runbook.md` §Cross-PM verification scheduling)

**Migration default** (PMs with <3 stages of audit-trail data):

- `pm_role` first appears at Stage 1 → tier = `standard` for Stages 1–2; tier computation begins at Stage 3 close
- Project upgrading from pre-Phase 2 (no audit-trail.jsonl history) → all PMs default `standard`; tier computation begins at first stage that produces 3 stages of post-RSS data
- **Reactivated PM** (dispatched, then absent for ≥3 stages, then re-dispatched): rolling 3-stage window contains <3 valid entries — default `standard` for first post-reactivation stage; if `audit-trail.jsonl` has earlier records outside the window showing prior `restricted` tier, TeamLead notes this in `## Self-Audit` ("RD reactivated; prior tier was restricted at Stage 4 — observe for re-trigger") so the historical context isn't silently lost

**Persistence**: `trust_tier` is **recomputed on demand from `audit-trail.jsonl`** at stage close — NOT stored as a separate file. If recomputation cost becomes prohibitive in Phase 4+ scale-out, introduce `trust-tier-cache.json` with stale-guard discipline (deferred — out of Phase 3 scope).

#### Tier promotion / demotion table (seed values; calibrate after Phase 3 dogfood)

| Tier | Promotion criterion (must satisfy ALL) | Demotion trigger (any one) |
|---|---|---|
| `trusted` | `divergence_mean < 3` AND `escalate_count == 0` AND `cross_pm_dispute_count == 0` over rolling 3-stage window | Any single `escalate` event OR any cross-PM dispute → demote 1 step (trusted → standard) |
| `standard` (default) | New PM, OR computed window doesn't satisfy `trusted` AND no demotion trigger fires | Rule 0.5 §Anti-gaming triggers (any) → demote to `restricted` |
| `restricted` | Anti-gaming trigger fired in last stage close OR `divergence_mean ≥ 7` OR `escalate_count ≥ 3 consecutive dispatches` | Returns to `standard` only after **next 3-stage window** with `divergence_mean < 5` AND `escalate_count == 0` (no jump straight to `trusted`). **If any anti-gaming trigger fires during the recovery window, the 3-stage recovery window resets from that stage** (no partial credit). |

**Calibration note**: thresholds (3 / 5 / 7 / counts) are **seed values for Phase 3 dogfood**. CEO can adjust per `pmp-ccb.md` §CCB-Light triggers ("Rule 0 threshold adjustment within ±2 of initial value"); cross-tier rule changes (e.g., adding new tier) are CCB-Heavy.

#### Anti-gaming triggers (force `restricted` regardless of rolling window math)

A PM is forced to `restricted` for the next stage if **any** of these fire:

1. **Loud-but-unreliable**: `redundancy_mean ≥ 7` AND `observed_PASS_mean < 0.5` over the window. PM is asserting trust they haven't earned.
2. **Direct-divergence trigger**: `divergence_mean ≥ 7` over the window. Even if redundancy is humble, sustained divergence is the most direct evidence of unreliability.
3. **Consecutive-escalate**: 3 consecutive dispatches with `divergence_flag: escalate` (regardless of stage boundary). Hard escalation pattern.

When forced to `restricted`, TeamLead also logs RAID-I issue:
- `severity: med`
- `content: "<PM role> tier-forced restricted: [<Trigger N>: <reason>; <Trigger M>: <reason>; ...]"` — when multiple triggers fire on the same PM at the same stage close, list ALL fired triggers semicolon-delimited inside the brackets (do NOT keep only the first). Example with both Trigger 1 and Trigger 2 firing: `"RD tier-forced restricted: [Trigger 1: redundancy_mean=8 + observed_PASS_mean=0.4; Trigger 2: divergence_mean=7.5]"`. Append `(audit-trail dispatches: <list dispatch_ids>)` at end.
- `next action: review last 3 stages of <PM> dispatches before next promotion attempt`
- `status: open`

### Rule 1 — Artifact existence check

Every `outcome=SUCCESS` claim must be backed by an `artifacts_touched` path. TeamLead Reads at least the **most-changed file** to confirm the work actually happened.

If `artifacts_touched` is empty AND `outcome=SUCCESS` (e.g., review-only dispatch) → check `verify_evidence` instead.

### Rule 2 — Verify command re-run (sampling)

TeamLead re-runs **`verify_evidence` commands per dispatch**, with sampling depth set by **`verify_policy` knob × per-PM `trust_tier`** (Phase 3 N1 modulates Phase 2 T4 knob).

**Effective sampling decision** (precedence: Rule 0 escalate > trust_tier `restricted` > trust_tier `trusted` > knob):

| Condition | Effective sampling | `sampling_applied` jsonl value |
|---|---|---|
| Rule 0 escalate (`divergence_score ≥ 10` per-dispatch) AND trust_tier `restricted` | `broad` | `tier_and_escalate_broad` |
| Rule 0 escalate (`divergence_score ≥ 10` per-dispatch), tier ≠ `restricted` | `broad` | `escalated_broad` |
| trust_tier `restricted`, current dispatch's `divergence_flag ≠ escalate` (i.e., `aligned` or `watch` per Rule 0 routing) | `broad` | `tier_forced_broad` |
| trust_tier `trusted`, knob ∈ `{default, broad}` | `minimal-per-dispatch` (PM has earned the relaxed sample) | `minimal-per-dispatch` |
| trust_tier `trusted`, knob = `minimal-per-dispatch` | `minimal-per-dispatch` (no further relaxation possible) | `minimal-per-dispatch` |
| trust_tier `standard` (default) | follow knob: `minimal-per-dispatch` \| `default` \| `broad` | matches knob value |

The `sampling_applied` field in `audit-trail.jsonl` (per `progress-md-schema.md` §Audit-trail sidecar) reflects the **effective** sampling used, NOT the knob value. This lets dogfood metrics distinguish "PM is tier-restricted" from "PM had a bad dispatch this time" from "knob is set permissively".

**Sampling rationale per effective tier**:

| Effective sampling | Per-dispatch behavior |
|---|---|
| `minimal-per-dispatch` | Highest-risk claim ONLY (lowest-confidence dropped — weakens Rule 2; only earned via trust_tier=trusted OR explicit CEO_Gate_0 consent on knob) |
| `default` (baseline) | Highest-risk + lowest-confidence claims (per Round 2 Arch MED-10 — original Rule 2 behavior) |
| `broad` | All `verify_evidence` entries re-run |

Sampling rationale (when `default`):

- **Highest-risk claim** — pick the verify_evidence entry whose failure would have biggest impact
- **Lowest-confidence claim** (per Round 2 Arch MED-10) — pick the one TeamLead is least sure about based on raw evidence
- Log BOTH selections in `## Self-Audit` so CEO can spot pattern of consistently low-risk-only sampling

NOT all commands when `default` — cost-bounded. The point is to catch sloppy returns, not be a redundant re-runner. `broad` is the no-cost-bound mode for high-stakes work.

### Rule 3 — Sample diff inspection

For code changes, read at least one critical file's actual diff (not just PM's summary). Use `git diff` if in repo, else direct Read of the changed file.

### Rule 4 — RAID review

Read PM-reported `raid_updates`, judge severity independently. Do NOT paste-through. If PM marked an issue as `severity: low` but it looks `med` to you, override.

### Rule 5 — Distinguish trusted vs unverified

`## Last Action` line uses prefix:
- `[TRUSTED]` — TeamLead verified per rules 1-4
- `[CLAIMED]` — PM said but not yet verified (allowed mid-stage; **MUST be `[TRUSTED]` before Stage close**)

## Mandatory rejection criteria (per §3.2)

PM return missing ANY required field → TeamLead returns INCOMPLETE without accepting (matches `dispatch-header.md` §Return contract — that file is canonical):

- `outcome`
- `value_hypothesis`
- `value_realized`
- `dod_status`
- `dod_evidence`
- `artifacts_touched` (may be empty array)
- `verify_evidence` (may be empty array if read-only)
- `raid_updates`
- `ccb_requests`
- `token_estimate_kT`
- `handoff`

Re-dispatch ONCE with schema reminder. Second incomplete → escalate CEO.

Same applies if return is **not** in fenced ` ```json ` block (parse fails per §7.0).

## Cross-PM verification (per §3.4)

To prevent TeamLead-as-single-point-of-failure:

| Cross-check | Performed by | Sampling |
|---|---|---|
| QA verifies one of RD's claimed test passes | QA PM in next dispatch after RD complete | ≥1 per stage, highest-risk component |
| PO confirms Gate_Requirement findings about spec gaps | PO PM after Gate_Requirement runs | All spec-gap findings |
| UX cross-checks RD's Mezzanine/styling claims | UX PM in post-build review | ≥1 per stage, highest-risk component |

If cross-PM verification fails (sibling PM disputes the original claim) → TeamLead reverts the original `[TRUSTED]` to `[CLAIMED]` + dispatches investigation.

## Self-Audit format (PROGRESS.md `## Self-Audit` section)

Canonical format lives in `progress-md-schema.md` §`## Self-Audit` (Phase 2 RSS short form + legacy verbose form + migration note). This file no longer duplicates the format to avoid drift.

Per-dispatch structured records → `<project>/docs/audit-trail.jsonl` (per `progress-md-schema.md` §Audit-trail sidecar). PROGRESS.md `## Self-Audit` is now the **per-stage human-readable summary** only.

CEO_Gate_N AskUserQuestion includes a one-line summary: "I verified <X>/<Y> PM claims this stage. Divergence distribution: aligned <a>, watch <w>, escalate <e>." This converts CEO from rubber-stamper to spot-checker (per Round 2 PMP MED-4) and surfaces divergence patterns CEO would otherwise miss.

## When CEO sees something concerning

CEO's recourse at any gate:
- `revise_next` — if next-stage plan looks off
- `revise_charter` — if overall direction needs CCB-Heavy
- `pause` — to investigate manually before proceeding
- `abort` — terminate

## Failure modes (TeamLead must recognize and reject)

- **PM returns prose-only** (no fenced JSON) → INCOMPLETE
- **PM returns `outcome=SUCCESS` with empty verify_evidence** for non-read-only work → INCOMPLETE
- **PM returns "test passed"** without command + key output → INCOMPLETE
- **PM marks own RAID-I as severity:low** when impact looks higher → TeamLead overrides
- **TeamLead chooses easy verify command repeatedly** (avoiding hard ones) → CEO can spot in `## Self-Audit` rotation log; should adjust

## Why this discipline matters

User's prior incident pattern (referenced in design doc §3 motivation):
- Without anti-rubber-stamp, TeamLead silently nods at PM's "test passed" claims
- Bugs slip through stages
- Lessons-learned can't compound (no record of what was actually verified vs claimed)
- CEO loses trust in TeamLead → defeats the orchestrator's purpose
