"""Background push of the data repository (core/git_backup.py)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from nblane.core import git_backup


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, text=True, capture_output=True
    ).stdout.strip()


@pytest.fixture()
def repos(tmp_path: Path):
    remote = tmp_path / "remote.git"
    _git(tmp_path, "init", "-q", "--bare", str(remote))
    work = tmp_path / "data"
    work.mkdir()
    _git(work, "init", "-q", "-b", "main")
    _git(work, "config", "user.email", "t@example.com")
    _git(work, "config", "user.name", "t")
    _git(work, "remote", "add", "origin", str(remote))
    (work / "seed.txt").write_text("seed\n", encoding="utf-8")
    _git(work, "add", "seed.txt")
    _git(work, "commit", "-qm", "seed")
    _git(work, "push", "-q", "-u", "origin", "main")
    env = {"NBLANE_DATA_GIT_AUTOCOMMIT": "1", "NBLANE_DATA_GIT_AUTOPUSH": "1"}
    with patch.dict(os.environ, env):
        yield work, remote
    git_backup.disable_background_push()
    git_backup._push_state.clear()


def test_sync_push_by_default(repos) -> None:
    work, remote = repos
    (work / "a.txt").write_text("a\n", encoding="utf-8")
    result = git_backup.record_change([work / "a.txt"], action="add a")
    assert result.committed and result.pushed and not result.push_queued
    assert _git(remote, "rev-parse", "main") == _git(work, "rev-parse", "HEAD")


def test_background_push_returns_before_push_and_catches_up(repos) -> None:
    work, remote = repos
    git_backup.enable_background_push()
    (work / "b.txt").write_text("b\n", encoding="utf-8")
    result = git_backup.record_change([work / "b.txt"], action="add b")
    assert result.committed and result.push_queued and not result.pushed
    assert git_backup.wait_for_pushes()
    assert _git(remote, "rev-parse", "main") == _git(work, "rev-parse", "HEAD")
    state = next(iter(git_backup.push_status().values()))
    assert state["last_error"] == "" and state["last_ok_at"]


def test_background_push_failure_is_recorded_not_raised(repos, tmp_path: Path) -> None:
    work, _remote = repos
    _git(work, "remote", "set-url", "origin", str(tmp_path / "missing.git"))
    git_backup.enable_background_push()
    (work / "c.txt").write_text("c\n", encoding="utf-8")
    result = git_backup.record_change([work / "c.txt"], action="add c")
    assert result.committed and result.push_queued
    assert git_backup.wait_for_pushes()
    state = next(iter(git_backup.push_status().values()))
    assert state["last_error"]


def test_startup_pushes_commits_left_unpushed(repos) -> None:
    work, remote = repos
    (work / "d.txt").write_text("d\n", encoding="utf-8")
    _git(work, "add", "d.txt")
    _git(work, "commit", "-qm", "offline commit")
    git_backup.enable_background_push(work)
    assert git_backup.wait_for_pushes()
    assert _git(remote, "rev-parse", "main") == _git(work, "rev-parse", "HEAD")


def test_git_timeout_becomes_failed_result(tmp_path: Path) -> None:
    def boom(*_a, **_k):
        raise subprocess.TimeoutExpired(cmd="git push", timeout=1)

    with patch("nblane.core.git_backup.subprocess.run", side_effect=boom):
        result = git_backup._run_git(tmp_path, ["push"], timeout=1)
    assert result.returncode != 0
    assert "timed out" in result.stderr
