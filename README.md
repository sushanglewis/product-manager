# Lincoln — 产品经理需求调研工作流模板

> **Lincoln 是什么？** Lincoln 是一个基于 **Conductor + Claude Code + OpenSpec + GitHub + Obsidian** 的 AI 原生产品管理工作流模板仓库。它提供从需求访谈到代码实现、再到知识库沉淀的完整工作流，通过阶段化、门控化、技能路由化的方式，让 Agent 和人类在各自擅长的环节高效协作。

> **你是 Lincoln 开发者还是使用者？**
> - **使用者**（产品经理、设计师、工程师）：直接跳到 [快速开始](#快速开始)，选择你的场景入口。
> - **开发者**（工作流开发者、框架维护者）：阅读 [框架文档](#框架文档)，了解 Lincoln 元模型、技能路由与扩展机制。

> 完整的用户旅程与角色路径说明见 [`docs/framework/user-journey.md`](docs/framework/user-journey.md)。

---

## 快速开始

在 GitHub 上点击 **Use this template**，创建新项目仓库，然后 clone 到本地 Conductor 工作区。

### 场景 A：从访谈录音开始（interview-to-knowledge）

适合：有利益相关者访谈录音，需要从中提取需求并推进到研发。

```bash
# 1. 放入访谈录音
cp ~/Downloads/2026-06-27-stakeholder.m4a recordings/

# 2. 初始化 Lincoln 分支
scripts/init-lincoln-branch.sh 2026-06-27-stakeholder checkout-redesign --push

# 3. 触发工作流
claude process-interview recordings/2026-06-27-stakeholder.m4a
claude clarify-requirements 2026-06-27-stakeholder
claude draft-product-design 2026-06-27-stakeholder checkout-redesign
claude build-product-prototype 2026-06-27-stakeholder checkout-redesign
claude plan-tdd-development 2026-06-27-stakeholder checkout-redesign
claude propose-with-openspec 2026-06-27-stakeholder checkout-redesign add-csv-export
claude split-to-github 2026-06-27-stakeholder add-csv-export
# 研发完成后
claude sync-to-knowledge <issue-number> <pr-number>
```

### 场景 B：已有代码库但无知识库（existing-project-iteration）

适合：项目已有源码，但缺乏结构化的功能知识库，需要补全文档后再迭代。

```bash
# 1. 初始化 Lincoln 分支
scripts/init-lincoln-branch.sh <session-id> <design-id> --push

# 2. 运行 workflow-router，选择 existing-project-iteration 模板
# Agent 会自动扫描代码库并生成 docs/knowledge/ 功能文档

# 3. 进入 clarify 阶段后，按标准流程推进
```

### 场景 C：明确 bug/issue（bug-fix）

适合：已有明确的 bug 报告或 issue，需要快速定位、修复、验证。

```bash
# 1. 初始化 Lincoln 分支
scripts/init-lincoln-branch.sh <session-id> <design-id> --push

# 2. 运行 workflow-router，选择 bug-fix 模板
# clarify 阶段会自动注入 superpowers:debugging 和 gsd:debug 技能
# tdd-development-plan 阶段聚焦回归测试
```

### 场景 D：方案预研（design-spike / oss-first-design）

适合：需求尚不明确，需要先做技术方案预研或调研开源方案。

```bash
# 1. 初始化 Lincoln 分支
scripts/init-lincoln-branch.sh <session-id> <design-id> --push

# 2. 运行 workflow-router，选择 design-spike 或 oss-first-design 模板
# design-spike：终止于 product-prototype 或 tdd-development-plan
# oss-first-design：clarify 后自动触发 lincoln-explore-opensource 调研
```

---

## 新增能力（v1.1.0）

- **技能依赖清单**：`.claude/skill-dependencies.yaml` 显式声明 `superpowers`、`gsd`、`openspec` 等外部依赖，配合 `scripts/check-skill-dependencies.sh` 一键检查。
- **工作流路由**：新增 `lincoln-workflow-router`，根据仓库上下文选择最合适的工作流模板，不再只有单一固定流程。
- **多模板支持**：除默认 `interview-to-knowledge` 外，新增 `existing-project-iteration`、`bug-fix`、`design-spike`、`oss-first-design` 模板。
- **自定义 Lincoln 技能**：
  - `lincoln-build-codebase-knowledge`：扫描已有代码库，生成 `docs/knowledge/` 功能文档。
  - `lincoln-explore-opensource`：在设计阶段调研可借鉴的开源方案，输出 `docs/research/{change_name}-oss-options.md`。
- **更密集的技能调用**：各阶段已绑定 `superpowers:brainstorming`、`superpowers:writing-plans`、`superpowers:test-driven-development`、`superpowers:verification-before-completion`、`gsd-import`、`gsd-docs-update` 等方法论子技能。

---

## 工作状态与交接

每个 Lincoln 分支都有实时状态报告和交接机制，确保跨窗口、跨人机协作不丢上下文。

### 查看当前分支状态

```bash
python scripts/lincoln-status.py --format table
```

输出包含：当前阶段、等待对象、已加载上下文、推荐技能、产物状态、下一步动作。支持 `--format json|table|markdown`。

### 生成交接文档

当需要暂停工作或切换协作者时：

```bash
python scripts/stage_loader.py --stage <current-stage> --action handoff-report
```

生成 `.context/lincoln-handoff.md`，包含当前阶段、已确认产物、待解决问题、下一角色、推荐技能。

### 查看所有进行中的 Lincoln 分支

```bash
scripts/list-active-lincoln-branches.sh
# 仅查看等待我的分支
scripts/list-active-lincoln-branches.sh --waiting-for-me
```

### 审计工作流健康度

```bash
python scripts/lincoln-audit.py --format markdown
```

输出 PASS/WARN/FAIL 报告，覆盖状态一致性、产物完整性、门控合规性、技能覆盖、异常检测。

---

## 框架文档

Lincoln 框架的核心设计文档：

- [`docs/framework/framework-design.md`](docs/framework/framework-design.md) — Lincoln 元模型：Stage、Gate、Artifact、Skill、Role、Template 的定义与能力边界。
- [`docs/framework/skill-routing-guide.md`](docs/framework/skill-routing-guide.md) — 完整技能路由表：按阶段、项目类型、场景映射外部技能仓库能力。
- [`docs/framework/evaluation-rubric.md`](docs/framework/evaluation-rubric.md) — Lincoln 健康度评估维度与自动/人工检查项。
- [`docs/framework/user-journey.md`](docs/framework/user-journey.md) — 按角色与场景的使用旅程指南。

---

## 分支级工作流与阶段状态

每个需求使用独立的 Lincoln feature 分支，阶段状态随分支提交：

```bash
# 创建新需求分支（从 main 切出）
scripts/init-lincoln-branch.sh <session-id> <design-id> --push

# 查看所有进行中的 Lincoln 分支
scripts/list-active-lincoln-branches.sh
```

分支命名：`lincoln/<session-id>-<design-id>`，例如 `lincoln/2026-06-27-stakeholder-checkout-redesign`。

阶段状态保存在 `.claude/workflow-state.yaml`，关键规则：
- 状态文件是**分支级**的，不同 feature 分支互不干扰；
- PM 在本地推进阶段后，**push feature 分支**到远程，不合并 `main`；
- 下游角色（测试、研发）checkout 同一 feature 分支继续；
- 每个阶段都有 `.claude/stages/<stage-id>/` 下的专属上下文（AGENTS.md、CHECKLIST.md、SKILLS.md、PROMPT.md）。

Agent 启动时会通过 hook 加载当前阶段上下文；若 hook 未启用，Agent 必须手动调用 `scripts/stage_loader.py` 执行准入/准出校验。

---

## 工作流概览

```
访谈录音 → 转写摘要 → 需求澄清 → 产品设计 → Pencil 原型 → TDD 研发计划 → OpenSpec 提案 → GitHub Issues → 代码实现 → PR 合并 → Obsidian 知识库
```

## 技能生态与工作流模板

Lincoln 默认走 `interview-to-knowledge` 模板，但根据项目上下文也可切换到其他模板：

| 上下文 | 推荐模板 |
|--------|----------|
| 有访谈录音 | `interview-to-knowledge` |
| 已有源码但知识库为空 | `existing-project-iteration` |
| 明确 bug/issue | `bug-fix` |
| 仅方案预研 | `design-spike` |
| 强依赖开源方案 | `oss-first-design` |

Agent 通过 `lincoln-workflow-router` 评估上下文并推荐模板，经 PM 确认后写入 `.claude/workflow-state.yaml`。

外部技能依赖声明在 `.claude/skill-dependencies.yaml`，运行 `scripts/check-skill-dependencies.sh` 可检查是否已安装：

```bash
scripts/check-skill-dependencies.sh
```

各阶段可调用的方法论子技能包括：

- `superpowers:brainstorming` — 需求/设计/UI 探索
- `superpowers:writing-plans` — 文档与计划结构化
- `superpowers:test-driven-development` — TDD 红/绿/重构约束
- `superpowers:verification-before-completion` — 产物完成前验证
- `superpowers:dispatching-parallel-agents` — 并行处理独立 Issue
- `superpowers:using-git-worktrees` — 隔离工作区
- `gsd-import` — 外部计划导入与冲突检测
- `gsd-docs-update` / `gsd-forensics` — 知识库生成与失败诊断

---

## 目录结构

```
.
├── recordings/              # 原始音频（gitignored）
├── interviews/              # 转写和摘要产物
├── requirements/            # 需求文档
├── designs/                 # 产品设计文档、Pencil 原型和 TDD 研发计划
├── openspec/                # OpenSpec 变更目录
├── docs/knowledge/          # 项目独立 Obsidian vault
├── docs/framework/          # Lincoln 框架设计文档
├── .claude/                 # Claude Code skill 与工作流
│   ├── stages/              # 阶段上下文（AGENTS.md / CHECKLIST.md / SKILLS.md / PROMPT.md）
│   ├── skill-routing.yaml   # 阶段→技能映射
│   └── workflow-state.yaml  # 分支级工作流状态
├── .context/                # 交接文档（lincoln-handoff.md）
├── .github/                 # GitHub issue 模板、Actions、配置
└── scripts/                 # 初始化脚本、状态命令、审计工具
```

---

## 依赖

- `ffmpeg`
- `faster-whisper` 或 OpenAI Whisper API key
- `gh` CLI（已登录）
- `openspec` CLI：`npm install -g @fission-ai/openspec`
- Pencil 应用或 Pencil MCP（用于 `.pen` 原型）
- `ecc` CLI（来自 everything-claude-code）
- Obsidian（可选，用于可视化浏览 vault）

此外，Lincoln 依赖若干外部 skill/CLI，清单见 `.claude/skill-dependencies.yaml`。初始化或升级后请运行：

```bash
scripts/check-skill-dependencies.sh
```

---

## 规范约束

Agent 必须遵守：
- `.claude/AGENTS.md` — Agent 行为总则
- `CLAUDE.md` — Agent 启动自检与汇报契约（分支级上下文加载、阶段汇报、技能调用规范）
- `.claude/workflows/interview-to-knowledge.yaml` — 工作流定义
- `.claude/skills/interview-workflow/validators/validate.py` — 准入准出校验 runner

人类产品经理拥有以下节点的最终确认权：
- 需求澄清完成
- 产品设计文档确认
- Pencil 原型确认
- OpenSpec 提案确认
- GitHub Issues 拆分确认
- 研发实现完成

---

## 了解更多

- [OpenSpec 文档](https://github.com/Fission-AI/openspec)
- [Obsidian WikiLinks](https://help.obsidian.md/Linking+notes+and+files/Internal+links)
