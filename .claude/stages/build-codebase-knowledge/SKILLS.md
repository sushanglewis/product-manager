# build-codebase-knowledge 阶段技能

## 技能路由

本阶段技能路由定义见 `.claude/skills/routing.yaml`：
- **required**: （无 — 由 `lincoln-build-codebase-knowledge` 内联技能主导）
- **optional**: `gsd:map-codebase`
- **human_gate**: 否

## 主技能

- `lincoln-build-codebase-knowledge`

## 辅助工具

- `scripts/build-codebase-knowledge.py` — 扫描代码库结构
- `Read` / `Glob` / `Bash` — 读取源码和文档
- `Edit` / `Write` — 生成知识文档

## 输出位置

- `docs/knowledge/00-index.md`
- `docs/knowledge/03-features/existing-*.md`
- `docs/knowledge/05-glossary/00-index.md`
