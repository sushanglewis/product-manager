#!/usr/bin/env bash
set -euo pipefail

# PreToolUse hook for Lincoln workflow.
# Blocks side-effect tools when the current stage has not passed entry checks
# or is paused/waiting_for_human/validation_failed.
#
# Usage (manual):
#   .claude/hooks/pre-tool-use.sh "Write" '{"file_path": "foo.md"}'
#
# Expected arguments:
#   $1: tool name (e.g. Bash, Write, Edit, mcp__pencil__batch_design)
#   $2: JSON-encoded tool arguments

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ -x "$ROOT/.venv/bin/python3" ]; then
    PYTHON="$ROOT/.venv/bin/python3"
elif [ -x "$ROOT/venv/bin/python3" ]; then
    PYTHON="$ROOT/venv/bin/python3"
else
    PYTHON="python3"
fi

TOOL_NAME="${1:-}"
TOOL_ARGS="${2:-}"
STATE_FILE="${LINCOLN_STATE_FILE:-$ROOT/.claude/workflow-stage.yaml}"
LEGACY_STATE_FILE="$ROOT/.claude/workflow-state.yaml"

if [[ ! -f "$STATE_FILE" && -f "$LEGACY_STATE_FILE" ]]; then
    STATE_FILE="$LEGACY_STATE_FILE"
fi

# If state file does not exist, allow everything (not a Lincoln project or not initialized)
if [[ ! -f "$STATE_FILE" ]]; then
    exit 0
fi

# Read current stage and status using Python for reliable YAML parsing
read_state() {
    "$PYTHON" - "$STATE_FILE" <<'PY'
import sys
import yaml
path = sys.argv[1]
state = yaml.safe_load(open(path, encoding="utf-8"))
current = state.get("current_run", {}).get("current_stage") or "not_started"
# New schema: derive status from latest node; legacy schema: from stages map.
nodes = state.get("nodes")
if nodes:
    stage_state = nodes[-1]
elif "stages" in state and current in state["stages"]:
    stage_state = state["stages"][current]
else:
    stage_state = {}
status = stage_state.get("status") or "not_started"
print(current)
print(status)
PY
}

STATE_OUTPUT=$(read_state)
CURRENT_STAGE=$(echo "$STATE_OUTPUT" | sed -n '1p')
STAGE_STATUS=$(echo "$STATE_OUTPUT" | sed -n '2p')

# Task-tool guard: prevent TaskCreate/TaskUpdate from being used as
# placeholders for user messages in dialogue stages, and cap consecutive
# task-tool calls everywhere else.  This is invoked for every tool so it can
# reset the burst counter on non-task actions.
"$PYTHON" "$ROOT/scripts/task_tool_guard.py" \
    --state-file "$STATE_FILE" \
    --tool-name "$TOOL_NAME" \
    --tool-args "$TOOL_ARGS"

# Define side-effect tools
SIDE_EFFECT_TOOLS=(
    "Bash"
    "Edit"
    "Write"
    "NotebookEdit"
    "mcp__pencil__batch_design"
    "mcp__pencil__export_nodes"
    "mcp__pencil__export_html"
    "mcp__plugin_ecc_github__create_issue"
    "mcp__plugin_ecc_github__create_pull_request"
    "mcp__plugin_ecc_github__merge_pull_request"
)

is_side_effect() {
    local tool="$1"
    for t in "${SIDE_EFFECT_TOOLS[@]}"; do
        if [[ "$tool" == "$t" ]]; then
            return 0
        fi
    done
    return 1
}

# Block side-effect tools when entry checks have not passed
if [[ "$STAGE_STATUS" == "not_started" || "$STAGE_STATUS" == "entry_validating" ]]; then
    if is_side_effect "$TOOL_NAME"; then
        echo "BLOCKED: Entry checks for stage '$CURRENT_STAGE' have not passed yet." >&2
        echo "Run: python scripts/stage_loader.py --stage $CURRENT_STAGE --action validate-entry" >&2
        exit 1
    fi
fi

# When paused/waiting_for_human/validation_failed, only allow read-only tools
if [[ "$STAGE_STATUS" == "paused" || "$STAGE_STATUS" == "waiting_for_human" || "$STAGE_STATUS" == "validation_failed" ]]; then
    if [[ "$TOOL_NAME" != "Read" && "$TOOL_NAME" != "Grep" && "$TOOL_NAME" != "Glob" ]]; then
        echo "BLOCKED: Stage '$CURRENT_STAGE' is $STAGE_STATUS. Only Read/Grep/Glob allowed." >&2
        echo "To resume: run the stage's skill command or call workflow-continue." >&2
        exit 1
    fi
fi

# Exit gate check: block side-effect tools that would advance to the next stage
# if the current stage's exit gate has not been approved.
if is_side_effect "$TOOL_NAME"; then
    GATE_STATUS=$("$PYTHON" "$ROOT/scripts/stage_loader.py" \
        --stage "$CURRENT_STAGE" \
        --action validate-exit \
        2>/dev/null | grep -c "^PASS:" || echo "0")
    # For now, only warn rather than block to avoid breaking legitimate edits.
    if [[ "$GATE_STATUS" == "0" && "$TOOL_NAME" != "Read" ]]; then
        echo "[Lincoln] Warning: exit gate for '$CURRENT_STAGE' is not yet approved." >&2
        echo "[Lincoln] Run 'python scripts/stage_loader.py --stage $CURRENT_STAGE --action validate-exit' to check." >&2
    fi
fi

exit 0
