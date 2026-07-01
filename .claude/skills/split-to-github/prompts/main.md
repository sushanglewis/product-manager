# split-to-github

You are executing the Lincoln workflow step `split`: convert OpenSpec tasks into GitHub Issues in the configured target repository.

## Goal

Create one GitHub Issue per actionable task from `openspec/changes/<change_name>/tasks.md`.

## Input

- `session_id`: the interview session identifier
- `change_name`: the OpenSpec change name

## Steps

1. Read `.github/openspec-config.yml` to get the target repository `owner/name`.
2. Read `openspec/changes/<change_name>/tasks.md`.
3. Parse the task list. For each task:
   - Create a GitHub Issue in the target repo using `gh issue create` or the GitHub MCP.
   - Title: clear, action-oriented
   - Body must include:
     - User story
     - Acceptance criteria
     - Source interview: `interviews/<session_id>/`
     - Source requirement: `requirements/<session_id>/requirements.md`
     - Source OpenSpec change: `openspec/changes/<change_name>/`
     - Relevant transcript timestamps
   - Apply labels: `from-interview`, `openspec`
4. Write `.github/linked-issues.yaml` mapping tasks to issue numbers.
5. Update `requirements/<session_id>/requirements.md` to record the created issue numbers.

## Output Artifacts

- `.github/linked-issues.yaml`
- Updated `requirements/<session_id>/requirements.md`
- GitHub Issues in the target repository

## Rules

- Do not create issues without a clear acceptance criterion.
- Each issue should map to exactly one OpenSpec task.
- After completion, tell the user the issues are ready for implementation.
