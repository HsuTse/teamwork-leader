# CCB-Light Request

<!--
Authority: PO PM (per design doc §3 RACI matrix).
Used for in-stage spec ambiguity / spec_gap / minor scope refinement that does NOT change Charter.
Per references/pmp-ccb.md.

Cap rule (per design doc §8): ≥3 same section / ≥5 stage total → auto-escalate to CCB-Heavy.

After resolution, this entry rolls up to PROGRESS.md ## CCB Activity section.
At stage close, PO appends a row to <project>/docs/decisions/ccb-log.md per templates/ccb-log.md.tpl.

CCB-Light is TeamLead-acked only — no CEO involvement (per references/pmp-ccb.md step 5).
-->

## Metadata

- **Time raised**: <ISO-8601>
- **Stage**: <N>
- **Section affected**: <PROGRESS.md ## anchor or docs/spec section>
- **Requested by**: <PM that surfaced it>
- **Resolves to**: <open | applied | rejected>

## Trigger

<!-- What surfaced this CCB-Light? Cite the dispatch / RAID entry / gate verdict. -->

- Source: <dispatch-N PM / Gate_Forward classifier / RAID [I] / RD blocker / etc.>
- Description: <one paragraph>

## Spec impact

<!-- One-line summary of what changes in the spec / Charter / scope. Non-Charter ONLY. -->

<one-line>

## Proposed resolution

<!-- PO PM's proposed clarification, scope refinement, or wording fix. -->

<one paragraph>

## Affected artifacts

- [ ] <docs/spec.md §X.Y> — wording change
- [ ] <PROGRESS.md ## RAID Register> — close [A] or [I] entry
- [ ] <tasks.md T-N-X> — task scope adjusted
- [ ] <other>

## Verification

<!-- How will we know the resolution worked? Per references/value-driven.md observable-outcome principle. -->

- Verify: <test name | command | observable behavior>

## CEO awareness

<!-- CCB-Light defaults to no-CEO-involvement per pmp-ccb.md step 5 (TeamLead acks only).
     CEO sees aggregated rollup in StageReport ## CCB Activity table at CEO_Gate_N.
     Exception: if this Light touches a high-severity RAID-R entry, TeamLead may surface to CEO via AskUserQuestion — note rationale here. -->

- Surface to CEO before applying? <no (default) | yes — rationale: high-risk RAID-R entry "<R-N>" affected>

## Anti-cap-creep check

<!-- Before applying, check whether this CCB-Light pushes the stage near the cap. -->

- Same section CCB-Light count this stage (incl. this entry): <N>
- Total CCB-Light count this stage (incl. this entry): <N>
- ≥3 same section OR ≥5 stage total? <yes → ESCALATE to CCB-Heavy | no → proceed>

## Resolution log

- Applied at: <ISO-8601>
- Outcome: <one-line>
- Insight: <if non-obvious learning>
