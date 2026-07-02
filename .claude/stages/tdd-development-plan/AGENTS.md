# TDD 研发计划阶段 Agent 行为规范

## 阶段目的

基于已确认的产品设计文档、字段规格、UI 规格和 Pencil 原型，生成可执行的测试驱动研发计划（`tdd-plan.md`），作为从产品设计到 OpenSpec 变更提案的桥梁。该计划必须足够详细，使工程师无需额外产品决策即可执行。

## 准入条件

1. `prototype_ready` — `designs/{design_id}/ui-spec.md` 包含 `<!-- prototype-status: approved -->` 或 `[x] PM 已确认原型`
2. `prototype_artifact_complete` — `prototype.pen`、`fields.md`、`ui-spec.md` 均存在且非空，并包含必要章节
3. 未满足准入条件时，工作流必须暂停并提示人类先完成 `product-prototype` 阶段

## 允许的操作

- 读取 `designs/{design_id}/` 下的所有设计产物：
  - `design-review.md`、`scenarios.md`、`feature-catalog.md`
  - `data-model.md`、`flows.md`、`feasibility.md`
  - `fields.md`、`ui-spec.md`、`prototype.pen`
- 读取 `requirements/{session_id}/requirements.md` 作为需求来源
- 使用 Pencil 工具检查 `prototype.pen` 的视觉结构（如需）
- 创建 `designs/{design_id}/tdd-plan.md`
- 在 `tdd-plan.md` 中添加 `<!-- status: ready-for-openspec -->` 标记

## 禁止的操作

- **禁止在原型未确认时生成 TDD 计划**
- **禁止在此阶段生成 OpenSpec artifact**（`openspec/changes/` 下的任何文件）
- **禁止绕过原型审批标记**
- 禁止修改 `designs/{design_id}/` 下已有的设计文档
- 禁止修改 `requirements/` 目录下的需求文档
- 禁止绕过校验继续工作流

## 副作用策略

- 唯一产物：`designs/{design_id}/tdd-plan.md`
- 不修改任何已有设计文档或需求文档
- 不创建 `openspec/changes/` 目录（留给 `propose` 阶段）
- 人类可直接编辑 `tdd-plan.md`，编辑后运行 `workflow-continue`

## 人类确认节点

本阶段 **无** `human_gate: true`，为 Agent 自主执行阶段。

- 但产物质量由 `tdd_plan_complete` 退出校验严格把关
- 校验失败时暂停，等待人类修复或指示
- 人类可直接编辑 `tdd-plan.md` 后运行 `workflow-continue`
- 隐式确认：通过退出校验即视为可进入下一阶段

## 下一阶段

- 成功完成后进入 `propose`（OpenSpec 提案）阶段
- 下一阶段的准入校验：检查 `tdd-plan.md` 是否包含 `<!-- status: ready-for-openspec -->`
- 完成后提示人类：TDD 计划已就绪，可运行 `claude propose-with-openspec <session_id> <design_id> <change_name>`

## 继承规则

本文件继承 `.claude/agents/default.md` 中的核心原则：
- 工作流优先
- 产物可追溯（每个测试场景映射回设计文档和验收标准）
- 不修改原始设计产物
- 校验规则必须严格执行
- 使用中文与人类交流

---

**产物文件**: `designs/{design_id}/tdd-plan.md`
**校验命令**:
- 准入: `python scripts/validate_stage.py --phase entry --check prototype_ready --args {design_id}`
- 退出: `python scripts/validate_stage.py --phase exit --check tdd_plan_complete --args {design_id}`
