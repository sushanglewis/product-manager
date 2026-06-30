# Lincoln 技能路由指南

本文档是 Lincoln 框架的核心参考手册，描述五类外部能力仓库的全部技能、按阶段/类型/场景的路由规则，以及如何扩展路由表。

---

## 技能生态总览

Lincoln 作为编排层，不替代任何专业工具。每个阶段声明推荐技能集（required + optional），Agent 通过 `SKILLS.md` 和 `skill-routing.yaml` 知道本阶段可以调用哪些技能、触发条件、限制条件。

---

## 1. OpenSpec（变更提案与任务管理）

| 技能/命令 | 能力定位 | 典型触发阶段 |
|-----------|----------|--------------|
| `openspec:explore` | 变更前期的方案探索与澄清 | `clarify` / `design-spike` |
| `openspec:propose` | 生成完整变更提案（proposal.md、design.md、tasks.md、specs/） | `propose` |
| `openspec:apply-change` | 按任务实施变更 | `implement` |
| `openspec:sync-specs` | 将 delta spec 同步回主 spec | `sync-knowledge` |
| `openspec:archive-change` | 归档已完成的变更 | `ship` / `sync-knowledge` |

---

## 2. Superpowers（方法论子技能）

| 技能 | 能力定位 | 典型触发阶段 |
|------|----------|--------------|
| `superpowers:bootstrap` | 会话启动时的环境感知与技能发现 | `workflow-router` / 任意阶段启动 |
| `superpowers:brainstorming` | 需求/设计/UI 探索 | `clarify` / `product-design-docs` / `product-prototype` |
| `superpowers:planning` | 结构化计划与文档 | `clarify` / `tdd-development-plan` |
| `superpowers:writing-plans` | 文档与计划结构化 | `product-design-docs` / `tdd-development-plan` |
| `superpowers:test-driven-development` | TDD 红/绿/重构约束 | `tdd-development-plan` / `implement` |
| `superpowers:subagent-driven-development` | 用子 Agent 并行/分阶段实施 | `implement` / `split` |
| `superpowers:dispatching-parallel-agents` | 并行处理独立 Issue | `split` / `implement` |
| `superpowers:using-git-worktrees` | 隔离工作区 | `product-prototype` / `implement` |
| `superpowers:systematic-debugging` | 系统调试 | `implement` / `bug-fix` |
| `superpowers:finishing-a-development-branch` | 分支收尾、准备 PR | `implement` / `ship` |
| `superpowers:requesting-code-review` | 发起代码审查 | `implement` |
| `superpowers:receiving-code-review` | 处理审查反馈 | `implement` |
| `superpowers:verification-before-completion` | 完成前验证 | `propose` / `implement` / `sync-knowledge` |
| `superpowers:apply-review` | 审慎处理代码审查反馈 | `implement` |

---

## 3. Everything-Claude-Code（引擎与 Hooks 层）

| 能力 | 定位 | 典型触发 |
|------|------|----------|
| `ecc` engine + hooks | 强制执行阶段校验、限制副作用工具、追踪产物 | 所有阶段 |
| `pre-tool-use.sh` | 拦截未通过准入校验的副作用工具 | 所有阶段 |
| `post-tool-use.sh` | 记录产物与关键工具调用 | 所有阶段 |
| `on-session-start.sh` | 加载当前阶段上下文 | 所有会话 |

---

## 4. oh-my-claudecode（多 Agent 编排与增强模式）

| 技能 | 能力定位 | 典型触发阶段 |
|------|----------|--------------|
| `oh-my-claudecode:plan` | 复杂阶段的前期规划 | `clarify` / `product-design-docs` / `tdd-development-plan` |
| `oh-my-claudecode:team` | 多 Agent 并行协作 | `implement` / `split` |
| `oh-my-claudecode:verify` | 独立验证与审查 | `propose` / `implement` / `sync-knowledge` |
| `oh-my-claudecode:autopilot` | 自主执行已知任务 | `implement` |
| `oh-my-claudecode:ralph` | 自循环直到完成 | `implement` |
| `oh-my-claudecode:ultrawork` | 高强度批量执行 | `implement` / `split` |
| `oh-my-claudecode:deep-interview` | 深度访谈辅助 | `ingest` / `clarify` |
| `oh-my-claudecode:ai-slop-cleaner` | 清理低质量 AI 输出 | `sync-knowledge` / 任意文档阶段 |
| `oh-my-claudecode:wiki` | 知识库/wiki 维护 | `sync-knowledge` |
| `oh-my-claudecode:writer-memory` | 写作记忆 | `sync-knowledge` |

---

## 5. GSD（项目生命周期管理）

| 技能 | 能力定位 | 典型触发阶段 |
|------|----------|--------------|
| `gsd:new-project` | 新项目初始化 | `workflow-router` |
| `gsd:new-milestone` | 新里程碑 | `workflow-router` |
| `gsd:discuss-phase` | 规划前上下文澄清 | `clarify` / `plan-phase` |
| `gsd:spec-phase` | 明确阶段交付内容 | `product-design-docs` |
| `gsd:plan-phase` | 生成 PLAN.md | `tdd-development-plan` |
| `gsd:mvp-phase` | 垂直 MVP 切片规划 | `tdd-development-plan` |
| `gsd:ui-phase` | UI 设计合约 | `product-prototype` |
| `gsd:ai-integration-phase` | AI 功能设计合约 | `product-design-docs` / `product-prototype` |
| `gsd:execute-phase` | 执行阶段计划 | `implement` |
| `gsd:verify-work` | 对话式 UAT | `test/verify` |
| `gsd:ship` | 创建 PR 并准备合并 | `ship` |
| `gsd:code-review` | 代码审查 | `implement` / `test` |
| `gsd:eval-review` | AI 阶段评估审计 | `sync-knowledge` / `test` |
| `gsd:debug` | 失败调试 | `implement` / `bug-fix` |
| `gsd:import` | 外部计划导入与冲突检测 | `clarify` |
| `gsd:ingest-docs` | 启动 .planning/ 文档结构 | `existing-project-iteration` |
| `gsd:docs-update` | 文档更新与校验 | `sync-knowledge` |
| `gsd:forensics` | 失败诊断 | 任意阶段失败恢复 |
| `gsd:audit-uat` | UAT 与验证项审计 | `test/verify` |
| `gsd:milestone-summary` | 里程碑总结 | `sync-knowledge` |

---

## 按 Lincoln 阶段路由

| Lincoln Stage | Required Skills | Optional Skills | Human Gate |
|---------------|-----------------|-----------------|------------|
| **workflow-router** | `superpowers:bootstrap` | `gsd:new-project` / `gsd:new-milestone`, `oh-my-claudecode:plan` | 是 |
| **ingest** | — | `oh-my-claudecode:deep-interview` | 否 |
| **clarify** | `superpowers:brainstorming` | `gsd:import`, `gsd:discuss-phase`, `oh-my-claudecode:deep-interview`, `openspec:explore` | 是 |
| **product-design-docs** | `superpowers:brainstorming`, `superpowers:writing-plans` | `gsd:spec-phase`, `oh-my-claudecode:plan`, `openspec:propose`（早期草案） | 是 |
| **product-prototype** | `superpowers:brainstorming` | `gsd:ui-phase`, `superpowers:using-git-worktrees`, `oh-my-claudecode:designer` | 是 |
| **tdd-development-plan** | `superpowers:writing-plans`, `superpowers:test-driven-development` | `gsd:plan-phase`, `gsd:mvp-phase`, `oh-my-claudecode:plan` | 否 |
| **propose** | `openspec:propose` | `superpowers:verification-before-completion`, `oh-my-claudecode:verify` | 否 |
| **split** | `superpowers:dispatching-parallel-agents` | `gsd:phase`, `oh-my-claudecode:team` | 否 |
| **implement** | `superpowers:test-driven-development`, `superpowers:verification-before-completion` | `openspec:apply-change`, `superpowers:subagent-driven-development`, `superpowers:using-git-worktrees`, `superpowers:systematic-debugging`, `superpowers:finishing-a-development-branch`, `superpowers:requesting-code-review`, `superpowers:receiving-code-review`, `gsd:execute-phase`, `gsd:code-review`, `gsd:debug`, `oh-my-claudecode:team`, `oh-my-claudecode:autopilot`, `oh-my-claudecode:ralph`, `oh-my-claudecode:ultrawork` | 是 |
| **test/verify** | `superpowers:verification-before-completion`, `superpowers:receiving-code-review` | `gsd:verify-work`, `gsd:audit-uat`, `gsd:eval-review`, `oh-my-claudecode:verify`, `oh-my-claudecode:ultraqa` | 否 |
| **ship** | `superpowers:finishing-a-development-branch` | `openspec:archive-change`, `gsd:ship`, `oh-my-claudecode:release` | 否 |
| **sync-knowledge** | `gsd:docs-update` | `gsd:forensics`, `gsd:milestone-summary`, `openspec:sync-specs`, `oh-my-claudecode:wiki`, `oh-my-claudecode:writer-memory`, `superpowers:verification-before-completion` | 否 |

---

## 按项目类型路由

| 项目类型 | 入口模板 | 特殊技能注入 |
|----------|----------|--------------|
| 新需求（有访谈录音） | `interview-to-knowledge` | 标准路由 |
| 已有源码、知识库为空 | `existing-project-iteration` | 在 `workflow-router` 后增加 `gsd:ingest-docs` + `lincoln-build-codebase-knowledge` |
| 明确 bug/issue | `bug-fix` | `clarify` 阶段注入 `superpowers:debugging`、`gsd:debug`；`tdd-development-plan` 聚焦回归测试 |
| 方案预研 | `design-spike` | 终止于 `product-prototype` 或 `tdd-development-plan`，启用 `openspec:explore`、`oh-my-claudecode:plan` |
| 强依赖开源方案 | `oss-first-design` | `clarify` 后增加 `lincoln-explore-opensource`，`product-design-docs` 引用 OSS 方案 |
| 多 Agent 并行实施 | — | `implement` 阶段启用 `oh-my-claudecode:team` + `superpowers:dispatching-parallel-agents` |

---

## 按场景路由

| 场景 | 触发条件 | 推荐能力组合 |
|------|----------|--------------|
| 会话冷启动 | Agent 首次进入分支 | `superpowers:bootstrap` → `lincoln-status.py` → 当前阶段 `AGENTS.md` |
| 需求模糊 | `clarify` 阶段人类回答多次不明确 | `oh-my-claudecode:deep-interview` + `gsd:discuss-phase` |
| 设计冲突 | `product-design-docs` 阶段出现技术/业务冲突 | `gsd:import` + `superpowers:brainstorming` + 人工裁决 |
| UI 复杂 | `product-prototype` 阶段需要高保真原型 | `gsd:ui-phase` + Pencil MCP + `oh-my-claudecode:designer` |
| AI 功能 | 需求涉及 LLM/Agent/MCP | `gsd:ai-integration-phase` + `gsd:eval-review` |
| 并行开发 | 多个独立 Issue 可同时推进 | `superpowers:dispatching-parallel-agents` + `oh-my-claudecode:team` + git worktrees |
| 代码审查反馈复杂 | PR review 意见多或技术争议大 | `superpowers:apply-review` + `superpowers:receiving-code-review` + `gsd:code-review` |
| 失败恢复 | 阶段校验失败或 Agent 陷入循环 | `gsd:forensics` + `superpowers:systematic-debugging` + `oh-my-claudecode:debug` |

---

## 路由机制详解

### 四层路由体系

1. **默认路由**：`.claude/skill-routing.yaml` 定义全局默认映射。
   ```yaml
   routing:
     clarify:
       required: [superpowers:brainstorming]
       optional: [gsd:import, gsd:discuss-phase, oh-my-claudecode:deep-interview, openspec:explore]
       human_gate: true
     implement:
       required: [superpowers:test-driven-development, superpowers:verification-before-completion]
       optional: [openspec:apply-change, superpowers:subagent-driven-development, gsd:execute-phase, oh-my-claudecode:team]
       human_gate: true
   ```

2. **模板覆盖**：`.claude/workflows/templates/{template}.yaml` 可声明 `skill_overrides` 覆盖默认路由。
   ```yaml
   template: bug-fix
   skill_overrides:
     clarify:
       optional_add: [superpowers:systematic-debugging, gsd:debug]
       optional_remove: [openspec:explore]
   ```

3. **阶段路由**：每个 `.claude/stages/<stage>/SKILLS.md` 引用 `skill-routing.yaml` 中对应条目，并补充阶段特化说明。
   ```markdown
   ## 本阶段技能
   
   引用 `skill-routing.yaml` → `routing.implement`：
   - Required: `superpowers:test-driven-development`, `superpowers:verification-before-completion`
   - Optional: `openspec:apply-change`, `superpowers:subagent-driven-development`, ...
   
   ## 阶段特化
   - 若人类指定 `/team` 模式，启用 `oh-my-claudecode:team`
   - 若遇到调试需求，优先调用 `superpowers:systematic-debugging`
   ```

4. **动态选择**：Agent 通过 `scripts/lincoln-status.py` 知道当前阶段与推荐技能；若人类指定模式（如 `/team`），则按场景路由启用 `oh-my-claudecode:team`。

---

## 如何添加新技能到路由表

### 步骤 1：确认技能归属域

判断新技能属于哪个能力域：

- 变更提案/任务管理 → OpenSpec
- 方法论/开发规范 → Superpowers
- 引擎约束/Hooks → Everything-Claude-Code
- 多 Agent 编排/增强模式 → oh-my-claudecode
- 项目生命周期 → GSD
- Lincoln 专属 → 自定义（`lincoln-*` 前缀）

### 步骤 2：定义技能元数据

```yaml
# .claude/skill-routing.yaml 新增条目
routing:
  <stage_id>:
    required: [existing-skill, new-skill-id]    # 或加到 optional
    optional: [new-skill-id]
    human_gate: true/false
```

### 步骤 3：更新阶段 SKILLS.md

在对应阶段的 `.claude/stages/<stage>/SKILLS.md` 中引用新技能，说明触发条件与限制。

### 步骤 4：更新技能依赖清单

若新技能需要外部 CLI 或插件，在 `.claude/skill-dependencies.yaml` 中声明：

```yaml
optional:
  - id: new-skill-id
    cli: new-cli-command
    install_url: https://github.com/org/new-tool
    check_command: "new-cli --version"
```

### 步骤 5：更新文档

在本文档（`docs/framework/skill-routing-guide.md`）的对应能力域表格中添加新技能行。

### 步骤 6：验证

```bash
# 检查技能依赖
scripts/check-skill-dependencies.sh

# 验证路由一致性
pytest tests/test_skill_routing.py

# 验证阶段清单一致性
pytest tests/test_stage_manifest.py
```

---

## 自定义 Lincoln 技能

| 技能 | 触发条件 | 产物 | 归属阶段 |
|------|----------|------|----------|
| `lincoln-build-codebase-knowledge` | 已有源码但知识库为空 | `docs/knowledge/00-index.md` + feature docs | `existing-project-iteration` |
| `lincoln-explore-opensource` | 设计阶段可借鉴开源方案 | `docs/research/{change_name}-oss-options.md` | `oss-first-design` |
| `lincoln-workflow-router` | 工作流模板选择 | `.claude/workflow-state.yaml`（模板记录） | `workflow-router` |

添加自定义 Lincoln 技能时，需在 `docs/framework/skill-routing-guide.md` 的"自定义 Lincoln 技能"表格中登记，并在 `skill-routing.yaml` 中绑定到对应阶段。
