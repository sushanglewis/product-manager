#!/usr/bin/env bash
set -euo pipefail

# PostToolUse hook for Lincoln workflow.
# Tracks artifacts produced by side-effect tools in the workflow state file.
#
# Usage (manual):
#   .claude/hooks/post-tool-use.sh "Write" '{"file_path": "foo.md"}' 0
#
# Expected arguments:
#   $1: tool name
#   $2: JSON-encoded tool arguments
#   $3: tool exit code

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
EXIT_CODE="${3:-0}"
STATE_FILE="${LINCOLN_STATE_FILE:-$ROOT/.claude/workflow-state.yaml}"

# Only track successful side-effect tool uses
if [[ "$EXIT_CODE" != "0" ]]; then
    exit 0
fi

if [[ ! -f "$STATE_FILE" ]]; then
    exit 0
fi

SIDE_EFFECT_TOOLS=(
    "Bash"
    "Edit"
    "Write"
    "mcp__pencil__batch_design"
    "mcp__pencil__export_nodes"
    "mcp__pencil__export_html"
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

if ! is_side_effect "$TOOL_NAME"; then
    exit 0
fi

"$PYTHON" "$ROOT/scripts/track-artifacts.py" \
    --state-file "$STATE_FILE" \
    --tool "$TOOL_NAME" \
    --args "$TOOL_ARGS" \
    --project-root "$ROOT" \
    2>/dev/null || true

# Trace logging: record key tool invocations to lincoln-trace.jsonl
# Do not fail the hook if trace write fails; log to stderr and continue.
TRACE_DIR="$ROOT/.omc/state"
TRACE_FILE="$TRACE_DIR/lincoln-trace.jsonl"

# Determine if this tool should be traced
TRACE=false
TARGET=""
if [[ "$TOOL_NAME" == "Skill" ]]; then
    TRACE=true
    # Extract skill name from JSON args
    SKILL_NAME=$(echo "$TOOL_ARGS" | "$PYTHON" -c "import sys,json; d=json.load(sys.stdin); print(d.get('skill',''))" 2>/dev/null || echo "")
    SKILL_ARGS=$(echo "$TOOL_ARGS" | "$PYTHON" -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d.get('args','')))" 2>/dev/null || echo "")
    TARGET="skill:$SKILL_NAME"
    TRACE_JSON=$(cat <<EOF
{"tool": "Skill", "skill": "$SKILL_NAME", "args": $SKILL_ARGS, "stage": "STAGE_PLACEHOLDER", "timestamp": "TIMESTAMP_PLACEHOLDER"}
EOF
)
elif [[ "$TOOL_NAME" == "Write" || "$TOOL_NAME" == "Edit" || "$TOOL_NAME" == "Bash" ]]; then
    TRACE=true
    if [[ "$TOOL_NAME" == "Bash" ]]; then
        TARGET=$(echo "$TOOL_ARGS" | "$PYTHON" -c "import sys,json; d=json.load(sys.stdin); print(d.get('command','')[:80])" 2>/dev/null || echo "bash")
    else
        TARGET=$(echo "$TOOL_ARGS" | "$PYTHON" -c "import sys,json; d=json.load(sys.stdin); print(d.get('file_path',''))" 2>/dev/null || echo "")
    fi
    TRACE_JSON=$(cat <<EOF
{"tool": "$TOOL_NAME", "target": "$TARGET", "stage": "STAGE_PLACEHOLDER", "timestamp": "TIMESTAMP_PLACEHOLDER"}
EOF
)
fi

if [[ "$TRACE" == true ]]; then
    # Read current stage from workflow state
    CURRENT_STAGE=$("$PYTHON" - "$STATE_FILE" <<'PY' 2>/dev/null
import sys, yaml
path = sys.argv[1]
state = yaml.safe_load(open(path, encoding="utf-8"))
print(state.get("current_run", {}).get("current_stage") or "unknown")
PY
) || CURRENT_STAGE="unknown"

    TIMESTAMP=$("$PYTHON" -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))" 2>/dev/null) || TIMESTAMP=""

    # Replace placeholders
    TRACE_LINE=$(echo "$TRACE_JSON" | sed "s/STAGE_PLACEHOLDER/$CURRENT_STAGE/g; s/TIMESTAMP_PLACEHOLDER/$TIMESTAMP/g")

    # Ensure directory exists and append
    mkdir -p "$TRACE_DIR" 2>/dev/null || true
    echo "$TRACE_LINE" >> "$TRACE_FILE" 2>/dev/null || echo "[lincoln-trace] Failed to write trace entry" >&2
fi

exit 0
