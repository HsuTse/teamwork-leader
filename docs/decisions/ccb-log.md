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

## Heavy events

<!-- No CCB-Heavy events have reached CEO decision stage as of 2026-05-04 (Stages 1-4).
     TeamLead will append detail blocks here if/when a Heavy is decided. -->

## Cap-rule audit (per stage, derived from Light tables above)

| Stage | Light count | Same-section max | ≥3 same-section breach? | ≥5 stage total breach? | Auto-escalated to CCB-Heavy? |
|---|---|---|---|---|---|
| 1 | 2 | 1 (CCBL-Stage1-M2 and CCBL-Stage1-M4 are different subsections within §methodology-deviations) | no | no | no |
| 2 | 3 | 1 (CCBL-001/002/003 each different sections) | no | no | no |
| 3 | 1 | 1 | no | no | no |
| 4 | 2 | 1 (CCBL-Stage4-S4-PLAN-PO and CCBL-Stage4-T-4-6 are different sections) | no | no | no |
| 5 (v0.1.8) | 1 | 1 (§7 is net-new section; no prior entry) | no | no | no |

## Suppression escape hatch usage (per pmp-ccb.md §Cap rules)

| Stage | Suppressed? | Reason |
|---|---|---|
| 1 | no | n/a |
| 2 | no | n/a |
| 3 | no | n/a |
| 4 | no | n/a |
| 5 (v0.1.8) | no | n/a |
| 1 (v0.1.9 M-4) | no | n/a |

## Project-level CCB statistics

<!-- Will be populated at ProjectClose. -->

- Total CCB-Light: 8 (CCBL-001 + CCBL-002 + CCBL-003 + CCBL-Stage3-001 + CCBL-Stage4-S4-PLAN-PO + CCBL-Stage4-T-4-6 + CCBL-Stage5-S1-D1 + CCBL-Stage1-v0.1.9-M4)
- Total CCB-Heavy: 0
- Most-revised sections: §4 daemon.py contract (1), payload-channel (1), plan-decomp-strategy (1)

## Cross-reference

- PROGRESS.md ## CCB Activity — current stage's open CCB-Light entries (resets at stage close)
- PROGRESS.md ## CCB-Heavy Pending — currently-open CCB-Heavy (cleared on CEO decision; transient)
- references/pmp-ccb.md — operational rules + 4-col Audit log file format authority
