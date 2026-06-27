from __future__ import annotations

import re
from pathlib import Path

SESSION_ID_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9-]+$")


def validate_session_id(session_id: str) -> str:
    if not session_id:
        raise ValueError("session_id is required")
    if not SESSION_ID_PATTERN.match(session_id):
        raise ValueError(
            f"session_id '{session_id}' has invalid characters. "
            "Expected format: YYYY-MM-DD-descriptive-name"
        )
    return session_id


def resolve_workspace_root(start_path: str | None = None) -> Path:
    path = Path(start_path or ".").resolve()
    for current in [path, *path.parents]:
        if all((current / d).is_dir() for d in ("recordings", "interviews", ".claude")):
            return current
    raise FileNotFoundError("Lincoln workspace root not found: missing recordings/, interviews/, or .claude/")
