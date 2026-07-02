# split 阶段检查清单

## 入口检查 (Entry Checks)

- [ ] 前置阶段 `propose` 状态为 `completed`
- [ ] 运行入口校验：`python scripts/validate_stage.py --phase entry --check openspec_tasks_ready --args <change_name>`
- [ ] 确认 `openspec/changes/<change_name>/tasks.md` 存在且非空
- [ ] 确认 tasks.md 包含可识别的任务列表（`[-*] [ ]` 格式）
- [ ] 确认 `.github/openspec-config.yml` 存在且包含目标仓库配置

## 执行检查 (Execution Checks)

- [ ] 已按需调用 `superpowers:dispatching-parallel-agents`
- [ ] 已调用 `superpowers:verification-before-completion` 验证回链
- [ ] 读取并解析 `openspec/changes/<change_name>/tasks.md`
- [ ] 为每个任务创建独立的 GitHub Issue
- [ ] 每个 Issue 包含完整的来源追溯信息
- [ ] 每个 Issue 应用标签：`from-interview`、`openspec`
- [ ] 写入 `.github/linked-issues.yaml` 记录映射关系
- [ ] 更新 `requirements/<session_id>/requirements.md` 记录 Issue 编号

## 退出检查 (Exit Checks)

- [ ] 运行退出校验：`python scripts/validate_stage.py --phase exit --check issues_created --args <session_id>`
- [ ] 运行退出校验：`python scripts/validate_stage.py --phase exit --check tasks_link_back_to_issues --args <session_id>`
- [ ] 确认 `.github/linked-issues.yaml` 包含有效的 issue_number
- [ ] 确认 `requirements/<session_id>/requirements.md` 中引用了所有创建的 Issue 编号

## 产物验证

- [ ] `.github/linked-issues.yaml` 已创建/更新
- [ ] `requirements/<session_id>/requirements.md` 已更新
- [ ] GitHub Issues 在目标仓库中可见且可访问

## 状态文件更新

- [ ] 更新 `.claude/workflow-stage.yaml`：
  - `stages.split.status` = `completed`
  - `stages.split.exit_checks_passed` = `true`
  - `stages.split.completed_at` = 当前 ISO 时间
  - `current_run.current_stage` = `implement`
  - `stages.implement.status` = `not_started`
