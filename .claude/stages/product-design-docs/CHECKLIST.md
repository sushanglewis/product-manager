# CHECKLIST.md - 产品设计文档阶段

## 入口检查

- [ ] `requirements/<session_id>/requirements.md` 存在且非空
- [ ] 需求文档包含批准标记（`<!-- status: approved -->` 或 `[x] PM 已确认需求`）
- [ ] `requirements/<session_id>/user-stories.md` 存在且非空
- [ ] `requirements/<session_id>/prd.md` 存在且非空
- [ ] 校验命令通过：`python .claude/skills/interview-workflow/validators/validate.py --phase entry --check requirements_approved --args <session_id>`

## 执行中检查

- [ ] 已调用 `superpowers:brainstorming` 探索 ≥2 种设计方向
- [ ] PM 已确认设计方向（`design-review.md` 含 `<!-- status: approved -->` 或 `[x] PM 已确认设计文档`）
- [ ] 已调用 `superpowers:writing-plans` 规划文档结构
- [ ] 已创建 `designs/<design_id>/` 目录
- [ ] 已读取全部需求文档
- [ ] `design-review.md` 包含决策摘要、范围、文档链接、待解决问题和审批清单
- [ ] `scenarios.md` 包含目标用户、主场景、边界场景和非目标
- [ ] `feature-catalog.md` 包含功能列表、优先级、验收映射和需求来源链接
- [ ] `data-model.md` 包含核心实体、字段、约束、校验规则和状态转换
- [ ] `flows.md` 包含至少一个 Mermaid 图表（用户流、业务流、序列图或架构图）
- [ ] `feasibility.md` 包含业务可行性、技术可行性、开源项目/技术框架建议、风险评估
- [ ] 所有文档使用中文（除非需求原文为英文）
- [ ] 技术框架和开源项目建议已查阅当前官方文档或主仓库

## 出口检查

- [ ] `design-review.md` 存在且非空
- [ ] `scenarios.md` 存在且非空
- [ ] `feature-catalog.md` 存在且非空
- [ ] `data-model.md` 存在且非空
- [ ] `flows.md` 存在且非空，包含至少一个 ` ```mermaid ` 代码块
- [ ] `feasibility.md` 存在且非空
- [ ] `design-review.md` 包含指向所有其他设计文档的链接
- [ ] `feature-catalog.md` 包含验收标准映射（"验收" 或 "Acceptance" 标题）
- [ ] `data-model.md` 包含字段或约束描述（"字段"/"Field" 或 "约束"/"Constraint" 标题）
- [ ] `feasibility.md` 包含业务可行性、技术可行性、开源项目/技术框架章节
- [ ] 校验命令通过：`python .claude/skills/interview-workflow/validators/validate.py --phase exit --check design_docs_complete --args <design_id>`

## 产物验证

- [ ] 设计文档包完整（6 个文件）
- [ ] 文档可追溯回原始需求文件
- [ ] 文档简洁、以表格和图表为主，避免冗长叙述

## 人类门控

- [ ] 人类 PM 已审阅 `design-review.md`
- [ ] PM 确认设计文档满足需求
- [ ] `design-review.md` 已添加 `<!-- status: approved -->` 或 `[x] PM 已确认设计文档`
- [ ] 校验命令通过：`python .claude/skills/interview-workflow/validators/validate.py --phase exit --check design_docs_human_approved --args <design_id>`

## 状态文件更新

- [ ] 本阶段状态更新为 `completed`
- [ ] `completed_at` 已记录
- [ ] 下一阶段 `product-prototype` 状态初始化为 `not_started`
- [ ] `current_run.current_stage` 更新为 `product-prototype`
