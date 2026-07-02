# PROMPT.md - 产品原型阶段入口提示

你即将执行 Lincoln 工作流的 **产品原型** 阶段（`product-prototype`）。

## 当前状态

- 前置阶段：产品设计文档（`product-design-docs`）已完成
- 当前 stage：`product-prototype`
- 人类门控：是（`human_gate: true`）
- 下一 stage：`tdd-development-plan`

## 子技能准备

1. （可选，需 PM 同意）调用 `superpowers:brainstorming` 的视觉 companion 探索 UI/UX 选项。
2. （可选）若原型需要在独立分支/工作区开发，调用 `superpowers:using-git-worktrees`。

## 执行指令

1. 读取 `.claude/skills/build-product-prototype/prompts/main.md` 获取完整执行步骤
2. 确认 `designs/<design_id>/design-review.md` 已获批准
3. 读取 `designs/<design_id>/` 下的全部设计文档
4. 创建 `fields.md`（字段规格）和 `ui-spec.md`（UI 规格）
5. 使用 Pencil MCP 工具创建或更新 `prototype.pen`：
   - 操作前调用 `get_editor_state(include_schema: true)` 获取 schema
   - 使用 `batch_design` 生成原型内容
   - 使用 `snapshot_layout` 检查并修复布局问题
6. 请人类 PM 在 Pencil 中打开并审阅 `prototype.pen`
7. PM 确认后，在 `ui-spec.md` 添加 `<!-- prototype-status: approved -->`
8. 提示用户运行：`claude plan-tdd-development <session_id> <design_id>`

## 产物清单

- `designs/<design_id>/fields.md` - 字段规格
- `designs/<design_id>/ui-spec.md` - UI 规格
- `designs/<design_id>/prototype.pen` - Pencil 原型（仅通过 Pencil 工具操作）

## 关键约束

- **严禁**使用普通文件工具（Read/Write/Edit/Grep）操作 `.pen` 文件
- 所有 `.pen` 操作必须通过 Pencil MCP 工具完成
- 控件状态必须完整：默认、悬停/聚焦、禁用、空、加载、错误、成功
- 截图和 HTML 仅作为辅助审阅材料，不作为主要审批产物
- 保存后的 `.pen` 是最终开发参照
