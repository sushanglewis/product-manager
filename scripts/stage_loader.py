#!/usr/bin/env python3
"""
Lincoln stage loader / dispatcher.

Loads stage-specific context, runs entry/exit validators, and manages the
branch-scoped workflow state file at `.claude/workflow-state.yaml`.

Usage:
    python scripts/stage-loader.py --stage clarify --action load
    python scripts/stage-loader.py --stage product-design-docs --action validate-entry
    python scripts/stage-loader.py --stage product-design-docs --action validate-exit
    python scripts/stage-loader.py --stage clarify --action transition-next
    python scripts/stage-loader.py --action recover
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
STATE_PATH = PROJECT_ROOT / ".claude" / "workflow-state.yaml"
STAGES_DIR = PROJECT_ROOT / ".claude" / "stages"
VALIDATOR_PATH = (
    PROJECT_ROOT
    / ".claude"
    / "skills"
    / "interview-workflow"
    / "validators"
    / "validate.py"
)

SKILL_ROUTING_PATH = PROJECT_ROOT / ".claude" / "skill-routing.yaml"
CONTEXT_DIR = PROJECT_ROOT / ".context"

REQUIRED_STATE_KEYS = {
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
    template_path = WORKFLOW_TEMPLATE_DIR / f"{template_name}.yaml"
    if not template_path.exists():
        raise FileNotFoundError(f"Workflow template not found: {template_path}")
    return template_path


def load_workflow(template_name: str | None = None) -> dict[str, Any]:
    path = resolve_workflow_path(template_name)
    data = load_yaml(path)
    return data.get("workflow", data)


def list_workflow_templates() -> list[str]:
    if not WORKFLOW_TEMPLATE_DIR.exists():
        return []
    return sorted(p.stem for p in WORKFLOW_TEMPLATE_DIR.glob("*.yaml"))


def load_state(path: Path | None = None) -> dict[str, Any]:
    path = path or STATE_PATH
    state = load_yaml(path)
    if not isinstance(state, dict):
        raise ValueError(f"State file {path} must contain a YAML mapping")
    missing = REQUIRED_STATE_KEYS - set(state.keys())
    if missing:
        raise ValueError(f"State file missing keys: {', '.join(missing)}")
    return state


def save_state(state: dict[str, Any], path: Path | None = None) -> None:
    path = path or STATE_PATH
    state["current_run"]["last_updated_at"] = now_iso()
    save_yaml(path, state)


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
    """Replace `{var}` placeholders with variable values."""

    def replacer(match: re.Match) -> str:
        key = match.group(1)
        if key in variables and variables[key] is not None:
            return str(variables[key])
        return match.group(0)

    return re.sub(r"\{(\w+)\}", replacer, value)


def run_validator(
    phase: str,
    check_name: str,
    args: list[str],
    project_root: Path | None = None,
) -> tuple[int, str, str]:
    """Run a validator check via validate.py subprocess."""
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
        # validate.py computes PROJECT_ROOT from its own location; to support
        # testing against a temporary project, we would need to refactor it to
        # accept an env var. For now we run against the real project root.
        pass

    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result.returncode, result.stdout, result.stderr


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------


def action_load(stage_id: str, state: dict[str, Any]) -> dict[str, Any]:
    template_name = state.get("current_run", {}).get("workflow_template")
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

    variables = state.get("variables", {})
    context = "\n\n---\n\n".join(context_parts)
    context = interpolate(context, variables)

    # Load skills from skill-routing.yaml if available
    skills = {"required": [], "optional": []}
    if SKILL_ROUTING_PATH.exists():
        try:
            routing_data = yaml.safe_load(SKILL_ROUTING_PATH.read_text(encoding="utf-8"))
            if isinstance(routing_data, dict):
                routing = routing_data.get("routing", {})
                stage_routing = routing.get(stage_id, {})
                skills = {
                    "required": stage_routing.get("required", []),
                    "optional": stage_routing.get("optional", []),
                }
        except Exception:
            pass

    return {
        "stage_id": stage_id,
        "stage_name": stage_def.get("name", stage_id),
        "stage_status": state.get("stages", {}).get(stage_id, {}).get("status"),
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
    template_name = state.get("current_run", {}).get("workflow_template")
    workflow = load_workflow(template_name)
    stage_def = find_stage(workflow, stage_id)
    checks = stage_def.get(f"{phase}_checks", [])
    variables = state.get("variables", {})

    stage_state = state.setdefault("stages", {}).setdefault(stage_id, {})
    stage_state["started_at"] = stage_state.get("started_at") or now_iso()
    if phase == "entry":
        stage_state["status"] = "entry_validating"
    save_state(state, state_file)

    # Initialize validator_history if not present
    if "validator_history" not in stage_state:
        stage_state["validator_history"] = []

    for check in checks:
        check_name = check["check"]
        raw_args = check.get("args", [])
        args = [interpolate(str(a), variables) for a in raw_args]
        exit_code, stdout, stderr = run_validator(phase, check_name, args)

        # Record validator history
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
            stage_state["status"] = "validation_failed"
            stage_state["error_message"] = (
                f"{phase} check '{check_name}' failed.\nstdout: {stdout}\nstderr: {stderr}"
            )
            stage_state["retry_count"] = stage_state.get("retry_count", 0) + 1
            save_state(state, state_file)
            print(f"FAIL: {phase} check '{check_name}'", file=sys.stderr)
            print(stdout, file=sys.stderr)
            print(stderr, file=sys.stderr)
            return 1

    now = now_iso()
    if phase == "entry":
        stage_state["status"] = "in_progress"
        stage_state["entry_checks_passed"] = True
        stage_state["entry_checks_run_at"] = now
    else:
        stage_state["exit_checks_passed"] = True
        stage_state["exit_checks_run_at"] = now
    stage_state["error_message"] = None
    save_state(state, state_file)
    print(f"PASS: all {phase} checks for '{stage_id}'")
    return 0


def action_transition_next(stage_id: str, state: dict[str, Any], state_file: Path | None = None) -> str | None:
    template_name = state.get("current_run", {}).get("workflow_template")
    workflow = load_workflow(template_name)
    next_stage_id = compute_next_stage(workflow, stage_id)

    stage_state = state.setdefault("stages", {}).setdefault(stage_id, {})
    stage_state["status"] = "completed"
    stage_state["completed_at"] = now_iso()

    # Compute duration_seconds from started_at to completed_at
    started_at = stage_state.get("started_at")
    completed_at = stage_state.get("completed_at")
    if started_at and completed_at:
        try:
            from datetime import datetime
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

    save_state(state, state_file)
    print(f"Transitioned from '{stage_id}' to '{next_stage_id}'")
    return next_stage_id


def action_recover(state: dict[str, Any], state_file: Path | None = None) -> dict[str, Any]:
    stages = state.get("stages", {})
    template_name = state.get("current_run", {}).get("workflow_template")
    workflow = load_workflow(template_name)
    step_ids = [s["id"] for s in workflow.get("steps", [])]

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

def action_status(state: dict[str, Any]) -> dict[str, Any]:
    """Return status report by delegating to lincoln-status logic."""
    # Import here to avoid circular import at module level
    # When called as __main__, sys.path already includes project root
    import importlib.util
    status_path = PROJECT_ROOT / "scripts" / "lincoln-status.py"
    spec = importlib.util.spec_from_file_location("lincoln_status", status_path)
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.build_status_report(state)
    # Fallback: try direct import
    try:
        from lincoln_status import build_status_report
        return build_status_report(state)
    except ImportError:
        raise RuntimeError("Could not import lincoln-status module")


def action_handoff_report(stage_id: str, state: dict[str, Any]) -> str:
    """Generate .context/lincoln-handoff.md with current stage summary."""
    template_name = state.get("current_run", {}).get("workflow_template")
    workflow = load_workflow(template_name)
    stage_def = find_stage(workflow, stage_id)
    stage_state = state.get("stages", {}).get(stage_id, {})

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
    lines.append(f"- **Status:** {stage_state.get('status', 'unknown')}")
    lines.append("")
    lines.append("## Waiting For")
    lines.append(f"- **Waiting for:** {'human' if stage_def.get('human_gate') and not stage_state.get('human_gate_passed') else 'agent'}")
    lines.append("")
    lines.append("## Artifacts")
    produced = stage_state.get("artifacts_produced", [])
    required = stage_def.get("artifacts", [])
    if produced:
        lines.append("### Produced")
        for art in produced:
            lines.append(f"- [x] {art}")
    if required:
        lines.append("### Required")
        for art in required:
            checked = "x" if art in produced else " "
            lines.append(f"- [{checked}] {art}")
    lines.append("")
    lines.append("## Next Action")
    lines.append(f"{stage_state.get('status', 'unknown')}")
    lines.append("")
    lines.append("---")
    lines.append("*This file is auto-generated by `scripts/stage_loader.py --action handoff-report`*")

    content = "\n".join(lines)
    CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
    handoff_path = CONTEXT_DIR / "lincoln-handoff.md"
    handoff_path.write_text(content, encoding="utf-8")
    return str(handoff_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Lincoln stage loader")
    parser.add_argument("--stage", help="Stage ID")
    parser.add_argument(
        "--action",
        required=True,
        choices=["load", "validate-entry", "validate-exit", "transition-next", "recover", "status", "handoff-report"],
    )
    parser.add_argument("--state-file", type=Path, default=STATE_PATH)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
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
        phase = args.action.split("-")[1]
        return action_validate(args.stage, state, phase, args.state_file)

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
        # Print as table by default
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
