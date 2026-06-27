import pytest
from pathlib import Path
from record_interview.validator import validate_session_id, resolve_workspace_root


def test_validate_session_id_rejects_empty():
    with pytest.raises(ValueError, match="session_id is required"):
        validate_session_id("")


def test_validate_session_id_rejects_invalid_chars():
    with pytest.raises(ValueError, match="invalid characters"):
        validate_session_id("2026-06-27 hello world")


def test_validate_session_id_accepts_valid():
    assert validate_session_id("2026-06-27-stakeholder-checkout") == "2026-06-27-stakeholder-checkout"


def test_resolve_workspace_root_finds_lincoln_root(tmp_path):
    (tmp_path / "recordings").mkdir()
    (tmp_path / "interviews").mkdir()
    (tmp_path / ".claude").mkdir()
    assert resolve_workspace_root(str(tmp_path / "subdir")) == tmp_path


def test_resolve_workspace_root_raises_when_not_found(tmp_path):
    with pytest.raises(FileNotFoundError, match="Lincoln workspace root not found"):
        resolve_workspace_root(str(tmp_path))
