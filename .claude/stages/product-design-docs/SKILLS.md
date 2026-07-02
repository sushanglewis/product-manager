# SKILLS.md - 产品设计文档阶段

## 技能路由

本阶段技能路由定义见 `.claude/skills/routing.yaml`：
- **required**: `superpowers:brainstorming`, `superpowers:writing-plans`
- **optional**: `gsd:spec-phase`, `oh-my-claudecode:plan`, `openspec:propose`
- **human_gate**: 是

## 主要技能命令

- `claude draft-product-design <session_id> <design_id>`
  - 基于已确认需求生成产品设计评审文档包
  - 参数：
    - `session_id`: 访谈会话 ID，如 `2026-06-27-stakeholder`
    - `design_id`: 产品设计 ID（kebab-case），如 `checkout-redesign`
  - 完整 prompt 文件：`.claude/skills/draft-product-design/prompts/main.md`

## 辅助技能

- `claude workflow-continue`
  - 当人类 PM 修改文件后，恢复被暂停的工作流
- `superpowers:brainstorming` — 生成设计文档前先探索 2-3 种设计方向，列出 trade-offs。  
  **限制**：PM 未批准前不得调用 `writing-plans` 进入文档实施。
- `superpowers:writing-plans` — 将设计文档包结构化为可执行计划，明确每个文件的职责与路径。
- `lincoln-explore-opensource` — 当设计涉及可借鉴开源方案时，在设计文档前先做 OSS 研究。产物：`docs/research/{change_name}-oss-options.md`。

## human_gate 子技能规则

`brainstorming` 完成后的 HARD-GATE 与 Lincoln 的 `human_gate` 合并：必须获得 PM 对设计方向的确认，才能继续生成 `design-review.md` 等产物。

## 校验器使用

- 入口校验：`python scripts/validate_stage.py --phase entry --check requirements_approved --args <session_id>`
- 出口校验：`python scripts/validate_stage.py --phase exit --check design_docs_complete --args <design_id>`
- 人类批准校验：`python scripts/validate_stage.py --phase exit --check design_docs_human_approved --args <design_id>`
- 校验失败时：停止 loop、报告失败项、给出修复建议、等待人类处理

## MCP 工具

本阶段主要使用标准文件读写工具：

- `Read` - 读取需求文档
- `Write` - 创建设计文档
- `Edit` - 修改设计文档（如需修正）
- `WebSearch` / `WebFetch` - 查询技术框架和开源项目的当前官方文档

## 错误处理

- 需求文档缺失或未经批准：暂停工作流，提示用户先完成 `clarify-requirements` 阶段
- 设计文档生成失败：报告具体失败文件和原因，给出修复建议
- 校验失败：根据校验器输出定位缺失内容，补充后重新校验
- 技术文档查询失败：记录查询失败的框架/项目，使用备选方案或标注为待确认
