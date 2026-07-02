---
name: propose-with-openspec
description: 基于已确认 TDD 研发计划调用 OpenSpec CLI 生成变更提案 artifact
triggers:
  - "生成 OpenSpec 提案"
  - "propose-with-openspec"
inputs:
  - name: session_id
    description: 访谈会话 ID
    required: true
  - name: design_id
    description: 产品设计 ID
    required: true
  - name: change_name
    description: OpenSpec 变更名称，如 add-csv-export
    required: true
outputs:
  - openspec/changes/{change_name}/proposal.md
  - openspec/changes/{change_name}/design.md
  - openspec/changes/{change_name}/tasks.md
  - openspec/changes/{change_name}/specs/
required_tools:
  - Read
  - Bash
  - Write
---

# propose-with-openspec

调用 OpenSpec CLI 基于 TDD 研发计划生成完整变更提案 artifact。

运行入口： prompts/main.md
