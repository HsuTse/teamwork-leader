# CCB-Heavy Request

<!--
Authority: TeamLead drafts; CEO is sole approver (per design doc §3 RACI matrix + §8).
CCB-Heavy is required for risk-driven change (security posture adjustment on user-personal Mac).
Per references/pmp-ccb.md.

Once raised, PROGRESS.md ## CCB-Heavy Pending section is populated; cleared when CEO decides.
-->

## Metadata

- **Time raised**: 2026-05-10T14:10+08:00
- **Stage when raised**: 3
- **Origin**: PM-surfaced material issue (Phase C transparency finding RAID-I-S3-D2-1)
- **CEO state**: pending

## Material change description

Authorize TeamLead to coordinate a scope-limited, time-bounded relaxation of the user's
`~/.claude/hooks/pretooluse_guard.py` denylist (currently blocks `\bcrontab\b|\blaunchctl\b|\bsystemctl\b`)
to permit `launchctl bootstrap` invocations targeting the teamwork-leader plist file specifically
(`com.teamwork-leader.auto-resume-daemon.plist`), for the duration of one Phase B measurement session.
After measurement completion, the original denylist pattern is restored. Charter scope is unchanged;
this CR authorizes a one-shot security-posture adjustment, not a permanent policy revision.

## Why this is CCB-Heavy (not CCB-Light)

- [ ] Charter-level change (success criteria / constraints / overall goal)
- [ ] Cross-stage scope shift
- [ ] CCB-Light cap exceeded (≥3 same section OR ≥5 stage total) — see linked CCB-Light entries
- [ ] Budget breach (>100% per-stage with no recovery, or 2× cumulative)
- [ ] Multi-PM impact requiring re-baseline
- [x] Other (specify): Security posture adjustment on user's personal Mac. Even though scope-limited
  and time-bounded, modifying user-personal hook config is a risk-driven change per
  `~/.claude/rules/CONTRIBUTING.md` §禁止事項 (CI/infra/permissions/secrets); CCB-Heavy is the
  lowest governance level that includes CEO mandatory sign-off.

## Linked CCB-Light entries (if cap-driven)

Not cap-driven. Linked for context:

- 2026-05-10 | section: `design.md §7 (h)` | resolution: CCBL-Stage3-v0.1.11-AC3-LOCAL-REFRAME
  (AC-3 host-class reframe that surfaced the necessity of Phase B real-launchd measurement)

## Proposed resolution

Phase B execution plan — laddered, time-bounded, with sha256 audit:

**Step 1 — Pre-measurement snapshot** (TeamLead):
Take sha256 of `~/.claude/hooks/pretooluse_guard.py` and record to governance evidence file
`docs/specs/v0.1.11-evidence/measurement-real-launchd-local.v0.1.11.md`. No content exfiltration;
hash only. This establishes the restore-verification baseline.

**Step 2 — Guard relax** (TeamLead, one atomic edit):
Narrow the denylist regex in `~/.claude/hooks/pretooluse_guard.py` to permit ONLY
`launchctl bootstrap.*com\.teamwork-leader\.auto-resume-daemon\.plist` (or equivalent
precise pattern). All other `launchctl` invocations remain denied. No other denylist
patterns are touched.

**Step 3 — Install** (TeamLead):
Run `python3 install.py` from `/Users/HsuTse/ClaudeProject/teamwork-leader`. With the guard
narrowed, Layer 1 (launchctl bootstrap) is now permitted for this specific plist target.
Expect Layer 1 success; Layer 2 (validation) follows.

**Step 4 — Measurement** (TeamLead):
Trigger ≥1 cold (daemon respawn) + ≥1 warm (daemon already loaded) SESSION_RESUMED iteration
via `tools/measure-write-baton.py` while monitoring `.teamlead/baton.json` gate_state transitions.
Capture wall-clock latency for each iteration.

**Step 5 — Restore** (TeamLead, immediately after measurement):
Re-edit `~/.claude/hooks/pretooluse_guard.py` to restore the original denylist pattern. Verify
via sha256 that the restored file matches the Step 1 pre-snapshot hash. Mismatch → ABORT and
flag for manual review before proceeding.

**Step 6 — Evidence doc** (TeamLead):
Write `docs/specs/v0.1.11-evidence/measurement-real-launchd-local.v0.1.11.md` with:
- Pre-snapshot sha256 + restore-verification sha256 (must match)
- Cold/warm latency stats (≥1 cold + ≥1 warm SESSION_RESUMED iterations)
- Charter §AC-3 DoD claim: met / not-met (per results)

**Step 7 — Time bound** (hard cap):
Entire Phase B execution window ≤ 2 hours wall-clock from guard relax (Step 2) to restore
confirmed (Step 5). If measurement loops fail repeatedly within the window, ABORT and restore
guard before expiry. No open-ended exemption window is authorized.

## Impact analysis

| Area | Impact | Required action |
|---|---|---|
| Charter | No change; AC-3 wording already updated by CCBL-Stage3-v0.1.11-AC3-LOCAL-REFRAME | None (Charter scope unchanged) |
| Stage decomposition | Stage 3 EXECUTING continues; Phase B execution adds ~25-40 kT (within Stage 3 baseline 220 kT; remaining ~174 kT per PROGRESS.md) | No re-baseline required |
| RAID Register | RAID-I-S3-D2-1 transitions in_progress→pending_validation on Phase B execute; on Phase B PASS → RAID-I-S3-D2-1 closed + RAID-V11-real-claude-integration AC-3 portion CLOSED + Charter §AC-3 DoD met | TeamLead updates RAID Register at Phase B close |
| Value Hypothesis | Charter §AC-3 DoD becomes empirically claimable post-Phase-B PASS; no Value Hypothesis wording change | No update required unless Phase B PASS achieved |
| Budget | Delta +25-40 kT execution; well within Stage 3 baseline remaining (~174 kT) | No CEO budget re-baseline required |
| Active PMs | TeamLead leads execution; RD assists for any tooling tweaks; PO reads restore evidence at Phase B close | No new PM activation required |
| Tasks/code | No daemon code changes (scripts/daemon.py FROZEN per §1-§6 + §7 (a)-(h)); guard hook is user-personal config not part of repo (not committed to teamwork-leader) | tasks.md Phase B task updated by TeamLead on execute |

## RAID delta proposed

**New entries** (added to PROGRESS.md ## RAID Register on CEO approve):

- [R] `RAID-R-S3-PhaseB-guard-relaxation` sev:MED — Brief security posture relaxation window
  (guard narrowed for ≤2h wall-clock); mitigation: time-bound hard cap + narrow plist-specific
  regex + sha256 pre/post audit + abort-on-mismatch protocol
- [A] `RAID-A-S3-PhaseB-restore-reliable` — Assume guard hook restoration is reliable via sha256
  comparison; validates if: post-measurement sha256 matches pre-snapshot hash exactly
- [V] `RAID-V-S3-PhaseB-ac3-met` — Charter §AC-3 DoD empirically met (≥1 cold + ≥1 warm
  SESSION_RESUMED reached on real launchd); pending Phase B execute

**Closed entries** (marked closed on Phase B PASS):

- [I] RAID-I-S3-D2-1 (Phase C transparency finding: §7 (g-1) AC-2 fix not exercised by
  `_run_t5_actor(test_mode=True)`) — closed when Phase B produces empirical cold+warm evidence
- [V] RAID-V11-real-claude-integration AC-3 portion — closed when §AC-3 DoD empirically met

## CEO decision

<!-- CCB-Heavy uses the extraordinary CEO_Gate verb set per references/pmp-ccb.md §CCB-Heavy step 6:
     - approve  → resume Stage with new spec
     - reject   → continue with old spec (no PROGRESS.md ## Charter / Budget changes)
     - defer    → freeze stage; CEO will re-decide later -->

- Verb: <pending>
- Decided at: <pending>
- Notes: <pending>

## Post-decision actions (TeamLead)

**On `approve`**:
- [ ] Update PROGRESS.md ## Charter (append-only per §5.5.1)
- [ ] Update PROGRESS.md ## Budget Baseline (re-baseline if budget changed)
- [ ] Update PROGRESS.md ## RAID Register with delta
- [ ] Clear PROGRESS.md ## CCB-Heavy Pending section
- [ ] Notify all activated PMs of revised Charter / budget
- [ ] Append CCB-Heavy event detail block to docs/decisions/ccb-log.md §Heavy events
- [ ] Resume next dispatch / state transition (Phase B execution)

**On `reject`**:
- [ ] Clear PROGRESS.md ## CCB-Heavy Pending section
- [ ] Append CCB-Heavy event to docs/decisions/ccb-log.md §Heavy events with `verb: reject`
- [ ] No Charter / Budget / RAID changes
- [ ] Resume Stage 3 with Phase D fallback path: AC-3 partial-demote to v0.1.12 via separate
  CCB-Heavy revise_charter at ProjectClose; v0.1.11 ships with §7 (g-1) zero empirical validation

**On `defer`**:
- [ ] Update PROGRESS.md ## State to `ESCALATED`
- [ ] Keep PROGRESS.md ## CCB-Heavy Pending populated (do NOT clear)
- [ ] Surface to CEO at next CEO_Gate via AskUserQuestion: "CCB-Heavy still deferred — re-decide?"
- [ ] No further dispatches until CEO returns approve/reject
