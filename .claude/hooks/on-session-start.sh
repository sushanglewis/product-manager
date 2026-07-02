#!/usr/bin/env bash
set -euo pipefail

# On-session-start hook for Lincoln workflow.
# Loads stage context, checks dependencies, parses workflow-stage.yaml,
# reads previous node handoff, and injects current node driving context.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ -x "$ROOT/.venv/bin/python3" ]; then
    PYTHON="$ROOT/.venv/bin/python3"
elif [ -x "$ROOT/venv/bin/python3" ]; then
    PYTHON="$ROOT/venv/bin/python3"
else
    PYTHON="python3"
fi

STATE_FILE="$ROOT/.claude/workflow-stage.yaml"
LEGACY_STATE_FILE="$ROOT/.claude/workflow-state.yaml"

# Reset any stale task-tool burst counter from a previous session
rm -f "$ROOT/.context/task-tool-burst.json"

echo ""
echo "=== Lincoln Session Start ==="
echo ""

# 1. Dependency check (detect + prompt, do not auto-install)
if [[ -f "$ROOT/.claude/skills/dependencies.yaml" ]]; then
    echo "[Lincoln] Checking dependencies..."
    "$PYTHON" "$ROOT/scripts/check-skill-dependencies.sh" --silent 2>/dev/null || true
    echo ""
fi

# 2. Determine state file (new workflow-stage.yaml preferred, legacy fallback)
if [[ ! -f "$STATE_FILE" && -f "$LEGACY_STATE_FILE" ]]; then
    STATE_FILE="$LEGACY_STATE_FILE"
fi

if [[ ! -f "$STATE_FILE" ]]; then
    echo "No Lincoln state file found ($STATE_FILE)."
    echo "Run: scripts/init-lincoln-branch.sh <session-id> <design-id> --push"
    echo "=== End Lincoln Session Start ==="
    echo ""
    exit 0
fi

# 3. Read current stage and node info
STATE_JSON=$("$PYTHON" - "$STATE_FILE" <<'PY'
import sys, yaml, json
state = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
current = state.get("current_run", {}).get("current_stage") or "not_started"
status = state.get("current_run", {}).get("status") or "not_started"
workflow_name = state.get("workflow", {}).get("name") or "unknown"
workflow_template = state.get("workflow", {}).get("template") or workflow_name
nodes = state.get("nodes", [])
last_node = nodes[-1] if nodes else {}
waiting_for = last_node.get("status") if last_node else None
if waiting_for in ("completed", "merged"):
    waiting_for = "next_stage"
variables = state.get("current_run", {}).get("variables", {})
print(json.dumps({
    "current_stage": current,
    "status": status,
    "workflow_name": workflow_name,
    "workflow_template": workflow_template,
    "last_node": last_node,
    "waiting_for": waiting_for,
    "session_id": variables.get("session_id", ""),
    "design_id": variables.get("design_id", ""),
}))
PY
)

CURRENT_STAGE=$(echo "$STATE_JSON" | "$PYTHON" -c "import sys,json; print(json.load(sys.stdin)['current_stage'])")
STATUS=$(echo "$STATE_JSON" | "$PYTHON" -c "import sys,json; print(json.load(sys.stdin)['status'])")
WORKFLOW_NAME=$(echo "$STATE_JSON" | "$PYTHON" -c "import sys,json; print(json.load(sys.stdin)['workflow_name'])")
WORKFLOW_TEMPLATE=$(echo "$STATE_JSON" | "$PYTHON" -c "import sys,json; print(json.load(sys.stdin)['workflow_template'])")
LAST_NODE=$(echo "$STATE_JSON" | "$PYTHON" -c "import sys,json; print(json.dumps(json.load(sys.stdin)['last_node']))")
WAITING_FOR=$(echo "$STATE_JSON" | "$PYTHON" -c "import sys,json; print(json.load(sys.stdin)['waiting_for'] or 'none')")
SESSION_ID=$(echo "$STATE_JSON" | "$PYTHON" -c "import sys,json; print(json.load(sys.stdin)['session_id'])")
DESIGN_ID=$(echo "$STATE_JSON" | "$PYTHON" -c "import sys,json; print(json.load(sys.stdin)['design_id'])")

echo "Workflow: $WORKFLOW_NAME ($WORKFLOW_TEMPLATE)"
echo "Current stage: $CURRENT_STAGE"
echo "Stage status: $STATUS"
echo "Session ID: ${SESSION_ID:-(unset)}"
echo "Design ID: ${DESIGN_ID:-(unset)}"
echo "Waiting for: $WAITING_FOR"
echo ""

# 4. Load stage context files
if [[ "$CURRENT_STAGE" != "not_started" && -d "$ROOT/.claude/stages/$CURRENT_STAGE" ]]; then
    echo "=== Stage Context ==="
    for f in AGENTS.md CHECKLIST.md SKILLS.md PROMPT.md; do
        file="$ROOT/.claude/stages/$CURRENT_STAGE/$f"
        if [[ -f "$file" ]]; then
            echo ""
            echo "--- $f ---"
            cat "$file"
        fi
    done
    echo ""
    echo "=== End Stage Context ==="
    echo ""
fi

# 5. Read last node handoff
HANDOFF_FILE=""
if [[ "$LAST_NODE" != "{}" ]]; then
    HANDOFF_FILE=$(echo "$LAST_NODE" | "$PYTHON" -c "import sys,json; print(json.load(sys.stdin).get('handoff_file',''))" 2>/dev/null || echo "")
fi

if [[ -n "$HANDOFF_FILE" && -f "$ROOT/$HANDOFF_FILE" ]]; then
    echo "=== Last Node Handoff ==="
    cat "$ROOT/$HANDOFF_FILE"
    echo ""
    echo "=== End Handoff ==="
    echo ""
fi

# 6. Run status summary
STATUS_OUTPUT=$("$PYTHON" "$ROOT/scripts/lincoln-status.py" --format markdown 2>/dev/null) || STATUS_OUTPUT=""
if [[ -n "$STATUS_OUTPUT" ]]; then
    echo "=== Lincoln Status Summary ==="
    echo "$STATUS_OUTPUT"
    echo "=== End Lincoln Status Summary ==="
    echo ""
fi

echo "=== End Lincoln Session Start ==="
echo ""

exit 0
