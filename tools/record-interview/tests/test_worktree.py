from subprocess import CalledProcessError

import pytest

from record_interview.worktree import WorktreeError, find_worktree_root, is_inside_worktree


def test_find_worktree_root_returns_git_root(mocker, tmp_path):
    expected = tmp_path / "repo"
    expected.mkdir()
    mocker.patch(
        "subprocess.run",
        return_value=mocker.MagicMock(stdout=str(expected) + "\n", returncode=0),
    )
    assert find_worktree_root() == expected


def test_find_worktree_root_raises_when_not_git(mocker):
    mocker.patch(
        "subprocess.run",
        side_effect=CalledProcessError(128, "git", stderr="not a git repository"),
    )
    with pytest.raises(WorktreeError):
        find_worktree_root()


def test_is_inside_worktree_true(mocker, tmp_path):
    mocker.patch(
        "subprocess.run",
        return_value=mocker.MagicMock(stdout=str(tmp_path) + "\n", returncode=0),
    )
    assert is_inside_worktree() is True


def test_is_inside_worktree_false(mocker):
    mocker.patch(
        "subprocess.run",
        side_effect=CalledProcessError(128, "git", stderr="not a git repository"),
    )
    assert is_inside_worktree() is False


def test_find_worktree_root_accepts_start_path(mocker, tmp_path):
    mocker.patch(
        "subprocess.run",
        return_value=mocker.MagicMock(stdout=str(tmp_path) + "\n", returncode=0),
    )
    assert find_worktree_root(str(tmp_path / "subdir")) == tmp_path
