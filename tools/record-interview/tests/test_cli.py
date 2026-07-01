import json
from unittest.mock import MagicMock, patch

from record_interview.cli import run_recording_flow
from record_interview.config import Config


def test_run_recording_flow_creates_metadata_and_triggers_process(tmp_path):
    recordings_dir = tmp_path / "recordings"
    interviews_dir = tmp_path / "interviews"
    claude_dir = tmp_path / ".claude"
    recordings_dir.mkdir()
    interviews_dir.mkdir()
    claude_dir.mkdir()

    recorder_mock = MagicMock()
    recorder_mock.start.return_value = None
    recorder_mock.stop.return_value = 120
    recorder_mock.is_recording.return_value = False

    with patch("record_interview.cli.FfmpegRecorder", return_value=recorder_mock), \
         patch("record_interview.cli.trigger_process_interview") as mock_trigger, \
         patch("record_interview.cli._confirm", return_value=True), \
         patch("builtins.input", return_value=""):
        run_recording_flow(
            workspace_root=tmp_path,
            session_id="2026-06-27-test",
            config=Config(),
            design_id="d1",
            topic="test topic",
            branch="main",
        )

    recorder_mock.start.assert_called_once_with(tmp_path / "recordings" / "2026-06-27-test.m4a")
    metadata_path = interviews_dir / "2026-06-27-test" / "metadata.json"
    assert metadata_path.exists()
    meta = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert meta["session_id"] == "2026-06-27-test"
    assert meta["duration_seconds"] == 120
    mock_trigger.assert_called_once_with(tmp_path, "2026-06-27-test")


def test_run_recording_flow_no_confirm_skips_trigger(tmp_path):
    recordings_dir = tmp_path / "recordings"
    interviews_dir = tmp_path / "interviews"
    claude_dir = tmp_path / ".claude"
    recordings_dir.mkdir()
    interviews_dir.mkdir()
    claude_dir.mkdir()

    recorder_mock = MagicMock()
    recorder_mock.start.return_value = None
    recorder_mock.stop.return_value = 120
    recorder_mock.is_recording.return_value = False

    with patch("record_interview.cli.FfmpegRecorder", return_value=recorder_mock), \
         patch("record_interview.cli.trigger_process_interview") as mock_trigger, \
         patch("builtins.input", return_value=""):
        result = run_recording_flow(
            workspace_root=tmp_path,
            session_id="2026-06-27-test",
            config=Config(),
            design_id="d1",
            topic="test topic",
            branch="main",
            no_confirm=True,
        )

    recorder_mock.start.assert_called_once_with(tmp_path / "recordings" / "2026-06-27-test.m4a")
    metadata_path = interviews_dir / "2026-06-27-test" / "metadata.json"
    assert metadata_path.exists()
    mock_trigger.assert_not_called()
    assert result == 0


def test_run_recording_flow_cancels_when_not_confirmed(tmp_path):
    recordings_dir = tmp_path / "recordings"
    interviews_dir = tmp_path / "interviews"
    claude_dir = tmp_path / ".claude"
    recordings_dir.mkdir()
    interviews_dir.mkdir()
    claude_dir.mkdir()

    recorder_mock = MagicMock()
    recorder_mock.start.return_value = None
    recorder_mock.stop.return_value = 120
    recorder_mock.is_recording.return_value = False

    with patch("record_interview.cli.FfmpegRecorder", return_value=recorder_mock), \
         patch("record_interview.cli.trigger_process_interview") as mock_trigger, \
         patch("record_interview.cli._confirm", return_value=False), \
         patch("builtins.input", return_value=""):
        result = run_recording_flow(
            workspace_root=tmp_path,
            session_id="2026-06-27-test",
            config=Config(),
            design_id="d1",
            topic="test topic",
            branch="main",
        )

    mock_trigger.assert_not_called()
    assert result == 0


def test_run_recording_flow_cancels_on_keyboard_interrupt(tmp_path):
    recordings_dir = tmp_path / "recordings"
    interviews_dir = tmp_path / "interviews"
    claude_dir = tmp_path / ".claude"
    recordings_dir.mkdir()
    interviews_dir.mkdir()
    claude_dir.mkdir()

    recorder_mock = MagicMock()
    recorder_mock.start.return_value = None
    recorder_mock.stop.return_value = 120
    recorder_mock.is_recording.return_value = False

    with patch("record_interview.cli.FfmpegRecorder", return_value=recorder_mock), \
         patch("record_interview.cli.trigger_process_interview") as mock_trigger, \
         patch("builtins.input", side_effect=KeyboardInterrupt):
        result = run_recording_flow(
            workspace_root=tmp_path,
            session_id="2026-06-27-test",
            config=Config(),
            design_id="d1",
            topic="test topic",
            branch="main",
        )

    mock_trigger.assert_not_called()
    assert result == 130
