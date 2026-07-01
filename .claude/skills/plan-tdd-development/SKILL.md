---
name: plan-tdd-development
description: 基于已确认产品设计和原型生成 TDD 研发计划
triggers:
  - "生成 TDD 研发计划"
  - "plan-tdd-development"
inputs:
  - name: session_id
    description: 访谈会话 ID
    required: true
  - name: design_id
    description: 产品设计 ID
    required: true
outputs:
  - designs/{design_id}/tdd-plan.md
required_tools:
  - Read
  - Bash
  - Write
---

# plan-tdd-development

基于已确认产品设计、字段规格、UI 规格和 Pencil 原型生成 TDD 研发计划。

运行入口： prompts/main.md
