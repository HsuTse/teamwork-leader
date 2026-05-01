# CCB Audit Log — <PROJECT_NAME>

<!--
Canonical location: <project>/docs/decisions/ccb-log.md
Authority for format: references/pmp-ccb.md §Audit log file (4-col Light entries) + §CCB-Heavy.

Two sections:
1. Per-stage Light tables (4-col, PO-only writes)
2. Heavy events sub-section (post-CEO-decision detail blocks; TeamLead writes after CEO decides)

Stale guard (mtime + sha256) runs before every append.
-->

## Light entries (per stage, 4-col format per pmp-ccb.md §Audit log file)

<!-- PO appends a row each time a CCB-Light is applied (per pmp-ccb.md §CCB-Light step 4).
     Section identifier (column 2) = doc-anchor heading slug — used for "same section" cap counting (per pmp-ccb.md §Section identification). -->

### Stage 1

| Date | Section | Rationale | Original→New |
|---|---|---|---|
| 2026-05-02 | order-validation/payload-shape | Clarify SKU format expectation | L42-45 → L42-50 |
| 2026-05-03 | order-validation/error-codes | Add missing error code 4032 | L88 → L88-89 |

### Stage 2

| Date | Section | Rationale | Original→New |
|---|---|---|---|
| ... | ... | ... | ... |

## Heavy events

<!-- TeamLead appends a detail block here after CEO decides on a CCB-Heavy.
     Pre-decision tracking lives in PROGRESS.md ## CCB-Heavy Pending (transient, cleared on decision).
     Format mirrors templates/ccb-heavy.md.tpl §CEO decision + §Post-decision actions. -->

### Stage 1, CCB-Heavy #1 (decided <YYYY-MM-DD>)

- **Origin**: <CCB-Light cap auto-escalation | budget breach | Charter material change | other>
- **Linked Light entries** (if cap-driven): Stage 1 rows 1, 2 (above)
- **Material change description**: <one paragraph>
- **CEO verb**: <approve | reject | defer>
- **CEO rationale**: <one paragraph>
- **Post-decision actions taken**:
  - [x] PROGRESS.md ## Charter appended (append-only per §5.5.1)
  - [x] PROGRESS.md ## Budget Baseline re-issued (per templates/budget-proposal.md.tpl)
  - [x] PROGRESS.md ## RAID Register delta applied
  - [x] All activated PMs notified
- **RAID delta applied**: new [R] <risk>, new [V] <criterion>, closed [I] <issue>

### Stage 2, CCB-Heavy #1 (decided <YYYY-MM-DD>)

<as above>

## Cap-rule audit (per stage, derived from Light tables above)

<!-- TeamLead can grep the Light tables to verify cap-rule trigger conditions before allowing a new Light. -->

| Stage | Light count | Same-section max | ≥3 same-section breach? | ≥5 stage total breach? | Auto-escalated to CCB-Heavy? |
|---|---|---|---|---|---|
| 1 | <N> | <N at most-affected section> | <yes/no> | <yes/no> | <yes/no, which Heavy event> |
| 2 | <N> | ... | ... | ... | ... |

## Suppression escape hatch usage (per pmp-ccb.md §Cap rules)

<!-- TeamLead may suppress an auto-escalation once per stage with documented reason.
     Track usage here to enable post-project calibration (after 3 dogfood projects). -->

| Stage | Suppressed? | Reason |
|---|---|---|
| 1 | <yes/no> | <if yes — one-line rationale> |
| 2 | <yes/no> | ... |

## Project-level CCB statistics

<!-- Populated at ProjectClose (per templates/project-close.md.tpl §Step 2 failure-mode taxonomy). -->

- Total CCB-Light: <N>
- Total CCB-Heavy: <N>
- CCB-Heavy origin breakdown:
  - Cap auto-escalation: <N>
  - Budget breach: <N>
  - Charter material change: <N>
  - Other: <N>
- Most-revised PROGRESS.md sections (top 3, by Light section column): <list>
- Stages with cap-rule trigger: <list>

## Cross-reference

- PROGRESS.md ## CCB Activity — current stage's open CCB-Light entries (resets at stage close)
- PROGRESS.md ## CCB-Heavy Pending — currently-open CCB-Heavy (cleared on CEO decision; transient)
- StageReport ## CCB Activity (per stage) — stage-level rollup, lives in PROGRESS.md ## Stage History
- references/pmp-ccb.md — operational rules + 4-col Audit log file format authority
- references/pmp-lessons-learned.md §Step 2 failure-mode taxonomy — `scope_creep` count derives partially from this log
