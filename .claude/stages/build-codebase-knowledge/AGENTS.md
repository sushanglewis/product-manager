# build-codebase-knowledge 阶段 Agent 规范

## 阶段目的

为已有源码项目构建功能知识库，使后续 PM 迭代能基于事实。

## 入口条件

- 当前 workflow 模板为 `existing-project-iteration`
- 或 PM 明确说 "先理解现有代码"

## 允许的操作

- 读取源码、README、CHANGELOG
- 调用 `lincoln-build-codebase-knowledge`
- 生成/更新 `docs/knowledge/` 下的 Markdown 文件

## 禁止的操作

- 修改源码
- 生成未经验证的假设
- 跳过 PM 确认直接标记完成

## 人类确认节点

PM 必须确认 `docs/knowledge/00-index.md` 中的功能列表后，阶段才能标记完成。
