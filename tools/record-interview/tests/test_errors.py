
from record_interview.errors import (
    ApiKeyMissingError,
    ClaudeCliMissingError,
    FfmpegMissingError,
    GitWorktreeError,
    GuidanceError,
    NoMicrophoneError,
    PyannoteMissingError,
    WhisperNotInstalledError,
)


def test_guidance_error_exposes_message_and_remediation():
    err = GuidanceError("msg", "fix it")
    assert err.message == "msg"
    assert err.remediation == "fix it"


def test_ffmpeg_missing_error_has_remediation():
    err = FfmpegMissingError()
    assert "ffmpeg" in err.message
    assert "brew install ffmpeg" in err.remediation


def test_no_microphone_error_has_remediation():
    err = NoMicrophoneError()
    assert "microphone" in err.message
    assert "Privacy" in err.remediation


def test_whisper_not_installed_error_has_remediation():
    err = WhisperNotInstalledError()
    assert "faster-whisper" in err.message
    assert "pip install" in err.remediation


def test_api_key_missing_error_has_remediation():
    err = ApiKeyMissingError("openai")
    assert "OPENAI_API_KEY" in err.remediation


def test_git_worktree_error_has_remediation():
    err = GitWorktreeError()
    assert "git" in err.message
    assert "worktree" in err.remediation


def test_claude_cli_missing_error_has_remediation():
    err = ClaudeCliMissingError()
    assert "claude" in err.message
    assert "anthropic/tap/claude-code" in err.remediation


def test_pyannote_missing_error_has_remediation():
    err = PyannoteMissingError()
    assert "pyannote" in err.message
    assert "pip install" in err.remediation
