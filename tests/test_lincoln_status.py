"""Tests for scripts/lincoln-status.py."""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
STATUS_SCRIPT = ROOT / "scripts" / "lincoln-status.py"


def _load_status_module():
    """Load lincoln-status.py as a module (filename has hyphen)."""
    spec = importlib.util.spec_from_file_location("lincoln_status", STATUS_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_status(*args):
    return subprocess.run(
        [sys.executable, str(STATUS_SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


@pytest.fixture
def status_mod():
    return _load_status_module()


@pytest.fixture
def minimal_state():
    """Return a minimal valid state dict."""
    return {
        "schema_version": "1.0.0",
        "workflow": {"name": "interview-to-knowledge", "steps": []},
        "current_run": {
            "run_id": "test-run",
            "branch": "lincoln/test-branch",
            "current_stage": "ingest",
            "previous_stage": None,
            "status": "in_progress",
            "workflow_template": None,
            "started_at": "2026-06-27T00:00:00Z",
            "last_updated_at": "2026-06-27T00:00:00Z",
        },
        "stages": {
            "ingest": {
                "status": "in_progress",
                "started_at": "2026-06-27T00:00:00Z",
                "completed_at": None,
                "entry_checks_passed": True,
                "entry_checks_run_at": "2026-06-27T00:00:00Z",
                "exit_checks_passed": None,
                "exit_checks_run_at": None,
                "human_gate_passed": None,
                "human_gate_passed_at": None,
                "artifacts_produced": [],
                "error_message": None,
                "retry_count": 0,
            },
            "clarify": {
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
            },
        },
        "variables": {
            "session_id": "2026-06-27-test",
            "design_id": None,
            "change_name": None,
            "issue_number": None,
            "pr_number": None,
            "feature_slug": None,
        },
        "recovery": {
            "last_validated_checkpoint": None,
            "can_resume_from": None,
            "abort_reason": None,
            "abort_at": None,
        },
    }


# ---------------------------------------------------------------------------
# get_waiting_for tests
# ---------------------------------------------------------------------------


def test_get_waiting_for_waiting_for_human(status_mod):
    assert status_mod.get_waiting_for("waiting_for_human", {"human_gate": True}) == "pm"


def test_get_waiting_for_validation_failed(status_mod):
    assert status_mod.get_waiting_for("validation_failed", {"human_gate": True}) == "agent-fix"


def test_get_waiting_for_in_progress(status_mod):
    assert status_mod.get_waiting_for("in_progress", {"human_gate": True}) == "agent"


def test_get_waiting_for_completed(status_mod):
    assert status_mod.get_waiting_for("completed", {"human_gate": True}) == "next-role"


def test_get_waiting_for_entry_validating(status_mod):
    assert status_mod.get_waiting_for("entry_validating", {"human_gate": False}) == "agent"


def test_get_waiting_for_not_started_with_human_gate(status_mod):
    assert status_mod.get_waiting_for("not_started", {"human_gate": True}) == "pm"


def test_get_waiting_for_not_started_without_human_gate(status_mod):
    assert status_mod.get_waiting_for("not_started", {"human_gate": False}) == "agent"


def test_get_waiting_for_none(status_mod):
    assert status_mod.get_waiting_for(None, {}) == "none"


# ---------------------------------------------------------------------------
# build_status_report tests
# ---------------------------------------------------------------------------


def test_build_status_report_keys(status_mod, minimal_state):
    report = status_mod.build_status_report(minimal_state)
    expected_keys = {
        "branch",
        "run_id",
        "workflow_template",
        "current_stage",
        "previous_stage",
        "run_status",
        "stage_status",
        "entry_checks_passed",
        "exit_checks_passed",
        "human_gate_passed",
        "retry_count",
        "waiting_for",
        "loaded_context",
        "required_skills",
        "optional_skills",
        "required_artifacts",
        "next_action",
        "metrics",
    }
    assert set(report.keys()) == expected_keys


def test_build_status_report_branch(status_mod, minimal_state):
    report = status_mod.build_status_report(minimal_state)
    assert report["branch"] == "lincoln/test-branch"


def test_build_status_report_current_stage(status_mod, minimal_state):
    report = status_mod.build_status_report(minimal_state)
    assert report["current_stage"] == "ingest"


def test_build_status_report_waiting_for(status_mod, minimal_state):
    report = status_mod.build_status_report(minimal_state)
    assert report["waiting_for"] == "agent"


def test_build_status_report_metrics(status_mod, minimal_state):
    report = status_mod.build_status_report(minimal_state)
    metrics = report["metrics"]
    assert "total_stages" in metrics
    assert "completed" in metrics
    assert "failed" in metrics
    assert "waiting_for_human" in metrics


def test_build_status_report_no_current_stage(status_mod):
    state = {
        "schema_version": "1.0.0",
        "workflow": {"name": "test", "steps": []},
        "current_run": {
            "run_id": "test-run",
            "branch": "lincoln/test-branch",
            "current_stage": None,
            "previous_stage": "sync-knowledge",
            "status": "completed",
            "workflow_template": None,
            "started_at": "2026-06-27T00:00:00Z",
            "last_updated_at": "2026-06-27T00:00:00Z",
        },
        "stages": {},
        "variables": {},
        "recovery": {},
    }
    report = status_mod.build_status_report(state)
    assert report["current_stage"] is None
    assert report["next_action"] == "Workflow complete. No further action required."


# ---------------------------------------------------------------------------
# get_required_skills tests
# ---------------------------------------------------------------------------


def test_get_required_skills_existing_stage(status_mod):
    skills = status_mod.get_required_skills("clarify")
    assert "superpowers:brainstorming" in skills["required"]


def test_get_required_skills_missing_routing(status_mod):
    skills = status_mod.get_required_skills("nonexistent-stage")
    assert skills["required"] == []
    assert skills["optional"] == []


# ---------------------------------------------------------------------------
# Format tests
# ---------------------------------------------------------------------------


def test_format_json_produces_valid_json(status_mod, minimal_state):
    report = status_mod.build_status_report(minimal_state)
    output = status_mod.format_json(report)
    parsed = json.loads(output)
    assert parsed["branch"] == "lincoln/test-branch"


def test_format_table_contains_headers(status_mod, minimal_state):
    report = status_mod.build_status_report(minimal_state)
    output = status_mod.format_table(report)
    assert "LINCOLN BRANCH STATUS" in output
    assert "Branch:" in output
    assert "METRICS" in output


def test_format_markdown_contains_headers(status_mod, minimal_state):
    report = status_mod.build_status_report(minimal_state)
    output = status_mod.format_markdown(report)
    assert "# Lincoln Branch Status" in output
    assert "## Loaded Context" in output
    assert "## Next Action" in output


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------


def test_cli_format_json():
    result = run_status("--format", "json")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "branch" in data


def test_cli_format_table():
    result = run_status("--format", "table")
    assert result.returncode == 0
    assert "LINCOLN BRANCH STATUS" in result.stdout


def test_cli_format_markdown():
    result = run_status("--format", "markdown")
    assert result.returncode == 0
    assert "# Lincoln Branch Status" in result.stdout


# ---------------------------------------------------------------------------
# Missing skill-routing.yaml handling
# ---------------------------------------------------------------------------


def test_get_required_skills_missing_file(status_mod, tmp_path, monkeypatch):
    """Test that missing skill-routing.yaml doesn't crash."""
    fake_routing = tmp_path / "skill-routing.yaml"
    monkeypatch.setattr(status_mod, "SKILL_ROUTING_PATH", fake_routing)
    skills = status_mod.get_required_skills("clarify")
    assert skills == {"required": [], "optional": []}
