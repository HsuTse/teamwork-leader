#!/bin/bash
TASK_ID="$1"
[ -z "$TASK_ID" ] && { echo "usage: _write_header.sh <task-id>" >&2; exit 1; }
cat <<HDR
# task: ${TASK_ID}
# date: $(date -Iseconds)
# claude_version: $(claude --version 2>/dev/null || echo "unknown")
# branch: $(git rev-parse --abbrev-ref HEAD)
HDR
