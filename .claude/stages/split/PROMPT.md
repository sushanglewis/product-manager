# split 阶段入口提示

你正在进入 Lincoln 工作流的 **split** 阶段：将 OpenSpec 任务拆分为 GitHub Issues。

## 当前状态

- 前一阶段：`propose`（OpenSpec 提案）
- 当前阶段：`split`（拆分到 GitHub）
- 下一阶段：`implement`（研发实现）

## 快速开始

1. **确认入口条件**：运行入口校验 `openspec_tasks_ready`
2. **读取完整提示**：参考 `.claude/skills/interview-workflow/prompts/split-to-github.md` 获取详细步骤
3. **执行拆分**：为每个 OpenSpec 任务创建一个 GitHub Issue；若任务 ≥3 个且相互独立，可调用 `superpowers:dispatching-parallel-agents` 并行创建
4. **记录映射**：写入 `.github/linked-issues.yaml`
5. **更新需求文档**：在 `requirements/<session_id>/requirements.md` 中记录 Issue 编号
6. **验证回链**：调用 `superpowers:verification-before-completion`，确认 `requirements.md` 引用了所有 `#<issue_number>`
7. **运行退出校验**：确认 `issues_created` 和 `tasks_link_back_to_issues` 通过

## 状态感知

- 检查 `.claude/workflow-state.yaml` 获取当前 `session_id` 和 `change_name`
- 如果 `stages.split.status` 不是 `not_started`，说明本阶段可能已部分执行，检查已有产物
- 如果 `stages.propose.status` 不是 `completed`，必须先完成 propose 阶段

## 关键产出

- `.github/linked-issues.yaml` — 任务与 Issue 的映射表
- 目标仓库中的 GitHub Issues — 每个 Issue 对应一个 OpenSpec 任务
- 更新后的 `requirements/<session_id>/requirements.md`

## 完成后

告知人类："Issues 已就绪，可进入研发阶段。"
运行 `scripts/stage_loader.py --stage split --action transition-next` 进入 implement 阶段。
