import pytest
import pytest_asyncio

from record_interview.config import Config, DiarizationConfig, SummarizationConfig, TranscriptionConfig
from record_interview.tui.app import LincolnRecordApp
from record_interview.tui.screens.summary import SummaryScreen


@pytest_asyncio.fixture
async def summary_app(tmp_path):
    (tmp_path / "recordings").mkdir()
    (tmp_path / "interviews").mkdir()
    (tmp_path / ".claude").mkdir()
    config = Config(
        transcription=TranscriptionConfig(),
        diarization=DiarizationConfig(provider="heuristic"),
        summarization=SummarizationConfig(provider="openai", openai_api_key="sk-key"),
    )
    app = LincolnRecordApp(
        workspace_root=tmp_path,
        session_id="2026-06-27-test",
        config=config,
    )
    app.duration_seconds = 125
    app.summary_path = tmp_path / "summary.md"
    app.phase_summaries = [tmp_path / "phase-summary-01.md"]
    async with app.run_test() as pilot:
        app.push_screen("summary")
        yield pilot


@pytest.mark.asyncio
async def test_summary_screen_shows_duration_and_paths(summary_app):
    await summary_app.pause()
    screen = summary_app.app.screen
    assert isinstance(screen, SummaryScreen)
    body = screen.query_one("#summary-body")
    text = "\n".join(str(child.render()) for child in body.children)
    assert "02:05" in text
    assert "phase-summary-01.md" in text
