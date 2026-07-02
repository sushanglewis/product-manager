#!/usr/bin/env bash
set -euo pipefail

# on-pr-event.sh
# Helper invoked by post-tool-use.sh or Stop hook when a PR/branch sync event is detected.
# Updates workflow-stage.yaml with append-only node record.
#
# Usage:
#   .claude/hooks/on-pr-event.sh <event> [<node-id>] [<status>]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ -x "$ROOT/.venv/bin/python3" ]; then
    PYTHON="$ROOT/.venv/bin/python3"
elif [ -x "$ROOT/venv/bin/python3" ]; then
    PYTHON="$ROOT/venv/bin/python3"
else
    PYTHON="python3"
fi

EVENT="${1:-}"
NODE_ID="${2:-implement}"
STATUS="${3:-pr_submitted}"

if [[ -z "$EVENT" ]]; then
    exit 0
fi

"$PYTHON" "$ROOT/scripts/stage_loader.py" \
    --action append-node \
    --node-id "$NODE_ID" \
    --status "$STATUS" \
    2>/dev/null || true

exit 0
