# Value-Driven — Hypothesis & Definition of Done

> **Source of truth**: design doc v3 §3.2, §6.1, §11.2 [V] entries. This file operationalizes Value-Driven principle.

Per user's PMP requirement (Q3-3 Value-Driven). Every dispatch declares value; every stage closes with value check.

## Value Hypothesis (per dispatch, mandatory)

Every PM dispatch's intake header includes:

```
## Value Hypothesis (mandatory)

What business outcome should this dispatch enable? How will it be measured?
<TeamLead injects expected value statement>
```

PM may **refine** wording on return; **must reaffirm** if accepted as-is.

### Acceptance criteria for "good" Value Hypothesis

A good hypothesis:
- States an **observable outcome** (not just an activity)
- Specifies **how it will be measured** (test, metric, user behavior)
- Connects to a project-level Charter goal

### Rejected examples (return BLOCKED)

- "enabled feature X" — no observable outcome
- "improved code quality" — no measurement
- "happy users" — no metric
- "as per spec" — circular (spec doesn't own value)

### Accepted examples

- "Order validation reduces invalid-payload error rate by 80% in staging benchmarks (measured: errors per 1000 orders)"
- "Login form supports keyboard-only navigation (measured: Playwright a11y check passes)"
- "Catalog import handles 10K SKUs in <30s (measured: import duration test)"

## Value Realized (per dispatch return + StageReport)

PM return contract field `value_realized`:

- **During Stage** (mid-dispatch): `"pending Stage close"` is allowed if value can only be observed end-to-end
- **At Stage close**: must be replaced with observable evidence: `"benchmark run shows 84% reduction (errors/1000: 12 → 1.9)"` etc.

## Definition of Done (per dispatch, mandatory)

Every PM dispatch's intake header includes:

```
## Definition of Done (mandatory)

What observable state == "this dispatch's work is complete"?
<TeamLead injects DoD criteria>
```

PM self-reports `dod_status: met | partial | missed` in return.

### `dod_status` semantics

- `met` — all DoD criteria observably satisfied; `dod_evidence` cites observable state
- `partial` — some criteria met, some not; `dod_evidence` lists gap; **forces CCB-Light entry**
- `missed` — DoD not achieved; `dod_evidence` describes what's missing; **forces CCB-Light entry**

## DoD enforcement at gate close (per Round 2 PMP NH1)

Gate classifier output (per `three-gates.md`) includes `dod_status` field. Gate verdict alone is insufficient — gate must explicitly check whether the DoD was met.

CEO_Gate_N AskUserQuestion **must include**:
"DoD met for this stage: [yes/partial/no]"

PARTIAL/MISSED → forced CCB-Light entry. Cannot proceed via `approve` verb until resolved.

## [V] entries in RAID Register

Per design doc §11.2, RAID Register includes a fifth type:

```markdown
- [V] <value-criterion> | hypothesis: <expected outcome> | realized: pending/yes/partial/no | measured_by: <evidence>
```

[V] entries link directly to dispatches' `value_hypothesis` field. Each stage's [V] entries are aggregated at ProjectClose into Value Realization summary (per `pmp-lessons-learned.md` Step 3).

## StageReport `## Value Realized vs Hypothesis` section

Each StageReport includes:

```markdown
## Value Realized vs Hypothesis

| Dispatch | Value Hypothesis | Value Realized | DoD Status |
|---|---|---|---|
| PO PM Stage 2 spec drafting | "Schema validates 100% of enumerated edge cases" | "Pending — RD test pending" | met |
| RD PM Stage 2 implementation | "Schema rejects 100% invalid payloads in test" | "98% — 1 edge case escaped" | partial |
| QA PM Stage 2 gates | "All gates pass" | "yes" | met |
```

PARTIAL rows trigger CCB-Light entries (already counted in §CCB Activity section).

## ProjectClose Value Realization

Per `pmp-lessons-learned.md` Step 3, all stages' [V] entries aggregated:

```markdown
### Value Realization

| Value Criterion | Hypothesis | Realized | Evidence |
|---|---|---|---|
| Order validation error rate | 80% reduction | yes | benchmark: 84% reduction |
| Catalog import perf | <30s for 10K | yes | test: 22s |
| Login a11y | keyboard-only nav | partial | Playwright passes; subjective UX feedback pending |
```

CEO sees this at CEO_Gate_Final.

## Why this matters (Value-Driven principle)

User's PMP requirement: project consumption (tokens, retries, gates passed) is NOT the same as project outcome (value delivered).

A stage can:
- Pass all 3 gates (Forward + Human + Requirement)
- Be on budget
- Have all DoDs `met`

…and still deliver near-zero value if the original Charter scoping was off.

Value-Driven adds the **outcome question** as a forced check at gate time. CEO_Gate_N asks "DoD met for stage" before `approve` is accepted. ProjectClose surfaces aggregate Value Realization for honest project-level assessment.
