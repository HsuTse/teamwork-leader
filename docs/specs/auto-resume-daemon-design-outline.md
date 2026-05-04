# Auto-Resume Daemon — Design Doc Outline (Stage 2 PLANNING artifact)

**Status**: PLANNING outline — section scaffolding only. Body authored in Stage 2 EXECUTING.

**Owner**: PO-PM (this outline) → RD-PM + PO-PM (body in Stage 2 EXECUTING).

**Branch**: `feat/v0.1.7-auto-resume-daemon`.

**Charter goal restated**: Plugin-self-contained AutoCompact resilience — Claude Code sessions survive AutoCompact / cross-session boundaries without losing work, with CEO intervening only at approve points.

**Output target of EXECUTING**: `docs/specs/auto-resume-daemon-design.md` covering 5 main sections + 1 cross-cutting section, each grounded in Stage 1 RAID evidence.

---

## 1. Section coverage map

Six sections total (5 main per charter + 1 cross-cutting per Wave Refinement note 1). Order below reflects authoring order recommended in §3 dependency graph.

| Order | Heading slug | Section purpose (one-line) |
|---|---|---|
| 1 | `## state-machine` | Defines the auto-resume lifecycle states and transitions across PreCompact → daemon-detect → relaunch → SessionStart restoration. |
| 2 | `## baton-schema` | Defines the on-disk handoff payload (`.teamlead/baton.json`) — fields, write atomicity, size cap, retention. |
| 3 | `## gate-lock-schema` | Defines the cross-process coordination lock (`.teamlead/gate.lock`) — preventing concurrent resume attempts; idempotency contract. |
| 4 | `## launchd-plist-template` | Defines the macOS daemon launchd plist for compact-detect + relaunch (Stage 4 target); template + interpolation contract. |
| 5 | `## security-model` | Defines prompt-injection mitigation (resume prompt is operator-trusted, not user-trusted), git stash safety, non-Auto-Mode default for resumed sessions. |
| 6 | `## env-portability` (cross-cutting) | Defines guard-tolerant probe-and-fall-back at install time (per R-002 / I-018) — works across PreToolUse-guard hosts and clean hosts. |

---

## 2. Per-section detail

### 2.1 `## state-machine`

- **Heading slug**: `## state-machine`
- **Section purpose**: Define the auto-resume lifecycle states (e.g., `IDLE`, `PRE_COMPACT_FIRED`, `BATON_WRITTEN`, `DAEMON_DETECTED`, `RELAUNCHING`, `RESUMED_AWAITING_CEO`, `RESUMED_EXECUTING`, `FAILED`) and the transitions between them, plus which actor fires each transition (PreCompact hook / daemon / SessionStart hook / CEO).
- **Acceptance criteria stubs**:
  - [ ] Every state listed has at least one entry transition (with actor + trigger event named).
  - [ ] Every state has at least one exit transition OR is explicitly labeled terminal.
  - [ ] State diagram (mermaid or ASCII) renders the full lifecycle with no orphan nodes.
  - [ ] Failure / fallback path is named for each non-terminal state (what happens if the actor's trigger never fires).
  - [ ] State transitions explicitly cite which Stage 1 evidence supports the transition's feasibility (e.g., "RELAUNCHING → RESUMED via `claude --resume <id> -p` per FV-T-1-1").
- **Stage 1 dependencies**: A-001 (CLI resume-with-prompt is viable), A-002 (baton location is project `.teamlead/`), I-014/I-015 (`--print`/`-p` is hook-free zone — dogfood validation deferred to Stage 3), I-003 (PreCompact ↔ Stop ordering open — design must be lock+idempotent).
- **Open questions**:
  - ? Should `RESUMED_AWAITING_CEO` be a hard halt (CEO must approve) or a soft halt (CEO can pre-approve via baton field)? Default: hard halt per `~/CLAUDE.md` §高風險操作 unless CEO opts in.
  - ? How does the state machine handle a daemon that detects compact but the prior Claude process is still alive (race condition)? Answer expected from gate.lock semantics (§2.3).
  - ? Failure recovery: if relaunch fails 3× in a row, what's the terminal state and CEO notification path?
- **Length estimate**: ~80-120 lines (~3-4 paragraphs prose + 1 state diagram + 1 transition table).

---

### 2.2 `## baton-schema`

- **Heading slug**: `## baton-schema`
- **Section purpose**: Define the on-disk handoff payload (`$CLAUDE_PROJECT_DIR/.teamlead/baton.json`) — schema fields, write-atomicity discipline, size cap, retention/cleanup, and how the daemon + SessionStart hook consume it.
- **Acceptance criteria stubs**:
  - [ ] JSON schema lists every field with type + required/optional + one-line meaning.
  - [ ] Required fields cover: `prior_session_id`, `prior_pause_commit`, `branch`, `last_action_iso`, `progress_md_anchor`, `restore_prompt`, `auto_mode_resumed` (must be `false` by default).
  - [ ] Write protocol is explicitly atomic: write `<baton>.tmp` → `mv` (per FV-T-1-7 §1 "Timeout budget" implication).
  - [ ] Size cap stated with rationale: **chosen design cap = ≤ 1 MB** (per FV-T-1-7 line 587 design recommendation, for round-trip + log-noise reasons, not because of hook limits). Note: 16 MB is the **observed-no-truncation upper bound** per FV-T-1-7 line 580 — NOT the chosen cap. T-2-1 skeleton MUST freeze "baton size limit = 1 MB" as a frozen design decision (per advisor recommendation; cross-section drift case study from PLAN_AUDIT cycle).
  - [ ] Retention policy stated: when does an old baton get archived/deleted? Who is the actor?
  - [ ] Example baton document inlined (real-shaped JSON with concrete sample values, no stub markers).
- **Stage 1 dependencies**: A-002 (baton CAN live in project `.teamlead/`), FV-T-1-7 (timeout = hard kill → atomic write required; payload size budget 1 MB recommended; disk-write trusted over stdout per FV-T-1-2 implication).
- **Open questions**:
  - ? Should baton include the full PROGRESS.md inline or just an anchor + read-it-yourself instruction? Trade-off: inline = self-contained but bloats baton; anchor = relies on PROGRESS.md disk read at restore time but stays small.
  - ? Should `restore_prompt` be templated (assembled at restore time from a template file) or pre-rendered (assembled at PreCompact time and frozen)? Pre-rendered is more deterministic; templated allows late-binding fixes.
  - ? Does baton need a schema-version field for forward compatibility across plugin versions?
- **Length estimate**: ~100-140 lines (~2 paragraphs prose + 1 JSON schema table + 1 example doc + 1 retention table).

---

### 2.3 `## gate-lock-schema`

- **Heading slug**: `## gate-lock-schema`
- **Section purpose**: Define the cross-process coordination lock (`$CLAUDE_PROJECT_DIR/.teamlead/gate.lock`) — file format, acquire/release protocol, stale-lock detection, idempotency contract that allows safe re-trigger if PreCompact fires twice or daemon detects redundantly.
- **Acceptance criteria stubs**:
  - [ ] Lock file format defined (e.g., `pid + iso8601 + actor_role + state_token`) with parse/write contract.
  - [ ] Acquire protocol: how does an actor (PreCompact / daemon / SessionStart) attempt to take the lock? Recommend `flock` or atomic `O_EXCL` create.
  - [ ] Release protocol: who releases on success? Who reaps a stale lock (and based on what staleness criteria — PID alive check, mtime threshold)?
  - [ ] Idempotency contract: if PreCompact fires twice in 100ms, the second invocation MUST be a no-op (not produce a second baton, not split state).
  - [ ] Recovery from corrupt/torn lock: documented procedure (recommend: gate.lock.bak + manual escalation).
  - [ ] Cross-reference to `state-machine` showing which state transitions require holding the lock.
- **Stage 1 dependencies**: I-003 (hook ordering undocumented → MUST design as lock+idempotent, not relying on PreCompact-then-Stop sequencing), A-002 (lock file lives in project `.teamlead/`), I-018 (bash-shell idioms for filesystem ops blocked by host pretooluse_guard.py — use python or non-shell for lock manipulation in scripts).
- **Open questions**:
  - ? Should gate.lock be POSIX `flock(2)` (advisory, fast) or `O_EXCL` create-then-write (portable, slightly slower)? Recommend `flock` for daemon path, `O_EXCL` for hook path (hooks may not have flock-friendly fd lifecycles).
  - ? What's the staleness threshold — PID-not-alive AND mtime > N minutes? What N?
  - ? Does the SessionStart hook need to acquire the lock on resume-detect, or is read-only state inspection sufficient?
- **Length estimate**: ~80-110 lines (~2 paragraphs prose + 1 protocol table + 1 staleness recovery flow).

---

### 2.4 `## launchd-plist-template`

- **Heading slug**: `## launchd-plist-template`
- **Section purpose**: Define the macOS launchd plist template that runs the compact-detect daemon (Stage 4 target). Include label naming convention, RunAtLoad / KeepAlive policy, working directory, env injection, log paths, and the install/uninstall procedure — including the guard-tolerant fallback path per R-002.
- **Acceptance criteria stubs**:
  - [ ] Plist template file present (XML body inlined OR linked to a `templates/` file in the design doc — author's choice).
  - [ ] Label namespace declared (e.g., `com.teamwork-leader.auto-resume-daemon`) with collision-avoidance rationale.
  - [ ] All path placeholders use `${CLAUDE_PLUGIN_ROOT}` or operator-supplied vars (no hardcoded `/Users/...`).
  - [ ] Install procedure documented at two layers: (a) auto-install via `launchctl bootstrap gui/$UID <plist>`, (b) manual-install README fallback (per R-002 + I-018 host PreToolUse guard regex `\blaunchctl\b` blocks auto-install).
  - [ ] Uninstall procedure documented (`launchctl bootout` + plist removal).
  - [ ] Out-of-scope notes: this is Stage 4 deployment template; Stage 3 hook layer can run without launchd (file-watcher polling fallback). Cross-reference `state-machine` for what changes when daemon is absent.
- **Stage 1 dependencies**: R-002 (guard-tolerant probe-and-fall-back required at install time), I-018 (`pretooluse_guard.py` blocks `chmod +x`, `rm`, Write-outside-project literal-string-in-heredoc patterns), FV-T-1-5 (pending — install UX cost not yet measured; section MUST flag this as "Stage 4 to validate at first install attempt").
- **Open questions**:
  - ? Can the daemon detect AutoCompact purely from filesystem signals (baton.json mtime change) or does it need to attach to Claude Code stdout/log stream? Filesystem-only is portable; stream attachment is faster but fragile.
  - ? Should KeepAlive be unconditional or `SuccessfulExit: false` (only restart on crash)?
  - ? FV-T-1-5 verdict pending — does install require Full Disk Access prompt? If yes, is plugin-driven install acceptable UX or must it always be manual?
- **Length estimate**: ~120-160 lines (~2 paragraphs prose + 1 plist XML body + 1 install/uninstall procedure + 1 fallback decision tree). Largest section.

---

### 2.5 `## security-model`

- **Heading slug**: `## security-model`
- **Section purpose**: Define the security posture of auto-resume — (1) prompt-injection mitigation (the restore prompt is operator-trusted, not user-content-trusted; baton fields like `restore_prompt` are sanitized/whitelisted), (2) git stash safety net for uncommitted work (Stage 4 daemon must not silently lose dirty working tree), (3) non-Auto-Mode default for resumed sessions (CEO must explicitly opt resumed session into Auto Mode), (4) mitigation of I-001 (silent 30+ min auto-resume going wrong).
- **Acceptance criteria stubs**:
  - [ ] Threat model section enumerates ≥3 adversarial scenarios with mitigations: (a) baton tampering by malicious local process, (b) prompt-injection in PROGRESS.md content reflected into restore_prompt, (c) daemon hijack (e.g., wrong Claude session resumed).
  - [ ] Non-Auto-Mode default explicitly stated and traced to a baton field (e.g., `auto_mode_resumed: false`) that SessionStart hook checks.
  - [ ] Git stash safety net flow documented: when Stage 4 daemon detects compact mid-edit, dirty tree handling (auto-stash with named ref, recoverable via plain `git stash list`).
  - [ ] CEO notification path documented for "auto-resume failed N times" → no silent failures (mitigates I-001).
  - [ ] `step_review_mandatory: true` restated as a security control (not just process control) — resumed sessions require step-review reviewer to catch rogue auto-resume direction drift.
  - [ ] Cross-reference to `~/CLAUDE.md` §高風險操作 invocation conditions.
- **Stage 1 dependencies**: I-001 (silent auto-resume failure cost), A-001 (the resume CLI accepts `-p` payload as new turn — security implication: payload IS user input from the resumed session's perspective, must be trusted accordingly), R-001 (no native Anthropic feature → we own the security model end-to-end).
- **Open questions**:
  - ? Should baton be signed/HMAC'd to detect tampering, or is filesystem permissions (`0600`) sufficient for v0.1.7 threat model?
  - ? Git stash naming convention — stash ref name must encode session id + timestamp for recovery. How does daemon avoid stashing during active commits (race with operator)?
  - ? CEO notification channel — terminal print? launchd LaunchEvents user-notification? Email? Recommend: terminal print on next interactive session start + persistent `.teamlead/last-resume-failure.txt`.
  - ? Prompt-injection allowlist for restore_prompt — can it contain markdown code blocks? Hyperlinks? Recommend: plain-text only with strict char allowlist for v0.1.7.
- **Length estimate**: ~100-130 lines (~3 paragraphs prose + 1 threat-model table + 1 git stash flow + 1 cross-reference list).

---

### 2.6 `## env-portability` (cross-cutting)

- **Heading slug**: `## env-portability`
- **Section purpose**: Define how the design works across host environments with varying PreToolUse guards, missing CLI tools (`gdate`, `coreutils`), and macOS permission-prompt cost variation. Specify the install-time probe-and-fall-back behavior so plugin install never hard-fails on guard-protected hosts.
- **Acceptance criteria stubs**:
  - [ ] Probe-and-fall-back algorithm stated for each install-time op: try `launchctl bootstrap` → on guard-block, surface manual-install README; try `chmod +x` → on guard-block, fall back to `python -c "os.chmod(...)"` or pre-shipped executable bits.
  - [ ] Hook scripts use Python (not bash) for filesystem ops blocked by guard (per I-018: `chmod`, `rm`, Write-outside-project blocked even in heredoc).
  - [ ] Tool-availability matrix lists every external tool used (`launchctl`, `flock`, `python3`, `gdate`/`date`) with portable fallback for each.
  - [ ] No hardcoded user paths — all paths via `${CLAUDE_PLUGIN_ROOT}` / `${CLAUDE_PROJECT_DIR}` / `$HOME`.
  - [ ] Test plan stated: install dry-run on guard-protected host (this repo's host) AND on a clean host (e.g., CI macOS runner) at Stage 4 close.
- **Stage 1 dependencies**: R-002 (guard-tolerant probe-and-fall-back at install time), I-018 (guard regex blocks `chmod +x`, `rm`, Write-outside-project; bash literal-strings-in-heredoc do not bypass), FV-T-1-3 (gdate absent on macOS host without coreutils → portable date fallback documented).
- **Open questions**:
  - ? Should the plugin ship a "doctor" subcommand that audits host environment readiness before install? Recommend yes — `claude /teamwork-leader doctor` returns missing-tool list.
  - ? Linux support — out of scope for v0.1.7 (launchd is macOS-only) or in scope via systemd-user-units? Recommend out of scope; Stage 4 deliverable is macOS-only with explicit non-goal.
  - ? Windows support — explicitly non-goal; document in env-portability.
- **Length estimate**: ~70-100 lines (~2 paragraphs prose + 1 tool-availability matrix + 1 probe-and-fall-back flow per op).

---

## 3. Section dependency graph

Authoring order (in Stage 2 EXECUTING) should respect these dependencies. A section that depends on another should be drafted AFTER the depended-on section is at least skeleton-complete.

```text
state-machine  ──┬──>  baton-schema       (baton fields are populated at specific state transitions)
                 ├──>  gate-lock-schema   (lock acquisition gates state transitions)
                 └──>  launchd-plist-template  (daemon implements DAEMON_DETECTED → RELAUNCHING transitions)

baton-schema   ──┬──>  security-model     (baton fields drive threat-model — auto_mode_resumed, restore_prompt sanitization)
                 └──>  gate-lock-schema   (lock release happens after baton is committed; ordering matters)

gate-lock-schema ──>  launchd-plist-template  (daemon must respect lock semantics)

env-portability is CROSS-CUTTING — its constraints (guard-tolerant install, Python-not-bash for filesystem ops, portable tool fallbacks) apply to ALL of the above. Draft env-portability LAST as a synthesis pass so it can cite concrete constraints from each prior section.
```

Authoring order recommendation: **state-machine → baton-schema → gate-lock-schema → launchd-plist-template → security-model → env-portability**.

---

## 4. Length estimate roll-up (for Stage 2 EXECUTING budget)

| Section | Estimated lines |
|---|---|
| `state-machine` | 80-120 |
| `baton-schema` | 100-140 |
| `gate-lock-schema` | 80-110 |
| `launchd-plist-template` | 120-160 |
| `security-model` | 100-130 |
| `env-portability` | 70-100 |
| Front matter + TOC + intro + cross-section nav | 30-50 |
| **Total estimated body** | **580-810 lines** |

This estimate is for body of `auto-resume-daemon-design.md` (excluding this outline file). Stage 2 EXECUTING budget kT cost should be sized accordingly: 580-810 lines of design prose + diagrams ≈ 25-40 kT writing cost (within Stage 2 PO 60 kT + RD 30 kT allocation).

---

## 5. CCB-Light requests

None at this outline stage.

The following items are flagged as **open design questions** (in §2 per-section "Open questions") rather than CCB-Light requests, because they are answerable during Stage 2 EXECUTING by the design author with reference to Stage 1 evidence + first principles. They DO NOT block Stage 2 EXECUTING start; they are tracked so the EXECUTING design doc explicitly states the chosen answer + rationale.

If during Stage 2 EXECUTING any open question turns out to require CEO charter clarification (e.g., the trade-off has business/policy implications beyond technical design), it will be raised as a CCB-Light at that time via PO-PM dispatch return.

---

## 6. Stage 2 EXECUTING handoff notes

When Stage 2 transitions PLANNING → PLAN_AUDIT → EXECUTING, this outline becomes the **scope-locking artifact** — design doc author MUST:

1. Produce one section per outline section (no consolidation, no skipping).
2. For each section, satisfy ALL acceptance-criteria stubs listed in §2 (or carry remaining stubs as RAID-A with rationale at design doc handback).
3. Resolve every open question in §2 — either with a design decision (citing rationale) or by carrying as a RAID-I (with explicit reason design can proceed without resolution).
4. Cite Stage 1 RAID dependencies inline using the exact RAID IDs listed in §2 ("per FV-T-1-N <verdict>" or "per RAID I-NNN").
5. Maintain section dependency order per §3 — if a later-section decision invalidates an earlier section, raise a CCB-Light, do NOT silently rewrite prior sections.

This outline file (`docs/specs/auto-resume-daemon-design-outline.md`) is consumed by Stage 2 EXECUTING and may be referenced by PlanAudit reviewer for scope-conformance check. It SHOULD NOT be deleted at Stage 2 close — it remains the audit trail for "what did Stage 2 EXECUTING agree to deliver."
