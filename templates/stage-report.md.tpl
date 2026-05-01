# StageReport: Stage <N> — <stage-name>

<!--
Per design doc §5.2 + references/progress-md-schema.md §Stage History.
TeamLead drafts this at REPORTING state; CEO reviews at CEO_Gate_N.
After CEO approve, this content is appended to PROGRESS.md ## Stage History under heading `### Stage N (closed YYYY-MM-DD)`.
-->

## Scope

<!-- Stage scope as authored at CEO_Gate_(N-1) BudgetProposal / WaveRefinement.
     Material change between stage open and close → CCB-Heavy (per design doc §5.5.1). -->

<one paragraph: what this stage delivered>

## PMs activated

| PM | Role this stage |
|---|---|
| PO | <e.g., spec drafting + CCB-Light triage> |
| RD | <e.g., implementation T-N-1 through T-N-7> |
| QA | <e.g., 3 gates + cross-verification of RD test claims> |
| UX | <e.g., Mezzanine compliance + UI-only items> |
| <Ad-hoc> | <if activated> |

## Dispatches summary

| Dispatch # | PM | Task | Outcome | Verified by TeamLead |
|---|---|---|---|---|
| 1 | PO | Draft spec §3.2 | SUCCESS | [TRUSTED] artifact + verify_evidence sample |
| 2 | RD | T-N-1 implement schema | SUCCESS | [TRUSTED] diff + 1/3 verify cmd re-run |
| ... | ... | ... | ... | ... |

## Gates

| Gate | Verdict | DoD status | Root cause (if not PASS) | Action |
|---|---|---|---|---|
| Forward | PASS | met | — | proceed |
| Human | PARTIAL | partial | spec_ambiguity | CCB-Light → PO |
| Requirement | PASS | met | — | proceed |

<!-- Detailed classifier outputs preserved in references/three-gates.md format if any non-PASS verdicts. -->

## Value Realized vs Hypothesis

<!-- Per references/value-driven.md §StageReport Value Realized vs Hypothesis section. -->

| Dispatch | Value Hypothesis | Value Realized | DoD Status |
|---|---|---|---|
| <PM> <task> | "<expected outcome>" | "<observed outcome>" | <met|partial|missed> |
| ... | ... | ... | ... |

## CCB Activity (this stage)

<!-- Roll-up of PROGRESS.md ## CCB Activity section before reset.
     All Light entries must be applied or rejected before stage close; lingering open entries auto-escalate to CCB-Heavy per references/pmp-ccb.md cap rules.
     The 4-col canonical Light entries are also appended by PO PM to <project>/docs/decisions/ccb-log.md per templates/ccb-log.md.tpl. -->

| Time | Section | Requested by | Spec impact | Resolution |
|---|---|---|---|---|
| <ISO-8601> | <PROGRESS.md anchor> | <PM> | <one-line> | <applied|rejected> |

## RAID delta (this stage)

<!-- New / closed / changed entries this stage. Full RAID Register lives in PROGRESS.md ## RAID Register. -->

**New**:
- [R] <new risk introduced this stage>
- [I] <new issue raised>
- [V] <value criterion declared>

**Closed**:
- [I] <issue resolved>
- [D] <dependency resolved>

**Severity changed**:
- [R] <risk> | <old severity> → <new severity> | reason: <one-line>

## Token tally

| PM | kT used | vs baseline | breach? |
|---|---|---|---|
| PO | <X> | <baseline> | no |
| RD | <X> | <baseline> | <no | 80% warned | 100% breached> |
| QA | <X> | <baseline> | no |
| UX | <X> | <baseline> | no |
| Gate_Requirement | <X> | per-run cost | n/a |
| **Total stage** | <X> | <stage baseline> | <no | warned | breached> |

**Cumulative project**: <X> kT vs <2 * project baseline> ceiling.

## WaveRefinement (next stage)

<!-- Per design doc §10 rolling-wave: refine next stage's scope based on what was learned this stage.
     If decomposition changes Charter materially → CCB-Heavy required. -->

**Next stage**: Stage <N+1> — <name>
**Scope adjustment**: <none | refined | requires CCB-Heavy>
**New tasks identified**: <list>
**Dependencies surfaced**: <list>

## Self-Audit (this stage)

<!-- Mirror of PROGRESS.md ## Self-Audit / ### Stage N entry, embedded here for stage-archive completeness. -->

- I verified <X> of <Y> PM claims this stage.
- Unverified items: <list with reason>
- Highest-risk claim selected: "<claim>" by <PM>
- Lowest-confidence claim selected: "<claim>" by <PM>
- Sampling rotation: <which cross-PM verifications ran>

## CEO_Gate_<N> verbs available

- `approve` — close this stage, proceed to next
- `revise_next` — adjust next-stage plan before proceeding
- `revise_charter` — material change → CCB-Heavy (delays close)
- `redirect` — point project at different goal (Charter-level)
- `pause` — halt for CEO investigation
- `abort` — terminate project
