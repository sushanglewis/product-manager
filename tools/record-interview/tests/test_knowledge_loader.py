
from record_interview.knowledge_loader import (
    build_knowledge_context,
    list_knowledge_files,
    load_relevant_knowledge,
)


def test_list_knowledge_files_returns_md_files(tmp_path):
    docs = tmp_path / "docs" / "knowledge"
    docs.mkdir(parents=True)
    (docs / "a.md").write_text("product vision")
    (docs / "b.txt").write_text("ignore me")
    files = list_knowledge_files(tmp_path)
    assert files == [docs / "a.md"]


def test_load_relevant_knowledge_orders_by_keyword_overlap(tmp_path):
    docs = tmp_path / "docs" / "knowledge"
    docs.mkdir(parents=True)
    (docs / "vision.md").write_text("product vision roadmap")
    (docs / "tech.md").write_text("technical architecture api")
    (docs / "ops.md").write_text("deployment runbook")
    result = load_relevant_knowledge(tmp_path, "product roadmap")
    assert result[0] == docs / "vision.md"


def test_build_knowledge_context_includes_file_contents(tmp_path):
    docs = tmp_path / "docs" / "knowledge"
    docs.mkdir(parents=True)
    (docs / "vision.md").write_text("product vision")
    context = build_knowledge_context(tmp_path, "product")
    assert "vision.md" in context
    assert "product vision" in context


def test_load_relevant_knowledge_returns_empty_when_no_match(tmp_path):
    docs = tmp_path / "docs" / "knowledge"
    docs.mkdir(parents=True)
    (docs / "tech.md").write_text("api gateway")
    result = load_relevant_knowledge(tmp_path, "unrelated nonsense")
    assert result == []
