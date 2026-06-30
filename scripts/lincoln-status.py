#!/usr/bin/env python3
"""
Lincoln branch status reporter.

Reports the current Lincoln branch state including stage, status, waiting_for,
loaded context files, required skills, artifacts, and next action.

Usage:
    python scripts/lincoln-status.py [--format json|table|markdown] [--branch <branch>]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

# Re-use stage_loader helpers
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.stage_loader import (  # noqa: E402
    PROJECT_ROOT,
    STATE_PATH,
    STAGES_DIR,
    compute_next_stage,
    find_stage,
    load_state,
    load_workflow,
    now_iso,
)

SKILL_ROUTING_PATH = PROJECT_ROOT / ".claude" / "skill-routing.yaml"


def get_waiting_for(stage_status: str | None, stage_def: dict[str, Any]) -> str:
    """Determine who/what is being waited for based on stage status."""
    if stage_status == "waiting_for_human":
        return "pm"
    if stage_status == "validation_failed":
        return "agent-fix"
    if stage_status == "in_progress":
        return "agent"
    if stage_status == "completed":
        return "next-role"
    if stage_status == "entry_validating":
        return "agent"
    if stage_status == "not_started":
        # If stage has human_gate and hasn't started, waiting for human to kick it off
        if stage_def.get("human_gate", False):
            return "pm"
        return "agent"
    return "none"


def get_loaded_context(stage_id: str) -> list[str]:
    """Return paths to context files for the given stage."""
    stage_dir = STAGES_DIR / stage_id
    context_files = []
    for filename in ["AGENTS.md", "CHECKLIST.md", "SKILLS.md", "PROMPT.md"]:
        path = stage_dir / filename
        if path.exists():
            context_files.append(str(path.relative_to(PROJECT_ROOT)))
    return context_files


def get_required_skills(stage_id: str) -> dict[str, list[str]]:
    """Read skill-routing.yaml for required/optional skills for the stage."""
    if not SKILL_ROUTING_PATH.exists():
        return {"required": [], "optional": []}
    try:
        data = yaml.safe_load(SKILL_ROUTING_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"required": [], "optional": []}

    routing = data.get("routing", {}) if isinstance(data, dict) else {}
    stage_routing = routing.get(stage_id, {})
    return {
        "required": stage_routing.get("required", []),
        "optional": stage_routing.get("optional", []),
    }


def get_required_artifacts(workflow: dict[str, Any], stage_id: str) -> list[str]:
    """Return artifact paths declared in the workflow for the stage."""
    stage_def = find_stage(workflow, stage_id)
    return stage_def.get("artifacts", [])


def get_next_action(state: dict[str, Any], stage_id: str | None, workflow: dict[str, Any]) -> str:
    """Generate a human-readable one-liner describing the next action."""
    if not stage_id:
        run_status = state.get("current_run", {}).get("status", "unknown")
        if run_status == "completed":
            return "Workflow complete. No further action required."
        return "No active stage. Run recovery to determine resume point."

    stage_state = state.get("stages", {}).get(stage_id, {})
    stage_status = stage_state.get("status", "unknown")
    stage_def = find_stage(workflow, stage_id)
    human_gate = stage_def.get("human_gate", False)
    waiting_for = get_waiting_for(stage_status, stage_def)

    if stage_status == "not_started":
        if human_gate:
            return f"Stage '{stage_id}' not started. Human confirmation required to begin."
        return f"Stage '{stage_id}' ready to start. Run entry validation and begin work."

    if stage_status == "entry_validating":
        return f"Entry validation in progress for stage '{stage_id}'."

    if stage_status == "in_progress":
        if human_gate and not stage_state.get("human_gate_passed"):
            return f"Stage '{stage_id}' in progress. Complete work and await human gate approval."
        return f"Stage '{stage_id}' in progress. Complete work and run exit validation."

    if stage_status == "waiting_for_human":
        return f"Stage '{stage_id}' paused for human review/approval."

    if stage_status == "validation_failed":
        retry = stage_state.get("retry_count", 0)
        return f"Stage '{stage_id}' validation failed (retry {retry}). Fix issues and re-run validation."

    if stage_status == "completed":
        next_stage = compute_next_stage(workflow, stage_id)
        if next_stage:
            return f"Stage '{stage_id}' completed. Proceed to next stage: '{next_stage}'."
        return f"Stage '{stage_id}' completed. This is the final stage."

    return f"Stage '{stage_id}' status: {stage_status}. Waiting for: {waiting_for}."


def compute_metrics(state: dict[str, Any]) -> dict[str, Any]:
    """Compute workflow metrics summary."""
    stages = state.get("stages", {})
    total = len(stages)
    completed = sum(1 for s in stages.values() if s.get("status") == "completed")
    failed = sum(1 for s in stages.values() if s.get("status") == "validation_failed")
    waiting_for_human = sum(
        1 for sid, s in stages.items()
        if s.get("status") in ("waiting_for_human", "not_started")
        and _stage_has_human_gate(state, sid)
    )
    return {
        "total_stages": total,
        "completed": completed,
        "failed": failed,
        "waiting_for_human": waiting_for_human,
    }


def _stage_has_human_gate(state: dict[str, Any], stage_id: str) -> bool:
    """Check if a stage has human_gate enabled by looking at the workflow."""
    template_name = state.get("current_run", {}).get("workflow_template")
    try:
        workflow = load_workflow(template_name)
        stage_def = find_stage(workflow, stage_id)
        return stage_def.get("human_gate", False)
    except Exception:
        return False


def build_status_report(state: dict[str, Any]) -> dict[str, Any]:
    """Build the full status report dictionary."""
    current_run = state.get("current_run", {})
    stage_id = current_run.get("current_stage")
    template_name = current_run.get("workflow_template")

    workflow = load_workflow(template_name)

    stage_state = state.get("stages", {}).get(stage_id, {}) if stage_id else {}
    stage_def = find_stage(workflow, stage_id) if stage_id else {}

    skills = get_required_skills(stage_id) if stage_id else {"required": [], "optional": []}
    artifacts = get_required_artifacts(workflow, stage_id) if stage_id else []

    return {
        "branch": current_run.get("branch", "unknown"),
        "run_id": current_run.get("run_id", "unknown"),
        "workflow_template": template_name or "unknown",
        "current_stage": stage_id,
        "previous_stage": current_run.get("previous_stage"),
        "run_status": current_run.get("status", "unknown"),
        "stage_status": stage_state.get("status", "unknown"),
        "entry_checks_passed": stage_state.get("entry_checks_passed"),
        "exit_checks_passed": stage_state.get("exit_checks_passed"),
        "human_gate_passed": stage_state.get("human_gate_passed"),
        "retry_count": stage_state.get("retry_count", 0),
        "waiting_for": get_waiting_for(stage_state.get("status"), stage_def) if stage_id else "none",
        "loaded_context": get_loaded_context(stage_id) if stage_id else [],
        "required_skills": skills.get("required", []),
        "optional_skills": skills.get("optional", []),
        "required_artifacts": artifacts,
        "next_action": get_next_action(state, stage_id, workflow),
        "metrics": compute_metrics(state),
    }


def format_json(report: dict[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2)


def format_table(report: dict[str, Any]) -> str:
    lines = []
    lines.append("=" * 70)
    lines.append("LINCOLN BRANCH STATUS")
    lines.append("=" * 70)
    lines.append(f"{'Branch:':<25} {report['branch']}")
    lines.append(f"{'Run ID:':<25} {report['run_id']}")
    lines.append(f"{'Workflow Template:':<25} {report['workflow_template']}")
    lines.append(f"{'Current Stage:':<25} {report['current_stage'] or '(none)'}")
    lines.append(f"{'Previous Stage:':<25} {report['previous_stage'] or '(none)'}")
    lines.append(f"{'Run Status:':<25} {report['run_status']}")
    lines.append(f"{'Stage Status:':<25} {report['stage_status']}")
    lines.append(f"{'Entry Checks:':<25} {report['entry_checks_passed']}")
    lines.append(f"{'Exit Checks:':<25} {report['exit_checks_passed']}")
    lines.append(f"{'Human Gate:':<25} {report['human_gate_passed']}")
    lines.append(f"{'Retry Count:':<25} {report['retry_count']}")
    lines.append(f"{'Waiting For:':<25} {report['waiting_for']}")
    lines.append("")
    lines.append("-" * 70)
    lines.append("LOADED CONTEXT")
    lines.append("-" * 70)
    for ctx in report["loaded_context"]:
        lines.append(f"  - {ctx}")
    if not report["loaded_context"]:
        lines.append("  (none)")
    lines.append("")
    lines.append("-" * 70)
    lines.append("REQUIRED SKILLS")
    lines.append("-" * 70)
    for skill in report["required_skills"]:
        lines.append(f"  [R] {skill}")
    for skill in report.get("optional_skills", []):
        lines.append(f"  [O] {skill}")
    if not report["required_skills"] and not report.get("optional_skills"):
        lines.append("  (none configured)")
    lines.append("")
    lines.append("-" * 70)
    lines.append("REQUIRED ARTIFACTS")
    lines.append("-" * 70)
    for art in report["required_artifacts"]:
        lines.append(f"  - {art}")
    if not report["required_artifacts"]:
        lines.append("  (none)")
    lines.append("")
    lines.append("-" * 70)
    lines.append("NEXT ACTION")
    lines.append("-" * 70)
    lines.append(f"  {report['next_action']}")
    lines.append("")
    lines.append("-" * 70)
    lines.append("METRICS")
    lines.append("-" * 70)
    m = report["metrics"]
    lines.append(f"  Total stages:        {m['total_stages']}")
    lines.append(f"  Completed:           {m['completed']}")
    lines.append(f"  Failed:              {m['failed']}")
    lines.append(f"  Waiting for human:   {m['waiting_for_human']}")
    lines.append("=" * 70)
    return "\n".join(lines)


def format_markdown(report: dict[str, Any]) -> str:
    lines = []
    lines.append("# Lincoln Branch Status")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("|-------|-------|")
    lines.append(f"| Branch | `{report['branch']}` |")
    lines.append(f"| Run ID | `{report['run_id']}` |")
    lines.append(f"| Workflow Template | `{report['workflow_template']}` |")
    lines.append(f"| Current Stage | `{report['current_stage'] or 'none'}` |")
    lines.append(f"| Previous Stage | `{report['previous_stage'] or 'none'}` |")
    lines.append(f"| Run Status | `{report['run_status']}` |")
    lines.append(f"| Stage Status | `{report['stage_status']}` |")
    lines.append(f"| Entry Checks Passed | `{report['entry_checks_passed']}` |")
    lines.append(f"| Exit Checks Passed | `{report['exit_checks_passed']}` |")
    lines.append(f"| Human Gate Passed | `{report['human_gate_passed']}` |")
    lines.append(f"| Retry Count | `{report['retry_count']}` |")
    lines.append(f"| Waiting For | `{report['waiting_for']}` |")
    lines.append("")
    lines.append("## Loaded Context")
    if report["loaded_context"]:
        for ctx in report["loaded_context"]:
            lines.append(f"- `{ctx}`")
    else:
        lines.append("_No context files found._")
    lines.append("")
    lines.append("## Required Skills")
    if report["required_skills"]:
        lines.append("**Required:**")
        for skill in report["required_skills"]:
            lines.append(f"- `{skill}`")
    if report.get("optional_skills"):
        lines.append("**Optional:**")
        for skill in report["optional_skills"]:
            lines.append(f"- `{skill}`")
    if not report["required_skills"] and not report.get("optional_skills"):
        lines.append("_No skills configured._")
    lines.append("")
    lines.append("## Required Artifacts")
    if report["required_artifacts"]:
        for art in report["required_artifacts"]:
            lines.append(f"- `{art}`")
    else:
        lines.append("_No artifacts required._")
    lines.append("")
    lines.append("## Next Action")
    lines.append(f"> {report['next_action']}")
    lines.append("")
    lines.append("## Metrics")
    m = report["metrics"]
    lines.append(f"- **Total stages:** {m['total_stages']}")
    lines.append(f"- **Completed:** {m['completed']}")
    lines.append(f"- **Failed:** {m['failed']}")
    lines.append(f"- **Waiting for human:** {m['waiting_for_human']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Lincoln branch status reporter")
    parser.add_argument(
        "--format",
        choices=["json", "table", "markdown"],
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument(
        "--branch",
        help="Branch name (default: read from workflow-state.yaml)",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        default=STATE_PATH,
        help="Path to workflow-state.yaml",
    )
    args = parser.parse_args()

    state = load_state(args.state_file)

    # If --branch is specified but differs from state, note it but still report state
    report = build_status_report(state)
    if args.branch and report["branch"] != args.branch:
        report["_note"] = f"Requested branch '{args.branch}' but state shows '{report['branch']}'"

    if args.format == "json":
        print(format_json(report))
    elif args.format == "table":
        print(format_table(report))
    elif args.format == "markdown":
        print(format_markdown(report))

    return 0


if __name__ == "__main__":
    sys.exit(main())
