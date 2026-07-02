from pathlib import Path

import pytest
import yaml


def test_skill_dependencies_yaml_is_valid():
    root = Path(__file__).resolve().parents[1]
    manifest_path = root / ".claude" / "skills" / "dependencies.yaml"
    assert manifest_path.exists()
    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0.0"
    assert "skills" in data
    assert "superpowers" in data["skills"]
    assert "openspec" in data["skills"]


def test_openspec_dependency_is_cli_type():
    root = Path(__file__).resolve().parents[1]
    data = yaml.safe_load((root / ".claude" / "skills" / "dependencies.yaml").read_text(encoding="utf-8"))
    openspec = data["skills"]["openspec"]
    assert openspec["type"] == "cli"
    assert openspec["binary"] == "openspec"
