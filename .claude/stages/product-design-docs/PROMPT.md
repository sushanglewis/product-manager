# PROMPT.md - 产品设计文档阶段入口提示

你即将执行 Lincoln 工作流的 **产品设计文档** 阶段（`product-design-docs`）。

## 当前状态

- 前置阶段：需求澄清（`clarify-requirements`）已完成
- 当前 stage：`product-design-docs`
- 人类门控：是（`human_gate: true`）
- 下一 stage：`product-prototype`

## 子技能准备

1. 调用 `superpowers:brainstorming` 提出 2-3 种设计方案及 trade-offs，等待 PM 确认。
2. PM 确认后，调用 `superpowers:writing-plans` 规划 `designs/{design_id}/` 下的文件结构与每份文档的职责。

## 执行指令

1. 读取 `.claude/skills/draft-product-design/prompts/main.md` 获取完整执行步骤
2. 确认 `requirements/<session_id>/requirements.md` 已获批准
3. 读取需求文档包（requirements.md、user-stories.md、prd.md）
4. （可选）如果设计涉及可借鉴开源方案，调用 `lincoln-explore-opensource` 生成 `docs/research/{change_name}-oss-options.md`，并等待 PM 确认后再继续
5. 创建 `designs/<design_id>/` 目录并生成 6 份设计文档
6. 请人类 PM 审阅 `design-review.md`
7. PM 确认后，在 `design-review.md` 添加 `<!-- status: approved -->`
8. 提示用户运行：`claude build-product-prototype <session_id> <design_id>`

## 产物清单

- `designs/<design_id>/design-review.md` - PM 评审入口
- `designs/<design_id>/scenarios.md` - 用户场景
- `designs/<design_id>/feature-catalog.md` - 功能清单
- `designs/<design_id>/data-model.md` - 数据模型
- `designs/<design_id>/flows.md` - 流程图（Mermaid）
- `designs/<design_id>/feasibility.md` - 可行性分析

## 关键约束

- 使用中文撰写（除非需求原文为英文）
- 保持简洁，优先使用表格和 Mermaid 图表
- 技术框架建议必须查询当前官方文档
- 本阶段不创建 Pencil 原型
- 不生成 TDD 计划或 OpenSpec artifact
