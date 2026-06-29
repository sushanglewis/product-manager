# clarify-requirements

You are executing the Lincoln workflow step `clarify`: turn interview artifacts into a structured requirements document through multi-round clarification with the human PM.

## Goal

Produce a clear, agreed-upon `requirements/<session-id>/requirements.md` that serves as the single source of truth for this interview.

## Input

- `session_id`: the interview session identifier

## 子技能准备

在执行本 prompt 前：
- 若存在外部需求/计划文件，先调用 `gsd-import` 进行冲突检测。
- 调用 `superpowers:brainstorming` 与 PM 一起探索 2-3 种可能的需求视角，列出 trade-offs。  
  **在 PM 明确选择方向前，禁止继续生成需求文档。**

## Steps

1. Read `interviews/<session-id>/transcript.md`, `summary.md`, and `raw-insights.md`.
2. Create `requirements/<session-id>/` if it does not exist.
3. Draft an initial `requirements.md` using the template:
   - `背景`
   - `问题`
   - `用户`
   - `方案`
   - `验收标准`
   - `非目标`
   - `开放问题`
4. Identify 1-3 ambiguities or missing details.
5. Ask the human PM these questions one batch at a time in the terminal.
6. Update `requirements.md` based on the answers.
7. Repeat until the PM confirms the requirements are clear.
8. Also generate `user-stories.md` and `prd.md` from the finalized requirements.
9. When the PM confirms, add an approval marker to `requirements.md`: `<!-- status: approved -->`.

## Human Interaction Rules

- Ask at most 3 questions per turn.
- After each answer, update the document and show the changed sections.
- If the PM edits `requirements.md` directly and runs `workflow-continue`, re-read the file and continue from there.
- Do not proceed to the next step until the PM explicitly confirms (e.g., says "confirm" or "确认").

## Output Artifacts

- `requirements/<session-id>/requirements.md`
- `requirements/<session-id>/user-stories.md`
- `requirements/<session-id>/prd.md`

## Traceability

Every requirement must reference the transcript timestamp where it originated, e.g., `(来源: 00:03:22)`.

## Next Step

After confirmation, tell the user to run: `claude propose-with-openspec <session-id> <change-name>`.
