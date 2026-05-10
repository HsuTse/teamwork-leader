# CCB Audit Log — teamwork-leader v0.1.7 Auto-Resume Daemon

<!--
Canonical location: docs/decisions/ccb-log.md
Authority for format: references/pmp-ccb.md §Audit log file (4-col Light entries) + §CCB-Heavy.
Created: 2026-05-04 (S4-PLAN-PO dispatch; first PO Light entry for Stage 4 design.md §4 extension).
-->

## Light entries (per stage, 4-col format per pmp-ccb.md §Audit log file)

<!-- PO appends a row each time a CCB-Light is applied (per pmp-ccb.md §CCB-Light step 4).
     Section identifier (column 2) = doc-anchor heading slug. -->

### Stage 1

| Date | Section | Rationale | Original→New |
|---|---|---|---|
| 2026-05-06 | `measurement-protocol.v0.1.9.md §methodology-deviations` (NEW section) + `measurement.v0.1.9.md §interpretation` (back-link) | M-2: Add normative §methodology-deviations subsection authorizing stub-based claude binary as equivalent for T5 SESSION_RESUMED signal-path validation on GHA macOS runners; bidirectional link with archive (dispatch_id: V0.1.9-S1-D7) | §methodology-deviations absent → new section inserted between §archive-target and §parallel-execution-note (L379+); archive §interpretation stub paragraph → opening sentence extended with `(authorized per measurement-protocol.v0.1.9.md §methodology-deviations deviation-1)` |
| 2026-05-06 | `measurement-protocol.v0.1.9.md §methodology-deviations` (deviation-2 additive) | M-4: Add deviation-2 (Gate_Human declared N/A for non-interactive evidence) per Opus advisor 2nd consultation R1 BLOCKER; declares structural absence per three-gates.md L136-141 normative scope; M-2 transparency principle requires explicit registration (dispatch_id: V0.1.9-S1-D8) | deviation-2 absent → new `### deviation-2: Gate_Human declared N/A for non-interactive evidence` block inserted after deviation-1 Evidentiary anchor, before `---` separator |

### Stage 2

| Date | Section | Rationale | Original→New |
|---|---|---|---|
| (Stage 2 CCB-Light entries CCBL-001..CCBL-003 tracked in PROGRESS.md ## CCB Activity; pre-date this log file creation) | | | |

### Stage 3

| Date | Section | Rationale | Original→New |
|---|---|---|---|
| (Stage 3 CCBL-Stage3-001 tracked in PROGRESS.md ## CCB Activity; pre-date this log file creation) | | | |

### Stage 4

| Date | Section | Rationale | Original→New |
|---|---|---|---|
| 2026-05-04 | `launchd-plist-template/daemonpy-contract` | §4 extended with daemon.py contract + invocation + state machine + crash recovery + PID lifecycle + Stage 4 acceptance criteria + open questions + cross-script integration invariants (S4-PLAN-PO dispatch; dispatch_id: S4-PLAN-PO) | §4 lines 404-414 (Install-procedure bullet list) → §4 lines 404-end-of-new-subsections (≥180 lines added; existing plist template, key-directive rationale, and Touchpoints unchanged) |
| 2026-05-04 | `gate-lock-reap-subcommand` | lib/gate-lock.py `--reap` extended to accept explicit `<lock_path>` positional arg (in addition to existing env-var production path); enables daemon.py subprocess invocation `python3 lib/gate-lock.py --reap <lock_path>` per design.md line 304 + I-049 PLAN_AUDIT authorization. Additive only — `--acquire`/`--release`/`--test-acquire`/`--test-release` behaviour unchanged. Existing `--self-test` must still PASS (regression-safety). (S4-D6; dispatch_id: S4-D6) | `--reap` (no args, env-var only) → `--reap [<lock_path>]` (optional path arg; defaults to env-var when absent) |

### Stage 5 (v0.1.8 charter)

| Date | Section | Rationale | Original→New |
|---|---|---|---|
| 2026-05-05 | `design.md §7 (NEW additive)` | v0.1.8 charter codifies v0.1.7 degraded-mode ship rationale as explicit shipping constraint; ≤30s threshold retained; measurement deferred to v0.1.9 with reference-host prerequisite (S1-D1; dispatch_id: S1-D1) | §7 absent (EOF line 910, after `## QA Sign-off`) → §7 appended (lines 912–end; §1–§6 byte-identical) |

### Stage 1 (v0.1.10 charter)

| Date | Section | Rationale | Original→New |
|---|---|---|---|
| 2026-05-08 | `PROGRESS.md ## Charter AC-1 wording (CCBL-Stage1-v0.1.10-AC1-WORDING)` | Opus PlanAudit blocker: AC-1 wording '重構' contradicts v0.1.7 close-report classification of I-061 as COSMETIC. Anti-scope-creep mandate prohibits behavior-changing 'fixes' to non-defects. CEO selected `C + amend AC-1`. AC-1 wording amendment is scoped clarification (preserves charter intent: close I-061 disposition; does not change Stage 1 AC count or Stage 2 scope) → CCB-Light. | AC-1: `I-061 daemon array structure 重構` → `I-061 daemon array structure 收斂 (close disposition: cosmetic-as-documented per v0.1.7 classification; comment-only edit at scripts/daemon.py lines 38-41)` |
| 2026-05-08 | `auto-resume-daemon-design.md §4 placement of AC-4-H/I/J (CCBL-Stage1-v0.1.10-AC4-PLACEMENT)` | Opus PlanAudit blocker: appending AC-4-H/I/J into existing §4 7-row table violates v0.1.7 Opus C1 attribution-truth (design-frozen DoD vs task-level acceptance must remain visually distinct). CEO selected separate subsection. RAID-V0.1.10-A-1 closed by this entry. | T-1-A4 plan: `append 3 rows after AC-4-G in §4 table` → `add new subsection §4.X 'Task-level acceptance criteria (post-hoc TeamLead-coined; not design-frozen DoD)' below 7-row table; intro at line 533 reads '7 design-frozen DoD acceptance criteria below; see §4.X for 3 task-level addenda'` |
| 2026-05-08 | `PROGRESS.md ## Charter AC-10 sub-AC + new T-1-A5 (CCBL-Stage1-v0.1.10-AC10-EVIDENCE)` | Opus PlanAudit major: Security findings D-1/D-2/D-3 hook lives at `~/.claude/hooks/pretooluse_guard.py` OUTSIDE repo; AC-10 closure needs in-repo evidence path. CEO selected `AC-10 sub-AC + docs/security/*`. New sub-task T-1-A5 added to Stage 1 active scope (in-scope sub-AC; not net-new charter scope — closure mechanism for already-locked AC-10). | AC-10 (`Ad-hoc Security PM 完成 hook 白名單 attack surface 評估 + 留 RAID-I 或 advisory note (依結論)`) extended with sub-AC: `closure evidence committed to docs/security/v0.1.10-hook-hardening.md including before/after regex (D-2 third-branch tightening), before/after ask-prompt string (D-1), compound-operator detection logic (D-3), and pytest/manual smoke transcript verifying T1-T4 baseline + new T5-T7 attack scenario tests (FN-1 semicolon / FN-2 && / FN-3 path-spoof) all behave as intended. Hook code edit applied out-of-tree at ~/.claude/hooks/pretooluse_guard.py NOT committed to teamwork-leader repo.` New sub-task T-1-A5 dispatched at EXECUTING. |
| 2026-05-08 | `docs/specs/measurement-protocol.v0.1.10.md (NEW additive) + docs/specs/measurement-protocol.v0.1.9.md §C-4 (text-vs-evidence preserved) (CCBL-Stage1-v0.1.10-MP-PROTOCOL)` | RAID-I-2 closure: workflow-as-truth (engineering rationale: ThrottleInterval 10s + cold-start launchd overhead → C-4=90s correct). New v0.1.10 protocol with corrected C-4=90s; v0.1.9 protocol unchanged to preserve archived measurement evidence-truth (actual runs used 90s; spec text 60s was copy-paste error). (V0.1.10-S1-EX2; dispatch_id: V0.1.10-S1-EX2) | `docs/specs/measurement-protocol.v0.1.10.md` absent → new file ~60 lines; v0.1.9 protocol §C-4 text unchanged |
| 2026-05-08 | `Stage 1 Gate_Human declared N/A (CCBL-Stage1-v0.1.10-GATE-HUMAN-NA)` | Per `references/three-gates.md` L136-141 normative scope (Gate_Human covers UI 操作行為), Stage 1 scope is non-interactive: daemon code (scripts/daemon.py), spec doc (design.md §4.X), hook hardening (~/.claude/hooks/pretooluse_guard.py — out-of-tree), agent intake (po-pm.md), measurement protocol (measurement-protocol.v0.1.10.md), ccb-log. Zero UI surface area. Per v0.1.9 M-4 precedent + `feedback_silent-deviation-prohibited.md`, structural absence requires explicit CCB-Light registration (not silent skip). (V0.1.10-S1-G1; dispatch_id: V0.1.10-S1-G1) | Gate_Human absent → declared N/A with structural-absence justification; cross-PM verification of declaration: QA Gate_Forward Sonnet confirmed via dispatch scope review + non_functional_findings empty for UI category |

### Stage 2 (v0.1.10 charter)

| Date | Section | Rationale | Original→New |
|---|---|---|---|
| 2026-05-08 | `auto-resume-daemon-design.md §7 term (f) vs charter AC-8 anchor (CCBL-Stage2-v0.1.10-T24-ANCHOR)` | Opus PlanAudit S2 major: Charter AC-8 wording references `§reliability budget` anchor but design.md has no such heading; PO T-2-4 plan A appends §7 term (f) (additive — established pattern from terms (a)-(e) per v0.1.8 amendment). Charter-clarification CCB-Light: AC-8 anchor `§reliability budget` pragmatically realized as `§7 term (f)`; semantic equivalence preserved (cold p50 utilization + headroom note); no FROZEN-spec violation. (V0.1.10-S2-PA; dispatch_id: V0.1.10-S2-PA) | AC-8 closure target: `§reliability budget` (anchor-as-named in charter) → `§7 term (f) — cold-start reliability budget` (anchor-as-realized in design.md per v0.1.10 PlanAudit) |
| 2026-05-08 | `Stage 2 T-2-1 local real-claude measurement BLOCKED (CCBL-Stage2-v0.1.10-T21-LOCAL-BLOCKED) + measurement-protocol.v0.1.10.md §methodology-deviations deviation-3` | RD V0.1.10-S2-EX1 EXECUTING: T-2-1 BLOCKED by env-class issue (system python3 3.9.6 on macOS 15.3 vs daemon.py PEP 604 syntax requiring 3.10+; install.py + plist template re-render loses patch-plist-python3.py runtime fix; reload via launchctl bootout/bootstrap hard-denied by hook after repeated approved ask-prompts — D-3 escalation behavior). 3 resolution options (A/B/C) surfaced; TeamLead Auto Mode selected Option **C** (Accept BLOCKED + GHA-only AC-7) per Opus PlanAudit `partial_acceptable_for_Stage2_close` rule + [HsuTse] blanket "直接開發至結束" authorization. Empirical block proof: see RAID-I-S2-launchctl-hook closure note. AC-7(i) status: PROVEN-UNAVAILABLE on this host class. Install-lifecycle hardening (Option B template fix or Option A permission rule) deferred to v0.1.11. (V0.1.10-S2-EX1; dispatch_id: V0.1.10-S2-EX1) | Charter AC-7: `(i) 本機 macOS host (Hook 白名單路徑) AND (ii) GHA macos-14 reference host 雙處執行` → AC-7 partial: (i) PROVEN-UNAVAILABLE (env-class block; deferred to v0.1.11) + (ii) GHA real-claude (Candidate A confirmed via pre-val) — pending main measurement run; deviation-3 added to measurement-protocol.v0.1.10.md §methodology-deviations |
| 2026-05-08 | `Stage 2 T-2-2 GHA real-claude/daemon integration gap empirically proven (CCBL-Stage2-v0.1.10-T22-GHA-INTEGRATION-GAP) + measurement-protocol.v0.1.10.md §methodology-deviations deviation-4` | GHA workflow run 25532761179 (Candidate A real-claude path; commit efbd5af): pre-validation PASS confirmed claude installable; main run installed claude 2.1.133 + daemon installed each cold cycle (~13s install) BUT 10/10 cold + 10/10 warm SESSION_RESUMED never reached within timeouts (C-4 90s; W-3 60s). cold_runs.jsonl + warm_runs.jsonl: 0 bytes. Root cause: daemon's polling target (designed against stub-claude artifact format) does not match what real claude produces on `--resume`. This is a v0.1.7 daemon-design assumption that surfaced at v0.1.10 first real-claude end-to-end attempt. Anti-scope-creep mandate prohibits scope expansion to debug integration; deferred to v0.1.11 RAID-V11-real-claude-integration (sev:HIGH). AC-7(ii) status: PROVEN-INTEGRATION-GAP. AC-7 (overall) → PARTIAL with comprehensive empirical proof for both host paths (deviation-3 + deviation-4). (V0.1.10-S2-EX1-result-followup; dispatch_id: V0.1.10-S2-G1-prep) | AC-7(ii) target: `GHA macos-14 reference host real-claude end-to-end measurement` → AC-7(ii) PROVEN-INTEGRATION-GAP (install-layer PASS + integration-layer FAIL); deviation-4 added to measurement-protocol.v0.1.10.md §methodology-deviations; AC-7 overall PARTIAL |

## Heavy events

<!-- No CCB-Heavy events have reached CEO decision stage as of 2026-05-04 (Stages 1-4).
     TeamLead will append detail blocks here if/when a Heavy is decided. -->

### Stage 2 (v0.1.10 charter), CCB-Heavy #1 (decided 2026-05-10)

- **id**: CCBH-v0.1.10-AC7-DEMOTE-V0.1.11
- **time-raised**: 2026-05-08T10:35+08:00 (ESCALATED state entry; AC-7 PROVEN-INTEGRATION-GAP confirmed from GHA run 25532761179)
- **time-decided**: 2026-05-10T09:03:41+08:00 (CEO selected verb=`revise_charter` from 4-verb ESCALATED menu via AskUserQuestion)
- **Origin**: ESCALATED — charter-level AC failure (AC-7 real-claude end-to-end measurement PROVEN-BLOCKED on both host classes); CEO 4-verb decision required before release
- **Linked Light entries**: CCBL-Stage2-v0.1.10-T21-LOCAL-BLOCKED (deviation-3; local env-class block) + CCBL-Stage2-v0.1.10-T22-GHA-INTEGRATION-GAP (deviation-4; GHA integration-layer failure)
- **Material change**: AC-7 demoted from v0.1.10 must-have to v0.1.11-deferred per deviation-3 (local PROVEN-UNAVAILABLE env-class) + deviation-4 (GHA PROVEN-INTEGRATION-GAP); v0.1.10 ship gate proceeds without AC-7
- **CEO verb**: approve (`revise_charter` — recommended path from ESCALATED 4-verb menu)
- **Impact summary**: 5 v0.1.11 RAID carry-forward registered (RAID-V11-real-claude-integration sev:HIGH + RAID-V11-install-lifecycle-python3-path sev:MED + RAID-V11-ccb-token-cost sev:MED + RAID-V11-pm-subagent-disclosure sev:MED + RAID-SEC-V11-backtick-subshell-injection sev:MED — last entry registered post-Phase C Ad-hoc Security PM LessonsLearned introspection); no budget recalculation required (Stage 2 actual ~195 kT vs 450 baseline); tag v0.1.10 proceeds per CEO_Gate_Final approve
- **Post-decision actions taken**:
  - [x] PROGRESS.md ## Charter APPENDED (append-only per §5.5.1): AC-7 demoted; AC-1..6+8+9+10 met; tag v0.1.10 proceeds
  - [x] PROGRESS.md State: ESCALATED → REPORTING; Stage 2 StageReport written
  - [x] PROGRESS.md ## RAID Register §Stage 2 → v0.1.11 carry: 5 RAIDs registered (4 at Phase A + 1 added at Phase C from Ad-hoc Security PM LL discovery)
  - [x] docs/decisions/ccb-log.md §Heavy events: this row appended
- **RAID delta applied**: RAID-V11-real-claude-integration (open-v0.1.11, sev:HIGH) + RAID-V11-install-lifecycle-python3-path (open-v0.1.11, sev:MED) + RAID-V11-ccb-token-cost (open-v0.1.11, sev:MED) + RAID-V11-pm-subagent-disclosure (open-v0.1.11, sev:MED) + RAID-SEC-V11-backtick-subshell-injection (open-v0.1.11, sev:MED)

## Cap-rule audit (per stage, derived from Light tables above)

| Stage | Light count | Same-section max | ≥3 same-section breach? | ≥5 stage total breach? | Auto-escalated to CCB-Heavy? |
|---|---|---|---|---|---|
| 1 | 2 | 1 (CCBL-Stage1-M2 and CCBL-Stage1-M4 are different subsections within §methodology-deviations) | no | no | no |
| 2 | 3 | 1 (CCBL-001/002/003 each different sections) | no | no | no |
| 3 | 1 | 1 | no | no | no |
| 4 | 2 | 1 (CCBL-Stage4-S4-PLAN-PO and CCBL-Stage4-T-4-6 are different sections) | no | no | no |
| 5 (v0.1.8) | 1 | 1 (§7 is net-new section; no prior entry) | no | no | no |
| 1 (v0.1.10) | 5 | 1 (AC1-WORDING / AC4-PLACEMENT / AC10-EVIDENCE / MP-PROTOCOL / GATE-HUMAN-NA — five different sections) | no | yes (5 stage-total = cap; auto-cap-rule audit — see Suppression escape hatch) | no |
| 2 (v0.1.10) | 3 | 1 (T24-ANCHOR / T21-LOCAL-BLOCKED / T22-GHA-INTEGRATION-GAP — three different sections) | no | no | no |

## Suppression escape hatch usage (per pmp-ccb.md §Cap rules)

| Stage | Suppressed? | Reason |
|---|---|---|
| 1 | no | n/a |
| 2 | no | n/a |
| 3 | no | n/a |
| 4 | no | n/a |
| 5 (v0.1.8) | no | n/a |
| 1 (v0.1.9 M-4) | no | n/a |
| 1 (v0.1.10) | **yes — escape hatch invoked** | All 5 entries (AC1-WORDING / AC4-PLACEMENT / AC10-EVIDENCE / MP-PROTOCOL / GATE-HUMAN-NA) originated from a single atomic governance event chain: Opus PlanAudit verdict APPROVED_WITH_REVISIONS → CEO 3-decision menu → applied at Stage 1 entry to EXECUTING + Gate_Forward declaration. Each entry closes a distinct PlanAudit blocker / major / RAID; none reflect chronic drift, churn, or scope creep. Per `references/pmp-ccb.md §Cap rules`, suppression escape hatch is the correct call when cap is reached via single-event atomic closures rather than recurring clarification need. |
| 2 (v0.1.10) | no | n/a |

## Project-level CCB statistics

<!-- Will be populated at ProjectClose. -->

- Total CCB-Light: 16 (CCBL-001 + CCBL-002 + CCBL-003 + CCBL-Stage3-001 + CCBL-Stage4-S4-PLAN-PO + CCBL-Stage4-T-4-6 + CCBL-Stage5-S1-D1 + CCBL-Stage1-v0.1.9-M4 + CCBL-Stage1-v0.1.10-AC1-WORDING + CCBL-Stage1-v0.1.10-AC4-PLACEMENT + CCBL-Stage1-v0.1.10-AC10-EVIDENCE + CCBL-Stage1-v0.1.10-MP-PROTOCOL + CCBL-Stage1-v0.1.10-GATE-HUMAN-NA + CCBL-Stage2-v0.1.10-T24-ANCHOR + CCBL-Stage2-v0.1.10-T21-LOCAL-BLOCKED + CCBL-Stage2-v0.1.10-T22-GHA-INTEGRATION-GAP)
- Total CCB-Heavy: 1 (CCBH-v0.1.10-AC7-DEMOTE-V0.1.11)
- Most-revised sections: §4 daemon.py contract (1), payload-channel (1), plan-decomp-strategy (1)

## Cross-reference

- PROGRESS.md ## CCB Activity — current stage's open CCB-Light entries (resets at stage close)
- PROGRESS.md ## CCB-Heavy Pending — currently-open CCB-Heavy (cleared on CEO decision; transient)
- references/pmp-ccb.md — operational rules + 4-col Audit log file format authority
