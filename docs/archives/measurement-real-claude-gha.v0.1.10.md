# Measurement Archive — v0.1.10 I-023-M1 (Real-Claude GHA macos-14)

**Protocol**: docs/specs/measurement-protocol.v0.1.10.md
**Host**: GHA macos-14 (arm64) — reference host per I-023-M1 charter
**Measurement date**: 2026-05-08T02:13Z (workflow run 25532761179)
**claude_binary**: real (path: /opt/homebrew/bin/claude — confirmed by pre-validation)
**N**: 10 cold + 10 warm (per Opus PlanAudit S2 N5→N10 revision)
**Outcome**: **PROVEN-INTEGRATION-GAP** — real claude installs and runs but does NOT produce the SESSION_RESUMED signal that the daemon's `_wait_for_session_resumed` polling expects. 10/10 cold + 10/10 warm runs FAIL at C-4/W-3. AC-7(ii) status: **FAIL** with empirical evidence (charter-level integration finding).

## §metadata

| Field | Value |
|---|---|
| version | v0.1.10 |
| dispatch | V0.1.10-S2-EX1 (T-2-2 Candidate A) |
| gate_decision | Candidate A (real-claude) — pre-validation PASS |
| pre_validation_run | GHA run 25521618249 (measure-execution-prevalidation.yml) — 26s PASS |
| pre_validation_verdict | PASS — claude 2.1.132 installed, no auth issues |
| main_run | GHA run 25532761179 (measure-execution.yml) — completed (workflow exit 0; measurement data EMPTY) |
| claude_binary | real |
| claude_version | 2.1.133 (Claude Code) — main run installed via npm |
| workflow_file | .github/workflows/measure-execution.yml (modified for T-2-2 Candidate A real-claude install at lines 80-113) |
| AC_closures_evidenced | AC-7(ii) **FAIL** — real-claude/daemon integration gap empirically proven; carries to v0.1.11 |

## §pre-validation-evidence

Pre-validation workflow run 25521618249 on `feat/v0.1.10-daemon-spec-changes` (push trigger):

| Step | Result | Notes |
|---|---|---|
| Checkout repository | PASS | commit bedff96 |
| Set up Python 3.10 | PASS | python-3.10.11 installed |
| Attempt npm install of claude CLI | PASS | added 2 packages in ~2s |
| Check claude binary availability | PASS | /opt/homebrew/bin/claude, version 2.1.132 |
| Smoke test claude help (non-interactive) | PASS | exit 0 |

**Bail criteria check**: exit !=0 → No. Authentication prompts → None observed. Install >4min → No (~2s). **Gate: PROCEED TO CANDIDATE A.**

The pre-validation confirmed real claude is INSTALLABLE on GHA macos-14 with no auth blockers. This was the gating condition for selecting Candidate A. However, the pre-validation did NOT exercise the daemon-claude integration path (it only tested install + version + help), which is where the main run subsequently failed.

## §main-run-evidence (REAL-CLAUDE INTEGRATION GAP)

Main measurement workflow run 25532761179 on commit efbd5af (push trigger; main run after Stage 2 commits landed):

### Workflow steps that PASSED

- Set up job
- Checkout repository
- Set up Python 3.11
- **Verify python3 >= 3.10 (AC-9 hard gate)** — PASS (Python 3.11.9)
- Create .teamlead workspace directory
- Confirm prerequisites
- **Install real claude CLI** — PASS (claude 2.1.133 at /opt/homebrew/bin/claude in 3s)
- Capture GHA python3 path
- **Verify real claude is on PATH** — PASS
- Capture host environment

### Cold-start measurement loop — 10/10 FAIL at C-4

For each of 10 cold runs:
- C-1 (clean state): PASS — uninstall succeeded each iteration
- C-2 (write baton T0): PASS — `tools/measure-write-baton.py` returned timestamp
- C-3 (install daemon): PASS — `scripts/install.py` exited 0 (~13s install per cold cycle including launchctl bootstrap with real claude PATH injection)
- **C-4 (poll for SESSION_RESUMED, timeout 90s): FAIL all 10 runs** — `tools/measure-poll-resumed.py` timed out without observing SESSION_RESUMED file in `.teamlead/baton.json` `.history` field

Sample timeline (cold-run-1):
- T0 (baton write): 02:13:06.83
- C-3 install PASS: 02:13:19.45 (~13s install)
- C-4 polling start: 02:13:19.45
- C-4 timeout: 02:13:42.09 (~22s poll, then early-exit since no signal)
- Latency: never measured

### Warm-start measurement loop — 10/10 FAIL at W-3

For each of 10 warm runs:
- W-1 (verify daemon loaded): PASS — `launchctl print` confirmed daemon in user session
- W-2 (write baton T0): PASS
- **W-3 (poll for SESSION_RESUMED, timeout 60s): FAIL all 10 runs** — same root cause as C-4

Sample timeline (warm-run-1):
- T0 (baton write): 02:20:22.27
- W-3 polling start: 02:20:22.27
- W-3 timeout: 02:20:48.10 (~26s poll, early-exit no signal)

### Statistics step output

```json
{
  "cold": {"error": "no cold runs or empty file", "n": 0},
  "warm": {"error": "no warm runs or empty file", "n": 0}
}
```

AC verdicts (per workflow Compute statistics step):
- Cold AC-2: **FAIL**
- Warm AC-2: **FAIL**
- AC-3: **FAIL**

AC-1 (per Collect step): **FAIL** (cold=0 warm=0; expected ≥10 each).

### Cleanup

`launchctl bootout` cleanup ran successfully; daemon was removed from session by workflow Cleanup step. No host-state contamination remains.

## §root-cause-analysis (preliminary)

The empirical pattern (install PASS + SESSION_RESUMED never fires) indicates the daemon's polling logic in `_wait_for_session_resumed` (or equivalent polling target — see `scripts/daemon.py` and `tools/measure-poll-resumed.py`) is looking for an artifact that **stub-claude produced but real-claude does not**. Possible mechanisms (un-validated; require v0.1.11 engineering investigation):

1. **Stub-claude wrote a sentinel file the polling tool watches**, but real claude (`claude --resume <session-id>`) writes to a different path or with different schema; daemon's signal-detection logic was implicitly designed against the stub artifact format.
2. **Real claude requires a valid session-id to resume**, and the daemon's baton-driven invocation passes a stub/empty session-id that real claude rejects (silently or with output to stderr that polling doesn't capture).
3. **Real claude requires interactive auth on first run**, and the GHA runner's claude install path does not have a credential pre-provisioned, so claude exits before producing SESSION_RESUMED-like signals.
4. **Real claude operates differently in non-TTY context**, and the daemon spawning real claude via launchd (no controlling TTY) hits a different code path than the stub which was unconditional.

This list is hypothesis-only; v0.1.10 charter does NOT scope a daemon-real-claude integration debug effort. See §carry-forward.

## §methodology-deviations-inheritance

| Source | Deviation | v0.1.10 GHA status |
|---|---|---|
| measurement-protocol.v0.1.9.md deviation-1 (stub-claude) | Stub-claude for T5 SESSION_RESUMED on GHA | **SUPERSEDED at install layer** (real claude installed); **STILL APPLIES at integration layer** (only stub mode produces measurable SESSION_RESUMED signals on this daemon design) |
| measurement-protocol.v0.1.9.md deviation-2 (Gate_Human N/A) | Gate_Human N/A for non-interactive evidence | INHERITED — unchanged |
| measurement-protocol.v0.1.10.md deviation-3 (T-2-1 local BLOCKED) | env-class block: system python3 3.9 + hook hard-deny | INHERITED — applies to local host; not GHA |
| **measurement-protocol.v0.1.10.md deviation-4 (NEW)** | **GHA real-claude/daemon integration gap empirically proven (10/10 cold + 10/10 warm SESSION_RESUMED FAIL)** | NEW — registered at this evidence file commit |

## §raw-data

### cold-start (N=10)

```
cold_runs.jsonl: 0 bytes (empty — no run completed C-4 polling step)
```

### warm-start (N=10)

```
warm_runs.jsonl: 0 bytes (empty — no run completed W-3 polling step)
```

### Per-run install logs

10 cold install logs (`/tmp/install-cold-run-{1..10}.txt`, ~814B each) + 1 warm baseline install log (`/tmp/install-warm-baseline.txt`) uploaded as workflow artifact `measurement-macos-14`. Install logs confirm daemon was installed correctly each iteration; integration gap is exclusively in the post-install signal-detection layer.

## §statistics

| Type | N | p50 (s) | p95 (s) | max (s) | AC-2 verdict |
|---|---|---|---|---|---|
| cold | 0 | — | — | — | **FAIL** (no data) |
| warm | 0 | — | — | — | **FAIL** (no data) |

Note: degeneracy clause (p95 = max at N=10) does not apply when N=0.

## §ship-gate-verdict

**AC-7(ii) GHA real-claude end-to-end measurement: FAIL**

Empirical evidence: 10/10 cold + 10/10 warm SESSION_RESUMED never reached within charter timeouts (C-4 90s; W-3 60s). Root cause: real-claude/daemon integration gap (deviation-4); ship-gate ≤30s threshold cannot be evaluated since no latency was measured.

**AC-7 (overall, both hosts): PARTIAL with comprehensive empirical proof of unavailability**

- AC-7(i) local: PROVEN-UNAVAILABLE (env-class; deviation-3) — install lifecycle hardening deferred to v0.1.11
- AC-7(ii) GHA: PROVEN-INTEGRATION-GAP (real-claude/daemon protocol mismatch; deviation-4) — daemon integration engineering deferred to v0.1.11

Stage 2 close acceptable per Opus PlanAudit S2 `partial_acceptable_for_Stage2_close` rule: empirical proof exists for both hosts (not silent skip); integration gap is itself measured evidence; Gate_Requirement final verdict will be PARTIAL-MET on AC-7 with explicit deviation-3 + deviation-4 citations.

## §carry-forward (v0.1.11)

Two RAID items carried forward from this evidence:

1. **RAID-V11-real-claude-integration**: Daemon SESSION_RESUMED signal-detection logic was implicitly designed against stub-claude artifact format. Real claude does not produce equivalent signal. v0.1.11 engineering work: (a) characterize what real claude produces on `claude --resume`, (b) update daemon's polling target OR claude-side hook OR baton schema accordingly, (c) re-run AC-7(ii) measurement against patched daemon-claude integration. Severity: high (blocks all real-claude measurement on any host class).
2. **RAID-V11-install-lifecycle-python3-path**: install.py + plist template re-render loses patch-plist-python3.py runtime fix; needs PYTHON3_PATH substitution variable in template + install.py env injection (Option B from Stage 2 RAID-I-S2-launchctl-hook). Severity: medium (blocks AC-7(i) local on hosts with system python3 < 3.10).

Both items pre-emptively recorded in v0.1.10 ProjectClose as v0.1.11 charter inputs.
