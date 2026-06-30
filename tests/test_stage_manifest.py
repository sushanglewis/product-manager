"""Tests for .claude/stages/stage-manifest.yaml."""
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / ".claude" / "stages" / "stage-manifest.yaml"
WORKFLOW_PATH = ROOT / ".claude" / "workflows" / "interview-to-knowledge.yaml"


@pytest.fixture
def manifest():
    data = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------


def test_yaml_has_schema_version(manifest):
    assert "schema_version" in manifest


def test_yaml_has_stages(manifest):
    assert "stages" in manifest
    assert isinstance(manifest["stages"], list)


# ---------------------------------------------------------------------------
# Stage manifest structure tests
# ---------------------------------------------------------------------------


def test_every_stage_has_id(manifest):
    for stage in manifest["stages"]:
        assert "id" in stage, f"Stage missing 'id': {stage}"


def test_every_stage_has_name(manifest):
    for stage in manifest["stages"]:
        assert "name" in stage, f"Stage '{stage.get('id', '?')}' missing 'name'"


def test_every_stage_has_human_gate(manifest):
    for stage in manifest["stages"]:
        assert "human_gate" in stage, f"Stage '{stage.get('id', '?')}' missing 'human_gate'"
        assert isinstance(stage["human_gate"], bool)


def test_every_stage_has_required_skills(manifest):
    for stage in manifest["stages"]:
        assert "required_skills" in stage, f"Stage '{stage.get('id', '?')}' missing 'required_skills'"


def test_every_stage_has_context_files(manifest):
    for stage in manifest["stages"]:
        assert "context_files" in stage, f"Stage '{stage.get('id', '?')}' missing 'context_files'"
        ctx = stage["context_files"]
        for key in ["agents_md", "checklist_md", "skills_md", "prompt_md"]:
            assert key in ctx, f"Stage '{stage.get('id', '?')}' context_files missing '{key}'"


# ---------------------------------------------------------------------------
# Physical directory tests
# ---------------------------------------------------------------------------


def test_every_stage_has_physical_directory(manifest):
    for stage in manifest["stages"]:
        stage_dir = ROOT / ".claude" / "stages" / stage["id"]
        assert stage_dir.is_dir(), f"Stage directory missing: {stage_dir}"


def test_every_stage_has_agents_md(manifest):
    for stage in manifest["stages"]:
        path = ROOT / ".claude" / "stages" / stage["id"] / "AGENTS.md"
        assert path.exists(), f"AGENTS.md missing for stage '{stage['id']}'"


def test_every_stage_has_checklist_md(manifest):
    for stage in manifest["stages"]:
        path = ROOT / ".claude" / "stages" / stage["id"] / "CHECKLIST.md"
        assert path.exists(), f"CHECKLIST.md missing for stage '{stage['id']}'"


def test_every_stage_has_skills_md(manifest):
    for stage in manifest["stages"]:
        path = ROOT / ".claude" / "stages" / stage["id"] / "SKILLS.md"
        assert path.exists(), f"SKILLS.md missing for stage '{stage['id']}'"


def test_every_stage_has_prompt_md(manifest):
    for stage in manifest["stages"]:
        path = ROOT / ".claude" / "stages" / stage["id"] / "PROMPT.md"
        assert path.exists(), f"PROMPT.md missing for stage '{stage['id']}'"


# ---------------------------------------------------------------------------
# Workflow coverage tests
# ---------------------------------------------------------------------------


def test_every_workflow_stage_in_manifest(manifest):
    workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    workflow_steps = workflow.get("workflow", {}).get("steps", [])
    workflow_stage_ids = {step["id"] for step in workflow_steps}

    manifest_stage_ids = {stage["id"] for stage in manifest["stages"]}

    missing = workflow_stage_ids - manifest_stage_ids
    assert not missing, f"Workflow stages missing from manifest: {missing}"


# ---------------------------------------------------------------------------
# Context file existence tests
# ---------------------------------------------------------------------------


def test_context_files_paths_exist(manifest):
    for stage in manifest["stages"]:
        ctx = stage.get("context_files", {})
        for key, rel_path in ctx.items():
            full_path = ROOT / rel_path
            assert full_path.exists(), (
                f"Stage '{stage['id']}' context file '{key}' not found: {full_path}"
            )
