#!/usr/bin/env bash
set -euo pipefail

# List all active Lincoln feature branches and their current stage state.
#
# Usage:
#   scripts/list-active-lincoln-branches.sh [--waiting-for-me <role>]
#
# Options:
#   --waiting-for-me <role>  Filter by waiting_for role (pm|agent|agent-fix|next-role)
#
# Output:
#   Calls lincoln-status.py --format table for each remote lincoln/* branch.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

REMOTE="${1:-origin}"
FILTER_ROLE=""

# Parse optional --waiting-for-me flag
while [[ $# -gt 0 ]]; do
    case "$1" in
        --waiting-for-me)
            FILTER_ROLE="$2"
            shift 2
            ;;
        *)
            REMOTE="$1"
            shift
            ;;
    esac
done

echo "==> Fetching remote branches from $REMOTE"
git fetch "$REMOTE" 'lincoln/*:refs/remotes/'"$REMOTE"'/lincoln/*' 2>/dev/null || true

BRANCHES=$(git branch -r --list "$REMOTE/lincoln/*" 2>/dev/null || true)

if [[ -z "$BRANCHES" ]]; then
    echo "No active Lincoln branches found."
    exit 0
fi

echo ""

for ref in $BRANCHES; do
    # Extract branch name without remote prefix
    branch="${ref#$REMOTE/}"

    # Call lincoln-status.py for this branch
    status_json=$(git show "$ref:.claude/workflow-state.yaml" 2>/dev/null | \
        python3 "$ROOT/scripts/lincoln-status.py" --format json --state-file /dev/stdin 2>/dev/null || true)

    if [[ -z "$status_json" ]]; then
        printf "%-50s %-22s %-20s %-15s\n" "$branch" "unknown" "no-state-file" ""
        continue
    fi

    # Extract fields using Python
    python3 - "$branch" "$status_json" "$FILTER_ROLE" <<'PY'
import json
import sys

branch, raw, filter_role = sys.argv[1:4]
data = json.loads(raw)

stage_id = data.get("current_stage") or "unknown"
stage_status = data.get("stage_status") or "unknown"
waiting_for = data.get("waiting_for") or ""

if filter_role and waiting_for != filter_role:
    sys.exit(0)

print(f"{branch:50} {stage_id:22} {stage_status:20} {waiting_for:15}")
PY
done
