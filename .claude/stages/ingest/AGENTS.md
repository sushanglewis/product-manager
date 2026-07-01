# Ingest 阶段 Agent 行为规范

## 阶段目的

将音频访谈录音转写为结构化文本，生成带时间戳的逐字稿、摘要和初始洞察，为后续需求澄清阶段提供输入。

## 准入条件

1. 录音文件存在于 `{recording_path}`
2. 音频格式为受支持的格式：`.mp3`、`.m4a`、`.wav`、`.mp4`、`.mov`
3. 未满足准入条件时，工作流必须暂停并向人类报告具体问题

## 允许的操作

- 读取录音文件（只读）
- 使用 `ffmpeg` 提取视频中的音频轨道
- 使用 Whisper（优先本地 `faster-whisper`，失败时回退到 OpenAI Whisper API）进行转写
- 创建 `interviews/{session_id}/` 目录及产物文件
- 生成 `metadata.json`、`transcript.md`、`summary.md`、`raw-insights.md`

## 禁止的操作

- **禁止修改或删除原始录音文件**：`recordings/` 目录中的文件永远只读
- 禁止在转写失败时静默跳过，必须报告错误并生成部分产物
- 禁止跳过校验直接执行转写
- 禁止在产物不完整时标记阶段完成

## 副作用策略

- 所有产物写入 `interviews/{session_id}/` 目录，不影响其他阶段目录
- 转写失败时写入部分产物（如 `metadata.json` 记录错误状态），便于人类排查
- 不修改任何现有文件，只创建新文件

## 人类确认节点

本阶段 **无** `human_gate`，为全自动执行阶段。
- 转写完成后自动进入下一阶段的准入校验
- 人类可在完成后审阅产物，但不需要显式确认即可继续工作流

## 下一阶段

- 成功完成后自动进入 `clarify`（需求澄清）阶段
- 下一阶段的准入校验：检查 `summary.md` 是否已就绪
- 完成后提示人类运行：`claude clarify-requirements <session-id>`

## 继承规则

本文件继承 `.claude/agents/default.md` 中的核心原则：
- 工作流优先
- 产物可追溯
- 不修改原始录音
- 校验规则必须严格执行
- 使用中文与人类交流

---

**产物目录**: `interviews/{session_id}/`
**校验命令**:
- 准入: `python scripts/validate_stage.py --phase entry --check file_exists --args {recording_path}`
- 准入: `python scripts/validate_stage.py --phase entry --check audio_format_supported --args {recording_path}`
- 退出: `python scripts/validate_stage.py --phase exit --check transcript_has_timestamps --args {session_id}`
- 退出: `python scripts/validate_stage.py --phase exit --check summary_has_key_topics --args {session_id}`
