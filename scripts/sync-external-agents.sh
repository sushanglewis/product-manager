#!/usr/bin/env bash
set -euo pipefail

# Sync external agent definitions from everything-claude-code / oh-my-claude-code.
# Usage:
#   scripts/sync-external-agents.sh
#   scripts/sync-external-agents.sh --dry-run

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
fi

AGENTS_DIR="$ROOT/.claude/agents/external"
mkdir -p "$AGENTS_DIR"

"$ROOT/.venv/bin/python3" - "$AGENTS_DIR" "$DRY_RUN" <<'PY'
import sys
from pathlib import Path
import yaml

agents_dir = Path(sys.argv[1])
dry_run = sys.argv[2].lower() == "true"

for manifest_path in agents_dir.glob("*.manifest.yaml"):
    docs = list(yaml.safe_load_all(manifest_path.read_text(encoding="utf-8")))
    data = docs[0] if docs else None
    if not isinstance(data, dict):
        print(f"Skipping {manifest_path.name}: invalid manifest")
        continue

    framework = manifest_path.stem.replace(".manifest", "")
    source = data.get("source", "")
    ref = data.get("ref", "main") or "main"
    agents_subdir = data.get("paths", {}).get("agents", ".claude/agents")

    if not source:
        print(f"Skipping {manifest_path.name}: no source declared")
        continue

    target_dir = agents_dir / framework
    print(f"Syncing {framework} from {source} @ {ref}")

    if dry_run:
        print(f"  [dry-run] Would clone/sparse-checkout into {target_dir}")
        continue

    import shutil
    import subprocess

    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    try:
        subprocess.run(
            [
                "git", "clone", "--depth", "1", "--branch", ref,
                "--filter=blob:none", "--sparse", source, str(target_dir),
            ],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "sparse-checkout", "set", agents_subdir],
            cwd=target_dir,
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        print(f"  Failed to sync {framework}: {exc}")
        if exc.stderr:
            print(exc.stderr.decode("utf-8", errors="replace"))

print("External agent sync complete.")
PY
