#!/usr/bin/env python3
"""
Lincoln workflow health auditor.

Runs a set of audit rules against the workflow state and reports PASS/WARN/FAIL.

Usage:
    python scripts/lincoln-audit.py [--format json|markdown]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.stage_loader import (  # noqa: E402
    PROJECT_ROOT,
    STATE_PATH,
    compute_next_stage,
    find_stage,
    load_state,
    load_workflow,
)

HANDOFF_PATH = PROJECT_ROOT / ".context" / "lincoln-handoff.md"


def _parse_iso(ts: str | None) -> Any:
    """Parse ISO timestamp string to datetime, or None."""
    if not ts:
        return None
    from datetime import datetime
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def audit_state_consistency(state: dict[str, Any], workflow: dict[str, Any]) -> dict[str, Any]:
    """Check that current_stage is consistent with completed stages sequence."""
    stages = state.get("stages", {})
    current_stage = state.get("current_run", {}).get("current_stage")
    step_ids = [s["id"] for s in workflow.get("steps", [])]

    if not current_stage:
        # Workflow may be completed
        run_status = state.get("current_run", {}).get("status")
        if run_status == "completed":
            return {"check": "state_consistency", "status": "PASS", "message": "Workflow completed; no current stage."}
        return {"check": "state_consistency", "status": "WARN", "message": "No current stage and workflow not marked completed."}

    # All stages before current_stage should be completed
    try:
        current_idx = step_ids.index(current_stage)
    except ValueError:
        return {"check": "state_consistency", "status": "FAIL", "message": f"Current stage '{current_stage}' not found in workflow."}

    issues = []
    for i, sid in enumerate(step_ids[:current_idx]):
        stage_state = stages.get(sid, {})
        if stage_state.get("status") != "completed":
            issues.append(f"Stage '{sid}' (before current) has status '{stage_state.get('status')}' not 'completed'")

    if issues:
        return {"check": "state_consistency", "status": "FAIL", "message": "; ".join(issues)}
    return {"check": "state_consistency", "status": "PASS", "message": "Stage sequence is consistent."}


def audit_artifact_completeness(state: dict[str, Any], workflow: dict[str, Any]) -> dict[str, Any]:
    """Check that required artifacts exist for current and completed stages."""
    stages = state.get("stages", {})
    step_ids = [s["id"] for s in workflow.get("steps", [])]
    current_stage = state.get("current_run", {}).get("current_stage")

    # Check completed stages and current stage
    check_stages = [sid for sid in step_ids if stages.get(sid, {}).get("status") in ("completed", "in_progress")]
    if current_stage and current_stage not in check_stages:
        check_stages.append(current_stage)

    missing = []
    for sid in check_stages:
        stage_def = find_stage(workflow, sid)
        artifacts = stage_def.get("artifacts", [])
        stage_state = stages.get(sid, {})
        produced = stage_state.get("artifacts_produced", [])
        for art in artifacts:
            # Check if artifact exists on disk or is listed in artifacts_produced
            art_path = PROJECT_ROOT / art
            if not art_path.exists() and art not in produced:
                missing.append(f"{sid}: {art}")

    if missing:
        return {"check": "artifact_completeness", "status": "WARN", "message": f"Missing artifacts: {', '.join(missing)}"}
    return {"check": "artifact_completeness", "status": "PASS", "message": "All required artifacts present or recorded."}


def audit_human_gate_compliance(state: dict[str, Any], workflow: dict[str, Any]) -> dict[str, Any]:
    """Completed stages with human_gate=true must have human_gate_passed=true."""
    stages = state.get("stages", {})
    violations = []
    for sid, stage_state in stages.items():
        if stage_state.get("status") != "completed":
            continue
        try:
            stage_def = find_stage(workflow, sid)
        except ValueError:
            continue
        if stage_def.get("human_gate", False) and not stage_state.get("human_gate_passed"):
            violations.append(sid)

    if violations:
        return {"check": "human_gate_compliance", "status": "FAIL", "message": f"Stages missing human gate approval: {', '.join(violations)}"}
    return {"check": "human_gate_compliance", "status": "PASS", "message": "All human-gated stages have approval."}


def audit_entry_exit_compliance(state: dict[str, Any]) -> dict[str, Any]:
    """Completed stages should have entry and exit checks passed."""
    stages = state.get("stages", {})
    violations = []
    for sid, stage_state in stages.items():
        if stage_state.get("status") != "completed":
            continue
        if not stage_state.get("entry_checks_passed"):
            violations.append(f"{sid}: entry checks not passed")
        if not stage_state.get("exit_checks_passed"):
            violations.append(f"{sid}: exit checks not passed")

    if violations:
        return {"check": "entry_exit_compliance", "status": "WARN", "message": f"Check issues: {', '.join(violations)}"}
    return {"check": "entry_exit_compliance", "status": "PASS", "message": "All completed stages have entry/exit checks passed."}


def audit_skill_coverage(state: dict[str, Any]) -> dict[str, Any]:
    """Current stage should have at least one skill invoked (from metrics/skills_invoked)."""
    current_stage = state.get("current_run", {}).get("current_stage")
    if not current_stage:
        return {"check": "skill_coverage", "status": "PASS", "message": "No current stage; skipping skill coverage check."}

    stage_state = state.get("stages", {}).get(current_stage, {})
    skills_invoked = stage_state.get("skills_invoked", [])
    if not skills_invoked:
        return {"check": "skill_coverage", "status": "WARN", "message": f"No skills recorded for current stage '{current_stage}'."}
    return {"check": "skill_coverage", "status": "PASS", "message": f"{len(skills_invoked)} skill(s) recorded for current stage."}


def audit_anomaly_detection(state: dict[str, Any]) -> dict[str, Any]:
    """Detect anomalies: retry_count > 1 or validation_failed stages."""
    stages = state.get("stages", {})
    anomalies = []
    for sid, stage_state in stages.items():
        retry = stage_state.get("retry_count", 0)
        if retry > 1:
            anomalies.append(f"{sid}: retry_count={retry}")
        if stage_state.get("status") == "validation_failed":
            anomalies.append(f"{sid}: status=validation_failed")

    if anomalies:
        return {"check": "anomaly_detection", "status": "WARN", "message": f"Anomalies detected: {', '.join(anomalies)}"}
    return {"check": "anomaly_detection", "status": "PASS", "message": "No anomalies detected."}


def audit_handoff_file(state: dict[str, Any]) -> dict[str, Any]:
    """Check .context/lincoln-handoff.md exists if current stage is waiting_for_human."""
    current_stage = state.get("current_run", {}).get("current_stage")
    if not current_stage:
        return {"check": "handoff_file", "status": "PASS", "message": "No current stage; skipping handoff check."}

    stage_state = state.get("stages", {}).get(current_stage, {})
    if stage_state.get("status") != "waiting_for_human":
        return {"check": "handoff_file", "status": "PASS", "message": "Current stage not waiting for human; handoff file optional."}

    if HANDOFF_PATH.exists():
        return {"check": "handoff_file", "status": "PASS", "message": "Handoff file exists."}
    return {"check": "handoff_file", "status": "WARN", "message": f"Stage waiting for human but handoff file missing: {HANDOFF_PATH}"}


def run_all_audits(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Run all audit rules and return results."""
    template_name = state.get("current_run", {}).get("workflow_template")
    workflow = load_workflow(template_name)

    results = [
        audit_state_consistency(state, workflow),
        audit_artifact_completeness(state, workflow),
        audit_human_gate_compliance(state, workflow),
        audit_entry_exit_compliance(state),
        audit_skill_coverage(state),
        audit_anomaly_detection(state),
        audit_handoff_file(state),
    ]
    return results


def compute_overall_status(results: list[dict[str, Any]]) -> str:
    statuses = [r["status"] for r in results]
    if "FAIL" in statuses:
        return "FAIL"
    if "WARN" in statuses:
        return "WARN"
    return "PASS"


def format_json(results: list[dict[str, Any]], overall: str) -> str:
    return json.dumps({"overall_status": overall, "checks": results}, ensure_ascii=False, indent=2)


def format_markdown(results: list[dict[str, Any]], overall: str) -> str:
    lines = []
    lines.append("# Lincoln Workflow Audit Report")
    lines.append("")
    status_emoji = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}
    lines.append(f"**Overall Status:** {status_emoji.get(overall, '')} {overall}")
    lines.append("")
    lines.append("| Check | Status | Message |")
    lines.append("|-------|--------|---------|")
    for r in results:
        emoji = status_emoji.get(r["status"], "")
        lines.append(f"| {r['check']} | {emoji} {r['status']} | {r['message']} |")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Lincoln workflow health auditor")
    parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        default=STATE_PATH,
        help="Path to workflow-state.yaml",
    )
    args = parser.parse_args()

    state = load_state(args.state_file)
    results = run_all_audits(state)
    overall = compute_overall_status(results)

    if args.format == "json":
        print(format_json(results, overall))
    else:
        print(format_markdown(results, overall))

    return 0 if overall != "FAIL" else 1


if __name__ == "__main__":
    sys.exit(main())
