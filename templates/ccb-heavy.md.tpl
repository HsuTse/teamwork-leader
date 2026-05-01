# CCB-Heavy Request

<!--
Authority: TeamLead drafts; CEO is sole approver (per design doc §3 RACI matrix + §8).
CCB-Heavy is required for any of:
- Charter material change
- Cross-stage scope shift
- ≥3 same-section OR ≥5 stage-total CCB-Light auto-escalation
- 2× cumulative project budget breach
- Multi-PM impact requiring re-baseline

Per references/pmp-ccb.md.

Once raised, PROGRESS.md ## CCB-Heavy Pending section is populated; cleared when CEO decides.
-->

## Metadata

- **Time raised**: <ISO-8601>
- **Stage when raised**: <N>
- **Origin**: <CCB-Light cap auto-escalation | budget circuit breaker | CEO request | PM-surfaced material issue>
- **CEO state**: <pending | approved | rejected>

## Material change description

<!-- What is materially changing? Be precise — Charter-level changes have downstream impact across stages, RAID, value hypothesis. -->

<one paragraph>

## Why this is CCB-Heavy (not CCB-Light)

<!-- Justify why this cannot be handled by in-stage CCB-Light. Cite cap rule, Charter scope, or budget threshold. -->

- [ ] Charter-level change (success criteria / constraints / overall goal)
- [ ] Cross-stage scope shift
- [ ] CCB-Light cap exceeded (≥3 same section OR ≥5 stage total) — see linked CCB-Light entries
- [ ] Budget breach (>100% per-stage with no recovery, or 2× cumulative)
- [ ] Multi-PM impact requiring re-baseline
- [ ] Other (specify): _______________

## Linked CCB-Light entries (if cap-driven)

<!-- If this CCB-Heavy was triggered by CCB-Light auto-escalation, cite the entries. -->

- <ISO-8601> | section: <X> | resolution: <Y>
- <ISO-8601> | section: <X> | resolution: <Y>
- <ISO-8601> | section: <X> | resolution: <Y>

## Proposed resolution

<!-- TeamLead drafts; CEO can revise / redirect / abort. -->

<multi-paragraph: revised Charter wording, revised stage decomposition, revised budget, etc.>

## Impact analysis

| Area | Impact | Required action |
|---|---|---|
| Charter | <yes/no/append> | <if yes — append vs in-place edit per design doc §5.5.1 immutability rule> |
| Stage decomposition | <which stages added/removed/changed> | <re-baseline budget per templates/budget-proposal.md.tpl> |
| RAID Register | <new [R] / [V] entries> | <add to PROGRESS.md ## RAID Register> |
| Value Hypothesis | <changed/unchanged> | <update [V] entries; reset realized status to pending> |
| Budget | <delta in kT> | <revise per-stage baseline; CEO approval required> |
| Active PMs | <which PMs affected> | <may require Ad-hoc PM activation> |
| Tasks/code | <which tasks orphaned/added> | <RD PM handles tasks.md migration> |

## RAID delta proposed

**New entries** (will be added to PROGRESS.md ## RAID Register on approve):
- [R] <new risk this CCB introduces>
- [A] <new assumption from this CCB>
- [V] <new or revised value criterion>

**Closed entries** (will be marked closed):
- [I] <issue resolved by this CCB>

## CEO decision

<!-- CCB-Heavy uses the extraordinary CEO_Gate verb set per references/pmp-ccb.md §CCB-Heavy step 6:
     - approve  → resume Stage with new spec
     - reject   → continue with old spec (no PROGRESS.md ## Charter / Budget changes)
     - defer    → freeze stage; CEO will re-decide later

     This is DIFFERENT from CEO_Gate_N's 6-verb set (approve / revise_next / revise_charter / redirect / pause / abort).
     If CEO wants to redirect or abort the project entirely, that happens at the next CEO_Gate_N, not via this CCB-Heavy form. -->

- Verb: <approve | reject | defer>
- Decided at: <ISO-8601>
- Notes: <CEO's rationale; any conditions on approval>

## Post-decision actions (TeamLead)

**On `approve`**:
- [ ] Update PROGRESS.md ## Charter (append-only per §5.5.1)
- [ ] Update PROGRESS.md ## Budget Baseline (re-baseline if budget changed)
- [ ] Update PROGRESS.md ## RAID Register with delta
- [ ] Clear PROGRESS.md ## CCB-Heavy Pending section
- [ ] Notify all activated PMs of revised Charter / budget
- [ ] Append CCB-Heavy event detail block to <project>/docs/decisions/ccb-log.md §Heavy events (per templates/ccb-log.md.tpl)
- [ ] Resume next dispatch / state transition

**On `reject`**:
- [ ] Clear PROGRESS.md ## CCB-Heavy Pending section
- [ ] Append CCB-Heavy event to <project>/docs/decisions/ccb-log.md §Heavy events with `verb: reject`
- [ ] No Charter / Budget / RAID changes
- [ ] Resume Stage with old spec; notify triggering PM

**On `defer`**:
- [ ] Update PROGRESS.md ## State to `ESCALATED` (per references/progress-md-schema.md state diagram)
- [ ] Keep PROGRESS.md ## CCB-Heavy Pending populated (do NOT clear)
- [ ] Surface to CEO at next CEO_Gate via AskUserQuestion: "CCB-Heavy still deferred — re-decide?"
- [ ] No further dispatches until CEO returns approve/reject
