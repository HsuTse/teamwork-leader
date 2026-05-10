# Changelog

All notable changes to the `/teamwork-leader` plugin documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) loosely; semver per `.claude-plugin/plugin.json`.

<!-- Entry conventions (forward-going `### Notes` plural; ### Note: avoided): see docs/conventions/changelog.md -->

## [0.1.10] — 2026-05-10

### Added

- **Daemon FROZEN-spec deltas** — `scripts/daemon.py` + `docs/specs/auto-resume-daemon-design.md` updated for I-061 (array structure cosmetic-as-doc per v0.1.7 classification), I-064 (single-line format normalization), I-065 (argparse mutually_exclusive_group), I-071 (post-hoc TeamLead-coined keys → canonical naming). All changes authorized as FROZEN-DELTA per Opus PlanAudit explicit notation.
- **Hook hardening D-1+D-2+D-3** — `~/.claude/hooks/pretooluse_guard.py` (out-of-tree): D-1 opaque ask-reason fix (first ~120 chars of cmd in reason string); D-2 open-path-branch collapsed to exact plist filename; D-3 compound-operator detection (`;`/`&&`/`||`/`|` strip before whitelist exception fires). In-repo evidence at `docs/security/v0.1.10-hook-hardening.md` (151 lines; 6 sections; FN-1/FN-2/FN-3 attack scenarios + before/after regex + smoke transcript).
- **`docs/specs/measurement-protocol.v0.1.10.md`** — corrected C-4 timeout 60→90s (engineering rationale: ThrottleInterval 10s + cold-start launchd overhead; v0.1.9 spec text was copy-paste error; v0.1.9 actual runs used 90s and are evidence-truth). Includes `§methodology-deviations` with deviation-3 (local PROVEN-UNAVAILABLE env-class) + deviation-4 (GHA PROVEN-INTEGRATION-GAP).
- **AC-9 Python ≥3.10 hard gate** — `.github/workflows/measure-execution.yml` lines 59-62: `python3 --version` assert step added; env-class hard gate at workflow level.
- **deviation-3** (CCBL-Stage2-v0.1.10-T21-LOCAL-BLOCKED) — `measurement-protocol.v0.1.10.md §methodology-deviations`: T-2-1 BLOCKED by system python3 3.9.6 on macOS 15.3 (plist `/usr/bin/python3`; PEP 604 syntax crash) + launchctl bootout/bootstrap hard-denied by hook after repeated approved ask-prompts (D-3 escalation behavior). AC-7(i) status: PROVEN-UNAVAILABLE on local macOS 15.3 host class.
- **deviation-4** (CCBL-Stage2-v0.1.10-T22-GHA-INTEGRATION-GAP) — `measurement-protocol.v0.1.10.md §methodology-deviations` + `docs/archives/measurement-real-claude-gha.v0.1.10.md` (151 lines, 4 hypothesis vectors): GHA run 25532761179 Candidate A real-claude path — install-layer PASS (claude 2.1.133 installed per cold cycle ~13s) but 10/10 cold + 10/10 warm SESSION_RESUMED never reached. Root cause: daemon polling target designed against stub-claude artifact format; does not match what real claude produces on `--resume`. AC-7(ii) status: PROVEN-INTEGRATION-GAP.
- **PM-discipline pre-emit `meta` integer guard table** — `skills/teamwork-leader-workflow/agents/po-pm.md`: guard table with 5 int + 2 enum + 1 bool fields; closes RAID-I-SCHEMA-1 (PO meta integer self-check).
- **`docs/specs/auto-resume-daemon-design.md §7 term (f)`** — cold-start reliability budget: cold p50=15.5s / 30s gate = 52% utilization / 48% headroom; cross-referenced to measurement archive and measurement-protocol.v0.1.10.md. AC-8 realized as §7 term (f) per CCBL-Stage2-v0.1.10-T24-ANCHOR.

### Changed

- **PROGRESS.md state machine** — ESCALATED → REPORTING via CCB-Heavy `revise_charter` (CCBH-v0.1.10-AC7-DEMOTE-V0.1.11; CEO verb=approve 2026-05-10T09:03:41+08:00). Stage 2 closes PARTIAL via CCB-Heavy approve route.
- **Charter §APPENDED 2026-05-10** (CCBH-v0.1.10-AC7-DEMOTE-V0.1.11) — AC-7 demoted from v0.1.10 must-have to v0.1.11-deferred. AC-1..AC-6 + AC-8 + AC-9 + AC-10 all met.

### Why

AC-7 (real-claude end-to-end measurement) PROVEN-BLOCKED on both host classes with comprehensive empirical proof: local PROVEN-UNAVAILABLE env-class (system python3 3.9 on macOS 15.3 + hook hard-deny escalation behavior) + GHA PROVEN-INTEGRATION-GAP (10/10 cold + 10/10 warm SESSION_RESUMED never reached because daemon's polling target was implicitly designed against stub-claude artifact format). This is a v0.1.7 daemon-design assumption that surfaced at v0.1.10's first real-claude end-to-end attempt. CCB-Heavy `revise_charter` demoted AC-7 to v0.1.11; release proceeds with what's done. Production usage signal (patent-examiner-plugin + BeiliSystem) acknowledged as real-world adoption beyond self-dogfood. 5 v0.1.11 carry-forward RAIDs registered: RAID-V11-real-claude-integration (HIGH — gating prerequisite for AC-7 retry) + RAID-V11-install-lifecycle-python3-path (MED) + RAID-V11-ccb-token-cost (MED, NEW production feedback) + RAID-V11-pm-subagent-disclosure (MED, NEW production feedback) + **RAID-SEC-V11-backtick-subshell-injection** (MED, NEW from Phase C Ad-hoc Security PM LessonsLearned introspection — D-3 `_COMPOUND_OP_RE` regex doesn't cover backtick `` ` `` or `$()` subshell forms).

### Migration

`scripts/daemon.py` `_enter_aborted` failure_message normalized to single-line space-delimited key=value per I-064 — observable contract change for downstream parsers reading `last-resume-failure.txt`: pre-v0.1.10 emitted multi-line `transition: T7\nreason: ...\nsuggested_action: ...` with `stash_ref:` only when `last-stash.txt` was present; v0.1.10 emits `transition=T7 reason=... suggested_action=... stash_ref=<value>` always (empty value when stash file absent). Format change is intended (I-064 normalization per `design.md §5 lines 701-714`); always-present-empty for `stash_ref` is a side effect — downstream `lib/notifier.py` parsers should treat `stash_ref=` (empty) and `stash_ref=<path>` as functionally equivalent. Hook hardening (D-1+D-2+D-3) is out-of-tree at `~/.claude/hooks/pretooluse_guard.py`; in-repo evidence only.

### Notes

- **v0.1.11 carry-forward RAIDs (5 total)**: RAID-V11-real-claude-integration (sev:HIGH — blocks all real-claude measurement) + RAID-V11-install-lifecycle-python3-path (sev:MED — plist `{{PYTHON3_PATH}}` substitution) + RAID-V11-ccb-token-cost (sev:MED — CCB ceremony token-cost friction from production usage) + RAID-V11-pm-subagent-disclosure (sev:MED — return contract `sub_agent_invocations` field gap) + **RAID-SEC-V11-backtick-subshell-injection** (sev:MED, NEW — D-3 regex extends to backtick + `$()` in v0.1.11; compounds with PM-subagent-disclosure for security-class enforcement gap).

## [0.1.9] — 2026-05-08

### Added

- **`docs/specs/measurement-protocol.v0.1.9.md`** — 9 normative sections + AC-1..AC-5 strict three-statistic ≤30s + PO-2 N=10 p95=max degeneracy clause + PO-4 parallel/Q0 carryover note + `§methodology-deviations` (deviation-1: stub-claude TimeoutExpired equivalent; deviation-2: Gate_Human N/A non-interactive evidence). Deviations registered via M-2 + M-4 CCB-Light.
- **`docs/archives/measurement.v0.1.9.md`** — I-023-M1 measurement evidence archive: GHA macos-14 arm64 run 25375693016; N=10 cold + N=10 warm all OK; cold p50/p95/max=15.5/15.9/15.9s; warm p50/p95/max=5.3/5.8/5.8s — all ≤30s ship gate. Includes `host_env.json` (os/arch/launchctl_bootstrap_path/hook_chain/plist_install_path/runner_info).
- **`.github/workflows/measure-execution.yml`** — measurement workflow with matrix `[macos-14, macos-13]` `fail-fast: false` + dual-detection + per-arch evidence upload.
- **`tools/measure-{write-baton,poll-resumed,compute-stats}.py`** + `tools/patch-plist-python3.py` (workflow-layer GHA macOS Python 3.9 PEP 604 compatibility fix; daemon spec NOT modified).
- **`docs/specs/auto-resume-daemon-design.md §7 — term (e) v0.1.9 measurement closure`** — APPENDED 2026-05-08; ADDITIVE to (a)–(d) FROZEN content. Records p50/max + cross-references measurement archive + methodology deviations.
- **`skills/teamwork-leader-workflow/references/stage-runbook.md §step-review-rubric + §GATING attribution-truth`** — L-2 advisory→MUST one-way ratchet codification with revert criterion (T-1-0 ship-blocking per Opus PlanAudit promotion).
- `.claude-plugin/plugin.json` version 0.1.9.

### Changed

- **`README.md` §已知量測缺口 警語移除** (line 105 area) — replaced v0.1.7→v0.1.9 deferral warning paragraph with v0.1.9 measurement closure summary citing archive + protocol + design.md §7 (e). Reflects I-023-M1 RAID closure.

### Why

v0.1.9 closes the v0.1.7 measurement deferral codified in `design.md §7` term (b) by executing I-023-M1 on a non-guarded reference host (GHA macos-14 arm64) per term (c). All three statistics (cold/warm × p50/p95/max) confirm baton-write→SESSION_RESUMED ≤30s ship gate (term a). Two methodology deviations were registered as spec authorizations (M-2 + M-4 CCB-Light) rather than silent reinterpretation, keeping the tag commit self-evidencing per `feedback_tag-commit-self-evidence` discipline. FROZEN spec held end-to-end (`git diff origin/main..HEAD -- daemon.py design.md` empty before §7 (e) APPEND). Daemon FROZEN-spec changes (I-061/I-064/I-065) deferred to v0.1.10 per Opus PlanAudit B1 anti-staleness ruling.

### Migration

None. Doc + workflow + measurement-tool additions; no API / schema / runtime behavior changes. Existing installations continue to work; v0.1.9 measurement evidence is read-only archival.

### Notes

- **[0.1.7] back-fill remains deferred**: full v0.1.7 release record preserved in `docs/archives/lessons-learned.v0.1.7.md`, `docs/archives/PROGRESS.v0.1.7.md`, and `docs/specs/phase-4-evidence/stage-4-close-report.txt`. Back-fill of `[0.1.7]` CHANGELOG entry remains deferred as OPTIONAL future CCB-Light (per v0.1.8 RAID-I I-2 inheritance); v0.1.9 does not back-fill it.

## [0.1.8] — 2026-05-05

### Added

- `docs/specs/auto-resume-daemon-design.md §7 — Measurement Deferral & Shipping Constraint (v0.1.8 amendment)` — formal codification of v0.1.7 degraded-mode ship rationale. Documents (a) ≤30s threshold retained as ship gate, (b) measurement deferred to v0.1.9, (c) reference-host requirement (non-guarded macOS), (d) degraded-mode acceptance path = v0.1.7 ship rationale. CCB marker embedded.
- `docs/archives/lessons-learned.v0.1.7.md` — formal persistence of L-1..L-4 from v0.1.7 ProjectClose audit-trail. L-2/L-4 inheritance notes use advisory language only (no v0.1.9 commitment); L-1/L-3 carry v0.1.9 measurement / reference-host reference.
- `.claude-plugin/plugin.json` version 0.1.8.

### Changed

- `README.md` shipping caveat (line 105 area) expanded from one-liner to substantive 100+ word 繁中 paragraph with cross-refs to design.md §7 and lessons-learned.v0.1.7.md §L-1/§L-3.
- `README.md` version badge 0.1.6 → 0.1.8 (skip-version intentional; see Why below).

### Why

v0.1.7 closed under acceptance (d) degraded-mode authorization because the developer host's bash-hook + launchctl-guard structurally blocked real launchd-load integration. The ≤30s baton-write→SESSION_RESUMED KPI was therefore **never measured** on any real host. v0.1.7 shipped without this gap being honestly inscribed into permanent project artifacts (only the close report mentioned it). v0.1.8 codifies the shipping constraint into design.md and creates a stable archival location for the LessonsLearned, so that v0.1.9 inheritors and external auditors cannot accidentally treat v0.1.7 as production-verified. Doc-only patch; no functional behavior change.

### Migration

None. Doc-only; no API / schema / behavior changes. Existing v0.1.7 installations continue to work; degraded-mode users remain in degraded-mode until v0.1.9 establishes a reference host.

### Note: [0.1.7] CHANGELOG entry not back-filled

`[0.1.7]` was never written into this CHANGELOG at v0.1.7 release — the auto-resume daemon feature shipped with the version badge / plugin.json bumped but the `## [0.1.7]` entry was omitted. The `[0.1.8]` entry above does NOT back-fill v0.1.7 content. The full v0.1.7 release record is preserved in `docs/archives/lessons-learned.v0.1.7.md`, `docs/archives/PROGRESS.v0.1.7.md`, and `docs/specs/phase-4-evidence/stage-4-close-report.txt`. Back-fill of `[0.1.7]` entry is deferred as an OPTIONAL future CCB-Light (per RAID-I I-2 in v0.1.8 charter).

## [0.1.7] — 2026-05-04 (back-filled 2026-05-05 per RAID-I I-2 / v0.1.8 CCB-Light)

### Added

- **Auto-Resume Daemon — Phase 1+2 (plugin-self-contained AutoCompact resilience)** — multi-charter delivery shipping a polling daemon that detects baton-write events from `hooks/stop.py` and resumes Claude Code sessions without requiring host-side cron / launchd ownership.
- **Phase 1 — Stages 1-3** (delivered prior charters within v0.1.7 scope): 3 hooks (`stop.py` baton-write, plus session-lifecycle integration), 4 lib modules (`gate-lock.py`, schema validators, baton primitives), 5 measurement tools (`measure-latency.sh`, `measure-fault-awareness.sh`, `measure-checkout-fp.sh`, `check-cross-refs.sh`, plus phase-evidence collectors).
- **Phase 2 — Stage 4 FINAL**:
  - `scripts/daemon.py` (991 lines): 5 actor states (POLL / BATON_DETECTED / SESSION_RESUMING / SESSION_RESUMED / ABORTED), 5 self-test sub-flags (`--self-test-t5/-t6/-t7/-pid/-reaper`), 7-field schema validation, 1s/4s/16s exponential backoff with retry counter, ABORTED state with `last-resume-failure.txt` + notifier, stale-lock reaper subprocess, PID lifecycle (0600 perms, atomic os.replace, NOT removed on clean exit per design §3.12), crash recovery.
  - `scripts/install.py` (236 lines): 3-layer install (plist template render → launchctl bootstrap → verification), `--dry-run` mode, `--uninstall` reverse path.
  - `templates/com.user.claude-code-resume-daemon.plist` — launchd plist template for production deployment.
- **`docs/specs/auto-resume-daemon-design.md`** — FROZEN design spec: 7 acceptance criteria (AC-4-A through AC-4-G), 7 cross-script invariants (CI-1..CI-7), `templates/budget-proposal.md.tpl` integration with new daemon section.
- **`docs/specs/phase-{1,2,3,4}-evidence/`** — 4 phase-evidence dirs with reproducible artifacts (test-mode results, latency measurements, cross-refs status, real-session integration markdown, stage-4 close report).

### Changed

- **`README.md`** — added Auto-Resume Daemon section documenting plugin-self-contained design, install/uninstall flow, baton-write protocol, degraded-mode caveat (I-019 host-guard).
- **`.claude-plugin/plugin.json`** — version 0.1.6 → 0.1.7.

### Why

Pre-v0.1.7, AutoCompact-induced session compaction would silently truncate ongoing TeamLead charter state. Recovery required manual `/teamwork-leader` re-invocation with no automated handoff signal. v0.1.7 closes this gap with a poll-driven baton-write protocol entirely owned by the plugin (no host cron / launchd ownership required for the protocol itself; only the Stage 4 daemon runner needs launchd, and that path supports degraded-mode operation when the host is bash-hook-guarded).

### Migration

- Existing charter projects (pre-v0.1.7): hooks remain backward compatible; baton-write protocol activates only when `hooks/stop.py` detects an active TeamLead state. No PROGRESS.md schema migration required.
- Daemon adoption is **opt-in**: charters that don't install the daemon continue to operate exactly as before (manual resume on AutoCompact). The Phase 1 hooks function as a no-op for charters without the daemon installed.

### Caveat — Shipping Constraint

**I-023-M1 — actual baton-write → SESSION_RESUMED wall-clock latency is UNMEASURED in v0.1.7.** The single quantitative success metric committed in `design.md` Q4 ("Stage 4 will produce the first real latency data + report observed at Stage 4 close") could not be measured on the developer's bash-hook + launchctl-guarded macOS host (per RAID-I I-019). The daemon ships under acceptance path (d) — degraded-mode close, with explicit CEO acceptance of unmeasured KPI granted at `CEO_Gate_4_final`.

  - Synthetic `--self-test-t5` path: sub-second by design (no I/O — not representative of production).
  - Production poll-path estimate: 10-15s (DESIGN-LEVEL only, NOT measured).
  - **Real measurement deferred to v0.1.9 first-action** on a non-guarded reference host.

This shipping constraint is formally codified in `[0.1.8]` via `docs/specs/auto-resume-daemon-design.md §7` (Measurement Deferral & Shipping Constraint amendment) and `docs/archives/lessons-learned.v0.1.7.md` §L-1 / §L-3. See `[0.1.8]` Why for the codification rationale.

### Note (back-fill rationale)

This `[0.1.7]` entry was reconstructed post-ship from archive sources after being omitted at original v0.1.7 release (only `plugin.json` + README badge bumped; CHANGELOG entry was forgotten). v0.1.8's `### Note: [0.1.7] CHANGELOG entry not back-filled` subsection deferred this back-fill as optional CCB-Light per RAID-I I-2 in v0.1.8 charter; this entry now closes that backlog item.

  - **Source archives (canonical record)**: `docs/archives/lessons-learned.v0.1.7.md` (L-1..L-4), `docs/archives/PROGRESS.v0.1.7.md` (Stage Histories + Self-Audit), `docs/specs/phase-4-evidence/stage-4-close-report.txt` (Sections 1-7 + Appendix A post-Opus revisions).
  - **What this entry does NOT do**: re-tag v0.1.7 (already published 2026-05-04); modify the GitHub release page (preserved as-was); restate Stage-by-Stage internal kT breakdown (canonical record lives in archives).
  - **Project total kT**: ~453 kT across all 4 stages (Stage 4: ~173 kT vs Plan B 155 baseline; +18 kT / 11.6% over Plan B but well within Plan A 250 kT envelope).

## [0.1.6] — 2026-05-03

### Added

- **Rule 7 in `references/anti-rubber-stamp.md`** — Plan-audit anti-self-skip rule with 4 enforcements: (1) dispatch prompt blacklist of self-skip phrases, (2) `suggested_fix` structured-field actionability requirement, (3) all logged issues surfaced to CEO regardless of severity, (4) 1-retry post-receive guard with escalation on persistence.
- **New `references/plan-audit-rubric.md`** — Standalone Rule 7 rubric (~123 lines): §Scope (TeamLead-dispatched Opus, NOT host `/opus-review final`), §Dispatch prompt blacklist (verbatim block), §Structured-field validation (detection procedure + scope limit to structured field only), §Verdict aggregation, §Post-receive guard (corrective re-dispatch prompt + escalation path), §Cross-references.
- **`plan_audit_self_skip_detected: boolean | null` field** in `audit-trail.jsonl` schema (`references/progress-md-schema.md` §Audit-trail sidecar) — `true` if Rule 7 fired detection this PLAN_AUDIT session; `false` if Rule 7 ran clean; `null` if Rule 7 did not run (single-plan mode without `suggested_fix` emission, OR `plan_audit_anti_self_skip_mode == off`).
- **`plan_audit_anti_self_skip_mode` knob** in `templates/budget-proposal.md.tpl` §Knobs — `strict` (default, full Rule 7 enforcement), `warn` (validate + log but no re-dispatch / escalate), `off` (skip Rule 7; field logs `null`). Both `warn` and `off` require CCB-Heavy.

### Changed

- **`references/stage-runbook.md` §PLAN_AUDIT rewritten** — step 3 now embeds Rule 7 dispatch prompt blacklist cross-ref before plan content; new step 3.5 (post-receive Rule 7 validation: parse `suggested_fix` fields, detect blacklisted values, on detection re-dispatch ONCE with corrective prompt); step 4 verdict routing updated to filter out issues with non-actionable `suggested_fix` before surfacing to CEO; exit condition updated to include `plan_audit_self_skip_persistent` escalation path.
- **`references/three-gates.md` §JSON parse failure** — added cross-ref note: PLAN_AUDIT has additional Rule 7 anti-self-skip protection; consult `references/plan-audit-rubric.md` for plan-audit-specific reviewer dispatch protocol.
- **`references/reuse-map.md` PlanAudit row** — explicit clarification that PlanAudit uses Agent tool with `model: opus`, NOT host `/opus-review final` skill, with rationale: portability ethos + Rule 7 enforcement requires plugin-controlled dispatch.
- **README.md** — version badge bumped 0.1.5 → 0.1.6; new §Anti-self-skip (v0.1.6) section after §三道驗證閘 documenting Rule 7 scope (TeamLead-dispatched Opus only, NOT host `/opus-review final`), 4-enforcement table, knob configuration, and cross-refs to `plan-audit-rubric.md` / `anti-rubber-stamp.md` §Rule 7.

### Why

Post-v0.1.5 design observation: Rules 0/0.5/2 protect EXECUTING-phase PM dispatches, but PLAN_AUDIT-phase Opus reviewers had no dedicated self-skip guard. A reviewer can flag a real plan issue, then suggest `"skip"` / `"none"` / `"no change"` / `"cosmetic only"` / `"minimal-diff"` as `suggested_fix` — effectively rubber-stamping the issue while appearing to log it. Rule 7 closes this gap with structured-field validation (NOT prose regex, which carries false-positive risk on legitimate text like "skip migration if X"). The 1-retry design prevents cascading escalation; CEO arbitrates only on persistent failures.

### Migration

- Legacy PLAN_AUDIT runs (pre-v0.1.6) have `plan_audit_self_skip_detected: null` in any existing audit-trail.jsonl rows (no retroactive backfill; follows `kmr_*` pattern precedent).
- Post-v0.1.6: Rule 7 enforcement is mandatory (`plan_audit_anti_self_skip_mode: strict` default) unless CCB-Heavy sets `warn` or `off`.
- In-flight v0.1.5 projects upgrading mid-stage: no PROGRESS.md migration required; Rule 7 takes effect on the next PLAN_AUDIT dispatch. Existing audit-trail.jsonl rows lack the field — this is treated as `null` (legacy).

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
