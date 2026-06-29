# TDD 研发计划阶段执行检查清单

## 准入检查 (Entry Checks)

执行阶段前必须全部通过：

- [ ] **原型就绪检查**: `prototype_ready {design_id}`
  - `designs/{design_id}/ui-spec.md` 包含 `<!-- prototype-status: approved -->` 或 `[x] PM 已确认原型`
  - 失败时：提示人类先完成 `product-prototype` 阶段

- [ ] **原型产物完整性检查**: `prototype_artifact_complete {design_id}`
  - `designs/{design_id}/prototype.pen` 存在且非空
  - `designs/{design_id}/fields.md` 存在且包含必要章节（字段、校验、错误状态）
  - `designs/{design_id}/ui-spec.md` 存在且包含必要章节（界面、交互、状态）
  - 失败时：提示人类补充缺失的原型产物

## 执行中检查 (During Execution)

- [ ] 已调用 `superpowers:writing-plans` 规划文档结构
- [ ] 计划头部声明了 required sub-skill `superpowers:test-driven-development`
- [ ] 每个任务切片包含红/绿/重构步骤
- [ ] 读取 `requirements/{session_id}/requirements.md`（需求来源）
- [ ] 读取 `designs/{design_id}/design-review.md`（设计评审）
- [ ] 读取 `designs/{design_id}/scenarios.md`（场景）
- [ ] 读取 `designs/{design_id}/feature-catalog.md`（功能清单）
- [ ] 读取 `designs/{design_id}/data-model.md`（数据模型）
- [ ] 读取 `designs/{design_id}/flows.md`（流程图）
- [ ] 读取 `designs/{design_id}/feasibility.md`（可行性分析）
- [ ] 读取 `designs/{design_id}/fields.md`（字段规格）
- [ ] 读取 `designs/{design_id}/ui-spec.md`（UI 规格）
- [ ] 检查 `designs/{design_id}/prototype.pen`（如需视觉结构，使用 Pencil 工具）
- [ ] 创建 `designs/{design_id}/tdd-plan.md`，包含以下章节：
  - 来源链接（指向需求、设计文档、字段、UI 规格、原型）
  - 验收标准映射
  - 测试场景（按用户工作流分组）
  - 红/绿/重构实现序列
  - 单元、集成、契约、UI、回归测试边界
  - 数据 fixtures 和验证用例
  - 任务切片（适合 OpenSpec tasks 和 GitHub Issues）
  - 风险、依赖项和范围外项
- [ ] 在 `tdd-plan.md` 末尾添加 `<!-- status: ready-for-openspec -->` 标记

## 退出检查 (Exit Checks)

阶段完成后必须全部通过：

- [ ] **TDD 计划完整性检查**: `tdd_plan_complete {design_id}`
  - `designs/{design_id}/tdd-plan.md` 存在且非空
  - 包含以下章节：
    - 验收映射 / Acceptance mapping / 验收标准映射
    - 测试场景 / Test scenarios
    - 红/绿/重构 / Red/Green/Refactor / 红绿重构
    - 任务切片 / Task slices
    - 回归范围 / Regression
  - 包含对以下产物的引用：
    - `requirements/{session_id}/requirements.md`
    - `designs/{design_id}/design-review.md`
    - `designs/{design_id}/fields.md`
    - `designs/{design_id}/ui-spec.md`
    - `designs/{design_id}/prototype.pen`
  - 失败时：根据校验器反馈补充缺失章节或引用

## 产物验证

- [ ] `designs/{design_id}/tdd-plan.md` — 非空，包含所有必要章节和引用
- [ ] 每个测试场景映射回至少一个设计文档和验收标准
- [ ] 每个任务切片可追溯到设计产物和验收标准
- [ ] 包含 `<!-- status: ready-for-openspec -->` 标记

## 人类确认节点

- [ ] 本阶段 **无** `human_gate: true`，Agent 自主执行
- [ ] 隐式确认：通过 `tdd_plan_complete` 退出校验即视为就绪
- [ ] 人类可直接编辑 `tdd-plan.md` 后运行 `workflow-continue`
- [ ] 校验失败时暂停，向人类报告缺失项并给出修复建议

## 状态文件更新

阶段完成后，更新 `.claude/workflow-state.yaml`：

```yaml
stages:
  tdd-development-plan:
    status: completed
    entry_checks_passed: true
    exit_checks_passed: true
    artifacts_produced:
      - designs/{design_id}/tdd-plan.md
```

## 失败恢复

- 准入校验失败（原型未确认）：提示人类先完成 `product-prototype` 阶段
- 准入校验失败（产物缺失）：提示人类补充缺失的原型产物
- 退出校验失败（章节缺失）：根据校验器反馈补充缺失章节，重新校验
- 人类直接编辑文件后：运行 `workflow-continue`，Agent 重新读取文件并重新校验
