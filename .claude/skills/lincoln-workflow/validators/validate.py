#!/usr/bin/env python3
"""
Lincoln workflow validators.

Usage:
    python validate.py --phase entry --check file_exists --args path/to/file
    python validate.py --phase exit --check transcript_has_timestamps --args interviews/session-id

Exit code 0 means pass, 1 means fail.
"""

import argparse
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]


def fail(message: str):
    print(f"FAIL: {message}")
    sys.exit(1)


def pass_check(message: str = ""):
    print(f"PASS{' - ' + message if message else ''}")
    sys.exit(0)


def has_any_heading(content: str, aliases: list[str]) -> bool:
    return any(heading in content for heading in aliases)


def missing_heading_groups(content: str, required_groups: dict[str, list[str]]) -> list[str]:
    return [
        label
        for label, aliases in required_groups.items()
        if not has_any_heading(content, aliases)
    ]


def read_flat_yaml(path: Path) -> dict[str, str]:
    data = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        data[key.strip()] = value.strip().strip("'\"")
    return data


def design_base(design_id: str) -> Path:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", design_id):
        fail(f"Invalid design_id '{design_id}'. Use kebab-case, e.g. checkout-redesign")
    return PROJECT_ROOT / "designs" / design_id


def require_nonempty_file(path: Path, label: str):
    if not path.exists() or not path.is_file() or path.stat().st_size == 0:
        fail(f"{label} missing or empty: {path}")


def read_required_file(path: Path, label: str) -> str:
    require_nonempty_file(path, label)
    return path.read_text(encoding="utf-8")


def has_approval_marker(content: str, zh_label: str) -> bool:
    return "<!-- status: approved -->" in content or f"[x] PM 已确认{zh_label}" in content


# ---------------------------------------------------------------------------
# Entry checks
# ---------------------------------------------------------------------------

def check_file_exists(path: str):
    target = PROJECT_ROOT / path
    if not target.exists():
        fail(f"File does not exist: {target}")
    pass_check(str(target))


def check_audio_format_supported(path: str):
    supported = {".mp3", ".m4a", ".wav", ".mp4", ".mov"}
    ext = Path(path).suffix.lower()
    if ext not in supported:
        fail(f"Unsupported audio format: {ext}. Supported: {', '.join(supported)}")
    pass_check(ext)


def check_summary_ready(session_id: str):
    summary = PROJECT_ROOT / "interviews" / session_id / "summary.md"
    if not summary.exists() or summary.stat().st_size == 0:
        fail(f"Summary not ready: {summary}")
    pass_check(str(summary))


def check_requirements_approved(session_id: str):
    req = PROJECT_ROOT / "requirements" / session_id / "requirements.md"
    if not req.exists():
        fail(f"Requirements document missing: {req}")
    content = req.read_text(encoding="utf-8")
    if "<!-- status: approved -->" not in content and "[x] PM 已确认" not in content:
        fail("Requirements document exists but is not marked as approved")
    pass_check(str(req))


def check_openspec_tasks_ready(change_name: str):
    tasks = PROJECT_ROOT / "openspec" / "changes" / change_name / "tasks.md"
    if not tasks.exists() or tasks.stat().st_size == 0:
        fail(f"OpenSpec tasks not ready: {tasks}")
    content = tasks.read_text(encoding="utf-8")
    if not re.search(r"[-*]\s+\[.?\]", content):
        fail("OpenSpec tasks.md does not contain a recognizable task list")
    pass_check(str(tasks))


def check_issues_ready(session_id: str):
    linked = PROJECT_ROOT / ".github" / "linked-issues.yaml"
    if not linked.exists():
        fail("Linked issues file missing; run split-to-github first")
    pass_check(str(linked))


def check_pr_merged(pr_number: str):
    queue_file = PROJECT_ROOT / ".github" / "lincoln-sync-queue" / f"pr-{pr_number}.yaml"
    if not queue_file.exists():
        fail(f"PR {pr_number} sync queue file missing: {queue_file}")

    data = read_flat_yaml(queue_file)
    required = ["status", "repository", "issue_number", "pr_number", "merged_at"]
    missing = [key for key in required if not data.get(key)]
    if missing:
        fail(f"PR sync queue file missing fields: {', '.join(missing)}")
    if data["pr_number"] != str(pr_number):
        fail(f"PR sync queue file is for PR {data['pr_number']}, expected {pr_number}")
    if data["status"] != "pending":
        fail(f"PR {pr_number} sync status is {data['status']}, expected pending")
    pass_check(str(queue_file))


def check_issue_exists(issue_number: str):
    linked = PROJECT_ROOT / ".github" / "linked-issues.yaml"
    if not linked.exists():
        fail("Linked issues file missing")
    content = linked.read_text(encoding="utf-8")
    if issue_number not in content:
        fail(f"Issue {issue_number} not found in linked issues")
    pass_check(f"Issue {issue_number} linked")


def check_design_docs_ready(design_id: str):
    validate_design_docs_complete(design_id)
    pass_check(f"Design docs ready: {design_id}")


def check_product_design_approved(design_id: str):
    validate_design_docs_complete(design_id)
    content = read_required_file(design_base(design_id) / "design-review.md", "Design review")
    if not has_approval_marker(content, "设计文档"):
        fail("Product design docs are not marked as approved")
    pass_check(f"Product design approved: {design_id}")


def check_prototype_ready(design_id: str):
    validate_prototype_artifact_complete(design_id)
    content = read_required_file(design_base(design_id) / "ui-spec.md", "UI spec")
    if "<!-- prototype-status: approved -->" not in content and "[x] PM 已确认原型" not in content:
        fail("Prototype is not marked as approved")
    pass_check(f"Prototype ready: {design_id}")


def check_tdd_plan_ready(design_id: str):
    validate_tdd_plan_complete(design_id)
    content = read_required_file(design_base(design_id) / "tdd-plan.md", "TDD plan")
    if "<!-- status: ready-for-openspec -->" not in content:
        fail("TDD plan is not marked as ready for OpenSpec")
    pass_check(f"TDD plan ready: {design_id}")


# ---------------------------------------------------------------------------
# Exit checks
# ---------------------------------------------------------------------------

def check_transcript_has_timestamps(session_id: str):
    transcript = PROJECT_ROOT / "interviews" / session_id / "transcript.md"
    if not transcript.exists():
        fail(f"Transcript missing: {transcript}")
    content = transcript.read_text(encoding="utf-8")
    if not re.search(r"\d{2}:\d{2}:\d{2}", content):
        fail("Transcript does not contain timestamps")
    pass_check()


def check_summary_has_key_topics(session_id: str):
    summary = PROJECT_ROOT / "interviews" / session_id / "summary.md"
    if not summary.exists():
        fail(f"Summary missing: {summary}")
    content = summary.read_text(encoding="utf-8")
    required = {
        "关键主题": ["关键主题", "Key topics", "Key Topics"],
        "决策": ["决策", "Decisions"],
        "行动项": ["行动项", "Action items", "Action Items"],
    }
    missing = missing_heading_groups(content, required)
    if missing:
        fail(f"Summary missing sections: {', '.join(missing)}")
    pass_check()


def check_requirements_has_background_problem_solution_acceptance(session_id: str):
    req = PROJECT_ROOT / "requirements" / session_id / "requirements.md"
    if not req.exists():
        fail(f"Requirements missing: {req}")
    content = req.read_text(encoding="utf-8")
    required = {
        "背景": ["背景", "Background"],
        "问题": ["问题", "Problem"],
        "用户": ["用户", "Users", "Personas"],
        "方案": ["方案", "Proposed Solution", "Solution"],
        "验收标准": ["验收标准", "Acceptance Criteria"],
    }
    missing = missing_heading_groups(content, required)
    if missing:
        fail(f"Requirements missing sections: {', '.join(missing)}")
    pass_check()


def check_human_approved(session_id: str):
    req = PROJECT_ROOT / "requirements" / session_id / "requirements.md"
    if not req.exists():
        fail(f"Requirements missing: {req}")
    content = req.read_text(encoding="utf-8")
    if "<!-- status: approved -->" not in content and "[x] PM 已确认" not in content:
        fail("Human PM approval marker not found")
    pass_check()


def check_openspec_artifact_complete(change_name: str, design_id: str = ""):
    base = PROJECT_ROOT / "openspec" / "changes" / change_name
    required_files = ["proposal.md", "design.md", "tasks.md"]
    required_dirs = ["specs"]
    for f in required_files:
        p = base / f
        if not p.exists() or p.stat().st_size == 0:
            fail(f"OpenSpec artifact missing or empty: {p}")
    for d in required_dirs:
        p = base / d
        if not p.exists() or not any(p.iterdir()):
            fail(f"OpenSpec artifact directory missing or empty: {p}")
    if design_id:
        required_refs = [
            f"designs/{design_id}/tdd-plan.md",
            f"designs/{design_id}/prototype.pen",
            f"designs/{design_id}/design-review.md",
        ]
        combined = "\n".join((base / f).read_text(encoding="utf-8") for f in required_files)
        missing_refs = [ref for ref in required_refs if ref not in combined]
        if missing_refs:
            fail(f"OpenSpec artifact missing design references: {', '.join(missing_refs)}")
    pass_check()


def check_tasks_extracted(change_name: str):
    tasks = PROJECT_ROOT / "openspec" / "changes" / change_name / "tasks.md"
    if not tasks.exists():
        fail(f"Tasks file missing: {tasks}")
    content = tasks.read_text(encoding="utf-8")
    matches = re.findall(r"[-*]\s+\[.?\]\s+(.+)", content)
    if len(matches) < 1:
        fail("No tasks extracted from OpenSpec tasks.md")
    pass_check(f"{len(matches)} tasks found")


def check_issues_created(session_id: str):
    linked = PROJECT_ROOT / ".github" / "linked-issues.yaml"
    if not linked.exists():
        fail("Linked issues file missing")
    content = linked.read_text(encoding="utf-8")
    if not re.search(r"issue_number:\s*\d+", content):
        fail("No issue numbers recorded")
    pass_check()


def check_tasks_link_back_to_issues(session_id: str):
    linked = PROJECT_ROOT / ".github" / "linked-issues.yaml"
    req = PROJECT_ROOT / "requirements" / session_id / "requirements.md"
    if not linked.exists():
        fail("Linked issues file missing")
    if not req.exists():
        fail("Requirements file missing")
    req_content = req.read_text(encoding="utf-8")
    issues = re.findall(r"issue_number:\s*(\d+)", linked.read_text(encoding="utf-8"))
    missing = [i for i in issues if f"#{i}" not in req_content]
    if missing:
        fail(f"Requirements do not link back to issues: {', '.join(missing)}")
    pass_check()


def check_feature_doc_has_business_and_technical_sections(feature_slug: str):
    doc = PROJECT_ROOT / "docs" / "knowledge" / "03-features" / f"{feature_slug}.md"
    if not doc.exists():
        fail(f"Feature doc missing: {doc}")
    content = doc.read_text(encoding="utf-8")
    required = {
        "业务知识": ["业务知识", "Business Knowledge"],
        "技术知识": ["技术知识", "Technical Knowledge"],
    }
    missing = missing_heading_groups(content, required)
    if missing:
        fail(f"Feature doc missing sections: {', '.join(missing)}")
    pass_check()


def check_feature_doc_has_links(feature_slug: str):
    doc = PROJECT_ROOT / "docs" / "knowledge" / "03-features" / f"{feature_slug}.md"
    if not doc.exists():
        fail(f"Feature doc missing: {doc}")
    content = doc.read_text(encoding="utf-8")
    links = re.findall(r"\[\[([^\]]+)\]\]", content)
    if len(links) < 3:
        fail(f"Feature doc has too few wikilinks: {len(links)}")
    pass_check(f"{len(links)} wikilinks found")


def check_no_conflict_with_existing_knowledge(feature_slug: str):
    # Placeholder for semantic conflict detection.
    # v1: ensure no other feature doc has the same ID in frontmatter.
    doc = PROJECT_ROOT / "docs" / "knowledge" / "03-features" / f"{feature_slug}.md"
    if not doc.exists():
        fail(f"Feature doc missing: {doc}")
    content = doc.read_text(encoding="utf-8")
    id_match = re.search(r"^id:\s*(.+)$", content, re.MULTILINE)
    if not id_match:
        pass_check("No id in frontmatter; skipping conflict check")
    feat_id = id_match.group(1).strip()
    features_dir = PROJECT_ROOT / "docs" / "knowledge" / "03-features"
    conflicts = []
    for other in features_dir.glob("*.md"):
        if other.name == doc.name:
            continue
        other_content = other.read_text(encoding="utf-8")
        other_id_match = re.search(r"^id:\s*(.+)$", other_content, re.MULTILINE)
        if other_id_match and other_id_match.group(1).strip() == feat_id:
            conflicts.append(other.name)
    if conflicts:
        fail(f"Conflicting feature ID found in: {', '.join(conflicts)}")
    pass_check()


def validate_design_docs_complete(design_id: str):
    base = design_base(design_id)
    docs = [
        "design-review.md",
        "scenarios.md",
        "feature-catalog.md",
        "data-model.md",
        "flows.md",
        "feasibility.md",
    ]
    for doc in docs:
        require_nonempty_file(base / doc, doc)

    review = read_required_file(base / "design-review.md", "Design review")
    missing_links = [doc for doc in docs[1:] if doc not in review]
    if missing_links:
        fail(f"Design review missing links to: {', '.join(missing_links)}")

    flows = read_required_file(base / "flows.md", "Flows")
    if "```mermaid" not in flows:
        fail("flows.md must contain at least one Mermaid diagram")

    feature_catalog = read_required_file(base / "feature-catalog.md", "Feature catalog")
    if not has_any_heading(feature_catalog, ["验收", "Acceptance"]):
        fail("feature-catalog.md must map features to acceptance criteria")

    data_model = read_required_file(base / "data-model.md", "Data model")
    if not has_any_heading(data_model, ["字段", "Field", "约束", "Constraint"]):
        fail("data-model.md must describe fields or constraints")

    feasibility = read_required_file(base / "feasibility.md", "Feasibility")
    required = {
        "业务可行性": ["业务可行性", "Business feasibility"],
        "技术可行性": ["技术可行性", "Technical feasibility"],
        "开源项目": ["开源项目", "Open-source", "Open Source"],
        "技术框架": ["技术框架", "Framework"],
    }
    missing = missing_heading_groups(feasibility, required)
    if missing:
        fail(f"feasibility.md missing sections: {', '.join(missing)}")


def check_design_docs_complete(design_id: str):
    validate_design_docs_complete(design_id)
    pass_check(f"Design docs complete: {design_id}")


def check_design_docs_human_approved(design_id: str):
    validate_design_docs_complete(design_id)
    content = read_required_file(design_base(design_id) / "design-review.md", "Design review")
    if not has_approval_marker(content, "设计文档"):
        fail("Design docs approval marker not found")
    pass_check(f"Design docs approved: {design_id}")


def validate_prototype_artifact_complete(design_id: str):
    base = design_base(design_id)
    require_nonempty_file(base / "prototype.pen", "Pencil prototype")
    fields = read_required_file(base / "fields.md", "Fields")
    ui_spec = read_required_file(base / "ui-spec.md", "UI spec")

    required_fields = {
        "字段": ["字段", "Field"],
        "校验": ["校验", "Validation"],
        "错误状态": ["错误状态", "Error"],
    }
    missing_fields = missing_heading_groups(fields, required_fields)
    if missing_fields:
        fail(f"fields.md missing sections: {', '.join(missing_fields)}")

    required_ui = {
        "界面": ["界面", "Screen", "UI"],
        "交互": ["交互", "Interaction"],
        "状态": ["状态", "State"],
    }
    missing_ui = missing_heading_groups(ui_spec, required_ui)
    if missing_ui:
        fail(f"ui-spec.md missing sections: {', '.join(missing_ui)}")


def check_prototype_artifact_complete(design_id: str):
    validate_prototype_artifact_complete(design_id)
    pass_check(f"Prototype artifacts complete: {design_id}")


def validate_tdd_plan_complete(design_id: str):
    base = design_base(design_id)
    content = read_required_file(base / "tdd-plan.md", "TDD plan")
    required = {
        "验收映射": ["验收映射", "Acceptance mapping", "验收标准映射"],
        "测试场景": ["测试场景", "Test scenarios"],
        "红绿重构": ["红/绿/重构", "红绿重构", "Red/Green/Refactor"],
        "任务切片": ["任务切片", "Task slices"],
        "回归范围": ["回归范围", "Regression"],
    }
    missing = missing_heading_groups(content, required)
    if missing:
        fail(f"tdd-plan.md missing sections: {', '.join(missing)}")
    required_refs = [
        f"requirements/",
        f"designs/{design_id}/design-review.md",
        f"designs/{design_id}/fields.md",
        f"designs/{design_id}/ui-spec.md",
        f"designs/{design_id}/prototype.pen",
    ]
    missing_refs = [ref for ref in required_refs if ref not in content]
    if missing_refs:
        fail(f"tdd-plan.md missing source references: {', '.join(missing_refs)}")


def check_tdd_plan_complete(design_id: str):
    validate_tdd_plan_complete(design_id)
    pass_check(f"TDD plan complete: {design_id}")


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

ENTRY_CHECKS = {
    "file_exists": check_file_exists,
    "audio_format_supported": check_audio_format_supported,
    "summary_ready": check_summary_ready,
    "requirements_approved": check_requirements_approved,
    "openspec_tasks_ready": check_openspec_tasks_ready,
    "issues_ready": check_issues_ready,
    "pr_merged": check_pr_merged,
    "issue_exists": check_issue_exists,
    "design_docs_ready": check_design_docs_ready,
    "product_design_approved": check_product_design_approved,
    "prototype_ready": check_prototype_ready,
    "tdd_plan_ready": check_tdd_plan_ready,
}

EXIT_CHECKS = {
    "transcript_has_timestamps": check_transcript_has_timestamps,
    "summary_has_key_topics": check_summary_has_key_topics,
    "requirements_has_background_problem_solution_acceptance": check_requirements_has_background_problem_solution_acceptance,
    "human_approved": check_human_approved,
    "openspec_artifact_complete": check_openspec_artifact_complete,
    "tasks_extracted": check_tasks_extracted,
    "issues_created": check_issues_created,
    "tasks_link_back_to_issues": check_tasks_link_back_to_issues,
    "feature_doc_has_business_and_technical_sections": check_feature_doc_has_business_and_technical_sections,
    "feature_doc_has_links": check_feature_doc_has_links,
    "no_conflict_with_existing_knowledge": check_no_conflict_with_existing_knowledge,
    "design_docs_complete": check_design_docs_complete,
    "design_docs_human_approved": check_design_docs_human_approved,
    "prototype_artifact_complete": check_prototype_artifact_complete,
    "tdd_plan_complete": check_tdd_plan_complete,
}


def main():
    parser = argparse.ArgumentParser(description="Lincoln workflow validators")
    parser.add_argument("--phase", required=True, choices=["entry", "exit"])
    parser.add_argument("--check", required=True)
    parser.add_argument("--args", default="", help="Comma-separated arguments for the check")
    args = parser.parse_args()

    registry = ENTRY_CHECKS if args.phase == "entry" else EXIT_CHECKS
    check_fn = registry.get(args.check)
    if not check_fn:
        fail(f"Unknown check: {args.check}. Available: {', '.join(registry.keys())}")

    check_args = [a.strip() for a in args.args.split(",")] if args.args else []
    try:
        check_fn(*check_args)
    except TypeError as e:
        fail(f"Invalid arguments for check '{args.check}': {e}")


if __name__ == "__main__":
    main()
