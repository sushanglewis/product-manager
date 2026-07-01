---
name: lincoln-workflow-router
description: Use at the start of a Lincoln session to assess repository context and select the most appropriate workflow template.
version: 1.0.0
---

# Lincoln Workflow Router

## Purpose

Inspects the current project context and chooses a workflow template from `.claude/workflows/templates/`.

## When to Use

- At session start when `.claude/workflow-stage.yaml` has no `workflow.template`.
- When the human PM says "重新评估工作流" or asks to switch templates.

## Inputs

- Repository root contents
- `.claude/workflow-stage.yaml`
- Human's stated intent (interview, bug fix, design spike, existing project, etc.)

## Outputs

- Recommended `workflow.template` name
- Recommended `current_run.current_stage`
- Confidence score and 1-3 confirmation questions if needed

## Rules

- Do not proceed with any implementation until the PM confirms or overrides the recommended template.
- If context is ambiguous, prefer the simplest template that matches the stated intent.
- Document the reasoning in `current_run.context_assessment`.
