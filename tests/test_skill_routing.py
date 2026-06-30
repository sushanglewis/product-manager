"""Tests for .claude/skill-routing.yaml."""
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILL_ROUTING_PATH = ROOT / ".claude" / "skill-routing.yaml"
WORKFLOW_PATH = ROOT / ".claude" / "workflows" / "interview-to-knowledge.yaml"

VALID_NAMESPACES = {
    "superpowers",
    "gsd",
    "openspec",
    "oh-my-claudecode",
    "lincoln",
}


@pytest.fixture
def skill_routing():
    data = yaml.safe_load(SKILL_ROUTING_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------


def test_yaml_has_schema_version(skill_routing):
    assert "schema_version" in skill_routing


def test_yaml_has_routing(skill_routing):
    assert "routing" in skill_routing
    assert isinstance(skill_routing["routing"], dict)


# ---------------------------------------------------------------------------
# Stage routing structure tests
# ---------------------------------------------------------------------------


def test_every_stage_has_required_optional_human_gate_notes(skill_routing):
    routing = skill_routing["routing"]
    for stage_id, stage_def in routing.items():
        assert "required" in stage_def, f"Stage '{stage_id}' missing 'required'"
        assert isinstance(stage_def["required"], list), f"Stage '{stage_id}' required not a list"
        assert "optional" in stage_def, f"Stage '{stage_id}' missing 'optional'"
        assert isinstance(stage_def["optional"], list), f"Stage '{stage_id}' optional not a list"
        assert "human_gate" in stage_def, f"Stage '{stage_id}' missing 'human_gate'"
        assert isinstance(stage_def["human_gate"], bool), f"Stage '{stage_id}' human_gate not a bool"
        assert "notes" in stage_def, f"Stage '{stage_id}' missing 'notes'"


# ---------------------------------------------------------------------------
# Workflow coverage tests
# ---------------------------------------------------------------------------


def test_every_interview_workflow_stage_has_routing_entry(skill_routing):
    workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    workflow_steps = workflow.get("workflow", {}).get("steps", [])
    step_ids = {step["id"] for step in workflow_steps}

    routing = skill_routing["routing"]
    routing_stages = set(routing.keys())

    missing = step_ids - routing_stages
    assert not missing, f"Workflow stages missing from skill routing: {missing}"


# ---------------------------------------------------------------------------
# Namespace validation tests
# ---------------------------------------------------------------------------


def _extract_namespace(skill_str: str) -> str:
    if ":" in skill_str:
        return skill_str.split(":", 1)[0]
    return skill_str


def test_required_skills_use_recognized_namespaces(skill_routing):
    routing = skill_routing["routing"]
    for stage_id, stage_def in routing.items():
        for skill in stage_def.get("required", []):
            ns = _extract_namespace(skill)
            assert ns in VALID_NAMESPACES, (
                f"Stage '{stage_id}' required skill '{skill}' has unrecognized namespace '{ns}'"
            )


def test_optional_skills_use_recognized_namespaces(skill_routing):
    routing = skill_routing["routing"]
    for stage_id, stage_def in routing.items():
        for skill in stage_def.get("optional", []):
            ns = _extract_namespace(skill)
            assert ns in VALID_NAMESPACES, (
                f"Stage '{stage_id}' optional skill '{skill}' has unrecognized namespace '{ns}'"
            )


# ---------------------------------------------------------------------------
# Specific stage tests
# ---------------------------------------------------------------------------


def test_clarify_has_brainstorming_required(skill_routing):
    routing = skill_routing["routing"]
    assert "superpowers:brainstorming" in routing["clarify"]["required"]


def test_clarify_has_human_gate(skill_routing):
    routing = skill_routing["routing"]
    assert routing["clarify"]["human_gate"] is True


def test_implement_has_tdd_required(skill_routing):
    routing = skill_routing["routing"]
    assert "superpowers:test-driven-development" in routing["implement"]["required"]


def test_implement_has_human_gate(skill_routing):
    routing = skill_routing["routing"]
    assert routing["implement"]["human_gate"] is True


def test_sync_knowledge_has_docs_update_required(skill_routing):
    routing = skill_routing["routing"]
    assert "gsd:docs-update" in routing["sync-knowledge"]["required"]
