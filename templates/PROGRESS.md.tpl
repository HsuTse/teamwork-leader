# Project: <PROJECT_NAME>

<!--
Schema authority: skills/teamwork-leader-workflow/references/progress-md-schema.md
TeamLead is the SOLE WRITER of this file. PMs return JSON payloads; TeamLead serializes.
Stale guard (mtime + sha256) runs immediately before every write.
Hard ceiling: 2000 lines. Archival rules per §11.6.
-->

## Schema decision: <migrate|coexist|side-file> at <YYYY-MM-DD>

<!-- Only present if PROGRESS.md existed before /teamwork-leader was invoked.
     See references/schema-migration.md for option semantics.
     Delete this section if project was created fresh by TeamLead. -->

## Charter

**Goal**: <one paragraph from CEO_Gate_0 — what business outcome this project delivers>

**Success criteria**:
- <observable criterion 1>
- <observable criterion 2>
- <observable criterion 3>

**Constraints**:
- <constraint 1 — e.g., timeline, budget, technology, scope>
- <constraint 2>

**Charter immutability**: per design doc §5.5.1, this section is APPENDED ONLY (no in-place edits) after CEO_Gate_0 sign-off. Material change → CCB-Heavy.

## Budget Baseline

**Knobs** (from BudgetProposal at CEO_Gate_0):
- Stage count: <N>
- Per-stage kT baseline: <X> kT
- Total project ceiling: <X * N * 2> kT (2× cumulative trigger)
- 80% per-stage warning threshold: <0.8 * X> kT
- 100% per-stage hard breach threshold: <X> kT

**Circuit breaker rules** (per design doc §9.1):
- 80% per-stage → warn CEO at next CEO_Gate
- 100% per-stage → halt; surface to CEO immediately
- 2× cumulative project → halt; CCB-Heavy required to continue

## Active Stage: <stage-name>
## State: <PLANNING | PLAN_AUDIT | EXECUTING | GATING | REPORTING | AWAITING_CEO | ESCALATED | COMPLETED | ABORTED>
## Last Action: <ISO-8601 timestamp> [TRUSTED|CLAIMED] — <one-line Insight>

<!-- Last Action is OVERWRITTEN on each TeamLead write (not appended).
     [TRUSTED] = TeamLead verified per anti-rubber-stamp §3.3
     [CLAIMED] = PM reported but not yet verified (must become [TRUSTED] before stage close) -->

## RAID Register

<!-- Per references/progress-md-schema.md §RAID Register and design doc §11.2.
     Severity / status fields mandatory per Round 2 PMP MED-3. -->

- [R] <risk> | likelihood: <low|med|high> | impact: <low|med|high> | mitigation: <plan> | status: <open|mitigating|closed> | owner: <PM> | review_date: <YYYY-MM-DD>
- [A] <assumption> | validates if: <criterion> | validation_status: <pending|validated|invalidated> | validated_at: <YYYY-MM-DD>
- [I] <issue> | severity: <low|med|high> | owner: <PM> | next action: <step> | status: <open|closed>
- [D] <dependency> | external: <y|n> | blockedBy: <thing> | status: <open|resolved>
- [V] <value-criterion> | hypothesis: <expected outcome> | realized: <pending|yes|partial|no> | measured_by: <evidence>

## Stage History

<!-- Append-only. Each stage gets its full StageReport content per templates/stage-report.md.tpl.
     When PROGRESS.md hits 2000 lines, oldest stage moves to docs/stage-archives/stage-N.md
     and is replaced here with a one-line back-reference.
     Empty until first stage closes — TeamLead populates `### Stage 1 (closed YYYY-MM-DD)` at first CEO_Gate_1 approve. -->

## CCB Activity

<!-- Rolling list of CCB-Light entries opened during current stage.
     Reset at stage close; PO archives row to <project>/docs/decisions/ccb-log.md per templates/ccb-log.md.tpl
     (canonical path per references/pmp-ccb.md §Audit log file).
     All entries must be applied or rejected before stage close; lingering open entries auto-escalate to CCB-Heavy.
     Cap rule: ≥3 same section / ≥5 stage total → auto-escalate (see references/pmp-ccb.md §Cap rules). -->

- <YYYY-MM-DDThh:mm> | section: <PROGRESS.md anchor> | requested-by: <PM> | spec-impact: <one-line> | resolution: <open|applied|rejected>

## CCB-Heavy Pending

<!-- Only present when CCB-Heavy raised; cleared when CEO decides.
     Per references/pmp-ccb.md and design doc §8. -->

## Self-Audit

<!-- TeamLead's stage-by-stage record of verified vs unverified PM claims.
     Per references/anti-rubber-stamp.md §Self-Audit format and design doc §3.3. -->

### Stage 1
- I verified <X> of <Y> PM claims this stage.
- Unverified items (allowed mid-stage only): <list>
- Highest-risk claim selected for verification: "<claim>" by <PM>
- Lowest-confidence claim selected: "<claim>" by <PM>
- Sampling rotation: <which cross-PM verifications ran this stage>

## Exception

<!-- Only present when active exception; cleared when escalation resolved.
     Per references/progress-md-schema.md §Exception and design doc §11.10. -->

## Lessons Learned

<!-- Only present at ProjectClose.
     Populated per templates/project-close.md.tpl and references/pmp-lessons-learned.md. -->
