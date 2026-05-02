# Stage Execution Runbook — TeamLead's per-state procedural handbook

> **Source of truth**: design doc v3 §5 (state machine), §6 (PM specs), §7 (gates), §10 (iteration).
> This file is the **operational glue** that connects the rules in other reference docs into a sequenced runbook for TeamLead's runtime execution.

**When to load**: at every `/teamwork-leader` invocation (per `commands/teamwork-leader.md` Step 0).

**How to use**: when entering a state, find the §<STATE> section below and execute the numbered steps in order. Do NOT improvise.

---

## State machine (canonical)

```
                CEO_Gate_0 approve
                       │
                       ▼
                  PLANNING ◄─────────────┐
                       │                 │
                       ▼                 │
                  PLAN_AUDIT             │
                  │       │              │
        APPROVED  │       │  REJECTED    │ (CEO revise_next on prior gate)
                  ▼       └──► AWAITING_CEO
                  EXECUTING                │
                       │                   │
                       ▼                   │
                    GATING                 │
                  │       │                │
        all PASS  │       │  any FAIL/INC. │
                  ▼       └──► ESCALATED ──┘  (CEO decides; revise → PLANNING)
                  REPORTING                │
                       │                   │
                       ▼                   │
                  AWAITING_CEO ◄───────────┘
                       │
              (CEO_Gate_N verb)
                       │
            ┌──────────┼──────────┐
            ▼          ▼          ▼
       approve    revise_*    abort/pause
            │          │          │
       (last       (loop      ABORTED
       stage?)     back)
        │   │
        N   Y
        │   │
        ▼   ▼
    PLANNING ProjectClose protocol
              │
              ▼
        CEO_Gate_Final
              │
              ▼
        COMPLETED
```

---

## §PLANNING

**Enter when**: CEO_Gate_(N-1) approve OR CEO `revise_next` on prior gate (loop back).

**Steps**:

1. **Pre-write stale guard** (per §11.3): snapshot `mtime+sha256` of PROGRESS.md.
2. Run §Stale-guard 4-step (below) → if mismatch, halt + surface to CEO.
3. Set `## State: PLANNING` and overwrite `## Last Action: <ISO-8601> [TRUSTED] — Entered PLANNING for Stage <N>`.
4. **Run §Size guard** (below): `wc -l PROGRESS.md`. If >1900, schedule archival at next stage close. If >2000, halt and surface to CEO.
5. **Determine PM dispatch list** for this stage based on TeamFormation + stage scope (per `templates/budget-proposal.md.tpl` PM activation table).
6. **Build per-PM dispatch payload** by substituting placeholders in `dispatch-header.md` template:
   - `{TEAMLEAD_INJECTS_PROGRESS_EXCERPT}` ← current Charter + Budget Baseline + active RAID + current Stage scope (NOT full PROGRESS.md per §11.6 default-excerpt rule)
   - `{TEAMLEAD_INJECTS_VALUE_HYPOTHESIS}` ← per-dispatch hypothesis, must satisfy `value-driven.md` acceptance criteria
   - `{TEAMLEAD_INJECTS_DOD}` ← observable DoD criteria
   - `{TEAMLEAD_INJECTS_TASK_RANGE}` ← e.g., "T-2-1 through T-2-3"
7. **Parallel dispatch** via Task tool (max `parallel_pm_limit` per design doc §9.1, default 2):
   - PO PM (`subagent_type: po-pm`) for spec drafting/review
   - RD PM (`subagent_type: rd-pm`) for plan drafting + task decomposition
   - (Other PMs as activated)
8. Wait for all returns.

**Exit to**: PLAN_AUDIT once all PMs return.

**Error / timeout handling**:
- A PM returns prose (no fenced JSON) → see §JSON parse failure (below)
- A PM returns INCOMPLETE (parse OK but missing mandatory fields) → schema-validation re-dispatch per §EXECUTING step 5 (v0.1.3); separate retry pool from step-review (does NOT consume step 7 retry slot); second INCOMPLETE → `schema_validation_status: rejected_and_escalated` + ESCALATED
- Token estimate from any PM exceeds 80% per-stage threshold → warn CEO at next gate per `budget-proposal.md.tpl`

---

## §PLAN_AUDIT

**Enter when**: PLANNING state collected all PM plans.

**Steps**:

1. Set `## State: PLAN_AUDIT`.
2. **Run §Stale-guard** before write.
3. **Dispatch single Opus reviewer** (per `auto-review-cadence.md §Planning Cadence`):
   - `subagent_type: general-purpose`, `model: opus`
   - Embed all PM plans + Charter + Budget Baseline as context

   **Mode branches by `plan_candidates` presence** (Phase 2 T5 — see `dispatch-header.md` §`plan_candidates` block):

   - **Single-plan mode** (no PM emitted `plan_candidates`, OR K=1 fall-through per `dispatch-header.md` §`plan_candidates` block degenerate cases):
     - Use the Opus rubric from `auto-review-cadence.md §Planning Cadence` verbatim
     - Output schema: `verdict: APPROVED | APPROVED_WITH_REVISIONS | REJECTED` + issues list
     - For K=1 fall-through: treat the singleton candidate's `summary` + `dod` + `cost_estimate_kT` as the single plan; ignore the `plan_candidates` array wrapper

   - **Candidate-set mode** (RD PM emitted `plan_candidates: [A, B, C]`, max K=3):
     - Opus runs the 6-criterion rubric **per candidate** independently (each candidate gets its own verdict + issues list)
     - Then Opus computes `selector_score` per candidate:
       ```
       selector_score = (blocker × 4 + important × 2 + minor × 1)
                      + 0.5 × cost_estimate_kT
                      − 1 × novelty_bonus    (1 if risk_class != "none", else 0)
       ```
       Lower score ranks higher. **Coefficients are seed values for Phase 2 dogfood — calibrate empirically per `references/anti-rubber-stamp.md` §Threshold rationale; CEO can adjust via CCB-Light at later gates.**
       The `novelty_bonus` is a **coarse heuristic** — any non-`none` risk_class earns it (env/spec/impl/verifier all treated equally). Fine-grained differentiation between risk types is left to the Opus 6-criterion rubric in step 3 (which gives blocker/important/minor severity per finding); novelty_bonus only flags "candidate surfaces SOME tradeoff" vs "candidate claims no risk".
     - Output schema:
       ```json
       {
         "verdict": "APPROVED | APPROVED_WITH_REVISIONS | REJECTED",
         "selected_id": "A | B | C | null",
         "per_candidate": [
           {"id": "A", "verdict": "APPROVED", "issues": [], "selector_score": 5.2},
           {"id": "B", "verdict": "APPROVED_WITH_REVISIONS", "issues": [...], "selector_score": 8.5},
           {"id": "C", "verdict": "REJECTED", "issues": [...], "selector_score": 12.0}
         ],
         "summary": "<rationale for selected_id>"
       }
       ```
     - `selected_id: null` if all candidates REJECTED (treated as overall REJECTED).

4. **On verdict**:
   - **Single-plan mode**:
     - `APPROVED` → proceed to EXECUTING
     - `APPROVED_WITH_REVISIONS` → run §Stale-guard → apply revisions inline to PM plans → proceed to EXECUTING
     - `REJECTED` → re-dispatch PMs ONCE with feedback (max 1 retry per cadence rule); second REJECTED → ESCALATED
   - **Candidate-set mode** (additional handling):
     - `APPROVED` → promote `selected_id`'s plan to active; **archive unselected candidates** to `## RAID Register` as `[A]` (assumption) entries per canonical RAID-A schema (per `references/progress-md-schema.md` §RAID Register): `assumption: "<id> backup plan: <summary>"` | `validates if: "selected plan <selected_id> fails mid-stage and rollback to this candidate is needed"` | `validation_status: pending` | `validated_at: <empty until triggered>`. Proceed to EXECUTING.
     - `APPROVED_WITH_REVISIONS` → run §Stale-guard → apply revisions to `selected_id`'s plan only; archive unselected as RAID-A as above; proceed to EXECUTING.
     - `REJECTED` (selected_id == null OR all candidates REJECTED) → re-dispatch RD PM ONCE with per-candidate feedback (max 1 retry per cadence rule); second REJECTED → ESCALATED.
5. **Run §Anti-rubber-stamp 5-rule checklist** on Opus's claims (yes — even Opus can hallucinate). In candidate-set mode, sample at least 1 of the per-candidate verdicts for verification (don't just trust the aggregate `selected_id`).

**Exit to**: EXECUTING (on APPROVED) | ESCALATED (on retry-exhausted REJECTED).

---

## §EXECUTING

**Enter when**: PLAN_AUDIT APPROVED (with or without revisions).

This state implements the **subagent-driven-development PATTERN** (per `reuse-map.md` — do NOT load the skill itself, replicate inline here).

**Steps** (per-task loop, runs once per task in plan):

1. Set `## State: EXECUTING`.
2. **Run §Stale-guard** before any PROGRESS.md write.
3. **Pick next pending task** from RD PM's plan (T-N-1 → T-N-2 → ...).
3a. **Write pre-task estimate** (Phase 3 T11 — KMR input). Append one line to `<project>/docs/pre-task-estimates.jsonl` per `references/progress-md-schema.md` §Pre-task estimates sidecar:
    - **Mint `dispatch_id` here, pre-dispatch** (format `S<stage>-D<seq>`, monotonic within stage). This supersedes the Phase 2 post-dispatch minting pattern in `dispatch-header.md` §After you return — Phase 3 KMR requires pre-dispatch minting so the pre-task and post-dispatch records can be joined. The SAME `dispatch_id` is used by the post-dispatch audit-trail.jsonl record.
    - Source `expected_cost_kT` from RD PM's selected `plan_candidate` entry (Phase 2 T5) at PLAN_AUDIT close, OR from RD's tasks.md entry for this task in single-plan mode. TeamLead does NOT independently re-estimate.
    - Source `expected_scope_files` from RD's plan declaration for this task
    - Source `expected_raid_delta` from RD's risk annotations (default 0 for routine tasks)
    - If no pre-task estimate available (single-plan mode without explicit task verify cost annotation) → write the line with `expected_cost_kT: null`; KMR proxy skips the `budget_surprise` term for this dispatch.
4. **Dispatch RD PM** (or relevant PM per task type):
   - Task: implement T-N-X
   - Inputs: dispatch-header.md substituted + task-specific scope
   - Allowed tools: per `dispatch-header.md` allow-list for that PM
5. **On RD return**:
   - Extract JSON via `/```json\s*\n([\s\S]+?)\n```/` regex (multiline-safe). Strip leading prose if any. If parse fails → §JSON parse failure.
   - **Schema validation (v0.1.3)** — Validate all 11 required fields per `anti-rubber-stamp.md` §Mandatory rejection criteria (canonical list: `outcome`, `value_hypothesis`, `value_realized`, `dod_status`, `dod_evidence`, `artifacts_touched`, `verify_evidence`, `raid_updates`, `ccb_requests`, `token_estimate_kT`, `handoff`).
     - **First attempt PASS** → record `schema_validation_status: pass` in audit-trail.jsonl (written at step 7a). Continue to anti-rubber-stamp checklist below.
     - **First attempt INCOMPLETE** (any of the 11 fields missing or malformed) → re-dispatch ONCE with prompt `"Your prior return missed required fields: <list>. Required schema per dispatch-header.md §Return contract. Re-emit complete return."` This re-dispatch **does NOT** consume step 7's step-review retry slot — schema validation has its own 1-retry pool (per `references/progress-md-schema.md` §`schema_validation_status` field §Retry budget invariant).
       - **Second attempt PASS** → record `schema_validation_status: rejected_and_retried`. Continue to anti-rubber-stamp checklist.
       - **Second attempt INCOMPLETE** → record `schema_validation_status: rejected_and_escalated`; transition to §ESCALATED with `## Exception` populated: `Type: schema_validation_exhausted`, `Detail: PM <role> failed schema validation twice; missing fields second attempt: <list>`. **KMR observability**: this short-circuits step 7 + step 7a entirely (no PM-content to score). Record `kmr_proxy: null`, `kmr_fired: null`, `kmr_verdict: null`, `kmr_root_cause: null`. Phase 3/4 calibration queries computing KMR-vs-step-review agreement rate MUST filter `schema_validation_status != 'rejected_and_escalated'` to avoid skewing the denominator.
     - **`schema_enforcement_mode == warn` knob** (per `templates/budget-proposal.md.tpl`) → run validation, compute outcome (`pass` / `rejected_and_retried`-equivalent / `rejected_and_escalated`-equivalent), record `schema_validation_status` accordingly, but **DO NOT reject** the dispatch — accept the original PM return as-is and proceed to anti-rubber-stamp checklist regardless of validation outcome. Preserves v0.1.2 silent-acceptance semantics for project-specific operational reasons. Activation requires CCB-Heavy.
     - **`schema_enforcement_mode == off` knob** (per `templates/budget-proposal.md.tpl`) → skip validation entirely; record `schema_validation_status: null`; proceed to anti-rubber-stamp directly. This kill-switch is CCB-Heavy because it disables a deployed enforcement mechanism.
   - **Run §Anti-rubber-stamp 5-rule checklist** (below) on this return.
   - Serialize raid_updates / ccb_requests into PROGRESS.md (after stale guard).
   - Update Last Action with `[TRUSTED]` if all 5 anti-rubber-stamp rules passed; else `[CLAIMED]`.
6. **Dispatch Sonnet step-reviewer** (per `auto-review-cadence.md §Coding Cadence`):
   - `subagent_type: general-purpose`, `model: sonnet`
   - Inputs: task scope, RD's diff, surgical-change rubric from `references/discipline/surgical-change.md`
   - Output: `verdict: PASS | PASS_WITH_MINOR | FAIL`
7. **On step-reviewer verdict**:
   - `PASS` → mark task complete in tasks.md (RD writes), continue loop
   - `PASS_WITH_MINOR` → record follow-up, continue loop
   - `FAIL` → 1 retry: re-dispatch RD with fix instructions; second FAIL → ESCALATED
7a. **KMR per-task divergence proxy** (Phase 3 T10 — content-conditioned mini gate firing). After step 7's routing decision, compute the per-task divergence proxy using normalized inputs (each term ∈ [0, 9]):

    ```
    per_task_divergence_proxy = max(
      budget_surprise,
      scope_surprise,
      ambient_instability,
      step_review_signal
    )
    ```

    where:
    - `budget_surprise = min(9, max(0, round((actual_token_estimate_kT / expected_cost_kT − 1) × 10)))` — ratio of PM-reported `meta.token_estimate_kT` to TeamLead's `expected_cost_kT` from `<project>/docs/pre-task-estimates.jsonl`. **Skip term (treat as 0)** if `expected_cost_kT == null` (single-plan mode without explicit cost).
    - `scope_surprise = min(9, count of paths in artifacts_touched NOT in expected_scope_files)` — out-of-expectation file touches.
    - `ambient_instability = min(9, count of new RAID entries created by this PM during this task)` — read from PM return's `raid_updates` array filtered to NEW (status: open) entries.
    - `step_review_signal = 9 if step-review verdict == FAIL else 0` — binary direct signal from step 7. PASS_WITH_MINOR is not a failure (per design); use 0.

    **Decision**:

    - **If step-review verdict was FAIL** (step 7 already dispatched and resolved the 1-retry auto-fix synchronously): Mini Gate STILL fires for audit/calibration evidence (Phase 3 dogfood requires uniform `kmr_*` observability across PASS/FAIL paths to compute Mini-Gate-vs-step-review agreement rate); routing differs from PASS path. **Sequencing**: step 7a runs BEFORE the §ESCALATED state transition (which step 7's "second FAIL → ESCALATED" might otherwise trigger), while still inside the EXECUTING per-task iteration — the step 7a outcomes determine whether Mini Gate evidence joins the ESCALATED `## Exception` Detail or is logged as RAID-I, so step 7a MUST complete before any state transition out of EXECUTING. Run Mini Gate per `references/three-gates.md` §Mini Gate_Forward; log `kmr_*` fields per `references/progress-md-schema.md` §Audit-trail sidecar. Mini Gate's verdict does **NOT** trigger re-dispatch (retry slot already consumed by step 7). On Mini Gate verdict:
      - `PASS` → log `kmr_verdict: PASS` (Mini Gate concurs with retry outcome); continue to step 8.
      - `PARTIAL` / `FAIL` → log `kmr_verdict` + `kmr_root_cause`. Two sub-paths:
        - **If step 7's retry also FAILed** (task heading to ESCALATED) → Mini Gate's evidence is appended to the `## Exception` Detail field at ESCALATED entry (provides second diagnostic surface for CEO arbitration).
        - **If step 7's retry PASSed** (task complete despite original step-review FAIL) → Mini Gate's PARTIAL/FAIL becomes a RAID-`[I]` entry with `severity: med` (default) or `severity: high` (if Mini Gate `non_functional_findings` includes any `severity: high` item), `next action: review Mini Gate findings before stage close`, `status: open`. CEO sees this in the next gate's RAID review.
      - `INCONCLUSIVE` → log `kmr_verdict: INCONCLUSIVE`; do **NOT** escalate CEO from this path (the FAIL path is already escalating or completing; double-escalation creates noise).

    - **Else** (step-review was PASS or PASS_WITH_MINOR), if `per_task_divergence_proxy >= 4` → fire Mini Gate_Forward per `references/three-gates.md` §Mini Gate_Forward. Pass the task's `artifacts_touched` as scope. On Mini Gate verdict:
      - `PASS` → continue to step 8.
      - `PARTIAL` / `FAIL` → loop back to step 7's auto-fix path (re-dispatch original PM with Mini Gate's evidence as failure rationale). 1 retry per cadence rule; second FAIL → ESCALATED. **This is the only path where step 7's retry slot is consumed BY KMR.**
      - `INCONCLUSIVE` → escalate CEO per `references/three-gates.md` §JSON parse failure pattern.

    - `per_task_divergence_proxy < 4` → continue to step 8 normally.

    **Append to audit-trail.jsonl** for this dispatch: write structured top-level fields per `references/progress-md-schema.md` §Audit-trail sidecar — `kmr_proxy: <float>`, `kmr_fired: <bool>`, `kmr_verdict: <enum|null>`, `kmr_root_cause: <enum|null>`, **`schema_validation_status: <enum|null>` (v0.1.3 — outcome of step 5 schema validation: `pass` / `rejected_and_retried` / `rejected_and_escalated` / `null` per kill-switch)**. Do NOT pipe-delimit structured data into the `notes` field (would defeat `jq` queries).

    **Worked examples**:
    - **Aligned (no mini-gate)**: PM reports 14 kT vs expected 12 → ratio 1.17, budget_surprise = round(1.7) = 2. Touched only 2 expected files → scope_surprise = 0. 0 new RAID. Step-review PASS. proxy = max(2, 0, 0, 0) = **2** < 4 → no mini-gate.
    - **Budget overrun fires**: PM reports 22 kT vs expected 12 → ratio 1.83, budget_surprise = round(8.3) = 8. Others 0. proxy = **8** ≥ 4 → mini-gate fires.
    - **Scope creep fires**: PM touched 6 files but expected 2 → scope_surprise = 4. proxy = **4** ≥ 4 → mini-gate fires.
    - **Step-review FAIL always fires (evidence-only)**: step_review_signal = 9. proxy = **9** ≥ 4 → step 7's auto-fix retry runs first (synchronous, consuming the 1 retry slot); after retry returns, Mini Gate fires post-hoc for audit/calibration evidence. Mini Gate does NOT consume a second retry slot regardless of its verdict — its outcome routes to ESCALATED Exception detail (if retry FAILed) or RAID-I (if retry PASSed), per the FAIL-branch decision rules above.

    **Threshold rationale**: 4 is the seed value — any 50%+ budget overrun (ratio ≥1.5) fires (round(5) = 5 > 4); any 4+ scope-creep paths fires; any step-review FAIL always fires; modest signals on multiple dimensions don't auto-compound (we use `max`, not sum, to avoid noise). **Calibrate after Phase 3 dogfood**; threshold change per `references/pmp-ccb.md` §CCB-Light triggers (Rule 0 threshold ±2 = Light; beyond ±2 = Heavy).
8. **After ALL tasks done** (or stage scope satisfied per WBS): exit to GATING.

**Exit to**: GATING (when stage tasks complete) | ESCALATED (retry-exhausted FAIL).

**Cross-PM verification scheduling** (per anti-rubber-stamp §Cross-PM): **before exiting EXECUTING**, ensure for this stage:
- QA verified ≥1 of RD's claimed test passes (highest-risk component) → if not done, dispatch QA cross-check now
- UX verified ≥1 of RD's Mezzanine/styling claims → if UX activated and not done, dispatch UX cross-check now
- PO verified all spec-gap findings from any prior Gate_Requirement runs → if not done, dispatch PO cross-check now

If any cross-PM verification fails (sibling PM disputes original claim) → revert original `[TRUSTED]` to `[CLAIMED]` + dispatch investigation. **Investigation outcome must route to one of three explicit paths** (do NOT exit to GATING with unresolved dispute):

- **(a) Evidence missing only** (sibling could not reproduce due to env / data, no actual disagreement on substance) → log RAID-`[I]` entry with `severity: low` + `status: closed`; restore `[TRUSTED]`; continue to GATING.
- **(b) Implementation defect confirmed** (sibling found real bug in original PM's claim) → revert task to incomplete; re-dispatch original PM (RD or whoever) with corrected expectation; loop back to §EXECUTING step 4 (next iteration). Do NOT proceed to GATING until re-dispatched task PASSes step-review.
- **(c) Substantive disagreement that resists resolution** (PMs hold incompatible interpretations of spec / requirement) → transition to §ESCALATED with `## Exception` populated: `Type: cross_pm_dispute` (one of the values listed under `progress-md-schema.md` §Exception (active) → `Type:` field), `Stage: <N>`, `Detail: <one paragraph>`. CEO arbitrates at next AskUserQuestion.

---

## §GATING

**Enter when**: EXECUTING completed all stage tasks + cross-PM verifications scheduled.

**Steps** (run gates **sequentially**, no skipping per `three-gates.md` §Sequencing under failure):

1. Set `## State: GATING`.
2. **Gate_Forward**: dispatch QA PM with task "trace execution path; classify per three-gates.md schema"
   - On classifier `verdict: PASS` + `dod_status: met` → continue to Gate_Human
   - On any non-PASS → route per `root_cause` (code_bug → RD; spec_ambiguity → CCB-Light → PO; spec_gap → CCB-Heavy; environmental → DevOps Ad-hoc; inconclusive → ESCALATED)
   - Retry cap = 2 rounds per gate; exhausted → ESCALATED
3. **Gate_Human**: dispatch QA PM with task "exercise UI scenarios via playwright-cli or chrome-devtools-batch-scraper; classify"
   - Subjective items marked `[SUBJECTIVE]` → surface to CEO via AskUserQuestion ("Subjective verification needed: <item>. Pass or revise?")
   - Otherwise route as Gate_Forward
4. **Gate_Requirement** (final stage only by default; mid-stage opt-in per `gate_requirement_mode` knob):
   - TeamLead writes `/tmp/teamlead-gate-req-<ISO-8601>.json` manifest
   - Run `bash ~/.claude/plugins/teamwork-leader/scripts/gate-requirement-runner.sh <manifest-path>`
   - Capture stdout, extract classifier via §JSON parse (below)
   - Route per classifier
5. **All 3 gates PASS** → exit to REPORTING.

**Exit to**: REPORTING (all PASS) | ESCALATED (any retry-exhausted) | (route to fixing PM, then loop back to GATING).

**Anti-rubber-stamp on QA**: TeamLead independently re-runs ≥1 of QA's `verify_evidence` commands per stage (sampling: highest-risk + lowest-confidence; log both selections in `## Self-Audit`).

---

## §REPORTING

**Enter when**: GATING all 3 gates PASS.

**Steps**:

1. Set `## State: REPORTING`.
2. **Run §Stale-guard** before write.
3. Draft StageReport using `templates/stage-report.md.tpl`:
   - Aggregate PM dispatches summary
   - Roll up `## CCB Activity` entries (PO has already appended each row to `<project>/docs/decisions/ccb-log.md`)
   - Compute Value Realized vs Hypothesis table from `[V]` RAID entries
   - Tally tokens used vs baseline
   - Self-Audit aggregate for this stage
4. Draft WaveRefinement (per `pmp-wbs.md` §Rolling-wave): based on what was learned this stage, refine next stage's task-level decomposition. If refinement materially changes Charter scope → CCB-Heavy required (see §ESCALATED transition).
5. Append StageReport content to PROGRESS.md `## Stage History` under `### Stage <N> (closed YYYY-MM-DD)`.
6. **Run §Size guard**. If >1900 lines, archive oldest stage to `<project>/docs/stage-archives/stage-<oldest>.md` and replace with one-line back-reference.
7. **Run §Self-Audit aggregate** for this stage:
   - Count: I verified X of Y PM claims this stage
   - Log unverified items + reason
   - Log highest-risk and lowest-confidence claims selected
   - Log sampling rotation distribution (cross-PM verifications run)

**Exit to**: AWAITING_CEO.

---

## §AWAITING_CEO (CEO_Gate_N or any structured CEO interaction)

**Enter when**: REPORTING done OR mid-stage subjective Gate_Human surface OR error needing CEO direction.

**Steps**:

1. Set `## State: AWAITING_CEO`.
2. Run §Stale-guard before write.
3. Build AskUserQuestion with verbs (per design doc §5.2):
   - `approve` — close this stage, proceed
   - `revise_next` — adjust next-stage plan
   - `revise_charter` — material change → CCB-Heavy
   - `redirect` — point at different goal
   - `pause` — halt for investigation
   - `abort` — terminate
4. **MUST include** in question: "DoD met for this stage: yes / partial / no" (per `value-driven.md` §DoD enforcement at gate close).
5. **MUST include** Self-Audit summary line: "I verified <X>/<Y> PM claims this stage."
5a. **MUST include trust_tier change summary if any tier transitioned this stage** (Phase 3 N1, per `references/anti-rubber-stamp.md` Rule 0.5): one line in the format "trust_tier changes: <PM> <old>→<new> (<trigger>); <PM> <old>→<new> (<trigger>); ..." — empty line if no changes. If **all activated PMs** changed tier this stage (rare but possible during big calibration shifts), surface as an indented block rather than a single line to preserve CEO readability:
   ```
   trust_tier changes (this stage):
   - PO standard→trusted (rolling window clean)
   - RD trusted→standard (1 escalate fired)
   - QA standard→restricted (anti-gaming trigger §1)
   - UX trusted→standard (cross-PM dispute)
   ```
   CEO sees calibration drift here without having to read PROGRESS.md ## Self-Audit.
6. Wait for CEO response.
7. **DoD-gate enforcement** (per design doc §5.2 + `value-driven.md` §DoD enforcement at gate close):
   - If CEO returned `approve` AND DoD response ∈ {`partial`, `no`} → **HALT**: do NOT accept the `approve`. Force CCB-Light entry per `templates/ccb-light.md.tpl` documenting the DoD gap and CEO's rationale for accepting partial/no DoD. Only after the CCB-Light is `applied` (resolution logged) may CEO re-issue a verb at this gate.
   - This applies to ALL `approve` paths (whether next-stage or final-stage / ProjectClose).

**On CEO verb** (after step 7 enforcement passes):

| Verb | Action |
|---|---|
| `approve` (DoD=yes) | Run §ProjectClose detection (below). If last stage → ProjectClose. Else → PLANNING for Stage <N+1>. |
| `approve` (DoD=partial/no) | **Blocked at step 7** — force CCB-Light first; do not transition. |
| `revise_next` | Loop back to PLANNING with revised next-stage plan. |
| `revise_charter` | Trigger CCB-Heavy: TeamLead drafts using `templates/ccb-heavy.md.tpl`; transitions to ESCALATED. |
| `redirect` | Same as revise_charter (Charter-level change). |
| `pause` | Stay in AWAITING_CEO; preserve state; no further action until CEO returns. |
| `abort` | Set `## State: ABORTED`; log reason in `## Exception`; project terminated. |

**Free-text fallback**: per `commands/teamwork-leader.md` §Free-text verb fallback.

---

## §ProjectClose detection (HIGH-2 fix)

**When CEO `approve` at CEO_Gate_N**, before transitioning to next-stage PLANNING:

0. **Run §Stale-guard on PROGRESS.md** to refresh in-memory view of `## Budget Baseline` (a CCB-Heavy may have appended/removed stages since session start; cached values are unsafe). After Stale-guard passes, parse the latest `## Budget Baseline` stage decomposition.
1. Compare `current Stage_N` against the `final stage from Charter` (last entry in the just-refreshed Budget Baseline stage decomposition).
2. **If `current Stage_N == final stage`**:
   - Surface explicit AskUserQuestion: "Final stage approved. Begin ProjectClose protocol now? (yes / no — defer)"
   - On `yes` → enter ProjectClose state (run `templates/project-close.md.tpl` 7-step protocol per `pmp-lessons-learned.md`)
   - On `no` → stay in AWAITING_CEO; CEO can return later for ProjectClose
3. **If `current Stage_N < final stage`**:
   - Loop to PLANNING for Stage_<N+1>

This rule is **mandatory** — without it, ProjectClose / Lessons-learned / MemoryEntry never fire after the last stage approves. Step 0 is **mandatory** — never cache final-stage value across stages, since CCB-Heavy may have shifted it.

---

## §ESCALATED

**Enter when**:
- 2-round retry exhausted in any state (PLAN_AUDIT REJECTED, EXECUTING FAIL, GATING any non-PASS, INCOMPLETE return)
- CCB-Heavy `defer` verb chosen at extraordinary CEO_Gate
- Budget circuit breaker tripped (100% per-stage hard breach OR 2× cumulative)
- Classifier `verdict: INCONCLUSIVE`

**Steps**:

1. Set `## State: ESCALATED`.
2. Run §Stale-guard before write.
3. Populate `## Exception` section per `progress-md-schema.md` §Exception format.
4. Set Last Action `[TRUSTED] — ESCALATED: <reason summary>`.
5. Surface to CEO via AskUserQuestion immediately. Question structure depends on origin:
   - **Retry-exhausted** (state-machine cause): "<state> retry exhausted: <details>. Verbs: investigate / revise / pause / abort"
   - **Budget breach**: "Budget circuit breaker tripped at <X> kT. Verbs: extend_budget / halt / abort"
   - **CCB-Heavy defer pending re-decision**: dispatch CCB-Heavy 3-verb gate (`approve / reject / defer`), NOT CEO_Gate_N's 6-verb set — per `templates/ccb-heavy.md.tpl` §CEO decision (MED-7 fix).

**Exit**: only via CEO decision at the appropriate gate. Do NOT auto-proceed.

---

## §COMPLETED

**Enter when**: CEO_Gate_Final approve at end of ProjectClose protocol.

**Steps**:

1. Set `## State: COMPLETED`.
2. Final timestamp logged.
3. PROGRESS.md retained as immutable record.
4. No further dispatches.

**Exit**: terminal state.

---

## §ABORTED

**Enter when**: CEO `abort` verb at any AWAITING_CEO or ESCALATED.

**Steps**:

1. Set `## State: ABORTED`.
2. Log reason in `## Exception`.
3. PROGRESS.md retained as immutable record.

**Exit**: terminal state.

---

## §Anti-rubber-stamp 5-rule checklist (run on EVERY PM return)

This is the runtime checklist for `anti-rubber-stamp.md` §3.3. Run all 5 on every PM dispatch return before serializing into PROGRESS.md or marking Last Action `[TRUSTED]`:

```
[ ] Rule 1 — Artifact existence check:
    Read at least the most-changed file in `artifacts_touched`.
    If `outcome=SUCCESS` AND `artifacts_touched=[]` AND not read-only → INCOMPLETE.

[ ] Rule 2 — Verify command re-run (sampling):
    Re-run ≥1 command from `verify_evidence`.
    Pick the highest-risk command AND the lowest-confidence command (log both).

[ ] Rule 3 — Sample diff inspection:
    Read at least one critical file's actual diff (git diff or direct Read).

[ ] Rule 4 — RAID review:
    Read PM-reported `raid_updates`, judge severity independently.
    Override severity if PM under-classified (e.g., severity:low → med if impact warrants).

[ ] Rule 5 — Distinguish trusted vs unverified:
    Set Last Action prefix:
    - All 5 rules passed → [TRUSTED]
    - Any rule deferred to mid-stage → [CLAIMED] (must become [TRUSTED] before stage close)
```

**Self-Audit logging**: write to `## Self-Audit` ### Stage <N> entry per stage:

```
- I verified X of Y PM claims this stage.
- Unverified items (mid-stage only): [...]
- Highest-risk claim selected: "<claim>" by <PM>
- Lowest-confidence claim selected: "<claim>" by <PM>
- Sampling rotation: [QA→RD test claim "<X>"; PO→Gate_Requirement spec gap "<Y>"; UX→RD Mezzanine "<Z>"]
```

---

## §Stale-guard 4-step procedure (run before EVERY PROGRESS.md write)

Per `progress-md-schema.md` §Stale guard + design doc §11.3:

```
[ ] Step 1 — Snapshot:
    Capture mtime + sha256 of PROGRESS.md (and tasks.md if writing).
    Bash: stat -f "%m" PROGRESS.md && shasum -a 256 PROGRESS.md
    Linux: stat -c "%Y" PROGRESS.md && sha256sum PROGRESS.md

[ ] Step 2 — Compare immediately before write:
    Re-read mtime + sha256.

[ ] Step 3 — Bail on mismatch:
    If mtime or hash differs from snapshot → halt write.
    Surface diff to CEO: "PROGRESS.md changed since I last read it. Show diff and confirm before I overwrite?"

[ ] Step 4 — Backup:
    If snapshot matches, write `PROGRESS.md.bak.<ISO-8601>` before applying changes.
```

**Why this matters**: prevents TeamLead overwriting a PROGRESS.md that the CEO manually edited mid-flow.

---

## §Size guard procedure (run after EVERY PROGRESS.md write)

Per `progress-md-schema.md` §Size discipline + design doc §11.6:

```
[ ] Run: wc -l <project>/PROGRESS.md
[ ] If line count < 1900 → no action.
[ ] If 1900 ≤ line count < 2000 → schedule archival of oldest stage at next stage close.
    Note in `## Self-Audit` ### Stage <N>: "Size warning: PROGRESS.md at <X> lines; archive at next close."
[ ] If line count ≥ 2000 → halt + surface to CEO:
    "PROGRESS.md hit 2000-line ceiling. Archive oldest stage now? (yes / no — defer with risk acknowledgment)"
[ ] On archival approve:
    1. Create `<project>/docs/stage-archives/stage-<N>.md` with full Stage <N> StageReport content
    2. Replace Stage <N> block in PROGRESS.md with one-line: `<!-- archived to docs/stage-archives/stage-<N>.md -->`
    3. Verify line count drops below 1900
```

---

## §JSON parse failure procedure (run on every PM/gate return that should contain a fenced JSON block)

Per `three-gates.md` §JSON parse failure (per design doc §7.0):

```
[ ] Step 1 — Extract:
    Run regex: `/```json\s*\n([\s\S]+?)\n```/g` (multiline, lazy match, GLOBAL — find ALL matches, not first).
    If first preamble line breaks pattern, try fallback: split on /```json/ then split on /```/.
    Strip leading whitespace.

    **Multi-block rule**: PMs may emit multiple ```json blocks (e.g., schema example
    followed by actual return). The **last** ```json block in the response is
    authoritative — that is the PM's final verdict. Discard earlier blocks.
    This matches typical Claude output convention where examples precede answers.

[ ] Step 2 — Parse:
    json.loads / jq -e the extracted text.

[ ] Step 3 — On parse exception:
    Capture: raw output + parse error message + offending PM name + dispatch ID.

[ ] Step 4 — Re-dispatch ONCE:
    Send back to PM with prompt:
    "Your prior return failed JSON parse: <error>. Required schema: <schema>. Re-emit per `dispatch-header.md` §Return contract."

[ ] Step 5 — On second malformed:
    Escalate CEO with both raw outputs preserved verbatim.
    Set `## State: ESCALATED`. Populate `## Exception`.
```

**Strict rule**: NO prose fallback. NO best-effort interpretation. Either parse or escalate.

---

## §Schema validation worked examples (v0.1.3)

Per §EXECUTING step 5 schema validation. Worked examples for the three terminal `schema_validation_status` values:

**Example 1 — `pass` (first attempt PASS)**:
PM rd-pm dispatch S1-D3 returns valid fenced ` ```json ` with all 11 mandatory fields present. TeamLead step 5 validates → all fields present → continues to anti-rubber-stamp checklist. audit-trail.jsonl row records `schema_validation_status: pass`. Step 7 step-review retry pool untouched (1 slot still available for content-quality issues).

**Example 2 — `rejected_and_retried` (first INCOMPLETE → second PASS)**:
PM rd-pm dispatch S2-D5 first attempt returns prose only with `outcome` field, missing `verify_evidence` and `token_estimate_kT`. TeamLead step 5 validation → INCOMPLETE → re-dispatch with prompt naming the missing fields. PM second attempt returns complete 11-field JSON. TeamLead step 5 validation → PASS → continues. audit-trail.jsonl row records `schema_validation_status: rejected_and_retried`. **Step 7 step-review retry pool still has 1 slot** (schema retry pool was consumed, but they are separate pools).

**Example 3 — `rejected_and_escalated` (both INCOMPLETE)**:
PM ux-pm dispatch S3-D2 first attempt missing `dod_evidence` + `artifacts_touched`. TeamLead step 5 → re-dispatch. Second attempt still missing `dod_evidence` (PM persistently confused about schema). TeamLead step 5 → second INCOMPLETE → record `schema_validation_status: rejected_and_escalated`; transition to §ESCALATED with `## Exception` populated `Type: schema_validation_exhausted, Detail: PM ux-pm S3-D2 missing dod_evidence twice`. CEO arbitrates.

**Anti-anchoring note**: v0.1.3 ship target — `schema_validation_status` distribution should be ≥95% `pass` after PMs adapt. Any project showing >5% `rejected_and_retried` after Stage 2 indicates a PM-side schema-comprehension issue worth surfacing as RAID-I (not a tooling-side defect). `rejected_and_escalated` should be near-zero; non-zero is an immediate CCB-Light trigger.

---

## §Cross-PM verification scheduling (per anti-rubber-stamp §3.4)

To run BEFORE exiting EXECUTING:

```
[ ] QA cross-verification of RD test claims:
    Pick the highest-risk component changed this stage.
    Dispatch QA PM with task "re-execute RD's verify_evidence command for component X; classify per three-gates.md schema."
    Log result in `## Self-Audit` sampling rotation.

[ ] PO cross-verification of Gate_Requirement findings:
    If Gate_Requirement ran this stage AND found spec gaps, dispatch PO PM with each finding for confirmation.
    All findings (not sampled) — small list.

[ ] UX cross-verification of RD Mezzanine claims:
    Only if UX PM activated. Pick highest-risk UI component.
    Dispatch UX PM with task "verify RD's claim that <component> meets Mezzanine pattern X."
```

**On dispute**: revert original `[TRUSTED]` to `[CLAIMED]`. Dispatch investigation. Resolution may produce CCB-Light or RAID-I entry.

---

## Why this runbook exists

The 9 reference docs (`pmp-*.md`, `three-gates.md`, `anti-rubber-stamp.md`, `value-driven.md`, etc.) describe **what** the rules are. Without this runbook tying them into a sequenced procedure, TeamLead at runtime would have to improvise the order — and that's where projects fail.

This runbook makes operational behavior **mechanical, not improvisational**.
