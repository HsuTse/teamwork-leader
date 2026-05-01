# PMP WBS — Rolling-Wave Decomposition

> **Source of truth**: design doc v3 §5.5. This file operationalizes the rule.

## Rolling-wave depth rule

| Stage offset (relative to current Stage N) | Plan depth | Verify clauses required? |
|---|---|---|
| Current Stage (N) | **Task-level** | **YES** — every task has a verify command + expected output OR red-green pair |
| N+1 | **Deliverable-level** | NO — describe end-user-visible artifacts only |
| N+2 onward | **Milestone-level** (one-line) | NO — phase boundary description only |

## CEO_Gate_0 Charter requirements

- Milestone-level plan for **ALL** stages (so CEO sees overall arc)
- Task-level plan for **Stage_1 only**
- Stage_2 onward at deliverable level (or milestone if too far out)

## WaveRefinement (between StageReport and CEO_Gate_N)

At each stage close, TeamLead refines Stage_(N+1):
- Expand from milestone-level (or deliverable-level) → task-level
- Surface refined plan at CEO_Gate_N as **informational** (per design doc §5.5.1)
- Stage_(N+1) plan only "active" after CEO `approve` verb

## Decidability test (resolves Round 2 Arch MED-5)

Use these criteria when classifying a unit of work:

### Task-level

- Single PM, single dispatch
- ≤1 day wall clock
- Has a concrete acceptance test command (or red-green test pair)
- Example: "Implement `validateOrderPayload()` function with unit tests covering invalid SKU, negative quantity, missing buyer"

### Deliverable-level

- 2-5 tasks
- Single PM owns
- Ships an end-user-visible artifact
- Example: "Order validation feature (v1)"

### Milestone-level

- Phase boundary
- May span multiple PMs / deliverables
- One-line description
- Example: "Stage 2: Backend validation framework"

### Boundary cases

- "Build login form" — task-level if scope=single page; deliverable-level if scope=login + signup + reset
- "Migrate auth module" — deliverable-level if same architecture; milestone-level if architectural rewrite

If two PMs disagree on classification, TeamLead is the tiebreaker. Persistent disagreement → CCB-Light to refine spec.

## Charter immutability (per design doc §5.5.1)

WaveRefinement may **only** refine N+1 within the milestone-level Charter scope.

Any change to:
- Milestone count
- Milestone goal / scope
- Project end-state
- Budget baseline (knobs in §9.1)

→ requires **CCB-Heavy**, NOT WaveRefinement.

**Tripwire**: if WaveRefinement's deliverable-level plan diverges from the original milestone description (semantic drift), TeamLead halts WaveRefinement, raises CCB-Heavy, surfaces to CEO.
