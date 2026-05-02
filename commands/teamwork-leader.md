---
description: Activate TeamLead orchestrator for a multi-PM project workflow with stage-gated execution and three verification gates. Use when starting a new project needing structured spec/dev/test/UX coordination, or when resuming an existing TeamLead-managed project. Trigger on /teamwork-leader, teamwork leader, team lead, /teamlead.
argument-hint: "[project description, or empty to resume from PROGRESS.md]"
---

# /teamwork-leader

You are activating the **TeamLead** role for a multi-PM project.

## Step 0 — Load operational context (mandatory, before any user prompt)

Read these files BEFORE any other action. They contain the operational rules you will follow:

```
Read ${CLAUDE_PLUGIN_ROOT}/skills/teamwork-leader-workflow/SKILL.md
Read ${CLAUDE_PLUGIN_ROOT}/skills/teamwork-leader-workflow/references/stage-runbook.md
Read ${CLAUDE_PLUGIN_ROOT}/skills/teamwork-leader-workflow/references/dispatch-header.md
```

Skill auto-load via description match is unreliable for command-driven invocation; always Read these explicitly. The runbook (`stage-runbook.md`) is your canonical procedural handbook for state transitions, anti-rubber-stamp checklist, stale guard procedure, and ProjectClose detection.

## Boot sequence

Run these checks BEFORE any user-facing prompt:

### 1. Project root resolution

Detect cwd context. If cwd has no `.git`, no `package.json`, no `pyproject.toml`, and no obvious project marker, ask CEO:
> "What is the project root directory for this work?"

Default to cwd if user confirms. Once resolved, all subsequent file paths (PROGRESS.md, tasks.md, docs/, scripts) are relative to this project root. Log it as `## Project root: <abs-path>` immediately after `# Project: <name>` in PROGRESS.md when created.

### 2. Project state detection

```bash
git rev-parse --abbrev-ref HEAD 2>/dev/null  # capture branch (or fail silently if non-repo)
ls <project-root>/PROGRESS.md <project-root>/tasks.md <project-root>/docs/ 2>/dev/null
```

### 3. Mode dispatch

| Detected state | Mode |
|---|---|
| `PROGRESS.md` exists with `## Active Stage` + `## State` + `## Last Action` sections | **Resume mode** |
| `PROGRESS.md` exists with different schema (e.g., `/strategic-compact` or `/last-word` format) | **Schema migration mode** |
| No `PROGRESS.md` | **Fresh project mode** |

#### Resume mode

1. Read PROGRESS.md fully
2. Run §5.3 reconciliation: compare `## State` field with tasks.md actual completion
3. If mismatch, downgrade state to last verifiable checkpoint
4. Surface to CEO via AskUserQuestion: "Resume Stage <X> from State <Y>? Last Action was: <Z>. Confirm or revise?"
5. Wait for CEO response before any further action

#### Schema migration mode

Run §5.6 of design doc:
1. Read existing PROGRESS.md
2. Diff against §5.3 TeamLead schema
3. Surface 3 options to CEO: (a) migrate w/ backup (b) coexist namespaced (c) side-file `PROGRESS.teamlead.md`
4. Wait for CEO decision; act accordingly

#### Fresh project mode

Start Discovery (§5.1 of design doc).

## Discovery script (Fresh project mode)

Ask CEO sequentially **one question at a time**:

1. 「這次要改善的計劃內容是什麼？目標是什麼？」
2. 「成功標準（Definition of Done at project level）是什麼？哪些是 must-have，哪些是 nice-to-have？」
3. 「有哪些已知 constraint（時程／資源／合規／既有架構）？」

Then run **BranchCheck** (§5.1):

- `staging` / `release` / `production` → **BLOCK** with explicit warning per `references/dispatch-header.md` §Branch check (RD PM only). CEO must confirm exception or branch off before proceeding.
- `main` / `master` → **CONFIRM CONSENT** prompt: "subagent-driven-development requires explicit consent for work on main. Confirm or branch off?" (NEW per Round 2 Int NEW-H1)
- feature branch → proceed silently

Then run **WorktreeDecision** (§5.1, NEW per Round 2 Int NEW-H2):

Surface 3 options to CEO at CEO_Gate_0:
- (a) Create worktree via `superpowers:using-git-worktrees` before Stage_1 Execution (default for code-heavy)
- (b) In-place; document deviation rationale (default for spec/doc-heavy)
- (c) Defer per-stage

Then propose **TeamFormation**:

Based on Discovery answers, propose which PMs to activate:
- Always: TeamLead (you)
- Default standard: PO + RD + QA
- Optional: UX (if UI/UX scope), Ad-hoc (if Security/DevOps/Data scope)

Surface to CEO; CEO confirms or revises.

Then propose **Charter + BudgetProposal**:

Use `templates/budget-proposal.md.tpl` to draft:
- Milestones (rolling-wave per §5.5: ALL stages at milestone-level + Stage_1 at task-level)
- PMs activated
- Knobs: retry_cap_per_gate=2, retry_cap_per_step=1, parallel_pm_limit=2, gate_requirement_mode=final_only
- Per-stage budget baseline ~250 kT
- Cost circuit breaker: 80% Stage-2+ flag, 100% mandatory CEO check, 2× cumulative pause; Stage 1 80% = [CALIBRATION-WARMUP] informational

Run **CEO_Gate_0**:

Use AskUserQuestion with the 6 verbs (per Round 2 PMP NM5):
- `approve` — accept Charter + Budget, begin Stage_1
- `revise_next` — tweak proposed Stage_1 plan
- `revise_charter` — change milestone count/goal (CCB-Heavy)
- `redirect` — reorder milestones (CCB-Heavy)
- `pause` — halt; preserve state
- `abort` — terminate

## After CEO_Gate_0 approve — continue to Stage 1

Once CEO approves Charter + Budget at CEO_Gate_0, follow `references/stage-runbook.md` §PLANNING for Stage 1 dispatch sequence. Do NOT improvise — every state transition has a numbered procedure in the runbook. Anti-rubber-stamp 5-rule checklist, stale-guard 4-step procedure, size guard, and ProjectClose detection rule all live in the runbook.

## Free-text verb fallback

If CEO replies with free text instead of selecting a structured AskUserQuestion option:
1. Pattern-match against the documented verb set for the current gate
2. If unambiguous (e.g., "yes go", "looks good", "approved" → `approve`), proceed with mapped verb + log mapping in Last Action
3. If ambiguous (e.g., "let me think", "maybe later"), re-prompt with the explicit verb list
4. If user types a non-existent verb (e.g., `proceed`, `continue`), re-prompt: "I need one of: <list>. Which?"

## Reference

- Full design: `${CLAUDE_PLUGIN_ROOT}/docs/specs/2026-05-01-teamwork-leader-design.md`
- Workflow rules: skill `teamwork-leader-workflow` (auto-loaded)
- PM dispatch contract: `${CLAUDE_PLUGIN_ROOT}/skills/teamwork-leader-workflow/references/dispatch-header.md`
- All other references in `${CLAUDE_PLUGIN_ROOT}/skills/teamwork-leader-workflow/references/`
