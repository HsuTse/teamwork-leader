# Reuse Map — Existing Skills & Rules

> **Source of truth**: design doc v3 §12. This file is the operational mapping.

Per user's Q1.B decision: `/teamwork-leader` is an orchestrator that COMPOSES with existing infrastructure. This file documents what's reused and HOW.

## Phase-by-phase mapping

| Phase | Existing skill / rule | Reuse mechanism |
|---|---|---|
| Discovery | `superpowers:brainstorming` rubric | **Inline rubric only** — TeamLead asks brainstorming-style questions in own state machine. **DO NOT** auto-invoke the skill (its HARD-GATE doesn't compose). |
| TeamFormation | TeamLead | Built-in logic |
| BudgetProposal | `templates/budget-proposal.md.tpl` | Local template |
| Planning | `superpowers:writing-plans` rubric | **Inline rubric** — PMs follow structure (Discovery → File Structure → Bite-Sized Tasks → No Placeholders → Self-Review) but emit plans for TeamLead. **DO NOT** trigger writing-plans' executing-plans handoff. |
| PlanAudit | Plugin-internal Opus dispatch prompt (Planning Cadence rubric — derived from host-level auto-review-cadence rules if present, otherwise plugin-bundled defaults) | TeamLead replicates rubric in Opus dispatch prompt (parameterization, not duplication) |
| Execution iteration | `superpowers:subagent-driven-development` **PATTERN** | TeamLead manually replicates the per-task dispatch + step-review pattern (DO NOT load the skill itself — it's FORBIDDEN per §6.1) |
| Step-review | `auto-review-cadence.md` §Coding Cadence rubric | TeamLead dispatches Sonnet per step |
| Gate_Forward | Sonnet trace + structured classifier | QA PM dispatches |
| Gate_Human | `playwright-cli` / `claude-in-chrome` MCP | QA PM invokes (Skill tool, synchronous) |
| Gate_Requirement | `claude -p` via `scripts/gate-requirement-runner.sh` | TeamLead self-runs |
| Stale guard | `auto-review-cadence.md` Plan staleness pattern | Extended to PROGRESS.md / tasks.md / docs/ / MEMORY.md |
| Cadence hard guards | `auto-review-cadence.md` §4 | Inherited verbatim + opt-out tokens |
| Final review (optional) | `/opus-review final` | TeamLead invokes; **must check `git rev-parse --is-inside-work-tree` first** — for non-repo workspaces, downgrade to inline review or skip with CEO consent. Do NOT auto-invoke under Auto Mode without explicit CEO opt-in. |
| Cleanup | Plugin-internal cleanup discipline (host-level CLAUDE.md §清理紀律 used as override if present) | All PMs follow + ProjectClose CleanupGate (Sonnet prompt embeds rule verbatim) |
| Branch check | `references/dispatch-header.md` §Branch check (RD PM only) | Discovery + RD PM intake (staging/release/production = HALT; main/master = consent check) |
| Memory entry | User memory pattern at `~/.claude/projects/<encoded-home>/memory/` (see `pmp-lessons-learned.md` §Step 4) | ProjectClose MemoryEntry; format conforms to existing `project_<slug>.md` pattern |
| Mezzanine | `mezzanine-*` skills + `references/discipline/mezzanine-discipline.md` (plugin default) | UX PM (with availability fallback to inline discipline reading) |
| Surgical change | `references/discipline/surgical-change.md` (plugin default) | All PMs constrained |
| Verification | `references/discipline/testing-discipline.md` (plugin default) §Goal-Driven Execution | All PMs follow |
| Styling | `references/discipline/styling-discipline.md` (plugin default) | RD + UX |
| Simplicity / YAGNI | `references/discipline/simplicity.md` (plugin default) | All PMs constrained |
| TypeScript | `references/discipline/typescript-discipline.md` (plugin default) | RD on TS projects |

## What is NOT reused (intentionally re-implemented)

| Item | Why not reused |
|---|---|
| `superpowers:brainstorming` skill (the actual skill, not its rubric) | HARD-GATE forces user-facing yes/no flow that conflicts with TeamLead's CEO_Gate state machine |
| `superpowers:writing-plans` skill | Its `## Execution Handoff` mandates transition to executing-plans/subagent-driven-development; TeamLead must keep control of the plan artifact |
| `superpowers:executing-plans` skill | Sibling problem — has its own state machine that conflicts |
| `superpowers:subagent-driven-development` skill | Has main/master red-flag + worktree REQUIRED inheritance that must be handled at TeamLead level via §5.1 BranchCheck + §5.1 WorktreeDecision |

For all 4 of the above, TeamLead **replicates the rubric** in its own dispatch prompts but does NOT load the skill content into PM contexts.

## What is duplicated (acknowledged, not avoidable)

| Item | Where | Why acceptable |
|---|---|---|
| Sonnet step-review rubric | TeamLead's inline step dispatch prompt ↔ host-level auto-review-cadence rules (if present) | TeamLead must inline the rubric for parameterized dispatches; not a copy of code, just a copy of intent |
| 2-round retry cap | TeamLead inline knob ↔ design doc §9.1 hard knobs | Same value, two places — stating the same constraint at different abstraction levels |

These are intentional parameterizations, not regressions.

## How to verify the reuse claims

When TeamLead invokes a phase, sanity-check that the reused skill/rule is actually loaded:

- Skill availability: check the available-skills system-reminder
- Plugin discipline files: confirm `ls -la references/discipline/*.md` returns the 6 expected files (plugin-bundled, always present)
- Optional project overrides: project's `CLAUDE.md` (per Claude Code standard precedence — project instructions > plugin defaults; plugin works without)
- Command files: confirm `ls -la ~/.claude/commands/<file>.md` exists for `/opus-review final`

Missing reuse target (plugin-internal) → surface to CEO via AskUserQuestion before proceeding (likely plugin install corruption). Missing optional host rules → fall back to plugin defaults silently.
