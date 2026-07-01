from unittest.mock import MagicMock

import pytest

from record_interview.recorder import ChunkedRecorder, RecordingError


def test_chunked_recorder_build_command_uses_segment_muxer(tmp_path):
    recorder = ChunkedRecorder(output_dir=tmp_path / "chunks", chunk_seconds=5)
    cmd = recorder._build_command()
    assert "segment" in cmd
    assert "5" in cmd
    assert str(tmp_path / "chunks" / "chunk_%03d.m4a") in cmd


def test_chunked_recorder_start_raises_when_ffmpeg_missing(mocker, tmp_path):
    mocker.patch("shutil.which", return_value=None)
    recorder = ChunkedRecorder(output_dir=tmp_path)
    with pytest.raises(RecordingError, match="ffmpeg not found"):
        recorder.start()


def test_chunked_recorder_start_stop_lifecycle(mocker, tmp_path):
    mocker.patch("shutil.which", return_value="/usr/bin/ffmpeg")
    process_mock = MagicMock()
    process_mock.poll.return_value = None
    process_mock.returncode = 0
    process_mock.stderr.read.return_value = "Exiting normally"
    mocker.patch("subprocess.Popen", return_value=process_mock)

    recorder = ChunkedRecorder(output_dir=tmp_path / "chunks", chunk_seconds=5)
    recorder.start()
    assert recorder.is_recording() is True
    duration = recorder.stop()
    assert isinstance(duration, int)
    process_mock.terminate.assert_called_once()


def test_chunked_recorder_raises_when_already_recording(mocker, tmp_path):
    mocker.patch("shutil.which", return_value="/usr/bin/ffmpeg")
    process_mock = MagicMock()
    process_mock.poll.return_value = None
    mocker.patch("subprocess.Popen", return_value=process_mock)

    recorder = ChunkedRecorder(output_dir=tmp_path)
    recorder.start()
    with pytest.raises(RecordingError, match="already recording"):
        recorder.start()
