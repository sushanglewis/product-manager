# explore-opensource 阶段 Agent 规范

## 阶段目的

在设计阶段探索开源方案，避免从零造轮子，并为实现提供参考。

## 入口条件

- 当前 workflow 模板为 `oss-first-design`
- 或 `product-design-docs` 阶段明确识别出可借鉴开源方案的子问题

## 允许的操作

- 使用 WebSearch/GitHub MCP 搜索开源项目
- 阅读项目 README、license、发布历史
- 生成 `docs/research/{change_name}-oss-options.md`

## 禁止的操作

- 下载或执行第三方代码
- 自动选择最终方案（必须 PM 确认）
- 阻塞设计流程：搜索失败时降级为简短摘要并继续

## 人类确认节点

PM 必须确认推荐方案或明确要求继续自行设计。
