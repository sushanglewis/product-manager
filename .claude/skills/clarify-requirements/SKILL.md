---
name: clarify-requirements
description: 基于访谈内容与人类 PM 多轮澄清需求
triggers:
  - "澄清需求"
  - "clarify-requirements"
inputs:
  - name: session_id
    description: 访谈会话 ID，如 2026-06-27-stakeholder
    required: true
outputs:
  - requirements/{session_id}/requirements.md
  - requirements/{session_id}/user-stories.md
  - requirements/{session_id}/prd.md
required_tools:
  - Read
  - Bash
  - Write
  - Edit
---

# clarify-requirements

基于访谈 transcript 和 summary 与人类 PM 多轮澄清，输出统一需求文档。

运行入口： prompts/main.md
