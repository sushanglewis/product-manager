# draft-product-design

You are executing the Lincoln workflow step `product-design-docs`: turn approved requirements into a concise product design review package for the human PM.

## Goal

Create `designs/<design_id>/` with enough product, data, flow, feasibility, and technical framing for PM review and later development planning, without creating unnecessary review burden.

## Input

- `session_id`: the interview session identifier
- `design_id`: a kebab-case product design identifier

## 子技能准备

在执行本 prompt 前：
1. 调用 `superpowers:brainstorming` 探索 ≥2 种设计方向并说明 trade-offs，等待 PM 确认。
2. PM 确认后，调用 `superpowers:writing-plans` 规划文档文件结构与每份文档的职责。

## Steps

1. Validate that `requirements/<session_id>/requirements.md` is approved.
2. Create `designs/<design_id>/`.
3. Read `requirements/<session_id>/requirements.md`, `user-stories.md`, and `prd.md`.
4. Produce the design package:
   - `design-review.md`: PM-facing entry point with decision summary, scope, links to all design docs, open questions, and approval checklist.
   - `scenarios.md`: target users, primary scenarios, boundary scenarios, and non-goals.
   - `feature-catalog.md`: concise feature list, priority, acceptance mapping, and source requirement links.
   - `data-model.md`: core entities, fields, constraints, validation rules, and state transitions.
   - `flows.md`: Mermaid user flow, business flow, sequence diagram, and architecture diagram.
   - `feasibility.md`: business feasibility, technical feasibility, current official framework/library options, usable open-source projects, risks, and recommended stack.
5. Keep all documents traceable to the approved requirement and transcript timestamps where available.
6. Ask the PM to review `design-review.md` and linked docs.
7. When the PM confirms, add `<!-- status: approved -->` to `design-review.md`.

## Rules

- Use Chinese for PM-facing content unless the requirements are in English.
- Keep documents short and reviewable; prefer tables and Mermaid diagrams over long prose.
- For technical frameworks and open-source projects, check current official docs or primary repositories before recommending.
- Do not create a Pencil prototype in this step.
- After approval, tell the user to run: `claude build-product-prototype <session_id> <design_id>`.
