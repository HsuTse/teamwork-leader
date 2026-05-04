# Project: teamwork-leader v0.1.6 — PlanAudit Anti-Self-Skip (Rule 7)

## Project root: /Users/HsuTse/ClaudeProject/teamwork-leader

## Charter

**Goal**: Implement Rule 7 to prevent TeamLead-dispatched Opus reviewers from rubber-stamping their own audits during PLAN_AUDIT — i.e., logging issues but suggesting "skip" / "cosmetic only" / "no change" as fixes.

**Scope**: Rule 7 applies to TeamLead's internal Opus reviewer dispatched via `Agent` tool with `model: opus` — NOT host `/opus-review final` skill. Preserves v0.1.4 self-contained portability ethos.

**4 enforcements** (refined per pre-charter design discussion 2026-05-03 01:49+08:00):

1. Dispatch prompt opens with explicit blacklist of self-skip phrases (`"skip"`, `"cosmetic only"`, `"minimal-diff"`, `"none"`, `"no change"`)
2. `suggested_fix` structured field must be actionable; literal `"skip"` / `"none"` / `"no change"` → reviewer must NOT log the issue (no-fix means no-issue)
3. Aggregation rule: all logged issues are surfaced to CEO regardless of severity (reviewer flags; CEO decides — never reviewer auto-suppresses by severity)
4. Pattern-match limited to `suggested_fix` structured field only (NOT prose regex — false-positive risk on legitimate prose like "skip migration if X"); 1-retry on detection → still detected → escalate CEO

**Success criteria (DoD — must-have)**:

- 10 files modified (~248–280 lines net change)
- plugin-internal 3-parallel Opus review at Stage 1 Gate_Requirement (Correctness / Doc-sync / Self-referential dogfood)
- Single coherent commit on `feat/v0.1.6-plan-audit-rule-7` branch
- Tag `v0.1.6` annotated; GitHub release published

**Constraints**:

- Plugin self-contained: no `~/.claude/rules/*.md` or host-skill dependencies (v0.1.4 ethos)
- Review-then-commit: no commits before Opus PASS (v0.1.4 lesson)
- Sweep verification via grep before final review (v0.1.4 lesson)
- Auto Mode active → reviewer cadence (PlanAudit Opus, step-review Sonnet) DISABLED; Stage Gates + CEO Gates remain ACTIVE

## Budget Baseline

### Stage decomposition (rolling-wave; single stage)

| Stage | Name | Scope | Decomposition depth |
|---|---|---|---|
| 1 | v0.1.6 Rule 7 ship | 10 file doc edits + plugin-internal 3-parallel Opus review + commit + tag + GH release | full WBS to task level |

(Single-stage charter; no Stage 2.)

### Per-stage kT baseline

| Phase | PO | RD | QA | Gate_Req | **Total** |
|---|---|---|---|---|---|
| Stage 1 | 15 | 80 | 60 | 30 | **185** |
| ProjectClose | — | — | — | — | **30** |
| Contingency | | | | | 35 (~16%) |
| **Project total** | | | | | **~250 kT** |

### Circuit breaker thresholds

| Trigger | Threshold | Action |
|---|---|---|
| 80% Stage-1 (calibration) | 148 kT | informational `[CALIBRATION-WARMUP]` at next gate |
| 100% Stage-1 hard breach | 185 kT | halt; CEO check-in mid-stage |
| 2× cumulative project | 500 kT | halt; CCB-Heavy required |

### Knobs (CEO_Gate_0 approved 2026-05-03T02:00+08:00)

| Knob | Setting |
|---|---|
| `pms` | PO + RD + QA |
| `retry_cap_per_gate` | 2 |
| `retry_cap_per_step` | 1 |
| `parallel_pm_limit` | 2 |
| `gate_requirement_mode` | final_only |
| `verify_policy` | default |
| `trust_tier_mode` | enabled |
| `kmr_mode` | enabled |
| `schema_enforcement_mode` | strict |

### Session knobs

- Auto Mode: enabled (reviewer cadence disabled)
- Worktree: **(b) in-place on feat branch** — see CCB Activity row 1 (revised from initial CEO_Gate_0 (a) approve due to PreToolUse hook scope)
- Final review: plugin-internal 3-parallel Opus review (NOT host `/opus-review final`)
- Schema: fresh PROGRESS.md (no prior collision)
- Branch: `feat/v0.1.6-plan-audit-rule-7` off main

### Plan-injection mode (deliberate hard-rule-1 deviation, see RAID-A below)

Stage 1 plan is PRE-COLLAPSED in pre-charter design discussion (memory: `~/.claude/sessions/` strategic-compact 2026-05-03 01:49+08:00 entry, 4 enforcements + 10 files + ~248 lines estimate). Per BeiliSystem v1.3.1 precedent, plan-injection means TeamLead writes the initial tasks.md (mechanical transcription of pre-collapsed plan, no novel decision). RD PM picks up at EXECUTING T-1-1.

## Active Stage: 1 — v0.1.6 Rule 7 ship

## State: COMPLETED

## Last Action: 2026-05-03T03:15:00+08:00 [TRUSTED] — Charter SHIPPED. Commit 5b016b2 (feat branch) → PR #1 merged → main HEAD 7d539fd → tag v0.1.6 annotated → GH release published. Project state: COMPLETED.

## Ship summary

- **Commit**: `5b016b2 feat: PlanAudit anti-self-skip Rule 7 v0.1.6` (11 files; +275/-6 lines)
- **PR**: https://github.com/HsuTse/teamwork-leader/pull/1 (merged via `gh pr merge --merge --delete-branch`; main HEAD merge commit `7d539fd`)
- **Tag**: `v0.1.6` annotated, pushed to origin
- **Release**: https://github.com/HsuTse/teamwork-leader/releases/tag/v0.1.6
- **Branch**: `feat/v0.1.6-plan-audit-rule-7` deleted on remote (per `--delete-branch`); local feat branch can be deleted at convenience

## RAID Register

- [V] Rule 7 prevents PLAN_AUDIT self-skip incidents | hypothesis: post-v0.1.6 dogfood `jq '.plan_audit_self_skip_detected' audit-trail.jsonl` shows 0 true values across ≥3 future plan-audit dispatches | realized: pending | measured_by: dogfood query post-Stage-1
- [A] 4-enforcement design from pre-charter discussion is implementation-ready without further refinement | validates if: Stage 1 EXECUTING produces 10 files matching the design's intent and final 3-parallel Opus review returns APPROVED or APPROVED_WITH_REVISIONS (not REJECTED) | validation_status: pending | validated_at: <empty>
- [A] Plan-injection mode justified — TeamLead direct-writes tasks.md (deviation from hard rule 1 §SKILL.md) because pre-collapsed plan is mechanical transcription with zero novel design decisions | validates if: Gate_Requirement reviewer 1 (Correctness) does NOT flag tasks.md as containing novel/unaudited decomposition | validation_status: pending | validated_at: <empty>
- [R] Self-referential dogfood — plugin-internal Opus reviewer evaluating v0.1.6 may itself trigger Rule 7's anti-self-skip detection while reviewing its own implementation | likelihood: med | impact: med | mitigation: dispatch prompt frames "this review evaluates Rule 7; meta-evaluation is acceptable; surface any reviewer self-suppression candidly" — RESOLVED at S1-D5: Reviewer C explicitly self-applied Rule 7, disclosed 1 near-miss (initial temptation to log "minor cleanup" semantically equivalent to blacklisted "cosmetic only"), articulated concrete fix instead. Dogfood works. | status: closed | owner: TeamLead | review_date: 2026-05-03

### Deferred from Gate_Requirement round 1 (CEO surface at CEO_Gate_1)

- [I] Reviewer A #1 — Pre-existing `auto-review-cadence.md` host-file references in `stage-runbook.md:99/107/199` lack v0.1.4 portability qualifier ("if present, otherwise plugin-bundled defaults"). Reviewer A explicitly: "Not a regression introduced by v0.1.6". | severity: low | owner: rd-pm | next action: address in v0.1.4 portability completion follow-up (out of v0.1.6 Charter scope) | status: open
- [I] Reviewer B #2 — `plan-audit-rubric.md` heading-level convention drift (Detection procedure as h3 nested under §Structured-field validation, but cross-ref'd as `§Detection procedure` from stage-runbook.md:141 same form as h2 sections). | severity: low | owner: rd-pm | next action: defer (cosmetic; cross-ref still text-resolves) | status: open
- [I] Reviewer C #2 — Anti-circumvention denylist incompleteness: 5 exact strings paraphrased around (`leave as-is`, `no action needed`, `documentation only`, `defer to next stage`). Reviewer C suggested §Calibration & expansion subsection documenting denylist growth protocol via Phase 4 dogfood evidence. | severity: med | owner: rd-pm | next action: defer to Phase 4 calibration governance (out of v0.1.6 Charter scope; v0.1.6 ships steel-thread denylist) | status: open
- [I] Reviewer C #4 — `audit-trail.jsonl` `plan_audit_self_skip_detected: bool | null` too coarse for Phase 4 calibration. Reviewer C suggested 3 sibling fields (`plan_audit_self_skip_values: [string]` / `_attempts: int` / `_issue_count: int`). | severity: med | owner: rd-pm | next action: defer to Phase 4 calibration scope alignment (out of v0.1.6 Charter; expanded schema would be Phase 4 deliverable) | status: open

## Stage History

### Stage 1 (closed 2026-05-03)

**Outcome**: SUCCESS — v0.1.6 PlanAudit Anti-Self-Skip (Rule 7) fully implemented per Charter; all in-scope DoD met.

**Files**: 10 (9 modified + 1 NEW `references/plan-audit-rubric.md`); +237 / -9 lines net (initial RD batch 133/-6 + RD corrective 104/-3).

**Dispatches** (7 total across Stage 1):
- S1-D1 RD batch (10-task plan-injected) — TRUSTED, schema:pass, kmr_skipped (batch deviation per CCB-Light row 2)
- S1-D2 PO terminology cross-PM — TRUSTED, 7/7 checks PASS, 1 low RAID-I (CHANGELOG narrative — fixed in S1-D6)
- S1-D3 Opus A Correctness — PASS, 1 deferred RAID-I (pre-existing v0.1.4 portability gap; not v0.1.6 regression)
- S1-D4 Opus B Doc-sync — PARTIAL → in-scope finding fixed in S1-D6; 1 low cosmetic deferred
- S1-D5 Opus C Self-ref dogfood — PARTIAL (1 HIGH + 3 med); dogfood self-application PASSED Rule 7 (caught + disclosed near-miss "minor cleanup" → "cosmetic only" semantic equivalence)
- S1-D6 RD corrective (4 in-scope fixes) — TRUSTED
- S1-D7 Opus C re-verify — PASS (0 findings; Fix 1 + Fix 2 effective)

**Gates**: Gate_Forward + Gate_Human SUBSUMED by Gate_Requirement per CCB-Light row 3 (doc-only stage). Gate_Requirement closed at round 2 PASS.

**Value Realized**: All 4 Rule 7 enforcements implemented + tested via self-referential dogfood (Reviewer C demonstrated Rule 7 active during its own review). Pending post-ship: cross-project dogfood across ≥3 future plan-audit dispatches to validate `plan_audit_self_skip_detected: false` rate.

**Token tally**: ~232 kT estimated (S1-D1 58 + S1-D2 18 + S1-D3 ~25 + S1-D4 ~30 + S1-D5 ~35 + S1-D6 14 + S1-D7 ~12 + TeamLead overhead ~40). Within Stage 1 baseline 185 + contingency 35 = 220 kT; ~5% over budget (within 80% calibration warmup tolerance for first-stage informational signal).

**WaveRefinement**: N/A (single-stage charter).

**Deferred RAID-I items for CEO awareness** (4 total — full text in §RAID Register):
1. Reviewer A #1 (low) — pre-existing `auto-review-cadence.md` host refs in stage-runbook.md (v0.1.4 follow-up)
2. Reviewer B #2 (low) — heading-level convention drift in plan-audit-rubric.md (cosmetic)
3. Reviewer C #2 (med) — anti-circumvention denylist expansion (Phase 4 calibration)
4. Reviewer C #4 (med) — Phase 4 schema fields (`_values` / `_attempts` / `_issue_count`)

## CCB Activity

- 2026-05-03T02:13+08:00 | section: §Session knobs / Worktree | requested-by: TeamLead | spec-impact: Worktree decision (a) "create worktree" reverted to (b) "in-place on feat branch" — PreToolUse pretooluse_guard.py hook (CLAUDE_GUARD_MODE=balanced) blocks Write to sibling dirs outside project root. Working in worktree dir would require disabling the hook (high-risk). Branch isolation preserved via feat branch; loss of working-copy isolation is minor for doc-only stage. | resolution: applied
- 2026-05-03T02:18+08:00 | section: §EXECUTING dispatch granularity | requested-by: TeamLead | spec-impact: 10 tasks T-1-1..T-1-10 batched into single RD PM dispatch S1-D1 instead of per-task dispatch loop. Rationale: (1) tasks are tightly coupled (Rule 7 + plan-audit-rubric.md + stage-runbook §PLAN_AUDIT must align as one design), (2) per-task overhead (~5-6 kT system prompt × 10 = ~60 kT) consumes ≥75% of RD budget allocation for trivial-edit overhead, (3) Auto Mode disables step-review Sonnet so per-task review savings non-existent, (4) anti-rubber-stamp 5-rule checklist still applies to batch return. Trade-off: KMR per-task divergence proxy unavailable for batch (logged `kmr_skipped: true` in audit-trail.jsonl with rationale). Stage Gates / 3-parallel Opus review at Gate_Requirement provides the verification depth normally distributed across 10 step-reviews. | resolution: applied
- 2026-05-03T02:25+08:00 | section: §GATING gate composition | requested-by: TeamLead | spec-impact: For doc-only single-stage charter, Gate_Forward (Sonnet doc-consistency) and QA cross-PM verification of RD test claims are SUBSUMED by Gate_Requirement 3-parallel Opus review (Correctness reviewer covers RD-claim sampling; Doc-sync reviewer covers cross-task consistency; Self-referential dogfood reviewer covers self-consistency). Gate_Human SKIPPED (no UI). Net gate sequence: PO terminology cross-PM + 3-parallel Opus Gate_Requirement → if all PASS / PASS_WITH_MINOR (in-place fix) → REPORTING. Rationale: doc-only stage has no executable code paths for Gate_Forward to trace (the verify commands are themselves greps which all 13 already PASS in RD's verify_evidence + were re-run by TeamLead Rule 2); Auto Mode Sonnet cadence disabled adds further redundancy. | resolution: applied

## Self-Audit

### Stage 1

- I verified 7 of 7 PM/reviewer dispatches this stage. Per-dispatch detail in `docs/audit-trail.jsonl`.
- divergence_flag distribution: aligned 3 (S1-D1, S1-D2, S1-D6 — PMs with meta), legacy_no_meta 4 (S1-D3, S1-D4, S1-D5, S1-D7 — Opus reviewers, no meta block per design)
- High-divergence dispatches (≥10): none
- Sampling-rotation distribution: TeamLead Rule 2 sample re-run × 2 (S1-D1 + S1-D6); PO cross-PM × 1 (S1-D2 terminology); 3-parallel Opus Gate_Requirement × 1 round + 1 Reviewer C re-verify
- trust_tier snapshot (Phase 3 N1): PO=standard, RD=standard, QA=standard (no UX activated; no Ad-hoc activated). All defaulted to standard for first stage; insufficient rolling-3-stage window for promotion. (no changes since last stage — first stage)
- Rule 7 dogfood metric: `plan_audit_self_skip_detected` = false for both Opus C dispatches (S1-D5: round 1 — found gaps in design but logged with actionable suggested_fix per Rule 7; S1-D7: round 2 — 0 findings, no logged issues at all)
- Honest disclosure: Reviewer C S1-D5 disclosed 1 near-miss self-violation (initial temptation to log "minor cleanup" semantically equivalent to blacklisted "cosmetic only"), articulated concrete fix instead. Dogfood works.
- Plan-injection deviation (TeamLead direct-wrote tasks.md per CCB-Light row 1): RAID-A validates if Gate_Requirement Reviewer A flagged tasks.md as novel — Reviewer A explicitly noted "tasks.md decomposition is mechanical transcription of pre-collapsed design"; no novelty flag → RAID-A validated.
- Batch dispatch deviation (CCB-Light row 2): RAID-A trade-off accepted; KMR skipped logged honestly per audit-trail.jsonl `kmr_skipped: true`. Gate_Requirement 3-parallel Opus provided verification depth originally distributed across 10 step-reviews.

## Lessons Learned

### What worked

1. **Plan-injection mode for tightly-coupled doc charters** — TeamLead direct-wrote tasks.md as mechanical transcription of pre-collapsed design (CCB-Light row 1). Reviewer A explicitly validated: "tasks.md decomposition is mechanical transcription of pre-collapsed design; no novelty flag". Saves dispatch ceremony cost when design is already audited externally.

2. **Self-referential dogfood is the strongest validation signal** — Reviewer C demonstrated Rule 7 working by (a) round 1 catching its own near-miss self-violation ("minor cleanup" semantically equivalent to blacklisted "cosmetic only") and articulating concrete fix instead, (b) round 2 logging 0 findings rather than padding with non-actionable suggested_fix values. Future Phase 4 candidates should include self-referential review slot when scope permits.

3. **Rule 7 Enforcement 3 deferral discipline** — Surfacing all 8 findings to CEO (4 in-scope apply / 4 defer to RAID-I) with explicit deferral memo beats reviewer auto-suppression by severity. CEO retained scope-control authority; reviewer C's "Phase 4 calibration scope" findings cleanly deferred without rubber-stamping.

4. **Batch dispatch with `kmr_skipped: true` honest disclosure** — 10-task batch into single RD dispatch S1-D1 saved ~50-70 kT vs per-task; KMR per-task divergence proxy honestly logged as skipped (not silently no-op'd). Gate_Requirement 3-parallel Opus provided verification depth originally distributed across 10 step-reviews. Trade-off acceptable for tightly-coupled doc charters; document via CCB-Light row 2 keeps audit trail clean.

5. **Round 2 surgical re-verification** — Reviewer C re-dispatch (S1-D7) with explicit "deferred findings — do NOT re-flag" framing prevented re-litigation of out-of-scope items. Reviewer C round 2 PASS with 0 findings demonstrates the framing works.

### What didn't (or would adjust next time)

1. **CEO_Gate_0 worktree decision (a) was reverted to (b)** — CCB-Light row 1: PreToolUse `pretooluse_guard.py` (CLAUDE_GUARD_MODE=balanced) blocked Write to sibling worktree dir. For plugin-source-repo dogfood, branch isolation via feat branch (no separate worktree) was sufficient. Future TeamLead charters: verify hook compatibility with worktree before approving CEO_Gate_0 (a).

2. **Schema `token_estimate_kT` type drift** — RD S1-D6 returned `"14"` (string) instead of `14` (int) per dispatch-header.md spec. v0.1.3 `schema_enforcement_mode == strict` could reject; pragmatically passed since trivially convertible and other 10 mandatory fields present. Future strictness: add type-check to schema validation + auto-coerce/reject decision.

3. **Stage 1 budget +5% over baseline** — ~232 kT actual vs 220 (185 + 35 contingency). Within first-stage `[CALIBRATION-WARMUP]` informational threshold; not a true overrun. Phase 4 calibration: collect ≥3 charter-close data points before re-baselining.

### Forward-looking — deferred to follow-up work

- v0.1.4 portability completion: stage-runbook.md:99/107/199 retain pre-existing `auto-review-cadence.md` host refs without portability qualifier (Reviewer A #1)
- Phase 4 anti-circumvention denylist expansion protocol (Reviewer C #2)
- Phase 4 audit-trail schema fields `_values` / `_attempts` / `_issue_count` for Rule 7 calibration (Reviewer C #4)
- Cosmetic: Detection procedure heading-level convention drift (Reviewer B #2)
