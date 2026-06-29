# TDD 研发计划阶段入口提示

你正在执行 Lincoln 工作流的 **tdd-development-plan**（TDD 研发计划）阶段。

## 当前阶段状态

- **阶段 ID**: `tdd-development-plan`
- **阶段名称**: TDD 研发计划
- **阶段类型**: Agent 自主执行（`human_gate: false`）
- **前置阶段**: `product-prototype`（产品原型）
- **后续阶段**: `propose`（OpenSpec 提案）

## 阶段目标

基于已确认的产品设计文档、字段规格、UI 规格和 Pencil 原型，生成可执行的测试驱动研发计划，作为产品设计与 OpenSpec 变更提案之间的桥梁。

## 子技能准备

1. 调用 `superpowers:writing-plans` 规划 `tdd-plan.md` 的文件结构与任务切片。
2. 在计划头部插入：  
   `> **Required sub-skill:** Use superpowers:test-driven-development for all implementation`
3. 每个任务切片必须包含：失败的测试样例、最小实现命令、重构提示。

## 执行指令

1. **读取完整提示文件**: `.claude/skills/interview-workflow/prompts/plan-tdd-development.md`
   - 该文件包含详细的 TDD 计划生成步骤和格式要求
   - 按照提示文件中的步骤 1-5 执行

2. **阶段状态感知**:
   - 检查 `.claude/workflow-state.yaml` 中的 `stages.tdd-development-plan` 状态
   - 若状态为 `completed`，检查是否需要重新生成（人类要求时）
   - 若状态为 `validation_failed`，根据 `error_message` 修复后重试
   - 若人类运行 `workflow-continue`，重新读取 `tdd-plan.md` 并重新校验

3. **变量替换**:
   - 使用 `state.variables.session_id` 作为会话标识
   - 使用 `state.variables.design_id` 作为设计标识

## 产物清单

阶段完成后必须存在以下产物：

- `designs/{design_id}/tdd-plan.md` — 含 `<!-- status: ready-for-openspec -->` 标记

## 执行流程

1. 运行准入校验器确认原型已确认且产物完整
2. 读取所有设计文档和需求文档作为输入
3. 如需检查原型视觉结构，使用 Pencil 工具
4. 生成 `tdd-plan.md`，包含：来源链接、验收映射、测试场景、红绿重构序列、测试边界、数据 fixtures、任务切片、风险依赖
5. 在文件末尾添加 `<!-- status: ready-for-openspec -->` 标记
6. 运行退出校验器验证产物完整性

## 完成后操作

1. 运行退出校验器验证 `tdd-plan.md` 完整性和引用完整性
2. 更新 `workflow-state.yaml` 中 `stages.tdd-development-plan` 状态为 `completed`
3. 向人类汇报：
   - TDD 计划已生成
   - 产物存放路径：`designs/{design_id}/tdd-plan.md`
   - 下一阶段入口：`propose`（运行 `claude propose-with-openspec <session_id> <design_id> <change_name>`）

## 关键提醒

- **原型必须已确认**：未确认原型不得生成 TDD 计划
- **不生成 OpenSpec artifact**：本阶段只产出 `tdd-plan.md`，OpenSpec 文件留给 `propose` 阶段
- **计划必须可执行**：每个任务切片必须具体到工程师无需额外产品决策即可执行
- **可追溯性**：每个测试场景必须映射回设计文档和验收标准
- **支持直接编辑**：人类可编辑 `tdd-plan.md` 后运行 `workflow-continue`
