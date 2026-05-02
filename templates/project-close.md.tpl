# Project Close — <PROJECT_NAME>

<!--
Authored at ProjectClose state, after final Stage gates pass.
Per references/pmp-lessons-learned.md (7-step protocol) + design doc §5.4.

This template guides TeamLead through the 7-step ProjectClose protocol.
Each step has a sub-section below. Mark steps complete as TeamLead progresses.
-->

## Step 1 — Per-PM lessons-learned dispatch

<!-- TeamLead dispatches each activated PM with the prompt in references/pmp-lessons-learned.md §Step 1. -->

- [ ] PO PM dispatched — return received: <yes/no>
- [ ] RD PM dispatched — return received: <yes/no>
- [ ] QA PM dispatched — return received: <yes/no>
- [ ] UX PM dispatched — return received: <yes/no>
- [ ] Ad-hoc PM(s) dispatched (if any): <list>

## Step 2 — TeamLead consolidation

<!-- Aggregate returned lessons into PROGRESS.md ## Lessons Learned section.
     Format per references/pmp-lessons-learned.md §Step 2. -->

### What worked
- (PO) <lesson> — <Stage / evidence>
- (RD) <lesson> — <Stage / evidence>
- (QA) <lesson> — <Stage / evidence>
- (UX) <lesson> — <Stage / evidence>

### What didn't work
- (<PM>) <lesson> — <Stage / evidence>

### What I'd do differently
- (<PM>) <lesson> — <Stage / evidence>

### Failure-mode taxonomy aggregate

<!-- Count instances per label across all stages. Per references/pmp-lessons-learned.md §Step 1 taxonomy. -->

| Failure mode | Count | Stages |
|---|---|---|
| spec_drift | <N> | <list> |
| scope_creep | <N> | <list> |
| gate_routing_error | <N> | <list> |
| value_hypothesis_unmet | <N> | <list> |
| dod_drift | <N> | <list> |
| over-budget | <N> | <list> |
| branch-discipline-violation | <N> | <list> |
| cleanup-oversight | <N> | <list> |
| cross-pm-verification-gap | <N> | <list> |
| other | <N> | <list with specify-text> |

### Self-Audit aggregate

- TeamLead verified <X>/<Y> PM claims across <N> stages
- Verification-gap patterns observed: <list>
- Sampling-rotation distribution: <which PM got cross-verified each stage>

## Step 3 — Value Realization summary

<!-- Aggregate all [V] RAID entries from all stages.
     Per references/value-driven.md §ProjectClose Value Realization + references/pmp-lessons-learned.md §Step 3. -->

| Value Criterion | Hypothesis | Realized | Evidence |
|---|---|---|---|
| <criterion> | <expected outcome> | <yes/partial/no> | <citation: benchmark / test / user observation> |

**Aggregate**: <X yes / Y partial / Z no> out of <total> declared value criteria.

## Step 4 — MemoryEntry draft

<!-- Draft `~/.claude/projects/<encoded-home>/memory/project_<slug>.md` using the canonical template
     defined in references/pmp-lessons-learned.md §Step 4 (TeamLead Reads that file before drafting).
     `<encoded-home>` is Claude Code's URL-encoded form of $HOME ($HOME with `/` → `-`,
     e.g. `/Users/alice` → `-Users-alice`); TeamLead resolves at runtime.
     Place the drafted content below; CEO reviews at Step 5. -->

<!-- TeamLead inserts drafted MemoryEntry content here, conforming to the canonical template. -->

## Step 5 — MemoryEntry CEO review

- [ ] Surfaced draft to CEO via AskUserQuestion
- [ ] CEO decision: <approve append | edit | skip>
- [ ] If approved: written to `~/.claude/projects/<encoded-home>/memory/project_<slug>.md`
- [ ] If approved: index line appended to `~/.claude/projects/<encoded-home>/memory/MEMORY.md` under `## Projects`:
  ```markdown
  - [<Project Name>](project_<slug>.md) — <one-line description>
  ```
- [ ] Stale guard verified before MEMORY.md append (per references/pmp-lessons-learned.md §Step 5)

## Step 6 — CleanupGate

<!-- TeamLead dispatches Sonnet with plugin's cleanup discipline embedded verbatim + session-start ISO-8601 timestamp.
     Project's CLAUDE.md (if present) overrides plugin defaults per Claude Code standard precedence.
     Per references/pmp-lessons-learned.md §Step 6. -->

- [ ] Sonnet dispatched with cleanup rule + session-start timestamp
- [ ] Sonnet enumerated untracked/temp artifacts: <count>
- [ ] TeamLead surfaced deletion proposals to CEO **per item**
- [ ] CEO approved deletions: <list>
- [ ] CEO declined deletions (preserved): <list>
- [ ] Pre-existing artifacts (older than session start) retained without deletion proposal

## Step 7 — CEO_Gate_Final

- [ ] AskUserQuestion: "Project complete? Sign off?"
- [ ] CEO verb: <approve | pause | abort>
- [ ] If approve:
  - [ ] PROGRESS.md `## State` set to `COMPLETED`
  - [ ] Final timestamp logged
  - [ ] Project archived (PROGRESS.md retained as record)
- [ ] If pause: TeamLead awaits CEO further direction
- [ ] If abort: PROGRESS.md `## State` set to `ABORTED`, reason logged in `## Exception`

## Token tally (final)

| Category | kT used | vs baseline |
|---|---|---|
| All PM dispatches | <X> | <baseline> |
| All step-reviews (Sonnet) | <X> | <baseline> |
| All plan audits (Opus) | <X> | <baseline> |
| Gate_Forward (all stages) | <X> | <baseline> |
| Gate_Human (all stages) | <X> | <baseline> |
| Gate_Requirement (all runs) | <X> | <baseline> |
| TeamLead orchestration | <X> | <baseline> |
| **Project total** | <X> | <project baseline> |

**Variance**: <under | on | over> baseline by <X>%.
