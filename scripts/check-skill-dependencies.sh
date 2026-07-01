#!/usr/bin/env bash
set -euo pipefail

# Check Lincoln skill/CLI dependencies.
# Usage:
#   scripts/check-skill-dependencies.sh
#   scripts/check-skill-dependencies.sh --silent

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"
SILENT=false
if [[ "${1:-}" == "--silent" ]]; then
    SILENT=true
fi

DEP_FILE="$ROOT/.claude/skills/dependencies.yaml"
LEGACY_DEP_FILE="$ROOT/.claude/skill-dependencies.yaml"
if [[ ! -f "$DEP_FILE" && -f "$LEGACY_DEP_FILE" ]]; then
    DEP_FILE="$LEGACY_DEP_FILE"
fi

if [[ "$SILENT" == false ]]; then
    echo "==> Validate $(basename "$DEP_FILE")"
fi
"$PYTHON" -c "import yaml; yaml.safe_load(open('$DEP_FILE'))"

if [[ "$SILENT" == false ]]; then
    echo "==> Check declared skills and CLIs"
fi

"$PYTHON" - "$ROOT" "$DEP_FILE" "$SILENT" <<'PY'
import sys
import shutil
from pathlib import Path
import yaml

root = Path(sys.argv[1])
dep_file = Path(sys.argv[2])
silent = sys.argv[3].lower() == "true"

manifest = yaml.safe_load(dep_file.read_text(encoding="utf-8"))

skill_root = Path.home() / ".claude" / "skills"
errors = []
warnings = []
install_commands = []

for name, cfg in manifest.get("skills", {}).items():
    typ = cfg.get("type", "skill")
    is_required = cfg.get("required", True)
    source = cfg.get("source", "")
    if typ == "cli":
        binary = cfg.get("binary", name)
        if not shutil.which(binary):
            msg = f"CLI missing: {binary} (skill: {name})"
            if cfg.get("install"):
                install_commands.append(f"# Install {name}: {cfg['install']}")
            if is_required:
                errors.append(msg)
            else:
                warnings.append(msg)
    else:
        path = cfg.get("path")
        if path:
            expected = root / path / "SKILL.md"
        else:
            expected = skill_root / name / "SKILL.md"
        if not expected.exists():
            msg = f"Skill missing: {name} (expected {expected})"
            if source and source != "inline":
                install_commands.append(f"# Install {name}: git clone {source} {skill_root / name}")
            if is_required:
                errors.append(msg)
            else:
                warnings.append(msg)

if warnings and not silent:
    print("Optional dependencies missing (warnings only):")
    for w in warnings:
        print(f"  - {w}")

if errors and not silent:
    print("Required dependencies missing:")
    for e in errors:
        print(f"  - {e}")

if install_commands and not silent:
    print("")
    print("Suggested installation commands:")
    for cmd in install_commands:
        print(f"  {cmd}")

if errors:
    sys.exit(1)

if not silent:
    print("All declared skills/CLIs are present.")
PY

if [[ "$SILENT" == false ]]; then
    echo "==> All skill dependencies satisfied"
fi
