# Clarify 阶段技能与工具

## 技能路由

本阶段技能路由定义见 `.claude/skills/routing.yaml`：
- **required**: `superpowers:brainstorming`
- **optional**: `gsd:import`, `gsd:discuss-phase`, `oh-my-claudecode:deep-interview`, `openspec:explore`
- **human_gate**: 是

## 主技能命令

- **命令**: `clarify-requirements`
- **来源**: `.claude/skills/`
- **参数**:
  - `session_id` (必填): 访谈会话 ID，如 `2026-06-27-stakeholder`
- **提示文件**: `.claude/skills/clarify-requirements/prompts/main.md`

## 辅助子技能

- `superpowers:brainstorming` — 在起草需求前探索 2-3 种需求/方案视角，并列出 trade-offs。  
  **限制**：仅在人类 PM 批准某一方向后才能继续写 `requirements.md`。
- `gsd:import` — 当存在外部需求文档或计划时，先调用以检测与项目已有决策的冲突。  
  用法：`Skill("gsd-import", args="--from <path>")`。

## human_gate 子技能规则

在 `clarify` 阶段，即使使用了 `brainstorming` 也不得绕过人类确认。  
PM 必须输入 `confirm` 或在 `requirements.md` 中写入 `<!-- status: approved -->` 后才能进入 `product-design-docs`。

## 辅助技能

- `workflow-continue` — 人类修改文件后恢复被暂停的工作流
  - 人类可直接编辑 `requirements.md` 后运行此命令
  - Agent 重新读取文件并继续澄清流程
- `draft-product-design` — 下一阶段命令（需求确认后执行）

## 校验器使用

- **校验器路径**: `scripts/validate_stage.py`
- **使用方式**:
  ```bash
  # 准入校验
  python scripts/validate_stage.py \
    --phase entry --check summary_ready --args {session_id}
  
  # 退出校验
  python scripts/validate_stage.py \
    --phase exit --check requirements_has_background_problem_solution_acceptance --args {session_id}
  
  python scripts/validate_stage.py \
    --phase exit --check human_approved --args {session_id}
  ```

## 允许的工具

根据 `skill.yaml` 的 `tools` 列表，本阶段可用：

| 工具 | 用途 |
|------|------|
| `Read` | 读取访谈产物、需求文档 |
| `Grep` | 在逐字稿中搜索关键词、时间戳 |
| `Glob` | 查找访谈产物文件 |
| `Bash` | 创建目录、文件操作 |
| `Edit` | 更新需求文档（补充章节、修改内容） |
| `Write` | 创建初始需求文档、user-stories.md、prd.md |

## 人类交互规则

| 规则 | 说明 |
|------|------|
| 每轮最多 3 个问题 | 避免信息过载，保持对话聚焦 |
| 展示变更部分 | 每次更新文档后，向人类展示修改了哪些部分 |
| 支持直接编辑 | 人类可直接编辑 `requirements.md`，编辑后运行 `workflow-continue` |
| 确认门槛 | 必须获得显式确认（`confirm` / "确认" / `<!-- status: approved -->`） |
| 可追溯性 | 每个需求必须引用访谈时间戳 `(来源: HH:MM:SS)` |

## 需求文档模板

`requirements.md` 必须包含以下章节：

```markdown
# 需求文档

## 背景

## 问题

## 用户

## 方案

## 验收标准

## 非目标

## 开放问题

<!-- status: approved -->
```

## 错误处理

| 错误场景 | 处理方式 |
|---------|---------|
| 访谈产物不存在 | 暂停，提示人类先完成 `ingest` 阶段 |
| 人类回答模糊 | 追问澄清，不猜测 |
| 需求冲突 | 暂停，向人类报告冲突点，等待决策 |
| 退出校验失败（章节缺失） | 自动补充缺失章节，重新校验 |
| 退出校验失败（未确认） | 暂停，等待人类确认 |
| 人类直接编辑后运行 continue | 重新读取文件，检查审批标记，继续或提示 |

## 产物规范

- 所有文档使用中文
- Markdown 使用统一 frontmatter 格式
- 需求项必须关联访谈时间戳
- `requirements.md` 确认后必须包含 `<!-- status: approved -->` 标记
- `user-stories.md` 和 `prd.md` 从已确认的需求派生，保持一致性
