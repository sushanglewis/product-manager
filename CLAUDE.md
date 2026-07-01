# Lincoln - Agent Contract

This file defines the contract for any Claude Code Agent working in a Lincoln repository. Lincoln is an AI-native product-management workflow template that orchestrates stages, gates, artifacts, skills, and roles to turn raw inputs into shipped features and maintained knowledge.

This file is for users of the template. If you are developing Lincoln itself, see the repository README and framework docs in `docs/framework/`.

## Session Startup Protocol

Every Agent entering a Lincoln session must execute the following steps in order:

1. Run `python3 scripts/lincoln-status.py --format markdown` and display the result.
2. Read `.claude/workflow-stage.yaml` and `.claude/stages/stage-manifest.yaml`.
3. Read current stage context files from stage-manifest.yaml: AGENTS.md, CHECKLIST.md, SKILLS.md, PROMPT.md.
4. Read `.claude/agents/default.md` and the role agent matching the current stage (pm / designer / engineer).
5. Read `.claude/skills/routing.yaml` for current stage required/optional skills.
6. Run `python3 scripts/stage_loader.py --stage <current_stage> --action validate-entry`.
7. Report to human: current stage, loaded context files, required skills, waiting_for, next action.

If `.claude/workflow-stage.yaml` does not exist but `.claude/workflow-state.yaml` exists, read the legacy file and note that a migration is needed.

If any step fails, pause and report the failure before proceeding.

Note: When `.claude/settings.json` is honored by Claude Code, the `SessionStart` hook automatically performs dependency detection, state parsing, handoff reading, and context injection. Agents should still verify the output and report to the human PM.

## Human Gate Rules

- `human_gate: true` steps cannot be skipped.
- Required explicit `confirm` or approved marker from the human PM.
- Do not proceed to the next stage until the human gate is explicitly passed.
- The `pre-tool-use.sh` hook enforces read-only mode when a stage is paused or waiting for human.

## Handoff Protocol

When pausing or switching windows:

1. Run `python3 scripts/stage_loader.py --stage <current_stage> --action handoff-report` to update `.context/lincoln-handoff-<stage>.md`.
2. Push the branch so others can resume.
3. The `.context/lincoln-handoff-<stage>.md` file contains the human-readable summary of current stage, artifacts, blockers, and next action.
4. Run `python3 scripts/stage_loader.py --stage <current_stage> --action approve-gate` after the human PM confirms the stage is complete.

## Observability Reporting

Every reply must briefly state:

- Current stage
- Skills used in this reply
- Artifacts produced or modified
- Validation status (entry checks passed, exit checks pending, etc.)

## Skill Invocation Rules

- Invoke skills via the Skill tool using exact names from `.claude/skills/routing.yaml`.
- Never substitute `human_gate` with a skill invocation.
- Required skills for the current stage should be invoked when the stage begins.
- Optional skills may be invoked based on situational need.
- Skill names use colon notation: `superpowers:brainstorming`, `gsd:plan-phase`, `oh-my-claudecode:team`, etc.

## Branch Progress Documentation

- Authoritative state: `.claude/workflow-stage.yaml`
- Legacy state (migrate): `.claude/workflow-state.yaml`
- Human-readable handoff: `.context/lincoln-handoff-<stage>.md`
- Branch progress dashboard: `scripts/list-active-lincoln-branches.sh`
- Skill routing: `.claude/skills/routing.yaml`
- Stage manifest: `.claude/stages/stage-manifest.yaml`
- Agent templates: `.claude/agents/`
- Hooks configuration: `.claude/settings.json`

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
