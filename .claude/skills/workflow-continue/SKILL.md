---
name: workflow-continue
description: 人类修改文件后继续被暂停的工作流
triggers:
  - "继续工作流"
  - "workflow-continue"
inputs: []
outputs:
  - 推进当前 stage 到下一个节点
required_tools:
  - Read
  - Bash
---

# workflow-continue

在人类修改文件或回复后继续被暂停的 Lincoln 工作流。

运行入口： prompts/main.md
