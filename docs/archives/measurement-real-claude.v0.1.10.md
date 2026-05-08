# v0.1.10 real-claude end-to-end measurement (dual-host aggregate)

## §metadata

| Field | Value |
|---|---|
| Version | v0.1.10 |
| Charter | v0.1.10 Stage 2: real-claude end-to-end measurement (本機 + GHA dual) |
| Measurement protocol | docs/specs/measurement-protocol.v0.1.10.md (C-4 cold timeout=90s; W-3 warm timeout=60s) |
| Hosts measured | (i) local macOS host (hook whitelist applied) + (ii) GHA macos-14 reference host |
| AC closures evidenced | AC-7 (real-claude end-to-end measurement dual-host) |
| Authored by | PO V0.1.10-S2-EX2 (skeleton); RD V0.1.10-S2-EX1 (per-host evidence) |
| Measurement date | [POPULATED BY EXECUTING after RD T-2-1/T-2-2] |
| N per host per type | 10 (per inherited measurement-protocol.v0.1.9.md AC-1; revised from initial wave-refinement N=5 per Opus PlanAudit S2 critical decision) |

## §summary

| Host | claude_binary | Cold p50 (s) | Cold p95 (s) | Cold max (s) | Warm p50 (s) | Warm p95 (s) | Warm max (s) | Ship gate ≤30s |
|---|---|---|---|---|---|---|---|---|
| local macOS | [POPULATED] | [POPULATED] | [POPULATED] | [POPULATED] | [POPULATED] | [POPULATED] | [POPULATED] | [POPULATED] |
| GHA macos-14 | [POPULATED — `=real` if T-2-2 Plan A; `=stub` if Plan B fallback] | [POPULATED] | [POPULATED] | [POPULATED] | [POPULATED] | [POPULATED] | [POPULATED] | [POPULATED] |

**Cross-host verdict**: [POPULATED — PASS if both hosts ≤30s on all stats; PARTIAL if one host stub-confirmed; FAIL if any stat >30s]

## §evidence-pointer

- Local macOS host detail: `docs/archives/measurement-real-claude-local.v0.1.10.md` (RD T-2-1 artifact)
- GHA macos-14 host detail: `docs/archives/measurement-real-claude-gha.v0.1.10.md` (RD T-2-2 artifact)
- v0.1.10 measurement protocol: `docs/specs/measurement-protocol.v0.1.10.md`
- v0.1.9 baseline reference: `docs/archives/measurement.v0.1.9.md` (cold p50=15.5s; warm p50=5.3s)

## §session-resumed-verification

| Host | claude_version | session_resumed observed | sample_session_id_format | evidence_ref |
|---|---|---|---|---|
| local macOS | [POPULATED] | [POPULATED true/false] | [POPULATED real-UUID or stub-token] | per-host §raw-data |
| GHA macos-14 | [POPULATED] | [POPULATED] | [POPULATED] | per-host §raw-data |

## §interpretation

**Cross-host comparison**: [POPULATED EXECUTING — local-vs-GHA cold and warm delta; explanation of any divergence]

**Cold-headroom calculation**: cold p50 ÷ 30s ship gate = utilization%; 1 - utilization = headroom%. v0.1.9 baseline = 52%/48%. v0.1.10 dual-host: [POPULATED]. Cross-ref design.md §7 term (f) for budget-erosion threshold.

**Warm-headroom calculation**: warm p50 ÷ 30s ship gate = utilization%. [POPULATED]

**Q3-path statement**: [POPULATED — if any host triggers budget-erosion (>52% utilization) → RAID-I raised for v0.1.11; otherwise budget held]

**Charter constraint reconciliation**: charter Q3 says "real-claude 驗證限本機同一 host (跨機型留 v0.1.11)". This is reconciled with AC-7 dual-host (本機 + GHA) by reading "same-host" as "each measurement self-contained on a single host without cross-host transfer mid-measurement", not "only one host total". The two reference environments (本機 + GHA macos-14) are deliberately specific reference hosts, not multi-host generalization. Cross-host generalization (other macOS versions / Linux / x86_64 vs arm64) remains deferred to v0.1.11 per charter.

## §methodology-deviations-inheritance

| Source | Deviation | v0.1.10 status |
|---|---|---|
| measurement-protocol.v0.1.9.md deviation-1 (CCBL-Stage1-v0.1.9-M-2 stub-claude) | Stub-claude as equivalent for T5 SESSION_RESUMED signal-path validation on GHA | **Local host**: NO LONGER APPLIES (real claude used). **GHA host**: [POPULATED — APPLIES if T-2-2=B stub-fallback; SUPERSEDED if T-2-2=A real-claude] |
| measurement-protocol.v0.1.9.md deviation-2 (CCBL-Stage1-v0.1.9-M-4 Gate_Human N/A) | Gate_Human declared N/A for non-interactive evidence | INHERITED — applies to v0.1.10 measurement equivalently (still non-interactive) |
| (NEW v0.1.10) deviation-3 if registered | [POPULATED — if T-2-2=B stub-fallback registers a new deviation-3 in v0.1.10 protocol; otherwise omit row] | [POPULATED] |

---

**Note on file lifecycle**: This is the AGGREGATE summary. RD's per-host evidence files (`measurement-real-claude-local.v0.1.10.md` + `measurement-real-claude-gha.v0.1.10.md`) hold the raw data + per-run JSON references. This summary file populated by PO V0.1.10-S2-EX2 Phase B after RD V0.1.10-S2-EX1 completes.
