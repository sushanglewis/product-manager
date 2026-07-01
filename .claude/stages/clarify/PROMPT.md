# Clarify 阶段入口提示

你正在执行 Lincoln 工作流的 **clarify**（需求澄清）阶段。

## 当前阶段状态

- **阶段 ID**: `clarify`
- **阶段名称**: 需求澄清
- **阶段类型**: 人类交互（`human_gate: true`）
- **前置阶段**: `ingest`（摄入录音）
- **后续阶段**: `product-design-docs`（产品设计文档）

## 阶段目标

基于访谈产物与人类 PM 多轮澄清，产出统一、已确认的需求文档，作为后续阶段的单一事实来源。

## 子技能准备

1. （可选）如果存在外部需求或计划文件，先调用 `gsd-import` 检测冲突。
2. 调用 `superpowers:brainstorming` 向 PM 提出 2-3 种可能的需求视角/方案，并说明 trade-offs。  
   **HARD-GATE**：展示方案后必须停下来等待 PM 选择或确认方向，未确认前不得写 `requirements.md`。

## 执行指令

1. **读取完整提示文件**: `.claude/skills/clarify-requirements/prompts/main.md`
   - 该文件包含详细的澄清步骤、人类交互规则和产物格式
   - 按照提示文件中的步骤 1-9 执行

2. **阶段状态感知**:
   - 检查 `.claude/workflow-stage.yaml` 中的 `stages.clarify` 状态
   - 若状态为 `completed`，检查是否需要重新澄清（人类要求时）
   - 若状态为 `validation_failed`，根据 `error_message` 修复后重试
   - 若人类运行 `workflow-continue`，重新读取 `requirements.md` 并从中断处继续

3. **变量替换**:
   - 使用 `state.variables.session_id` 作为会话标识
   - 读取 `interviews/{session_id}/` 下的 transcript.md、summary.md、raw-insights.md

## 产物清单

阶段完成后必须存在以下产物：

- `requirements/{session_id}/requirements.md` — 含审批标记
- `requirements/{session_id}/user-stories.md`
- `requirements/{session_id}/prd.md`

## 人类交互流程

1. 起草初始 `requirements.md` 并展示给人类
2. 识别 1-3 个模糊点，每轮提出最多 3 个问题
3. 根据回答更新文档，展示变更部分
4. 重复直到 PM 显式确认（`confirm` / "确认"）
5. 添加 `<!-- status: approved -->` 标记

## 完成后操作

1. 运行退出校验器验证产物完整性和人类确认状态
2. 更新 `workflow-state.yaml` 中 `stages.clarify` 状态为 `completed`
3. 向人类汇报：
   - 需求已锁定
   - 产物存放路径
   - 下一阶段入口：`product-design-docs`（将在需求确认后自动准入）

## 关键提醒

- **人类确认不可跳过**：未获得显式确认不得进入下一阶段
- **每轮最多 3 个问题**：避免信息过载
- **可追溯性**：每个需求必须关联访谈时间戳 `(来源: HH:MM:SS)`
- **支持直接编辑**：人类可编辑 `requirements.md` 后运行 `workflow-continue`
- **不修改原始产物**：`interviews/` 目录只读
