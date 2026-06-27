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
import os
import re
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[5]


def fail(message: str):
    print(f"FAIL: {message}")
    sys.exit(1)


def pass_check(message: str = ""):
    print(f"PASS{' - ' + message if message else ''}")
    sys.exit(0)


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
    # This check is intended to run in CI where GH context is available.
    # In local mode, we accept a state file marker.
    marker = PROJECT_ROOT / ".context" / f"pr-{pr_number}-merged"
    if marker.exists():
        pass_check(str(marker))
    # If running in GitHub Actions, the env var GITHUB_EVENT_NAME indicates merge.
    if os.environ.get("GITHUB_EVENT_NAME") == "pull_request" and os.environ.get("GITHUB_ACTION"):
        pass_check("Running in GitHub Actions PR merge context")
    fail(f"PR {pr_number} merge marker not found and not running in GitHub Actions")


def check_issue_exists(issue_number: str):
    linked = PROJECT_ROOT / ".github" / "linked-issues.yaml"
    if not linked.exists():
        fail("Linked issues file missing")
    content = linked.read_text(encoding="utf-8")
    if issue_number not in content:
        fail(f"Issue {issue_number} not found in linked issues")
    pass_check(f"Issue {issue_number} linked")


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
    required = ["关键主题", "决策", "行动项"]
    missing = [h for h in required if h not in content]
    if missing:
        fail(f"Summary missing sections: {', '.join(missing)}")
    pass_check()


def check_requirements_has_background_problem_solution_acceptance(session_id: str):
    req = PROJECT_ROOT / "requirements" / session_id / "requirements.md"
    if not req.exists():
        fail(f"Requirements missing: {req}")
    content = req.read_text(encoding="utf-8")
    required = ["背景", "问题", "用户", "方案", "验收标准"]
    missing = [h for h in required if h not in content]
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


def check_openspec_artifact_complete(change_name: str):
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
    required = ["业务知识", "技术知识"]
    missing = [h for h in required if h not in content]
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
