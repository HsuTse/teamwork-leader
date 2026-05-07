#!/usr/bin/env bash
# tools/claude-stub.sh — Stub claude binary for GHA measurement environment.
#
# GHA macOS runners do not have claude CLI installed. daemon.py T5 actor
# attempts to spawn "claude --resume <session_id> -p <prompt>" and uses
# proc.wait(timeout=2.0) to detect immediate failure.
#
# This stub sleeps 3 seconds so the 2-second wait() times out (TimeoutExpired
# is treated as exit_code=0 = success in daemon.py), allowing T5 to write
# gate_state=SESSION_RESUMED and complete the latency measurement.
#
# Installation (in GHA workflow before daemon install):
#   mkdir -p "$HOME/.local/bin"
#   cp tools/claude-stub.sh "$HOME/.local/bin/claude"
#   chmod +x "$HOME/.local/bin/claude"
#   echo "$HOME/.local/bin" >> "$GITHUB_PATH"

sleep 3
exit 0
