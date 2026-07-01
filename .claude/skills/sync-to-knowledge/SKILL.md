---
name: sync-to-knowledge
description: PR 合并后将代码和 issue 沉淀到 Obsidian 知识库
triggers:
  - "同步到知识库"
  - "sync-to-knowledge"
inputs:
  - name: issue_number
    description: GitHub Issue 编号
    required: true
  - name: pr_number
    description: GitHub PR 编号
    required: true
outputs:
  - .github/lincoln-sync-queue/pr-{pr_number}.yaml
  - docs/knowledge/01-interviews/{session_id}.md
  - docs/knowledge/02-requirements/{requirement_id}.md
  - docs/knowledge/03-features/{feature_slug}.md
  - docs/knowledge/04-decisions/{decision_id}.md
required_tools:
  - Read
  - Bash
  - Write
---

# sync-to-knowledge

PR 合并后读取代码 diff、issue、需求文档和 OpenSpec design，沉淀到 Obsidian 知识库。

运行入口： prompts/main.md
