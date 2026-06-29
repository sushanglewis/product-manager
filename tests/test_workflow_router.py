from pathlib import Path

import pytest
import yaml

from scripts.stage_loader import load_workflow, resolve_workflow_path


def test_default_workflow_loads():
    workflow = load_workflow()
    assert workflow["name"] == "interview-to-knowledge"


def test_template_workflow_loads():
    workflow = load_workflow("bug-fix")
    assert workflow["name"] == "bug-fix"
    stage_ids = [s["id"] for s in workflow["steps"]]
    assert "workflow-router" in stage_ids
    assert "implement" in stage_ids


def test_missing_template_raises():
    with pytest.raises(FileNotFoundError):
        resolve_workflow_path("does-not-exist")


def test_all_templates_have_valid_yaml():
    root = Path(__file__).resolve().parents[1]
    templates_dir = root / ".claude" / "workflows" / "templates"
    for path in templates_dir.glob("*.yaml"):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert "workflow" in data
        assert "steps" in data["workflow"]
        for step in data["workflow"]["steps"]:
            assert "id" in step
