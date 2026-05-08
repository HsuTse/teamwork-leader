# Measurement Protocol — v0.1.10 I-023-M1 (Real-Claude End-to-End)

**Status**: normative (RAID-I-2 closure + v0.1.10 Stage 2 execution reference)

---

## §metadata

| Field | Value |
|---|---|
| version | v0.1.10 |
| supersedes | v0.1.9 (see `docs/specs/measurement-protocol.v0.1.9.md`) |
| charter_ref | v0.1.10 Stage 2 — Real-Claude End-to-End Measurement (`feat/v0.1.10-daemon-spec-changes`) |
| date | 2026-05-08 |
| authored_by | PO PM dispatch V0.1.10-S1-EX2 (T-1-B2) |
| frozen_design_ref | `docs/specs/auto-resume-daemon-design.md §7` |
| change_summary | C-4 cold-start poll timeout corrected 60s→90s to match workflow (`measure-execution.yml` line 255); v0.1.9 §C-4 spec text preserved unchanged as evidence-truth (actual v0.1.9 measurement runs used 90s; spec text 60s was a copy-paste error captured at RAID-I-2) |

---

## §reference

This protocol supersedes `docs/specs/measurement-protocol.v0.1.9.md` for v0.1.10 Stage 2 measurement runs.

**v0.1.9 protocol evidence-truth preservation**: The v0.1.9 protocol at `docs/specs/measurement-protocol.v0.1.9.md` §C-4 (line ~99) reads:

```
# Step C-4: Wait for SESSION_RESUMED event (poll up to 60 s)
python3 tools/measure-latency.sh --wait-session-resumed --timeout 60 --out /tmp/run-${i}.json
```

This spec text (`--timeout 60`) was a copy-paste error. The actual v0.1.9 measurement runs on GHA (`measure-execution.yml` line 255) used `--timeout 90`. The v0.1.9 protocol file is **NOT retroactively edited** — its text is preserved as evidence-truth documenting the error as it existed during the v0.1.9 measurement execution. Retroactive editing would misrepresent the executed evidence record.

**Workflow-as-truth authority**: `measure-execution.yml` is the governing authority for actual execution parameters. Where spec text and workflow differ, workflow takes precedence for measurement execution. This protocol corrects the spec text to match workflow reality.

---

## §C-4 (cold-start poll — CORRECTED from v0.1.9)

<!-- ccb: clarify 2026-05-08 — RAID-I-2 closure: C-4 timeout corrected 60s→90s to match workflow line 255 (ThrottleInterval 10s + cold-start launchd overhead) -->

Cold-start step C-4 replaces the v0.1.9 §C-4 text:

```bash
# Step C-4: Wait for SESSION_RESUMED event (poll up to 90 s)
# Rationale: ThrottleInterval=10s + poll cycle 5s + T5 processing (~3s stub) = expect ~18s max;
#            cold-start needs launchd spin-up overhead budget; 90s confirmed as workflow-as-truth
#            (measure-execution.yml line 252-255).
python3 tools/measure-poll-resumed.py "$BATON_PATH" "$BATON_WRITE_TS" "$RUN_ID" "cold" 90
```

**CORRECTED timeout**: `90` (was: `60` in v0.1.9 spec text; workflow always used `90`).

---

## §W-3 (warm-start poll — UNCHANGED from v0.1.9)

Warm-start step W-3 is unchanged from v0.1.9:

```bash
# Step W-3: Wait for SESSION_RESUMED event (poll up to 60 s)
# Rationale: warm-start has no launchd cold-path overhead; 60s budget is sufficient.
#            Confirmed as workflow-as-truth (measure-execution.yml line 393-396).
python3 tools/measure-poll-resumed.py "$BATON_PATH" "$BATON_WRITE_TS" "$RUN_ID" "warm" 60
```

**Timeout**: `60` (unchanged; matches workflow line 396).

---

## §rationale

### Why C-4 = 90s and W-3 = 60s

**Workflow-as-truth** (`measure-execution.yml`):

- Line 251-255 (cold C-4): comment reads "ThrottleInterval=10s + poll cycle 5s + T5 processing (~3s stub) = expect ~18s max; cold needs launchd spin-up overhead" → timeout 90.
- Line 393-396 (warm W-3): timeout 60 (no cold-path overhead; daemon already running).

**Engineering rationale for split**:

Cold-start must accommodate launchd process spawn latency on top of the steady-state signal path:
- ThrottleInterval (launchd plist key): 10s minimum between daemon respawns
- Poll cycle in `measure-poll-resumed.py`: 5s sleep between checks
- T5 `subprocess.Popen` + stub sleep: ~3s processing time
- launchd cold-start kernel dispatch overhead: variable, budget ~17s additional margin
- Total cold-path budget: ~18s expected + ~72s margin → 90s ceiling

Warm-start has no launchd cold-path overhead (daemon already running and polling baton):
- Expected latency: poll cycle (5s) + T5 processing (~3s) = ~8s typical
- 60s provides ~52s margin over expected warm-start latency

**v0.1.9 measured results** (from `docs/archives/measurement.v0.1.9.md`):
- Cold p50=15.5s, warm p50=5.3s — both well within 30s threshold
- Cold headroom at 90s timeout: ~74.5s available margin over p50
- Warm headroom at 60s timeout: ~54.7s available margin over p50

---

## §acceptance-criteria-inheritance

All acceptance criteria from `docs/specs/measurement-protocol.v0.1.9.md §acceptance-criteria` (AC-1 through AC-5) are inherited unchanged for v0.1.10, except:

- AC-5 archive target: `docs/archives/measurement-real-claude.v0.1.10.md` (per charter AC-7)
- §C-4 timeout parameter: 90s (this document; supersedes v0.1.9 §C-4 text)

---

## §methodology-deviations-inheritance

`docs/specs/measurement-protocol.v0.1.9.md §methodology-deviations` deviation-1 (stub-based claude binary) and deviation-2 (Gate_Human N/A for non-interactive evidence) are inherited with the following re-evaluation:

- **deviation-1 (stub)**: v0.1.10 Stage 2 targets real-claude end-to-end measurement (charter AC-7). Stub-based measurement MAY be used as fallback if real-claude is unavailable on the reference host, but the primary path MUST use actual `claude` CLI. If stub is used in v0.1.10, a new deviation entry MUST be registered in this protocol's §methodology-deviations section before measurement proceeds.
- **deviation-2 (Gate_Human N/A)**: inherited unchanged — v0.1.10 Stage 2 evidence surface remains non-interactive (JSONL + markdown archive).

## §methodology-deviations (v0.1.10 net-new)

### deviation-3: T-2-1 local real-claude measurement BLOCKED (env-class) — AC-7(i) PROVEN-UNAVAILABLE on this host class

**Date registered**: 2026-05-08 (CCBL-Stage2-v0.1.10-T21-LOCAL-BLOCKED)

**Scope**: AC-7(i) `本機 macOS host (Hook 白名單路徑)` real-claude end-to-end measurement.

**Empirical block proof**:
- Local host: macOS 15.3 with system `/usr/bin/python3` = 3.9.6
- Daemon plist template uses `/usr/bin/env python3` shebang → resolves to system 3.9.6 at launchd spawn time
- `scripts/daemon.py` uses PEP 604 syntax (`list[str] | None`) requiring Python 3.10+
- Daemon process crashes at module import; SESSION_RESUMED signal never fires
- `tools/patch-plist-python3.py` exists (v0.1.9 fix; patches installed plist to use pyenv-resolved 3.13.12) but requires `launchctl bootout` + `launchctl bootstrap` reload to apply
- After two approved hook ask-prompts for launchctl reload, the pretooluse_guard.py D-3 compound-operator guard (or repeated-attempts heuristic) hard-denied subsequent launchctl invocations during the same dispatch window
- `install.py --uninstall` + `install.py` cycle re-renders the plist from template, losing the patch — install lifecycle does not preserve the python3 path correction
- Net effect: T-2-1 local measurement cannot complete in the v0.1.10 charter window without either (A) explicit Bash permission rule for launchctl on the daemon plist, (B) plist template PYTHON3_PATH substitution + install.py env injection, or (C) charter close with PARTIAL AC-7 acceptance

**Validity boundary**: This deviation declares AC-7(i) UNAVAILABLE on this specific host class (macOS 15.3 with system python3 < 3.10) within v0.1.10 charter time-budget. AC-7 evidence for v0.1.10 is provided by AC-7(ii) GHA macos-14 reference host real-claude measurement only. Cross-host real-claude validation generalization remains deferred to v0.1.11 per charter Q3 constraint (跨機型留 v0.1.11) extended to include install-lifecycle hardening.

**Inheritance to future charters**: v0.1.11 carries forward — install-lifecycle hardening (Option B template fix or Option A permission rule), and once shipped, AC-7(i) local measurement re-validates against this deviation. If v0.1.11 install-lifecycle work resolves the env-class block, deviation-3 is superseded; if not, deviation-3 status escalates to permanent host-class restriction documented at v0.1.7+ design baseline.

**Ship gate impact**: AC-7 overall PARTIAL for v0.1.10. Stage 2 close acceptable per Opus PlanAudit S2 `partial_acceptable_for_Stage2_close` rule (empirical proof exists; not silent skip). Gate_Requirement at Stage 2 close evaluates AC-7 as PARTIAL-MET with explicit deviation-3 evidence.
