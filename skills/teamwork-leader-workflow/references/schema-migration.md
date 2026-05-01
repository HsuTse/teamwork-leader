# Schema Migration — Existing PROGRESS.md Collision Handling

> **Source of truth**: design doc v3 §5.6. This file operationalizes the migration flow.

When `/teamwork-leader` runs in a project that already has `PROGRESS.md` from prior workflows (`/strategic-compact`, `/last-word`, manual notes, etc.), TeamLead must reconcile.

## Detection

In `/teamwork-leader` boot sequence (per `commands/teamwork-leader.md`):

1. Read `PROGRESS.md` if exists
2. Check for TeamLead state-machine signature sections:
   - `## Active Stage`
   - `## State`
   - `## Last Action`
3. If all 3 present → **Resume mode** (not migration)
4. If PROGRESS.md exists but signature sections missing → **Schema migration mode**

## 3 options surfaced to CEO

Use AskUserQuestion with 3 options:

### Option (a) — Migrate

TeamLead drafts a **merge proposal**: existing sections + TeamLead schema additions, with explicit conflict resolution.

**Backup required (per Round 2 Arch MED-6)**:

1. Before drafting merge → write `PROGRESS.md.pre-teamlead-<timestamp>.bak`
2. Surface full diff via AskUserQuestion: "Review proposed merge. Approve write or revise?"
3. CEO `approve` → write the merged PROGRESS.md (per §11.3 stale guard)
4. CEO `revise` → loop back to draft

**Recovery path**: restore from `.bak` file if migration goes wrong.

**When to recommend (a)**:
- Existing PROGRESS.md is short (<100 lines) and not actively used
- User wants single source of truth going forward
- Migration is one-time conversion

### Option (b) — Coexist

Namespace TeamLead sections with `TeamLead/` prefix. The full namespaced section list mirrors `progress-md-schema.md` §Required sections (state-machine subset shown below for emphasis):

- `## TeamLead/Charter`
- `## TeamLead/Budget Baseline`
- `## TeamLead/Active Stage`
- `## TeamLead/State`
- `## TeamLead/Last Action`
- `## TeamLead/RAID Register`
- `## TeamLead/Stage History`
- `## TeamLead/CCB Activity`
- `## TeamLead/CCB-Heavy Pending` (conditional)
- `## TeamLead/Self-Audit`
- `## TeamLead/Exception` (conditional)
- `## TeamLead/Lessons Learned` (ProjectClose only)

ALL schema sections from `progress-md-schema.md` are namespaced with the `TeamLead/` prefix in option-b mode. Existing sections preserved as-is; TeamLead writes only to namespaced sections.

**When to recommend (b)**:
- Existing PROGRESS.md has active maintenance by other workflows or human reader
- User wants coexistence rather than replacement
- Multiple agents may read PROGRESS.md and shouldn't see TeamLead state

### Option (c) — Side-file

Use `PROGRESS.teamlead.md` as separate file. Existing `PROGRESS.md` untouched.

**Substitution rule (per Round 2 Int NEW-M3)**: All §11.3 stale guard, §3 RACI matrix references to "PROGRESS.md", and §11.6 size discipline references substitute `PROGRESS.teamlead.md` in TeamLead's state for this project. Decision logged once; downstream sections do not need to keep restating the substitution.

**When to recommend (c)**:
- Project has a PROGRESS.md format that conflicts with TeamLead schema (e.g., entirely different structure)
- User explicitly wants two files for separation of concerns
- TeamLead activity is short-lived (one-off project) and shouldn't pollute long-lived PROGRESS.md

## Decision logging

After CEO chooses, TeamLead logs once at the top of the working PROGRESS.md (or PROGRESS.teamlead.md):

```markdown
## Schema decision: <migrate|coexist|side-file> at YYYY-MM-DD
```

This decision is referenced in subsequent operations to disambiguate filename / section names.

## Comparison table

| Aspect | (a) Migrate | (b) Coexist | (c) Side-file |
|---|---|---|---|
| Existing content | Replaced/merged | Preserved | Preserved (untouched) |
| File name | `PROGRESS.md` | `PROGRESS.md` | `PROGRESS.teamlead.md` |
| TeamLead writes | Standard sections | Namespaced sections | Standard sections in side-file |
| Conflict risk | Medium (CEO must approve merge) | Low (separate sections) | None (separate file) |
| Best for | Stale legacy PROGRESS.md | Active multi-workflow project | Short-lived TeamLead use |

## Migration safety checklist (TeamLead must verify before option-a write)

- [ ] `PROGRESS.md.pre-teamlead-<timestamp>.bak` written
- [ ] Diff surfaced to CEO via AskUserQuestion
- [ ] CEO explicitly approved merge
- [ ] §11.3 stale guard mtime+sha256 check passed immediately before write
- [ ] No existing `## Active Stage` / `## State` / `## Last Action` sections will be silently overwritten

If any item fails → halt, surface to CEO, do not proceed.

## After migration

Subsequent TeamLead operations work as if PROGRESS.md was created fresh by `/teamwork-leader`. All §5.3 state field schema, §11.6 size discipline, §11.3 stale guard apply normally.

For options (b) and (c), TeamLead reads ONLY its own namespaced sections / side-file at intake time; does not parse or interfere with existing structure.
