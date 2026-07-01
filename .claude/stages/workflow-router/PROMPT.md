# workflow-router 阶段入口提示

你正在执行 Lincoln 的 **workflow-router** 阶段。

## 目标

评估当前项目上下文，从模板库中选择最适合的工作流模板，并等待 PM 确认。

## 执行步骤

1. 读取 `.claude/skills/lincoln-workflow-router/prompts/router-prompt.md`。
2. 按 prompt 评估仓库上下文。
3. 推荐模板并等待 PM 确认。
4. 确认后更新 `.claude/workflow-stage.yaml`。

## 产物

- 更新后的 `workflow-state.yaml`（含 `workflow_template` 和 `current_stage`）
