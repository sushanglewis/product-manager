#!/usr/bin/env bash
set -euo pipefail

# On-stop hook for Lincoln workflow.
# Updates last_updated_at in the workflow stage file when a session ends.
#
# The state file is branch-scoped: .claude/workflow-stage.yaml
# (falls back to legacy .claude/workflow-state.yaml if present).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ -x "$ROOT/.venv/bin/python3" ]; then
    PYTHON="$ROOT/.venv/bin/python3"
elif [ -x "$ROOT/venv/bin/python3" ]; then
    PYTHON="$ROOT/venv/bin/python3"
else
    PYTHON="python3"
fi

STATE_FILE="${LINCOLN_STATE_FILE:-$ROOT/.claude/workflow-stage.yaml}"
LEGACY_STATE_FILE="$ROOT/.claude/workflow-state.yaml"

if [[ ! -f "$STATE_FILE" && -f "$LEGACY_STATE_FILE" ]]; then
    STATE_FILE="$LEGACY_STATE_FILE"
fi

if [[ ! -f "$STATE_FILE" ]]; then
    exit 0
fi

"$PYTHON" - "$STATE_FILE" <<'PY'
import sys
from datetime import datetime, timezone
import yaml

path = sys.argv[1]
state = yaml.safe_load(open(path, encoding="utf-8"))
state["current_run"]["last_updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
with open(path, "w", encoding="utf-8") as f:
    yaml.dump(state, f, allow_unicode=True, sort_keys=False)
PY

exit 0
