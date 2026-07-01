---
name: draft-product-design
description: 基于已确认需求生成产品设计评审文档包
triggers:
  - "生成产品设计文档"
  - "draft-product-design"
inputs:
  - name: session_id
    description: 访谈会话 ID
    required: true
  - name: design_id
    description: 产品设计 ID，如 checkout-redesign
    required: true
outputs:
  - designs/{design_id}/design-review.md
  - designs/{design_id}/scenarios.md
  - designs/{design_id}/feature-catalog.md
  - designs/{design_id}/data-model.md
  - designs/{design_id}/flows.md
  - designs/{design_id}/feasibility.md
required_tools:
  - Read
  - Bash
  - Write
---

# draft-product-design

基于已确认需求生成面向 PM 评审的简洁产品设计文档包。

运行入口： prompts/main.md
