# propose-with-openspec

You are executing the Lincoln workflow step `propose`: generate an OpenSpec change proposal directly using the OpenSpec CLI.

## Goal

Invoke `openspec propose` using the confirmed TDD development plan to create the standard OpenSpec artifact directory under `openspec/changes/<change-name>/`.

## Input

- `session_id`: the interview session identifier
- `design_id`: the product design identifier
- `change_name`: a short kebab-case change name (e.g., `add-csv-export`)

## Steps

1. Read `requirements/<session_id>/requirements.md`.
2. Read `designs/<design_id>/tdd-plan.md`, `design-review.md`, `feature-catalog.md`, `data-model.md`, `flows.md`, `feasibility.md`, `fields.md`, and `ui-spec.md`.
3. Verify `designs/<design_id>/tdd-plan.md` contains `<!-- status: ready-for-openspec -->`.
4. Ensure `openspec/changes/<change_name>/` does not already exist, or ask the user if they want to overwrite.
5. Call the OpenSpec CLI. Try the following forms in order:
   - `openspec propose <change_name> --from designs/<design_id>/tdd-plan.md`
   - `openspec propose <change_name>` and pipe the TDD plan plus design summary into stdin
   - If neither works, read the OpenSpec CLI help (`openspec propose --help`) and adapt.
6. Verify the generated artifacts:
   - `openspec/changes/<change_name>/proposal.md`
   - `openspec/changes/<change_name>/specs/` (at least one file)
   - `openspec/changes/<change_name>/design.md`
   - `openspec/changes/<change_name>/tasks.md`
7. Ensure the OpenSpec artifact references:
   - `designs/<design_id>/tdd-plan.md`
   - `designs/<design_id>/prototype.pen`
   - Core design docs under `designs/<design_id>/`
8. Call `superpowers:verification-before-completion` to verify the artifacts before claiming completion:
   - Run `python .claude/skills/interview-workflow/validators/validate.py --phase exit --check openspec_artifact_complete --args <change_name>,<design_id>`
   - Run `python .claude/skills/interview-workflow/validators/validate.py --phase exit --check tasks_extracted --args <change_name>`
   - Read the output and confirm PASS. Do not claim completion without fresh verification evidence.
9. If any artifact is missing, empty, or missing design references, report the error and pause for human intervention.

## Output Artifacts

- `openspec/changes/<change_name>/proposal.md`
- `openspec/changes/<change_name>/specs/*.md`
- `openspec/changes/<change_name>/design.md`
- `openspec/changes/<change_name>/tasks.md`

## Rules

- Do not bypass the OpenSpec CLI by manually writing the artifact files.
- Preserve the OpenSpec structure exactly as the CLI generates it.
- OpenSpec tasks must be driven by `designs/<design_id>/tdd-plan.md`.
- After success, tell the user to run: `claude split-to-github <session_id> <change_name>`.
