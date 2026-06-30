#!/usr/bin/env bash
set -euo pipefail

# On-session-start hook for Lincoln workflow.
# Loads and prints the current stage context so the Agent sees it immediately.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ -x "$ROOT/.venv/bin/python3" ]; then
    PYTHON="$ROOT/.venv/bin/python3"
elif [ -x "$ROOT/venv/bin/python3" ]; then
    PYTHON="$ROOT/venv/bin/python3"
else
    PYTHON="python3"
fi

STATE_FILE="${LINCOLN_STATE_FILE:-$ROOT/.claude/workflow-state.yaml}"

# Reset any stale task-tool burst counter from a previous session so a fresh
# conversation does not start already throttled.
rm -f "$ROOT/.context/task-tool-burst.json"

if [[ ! -f "$STATE_FILE" ]]; then
    exit 0
fi

# Read current stage
CURRENT_STAGE=$("$PYTHON" - "$STATE_FILE" <<'PY'
import sys
import yaml
path = sys.argv[1]
state = yaml.safe_load(open(path, encoding="utf-8"))
print(state.get("current_run", {}).get("current_stage") or "not_started")
PY
)

echo ""
echo "=== Lincoln Stage Context ==="
echo "Current stage: $CURRENT_STAGE"
echo ""

if [[ "$CURRENT_STAGE" != "not_started" ]]; then
    "$PYTHON" "$ROOT/scripts/stage_loader.py" \
        --stage "$CURRENT_STAGE" \
        --action load \
        --state-file "$STATE_FILE" \
        2>/dev/null || echo "[Could not load stage context for $CURRENT_STAGE]"
fi

echo "=== End Stage Context ==="
echo ""

# Run lincoln-status.py for a comprehensive summary at the end of startup
STATUS_OUTPUT=$("$PYTHON" "$ROOT/scripts/lincoln-status.py" --format markdown 2>/dev/null) || STATUS_OUTPUT=""
if [[ -n "$STATUS_OUTPUT" ]]; then
    echo "=== Lincoln Status Summary ==="
    echo "$STATUS_OUTPUT"
    echo "=== End Lincoln Status Summary ==="
    echo ""
else
    echo "[Lincoln status summary unavailable. Run manually: python3 scripts/lincoln-status.py --format markdown]"
    echo ""
fi

exit 0
