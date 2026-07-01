# Ingest 阶段技能与工具

## 技能路由

本阶段技能路由定义见 `.claude/skills/routing.yaml`：
- **required**: （无）
- **optional**: `oh-my-claudecode:deep-interview`
- **human_gate**: 否

## 主技能命令

- **命令**: `process-interview`
- **来源**: `.claude/skills/`
- **参数**:
  - `recording_path` (必填): 录音文件路径，如 `recordings/2026-06-27-stakeholder.m4a`
- **提示文件**: `.claude/skills/process-interview/prompts/main.md`

## 辅助技能

- `workflow-continue` — 人类修改文件后恢复被暂停的工作流
- `clarify-requirements` — 下一阶段命令（完成后提示人类执行）

## 校验器使用

- **校验器路径**: `scripts/validate_stage.py`
- **使用方式**:
  ```bash
  # 准入校验
  python scripts/validate_stage.py \
    --phase entry --check file_exists --args {recording_path}
  
  python scripts/validate_stage.py \
    --phase entry --check audio_format_supported --args {recording_path}
  
  # 退出校验
  python scripts/validate_stage.py \
    --phase exit --check transcript_has_timestamps --args {session_id}
  
  python scripts/validate_stage.py \
    --phase exit --check summary_has_key_topics --args {session_id}
  ```

## 允许的工具

根据 `skill.yaml` 的 `tools` 列表，本阶段可用：

| 工具 | 用途 |
|------|------|
| `Read` | 读取录音文件元数据、已有产物 |
| `Grep` | 在转写文本中搜索关键词 |
| `Glob` | 查找录音文件、匹配目录 |
| `Bash` | 执行 `ffmpeg`、Whisper CLI、文件操作 |
| `Edit` | 修改产物文件（如补充缺失章节） |
| `Write` | 创建产物文件 |

## 外部工具依赖

- `ffmpeg` — 视频提取音频（可选，仅在输入为视频时需要）
- `faster-whisper` (本地) — 优先转写引擎
- OpenAI Whisper API — 本地失败时的回退方案

## 错误处理

| 错误场景 | 处理方式 |
|---------|---------|
| 录音文件不存在 | 暂停，报告路径错误，等待人类确认 |
| 音频格式不支持 | 暂停，建议转换格式，给出 `ffmpeg` 命令示例 |
| 本地 Whisper 失败 | 回退到 OpenAI Whisper API |
| 转写 API 失败 | 写入部分产物，`status: failed`，报告错误 |
| 产物缺少时间戳 | 重新检查转写输出，必要时重新转写 |
| 摘要缺少必要章节 | 自动补充缺失章节 |

## 产物规范

- 所有 Markdown 产物使用中文（除非访谈本身为英文）
- `metadata.json` 使用 UTF-8 编码，包含标准字段
- 时间戳格式统一为 `HH:MM:SS`
