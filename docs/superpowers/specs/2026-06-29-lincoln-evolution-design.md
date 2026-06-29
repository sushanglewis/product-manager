---
title: Lincoln 工作流进化设计：动态路由、技能依赖与开源探索
author: Lincoln Template
date: 2026-06-29
status: draft
---

# Lincoln 工作流进化设计

## 目标

让 Lincoln 从一条固定的“访谈 → 知识库”流水线，演进为一个**上下文感知的 PM 工作方法框架**：

1. 启动时由 Agent 评估当前场景，自动选择最适合的工作流模板、方法论与执行标准。
2. 显式声明对外部 skill 仓库的依赖，并提供可校验机制。
3. 在需求/设计阶段引入开源项目探索，避免从零造轮子，并为 AI 实现功能提供可借鉴的代码和方案。
4. 让已有源码的项目也能直接接入 Lincoln，先构建代码功能知识库，再基于访谈/issue/反馈迭代。

## 上下文

- 当前 Lincoln 是线性 8 阶段工作流：`ingest → clarify → product-design-docs → product-prototype → tdd-development-plan → propose → split → implement → sync-knowledge`。
- 已集成 `everything-claude-code` 引擎、`openspec` CLI、`superpowers` 部分技能、`gsd` 部分技能。
- 用户反馈：流程太死板、技能引用率不足、缺少开源探索、缺少对已有项目的平滑接入。

## 设计决策

1. **不替换现有引擎**：继续以 `everything-claude-code` 为循环引擎，通过“工作流模板 + 路由器”实现柔性，而非重写 DAG 执行引擎。
2. **模板化而非完全自由**：提供若干预定义模板，Agent 根据上下文选择；PM 可覆盖。避免无限制配置带来的复杂度和不可预测性。
3. **依赖清单独立**：用 `.claude/skill-dependencies.yaml` 声明外部 skill 仓库依赖，不混入 `pyproject.toml`/`package.json`，因为 skill 是 Agent 运行时依赖，不是项目构建依赖。
4. **开源探索作为可选阶段/子技能**：在需要时触发，不强制每个需求都走一遍，避免流程臃肿。
5. **已有项目先建知识库**：新增 `build-codebase-knowledge` 入口，让 PM 能从源码反推出功能知识文档，再进入迭代。

## 推荐方案：Approach 2 — Workflow Router + 依赖清单 + OSS Skill

### 新增/修改的组件

#### 1. `.claude/skill-dependencies.yaml` — 技能依赖清单

```yaml
schema_version: 1.0.0
skills:
  superpowers:
    source: https://github.com/sushanglewis/claude-superpowers.git
    ref: v1.2.0
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
    path: .claude/skills/lincoln-explore-opensource
```

- `ref` 可以是 tag、commit 或 branch。
- `type: cli` 表示需要可执行命令；`type: skill` 表示 Claude Code skill。
- 清单由 `scripts/check-skill-dependencies.sh` 校验：检查本地是否安装了对应 skill/CLI。

#### 2. `workflow-router` — 启动时上下文评估与模板选择

新增 skill/阶段：`.claude/skills/lincoln-workflow-router/`。

执行时机：会话开始时，若 `workflow-state.yaml` 的 `current_run.workflow_template` 为空或 PM 明确说“重新评估”。

输入：
- 当前仓库结构（是否有 `docs/knowledge/`、是否有 `.pen`、是否有 `src/`、是否有 GitHub Issues 等）
- `workflow-state.yaml`
- 用户第一句话的意图（访谈录音、bug 反馈、设计讨论、已有项目导入等）

输出：
- 选中的 `workflow_template` 文件名
- 建议的 `current_stage`
- 1-3 条向 PM 确认的问题（若置信度不足）

模板库 `.claude/workflows/templates/`：

| 模板 | 场景 | 核心路径 |
|------|------|----------|
| `interview-to-knowledge.yaml` | 新需求，从访谈录音开始 | 现有完整 8 阶段 |
| `existing-project-iteration.yaml` | 已有源码，基于 issue/访谈迭代 | build-codebase-knowledge → clarify/design → implement |
| `bug-fix.yaml` | 明确 bug/issue，快速修复 | clarify → design-mini → tdd-plan → implement |
| `design-spike.yaml` | 仅做方案预研，不立即开发 | clarify → design-docs → prototype → sync-knowledge（无 implement） |
| `oss-first-design.yaml` | 强烈依赖开源方案时 | clarify → explore-opensource → design-docs → prototype → ... |

模板使用共同的 stage 目录，但通过 `workflow_template` 字段决定哪些 stage 启用、顺序和 human_gate 配置。

#### 3. `build-codebase-knowledge` — 已有项目接入

新增 skill/阶段：`.claude/skills/lincoln-build-codebase-knowledge/`。

执行时机：被 `existing-project-iteration.yaml` 模板选中时。

步骤：
1. 扫描代码库结构，识别主要模块/服务。
2. 对每个核心功能，调用 `gsd-docs-update` + 代码探索生成 `docs/knowledge/03-features/<feature>.md`。
3. 生成 `docs/knowledge/00-index.md` 与 `05-glossary/` 初始条目。
4. 标记 `codebase-knowledge-ready`，允许后续阶段引用现有功能。

产物：
- `docs/knowledge/03-features/existing-*.md`
- `docs/knowledge/02-requirements/existing-*.md`（从 README/CHANGELOG 推断）
- `docs/knowledge/05-glossary/*.md`

#### 4. `explore-opensource` — 开源项目探索

新增 skill：`.claude/skills/lincoln-explore-opensource/`。

触发方式：
- 在 `product-design-docs` 阶段，当设计涉及“可借鉴开源方案”时由 Agent 调用；
- 或在 `oss-first-design.yaml` 模板中作为独立阶段。

输入：需求片段、功能关键词、目标技术栈。

输出：`docs/research/YYYY-MM-DD-<topic>-oss-options.md`，包含：
- 候选项目列表（名称、仓库链接、license、stars、最近更新时间）
- README/文档与需求的重合度评分
- 与当前代码库的集成复杂度估算
- 推荐方案与备选方案

评估维度：
- 高 star / 活跃维护
- README 说明与当前需求高度重合
- 当前最佳实践（测试、CI、类型安全等）
- License 兼容性

工具：GitHub MCP / WebSearch / 包管理器 API（npm/pypi/cargo）。

#### 5. 增强各阶段技能绑定

| 阶段 | 新增/强化子技能 |
|------|----------------|
| `ingest` | `gsd-ingest-docs`（外部文档导入）、`superpowers:brainstorming`（话题探索） |
| `clarify` | `superpowers:brainstorming`、`gsd-import` |
| `product-design-docs` | `superpowers:brainstorming`、`superpowers:writing-plans`、**`lincoln-explore-opensource`** |
| `product-prototype` | `superpowers:brainstorming`、`superpowers:using-git-worktrees` |
| `tdd-development-plan` | `superpowers:writing-plans`、TDD 方法论 |
| `propose` | `superpowers:verification-before-completion` |
| `split` | `superpowers:dispatching-parallel-agents`、`superpowers:verification-before-completion` |
| `implement` | `superpowers:using-git-worktrees`、`subagent-driven-development`、`test-driven-development`、`systematic-debugging`、`finishing-a-development-branch`、`requesting-code-review`、`receiving-code-review`、`verification-before-completion`、`gsd-code-review`、`gsd-debug` |
| `sync-knowledge` | `gsd-docs-update`、`gsd-forensics`、`gsd-eval-review` |

#### 6. 引擎层最小改动

- `interview-to-knowledge.yaml` 保持不变作为默认模板。
- `scripts/stage_loader.py` 增加读取 `workflow_template` 字段：
  - `load_workflow(template_name)` 从 `.claude/workflows/templates/` 加载对应 YAML。
  - 校验模板中的 stage 是否都有对应 `.claude/stages/<stage>/` 目录。
- `workflow-state.yaml` 增加字段：
  - `current_run.workflow_template`
  - `current_run.context_assessment`（路由决策摘要）

## 数据流

```text
会话开始
  │
  ▼
workflow-router 评估上下文
  │
  ├── 若已有源码 + 无知识库 → 推荐 existing-project-iteration
  │   → build-codebase-knowledge
  │
  ├── 若访谈录音 → 推荐 interview-to-knowledge
  │
  ├── 若明确 bug/issue → 推荐 bug-fix
  │
  ├── 若需方案预研 → 推荐 design-spike
  │
  └── 若强依赖开源方案 → 推荐 oss-first-design
  │
  ▼
PM 确认/覆盖模板
  │
  ▼
按模板顺序执行阶段
  │
  ▼
每个阶段按 SKILLS.md 调用对应子技能
  │
  ▼
产物沉淀到 docs/knowledge/ + GitHub Issues + OpenSpec artifacts
```

## 错误处理

- **依赖缺失**：`scripts/check-skill-dependencies.sh` 在启动时运行，缺失时暂停并给出安装命令。
- **路由置信度低**：Agent 列出 2-3 个候选模板，向 PM 提问确认。
- **OSS 搜索失败**：降级为 WebSearch 摘要，记录失败原因，不阻塞设计流程。
- **代码库知识构建失败**：允许 PM 手动提供功能摘要作为替代。
- **模板阶段缺失**：`stage_loader` 校验失败，提示补充对应 stage 目录。

## 融入已有项目

1. PM 在已有仓库运行 `claude lincoln-init --existing-project`。
2. Agent 自动调用 `workflow-router` 识别为 `existing-project-iteration`。
3. 运行 `build-codebase-knowledge`：基于源码生成现有功能知识库。
4. 后续新需求/bug 按标准流程迭代，所有产物关联回现有知识库。

## 测试策略

- `tests/test_skill_dependencies.py`：解析 `.claude/skill-dependencies.yaml`，检查所有 `required_skills` 已声明。
- `tests/test_workflow_router.py`：给定模拟仓库结构，验证路由推荐符合预期。
- `tests/test_build_codebase_knowledge.py`：验证扫描逻辑和产物格式。
- `tests/test_explore_opensource.py`：验证评估输出包含必要字段。
- `scripts/static-check.sh` 增加：
  - 校验 `skill-dependencies.yaml` 格式；
  - 校验所有模板 YAML 与 stage 目录一致性。

## 待实现计划（供 writing-plans 展开）

1. 创建 `.claude/skill-dependencies.yaml` 与 `scripts/check-skill-dependencies.sh`。
2. 创建 `lincoln-workflow-router` skill 与 `.claude/workflows/templates/` 下的 4 个新模板。
3. 扩展 `scripts/stage_loader.py` 支持按模板名加载工作流。
4. 创建 `lincoln-build-codebase-knowledge` skill 与对应 stage 目录。
5. 创建 `lincoln-explore-opensource` skill 与对应 stage/子技能调用。
6. 更新各阶段 `SKILLS.md`/`PROMPT.md`/`CHECKLIST.md`，纳入新技能。
7. 补充测试与静态检查。

## 未决问题

- `workflow-router` 是否允许 PM 在任意时刻切换模板？切换后如何处理已生成的产物？
- `build-codebase-knowledge` 对大型代码库（>100 文件）如何控制成本和 token？
- `explore-opensource` 的评分标准是否需要 PM 可配置？
- 是否需要为每个模板独立维护一套 `validators`？

## 结论

采用 **Approach 2**：通过 `workflow-router` 动态选择模板，配合 `.claude/skill-dependencies.yaml` 管理外部 skill 依赖，并新增 `lincoln-explore-opensource` 与 `lincoln-build-codebase-knowledge` 两个自定义 skill，在不重写引擎的前提下显著提升 Lincoln 的灵活性、覆盖率和可落地性。
