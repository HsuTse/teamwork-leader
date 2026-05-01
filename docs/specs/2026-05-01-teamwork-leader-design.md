# Teamwork-Leader Plugin — Design Spec (v3)

| Field | Value |
|---|---|
| **Spec ID** | `teamwork-leader-v3` |
| **Date** | 2026-05-01 |
| **Author** | HsuTse + Claude (brainstorming session) |
| **Status** | v3 — Phase 1+2 (RSS) + Phase 3 (N1 trust_tier + KMR per-task proxy) ship-complete 2026-05-02; not yet dogfooded |
| **Target install path** | `~/.claude/plugins/teamwork-leader/` |
| **Form** | Plugin (cross-project, user-level) |
| **Related rules** | `~/.claude/rules/auto-review-cadence.md`, `~/.claude/rules/CONTRIBUTING.md`, `~/.claude/rules/TESTING.md`, `~/.claude/rules/context-management.md`, `~/.claude/rules/branch-discipline.md` |

---

## Revision history

- **v1 (2026-05-01)** — initial draft
- **v2 (2026-05-01)** — applied 9 HIGH + 9 MED + 4 LOW revisions from Round 1 Opus reviewers (architecture / PMP / integration). Replaced `/loop` with `superpowers:subagent-driven-development`; TeamLead-only PROGRESS.md writer; Value Hypothesis + DoD intake field; ProjectClose retrospective; wave-depth rule; recalibrated token budget; OQ3 resolved.
- **v3 (2026-05-01)** — applied 6 HIGH + 5 MED revisions from Round 2 Opus reviewers. New HIGHs addressed: classifier malformed-JSON fallback (Arch); DoD enforcement at gate close + Charter immutability (PMP); subagent-driven-development inheritance (main-branch consent + worktree REQUIRED) + claude-p handoff contract (Integration). v2 partial-resolutions tightened: PROGRESS.md ceiling triggers now explicit; brainstorming/writing-plans skills now FORBIDDEN in PM intake (replacement: inline rubric only).

---

## 1. Executive Summary

`teamwork-leader` is a **multi-agent project orchestration plugin** that simulates a small project team inside a single Claude Code session. The user takes the **CEO** role; an entry command `/teamwork-leader` activates the **TeamLead** orchestrator, which composes role-based **PM agents** (PO / RD / QA / UX + ad-hoc) on demand, drives a stage-gated workflow with three verification gates, and reuses the existing skill stack (`brainstorming`, `writing-plans`, `executing-plans`, `subagent-driven-development`, `opus-review`, `auto-review-cadence`) rather than reinventing it.

**Core promises**:

1. **Role discipline** — every action is owned by a named role with a job description; nothing happens "in the air".
2. **Stage-gated** — work proceeds in stages; each stage has a CEO approval gate at the boundary.
3. **Three verification gates per stage** — forward path / human path / requirement alignment.
4. **Budget transparency** — milestone × PM × retry-cap is declared up-front and tallied at each stage report; cost circuit breaker forces CEO check-in if cumulative cost exceeds 2× declared baseline.
5. **Anti-rubber-stamp** — TeamLead must verify PM reports against artifacts, not just believe them. Mandatory rejection on incomplete returns.
6. **Value-Driven** — every dispatch declares a Value Hypothesis; every stage closes with Value Realized check.

**Non-goals**:

- Not an autonomous fire-and-forget agent. CEO gates are non-skippable.
- Not a replacement for `brainstorming` / `writing-plans` / `subagent-driven-development` — it composes alongside them with explicit boundaries.
- Not a budget enforcer at token level — token cost is informational, the enforced budget is in milestone/retry counts.

---

## 2. Goals & Non-Goals

### Goals

- **G1**: Reusable scaffold for projects needing >1 logical workstream (spec / dev / test / UX).
- **G2**: Explicit role boundaries — every artifact has a named role owner.
- **G3**: Verification before stage-close (3 gates).
- **G4**: Budget consumption surfaced every stage so CEO can recalibrate.
- **G5**: Clean cross-session resumption — no state loss after `/clear`.
- **G6**: Reuse existing infrastructure; no duplication of review cadence logic.
- **G7**: Value delivered (not just consumed) — every stage answers "what business outcome did we enable?".
- **G8**: Lessons compounding — every project closure captures lessons-learned to user memory for future sessions.

### Non-Goals

- **NG1**: Fully autonomous shipping. Every stage close requires CEO sign-off.
- **NG2**: General team-management tool. Scope is project execution inside CC.
- **NG3**: Code-level review tooling. Use `auto-review-cadence` and `/opus-review` for that.
- **NG4**: Replacing PMP enterprise tooling. We pick **WBS / CCB / Value-Driven / RAID / Lessons-Learned** subset only.

---

## 3. Roles & Hierarchy

```
CEO (user)
 └── TeamLead (orchestrator, main agent)
      ├── PO PM (agent — Spec / docs / docs-sync)
      ├── RD PM (agent — tasks.md / development)
      ├── QA PM (agent — tests / CodeReview / 3-gate execution / cross-PM verification)
      ├── UX PM (agent — UX evaluation / mezzanine compliance)
      └── Ad-hoc PM (template — Security / DevOps / Data / arbitrary)
```

### 3.1 Authority matrix (RACI-flavored)

| Role | Plans | Edits code | Edits docs/ | **Edits PROGRESS.md** | Edits tasks.md | Runs tests | CCB-Light | CCB-Heavy | Approves stage |
|---|---|---|---|---|---|---|---|---|---|
| CEO | input | — | input only | — | — | — | input | **decides** | **decides** |
| TeamLead | reviews | — | — | **sole writer** | — | — | **acks** | proposes | proposes |
| PO PM | own scope | — | **yes** | returns RAID/status payload | — | — | proposes | proposes | — |
| RD PM | own scope | **yes** | — | returns RAID/status payload | **yes** | runs | requests | requests | — |
| QA PM | own scope | — | — | returns RAID/status + gate evidence | — | **yes** | requests | requests | — |
| UX PM | own scope | — | — | returns RAID/status payload | — | — | requests | requests | — |

**Critical rule**: **TeamLead is the SOLE writer of PROGRESS.md** (resolves Architecture Reviewer HIGH-1 race condition). PMs return structured payloads in their dispatch reply; TeamLead serializes payloads into PROGRESS.md after dispatch returns. This eliminates parallel-write conflicts even when 2+ PMs dispatched concurrently.

### 3.2 PM dispatch return contract (mandatory)

Every PM dispatch return MUST contain these fields. Missing any → TeamLead returns INCOMPLETE; re-dispatches once; second incomplete → escalate CEO.

**Return format** (per Round 2 Int NEW-M6): PM MUST emit return as a fenced ` ```json ` block. TeamLead extracts via regex-bounded parse (`/```json\n([\s\S]+?)\n```/`). On parse failure → INCOMPLETE → re-dispatch once with explicit schema reminder → second failure → escalate CEO.

```json
{
  "outcome": "SUCCESS | PARTIAL | BLOCKED | INCOMPLETE",
  "value_hypothesis": "<expected business outcome, how measured>",
  "value_realized": "<observed evidence, or 'pending Stage close'>",
  "dod_status": "met | partial | missed",
  "dod_evidence": "<observable state proving DoD criteria, or gap description>",
  "artifacts_touched": ["<absolute path>", ...],
  "verify_evidence": [
    {"command": "<exact command run>", "key_output": "<excerpt>", "result": "PASS|FAIL"}
  ],
  "raid_updates": [
    {"type": "R|A|I|D|V", "content": "...", "owner": "<PM>", "status": "open|mitigating|closed|validated|invalidated"}
  ],
  "ccb_requests": [{"track": "light|heavy", "description": "..."}],
  "token_estimate_kT": <self-reported usage>,
  "handoff": "<next role | none>"
}
```

**`dod_status` field** (NEW per Round 2 PMP NH1): every PM dispatch must self-report whether the dispatch achieved its declared DoD. PARTIAL/MISSED triggers automatic CCB-Light entry referencing the gap. TeamLead verifies `dod_evidence` against artifacts (per §3.3 anti-rubber-stamp).

### 3.3 TeamLead anti-rubber-stamp discipline

TeamLead MUST verify before accepting any PM return. Five mandatory rules + sampling policy:

1. **Artifact existence check** — every "outcome=SUCCESS" claim with an `artifacts_touched` path → TeamLead Reads at least the most-changed file to confirm.
2. **Verify command re-run (sampling)** — TeamLead re-runs ≥1 verify_evidence command per dispatch, prioritizing the highest-risk claim (not all commands; cost-bounded).
3. **Sample diff inspection** — for code changes, read at least one critical file's actual diff.
4. **RAID review** — read PM-reported RAID items, judge severity independently, do not paste-through.
5. **Distinguish trusted vs unverified** — `## Last Action` line uses prefix:
   - `[TRUSTED]` — TeamLead verified
   - `[CLAIMED]` — PM said but not yet verified (only allowed mid-stage; must be `[TRUSTED]` by stage close)

**Non-negotiable**: this is the line between PMP-style management and "AI summarizing AI" theater.

### 3.4 Cross-PM independent verification

To prevent TeamLead-as-single-point-of-failure (PMP Reviewer MED-4):

- Per stage, **QA PM independently re-verifies one of RD's claimed test passes** (not all; sampling)
- **PO PM independently confirms Gate_Requirement findings about spec gaps**
- TeamLead at CEO_Gate_N includes a `## Self-Audit` line: "I verified X of Y PM claims this stage; unverified items: [...]"

---

## 4. Architecture

### 4.1 Plugin layout (`~/.claude/plugins/teamwork-leader/`)

```
.claude-plugin/
  plugin.json
commands/
  teamwork-leader.md                   # /teamwork-leader entry
skills/
  teamwork-leader-workflow/
    SKILL.md                           # team rules + role definitions + state machine
    references/
      pmp-wbs.md                       # Rolling-wave depth specification
      pmp-ccb.md                       # Light / Heavy CCB tracks + cap rules
      value-driven.md                  # Value Hypothesis + DoD criteria
      pmp-lessons-learned.md           # ProjectClose retrospective protocol
      three-gates.md                   # forward / human / requirement gate mechanics + structured classifier schema
      progress-md-schema.md            # required sections + size discipline
      reuse-map.md                     # mapping to existing skills/rules
      dispatch-header.md               # canonical PM dispatch intake header
      anti-rubber-stamp.md             # 5 verification rules + sampling policy
      schema-migration.md              # collision handling for pre-existing PROGRESS.md
agents/
  po-pm.md
  rd-pm.md
  qa-pm.md
  ux-pm.md
  ad-hoc-pm.md
templates/
  PROGRESS.md.tpl
  tasks.md.tpl
  stage-report.md.tpl
  budget-proposal.md.tpl
  ccb-light.md.tpl
  ccb-heavy.md.tpl
  project-close.md.tpl
  ccb-log.md.tpl                       # central CCB-Light audit log
scripts/
  gate-requirement-runner.sh           # claude -p shell-out wrapper for Gate_Requirement
docs/
  specs/
    2026-05-01-teamwork-leader-design.md  # this file
  README.md                            # user-facing quickstart
```

### 4.2 Per-project state (minimal, per user explicit preference)

```
<project>/
  PROGRESS.md                          # owned by TeamLead — single source of truth (sole writer)
  tasks.md                             # owned by RD PM — actionable task list
  docs/
    <existing project specs>          # owned by PO PM
    decisions/
      ccb-log.md                       # central CCB-Light audit log (NEW per Arch MED-3 + PMP MED-1)
    stage-archives/                    # archived StageReports when PROGRESS.md hits ceiling (NEW per Arch HIGH-2)
      stage-N.md
```

No per-project `.teamleader/` directory. All cross-stage persistent state lives in `PROGRESS.md` + the small set above.

---

## 5. State Machine

### 5.1 Macro flow

```
Discovery → BranchCheck → TeamFormation → BudgetProposal → ★CEO_Gate_0 (Charter)★
   │
   ▼
[StageLoop]
   ├── Stage_N
   │     Planning → PlanAudit(Opus) →
   │     Execution(subagent-driven-development + Sonnet step-review) →
   │     Gate_Forward → Gate_Human → Gate_Requirement →
   │     StageReport (incl. RAID burndown + Value Realized) → 
   │     WaveRefinement(propose Stage_N+1 details) → ★CEO_Gate_N★
   ▼
ProjectClose
   ├── LessonsLearned (each PM drafts, TeamLead consolidates)
   ├── CleanupGate (artifact ownership audit + cleanup proposal)
   ├── MemoryEntry (write project_<slug>.md to user memory)
   └── ★CEO_Gate_Final★
```

**Discovery** runs without auto-invoking `superpowers:brainstorming` (that skill has a HARD-GATE that doesn't compose with TeamLead's state machine — see Integration Reviewer HIGH-2). Instead, TeamLead asks brainstorming-style questions inline using the SKILL's rubric (purpose / constraints / success criteria) but stays in the TeamLead state machine.

**BranchCheck** (per `branch-discipline.md` + Round 2 Int NEW-H1): TeamLead runs `git rev-parse --abbrev-ref HEAD`. Three branches:
- `staging` / `release` / `production` → surface BLOCKING warning via AskUserQuestion before TeamFormation
- `main` / `master` → surface CONFIRM-CONSENT prompt (subagent-driven-development skill's red-flag rule requires explicit consent for work on default branch). CEO must confirm "yes, work on main" or branch off
- feature branch → proceed normally

**WorktreeDecision** (NEW per Round 2 Int NEW-H2): subagent-driven-development skill states `superpowers:using-git-worktrees` is REQUIRED before starting. TeamLead surfaces three options at CEO_Gate_0:
- (a) **Create worktree** — TeamLead invokes `superpowers:using-git-worktrees` to create isolated worktree before Stage_1 Execution (default for code-heavy projects)
- (b) **In-place** — Skip worktree, work directly in current dir (default for spec/doc-heavy projects). TeamLead documents Non-Goal deviation rationale in PROGRESS.md ## Charter
- (c) **Per-stage decision** — defer worktree decision until each Stage Execution begins
CEO picks at CEO_Gate_0; decision logged to PROGRESS.md.

### 5.2 Micro flow per stage

```
[Stage_N entered]
  │
  ├─ Planning
  │   ├─ TeamLead dispatches PMs for stage scope
  │   ├─ PMs follow writing-plans rubric INLINE (no auto-invoke of writing-plans skill)
  │   ├─ Each PM emits plan + verify clauses + value hypothesis
  │   └─ PMs RETURN plan to TeamLead (no executing-plans handoff); TeamLead writes to PROGRESS.md
  │
  ├─ PlanAudit (Opus)
  │   ├─ TeamLead dispatches Opus reviewer with rubric from auto-review-cadence §Planning
  │   ├─ Verdict: APPROVED / APPROVED_WITH_REVISIONS / REJECTED / INCONCLUSIVE
  │   ├─ REJECTED → 1 retry; still REJECTED → escalate CEO
  │   ├─ INCONCLUSIVE → escalate CEO immediately
  │   └─ Stale guard before any plan auto-edit (extends auto-cadence pattern)
  │
  ├─ Execution (uses superpowers:subagent-driven-development pattern, NOT /loop)
  │   ├─ TeamLead invokes subagent-driven-development to iterate over RD's tasks.md items
  │   ├─ Each task → dispatch sub-agent → step-review (Sonnet) → mark complete
  │   ├─ Step-review FAIL → auto-fix loop (max 1 retry, surgical edit only)
  │   └─ Loop exits when stage's tasks all complete OR step-review hard-fails
  │
  ├─ Gate_Forward (with structured classifier output)
  │   ├─ Executor: QA PM → Sonnet trace
  │   ├─ Output schema (mandatory):
  │   │   {root_cause: code_bug|spec_ambiguity|spec_gap|environmental|inconclusive,
  │   │    evidence: <citation to spec section + code line>,
  │   │    suggested_owner: <PM name>}
  │   ├─ TeamLead routes on `root_cause`, NOT on prose interpretation
  │   ├─ INCONCLUSIVE → escalate CEO immediately
  │   └─ Retry cap: 2 rounds
  │
  ├─ Gate_Human
  │   ├─ Executor: QA PM (playwright-cli / claude-in-chrome)
  │   ├─ Subjective items → surface to CEO via AskUserQuestion (no auto-pass)
  │   └─ Same structured classifier output
  │
  ├─ Gate_Requirement
  │   ├─ Default: Final Stage only (resolves OQ3 — cost mitigation)
  │   ├─ Mid-stage opt-in via CEO approval at CEO_Gate_(N-1)
  │   ├─ Executor: TeamLead via scripts/gate-requirement-runner.sh
  │   └─ Same structured classifier output
  │
  ├─ StageReport
  │   ├─ Format from templates/stage-report.md.tpl
  │   ├─ Sections: Outcome / Gate Results / RAID Burndown / Value Realized vs Hypothesis / Token Tally / CCB Activity / Self-Audit (TeamLead) / Next Stage Proposal
  │   └─ Append to PROGRESS.md ## Stage History (TeamLead writes)
  │
  ├─ WaveRefinement (NEW — wave depth rule)
  │   ├─ TeamLead refines Stage_(N+1) from milestone-level → deliverable-level
  │   ├─ Stage_(N+2) onward stays at milestone-level
  │   └─ Surface refinement at CEO_Gate_N for approval
  │
  └─ CEO_Gate_N
      ├─ TeamLead invokes AskUserQuestion with structured options
      ├─ Recognized verbs (NEW per Round 2 PMP NM5):
      │     - approve         (Stage_N closed, Stage_N+1 plan accepted, proceed)
      │     - revise_next     (tweak Stage_N+1 plan; loop back to WaveRefinement)
      │     - revise_charter  (change milestone count / goal → triggers CCB-Heavy)
      │     - redirect        (reorder remaining milestones → CCB-Heavy)
      │     - pause           (halt with state preserved)
      │     - abort           (terminate project)
      ├─ Pre-approval CEO must confirm "DoD met for stage: yes/partial/no" 
      │     (NEW per Round 2 PMP NH1 — DoD enforcement at gate close)
      │     partial/no → forced CCB-Light entry; cannot proceed via approve until resolved
      ├─ Anything else → re-prompt with explicit verbs
      └─ approve → next Stage_(N+1) Planning
```

### 5.3 PROGRESS.md state field schema

```
## Active Stage: <name>
## State: PLANNING | PLAN_AUDIT | EXECUTING | GATING | REPORTING | AWAITING_CEO | ESCALATED | COMPLETED | ABORTED
## Last Action: <ISO-8601 timestamp> [TRUSTED|CLAIMED] — <one-line Insight>
```

**ESCALATED state** (NEW per Arch MED-1): when retry exhausted or INCONCLUSIVE verdict received. `## Last Action` describes what's escalated. CEO must respond before any further work.

**In-flight dispatch on /clear**: Task tool dispatches do NOT survive `/clear`. On resume, if `## State` shows `PLAN_AUDIT` / `GATING` / step-review-active state, TeamLead MUST re-dispatch the in-flight work; it cannot resume mid-flight.

**Resumption reconciliation**: TeamLead reads PROGRESS.md state field AND tasks.md actual status; if mismatch (e.g., state=EXECUTING but no tasks marked completed since last Last Action), downgrade state to last verifiable checkpoint and re-dispatch from there.

### 5.4 ProjectClose detail (NEW — PMP HIGH-2 lessons-learned)

```
[ProjectClose entered]
  │
  ├─ LessonsLearned
  │   ├─ TeamLead dispatches each PM with single prompt:
  │   │   "Draft 3-5 lessons: what worked / what didn't / what would you do differently"
  │   ├─ PMs return lessons in structured payload
  │   └─ TeamLead consolidates into PROGRESS.md ## Lessons Learned
  │
  ├─ CleanupGate (NEW — Integration Reviewer MED-2 + R2 NEW-M4)
  │   ├─ TeamLead dispatches Sonnet to enumerate untracked/temp artifacts
  │   ├─ Dispatch prompt MUST embed (NEW per Round 2 Int NEW-M4):
  │   │   - `~/CLAUDE.md §清理紀律` text verbatim
  │   │   - Session-start ISO-8601 timestamp (for ownership classification)
  │   │   - Explicit instruction: "Do NOT propose deletion of files older than session-start unless explicitly user-marked-disposable"
  │   ├─ Classify by ownership: this-session / prior-session / long-term-keep
  │   ├─ Surface to CEO with proposed deletions; require explicit approval per item
  │   └─ Per CLAUDE.md §清理紀律 — no batch delete without confirmation
  │
  ├─ MemoryEntry (NEW — Integration Reviewer MED-3 + R2 NEW-M5)
  │   ├─ TeamLead drafts ~/.claude/projects/<encoded-home>/memory/project_<slug>.md
  │   │   matching user's existing pattern (goal / approach / decisions / RAID outcomes / lessons)
  │   ├─ Frontmatter format (per existing memory examples — verified 2026-05-01):
  │   │   ```
  │   │   ---
  │   │   name: <project-name>
  │   │   description: <one-line description>
  │   │   type: project
  │   │   ---
  │   │   ```
  │   ├─ Surface to CEO for review/edit before append
  │   ├─ Append a one-liner to MEMORY.md `## Projects` index using format
  │   │   `- [<Title>](<file>.md) — <one-line hook>` (NEW per Round 2 Int NEW-M5)
  │   └─ Apply §11.3 stale guard to MEMORY.md write (CC may regenerate it concurrently)
  │
  └─ CEO_Gate_Final
      ├─ Formal acceptance via AskUserQuestion
      └─ Sign-off → project archived; PROGRESS.md frozen with COMPLETED state
```

### 5.5 Wave depth rule (NEW — PMP HIGH-3)

| Stage offset | Plan depth | Verify clauses required? |
|---|---|---|
| Current Stage (N) | Task-level | **YES** |
| N+1 | Deliverable-level | NO |
| N+2 onward | Milestone-level (one-line) | NO |

CEO_Gate_0 Charter requires:
- Milestone-level plan for ALL stages
- Task-level plan for Stage_1 only

WaveRefinement step (§5.2) at each StageReport refines the next stage from deliverable → task level, surfaced for CEO approval.

**Decidability test** (NEW per Round 2 Arch MED-5):
- **task-level**: single PM, single dispatch, ≤1 day wall clock, has acceptance test command
- **deliverable-level**: 2-5 tasks, single PM, ships an end-user-visible artifact
- **milestone-level**: phase boundary, may span multiple PMs/deliverables

This decidability rule lives in `references/pmp-wbs.md` (Phase 1 deliverable).

### 5.5.1 Charter immutability (NEW per Round 2 PMP NH2)

**WaveRefinement may ONLY refine N+1 within the milestone-level Charter scope**. Any change to:
- milestone count
- milestone goal / scope
- project end-state
- budget baseline (knobs in §9.1)

→ requires **CCB-Heavy**, NOT WaveRefinement.

**Tripwire**: if WaveRefinement's deliverable-level plan diverges from the original milestone description (semantic drift), TeamLead halts WaveRefinement, raises CCB-Heavy, surfaces to CEO.

**WaveRefinement output is informational at CEO_Gate_N**; the refined Stage_N+1 plan only becomes "active" after CEO `approve`. If CEO uses `revise_next`, no work begins on Stage_N+1 until next iteration.

### 5.6 Schema migration (NEW — Integration Reviewer MED-5)

When `/teamwork-leader` runs in a project that already has `PROGRESS.md` from prior workflows (`/strategic-compact`, `/last-word`, manual notes):

1. TeamLead reads existing PROGRESS.md
2. Detect existing sections → diff against §5.3 schema
3. Surface to CEO via AskUserQuestion: choose
   - (a) **Migrate** — replace existing sections with §5.3 schema (TeamLead drafts merge proposal). **Backup required (NEW per Round 2 Arch MED-6)**: TeamLead writes `PROGRESS.md.pre-teamlead-<timestamp>.bak` BEFORE drafting merge; surfaces full diff via AskUserQuestion; CEO must explicitly approve before write commits. Recovery path = restore from .bak.
   - (b) **Coexist** — namespace TeamLead sections (`## TeamLead/Active Stage`, `## TeamLead/State`, etc.)
   - (c) **Side-file** — use `PROGRESS.teamlead.md` as separate file. **All §11.3 stale guard, §3 RACI matrix "PROGRESS.md", §11.6 size discipline references substitute `PROGRESS.teamlead.md` in TeamLead's state for this project (NEW per Round 2 Int NEW-M3).** Decision logged once; downstream sections do not need to keep restating the substitution.
4. Decision logged in `## Active Stage` section under "Schema decision: <choice> at <date>"

---

## 6. PM Agent Specifications

> **§6 is spec**, defining what each `agents/<role>-pm.md` file should contain. Phase 1 implementation creates the actual agent .md files. Standard dispatch header is canonicalized in `references/dispatch-header.md` (read-once, all PMs reference).

### 6.0 Color assignments

| Agent | Color |
|---|---|
| `po-pm` | blue |
| `rd-pm` | green |
| `qa-pm` | orange |
| `ux-pm` | purple |
| `ad-hoc-pm` | gray |

### 6.1 Standard dispatch header (canonical)

```
---
name: <role>-pm
model: sonnet
color: <see §6.0>
description: <when to invoke>
---

# <Role> PM Agent

## Standard intake header

You are dispatched as <Role> PM by TeamLead for project <project name>.

**Frozen PROGRESS.md excerpt** (TeamLead embeds the relevant sections at dispatch time, so PM doesn't re-read for race-free):
<TeamLead-injected excerpt of ## Active Stage / ## State / relevant ## RAID Register subset>

**Read first** (for full context):
- <project>/tasks.md (your relevant section)
- <project>/docs/ (relevant spec)

**Your scope this dispatch**: <TeamLead injects scope description>

**Value Hypothesis** (mandatory): What business outcome should this dispatch enable? How will it be measured?
<TeamLead injects expected value statement; PM reaffirms or proposes refinement>

**Definition of Done** (mandatory): What observable state == "this dispatch's work is complete"?
<TeamLead injects DoD criteria from stage plan>

**Constraints**:
- Do NOT exceed scope. Out-of-scope discoveries → return as RAID issue, do not act.
- Surgical changes only (per ~/.claude/rules/CONTRIBUTING.md §Surgical Change).
- Verification per ~/.claude/rules/TESTING.md.
- **FORBIDDEN skills** (NEW per Round 2 Int H2 / PMP NM4): you MUST NOT invoke `superpowers:writing-plans`, `superpowers:brainstorming`, `superpowers:executing-plans`, `superpowers:subagent-driven-development`. These have HARD-GATE / Execution Handoff terminal states that conflict with TeamLead orchestration. Instead, follow their rubric INLINE without loading the skill content into your context.
- **ALLOWED skills**: `mezzanine-antipatterns`, `using-mezzanine-ui-react`, `using-mezzanine-ui-ng`, `mezzanine-page-patterns`, `mezzanine-copywriting`, `playwright-cli`, `chrome-devtools-batch-scraper`, `markitdown`, `pdf-to-markdown`, `text-extractor`. Skill availability check first; fall back to inline rule files if missing.
- You MUST NOT Task-dispatch sub-agents unless your plan declares parallel-dispatch with TeamLead approval.

**Return contract** (per §3.2): All fields mandatory. Missing fields → INCOMPLETE → re-dispatch.

**Branch check** (RD only): Run `git rev-parse --abbrev-ref HEAD` before any edit; halt if on staging/release/production.
```

### 6.2 PO PM (specialization)

> **Mission**: Spec is the source of truth. Keep `/docs` aligned with reality.
>
> **Owns**:
> - `<project>/docs/**`
> - docs-sync between code and spec
> - CCB-Light spec clarifications + ccb-log.md entries
> - Validates Gate_Requirement findings about spec gaps (cross-PM verification per §3.4)
>
> **Failure modes**:
> - Vague requirements → reject; demand measurable criteria
> - Spec drift from code → flag CCB-Heavy
> - Phantom features (no caller) → flag YAGNI

### 6.3 RD PM (specialization)

> **Mission**: Code reflects spec. Tasks decomposed to verifiable units.
>
> **Owns**:
> - `<project>/tasks.md`
> - Code changes per Stage scope
> - Step-review compliance (Sonnet)
>
> **Failure modes**:
> - Spec ambiguity → STOP, raise CCB-Light, do not guess
> - Out-of-scope refactor temptation → STOP, log as RAID-I
> - Branch on staging/release/production → STOP per §6.1 BranchCheck
> - Leaving debug code, .bak files, throwaway scripts past stage close → fail (per CLAUDE.md §清理紀律)

### 6.4 QA PM (specialization)

> **Mission**: 3 gates pass with evidence + structured classifier output, not vibes.
>
> **Owns**:
> - Test plan per Stage
> - Gate_Forward execution + structured classifier output
> - Gate_Human execution (Playwright/chrome) + subjective surface to CEO
> - CodeReview between RD task complete and Gate_Forward
> - Cross-PM verification: independently re-runs ≥1 of RD's claimed test passes per stage (§3.4)
>
> **Failure modes**:
> - Cargo-cult tests (added to add) — fail; each test must mitigate stated risk
> - "Gate passed because nothing crashed" — fail; require positive evidence
> - Auto-pass subjective UX items without CEO touch — fail (R5 mitigation)

### 6.5 UX PM (specialization)

> **Mission**: Mezzanine compliance + UX coherence.
>
> **Owns**:
> - UX evaluation pre-Stage
> - Mezzanine pattern check (invoke skills synchronously: `mezzanine-antipatterns`, `using-mezzanine-ui-react`)
> - Style discipline check (`styling-discipline.md`)
> - Post-build UI artifact review
>
> **Skill availability check**: Before invoking mezzanine-* skills, verify they're listed in available-skills system-reminder. If missing, fall back to inline reading of `~/.claude/rules/mezzanine-ui.md` and `styling-discipline.md`.
>
> **Failure modes**:
> - Skipping pre-Stage UX assessment — fail
> - Post-build review without skill content reference — fail

### 6.6 Ad-hoc PM template

For domains outside the 4 standard PMs (Security / DevOps / Data PM). TeamLead injects custom Mission / Owns / Failure modes block. Used sparingly.

---

## 7. Three Gates — Detailed Mechanics (with structured classifier)

All three gates output the same classifier schema (resolves Arch MED-1):

```json
{
  "verdict": "PASS | PARTIAL | FAIL | INCONCLUSIVE",
  "root_cause": "code_bug | spec_ambiguity | spec_gap | environmental | inconclusive",
  "evidence": "<citation: spec section anchor + code line + observed behavior>",
  "suggested_owner": "<PM name>",
  "dod_status": "met | partial | missed",
  "non_functional_findings": [{type: "perf|security|a11y|reliability", severity: "high|med|low", note: "..."}]
}
```

TeamLead routes on `root_cause`, NOT on prose. INCONCLUSIVE → escalate CEO immediately (per /opus-review pattern in auto-cadence). `non_functional_findings` is a NEW field per PMP MED-2 — captures perf/security/a11y findings even when verdict=PASS. `dod_status` is added per Round 2 PMP NH1 — gate verdict alone is insufficient; gate must explicitly check whether the DoD was met.

### 7.0 Classifier parse failure (NEW per Round 2 Arch NH4)

Output emitted as fenced ` ```json ` block. TeamLead extracts via regex parse. Failure modes:

- **JSON parse exception** → TeamLead returns INCOMPLETE to gate executor with raw output + parse error message embedded
- **Re-dispatch ONCE** with corrected schema reminder
- **Second malformed** → escalate CEO with both raw outputs preserved verbatim (NO prose fallback, NO best-effort interpretation)

This unifies with §3.2 PM dispatch return contract (same INCOMPLETE → re-dispatch → escalate pattern).

### 7.1 Gate_Forward — code logic trace

- **Question**: 「程式跑起來符不符合我們以為它會做的事？」
- **Executor**: QA PM dispatches Sonnet
- **Tools**: Read, Grep, Bash for unit-test
- **Pass**: Sonnet returns step-by-step trace ending in observed correctness + structured classifier
- **Fail handling**: Route per `root_cause` → matching PM (RD for code_bug, PO+CCB for spec_*)
- **Retry cap**: 2 rounds

### 7.2 Gate_Human — UI operational verification

- **Question**: 「真人操作介面，行為是不是預期的？」
- **Executor**: QA PM via `playwright-cli` / `claude-in-chrome` MCP
- **Subjective items**: QA captures evidence → returns to TeamLead → TeamLead surfaces to CEO via AskUserQuestion (cannot auto-pass)
- **Fail handling**: Route per `root_cause`; UX issues → UX PM lead, code defects → RD PM lead

### 7.3 Gate_Requirement — external expert alignment

- **Default**: Final Stage only (cost mitigation per Arch HIGH-3)
- **Mid-stage opt-in**: CEO approves at CEO_Gate_(N-1)
- **Executor**: TeamLead runs `scripts/gate-requirement-runner.sh` which wraps `claude -p`

**Handoff contract** (NEW per Round 2 Int NEW-H3 — `claude -p` is a fresh Claude session, does NOT inherit context, only env + stdin):

1. TeamLead writes a temp manifest file: `/tmp/teamlead-gate-req-<timestamp>.json` containing all inputs:
   ```json
   {
     "stage_name": "...",
     "stage_scope": "...",
     "docs_paths": ["<absolute-path>"],
     "code_diff": "<git diff output, or file listing if non-repo>",
     "rules_paths": ["~/.claude/rules/auto-review-cadence.md", ...],
     "prompt": "Does this implementation satisfy the documented requirements and project conventions? Output classifier per §7 schema."
   }
   ```
2. `scripts/gate-requirement-runner.sh` receives manifest path via argv: `gate-requirement-runner.sh /tmp/teamlead-gate-req-<timestamp>.json`
3. Script reads manifest, builds full prompt embedding all referenced files, pipes to `claude -p`
4. Captures `claude -p` output (must be ` ```json ` block per §7.0); parse failure → INCOMPLETE per §7.0
5. Manifest file deleted on success (per CLAUDE.md §清理紀律)

- **Output**: structured classifier (PASS/PARTIAL/FAIL + root_cause)
- **Cost note**: each run = full Claude session; costs ~50-100kT. Surfaced in token tally.

### 7.4 Gate sequencing under failure

Sequential, no skipping. If Gate_Forward fails, retry only Gate_Forward. Other gates blocked until prior passes.

---

## 8. CCB Tracks

### 8.1 CCB-Light (within-session, scoped clarification)

**Triggers** (any one):
- Spec ambiguous, PO can clarify in <30 lines without scope/budget change
- New requirement fits within current stage scope and budget
- Naming / formatting standardization

**Process**:
1. Triggering PM raises CCB-Light request to TeamLead
2. PO PM updates `docs/` with `<!-- ccb: clarify YYYY-MM-DD — <one-line rationale> -->` marker
3. **PO ALSO appends one-line entry to `<project>/docs/decisions/ccb-log.md`** (NEW per Arch MED-3 + PMP MED-1):
   ```
   YYYY-MM-DD | section: <doc-anchor> | rationale: <one line> | original→new (line range)
   ```
4. TeamLead acks
5. RD PM continues with updated spec

**Audit cap (NEW)**:
- ≥3 CCB-Light entries within one stage touching same doc section → TeamLead auto-escalates to CCB-Heavy
- ≥5 CCB-Light entries within one stage total → TeamLead surfaces to CEO as potential scope creep

### 8.2 CCB-Heavy (cross-session or scope-changing)

**Triggers** (any one):
- Scope change (new feature not in Charter)
- Budget change (time/milestone/retry-cap revision)
- Cross-session work (spec rewrite spanning sessions)
- Spec contradiction with shipped code (migration needed)
- **Risk-driven change** (mitigation requires shift) (NEW per PMP MED-1)
- **Regulatory/compliance-driven change** (external standards) (NEW per PMP MED-1)
- **CCB-Light cap escalation** (per §8.1)

**Process**: same as v1 — PO drafts CR, TeamLead recalculates budget, **CEO_Gate (extraordinary)** for decision.

---

## 9. Budget Model

### 9.1 Hard knobs (C — declared in BudgetProposal)

| Knob | Default | Hard limit |
|---|---|---|
| `milestones` | per project | — |
| `pms` | 1-4 standard + 0..n ad-hoc | — |
| `retry_cap_per_gate` | 2 | 2 (matches auto-cadence) |
| `retry_cap_per_step` | 1 | 1 (matches auto-cadence) |
| `parallel_pm_limit` | 2 | 4 |
| `gate_requirement_mode` | `final_only` | mid-stage opt-in via CEO |

### 9.2 Soft signals (A — reported in StageReport)

| Signal | Format |
|---|---|
| Per-stage tokens | "~Yk this stage" |
| Cumulative tokens | "~Wk total / Z% of declared baseline" |
| Wall clock | "Stage took N turns over M min" |
| Sub-agent dispatch count | "1 Opus plan-audit, 6 Sonnet step-review, 3 Sonnet trace, 0 claude-p" |
| CEO touch-points | "3 this stage" |

### 9.3 Realistic baseline (recalibrated per Arch HIGH-3)

Per-stage typical cost: **180-280 kT** (PlanAudit Opus + 6-10 step-reviews + Gate_Forward + optional Gate_Human + 4 PM dispatches).

CEO_Gate_0 BudgetProposal should declare per-stage baseline × milestones, not total.

### 9.4 Cost circuit breaker (NEW per Arch HIGH-3 + R2 MED-9)

- **Stage 1 80% trigger**: TeamLead annotates `[CALIBRATION-WARMUP]` tag, presents as informational not action-required (Stage 1 typically over-baseline due to setup overhead). Re-baseline at CEO_Gate_1 if Stage 1 actual exceeds declared by ≥30%.
- **Stage 2+ 80% of declared per-stage** → TeamLead proactively flags in Last Action; offers re-baseline at next CEO_Gate
- **Any stage 100% of declared per-stage** → mandatory CEO check-in mid-stage
- **2× cumulative declared** → mandatory CEO_Gate (extraordinary), automatic stage pause until CEO decides

### 9.5 Knob breach handling

Knob breach (retry_cap exceeded, parallel_pm_limit exceeded) → mandatory CEO escalation; cannot be auto-resolved.

---

## 10. Iteration Mechanism (renamed from "/loop integration")

> **Important correction (per Integration Reviewer HIGH-1)**: the user-installed `loop` skill is an INTERVAL-FIRE scheduler, not an "until-condition" iterator. Wrapping `/loop` around Execution misuses the skill. The correct primitive is **`superpowers:subagent-driven-development`** (or `superpowers:executing-plans`), which already provides per-task dispatch + review checkpoint pattern.

### 10.1 Inside Stage Execution

- TeamLead invokes `superpowers:subagent-driven-development` over RD's tasks.md items for the current stage
- Each task: dispatch sub-agent (Sonnet) → step-review (Sonnet) → mark complete
- Step-review FAIL → 1 retry; still fail → escalate to TeamLead
- Loop exits when all tasks for stage are completed OR escalation

### 10.2 Cadence enablement (auto-disable conditions)

PlanAudit + StepReview reviewer dispatches are **disabled** when ANY of these (matches `auto-review-cadence.md` §4 verbatim):

- `CI=true` / `CI=1`
- `CLAUDE_AUTO_CADENCE=off`
- No TTY (non-interactive shell)
- Autonomous-loop sentinels (`<<autonomous-loop>>`, `<<autonomous-loop-dynamic>>`)
- Auto Mode banner present
- **Opt-out token in user message** (NEW — Integration Reviewer LOW-3): `「先快過一輪」` / `「skip review」` / `「skip cadence」` → suspend reviewer dispatches for session

**Important**: Stage Gates (Forward/Human/Requirement) and CEO Gates remain ACTIVE under all hard-guard conditions. Cadence guards apply only to optional reviewer cadence, not to user-required verification. Disabled state means: still run gates, but skip mid-loop step-reviews.

### 10.3 Stage boundary forces iteration break

`subagent-driven-development` MUST NOT cross stage boundaries (must stop before any Gate_*). After stage tasks complete (or step-review hard-fail), iteration exits, TeamLead runs Gates sequentially, then CEO_Gate_N. Only after CEO approves does TeamLead optionally resume iteration for next stage.

---

## 11. Optimizations & Safeguards

### 11.1 Parallel PM dispatch

PO + UX run concurrently in pre-Execution Planning. TeamLead launches both via parallel Task tool calls in same turn. Bounded by `parallel_pm_limit`.

**Frozen PROGRESS.md snapshot**: TeamLead reads PROGRESS.md once before parallel dispatch, embeds the relevant excerpt in each PM's intake header. PMs do NOT re-read PROGRESS.md from disk during dispatch (avoids stale-vs-fresh race).

### 11.2 RAID register (with status fields per PMP MED-3)

Format in `PROGRESS.md ## RAID Register`:

```
- [R] <risk> | likelihood: low/med/high | impact: low/med/high | mitigation: <plan> | status: open/mitigating/closed | owner: <PM> | review_date: YYYY-MM-DD
- [A] <assumption> | validates if: <criterion> | validation_status: pending/validated/invalidated | validated_at: YYYY-MM-DD
- [I] <issue> | severity: low/med/high | owner: <PM> | next action: <step> | status: open/closed
- [D] <dependency> | external: y/n | blockedBy: <thing> | status: open/resolved
- [V] <value-criterion> | hypothesis: <expected outcome> | realized: pending/yes/partial/no | measured_by: <evidence>
```

`[V]` value entries (NEW per PMP HIGH-1) are linked to dispatches' `value_hypothesis` field.

**Burndown**: StageReport's `## RAID Burndown` lists deltas — risks closed this stage, assumptions validated, issues still open count, dependencies resolved. Stale assumptions (>2 stages unvalidated) auto-promote to risks.

### 11.3 Stale state guard (extends auto-cadence pattern)

> **Extends** auto-review-cadence's Plan staleness guard pattern (mtime + sha256 snapshot) to PROGRESS.md / tasks.md / docs/.

TeamLead is sole writer of PROGRESS.md. Before any TeamLead auto-edit:
1. Snapshot mtime + sha256
2. Compare immediately before write
3. Mismatch → bail, surface diff to CEO
4. Backup `<file>.bak.<timestamp>` before write

PMs return payloads (not direct writes), so PMs don't trigger this guard.

### 11.4 Token tally per stage

Per §9.2 / 9.3 / 9.4. Reported in StageReport.

### 11.5 Flat dispatch (hard rule per Arch HIGH-3)

- TeamLead → PM (single Task subagent layer)
- PM does NOT Task-dispatch sub-agents UNLESS:
  - Plan declares parallel-dispatch
  - TeamLead approves at PlanAudit
  - Counted toward `parallel_pm_limit` knob
- Reviewer dispatches (Opus, Sonnet) all originate from TeamLead
- Skill tool invocation (writing-plans, mezzanine-antipatterns) is allowed in PM context (synchronous in-context load, not Task) — but PM MUST intercept any handoff attempt (e.g., writing-plans → executing-plans) and return artifact instead

### 11.6 PROGRESS.md size discipline (NEW per Arch HIGH-2 + R2 H2 tightening)

- **Hard ceiling**: 2000 lines
- **Trigger ownership** (NEW per Round 2 Arch H2 partial-resolution): TeamLead checks line count after EVERY write. Two-policy archival:
  - **StageReport archival**: when ceiling hit, archive oldest stage's StageReport → `docs/stage-archives/stage-N.md`; replaced with `<!-- archived to docs/stage-archives/stage-N.md -->` back-reference (one line)
  - **RAID archival**: closed/validated/resolved entries older than 2 stages → moved to `docs/stage-archives/raid-archive.md` (cumulative file)
- **Calibration warning**: 2000 lines is tight for >10-stage projects with rich RAID. If projection (current line count + projected next-stage delta) > 2000, TeamLead warns CEO at CEO_Gate_(N-1) to consider archival cadence increase OR re-baseline
- **Default PM intake**: TeamLead embeds relevant excerpt only (current stage state + active RAID), not full PROGRESS.md
- **On-demand full read**: PM may explicitly request full PROGRESS.md via dispatch return field; TeamLead provides

### 11.7 Branch discipline integration (NEW per Integration MED-1)

- Discovery phase: `git rev-parse --abbrev-ref HEAD` check; warn if on staging/release/production
- RD PM intake: same check before any code edit
- Per `~/.claude/rules/branch-discipline.md`

### 11.8 Cleanup discipline integration (NEW per Integration MED-2)

- ProjectClose CleanupGate (§5.4) — no batch delete without ownership classification + CEO approval
- Per `~/CLAUDE.md §清理紀律`

### 11.9 Memory entry on ProjectClose (NEW per Integration MED-3)

- ProjectClose MemoryEntry step (§5.4) writes `~/.claude/projects/<encoded-home>/memory/project_<slug>.md` (`<encoded-home>` per `references/pmp-lessons-learned.md` §Step 4)
- Append one-liner to `MEMORY.md ## Projects` index

### 11.10 Exception reporting tier (NEW per PMP LOW-2)

When budget breach / gate FAIL / RAID escalates / CCB-Heavy raised, TeamLead emits an `## Exception` entry separate from `## Last Action`, surfaces immediately to CEO via AskUserQuestion mid-stage (not just at gate boundary).

---

## 12. Reuse Map (clarified relationships)

| Phase | Existing skill / rule | How (corrected) |
|---|---|---|
| Discovery | `superpowers:brainstorming` rubric | **Inline rubric only**; do NOT auto-invoke skill (its HARD-GATE doesn't compose). TeamLead asks brainstorming-style questions in own state machine. |
| TeamFormation | TeamLead | — |
| BudgetProposal | `templates/budget-proposal.md.tpl` | Local template |
| Planning | `superpowers:writing-plans` rubric | **Inline rubric**; PMs follow structure but emit plans for TeamLead, do NOT trigger writing-plans' executing-plans handoff |
| PlanAudit | `auto-review-cadence.md` §Planning rubric | TeamLead replicates rubric in dispatch prompt (parameterization, not duplication) |
| Execution iteration | **`superpowers:subagent-driven-development`** | TeamLead invokes; replaces v1's `/loop` misuse |
| Step-review | `auto-review-cadence.md` §Coding rubric | TeamLead dispatches per step |
| Gate_Forward | Sonnet trace + structured classifier | QA PM |
| Gate_Human | `playwright-cli` / `claude-in-chrome` | QA PM |
| Gate_Requirement | `claude -p` via `scripts/gate-requirement-runner.sh` | TeamLead |
| Stale guard | `auto-review-cadence.md` Plan staleness pattern | Extended to PROGRESS.md/tasks.md/docs/ |
| Cadence hard guards | `auto-review-cadence.md` §4 | Inherited verbatim + opt-out tokens |
| Final review (optional) | `/opus-review final` | TeamLead invokes; **must check `git rev-parse --is-inside-work-tree` first** — for non-repo workspaces, downgrade to inline review or skip with CEO consent. Do NOT auto-invoke under Auto Mode without explicit CEO opt-in. |
| Cleanup | `~/CLAUDE.md §清理紀律` | All PMs follow + ProjectClose CleanupGate |
| Branch check | `~/.claude/rules/branch-discipline.md` | Discovery + RD PM intake |
| Memory entry | User memory pattern | ProjectClose MemoryEntry |
| Mezzanine | `mezzanine-*` skills + `mezzanine-ui.md` rule | UX PM (with availability fallback) |

---

## 13. Implementation Phases

### Phase 0 — Plugin scaffold

- [x] Plugin directories created
- [x] `plugin.json` manifest
- [x] design doc v2 (this file) — 9 HIGH revisions applied
- [ ] CEO approval

### Phase 1 — Skeleton workflow (MVP)

- [ ] `commands/teamwork-leader.md` — entry command
- [ ] `skills/teamwork-leader-workflow/SKILL.md` — team rules + state machine
- [ ] `skills/teamwork-leader-workflow/references/*.md` (10 files per §4.1)
- [ ] `agents/po-pm.md`, `rd-pm.md`, `qa-pm.md`, `ux-pm.md`, `ad-hoc-pm.md`
- [ ] `templates/*.tpl` (8 templates per §4.1)
- [ ] `scripts/gate-requirement-runner.sh`
- [ ] Smoke test on toy project: Discovery → CEO_Gate_0 → Stage_1 (no Gate_Requirement) → Stage_1 close

### Phase 2 — Gate machinery + classifier

- [ ] `references/three-gates.md` with classifier output schema
- [ ] Gate_Forward dispatch template + classifier validation
- [ ] Gate_Human Playwright integration
- [ ] Gate_Requirement runner script + Final-only default

### Phase 3 — CCB + audit log

- [ ] `references/pmp-ccb.md` with full Light/Heavy
- [ ] `templates/ccb-light.md.tpl`, `ccb-heavy.md.tpl`, `ccb-log.md.tpl`
- [ ] CCB-Light cap auto-escalation logic

### Phase 4 — Optimizations & PMP completeness

- [ ] Parallel dispatch helper
- [ ] RAID burndown w/ status fields
- [ ] Stale guard wrapper
- [ ] Token tally + circuit breaker
- [ ] CI hard-guard auto-disable check + opt-out tokens
- [ ] Wave Refinement step
- [ ] Schema migration handler
- [ ] Branch check at Discovery + RD intake

### Phase 5 — ProjectClose

- [ ] LessonsLearned dispatch protocol
- [ ] CleanupGate Sonnet prompt
- [ ] MemoryEntry drafter
- [ ] CEO_Gate_Final formal acceptance

### Phase 6 — Self-dogfood

- [ ] Use `/teamwork-leader` on a real internal codebase (multi-deliverable, multi-PM-role candidate)
- [ ] Capture lessons-learned in user memory; iterate on plugin

---

## 14. Open Questions & Risks (post-revision)

### Open Questions (status updates)

- **OQ1 (open)**: PM 工作說明書 (external reference doc) — currently inaccessible; using PMP defaults until provided.
- **OQ2 (resolved)**: TeamLead via SKILL.md (description-matched + reference-loaded by command) ✓
- **OQ3 (resolved)**: Gate_Requirement default = Final Stage only; mid-stage opt-in via CEO_Gate_(N-1) ✓ (per Arch HIGH-3)
- **OQ4 (new)**: TeamLead pre-checks `enabledPlugins` for required skills (mezzanine-*, playwright-cli) before TeamFormation? **Recommendation**: yes; surface missing skills to CEO so PMs don't dispatch and silently fall back.

### Risks (with mitigations updated)

- **R1 (med→low)**: Subagent context bleed — mitigated by §6.1 frozen PROGRESS.md excerpt embed
- **R2 (med)**: CEO impatience with stage gates — mitigated by SKILL.md non-skip rule; CEO can `pause` or `abort`, never bypass gate
- **R3 (low)**: SKILL.md token cost — mitigated by reference-link pattern
- **R4 (med→low)**: PROGRESS.md unbounded growth — mitigated by §11.6 size discipline
- **R5 (high→med)**: Gate_Human auto-pass risk — mitigated by §7.2 + AskUserQuestion for subjective items
- **R6 (med→resolved)**: Multi-PM PROGRESS.md concurrent write — resolved by §3 TeamLead-sole-writer
- **R7 (NEW high)**: Token cost runaway across multi-stage projects — mitigated by §9.4 circuit breaker (2× declared = mandatory pause)
- **R8 (NEW med)**: Schema collision with existing PROGRESS.md — mitigated by §5.6 migration prompt
- **R9 (NEW med)**: Skill availability mismatch in subagent context — mitigated by §6.5 availability check + fallback

---

## 15. Acceptance Criteria

Design v2 acceptable when:

1. ✓ Three Opus reviewers' HIGH issues all addressed (9/9 confirmed in this v2)
2. CEO reviews v2 and approves
3. ✓ All "OQ" entries resolved or explicitly deferred (OQ1 deferred to user input; OQ2/OQ3 resolved; OQ4 new)
4. ✓ All "R" entries have stated mitigations (9/9)
5. ✓ Reuse map confirms no duplication; explicit fork-and-cite for brainstorming/writing-plans

---

## 16. Quickstart (preview)

```
$ /teamwork-leader

[CEO] Welcome. What project / improvement plan are we working on?
> <use case>

[TeamLead] Discovery summary:
- Goal: ...
- Surface: ...
- Likely PMs: PO, RD, QA (UX optional)
- Branch check: on `main` ✓ (not staging/release/production)
- Existing PROGRESS.md: not found → will scaffold from template
- Likely milestones: 3 stages (per rolling-wave: Stage 1 task-level, Stage 2-3 milestone-level)

Shall I draft the Budget Proposal? [y/n]
> y

[TeamLead] (writes PROGRESS.md ## Charter + ## Budget Baseline)

★ CEO_Gate_0 — Charter & Budget Approval
- Milestones: 3 (Stage 1 task-level decomposed; 2-3 milestone-level placeholders)
- PMs: PO, RD, QA
- Caps: retry_cap_per_gate=2, retry_cap_per_step=1
- Parallelism: parallel_pm_limit=2
- Gate_Requirement: Final Stage only (default)
- Per-stage budget baseline: ~250 kT (Sonnet-heavy)
- Cost circuit breaker: 80%/100% per-stage flags, 2× cumulative = mandatory pause

Approve to begin Stage 1? [approve / revise / abort]
> approve

[TeamLead] Stage 1 commencing. Dispatching PO PM and RD PM in parallel for planning...
```

---

## Appendix A — Reviewer summary

### Round 1 (v1 → v2 changes)

3 parallel Opus reviewers (architecture / PMP / integration) audited v1. All returned APPROVED_WITH_REVISIONS.

**HIGH issues addressed (9/9)**:
- Arch H1 (PROGRESS.md race) → §3 TeamLead sole-writer
- Arch H2 (unbounded growth) → §11.6 size discipline + archival
- Arch H3 (token cost runaway) → §9.3 recalibrated baseline + §9.4 circuit breaker + §11.5 flat dispatch hard rule
- PMP H1 (Value-Driven not measured) → §3.2 Value Hypothesis field + §11.2 [V] entries + StageReport Value Realized
- PMP H2 (lessons-learned missing) → §5.4 ProjectClose flow with LessonsLearned + MemoryEntry
- PMP H3 (WBS depth missing) → §5.5 wave depth rule + WaveRefinement step
- Int H1 (/loop misuse) → §10 replaced with subagent-driven-development; cadence enablement separated from gate enablement
- Int H2 (brainstorming/writing-plans handoff conflict) → §12 explicit "inline rubric, do not auto-invoke" + §6.1 PM intake interception rule
- Int H3 (skill chain depth) → §6.1 + §11.5 explicit Skill (in-context) vs Task (dispatch) distinction

### Round 2 (v2 → v3 changes)

3 parallel Opus reviewers (architecture / PMP / integration) audited v2. All returned APPROVED_WITH_REVISIONS.

**Round 1 HIGH issue resolution status (per round 2 verifiers)**:
- Arch H1 (race) → **RESOLVED**
- Arch H2 (growth) → **PARTIALLY** — ceiling triggers ambiguous (now tightened in v3 §11.6)
- Arch H3 (cost) → **RESOLVED**
- PMP H1 (Value) → **PARTIALLY** — DoD declared mandatory but NOT enforced at gate close (fixed in v3 §3.2 dod_status field + §5.2 CEO_Gate DoD check + §7 classifier dod_status)
- PMP H2 (lessons) → **PARTIALLY** — lessons-learned format unstructured (deferred to Phase 5 reference doc)
- PMP H3 (WBS) → **RESOLVED**
- Int H1 (/loop swap) → **RESOLVED**
- Int H2 (skill-load HARD-GATE inheritance) → **PARTIALLY** — interception fragile (fixed in v3 §6.1 by FORBIDDING those skills entirely)
- Int H3 (chain depth) → **RESOLVED**

**Round 2 NEW HIGH issues addressed (6/6)**:
- Arch NH4 (classifier malformed-JSON fallback) → §7.0 INCOMPLETE → re-dispatch → escalate; no prose fallback
- PMP NH1 (DoD enforcement at gate close) → §3.2 + §7 + §5.2 dod_status field; CEO_Gate DoD check before approve
- PMP NH2 (Charter immutability vs WaveRefinement) → §5.5.1 explicit rule + tripwire
- Int NEW-H1 (subagent-driven-development main-branch consent) → §5.1 BranchCheck expanded for main/master
- Int NEW-H2 (subagent-driven-development worktree REQUIRED) → §5.1 WorktreeDecision step at CEO_Gate_0
- Int NEW-H3 (claude -p handoff contract) → §7.3 manifest file pattern with tmp file + argv + stdin

**Round 2 MED issues addressed (5 of 13)**:
- Arch MED-9 (calibration warmup Stage 1) → §9.4 [CALIBRATION-WARMUP] tag
- Arch MED-6 (schema migration backup) → §5.6 explicit .bak.timestamp before write
- PMP NM5 (CEO verb set) → §5.2 expanded to 6 verbs
- Int NEW-M3 (option-c side-file naming) → §5.6 substitution rule
- Int NEW-M4 (CleanupGate prompt 清理紀律) → §5.4 mandatory embed
- Int NEW-M5 (MEMORY.md format conformance) → §5.4 explicit format + §11.3 stale guard
- Int NEW-M6 (JSON parsing robustness) → §3.2 fenced ```json block

**Round 2 deferred to Phase 1-5 implementation** (tracked in §14 Open Questions):
- Arch MED-7 (atomic Last Action + State + Stage History write) — Phase 4 implementation
- Arch MED-10 (sampling rotation discipline) — Phase 4 reference doc
- PMP NM1 (Self-Audit ↔ Lessons-Learned consolidation) — Phase 5 reference doc
- PMP NM2 (UX cross-verifies RD's Mezzanine) — Phase 4 reference doc
- PMP NM3 (high-impact risk closure ack) — Phase 4 reference doc
- PMP NM4 (CCB-Light cap calibration) — Phase 6 self-dogfood
- PMP NM6 (WaveRefinement+CEO_Gate cognitive bundling) — Phase 4 (resolution: refined N+1 plan informational at gate per §5.5.1)
- Int NEW-M1 (Auto Mode + CEO_Gate reconciliation) — Phase 4 doc
- Int NEW-M2 (enabledPlugins API) — Phase 4 (try-and-catch fallback)
- Int NEW-M7 (WaveRefinement under cadence-disabled) — Phase 4 (mark as `[CLAIMED]`)

Token cost of review rounds: ~270 kT (Round 1) + ~270 kT (Round 2) = **~540 kT total** for spec validation.

**MED issues addressed (selection)**:
- Arch M1 (gate routing decidability) → §7 structured classifier
- Arch M2 (anti-rubber-stamp impl) → §3.2 mandatory rejection + §3.3 sampling policy
- Arch M3 (CCB-Light scope drift) → §8.1 cap + ccb-log.md
- PMP M1 (CCB categories) → §8.2 risk-driven + regulatory triggers
- PMP M2 (non-functional V&V) → §7 classifier `non_functional_findings`
- PMP M3 (RAID burndown) → §11.2 status fields + burndown
- PMP M4 (single-point-of-failure TeamLead) → §3.4 cross-PM verification + §3.3 Self-Audit
- Int M1 (branch discipline) → §11.7 + §6.3 RD intake
- Int M2 (cleanup) → §5.4 CleanupGate + §11.8
- Int M3 (memory) → §5.4 MemoryEntry + §11.9
- Int M4 (/opus-review repo guard) → §12 explicit guard
- Int M5 (schema migration) → §5.6

**LOW issues addressed**:
- Arch L1 (`scripts/`) → §4.1 added
- Arch L2 (in-flight dispatch loss) → §5.3 explicit note
- Int L2 (stale guard cite) → §11.3 explicit "extends auto-cadence pattern"
- Int L3 (opt-out tokens) → §10.2 added

Token cost of review round: ~270 kT (3 Opus × ~90kT each).

---

## Appendix B — Decisions captured from brainstorming session

- Q1.B (包住既有 skills)
- Q2.C+A (knobs primary, abstract supplementary)
- Q3-1.B (rolling-wave; now made explicit per PMP HIGH-3)
- Q3-2 (gate routing — now structured classifier per Arch MED-1)
- Q3-3.B>A (CCB triggers; now expanded per PMP MED-1)
- Q3-4 (2-round retry; matches auto-cadence)
- Q3-5 (iteration in stage execution; mechanism corrected to subagent-driven-development per Int HIGH-1)
- Q4.Route-2 + 多 Opus reviewer (delivered)
- A (PM = Task subagent, fresh context, state in files)
- B (nested allowed but flat default — clarified per Int HIGH-3)
- C (Light if same-session-resolvable, Heavy if cross-session/large-scope — clarified)
- D (Gate executors as proposed)
- E (state machine + Last Action Insight; added [TRUSTED]/[CLAIMED] prefix)
- F (auto-scaffold; expanded with §5.6 migration)
- User explicit preferences:
  - Minimize file count (single PROGRESS.md, single tasks.md, no per-project `.teamleader/`) ✓ preserved
  - Every action emits short Insight ✓
  - Cross-project plugin ✓
  - Multiple Opus pre-delivery review ✓ delivered
- External PM 工作說明書 spec sheets — pending access

---

*End of design doc v3 — Phase 1+2 (RSS) + Phase 3 (N1+KMR) ship-complete 2026-05-02.*
