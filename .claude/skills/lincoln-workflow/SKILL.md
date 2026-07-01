---
name: lincoln-workflow
description: Lincoln 访谈到知识库完整工作流 bundle，按需组合 9 个阶段 skill
triggers:
  - "启动 Lincoln 访谈工作流"
  - "lincoln-workflow"
  - "Lincoln 工作流"
inputs:
  - name: action
    description: 可选：process-interview / clarify-requirements / draft-product-design / build-product-prototype / plan-tdd-development / propose-with-openspec / split-to-github / sync-to-knowledge / workflow-continue
    required: false
outputs:
  - 按所选阶段产出对应 artifact
required_tools:
  - Skill
---

# lincoln-workflow

 Lincoln 标准工作流 bundle：将访谈录音转化为结构化需求、产品设计、Pencil 原型、TDD 计划、OpenSpec 提案、GitHub Issues，最终沉淀到知识库。

当用户说“启动 Lincoln 访谈工作流”时，根据当前 stage 调用对应的子 skill：
- ingest → `process-interview`
- clarify → `clarify-requirements`
- product-design-docs → `draft-product-design`
- product-prototype → `build-product-prototype`
- tdd-development-plan → `plan-tdd-development`
- propose → `propose-with-openspec`
- split → `split-to-github`
- sync-knowledge → `sync-to-knowledge`
- paused → `workflow-continue`

Lincoln 辅助 skill 会在会话启动、状态查询、分支初始化、handoff 等时机自动介入：
- `lincoln-status`：查询当前分支工作状态
- `lincoln-handoff`：生成阶段交接文档
- `lincoln-init-branch`：初始化 feature branch 过程文档
- `lincoln-build-codebase-knowledge`：扫描代码库构建业务/技术知识
- `lincoln-explore-opensource`：探索开源方案与技术框架
- `lincoln-workflow-router`：在会话开始时评估并选择工作流模板

如果用户明确指定了阶段，直接调用对应 skill。
