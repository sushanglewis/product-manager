# Clarify 阶段 Agent 行为规范

## 阶段目的

基于访谈产物（逐字稿、摘要、初始洞察）与人类 PM 进行多轮澄清，形成统一、可追溯、已确认的需求文档，作为后续所有阶段的单一事实来源。

## 准入条件

1. `summary.md` 已就绪（`interviews/{session_id}/summary.md` 存在且非空）
2. 未满足准入条件时，工作流必须暂停并提示人类先完成 `ingest` 阶段

## 允许的操作

- 读取 `interviews/{session_id}/` 下的所有产物（transcript.md、summary.md、raw-insights.md）
- 创建 `requirements/{session_id}/` 目录及产物文件
- 起草、更新 `requirements.md`、`user-stories.md`、`prd.md`
- 向人类 PM 提出澄清问题（每轮最多 3 个）
- 根据人类回答更新需求文档
- 在人类直接编辑文件后，通过 `workflow-continue` 恢复并重新读取文件
- 在 `requirements.md` 中添加 `<!-- status: approved -->` 标记

## 禁止的操作

- **禁止跳过人类确认**：未获得人类 PM 显式确认（如输入 "confirm" 或 "确认"）不得进入下一阶段
- **禁止一次提出超过 3 个问题**
- **禁止在需求未确认时直接生成设计文档或 OpenSpec artifact**
- **禁止将 TaskCreate/TaskUpdate 当作消息占位符**：本阶段必须直接向人类 PM 发送澄清问题/文档草案，不得用任务工具拆分或延迟“发消息”动作
- 禁止修改 `interviews/` 目录下的原始产物
- 禁止绕过校验继续工作流
- 禁止在 requirements.md 中遗漏来源时间戳

## 副作用策略

- 所有产物写入 `requirements/{session_id}/` 目录
- 每次更新需求文档后，保留修改痕迹或变更说明
- 不修改 `interviews/` 目录中的任何文件
- 人类可直接编辑 `requirements.md`，Agent 通过 `workflow-continue` 恢复时重新读取

## 人类确认节点

本阶段 **有** `human_gate: true`，为强制人类确认阶段。

- 人类确认方式：
  - 在对话中输入 `confirm` 或 "确认"
  - 或直接在 `requirements.md` 中添加 `<!-- status: approved -->` 标记后运行 `workflow-continue`
- 未获得确认时，工作流必须暂停，不得自动进入下一阶段
- 确认后添加审批标记到 `requirements.md`

## 下一阶段

- 成功完成后进入 `product-design-docs`（产品设计文档）阶段
- 下一阶段的准入校验：检查 `requirements.md` 是否已标记为 approved
- 完成后提示人类：需求已确认，可进入产品设计阶段

## 继承规则

本文件继承 `.claude/agents/default.md` 中的核心原则：
- 工作流优先
- 人类确认节点不可跳过
- 产物可追溯（每个需求关联访谈时间戳）
- 不修改原始访谈产物
- 校验规则必须严格执行
- 使用中文与人类交流

---

**产物目录**: `requirements/{session_id}/`
**校验命令**:
- 准入: `python scripts/validate_stage.py --phase entry --check summary_ready --args {session_id}`
- 退出: `python scripts/validate_stage.py --phase exit --check requirements_has_background_problem_solution_acceptance --args {session_id}`
- 退出: `python scripts/validate_stage.py --phase exit --check human_approved --args {session_id}`
