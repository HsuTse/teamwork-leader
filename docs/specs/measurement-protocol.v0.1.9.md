# Measurement Protocol — v0.1.9 I-023-M1

**Status**: normative (T-1-b output; DoD: §acceptance-criteria gates T-1-c execution)

---

## §metadata

| Field | Value |
|---|---|
| version | v0.1.9 |
| charter_ref | I-023-M1 Measurement on Reference Host (`feat/v0.1.9-measurement`) |
| date | 2026-05-05 |
| authored_by | PO PM dispatch V0.1.9-S1-D5 (T-1-b) |
| frozen_design_ref | `docs/specs/auto-resume-daemon-design.md §7` |

### Acceptance criteria accepted values (Q2 defaults locked)

| AC | Accepted value |
|---|---|
| AC-1 | N ≥ 10 measurement runs per type (cold and warm are separate counters; both must reach N ≥ 10) |
| AC-2 | Strict three-statistic gate per set: p50 ≤ 30 s ∧ p95 ≤ 30 s ∧ max ≤ 30 s; evaluated independently for cold-start set and warm-start set |
| AC-3 | Cold-start (no prior plist; fresh install state) and warm-start (plist present, daemon running) measured separately; each independently gated by AC-2; both MUST pass |
| AC-4 | Host environment recorded: OS version, launchctl bootstrap path, hook chain status, plist install path |
| AC-5 | Evidence archived at `docs/archives/measurement.v0.1.9.md` per §archive-target |

---

## §definitions

**baton-write event**: the filesystem write of `$CLAUDE_PROJECT_DIR/.teamlead/baton.json` by the PreCompact hook (or Stop hook as fallback). The wall-clock timestamp of this write is the START anchor for latency measurement. Defined by design.md §2 write protocol.

**SESSION_RESUMED event**: the log entry or stdout line emitted by the SessionStart hook when it detects a valid baton and initiates `claude --resume <session_id> -p`. The wall-clock timestamp of this emission is the END anchor for latency measurement. Defined by design.md §1 state machine `POST_RESUME_VERIFIED` checkpoint.

**wall-clock latency**: the elapsed time in seconds between baton-write event and SESSION_RESUMED event, measured on the same host without clock adjustment. Computed as: `latency_s = SESSION_RESUMED_timestamp - baton_write_timestamp`. The ≤ 30 s threshold derives from design.md §7 term (a) (NOT relaxed by this protocol).

**cold-start**: a measurement run in which no launchd plist for the daemon exists at the expected install path prior to the run, and no daemon process is running. The install script (`scripts/install.py`) must be invoked at the start of each cold-start run to bring the daemon up from scratch. Cold-start reflects worst-case latency: launchd must load the plist, spawn the process, and the SessionStart hook must execute before SESSION_RESUMED is recorded.

**warm-start**: a measurement run in which the launchd plist is already present and the daemon process is already running from a prior successful installation. The daemon is NOT restarted between warm-start runs (except for the mandatory inter-run settle period). Warm-start reflects steady-state latency under normal operating conditions.

---

## §measurement-procedure

### Prerequisites (must be confirmed before T-1-c kickoff)

1. GHA macOS runner meets reference-host requirements per design.md §7 term (c):
   - `pretooluse_guard.py` (or equivalent bash-hook) NOT active or `launchctl` excluded from its intercept pattern
   - `launchctl bootstrap` executable under the runner's user session without permission denial
   - `python3` available at a path resolvable by launchd `ProgramArguments`
   - Claude Code installable with plugin `teamwork-leader` loaded (or stub-equivalent per §methodology-deviations)
2. T-1-a workflow (`measure-latency.yml`) has produced PASS verdict (at least `macos-14` arm64) — per M-2 gate.
3. T-1-b (this protocol doc) merged to `feat/v0.1.9-measurement`.

### Environment setup (once per runner job)

```
# 1. Checkout repo
git checkout feat/v0.1.9-measurement

# 2. Setup Python
python3 --version  # confirm 3.11+

# 3. Confirm launchctl availability
launchctl bootstrap --help 2>&1 | head -5

# 4. Confirm project dir
echo "$CLAUDE_PROJECT_DIR"
ls "$CLAUDE_PROJECT_DIR/.teamlead/" 2>/dev/null || echo "teamlead dir absent — expected for cold-start"
```

### Cold-start sequence (N = 10 runs minimum)

Cold-start run `i` (for i = 1..N_cold):

```
# Step C-1: Verify no plist present (cold precondition)
PLIST_PATH="$HOME/Library/LaunchAgents/com.teamwork-leader.auto-resume.plist"
if [ -f "$PLIST_PATH" ]; then
  launchctl unload "$PLIST_PATH" 2>/dev/null || true
  python3 scripts/install.py --uninstall
fi
ls "$PLIST_PATH" 2>/dev/null && echo "FAIL: plist still present" && exit 1

# Step C-2: Record baton-write start time (T0)
# T0 is the mtime of baton.json written by the hook under test.
# For GHA runner execution: trigger a synthetic PreCompact event via
# tools/measure-latency.sh --trigger-baton-write
T0=$(python3 -c "import time; print(time.time())")

# Step C-3: Install daemon (cold install)
python3 scripts/install.py 2>&1 | tee /tmp/install-run-${i}.txt
# Verify install PASS (dual-detection per T-1-a C-2):
grep -v "MANUAL INSTALLATION REQUIRED" /tmp/install-run-${i}.txt
STATUS_FILE="$CLAUDE_PROJECT_DIR/.teamlead/install-state.json"
python3 -c "import json,sys; s=json.load(open('$STATUS_FILE')); sys.exit(0 if s.get('status') != 'manual-pending' else 1)"

# Step C-4: Wait for SESSION_RESUMED event (poll up to 60 s)
python3 tools/measure-latency.sh --wait-session-resumed --timeout 60 --out /tmp/run-${i}.json

# Step C-5: Compute latency_s from /tmp/run-${i}.json
python3 -c "
import json
r = json.load(open('/tmp/run-${i}.json'))
print(f'run={i} type=cold latency_s={r[\"latency_s\"]:.3f}')
"

# Step C-6: Inter-run cleanup (uninstall daemon; allow settle 5 s)
python3 scripts/install.py --uninstall
sleep 5
```

Collect run records for all N_cold runs into `cold_runs.jsonl` (one JSON object per line, format per §evidence-format).

### Warm-start sequence (N = 10 runs minimum)

Prerequisite: daemon is installed and running (install once before warm-start loop):

```
python3 scripts/install.py 2>&1 | tee /tmp/install-warm-baseline.txt
# Verify PASS via dual-detection (same as C-3 above)
```

Warm-start run `j` (for j = 1..N_warm, daemon remains installed between runs):

```
# Step W-1: Confirm plist present and daemon running (warm precondition)
if [ ! -f "$PLIST_PATH" ]; then echo "FAIL: plist absent — not warm-start"; exit 1; fi
launchctl list | grep "com.teamwork-leader.auto-resume" || { echo "FAIL: daemon not listed"; exit 1; }

# Step W-2: Trigger baton-write event
python3 tools/measure-latency.sh --trigger-baton-write

# Step W-3: Wait for SESSION_RESUMED event
python3 tools/measure-latency.sh --wait-session-resumed --timeout 60 --out /tmp/run-warm-${j}.json

# Step W-4: Compute latency_s
python3 -c "
import json
r = json.load(open('/tmp/run-warm-${j}.json'))
print(f'run={j} type=warm latency_s={r[\"latency_s\"]:.3f}')
"

# Step W-5: Inter-run settle (5 s); do NOT uninstall between warm runs
sleep 5
```

Post warm-loop: uninstall daemon (`python3 scripts/install.py --uninstall`).

Collect run records for all N_warm runs into `warm_runs.jsonl`.

### Per-run artifact collection

After completing cold and warm loops, collect:

1. `cold_runs.jsonl` — N_cold raw run records
2. `warm_runs.jsonl` — N_warm raw run records
3. `host_env.json` — host environment block (§evidence-format)
4. `/tmp/install-run-*.txt` — install log per cold run
5. `/tmp/install-warm-baseline.txt` — warm-start baseline install log

Upload all as GHA artifact `t1c-measurement-${{ runner.os }}-${{ runner.arch }}`.

---

## §acceptance-criteria

> This section is normative. T-1-d gate evaluation MUST reference these exact criteria.

### AC-1 — Sample size (N)

- Cold-start counter: N_cold ≥ 10 completed measurement runs (runs where SESSION_RESUMED was recorded within 60 s timeout and no install error occurred)
- Warm-start counter: N_warm ≥ 10 completed measurement runs (same completion conditions)
- Cold and warm counters are INDEPENDENT; N_cold and N_warm are evaluated separately
- Aborted runs (install error, timeout, or launchctl denial) do NOT count toward N

### AC-2 — Latency gate (three-statistic)

For **each** of cold-start set and warm-start set, evaluated independently:

- p50 ≤ 30 s (see §statistics-computation for p50 method)
- p95 ≤ 30 s (see §statistics-computation for p95 method, including N=10 degeneracy clause)
- max ≤ 30 s (raw maximum of all N runs in the set)

The ≤ 30 s threshold is the design.md §7 term (a) value and is NOT relaxed by this protocol.

AC-2 is satisfied for a given set iff ALL THREE statistics are ≤ 30 s.

### AC-3 — Independent cold + warm gating

- Cold-start and warm-start MUST be measured separately (no pooling of cold and warm runs)
- AC-2 is applied independently to the cold-start set AND independently to the warm-start set
- AC-3 is satisfied iff: AC-2(cold) = PASS AND AC-2(warm) = PASS
- Partial satisfaction (one set PASS, one FAIL) = AC-3 FAIL

### AC-4 — Host environment recorded

All of the following fields MUST be present in the archived `host_env.json` block:

- `os` — OS name and version (e.g., `"macOS 14.5 (Sonoma)"`)
- `arch` — CPU architecture (e.g., `"arm64"`)
- `launchctl_bootstrap_path` — absolute path of `launchctl` binary used (from `which launchctl`)
- `hook_chain` — list of active hook types (e.g., `["PreCompact", "SessionStart"]`) and their script paths
- `plist_install_path` — absolute path where daemon plist was installed (e.g., `"$HOME/Library/LaunchAgents/com.teamwork-leader.auto-resume.plist"`)
- `runner_info.gha_runner_label` — GHA runner label (e.g., `"macos-14"`)
- `runner_info.gha_runner_arch` — GHA reported arch (from `${{ runner.arch }}`)

---

## §statistics-computation

### p50 (median)

Sort the N latency values in ascending order. p50 = the value at index `⌈N/2⌉ - 1` (0-indexed, ceiling midpoint). For N=10: p50 = value at index 4 (the 5th-smallest value).

### p95 (95th percentile — ceiling rule for small N)

Sort the N latency values in ascending order. p95 = the value at index `⌈0.95 × N⌉ - 1` (0-indexed, ceiling rule). This is the nearest-rank method.

For N=10: `⌈0.95 × 10⌉ = ⌈9.5⌉ = 10`; p95 = value at index 9 = the 10th-order-statistic (i.e., the maximum).

**N=10 p95=max degeneracy clause (PO-2)**: At N=10, p95 is computed as the 10th-order-statistic (i.e., equals max by sample definition); AC-2 evaluation at N=10 therefore reduces to two independent gates (p50 ≤ 30 s AND max ≤ 30 s); AC-2 is satisfied iff both hold. To obtain a p95 statistic distinct from max, N ≥ 20 is required; relaxation to N ≥ 20 to recover distinct p95 is permitted via CCB-Light at T-1-c kickoff if cold-start-only N=10 cost-budget headroom is available.

### max

Raw maximum: `max = max(latency_1, ..., latency_N)`. No percentile computation; this is the observed worst-case value.

### Summary computation example (N=10 cold-start set)

```python
import statistics, math

runs = [r["latency_s"] for r in cold_runs]  # N=10 values
runs_sorted = sorted(runs)

p50 = runs_sorted[math.ceil(10 / 2) - 1]          # index 4
p95 = runs_sorted[math.ceil(0.95 * 10) - 1]       # index 9 (= max at N=10)
max_val = runs_sorted[-1]

ac2_cold = (p50 <= 30.0) and (p95 <= 30.0) and (max_val <= 30.0)
# At N=10: p95 == max_val always; ac2_cold reduces to p50 <= 30 and max_val <= 30
```

---

## §evidence-format

### Per-run record (one JSON object per line in `cold_runs.jsonl` / `warm_runs.jsonl`)

```json
{
  "run_id": "cold-001",
  "type": "cold",
  "latency_s": 12.345,
  "timestamp_iso": "2026-05-10T08:23:41Z",
  "baton_write_ts": 1747034621.000,
  "session_resumed_ts": 1747034633.345,
  "runner_info": {
    "os": "macOS 14.5 (Sonoma)",
    "arch": "arm64",
    "gha_runner_label": "macos-14",
    "gha_runner_arch": "ARM64"
  }
}
```

For warm-start runs: `"run_id": "warm-001"`, `"type": "warm"`.

### Summary table format (per type, in final archive doc)

| Type | N | p50 (s) | p95 (s) | max (s) | AC-2 verdict |
|---|---|---|---|---|---|
| cold | 10 | &lt;value&gt; | &lt;value&gt; | &lt;value&gt; | PASS / FAIL |
| warm | 10 | &lt;value&gt; | &lt;value&gt; | &lt;value&gt; | PASS / FAIL |

Note: at N=10, p95 = max (per §statistics-computation degeneracy clause). Summary table MUST include a footnote: "p95 = max at N=10 by sample definition (see §statistics-computation)."

### Host environment block format (`host_env.json`)

```json
{
  "os": "macOS 14.5 (Sonoma)",
  "arch": "arm64",
  "launchctl_bootstrap_path": "/bin/launchctl",
  "hook_chain": [
    {"type": "PreCompact", "script": "hooks/precompact_hook.py"},
    {"type": "SessionStart", "script": "hooks/session_start_hook.py"}
  ],
  "plist_install_path": "/Users/runner/Library/LaunchAgents/com.teamwork-leader.auto-resume.plist",
  "runner_info": {
    "gha_runner_label": "macos-14",
    "gha_runner_arch": "ARM64"
  }
}
```

---

## §failure-mode

### AC-2 FAIL on cold or warm set

If either cold-start or warm-start set fails AC-2 (any statistic exceeds 30 s):

Execute Q3 verb per charter. Available sub-paths:

- **(i) Investigate and remediate**: diagnose latency source; if root cause identifiable and patchable within v0.1.9 scope, apply fix, re-run measurement on same runner, re-evaluate AC-2. Requires new CCB-Light entry documenting the fix.
- **(iii) Accept with documented caveat**: if latency exceeds 30 s but is within an acceptable margin (to be determined by CEO at that time), accept as degraded-mode v0.1.9 ship and update design.md §7 term (a) with measured reality. Requires CCB-Heavy (threshold change is a design parameter).
- **(iv) Defer to v0.1.10**: if root cause is not addressable within v0.1.9 scope or budget, close v0.1.9 as MEASUREMENT-DEFERRED-AGAIN; update I-023-M1 RAID entry status; carry protocol doc forward as v0.1.10 carryover asset.

The ≤ 30 s threshold in design.md §7 term (a) is NOT relaxed by this protocol; Q3 path (iii) or (iv) requires CCB-Heavy if the threshold itself changes.

### AC-1 FAIL (N < 10 due to runner timeout)

If GHA runner times out before N=10 completed runs for either type:

- AC-1 FAIL → CCB-Heavy required before any gate evaluation proceeds
- Do NOT evaluate AC-2 or AC-3 on a partial sample (N < 10)
- Record the incomplete sample in the archive doc with explicit `"ac1_status": "FAIL"` and `"n_completed"` count
- Escalate to TeamLead for charter scope decision

### Q0 fallback (launchctl bootstrap blocked on GHA)

If T-1-a or T-1-c detects `launchctl bootstrap` blocked at the OS level on both architectures (GHA runner is effectively guarded like the developer host):

- Q0 fallback fires per charter Q0 clause
- v0.1.9 closes as MEASUREMENT-DEFERRED-AGAIN (same outcome as v0.1.7 degraded-mode accept)
- This protocol doc (T-1-b output) is preserved as v0.1.10 carryover — see §parallel-execution-note
- Update I-023-M1 RAID entry: `validation_status: DEFERRED-Q0`, `deferred_to: v0.1.10`
- GHA structured failure marker format (from T-1-a): `Q1.5: launchctl bootstrap FAILED on <both arches>`

---

## §archive-target

### Target file

`docs/archives/measurement.v0.1.9.md`

This is the L-3 archive pattern lock (v0.1.7 LessonsLearned L-3: host-environment): the final measurement archive document MUST reside at the above path. Do NOT use a different filename or path.

### T-1-c QA merge responsibility

T-1-c QA merges per-arch partials written by T-1-a into the final archive doc:

- `docs/archives/measurement.v0.1.9.macos-14.partial.md` (from T-1-a macos-14 job)
- `docs/archives/measurement.v0.1.9.macos-13.partial.md` (from T-1-a macos-13 job, if PASS)

Merge structure in final `docs/archives/measurement.v0.1.9.md`:

```
# Measurement Archive — v0.1.9 I-023-M1

## §host-environment
### macos-14 arm64 (primary)
<from macos-14 partial>
### macos-13 x86_64 (secondary, if PASS)
<from macos-13 partial>

## §raw-data
### cold-start
<cold_runs.jsonl contents>
### warm-start
<warm_runs.jsonl contents>

## §statistics
<summary table per §evidence-format>

## §interpretation
<T-1-c QA narrative: AC-1/AC-2/AC-3/AC-4 verdicts; Q3 path if applicable>
```

### Partial-only path (one arch PASS)

If only macos-14 PASS (macos-13 FAIL): final archive doc contains only macos-14 §host-environment subsection, with explicit note: `"macos-13 x86_64: not included — T-1-a FAIL; see x86_64-fallback caveat in measurement.v0.1.9.macos-13.partial.md"`.

---

<!-- ccb: clarify 2026-05-06 — M-2 §methodology-deviations subsection added per Sonnet T-1-c step-review Q3 finding + Opus advisor R2 -->

## §methodology-deviations

> This section is **normative**. It authorizes documented deviations from §prerequisites that preserve T5 signal-path validity. An authorized deviation is one where the substituted mechanism exercises the identical daemon code path as the nominal mechanism, differing only in the environment artifact being substituted.

### deviation-1: stub-based claude binary

**Trigger condition**: The reference host environment (GHA macOS runners) does not have `claude` CLI pre-installed and the tool is not installable within the CI job scope. §prerequisites item 4 ("Claude Code installable with plugin `teamwork-leader` loaded") cannot be satisfied on GHA macOS runners under normal workflow constraints.

**Substitution mechanism**: `tools/claude-stub.sh` — a minimal shell script that sleeps 3 seconds then exits 0 — is placed ahead of the system `$PATH` in the daemon's `EnvironmentVariables.PATH` entry. This path injection is performed post-install via `tools/patch-plist-python3.py`, which rewrites the launchd plist to add the stub directory (e.g., `$HOME/.local/bin`) as the first PATH component. The plist reload (`launchctl bootout` + `launchctl bootstrap`) is performed by the GHA workflow step (`measure-execution.yml`) immediately after `tools/patch-plist-python3.py` rewrites the plist.

**Equivalence justification**: The daemon T5 actor (`daemon.py` function `_run_t5_actor`) invokes `subprocess.Popen(['claude', '--resume', <session_id>, '-p', <prompt>])` then `proc.wait(timeout=2.0)`. When the stub is present: the stub sleeps 3 seconds, causing `proc.wait(timeout=2.0)` to raise `subprocess.TimeoutExpired`. The T5 actor explicitly treats `TimeoutExpired` as a successful spawn (the comment in `daemon.py` L570: "Process still running — treat as success (expected long-lived)"), sets `exit_code = 0`, and proceeds to step (f): `_update_baton_gate_state(baton_path, SESSION_RESUMED)`. The same `TimeoutExpired` path is taken by a real `claude` binary, which would remain running interactively well past the 2-second window. The signal path measured — baton detection → daemon dispatch → `subprocess.Popen` spawn → `SESSION_RESUMED` gate_state write — is structurally identical under both real `claude` and the stub.

**Validity boundary**: Stub-based measurement validates the **plumbing path**: baton detection, daemon dispatch, subprocess spawn initiation, and `SESSION_RESUMED` record write. It does **NOT** validate downstream Claude Code session restoration semantics (i.e., whether `claude --resume` actually restores the prior session context). Full end-to-end validation — confirming that a real Claude Code session resumes correctly — requires a non-stub reference host with `claude` CLI installed and is **OUT-OF-SCOPE for v0.1.9 I-023-M1**. This is deferred to v0.1.10 carry-forward. **Untested branch enumeration (Opus final review R3)**: The stub guarantees the `TimeoutExpired` branch (`daemon.py` L568-571) is hit deterministically; the alternative `CalledProcessError` branch (real `claude` fast non-zero exit triggering T6 retry / potential ABORTED state via `daemon.py` T6 actor) remains untested by this measurement and is part of the v0.1.10 carry-forward end-to-end validation surface.

**Authorization scope**: This deviation is authorized for v0.1.9 I-023-M1 measurement on GHA macOS runners (`macos-14` arm64 primary; `macos-13` x86_64 if triggered). Future measurement protocols that inherit or cite this clause MUST re-evaluate whether the stub-equivalence claim holds for their specific T5 implementation (e.g., if the T5 `proc.wait` timeout value or error-handling logic is changed, the stub sleep duration and the equivalence argument must be re-validated).

**Evidentiary anchor**: `docs/archives/measurement.v0.1.9.md §interpretation` — "Measurement methodology notes" paragraph documents the stub deployment as executed and confirms the `TimeoutExpired` path was the operative mechanism in the v0.1.9 GHA run.

<!-- ccb: clarify 2026-05-06 — M-4 deviation-2 (Gate_Human N/A) added per Opus advisor 2nd consultation R1 BLOCKER -->

### deviation-2: Gate_Human declared N/A for non-interactive evidence

**Trigger condition**: The Stage's evidence surface is non-interactive (workflow run + JSONL data + measurement archive markdown), with NO interactive UI / page / modal / form / button / browser-rendered surface. v0.1.9 I-023-M1 is the canonical example: measurement is GHA-runner-produced raw data + statistical summary + protocol compliance check, none of which involves a user-facing interactive interface. `references/three-gates.md` L136-141 normatively scopes Gate_Human to interactive UI verification via `playwright-cli` / `chrome-devtools-batch-scraper`; absent such surface, the gate is structurally satisfied-by-absence.

**Substitution mechanism**: Gate_Forward (QA PM Sonnet dispatch reading raw JSONL + archive markdown + workflow yml + spec compliance) covers **artifact integrity** in lieu of interactive UI verification. Specifically, Forward gate verifies: (a) JSONL records are well-formed and complete, (b) statistical summary in archive matches raw data, (c) AC verdicts in archive correctly classify against measurement-protocol.v0.1.9.md §acceptance-criteria, (d) workflow yml execution order produces post-patch attribution as documented. These are read-grep-bash verifications — same toolchain Forward uses for code-logic-correctness. The "artifact" being verified IS the user-equivalent surface for non-interactive evidence.

**Validity boundary**: This deviation does **NOT** authorize folding Gate_Human into Gate_Forward when interactive UI **is** in scope. Future stages or charters that produce interactive surfaces (admin pages, web UI, CLI prompts requiring keystroke interaction) MUST run actual Gate_Human via `playwright-cli` / `chrome-devtools-batch-scraper` per three-gates.md normative scope. The deviation is scope-limited to **non-interactive evidence stages** — concretely defined as: dispatch-produced artifacts whose entire user surface is text files (markdown / JSONL / YAML / log) accessible via Read tool.

**Audit-trail discipline**: TeamLead logs Gate_Human verdict object **inline** in PROGRESS.md `## Stage History` (or per-stage gate log) as a distinct verdict object preserving per-gate granularity per three-gates.md §Sequencing under failure. Required form:
```json
{
  "gate": "Gate_Human",
  "verdict": "PASS",
  "root_cause": "n/a",
  "evidence": "N/A — non-interactive evidence; deviation-2 §methodology-deviations",
  "suggested_owner": "n/a",
  "dod_status": "met",
  "non_functional_findings": []
}
```
Folding into Forward's verdict (single combined classifier) is **NOT permitted** — distinct verdict object preserved.

**Authorization scope**: This deviation is authorized for v0.1.9 I-023-M1 **only**. Future measurement protocols inheriting or citing this clause MUST re-evaluate whether the non-interactive-evidence claim holds for their specific evidence surface (e.g., if a future charter measures an admin dashboard page render time, Gate_Human becomes load-bearing again and deviation-2 does NOT transfer).

**Evidentiary anchor**: `references/three-gates.md` §Gate_Human L136-141 normatively scopes the gate to interactive verification; this deviation declares structural absence rather than reinterpreting scope. Cross-reference: `agents/qa-pm.md` L57-68 for QA PM's tool ownership of `playwright-cli` / `chrome-devtools-batch-scraper`.

---

## §parallel-execution-note

T-1-b protocol design executes in parallel with T-1-a (workflow file authoring). If T-1-a triggers Q0 fallback before T-1-b completes, T-1-b output is preserved as v0.1.10 carryover (NOT wasted — protocol doc has independent v0.1.10 value). Sequential execution would save 30 kT under Q0 but adds 30 kT serial latency under non-Q0; parallel preferred since non-Q0 = expected path.
