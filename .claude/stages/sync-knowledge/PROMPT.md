# sync-knowledge 阶段入口提示

你正在进入 Lincoln 工作流的 **sync-knowledge** 阶段：PR 合并后将知识沉淀到 Obsidian 知识库。

## 当前状态

- 前一阶段：`implement`（研发实现）
- 当前阶段：`sync-knowledge`（同步到知识库）
- 下一阶段：无（工作流闭环完成）

## 触发方式

- **自动触发**：PR 合并后，`.github/lincoln-sync-queue/pr-{pr_number}.yaml` 被创建
- **手动触发**：人类运行 `claude sync-to-knowledge <issue_number> <pr_number>`

## 子技能准备

- 调用 `gsd-docs-update` 生成或更新知识文档，确保文档内容与代码库一致。
- 若同步失败，调用 `gsd-forensics` 进行失败复盘，找到根因后再继续。

## 快速开始

1. **确认入口条件**：
   - 运行入口校验 `pr_merged`（检查 sync-queue 文件）
   - 运行入口校验 `issue_exists`（检查 Issue 映射）
2. **读取完整提示**：参考 `.claude/skills/sync-to-knowledge/prompts/main.md` 获取详细步骤
3. **获取 PR 信息**：使用 GitHub MCP 读取 Issue 和 PR 详情
4. **读取关联文档**：需求文档、OpenSpec 设计文档
5. **审查代码变更**：读取 PR diff，提取技术实现信息
6. **创建知识文档**：
   - `docs/knowledge/03-features/<feature_slug>.md`（必须包含业务知识 + 技术知识）
   - `docs/knowledge/02-requirements/<requirement_id>.md`
   - `docs/knowledge/01-interviews/<session_id>.md`
   - `docs/knowledge/04-decisions/<decision_id>.md`（如适用）
7. **建立关联**：使用 Obsidian wikilinks（`[[...]]`）
8. **检查冲突**：与已有知识文档对比，发现冲突则暂停
9. **运行退出校验**：确认 `feature_doc_has_business_and_technical_sections`、`feature_doc_has_links`、`no_conflict_with_existing_knowledge`
10. **更新 sync-queue 文件**：将状态改为 `completed`

## 状态感知

- 检查 `.github/lincoln-sync-queue/pr-{pr_number}.yaml` 获取同步任务信息
- 检查 `.claude/workflow-stage.yaml` 获取当前 `session_id` 和 `change_name`
- 如果 sync-queue 文件状态不是 `pending`，检查是否已处理过

## 关键产出

- `docs/knowledge/03-features/<feature_slug>.md` — 核心功能知识文档
- `docs/knowledge/00-index.md` — 更新后的知识库索引
- 更新后的 `.github/lincoln-sync-queue/pr-{pr_number}.yaml`（状态 `completed`）

## 文档模板要求

功能文档必须包含：

```markdown
---
id: <feature-id>
title: <功能标题>
source_interview: [[01-interviews/<session_id>]]
source_requirement: [[02-requirements/<requirement_id>]]
source_issue: <issue_number>
source_pr: <pr_number>
---

## 业务知识

- 背景：...
- 用户需求：...
- 验收标准：...
- 价值：...

## 技术知识

- 实现概述：...
- 代码位置：...
- 设计决策：...
- 依赖关系：...
- API/数据模型：...
```

## 完成后

向人类汇报知识库更新摘要，包括：
- 创建/更新了哪些文档
- 文档路径和关联关系
- 是否有知识冲突及处理方式

本阶段完成后，Lincoln 工作流闭环。同一访谈的后续迭代从新的 `propose` 阶段开始。
