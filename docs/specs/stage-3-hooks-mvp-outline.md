# Auto-Resume Daemon — Stage 3 MVP Hooks Outline (Stage 3 PLANNING artifact)

**Status**: PLANNING outline — section scaffolding only. Body authored in Stage 3 EXECUTING.

**Owner**: PO-PM (this outline) → RD-PM (body in Stage 3 EXECUTING per parallel_pm_limit=2).

**Branch**: `feat/v0.1.7-auto-resume-daemon`.

**Spec authority**: `docs/specs/auto-resume-daemon-design.md` (732 lines, FROZEN at Stage 2 close). Stage 3
implementation cites this document but DOES NOT modify it. CCB-Light required for any revision.

**Charter goal for Stage 3**: Deliver the plugin-self-contained hook layer (Phase 1 MVP) — 7 hook/lib
scripts that implement the §1 state machine transitions fired by Claude Code's built-in
`PreCompact` / `Stop` / `SessionStart` events, without any launchd daemon (Stage 4 target).

---

## 1. Cross-invocation diagram

The three Claude Code hook events each fan out to one or more lib scripts:

```text
Claude Code hook events:

  PreCompact  ──>  hooks/pre-compact.sh
                       ├──>  lib/gate-lock.sh  (acquire gate.lock before write)
                       ├──>  lib/handoff-builder.sh  (assemble RESUME context payload)
                       └──>  lib/baton-writer.sh  (atomic baton write + chmod 0600)
                       └──>  lib/gate-lock.sh  (release gate.lock after atomic rename)

  Stop        ──>  hooks/stop.sh
                       └──>  lib/notifier.sh  (osascript macOS notification)

  SessionStart  ──>  hooks/session-start.sh
                       ├──>  (reads baton.json if present — direct file read, no lib)
                       └──>  lib/gate-lock.sh  (stale-lock reaper sweep at entry; optional acquire)
```

No lib script may call another lib script (flat invocation depth = 1). Each hook script is the
sole caller for its own lib dependencies. Stage 3 does NOT include the launchd daemon
(`scripts/daemon.py`) — the `BATON_WRITTEN → SESSION_RESUMED` T5 transition (design.md §1 T5)
is a Stage 4 deliverable.

---

## 2. Per-script section detail

One section per script. Each section maps to exactly one implementation task in Stage 3
EXECUTING (7 scripts = 7 EXECUTING tasks minimum, each with its own Sonnet step-review).

---

## hooks/pre-compact.sh

- **Purpose**: Fired by Claude Code `PreCompact` event (design.md §1 T2 trigger). Drives the state
  machine transition `ARMED → PRE_COMPACT_TRIGGERED → BATON_WRITTEN` (T2→T3) or to `ABORTED` (T4).
  Primary orchestrator: acquires gate.lock via `lib/gate-lock.sh`, invokes `lib/handoff-builder.sh`
  to assemble the RESUME context payload, writes the baton via `lib/baton-writer.sh`, then releases
  the lock. All filesystem operations use Python per design.md §1 "Hook-script-language constraint
  (I-018)".
- **Interface stub**:
  - Input env vars: `CLAUDE_PROJECT_DIR` (per A-002 VALIDATED), `CLAUDE_PLUGIN_ROOT`
    (for lib script resolution), `CLAUDE_SESSION_ID` (baton `session_id` field)
  - Input args: none (hook receives no positional args from Claude Code built-in event API)
  - Output: writes `$CLAUDE_PROJECT_DIR/.teamlead/baton.json` (via lib/baton-writer.sh);
    writes `$CLAUDE_PROJECT_DIR/.teamlead/gate.lock` (via lib/gate-lock.sh); exit 0 on
    `BATON_WRITTEN`; exit 1 on `ABORTED` (failure written to
    `$CLAUDE_PROJECT_DIR/.teamlead/last-resume-failure.txt`)
- **Acceptance criteria**:
  - [ ] `baton.json` exists at `$CLAUDE_PROJECT_DIR/.teamlead/baton.json` with all 7 required
        fields populated and non-null after a successful invocation (design.md §2 JSON schema
        fragment: `session_id`, `prior_pause_commit`, `branch`, `last_action_iso`,
        `progress_md_anchor`, `restore_prompt`, `auto_mode_resumed: false`)
  - [ ] `baton.json` permissions are `0600` immediately after write (design.md §2 "File location
        and permissions")
  - [ ] Gate.lock is NOT present on disk after successful invocation (released by
        `lib/gate-lock.sh` after atomic rename completes per design.md §3 "Release protocol")
  - [ ] If payload size exceeds 1 MB chosen design cap, hook exits non-zero and writes
        `last-resume-failure.txt` with reason `restore_prompt-allowlist-rejection` or
        `payload-size-exceeded-1mb-cap`; `baton.json` is NOT written (design.md §2 "Size budget"
        + design.md §1 T4 branch)
  - [ ] `restore_prompt` field passes plain-text allowlist: ASCII letters/digits/whitespace/
        permitted punctuation per design.md §5 "Allowlist policy at baton-write time"; backtick,
        `$`, `${`, `\x00` are rejected and trigger exit non-zero
  - [ ] `auto_mode_resumed` is always written as boolean `false` in PreCompact-invocation path
        (design.md §2 `auto_mode_resumed: false` rationale; frozen design decision)
  - [ ] On gate.lock contention (lock already held by another actor), hook retries up to 30 s
        then aborts to `ABORTED` via T4 path (design.md §3 "Acquire / release semantics —
        PreCompact hook waits up to 30 s then aborts T3 → T4")
- **Stage 1+2 dependencies**:
  - A-001 VALIDATED (design.md §1 T3 side-effect: resume CLI uses `session_id` from baton)
  - A-002 VALIDATED (design.md §2 "File location": `$CLAUDE_PROJECT_DIR/.teamlead/` writable)
  - FV-T-1-7 (design.md §2 "Size budget" + §3 `ttl_seconds` default 90): 60 s hook timeout
    hard-kill drives atomic write requirement
  - I-018 OPEN (design.md §1 "Hook-script-language constraint"): Python only, no bash
    `chmod`/`rm`/Write-outside-project
  - I-003 OPEN (design.md §3 "Acquire / release semantics"): lock+idempotent because hook
    ordering is undocumented; re-validate Stage 3 dogfood
- **Open questions** (PLAN_AUDIT or EXECUTING must resolve):
  - ? Should `hooks/pre-compact.sh` be a Python script (`.py` extension) or a bash shebang
    wrapper that exec's Python? The bash wrapper preserves Claude Code's hooks.json
    `executable` convention; pure `.py` is cleaner. Decide at PLAN_AUDIT.
  - ? If `CLAUDE_SESSION_ID` env var is not set by Claude Code's `PreCompact` event (env var
    availability per hook type is undocumented — design.md §1 T3 cites A-001 but A-001 tested
    `--resume <id>` with a known ID, not the hook-environment injection), what fallback does
    the hook use to populate `session_id`? Candidate: read from `claude` process env or a
    known sessionstate file. Stage 3 dogfood must verify.
  - ? What is the exact set of env vars available inside the `PreCompact` hook invocation?
    Claude Code hook development docs are sparse; Stage 3 must instrument to discover.

---

## hooks/stop.sh

- **Purpose**: Fired by Claude Code `Stop` event (design.md §1 T1 context: Stop is relevant
  only if prior session was interactive — per I-015, Stop does NOT fire in `--print` mode).
  Emits a macOS courtesy notification via `lib/notifier.sh` to signal session end (per design.md
  §5 CEO notification channel "best-effort courtesy notification"). Also appends a last-action
  sentinel to `$CLAUDE_PROJECT_DIR/.teamlead/last-stop.txt` so the daemon can distinguish
  "baton written + session ended normally" from "baton written + session still running".
- **Interface stub**:
  - Input env vars: `CLAUDE_PROJECT_DIR`, `CLAUDE_PLUGIN_ROOT`, `CLAUDE_SESSION_ID` (if
    available in Stop event — see open question below)
  - Input args: none
  - Output: invokes `lib/notifier.sh` (best-effort; silent no-op on non-macOS or osascript
    absent); appends one-line JSON record to
    `$CLAUDE_PROJECT_DIR/.teamlead/last-stop.txt`
    (`{ "session_id": "...", "stopped_at": "<ISO>", "baton_present": true|false }`);
    always exits 0 (Stop hook must not block session teardown)
- **Acceptance criteria**:
  - [ ] macOS notification is emitted via `lib/notifier.sh` when `osascript` is available on
        `PATH` (verifiable in Stage 3 dogfood by observing notification banner; design.md §5
        "Channel scope")
  - [ ] On non-macOS or `osascript` absent, `stop.sh` exits 0 silently with no error output
        (design.md §6 "Tool-availability matrix": osascript listed as macOS-only; guard-tolerant)
  - [ ] `last-stop.txt` is appended (not overwritten) with a one-line JSON record containing
        at minimum `stopped_at` ISO-8601 timestamp and `baton_present` boolean
  - [ ] `stop.sh` ALWAYS exits 0 regardless of notifier errors, file-write errors, or missing
        env vars; the hook must never block Claude Code session teardown
  - [ ] If `baton.json` is NOT present at Stop time (no PreCompact in this session),
        `baton_present: false` is written and no notification references a resume episode
- **Stage 1+2 dependencies**:
  - I-015 OPEN (design.md §1 "Interactive-only track": Stop does not fire in `--print` mode;
    Stage 3 dogfood re-validates in real interactive session)
  - design.md §5 CEO notification channel §5 step 2 (osascript best-effort)
  - design.md §6 tool-availability matrix (osascript = macOS-only, no hard requirement)
- **Open questions** (PLAN_AUDIT or EXECUTING must resolve):
  - ? Does Claude Code's `Stop` event fire with a `CLAUDE_SESSION_ID` env var, or must the
    hook read `session_id` from an existing `baton.json` (if present)? This affects how
    `last-stop.txt` record is populated.
  - ? Is the notification content ("Session stopped — baton at .teamlead/baton.json") the
    correct trigger for a Stop notification, or should `stop.sh` only notify when a baton IS
    present (i.e., a resume episode is in flight)? Decision affects UX noise level.

---

## hooks/session-start.sh

- **Purpose**: Fired by Claude Code `SessionStart` event (design.md §1 T1 for normal arm, and
  T8 for the resumed-session path). Reads `baton.json` if present; if baton `gate_state =
  BATON_WRITTEN` (unconsumed resume episode), auto-injects the RESUME context prompt to the
  session; also runs the stale-lock reaper sweep (design.md §1 T11 `BATON_WRITTEN` fallback
  path when daemon is absent). Acts as the "operator-driven resume fallback" path for hosts
  where Stage 4 daemon is not installed.
- **Interface stub**:
  - Input env vars: `CLAUDE_PROJECT_DIR`, `CLAUDE_PLUGIN_ROOT`, `CLAUDE_SESSION_ID`
  - Input args: none
  - Output: if baton is present and unconsumed, emits RESUME context to stdout (format: a
    multi-line text block beginning with `RESUME CONTEXT:` that Claude Code injected into the
    session's first message per design.md §1 T8 "SessionStart hook fires; baton present"); also
    runs `lib/gate-lock.sh` stale-lock reaper (may write
    `$CLAUDE_PROJECT_DIR/.teamlead/last-reaper-action.json`); if `last-resume-failure.txt`
    exists with newer mtime than `last-resume-failure.acked`, emits banner line; exits 0
    always
- **Acceptance criteria**:
  - [ ] When `baton.json` is present with `gate_state=BATON_WRITTEN`, hook emits a `RESUME
        CONTEXT:` block to stdout containing at minimum: `restore_prompt` value, last dispatch
        ID (`last_dispatch_id`), branch, and `prior_pause_commit` (design.md §1 T8
        "compose `restore_prompt`")
  - [ ] When `baton.json` is absent or `gate_state=DONE` (consumed), hook exits 0 silently
        with no output (normal session-start path: `ARMED` state, T1)
  - [ ] When `last-resume-failure.txt` exists with mtime newer than
        `last-resume-failure.acked`, hook emits a banner line beginning with
        `PRIOR AUTO-RESUME FAILED` to stdout before any RESUME CONTEXT block (design.md §5
        CEO notification channel step 3)
  - [ ] Stale-lock reaper sweep is run at hook entry via `lib/gate-lock.sh`: if a stale lock
        is detected (PID-not-alive + mtime > TTL), reaper force-releases gate.lock and writes
        `last-reaper-action.json` (design.md §3 "Stale-lock recovery")
  - [ ] `progress_md_anchor` in baton is recomputed (SHA-256 of current `PROGRESS.md`) and
        compared; mismatch emits warning in RESUME CONTEXT block ("PROGRESS.md changed since
        pause — manual reconciliation may be needed") but does NOT abort the resume (design.md
        §1 T8: mismatch → "operator must reconcile before T9 ack")
  - [ ] Hook always exits 0; never blocks session start
- **Stage 1+2 dependencies**:
  - A-001 VALIDATED (design.md §1 T8: resume via `claude --resume <session_id>` is the Stage 4
    daemon's job; Stage 3 session-start.sh provides the in-session RESUME context injection
    after the session is already started)
  - A-002 VALIDATED (design.md §1 T1: `.teamlead/` dir creation at hook entry)
  - I-014 OPEN (design.md §1 "Interactive-only track": Stage 3 dogfood re-validates
    SessionStart fires in interactive mode; i.e., the resumed session is interactive per §1 Q4)
  - I-001 OPEN (design.md §5 "CEO notification channel": banner on next SessionStart is step 3
    of 3-track notification)
  - design.md §3 "Stale-lock recovery" (T11 reaper runs at SessionStart hook entry)
- **Open questions** (PLAN_AUDIT or EXECUTING must resolve):
  - ? How does the `RESUME CONTEXT:` block actually get injected into the session? The design.md
    §1 T8 says SessionStart hook "composes `restore_prompt`" — but the exact Claude Code API
    for SessionStart hook output injection (stdout? a specific env var? a structured JSON
    message?) must be verified against Claude Code hook-development docs before implementation.
  - ? Should `session-start.sh` unconditionally run the stale-lock reaper, or only when
    gate.lock is detected on disk? Unconditional approach adds a stat() call per session start;
    conditional is cheaper but requires detecting lock presence first.
  - ? `session-start.sh` is responsible for T1 (arm: ensure `.teamlead/` dir exists, verify
    gate.lock absent or stale-recoverable) per design.md §1 transition table. Should T1 arm
    logic live in `session-start.sh` directly, or in a helper function invoked by it?

---

## lib/handoff-builder.sh

- **Purpose**: Internal lib invoked by `hooks/pre-compact.sh`. Constructs the RESUME context
  payload: reads `PROGRESS.md` for the `Last Action` anchor, reads the tail of
  `audit-trail.jsonl` (last N rows, configurable), reads the current dispatch ID from
  PROGRESS.md `Active Stage`, and assembles `restore_prompt` + `progress_md_anchor` (SHA-256
  of `PROGRESS.md` content). Also enforces the 8 KB length cap on `restore_prompt` per
  design.md §5 "Prompt-injection mitigation — Length cap".
- **Interface stub**:
  - Input env vars: `CLAUDE_PROJECT_DIR` (for PROGRESS.md + audit-trail.jsonl paths),
    `CLAUDE_PLUGIN_ROOT`
  - Input args: none (reads well-known paths defined by `CLAUDE_PROJECT_DIR`)
  - Output: writes to stdout a JSON object with fields `restore_prompt` (string ≤ 8 KB),
    `progress_md_anchor` (SHA-256 hex), `last_action_iso` (ISO-8601 from PROGRESS.md
    `Last Action` line), `last_dispatch_id` (dispatch ID from PROGRESS.md); exit 0 on success,
    exit 1 if PROGRESS.md unreadable or anchor-computation fails
- **Acceptance criteria** (Opus PLAN_AUDIT cross-PM scope alignment: handoff-builder is the natural git-rev-parse caller; PreCompact orchestrator does not call git directly. Output now 6 fields not 4):
  - [ ] Output JSON contains all 6 fields: `restore_prompt`, `progress_md_anchor`,
        `last_action_iso`, `last_dispatch_id`, **`prior_pause_commit`** (via `git rev-parse HEAD` subprocess),
        **`branch`** (via `git rev-parse --abbrev-ref HEAD` subprocess) (design.md §2 required fields
        that originate in handoff-builder)
  - [ ] `prior_pause_commit` is a 40-char hex SHA matching the working tree's HEAD commit at the
        time of PreCompact firing
  - [ ] `branch` is a string matching the current git branch (or `(detached HEAD)` if HEAD is detached)
  - [ ] `progress_md_anchor` matches `sha256sum $CLAUDE_PROJECT_DIR/PROGRESS.md` (or Python
        `hashlib.sha256` equivalent) — verifiable by independent checksum computation
  - [ ] `restore_prompt` is ≤ 8192 bytes (8 KB cap per design.md §5 "Length cap"); if raw
        assembled content exceeds cap, truncate with a marker (e.g., `[TRUNCATED AT 8KB —
        consult PROGRESS.md directly]`) rather than failing
  - [ ] `restore_prompt` passes the plain-text allowlist (same allowlist as §5 write-time
        check): backtick, `$`, `${`, `\x00` absent (design.md §5 "Allowlist policy")
  - [ ] `last_action_iso` parses as a valid ISO-8601 timestamp (if PROGRESS.md `Last Action`
        line is absent or malformed, fall back to current UTC time and log a warning to stderr)
  - [ ] `last_dispatch_id` is extracted from PROGRESS.md `Last Action` `dispatch_id` field;
        if not found, set to `"unknown"` (never null per design.md §2 optional field handling)
- **Stage 1+2 dependencies**:
  - design.md §2 `restore_prompt` schema field + size budget (§5 §8 KB cap)
  - design.md §5 "Prompt-injection mitigation — Allowlist policy at baton-write time"
  - design.md §5 "Prompt-injection mitigation — Length cap" (8 KB)
  - FV-T-1-7 (design.md §2 "Size budget"): 1 MB baton cap; `restore_prompt` is largest
    variable-size field; 8 KB cap ensures baton stays well under 1 MB even with all optional
    fields populated
- **Open questions** (PLAN_AUDIT or EXECUTING must resolve):
  - ? How many tail rows from `audit-trail.jsonl` should be included in the `restore_prompt`
    assembly? Including too many may inflate `restore_prompt` past 8 KB; including too few
    reduces resume fidelity. Candidate: last 3 rows (covers recent dispatch chain). EXECUTING
    task should validate this with a real PROGRESS.md.
  - ? Should `handoff-builder.sh` call Python inline (`python3 -c "import hashlib; ..."`) for
    the SHA-256 computation, or can it use `shasum -a 256` (BSD) / `sha256sum` (GNU) with a
    portability guard? Prefer Python for consistency with I-018 discipline, but the hash
    computation itself is not a guard-sensitive operation.

---

## lib/notifier.sh

- **Purpose**: Internal lib invoked by `hooks/stop.sh`. macOS `osascript` wrapper with
  guard-tolerant probe-and-fall-back per design.md §6 env-portability philosophy. If
  `osascript` is present, emits a macOS notification; if absent (or returns non-zero), silently
  no-ops. Never causes its caller to exit non-zero.
- **Interface stub**:
  - Input env vars: none required (message content passed via args)
  - Input args: `--title <string>` and `--message <string>` (or `$1=title`, `$2=message` —
    exact arg convention deferred to EXECUTING per §6 open question 7; pick one consistently)
  - Output: exits 0 always; emits macOS notification if `osascript` available; writes nothing
    to stdout; writes errors to stderr only if `TEAMLEAD_DEBUG=1` is set
- **Acceptance criteria**:
  - [ ] When `osascript` is on `PATH` and returns exit code 0, caller receives notification
        with the provided title and message (design.md §5 CEO notification channel step 2:
        `display notification "..." with title "TeamLead"`)
  - [ ] When `osascript` is absent from `PATH`, `lib/notifier.sh` exits 0 silently with no
        stderr output (design.md §6 tool-availability matrix — osascript is macOS-only,
        not a hard requirement)
  - [ ] When `osascript` returns non-zero (e.g., notification permissions denied), `lib/
        notifier.sh` still exits 0 (the caller stop.sh must never be blocked by notification
        failure per design.md §5 "BEST-EFFORT courtesy notification")
  - [ ] `--title` and `--message` args are passed through to `osascript -e 'display
        notification "<message>" with title "<title>"'` without shell-injection exposure (args
        passed as single-quoted string literals embedded in the AppleScript; no shell expansion
        in the AppleScript string body)
  - [ ] `lib/notifier.sh` has no side effects on disk (no file writes, no baton interaction)
- **Stage 1+2 dependencies**:
  - design.md §5 CEO notification channel step 2 (osascript wrapper)
  - design.md §6 tool-availability matrix row for `osascript` (best-effort, macOS-only)
  - R-002 MITIGATING (design.md §6 guard-tolerant install): notifier is a runtime lib, not an
    install-time op; guard impact is LOW here (osascript is not in the guard regex); but the
    probe-and-fall-back philosophy (never hard-fail on env variation) applies
- **Open questions** (PLAN_AUDIT or EXECUTING must resolve):
  - ? Should `lib/notifier.sh` be a bash script or a Python script? osascript is called via
    subprocess either way; bash is simpler for a one-liner wrapper; Python is consistent with
    I-018 discipline. Given notifier.sh does NO filesystem ops (only subprocess exec), bash is
    arguably acceptable here — decide at PLAN_AUDIT with explicit I-018 applicability ruling.
  - ? Should the notification include the `baton.json` path or only a generic message? Detailed
    message aids diagnosis but may expose project-internal paths in OS notification center.

---

## lib/baton-writer.sh

- **Purpose**: Internal lib for the atomic baton write sequence: (1) serialize the baton JSON
  payload to `baton.json.tmp`, (2) `os.replace(tmp, baton.json)` (POSIX atomic rename on same
  filesystem), (3) `os.chmod(baton.json, 0o600)`. This lib is the sole writer of `baton.json`.
  Per design.md §2 "Atomic-write protocol" and design.md §1 T3 side-effect, the atomic rename
  MUST occur under the gate.lock held by the caller (`hooks/pre-compact.sh`). This lib does
  NOT acquire or release the lock — that is the caller's responsibility.
- **Interface stub**:
  - Input env vars: `CLAUDE_PROJECT_DIR` (target dir), `CLAUDE_PLUGIN_ROOT`
  - Input args: `$1` = path to JSON payload file assembled by caller (or JSON piped via stdin
    — exact interface deferred to EXECUTING per §6 open question 5; stdin preferred to avoid
    tempfile proliferation)
  - Output: writes `$CLAUDE_PROJECT_DIR/.teamlead/baton.json` with `0600` permissions;
    removes `baton.json.tmp` after successful rename; exits 0 on success, exit 1 if rename
    fails (disk full, permission denied) — caller maps exit 1 to T4 `ABORTED` path
- **Acceptance criteria**:
  - [ ] After successful invocation, `baton.json` is present at
        `$CLAUDE_PROJECT_DIR/.teamlead/baton.json` with the exact JSON content passed as input
        (no field additions or mutations by baton-writer; it is a transparent write layer)
  - [ ] `baton.json` permissions are `0600` immediately after write (design.md §2 "File
        location and permissions" — `os.chmod` called AFTER `os.replace`, BEFORE returning to
        caller)
  - [ ] `baton.json.tmp` is NOT present after successful invocation (removed by atomic rename
        operation)
  - [ ] If rename fails (e.g., disk full), `baton.json.tmp` is left on disk for the T11 reaper
        to quarantine (design.md §2 "Atomic-write protocol — torn write left by hook-timeout
        kill"); lib exits 1; caller aborts to `ABORTED`
  - [ ] Payload size is validated against 1 MB cap before write attempt; if payload exceeds
        cap, lib exits 1 immediately without creating `baton.json.tmp` (design.md §2 "Size
        budget: chosen design cap ≤ 1 MB")
  - [ ] Lib is implemented in Python (not bash) per I-018 (design.md §1 "Hook-script-language
        constraint"): uses `os.replace()` for atomic rename, `os.chmod()` for permissions
- **Stage 1+2 dependencies**:
  - design.md §2 "Atomic-write protocol" (`baton.json.tmp → os.replace → baton.json`)
  - design.md §2 "File location and permissions" (`0600` post-rename)
  - design.md §2 "Size budget" (1 MB cap at write time)
  - FV-T-1-7 (design.md §2 "Size budget"): 60 s hook timeout = hard kill; atomic rename is
    the crash-safe operation that survives a mid-write kill
  - I-018 OPEN (design.md §1 "Hook-script-language constraint"): Python `os.replace` / 
    `os.chmod`; bash `mv` rejected due to guard + non-atomic behavior on some filesystems
- **Open questions** (PLAN_AUDIT or EXECUTING must resolve):
  - ? Should `lib/baton-writer.sh` accept JSON via stdin or via a named temp file path? Stdin
    avoids leaving an extra temp file; named file is easier to debug in dogfood. Decide at
    EXECUTING (low consequence; can be revised without CCB).
  - ? Should baton-writer validate JSON schema correctness (check all 7 required fields
    present and non-null) before writing, or trust the caller to have assembled a valid payload?
    Validation adds safety but duplicates caller-side logic. Recommendation: minimal schema
    check (key presence only, no type coercion) at baton-writer layer; defer full validation to
    session-start.sh reader.

---

## lib/gate-lock.sh

- **Purpose**: Internal lib implementing the `O_CREAT|O_EXCL` gate.lock acquire/release/reaper
  operations per design.md §3. Used by `hooks/pre-compact.sh` (acquire before baton write;
  release after atomic rename), `hooks/session-start.sh` (stale-lock reaper sweep at hook
  entry), and potentially by the Stage 4 daemon (T5 `BATON_WRITTEN → SESSION_RESUMED`
  transition). All operations are Python per I-018; shell `flock(1)` is explicitly rejected per
  design.md §3 "I-009 flock pitfall reference".
- **Interface stub**:
  - Input env vars: `CLAUDE_PROJECT_DIR` (lock file path: `$CLAUDE_PROJECT_DIR/.teamlead/
    gate.lock`), `CLAUDE_PLUGIN_ROOT`
  - Input args: subcommand `acquire <holder_role> <state_token>` | `release` |
    `reap [--dry-run]`
  - Output:
    - `acquire`: writes gate.lock JSON (`pid`, `acquired_at`, `holder_role`, `state_token`,
      `ttl_seconds=90`) on success; exits 0; exits 1 on `FileExistsError` with live holder
      (contention); exits 2 on unrecoverable error
    - `release`: removes gate.lock via `os.unlink`; exits 0; exits 1 if lock not held by
      current process (wrong PID — should not happen in normal flow)
    - `reap`: force-releases stale locks (dead holder OR TTL expired OR role mismatch per
      design.md §3 "Stale-lock recovery"); writes `last-reaper-action.json`; exits 0 (even if
      no stale lock found); `--dry-run` reports but does not unlink
- **Acceptance criteria**:
  - [ ] `acquire` uses `os.open(path, O_CREAT|O_EXCL|O_WRONLY, 0o600)` (design.md §3
        "Acquire / release semantics — the `O_EXCL` flag makes the create-or-fail atomic");
        on `FileExistsError`, reads existing lock and applies liveness probe
        `os.kill(pid, 0)` per design.md §3 step 2
  - [ ] `release` is called only by the PID that holds the lock; if called by a different PID,
        log warning to stderr and exit 1 (guard against double-release races in future)
  - [ ] `reap` identifies stale locks via all three criteria in design.md §3 "Stale-lock
        recovery": (a) TTL expiry (`now - acquired_at > ttl_seconds`), (b) dead holder
        (`os.kill(pid, 0)` raises `ProcessLookupError`), (c) role/PID mismatch against
        daemon.pid file; writes `last-reaper-action.json` record on any force-release
  - [ ] Lock file format matches design.md §3 schema exactly: 3 required fields (`pid`,
        `acquired_at`, `holder_role`) + 2 optional (`state_token`, `ttl_seconds`)
  - [ ] `gate-lock.sh` is implemented in Python per I-018; no shell `flock(1)` invocation
        anywhere in the implementation (design.md §3 "I-009 flock pitfall reference")
  - [ ] Idempotency: if `reap` is invoked twice in rapid succession, the second invocation
        succeeds with no action (no `O_EXCL` race on the `last-reaper-action.json` overwrite;
        single-record overwrite is safe per design.md §3 reaper definition)
- **Stage 1+2 dependencies**:
  - design.md §3 entire section (lock schema, acquire/release, stale-lock recovery)
  - I-003 OPEN (design.md §3 "Scope"): hook ordering undocumented; gate.lock must be
    lock+idempotent to handle PreCompact firing twice in 100 ms
  - I-009 CLOSED (design.md §3 "I-009 flock pitfall reference"): shell flock quoting bug —
    explicitly rejected; `O_EXCL` is the correct primitive
  - I-018 OPEN (design.md §1 "Hook-script-language constraint"): Python required for
    `os.open(O_CREAT|O_EXCL)` / `os.kill(pid, 0)` / `os.unlink`
  - FV-T-1-7 (design.md §3 `ttl_seconds=90`): TTL = 60 s baton write timeout + 30 s buffer
- **Open questions** (PLAN_AUDIT or EXECUTING must resolve):
  - ? Should `lib/gate-lock.sh` be a Python module callable as a library (imported by
    pre-compact.sh Python code) or a standalone script invoked via subprocess? Library mode is
    more efficient (no subprocess overhead per lock operation); subprocess mode preserves the
    "all libs are independent scripts" invariant. Decide at PLAN_AUDIT — this affects the
    hooks/pre-compact.sh implementation architecture.
  - ? Should the `reap` subcommand also handle `baton.json.tmp` quarantine (rename torn temp
    file to `baton.json.tmp.torn-<ISO>`) or is that the caller's responsibility? Design.md §2
    says "T11 stale-lock reaper" handles this; gate-lock.sh is the T11 implementer, so
    inclusion seems correct — but needs explicit decision at EXECUTING.

---

## 3. Integration acceptance criteria

These invariants span multiple scripts and MUST be satisfied in the integrated system (not just
per-script unit test).

- [ ] **Gate-lock integrity**: `lib/gate-lock.sh acquire` MUST complete before
      `lib/baton-writer.sh` starts; `lib/gate-lock.sh release` MUST be called only AFTER
      `lib/baton-writer.sh` reports exit 0 (successful atomic rename). This ordering is
      enforced in `hooks/pre-compact.sh` caller logic, not in either lib. Test: run
      `hooks/pre-compact.sh` under `strace` or `dtrace` and verify syscall ordering.
      (design.md §3 "Cross-reference to §1 transitions: T3 PreCompact hook acquires with
      holder_role=PreCompact before writing baton.json.tmp, releases after atomic rename")
- [ ] **Stale-lock reaper is idempotent across concurrent callers**: if `hooks/session-start.sh`
      and a Stage 4 daemon (future) both call `lib/gate-lock.sh reap` simultaneously, neither
      crashes and `last-reaper-action.json` reflects the outcome of exactly one reap action.
      (design.md §3 "Multiple reaper invocations are idempotent — the `O_CREAT|O_EXCL` retry
      naturally serializes them")
- [ ] **Baton written once per PreCompact episode**: two rapid successive PreCompact firings
      (I-003 race) produce exactly ONE `baton.json` (the second invocation of `gate-lock.sh
      acquire` detects live holder and waits/aborts, never producing a split baton).
      (design.md §3 "Idempotency contract")
- [ ] **SessionStart auto-inject only for unconsumed batons**: `hooks/session-start.sh` emits
      RESUME CONTEXT only when `baton.json` is present AND `gate_state = BATON_WRITTEN`; if
      `gate_state = DONE` or `ABORTED`, no RESUME CONTEXT is emitted (design.md §1 T1 normal
      arm path).
- [ ] **Stop hook never fails silently in a way that blocks session teardown**: even when
      `lib/notifier.sh` times out or `last-stop.txt` write fails (e.g., `.teamlead/` dir
      missing), `hooks/stop.sh` exits 0. (design.md §5 CEO notification channel: "COURTESY,
      NOT SOURCE OF TRUTH")
- [ ] **No host-skill dependencies**: all 7 scripts resolve their dependencies via
      `${CLAUDE_PLUGIN_ROOT}` only; no `strategic-compact`, `last-word`, or other external
      plugin invocations. (Charter constraint: "Plugin self-contained: NO dependency on
      user-installed external plugins / skills")

---

## 4. Stage 1+2 cross-reference table

| Script | FV-T-1-X claims | Design.md §§ | Open RAID IDs |
|---|---|---|---|
| `hooks/pre-compact.sh` | FV-T-1-7 (timeout/size), FV-T-1-1 (A-001 resume CLI) | §1 T2/T3/T4, §2 (baton write), §3 (gate.lock acquire/release), §5 (allowlist + auto_mode_resumed) | I-018, I-003, A-001 |
| `hooks/stop.sh` | FV-T-1-7 (hook timeout: Stop must not block) | §5 CEO notification ch. step 2, §6 tool matrix | I-015, R-002 |
| `hooks/session-start.sh` | FV-T-1-4 (A-002: SessionStart writes outside CLAUDE_PLUGIN_ROOT) | §1 T1/T8/T11, §3 (reaper), §5 (banner), §6 (Python invariant) | I-014, I-015, I-001, I-003, A-002 |
| `lib/handoff-builder.sh` | FV-T-1-7 (baton size budget) | §2 (restore_prompt, progress_md_anchor, size cap), §5 (allowlist, length cap) | I-018, A-006 (length estimate assumption) |
| `lib/notifier.sh` | (none direct) | §5 CEO notification ch. step 2, §6 tool matrix row osascript | R-002 (guard-tolerant) |
| `lib/baton-writer.sh` | FV-T-1-7 (atomic write: hard kill → os.replace) | §2 (atomic-write protocol, permissions, size cap) | I-018, FV-T-1-7 |
| `lib/gate-lock.sh` | FV-T-1-7 (TTL ≥ 60 s write timeout) | §3 entire section (acquire/release, stale-lock, idempotency) | I-003, I-009 (closed), I-018 |

---

## 5. Build order (dependency graph)

Scripts must be drafted in this order; a later script MUST NOT be drafted until the prior
script's interface is frozen (exit codes, env vars, args):

```text
Wave 0 (pre-condition, from Stage 2 FROZEN):
  auto-resume-daemon-design.md  (frozen; not modified in Stage 3)

Wave 1 (foundational libs — no dependencies on other Stage 3 scripts):
  lib/gate-lock.sh  ──────┐
  lib/baton-writer.sh  ───┤──>  (both are leaf nodes with no Stage 3 deps)
  lib/notifier.sh  ───────┘

Wave 2 (assembly lib — depends on Wave 1 interface contracts):
  lib/handoff-builder.sh  (no lib deps, but its output is consumed by pre-compact.sh)

Wave 3 (hook scripts — depend on Wave 1 + Wave 2 libs):
  hooks/pre-compact.sh  (depends on gate-lock, handoff-builder, baton-writer interfaces)
  hooks/stop.sh  (depends on notifier interface)
  hooks/session-start.sh  (depends on gate-lock interface; reads baton directly)

Wave 4 (integration):
  Stage 3 integration acceptance criteria verified across all 7 scripts
```

Rationale for Wave 1 priority on `lib/gate-lock.sh`: it is the most-depended-on lib (3 hooks
depend on it: pre-compact.sh, session-start.sh, and the future Stage 4 daemon). Freezing its
`acquire|release|reap` subcommand interface first prevents cross-script drift — the dominant
Stage 2 defect class (I-029, I-030).

---

## 6. Open questions deferred to PLAN_AUDIT / EXECUTING

These items MUST NOT be resolved in this PLANNING outline. Stage 3 PLAN_AUDIT (Opus) or
EXECUTING tasks resolve them. Listed here so the PLAN_AUDIT reviewer can confirm they are
addressed in the RD implementation plan.

1. **Hook language convention** (`hooks/*.sh` bash wrapper vs pure Python `.py`): Claude Code
   hooks.json format requires an `executable` path. Both a bash wrapper that exec's Python and
   a pure `.py` with `#!/usr/bin/env python3` shebang can satisfy this. Affects
   hooks/pre-compact.sh, hooks/stop.sh, hooks/session-start.sh. (Cross-ref: I-018 + design.md
   §1 "Hook-script-language constraint")

2. **SessionStart output injection API**: How does a SessionStart hook inject content into the
   resumed session's first message? Claude Code hook docs do not clearly specify stdout vs a
   structured event message vs a file path convention for SessionStart output injection. Must
   verify with Claude Code hook-development documentation before any EXECUTING dispatch.

3. **CLAUDE_SESSION_ID env var availability** per hook type: A-001 validated `claude --resume
   <session_id>` works, but did not verify whether `CLAUDE_SESSION_ID` is injected into
   PreCompact / Stop / SessionStart hook environments by Claude Code. If absent, the fallback
   strategy for populating `baton.session_id` must be defined. (Stage 3 first-dispatch
   discovery task; low-risk but must be confirmed before RD drafts any baton-writing code)

4. **`lib/gate-lock.sh` interface mode** (library vs subprocess): affects whether hooks import
   Python functions or invoke subprocess per lock operation. Decision impacts test strategy and
   error handling across all three hook scripts.

5. **`lib/baton-writer.sh` stdin vs named-file interface**: affects how
   `hooks/pre-compact.sh` passes the assembled JSON payload to the writer.

6. **Stage 3 dogfood instrumentation**: I-023 requires Stage 3 to measure (a) PreCompact
   write→daemon read latency, (b) fault→operator-awareness latency for T-S-4, (c) frequency of
   legitimate operator mid-pause `git checkout` for T-S-3 calibration. These must be designed
   into the Stage 3 EXECUTING task list as explicit measurement tasks, not deferred to Stage 4.

7. **`lib/notifier.sh` bash vs Python**: given notifier.sh performs no filesystem ops (only
   subprocess exec of osascript), I-018's "Python for filesystem ops" rule may not strictly
   apply. PLAN_AUDIT must make an explicit ruling on whether I-018 applies to non-filesystem
   lib scripts.

8. **baton-writer schema validation depth**: whether baton-writer should validate all 7
   required fields (key presence + non-null) or trust the caller. Affects test coverage
   strategy and coupling between pre-compact.sh and baton-writer.sh.

9. **T11 reaper scope in gate-lock.sh**: whether `lib/gate-lock.sh reap` should also quarantine
   `baton.json.tmp` torn files (design.md §2 "Atomic-write protocol") or leave that to the
   caller. Needs explicit decision before RD drafts gate-lock.sh.

10. **governance overhead margin CCB-Light**: Wave Refinement note 1 recommends +10-15%
    governance overhead margin (~265-270 kT effective Stage 3 baseline vs 235 kT baseline).
    This should be proposed as a CCB-Light at PLAN_AUDIT entry per advisor recommendation
    (PROGRESS.md `Last Action` 2026-05-04T09:00+08:00).

---

## 7. Stage 3 EXECUTING handoff notes

When Stage 3 transitions PLANNING → PLAN_AUDIT → EXECUTING, this outline becomes the
scope-locking artifact. Implementation PM MUST:

1. Produce one script per outlined section (no consolidation, no skipping).
2. For each script, satisfy all `- [ ]` acceptance criteria in §2 (or carry remaining items as
   RAID-A with rationale at implementation handback).
3. Resolve the 10 open questions in §6 — either with a design decision (citing rationale) or by
   carrying as RAID-I (with explicit reason implementation can proceed without resolution).
4. Cite design.md section numbers + line numbers inline in commit messages and tasks.md verify
   clauses (NOT just "see design doc" — per dispatch anti-rubber-stamp requirement).
5. Each script passes Sonnet step-review (CEO `step_review_mandatory=true`); integration
   acceptance criteria (§3) pass in a final integration step-review before Stage 3 close.
6. Stage 3 does NOT implement the launchd daemon (`scripts/daemon.py`) — the T5 transition
   (`BATON_WRITTEN → SESSION_RESUMED`) is Stage 4. This is a hard scope boundary.
7. Stage 4 daemon (`scripts/daemon.py`) is a Stage 4 deliverable; design.md §4 plist template
   is FROZEN as its spec.

This outline file (`docs/specs/stage-3-hooks-mvp-outline.md`) SHOULD NOT be deleted at Stage 3
close — it remains the audit trail for "what did Stage 3 EXECUTING agree to deliver."
