# split 阶段技能与工具

## 技能路由

本阶段技能路由定义见 `.claude/skills/routing.yaml`：
- **required**: `superpowers:dispatching-parallel-agents`
- **optional**: `gsd:phase`, `oh-my-claudecode:team`
- **human_gate**: 否

## 主技能命令

```
claude split-to-github <session_id> <change_name>
```

对应 `interview-workflow` skill 中的 `split-to-github` 命令。

参数：
- `session_id`: 访谈会话 ID
- `change_name`: OpenSpec 变更名称

## 辅助子技能

- `superpowers:dispatching-parallel-agents` — 当需要创建 3 个以上相互独立的 GitHub Issues 时，可并行派发独立 agent 加速。
- `superpowers:verification-before-completion` — Issue 创建后必须验证：所有 issue 都能在 `requirements.md` 中通过 `#<number>` 回链。

## GitHub MCP 使用

本阶段使用 GitHub MCP 进行 Issue 操作：

- **创建 Issue**：`mcp__plugin_ecc_github__create_issue`
  - 参数：`owner`, `repo`, `title`, `body`, `labels`
  - 每个任务对应一个 Issue
- **列出 Issues**（验证用）：`mcp__plugin_ecc_github__list_issues`
  - 验证已创建的 Issue 是否存在

替代方案：使用 `gh issue create` CLI 命令（当 MCP 不可用时）

## Validator 使用

入口校验：
```bash
python scripts/validate_stage.py \
  --phase entry \
  --check openspec_tasks_ready \
  --args <change_name>
```

退出校验：
```bash
python scripts/validate_stage.py \
  --phase exit \
  --check issues_created \
  --args <session_id>

python scripts/validate_stage.py \
  --phase exit \
  --check tasks_link_back_to_issues \
  --args <session_id>
```

## 错误处理

| 错误场景 | 处理方式 |
|---------|---------|
| `tasks.md` 不存在或为空 | 暂停，报告错误，建议人类先完成 `propose` 阶段 |
| `.github/openspec-config.yml` 缺失 | 暂停，报告错误，提示人类创建配置文件 |
| GitHub API 创建失败 | 记录失败的任务，重试一次，仍失败则暂停 |
| Issue 创建后链接文件写入失败 | 重试写入，仍失败则暂停并报告已创建的 Issue 编号 |
| 校验失败 | 按 AGENTS.md 校验失败流程：停止、报告、修复建议、等待人类 |

## 输入文件

- `openspec/changes/<change_name>/tasks.md` — OpenSpec 任务列表
- `.github/openspec-config.yml` — 目标仓库配置
- `requirements/<session_id>/requirements.md` — 需求文档（追加 Issue 编号）

## 输出文件

- `.github/linked-issues.yaml` — 任务到 Issue 的映射
- `requirements/<session_id>/requirements.md` — 更新后的需求文档
