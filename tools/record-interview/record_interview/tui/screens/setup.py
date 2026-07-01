from __future__ import annotations

import asyncio

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static

from record_interview.checks import request_microphone_permission, run_setup_checks
from record_interview.metadata import build_metadata, write_metadata


class SetupScreen(Screen):
    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self) -> None:
        super().__init__()
        self._checks: dict[str, tuple[bool, str]] = {}
        self._requested_permission = False

    def compose(self) -> ComposeResult:
        yield Static("Lincoln Interview Recorder", id="title")
        yield Static("Checking environment...", id="status")
        yield Vertical(id="checks")
        with Horizontal(id="actions"):
            yield Button("Start Recording", id="start", variant="primary", disabled=True)
            yield Button("Exit", id="exit")

    def on_mount(self) -> None:
        self._run_checks()

    def _run_checks(self) -> None:
        app = self.app
        self._checks = run_setup_checks(app.config)
        mic_ready, _ = self._checks.get("microphone", (False, ""))
        if not mic_ready and not self._requested_permission:
            self._requested_permission = True
            status = self.query_one("#status", Static)
            status.update("Requesting microphone permission...")
            asyncio.create_task(self._request_permission_and_recheck())
            return
        self._render_checks()

    async def _request_permission_and_recheck(self) -> None:
        try:
            granted = await asyncio.to_thread(request_microphone_permission)
        except Exception:  # noqa: BLE001
            granted = False
        if granted:
            self._checks = run_setup_checks(self.app.config)
        self._render_checks()

    def _render_checks(self) -> None:
        container = self.query_one("#checks", Vertical)
        container.remove_children()
        all_ready = True
        for name, (ready, message) in self._checks.items():
            icon = "✓" if ready else "✗"
            label = Static(f"{icon} {name.capitalize()}: {message}", classes="check-ok" if ready else "check-fail")
            container.mount(label)
            if not ready:
                all_ready = False
        self.query_one("#start", Button).disabled = not all_ready
        status = self.query_one("#status", Static)
        status.update("Ready to record" if all_ready else "Fix the issues above to continue")

    def _prepare_metadata(self) -> None:
        app = self.app
        metadata = build_metadata(
            session_id=app.session_id,
            design_id=app.design_id,
            topic=app.topic,
            branch=app.branch,
            transcription_model=app.config.transcription.model if app.config.transcription else None,
            diarization_model=app.config.diarization.model if app.config.diarization else None,
            summarization_model=app.config.summarization.model if app.config.summarization else None,
        )
        write_metadata(app.workspace_root, app.session_id, metadata)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start":
            self._prepare_metadata()
            self.app.push_screen("recording")
        elif event.button.id == "exit":
            self.app.exit(0)
