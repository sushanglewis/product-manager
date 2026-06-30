import sys
from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.stage_loader import (
    load_state,
    save_state,
    action_transition_next,
    action_recover,
    compute_next_stage,
    load_workflow,
)

STATE_PATH = PROJECT_ROOT / ".claude" / "workflow-state.yaml"


@pytest.fixture
def fresh_state(tmp_path):
    """Return a copy of the project's workflow-state.yaml in a temp path."""
    state = yaml.safe_load(STATE_PATH.read_text(encoding="utf-8"))
    # Reset to a known starting point
    state["current_run"]["run_id"] = "test-001"
    state["current_run"]["branch"] = "lincoln/test-branch"
    state["current_run"]["current_stage"] = "ingest"
    state["current_run"]["previous_stage"] = None
    state["current_run"]["status"] = "in_progress"
    state["current_run"]["started_at"] = "2026-06-27T00:00:00Z"
    state["current_run"]["last_updated_at"] = "2026-06-27T00:00:00Z"
    for s in state["stages"]:
        state["stages"][s] = {
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
    state["variables"] = {
        "session_id": "2026-06-27-test",
        "design_id": None,
        "change_name": None,
        "issue_number": None,
        "pr_number": None,
        "feature_slug": None,
    }
    state["recovery"] = {
        "last_validated_checkpoint": None,
        "can_resume_from": None,
        "abort_reason": None,
        "abort_at": None,
    }
    out = tmp_path / "workflow-state.yaml"
    out.write_text(yaml.dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return out


def test_load_state_requires_schema_version(fresh_state):
    state = yaml.safe_load(fresh_state.read_text(encoding="utf-8"))
    del state["schema_version"]
    fresh_state.write_text(yaml.dump(state), encoding="utf-8")
    with pytest.raises(ValueError, match="missing keys"):
        load_state(fresh_state)


def test_compute_next_stage_follows_workflow_order():
    workflow = load_workflow()
    assert compute_next_stage(workflow, "ingest") == "clarify"
    assert compute_next_stage(workflow, "clarify") == "product-design-docs"
    assert compute_next_stage(workflow, "sync-knowledge") is None


def test_action_transition_next_updates_current_run(fresh_state):
    state = load_state(fresh_state)
    state["stages"]["ingest"]["status"] = "completed"
    next_stage = action_transition_next("ingest", state, fresh_state)
    assert next_stage == "clarify"
    updated = load_state(fresh_state)
    assert updated["current_run"]["current_stage"] == "clarify"
    assert updated["current_run"]["previous_stage"] == "ingest"
    assert updated["stages"]["clarify"]["status"] == "not_started"


def test_action_recover_finds_last_completed(fresh_state):
    state = load_state(fresh_state)
    state["stages"]["ingest"]["status"] = "completed"
    state["stages"]["clarify"]["status"] = "validation_failed"
    state["stages"]["clarify"]["retry_count"] = 1
    save_state(state, fresh_state)

    state = load_state(fresh_state)
    result = action_recover(state)
    assert result["last_completed"] == "ingest"
    assert result["can_resume_from"] == "clarify"


def test_state_file_in_project_has_all_stages():
    state = load_state(STATE_PATH)
    workflow = load_workflow()
    expected = {s["id"] for s in workflow["steps"]}
    actual = set(state["stages"].keys())
    assert actual == expected


def test_action_validate_records_validator_history(fresh_state):
    from scripts.stage_loader import action_validate
    state = load_state(fresh_state)
    # Set up a stage with entry checks that will fail (so we get history)
    # First, set ingest to completed so we can validate clarify entry
    state["stages"]["ingest"]["status"] = "completed"
    state["stages"]["ingest"]["entry_checks_passed"] = True
    state["stages"]["ingest"]["exit_checks_passed"] = True
    save_state(state, fresh_state)

    # Now run validate-entry for clarify - it will fail because summary.md doesn't exist
    action_validate("clarify", state, "entry", fresh_state)

    updated = load_state(fresh_state)
    clarify_state = updated["stages"]["clarify"]
    assert "validator_history" in clarify_state
    assert len(clarify_state["validator_history"]) > 0
    # Check the first history entry has the expected keys
    entry = clarify_state["validator_history"][0]
    assert "phase" in entry
    assert "check" in entry
    assert "exit_code" in entry
    assert "run_at" in entry


def test_action_validate_exit_records_validator_history(fresh_state):
    from scripts.stage_loader import action_validate
    state = load_state(fresh_state)
    # Set up a stage that is in_progress
    state["stages"]["ingest"]["status"] = "in_progress"
    state["stages"]["ingest"]["entry_checks_passed"] = True
    state["stages"]["ingest"]["started_at"] = "2026-06-27T00:00:00Z"
    save_state(state, fresh_state)

    # Run validate-exit for ingest - it will fail because summary.md doesn't exist
    action_validate("ingest", state, "exit", fresh_state)

    updated = load_state(fresh_state)
    ingest_state = updated["stages"]["ingest"]
    assert "validator_history" in ingest_state
    assert len(ingest_state["validator_history"]) > 0


def test_action_transition_next_records_duration_seconds(fresh_state):
    from scripts.stage_loader import action_transition_next
    state = load_state(fresh_state)
    state["stages"]["ingest"]["status"] = "completed"
    state["stages"]["ingest"]["entry_checks_passed"] = True
    state["stages"]["ingest"]["exit_checks_passed"] = True
    state["stages"]["ingest"]["started_at"] = "2026-06-27T00:00:00Z"
    state["stages"]["ingest"]["completed_at"] = None  # will be set by transition
    save_state(state, fresh_state)

    action_transition_next("ingest", state, fresh_state)

    updated = load_state(fresh_state)
    ingest_state = updated["stages"]["ingest"]
    assert "duration_seconds" in ingest_state
    assert isinstance(ingest_state["duration_seconds"], int) or ingest_state["duration_seconds"] is None
