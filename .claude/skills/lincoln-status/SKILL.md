---
name: lincoln-status
description: 查看当前 Lincoln 分支的阶段状态、等待对象、推荐技能和下一步动作
triggers:
  - "查看 Lincoln 状态"
  - "lincoln-status"
  - "当前阶段"
inputs: []
outputs:
  - 结构化状态报告
required_tools:
  - Read
  - Bash
---

# lincoln-status

调用 `python scripts/lincoln-status.py --format markdown` 输出当前 Lincoln 分支状态。

输出包含：当前阶段、等待对象、已加载上下文、推荐技能、产物状态、下一步动作。
