# Plan-Audit Rubric — Rule 7 Anti-Self-Skip

> **Scope**: applies to TeamLead's plugin-internal Opus reviewer dispatched during `§PLAN_AUDIT` via `Agent` tool with `model: opus`. Does NOT apply to the host `/opus-review final` skill.

This file is the authoritative procedure for Rule 7. `references/anti-rubber-stamp.md` §Rule 7 describes the design intent; this file provides the operational verbatim text and validation procedure.

---

## §Scope

Rule 7 covers:

- **Who**: the single (or parallel, in Gate_Requirement mode) Opus reviewer that TeamLead dispatches at `§PLAN_AUDIT` using the `Agent` tool with `model: opus`.
- **When**: immediately after PLANNING state collects all PM plans, before EXECUTING begins.
- **What it does NOT cover**: the host `/opus-review final` skill (invoked by the user outside TeamLead's dispatch loop), or Sonnet step-reviewers dispatched at §EXECUTING.

Rationale for scope limit: Rules 0–6 protect EXECUTING-phase PM dispatches. PLAN_AUDIT is an earlier, structurally distinct phase where the reviewer is an Opus agent operating under TeamLead's dispatch authority — not a PM. Rule 7 closes this earlier gap without duplicating EXECUTING-phase enforcement.

---

## §Dispatch prompt blacklist

Every Opus reviewer dispatch in §PLAN_AUDIT opens with this block verbatim (TeamLead substitutes at dispatch time):

```
RULE 7 — ANTI-SELF-SKIP (mandatory, read before any review output):

You are reviewing PM plans for TeamLead. Each issue you log MUST include an actionable
`suggested_fix`. The following values are FORBIDDEN as `suggested_fix` field values:
  - "skip"
  - "none"
  - "no change"
  - "cosmetic only"
  - "minimal-diff"

If you cannot produce a concrete, actionable fix for an issue, DO NOT LOG THE ISSUE.
No-fix means no-issue. Do not log issues you intend to soft-suppress.

This restriction applies ONLY to the `suggested_fix` structured field.
You may freely use these words in prose reasoning (e.g., "skip migration if X" is valid
reasoning — just not a valid suggested_fix value).
```

This block MUST appear before the plan content and rubric in the Opus dispatch prompt.

**Ordering**: this block MUST appear FIRST in the dispatch prompt, before the 6-criterion rubric and before plan content. Anchoring the Rule 7 constraint at position #1 reduces recency-bias dilution.

---

## §Structured-field validation

After receiving Opus reviewer output, TeamLead validates each structured issue entry:

### Detection procedure

1. Extract all structured issue objects from the reviewer's fenced ` ```json ``` ` block.
2. For each issue, read the `suggested_fix` field value.
2.5. **Verify field presence**: if the `suggested_fix` key is absent from an issue object, treat as detection-equivalent (logged issue without actionable fix). Fire detection per step 5 with the offending value reported as `<missing-field>` to the corrective re-dispatch prompt. Rationale: a reviewer can circumvent exact-match denylist by omitting the field entirely; presence-check closes this gap.
3. Normalize: trim whitespace, convert to lowercase.
4. Check against the blacklist (exact match):
   - `"skip"`, `"none"`, `"no change"`, `"cosmetic only"`, `"minimal-diff"`
5. If **any** issue's `suggested_fix` matches the blacklist → detection fires.

### Important: pattern-match scope is structured field only

Do NOT run blacklist detection on prose text in `summary`, `evidence`, or reasoning fields. False-positive risk is high (e.g., reviewer may legitimately write "you may skip migration if the schema hasn't changed" in a reasoning field). Rule 7 applies to the `suggested_fix` structured field only.

### On detection

- Set `plan_audit_self_skip_detected: true` in the audit-trail.jsonl record for this PLAN_AUDIT dispatch.
- Proceed to §Post-receive guard (1-retry).

### On clean pass (no blacklist match)

- Set `plan_audit_self_skip_detected: false`.
- Proceed normally to verdict routing per `references/stage-runbook.md` §PLAN_AUDIT step 4.

### Null case

- `plan_audit_self_skip_detected: null` if Rule 7 did not run (single-plan mode where no `suggested_fix` field was emitted, OR `plan_audit_anti_self_skip_mode == off` per `templates/budget-proposal.md.tpl` §Knobs).

---

## §Verdict aggregation

All logged issues with **actionable** `suggested_fix` values are surfaced to CEO at verdict routing — regardless of severity. The reviewer flags; CEO decides. The reviewer must not pre-filter by severity.

Issues with blacklisted `suggested_fix` values are treated as if they were never logged (they fail the actionability gate — no-fix means no-issue). They do not appear in the verdict summary presented to CEO.

---

## §Post-receive guard

On detection (any blacklisted `suggested_fix` in reviewer output):

**Retry 1**: re-dispatch the same Opus reviewer with:

```
Your prior plan-audit output contained one or more issues with non-actionable `suggested_fix`
values (detected: [list the offending values]). Per Rule 7, a non-actionable fix means the
issue must not be logged.

Please re-emit your plan-audit output with the following correction:
- Remove any issue whose `suggested_fix` you cannot make concrete and actionable.
- For remaining issues, ensure `suggested_fix` describes a specific change the PM should make.

Rule 7 blacklist (forbidden as `suggested_fix` values): "skip", "none", "no change",
"cosmetic only", "minimal-diff".
```

**If detection persists after retry 1**:

- Transition to §ESCALATED with `## Exception` populated:
  - `Type: plan_audit_self_skip_persistent`
  - `Detail: Opus reviewer emitted blacklisted suggested_fix values after 1 Rule 7 corrective re-dispatch. CEO arbitration required.`
- Set `plan_audit_self_skip_detected: true` in audit-trail.jsonl.
- Do NOT proceed to EXECUTING. Wait for CEO verb.

---

## §Cross-references

- `references/anti-rubber-stamp.md` §Rule 7 — design intent and 4-enforcement overview
- `references/stage-runbook.md` §PLAN_AUDIT — runtime hookup (step 3 dispatch prompt + step 3.5 post-receive guard + step 4 verdict routing update)
- `references/progress-md-schema.md` §Audit-trail sidecar — `plan_audit_self_skip_detected` field schema
- `templates/budget-proposal.md.tpl` §Knobs — `plan_audit_anti_self_skip_mode` knob (`strict` / `warn` / `off`)
