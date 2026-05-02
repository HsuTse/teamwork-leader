# Changelog

All notable changes to the `/teamwork-leader` plugin documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) loosely; semver per `.claude-plugin/plugin.json`.

## [0.1.5] — 2026-05-03

### Fixed

- **`.claude-plugin/marketplace.json` `source` field** — was `{"source": "url", "url": "https://github.com/HsuTse/teamwork-leader.git"}` (object form), which Claude Code's plugin loader does not understand. Changed to `"./"` (relative path string), matching the canonical pattern used by `anthropic-agent-skills`, `knowledge-work-plugins`, and `rytass-claude-code` marketplaces. Without this fix, `/plugin install teamwork-leader@teamwork-leader` could not resolve the plugin source after marketplace add — install silently produced no cache entry.
- Removed non-standard `category: "development"` field from plugin entry (not present in any reference marketplace.json; ignored by loader but kept for cleanliness).

### Why

v0.1.4 GH release was distribution-broken: marketplace add succeeded but plugin install could not complete because the loader couldn't parse `source: {object}`. This is a metadata-only fix — no code/agent/skill content changed from v0.1.4. Anyone who attempted v0.1.4 install should `/plugin marketplace update teamwork-leader` then `/plugin install teamwork-leader@teamwork-leader`.

### Migration

- v0.1.4 installations via **symlink workaround** — first remove the symlink (`rm ~/.claude/plugins/cache/teamwork-leader/teamwork-leader/0.1.4`) before running `/plugin marketplace update`, otherwise the loader may resolve the symlinked path instead of the corrected marketplace metadata.
- v0.1.4 installations via **unsuccessful install attempts** — just run `/plugin marketplace update teamwork-leader` to pick up corrected metadata, then `/plugin install teamwork-leader@teamwork-leader`.
- All v0.1.4 plugin content (discipline references, agent prompts, skills, runbook references) preserved as-is.

## [0.1.4] — 2026-05-02

### Added

- **`references/discipline/` directory** with 6 portable defaults — surgical-change / simplicity / typescript-discipline / testing-discipline / styling-discipline / mezzanine-discipline. Each has §Override footer pointing to project CLAUDE.md.
- **§Discipline references** section in 4 PM agents (rd-pm / qa-pm / ux-pm / po-pm) wiring the applicable subset.
- **§Role discipline references** section in README.

### Changed

- All `~/.claude/rules/*.md` references swept from plugin-internal files (PM agents + dispatch-header.md + stage-runbook.md + three-gates.md + reuse-map.md + pmp-lessons-learned.md + ad-hoc-pm.md + commands/teamwork-leader.md). Plugin now operates without dependency on host `~/.claude/rules/`.
- mezzanine-discipline.md removed user-personal references (`mezzanine.rytass.com` → "project's Storybook URL"; `admin-components` → "project's internal Mezzanine wrapper-package").
- Override mechanism reframed honestly: project `CLAUDE.md` overrides plugin defaults per Claude Code standard precedence (project instructions > plugin guidance) — this is Claude Code's built-in mechanism, not custom plugin loading logic.

### Why

Plugin distribution to other users via marketplace requires self-contained defaults. v0.1.4 makes the plugin work standalone with no dangling references to host-machine files. Project-level customization works through Claude Code's existing instruction-priority mechanism, not via plugin-specific override logic (avoids implementing fragile loading paths).

### Migration

- HsuTse's environment unaffected — host `~/.claude/rules/*.md` continues to load globally for non-plugin work and overrides plugin defaults via project CLAUDE.md when relevant.
- New users get plugin-bundled defaults out of the box; can override via their own project `CLAUDE.md`.



## [0.1.3] — 2026-05-02

### Added

- **Schema validation enforcement** (`stage-runbook.md` §EXECUTING step 5): inline 11-field canonical list with explicit INCOMPLETE → re-dispatch → PASS / second-INCOMPLETE → ESCALATED flow
- **`schema_validation_status` field** in `audit-trail.jsonl` row schema (enum: `pass | rejected_and_retried | rejected_and_escalated | null`)
- **`schema_enforcement_mode` knob** in `budget-proposal.md.tpl` (`strict` default; `warn` / `off` require CCB-Heavy)
- **Schema validation worked examples** section in `stage-runbook.md` (three terminal cases + anti-anchoring note)
- **v0.1.3 rollback contract** documentation (`docs/v0.1.3-rollback.md`)

### Changed

- **`dispatch-header.md` §Return contract** now explicitly documents retry-pool separation: schema-validation re-dispatch has its OWN 1-retry pool, distinct from §EXECUTING step 7 step-review retry pool. Schema correctness fix is structural, not content-quality.
- **`stage-runbook.md` §Error / timeout handling** INCOMPLETE entry rephrased to reference v0.1.3 step 5 schema-validation flow and retry-pool separation.

### Why

BeiliSystem PR #30/#34 dogfood pilot (3 stages, 25 dispatches) observed 3/25 (12%) incomplete returns. Pre-v0.1.3 mechanism was prose-only — INCOMPLETE handling described but no persisted record of validation outcome, ambiguous retry budget, no diagnostic trail when ESCALATED. v0.1.3 closes these gaps with non-interruptive enforcement (PM re-dispatch is no friction; user not interrupted).

Evidence base: 3 events / 25 dispatches / 1 project. Path 3 split-by-evidence-strength (independent 2-Opus deliberation consensus) classifies this as immediate-ship: high-evidence + non-interruptive, no calibration thresholds introduced.

### Migration

- v0.1.2 audit-trail.jsonl rows treated as `schema_validation_status: null` (legacy)
- New rows post-v0.1.3 ship → non-null (unless `schema_enforcement_mode == off`)
- No retroactive backfill
- **In-flight v0.1.2 projects upgrading mid-stage**: see `docs/v0.1.3-rollback.md` §Mid-stage upgrade guidance — recommended path is upgrading at next CEO_Gate boundary; `warn` mode supports one-stage evidence-gathering before flipping to `strict`

### Tag history note

The `v0.1.3` git tag was initially created at commit `142ef7e` (initial schema enforcement ship). After 3-parallel Opus final review returned `PASS_WITH_MINOR` with 4 important findings, a follow-up commit `e88b656` was created to address them inline (per `/opus-review final` blocking rule for important issues). The `v0.1.3` tag was then moved (locally, before push) to point at `e88b656` so that the released v0.1.3 includes both the initial ship AND the review-driven fixes as a single coherent release. Both commits are reachable via `git log v0.1.3` and the move is irrelevant once the tag is pushed (`git push origin v0.1.3` published the final tag location only).

### Final-review addenda (post-Opus PASS_WITH_MINOR)

3 parallel Opus reviewers (Correctness / Security / Doc-sync) returned PASS_WITH_MINOR with 4 important findings; all addressed in-place before tag finalization:

- **A.1**: `stage-runbook.md` §EXECUTING step 5 now documents `warn` mode runtime behavior (was only in template + rollback doc)
- **A.minor**: `step 5` second-INCOMPLETE → ESCALATED branch now documents `kmr_*` field nulling + Phase 3/4 calibration query filter
- **B.1**: `docs/v0.1.3-rollback.md` §Migration adds mid-stage upgrade guidance (defer to CEO_Gate boundary OR start with `warn`)
- **B.2**: `templates/budget-proposal.md.tpl` + rollback doc tighten initial-baseline rule — `warn`/`off` declared at Stage 1 BudgetProposal also requires CCB-Heavy ratification (not just mid-flight transitions)
- **C.1**: `README.md` synced — version badge → 0.1.3, §狀態與限制 reflects BeiliSystem dogfood completion + outstanding N≥2 gate, §Roadmap 3 items checked off + 3 new items, §核心特色 adds dispatch-level schema validation section

### Related

- Origin issue: `~/.claude/projects/-Users-HsuTse/memory/issues/teamwork-dispatch-schema-enforcement.md`
- Decision context: 2-Opus deliberation 2026-05-02 (split-by-evidence-strength)

## [0.1.2] — 2026-05-02 (prior)

Phase 3 N1 trust_tier + KMR per-task divergence proxy ship-complete with 8 final-Opus fixes in-place. Reference: `~/.claude/projects/-Users-HsuTse/memory/decisions/teamwork-leader-phase-3-shipment.md`.

## [0.1.1]

Version bump.

## [0.1.0]

Initial release.
