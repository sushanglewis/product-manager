#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Prefer project venv if available; otherwise rely on system python3 having pytest/pyyaml.
if [ -d "$ROOT/.venv" ] && [ -x "$ROOT/.venv/bin/python3" ]; then
    PYTHON="$ROOT/.venv/bin/python3"
elif [ -d "$ROOT/venv" ] && [ -x "$ROOT/venv/bin/python3" ]; then
    PYTHON="$ROOT/venv/bin/python3"
else
    PYTHON="python3"
fi

echo "==> Validate workflow YAML"
"$PYTHON" -c "import yaml; yaml.safe_load(open('.claude/workflows/interview-to-knowledge.yaml'))"

echo "==> Validate skill manifests"
for skill in .claude/skills/*/SKILL.md; do
    [ -f "$skill" ] || continue
    "$PYTHON" - "$skill" <<'PY'
import sys, yaml
path = sys.argv[1]
text = open(path, encoding="utf-8").read()
if text.startswith("---"):
    end = text.find("---", 3)
    if end != -1:
        frontmatter = text[3:end]
        try:
            yaml.safe_load(frontmatter)
        except Exception as exc:
            print(f"Invalid frontmatter in {path}: {exc}")
            sys.exit(1)
print(f"OK: {path}")
PY
    if [ $? -ne 0 ]; then
        exit 1
    fi
done

echo "==> Validate skill dependency manifest"
DEP_FILE=".claude/skills/dependencies.yaml"
if [ ! -f "$DEP_FILE" ]; then
    DEP_FILE=".claude/skill-dependencies.yaml"
fi
"$PYTHON" -c "import yaml; yaml.safe_load(open('$DEP_FILE'))"

if [ -x "scripts/check-skill-dependencies.sh" ]; then
    echo "==> Check skill dependencies (non-blocking)"
    bash scripts/check-skill-dependencies.sh || true
fi

echo "==> Validate workflow templates"
"$PYTHON" - "$ROOT" <<'PY'
import sys
from pathlib import Path
import yaml

root = Path(sys.argv[1])
templates_dir = root / ".claude" / "workflows" / "templates"
errors = []
for path in templates_dir.glob("*.yaml"):
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{path.name}: YAML parse error: {exc}")
        continue
    workflow = data.get("workflow", data)
    for step in workflow.get("steps", []):
        stage_id = step.get("id")
        if not stage_id:
            errors.append(f"{path.name}: step missing id")
            continue
        stage_dir = root / ".claude" / "stages" / stage_id
        if not stage_dir.exists():
            errors.append(f"{path.name}: missing stage directory {stage_dir}")

if errors:
    print("Workflow template issues:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)

print("All workflow templates reference valid stage directories.")
PY

echo "==> Validate JSON schemas are valid JSON"
"$PYTHON" - "$ROOT" <<'PY'
import sys, json
from pathlib import Path
root = Path(sys.argv[1])
errors = []
for schema_path in (root / ".claude" / "schemas").glob("*.json"):
    try:
        json.loads(schema_path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{schema_path.name}: {exc}")
if errors:
    print("Invalid JSON schemas:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
print("All JSON schemas are valid.")
PY

echo "==> Validate agent frontmatters"
"$PYTHON" - "$ROOT" <<'PY'
import sys, yaml
from pathlib import Path

root = Path(sys.argv[1])
errors = []
for agent_md in (root / ".claude" / "agents").glob("*.md"):
    text = agent_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        errors.append(f"{agent_md.name}: missing frontmatter")
        continue
    end = text.find("---", 3)
    if end == -1:
        errors.append(f"{agent_md.name}: unterminated frontmatter")
        continue
    try:
        fm = yaml.safe_load(text[3:end])
    except Exception as exc:
        errors.append(f"{agent_md.name}: invalid frontmatter: {exc}")
        continue
    if not isinstance(fm, dict):
        errors.append(f"{agent_md.name}: frontmatter is not a mapping")
        continue
    for key in ["name", "description"]:
        if key not in fm:
            errors.append(f"{agent_md.name}: missing {key}")
if errors:
    print("Agent frontmatter issues:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
print("All agent frontmatters valid.")
PY

echo "==> Validate Python syntax"
"$PYTHON" -m py_compile scripts/validate_stage.py

echo "==> Validate prompt paths in skills"
"$PYTHON" - "$ROOT" <<'PY'
import sys
from pathlib import Path

root = Path(sys.argv[1])
missing = []
for skill_dir in (root / ".claude" / "skills").iterdir():
    if not skill_dir.is_dir():
        continue
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        continue
    text = skill_md.read_text(encoding="utf-8")
    # Only enforce prompts/main.md when the skill explicitly declares it as entry
    if "prompts/main.md" not in text:
        continue
    main_prompt = skill_dir / "prompts" / "main.md"
    if not main_prompt.exists():
        missing.append(str(main_prompt))
if missing:
    print("Missing prompts:")
    for m in missing:
        print(f"  - {m}")
    sys.exit(1)
print("All prompt paths resolved.")
PY

echo "==> Validate workflow-stage.yaml schema"
"$PYTHON" - "$ROOT" <<'PY'
import sys
from pathlib import Path
import yaml

root = Path(sys.argv[1])
state_file = root / ".claude" / "workflow-stage.yaml"
legacy_state_file = root / ".claude" / "workflow-state.yaml"
if not state_file.exists() and legacy_state_file.exists():
    state_file = legacy_state_file

if not state_file.exists():
    print("workflow-stage.yaml not found; skipping")
    sys.exit(0)

state = yaml.safe_load(state_file.read_text(encoding="utf-8"))
required_top_legacy = ["schema_version", "workflow", "current_run", "stages", "recovery"]
required_top_new = ["schema_version", "workflow", "current_run", "nodes", "recovery"]
if "nodes" in state:
    missing = [k for k in required_top_new if k not in state]
elif "stages" in state:
    missing = [k for k in required_top_legacy if k not in state]
else:
    missing = [k for k in required_top_new if k not in state]
if missing:
    print(f"Missing top-level keys: {', '.join(missing)}")
    sys.exit(1)

print("workflow-stage.yaml schema valid.")
PY

echo "==> Validate stage directories are complete"
"$PYTHON" - "$ROOT" <<'PY'
import sys
from pathlib import Path
import yaml

root = Path(sys.argv[1])
workflow = yaml.safe_load((root / ".claude" / "workflows" / "interview-to-knowledge.yaml").read_text(encoding="utf-8"))

missing = []
for step in workflow["workflow"]["steps"]:
    stage_dir = root / ".claude" / "stages" / step["id"]
    if not stage_dir.exists():
        missing.append(f"Missing directory: {stage_dir}")
        continue
    for file in ["AGENTS.md", "CHECKLIST.md", "SKILLS.md", "PROMPT.md"]:
        if not (stage_dir / file).exists():
            missing.append(f"Missing {file} in {stage_dir}")

if missing:
    print("Incomplete stage directories:")
    for m in missing:
        print(f"  - {m}")
    sys.exit(1)
print("All stage directories complete.")
PY

echo "==> Validate stage-manifest.yaml schema"
"$PYTHON" - "$ROOT" <<'PY'
import sys
from pathlib import Path
import yaml
import json

root = Path(sys.argv[1])
schema = json.load(open(root / ".claude" / "schemas" / "stage-definition.schema.json"))
manifest = yaml.safe_load(open(root / ".claude" / "stages" / "stage-manifest.yaml").read())

# Minimal schema validation: check stages is a list with required keys
if "stages" not in manifest or not isinstance(manifest["stages"], list):
    print("stage-manifest.yaml missing stages list")
    sys.exit(1)

for stage in manifest["stages"]:
    for key in ["id", "name", "description", "human_gate", "template", "prerequisite_stage", "required_artifacts", "required_skills", "context_files", "next_stage"]:
        if key not in stage:
            print(f"Stage {stage.get('id', '?')} missing key: {key}")
            sys.exit(1)
    if "gates" not in stage:
        print(f"Stage {stage['id']} missing gates")
        sys.exit(1)

print("stage-manifest.yaml schema valid.")
PY

echo "==> Validate hook scripts are executable"
for hook in "$ROOT/.claude/hooks/"*.sh; do
    if [ -f "$hook" ] && [ ! -x "$hook" ]; then
        echo "Hook not executable: $hook"
        exit 1
    fi
done
echo "All hooks executable."

echo "==> Validate Python syntax for scripts"
"$PYTHON" -m py_compile scripts/stage_loader.py
"$PYTHON" -m py_compile scripts/lincoln-status.py
"$PYTHON" -m py_compile scripts/track-artifacts.py
"$PYTHON" -m py_compile scripts/task_tool_guard.py
"$PYTHON" -m py_compile scripts/validate_stage.py

echo "==> Validate bash syntax for scripts"
bash -n scripts/init-lincoln-branch.sh
bash -n scripts/init-project.sh
bash -n scripts/list-active-lincoln-branches.sh
bash -n scripts/check-skill-dependencies.sh
bash -n scripts/sync-external-agents.sh
for hook in "$ROOT/.claude/hooks/"*.sh; do
    bash -n "$hook"
done

echo "==> Run pytest"
"$PYTHON" -m pytest tests/ -v

echo "==> All static checks passed"
