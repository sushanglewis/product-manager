# Ingest 阶段执行检查清单

## 准入检查 (Entry Checks)

执行阶段前必须全部通过：

- [ ] **文件存在性检查**: `file_exists {recording_path}`
  - 录音文件路径有效且文件存在
  - 失败时：向人类确认文件路径是否正确

- [ ] **音频格式检查**: `audio_format_supported {recording_path}`
  - 格式为 `.mp3`、`.m4a`、`.wav`、`.mp4`、`.mov` 之一
  - 失败时：建议人类转换格式（如使用 `ffmpeg -i input.xxx output.m4a`）

## 执行中检查 (During Execution)

- [ ] 从文件名派生 `session_id`（去掉扩展名）
- [ ] 创建目录 `interviews/{session_id}/`
- [ ] 若输入为视频，使用 `ffmpeg` 提取音频轨道
- [ ] 使用 Whisper 转写（优先本地 `faster-whisper`）
- [ ] 生成 `transcript.md`：带时间戳的 Speaker A/B 分段
- [ ] 生成 `summary.md`：包含关键主题、决策、行动项、开放问题
- [ ] 生成 `raw-insights.md`：Agent 对潜在需求的初步观察
- [ ] 生成 `metadata.json`：sessionId、originalFile、duration、processedAt、transcriptModel、status

## 退出检查 (Exit Checks)

阶段完成后必须全部通过：

- [ ] **时间戳检查**: `transcript_has_timestamps {session_id}`
  - `transcript.md` 存在且包含 `HH:MM:SS` 格式时间戳
  - 失败时：检查转写输出是否完整，必要时重新转写

- [ ] **摘要完整性检查**: `summary_has_key_topics {session_id}`
  - `summary.md` 存在且包含以下章节：
    - 关键主题 / Key topics
    - 决策 / Decisions
    - 行动项 / Action items
  - 失败时：补充缺失章节

## 产物验证

- [ ] `interviews/{session_id}/metadata.json` — 非空，JSON 格式正确
- [ ] `interviews/{session_id}/transcript.md` — 非空，含时间戳
- [ ] `interviews/{session_id}/summary.md` — 非空，含必要章节
- [ ] `interviews/{session_id}/raw-insights.md` — 非空

## 人类确认节点

- [ ] 本阶段 **无** human_gate，全自动执行
- [ ] 完成后向人类汇报：产物位置、摘要要点、下一步命令
- [ ] 提示人类运行：`claude clarify-requirements <session-id>`

## 状态文件更新

阶段完成后，更新 `.claude/workflow-stage.yaml`：

```yaml
stages:
  ingest:
    status: completed
    entry_checks_passed: true
    exit_checks_passed: true
    artifacts_produced:
      - interviews/{session_id}/metadata.json
      - interviews/{session_id}/transcript.md
      - interviews/{session_id}/summary.md
      - interviews/{session_id}/raw-insights.md
```

## 失败恢复

- 准入校验失败：暂停，向人类报告具体失败项和修复建议
- 转写失败：写入部分产物，`metadata.json` 中 `status: failed`，报告错误
- 退出校验失败：根据校验器反馈补充或修正产物，重试一次（`max_retries: 1`）
