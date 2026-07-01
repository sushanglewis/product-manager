# build-product-prototype

You are executing the Lincoln workflow step `product-prototype`: turn approved product design documents into UI/field specifications and a Pencil prototype.

## Goal

Create a product prototype source file that the PM can directly inspect and modify in Pencil, with Markdown specs that developers can use later.

## Input

- `session_id`: the interview session identifier
- `design_id`: the product design identifier

## Steps

1. Verify `designs/<design_id>/design-review.md` contains `<!-- status: approved -->` or `[x] PM 已确认设计文档`.
2. Read the approved design package under `designs/<design_id>/`.
3. Write `fields.md` with screen/form fields, data type, required/optional status, validation, default value, copy, error state, and source data object.
4. Write `ui-spec.md` with target user flow, screens, interactions, component states, empty/loading/error states, accessibility notes, and implementation constraints.
5. Use Pencil tools to create or update `designs/<design_id>/prototype.pen`.
6. Before using Pencil tools, call `get_editor_state(include_schema: true)` if the current `.pen` schema is not already known.
7. After generating the prototype, use `snapshot_layout` to check for clipped or overlapping elements. Fix layout issues before asking for review.
8. Ask the PM to open and edit `designs/<design_id>/prototype.pen` in Pencil. Treat the saved `.pen` as the final development reference.
9. When the PM confirms the prototype, add `<!-- prototype-status: approved -->` to `ui-spec.md`.

## Output Artifacts

- `designs/<design_id>/fields.md`
- `designs/<design_id>/ui-spec.md`
- `designs/<design_id>/prototype.pen`

## Rules

- Never read or modify `.pen` files with normal file tools; use Pencil tools or the Pencil application only.
- Do not rely on screenshots or HTML as the main approval artifact. They are optional review aids only.
- Keep controls and states complete enough for implementation: default, hover/focus where relevant, disabled, empty, loading, error, and success.
- After approval, tell the user to run: `claude plan-tdd-development <session_id> <design_id>`.
