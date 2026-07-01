---
name: build-product-prototype
description: 基于已确认设计文档生成字段、界面规格和 Pencil 原型
triggers:
  - "生成产品原型"
  - "build-product-prototype"
inputs:
  - name: session_id
    description: 访谈会话 ID
    required: true
  - name: design_id
    description: 产品设计 ID
    required: true
outputs:
  - designs/{design_id}/fields.md
  - designs/{design_id}/ui-spec.md
  - designs/{design_id}/prototype.pen
required_tools:
  - Read
  - Bash
  - Write
  - mcp__pencil__batch_design
---

# build-product-prototype

基于已确认设计文档生成字段规格、UI 规格和 Pencil 原型。

运行入口： prompts/main.md
