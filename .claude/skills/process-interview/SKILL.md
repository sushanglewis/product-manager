---
name: process-interview
description: 处理访谈录音，生成转写、摘要和初始洞察
triggers:
  - "处理访谈录音"
  - "process-interview"
inputs:
  - name: recording_path
    description: 录音文件路径，如 recordings/2026-06-27-stakeholder.m4a
    required: true
outputs:
  - interviews/{session_id}/metadata.json
  - interviews/{session_id}/transcript.md
  - interviews/{session_id}/summary.md
  - interviews/{session_id}/raw-insights.md
required_tools:
  - Read
  - Bash
---

# process-interview

处理访谈录音，生成带时间戳的 transcript、summary 和 raw-insights。

运行入口： prompts/main.md
