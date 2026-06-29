# implement 阶段 Agent 规范

## 阶段目的

人类研发团队基于已创建的 GitHub Issues 进行代码开发并提交 PR。本阶段以人类为主导，Agent 仅在人类请求时提供辅助。

## 入口条件

1. 前置阶段 `split` 已完成并通过退出校验
2. 入口校验通过：`issues_ready`（`.github/linked-issues.yaml` 存在）
3. 当前 workflow state 中 `current_stage` 为 `implement`

## 允许的操作（Agent 辅助模式）

Agent 仅在人类明确请求时执行以下操作：

- **代码审查辅助**：审查 PR diff，提供代码质量建议
- **测试辅助**：协助编写或审查测试用例
- **文档辅助**：协助编写或更新技术文档
- **冲突解决辅助**：协助解决合并冲突
- **Issue 状态更新**：协助更新 Issue 状态、添加评论
- **PR 描述完善**：协助完善 PR 描述，确保关联正确的 Issue

## 禁止的操作

- **禁止**主动创建或修改代码文件（除非人类明确请求）
- **禁止**主动提交 PR（除非人类明确请求）
- **禁止**绕过人类确认合并代码
- **禁止将 TaskCreate/TaskUpdate 当作消息占位符**：本阶段以人类为主导，Agent 必须直接向人类发送辅助结果/问题，不得用任务工具拆分“发消息”动作
- **禁止**修改 `.github/linked-issues.yaml` 中的映射关系
- **禁止**删除或修改已创建的 GitHub Issues
- **禁止**跳过校验标记阶段为完成

## 人类驱动规则

1. 本阶段的核心工作（编码、提交 PR、代码审查）由人类完成
2. Agent 的角色是**助手**，不是**执行者**
3. 人类可以通过以下方式请求 Agent 协助：
   - "请帮我审查这个 PR"
   - "请帮我写这个功能的测试"
   - "请帮我解决这个合并冲突"
   - "请帮我完善 PR 描述"
4. 当人类未明确请求时，Agent 应保持待命，不主动干预

## 副作用策略

- Agent 不直接修改代码仓库
- 所有 Agent 辅助的修改必须经过人类确认后才能应用
- PR 合并后，由自动化流程（或人类手动）触发 `sync-knowledge` 阶段

## 人类确认节点

- 本阶段 **有** `human_gate`（workflow YAML 中标记为 `true`）
- PR 合并是人类确认本阶段完成的关键事件
- PR 合并后，应触发 `sync-knowledge` 阶段

## 按需调用的子技能

Agent 仅在人类明确请求时调用以下子技能：

| 场景 | 调用技能 |
|------|----------|
| 需要隔离工作区 | `superpowers:using-git-worktrees` |
| 需要 Agent 分任务实现 | `superpowers:subagent-driven-development` |
| 需要 TDD 指导 | `superpowers:test-driven-development` |
| 遇到 bug/测试失败 | `superpowers:systematic-debugging` |
| 完成实现后处理 PR | `superpowers:finishing-a-development-branch` |
| 需要代码审查 | `superpowers:requesting-code-review` |
| 收到审查意见 | `superpowers:receiving-code-review` |
| 任何“完成”声明前 | `superpowers:verification-before-completion` |

## 下一阶段

`sync-knowledge` — 同步到知识库（由 PR 合并自动触发）

## 触发 sync-knowledge 的方式

1. **自动触发**：PR 合并后，CI/CD 流程创建 `.github/lincoln-sync-queue/pr-{pr_number}.yaml`
2. **手动触发**：人类运行 `claude sync-to-knowledge <issue_number> <pr_number>`

## 关键规则

1. 每个 PR 必须关联至少一个 GitHub Issue
2. PR 描述应包含：关联 Issue 编号、变更摘要、测试计划
3. 代码合并前必须通过代码审查和自动化测试
4. Agent 辅助的代码审查应遵循 `.claude/AGENTS.md` 中的代码质量规范
