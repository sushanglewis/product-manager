# workflow-router 阶段技能

## 技能路由

本阶段技能路由定义见 `.claude/skills/routing.yaml`：
- **required**: `superpowers:bootstrap`
- **optional**: `gsd:new-project` / `gsd:new-milestone`, `oh-my-claudecode:plan`
- **human_gate**: 是

## 主技能

- `lincoln-workflow-router`

## 辅助工具

- `Read` — 读取 state 和目录
- `Glob` / `Bash` — 扫描仓库结构
- `Edit` — 更新 `workflow-state.yaml`

## 模板库

位于 `.claude/workflows/templates/`：

- `interview-to-knowledge.yaml`
- `existing-project-iteration.yaml`
- `bug-fix.yaml`
- `design-spike.yaml`
- `oss-first-design.yaml`
