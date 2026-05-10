# Real-claude `--resume` Characterization — v0.1.11 AC-1

**Purpose**: Empirical characterization of what real `claude --resume` produces (file-system side
effects + stdout/stderr + exit code + timing) for the 4 hypothesis vectors in
`docs/archives/measurement-real-claude-gha.v0.1.10.md §root-cause-analysis`.

**Dispatch**: V0.1.11-S1-EX1

## §metadata

| Field | Value |
|---|---|
| date | 2026-05-10 |
| host | macOS 25.3.0 (Darwin), local developer machine |
| claude_binary | real (path: /Users/HsuTse/.local/state/fnm_multishells/59076_1778374017372/bin/claude) |
| claude_version | 2.1.112 (Claude Code) |
| auth_status | provisioned (CEO actively using claude CLI on this host) |
| python3 | 3.13.13 (pyenv global 3.13.13 + brew python@3.13) |
| branch | feat/v0.1.11-real-claude-integration |
| experiment_time | 2026-05-10T11:31–11:32Z (approximate) |

## §V2 verification — Synthetic session_id rejection

### Root-cause hypothesis (from v0.1.10 §root-cause-analysis)

**Vector V2**: "Real claude requires a valid session-id to resume, and the daemon's baton-driven
invocation passes a stub/empty session-id that real claude rejects (silently or with output to stderr
that polling doesn't capture)."

### Experiment V2-A: non-UUID literal session_id (the exact daemon invocation)

The daemon's T5 actor reads `session_id` from `baton.json` and spawns:

```
claude --resume <session_id> -p <restore_prompt>
```

The measurement workflow writes `baton.json` via `tools/measure-write-baton.py` which hardcodes:

```python
"session_id": "measurement-run-synthetic-session"  # line 29
```

**Experiment command** (verbatim daemon T5 spawn for the measurement baton):

```bash
claude --resume measurement-run-synthetic-session -p "Measurement run synthetic resume prompt."
```

**Result**:

| Field | Value |
|---|---|
| exit_code | **1** |
| wall_clock_s | 7.910 (run 1), 15.281 (run 2), 10.629 (run 3), 8.298 (run 4) — cold-start variance due to OAuth/API initialization overhead |
| stdout | (empty) |
| stderr | `Error: --resume requires a valid session ID or session title when used with --print. Usage: claude -p --resume <session-id|title>. Provided value "measurement-run-synthetic-session" is not a UUID and does not match any session title.` |

**Classification**: **V2 confirmed-root-cause (non-UUID format rejection)**.

Real claude 2.1.112 (and 2.1.133 on GHA) validates the `--resume` argument when used with `--print`
(`-p`). A non-UUID literal like `"measurement-run-synthetic-session"` triggers immediate format
validation failure at startup with exit code 1.

### Experiment V2-B: valid UUID format, non-existent session

To differentiate "format rejected" vs "session not found" (both V2 sub-cases with different fix
implications):

```bash
claude --resume 25efaffa-2e35-49b4-8c11-fc1e25bd0353 -p "Measurement run synthetic resume prompt."
```

(UUID generated via `uuidgen | tr '[:upper:]' '[:lower:]'`; no such session exists locally.)

**Result**:

| Field | Value |
|---|---|
| exit_code | **1** |
| wall_clock_s | 7.319 |
| stdout | (empty) |
| stderr | `No conversation found with session ID: 25efaffa-2e35-49b4-8c11-fc1e25bd0353` |

**Classification**: Both V2 sub-cases (non-UUID format + valid-UUID-but-not-found) produce exit code
1. They differ in error message and fix implication:
- **V2-A (non-UUID)**: daemon must pass a real session UUID from a prior claude session. Fix scope:
  `tools/measure-write-baton.py` must capture a real session ID from a real prior session.
- **V2-B (UUID not found)**: even with UUID format, a session must actually exist. Fix scope: the
  measurement workflow must perform a real preceding claude session that creates the session-id, then
  pass that session-id via the baton.

### Critical timing analysis (daemon interaction model)

The daemon's T5 actor uses `proc.wait(timeout=2.0)` to detect immediate failure:

```python
try:
    exit_code = proc.wait(timeout=2.0)
except subprocess.TimeoutExpired:
    # Process still running — treat as success (expected long-lived)
    exit_code = 0
if exit_code != 0:
    raise subprocess.CalledProcessError(exit_code, cmd)
```

**Local host (auth provisioned)**: real claude takes **8–15 seconds** to exit (cold-start OAuth/API
initialization overhead). This exceeds the 2.0s timeout. Therefore:

1. Daemon's `proc.wait(timeout=2.0)` fires `TimeoutExpired`
2. `exit_code` is set to `0` (success)
3. `spawn_succeeded = True`
4. **Daemon writes `gate_state=SESSION_RESUMED`** to `baton.json` (line 606, `daemon.py`)
5. Measurement poller observes `gate_state=SESSION_RESUMED` and records a latency
6. However, claude exits with code 1 approximately 8–15s after spawn — the measured "SESSION_RESUMED"
   latency is a **false positive** (daemon wrote SESSION_RESUMED unilaterally; no actual session was
   resumed)

**GHA host (no auth credentials provisioned)**: claude exits fast (< 2.0s) because the auth check
fails immediately without network round-trip. Therefore:

1. Daemon's `proc.wait(timeout=2.0)` returns the actual exit code 1
2. Daemon raises `CalledProcessError` → T6 retry
3. After T6_MAX_RETRIES (3) exhausted: `gate_state=ABORTED`
4. Measurement poller exits at ABORTED state → 0 latency records

**This explains the GHA v0.1.10 evidence**: GHA claude exits within 2s (no auth → fast rejection) →
daemon sees exit_code=1 → T6 exhausted → ABORTED → SESSION_RESUMED never written.

**AC-2 fix implication**: Two distinct fixes required, not one:
1. `tools/measure-write-baton.py` must pass a real session UUID (not hardcoded literal)
2. The measurement workflow must ensure a valid prior session exists for that UUID to reference
3. Alternatively: redesign daemon's SESSION_RESUMED signal so it does NOT depend on `claude --resume`
   exit timing (e.g., poll claude process exit + verify actual session continuation via hook/baton
   written by the resumed claude process)

## §V1 ruling — Sentinel file written by claude

### Root-cause hypothesis (from v0.1.10 §root-cause-analysis)

**Vector V1**: "Stub-claude wrote a sentinel file the polling tool watches, but real claude writes to
a different path or with different schema."

### File-system diff (before vs after V2-A + V2-B experiments)

**Before experiments** (`.teamlead/` snapshot):

```
drwxr-xr-x  30 HsuTse  staff    960  5月  8 04:16 .teamlead/
-rw-------   1 HsuTse  staff    402  5月  4 09:24 baton.json
-rw-------   1 HsuTse  staff      2  5月  8 04:03 daemon-retries
-rw-------   1 HsuTse  staff      6  5月  8 04:16 daemon.pid
...total 28 files, all with mtime ≤ 2026-05-08
```

**After experiments** (`.teamlead/` snapshot):

```
drwxr-xr-x  30 HsuTse  staff    960  5月  8 04:16 .teamlead/
-rw-------   1 HsuTse  staff    402  5月  4 09:24 baton.json
-rw-------   1 HsuTse  staff      2  5月  8 04:03 daemon-retries
-rw-------   1 HsuTse  staff      6  5月  8 04:16 daemon.pid
...total 28 files — UNCHANGED
```

**Result**: `.teamlead/` directory: **IDENTICAL** before and after running
`claude --resume measurement-run-synthetic-session -p "..."` and
`claude --resume <uuid> -p "..."`. No new files created; no existing files modified.

**Claude projects directory** (`~/.claude/projects/-Users-HsuTse-ClaudeProject-teamwork-leader/`):
Only `b3487450-a005-41cc-94ce-a48005d1b7e8.jsonl` grew in size (2797459 → 2814838 bytes). This
is the session log for the **current conversation** (this dispatch itself running inside claude), NOT
a side-effect of the `claude --resume` invocations under test.

**Classification**: **V1 ruled out as root cause.**

Real claude does NOT write any sentinel file to `.teamlead/` when it exits with error. More
precisely: the poller tool (`tools/measure-poll-resumed.py`) does NOT watch a sentinel file at all —
it polls `baton.json`'s `gate_state` field. V1 hypothesis was based on a misread of the polling
architecture. The `gate_state=SESSION_RESUMED` transition is written exclusively by `daemon.py` (line
606) — not by claude or any claude-side hook.

**Implication**: The stub-claude's 3-second `sleep + exit 0` worked not because it wrote a sentinel
file, but because:
1. It kept running for 3 seconds (> 2.0s daemon timeout)
2. Daemon's `TimeoutExpired` set `exit_code=0`
3. Daemon wrote `gate_state=SESSION_RESUMED` unilaterally
4. Poller observed SESSION_RESUMED from baton.json

V1 was a red herring based on misattribution of what "the polling tool watches."

## §V3 status — Authentication requirement

### Root-cause hypothesis (from v0.1.10 §root-cause-analysis)

**Vector V3**: "Real claude requires interactive auth on first run, and the GHA runner's claude
install path does not have a credential pre-provisioned."

### Status: inferred-ruled-out-as-exclusive-cause (but partially contributory on GHA)

**Evidence from v0.1.10 pre-validation** (run 25521618249):

```
| Smoke test claude help (non-interactive) | PASS | exit 0 |
```

The pre-validation confirmed `claude --help` (non-interactive, non-`--print`) exits 0 on GHA without
auth prompts. Auth is NOT required for the binary to run.

**However**, with `--print` (`-p`) flag: real claude connects to the Anthropic API, which requires
credentials. On GHA runner (no claude auth configured):
- `claude --resume <id> -p "..."` would attempt API access and fail fast (< 2.0s) with auth error
- This causes exit code 1 within the daemon's 2.0s window → T6 retry chain → ABORTED

**V3 is NOT an exclusive root cause** — it is a contributing factor on GHA that causes the claude
process to exit fast (< 2.0s), which interacts with V2 to produce the T6-ABORTED outcome. The
primary root cause remains V2 (invalid session_id). Even with valid credentials + valid session_id, a
session-not-found error would still occur.

**Local host**: auth is provisioned (CEO actively using claude). On local host, auth does not cause
fast exit — claude initializes fully (~8–15s) before exiting with the session_id validation error.

**Classification**: V3 is **inferred-contributory-on-GHA** (accelerates fast exit → T6 path) but
**not an exclusive root cause**. Fixing V2 (valid session_id) would subsume V3 fix on GHA because a
valid session_id requires credentials to have been used during session creation anyway.

## §V4 status — Non-TTY execution context

### Root-cause hypothesis (from v0.1.10 §root-cause-analysis)

**Vector V4**: "Real claude operates differently in non-TTY context, and the daemon spawning real
claude via launchd (no controlling TTY) hits a different code path than the stub which was
unconditional."

### Status: inferred-not-blocking

**Reasoning**: V2 is the confirmed root cause. Real claude exits with code 1 for the
`measurement-run-synthetic-session` literal regardless of TTY context — this is a format-validation
check at startup before any TTY-dependent behavior. The non-TTY issue (if any) would only manifest if
a valid session_id were provided but the resumed session attempted to present interactive UI.

**V4 investigation is not needed for AC-2 patch scoping**: the daemon patch must fix the session_id
source (V2 fix). Once a valid session_id is passed and a real session exists, V4 may or may not
surface as a secondary issue. If it does, it will appear as a distinct failure mode distinguishable
from V2 (different error message, different timing pattern).

**Classification**: V4 is **inferred-not-blocking** for AC-2 patch design. Mark for monitoring
during V2-fix validation in Stage 2.

## §root-cause-summary

### Per-vector classification

| Vector | Description | Classification | Evidence |
|---|---|---|---|
| V1 | Stub wrote sentinel file poller watches | **ruled-out** | `.teamlead/` unchanged after claude --resume; poller watches `baton.json gate_state` written by daemon, not claude |
| V2 | Invalid session_id causes rejection | **confirmed-root-cause** | exit_code=1; stderr: "not a UUID and does not match any session title"; reproducible locally |
| V3 | GHA auth not provisioned → fast exit | **inferred-contributory-GHA** | Pre-validation PASS for --help; API-mode fast exit on GHA contributes to T6-ABORTED path |
| V4 | Non-TTY context difference | **inferred-not-blocking** | V2 is pre-TTY check; V4 may surface as secondary issue after V2 fix |

### AC-2 patch scope

**Primary fix (V2 confirmed)**:

1. `tools/measure-write-baton.py` must NOT hardcode `"measurement-run-synthetic-session"`.
   The session_id must be a real UUID from a real prior claude session.

2. The measurement workflow must perform a preceding real claude session (e.g.,
   `claude -p "measurement session init"`) and capture the resulting session_id for use in the baton.

3. The `patch-plist-python3.py` PATH injection correctly places real claude on launchd PATH. This
   part of the v0.1.10 workflow was correct.

**Secondary observation (timing model)**:

The daemon's `proc.wait(timeout=2.0)` + `TimeoutExpired=success` heuristic is architecturally
correct for a long-lived claude session (which would run > 2s). The issue is that when the session_id
is invalid, claude exits between 8–15s (local, auth provisioned) or < 2s (GHA, no auth) — producing
inconsistent daemon behavior across host classes. A more robust design would poll claude's actual
process exit and verify SESSION_RESUMED via a baton write from claude itself (or hook), rather than
relying on timing.

**Daemon behavior on local vs GHA with current code**:

| Host | Auth | claude exit timing | Daemon interpretation | Baton outcome |
|---|---|---|---|---|
| Local (auth) | provisioned | 8–15s | TimeoutExpired → exit_code=0 → SESSION_RESUMED written by daemon | SESSION_RESUMED (false positive) |
| GHA | not provisioned | < 2s | actual exit_code=1 → CalledProcessError → T6 retry → ABORTED | ABORTED |

## §carry-forward (Stage 2 — AC-2 daemon patch + measurement fix)

1. **Fix `measure-write-baton.py` session_id**: Replace hardcoded
   `"measurement-run-synthetic-session"` with a mechanism to obtain a real session UUID. Options:
   - (a) Read the most recent session-id from `~/.claude/projects/<project>/` (most recent `.jsonl`
     filename = session-id)
   - (b) Add a `--session-id <uuid>` CLI argument to `measure-write-baton.py` and have the workflow
     supply a real session-id from a prior step
   - (c) Create a dedicated "measurement init session" workflow step that runs
     `claude -p "init" --output-format json` and parses the session_id from response

2. **Measurement workflow prerequisite**: A real prior session must exist. The workflow must either
   create one or reference a known existing session_id from a previous run.

3. **V3 subsumption**: Once V2 is fixed with a valid session_id from a provisioned session, V3 (GHA
   auth) is automatically subsumed — a real session_id implies credentials were used during that
   session's creation.

4. **V4 monitoring**: After V2 fix, if `claude --resume <valid-id> -p "..."` still fails in the
   launchd/non-TTY context, register V4 as a new confirmed root cause. Expected evidence: different
   error message (not session_id format error) + potentially different timing profile.

5. **Daemon architecture note (RAID-A)**: The `proc.wait(timeout=2.0)` heuristic produces
   inconsistent behavior across host classes (local-auth vs GHA-no-auth). A more robust signal would
   be baton-written by the resumed claude process or its hook, eliminating the timing dependency.
   This is a design improvement for future consideration; not blocking AC-2.
