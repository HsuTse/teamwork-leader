# tasks.md — v0.1.10 Stage 1 + Stage 2

Dispatch: V0.1.10-S1-EX1 (Stage 1) / V0.1.10-S2-D1 (Stage 2 PLANNING) / V0.1.10-S2-EX1 (Stage 2 EXECUTING)
Updated: 2026-05-08

## Stage 1 tasks

| ID | Description | Status | Owner | verify_result |
|---|---|---|---|---|
| T-1-A1 | I-061 cosmetic: expand T6_BACKOFF_SECONDS[0] comment in daemon.py lines 38-41 to document intentional index-symmetry placeholder | [x] | RD | PASS: py_compile OK; comment shows "intentional index-symmetry placeholder" |
| T-1-A2 | I-064: rewrite _enter_aborted failure_message to single-line key=value; delete deferral comment lines 217-220 | [x] | RD | PASS: py_compile OK; t7-abort self-test exits 0; failure file shows single line with transition=T7 |
| T-1-A3 | I-065: add argparse mutually_exclusive_group for 5 self-test flags; remove I-065 deferral comment | [x] | RD | PASS: --self-test-t5 --self-test-pid rejected with "not allowed with argument"; solo --self-test-pid exits 0 |
| T-1-A4 | I-071: add §4.X subsection in design.md after 7-row §4 table; update intro sentence | [x] | RD | PASS: AC-4- count=17; §4.X heading present; AC-4-H/I/J all present |
| T-1-A5 | Hook hardening D-1+D-2+D-3 (out-of-tree); evidence file docs/security/v0.1.10-hook-hardening.md | [x] | RD | PASS: all 7 smoke tests pass; hook compiles; evidence file 151 lines |

## Stage 2 tasks (PLANNING — V0.1.10-S2-D1)

Owner: RD PM (T-2-1, T-2-2, T-2-5) | PO PM (T-2-3, T-2-4) | Opus (T-2-6)

| ID | Description | Status | Owner | blockedBy | verify_clause |
|---|---|---|---|---|---|
| T-2-1 | Local 本機 real-claude measurement: 10 cold + 10 warm runs; evidence at docs/archives/measurement-real-claude-local.v0.1.10.md | [BLOCKED] | RD | RAID-I-S2-launchctl-hook | BLOCKED: launchctl reload of patched plist denied by pretooluse_guard.py hook after D-3 escalation. Daemon requires Python 3.10+ but system python3=3.9; patch-plist-python3.py patches the file but reload is hook-denied. CEO must add Bash permission for launchctl on com.teamwork-leader.auto-resume-daemon.plist or allow the plist template to carry absolute python3 path. |
| T-2-2 | GHA real-claude measurement (or risk-surfaced fallback): assess real-claude availability on macos-14; modify/annotate measure-execution.yml; evidence at docs/archives/measurement-real-claude-gha.v0.1.10.md | [BLOCKED] | RD | T-2-5 DONE; pre-val workflow not triggered | BLOCKED: pre-validation workflow (measure-execution-prevalidation.yml) created and pushed, but GHA does not register new workflows on non-default branches for workflow_dispatch; push trigger did not fire. CEO must trigger manually via `gh workflow run` or merge workflow stub to main first. |
| T-2-5 | Add python3 >= 3.10 hard assert step to .github/workflows/measure-execution.yml near top of steps section | [x] | RD | none | PASS: grep 'AC-9 hard gate' shows line 58; grep 'sys.version_info >= (3, 10)' shows line 60; YAML_VALID; local python3 AC-9 command exits 0 |
| T-2-3 | Compose dual-host measurement summary at docs/archives/measurement-real-claude.v0.1.10.md (AC-7) | [ ] | PO | T-2-1, T-2-2 | file exists; contains §host-comparison table; session_resumed = true for all passing runs on each host |
| T-2-4 | Append cold p50 52% headroom note to docs/specs/auto-resume-daemon-design.md §reliability budget (AC-8) | [ ] | PO | T-2-1 | `grep -n "52%" docs/specs/auto-resume-daemon-design.md` returns result |
| T-2-6 | Final Opus independent review + Gate_Requirement runner | [ ] | Opus | T-2-1..T-2-5 complete | Opus returns APPROVED or APPROVED_WITH_REVISIONS + Gate_Requirement PASS |

### T-2-1 mechanism (local 本機 real-claude measurement)

**Phase 0 — Pre-run checklist (read-only)**
1. Confirm `which claude` resolves to real claude binary on this host (not stub). Expected: path under fnm/state dir or system install.
2. Confirm plist absent: `ls ~/Library/LaunchAgents/com.teamwork-leader.auto-resume-daemon.plist 2>/dev/null || echo absent`
3. Confirm `python3 --version` >= 3.10.

**Phase 1 — baton.json setup for measurement**
4. Set BATON_PATH and PLUGIN_ROOT env vars.
5. Set CLAUDE_PROJECT_DIR to a temp workspace: `export CLAUDE_PROJECT_DIR=/tmp/twl-measure-local`
6. `mkdir -p "$CLAUDE_PROJECT_DIR/.teamlead"`
7. Capture T0 (run separately from bootstrap):
   `BATON_WRITE_TS=$(python3 /Users/HsuTse/ClaudeProject/teamwork-leader/tools/measure-write-baton.py "$CLAUDE_PROJECT_DIR/.teamlead/baton.json")`

**Phase 2 — Cold-start loop (N=5; D-3 guard requires single-clause bash per invocation)**

For each cold run i in {1..5}:
- Step C-1 (separate invocation): `python3 /Users/HsuTse/ClaudeProject/teamwork-leader/scripts/install.py --uninstall 2>/dev/null || true`
- Step C-1b (separate invocation): `sleep 3`
- Step C-2: write baton (separate invocation — see Phase 1 step 7)
- Step C-3 (separate invocation): `python3 /Users/HsuTse/ClaudeProject/teamwork-leader/scripts/install.py`
- Step C-3b (separate invocation — bootstrap; ask-prompt will appear; CEO approves):
  `launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.teamwork-leader.auto-resume-daemon.plist"`
- Step C-4 (separate invocation — poll 90s):
  `python3 /Users/HsuTse/ClaudeProject/teamwork-leader/tools/measure-poll-resumed.py "$CLAUDE_PROJECT_DIR/.teamlead/baton.json" "$BATON_WRITE_TS" "local-cold-$(printf '%03d' $i)" "cold" 90`
- Step C-5: append RESULT_JSON to cold_runs.jsonl
- Step C-6 (separate invocation): `python3 /Users/HsuTse/ClaudeProject/teamwork-leader/scripts/install.py --uninstall 2>/dev/null || true`
- Step C-6b (separate invocation): `sleep 5`

**Phase 3 — Warm-start baseline + loop (N=5)**

- Install baseline (separate invocation): `python3 /Users/HsuTse/ClaudeProject/teamwork-leader/scripts/install.py`
- Bootstrap (separate invocation — ask-prompt): `launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.teamwork-leader.auto-resume-daemon.plist"`
- `sleep 10` (stabilization)
For each warm run j in {1..5}:
- Step W-1: confirm daemon listed: `launchctl list | grep com.teamwork-leader.auto-resume-daemon`
- Step W-2: write baton (BATON_WRITE_TS captured)
- Step W-3 (poll 60s, separate invocation):
  `python3 /Users/HsuTse/ClaudeProject/teamwork-leader/tools/measure-poll-resumed.py "$CLAUDE_PROJECT_DIR/.teamlead/baton.json" "$BATON_WRITE_TS" "local-warm-$(printf '%03d' $j)" "warm" 60`
- Step W-4: append RESULT_JSON to warm_runs.jsonl
- Step W-5: `sleep 5`

**Phase 4 — Statistics + evidence archive**
- Run: `python3 /Users/HsuTse/ClaudeProject/teamwork-leader/tools/measure-compute-stats.py "$CLAUDE_PROJECT_DIR/.teamlead/cold_runs.jsonl"`
- Run: `python3 /Users/HsuTse/ClaudeProject/teamwork-leader/tools/measure-compute-stats.py "$CLAUDE_PROJECT_DIR/.teamlead/warm_runs.jsonl"`
- Write evidence markdown to: `docs/archives/measurement-real-claude-local.v0.1.10.md`
  - Sections: §metadata, §host-environment, §raw-data (cold JSONL + warm JSONL), §statistics (table), §ship-gate-verdict (p50/p95/max ≤ 30s for both)

**Risk notes**:
- D-3 guard denies `launchctl ... && ...` or `launchctl ... ; ...` compound forms — every launchctl call must be a standalone single-clause Bash invocation.
- Ask-prompt for `launchctl bootstrap` will appear; CEO must approve at execution time.
- If install.py returns `manual-pending`, cold-start run fails and is logged as FAIL (not retried in this protocol; counted against N=5 success requirement).

### T-2-2 plan_candidates

Two approaches depending on GHA real-claude availability (assessed at EXECUTING entry):

**Candidate A — Full real-claude on GHA (if claude binary installable on macos-14)**
- Install real claude CLI via `npm install -g @anthropic-ai/claude-code` or Homebrew at workflow setup
- Remove or skip `Install stub claude binary` step (or make it conditional)
- Remove `patch-plist-python3.py` stub-dir injection (PATH no longer needs stub dir)
- Add `CLAUDE_SKIP_HOOK_CHECK=1` or equivalent env to avoid interactive prompts during GHA non-interactive measurement
- All cold/warm loops use real claude — SESSION_RESUMED signal is real end-to-end
- Evidence: `docs/archives/measurement-real-claude-gha.v0.1.10.md` with `claude_binary=real` annotation

**Candidate B — Stub-confirmed GHA (if real claude unavailable on macos-14 runner)**
- Real claude binary not installable on GHA macos-14 runner (npm global install may be blocked; brew may not have claude-code formula)
- Keep stub-based workflow unchanged; annotate evidence with `claude_binary=stub`
- Register RAID-I-Stage2 (sev:high): "AC-7 real-claude GHA evidence partial — stub used on GHA; real-claude evidence from 本機 only per T-2-1"
- Register methodology-deviation in docs/specs/measurement-protocol.v0.1.10.md §methodology-deviations: deviation entry for stub fallback on GHA
- GHA evidence file annotates: "stub-claude used; real-claude evidence = T-2-1 local measurement only"
- AC-7 partially met: (i) 本機 = real-claude PASS; (ii) GHA = stub-confirmed (per v0.1.9 methodology, not new real-claude evidence)

**Risk assessment**: Candidate A risk = `env` (npm/brew availability on GHA macos-14 runner is uncertain; interactive auth prompts may break non-interactive GHA shell). Candidate B risk = `spec` (AC-7 partial fulfillment requires CCB-Light for methodology-deviation registration). Recommended: attempt Candidate A first at EXECUTING; fall back to Candidate B if claude binary cannot be installed without interactive auth.

### T-2-5 mechanism (python3 >= 3.10 hard assert in measure-execution.yml)

Surgical addition: insert new step after `Set up Python 3.11` (line ~57) and before `Create .teamlead workspace directory` (line ~60):

```yaml
      - name: Assert python3 >= 3.10
        run: python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"
```

This step fails the job if python3 < 3.10. Placement: immediately after `setup-python@v5` to catch env-class failures before any other python3 usage.

Net diff: ~4 lines (name + run + blank lines for YAML formatting).

**Evidence schema (T-2-1 `docs/archives/measurement-real-claude-local.v0.1.10.md`)**:

```markdown
# Measurement Archive — v0.1.10 I-023-M1 (Real-Claude Local)
**Protocol**: docs/specs/measurement-protocol.v0.1.10.md
**Host**: macOS [version] ([arch]) — same host as hook whitelist
**Date**: [ISO]
**claude_binary**: real (path: [which claude output])

## §host-environment
[JSON]

## §raw-data
### cold-start (N=5)
[5 JSONL lines]
### warm-start (N=5)
[5 JSONL lines]

## §statistics
| Type | N | p50 (s) | p95 (s) | max (s) | AC-2 verdict |
|---|---|---|---|---|---|
| cold | 5 | … | … | … | PASS/FAIL |
| warm | 5 | … | … | … | PASS/FAIL |

Note: p95 = max at N=5 (degeneracy clause from §statistics-computation PO-2).

## §ship-gate-verdict
cold p50/p95/max ≤ 30s: [PASS/FAIL]; warm p50/p95/max ≤ 30s: [PASS/FAIL]
Overall: [PASS/FAIL]
```
