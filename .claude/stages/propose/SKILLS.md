# OpenSpec 提案阶段技能与工具

## 技能路由

本阶段技能路由定义见 `.claude/skills/routing.yaml`：
- **required**: `openspec:propose`
- **optional**: `superpowers:verification-before-completion`, `oh-my-claudecode:verify`
- **human_gate**: 否

## 主技能命令

- **命令**: `propose-with-openspec`
- **来源**: `.claude/skills/`
- **参数**:
  - `session_id` (必填): 访谈会话 ID，如 `2026-06-27-stakeholder`
  - `design_id` (必填): 产品设计 ID，如 `checkout-redesign`
  - `change_name` (必填): OpenSpec 变更名称，短横线命名，如 `add-csv-export`
- **提示文件**: `.claude/skills/propose-with-openspec/prompts/main.md`

## 辅助技能

- `workflow-continue` — 人类修改 OpenSpec artifact 后恢复被暂停的工作流
  - 人类可直接编辑 OpenSpec artifact 后运行此命令
  - Agent 重新读取文件并重新校验
- `split-to-github` — 下一阶段命令（OpenSpec 提案就绪后执行）
- `superpowers:verification-before-completion` — OpenSpec CLI 生成产物后，必须运行验证并阅读输出，确认 0 失败才能声明完成。  
  规则：没有新鲜验证证据，不得声称 `propose` 完成。

## OpenSpec CLI 使用

- **CLI 命令**: `openspec propose {change_name}`
- **输入文件**: `designs/{design_id}/tdd-plan.md`
- **调用优先级**:
  1. `openspec propose {change_name} --from designs/{design_id}/tdd-plan.md`
  2. `openspec propose {change_name}` 并 pipe TDD 计划内容到 stdin
  3. 若均失败：`openspec propose --help` 读取帮助并适配
- **输出目录**: `openspec/changes/{change_name}/`

## 校验器使用

- **校验器路径**: `scripts/validate_stage.py`
- **使用方式**:
  ```bash
  # 准入校验（TDD 计划就绪）
  python scripts/validate_stage.py \
    --phase entry --check tdd_plan_ready --args {design_id}

  # 退出校验（OpenSpec artifact 完整）
  python scripts/validate_stage.py \
    --phase exit --check openspec_artifact_complete --args {change_name},{design_id}

  # 退出校验（任务已提取）
  python scripts/validate_stage.py \
    --phase exit --check tasks_extracted --args {change_name}
  ```

## 允许的工具

根据 `skill.yaml` 的 `tools` 列表，本阶段可用：

| 工具 | 用途 |
|------|------|
| `Read` | 读取 TDD 计划、设计文档、需求文档、OpenSpec artifact |
| `Grep` | 在 artifact 中搜索设计引用 |
| `Glob` | 查找 OpenSpec 生成的文件 |
| `Bash` | 调用 OpenSpec CLI、检查目录状态 |
| `Edit` | 不适用（不修改 OpenSpec CLI 生成的文件） |
| `Write` | 不适用（不手动生成 artifact） |

## 产物规范

OpenSpec CLI 生成的标准目录结构：

```
openspec/changes/{change_name}/
├── proposal.md      # 变更提案概述
├── specs/           # 详细规格文件（至少一个 .md）
├── design.md        # 设计文档
└── tasks.md         # 任务列表（用于 GitHub Issues 拆分）
```

## 错误处理

| 错误场景 | 处理方式 |
|---------|---------|
| TDD 计划未就绪 | 暂停，提示人类先完成 `tdd-development-plan` 阶段 |
| `openspec/changes/{change_name}/` 已存在 | 询问人类是否覆盖 |
| OpenSpec CLI 调用失败 | 读取 `openspec propose --help`，尝试适配调用方式 |
| OpenSpec CLI 所有调用方式均失败 | 暂停，向人类报告 CLI 错误信息 |
| artifact 文件缺失 | 报告错误，暂停等待人类干预 |
| artifact 引用缺失 | 补充对设计产物的引用，重新校验 |
| 任务列表为空 | 报告错误，暂停等待人类干预 |
| 人类直接编辑后运行 continue | 重新读取文件，重新校验 |

## 关键规则

- **不绕过 OpenSpec CLI**：所有 artifact 必须通过 CLI 生成，不手动创建
- **保留原始结构**：不修改 OpenSpec CLI 生成的文件结构和格式
- **引用完整性**：artifact 必须引用 TDD 计划、Pencil 原型和核心设计文档
- **任务可拆分**：tasks.md 必须包含可识别的任务列表，供 `split` 阶段使用
- **change_name 格式**：短横线命名（kebab-case），如 `add-csv-export`
