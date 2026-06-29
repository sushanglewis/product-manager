# build-codebase-knowledge 阶段入口提示

你正在执行 Lincoln 的 **build-codebase-knowledge** 阶段。

## 目标

扫描现有代码库，生成功能知识文档，等待 PM 确认。

## 执行步骤

1. 读取 `.claude/skills/lincoln-build-codebase-knowledge/prompts/build-codebase-knowledge.md`。
2. 运行 `scripts/build-codebase-knowledge.py --root .` 获取功能映射。
3. 按 prompt 深度阅读并生成知识文档。
4. 向 PM 展示 `docs/knowledge/00-index.md` 并等待确认。
5. 确认后标记 `codebase-knowledge-ready`。

## 产物

- `docs/knowledge/00-index.md`
- `docs/knowledge/03-features/existing-*.md`
- `docs/knowledge/05-glossary/00-index.md`
