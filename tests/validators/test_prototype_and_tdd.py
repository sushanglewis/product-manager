import sys
from pathlib import Path

import pytest

VALIDATOR_DIR = Path(__file__).resolve().parents[2] / ".claude" / "skills" / "interview-workflow" / "validators"
sys.path.insert(0, str(VALIDATOR_DIR))

import validate


def run_validator(check_name, *args):
    check_fn = validate.EXIT_CHECKS[check_name]
    with pytest.raises(SystemExit) as exc_info:
        check_fn(*args)
    return exc_info.value.code


def write_prototype_package(root, design_id, prototype_approved=False):
    base = root / "designs" / design_id
    base.mkdir(parents=True, exist_ok=True)
    (base / "prototype.pen").write_text("pen-placeholder")
    (base / "fields.md").write_text("# 字段\n## 校验\n## 错误状态\n")
    ui = base / "ui-spec.md"
    ui.write_text(
        "# UI 规格\n## 界面\n## 交互\n## 状态\n"
        f"{'<!-- prototype-status: approved -->' if prototype_approved else ''}\n"
    )


def write_tdd_plan(root, design_id, ready=False):
    base = root / "designs" / design_id
    base.mkdir(parents=True, exist_ok=True)
    tdd = base / "tdd-plan.md"
    tdd.write_text(
        "# TDD Plan\n\n"
        "- Source: requirements/2026-06-27-stakeholder/requirements.md\n"
        f"- Source: designs/{design_id}/design-review.md\n"
        f"- Source: designs/{design_id}/fields.md\n"
        f"- Source: designs/{design_id}/ui-spec.md\n"
        f"- Source: designs/{design_id}/prototype.pen\n\n"
        "## 验收映射\n## 测试场景\n## 红/绿/重构\n## 任务切片\n## 回归范围\n"
        f"{'<!-- status: ready-for-openspec -->' if ready else ''}\n"
    )


class TestPrototypeArtifactComplete:
    def test_fails_when_prototype_pen_missing(self, tmp_project, design_id):
        validate.PROJECT_ROOT = tmp_project
        assert run_validator("prototype_artifact_complete", design_id) == 1

    def test_passes_when_all_artifacts_present(self, tmp_project, design_id):
        validate.PROJECT_ROOT = tmp_project
        write_prototype_package(tmp_project, design_id)
        assert run_validator("prototype_artifact_complete", design_id) == 0


class TestTddPlanComplete:
    def test_fails_when_sections_missing(self, tmp_project, design_id):
        validate.PROJECT_ROOT = tmp_project
        base = tmp_project / "designs" / design_id
        base.mkdir(parents=True, exist_ok=True)
        (base / "tdd-plan.md").write_text("# TDD Plan\n")
        assert run_validator("tdd_plan_complete", design_id) == 1

    def test_passes_when_all_sections_present(self, tmp_project, design_id):
        validate.PROJECT_ROOT = tmp_project
        write_tdd_plan(tmp_project, design_id)
        assert run_validator("tdd_plan_complete", design_id) == 0
