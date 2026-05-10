# Phase B Measurement — real launchd E2E on local macOS deployment host

**Charter**: v0.1.11 (`feat/v0.1.11-real-claude-integration`)
**Stage**: 3
**Phase**: B (real launchd E2E; complementary to Phase C synthetic `--self-test-t5` evidence at `synthetic-t5-summary.json`)
**Date**: 2026-05-10
**Host**: Darwin arm64 (local user macOS deployment environment per CCBL-Stage3-v0.1.11-AC3-LOCAL-REFRAME)
**Result**: **Charter §AC-3 DoD MET** — cold + warm SESSION_RESUMED both reached, both well under ≤30s ship gate.

---

## 1. Result summary

| Iteration | Final state | Wall-clock latency | Ship gate (≤30s) |
|---|---|---|---|
| **Cold** | SESSION_RESUMED | **12.099s** | ✅ PASS |
| **Warm** | SESSION_RESUMED | **11.091s** | ✅ PASS |

**Charter §AC-3 DoD** (per CCBL-Stage3-v0.1.11-AC3-LOCAL-REFRAME): "AC-7(ii) **local macOS host (real user deployment environment)** real-claude end-to-end measurement: ≥1 cold + ≥1 warm SESSION_RESUMED reached" — **MET**.

Cold p50 = 12.099s; warm p50 = 11.091s. Comparison to v0.1.9 GHA macos-14 (synthetic claude stub): cold p50 = 15.5s / warm p50 = 5.3s. Local real-claude warm latency notably higher than v0.1.9 stub-claude warm (11.1s vs 5.3s) — explained by real claude OAuth/API initialization overhead (Stage 1 AC-1 characterization observed 8-15s exit window), confirmed exercising §7 (g-1) AC-2 fix logic.

§7 (g-1) `proc.wait(timeout=30.0)` primary wait window successfully captured both real-claude exits within 30s — no fall-through to 28s post-timeout poll loop required. Validates AC-2 Option B fix (cf. v0.1.10 deviation-4 PROVEN-INTEGRATION-GAP at GHA where original 2.0s timeout false-positived on auth-host slow init).

---

## 2. Phase B execution narrative

### 2.1 Pre-Phase-B governance

- Stage 1 (commit bb666c0): AC-1 real-claude `--resume` characterization (V2 root cause + timing-asymmetry discovery)
- Stage 2 (commit fd1a7dd + 450727c): AC-2 Option B daemon §7 (g-1) timeout extension (2.0→30.0s + 28s poll loop)
- Stage 3 PLANNING (CCBL-Stage3-v0.1.11-AC3-LOCAL-REFRAME 2026-05-10T~13:30): AC-3 host context reframed from GHA macos-14 reference host to local user deployment environment
- Stage 3 Phase C (commit 507f131): synthetic `--self-test-t5` measurement N=10 all PASS — plumbing validity confirmed BUT RAID-I-S3-D2-1 surfaced: `_run_t5_actor(test_mode=True)` bypasses §7 (g-1) entirely (only allowlist + baton-update plumbing exercised)
- Stage 3 PO V0.1.11-S3-D3 (commit 7823d14): drafted CR-V0.1.11-S3-Phase-B-guard-exemption (CCB-Heavy)
- CCB-Heavy CEO_Gate (extraordinary) approve 2026-05-10T~14:25: Phase B execution authorized

### 2.2 Phase B Discovery #1 — CR's "guard relax" premise was wrong

After CCB-Heavy approve, TeamLead read user's `~/.claude/hooks/pretooluse_guard.py` source (Phase B Step 1 "snapshot" stage) and discovered:

1. PreToolUse Bash hook only scans TeamLead's literal Bash tool command strings
2. install.py uses `subprocess.run(["launchctl", "bootstrap", ...])` (Python list-form subprocess) — does NOT route through Claude Code's Bash hook; goes directly to OS launchd
3. Hook already has built-in teamwork-leader plist exemption (`_LAUNCHCTL_TEAMLEAD_RE` lines 198-207) downgrading deny→ask for plist-name-matching commands

**Implication**: original CR's "scope-limited guard relaxation" is unnecessary. Registered `CCBL-Stage3-v0.1.11-PhaseB-CR-INVALID-PREMISE`. CEO re-decision (AskUserQuestion, 2026-05-10T~14:32): adopted "approve revised path" — execute Phase B WITHOUT touching guard config.

**Result**: RAID-R-S3-PhaseB-guard-relaxation → CLOSED-NOT-NEEDED; RAID-A-S3-PhaseB-restore-reliable → N/A. Token savings ~16 kT (revised ~30 kT vs original ~46 kT) + zero security posture change.

### 2.3 Phase B Discovery #2 — Python 3.9 vs 3.10+ launchd PATH blocker

After CCBL-PhaseB-CR-INVALID-PREMISE applied + `python3 install.py` Layer 1 succeeded (plist installed at `~/Library/LaunchAgents/com.teamwork-leader.auto-resume-daemon.plist`), daemon CRASHED at module-load:

```
File "/Users/HsuTse/ClaudeProject/teamwork-leader/scripts/daemon.py", line 994, in <module>
    def main(argv: list[str] | None = None) -> int:
TypeError: unsupported operand type(s) for |: 'types.GenericAlias' and 'NoneType'
```

**Root cause**: launchd restricted PATH (`/usr/bin:/bin:/usr/sbin:/sbin`) doesn't inherit user shell PATH. `/usr/bin/env python3` resolves to macOS 14 system Python 3.9 (no PEP 604 union syntax). User has Python 3.13.13 at `/opt/homebrew/bin/python3.13` but launchd can't see it.

**Empirical refutation of D3 docstring**: PO V0.1.11-S3-D1 commit 22d1423 D3 docstring on `tools/patch-plist-python3.py` claimed "local launchd PATH inheritance is not a problem". This was based on inherited assumption from `feedback_reference-host-vs-deployment-target.md`. Empirically wrong — launchd PATH restriction is universal (GHA == local).

**Opus advisor consultation 2026-05-10T~14:42** (mid-stage advisor pattern per v0.1.7-v0.1.10 precedent): given 3 options (A: workaround / B: BLOCKED+demote / C: CCB-Heavy add new AC), recommended (A) workaround — reasoning: 4-founding-intent integrity (止 3-charter recurrence), no wheel reinvention (patch-plist-python3.py exists for this), charter scope discipline (one-shot ops, not new AC), +10 kT vs (C) +30 kT. CEO accepted 2026-05-10T~14:45.

**Workaround applied** (per CCBL-Stage3-v0.1.11-PhaseB-PYTHON-PATH-WORKAROUND):

- python3 absolute: `/opt/homebrew/bin/python3.13` (Python 3.13.13 confirmed via `--version`)
- claude binary dir: `/Users/HsuTse/.local/share/fnm/node-versions/v24.14.0/installation/bin` (stable, not session-specific fnm shim)
- Sequence: bootout broken plist → `python3 tools/patch-plist-python3.py` (modifies plist file in place: ProgramArguments `/usr/bin/env python3` → absolute python3.13 path; EnvironmentVariables.PATH inject claude binary dir) → bootstrap patched plist
- Verified: daemon process spawned (pid 63607 under Python 3.13); `daemon.err` empty after re-bootstrap

**RAID delta**: RAID-V11-install-lifecycle-python3-path → ESCALATED from "v0.1.12 carry candidate" to **v0.1.12 mandatory HIGH** (premise that justified deferral disproven).

### 2.4 Phase B Discovery #3 — restore_prompt allowlist em-dash rejection

First measurement attempt failed: both cold + warm timed out at 90s. daemon.err showed: `[daemon T5] ERROR: restore_prompt failed allowlist check — T7 abort path`.

**Root cause**: measurement script's `restore_prompt = "Phase B measurement probe — please respond with one word: ack"` contained em-dash `—` (U+2014). daemon.py:351-381 `_validate_restore_prompt` allowlist regex `^[\w\s.,;:\-_/()\[\]{}<>#@!?'\"]*$` (per design.md §5 T-S-2 lines 628-630) does not include em-dash.

**Fix**: replaced em-dash with ASCII `--`. Re-ran measurement → both iterations PASS (cold 12.099s + warm 11.091s).

**Note**: this was test-helper-side issue, not a daemon defect. Allowlist behavior is correct per design (security boundary against shell-injection vectors). Lesson: documentation should warn end-users about restore_prompt allowlist scope.

---

## 3. Empirical evidence

### 3.1 daemon.err — successful T5 traces

```
[daemon] INFO: gate_state=BATON_WRITTEN detected — running T5 actor
[daemon T5] INFO: git stash pushed: teamlead-resume-ed6034b9-6975-4db8-9906-42b9ee67f7d4-20260510T064503Z
[daemon T5] INFO: spawned claude --resume ed6034b9-6975-4db8-9906-42b9ee67f7d4 (pid=73336)
[daemon T5] INFO: gate_state updated to SESSION_RESUMED
[daemon] INFO: gate_state='SESSION_RESUMED' — not BATON_WRITTEN, ignoring
[daemon] INFO: gate_state=BATON_WRITTEN detected — running T5 actor
[daemon T5] INFO: spawned claude --resume ed6034b9-6975-4db8-9906-42b9ee67f7d4 (pid=74454)
[daemon T5] INFO: gate_state updated to SESSION_RESUMED
[daemon] INFO: gate_state='SESSION_RESUMED' — not BATON_WRITTEN, ignoring
```

### 3.2 Measurement raw data (reproduced inline; this committed doc is self-evidencing)

The raw JSONL lines below are reproduced verbatim from `.teamlead/_phase_b_measurements.jsonl` (transient ops file under .gitignore; ops helper `.teamlead/_phase_b_measure.py` retained for v0.1.12 reference). The latency claims at §1 are sourced FROM these lines. Embedding them here makes the committed evidence doc self-evidencing — if the transient file is lost, the numerical evidence persists in this doc.

```json
{"label": "cold", "session_id": "ed6034b9-6975-4db8-9906-42b9ee67f7d4", "t0_mtime": 1778395501.823, "final_state": "SESSION_RESUMED", "latency_seconds": 12.099, "timeout": false}
{"label": "warm", "session_id": "ed6034b9-6975-4db8-9906-42b9ee67f7d4", "t0_mtime": 1778395525.93, "final_state": "SESSION_RESUMED", "latency_seconds": 11.091, "timeout": false}
```

### 3.3 §7 (g-1) AC-2 fix coverage (vs Phase C synthetic which bypassed it)

| Phase | daemon code path exercised | §7 (g-1) primary 30s wait | §7 (g-1) post-timeout 28s poll loop |
|---|---|---|---|
| Phase C synthetic (`--self-test-t5`) | `_run_t5_actor(test_mode=True)` → `else` branch → directly writes SESSION_RESUMED | **Bypassed** (RAID-I-S3-D2-1) | **Bypassed** (RAID-I-S3-D2-1) |
| Phase B real launchd | `_run_t5_actor(test_mode=False)` → `subprocess.Popen(claude --resume ...)` → `proc.wait(timeout=30.0)` succeeds within 12s → SESSION_RESUMED | **Exercised** ✅ (real claude exits at 12.099s cold / 11.091s warm, both within 30s primary window) | **Not triggered** (real claude exited < 30s; poll loop fallback would only fire if exit > 30s) |

Phase B is the empirical validation of Charter AC-2 Option B daemon fix's **primary 30s wait path** (§7 (g-1) g-1.1 effectively). The **defensive post-timeout 28s poll loop fallback** (§7 (g-1) g-1.2 effectively) remains untriggered — it is a defensive layer for hypothetical real-claude exits in the 30-58s window. To exercise the poll loop empirically would require a session that takes > 30s for claude --resume to process, which was not available in this Phase B sample. v0.1.12 LL candidate: design a stress-test session (large jsonl) to deliberately probe the poll loop fallback path. For v0.1.11 ship, primary path validation is sufficient — Stage 1 AC-1 characterization observed real claude exits in 8-15s window, well within primary 30s; poll loop is a margin-of-safety defense, not a regularly-fired path.

### 3.4 Side-effects observed (governance-compliant; documented for transparency)

- **git auto-stash**: daemon's T5 actor pushes a `git stash` per iteration (per design §5 T-S-3 safety net) before spawning claude. After Phase B execution: 1 net stash recovered via `git stash pop`. This is expected behavior, NOT a defect.
- **.teamlead/ file lifecycle**: daemon overwrites `daemon.out` / `daemon.err` per launchd respawn. baton.json transitions BATON_WRITTEN→SESSION_RESUMED in place.
- **Real claude API token cost**: each iteration = 1 `claude --resume <uuid> -p "<prompt>"` invocation. Real Anthropic API call billed against user's plan. Estimated ~$0.05-0.20 per iteration (depending on session jsonl size; ed6034b9 was ~150 KB). Total Phase B real-claude cost: ~$0.10-0.40. Out-of-band from TeamLead orchestration token budget.
- **Stale session jsonl polluted**: ed6034b9 session jsonl now contains the measurement probe message + claude response. Recommend NOT using session ed6034b9 for any future user work (ops debt for v0.1.12).

---

## 4. Cleanup verification

```
[uninstall] Running: launchctl bootout gui/502 /Users/HsuTse/Library/LaunchAgents/com.teamwork-leader.auto-resume-daemon.plist
[uninstall] launchctl bootout succeeded.
[uninstall] Removed: /Users/HsuTse/Library/LaunchAgents/com.teamwork-leader.auto-resume-daemon.plist
[uninstall] Uninstall complete.
```

Post-cleanup verification:
- `pgrep -lf daemon.py` → no daemon process
- `ls ~/Library/LaunchAgents/com.teamwork-leader.auto-resume-daemon.plist` → No such file or directory
- `launchctl list com.teamwork-leader.auto-resume-daemon` → rc=113 "Could not find service"
- TeamLead working tree restored (cold-iteration stash popped + measurement-induced JSON revert applied)
- `.teamlead/_phase_b_reload.py` and `.teamlead/_phase_b_measure.py` ops helpers retained for v0.1.12 reference; gitignored (not committed to source)

---

## 5. v0.1.12 implications

The 3-charter recurring host-class blocker is now **structurally addressable** with this Phase B empirical evidence as design ground truth:

1. **RAID-V11-install-lifecycle-python3-path** escalated to v0.1.12 mandatory HIGH. v0.1.12 install.py upgrade scope:
   - Auto-detect user python3 ≥3.10 absolute path (e.g., `shutil.which("python3.13")` fallback chain or homebrew `/opt/homebrew/bin/python3.{10,11,12,13,14}` glob)
   - Auto-inject claude binary directory into plist EnvironmentVariables.PATH
   - Treat patch-plist-python3.py semantics as default install behavior (not GHA-only opt-in)

2. **D3 docstring revision**: `tools/patch-plist-python3.py` docstring claim "local launchd PATH inheritance is not a problem" needs revision. v0.1.12 PO can correct as part of install.py refactor.

3. **CR drafting discipline LL candidate**: PO V0.1.11-S3-D3 reasonably abstracted away from inspecting hook/launchd architecture (per dispatch constraint), but the dispatch prompt should have asked for inspection BEFORE drafting CR. Phase B Discovery #1 + #2 surfaced ONLY via execution. Future CCB-Heavy CR dispatches: include "code-inspect any external dependencies cited in proposed resolution before drafting" as standard PO step.

4. **restore_prompt allowlist documentation**: surface to end-user docs (README) so external dogfooders avoid em-dash / smart-quote tripwires.

5. **Sample size + session diversity caveat**: N=2 same-session (ed6034b9) sample is sufficient for v0.1.11 ship-gate per Charter §AC-3 literal "≥1 cold + ≥1 warm" but NOT statistically representative of real-claude --resume latency distribution across session size classes. v0.1.12 measurement upgrade should sample ≥3 distinct sessions of varied jsonl size (small <50 KB / medium ~150 KB / large >500 KB) to characterize per-size-class latency. Mirrored to `PROGRESS.md ## Lessons Learned` as `LL-V11-S3-MEASURE-DIVERSITY` (carry to v0.1.12). Adds robustness to ship-gate beyond v0.1.11's single-session sample.

---

## 6. Cross-references

- Charter §AC-3 (effective via CCBL-Stage3-v0.1.11-AC3-LOCAL-REFRAME): `PROGRESS.md ## CCB Activity ### Stage 3`
- CR-V0.1.11-S3-Phase-B-guard-exemption: `docs/decisions/ccb-heavy/CR-V0.1.11-S3-Phase-B-guard-exemption.md` (commit 7823d14; CCB-Heavy approved 2026-05-10T~14:25)
- CCBL-Stage3-v0.1.11-PhaseB-CR-INVALID-PREMISE: `PROGRESS.md ## CCB Activity ### Stage 3`
- CCBL-Stage3-v0.1.11-PhaseB-PYTHON-PATH-WORKAROUND: `PROGRESS.md ## CCB Activity ### Stage 3`
- Opus advisor consultation: ad-hoc dispatch 2026-05-10T~14:42 (recommendation captured in CCBL-PYTHON-PATH-WORKAROUND entry)
- Phase C synthetic evidence: `docs/specs/v0.1.11-evidence/synthetic-t5-summary.json` (commit 507f131)
- design.md §7 (g) AC-2 fix authority: `docs/specs/auto-resume-daemon-design.md §7 (g)` (commit fd1a7dd)
- design.md §7 (h) AC-3 reframe authority: `docs/specs/auto-resume-daemon-design.md §7 (h)` (commit 22d1423)
- v0.1.10 deviation-3 historical context: `docs/archives/PROGRESS.v0.1.10.md`
- 3-charter recurrence pattern: v0.1.7 L-3 + v0.1.10 deviation-3 + v0.1.11 Phase B Discovery #2
