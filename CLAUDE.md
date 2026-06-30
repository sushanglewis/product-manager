# Lincoln - Agent Contract

This file defines the contract for any Claude Code Agent working in a Lincoln repository. Lincoln is an AI-native product-management workflow template that orchestrates stages, gates, artifacts, skills, and roles to turn raw inputs into shipped features and maintained knowledge.

This file is for users of the template. If you are developing Lincoln itself, see the repository README and framework docs in `docs/framework/`.

## Session Startup Protocol

Every Agent entering a Lincoln session must execute the following steps in order:

1. Run `python3 scripts/lincoln-status.py --format markdown` and display the result.
2. Read `.claude/workflow-state.yaml` and `.claude/stages/stage-manifest.yaml`.
3. Read current stage context files from stage-manifest.yaml: AGENTS.md, CHECKLIST.md, SKILLS.md, PROMPT.md.
4. Read `.claude/skill-routing.yaml` for current stage required/optional skills.
5. Run `python3 scripts/stage_loader.py --stage <current_stage> --action validate-entry`.
6. Report to human: current stage, loaded context files, required skills, waiting_for, next action.

If any step fails, pause and report the failure before proceeding.

## Human Gate Rules

- `human_gate: true` steps cannot be skipped.
- Required explicit `confirm` or approved marker from the human PM.
- Do not proceed to the next stage until the human gate is explicitly passed.
- The `pre-tool-use.sh` hook enforces read-only mode when a stage is paused or waiting for human.

## Handoff Protocol

When pausing or switching windows:

1. Run `python3 scripts/stage_loader.py --stage <current_stage> --action handoff-report` to update `.context/lincoln-handoff.md`.
2. Push the branch so others can resume.
3. The `.context/lincoln-handoff.md` file contains the human-readable summary of current stage, artifacts, blockers, and next action.

## Observability Reporting

Every reply must briefly state:

- Current stage
- Skills used in this reply
- Artifacts produced or modified
- Validation status (entry checks passed, exit checks pending, etc.)

## Skill Invocation Rules

- Invoke skills via the Skill tool using exact names from `skill-routing.yaml`.
- Never substitute `human_gate` with a skill invocation.
- Required skills for the current stage should be invoked when the stage begins.
- Optional skills may be invoked based on situational need.
- Skill names use colon notation: `superpowers:brainstorming`, `gsd:plan-phase`, `oh-my-claudecode:team`, etc.

## Branch Progress Documentation

- Authoritative state: `.claude/workflow-state.yaml`
- Human-readable handoff: `.context/lincoln-handoff.md`
- Branch progress dashboard: `scripts/list-active-lincoln-branches.sh`
- Skill routing: `.claude/skill-routing.yaml`
- Stage manifest: `.claude/stages/stage-manifest.yaml`

## Core Principles

1. **Workflow first**: Every action must conform to the current stage and its checks.
2. **Human gate is sacred**: Never bypass a human gate.
3. **Artifacts are traceable**: Every output must link back to its source stage and validation.
4. **Knowledge dual-track**: Business and technical knowledge are maintained together.
5. **Do not modify originals**: `recordings/` files are read-only.
6. **Pencil files are special**: `.pen` files are handled only via Pencil tools, never plain text editors.

## Communication Style

- Use Chinese when communicating with the human PM.
- Keep progress reports concise: current step, artifact location, next human action.
- When uncertain, pause and ask. Never guess.
