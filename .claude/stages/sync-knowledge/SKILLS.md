# sync-knowledge 阶段技能与工具

## 技能路由

本阶段技能路由定义见 `.claude/skills/routing.yaml`：
- **required**: `gsd:docs-update`
- **optional**: `gsd:forensics`, `gsd:milestone-summary`, `openspec:sync-specs`, `oh-my-claudecode:wiki`, `oh-my-claudecode:writer-memory`, `superpowers:verification-before-completion`
- **human_gate**: 否

## 主技能命令

```
claude sync-to-knowledge <issue_number> <pr_number>
```

对应 `interview-workflow` skill 中的 `sync-to-knowledge` 命令。

参数：
- `issue_number`: GitHub Issue 编号
- `pr_number`: GitHub PR 编号

## 辅助子技能

- `gsd-docs-update` — 生成或更新经代码库验证的知识文档。  
  用法：`Skill("gsd-docs-update")`（可带 `--force` 或 `--verify-only`）。
- `gsd-forensics` — 若 `sync-knowledge` 失败，先调用进行失败复盘，再重试。  
  用法：`Skill("gsd-forensics")`。

## 约束

`gsd-docs-update` 的输出需要与 `docs/knowledge/` 目录结构对齐；生成后检查是否与已有知识冲突。

## GitHub MCP 使用

本阶段使用 GitHub MCP 获取 Issue 和 PR 信息：

- **获取 Issue 详情**：`mcp__plugin_ecc_github__get_issue`
  - 参数：`owner`, `repo`, `issue_number`
  - 用于提取关联的需求和 OpenSpec 变更信息
- **获取 PR 详情**：`mcp__plugin_ecc_github__get_pull_request`
  - 参数：`owner`, `repo`, `pull_number`
  - 用于获取 PR 描述、合并状态
- **获取 PR 文件变更**：`mcp__plugin_ecc_github__get_pull_request_files`
  - 用于审查代码变更，提取技术实现信息
- **获取 PR 评论**：`mcp__plugin_ecc_github__get_pull_request_comments`
  - 用于提取设计决策和讨论记录

## Validator 使用

入口校验：
```bash
python scripts/validate_stage.py \
  --phase entry \
  --check pr_merged \
  --args <pr_number>

python scripts/validate_stage.py \
  --phase entry \
  --check issue_exists \
  --args <issue_number>
```

退出校验：
```bash
python scripts/validate_stage.py \
  --phase exit \
  --check feature_doc_has_business_and_technical_sections \
  --args <feature_slug>

python scripts/validate_stage.py \
  --phase exit \
  --check feature_doc_has_links \
  --args <feature_slug>

python scripts/validate_stage.py \
  --phase exit \
  --check no_conflict_with_existing_knowledge \
  --args <feature_slug>
```

## 错误处理

| 错误场景 | 处理方式 |
|---------|---------|
| sync-queue 文件不存在 | 暂停，报告错误，提示人类检查 PR 是否已合并 |
| sync-queue 文件状态不是 `pending` | 检查是否已处理过，如已处理则跳过；否则暂停 |
| Issue 在 linked-issues.yaml 中不存在 | 暂停，报告错误，提示人类检查 split 阶段是否完成 |
| GitHub API 获取失败 | 重试一次，仍失败则暂停 |
| 知识冲突检测失败 | 暂停，报告冲突详情，等待人类处理 |
| 功能文档缺少业务/技术章节 | 补充缺失内容后重新校验 |
| 功能文档 wikilinks 不足 | 补充关联链接后重新校验 |

## 输入文件

- `.github/lincoln-sync-queue/pr-{pr_number}.yaml` — 同步队列文件
- `.github/openspec-config.yml` — 目标仓库配置
- `.github/linked-issues.yaml` — Issue 映射关系
- `requirements/<session_id>/requirements.md` — 需求文档
- `openspec/changes/<change_name>/design.md` — OpenSpec 设计文档
- `openspec/changes/<change_name>/tasks.md` — OpenSpec 任务列表

## 输出文件

- `docs/knowledge/03-features/<feature_slug>.md` — 功能知识文档
- `docs/knowledge/02-requirements/<requirement_id>.md` — 需求知识文档
- `docs/knowledge/01-interviews/<session_id>.md` — 访谈知识文档
- `docs/knowledge/04-decisions/<decision_id>.md` — 决策知识文档（如适用）
- `docs/knowledge/00-index.md` — 知识库索引
- 更新后的 `.github/lincoln-sync-queue/pr-{pr_number}.yaml`（状态改为 `completed`）
