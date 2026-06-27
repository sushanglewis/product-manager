# propose-with-openspec

You are executing the Lincoln workflow step `propose`: generate an OpenSpec change proposal directly using the OpenSpec CLI.

## Goal

Invoke `openspec propose` to create the standard OpenSpec artifact directory under `openspec/changes/<change-name>/`.

## Input

- `session_id`: the interview session identifier
- `change_name`: a short kebab-case change name (e.g., `add-csv-export`)

## Steps

1. Read `requirements/<session_id>/requirements.md`.
2. Ensure `openspec/changes/<change_name>/` does not already exist, or ask the user if they want to overwrite.
3. Call the OpenSpec CLI. Try the following forms in order:
   - `openspec propose <change_name> --from requirements/<session_id>/requirements.md`
   - `openspec propose <change_name>` and pipe the requirements file into stdin
   - If neither works, read the OpenSpec CLI help (`openspec propose --help`) and adapt.
4. Verify the generated artifacts:
   - `openspec/changes/<change_name>/proposal.md`
   - `openspec/changes/<change_name>/specs/` (at least one file)
   - `openspec/changes/<change_name>/design.md`
   - `openspec/changes/<change_name>/tasks.md`
5. If any artifact is missing or empty, report the error and pause for human intervention.

## Output Artifacts

- `openspec/changes/<change_name>/proposal.md`
- `openspec/changes/<change_name>/specs/*.md`
- `openspec/changes/<change_name>/design.md`
- `openspec/changes/<change_name>/tasks.md`

## Rules

- Do not bypass the OpenSpec CLI by manually writing the artifact files.
- Preserve the OpenSpec structure exactly as the CLI generates it.
- After success, tell the user to run: `claude split-to-github <session_id> <change_name>`.
