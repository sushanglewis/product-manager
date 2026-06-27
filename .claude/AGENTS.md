# Agent 行为规范

本文件定义了在 Lincoln 工作流模板中，Claude Code Agent 必须遵守的行为准则。所有 Agent 在操作本项目前必须先阅读本文件。

## 核心原则

1. **工作流优先**：任何操作必须符合 `.claude/workflows/interview-to-knowledge.yaml` 定义的顺序和校验规则。
2. **人类确认节点不可跳过**：YAML 中标记 `human_gate: true` 的步骤，必须获得人类 PM 的显式确认才能继续。
3. **产物可追溯**：每个需求、每个功能都必须能关联回原始访谈时间戳、OpenSpec 变更、GitHub Issue/PR。
4. **知识库双轨维护**：每个合并的 issue 必须同时沉淀业务知识和技术知识到 Obsidian vault。
5. **不修改原始录音**：`recordings/` 目录中的文件只读，永远不在原地修改。

## 工作流步骤

### 1. process-interview

- 只在用户手动触发时执行
- 校验音频文件存在、格式受支持
- 使用 Whisper 生成带时间戳的 transcript
- 生成 summary 和 raw-insights
- 失败时暂停并给出修复建议

### 2. clarify-requirements

- 基于 transcript 和 summary 向人类 PM 提问
- 一次最多提出 3 个澄清问题
- 将 PM 的回答写入 `requirements/<session>/requirements.md`
- 人类可直接编辑 requirements.md，编辑后运行 `workflow-continue`
- 只有人类输入 `confirm` 或通过文件修改触发继续时，才能进入下一步

### 3. propose-with-openspec

- 调用 `openspec propose <change-name>` CLI 直接生成 artifact
- 读取 `requirements/<session>/requirements.md` 作为输入
- 校验生成的 artifact 完整（proposal.md、specs/、design.md、tasks.md）
- 不绕过 OpenSpec CLI 手动生成 artifact

### 4. split-to-github

- 读取 `openspec/changes/<change>/tasks.md`
- 按任务拆分 GitHub Issues
- 目标仓库来自 `.github/openspec-config.yml`
- 每个 Issue 必须包含：标题、用户故事、验收标准、来源访谈、时间戳、需求链接、OpenSpec 变更链接
- Issue 创建后，更新 requirements.md 记录 issue 编号

### 5. sync-to-knowledge

- 在 PR 合并后触发
- 读取代码 diff、对应 issue、需求文档、OpenSpec design
- 创建或更新 `docs/knowledge/03-features/<feature-slug>.md`
- 文档必须同时包含业务知识和技术知识
- 使用 Obsidian wikilinks 建立关联
- 检查是否与已有知识冲突，有冲突则暂停等待人类处理

## 文件操作规范

- 始终创建新文件/新对象，不直接修改已有文件的核心内容（除非是人类明确要求的修正）
- 每次修改需求文档后，保留修改历史或变更说明
- 所有 JSON/YAML 文件必须格式正确
- Markdown 文件使用统一的 frontmatter 格式

## 校验规则

每个步骤执行前后必须调用对应 validator：

- entry checks：`.claude/skills/interview-workflow/validators/entry-checks/`
- exit checks：`.claude/skills/interview-workflow/validators/exit-checks/`

校验失败时：
1. 立即停止当前 loop
2. 向人类报告失败的校验项
3. 给出明确的修复建议
4. 等待人类处理，不自动重试超过 1 次

## 沟通风格

- 使用中文与人类 PM 交流
- 汇报进度时简洁，重点说明当前步骤、产物位置、下一步需要人类做什么
- 不确定时暂停并提问，不猜测

## 禁止事项

- 禁止在没有人类确认的情况下创建 GitHub Issues
- 禁止删除 `recordings/` 中的原始文件
- 禁止在 requirements 未确认时直接生成 OpenSpec artifact
- 禁止绕过校验继续工作流
- 禁止在 knowledge vault 中创建没有来源链接的功能文档
