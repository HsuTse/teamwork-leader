# tasks.md — v0.1.9 Stage 1 task decomposition (post Opus PLAN_AUDIT revisions applied)

> **Charter**: I-023-M1 Measurement on Reference Host (GHA macOS runner)
> **Scope**: T-1-0 / T-1-a / T-1-b / T-1-c / T-1-d (5 sub-tasks within Stage 1)
> **Branch**: `feat/v0.1.9-measurement` (from main `07aa9ce`)
> **Anti-scope-creep mandate**: active (v0.1.8 L-1 inheritance) — any work outside this list = CCB-Heavy
> **Selected RD plan**: Candidate **C** (matrix macos-14 + macos-13) per Opus selector_score 12.5
> **Stage 1 budget cap**: 320 kT (escalated from 275 via CCB-Light M-1; absorbs GHA first-time setup + retry slack + Opus final cost variance)

---

## Stage 1 — I-023-M1 Measurement (single-stage charter)

### T-1-0 — L-2 normative codification (Stage 1.0 ship-blocking sub-task)
- **Owner**: PO PM
- **Scope** (3 surgical edits to `skills/teamwork-leader-workflow/references/stage-runbook.md`):

  1. **Edit 1 — §GATING attribution-truth (line 293)**: search anchor `**Attribution-truth on TeamLead-owned gate artifacts (advisory; v0.1.7 lesson I-071)**:`. Promote `(advisory)` → `(MUST; v0.1.7 L-2 codified v0.1.9)`. Change `SHOULD` → `MUST`. Replace `Recommended discipline, not a state-machine block.` with `MUST-level discipline; violation requires CCB-Light entry at gate close.` **Append CCB-Light loop bound exemption** (PO-3): "CCB-Light entries written to log attribution drift are themselves exempt from re-triggering this rule (the CCB-Light entry IS the remediation; re-checking it would create a self-referential loop). The enforcement clause fires at most ONCE per gate-close event, not per audit-trail key written."

  2. **Edit 2 — §EXECUTING step 6 (line 201)**: add 4th bullet to Sonnet step-reviewer dispatch inputs: "**Attribution-truth check (MUST; v0.1.7 L-2)**: if this task's `artifacts_touched` includes Gate_Forward / Gate_Requirement audit-trail writes, step-reviewer MUST verify that any AC key cited in those writes matches design.md FROZEN spec enumeration — existence-grep of the key string is insufficient; verify the key traces to an AC in design.md §N. A review that passes on existence-grep alone with unverified attribution is a rubric failure."

  3. **Edit 3 — discoverability cross-ref comment (PO-1)**: after Edit 2's new bullet, append: `<!-- L-2 codified rubric items: this step + §GATING attribution-truth paragraph (lines ~292-294); historical name 'step-review-rubric' -->`. Costs ~2 kT; preserves grep-discoverability for future readers searching the archived L-2 name.

- **DoD**: 3 surgical edits applied; stage-runbook.md §step-review-rubric historical name grep-discoverable via comment; design.md FROZEN §1–§6 untouched (verify via `git diff -- docs/specs/auto-resume-daemon-design.md` returns empty); Sonnet step-review PASS.
- **Revert_Procedure (M-3)**: if T-1-c reveals MUST clause unworkable in practice (e.g., legitimate post-hoc AC relabel for novel design.md gaps), revert via `git revert <T-1-0 commit SHA>` + new CCB-Light entry: "L-2 MUST premature; reverting to advisory pending v0.1.10 redesign". Default expectation: MUST status is permanent; revert is an exception path.
- **Estimated**: 32 kT (30 + 2 for Edit 3)
- **Status**: COMPLETE (dispatch V0.1.9-S1-D3; 3 surgical edits applied; Sonnet step-review PASS_WITH_MINOR → minor fix on line 205 applied → effectively PASS; design.md FROZEN untouched verified)

### T-1-a — GHA macOS runner bring-up + smoke verify (matrix C; ⚠️ 80 kT time-box)
- **Owner**: RD PM
- **Selected plan**: Candidate C (matrix macos-14 + macos-13) per Opus selector_score 12.5; A/B archived as RAID-A backup plans
- **Scope**: Author `.github/workflows/measure-latency.yml` with parallel matrix jobs:

  1. **Matrix structure**: `strategy.matrix.os: [macos-14, macos-13]` with `fail-fast: false` (per-arch independent execution).

  2. **Common steps per arch**: checkout → setup-python 3.11 → mkdir `$CLAUDE_PROJECT_DIR/.teamlead` → `bash tools/measure-latency.sh --self-test` (smoke) → `python3 scripts/install.py 2>&1 | tee /tmp/install-output.txt` (Q1.5 verify) → **dual detection** (per C-2): grep stdout for `"MANUAL INSTALLATION REQUIRED"` AND check `$CLAUDE_PROJECT_DIR/.teamlead/install-state.json` for `status != "manual-pending"`. **Workflow PASS requires BOTH signals negative**; either signal positive → fail-fast exit 1.

  3. **Per-arch evidence artifact** (per C-3): each matrix job writes evidence to `docs/archives/measurement.v0.1.9.${{matrix.os}}.partial.md` (NOT the final archive doc). Upload as separate artifact `t1a-evidence-${{ runner.os }}-${{ runner.arch }}`. T-1-a does NOT touch `tasks.md` or final `docs/archives/measurement.v0.1.9.md` — those are T-1-c QA's responsibility (post-merge).

  4. **Workflow-level PASS criterion (revised per C-1)**: AT LEAST `macos-14` arm64 PASS (primary arch). `macos-13` x86_64 result is recorded but non-blocking — if it FAILS while macos-14 PASSes → T-1-c proceeds on macos-14 only with x86_64 caveat documented in measurement.v0.1.9.md §host-environment §x86_64-fallback. If BOTH FAIL → Q0 fallback fires (v0.1.9 closes as MEASUREMENT-DEFERRED-AGAIN). If macos-14 FAILS while macos-13 PASSes → T-1-c proceeds on macos-13 with explicit arch-mismatch caveat (degraded-evidence path; surfaced as RAID-I at Stage close).

  5. **Cleanup step**: `python3 scripts/install.py --uninstall` (idempotent) on each runner; runs in `if: always()` block.

  6. **Q0 fallback path documented**: workflow summary writes structured failure marker for TeamLead detection: `Q1.5: launchctl bootstrap FAILED on <both arches>` → step-review FAIL → step 7's 1-retry consumed → second FAIL → ESCALATED with Q0 fallback verb.

- **DoD**: workflow file `.github/workflows/measure-latency.yml` exists; PR run produces parallel macos-14 + macos-13 jobs; per-arch dual-detection (stdout grep + install-state.json) implemented; per-arch evidence artifacts uploaded; workflow PASS = at-least-macos-14-PASS; Q0 fallback marker emitted on both-arch FAIL; TeamLead can download artifacts to evaluate.
- **Estimated**: 60 kT (matrix candidate cost)
- **Status**: COMPLETE — verdict **PARTIAL_PASS** (matrix C primary-arch PASS criterion met). macos-14 (PRIMARY) all 11 steps PASS on run 25371652043 head `cef9caa`: Q1.5 dual-detection PASS (`install_exit=0`/`stdout_degraded=0`/`state_degraded=0`), daemon registered as LaunchAgent. macos-13 (FALLBACK) cancelled at 35min queued — GHA Intel x86_64 runner pool capacity-exhausted (system-wide; not workflow defect). Per Opus C-1 at-least-macos-14 PASS DoD, T-1-c kickoff gate (M-2) **GREEN**. x86_64 caveat documented at §host-environment §x86_64-fallback. Evidence: `docs/archives/measurement.v0.1.9.macos-14.partial.md`.

### T-1-b — Measurement protocol design + Sonnet review
- **Owner**: PO PM (drafts protocol) + QA PM (review)
- **Scope**: Write `docs/specs/measurement-protocol.v0.1.9.md` (8-section structure per PO PLANNING):
  - §metadata / §definitions / §measurement-procedure / §acceptance-criteria (normative) / §statistics-computation / §evidence-format / §failure-mode / §archive-target

- **Finalized AC values (Q2 defaults locked)**:
  - AC-1: N ≥ 10 measurement runs per type (cold + warm separate counters)
  - AC-2: strict three-statistic — p50 ≤ 30s ∧ p95 ≤ 30s ∧ max ≤ 30s
  - AC-3: cold-start (no prior plist; fresh install state) + warm-start (plist present, daemon running) measured SEPARATELY; each independently gated
  - AC-4: host env recorded — OS / launchctl bootstrap path / hook chain / plist install path
  - AC-5: evidence at `docs/archives/measurement.v0.1.9.md`

- **N=10 p95=max degeneracy clause (PO-2)**: §statistics-computation MUST include explicit text: "At N=10, p95 is computed as the 10th-order-statistic (i.e., equals max by sample definition); AC-2 evaluation at N=10 therefore reduces to two independent gates (p50 ≤ 30s AND max ≤ 30s); AC-2 is satisfied iff both hold. To obtain a p95 statistic distinct from max, N ≥ 20 is required; relaxation to N ≥ 20 to recover distinct p95 is permitted via CCB-Light at T-1-c kickoff if cold-start-only N=10 cost-budget headroom is available."

- **Parallel/Q0 dependency note (PO-4)**: T-1-b executes in parallel with T-1-a. If T-1-a triggers Q0 fallback before T-1-b completes, T-1-b output is preserved as v0.1.10 carryover (NOT wasted — protocol doc has independent v0.1.10 value). Sequential execution would save 30 kT under Q0 but adds 30 kT serial latency under non-Q0; parallel preferred (non-Q0 = expected path).

- **DoD**: protocol doc exists with all 8 sections + N=10 degeneracy clause; Sonnet step-review PASS.
- **Estimated**: 30 kT
- **Status**: COMPLETE (dispatch V0.1.9-S1-D5; 28 kT actual; 9 sections present + AC values match + PO-2 + PO-4 clauses verbatim; Sonnet step-review PASS, 0 issues)

### T-1-c — Execute measurement on GHA macOS runner
- **Owner**: QA PM (executes via workflow_dispatch + collects artifacts + merges per-arch partials)
- **Kickoff gate (M-2 explicit)**: T-1-c dispatch requires (a) **T-1-a verdict ∈ {PASS, PARTIAL_PASS}** AND (b) **T-1-b PR merged to `feat/v0.1.9-measurement`**. If T-1-a only macos-14 PASS (PARTIAL_PASS), T-1-c executes on macos-14 only with x86_64 caveat. If T-1-a only macos-13 PASS, T-1-c executes on macos-13 with arch-mismatch caveat (degraded path).
- **Scope**: Run measurement workflow N times per T-1-b protocol; collect baton-write→SESSION_RESUMED wall-clock latency for cold-start and warm-start; record p50/p95/max + raw datapoints; merge T-1-a per-arch partials (`measurement.v0.1.9.macos-14.partial.md` + `measurement.v0.1.9.macos-13.partial.md` if both PASS) into `docs/archives/measurement.v0.1.9.md` final with §host-environment subsections.
- **DoD**: ≥10 measurement runs per type + arch completed; raw data + p50/p95/max statistics captured; final measurement.v0.1.9.md populated with §host-environment + §statistics + §interpretation; Sonnet step-review PASS.
- **Estimated**: 60 kT
- **Status**: COMPLETE [CLAIMED-PENDING-STEPREVIEW] — QA dispatch V0.1.9-S1-D6 returned SUCCESS at 2026-05-05T20:24+08:00. Run 25375693016 macos-14: N=10 cold + N=10 warm all OK. Cold p50=15.523s / max=15.875s. Warm p50=5.270s / max=5.834s. **All 5 ACs PASS** (AC-1 ≥10 each / AC-2 ≤30s strict / AC-3 separate gates / AC-4 host env recorded / AC-5 archived). Evidence committed `c361442` + pushed origin. 7 commits since charter-open (4270fa6 → cef9caa → 6290f26 → 0990e62 → 895a910 → ec23fa0 → c361442). **Scope-expansion flag**: QA created `tools/patch-plist-python3.py` (NEW; workflow-layer workaround for system python3 PEP 604 incompatibility) — daemon.py FROZEN spec NOT modified, but this is a borderline scope expansion that needs Sonnet step-review verification on resume.

### T-1-d — Gate evaluation (AC-1..AC-4 verification)
- **Owner**: TeamLead (gate run via `scripts/gate-requirement-runner.sh`) + Opus reviewer (independent final review)
- **Scope**: Verify AC-1 (N≥10 per type), AC-2 (p50/p95/max all ≤30s OR variance rule met per PO-2 N=10 degeneracy clause), AC-3 (cold+warm separately gated), AC-4 (host env recorded). If any AC FAIL → execute Q3 verb (i / iii / iv).
- **DoD**: AC-0..AC-7 all met; Gate_Requirement classifier `verdict: PASS`; Opus final review APPROVED.
- **Estimated**: 30 kT (T-1-d) + 20 kT (Gate_Req) + 25 kT (Opus final) = 75 kT total
- **Status**: pending EXECUTING

---

## Stage 1 budget summary (post M-1 escalation)

| Sub-task | kT | Notes |
|---|---|---|
| T-1-0 | 32 | +2 for Edit 3 cross-ref comment |
| T-1-a (Candidate C matrix) | 60 | matrix; 80 kT time-box for host bring-up enforced |
| T-1-b | 30 | parallel with T-1-a |
| T-1-c | 60 | gated by T-1-a PASS + T-1-b merged |
| T-1-d | 30 | |
| Gate_Requirement | 20 | |
| Opus final review | 35 | escalated from 25 (historical 30-40 kT) |
| **Stage 1 sub-task total** | **267** | |
| **Stage 1 cap (M-1 escalation)** | **320 kT** | escalated from 275 via CCB-Light pre-execution; absorbs GHA first-time setup + 5×~10 kT retry slack + Opus final cost variance |
| Project total | ~395 kT | charter total; was ~355 |
| Contingency | 50 kT | unchanged |
| 2× cumulative breaker | 790 kT | |

---

## Plan_candidates archive (RAID-A backup plans per stage-runbook §PLAN_AUDIT step 4)

- **A** (REJECTED, selector_score 21.5): macos-14 arm64 only. Backup plan if matrix C runner allocation fails to schedule both arches simultaneously and we need fast single-runner fallback.
- **B** (REJECTED, selector_score 22.0): macos-13 x86_64 only. Backup plan if macos-14 arm64 GHA capacity unavailable AND user accepts arch-mismatch caveat (would require new CCB-Light to validate).

Both archived to PROGRESS.md `## RAID Register §v0.1.9 charter-active` as `[A]` (assumption) entries with `validation_status: pending`.

---

## Pre-EXECUTING note

This decomposition reflects Opus PLAN_AUDIT APPROVED_WITH_REVISIONS verdict + all 11 revisions applied (5 PO + 3 RD-C + 3 missing-items). Selected_id=C with revisions baked in. Dispatch sequence: T-1-0 (PO) + T-1-a (RD) parallel → T-1-b (PO) parallel with T-1-a → T-1-c (QA, gated) → T-1-d (TeamLead).
