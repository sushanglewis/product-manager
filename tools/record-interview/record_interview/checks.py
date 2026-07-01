from __future__ import annotations

import logging
import platform
import shutil
import subprocess
import threading

from record_interview.config import Config

_LOGGER = logging.getLogger(__name__)

# AVAuthorizationStatus raw values on macOS / iOS.
_AV_AUTHORIZATION_NOT_DETERMINED = 0
_AV_AUTHORIZATION_RESTRICTED = 1
_AV_AUTHORIZATION_DENIED = 2
_AV_AUTHORIZATION_AUTHORIZED = 3


def check_ffmpeg() -> tuple[bool, str]:
    if shutil.which("ffmpeg"):
        return True, "ffmpeg is available"
    return False, "ffmpeg not found in PATH. Install with: brew install ffmpeg"


def request_microphone_permission(timeout_seconds: float = 30.0) -> bool:
    """Request macOS microphone permission and return whether it was granted.

    On non-macOS platforms this returns False immediately.
    """
    if platform.system() != "Darwin":
        return False
    try:
        from AVFoundation import (  # type: ignore[import-untyped]
            AVCaptureDevice,
            AVMediaTypeAudio,
        )
    except ImportError:
        return False

    try:
        status = AVCaptureDevice.authorizationStatusForMediaType_(AVMediaTypeAudio)
        if status == _AV_AUTHORIZATION_AUTHORIZED:
            return True
        if status == _AV_AUTHORIZATION_DENIED:
            return False

        event = threading.Event()
        granted = False

        def completion(is_granted: bool) -> None:
            nonlocal granted
            if event.is_set():
                return
            granted = is_granted
            event.set()

        AVCaptureDevice.requestAccessForMediaType_completionHandler_(
            AVMediaTypeAudio, completion
        )
        return event.wait(timeout=timeout_seconds) and granted
    except Exception as exc:  # noqa: BLE001
        _LOGGER.warning("Failed to request microphone permission: %s", exc)
        return False


def _list_avfoundation_devices() -> str:
    try:
        result = subprocess.run(
            ["ffmpeg", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return ""
    return result.stderr or ""


def check_microphone() -> tuple[bool, str]:
    devices = _list_avfoundation_devices()
    if "[AVFoundation indev" in devices and "input device" in devices.lower():
        return True, "microphone detected"
    if not shutil.which("ffmpeg"):
        return False, "cannot check microphone because ffmpeg is missing"
    return (
        False,
        "no microphone detected. Check System Settings > Privacy & Security > Microphone.",
    )


def check_transcription(config: Config) -> tuple[bool, str]:
    if config.transcription is None:
        return False, "transcription configuration is missing"
    try:
        import faster_whisper  # noqa: F401
        return True, f"faster-whisper model '{config.transcription.model}' will be used"
    except ImportError:
        if config.summarization and config.summarization.openai_api_key:
            return True, "OpenAI Whisper API will be used (OPENAI_API_KEY present)"
        return (
            False,
            "local faster-whisper not installed and no OPENAI_API_KEY provided. "
            "Install with: pip install faster-whisper",
        )


def check_diarization(config: Config) -> tuple[bool, str]:
    provider = config.diarization.provider if config.diarization else "pyannote"
    if provider == "heuristic":
        return True, "heuristic speaker alternation will be used"
    if provider == "diarize":
        try:
            import diarize  # noqa: F401
            return True, "diarize (CPU) is available"
        except ImportError:
            return False, "diarize not installed. Install with: pip install diarize"
    if provider == "pyannote":
        try:
            import pyannote.audio  # noqa: F401
        except ImportError:
            return False, "pyannote.audio not installed. Install with: pip install pyannote.audio"
        token = config.diarization.huggingface_token if config.diarization else None
        if not token:
            return False, "HUGGINGFACE_TOKEN is required for pyannote. Set it or switch to diarize/heuristic."
        return True, "pyannote speaker diarization will be used"
    return False, f"unknown diarization provider: {provider}"


def check_summarization(config: Config) -> tuple[bool, str]:
    provider = config.summarization.provider if config.summarization else "claude"
    if provider == "claude":
        if shutil.which("claude"):
            return True, "claude CLI will be used for summarization"
        return False, "claude CLI not found. Install with: brew install anthropic/tap/claude-code"
    if provider == "openai":
        key = config.summarization.openai_api_key if config.summarization else None
        if key:
            return True, "OpenAI API will be used for summarization"
        return False, "OPENAI_API_KEY is required for OpenAI summarization"
    if provider == "anthropic":
        key = config.summarization.anthropic_api_key if config.summarization else None
        if key:
            return True, "Anthropic API will be used for summarization"
        return False, "ANTHROPIC_API_KEY is required for Anthropic summarization"
    return False, f"unknown summarization provider: {provider}"


def run_setup_checks(config: Config) -> dict[str, tuple[bool, str]]:
    return {
        "ffmpeg": check_ffmpeg(),
        "microphone": check_microphone(),
        "transcription": check_transcription(config),
        "diarization": check_diarization(config),
        "summarization": check_summarization(config),
    }
