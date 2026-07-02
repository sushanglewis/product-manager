import pytest
import pytest_asyncio

from record_interview.config import Config, DiarizationConfig, SummarizationConfig, TranscriptionConfig
from record_interview.tui.app import LincolnRecordApp
from record_interview.tui.screens.recording import RecordingScreen


@pytest_asyncio.fixture
async def app(tmp_path):
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
    async with app.run_test() as pilot:
        yield pilot


@pytest.mark.asyncio
async def test_setup_screen_renders_checks(app, mocker):
    mocker.patch("record_interview.tui.screens.recording.TranscriptionPipeline")
    mocker.patch("record_interview.checks.check_ffmpeg", return_value=(True, "ok"))
    mocker.patch("record_interview.checks.check_microphone", return_value=(True, "ok"))
    mocker.patch("record_interview.checks.check_transcription", return_value=(True, "ok"))
    mocker.patch("record_interview.checks.check_diarization", return_value=(True, "ok"))
    mocker.patch("record_interview.checks.check_summarization", return_value=(True, "ok"))
    app.app.screen._run_checks()
    await app.pause()
    await app.click("#start")
    await app.pause()
    assert isinstance(app.app.screen, RecordingScreen)


@pytest.mark.asyncio
async def test_setup_screen_requests_microphone_permission_when_missing(app, mocker):
    mocker.patch("record_interview.tui.screens.recording.TranscriptionPipeline")
    mocker.patch("record_interview.checks.check_ffmpeg", return_value=(True, "ok"))
    mocker.patch("record_interview.checks.check_transcription", return_value=(True, "ok"))
    mocker.patch("record_interview.checks.check_diarization", return_value=(True, "ok"))
    mocker.patch("record_interview.checks.check_summarization", return_value=(True, "ok"))
    mocker.patch("record_interview.checks.check_microphone", return_value=(False, "no microphone"))
    request_spy = mocker.patch(
        "record_interview.tui.screens.setup._request_microphone_permission_with_reason",
        return_value=(False, "denied"),
    )
    app.app.screen._requested_permission = False
    app.app.screen._run_checks()
    await app.pause()
    request_spy.assert_called_once()
    assert "denied" in app.app.screen._checks["microphone"][1]
