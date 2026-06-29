---
name: lincoln-build-codebase-knowledge
description: Use when starting Lincoln on an existing project with source code but no feature knowledge base yet.
version: 1.0.0
---

# Lincoln Build Codebase Knowledge

## Purpose

Scan an existing codebase, identify its major features/modules, and generate feature knowledge documents under `docs/knowledge/` so Lincoln can iterate from facts instead of assumptions.

## When to Use

- Project already has source code.
- `docs/knowledge/03-features/` is empty or out of date.
- The `existing-project-iteration` workflow template is active.

## Inputs

- Repository root
- Existing source tree
- Existing `README.md`, `CHANGELOG.md`, and any architectural docs

## Outputs

- `docs/knowledge/00-index.md` — master index
- `docs/knowledge/03-features/existing-<feature>.md` — one per core feature
- `docs/knowledge/05-glossary/00-index.md` — domain terms inferred from code

## Rules

- Do not modify source code.
- Infer features from directory structure, public APIs, and README.
- Cross-check generated docs against source files (cite file paths).
- Stop and ask the PM when confidence is low.
