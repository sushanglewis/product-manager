# OpenSpec 提案阶段入口提示

你正在执行 Lincoln 工作流的 **propose**（OpenSpec 提案）阶段。

## 当前阶段状态

- **阶段 ID**: `propose`
- **阶段名称**: OpenSpec 提案
- **阶段类型**: Agent 自主执行（`human_gate: false`）
- **前置阶段**: `tdd-development-plan`（TDD 研发计划）
- **后续阶段**: `split`（拆分到 GitHub）

## 阶段目标

基于已确认的 TDD 研发计划，调用 OpenSpec CLI 生成标准变更提案 artifact，将 TDD 计划转化为结构化的 OpenSpec 变更提案。

## 执行指令

1. **读取完整提示文件**: `.claude/skills/interview-workflow/prompts/propose-with-openspec.md`
   - 该文件包含详细的 OpenSpec CLI 调用步骤和 artifact 验证规则
   - 按照提示文件中的步骤 1-9 执行

2. **阶段状态感知**:
   - 检查 `.claude/workflow-state.yaml` 中的 `stages.propose` 状态
   - 若状态为 `completed`，检查是否需要重新生成（人类要求时）
   - 若状态为 `validation_failed`，根据 `error_message` 修复后重试
   - 若人类运行 `workflow-continue`，重新读取 OpenSpec artifact 并重新校验

3. **变量替换**:
   - 使用 `state.variables.session_id` 作为会话标识
   - 使用 `state.variables.design_id` 作为设计标识
   - 使用 `state.variables.change_name` 作为 OpenSpec 变更名称

## 产物清单

阶段完成后必须存在以下产物：

- `openspec/changes/{change_name}/proposal.md`
- `openspec/changes/{change_name}/specs/*.md`（至少一个文件）
- `openspec/changes/{change_name}/design.md`
- `openspec/changes/{change_name}/tasks.md`

## 执行流程

1. 运行准入校验器确认 TDD 计划已标记 `ready-for-openspec`
2. 读取所有设计文档和 TDD 计划作为输入
3. 检查 `openspec/changes/{change_name}/` 是否已存在，存在时询问人类是否覆盖
4. 按优先级调用 OpenSpec CLI：
   - 优先：`openspec propose {change_name} --from designs/{design_id}/tdd-plan.md`
   - 次选：`openspec propose {change_name}` 并 pipe TDD 计划内容
   - 失败时读取 `openspec propose --help` 并适配
5. 调用 `superpowers:verification-before-completion` 验证 artifact：先运行退出校验并阅读输出，确认 0 失败
6. 验证生成的 artifact 文件存在且非空
7. 验证 artifact 引用 TDD 计划、Pencil 原型和核心设计文档
8. 运行退出校验器验证 artifact 完整性和任务提取

## 完成后操作

1. 运行退出校验器验证 artifact 完整性和引用完整性
2. 更新 `workflow-state.yaml` 中 `stages.propose` 状态为 `completed`
3. 向人类汇报：
   - OpenSpec 提案已生成
   - 产物存放路径：`openspec/changes/{change_name}/`
   - 下一阶段入口：`split`（运行 `claude split-to-github <session_id> <change_name>`）

## 关键提醒

- **TDD 计划必须就绪**：未标记 `ready-for-openspec` 不得调用 OpenSpec CLI
- **不绕过 CLI**：所有 artifact 必须通过 OpenSpec CLI 生成，禁止手动创建
- **保留原始结构**：不修改 OpenSpec CLI 生成的文件结构和格式
- **引用完整性**：artifact 必须引用 TDD 计划、Pencil 原型和核心设计文档
- **覆盖确认**：若 `openspec/changes/{change_name}/` 已存在，需询问人类是否覆盖
- **支持直接编辑**：人类可编辑 OpenSpec artifact 后运行 `workflow-continue`
