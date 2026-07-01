
import pytest

from record_interview.config import (
    Config,
    DiarizationConfig,
    SummarizationConfig,
    TranscriptionConfig,
    load_config,
)


def test_load_config_returns_defaults(mocker):
    mocker.patch("record_interview.config._load_lincolnrc", return_value={})
    mocker.patch.dict("os.environ", {}, clear=True)
    cfg = load_config()
    assert cfg.chunk_seconds == 5
    assert cfg.phase_interval_seconds == 600
    assert cfg.transcription == TranscriptionConfig()
    assert cfg.diarization == DiarizationConfig()
    assert cfg.summarization == SummarizationConfig()


def test_load_config_reads_lincolnrc(mocker):
    mocker.patch(
        "record_interview.config._load_lincolnrc",
        return_value={
            "chunk_seconds": 10,
            "phase_interval_seconds": 300,
            "transcription": {"model": "medium"},
            "diarization": {"provider": "diarize"},
            "summarization": {"provider": "openai"},
        },
    )
    cfg = load_config()
    assert cfg.chunk_seconds == 10
    assert cfg.phase_interval_seconds == 300
    assert cfg.transcription.model == "medium"
    assert cfg.diarization.provider == "diarize"
    assert cfg.summarization.provider == "openai"


def test_load_config_reads_env_vars(mocker):
    mocker.patch("record_interview.config._load_lincolnrc", return_value={})
    env = {
        "HUGGINGFACE_TOKEN": "hf-token",
        "OPENAI_API_KEY": "openai-key",
        "ANTHROPIC_API_KEY": "anthropic-key",
    }
    mocker.patch.dict("os.environ", env, clear=False)
    cfg = load_config()
    assert cfg.diarization.huggingface_token == "hf-token"
    assert cfg.summarization.openai_api_key == "openai-key"
    assert cfg.summarization.anthropic_api_key == "anthropic-key"


def test_config_is_immutable():
    cfg = Config()
    with pytest.raises(AttributeError):
        cfg.chunk_seconds = 10
