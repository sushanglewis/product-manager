# TDD 研发计划阶段技能与工具

## 主技能命令

- **命令**: `plan-tdd-development`
- **来源**: `.claude/skills/interview-workflow/skill.yaml`
- **参数**:
  - `session_id` (必填): 访谈会话 ID，如 `2026-06-27-stakeholder`
  - `design_id` (必填): 产品设计 ID，如 `checkout-redesign`
- **提示文件**: `.claude/skills/interview-workflow/prompts/plan-tdd-development.md`

## 辅助技能

- `workflow-continue` — 人类修改 `tdd-plan.md` 后恢复被暂停的工作流
  - 人类可直接编辑 `tdd-plan.md` 后运行此命令
  - Agent 重新读取文件并重新校验
- `propose-with-openspec` — 下一阶段命令（TDD 计划就绪后执行）

## 校验器使用

- **校验器路径**: `.claude/skills/interview-workflow/validators/validate.py`
- **使用方式**:
  ```bash
  # 准入校验（原型就绪）
  python .claude/skills/interview-workflow/validators/validate.py \
    --phase entry --check prototype_ready --args {design_id}

  # 准入校验（原型产物完整）
  python .claude/skills/interview-workflow/validators/validate.py \
    --phase entry --check prototype_artifact_complete --args {design_id}

  # 退出校验（TDD 计划完整）
  python .claude/skills/interview-workflow/validators/validate.py \
    --phase exit --check tdd_plan_complete --args {design_id}
  ```

## 允许的工具

根据 `skill.yaml` 的 `tools` 列表，本阶段可用：

| 工具 | 用途 |
|------|------|
| `Read` | 读取设计文档、需求文档、原型文件 |
| `Grep` | 在设计文档中搜索关键词、验收标准 |
| `Glob` | 查找设计产物文件 |
| `Bash` | 创建目录、检查文件状态 |
| `Edit` | 不适用（本阶段只创建新文件） |
| `Write` | 创建 `tdd-plan.md` |

## Pencil 工具使用

如需检查 `prototype.pen` 的视觉结构：

| 工具 | 用途 |
|------|------|
| `pencil/get_editor_state` | 获取当前编辑器状态和 schema |
| `pencil/batch_get` | 读取原型节点结构 |
| `pencil/snapshot_layout` | 检查布局结构 |

> 注意：`.pen` 文件只能通过 Pencil 工具处理，不使用普通文件读取或编辑。

## 辅助子技能

- `superpowers:writing-plans` — 将 `tdd-plan.md` 写成 bite-sized 可执行计划，明确文件路径、命令与验收标准。
- `superpowers:test-driven-development` — 强制每个任务遵循红/绿/重构：先写失败测试，再写最小程序，再重构。  
  要求：计划头部必须声明 `> **Required sub-skill:** Use superpowers:test-driven-development for all implementation`。

## 产物规范

`tdd-plan.md` 必须包含以下章节：

```markdown
# TDD 研发计划

## 来源链接

## 验收标准映射

## 测试场景

## 红/绿/重构序列

## 测试边界

## 数据 Fixtures

## 任务切片

## 风险与依赖

## 范围外

<!-- status: ready-for-openspec -->
```

## 错误处理

| 错误场景 | 处理方式 |
|---------|---------|
| 原型未确认 | 暂停，提示人类先完成 `product-prototype` 阶段 |
| 设计产物缺失 | 暂停，提示人类补充缺失产物 |
| 退出校验失败（章节缺失） | 自动补充缺失章节，重新校验 |
| 退出校验失败（引用缺失） | 补充对设计产物的引用，重新校验 |
| 人类直接编辑后运行 continue | 重新读取文件，重新校验 |

## 关键规则

- 计划必须可执行：工程师无需额外产品决策即可按此开发
- 每个任务切片必须映射回设计产物和验收标准
- 不生成 OpenSpec artifact（留给 `propose` 阶段）
- 所有测试场景必须覆盖验收标准
- 红/绿/重构序列必须具体到可执行的步骤
