# Measurement Archive — v0.1.10 I-023-M1 (Real-Claude GHA macos-14)

**Protocol**: docs/specs/measurement-protocol.v0.1.10.md
**Host**: GHA macos-14 (arm64) — reference host per I-023-M1 charter
**Measurement date**: [PENDING — awaiting TeamLead commit + workflow trigger]
**claude_binary**: real (path: /opt/homebrew/bin/claude — confirmed by pre-validation)
**N**: 10 cold + 10 warm (per Opus PlanAudit S2 N5→N10 revision)

## §metadata

| Field | Value |
|---|---|
| version | v0.1.10 |
| dispatch | V0.1.10-S2-EX1 (T-2-2 Candidate A) |
| gate_decision | Candidate A (real-claude) — pre-validation PASS |
| pre_validation_run | GHA run 25521618249 (measure-execution-prevalidation.yml) |
| pre_validation_verdict | PASS — all 5 steps succeeded in 26s |
| claude_binary | real |
| claude_version | 2.1.132 (Claude Code) — from pre-validation run |
| workflow_file | .github/workflows/measure-execution.yml (modified for T-2-2 Candidate A) |
| AC_closures_evidenced | AC-7(ii) — GHA arm real-claude (PENDING full run) |

## §pre-validation-evidence

Pre-validation workflow run 25521618249 on feat/v0.1.10-daemon-spec-changes (push trigger):

| Step | Result | Notes |
|---|---|---|
| Checkout repository | PASS | commit bedff96 |
| Set up Python 3.10 | PASS | python-3.10.11 installed |
| Attempt npm install of claude CLI | PASS | added 2 packages in ~2s |
| Check claude binary availability | PASS | /opt/homebrew/bin/claude, version 2.1.132 |
| Smoke test claude help (non-interactive) | PASS | exit 0 |

**Bail criteria check**: exit !=0 → No. Authentication prompts → None observed. Install >4min → No (~2s). **Gate: PROCEED TO CANDIDATE A.**

## §methodology-deviations-inheritance

| Source | Deviation | v0.1.10 GHA status |
|---|---|---|
| measurement-protocol.v0.1.9.md deviation-1 (stub-claude) | Stub-claude for T5 SESSION_RESUMED on GHA | **SUPERSEDED** — T-2-2 Candidate A uses real claude (npm install -g @anthropic-ai/claude-code) |
| measurement-protocol.v0.1.9.md deviation-2 (Gate_Human N/A) | Gate_Human N/A for non-interactive evidence | INHERITED |

**No deviation-3 registration required** — Candidate A real-claude path executed; stub fallback not triggered.

## §raw-data

### cold-start (N=10)

[PENDING — awaiting TeamLead commit of measure-execution.yml Candidate A changes + GHA workflow run]

### warm-start (N=10)

[PENDING — awaiting GHA workflow run]

## §statistics

| Type | N | p50 (s) | p95 (s) | max (s) | AC-2 verdict |
|---|---|---|---|---|---|
| cold | 10 | [PENDING] | [PENDING] | [PENDING] | [PENDING] |
| warm | 10 | [PENDING] | [PENDING] | [PENDING] | [PENDING] |

Note: p95 = max at N=10 by sample definition (§statistics-computation PO-2 degeneracy clause).

## §ship-gate-verdict

[PENDING — awaiting full measurement run]

Overall AC-7(ii): [PENDING]
