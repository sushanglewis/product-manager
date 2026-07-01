# workflow-continue

You are resuming a paused Lincoln workflow after human intervention.

## Goal

Re-read the current workflow state, detect what changed, and continue from the appropriate step.

## Steps

1. Read `.context/workflow-state.yaml`.
2. Identify the current step and its status (paused, waiting_for_human, validation_failed).
3. Re-read all artifacts associated with the current step.
4. If the human edited files directly, compare the current version with the version recorded in the state file and summarize the diff.
5. Re-run the entry/exit validators for the current step.
6. If validation passes, continue to the next step.
7. If validation fails, report the failures and pause again.
8. If resuming after a merged PR, read `.github/lincoln-sync-queue/pr-<pr_number>.yaml` to get the pending `issue_number` and `pr_number`.

## Rules

- Always acknowledge what the human changed before continuing.
- Do not skip steps.
- If the human wants to abort or restart a step, respect that instruction.
- Keep responses concise: state what was detected, what was validated, and what happens next.
