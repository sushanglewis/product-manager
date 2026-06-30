# Lincoln 用户旅程

本文档描述不同角色使用 Lincoln 的完整路径。阅读前请先确认：

> **自检**：你是在**开发 Lincoln 框架本身**，还是在**用 Lincoln 管理产品需求**？
> - 如果是前者，请阅读 `docs/framework/framework-design.md` 和 `docs/framework/skill-routing-guide.md`。
> - 如果是后者，继续阅读本页，找到你的入口场景。

---

## 四种入口场景

### 场景一：新需求（有访谈录音）

最标准的 Lincoln 工作流，从用户访谈到知识库沉淀。

**命令序列**：

```bash
# 1. 创建需求分支
scripts/init-lincoln-branch.sh <session-id> <design-id> --push

# 2. 放入录音并处理
claude process-interview recordings/<session-id>.m4a

# 3. 需求澄清（多轮对话，人类 PM 确认）
claude clarify-requirements <session-id>

# 4. 产品设计文档（人类 PM 确认）
claude draft-product-design <session-id> <design-id>

# 5. Pencil 原型（人类 PM 确认）
claude build-product-prototype <session-id> <design-id>

# 6. TDD 研发计划
claude plan-tdd-development <session-id> <design-id>

# 7. OpenSpec 提案
claude propose-with-openspec <session-id> <design-id> <change-name>

# 8. 拆分到 GitHub Issues
claude split-to-github <session-id> <change-name>

# 9. 研发实现（Engineer  checkout 同一分支）
# ... 基于 GitHub Issues 开发，提交 PR ...

# 10. 同步到知识库
claude sync-to-knowledge <issue-number> <pr-number>
```

**预期产物**：

| 阶段 | 产物 | 人工门控 |
|------|------|----------|
| process-interview | `interviews/<session>/transcript.md`、`summary.md`、`raw-insights.md` | 否 |
| clarify-requirements | `requirements/<session>/requirements.md`、`user-stories.md`、`prd.md` | **是** |
| draft-product-design | `designs/<design-id>/design-review.md`、`scenarios.md`、`feature-catalog.md`、`data-model.md`、`flows.md`、`feasibility.md` | **是** |
| build-product-prototype | `designs/<design-id>/fields.md`、`ui-spec.md`、`prototype.pen` | **是** |
| plan-tdd-development | `designs/<design-id>/tdd-plan.md` | 否 |
| propose-with-openspec | `openspec/changes/<change>/proposal.md`、`design.md`、`tasks.md`、`specs/` | 否 |
| split-to-github | GitHub Issues | 否 |
| implement | PR | 否 |
| sync-to-knowledge | `docs/knowledge/` 下的业务/技术知识文档 | 否 |

**推荐技能**：`superpowers:brainstorming`、`superpowers:writing-plans`、`superpowers:test-driven-development`、`gsd:discuss-phase`、`gsd:spec-phase`、`gsd:plan-phase`

---

### 场景二：已有代码库，知识库为空

已有源码但缺乏功能文档，需要 Lincoln 帮助建立知识库。

**命令序列**：

```bash
# 1. 工作流路由选择 existing-project-iteration 模板
claude lincoln-workflow-router

# 2. 扫描代码库生成知识文档
claude lincoln-build-codebase-knowledge

# 3. 继续标准流程：clarify → product-design-docs → ...
claude clarify-requirements <session-id>
```

**预期产物**：

| 阶段 | 产物 | 人工门控 |
|------|------|----------|
| workflow-router | `.claude/workflow-state.yaml`（模板选择记录） | 否 |
| lincoln-build-codebase-knowledge | `docs/knowledge/00-index.md` + 功能文档 | **是**（确认知识覆盖度） |
| clarify-requirements | `requirements/<session>/requirements.md` | **是** |

**推荐技能**：`gsd:ingest-docs`、`lincoln-build-codebase-knowledge`、`superpowers:brainstorming`

---

### 场景三：Bug 修复

明确的 bug/issue，快速走精简流程。

**命令序列**：

```bash
# 1. 工作流路由选择 bug-fix 模板
claude lincoln-workflow-router

# 2. 需求澄清（聚焦问题描述与复现步骤）
claude clarify-requirements <session-id>

# 3. TDD 研发计划（聚焦回归测试）
claude plan-tdd-development <session-id> <design-id>

# 4. 研发实现
# ... 基于 GitHub Issue 开发，提交 PR ...

# 5. 验证与 Ship
claude sync-to-knowledge <issue-number> <pr-number>
```

**预期产物**：

| 阶段 | 产物 | 人工门控 |
|------|------|----------|
| clarify-requirements | `requirements/<session>/requirements.md`（含复现步骤） | **是** |
| plan-tdd-development | `designs/<design-id>/tdd-plan.md`（聚焦回归测试） | 否 |
| implement | PR（含修复 + 回归测试） | 否 |

**推荐技能**：`superpowers:systematic-debugging`、`gsd:debug`、`superpowers:test-driven-development`

---

### 场景四：方案预研 / 开源优先设计

不确定技术方案，需要快速探索或调研开源项目。

**命令序列**：

```bash
# 1. 工作流路由选择 design-spike 或 oss-first-design 模板
claude lincoln-workflow-router

# 2. 需求澄清
claude clarify-requirements <session-id>

# 3. 开源方案调研（仅 oss-first-design）
claude lincoln-explore-opensource <change-name>

# 4. 产品设计文档
claude draft-product-design <session-id> <design-id>

# 5. 终止或继续（design-spike 可在此终止）
# 若继续：product-prototype → tdd-development-plan → ...
```

**预期产物**：

| 阶段 | 产物 | 人工门控 |
|------|------|----------|
| clarify-requirements | `requirements/<session>/requirements.md` | **是** |
| lincoln-explore-opensource | `docs/research/<change-name>-oss-options.md` | **是** |
| draft-product-design | `designs/<design-id>/design-review.md` | **是** |

**推荐技能**：`openspec:explore`、`oh-my-claudecode:plan`、`lincoln-explore-opensource`

---

## 角色视角

### PM（产品经理）

**核心职责**：需求澄清、设计确认、门控裁决。

**常用命令**：

```bash
claude process-interview <recording>
claude clarify-requirements <session-id>
claude draft-product-design <session-id> <design-id>
claude build-product-prototype <session-id> <design-id>
```

**关键产物所有权**：`requirements/`、`designs/` 下所有需人类确认的文件。

**门控节点**：必须在以下节点显式确认后才能继续：
- 需求澄清完成
- 产品设计文档确认
- Pencil 原型确认
- OpenSpec 提案确认
- GitHub Issues 拆分确认

### Designer（设计师）

**核心职责**：UI/UX 设计、Pencil 原型输出。

**常用命令**：

```bash
claude build-product-prototype <session-id> <design-id>
# 在 Pencil 应用中打开并修改 .pen 文件
```

**关键产物所有权**：`designs/<design-id>/prototype.pen`。

**注意**：`.pen` 文件只能通过 Pencil 应用或 Pencil 工具处理，不用普通文本工具读取或编辑。

### Engineer（工程师）

**核心职责**：基于 GitHub Issues 开发、提交 PR、编写测试。

**常用命令**：

```bash
# checkout 同一 feature 分支
git checkout lincoln/<session-id>-<design-id>

# 基于 GitHub Issues 开发
# 提交 PR
```

**关键产物所有权**：代码实现、测试、PR。

**注意**：研发实现阶段 Agent 可调用 `superpowers:test-driven-development`、`superpowers:subagent-driven-development`、`superpowers:using-git-worktrees` 等方法论技能辅助，但不得绕过人类确认节点。

### Tech Lead（技术负责人）

**核心职责**：架构决策、技术可行性评估、跨阶段协调。

**常用命令**：

```bash
# 查看当前分支状态
python scripts/lincoln-status.py --format markdown

# 审计工作流健康度
python scripts/lincoln-audit.py

# 查看所有进行中的 Lincoln 分支
scripts/list-active-lincoln-branches.sh
```

**关键职责**：
- 确认技术可行性评估（`designs/<design-id>/feasibility.md`）
- 裁决设计冲突
- 审核 PR 中的技术方案与 Lincoln 设计文档的一致性

### Workflow Developer（工作流开发者）

**核心职责**：开发 Lincoln 框架本身、维护模板、配置技能路由。

**常用命令**：

```bash
# 检查技能依赖
scripts/check-skill-dependencies.sh

# 验证阶段定义
python scripts/stage_loader.py --action validate-entry --stage <stage>

# 运行全量测试
pytest tests/
```

**关键产物所有权**：`.claude/workflows/`、`.claude/stages/`、`docs/framework/`、`scripts/`。

**注意**：修改框架元模型或技能路由时，需同步更新 `docs/framework/framework-design.md` 和 `docs/framework/skill-routing-guide.md`。

---

## 首次使用检查清单

### 依赖安装

- [ ] `ffmpeg` — 音频处理
- [ ] `faster-whisper` 或 OpenAI Whisper API key — 语音转写
- [ ] `gh` CLI（已登录 GitHub）— GitHub 操作
- [ ] `openspec` CLI：`npm install -g @fission-ai/openspec` — 变更提案
- [ ] Pencil 应用或 Pencil MCP — 原型设计
- [ ] `ecc` CLI（来自 everything-claude-code）— 引擎约束
- [ ] Obsidian（可选）— 可视化浏览 vault

### GitHub 配置

- [ ] 编辑 `.github/openspec-config.yml`，将 `owner` 和 `name` 改成真实目标仓库
- [ ] 运行 `scripts/init-project.sh` 完成初始化
- [ ] 验证 `scripts/check-skill-dependencies.sh` 通过

### Obsidian 配置（可选）

- [ ] 打开 `docs/knowledge/` 作为 Obsidian vault
- [ ] 安装 Obsidian 社区插件：Dataview、Templater（可选）
- [ ] 验证 wikilinks 能正确链接到功能文档

### 角色选择

- [ ] 确认你的角色（PM / Designer / Engineer / Tech Lead / Workflow Developer）
- [ ] 根据角色阅读上方"角色视角"对应章节
- [ ] 找到你的入口场景，按命令序列执行

---

## 持续迭代 vs 首次使用

**首次使用**：按上方"首次使用检查清单"逐项完成，从 `workflow-router` 开始选择模板。

**持续迭代**：
- 已有 Lincoln 分支时，直接 `git checkout lincoln/<session-id>-<design-id>`
- 运行 `python scripts/lincoln-status.py` 了解当前阶段和下一动作
- 继续推进或等待人类门控确认
- 每次阶段推进后 push feature 分支到远程，不合并 `main`
