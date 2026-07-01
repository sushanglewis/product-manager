#!/usr/bin/env python3
"""
Lincoln stage loader / dispatcher.

Loads stage-specific context, runs entry/exit validators, and manages the
branch-scoped workflow state file at `.claude/workflow-stage.yaml`.

Usage:
    python scripts/stage-loader.py --stage clarify --action load
    python scripts/stage-loader.py --stage product-design-docs --action validate-entry
    python scripts/stage-loader.py --stage product-design-docs --action validate-exit
    python scripts/stage-loader.py --stage clarify --action transition-next
    python scripts/stage-loader.py --action recover
    python scripts/stage-loader.py --stage clarify --action approve-gate
    python scripts/stage-loader.py --action append-node --node-id clarify --status in_progress
    python scripts/stage-loader.py --stage clarify --action append-node --node-id clarify --status in_progress
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = PROJECT_ROOT / ".claude" / "workflows" / "interview-to-knowledge.yaml"
WORKFLOW_TEMPLATE_DIR = PROJECT_ROOT / ".claude" / "workflows" / "templates"
DEFAULT_WORKFLOW_PATH = WORKFLOW_PATH

# New default state file with legacy fallback
STATE_PATH = PROJECT_ROOT / ".claude" / "workflow-stage.yaml"
LEGACY_STATE_PATH = PROJECT_ROOT / ".claude" / "workflow-state.yaml"

STAGES_DIR = PROJECT_ROOT / ".claude" / "stages"
VALIDATOR_PATH = PROJECT_ROOT / "scripts" / "validate_stage.py"

# New skill routing path with legacy fallback
SKILL_ROUTING_PATH = PROJECT_ROOT / ".claude" / "skills" / "routing.yaml"
LEGACY_SKILL_ROUTING_PATH = PROJECT_ROOT / ".claude" / "skill-routing.yaml"

CONTEXT_DIR = PROJECT_ROOT / ".context"

REQUIRED_STATE_KEYS = {
    "schema_version",
    "workflow",
    "current_run",
    "nodes",
    "recovery",
}

LEGACY_REQUIRED_STATE_KEYS = {
    "schema_version",
    "workflow",
    "current_run",
    "stages",
    "variables",
    "recovery",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_yaml(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(path)
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def save_yaml(path: Path, data: Any) -> None:
    """Write YAML atomically to avoid corrupting the state file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".yaml.tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False, width=120)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def resolve_workflow_path(template_name: str | None = None) -> Path:
    if not template_name:
        return DEFAULT_WORKFLOW_PATH
    # First check templates directory, then fall back to main workflows directory
    template_path = WORKFLOW_TEMPLATE_DIR / f"{template_name}.yaml"
    if template_path.exists():
        return template_path
    main_path = PROJECT_ROOT / ".claude" / "workflows" / f"{template_name}.yaml"
    if main_path.exists():
        return main_path
    raise FileNotFoundError(f"Workflow template not found: {template_path} or {main_path}")


def load_workflow(template_name: str | None = None) -> dict[str, Any]:
    path = resolve_workflow_path(template_name)
    data = load_yaml(path)
    return data.get("workflow", data)


def list_workflow_templates() -> list[str]:
    if not WORKFLOW_TEMPLATE_DIR.exists():
        return []
    return sorted(p.stem for p in WORKFLOW_TEMPLATE_DIR.glob("*.yaml"))


def _is_legacy_state(state: dict[str, Any]) -> bool:
    """Detect whether a state file uses the legacy schema (has 'stages' key)."""
    return "stages" in state and "nodes" not in state


def load_state(path: Path | None = None) -> dict[str, Any]:
    path = path or STATE_PATH
    if not path.exists():
        if path == STATE_PATH and LEGACY_STATE_PATH.exists():
            path = LEGACY_STATE_PATH
        else:
            raise FileNotFoundError(path)
    state = load_yaml(path)
    if not isinstance(state, dict):
        raise ValueError(f"State file {path} must contain a YAML mapping")

    if _is_legacy_state(state):
        missing = LEGACY_REQUIRED_STATE_KEYS - set(state.keys())
        if missing:
            raise ValueError(f"Legacy state file missing keys: {', '.join(missing)}")
    else:
        missing = REQUIRED_STATE_KEYS - set(state.keys())
        if missing:
            raise ValueError(f"State file missing keys: {', '.join(missing)}")
    return state


def save_state(state: dict[str, Any], path: Path | None = None) -> None:
    path = path or STATE_PATH
    state["current_run"]["last_updated_at"] = now_iso()
    save_yaml(path, state)


def resolve_state_path(path: Path | None = None) -> Path:
    """Return the actual state file path to use, preferring new over legacy."""
    path = path or STATE_PATH
    if path.exists():
        return path
    if path == STATE_PATH and LEGACY_STATE_PATH.exists():
        return LEGACY_STATE_PATH
    return path


def find_stage(workflow: dict[str, Any], stage_id: str) -> dict[str, Any]:
    for step in workflow.get("steps", []):
        if step.get("id") == stage_id:
            return step
    raise ValueError(f"Stage '{stage_id}' not found in workflow")


def compute_next_stage(workflow: dict[str, Any], stage_id: str) -> str | None:
    steps = workflow.get("steps", [])
    ids = [s["id"] for s in steps]
    try:
        idx = ids.index(stage_id)
    except ValueError:
        raise ValueError(f"Stage '{stage_id}' not found in workflow")
    if idx + 1 < len(ids):
        return ids[idx + 1]
    return None


def interpolate(value: str, variables: dict[str, Any]) -> str:
    """Replace {var} placeholders with variable values."""

    def replacer(match: re.Match) -> str:
        key = match.group(1)
        if key in variables and variables[key] is not None:
            return str(variables[key])
        return match.group(0)

    return re.sub(r"\{(\w+)\}", replacer, value)


def get_variables(state: dict[str, Any]) -> dict[str, Any]:
    """Extract variables from state, handling both new and legacy schemas."""
    if _is_legacy_state(state):
        return state.get("variables", {})
    return state.get("current_run", {}).get("variables", {})


def get_stage_state(state: dict[str, Any], stage_id: str) -> dict[str, Any]:
    """Get stage state from legacy schema."""
    return state.get("stages", {}).get(stage_id, {})


def get_nodes(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Get nodes array from new schema."""
    return state.get("nodes", [])


def get_latest_node_for_stage(state: dict[str, Any], stage_id: str) -> dict[str, Any] | None:
    """Return the latest node for a given stage, or None."""
    nodes = get_nodes(state)
    matching = [n for n in nodes if n.get("stage_id") == stage_id]
    if not matching:
        return None
    return matching[-1]


def run_validator(
    phase: str,
    check_name: str,
    args: list[str],
    project_root: Path | None = None,
) -> tuple[int, str, str]:
    """Run a validator check via validate_stage.py subprocess."""
    if not VALIDATOR_PATH.exists():
        raise FileNotFoundError(f"Validator not found: {VALIDATOR_PATH}")

    args_str = ",".join(args)
    cmd = [
        sys.executable,
        str(VALIDATOR_PATH),
        "--phase",
        phase,
        "--check",
        check_name,
    ]
    if args_str:
        cmd.extend(["--args", args_str])

    env = os.environ.copy()
    if project_root:
        # validate_stage.py computes PROJECT_ROOT from its own location;
        # to support testing against a temporary project we'd need to refactor it.
        pass

    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result.returncode, result.stdout, result.stderr


def load_skill_routing() -> dict[str, Any] | None:
    """Load skill routing from new or legacy path."""
    path = SKILL_ROUTING_PATH
    if not path.exists():
        path = LEGACY_SKILL_ROUTING_PATH
    if not path.exists():
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return None


def get_stage_skills(routing_data: dict[str, Any] | None, stage_id: str) -> dict[str, list[str]]:
    """Extract required/optional skills for a stage from routing data."""
    skills = {"required": [], "optional": []}
    if routing_data is None:
        return skills
    routing = routing_data.get("routing", {})
    stage_routing = routing.get(stage_id, {})
    skills["required"] = stage_routing.get("required", [])
    skills["optional"] = stage_routing.get("optional", [])
    return skills


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------


def action_load(stage_id: str, state: dict[str, Any]) -> dict[str, Any]:
    template_name = state.get("workflow", {}).get("template")
    workflow = load_workflow(template_name)
    stage_def = find_stage(workflow, stage_id)
    stage_dir = STAGES_DIR / stage_id

    if not stage_dir.exists():
        raise FileNotFoundError(f"Stage directory not found: {stage_dir}")

    context_parts: list[str] = []
    context_paths: list[str] = []
    for filename in ["AGENTS.md", "CHECKLIST.md", "SKILLS.md", "PROMPT.md"]:
        path = stage_dir / filename
        if path.exists():
            context_parts.append(path.read_text(encoding="utf-8"))
            context_paths.append(str(path.relative_to(PROJECT_ROOT)))

    variables = get_variables(state)
    context = "\n\n---\n\n".join(context_parts)
    context = interpolate(context, variables)

    # Load skills from routing.yaml
    routing_data = load_skill_routing()
    skills = get_stage_skills(routing_data, stage_id)

    # Determine stage status from nodes (new) or legacy stages
    if _is_legacy_state(state):
        stage_status = state.get("stages", {}).get(stage_id, {}).get("status")
    else:
        latest_node = get_latest_node_for_stage(state, stage_id)
        stage_status = latest_node.get("status") if latest_node else state.get("current_run", {}).get("status")

    return {
        "stage_id": stage_id,
        "stage_name": stage_def.get("name", stage_id),
        "stage_status": stage_status,
        "human_gate": stage_def.get("human_gate", False),
        "next_stage": compute_next_stage(workflow, stage_id),
        "context": context,
        "context_paths": context_paths,
        "required_skills": skills["required"],
        "optional_skills": skills["optional"],
    }


def action_validate(
    stage_id: str,
    state: dict[str, Any],
    phase: str,
    state_file: Path | None = None,
) -> int:
    """Run entry/exit checks from the workflow template using validate_stage.py."""
    template_name = state.get("workflow", {}).get("template")
    workflow = load_workflow(template_name)
    stage_def = find_stage(workflow, stage_id)
    checks = stage_def.get(f"{phase}_checks", [])
    variables = get_variables(state)

    if _is_legacy_state(state):
        stage_state = state.setdefault("stages", {}).setdefault(stage_id, {})
        stage_state["started_at"] = stage_state.get("started_at") or now_iso()
        if phase == "entry":
            stage_state["status"] = "entry_validating"
        save_state(state, state_file)

        if "validator_history" not in stage_state:
            stage_state["validator_history"] = []
    else:
        # For new schema, update current_run status during validation
        if phase == "entry":
            state["current_run"]["status"] = "entry_validating"
        save_state(state, state_file)

    for check in checks:
        check_name = check["check"]
        raw_args = check.get("args", [])
        args = [interpolate(str(a), variables) for a in raw_args]
        exit_code, stdout, stderr = run_validator(phase, check_name, args)

        if _is_legacy_state(state):
            stage_state["validator_history"].append(
                {
                    "phase": phase,
                    "check": check_name,
                    "exit_code": exit_code,
                    "stdout": stdout,
                    "stderr": stderr,
                    "run_at": now_iso(),
                }
            )

        if exit_code != 0:
            if _is_legacy_state(state):
                stage_state["status"] = "validation_failed"
                stage_state["error_message"] = (
                    f"{phase} check '{check_name}' failed.\nstdout: {stdout}\nstderr: {stderr}"
                )
                stage_state["retry_count"] = stage_state.get("retry_count", 0) + 1
                save_state(state, state_file)
            else:
                state["current_run"]["status"] = "validation_failed"
                save_state(state, state_file)
            print(f"FAIL: {phase} check '{check_name}'", file=sys.stderr)
            print(stdout, file=sys.stderr)
            print(stderr, file=sys.stderr)
            return 1

    now = now_iso()
    if _is_legacy_state(state):
        if phase == "entry":
            stage_state["status"] = "in_progress"
            stage_state["entry_checks_passed"] = True
            stage_state["entry_checks_run_at"] = now
        else:
            stage_state["exit_checks_passed"] = True
            stage_state["exit_checks_run_at"] = now
        stage_state["error_message"] = None
    else:
        if phase == "entry":
            state["current_run"]["status"] = "in_progress"
        save_state(state, state_file)

    print(f"PASS: all {phase} checks for '{stage_id}'")
    return 0


def action_validate_exit(
    stage_id: str,
    state: dict[str, Any],
    state_file: Path | None = None,
) -> int:
    """Run exit checks from stage-manifest.yaml gates.exit."""
    manifest_path = STAGES_DIR / "stage-manifest.yaml"
    if not manifest_path.exists():
        print(f"FAIL: stage-manifest.yaml not found at {manifest_path}", file=sys.stderr)
        return 1

    manifest = load_yaml(manifest_path)
    stages = manifest.get("stages", [])
    stage_def = None
    for s in stages:
        if s.get("id") == stage_id:
            stage_def = s
            break

    if stage_def is None:
        print(f"FAIL: stage '{stage_id}' not found in stage-manifest.yaml", file=sys.stderr)
        return 1

    gates = stage_def.get("gates", {})
    exit_checks = gates.get("exit", [])
    if not exit_checks:
        print(f"PASS: no exit gates defined for '{stage_id}'")
        return 0

    variables = get_variables(state)
    all_passed = True

    for check in exit_checks:
        check_name = check.get("check")
        raw_args = check.get("args", [])
        args = [interpolate(str(a), variables) for a in raw_args]

        passed = _run_exit_gate_check(check_name, args, stage_id, state)
        if passed:
            print(f"PASS: exit check '{check_name}'")
        else:
            print(f"FAIL: exit check '{check_name}'", file=sys.stderr)
            all_passed = False

    return 0 if all_passed else 1


def _run_exit_gate_check(check_name: str, args: list[str], stage_id: str, state: dict[str, Any]) -> bool:
    """Execute a single exit gate check. Returns True if passed."""
    if check_name == "artifact_exists":
        for path_arg in args:
            target = PROJECT_ROOT / path_arg
            if not target.exists():
                return False
        return True

    if check_name == "human_approved":
        latest_node = get_latest_node_for_stage(state, stage_id)
        if latest_node is None:
            return False
        return bool(latest_node.get("gate_passed")) and bool(latest_node.get("approved_by"))

    if check_name == "gate_review_passed":
        # Same as human_approved for now
        latest_node = get_latest_node_for_stage(state, stage_id)
        if latest_node is None:
            return False
        return bool(latest_node.get("gate_passed")) and bool(latest_node.get("approved_by"))

    if check_name == "previous_gate_passed":
        if not args:
            return False
        prev_stage_id = args[0]
        prev_node = get_latest_node_for_stage(state, prev_stage_id)
        if prev_node is None:
            return False
        return bool(prev_node.get("gate_passed"))

    # Unknown check: try running through validator as fallback
    try:
        exit_code, _, _ = run_validator("exit", check_name, args)
        return exit_code == 0
    except Exception:
        return False


def action_approve_gate(
    stage_id: str,
    state: dict[str, Any],
    state_file: Path | None = None,
    approved_by: str = "human-pm",
) -> int:
    """Mark the current/latest node for the stage as gate_passed: true."""
    if _is_legacy_state(state):
        stage_state = state.setdefault("stages", {}).setdefault(stage_id, {})
        stage_state["human_gate_passed"] = True
        stage_state["human_gate_passed_at"] = now_iso()
        save_state(state, state_file)
        print(f"PASS: gate approved for stage '{stage_id}' (legacy mode)")
        return 0

    latest_node = get_latest_node_for_stage(state, stage_id)
    if latest_node is None:
        # Create a new node if none exists
        new_node = {
            "stage_id": stage_id,
            "node_id": f"{stage_id}-{now_iso()}",
            "status": "completed",
            "gate_passed": True,
            "approved_by": approved_by,
            "started_at": now_iso(),
            "completed_at": now_iso(),
            "artifacts": [],
            "handoff_file": None,
        }
        state.setdefault("nodes", []).append(new_node)
    else:
        latest_node["gate_passed"] = True
        latest_node["approved_by"] = approved_by
        latest_node["completed_at"] = now_iso()

    save_state(state, state_file)
    print(f"PASS: gate approved for stage '{stage_id}' by '{approved_by}'")
    return 0


def action_append_node(
    stage_id: str,
    state: dict[str, Any],
    node_id: str,
    status: str,
    state_file: Path | None = None,
    handoff_file: str | None = None,
    artifacts: list[str] | None = None,
) -> int:
    """Append a node record to the nodes array."""
    if _is_legacy_state(state):
        # Legacy: update the stage status in stages dict
        stage_state = state.setdefault("stages", {}).setdefault(stage_id, {})
        stage_state["status"] = status
        if status == "completed":
            stage_state["completed_at"] = now_iso()
        if "started_at" not in stage_state or stage_state["started_at"] is None:
            stage_state["started_at"] = now_iso()
        if artifacts:
            existing = set(stage_state.get("artifacts_produced", []))
            existing.update(artifacts)
            stage_state["artifacts_produced"] = list(existing)
        save_state(state, state_file)
        print(f"Legacy node appended: stage '{stage_id}' -> status '{status}'")
        return 0

    node = {
        "stage_id": stage_id,
        "node_id": node_id,
        "status": status,
        "started_at": now_iso(),
        "completed_at": None,
        "gate_passed": False,
        "approved_by": None,
        "artifacts": artifacts or [],
        "handoff_file": handoff_file,
    }
    state.setdefault("nodes", []).append(node)

    # Update current_run if this is the latest node
    state["current_run"]["current_stage"] = stage_id
    state["current_run"]["status"] = status

    save_state(state, state_file)
    print(f"Node appended: '{node_id}' for stage '{stage_id}' with status '{status}'")
    return 0


def action_transition_next(stage_id: str, state: dict[str, Any], state_file: Path | None = None) -> str | None:
    template_name = state.get("workflow", {}).get("template")
    workflow = load_workflow(template_name)
    next_stage_id = compute_next_stage(workflow, stage_id)

    if _is_legacy_state(state):
        stage_state = state.setdefault("stages", {}).setdefault(stage_id, {})
        stage_state["status"] = "completed"
        stage_state["completed_at"] = now_iso()

        # Compute duration_seconds from started_at to completed_at
        started_at = stage_state.get("started_at")
        completed_at = stage_state.get("completed_at")
        if started_at and completed_at:
            try:
                start_dt = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
                stage_state["duration_seconds"] = int((end_dt - start_dt).total_seconds())
            except (ValueError, TypeError):
                stage_state["duration_seconds"] = None
        else:
            stage_state["duration_seconds"] = None

        if next_stage_id:
            next_state = state.setdefault("stages", {}).setdefault(next_stage_id, {})
            next_state.update(
                {
                    "status": "not_started",
                    "started_at": None,
                    "completed_at": None,
                    "entry_checks_passed": None,
                    "entry_checks_run_at": None,
                    "exit_checks_passed": None,
                    "exit_checks_run_at": None,
                    "human_gate_passed": None,
                    "human_gate_passed_at": None,
                    "artifacts_produced": [],
                    "error_message": None,
                    "retry_count": 0,
                }
            )
            state["current_run"]["current_stage"] = next_stage_id
            state["current_run"]["previous_stage"] = stage_id
        else:
            state["current_run"]["current_stage"] = None
            state["current_run"]["previous_stage"] = stage_id
            state["current_run"]["status"] = "completed"
    else:
        # New schema: append a completed node for current stage and a new node for next
        now = now_iso()
        completed_node = {
            "stage_id": stage_id,
            "node_id": f"{stage_id}-completed",
            "status": "completed",
            "started_at": now,
            "completed_at": now,
            "gate_passed": True,
            "approved_by": "system",
            "artifacts": [],
            "handoff_file": None,
        }
        state.setdefault("nodes", []).append(completed_node)

        if next_stage_id:
            state["current_run"]["current_stage"] = next_stage_id
            state["current_run"]["previous_stage"] = stage_id
            state["current_run"]["status"] = "not_started"
        else:
            state["current_run"]["current_stage"] = None
            state["current_run"]["previous_stage"] = stage_id
            state["current_run"]["status"] = "completed"

    save_state(state, state_file)
    print(f"Transitioned from '{stage_id}' to '{next_stage_id}'")
    return next_stage_id


def action_recover(state: dict[str, Any], state_file: Path | None = None) -> dict[str, Any]:
    template_name = state.get("workflow", {}).get("template")
    workflow = load_workflow(template_name)
    step_ids = [s["id"] for s in workflow.get("steps", [])]

    if _is_legacy_state(state):
        stages = state.get("stages", {})
        last_completed = None
        for sid in step_ids:
            if stages.get(sid, {}).get("status") == "completed":
                last_completed = sid

        resume_point = state["current_run"].get("current_stage") or last_completed
        if resume_point and stages.get(resume_point, {}).get("status") == "completed":
            resume_point = compute_next_stage(workflow, resume_point)

        state["recovery"]["last_validated_checkpoint"] = last_completed
        state["recovery"]["can_resume_from"] = resume_point
        save_state(state, state_file)

        return {
            "last_completed": last_completed,
            "can_resume_from": resume_point,
            "current_stage": state["current_run"].get("current_stage"),
            "current_status": state["current_run"].get("status"),
        }
    else:
        # New schema: derive from nodes array
        nodes = get_nodes(state)
        last_completed = None
        for node in reversed(nodes):
            if node.get("status") == "completed" and node.get("stage_id") in step_ids:
                last_completed = node.get("stage_id")
                break

        current_stage = state["current_run"].get("current_stage")
        resume_point = current_stage or last_completed
        if resume_point:
            # Check if the resume point stage is completed in its latest node
            latest = get_latest_node_for_stage(state, resume_point)
            if latest and latest.get("status") == "completed":
                resume_point = compute_next_stage(workflow, resume_point)

        state["recovery"]["last_validated_checkpoint"] = last_completed
        state["recovery"]["can_resume_from"] = resume_point
        save_state(state, state_file)

        return {
            "last_completed": last_completed,
            "can_resume_from": resume_point,
            "current_stage": current_stage,
            "current_status": state["current_run"].get("status"),
        }


def action_status(state: dict[str, Any]) -> dict[str, Any]:
    """Return status report by delegating to lincoln-status logic."""
    import importlib.util
    status_path = PROJECT_ROOT / "scripts" / "lincoln-status.py"
    spec = importlib.util.spec_from_file_location("lincoln_status", status_path)
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.build_status_report(state)
    try:
        from lincoln_status import build_status_report
        return build_status_report(state)
    except ImportError:
        raise RuntimeError("Could not import lincoln-status module")


def action_handoff_report(stage_id: str, state: dict[str, Any]) -> str:
    """Generate .context/lincoln-handoff-{stage}.md with current stage summary."""
    template_name = state.get("workflow", {}).get("template")
    workflow = load_workflow(template_name)
    stage_def = find_stage(workflow, stage_id)

    if _is_legacy_state(state):
        stage_state = state.get("stages", {}).get(stage_id, {})
        artifacts_produced = stage_state.get("artifacts_produced", [])
    else:
        latest_node = get_latest_node_for_stage(state, stage_id)
        stage_state = latest_node or {}
        artifacts_produced = stage_state.get("artifacts", [])

    lines = []
    lines.append("# Lincoln Handoff Report")
    lines.append("")
    lines.append(f"**Generated:** {now_iso()}")
    lines.append(f"**Branch:** {state.get('current_run', {}).get('branch', 'unknown')}")
    lines.append(f"**Run ID:** {state.get('current_run', {}).get('run_id', 'unknown')}")
    lines.append("")
    lines.append("## Current Stage")
    lines.append(f"- **Stage:** {stage_id}")
    lines.append(f"- **Name:** {stage_def.get('name', stage_id)}")
    if _is_legacy_state(state):
        lines.append(f"- **Status:** {stage_state.get('status', 'unknown')}")
    else:
        lines.append(f"- **Status:** {stage_state.get('status', state.get('current_run', {}).get('status', 'unknown'))}")
    lines.append("")
    lines.append("## Waiting For")
    lines.append(f"- **Waiting for:** {'human' if stage_def.get('human_gate') and not stage_state.get('gate_passed') else 'agent'}")
    lines.append("")
    lines.append("## Artifacts")
    if artifacts_produced:
        lines.append("### Produced")
        for art in artifacts_produced:
            lines.append(f"- [x] {art}")
    required = stage_def.get("artifacts", [])
    if required:
        lines.append("### Required")
        for art in required:
            checked = "x" if art in artifacts_produced else " "
            lines.append(f"- [{checked}] {art}")
    lines.append("")
    lines.append("## Next Action")
    lines.append(f"{stage_state.get('status', 'unknown')}")
    lines.append("")
    lines.append("---")
    lines.append("*This file is auto-generated by `scripts/stage_loader.py --action handoff-report`*")

    content = "\n".join(lines)
    CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
    handoff_path = CONTEXT_DIR / f"lincoln-handoff-{stage_id}.md"
    handoff_path.write_text(content, encoding="utf-8")
    return str(handoff_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Lincoln stage loader")
    parser.add_argument("--stage", help="Stage ID")
    parser.add_argument(
        "--action",
        required=True,
        choices=[
            "load",
            "validate-entry",
            "validate-exit",
            "approve-gate",
            "append-node",
            "transition-next",
            "recover",
            "status",
            "handoff-report",
        ],
    )
    parser.add_argument("--state-file", type=Path, default=STATE_PATH)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--approved-by", default="human-pm", help="Approver name for approve-gate")
    parser.add_argument("--node-id", help="Node ID for append-node")
    parser.add_argument("--status", help="Node status for append-node")
    parser.add_argument("--handoff-file", help="Handoff file path for append-node")
    parser.add_argument("--artifacts", help="Comma-separated artifact paths for append-node")
    args = parser.parse_args()

    state = load_state(args.state_file)

    if args.action == "load":
        if not args.stage:
            parser.error("--stage is required for load")
        result = action_load(args.stage, state)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.action in ("validate-entry", "validate-exit"):
        if not args.stage:
            parser.error("--stage is required for validate-*")
        if args.action == "validate-exit":
            return action_validate_exit(args.stage, state, args.state_file)
        phase = args.action.split("-")[1]
        return action_validate(args.stage, state, phase, args.state_file)

    if args.action == "approve-gate":
        if not args.stage:
            parser.error("--stage is required for approve-gate")
        return action_approve_gate(args.stage, state, args.state_file, args.approved_by)

    if args.action == "append-node":
        if not args.node_id:
            parser.error("--node-id is required for append-node")
        if not args.status:
            parser.error("--status is required for append-node")
        stage_id = args.stage or args.node_id
        artifacts = [a.strip() for a in args.artifacts.split(",")] if args.artifacts else None
        return action_append_node(
            stage_id, state, args.node_id, args.status,
            args.state_file, args.handoff_file, artifacts,
        )

    if args.action == "transition-next":
        if not args.stage:
            parser.error("--stage is required for transition-next")
        action_transition_next(args.stage, state, args.state_file)
        return 0

    if args.action == "recover":
        result = action_recover(state, args.state_file)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.action == "status":
        result = action_status(state)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.action == "handoff-report":
        if not args.stage:
            parser.error("--stage is required for handoff-report")
        path = action_handoff_report(args.stage, state)
        print(f"Handoff report written to: {path}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
