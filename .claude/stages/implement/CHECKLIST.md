# implement 阶段检查清单

## 入口检查 (Entry Checks)

- [ ] 前置阶段 `split` 状态为 `completed`
- [ ] 运行入口校验：`python scripts/validate_stage.py --phase entry --check issues_ready --args <session_id>`
- [ ] 确认 `.github/linked-issues.yaml` 存在且包含有效 Issue 编号
- [ ] 确认目标仓库中的 Issues 可访问且状态正确

## 执行检查 (Execution Checks) — 人类主导

- [ ] 所有子技能调用均来自人类明确请求
- [ ] 人类研发团队认领 Issue 并创建开发分支
- [ ] 人类编写代码和测试
- [ ] 人类提交 PR 并关联 Issue（PR 描述中包含 `Fixes #<issue_number>` 或 `Closes #<issue_number>`）
- [ ] 代码审查通过（人类审查 + Agent 辅助审查可选）
- [ ] 自动化测试通过
- [ ] 人类合并 PR 到主分支

## Agent 辅助检查（人类请求时）

- [ ] Agent 协助审查 PR diff（代码质量、安全性、测试覆盖）
- [ ] Agent 协助完善 PR 描述
- [ ] Agent 协助编写或审查测试用例
- [ ] Agent 协助解决合并冲突

## 退出检查 (Exit Checks)

- [ ] PR 已合并到主分支
- [ ] `.github/lincoln-sync-queue/pr-{pr_number}.yaml` 已创建（由 CI 或人类手动创建）
- [ ] 确认 Issue 状态已更新为 `closed`

## 产物验证

- [ ] 合并的 PR 包含关联的 Issue 引用
- [ ] 代码变更符合需求文档中的验收标准
- [ ] 测试覆盖率达到项目最低要求（默认 80%）

## 状态文件更新

- [ ] 更新 `.claude/workflow-stage.yaml`：
  - `stages.implement.status` = `completed`
  - `stages.implement.completed_at` = 当前 ISO 时间
  - `current_run.current_stage` = `sync-knowledge`
  - `stages.sync-knowledge.status` = `not_started`

## 触发 sync-knowledge

- [ ] PR 合并后，创建 `.github/lincoln-sync-queue/pr-{pr_number}.yaml`：
  ```yaml
  status: pending
  repository: owner/repo
  issue_number: <issue_number>
  pr_number: <pr_number>
  merged_at: <ISO timestamp>
  ```
- [ ] 运行 `claude sync-to-knowledge <issue_number> <pr_number>` 或等待自动触发
