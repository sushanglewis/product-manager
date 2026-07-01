# Ingest 阶段入口提示

你正在执行 Lincoln 工作流的 **ingest**（摄入录音）阶段。

## 当前阶段状态

- **阶段 ID**: `ingest`
- **阶段名称**: 摄入录音
- **阶段类型**: 全自动（无 human_gate）
- **前置阶段**: 无（工作流入口）
- **后续阶段**: `clarify`（需求澄清）

## 阶段目标

将音频访谈录音转写为结构化文本，生成带时间戳的逐字稿、摘要和初始洞察。

## 执行指令

1. **读取完整提示文件**: `.claude/skills/process-interview/prompts/main.md`
   - 该文件包含详细的转写步骤、产物格式和规则
   - 按照提示文件中的步骤 1-9 执行

2. **阶段状态感知**:
   - 检查 `.claude/workflow-stage.yaml` 中的 `current_run` 和 `stages.ingest` 状态
   - 若状态为 `completed`，跳过重复执行
   - 若状态为 `validation_failed`，根据 `error_message` 修复后重试

3. **变量替换**:
   - 使用 `state.variables.recording_path` 作为输入文件路径
   - 使用 `state.variables.session_id` 作为会话标识（若未设置，从文件名派生）

## 产物清单

阶段完成后必须存在以下产物：

- `interviews/{session_id}/metadata.json`
- `interviews/{session_id}/transcript.md`
- `interviews/{session_id}/summary.md`
- `interviews/{session_id}/raw-insights.md`

## 完成后操作

1. 运行退出校验器验证产物完整性
2. 更新 `workflow-state.yaml` 中 `stages.ingest` 状态为 `completed`
3. 向人类汇报：
   - 产物存放路径
   - 访谈摘要要点（3-5 条）
   - 下一步命令：`claude clarify-requirements <session-id>`

## 关键提醒

- 原始录音文件 **只读**，绝不修改或删除
- 转写失败时写入部分产物并清晰报告错误
- 摘要和洞察使用中文（除非访谈为英文）
- 每个需求必须关联回访谈时间戳
