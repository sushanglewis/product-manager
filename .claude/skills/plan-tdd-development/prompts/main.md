# plan-tdd-development

You are executing the Lincoln workflow step `tdd-development-plan`: turn the confirmed product design and Pencil prototype into a TDD development plan.

## Goal

Create `designs/<design_id>/tdd-plan.md` as the bridge from product design to OpenSpec and GitHub Issues.

## Input

- `session_id`: the interview session identifier
- `design_id`: the product design identifier

## 子技能准备

在执行本 prompt 前：
1. 调用 `superpowers:writing-plans` 规划 `tdd-plan.md` 结构。
2. 遵循 `superpowers:test-driven-development` 方法论：确保每个任务切片都是“先写失败测试 → 最小实现 → 重构”序列。
3. 在 `tdd-plan.md` 头部加入：  
   `> **Required sub-skill:** Use superpowers:test-driven-development for all implementation`

## Steps

1. Verify that `designs/<design_id>/ui-spec.md` contains `<!-- prototype-status: approved -->` or `[x] PM 已确认原型`.
2. Confirm `designs/<design_id>/prototype.pen`, `fields.md`, and the design review package exist.
3. Read the confirmed design docs and inspect the `.pen` through Pencil tools if visual structure is needed.
4. Write `tdd-plan.md` with:
   - Source links to requirements, design docs, fields, UI spec, and `prototype.pen`
   - Acceptance criteria mapping
   - Test scenarios grouped by user workflow
   - Red/green/refactor implementation sequence
   - Unit, integration, contract, UI, and regression test boundaries
   - Data fixtures and validation cases
   - Task slices suitable for OpenSpec tasks and GitHub Issues
   - Risks, dependencies, and out-of-scope items
5. Add `<!-- status: ready-for-openspec -->` when the plan is complete.

## Rules

- Keep the plan executable by an engineer without requiring extra product decisions.
- Every task slice must map back to a design artifact and acceptance criterion.
- Do not generate OpenSpec artifacts in this step.
- After completion, tell the user to run: `claude propose-with-openspec <session_id> <design_id> <change_name>`.
