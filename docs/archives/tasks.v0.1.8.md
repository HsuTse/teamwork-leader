# Tasks — teamwork-leader v0.1.8

<!--
Owner: RD PM (writes), TeamLead (orchestrates dispatch).
Stage 1 plan decomposed by S1-PLAN-RD; Opus PLAN_AUDIT (a6d67c4a35a089055) verdict APPROVED_WITH_REVISIONS — 8 revisions applied inline.
v0.1.7 archived to docs/archives/tasks.v0.1.7.md.
-->

## Stage 1 — Measurement-Deferral Codification

**Total: 98 kT (vs 120 kT budget; 22 kT headroom = 18%)**

---

### T-1-1 PO — design.md amendment append

| Field | Value |
|---|---|
| Owner | PO PM |
| expected_cost_kT | 20 (actual 12 kT — under) |
| blockedBy | none |
| expected_scope_files | docs/specs/auto-resume-daemon-design.md |
| status | [x] complete (S1-D1, 2026-05-05T02:38; PASS step-review + Rule 2 sampling) |

**Description**: Append new top-level section `## §7 — Measurement Deferral & Shipping Constraint (v0.1.8 amendment)` to `docs/specs/auto-resume-daemon-design.md` AFTER current EOF (line 910), preceded by a single blank line separator. Section content per PO S1-PLAN-PO draft (~3750 chars).

**Opus minor revision applied** (po-deliverable-1): forward-looking AC-4-B commitment re-phrased to descriptive form: `'≤30s threshold remains the documented ship gate inherited from §1–§6; v0.1.9 charter (when authored) MUST address this gate as its first acceptance criterion'` — avoids pre-committing v0.1.9 scope from inside v0.1.8.

Cross-references in §7 must point to `docs/archives/lessons-learned.v0.1.7.md` (NOT `docs/lessons-learned/v0.1.7.md` — per Opus blocker ruling).

CCB marker preserved: `<!-- ccb: clarify 2026-05-05 — v0.1.8 charter codifies v0.1.7 degraded-mode ship rationale as explicit shipping constraint; ≤30s threshold retained; measurement deferred to v0.1.9 with reference-host prerequisite -->`

**Verify**:
- pre: `wc -l docs/specs/auto-resume-daemon-design.md` → 910
- pre: `tail -1 docs/specs/auto-resume-daemon-design.md` → confirm last line content
- post: `wc -l` → 910 + draft-line-count + 1 (blank separator)
- post: `grep -c '## §7' docs/specs/auto-resume-daemon-design.md` → ≥1
- post: `grep -n 'I-023-M1\|shipping constraint\|non-guarded' docs/specs/auto-resume-daemon-design.md | tail -10` → ≥3 matches in new section
- post (immutability proof per Opus minor): `git diff HEAD -- docs/specs/auto-resume-daemon-design.md | grep -c '^-'` → 0 (only insertions, §1–§6 byte-identical)

**Rollback**: if §1–§6 byte-changed → `git checkout HEAD -- docs/specs/auto-resume-daemon-design.md` + escalate CCB-Heavy.

---

### T-1-2 PO — LessonsLearned formal persistence

| Field | Value |
|---|---|
| Owner | PO PM |
| expected_cost_kT | 10 (actual 12 kT — slight over) |
| blockedBy | none |
| expected_scope_files | docs/archives/lessons-learned.v0.1.7.md (NEW) |
| status | [x] complete (S1-D2, 2026-05-05T02:48; PASS step-review; 57 lines, L-1..L-4 verified) |

**Description**: Create `docs/archives/lessons-learned.v0.1.7.md` (flat-versioned per docs/archives/ precedent — Opus blocker ruling: matches existing PROGRESS.v0.1.7.md + tasks.v0.1.7.md pattern; PO's docs/lessons-learned/ subdir option REJECTED). PO draft from S1-PLAN-PO (~120 lines) applies.

**Opus minor revision applied** (po-deliverable-2): L-2/L-4 inheritance notes constrained to ≤2 lines per entry, format `Inheritance: <flag noted, no new commitment>`. NO normative `shall|must` language. Only L-1/L-3 may carry v0.1.9 measurement reference.

Each entry structure: (1) v0.1.7 statement verbatim (2) v0.1.8 disposition (3) v0.1.9 inheritance note.

**Verify**:
- post: `wc -l docs/archives/lessons-learned.v0.1.7.md` → ≥40 (substantive)
- post: `grep -c 'L-[1-4]' docs/archives/lessons-learned.v0.1.7.md` → ≥4 (each lesson appears as heading)
- post (Opus minor enforcement): QA T-1-6 verifies NO normative `shall|must` language in L-2 / L-4 inheritance notes; only L-1/L-3 carry v0.1.9 measurement reference

---

### T-1-3 PO — README shipping note paragraph + badge bump

| Field | Value |
|---|---|
| Owner | PO PM |
| expected_cost_kT | 8 (actual 18 kT — 2.25× over; Mini Gate fired, verdict PASS via Rule 2 + step-review double-verify) |
| blockedBy | T-1-1 (cross-ref accuracy) |
| expected_scope_files | README.md |
| status | [x] complete (S1-D3, 2026-05-05T02:50; PASS step-review; KMR proxy=9 calibration recorded) |

**Description**: (1) Expand current line 105 one-liner to substantive paragraph (>50 words 繁中) per PO S1-PLAN-PO draft (~280 chars), insertion between lines 107 and 109. (2) Bump version badge line 5: `version-0.1.6` → `version-0.1.8` (skip-version intentional per RAID-I I-1; no v0.1.7 CHANGELOG entry exists). Cross-ref to `docs/archives/lessons-learned.v0.1.7.md` (per Opus location ruling).

**Verify**:
- post: `grep 'version-0\.1\.' README.md | head -1` → contains `0.1.8`
- post: `grep -c 'shipping constraint\|v0.1.9\|reference host' README.md` → ≥2

---

### T-1-4 RD — plugin.json version bump 0.1.7 → 0.1.8

| Field | Value |
|---|---|
| Owner | RD PM |
| expected_cost_kT | 5 (actual 4 kT — under) |
| blockedBy | none (parallel-capable with T-1-1/2/3) |
| expected_scope_files | .claude-plugin/plugin.json |
| status | [x] complete (S1-D4, 2026-05-05T02:42; first attempt schema INCOMPLETE → re-dispatch PASS; step-review PASS) |

**Description**: Single-field edit `"version": "0.1.7"` → `"0.1.8"`. NO other fields change.

**Verify (red-green)**:
- red: `python3 -c "import json; print(json.load(open('.claude-plugin/plugin.json'))['version'])"` → `0.1.7`
- green: `python3 -c "import json; assert json.load(open('.claude-plugin/plugin.json'))['version']=='0.1.8'; print('PASS')"` → `PASS`

---

### T-1-5 RD — CHANGELOG.md v0.1.8 entry

| Field | Value |
|---|---|
| Owner | RD PM |
| expected_cost_kT | 12 (actual 18 kT — 1.5× over; Mini Gate fired, verdict PASS via Bash verify) |
| blockedBy | T-1-1, T-1-2, T-1-3 |
| expected_scope_files | CHANGELOG.md |
| status | [x] complete (S1-D5, 2026-05-05T02:55; PASS step-review; KMR proxy=5 calibration recorded) |

**Description**: Prepend `## [0.1.8] — 2026-05-05` entry before existing `## [0.1.6]` entry. Follow v0.1.6 style: `### Added / ### Changed / ### Why / ### Migration`.

Content:
- Added: design.md §7 — Measurement Deferral & Shipping Constraint
- Added: `docs/archives/lessons-learned.v0.1.7.md` (formal L-1..L-4 persistence)
- Changed: README.md shipping caveat expanded; version badge 0.1.6 → 0.1.8 (skip 0.1.7 per RAID-I I-1)
- Why: v0.1.7 closed with I-023-M1 unmeasured under acceptance (d) degraded-mode; codification prevents v0.1.9 silent inheritance of unacknowledged debt
- Migration: doc-only; no migration

**Opus important revision applied** (T-1-5 / I-2 deferred): include explicit note inside entry body — `[0.1.7] entry was not back-filled at v0.1.7 ship; see docs/archives/lessons-learned.v0.1.7.md for v0.1.7 release record. Back-fill deferred to optional future CCB-Light.`

**Verify**:
- post: `head -5 CHANGELOG.md` → first non-comment content line is `## [0.1.8]`
- post: `grep -c '## \[0\.1\.' CHANGELOG.md` → ≥8 (existing 7 entries + new = 8; no entries deleted)

---

### T-1-6 QA — Gate_Forward verification (Opus minor revision — 5 explicit checks)

| Field | Value |
|---|---|
| Owner | QA PM |
| expected_cost_kT | 15 (actual 18 kT — 1.2× over) |
| blockedBy | T-1-1..T-1-5 (all PO + RD tasks complete) |
| expected_scope_files | read-only |
| status | [x] complete (S1-D6, 2026-05-05T03:00; first verdict PARTIAL — untracked lessons-learned blocker; TeamLead fix `git add -u` + `.gitignore` `docs/archives/*.jsonl` + CCB-Light row; re-verify PASS all 5 checks) |

**Description**: Sonnet step-review on all Stage 1 artifacts (`step_review_mandatory=true` per Charter). 5 explicit verify items (Opus minor revision):

1. **Diff scope ≤ 5 plan files**: `git diff --name-only HEAD` should list ONLY `docs/specs/auto-resume-daemon-design.md` + `docs/archives/lessons-learned.v0.1.7.md` + `README.md` + `.claude-plugin/plugin.json` + `CHANGELOG.md` (TeamLead-owned PROGRESS.md / tasks.md gitignored)
2. **Zero plugin code outside plugin.json + CHANGELOG**: verify NO edits in `scripts/` / `lib/` / `hooks/` / `tools/` / `templates/` / `agents/` / `skills/` / `commands/`
3. **design.md §1–§6 byte-identical immutability proof**: `git diff HEAD~ -- docs/specs/auto-resume-daemon-design.md | grep -c '^-'` → 0 (insertions only, no deletions)
4. **README badge bump 0.1.6 → 0.1.8** (skip-version intentional per I-1)
5. **lessons-learned L-2/L-4 contain NO normative `shall|must` language**; only L-1/L-3 carry v0.1.9 measurement reference

Additional: `python3 -c "import json; assert json.load(open('.claude-plugin/plugin.json'))['version']=='0.1.8'"` exit 0.

QA outputs per-artifact PASS/FAIL verdict. Blocking → re-dispatch responsible PM before T-1-7.

---

### T-1-7 TeamLead — Gate_Requirement (Opus important — split into 4 checkpoints)

| Field | Value |
|---|---|
| Owner | TeamLead |
| expected_cost_kT | 20 |
| blockedBy | T-1-6 PASS |
| expected_scope_files | PROGRESS.md, audit-trail.jsonl |
| status | [ ] pending |

**Description (4 ordered checkpoints — Opus important revision)**:

1. **Opus final-review verdict** captured to PROGRESS.md `## Self-Audit` (`subagent_type: general-purpose`, `model: opus`, `final_review_independent=true` per Charter). Independent Opus audits whole charter DoD criteria.
2. **CEO AskUserQuestion** (6-verb gate) — surface Opus verdict + per-criterion DoD evidence; CEO answer recorded
3. **On `approve`**: PROGRESS.md State → COMPLETED + audit-trail entry `STAGE_1_COMPLETED`
4. **`git tag -a v0.1.8`** + transition to T-1-8 (PR open)

**Rollback (Opus important)**: if Opus final-review verdict = REJECTED → T-1-7 HALT + transition to ESCALATED + populate `## Exception` with `Type: opus_final_review_rejected`. Do NOT auto-revise; CCB-Heavy required for Charter-level retry per Charter §Constraints.

---

### T-1-8 TeamLead — PR open + merge plan (NEW per Opus important "missing" #1)

| Field | Value |
|---|---|
| Owner | TeamLead |
| expected_cost_kT | 8 |
| blockedBy | T-1-7 |
| expected_scope_files | GitHub PR (no local file changes) |
| status | [ ] pending |

**Description**: Open PR `feat/v0.1.8-measurement-deferral` → `main`. PR body references:
- design.md §7 amendment
- `docs/archives/lessons-learned.v0.1.7.md`
- CHANGELOG.md `[0.1.8]` entry
- v0.1.7 → v0.1.9 measurement-deferral context

Wait CEO merge approve. After merge: ensure `git tag v0.1.8` pushed to origin (per T-1-7 step 4).

**Verify**:
- post: `gh pr list --head feat/v0.1.8-measurement-deferral` → 1 PR open
- post-merge: `git tag --list v0.1.8` → `v0.1.8`
- post-merge: `gh release view v0.1.8` → release exists

---

### Budget summary

| Task | Owner | kT |
|---|---|---|
| T-1-1 | PO | 20 |
| T-1-2 | PO | 10 |
| T-1-3 | PO | 8 |
| T-1-4 | RD | 5 |
| T-1-5 | RD | 12 |
| T-1-6 | QA | 15 |
| T-1-7 | TL | 20 |
| T-1-8 | TL | 8 |
| **Total** | | **98** |

Baseline: 120 kT. Headroom: 22 kT (18%).
