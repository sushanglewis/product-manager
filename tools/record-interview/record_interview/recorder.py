# tools/record-interview/record_interview/recorder.py
from __future__ import annotations

import logging
import queue
import shutil
import subprocess
import threading
import time
from pathlib import Path

_LOGGER = logging.getLogger(__name__)


class RecordingError(Exception):
    pass


class FfmpegRecorder:
    def __init__(self, sample_rate: int = 44100) -> None:
        self.sample_rate = sample_rate
        self._process: subprocess.Popen | None = None
        self._output_path: Path | None = None
        self._started_at: float | None = None

    def _build_command(self, output_path: Path) -> list[str]:
        return [
            "ffmpeg",
            "-y",
            "-f", "avfoundation",
            "-i", ":default",
            "-ar", str(self.sample_rate),
            "-c:a", "aac",
            "-b:a", "128k",
            str(output_path),
        ]

    def start(self, output_path: Path) -> None:
        if not shutil.which("ffmpeg"):
            raise RecordingError("ffmpeg not found in PATH")
        if self._process is not None:
            raise RecordingError("already recording")

        self._output_path = output_path
        self._started_at = time.monotonic()
        cmd = self._build_command(output_path)
        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        time.sleep(0.05)
        if self._process.poll() is not None:
            stderr = self._process.stderr.read() if self._process.stderr else ""
            self._process = None
            self._started_at = None
            _LOGGER.warning("ffmpeg failed to start: %s", stderr)
            raise RecordingError("ffmpeg failed to start. Check the logs for details.")

    def stop(self) -> int:
        if self._process is None:
            raise RecordingError("not recording")
        self._process.terminate()
        try:
            self._process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait(timeout=5)

        returncode = self._process.returncode
        stderr = self._process.stderr.read() if self._process.stderr else ""
        duration = int(time.monotonic() - self._started_at) if self._started_at else 0
        self._process = None
        self._started_at = None

        if returncode != 0:
            # ffmpeg often exits with 255 after receiving SIGTERM, even though
            # it has already flushed the output. Treat that as a successful stop.
            if "Exiting normally" in stderr:
                return duration
            _LOGGER.warning("ffmpeg exited with code %s: %s", returncode, stderr)
            raise RecordingError(
                f"ffmpeg exited with code {returncode}. Check the logs for details."
            )
        return duration

    def is_recording(self) -> bool:
        return self._process is not None and self._process.poll() is None


class ChunkedRecorder:
    """Record audio into fixed-duration chunks using ffmpeg's segment muxer."""

    def __init__(self, output_dir: Path, chunk_seconds: int = 5, sample_rate: int = 44100) -> None:
        self.output_dir = output_dir
        self.chunk_seconds = chunk_seconds
        self.sample_rate = sample_rate
        self.queue: queue.Queue[Path | None] = queue.Queue()
        self._process: subprocess.Popen | None = None
        self._started_at: float | None = None
        self._watcher_thread: threading.Thread | None = None
        self._running = False

    def _build_command(self) -> list[str]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        pattern = str(self.output_dir / "chunk_%03d.m4a")
        return [
            "ffmpeg",
            "-y",
            "-f", "avfoundation",
            "-i", ":default",
            "-ar", str(self.sample_rate),
            "-c:a", "aac",
            "-b:a", "128k",
            "-f", "segment",
            "-segment_time", str(self.chunk_seconds),
            "-reset_timestamps", "1",
            pattern,
        ]

    def _watcher(self) -> None:
        previous = set()
        while self._running:
            time.sleep(0.2)
            current = set(self.output_dir.glob("chunk_*.m4a"))
            new = current - previous
            for path in sorted(new):
                self.queue.put(path)
            previous = current

    def start(self) -> None:
        if not shutil.which("ffmpeg"):
            raise RecordingError("ffmpeg not found in PATH")
        if self._process is not None:
            raise RecordingError("already recording")

        self._started_at = time.monotonic()
        self._running = True
        self._watcher_thread = threading.Thread(target=self._watcher, daemon=True)
        self._watcher_thread.start()

        cmd = self._build_command()
        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        time.sleep(0.05)
        if self._process.poll() is not None:
            stderr = self._process.stderr.read() if self._process.stderr else ""
            self._process = None
            self._running = False
            _LOGGER.warning("ffmpeg failed to start: %s", stderr)
            raise RecordingError("ffmpeg failed to start. Check the logs for details.")

    def stop(self) -> int:
        if self._process is None:
            raise RecordingError("not recording")
        self._running = False
        self._process.terminate()
        try:
            self._process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait(timeout=5)

        returncode = self._process.returncode
        stderr = self._process.stderr.read() if self._process.stderr else ""
        duration = int(time.monotonic() - self._started_at) if self._started_at else 0
        self._process = None

        if self._watcher_thread is not None:
            self._watcher_thread.join(timeout=2)

        if returncode != 0 and "Exiting normally" not in stderr:
            _LOGGER.warning("ffmpeg exited with code %s: %s", returncode, stderr)
            raise RecordingError(
                f"ffmpeg exited with code {returncode}. Check the logs for details."
            )
        return duration

    def is_recording(self) -> bool:
        return self._process is not None and self._process.poll() is None
