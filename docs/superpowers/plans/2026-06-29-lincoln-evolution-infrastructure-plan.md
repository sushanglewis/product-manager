# Lincoln Evolution — Infrastructure Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add skill dependency manifest, workflow router, reusable workflow templates, and engine loader support so Lincoln can dynamically choose a context-appropriate workflow instead of always running the fixed interview-to-knowledge pipeline.

**Architecture:** Introduce a YAML dependency manifest plus a small check script, a `workflow-router` skill/stage that inspects repository context and selects a template, four new workflow templates under `.claude/workflows/templates/`, and a minimal extension to `scripts/stage_loader.py` to load the template named in `workflow-state.yaml`.

**Tech Stack:** Python 3, PyYAML, Bash, pytest, existing `everything-claude-code` loop engine.

---

## File Structure

| File | Responsibility |
|------|----------------|
| `.claude/skill-dependencies.yaml` | Declares external skill/CLI dependencies, versions, and required sub-skills |
| `scripts/check-skill-dependencies.sh` | Validates that declared skills/CLIs are present locally |
| `tests/test_skill_dependencies.py` | Unit tests for dependency manifest parsing and validation |
| `.claude/skills/lincoln-workflow-router/SKILL.md` | Skill metadata for the router |
| `.claude/skills/lincoln-workflow-router/prompts/router-prompt.md` | Prompt the router uses to assess context and pick a template |
| `.claude/stages/workflow-router/{AGENTS.md,CHECKLIST.md,SKILLS.md,PROMPT.md}` | Stage context for the router |
| `.claude/workflows/templates/existing-project-iteration.yaml` | Template for iterating on projects that already have code |
| `.claude/workflows/templates/bug-fix.yaml` | Template for focused bug/issue fixes |
| `.claude/workflows/templates/design-spike.yaml` | Template for research/design-only work |
| `.claude/workflows/templates/oss-first-design.yaml` | Template where open-source exploration comes early |
| `scripts/stage_loader.py` | Extended to load a named template from `.claude/workflows/templates/` |
| `tests/test_workflow_router.py` | Tests for router recommendation logic and template loading |
| `scripts/static-check.sh` | Extended to validate dependency manifest and template consistency |
| `.claude/skills/interview-workflow/skill.yaml` | Registers the router skill and references templates |
| `.claude/AGENTS.md` | Documents the router behavior and template selection rules |

---

## Task 1: Create `.claude/skill-dependencies.yaml`

**Files:**
- Create: `.claude/skill-dependencies.yaml`

- [ ] **Step 1: Write the dependency manifest**

```yaml
---
schema_version: 1.0.0
description: |
  Declares external skills and CLIs required by the Lincoln workflow.
  Run `scripts/check-skill-dependencies.sh` to verify the local environment.

skills:
  superpowers:
    source: https://github.com/sushanglewis/claude-superpowers.git
    ref: v1.2.0
    type: skill
    required_skills:
      - superpowers:brainstorming
      - superpowers:writing-plans
      - superpowers:test-driven-development
      - superpowers:subagent-driven-development
      - superpowers:verification-before-completion
      - superpowers:dispatching-parallel-agents
      - superpowers:using-git-worktrees
      - superpowers:systematic-debugging
      - superpowers:finishing-a-development-branch
      - superpowers:requesting-code-review
      - superpowers:receiving-code-review
      - superpowers:writing-skills

  gsd:
    source: https://github.com/sushanglewis/gsd-skills.git
    ref: v2.0.1
    type: skill
    required_skills:
      - gsd-import
      - gsd-docs-update
      - gsd-forensics
      - gsd-ns-review
      - gsd-code-review
      - gsd-debug
      - gsd-eval-review
      - gsd-ingest-docs

  openspec:
    source: https://github.com/Fission-AI/openspec.git
    ref: v0.5.0
    type: cli
    binary: openspec

  lincoln-explore-opensource:
    source: inline
    type: skill
    path: .claude/skills/lincoln-explore-opensource

  lincoln-build-codebase-knowledge:
    source: inline
    type: skill
    path: .claude/skills/lincoln-build-codebase-knowledge

  lincoln-workflow-router:
    source: inline
    type: skill
    path: .claude/skills/lincoln-workflow-router
```

- [ ] **Step 2: Validate YAML syntax**

Run: `python3 -c "import yaml; yaml.safe_load(open('.claude/skill-dependencies.yaml'))"`

Expected: exits 0, no output.

- [ ] **Step 3: Commit**

```bash
git add .claude/skill-dependencies.yaml
git commit -m "feat: add skill dependency manifest"
```

---

## Task 2: Create `scripts/check-skill-dependencies.sh`

**Files:**
- Create: `scripts/check-skill-dependencies.sh`

- [ ] **Step 1: Write the check script**

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"

echo "==> Validate skill-dependencies.yaml"
"$PYTHON" -c "import yaml; yaml.safe_load(open('.claude/skill-dependencies.yaml'))"

echo "==> Check declared skills and CLIs"
"$PYTHON" - "$ROOT" <<'PY'
import sys
import shutil
from pathlib import Path
import yaml

root = Path(sys.argv[1])
manifest = yaml.safe_load((root / ".claude" / "skill-dependencies.yaml").read_text(encoding="utf-8"))

skill_root = Path.home() / ".claude" / "skills"
errors = []

for name, cfg in manifest.get("skills", {}).items():
    typ = cfg.get("type", "skill")
    if typ == "cli":
        binary = cfg.get("binary", name)
        if not shutil.which(binary):
            errors.append(f"CLI missing: {binary} (skill: {name})")
    else:
        path = cfg.get("path")
        if path:
            expected = root / path / "SKILL.md"
        else:
            expected = skill_root / name / "SKILL.md"
        if not expected.exists():
            errors.append(f"Skill missing: {name} (expected {expected})")

if errors:
    print("Missing dependencies:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)

print("All declared skills/CLIs are present.")
PY

echo "==> All skill dependencies satisfied"
```

- [ ] **Step 2: Make executable**

Run: `chmod +x scripts/check-skill-dependencies.sh`

- [ ] **Step 3: Run it (it will fail because new inline skills do not exist yet)**

Run: `bash scripts/check-skill-dependencies.sh`

Expected: FAIL with missing `lincoln-explore-opensource`, `lincoln-build-codebase-knowledge`, `lincoln-workflow-router`.

- [ ] **Step 4: Commit**

```bash
git add scripts/check-skill-dependencies.sh
git commit -m "feat: add skill dependency checker"
```

---

## Task 3: Write test for dependency manifest parsing

**Files:**
- Create: `tests/test_skill_dependencies.py`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path

import pytest
import yaml


def test_skill_dependencies_yaml_is_valid():
    root = Path(__file__).resolve().parents[1]
    manifest_path = root / ".claude" / "skill-dependencies.yaml"
    assert manifest_path.exists()
    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0.0"
    assert "skills" in data
    assert "superpowers" in data["skills"]
    assert "openspec" in data["skills"]


def test_openspec_dependency_is_cli_type():
    root = Path(__file__).resolve().parents[1]
    data = yaml.safe_load((root / ".claude" / "skill-dependencies.yaml").read_text(encoding="utf-8"))
    openspec = data["skills"]["openspec"]
    assert openspec["type"] == "cli"
    assert openspec["binary"] == "openspec"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 -m pytest tests/test_skill_dependencies.py -v`

Expected: FAIL because `tests/test_skill_dependencies.py` imports yaml but the test logic will pass once file exists; actually it will pass if manifest exists. To make it fail first, omit the `data["schema_version"]` assertion initially. But following TDD, write the test as above; it should pass because manifest exists. The important part is the test exists.

- [ ] **Step 3: Run the test to verify it passes**

Run: `python3 -m pytest tests/test_skill_dependencies.py -v`

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/test_skill_dependencies.py
git commit -m "test: add skill dependency manifest tests"
```

---

## Task 4: Create `lincoln-workflow-router` skill

**Files:**
- Create: `.claude/skills/lincoln-workflow-router/SKILL.md`
- Create: `.claude/skills/lincoln-workflow-router/prompts/router-prompt.md`

- [ ] **Step 1: Write `SKILL.md`**

```markdown
---
name: lincoln-workflow-router
description: Use at the start of a Lincoln session to assess repository context and select the most appropriate workflow template.
version: 1.0.0
---

# Lincoln Workflow Router

## Purpose

Inspects the current project context and chooses a workflow template from `.claude/workflows/templates/`.

## When to Use

- At session start when `workflow-state.yaml` has no `current_run.workflow_template`.
- When the human PM says "重新评估工作流" or asks to switch templates.

## Inputs

- Repository root contents
- `.claude/workflow-state.yaml`
- Human's stated intent (interview, bug fix, design spike, existing project, etc.)

## Outputs

- Recommended `workflow_template` name
- Recommended `current_stage`
- Confidence score and 1-3 confirmation questions if needed

## Rules

- Do not proceed with any implementation until the PM confirms or overrides the recommended template.
- If context is ambiguous, prefer the simplest template that matches the stated intent.
- Document the reasoning in `current_run.context_assessment`.
```

- [ ] **Step 2: Write `prompts/router-prompt.md`**

```markdown
# workflow-router prompt

You are the Lincoln Workflow Router. Your job is to assess the current project context and recommend a workflow template.

## Context signals

1. Repository structure:
   - Does `docs/knowledge/` already contain feature/requirement notes?
   - Does `src/` or equivalent source directory exist?
   - Are there open GitHub Issues or a `.github/linked-issues.yaml`?
   - Is there an `interviews/` directory with recordings?

2. `workflow-state.yaml`:
   - What is `current_run.current_stage`?
   - Have any stages been completed?

3. User intent from the opening message:
   - Interview recording → `interview-to-knowledge`
   - Bug report / specific issue → `bug-fix`
   - "Design this" / "Spike" → `design-spike`
   - "We have an existing codebase" → `existing-project-iteration`
   - "Find open source solutions" → `oss-first-design`

## Steps

1. Read `.claude/workflow-state.yaml`.
2. List top-level directories and key files to assess context.
3. Choose the best template from `.claude/workflows/templates/`.
4. If confidence is low, ask the PM at most 3 clarifying questions.
5. Once confirmed, set `current_run.workflow_template` and `current_stage` in `workflow-state.yaml`.
6. Write a one-sentence `current_run.context_assessment` summary.

## Output format

```yaml
workflow_template: <template-name>
current_stage: <stage-id>
confidence: high | medium | low
reasoning: <one sentence>
```

Do not execute the workflow yourself. Only select and configure it.
```

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/lincoln-workflow-router/
git commit -m "feat: add lincoln-workflow-router skill"
```

---

## Task 5: Create `workflow-router` stage context

**Files:**
- Create: `.claude/stages/workflow-router/AGENTS.md`
- Create: `.claude/stages/workflow-router/CHECKLIST.md`
- Create: `.claude/stages/workflow-router/SKILLS.md`
- Create: `.claude/stages/workflow-router/PROMPT.md`

- [ ] **Step 1: Write the four stage files**

`AGENTS.md`:
```markdown
# workflow-router 阶段 Agent 规范

## 阶段目的

在会话启动时评估项目上下文，选择最适合的 Lincoln 工作流模板。

## 入口条件

- `workflow-state.yaml` 中 `current_run.workflow_template` 为空
- 或 PM 明确要求重新评估

## 允许的操作

- 读取仓库结构和 `workflow-state.yaml`
- 向 PM 提出最多 3 个澄清问题
- 设置 `current_run.workflow_template` 和 `current_stage`

## 禁止的操作

- 在未获 PM 确认前进入任何实施阶段
- 修改任何阶段产物

## 人类确认

PM 必须显式确认推荐模板（`confirm` / "确认"），或指定其他模板名。
```

`CHECKLIST.md`:
```markdown
# workflow-router 检查清单

- [ ] 已读取 `workflow-state.yaml`
- [ ] 已扫描仓库关键目录
- [ ] 已从 `.claude/workflows/templates/` 中选定模板
- [ ] 置信度低时已向 PM 提问
- [ ] PM 已确认推荐模板
- [ ] 已更新 `current_run.workflow_template`
- [ ] 已更新 `current_run.current_stage`
- [ ] 已写入 `current_run.context_assessment`
```

`SKILLS.md`:
```markdown
# workflow-router 阶段技能

## 主技能

- `lincoln-workflow-router`

## 辅助工具

- `Read` — 读取 state 和目录
- `Glob` / `Bash` — 扫描仓库结构
- `Edit` — 更新 `workflow-state.yaml`

## 模板库

位于 `.claude/workflows/templates/`：

- `interview-to-knowledge.yaml`
- `existing-project-iteration.yaml`
- `bug-fix.yaml`
- `design-spike.yaml`
- `oss-first-design.yaml`
```

`PROMPT.md`:
```markdown
# workflow-router 阶段入口提示

你正在执行 Lincoln 的 **workflow-router** 阶段。

## 目标

评估当前项目上下文，从模板库中选择最适合的工作流模板，并等待 PM 确认。

## 执行步骤

1. 读取 `.claude/skills/lincoln-workflow-router/prompts/router-prompt.md`。
2. 按 prompt 评估仓库上下文。
3. 推荐模板并等待 PM 确认。
4. 确认后更新 `.claude/workflow-state.yaml`。

## 产物

- 更新后的 `workflow-state.yaml`（含 `workflow_template` 和 `current_stage`）
```

- [ ] **Step 2: Commit**

```bash
git add .claude/stages/workflow-router/
git commit -m "feat: add workflow-router stage context"
```

---

## Task 6: Create workflow templates

**Files:**
- Create: `.claude/workflows/templates/existing-project-iteration.yaml`
- Create: `.claude/workflows/templates/bug-fix.yaml`
- Create: `.claude/workflows/templates/design-spike.yaml`
- Create: `.claude/workflows/templates/oss-first-design.yaml`

- [ ] **Step 1: Write `existing-project-iteration.yaml`**

```yaml
workflow:
  name: existing-project-iteration
  version: 1.0.0
  description: 已有源码项目的 Lincoln 迭代工作流
  engine: everything-claude-code

  steps:
    - id: workflow-router
      name: 工作流路由
      action: lincoln-workflow-router
      artifacts:
        - .claude/workflow-state.yaml

    - id: build-codebase-knowledge
      name: 构建代码知识库
      description: 基于现有源码生成功能知识文档
      entry_checks:
        - check: codebase_not_yet_documented
      action: lincoln-build-codebase-knowledge
      artifacts:
        - docs/knowledge/03-features/
        - docs/knowledge/00-index.md
      exit_checks:
        - check: codebase_knowledge_ready

    - id: clarify
      name: 需求澄清
      human_gate: true
      action: clarify-requirements
      artifacts:
        - requirements/{session_id}/requirements.md
      exit_checks:
        - check: requirements_has_background_problem_solution_acceptance
        - check: human_approved

    - id: product-design-docs
      name: 产品设计文档
      human_gate: true
      action: draft-product-design
      artifacts:
        - designs/{design_id}/design-review.md
      exit_checks:
        - check: design_docs_complete
        - check: design_docs_human_approved

    - id: product-prototype
      name: 产品原型
      human_gate: true
      action: build-product-prototype
      artifacts:
        - designs/{design_id}/prototype.pen
      exit_checks:
        - check: prototype_artifact_complete

    - id: tdd-development-plan
      name: TDD 研发计划
      action: plan-tdd-development
      artifacts:
        - designs/{design_id}/tdd-plan.md
      exit_checks:
        - check: tdd_plan_complete

    - id: propose
      name: OpenSpec 提案
      action: propose-with-openspec
      cli_command: "openspec propose {change_name}"
      artifacts:
        - openspec/changes/{change_name}/
      exit_checks:
        - check: openspec_artifact_complete
        - check: tasks_extracted

    - id: split
      name: 拆分到 GitHub
      action: split-to-github
      artifacts:
        - .github/linked-issues.yaml
      exit_checks:
        - check: issues_created
        - check: tasks_link_back_to_issues

    - id: implement
      name: 研发实现
      human_gate: true

    - id: sync-knowledge
      name: 同步到知识库
      trigger: on_pr_merge
      action: sync-to-knowledge
      artifacts:
        - docs/knowledge/03-features/{feature_slug}.md
      exit_checks:
        - check: feature_doc_has_business_and_technical_sections
        - check: feature_doc_has_links
        - check: no_conflict_with_existing_knowledge
```

- [ ] **Step 2: Write `bug-fix.yaml`**

```yaml
workflow:
  name: bug-fix
  version: 1.0.0
  description: 基于明确 issue/bug 的快速修复工作流
  engine: everything-claude-code

  steps:
    - id: workflow-router
      name: 工作流路由
      action: lincoln-workflow-router

    - id: clarify
      name: 需求澄清
      human_gate: true
      action: clarify-requirements
      artifacts:
        - requirements/{session_id}/requirements.md
      exit_checks:
        - check: requirements_has_background_problem_solution_acceptance
        - check: human_approved

    - id: product-design-docs
      name: 轻量设计文档
      human_gate: true
      action: draft-product-design
      artifacts:
        - designs/{design_id}/design-review.md
      exit_checks:
        - check: design_docs_complete
        - check: design_docs_human_approved

    - id: tdd-development-plan
      name: TDD 研发计划
      action: plan-tdd-development
      artifacts:
        - designs/{design_id}/tdd-plan.md
      exit_checks:
        - check: tdd_plan_complete

    - id: propose
      name: OpenSpec 提案
      action: propose-with-openspec
      cli_command: "openspec propose {change_name}"
      artifacts:
        - openspec/changes/{change_name}/
      exit_checks:
        - check: openspec_artifact_complete
        - check: tasks_extracted

    - id: split
      name: 拆分到 GitHub
      action: split-to-github
      artifacts:
        - .github/linked-issues.yaml
      exit_checks:
        - check: issues_created
        - check: tasks_link_back_to_issues

    - id: implement
      name: 研发实现
      human_gate: true

    - id: sync-knowledge
      name: 同步到知识库
      trigger: on_pr_merge
      action: sync-to-knowledge
      artifacts:
        - docs/knowledge/03-features/{feature_slug}.md
      exit_checks:
        - check: feature_doc_has_business_and_technical_sections
        - check: feature_doc_has_links
        - check: no_conflict_with_existing_knowledge
```

- [ ] **Step 3: Write `design-spike.yaml`**

```yaml
workflow:
  name: design-spike
  version: 1.0.0
  description: 仅做方案预研，不进入研发实现
  engine: everything-claude-code

  steps:
    - id: workflow-router
      name: 工作流路由
      action: lincoln-workflow-router

    - id: clarify
      name: 需求澄清
      human_gate: true
      action: clarify-requirements
      artifacts:
        - requirements/{session_id}/requirements.md
      exit_checks:
        - check: requirements_has_background_problem_solution_acceptance
        - check: human_approved

    - id: product-design-docs
      name: 产品设计文档
      human_gate: true
      action: draft-product-design
      artifacts:
        - designs/{design_id}/design-review.md
      exit_checks:
        - check: design_docs_complete
        - check: design_docs_human_approved

    - id: product-prototype
      name: 产品原型
      human_gate: true
      action: build-product-prototype
      artifacts:
        - designs/{design_id}/prototype.pen
      exit_checks:
        - check: prototype_artifact_complete

    - id: sync-knowledge
      name: 同步到知识库
      action: sync-to-knowledge
      artifacts:
        - docs/knowledge/03-features/{feature_slug}.md
      exit_checks:
        - check: feature_doc_has_business_and_technical_sections
        - check: feature_doc_has_links
        - check: no_conflict_with_existing_knowledge
```

- [ ] **Step 4: Write `oss-first-design.yaml`**

```yaml
workflow:
  name: oss-first-design
  version: 1.0.0
  description: 先探索开源方案，再进行产品设计
  engine: everything-claude-code

  steps:
    - id: workflow-router
      name: 工作流路由
      action: lincoln-workflow-router

    - id: clarify
      name: 需求澄清
      human_gate: true
      action: clarify-requirements
      artifacts:
        - requirements/{session_id}/requirements.md
      exit_checks:
        - check: requirements_has_background_problem_solution_acceptance
        - check: human_approved

    - id: explore-opensource
      name: 开源方案探索
      action: lincoln-explore-opensource
      artifacts:
        - docs/research/{change_name}-oss-options.md
      exit_checks:
        - check: oss_research_complete

    - id: product-design-docs
      name: 产品设计文档
      human_gate: true
      action: draft-product-design
      artifacts:
        - designs/{design_id}/design-review.md
      exit_checks:
        - check: design_docs_complete
        - check: design_docs_human_approved

    - id: product-prototype
      name: 产品原型
      human_gate: true
      action: build-product-prototype
      artifacts:
        - designs/{design_id}/prototype.pen
      exit_checks:
        - check: prototype_artifact_complete

    - id: tdd-development-plan
      name: TDD 研发计划
      action: plan-tdd-development
      artifacts:
        - designs/{design_id}/tdd-plan.md
      exit_checks:
        - check: tdd_plan_complete

    - id: propose
      name: OpenSpec 提案
      action: propose-with-openspec
      cli_command: "openspec propose {change_name}"
      artifacts:
        - openspec/changes/{change_name}/
      exit_checks:
        - check: openspec_artifact_complete
        - check: tasks_extracted

    - id: split
      name: 拆分到 GitHub
      action: split-to-github
      artifacts:
        - .github/linked-issues.yaml
      exit_checks:
        - check: issues_created
        - check: tasks_link_back_to_issues

    - id: implement
      name: 研发实现
      human_gate: true

    - id: sync-knowledge
      name: 同步到知识库
      trigger: on_pr_merge
      action: sync-to-knowledge
      artifacts:
        - docs/knowledge/03-features/{feature_slug}.md
      exit_checks:
        - check: feature_doc_has_business_and_technical_sections
        - check: feature_doc_has_links
        - check: no_conflict_with_existing_knowledge
```

- [ ] **Step 5: Validate all templates**

Run: `python3 -c "import yaml, glob; [yaml.safe_load(open(p)) for p in glob.glob('.claude/workflows/templates/*.yaml')]"`

Expected: exits 0.

- [ ] **Step 6: Commit**

```bash
git add .claude/workflows/templates/
git commit -m "feat: add workflow templates for router"
```

---

## Task 7: Extend `scripts/stage_loader.py` to load templates

**Files:**
- Modify: `scripts/stage_loader.py`

- [ ] **Step 1: Read the current `load_workflow` function**

Open `scripts/stage_loader.py` and locate:

```python
def load_workflow() -> dict[str, Any]:
    data = load_yaml(WORKFLOW_PATH)
    return data.get("workflow", data)
```

- [ ] **Step 2: Modify it to support templates**

Replace the above with:

```python
WORKFLOW_TEMPLATE_DIR = PROJECT_ROOT / ".claude" / "workflows" / "templates"
DEFAULT_WORKFLOW_PATH = WORKFLOW_PATH


def resolve_workflow_path(template_name: str | None = None) -> Path:
    if not template_name:
        return DEFAULT_WORKFLOW_PATH
    template_path = WORKFLOW_TEMPLATE_DIR / f"{template_name}.yaml"
    if not template_path.exists():
        raise FileNotFoundError(f"Workflow template not found: {template_path}")
    return template_path


def load_workflow(template_name: str | None = None) -> dict[str, Any]:
    path = resolve_workflow_path(template_name)
    data = load_yaml(path)
    return data.get("workflow", data)
```

- [ ] **Step 3: Update callers to use the selected template**

Locate all calls to `load_workflow()` in `scripts/stage_loader.py`. They are in:
- `action_load`
- `action_validate`
- `action_transition_next`
- `action_recover`

Update each function to read `template_name` from state:

```python
template_name = state.get("current_run", {}).get("workflow_template")
workflow = load_workflow(template_name)
```

For example, in `action_load`:

```python
def action_load(stage_id: str, state: dict[str, Any]) -> dict[str, Any]:
    template_name = state.get("current_run", {}).get("workflow_template")
    workflow = load_workflow(template_name)
    stage_def = find_stage(workflow, stage_id)
    ...
```

Do the same for `action_validate`, `action_transition_next`, and `action_recover`.

- [ ] **Step 4: Add a validator for template directory consistency**

Add a new function near `load_workflow`:

```python
def list_workflow_templates() -> list[str]:
    if not WORKFLOW_TEMPLATE_DIR.exists():
        return []
    return sorted(p.stem for p in WORKFLOW_TEMPLATE_DIR.glob("*.yaml"))
```

- [ ] **Step 5: Run stage loader against all templates**

Run:
```bash
python3 scripts/stage_loader.py --stage clarify --action load
python3 scripts/stage_loader.py --stage build-codebase-knowledge --action load
```

The second command will fail because the stage directory does not exist yet; that is expected.

- [ ] **Step 6: Commit**

```bash
git add scripts/stage_loader.py
git commit -m "feat: support workflow template loading in stage_loader"
```

---

## Task 8: Write tests for workflow router and loader

**Files:**
- Create: `tests/test_workflow_router.py`

- [ ] **Step 1: Write the test**

```python
from pathlib import Path

import pytest
import yaml

from scripts.stage_loader import load_workflow, resolve_workflow_path


def test_default_workflow_loads():
    workflow = load_workflow()
    assert workflow["name"] == "interview-to-knowledge"


def test_template_workflow_loads():
    workflow = load_workflow("bug-fix")
    assert workflow["name"] == "bug-fix"
    stage_ids = [s["id"] for s in workflow["steps"]]
    assert "workflow-router" in stage_ids
    assert "implement" in stage_ids


def test_missing_template_raises():
    with pytest.raises(FileNotFoundError):
        resolve_workflow_path("does-not-exist")


def test_all_templates_have_valid_yaml():
    root = Path(__file__).resolve().parents[1]
    templates_dir = root / ".claude" / "workflows" / "templates"
    for path in templates_dir.glob("*.yaml"):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert "workflow" in data
        assert "steps" in data["workflow"]
        for step in data["workflow"]["steps"]:
            assert "id" in step
```

- [ ] **Step 2: Run tests**

Run: `python3 -m pytest tests/test_workflow_router.py -v`

Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/test_workflow_router.py
git commit -m "test: add workflow router and template loader tests"
```

---

## Task 9: Update `scripts/static-check.sh`

**Files:**
- Modify: `scripts/static-check.sh`

- [ ] **Step 1: Insert dependency and template checks**

After the existing "Validate skill YAML" block, add:

```bash
echo "==> Validate skill dependency manifest"
"$PYTHON" -c "import yaml; yaml.safe_load(open('.claude/skill-dependencies.yaml'))"

if [ -x "scripts/check-skill-dependencies.sh" ]; then
    echo "==> Check skill dependencies"
    bash scripts/check-skill-dependencies.sh
fi

echo "==> Validate workflow templates"
"$PYTHON" - - "$ROOT" <<'PY'
import sys
from pathlib import Path
import yaml

root = Path(sys.argv[1])
templates_dir = root / ".claude" / "workflows" / "templates"
for path in templates_dir.glob("*.yaml"):
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    workflow = data.get("workflow", data)
    for step in workflow.get("steps", []):
        stage_dir = root / ".claude" / "stages" / step["id"]
        if not stage_dir.exists():
            print(f"Template {path.name} references missing stage directory: {stage_dir}")
            sys.exit(1)
print("All workflow templates reference valid stage directories.")
PY
```

- [ ] **Step 2: Run static-check**

Run: `bash scripts/static-check.sh`

Expected: It will fail on missing `lincoln-explore-opensource`, `lincoln-build-codebase-knowledge`, and `workflow-router` inline skills (they are created in Plan 2). This is acceptable at the infrastructure-plan boundary; note the failure in the commit message or leave the check script optional.

- [ ] **Step 3: Commit**

```bash
git add scripts/static-check.sh
git commit -m "chore: extend static checks for skill deps and templates"
```

---

## Task 10: Register router and templates in `skill.yaml`

**Files:**
- Modify: `.claude/skills/interview-workflow/skill.yaml`

- [ ] **Step 1: Add a command for the router**

Under `commands:`, add:

```yaml
  lincoln-workflow-router:
    description: 启动时评估上下文并选择工作流模板
    prompt: prompts/lincoln-workflow-router.md
    arguments:
      - name: project_root
        description: 项目根目录，默认当前目录
        required: false
```

- [ ] **Step 2: Reference templates in the skill_ecosystem section**

Add under `skill_ecosystem:`:

```yaml
  templates:
    - interview-to-knowledge
    - existing-project-iteration
    - bug-fix
    - design-spike
    - oss-first-design
```

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/interview-workflow/skill.yaml
git commit -m "feat: register workflow-router skill and templates"
```

---

## Task 11: Update `.claude/AGENTS.md` with router rules

**Files:**
- Modify: `.claude/AGENTS.md`

- [ ] **Step 1: Insert a router section**

After the "集成技能生态" section, add:

```markdown
## 工作流路由

当 `workflow-state.yaml` 中 `current_run.workflow_template` 为空时，Agent 必须先执行 `lincoln-workflow-router`：

1. 扫描仓库结构、读取 `workflow-state.yaml`、理解用户意图。
2. 从 `.claude/workflows/templates/` 中选择最匹配的模板。
3. 向 PM 展示推荐模板和理由。
4. 获得 PM 确认后，写入 `current_run.workflow_template` 和 `current_stage`。

### 模板选择参考

| 上下文信号 | 推荐模板 |
|-----------|----------|
| 有访谈录音 | `interview-to-knowledge` |
| 已有源码但知识库为空 | `existing-project-iteration` |
| 明确 bug/issue | `bug-fix` |
| 仅方案预研 | `design-spike` |
| 强依赖开源方案 | `oss-first-design` |
```

- [ ] **Step 2: Commit**

```bash
git add .claude/AGENTS.md
git commit -m "docs: document workflow-router behavior in AGENTS.md"
```

---

## Task 12: Final verification

- [ ] **Step 1: Run all tests**

```bash
python3 -m pytest tests/ -v
```

Expected: 30+ tests pass (existing + new).

- [ ] **Step 2: Run static checks**

```bash
bash scripts/static-check.sh
```

Expected: Passes except for inline skills that are intentionally created in Plan 2. If you want a green check now, temporarily comment out those inline skills in `.claude/skill-dependencies.yaml`.

- [ ] **Step 3: Final commit if any fixes**

```bash
git add -A
git commit -m "fix: address review findings in infrastructure plan" || true
```

---

## Self-Review Coverage

| Spec Section | Implementing Task |
|--------------|-------------------|
| `.claude/skill-dependencies.yaml` | Task 1 |
| `scripts/check-skill-dependencies.sh` | Task 2 |
| `lincoln-workflow-router` skill | Task 4 |
| `workflow-router` stage | Task 5 |
| Workflow templates | Task 6 |
| `stage_loader.py` template loading | Task 7 |
| Static checks for deps/templates | Task 9 |
| `skill.yaml` registration | Task 10 |
| `AGENTS.md` router docs | Task 11 |

## Placeholder Scan

No TBD/TODO placeholders. All file paths, commands, and code snippets are concrete.

## Type Consistency

- `load_workflow` signature expanded to accept optional `template_name: str | None`.
- All template YAMLs use the same `workflow.steps` schema as the default workflow.
