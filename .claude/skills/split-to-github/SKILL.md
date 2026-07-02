---
name: split-to-github
description: 将 OpenSpec tasks 拆分为 GitHub Issues
triggers:
  - "拆分到 GitHub"
  - "split-to-github"
inputs:
  - name: session_id
    description: 访谈会话 ID
    required: true
  - name: change_name
    description: OpenSpec 变更名称
    required: true
outputs:
  - .github/linked-issues.yaml
required_tools:
  - Read
  - Bash
  - Write
  - mcp__plugin_ecc_github__create_issue
---

# split-to-github

读取 OpenSpec tasks 并拆分为带清晰边界和验收标准的 GitHub Issues。

运行入口： prompts/main.md
