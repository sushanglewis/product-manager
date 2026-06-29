# Agent 行为规范

本文件定义了在 Lincoln 工作流模板中，Claude Code Agent 必须遵守的行为准则。所有 Agent 在操作本项目前必须先阅读本文件。

## 任务工具使用规范

`TaskCreate` / `TaskUpdate` 只能用于跟踪**已确定需要动手实施的工作项**，不能作为“准备发消息”、“稍后输出”或“内部占位”的心理替代品。

- **对话型阶段禁止使用任务工具**：在 `clarify`、`product-design-docs`、`product-prototype`、`implement` 等 `human_gate: true` 阶段，Agent 必须直接向人类 PM 发送消息，不得用 `TaskCreate`/`TaskUpdate` 暂存或拆分“发消息”动作。
- **实施阶段允许任务追踪**：在 `tdd-development-plan`、`propose`、`split`、`sync-knowledge` 等非对话阶段，可以使用任务工具跟踪已明确的执行步骤。
- **连续任务工具调用受限**：任何阶段连续调用 `TaskCreate`/`TaskUpdate` 超过 3 次且中间没有非任务动作时，hook 会强制暂停并要求 Agent 输出用户可见消息或执行其他操作。

违规时 `.claude/hooks/pre-tool-use.sh` 会拦截并报错。

## 阶段上下文加载

Agent 进入会话后，应首先确认当前分支和阶段：

1. 读取 `.claude/workflow-state.yaml` 了解 `current_run.current_stage`；
2. 若当前阶段不是 `not_started`，优先阅读 `.claude/stages/<current_stage>/AGENTS.md`、`CHECKLIST.md`、`SKILLS.md`；
3. 使用 `scripts/stage_loader.py --stage <stage> --action validate-entry` 运行准入校验；
4. 若 everything-claude-code hooks 已启用，hook 会自动拦截未通过准入校验的副作用工具；若 hooks 未启用，必须手动执行校验，禁止绕过。

## 核心原则

1. **工作流优先**：任何操作必须符合 `.claude/workflows/interview-to-knowledge.yaml` 定义的顺序和校验规则。
2. **人类确认节点不可跳过**：YAML 中标记 `human_gate: true` 的步骤，必须获得人类 PM 的显式确认才能继续。
3. **产物可追溯**：每个需求、每个功能都必须能关联回原始访谈时间戳、OpenSpec 变更、GitHub Issue/PR。
4. **知识库双轨维护**：每个合并的 issue 必须同时沉淀业务知识和技术知识到 Obsidian vault。
5. **不修改原始录音**：`recordings/` 目录中的文件只读，永远不在原地修改。
6. **Pencil 原型受控处理**：`.pen` 文件只能通过 Pencil 应用或 Pencil 工具处理，不用普通文件读取或编辑其内容。
7. **技能感知执行**：始终调用最适合当前阶段方法论需求的子技能，但子技能不能替代 `human_gate`。

## 集成技能生态

Lincoln 各阶段可调用以下子技能补充方法论：

| 阶段 | 调用技能 | 用途 |
|------|----------|------|
| clarify | `superpowers:brainstorming`, `gsd-import` | 方案探索、外部计划导入 |
| product-design-docs | `superpowers:brainstorming`, `superpowers:writing-plans` | 设计探索与文档结构化 |
| product-prototype | `superpowers:brainstorming`, `superpowers:using-git-worktrees` | UI 探索、原型隔离 |
| tdd-development-plan | `superpowers:writing-plans`, `superpowers:test-driven-development` | 计划拆分、TDD 约束 |
| propose | `superpowers:verification-before-completion` | 产物验证 |
| split | `superpowers:dispatching-parallel-agents`, `superpowers:verification-before-completion` | 并行建 Issue、回链验证 |
| implement | `superpowers:using-git-worktrees`, `superpowers:subagent-driven-development`, `superpowers:test-driven-development`, `superpowers:systematic-debugging`, `superpowers:finishing-a-development-branch`, `superpowers:requesting-code-review`, `superpowers:receiving-code-review`, `superpowers:verification-before-completion` | 按需辅助人类研发 |
| sync-knowledge | `gsd-docs-update`, `gsd-forensics` | 文档生成与失败诊断 |

### 调用规则

1. `human_gate: true` 阶段，子技能仅用于探索或结构化，**不得替代人类确认**。
2. 任何实施类技能（如 `subagent-driven-development`、`executing-plans`）必须在 PM 明确批准后才能调用。
3. 调用 GSD 技能时使用 `Skill` 工具，技能名即上表所示；不使用 Codex 的 `$gsd-*` 语法。

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

## 新增自定义技能

| 技能 | 触发条件 | 产物 |
|------|----------|------|
| `lincoln-build-codebase-knowledge` | 已有源码但知识库为空 | `docs/knowledge/00-index.md` + feature docs |
| `lincoln-explore-opensource` | 设计阶段可借鉴开源方案 | `docs/research/{change_name}-oss-options.md` |

## 工作流步骤

### 1. process-interview

- 只在用户手动触发时执行
- 校验音频文件存在、格式受支持
- 使用 Whisper 生成带时间戳的 transcript
- 生成 summary 和 raw-insights
- 失败时暂停并给出修复建议

### 2. clarify-requirements

- 基于 transcript 和 summary 向人类 PM 提问
- 一次最多提出 3 个澄清问题
- 将 PM 的回答写入 `requirements/<session>/requirements.md`
- 人类可直接编辑 requirements.md，编辑后运行 `workflow-continue`
- 只有人类输入 `confirm` 或通过文件修改触发继续时，才能进入下一步

### 3. draft-product-design

- 只在 requirements 已确认后执行
- 生成 `designs/<design_id>/` 下的简洁设计评审包
- 必须覆盖场景、功能清单、数据结构、流程图/序列图/架构图、业务可行性、技术可行性、开源项目和技术框架建议
- 技术框架和开源项目建议必须查当前官方文档或主仓库
- 人类 PM 确认后，才能进入原型阶段

### 4. build-product-prototype

- 基于已确认设计文档生成 `fields.md`、`ui-spec.md` 和 `prototype.pen`
- 创建或修改 `.pen` 前必须通过 Pencil 工具读取 editor state/schema
- 人类 PM 可以直接在 Pencil 应用中修改并保存 `.pen`
- PM 确认后的 `.pen` 是最终开发参照

### 5. plan-tdd-development

- 基于已确认设计文档、字段规格、UI 规格和 `prototype.pen` 生成 `tdd-plan.md`
- TDD plan 必须包含验收映射、测试场景、红/绿/重构步骤、任务切片和回归范围
- 不在该步骤生成 OpenSpec artifact

### 6. propose-with-openspec

- 调用 `openspec propose <change-name>` CLI 直接生成 artifact
- 读取 `designs/<design_id>/tdd-plan.md` 作为输入
- OpenSpec artifact 必须引用 TDD plan、Pencil 原型和核心设计文档
- 校验生成的 artifact 完整（proposal.md、specs/、design.md、tasks.md）
- 不绕过 OpenSpec CLI 手动生成 artifact

### 7. split-to-github

- 读取 `openspec/changes/<change>/tasks.md`
- 按任务拆分 GitHub Issues
- 目标仓库来自 `.github/openspec-config.yml`
- 每个 Issue 必须包含：标题、用户故事、验收标准、来源访谈、时间戳、需求链接、OpenSpec 变更链接
- Issue 创建后，更新 requirements.md 记录 issue 编号

### 8. sync-to-knowledge

- 在 PR 合并后触发
- 读取代码 diff、对应 issue、需求文档、OpenSpec design
- 创建或更新 `docs/knowledge/03-features/<feature-slug>.md`
- 文档必须同时包含业务知识和技术知识
- 使用 Obsidian wikilinks 建立关联
- 检查是否与已有知识冲突，有冲突则暂停等待人类处理

## 文件操作规范

- 始终创建新文件/新对象，不直接修改已有文件的核心内容（除非是人类明确要求的修正）
- 每次修改需求文档后，保留修改历史或变更说明
- 所有 JSON/YAML 文件必须格式正确
- Markdown 文件使用统一的 frontmatter 格式
- 不使用普通文本工具读取或修改 `.pen` 文件；需要检查原型时使用 Pencil 应用或 Pencil 工具。

## 校验规则

每个步骤执行前后必须调用统一 validator runner：

- runner：`.claude/skills/interview-workflow/validators/validate.py`
- entry check：`python .claude/skills/interview-workflow/validators/validate.py --phase entry --check <name> --args <comma-separated-args>`
- exit check：`python .claude/skills/interview-workflow/validators/validate.py --phase exit --check <name> --args <comma-separated-args>`

校验失败时：
1. 立即停止当前 loop
2. 向人类报告失败的校验项
3. 给出明确的修复建议
4. 等待人类处理，不自动重试超过 1 次

## 沟通风格

- 使用中文与人类 PM 交流
- 汇报进度时简洁，重点说明当前步骤、产物位置、下一步需要人类做什么
- 不确定时暂停并提问，不猜测

## 文档约定

- 描述能力更新时，**禁止使用“本次迭代”这类时间相对词**。必须关联到具体的 release 版本号（如 `v1.1.0`），或使用已通过版本控制的变更标识。
- 新增能力摘要应放在 README 的显眼位置，并使用版本号作为小节标题或前缀。
- 创建 release 后，应及时更新 README 中的版本号引用，确保文档与 release 一致。

## 禁止事项

- 禁止在没有人类确认的情况下创建 GitHub Issues
- 禁止删除 `recordings/` 中的原始文件
- 禁止在 requirements 未确认时直接生成 OpenSpec artifact
- 禁止在产品设计文档或 Pencil 原型未确认时生成 TDD plan 或 OpenSpec artifact
- 禁止绕过校验继续工作流
- 禁止在 knowledge vault 中创建没有来源链接的功能文档
