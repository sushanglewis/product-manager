# tools/record-interview/tests/test_recorder.py
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from record_interview.recorder import FfmpegRecorder, RecordingError


def test_recorder_builds_correct_command():
    recorder = FfmpegRecorder(sample_rate=44100)
    output = Path("/tmp/test.m4a")
    cmd = recorder._build_command(output)
    assert cmd[0] == "ffmpeg"
    assert "-f" in cmd
    assert "avfoundation" in cmd
    assert "-i" in cmd
    assert ":default" in cmd
    assert str(output) in cmd


@patch("record_interview.recorder.shutil.which", return_value="/usr/local/bin/ffmpeg")
@patch("record_interview.recorder.subprocess.Popen")
def test_recorder_start_stop(mock_popen, mock_which):
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None
    mock_proc.wait.return_value = 0
    mock_proc.returncode = 0
    mock_popen.return_value = mock_proc

    recorder = FfmpegRecorder(sample_rate=44100)
    recorder.start(Path("/tmp/test.m4a"))
    assert recorder.is_recording()

    duration = recorder.stop()
    mock_proc.terminate.assert_called_once()
    mock_proc.wait.assert_called_once()
    assert isinstance(duration, int)


@patch("record_interview.recorder.shutil.which", return_value="/usr/local/bin/ffmpeg")
@patch("record_interview.recorder.subprocess.Popen")
def test_recorder_raises_on_failure(mock_popen, mock_which):
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None
    mock_proc.wait.return_value = 1
    mock_proc.returncode = 1
    mock_proc.stderr.read.return_value = "Device not found"
    mock_popen.return_value = mock_proc

    recorder = FfmpegRecorder(sample_rate=44100)
    recorder.start(Path("/tmp/test.m4a"))
    with pytest.raises(RecordingError, match="ffmpeg exited with code 1"):
        recorder.stop()


@patch("record_interview.recorder.shutil.which", return_value="/usr/local/bin/ffmpeg")
@patch("record_interview.recorder.subprocess.Popen")
def test_recorder_treats_signal_termination_as_success(mock_popen, mock_which):
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None
    mock_proc.wait.return_value = 0
    mock_proc.returncode = 255
    mock_proc.stderr.read.return_value = "Exiting normally, received signal 15."
    mock_popen.return_value = mock_proc

    recorder = FfmpegRecorder(sample_rate=44100)
    recorder.start(Path("/tmp/test.m4a"))
    duration = recorder.stop()

    mock_proc.terminate.assert_called_once()
    mock_proc.wait.assert_called_once()
    assert isinstance(duration, int)


@patch("record_interview.recorder.shutil.which", return_value="/usr/local/bin/ffmpeg")
@patch("record_interview.recorder.subprocess.Popen")
def test_start_raises_when_already_recording(mock_popen, mock_which):
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None
    mock_popen.return_value = mock_proc

    recorder = FfmpegRecorder(sample_rate=44100)
    recorder.start(Path("/tmp/test.m4a"))
    with pytest.raises(RecordingError, match="already recording"):
        recorder.start(Path("/tmp/test2.m4a"))


def test_stop_raises_when_not_recording():
    recorder = FfmpegRecorder(sample_rate=44100)
    with pytest.raises(RecordingError, match="not recording"):
        recorder.stop()


@patch("record_interview.recorder.shutil.which", return_value=None)
def test_start_raises_when_ffmpeg_missing(mock_which):
    recorder = FfmpegRecorder(sample_rate=44100)
    with pytest.raises(RecordingError, match="ffmpeg not found in PATH"):
        recorder.start(Path("/tmp/test.m4a"))


@patch("record_interview.recorder.shutil.which", return_value="/usr/local/bin/ffmpeg")
@patch("record_interview.recorder.subprocess.Popen")
def test_start_raises_when_ffmpeg_fails_to_start(mock_popen, mock_which):
    mock_proc = MagicMock()
    mock_proc.poll.return_value = 1
    mock_proc.stderr.read.return_value = "Permission denied"
    mock_popen.return_value = mock_proc

    recorder = FfmpegRecorder(sample_rate=44100)
    with pytest.raises(RecordingError, match="ffmpeg failed to start"):
        recorder.start(Path("/tmp/test.m4a"))
    assert recorder._process is None
    assert recorder._started_at is None
