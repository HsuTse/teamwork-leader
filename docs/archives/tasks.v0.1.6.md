# tasks.md — v0.1.6 PlanAudit Anti-Self-Skip (Rule 7)

> Owner: RD PM (TeamLead plan-injected initial decomposition; RD owns from T-1-1 onward).
> Stage: 1 (single-stage charter)
> Branch: `feat/v0.1.6-plan-audit-rule-7`

## Stage 1 task list

### T-1-1 — Add Rule 7 to anti-rubber-stamp.md

- **File**: `references/anti-rubber-stamp.md`
- **Change**: Add new `## Rule 7 — Plan-audit anti-self-skip (Phase 4 candidate)` section after existing Rule 6 (or end of Rules section if no Rule 6). Cover the 4 enforcements with subsections per enforcement. Cross-ref to `references/plan-audit-rubric.md` for verbatim dispatch prompt + structured-field validation procedure. Cross-ref to `references/stage-runbook.md` §PLAN_AUDIT for runtime hookup.
- **expected_cost_kT**: 12
- **expected_scope_files**: `["references/anti-rubber-stamp.md"]`
- **expected_raid_delta**: 0
- **verify**: `grep -n "Rule 7" references/anti-rubber-stamp.md` returns ≥3 lines (heading + 4 enforcement sub-headings); `grep -c "plan-audit-rubric.md" references/anti-rubber-stamp.md` ≥ 1

### T-1-2 — NEW file plan-audit-rubric.md

- **File**: `references/plan-audit-rubric.md` (NEW)
- **Change**: Create standalone Rule 7 rubric. Sections: §Scope (TeamLead-dispatched Opus reviewer, NOT host `/opus-review final`); §Dispatch prompt blacklist (verbatim phrase list); §Structured-field validation (`suggested_fix` cannot equal `"skip"` / `"none"` / `"no change"`); §Verdict aggregation (all logged issues surface CEO regardless of severity); §Post-receive guard (1-retry → still detect → escalate); §Cross-references. ~80 lines.
- **expected_cost_kT**: 10
- **expected_scope_files**: `["references/plan-audit-rubric.md"]`
- **expected_raid_delta**: 0
- **verify**: `wc -l references/plan-audit-rubric.md` ≥ 60; `grep -c "Scope" references/plan-audit-rubric.md` ≥ 1

### T-1-3 — Rewrite stage-runbook.md §PLAN_AUDIT

- **File**: `references/stage-runbook.md`
- **Change**: Major rewrite of §PLAN_AUDIT section. Replace existing step 3 (single-plan / candidate-set Opus dispatch) with new step embedding Rule 7 dispatch prompt blacklist (cross-ref `plan-audit-rubric.md`). Add new step 3.5 (post-receive Rule 7 validation: parse `suggested_fix` fields, detect literal "skip"/"none"/"no change" values, on detection re-dispatch ONCE with corrective prompt). Document escalation path: persistent detection after 1 retry → ESCALATED with `## Exception` populated `Type: plan_audit_self_skip_persistent`. Step 4 (verdict routing) updated to filter out issues with non-actionable `suggested_fix`. ~50 lines net change.
- **expected_cost_kT**: 10
- **expected_scope_files**: `["references/stage-runbook.md"]`
- **expected_raid_delta**: 0
- **verify**: `grep -n "Rule 7" references/stage-runbook.md` returns ≥1 line; `grep -c "plan-audit-rubric.md" references/stage-runbook.md` ≥ 1; `grep -c "plan_audit_self_skip" references/stage-runbook.md` ≥ 1

### T-1-4 — progress-md-schema.md add field

- **File**: `references/progress-md-schema.md` §Audit-trail sidecar
- **Change**: Add `plan_audit_self_skip_detected: boolean | null` field to the `audit-trail.jsonl` schema list. Semantics:
  - `true` — Rule 7 fired this PLAN_AUDIT session (detected non-actionable `suggested_fix` in reviewer output)
  - `false` — Rule 7 ran but no detection (clean pass)
  - `null` — Rule 7 did not run (single-plan mode where no `suggested_fix` field emitted, OR `plan_audit_anti_self_skip_mode == off`)
  Field follows `kmr_*` pattern. ~10 lines.
- **expected_cost_kT**: 5
- **expected_scope_files**: `["references/progress-md-schema.md"]`
- **expected_raid_delta**: 0
- **verify**: `grep -n "plan_audit_self_skip_detected" references/progress-md-schema.md` returns ≥2 lines (field declaration + semantics)

### T-1-5 — three-gates.md cross-ref

- **File**: `references/three-gates.md`
- **Change**: Add cross-ref note in §JSON parse failure section: "PLAN_AUDIT phase has additional Rule 7 anti-self-skip protection per `references/plan-audit-rubric.md`; consult that file for plan-audit-specific reviewer dispatch protocol." ~5 lines.
- **expected_cost_kT**: 3
- **expected_scope_files**: `["references/three-gates.md"]`
- **expected_raid_delta**: 0
- **verify**: `grep -c "plan-audit-rubric.md" references/three-gates.md` ≥ 1

### T-1-6 — reuse-map.md PlanAudit clarification

- **File**: `references/reuse-map.md`
- **Change**: Update PlanAudit row (or add row if missing): explicit clarification "via Agent tool with `model: opus`, NOT via host `/opus-review final` skill (preserves v0.1.4 self-contained portability ethos; Rule 7 enforcement requires plugin-controlled dispatch)". ~5 lines.
- **expected_cost_kT**: 3
- **expected_scope_files**: `["references/reuse-map.md"]`
- **expected_raid_delta**: 0
- **verify**: `grep -c "Agent tool" references/reuse-map.md` ≥ 1; `grep -c "NOT.*opus-review final" references/reuse-map.md` ≥ 1

### T-1-7 — budget-proposal.md.tpl new knob

- **File**: `templates/budget-proposal.md.tpl` §Knobs
- **Change**: Add `plan_audit_anti_self_skip_mode` knob row in Budget knobs table:
  - `strict` (default) — Full Rule 7 enforcement: structured-field validation + 1-retry + escalate on persistence
  - `warn` — Validate + log `plan_audit_self_skip_detected: true` in audit-trail but DO NOT re-dispatch / escalate (preserves dispatch flow)
  - `off` — Skip Rule 7 entirely; field logged as `null`
  Both `warn` and `off` require CCB-Heavy to set (rollback of deployed enforcement mechanism). ~8 lines.
- **expected_cost_kT**: 5
- **expected_scope_files**: `["templates/budget-proposal.md.tpl"]`
- **expected_raid_delta**: 0
- **verify**: `grep -n "plan_audit_anti_self_skip_mode" templates/budget-proposal.md.tpl` returns ≥1 line; `grep -c "CCB-Heavy" templates/budget-proposal.md.tpl` ≥ 4 (existing 3 + 1 new)

### T-1-8 — plugin.json version bump

- **File**: `.claude-plugin/plugin.json`
- **Change**: `"version": "0.1.5"` → `"version": "0.1.6"`. Single-line change.
- **expected_cost_kT**: 1
- **expected_scope_files**: `[".claude-plugin/plugin.json"]`
- **expected_raid_delta**: 0
- **verify**: `jq -r '.version' .claude-plugin/plugin.json` returns `0.1.6`

### T-1-9 — CHANGELOG.md v0.1.6 entry

- **File**: `CHANGELOG.md`
- **Change**: New `## [0.1.6] — 2026-05-03` entry above existing `## [0.1.5]` section. Sub-sections:
  - **Added** — New Rule 7 in `references/anti-rubber-stamp.md`; new `references/plan-audit-rubric.md`; new `plan_audit_self_skip_detected` field in audit-trail.jsonl; new `plan_audit_anti_self_skip_mode` knob in budget-proposal.md.tpl
  - **Changed** — `references/stage-runbook.md` §PLAN_AUDIT rewritten with Rule 7 hookup (dispatch prompt blacklist + post-receive validation + escalation path); `references/three-gates.md` cross-ref; `references/reuse-map.md` PlanAudit clarification (Agent tool not host skill)
  - **Why** — Post-v0.1.5 design observation that Rule 0 / 0.5 / 2 protect EXECUTING-phase PM dispatches but PLAN_AUDIT-phase Opus reviewers had no dedicated self-skip guard. Reviewers can flag a real issue, then suggest "skip" / "none" / "no change" as fix, effectively rubber-stamping. Rule 7 closes this gap with structured-field validation (not prose regex which has false-positive risk).
  - **Migration** — Legacy PLAN_AUDIT runs without Rule 7 unaffected (logged as `plan_audit_self_skip_detected: null`). Post-v0.1.6 mandatory enforcement unless `plan_audit_anti_self_skip_mode == warn | off` (both CCB-Heavy).
  ~40 lines.
- **expected_cost_kT**: 5
- **expected_scope_files**: `["CHANGELOG.md"]`
- **expected_raid_delta**: 0
- **verify**: `grep -c "## \[0.1.6\]" CHANGELOG.md` = 1; `grep -c "Rule 7" CHANGELOG.md` ≥ 2

### T-1-10 — README.md version + section

- **File**: `README.md`
- **Change**: Two edits:
  1. Update version badge `0.1.5` → `0.1.6` in §Quick Start (or wherever the badge is)
  2. Add new §Anti-self-skip section after §三道驗證閘 (or §Three-gate verification): cover Rule 7 scope (TeamLead-dispatched Opus, NOT host skill), when it fires (PLAN_AUDIT only), 4 enforcements summary, knob configuration. Cross-ref `references/plan-audit-rubric.md` and `references/anti-rubber-stamp.md` Rule 7.
  ~25 lines net change.
- **expected_cost_kT**: 5
- **expected_scope_files**: `["README.md"]`
- **expected_raid_delta**: 0
- **verify**: `grep -c "0.1.6" README.md` ≥ 1; `grep -c "Anti-self-skip\|anti-self-skip" README.md` ≥ 1

---

## Cross-PM verification scheduling (run before EXITING EXECUTING)

- **QA**: re-run T-1-3's verify command (`grep` checks for stage-runbook §PLAN_AUDIT changes) and T-1-9's CHANGELOG verify; classify per `three-gates.md` schema.
- **PO**: confirm terminology consistency (`Rule 7` / `plan_audit_self_skip_detected` / `plan_audit_anti_self_skip_mode` / `plan-audit-rubric.md`) — flag if any naming drift between files.
- **UX**: SKIPPED (no UI / Mezzanine claims this stage).

## Stage 1 GATING

- **Gate_Forward**: QA dispatches Sonnet to verify doc consistency (cross-references resolve, schema fields align with usage). Skipped if Auto Mode disables Sonnet cadence (still classify via QA's own Read+Grep).
- **Gate_Human**: SKIPPED (no UI changes).
- **Gate_Requirement** (final stage = mid-stage of single-stage charter): TeamLead dispatches plugin-internal 3-parallel Opus review:
  - Reviewer A — Correctness: does the implementation match the 4-enforcement design?
  - Reviewer B — Doc-sync: are CHANGELOG / README / cross-refs internally consistent?
  - Reviewer C — Self-referential dogfood: does the implementation pass its own Rule 7 (no `suggested_fix: "skip"` etc.)?
  - All 3 must return APPROVED or APPROVED_WITH_REVISIONS (in-place fix) for ship.
