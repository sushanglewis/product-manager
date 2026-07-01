import pytest
from pathlib import Path

from record_interview.config import Config, DiarizationConfig
from record_interview.diarizer import HeuristicDiarizer, build_diarizer
from record_interview.transcriber import TranscriptionSegment


def test_build_diarizer_heuristic():
    cfg = Config(diarization=DiarizationConfig(provider="heuristic"))
    diarizer = build_diarizer(cfg)
    assert isinstance(diarizer, HeuristicDiarizer)


def test_build_diarizer_unknown_provider():
    cfg = Config(diarization=DiarizationConfig(provider="unknown"))
    with pytest.raises(ValueError, match="unknown diarization provider"):
        build_diarizer(cfg)


def test_heuristic_diarizer_alternates_speakers():
    diarizer = HeuristicDiarizer()
    segments = [
        TranscriptionSegment(start=0.0, end=1.0, text="hello"),
        TranscriptionSegment(start=1.0, end=2.0, text="world"),
        TranscriptionSegment(start=2.0, end=3.0, text="again"),
    ]
    result = diarizer.assign_speakers(Path("x.wav"), segments)
    assert result[0][1] == "SPEAKER_A"
    assert result[1][1] == "SPEAKER_B"
    assert result[2][1] == "SPEAKER_A"


def test_heuristic_diarizer_diarize_returns_empty():
    diarizer = HeuristicDiarizer()
    assert diarizer.diarize(Path("x.wav")) == []


def test_build_diarizer_pyannote_with_token(mocker):
    pipeline_cls = mocker.MagicMock()
    mocker.patch.dict(
        "sys.modules",
        {
            "pyannote": mocker.MagicMock(),
            "pyannote.audio": mocker.MagicMock(Pipeline=pipeline_cls),
        },
    )
    cfg = Config(diarization=DiarizationConfig(provider="pyannote", huggingface_token="hf-token"))
    build_diarizer(cfg)
    pipeline_cls.from_pretrained.assert_called_once()


def test_build_diarizer_pyannote_import_error(mocker):
    mocker.patch.dict("sys.modules", {"pyannote.audio": None})
    cfg = Config(diarization=DiarizationConfig(provider="pyannote"))
    with pytest.raises(ImportError, match="pyannote.audio is not installed"):
        build_diarizer(cfg)


def test_build_diarizer_diarize_import_error(mocker):
    mocker.patch.dict("sys.modules", {"diarize": None})
    cfg = Config(diarization=DiarizationConfig(provider="diarize"))
    with pytest.raises(ImportError, match="diarize is not installed"):
        build_diarizer(cfg)
