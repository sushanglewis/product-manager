from pathlib import Path

import yaml


def test_build_codebase_knowledge_skill_exists():
    root = Path(__file__).resolve().parents[1]
    skill = root / ".claude" / "skills" / "lincoln-build-codebase-knowledge" / "SKILL.md"
    assert skill.exists()
    assert "build codebase knowledge" in skill.read_text(encoding="utf-8").lower()


def test_explore_opensource_skill_exists():
    root = Path(__file__).resolve().parents[1]
    skill = root / ".claude" / "skills" / "lincoln-explore-opensource" / "SKILL.md"
    assert skill.exists()
    prompt = root / ".claude" / "skills" / "lincoln-explore-opensource" / "prompts" / "explore-opensource.md"
    assert prompt.exists()


def test_new_stages_registered_in_skill_yaml():
    root = Path(__file__).resolve().parents[1]
    data = yaml.safe_load((root / ".claude" / "skills" / "interview-workflow" / "skill.yaml").read_text(encoding="utf-8"))
    lincoln = data.get("skill_ecosystem", {}).get("lincoln", [])
    assert "lincoln-build-codebase-knowledge" in lincoln
    assert "lincoln-explore-opensource" in lincoln
    assert "lincoln-workflow-router" in lincoln
