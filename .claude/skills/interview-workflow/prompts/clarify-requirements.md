# clarify-requirements

You are executing the Lincoln workflow step `clarify`: turn interview artifacts into a structured requirements document through multi-round clarification with the human PM.

## Goal

Produce a clear, agreed-upon `requirements/<session-id>/requirements.md` that serves as the single source of truth for this interview.

## Input

- `session_id`: the interview session identifier

## Steps

1. Read `interviews/<session-id>/transcript.md`, `summary.md`, and `raw-insights.md`.
2. Create `requirements/<session-id>/` if it does not exist.
3. Draft an initial `requirements.md` using the template:
   - Background
   - Problem
   - Users / Personas
   - Proposed Solution
   - Acceptance Criteria
   - Out of Scope
   - Open Questions
4. Identify 1-3 ambiguities or missing details.
5. Ask the human PM these questions one batch at a time in the terminal.
6. Update `requirements.md` based on the answers.
7. Repeat until the PM confirms the requirements are clear.
8. Also generate `user-stories.md` and `prd.md` from the finalized requirements.

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
