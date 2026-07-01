# CHECKLIST.md - 产品原型阶段

## 入口检查

- [ ] `designs/<design_id>/design-review.md` 存在且非空
- [ ] 设计评审文档包含批准标记（`<!-- status: approved -->` 或 `[x] PM 已确认设计文档`）
- [ ] 设计文档包完整（6 个文件均存在且非空）
- [ ] 校验命令通过：`python scripts/validate_stage.py --phase entry --check product_design_approved --args <design_id>`

## 执行中检查

- [ ] 已询问 PM 是否需要 `superpowers:brainstorming` 视觉探索
- [ ] 已按需创建隔离工作区（`superpowers:using-git-worktrees`）
- [ ] 已读取 `designs/<design_id>/` 下的全部设计文档
- [ ] `fields.md` 已创建，包含：字段名、数据类型、必填/选填、校验规则、默认值、文案、错误状态、来源数据对象
- [ ] `ui-spec.md` 已创建，包含：目标用户流、界面列表、交互说明、组件状态、空/加载/错误状态、无障碍说明、实现约束
- [ ] `prototype.pen` 已创建或更新（仅通过 Pencil MCP 工具）
- [ ] 使用 Pencil 工具前已调用 `get_editor_state(include_schema: true)` 获取 schema
- [ ] 使用 `snapshot_layout` 检查并修复了裁剪或重叠元素
- [ ] 控件状态完整：默认、悬停/聚焦（如适用）、禁用、空、加载、错误、成功
- [ ] 未使用普通文件工具读取或修改 `.pen` 文件

## 出口检查

- [ ] `prototype.pen` 存在且非空（仅通过 Pencil MCP 工具验证）
- [ ] `fields.md` 存在且非空，包含字段、校验、错误状态章节
- [ ] `ui-spec.md` 存在且非空，包含界面、交互、状态章节
- [ ] 校验命令通过：`python scripts/validate_stage.py --phase exit --check prototype_artifact_complete --args <design_id>`

## 产物验证

- [ ] 字段规格完整，可直接用于开发
- [ ] UI 规格完整，覆盖所有界面和状态
- [ ] Pencil 原型布局无裁剪或重叠问题
- [ ] 原型可在 Pencil 应用中正常打开和编辑

## 人类门控

- [ ] 人类 PM 已在 Pencil 中打开并审阅 `prototype.pen`
- [ ] PM 确认原型满足设计需求
- [ ] `ui-spec.md` 已添加 `<!-- prototype-status: approved -->` 或 `[x] PM 已确认原型`
- [ ] 保存后的 `.pen` 被标记为最终开发参照

## 状态文件更新

- [ ] 本阶段状态更新为 `completed`
- [ ] `completed_at` 已记录
- [ ] 下一阶段 `tdd-development-plan` 状态初始化为 `not_started`
- [ ] `current_run.current_stage` 更新为 `tdd-development-plan`
