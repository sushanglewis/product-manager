# implement 阶段入口提示

你正在进入 Lincoln 工作流的 **implement** 阶段：研发实现。

## 当前状态

- 前一阶段：`split`（拆分到 GitHub）
- 当前阶段：`implement`（研发实现）
- 下一阶段：`sync-knowledge`（同步到知识库）

## 阶段性质

**本阶段以人类为主导，Agent 仅在人类请求时提供辅助。**

## 快速开始

1. **确认入口条件**：运行入口校验 `issues_ready`
2. **人类开始研发**：
   - 认领 GitHub Issue
   - 创建开发分支
   - 编写代码和测试
   - 提交 PR（PR 描述中关联 Issue：`Fixes #<issue_number>`）
3. **代码审查**：人类审查 + 可选请求 Agent 辅助审查
4. **合并 PR**：人类合并到主分支
5. **触发 sync-knowledge**：创建 `.github/lincoln-sync-queue/pr-{pr_number}.yaml`

## Agent 辅助方式

当人类请求时，Agent 可以：

- **审查 PR**：`claude /code-review` 或请求 Agent 审查 diff
- **安全审查**：`claude /security-review`
- **完善 PR 描述**：协助补充关联信息
- **测试辅助**：协助编写或审查测试用例
- **冲突解决**：分析合并冲突并提供建议

## 状态感知

- 检查 `.claude/workflow-stage.yaml` 获取当前 `session_id`
- 检查 `.github/linked-issues.yaml` 获取待实现的 Issue 列表
- 如果 `stages.implement.status` 不是 `not_started`，检查是否已部分完成

## 关键规则

1. 每个 PR 必须关联至少一个 GitHub Issue
2. PR 描述应包含：关联 Issue 编号、变更摘要、测试计划
3. 代码合并前必须通过审查和自动化测试
4. **Agent 不主动创建或修改代码，仅在人类请求时辅助**

## 可用子技能（人类请求时）

当人类 PM/研发请求时，可调用：
- `superpowers:using-git-worktrees` — 创建隔离工作区
- `superpowers:subagent-driven-development` — 分任务实现
- `superpowers:test-driven-development` — TDD 红/绿/重构
- `superpowers:systematic-debugging` — 根因排查
- `superpowers:finishing-a-development-branch` — PR/合并选项
- `superpowers:requesting-code-review` / `superpowers:receiving-code-review` — 审查
- `superpowers:verification-before-completion` — 完成前验证

**约束**：未收到明确请求前，Agent 只提供信息，不调用上述技能。

## 触发 sync-knowledge

PR 合并后，创建以下文件以触发知识同步：

```yaml
# .github/lincoln-sync-queue/pr-{pr_number}.yaml
status: pending
repository: owner/repo
issue_number: <issue_number>
pr_number: <pr_number>
merged_at: 2026-06-27T10:00:00Z
```

然后运行：
```
claude sync-to-knowledge <issue_number> <pr_number>
```

或等待 CI/CD 自动触发。

## 完成后

PR 合并且 sync-queue 文件创建后，本阶段自动完成，进入 `sync-knowledge` 阶段。
