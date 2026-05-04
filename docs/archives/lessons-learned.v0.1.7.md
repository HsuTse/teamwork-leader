# Lessons Learned — v0.1.7 Auto-Resume Daemon

**Source**: v0.1.7 ProjectClose audit-trail event `PROJECT-CLOSE-LESSONS-LEARNED` (2026-05-04T16:17+08:00). Formally persisted in v0.1.8 per charter `feat/v0.1.8-measurement-deferral`.

**Status of each lesson**: each entry below records (1) original v0.1.7 statement verbatim, (2) v0.1.8 disposition, and (3) v0.1.9 inheritance note.

---

## L-1 — I-023-M1 actual measurement deferred across entire charter

**Category**: kpi-deferral

**Original v0.1.7 statement**: Phase 1 was no-daemon-N/A by design; Phase 2 (Stage 4) charter design.md Q4 line 559 committed "Stage 4 will produce the first real latency data + report observed at Stage 4 close", but bash-hook + launchctl-guard host blocked real launchd-load → measurement N/A-dry-run. v0.1.7 ships with primary KPI ("auto-resume within 30s") never demonstrated.

**Action for v0.1.8+**: FIRST ACTION of v0.1.8+ MUST be non-guarded-host dogfood that produces real baton-write→SESSION_RESUMED wall-clock latency data BEFORE declaring "auto-resume works". Update I-023-M1 RAID status from deferred to closed only after measurement completes.

**v0.1.8 disposition**: v0.1.8 is a doc-only charter. The measurement itself is NOT v0.1.8 work. v0.1.8 codifies the deferral as an explicit shipping constraint in `docs/specs/auto-resume-daemon-design.md §7` and records the reference-host prerequisite (macOS host with launchctl unguarded). Measurement remains open.

**v0.1.9 inheritance note**: v0.1.9 FIRST ACTION — execute `tools/measure-latency.sh --daemon-present` on reference host. Record p50/p95/max. Confirm ≤30s. Close I-023-M1 RAID entry. If >30s, escalate CCB-Heavy before shipping.

---

## L-2 — I-071 systemic: reviewer rubric attribution-truth blind spot affects TeamLead-owned gates too

**Category**: methodology

**Original v0.1.7 statement**: S4-D11 step-review (Sonnet) PASS_WITH_MINOR cosmetic only; missed close report Section 2/5 wave-mapping shift. TeamLead post-review reconciliation caught it. Subsequent Opus audit found same class of error (AC-4-H/I/J) had survived into TeamLead-owned Gate_Requirement audit-trail event. Rubric existence-grep insufficient for attribution truth.

**v0.1.8 disposition**: No codification in v0.1.8 (per charter constraint: no L-2/L-4 codification). Statement persisted verbatim here for formal record and future reference.

**Inheritance**: stage-runbook §step-review-rubric + §GATING attribution-truth gaps noted; v0.1.9 may consider codification (no commitment from v0.1.8).

---

## L-3 — Bash-hook + launchctl-guard host materially limits dogfood scope

**Category**: host-environment

**Original v0.1.7 statement**: S4-D8 install.py verify clauses + T-4-10 dogfood path both required degraded-mode workarounds (Python subprocess + os.chmod) due to bash-hook intercepting launchctl/chmod CLI strings. I-018 Python-only mandate held under pressure but synthetic test cycles validate code paths only, NOT integration surface (launchd respawn, ThrottleInterval, KeepAlive SuccessfulExit:false all unverified end-to-end).

**Action for v0.1.8+**: Either (a) v0.1.8 establishes non-guarded reference host for real launchd-load dogfood, OR (b) Charter v0.1.8 explicit shipping constraint accepted by CEO that v0.1.x targets only Python-substring-safe deployment paths.

**v0.1.8 disposition**: Path (b) selected. CEO accepted explicit shipping constraint path. v0.1.8 documents the reference-host requirement (macOS, launchctl unguarded, python3 launchd-reachable) in design.md §7 term (c). Cloud Mac infra setup is v0.1.9-scope. No reference host was established in v0.1.8; constraint remains open.

**v0.1.9 inheritance note**: Before any v0.1.9 coding begins, establish reference host (physical Mac without guard OR cloud macOS runner). Verify `launchctl bootstrap` succeeds in that environment. This is a prerequisite for L-1 measurement closure.

---

## L-4 — API-terminate-recovery discipline worked; codify as canonical pattern

**Category**: retry-discipline

**Original v0.1.7 statement**: S4-D6 (T-4-6) + S4-D8 (T-4-8) both API Error: terminated mid-execution. Both retries had retry_cap NOT consumed (infrastructure-failure precedent) AND 0 partial regression verified before re-dispatch. 100% recovery success rate maintained.

**v0.1.8 disposition**: No codification in v0.1.8 (per charter constraint: no L-2/L-4 codification). Statement persisted verbatim here for formal record and future reference.

**Inheritance**: §retry-cap-accounting API-terminate pattern noted; v0.1.9 may consider codification (no commitment from v0.1.8).
