# Measurement Archive — v0.1.9 I-023-M1

**Charter**: v0.1.9 I-023-M1 — baton-write→SESSION_RESUMED latency measurement on reference host  
**GHA run**: 25375693016 (commit `ec23fa0`)  
**Measurement date**: 2026-05-05  
**Protocol**: `docs/specs/measurement-protocol.v0.1.9.md`  
**Authored by**: QA PM (V0.1.9-S1-D6)

---

## §host-environment

### macos-14 arm64 (primary)

```json
{
  "os": "macOS 14.8.5 (Sonoma)",
  "arch": "arm64",
  "launchctl_bootstrap_path": "/bin/launchctl",
  "hook_chain": [
    {"file": "hooks.json", "path": "/Users/runner/work/teamwork-leader/teamwork-leader/hooks/hooks.json"},
    {"file": "pre-compact.py", "path": "/Users/runner/work/teamwork-leader/teamwork-leader/hooks/pre-compact.py"},
    {"file": "session-start.py", "path": "/Users/runner/work/teamwork-leader/teamwork-leader/hooks/session-start.py"},
    {"file": "stop.py", "path": "/Users/runner/work/teamwork-leader/teamwork-leader/hooks/stop.py"}
  ],
  "plist_install_path": "/Users/runner/Library/LaunchAgents/com.teamwork-leader.auto-resume-daemon.plist",
  "runner_info": {
    "gha_runner_label": "macos-14",
    "gha_runner_arch": "ARM64"
  },
  "measurement_note": "claude CLI not installed on GHA; stub (tools/claude-stub.sh: sleeps 3s then exits 0) placed ahead of PATH to enable T5 SESSION_RESUMED transition without T6 retry exhaustion. Plist patched post-install via tools/patch-plist-python3.py to replace /usr/bin/env+python3 (system Python 3.9) with GHA python3 (3.10+) and inject stub dir into EnvironmentVariables.PATH."
}
```

macos-13 x86_64: not included — T-1-a macos-13 job not triggered (V19-I-7: macos-14 arm64 primary only; macos-13 x86_64 deferred).

---

## §raw-data

### cold-start

```jsonl
{"run_id": "cold-001", "type": "cold", "status": "OK", "latency_s": 15.875, "baton_write_ts": 1777983260.685, "session_resumed_ts": 1777983276.56, "timestamp_iso": "2026-05-05T12:14:36Z", "runner_info": {"os": "macOS 14", "arch": "arm64", "gha_runner_label": "macos-14", "gha_runner_arch": "ARM64"}}
{"run_id": "cold-002", "type": "cold", "status": "OK", "latency_s": 15.551, "baton_write_ts": 1777983281.863, "session_resumed_ts": 1777983297.415, "timestamp_iso": "2026-05-05T12:14:57Z", "runner_info": {"os": "macOS 14", "arch": "arm64", "gha_runner_label": "macos-14", "gha_runner_arch": "ARM64"}}
{"run_id": "cold-003", "type": "cold", "status": "OK", "latency_s": 15.616, "baton_write_ts": 1777983302.643, "session_resumed_ts": 1777983318.26, "timestamp_iso": "2026-05-05T12:15:18Z", "runner_info": {"os": "macOS 14", "arch": "arm64", "gha_runner_label": "macos-14", "gha_runner_arch": "ARM64"}}
{"run_id": "cold-004", "type": "cold", "status": "OK", "latency_s": 15.466, "baton_write_ts": 1777983323.39, "session_resumed_ts": 1777983338.856, "timestamp_iso": "2026-05-05T12:15:38Z", "runner_info": {"os": "macOS 14", "arch": "arm64", "gha_runner_label": "macos-14", "gha_runner_arch": "ARM64"}}
{"run_id": "cold-005", "type": "cold", "status": "OK", "latency_s": 15.454, "baton_write_ts": 1777983344.088, "session_resumed_ts": 1777983359.542, "timestamp_iso": "2026-05-05T12:15:59Z", "runner_info": {"os": "macOS 14", "arch": "arm64", "gha_runner_label": "macos-14", "gha_runner_arch": "ARM64"}}
{"run_id": "cold-006", "type": "cold", "status": "OK", "latency_s": 15.684, "baton_write_ts": 1777983364.671, "session_resumed_ts": 1777983380.356, "timestamp_iso": "2026-05-05T12:16:20Z", "runner_info": {"os": "macOS 14", "arch": "arm64", "gha_runner_label": "macos-14", "gha_runner_arch": "ARM64"}}
{"run_id": "cold-007", "type": "cold", "status": "OK", "latency_s": 15.523, "baton_write_ts": 1777983385.45, "session_resumed_ts": 1777983400.972, "timestamp_iso": "2026-05-05T12:16:40Z", "runner_info": {"os": "macOS 14", "arch": "arm64", "gha_runner_label": "macos-14", "gha_runner_arch": "ARM64"}}
{"run_id": "cold-008", "type": "cold", "status": "OK", "latency_s": 15.425, "baton_write_ts": 1777983406.102, "session_resumed_ts": 1777983421.527, "timestamp_iso": "2026-05-05T12:17:01Z", "runner_info": {"os": "macOS 14", "arch": "arm64", "gha_runner_label": "macos-14", "gha_runner_arch": "ARM64"}}
{"run_id": "cold-009", "type": "cold", "status": "OK", "latency_s": 15.357, "baton_write_ts": 1777983426.734, "session_resumed_ts": 1777983442.091, "timestamp_iso": "2026-05-05T12:17:22Z", "runner_info": {"os": "macOS 14", "arch": "arm64", "gha_runner_label": "macos-14", "gha_runner_arch": "ARM64"}}
{"run_id": "cold-010", "type": "cold", "status": "OK", "latency_s": 15.681, "baton_write_ts": 1777983447.288, "session_resumed_ts": 1777983462.969, "timestamp_iso": "2026-05-05T12:17:42Z", "runner_info": {"os": "macOS 14", "arch": "arm64", "gha_runner_label": "macos-14", "gha_runner_arch": "ARM64"}}
```

### warm-start

```jsonl
{"run_id": "warm-001", "type": "warm", "status": "OK", "latency_s": 5.834, "baton_write_ts": 1777983492.532, "session_resumed_ts": 1777983498.366, "timestamp_iso": "2026-05-05T12:18:18Z", "runner_info": {"os": "macOS 14", "arch": "arm64", "gha_runner_label": "macos-14", "gha_runner_arch": "ARM64"}}
{"run_id": "warm-002", "type": "warm", "status": "OK", "latency_s": 4.485, "baton_write_ts": 1777983505.75, "session_resumed_ts": 1777983510.235, "timestamp_iso": "2026-05-05T12:18:30Z", "runner_info": {"os": "macOS 14", "arch": "arm64", "gha_runner_label": "macos-14", "gha_runner_arch": "ARM64"}}
{"run_id": "warm-003", "type": "warm", "status": "OK", "latency_s": 5.715, "baton_write_ts": 1777983517.518, "session_resumed_ts": 1777983523.233, "timestamp_iso": "2026-05-05T12:18:43Z", "runner_info": {"os": "macOS 14", "arch": "arm64", "gha_runner_label": "macos-14", "gha_runner_arch": "ARM64"}}
{"run_id": "warm-004", "type": "warm", "status": "OK", "latency_s": 5.27, "baton_write_ts": 1777983530.48, "session_resumed_ts": 1777983535.75, "timestamp_iso": "2026-05-05T12:18:55Z", "runner_info": {"os": "macOS 14", "arch": "arm64", "gha_runner_label": "macos-14", "gha_runner_arch": "ARM64"}}
{"run_id": "warm-005", "type": "warm", "status": "OK", "latency_s": 4.999, "baton_write_ts": 1777983542.992, "session_resumed_ts": 1777983547.991, "timestamp_iso": "2026-05-05T12:19:07Z", "runner_info": {"os": "macOS 14", "arch": "arm64", "gha_runner_label": "macos-14", "gha_runner_arch": "ARM64"}}
{"run_id": "warm-006", "type": "warm", "status": "OK", "latency_s": 5.371, "baton_write_ts": 1777983555.249, "session_resumed_ts": 1777983560.62, "timestamp_iso": "2026-05-05T12:19:20Z", "runner_info": {"os": "macOS 14", "arch": "arm64", "gha_runner_label": "macos-14", "gha_runner_arch": "ARM64"}}
{"run_id": "warm-007", "type": "warm", "status": "OK", "latency_s": 4.608, "baton_write_ts": 1777983567.854, "session_resumed_ts": 1777983572.462, "timestamp_iso": "2026-05-05T12:19:32Z", "runner_info": {"os": "macOS 14", "arch": "arm64", "gha_runner_label": "macos-14", "gha_runner_arch": "ARM64"}}
{"run_id": "warm-008", "type": "warm", "status": "OK", "latency_s": 5.491, "baton_write_ts": 1777983579.753, "session_resumed_ts": 1777983585.244, "timestamp_iso": "2026-05-05T12:19:45Z", "runner_info": {"os": "macOS 14", "arch": "arm64", "gha_runner_label": "macos-14", "gha_runner_arch": "ARM64"}}
{"run_id": "warm-009", "type": "warm", "status": "OK", "latency_s": 5.1, "baton_write_ts": 1777983592.526, "session_resumed_ts": 1777983597.626, "timestamp_iso": "2026-05-05T12:19:57Z", "runner_info": {"os": "macOS 14", "arch": "arm64", "gha_runner_label": "macos-14", "gha_runner_arch": "ARM64"}}
{"run_id": "warm-010", "type": "warm", "status": "OK", "latency_s": 5.452, "baton_write_ts": 1777983604.888, "session_resumed_ts": 1777983610.339, "timestamp_iso": "2026-05-05T12:20:10Z", "runner_info": {"os": "macOS 14", "arch": "arm64", "gha_runner_label": "macos-14", "gha_runner_arch": "ARM64"}}
```

---

## §statistics

| Type | N | p50 (s) | p95 (s) | max (s) | AC-2 verdict |
|---|---|---|---|---|---|
| cold | 10 | 15.523 | 15.875 | 15.875 | PASS |
| warm | 10 | 5.270 | 5.834 | 5.834 | PASS |

**Footnote**: p95 = max at N=10 by sample definition (see §statistics-computation PO-2 degeneracy clause). AC-2 at N=10 reduces to two independent gates: p50 ≤ 30s AND max ≤ 30s.

Cold sorted values: [15.357, 15.425, 15.454, 15.466, 15.523, 15.551, 15.616, 15.681, 15.684, 15.875]  
Warm sorted values: [4.485, 4.608, 4.999, 5.100, 5.270, 5.371, 5.452, 5.491, 5.715, 5.834]

---

## §interpretation

### AC-1 — Sample size ≥ 10 per type

- cold: N=10, all status=OK — **PASS**
- warm: N=10, all status=OK — **PASS**

### AC-2 — p50/p95/max ≤ 30s per type

- cold: p50=15.523s ≤ 30s, max=15.875s ≤ 30s — **PASS**
- warm: p50=5.270s ≤ 30s, max=5.834s ≤ 30s — **PASS**

### AC-3 — Both cold AND warm pass AC-2

AC-2(cold)=PASS AND AC-2(warm)=PASS — **PASS**

### AC-4 — Host environment recorded

All required fields present in host_env.json: `os`, `arch`, `launchctl_bootstrap_path`, `hook_chain`, `plist_install_path`, `runner_info.gha_runner_label`, `runner_info.gha_runner_arch` — **PASS**

### AC-5 — Evidence archived

This document at `docs/archives/measurement.v0.1.9.md` — **PASS**

### Overall verdict

**ALL ACCEPTANCE CRITERIA MET — PASS**

### Measurement methodology notes

**Stub-based measurement**: The real `claude` CLI is not installable on GHA runners. `tools/claude-stub.sh` (sleeps 3s, exits 0) is placed ahead of `$PATH` in the daemon's `EnvironmentVariables.PATH` (injected via `tools/patch-plist-python3.py`). This causes the daemon's T5 actor `proc.wait(timeout=2.0)` to raise `TimeoutExpired`, which the T5 actor correctly treats as a successful spawn (non-zero exit within timeout also treated as spawn success per daemon.py design). The stub validates the full baton-write→SESSION_RESUMED signal path without requiring a real Claude session.

**Python 3.9 compatibility**: GHA macOS-14 system python3 is Python 3.9, which does not support `list[str] | None` union syntax (PEP 604, requires 3.10+). `tools/patch-plist-python3.py` replaces `/usr/bin/env+python3` in the plist `ProgramArguments` with the absolute GHA python3 binary path (Python 3.10+) and reloads the daemon via `launchctl bootout` + `launchctl bootstrap` after each cold iteration. daemon.err shows expected TypeError tracebacks from initial cold-install daemon instances (using system python3 before the first plist patch), but all 10 cold measurement iterations used the patched python3 daemon instance.

**Cold vs warm latency interpretation**: Cold p50=15.5s reflects the 5-second poll interval in daemon T4/T5 watchdog loop plus ~3s stub sleep plus timeout handling (~2s). Warm p50=5.3s reflects the daemon's FSEvent-backed WatchPaths trigger firing immediately on baton mtime change, bypassing the polling cycle. The ~10s gap between cold and warm confirms the daemon's two-path architecture is functioning as designed: poll-based T4 for cold-start watchdog, FSEvent-based WatchPaths trigger for warm-path responsiveness.

**Q3 path**: Not triggered. All AC-2 values well within 30s threshold (cold max=15.875s, warm max=5.834s).

### GHA artifact provenance

- Run ID: 25375693016
- Branch: feat/v0.1.9-measurement
- Commit: ec23fa0
- Workflow: `.github/workflows/measure-execution.yml`
- Artifact: `measurement-raw-macos-14`
