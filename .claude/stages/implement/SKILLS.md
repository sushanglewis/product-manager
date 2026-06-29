# implement 阶段技能与工具

## 主技能命令

本阶段无专门的 Agent 主动技能命令，由人类主导执行。

Agent 辅助时可使用的技能：

```
# 代码审查（人类请求时）
claude /code-review

# 安全审查（人类请求时）
claude /security-review
```

## GitHub MCP 使用

人类完成 PR 合并后，Agent 可使用 GitHub MCP 获取信息：

- **获取 PR 详情**：`mcp__plugin_ecc_github__get_pull_request`
  - 参数：`owner`, `repo`, `pull_number`
- **获取 PR 文件变更**：`mcp__plugin_ecc_github__get_pull_request_files`
  - 用于代码审查辅助
- **获取 PR 评论**：`mcp__plugin_ecc_github__get_pull_request_comments`
  - 用于审查意见汇总
- **更新 Issue**：`mcp__plugin_ecc_github__update_issue`
  - 参数：`owner`, `repo`, `issue_number`, `state`
  - 人类请求时协助更新 Issue 状态

## Validator 使用

入口校验：
```bash
python .claude/skills/interview-workflow/validators/validate.py \
  --phase entry \
  --check issues_ready \
  --args <session_id>
```

## 错误处理

| 错误场景 | 处理方式 |
|---------|---------|
| Issues 未就绪 | 暂停，提示人类先完成 `split` 阶段 |
| PR 审查发现问题 | Agent 提供建议，人类决定是否修改 |
| 合并冲突 | Agent 协助分析冲突，人类手动解决 |
| 测试失败 | Agent 协助分析失败原因，人类修复代码 |
| sync-queue 文件创建失败 | 提示人类手动创建，或重试 |

## 输入文件

- `.github/linked-issues.yaml` — Issue 映射关系
- GitHub Issues — 研发任务
- `requirements/<session_id>/requirements.md` — 需求文档（参考）
- `openspec/changes/<change_name>/` — OpenSpec 设计文档（参考）

## 输出文件

- 合并的 PR（由人类创建）
- `.github/lincoln-sync-queue/pr-{pr_number}.yaml` — 触发 sync-knowledge 的队列文件

## 按需调用的子技能

本阶段由人类研发团队主导，Agent 仅在收到明确请求时调用以下技能：

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

## human_gate 规则

- Agent **不得主动**调用任何实施类子技能。
- 所有子技能调用必须基于人类显式请求（如“帮我用 TDD 实现这个 issue”）。
- PR 合并作为人类确认事件，触发 `sync-knowledge`。
