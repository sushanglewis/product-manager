# OpenSpec 提案阶段 Agent 行为规范

## 阶段目的

基于已确认的 TDD 研发计划，调用 OpenSpec CLI 生成标准变更提案 artifact 目录（`openspec/changes/{change_name}/`），将 TDD 计划转化为结构化的 OpenSpec 变更提案，作为后续 GitHub Issues 拆分和研发实现的依据。

## 准入条件

1. `tdd_plan_ready` — `designs/{design_id}/tdd-plan.md` 包含 `<!-- status: ready-for-openspec -->`
2. 未满足准入条件时，工作流必须暂停并提示人类先完成 `tdd-development-plan` 阶段

## 允许的操作

- 读取 `requirements/{session_id}/requirements.md`（需求来源）
- 读取 `designs/{design_id}/` 下的所有设计产物：
  - `tdd-plan.md`、`design-review.md`、`feature-catalog.md`
  - `data-model.md`、`flows.md`、`feasibility.md`
  - `fields.md`、`ui-spec.md`
- 调用 OpenSpec CLI：`openspec propose {change_name}`
  - 优先尝试：`openspec propose {change_name} --from designs/{design_id}/tdd-plan.md`
  - 次选：`openspec propose {change_name}` 并 pipe TDD 计划内容
  - 失败时读取 `openspec propose --help` 并适配
- 验证生成的 OpenSpec artifact 完整性
- 检查 `openspec/changes/{change_name}/` 是否已存在，存在时询问人类是否覆盖

## 禁止的操作

- **禁止在 TDD 计划未标记 ready-for-openspec 时调用 OpenSpec CLI**
- **禁止绕过 OpenSpec CLI 手动生成 artifact 文件**（proposal.md、specs/、design.md、tasks.md）
- **禁止修改 OpenSpec CLI 生成的文件结构**
- 禁止修改 `designs/{design_id}/` 下的任何设计文档
- 禁止修改 `requirements/` 目录下的需求文档
- 禁止绕过校验继续工作流

## 副作用策略

- 产物写入 `openspec/changes/{change_name}/` 目录
- 不修改任何已有设计文档或需求文档
- 不修改 `tdd-plan.md`（只读取）
- 保留 OpenSpec CLI 生成的原始结构
- 人类可直接编辑 OpenSpec artifact，编辑后运行 `workflow-continue`

## 人类确认节点

本阶段 **无** `human_gate: true`，为 Agent 自主执行阶段。

- 但产物质量由 `openspec_artifact_complete` 和 `tasks_extracted` 退出校验严格把关
- 校验失败时暂停，等待人类修复或指示
- 人类可直接编辑 OpenSpec artifact 后运行 `workflow-continue`
- 隐式确认：通过退出校验即视为可进入下一阶段
- 若 `openspec/changes/{change_name}/` 已存在，需询问人类是否覆盖

## 下一阶段

- 成功完成后进入 `split`（拆分到 GitHub）阶段
- 下一阶段的准入校验：检查 `openspec/changes/{change_name}/tasks.md` 是否包含可识别的任务列表
- 完成后提示人类：OpenSpec 提案已生成，可运行 `claude split-to-github <session_id> <change_name>`

## 继承规则

本文件继承 `.claude/agents/default.md` 中的核心原则：
- 工作流优先
- 产物可追溯（OpenSpec artifact 必须引用 TDD 计划、Pencil 原型和核心设计文档）
- 不修改原始设计产物
- 校验规则必须严格执行
- 使用中文与人类交流

---

**产物目录**: `openspec/changes/{change_name}/`
**校验命令**:
- 准入: `python scripts/validate_stage.py --phase entry --check tdd_plan_ready --args {design_id}`
- 退出: `python scripts/validate_stage.py --phase exit --check openspec_artifact_complete --args {change_name},{design_id}`
- 退出: `python scripts/validate_stage.py --phase exit --check tasks_extracted --args {change_name}`
