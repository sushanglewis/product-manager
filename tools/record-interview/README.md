# Lincoln Record Interview CLI

在当前 Lincoln workspace 内录制访谈音频并触发 `process-interview`。

## 使用

```bash
# 进入 Lincoln workspace 后
python -m tools.record-interview SESSION_ID --design-id DESIGN_ID --topic "会议主题"
```

## 依赖

- Python 3.11+
- ffmpeg

## 测试

```bash
pytest tools/record-interview/tests -v
```
