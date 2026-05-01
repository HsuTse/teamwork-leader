# PMP CCB — Change Control Board Tracks

> **Source of truth**: design doc v3 §8. This file operationalizes the rule.

## Two tracks

### CCB-Light (within-session, scoped clarification)

**Triggers** (any one):

- Spec wording is ambiguous, but PO can clarify in <30 lines without scope/budget change
- New requirement that fits within current stage scope and budget
- Naming / formatting standardization
- **`verify_policy` single-tier change** (e.g., `default → broad` or `default → minimal-per-dispatch`; per `templates/budget-proposal.md.tpl` §`verify_policy` tier explanation)
- Rule 0 threshold adjustment within ±2 of initial value (per `references/anti-rubber-stamp.md` §Threshold rationale)
- **KMR proxy threshold adjustment within ±2 of initial value** (Phase 3 — per `references/stage-runbook.md` §EXECUTING step 7a threshold rationale)
- **Trust_tier promotion / demotion criteria adjustment within ±2 of seed values** (Phase 3 — per `references/anti-rubber-stamp.md` Rule 0.5 §Tier promotion / demotion table)
- **selector_score coefficient adjustment within ±0.5 of seed values** (Phase 2 T5 / Phase 3 carry-over — per `references/stage-runbook.md` §PLAN_AUDIT step 3 candidate-set mode formula)

**Process**:

1. Triggering PM raises CCB-Light request to TeamLead via `ccb_requests` field of return payload (track: `light`)
2. TeamLead dispatches PO PM with the clarification scope
3. PO updates `<project>/docs/<file>.md` with marker:
   ```html
   <!-- ccb: clarify YYYY-MM-DD — <one-line rationale> -->
   ```
4. PO **also** appends a row to `<project>/docs/decisions/ccb-log.md`:
   ```
   | YYYY-MM-DD | <doc-anchor> | <one-line rationale> | <line range: original→new> |
   ```
5. TeamLead acks (no CEO involvement for Light)
6. Original triggering PM is re-dispatched with updated spec

### CCB-Heavy (cross-session or scope-changing)

**Triggers** (any one):

- Scope change: new feature not in original Charter
- Budget change: time / milestone / retry-cap revision
- Cross-session work: spec rewrite spanning multiple sessions
- Spec contradiction with shipped code (migration needed)
- **Risk-driven change** (mitigation requires shift)
- **Regulatory / compliance-driven change** (external standards)
- **CCB-Light cap escalation** (see §Cap rules below)
- **`verify_policy` cross-tier jump** (e.g., `broad → minimal-per-dispatch`; weakens anti-rubber-stamp Rule 2 — treat as risk-driven change)
- Rule 0 threshold adjustment beyond ±2 of initial value (more aggressive escalation policy change)
- **KMR proxy formula structure change** (Phase 3 — e.g., switching `max(...)` to weighted sum, or adding/removing input terms)
- **Trust_tier system structural change** (Phase 3 — e.g., adding new tier, changing rolling window from 3 stages, removing anti-gaming triggers)
- **Phase 3 kill-switch activation** (`trust_tier_mode: disabled` OR `kmr_mode: disabled`) — disabling a deployed verification mechanism is risk-driven; requires CCB-Heavy CR documenting why Phase 3 features are being rolled back

**Process**:

1. Triggering PM raises CCB-Heavy request via `ccb_requests` (track: `heavy`)
2. TeamLead pauses Stage; logs request in `PROGRESS.md ## CCB-Heavy Pending` section
3. TeamLead dispatches PO PM to draft Change Request (CR) using `templates/ccb-heavy.md.tpl`
4. TeamLead recalculates budget impact (knobs + per-stage baseline)
5. **CEO_Gate (extraordinary)** — TeamLead surfaces CR + budget impact to CEO via AskUserQuestion
6. CEO decision: `approve` / `reject` / `defer`
7. Approved → resume Stage with new spec; rejected → continue with old spec; deferred → freeze stage

## Cap rules (auto-escalation triggers)

These prevent silent scope creep masquerading as Light clarifications:

| Threshold | Action |
|---|---|
| ≥3 CCB-Light entries within one stage touching **same doc section** | TeamLead auto-escalates to CCB-Heavy |
| ≥5 CCB-Light entries within one stage **total** | TeamLead surfaces to CEO as potential scope creep (informational, but logged) |

**Suppression escape hatch**: TeamLead may suppress an auto-escalation **once per stage** with documented reason in `ccb-log.md`. After 3 dogfood projects, calibrate or remove this discipline.

## Section identification (counting mechanism)

For "same doc section" counting:
- Section identifier = doc-anchor field in `ccb-log.md` row (PO extracts heading-slug from doc target at CCB-Light time)
- Counting = grep `ccb-log.md` for stage-tagged rows with matching section-anchor field
- Stale-anchor false positives accepted as MED risk (logged here for transparency)

## Audit log file (`<project>/docs/decisions/ccb-log.md`)

Format (use `templates/ccb-log.md.tpl`):

```markdown
# CCB Audit Log

## Stage 1

| Date | Section | Rationale | Original→New |
|---|---|---|---|
| 2026-05-02 | order-validation/payload-shape | Clarify SKU format expectation | L42-45 → L42-50 |

## Stage 2

| Date | Section | Rationale | Original→New |
|---|---|---|---|
| ...
```

**Light entries are PO-only**. RD/QA/UX may **request** CCB-Light, but only PO writes the spec change + log row.
