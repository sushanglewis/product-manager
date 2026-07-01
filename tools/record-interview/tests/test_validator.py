import pytest

from record_interview.worktree import WorktreeError
from record_interview.validator import validate_session_id, resolve_workspace_root


def test_validate_session_id_rejects_empty():
    with pytest.raises(ValueError, match="session_id is required"):
        validate_session_id("")


def test_validate_session_id_rejects_invalid_format():
    with pytest.raises(ValueError, match="invalid format"):
        validate_session_id("2026-06-27 hello world")


def test_validate_session_id_accepts_valid():
    assert validate_session_id("2026-06-27-stakeholder-checkout") == "2026-06-27-stakeholder-checkout"


def test_resolve_workspace_root_prefers_git_worktree(mocker, tmp_path):
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    mocker.patch(
        "record_interview.validator.find_worktree_root",
        return_value=worktree,
    )
    assert resolve_workspace_root(str(tmp_path / "subdir")) == worktree


def test_resolve_workspace_root_falls_back_to_lincoln_root(mocker, tmp_path):
    (tmp_path / "recordings").mkdir()
    (tmp_path / "interviews").mkdir()
    (tmp_path / ".claude").mkdir()
    mocker.patch(
        "record_interview.validator.find_worktree_root",
        side_effect=WorktreeError("not a git worktree"),
    )
    assert resolve_workspace_root(str(tmp_path / "subdir")) == tmp_path


def test_resolve_workspace_root_raises_when_not_found(mocker, tmp_path):
    mocker.patch(
        "record_interview.validator.find_worktree_root",
        side_effect=WorktreeError("not a git worktree"),
    )
    with pytest.raises(FileNotFoundError, match="Lincoln workspace root not found"):
        resolve_workspace_root(str(tmp_path))
