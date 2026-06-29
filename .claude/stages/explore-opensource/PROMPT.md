# explore-opensource 阶段入口提示

你正在执行 Lincoln 的 **explore-opensource** 阶段。

## 目标

为当前需求找到合适的开源方案，并生成评估报告。

## 执行步骤

1. 读取 `.claude/skills/lincoln-explore-opensource/prompts/explore-opensource.md`。
2. 从 `requirements/{session_id}/requirements.md` 提取关键词。
3. 搜索候选项目并评分。
4. 生成 `docs/research/{change_name}-oss-options.md`。
5. 向 PM 展示评分表，等待确认。

## 产物

- `docs/research/{change_name}-oss-options.md`
