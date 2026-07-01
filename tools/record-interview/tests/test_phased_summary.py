from record_interview.metadata import read_metadata
from record_interview.phased_summary import PhasedSummaryGenerator


def test_generate_phase_summary_writes_file_and_updates_metadata(tmp_path):
    class FakeSummarizer:
        def summarize(self, context: str, instruction: str) -> str:
            return "summary text"

    generator = PhasedSummaryGenerator(
        workspace_root=tmp_path,
        session_id="2026-06-27-test",
        summarizer=FakeSummarizer(),
        phase_interval_seconds=600,
    )
    path = generator.generate_phase_summary(
        transcript_segments=[(0.0, 1.0, "SPEAKER_A", "hello")],
        start_time="2026-06-27T10:00:00Z",
        end_time="2026-06-27T10:10:00Z",
    )
    assert path.exists()
    assert path.name == "phase-summary-01.md"
    assert path.read_text(encoding="utf-8") == "summary text"

    metadata = read_metadata(tmp_path, "2026-06-27-test")
    assert metadata["phased_summaries"][0]["file"] == str(path.relative_to(tmp_path))


def test_generate_final_summary_combines_phases(tmp_path):
    class FakeSummarizer:
        def summarize(self, context: str, instruction: str) -> str:
            return "final summary"

    generator = PhasedSummaryGenerator(
        workspace_root=tmp_path,
        session_id="2026-06-27-test",
        summarizer=FakeSummarizer(),
    )
    generator.generate_phase_summary(
        transcript_segments=[(0.0, 1.0, "A", "hello")],
        start_time="2026-06-27T10:00:00Z",
        end_time="2026-06-27T10:10:00Z",
    )
    summary_path = generator.generate_final_summary()
    assert summary_path.name == "summary.md"
    assert summary_path.read_text(encoding="utf-8") == "final summary"
