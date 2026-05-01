# PMP Lessons-Learned — ProjectClose Retrospective Protocol

> **Source of truth**: design doc v3 §5.4. This file operationalizes the protocol.

## When this fires

ProjectClose state, after all Stage gates have passed and CEO has signaled project completion. Before CEO_Gate_Final.

## Step 1 — Per-PM dispatch

TeamLead dispatches each activated PM (PO/RD/QA/UX + any Ad-hoc) with this prompt:

```
You are dispatched as <Role> PM for the project's lessons-learned retrospective.

## Frozen PROGRESS.md excerpt (full project)

<TeamLead injects: ## Charter, ## Stage History (all stages), ## RAID Register (full), ## Self-Audit (all stages so far)>

## Your task

Draft 3-5 lessons covering THESE structured categories (mandatory taxonomy):

1. **What worked** — practices, decisions, tools that produced value
2. **What didn't work** — practices/decisions that caused friction or rework
3. **What I'd do differently** — concrete change recommendation for next project
4. **Failure-mode taxonomy** — categorize any failures observed using these labels:
   - `spec_drift`
   - `scope_creep`
   - `gate_routing_error`
   - `value_hypothesis_unmet`
   - `dod_drift`
   - `over-budget`
   - `branch-discipline-violation`
   - `cleanup-oversight`
   - `cross-pm-verification-gap`
   - `other (specify)`

For each lesson, cite the specific Stage / dispatch / RAID entry that motivates it.

## Return contract

Per dispatch-header.md §Return contract. Lessons go in `raid_updates` as `[I]` items with `severity: low` and `status: closed` (since they're observations, not action items).
```

## Step 2 — TeamLead consolidation

TeamLead aggregates returned lessons into `PROGRESS.md ## Lessons Learned` section:

```markdown
## Lessons Learned

### What worked
- (PO) <lesson> — <Stage / evidence>
- (RD) <lesson> — <Stage / evidence>
- ...

### What didn't work
- (QA) <lesson> — <Stage / evidence>
- ...

### What I'd do differently
- (UX) <lesson> — <Stage / evidence>
- ...

### Failure-mode taxonomy aggregate
- spec_drift: <count> instances (Stages: 1, 3, 4)
- scope_creep: <count> (Stages: 2)
- ...

### Self-Audit aggregate (per Round 2 PMP NM1)
- TeamLead verified <X>/<Y> PM claims across <N> stages
- Verification-gap patterns observed: <list>
- Sampling-rotation distribution: <which PM got cross-verified each stage>
```

## Step 3 — Value Realization summary (per Round 2 PMP NL2)

Aggregate all `[V]` RAID entries from all stages into a table:

```markdown
### Value Realization

| Value Criterion | Hypothesis | Realized | Evidence |
|---|---|---|---|
| <criterion> | <expected outcome> | yes/partial/no | <citation> |
```

## Step 4 — MemoryEntry draft

TeamLead drafts `~/.claude/projects/<encoded-home>/memory/project_<slug>.md` (`<encoded-home>` = $HOME with `/` → `-`, e.g. `/Users/alice` → `-Users-alice`):

```markdown
---
name: <project-name>
description: <one-line, ≤80 chars>
type: project
---

# <Project Name>

**Period**: YYYY-MM-DD → YYYY-MM-DD (N stages)
**PMs activated**: PO, RD, QA, UX (+ any ad-hoc)

## Goal

<one paragraph from Charter>

## Approach

<one paragraph summary of stages + key decisions>

## Outcomes

- Value realized: <X yes / Y partial / Z no>
- Stages: <N> (<all-passed | M with revisions | etc.>)
- CCB events: <N Light, M Heavy>

## Key decisions

- <decision> — <rationale>
- ...

## RAID outcomes (closed)

- [R] <closed risk + how mitigated>
- [A] <validated assumption>
- [I] <resolved issue>

## Lessons compounded

- <top 3 lessons from §Lessons Learned>

## Patterns to apply to future projects

- <generalized pattern 1>
- <generalized pattern 2>

## Failure modes to watch

- <failure mode taxonomy entry from this project>
```

## Step 5 — MemoryEntry CEO review

TeamLead surfaces draft to CEO via AskUserQuestion: "Review draft memory entry. Approve append, edit, or skip?"

CEO approve → TeamLead writes the file + appends index line to `MEMORY.md`:

```markdown
- [<Project Name>](project_<slug>.md) — <one-line description>
```

Index append uses §11.3 stale guard (per `progress-md-schema.md`, which itself extends `~/.claude/rules/auto-review-cadence.md` Plan staleness pattern) to prevent CC memory system overwrite.

## Step 6 — CleanupGate

(Per design doc §5.4) TeamLead dispatches Sonnet with:
- `~/CLAUDE.md §清理紀律` text **embedded verbatim**
- Session-start ISO-8601 timestamp
- Explicit instruction: "Do NOT propose deletion of files older than session-start unless explicitly user-marked-disposable"

Sonnet enumerates untracked/temp artifacts; TeamLead surfaces deletion proposals to CEO **per item**.

### Per-item AskUserQuestion enforcement (mandatory; M-4 fix)

For EACH proposed deletion, TeamLead MUST issue a separate AskUserQuestion with this verbatim structure (do NOT batch multiple files into one question, do NOT free-text confirm a list):

```
Question: "Delete <path>? (mtime: <ISO-8601>, size: <bytes>, classification: <session-product | pre-existing | unknown>)"
Options:
  - keep — preserve file, do not delete
  - delete — confirm deletion of THIS specific path only
  - skip — defer decision; file kept; proceed to next item
  - abort — halt CleanupGate; no further deletions this session
```

**Enforcement rules**:
1. One AskUserQuestion per file (not per batch). If Sonnet enumerated 30 files, TeamLead issues up to 30 questions sequentially.
2. CEO answer of `delete` authorizes ONLY the specific path in that question — not a pattern, not a glob, not "all similar".
3. `abort` immediately exits the cleanup loop; remaining un-asked items are kept by default.
4. Pre-existing files (mtime older than session-start) MUST default to `keep` and require `delete` verb plus extra rationale field; per `~/CLAUDE.md §清理紀律` these are treated as out-of-scope unless explicitly user-marked-disposable.
5. TeamLead logs each (path, verb, rationale-if-pre-existing) row in `## Self-Audit` ### CleanupGate sub-section.

This rule prevents the failure mode documented in `~/CLAUDE.md §清理紀律 §Why` (2026-04-27 incident: batch-deletion of `.claude-artifacts/` lost prior-session design files). The per-item gate is the structural safeguard — without it, "TeamLead surfaces deletion proposals" can collapse into a single batch confirmation that defeats the whole discipline.

## Step 7 — CEO_Gate_Final

Formal acceptance via AskUserQuestion. Sign-off → PROGRESS.md `## State` set to `COMPLETED`, project archived.
