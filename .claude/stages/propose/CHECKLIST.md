# OpenSpec 提案阶段执行检查清单

## 准入检查 (Entry Checks)

执行阶段前必须全部通过：

- [ ] **TDD 计划就绪检查**: `tdd_plan_ready {design_id}`
  - `designs/{design_id}/tdd-plan.md` 存在且非空
  - 包含 `<!-- status: ready-for-openspec -->` 标记
  - 失败时：提示人类先完成 `tdd-development-plan` 阶段

## 执行中检查 (During Execution)

- [ ] OpenSpec CLI 已执行并生成产物
- [ ] 已调用 `superpowers:verification-before-completion` 验证产物
- [ ] 退出校验全部通过
- [ ] 读取 `requirements/{session_id}/requirements.md`（需求来源）
- [ ] 读取 `designs/{design_id}/tdd-plan.md`（TDD 计划输入）
- [ ] 读取 `designs/{design_id}/design-review.md`（设计评审）
- [ ] 读取 `designs/{design_id}/feature-catalog.md`（功能清单）
- [ ] 读取 `designs/{design_id}/data-model.md`（数据模型）
- [ ] 读取 `designs/{design_id}/flows.md`（流程图）
- [ ] 读取 `designs/{design_id}/feasibility.md`（可行性分析）
- [ ] 读取 `designs/{design_id}/fields.md`（字段规格）
- [ ] 读取 `designs/{design_id}/ui-spec.md`（UI 规格）
- [ ] 检查 `openspec/changes/{change_name}/` 是否已存在
  - 若已存在，询问人类是否覆盖
- [ ] 调用 OpenSpec CLI（按优先级尝试）：
  1. `openspec propose {change_name} --from designs/{design_id}/tdd-plan.md`
  2. `openspec propose {change_name}` 并 pipe TDD 计划内容
  3. 若均失败，读取 `openspec propose --help` 并适配
- [ ] 验证生成的 artifact 文件存在且非空：
  - `openspec/changes/{change_name}/proposal.md`
  - `openspec/changes/{change_name}/specs/`（至少一个文件）
  - `openspec/changes/{change_name}/design.md`
  - `openspec/changes/{change_name}/tasks.md`
- [ ] 验证 OpenSpec artifact 引用以下设计产物：
  - `designs/{design_id}/tdd-plan.md`
  - `designs/{design_id}/prototype.pen`
  - `designs/{design_id}/design-review.md`

## 退出检查 (Exit Checks)

阶段完成后必须全部通过：

- [ ] **OpenSpec artifact 完整性检查**: `openspec_artifact_complete {change_name},{design_id}`
  - `openspec/changes/{change_name}/proposal.md` 存在且非空
  - `openspec/changes/{change_name}/specs/` 目录存在且非空
  - `openspec/changes/{change_name}/design.md` 存在且非空
  - `openspec/changes/{change_name}/tasks.md` 存在且非空
  - 所有 artifact 文件综合内容中引用 `designs/{design_id}/tdd-plan.md`
  - 所有 artifact 文件综合内容中引用 `designs/{design_id}/prototype.pen`
  - 所有 artifact 文件综合内容中引用 `designs/{design_id}/design-review.md`
  - 失败时：报告错误并暂停，等待人类干预

- [ ] **任务提取检查**: `tasks_extracted {change_name}`
  - `openspec/changes/{change_name}/tasks.md` 包含至少一个可识别的任务项（`[-*] [.?] ...` 格式）
  - 失败时：报告错误并暂停

## 产物验证

- [ ] `openspec/changes/{change_name}/proposal.md` — 非空
- [ ] `openspec/changes/{change_name}/specs/*.md` — 至少一个文件，非空
- [ ] `openspec/changes/{change_name}/design.md` — 非空
- [ ] `openspec/changes/{change_name}/tasks.md` — 非空，包含可识别的任务列表
- [ ] OpenSpec artifact 引用 TDD 计划、Pencil 原型和核心设计文档
- [ ] 保留 OpenSpec CLI 生成的原始结构，未手动修改

## 人类确认节点

- [ ] 本阶段 **无** `human_gate: true`，Agent 自主执行
- [ ] 隐式确认：通过 `openspec_artifact_complete` 和 `tasks_extracted` 退出校验即视为就绪
- [ ] 若 `openspec/changes/{change_name}/` 已存在，需询问人类是否覆盖
- [ ] 人类可直接编辑 OpenSpec artifact 后运行 `workflow-continue`
- [ ] 校验失败时暂停，向人类报告错误并给出修复建议

## 状态文件更新

阶段完成后，更新 `.claude/workflow-stage.yaml`：

```yaml
stages:
  propose:
    status: completed
    entry_checks_passed: true
    exit_checks_passed: true
    artifacts_produced:
      - openspec/changes/{change_name}/proposal.md
      - openspec/changes/{change_name}/specs/
      - openspec/changes/{change_name}/design.md
      - openspec/changes/{change_name}/tasks.md
```

## 失败恢复

- 准入校验失败（TDD 计划未就绪）：提示人类先完成 `tdd-development-plan` 阶段
- OpenSpec CLI 调用失败：读取 `openspec propose --help`，尝试适配调用方式
- 退出校验失败（artifact 缺失）：报告错误，暂停等待人类干预
- 退出校验失败（引用缺失）：补充对设计产物的引用，重新校验
- 人类直接编辑文件后：运行 `workflow-continue`，Agent 重新读取文件并重新校验
