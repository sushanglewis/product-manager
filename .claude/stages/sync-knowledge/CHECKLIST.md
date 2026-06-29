# sync-knowledge 阶段检查清单

## 入口检查 (Entry Checks)

- [ ] 前置阶段 `implement` 已完成（PR 已合并）
- [ ] 运行入口校验：`python .claude/skills/interview-workflow/validators/validate.py --phase entry --check pr_merged --args <pr_number>`
- [ ] 运行入口校验：`python .claude/skills/interview-workflow/validators/validate.py --phase entry --check issue_exists --args <issue_number>`
- [ ] 确认 `.github/lincoln-sync-queue/pr-{pr_number}.yaml` 存在且状态为 `pending`
- [ ] 确认 sync-queue 文件包含必填字段：`status`, `repository`, `issue_number`, `pr_number`, `merged_at`
- [ ] 确认 Issue 编号在 `.github/linked-issues.yaml` 中存在

## 执行检查 (Execution Checks)

- [ ] 已调用 `gsd-docs-update` 生成/更新知识文档
- [ ] 若失败，已调用 `gsd-forensics` 诊断
- [ ] 读取 `.github/openspec-config.yml` 获取目标仓库
- [ ] 使用 GitHub MCP 获取 Issue 详情和 PR 详情
- [ ] 从 Issue 正文找到关联的需求和 OpenSpec 变更
- [ ] 读取相关文件：
  - `requirements/<session_id>/requirements.md`
  - `openspec/changes/<change_name>/design.md`
  - `openspec/changes/<change_name>/tasks.md`
- [ ] 审查合并的 PR diff
- [ ] 创建/更新 `docs/knowledge/03-features/<feature_slug>.md`
- [ ] 创建/更新 `docs/knowledge/01-interviews/<session_id>.md`（如不存在）
- [ ] 创建/更新 `docs/knowledge/02-requirements/<requirement_id>.md`
- [ ] 创建/更新 `docs/knowledge/04-decisions/<decision_id>.md`（如适用）
- [ ] 使用 Obsidian wikilinks 建立文档关联
- [ ] 更新 `docs/knowledge/00-index.md`
- [ ] 检查与已有知识的冲突

## 退出检查 (Exit Checks)

- [ ] 运行退出校验：`python .claude/skills/interview-workflow/validators/validate.py --phase exit --check feature_doc_has_business_and_technical_sections --args <feature_slug>`
- [ ] 运行退出校验：`python .claude/skills/interview-workflow/validators/validate.py --phase exit --check feature_doc_has_links --args <feature_slug>`
- [ ] 运行退出校验：`python .claude/skills/interview-workflow/validators/validate.py --phase exit --check no_conflict_with_existing_knowledge --args <feature_slug>`
- [ ] 确认功能文档包含至少 3 个 wikilinks
- [ ] 确认功能文档包含 `业务知识` 和 `技术知识` 两个章节

## 产物验证

- [ ] `docs/knowledge/03-features/<feature_slug>.md` 已创建/更新
- [ ] `docs/knowledge/02-requirements/<requirement_id>.md` 已创建/更新
- [ ] `docs/knowledge/01-interviews/<session_id>.md` 已创建/更新
- [ ] `docs/knowledge/04-decisions/<decision_id>.md` 已创建/更新（如适用）
- [ ] `docs/knowledge/00-index.md` 已更新
- [ ] `.github/lincoln-sync-queue/pr-{pr_number}.yaml` 状态已更新为 `completed`

## 状态文件更新

- [ ] 更新 `.claude/workflow-state.yaml`：
  - `stages.sync-knowledge.status` = `completed`
  - `stages.sync-knowledge.exit_checks_passed` = `true`
  - `stages.sync-knowledge.completed_at` = 当前 ISO 时间
  - `current_run.current_stage` = `null`（工作流完成）
  - `current_run.status` = `completed`

## 完成后汇报

向人类汇报：
- 更新了哪些知识文档
- 文档路径和关联关系
- 是否有知识冲突及处理方式
