from __future__ import annotations

import time
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Log, Static

from record_interview.metadata import update_recording_complete
from record_interview.pipeline import PipelineSegment, TranscriptionPipeline


class RecordingScreen(Screen):
    BINDINGS = [
        ("q", "stop", "Stop Recording"),
        ("space", "mark", "Mark"),
    ]

    elapsed_seconds: reactive[int] = reactive(0)
    transcript_lines: reactive[list[str]] = reactive([])

    def __init__(self) -> None:
        super().__init__()
        self._pipeline: TranscriptionPipeline | None = None
        self._start_time = 0.0

    def compose(self) -> ComposeResult:
        yield Static("Recording...", id="recording-title")
        with Horizontal(id="recording-stats"):
            yield Static("00:00", id="timer")
            yield Static("Next summary in --:--", id="countdown")
        yield Log(id="transcript")
        with Horizontal(id="recording-actions"):
            yield Button("Stop (Enter)", id="stop", variant="error")

    def on_mount(self) -> None:
        self._start_time = time.monotonic()
        self.set_interval(1, self._tick)
        self._start_pipeline()

    def _start_pipeline(self) -> None:
        app = self.app
        self._pipeline = TranscriptionPipeline(
            workspace_root=app.workspace_root,
            session_id=app.session_id,
            config=app.config,
            on_segment=self._on_segment,
            on_phase_summary=self._on_phase_summary,
            on_error=self._on_error,
        )
        self._pipeline.start()

    def _on_segment(self, segment: PipelineSegment) -> None:
        def update():
            self.transcript_lines.append(f"[{segment.start:.1f}s] {segment.speaker}: {segment.text}")
        self.app.call_from_thread(update)

    def _on_phase_summary(self, path: Path) -> None:
        def update():
            self.app.phase_summaries.append(path)
            log = self.query_one("#transcript", Log)
            log.write_line(f"[Phase summary saved: {path.name}]")
        self.app.call_from_thread(update)

    def _on_error(self, error: Exception) -> None:
        def update():
            log = self.query_one("#transcript", Log)
            log.write_line(f"[Error: {error}]")
        self.app.call_from_thread(update)

    def _tick(self) -> None:
        self.elapsed_seconds = int(time.monotonic() - self._start_time)

    def watch_elapsed_seconds(self, elapsed: int) -> None:
        minutes, seconds = divmod(elapsed, 60)
        self.query_one("#timer", Static).update(f"{minutes:02d}:{seconds:02d}")
        interval = self.app.config.phase_interval_seconds
        remaining = max(0, interval - (elapsed % interval))
        m, s = divmod(remaining, 60)
        self.query_one("#countdown", Static).update(f"Next summary in {m:02d}:{s:02d}")

    def watch_transcript_lines(self, lines: list[str]) -> None:
        log = self.query_one("#transcript", Log)
        log.clear()
        for line in lines[-100:]:
            log.write_line(line)

    def action_stop(self) -> None:
        self._stop()

    def action_mark(self) -> None:
        self.transcript_lines.append(f"[MARK at {self.elapsed_seconds}s]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "stop":
            self._stop()

    def _stop(self) -> None:
        if self._pipeline is None:
            return
        try:
            duration = self._pipeline.stop()
        except Exception as e:
            self._on_error(e)
            duration = self.elapsed_seconds
        self.app.duration_seconds = duration
        update_recording_complete(self.app.workspace_root, self.app.session_id, duration)
        try:
            summary_path = self._pipeline.generate_final_summary()
            self.app.summary_path = summary_path
        except Exception as e:
            self._on_error(e)
        self.app.push_screen("summary")
