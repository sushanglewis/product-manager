# Lincoln Evolution — New Skills Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `lincoln-build-codebase-knowledge` and `lincoln-explore-opensource` as first-class skills/stages, integrate them into the workflow templates created in the infrastructure plan, and ensure existing stages can call them when context requires.

**Architecture:** Two self-contained skills under `.claude/skills/` with their own prompts, stage context under `.claude/stages/`, a small Python scanner helper for codebase knowledge, and prompt-driven research/scoring for open-source exploration. No changes to the `everything-claude-code` loop engine.

**Tech Stack:** Python 3, Markdown, YAML, WebSearch/GitHub MCP, `superpowers:subagent-driven-development`.

---

## File Structure

| File | Responsibility |
|------|----------------|
| `.claude/skills/lincoln-build-codebase-knowledge/SKILL.md` | Skill metadata for building knowledge from existing code |
| `.claude/skills/lincoln-build-codebase-knowledge/prompts/build-codebase-knowledge.md` | Prompt that drives the codebase knowledge extraction |
| `.claude/stages/build-codebase-knowledge/{AGENTS.md,CHECKLIST.md,SKILLS.md,PROMPT.md}` | Stage context for codebase knowledge extraction |
| `scripts/build-codebase-knowledge.py` | Helper that scans the repo and emits a machine-readable feature map |
| `.claude/skills/lincoln-explore-opensource/SKILL.md` | Skill metadata for OSS exploration |
| `.claude/skills/lincoln-explore-opensource/prompts/explore-opensource.md` | Prompt that drives OSS research and scoring |
| `.claude/stages/explore-opensource/{AGENTS.md,CHECKLIST.md,SKILLS.md,PROMPT.md}` | Stage context for OSS exploration |
| `tests/test_new_skills.py` | Tests for scanner output format and skill file presence |
| `.claude/stages/product-design-docs/SKILLS.md` | Updated to optionally call `lincoln-explore-opensource` |
| `.claude/stages/product-design-docs/PROMPT.md` | Updated to trigger OSS exploration when relevant |
| `.claude/stages/tdd-development-plan/PROMPT.md` | Updated to consume OSS findings if available |
| `.claude/skills/interview-workflow/skill.yaml` | Registers the two new skills under `skill_ecosystem` |
| `.claude/AGENTS.md` | Documents when to call the new skills |

---

## Task 1: Create `lincoln-build-codebase-knowledge` skill

**Files:**
- Create: `.claude/skills/lincoln-build-codebase-knowledge/SKILL.md`
- Create: `.claude/skills/lincoln-build-codebase-knowledge/prompts/build-codebase-knowledge.md`

- [ ] **Step 1: Write `SKILL.md`**

```markdown
---
name: lincoln-build-codebase-knowledge
description: Use when starting Lincoln on an existing project with source code but no feature knowledge base yet.
version: 1.0.0
---

# Lincoln Build Codebase Knowledge

## Purpose

Scan an existing codebase, identify its major features/modules, and generate feature knowledge documents under `docs/knowledge/` so Lincoln can iterate from facts instead of assumptions.

## When to Use

- Project already has source code.
- `docs/knowledge/03-features/` is empty or out of date.
- The `existing-project-iteration` workflow template is active.

## Inputs

- Repository root
- Existing source tree
- Existing `README.md`, `CHANGELOG.md`, and any architectural docs

## Outputs

- `docs/knowledge/00-index.md` — master index
- `docs/knowledge/03-features/existing-<feature>.md` — one per core feature
- `docs/knowledge/05-glossary/00-index.md` — domain terms inferred from code

## Rules

- Do not modify source code.
- Infer features from directory structure, public APIs, and README.
- Cross-check generated docs against source files (cite file paths).
- Stop and ask the PM when confidence is low.
```

- [ ] **Step 2: Write `prompts/build-codebase-knowledge.md`**

```markdown
# build-codebase-knowledge prompt

You are the Lincoln Codebase Knowledge Builder. Your job is to turn an existing codebase into a concise feature knowledge base.

## Phase 1 — Structural scan

1. Run `scripts/build-codebase-knowledge.py --root .` to get a machine-readable feature map.
2. Read `README.md`, `CHANGELOG.md`, and any `ARCHITECTURE.md` / `docs/` files.
3. Identify the top 3-10 features/modules that a PM would care about.

## Phase 2 — Deep read per feature

For each feature from the map:

1. Read the entry-point files listed by the scanner.
2. Summarize in one paragraph:
   - What the feature does (business value)
   - How it is implemented (high-level technical approach)
   - Key files and public APIs
3. List acceptance criteria that could be derived from existing tests or behavior.

## Phase 3 — Write knowledge documents

1. Create `docs/knowledge/00-index.md` with a table of features and links.
2. Create `docs/knowledge/03-features/existing-<feature>.md` for each feature using the template below.
3. Create `docs/knowledge/05-glossary/00-index.md` with domain terms and definitions inferred from code.

## Feature document template

```markdown
# <Feature Name>

## Business knowledge

- Purpose:
- User value:
- Linked requirements:

## Technical knowledge

- Entry points:
- Key files:
- Public API / surface:
- Data model:
- Dependencies:

## Acceptance criteria

- [ ] <criterion 1>
- [ ] <criterion 2>

## Source references

- `src/...`
- `tests/...`
```

## Human gate

- Ask the PM to review `docs/knowledge/00-index.md` before continuing.
- Mark `codebase-knowledge-ready` in `workflow-state.yaml` only after PM confirms or 5 minutes pass with no objections.
```

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/lincoln-build-codebase-knowledge/
git commit -m "feat: add lincoln-build-codebase-knowledge skill"
```

---

## Task 2: Create `build-codebase-knowledge` stage context

**Files:**
- Create: `.claude/stages/build-codebase-knowledge/AGENTS.md`
- Create: `.claude/stages/build-codebase-knowledge/CHECKLIST.md`
- Create: `.claude/stages/build-codebase-knowledge/SKILLS.md`
- Create: `.claude/stages/build-codebase-knowledge/PROMPT.md`

- [ ] **Step 1: Write the four stage files**

`AGENTS.md`:
```markdown
# build-codebase-knowledge 阶段 Agent 规范

## 阶段目的

为已有源码项目构建功能知识库，使后续 PM 迭代能基于事实。

## 入口条件

- 当前 workflow 模板为 `existing-project-iteration`
- 或 PM 明确说 "先理解现有代码"

## 允许的操作

- 读取源码、README、CHANGELOG
- 调用 `lincoln-build-codebase-knowledge`
- 生成/更新 `docs/knowledge/` 下的 Markdown 文件

## 禁止的操作

- 修改源码
- 生成未经验证的假设
- 跳过 PM 确认直接标记完成

## 人类确认节点

PM 必须确认 `docs/knowledge/00-index.md` 中的功能列表后，阶段才能标记完成。
```

`CHECKLIST.md`:
```markdown
# build-codebase-knowledge 检查清单

- [ ] 已运行 `scripts/build-codebase-knowledge.py`
- [ ] 已读取 README/CHANGELOG/架构文档
- [ ] 已识别 3-10 个核心功能
- [ ] 已生成 `docs/knowledge/00-index.md`
- [ ] 已生成 `docs/knowledge/03-features/existing-*.md`
- [ ] 已生成 `docs/knowledge/05-glossary/00-index.md`
- [ ] PM 已确认功能索引
- [ ] 已在 `workflow-state.yaml` 中标记 `codebase-knowledge-ready`
```

`SKILLS.md`:
```markdown
# build-codebase-knowledge 阶段技能

## 主技能

- `lincoln-build-codebase-knowledge`

## 辅助工具

- `scripts/build-codebase-knowledge.py` — 扫描代码库结构
- `Read` / `Glob` / `Bash` — 读取源码和文档
- `Edit` / `Write` — 生成知识文档

## 输出位置

- `docs/knowledge/00-index.md`
- `docs/knowledge/03-features/existing-*.md`
- `docs/knowledge/05-glossary/00-index.md`
```

`PROMPT.md`:
```markdown
# build-codebase-knowledge 阶段入口提示

你正在执行 Lincoln 的 **build-codebase-knowledge** 阶段。

## 目标

扫描现有代码库，生成功能知识文档，等待 PM 确认。

## 执行步骤

1. 读取 `.claude/skills/lincoln-build-codebase-knowledge/prompts/build-codebase-knowledge.md`。
2. 运行 `scripts/build-codebase-knowledge.py --root .` 获取功能映射。
3. 按 prompt 深度阅读并生成知识文档。
4. 向 PM 展示 `docs/knowledge/00-index.md` 并等待确认。
5. 确认后标记 `codebase-knowledge-ready`。

## 产物

- `docs/knowledge/00-index.md`
- `docs/knowledge/03-features/existing-*.md`
- `docs/knowledge/05-glossary/00-index.md`
```

- [ ] **Step 2: Commit**

```bash
git add .claude/stages/build-codebase-knowledge/
git commit -m "feat: add build-codebase-knowledge stage"
```

---

## Task 3: Create `scripts/build-codebase-knowledge.py`

**Files:**
- Create: `scripts/build-codebase-knowledge.py`

- [ ] **Step 1: Write the failing test first**

Create `tests/test_build_codebase_knowledge.py`:

```python
from pathlib import Path

from scripts.build_codebase_knowledge import scan_features


def test_scan_features_finds_top_level_dirs(tmp_path):
    (tmp_path / "src" / "auth").mkdir(parents=True)
    (tmp_path / "src" / "auth" / "login.py").write_text("def login(): pass")
    (tmp_path / "src" / "billing").mkdir()
    (tmp_path / "src" / "billing" / "invoice.py").write_text("def invoice(): pass")
    (tmp_path / "tests" / "auth").mkdir(parents=True)
    (tmp_path / "tests" / "auth" / "test_login.py").write_text("")

    result = scan_features(tmp_path, max_features=10)
    names = {f["name"] for f in result["features"]}
    assert "auth" in names
    assert "billing" in names
    assert result["root"] == str(tmp_path)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 -m pytest tests/test_build_codebase_knowledge.py -v`

Expected: FAIL — `scripts/build_codebase_knowledge.py` does not exist.

- [ ] **Step 3: Implement the scanner**

Create `scripts/build-codebase-knowledge.py`:

```python
#!/usr/bin/env python3
"""Scan a codebase and emit a machine-readable feature map."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_SOURCE_DIRS = ("src", "lib", "app", "packages", "server", "client")
IGNORE_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build"}


def find_source_root(root: Path) -> Path | None:
    for candidate in DEFAULT_SOURCE_DIRS:
        path = root / candidate
        if path.is_dir():
            return path
    # Fallback: use the root if it contains Python/JS files directly
    if any(p.suffix in {".py", ".ts", ".js", ".go", ".rs"} for p in root.iterdir() if p.is_file()):
        return root
    return None


def scan_features(root: Path, max_features: int = 10) -> dict[str, Any]:
    root = root.resolve()
    source_root = find_source_root(root)
    features: list[dict[str, Any]] = []

    if source_root:
        for child in sorted(source_root.iterdir()):
            if not child.is_dir() or child.name in IGNORE_DIRS:
                continue
            entry_points = sorted(
                p.relative_to(root) for p in child.rglob("*")
                if p.is_file() and p.suffix in {".py", ".ts", ".js", ".tsx", ".go", ".rs"}
            )[:5]
            features.append(
                {
                    "name": child.name,
                    "path": str(child.relative_to(root)),
                    "entry_points": [str(ep) for ep in entry_points],
                    "has_tests": any((root / "tests" / child.name).exists() for _ in (True,)),
                }
            )
            if len(features) >= max_features:
                break

    return {"root": str(root), "source_root": str(source_root) if source_root else None, "features": features}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a feature map from an existing codebase.")
    parser.add_argument("--root", default=".", help="Project root")
    parser.add_argument("--max-features", type=int, default=10, help="Maximum features to emit")
    args = parser.parse_args()
    result = scan_features(Path(args.root), max_features=args.max_features)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
```

Note: the script filename uses a hyphen (`build-codebase-knowledge.py`), but the test imports from `scripts.build_codebase_knowledge`. Because Python module names cannot contain hyphens, create a thin wrapper:

```bash
cat > scripts/build_codebase_knowledge.py <<'PY'
from scripts.build_codebase_knowledge_impl import scan_features
PY
```

Then rename the implementation file to `scripts/build-codebase-knowledge_impl.py` and import from it. (Or simply name the implementation `scripts/build_codebase_knowledge.py` and call the CLI via `python3 -m scripts.build_codebase_knowledge`. The plan uses the latter: implement in `scripts/build_codebase_knowledge.py`.)

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 -m pytest tests/test_build_codebase_knowledge.py -v`

Expected: PASS.

- [ ] **Step 5: Make the CLI executable and test it**

Run:
```bash
chmod +x scripts/build-codebase-knowledge.py
python3 scripts/build-codebase-knowledge.py --root .
```

Expected: JSON output listing top-level source directories.

- [ ] **Step 6: Commit**

```bash
git add scripts/build-codebase-knowledge.py scripts/build_codebase_knowledge.py tests/test_build_codebase_knowledge.py
git commit -m "feat: add codebase knowledge scanner and tests"
```

---

## Task 4: Create `lincoln-explore-opensource` skill

**Files:**
- Create: `.claude/skills/lincoln-explore-opensource/SKILL.md`
- Create: `.claude/skills/lincoln-explore-opensource/prompts/explore-opensource.md`

- [ ] **Step 1: Write `SKILL.md`**

```markdown
---
name: lincoln-explore-opensource
description: Use during product design when the requirement can be solved or informed by existing open-source projects.
version: 1.0.0
---

# Lincoln Explore Open Source

## Purpose

Research existing open-source projects that solve a similar problem, score them against Lincoln criteria, and produce a recommendation document.

## When to Use

- `oss-first-design` workflow template is active.
- `product-design-docs` stage identifies a subproblem that could be delegated to an existing library/tool.
- PM says "看看有没有开源方案".

## Inputs

- Requirement keywords
- Target technology stack
- Constraints (license, self-host vs SaaS, language)

## Outputs

- `docs/research/{change_name}-oss-options.md`

## Rules

- Prefer active projects with clear documentation.
- Score on business fit, technical fit, license, maintenance, and integration cost.
- Do not download or execute third-party code.
- Present at least 2 options plus a "build from scratch" baseline.
```

- [ ] **Step 2: Write `prompts/explore-opensource.md`**

```markdown
# explore-opensource prompt

You are the Lincoln Open Source Researcher. Find and evaluate open-source projects that could address the current requirement.

## Inputs

- Requirement summary (from `requirements/{session_id}/requirements.md`)
- Design topic (from current design context)
- Target stack/language (from `designs/{design_id}/design-review.md`)

## Steps

1. Extract 2-5 search keywords from the requirement.
2. Search GitHub/npm/PyPI/crates for candidate projects:
   - Use `WebSearch` or GitHub MCP.
   - Record name, repo URL, license, last update, stars/downloads.
3. For each candidate, read README and summarize:
   - What problem it solves
   - Key features relevant to the requirement
   - Integration approach
   - License compatibility
4. Score each candidate 1-5 on:
   - Business fit: does it match the user problem?
   - Technical fit: does it match our stack?
   - Maintenance: recent commits, issue response, release cadence
   - Documentation: README, examples, API docs
   - Integration cost: API surface, deployment complexity
5. Compute a weighted total: business 30%, technical 25%, maintenance 20%, docs 15%, integration 10%.
6. Write `docs/research/{change_name}-oss-options.md` with:
   - Executive recommendation
   - Candidate table
   - Detailed pros/cons for top 2
   - Build-from-scratch baseline
   - Next-step recommendation

## Output format

```markdown
# Open Source Research: <Topic>

## Recommendation

**Top choice:** <project name>
**Reason:** <one sentence>

## Candidates

| Project | License | Stars | Business | Technical | Maintenance | Docs | Integration | Total |
|---------|---------|-------|----------|-----------|-------------|------|-------------|-------|
| ...     | ...     | ...   | ...      | ...       | ...         | ...  | ...         | ...   |

## Top candidate details

### 1. <Project A>
- Repo:
- Pros:
- Cons:
- Integration notes:

### 2. <Project B>
...

## Build-from-scratch baseline

- Effort estimate:
- Maintenance burden:
- When it wins:

## Next steps

1. ...
```

## Human gate

- Present the candidate table to PM.
- Do not make a final recommendation binding without PM confirmation.
```

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/lincoln-explore-opensource/
git commit -m "feat: add lincoln-explore-opensource skill"
```

---

## Task 5: Create `explore-opensource` stage context

**Files:**
- Create: `.claude/stages/explore-opensource/AGENTS.md`
- Create: `.claude/stages/explore-opensource/CHECKLIST.md`
- Create: `.claude/stages/explore-opensource/SKILLS.md`
- Create: `.claude/stages/explore-opensource/PROMPT.md`

- [ ] **Step 1: Write the four stage files**

`AGENTS.md`:
```markdown
# explore-opensource 阶段 Agent 规范

## 阶段目的

在设计阶段探索开源方案，避免从零造轮子，并为实现提供参考。

## 入口条件

- 当前 workflow 模板为 `oss-first-design`
- 或 `product-design-docs` 阶段明确识别出可借鉴开源方案的子问题

## 允许的操作

- 使用 WebSearch/GitHub MCP 搜索开源项目
- 阅读项目 README、license、发布历史
- 生成 `docs/research/{change_name}-oss-options.md`

## 禁止的操作

- 下载或执行第三方代码
- 自动选择最终方案（必须 PM 确认）
- 阻塞设计流程：搜索失败时降级为简短摘要并继续

## 人类确认节点

PM 必须确认推荐方案或明确要求继续自行设计。
```

`CHECKLIST.md`:
```markdown
# explore-opensource 检查清单

- [ ] 已从需求中提取关键词
- [ ] 已搜索至少 3 个候选项目
- [ ] 已读取候选项目 README/license
- [ ] 已生成评分表
- [ ] 已生成 `docs/research/{change_name}-oss-options.md`
- [ ] PM 已确认推荐方案或明确继续自行设计
```

`SKILLS.md`:
```markdown
# explore-opensource 阶段技能

## 主技能

- `lincoln-explore-opensource`

## 辅助工具

- `WebSearch` — 搜索候选项目
- GitHub MCP / `mcp__plugin_ecc_github__search_repositories` — GitHub 搜索
- `Read` / `WebFetch` — 阅读 README 和文档
- `Write` — 生成研究报告
```

`PROMPT.md`:
```markdown
# explore-opensource 阶段入口提示

你正在执行 Lincoln 的 **explore-opensource** 阶段。

## 目标

为当前需求找到合适的开源方案，并生成评估报告。

## 执行步骤

1. 读取 `.claude/skills/lincoln-explore-opensource/prompts/explore-opensource.md`。
2. 从 `requirements/{session_id}/requirements.md` 提取关键词。
3. 搜索候选项目并评分。
4. 生成 `docs/research/{change_name}-oss-options.md`。
5. 向 PM 展示评分表，等待确认。

## 产物

- `docs/research/{change_name}-oss-options.md`
```

- [ ] **Step 2: Commit**

```bash
git add .claude/stages/explore-opensource/
git commit -m "feat: add explore-opensource stage"
```

---

## Task 6: Wire new skills into existing stages

**Files:**
- Modify: `.claude/stages/product-design-docs/SKILLS.md`
- Modify: `.claude/stages/product-design-docs/PROMPT.md`
- Modify: `.claude/stages/tdd-development-plan/PROMPT.md`
- Modify: `.claude/skills/interview-workflow/skill.yaml`
- Modify: `.claude/AGENTS.md`

- [ ] **Step 1: Update `product-design-docs/SKILLS.md`**

Append:

```markdown
## 可选子技能

- `lincoln-explore-opensource` — 当设计涉及可借鉴开源方案时，在设计文档前先做 OSS 研究。产物：`docs/research/{change_name}-oss-options.md`。
```

- [ ] **Step 2: Update `product-design-docs/PROMPT.md`**

Insert before the design document generation step:

```markdown
4. （可选）如果设计涉及可借鉴开源方案，调用 `lincoln-explore-opensource` 生成 `docs/research/{change_name}-oss-options.md`，并等待 PM 确认后再继续。
```

- [ ] **Step 3: Update `tdd-development-plan/PROMPT.md`**

Append to the input list:

```markdown
- `docs/research/{change_name}-oss-options.md`（如果存在）：将其中的集成方案作为 TDD 计划的依赖项。
```

- [ ] **Step 4: Update `skill.yaml`**

Under `skill_ecosystem:`, add:

```yaml
  lincoln:
    - lincoln-build-codebase-knowledge
    - lincoln-explore-opensource
    - lincoln-workflow-router
```

- [ ] **Step 5: Update `.claude/AGENTS.md`**

Append to the router/技能生态章节:

```markdown
## 新增自定义技能

| 技能 | 触发条件 | 产物 |
|------|----------|------|
| `lincoln-build-codebase-knowledge` | 已有源码但知识库为空 | `docs/knowledge/00-index.md` + feature docs |
| `lincoln-explore-opensource` | 设计阶段可借鉴开源方案 | `docs/research/{change_name}-oss-options.md` |
```

- [ ] **Step 6: Commit**

```bash
git add .claude/stages/product-design-docs/SKILLS.md .claude/stages/product-design-docs/PROMPT.md .claude/stages/tdd-development-plan/PROMPT.md .claude/skills/interview-workflow/skill.yaml .claude/AGENTS.md
git commit -m "feat: wire new skills into stages and skill registry"
```

---

## Task 7: Add tests for new skills

**Files:**
- Create: `tests/test_new_skills.py`

- [ ] **Step 1: Write the test**

```python
from pathlib import Path

import yaml


def test_build_codebase_knowledge_skill_exists():
    root = Path(__file__).resolve().parents[1]
    skill = root / ".claude" / "skills" / "lincoln-build-codebase-knowledge" / "SKILL.md"
    assert skill.exists()
    assert "build codebase knowledge" in skill.read_text(encoding="utf-8").lower()


def test_explore_opensource_skill_exists():
    root = Path(__file__).resolve().parents[1]
    skill = root / ".claude" / "skills" / "lincoln-explore-opensource" / "SKILL.md"
    assert skill.exists()
    prompt = root / ".claude" / "skills" / "lincoln-explore-opensource" / "prompts" / "explore-opensource.md"
    assert prompt.exists()


def test_new_stages_registered_in_skill_yaml():
    root = Path(__file__).resolve().parents[1]
    data = yaml.safe_load((root / ".claude" / "skills" / "interview-workflow" / "skill.yaml").read_text(encoding="utf-8"))
    lincoln = data.get("skill_ecosystem", {}).get("lincoln", [])
    assert "lincoln-build-codebase-knowledge" in lincoln
    assert "lincoln-explore-opensource" in lincoln
    assert "lincoln-workflow-router" in lincoln
```

- [ ] **Step 2: Run the test**

Run: `python3 -m pytest tests/test_new_skills.py -v`

Expected: PASS after Task 6.

- [ ] **Step 3: Commit**

```bash
git add tests/test_new_skills.py
git commit -m "test: add new skill registration tests"
```

---

## Task 8: Final verification

- [ ] **Step 1: Run all tests**

```bash
python3 -m pytest tests/ -v
```

Expected: All existing + new tests pass.

- [ ] **Step 2: Run static checks**

```bash
bash scripts/static-check.sh
```

Expected: PASS now that all inline skills and stages exist.

- [ ] **Step 3: Run stage loader against new stages**

```bash
python3 scripts/stage_loader.py --stage build-codebase-knowledge --action load
python3 scripts/stage_loader.py --stage explore-opensource --action load
```

Expected: Both load successfully and output JSON with stage context.

- [ ] **Step 4: Commit any final fixes**

```bash
git add -A
git commit -m "fix: address review findings in new skills plan" || true
```

---

## Self-Review Coverage

| Spec Section | Implementing Task |
|--------------|-------------------|
| `lincoln-build-codebase-knowledge` skill | Task 1 |
| `build-codebase-knowledge` stage | Task 2 |
| Codebase scanner helper | Task 3 |
| `lincoln-explore-opensource` skill | Task 4 |
| `explore-opensource` stage | Task 5 |
| Integration with existing stages/templates | Task 6 |
| Tests | Task 7 |

## Placeholder Scan

No TBD/TODO placeholders. All file paths, code snippets, and commands are concrete.

## Type Consistency

- Scanner returns `dict[str, Any]` consistent across CLI and tests.
- Stage IDs `build-codebase-knowledge` and `explore-opensource` match directory names and template references.
