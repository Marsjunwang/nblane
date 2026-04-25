"""Optional Git backup hook for file-backed nblane data."""

from __future__ import annotations

import contextvars
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

_actor_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "nblane_git_actor",
    default="cli",
)
_results_var: contextvars.ContextVar[list["GitBackupResult"] | None] = (
    contextvars.ContextVar("nblane_git_results", default=None)
)


@dataclass(frozen=True)
class GitBackupResult:
    """Outcome for one optional Git backup operation."""

    enabled: bool
    committed: bool = False
    pushed: bool = False
    skipped_reason: str = ""
    error: str = ""
    push_error: str = ""
    commit_hash: str = ""

    @property
    def has_warning(self) -> bool:
        """True when the write succeeded but backup needs attention."""
        return bool(self.error or self.push_error)


def set_actor(actor: str) -> None:
    """Set the actor used in subsequent commit messages."""
    clean = (actor or "unknown").strip() or "unknown"
    _actor_var.set(clean)


def start_operation(actor: str | None = None) -> None:
    """Start collecting backup results for a web rerun/request."""
    if actor:
        set_actor(actor)
    _results_var.set([])


def consume_results() -> list[GitBackupResult]:
    """Return and clear results collected in the current operation."""
    results = _results_var.get()
    if results is None:
        return []
    _results_var.set([])
    return list(results)


def _enabled(name: str) -> bool:
    raw = os.getenv(name, "").strip().lower()
    return raw in ("1", "true", "yes", "on")


def autocommit_enabled() -> bool:
    """Whether data writes should commit to Git automatically."""
    return _enabled("NBLANE_DATA_GIT_AUTOCOMMIT")


def autopush_enabled() -> bool:
    """Whether successful commits should also be pushed."""
    return _enabled("NBLANE_DATA_GIT_AUTOPUSH")


def _append_result(result: GitBackupResult) -> GitBackupResult:
    results = _results_var.get()
    if results is not None:
        results.append(result)
    return result


def _find_git_root(path: Path) -> Path | None:
    """Find nearest parent containing a .git directory."""
    cur = path.resolve()
    if cur.is_file():
        cur = cur.parent
    for candidate in (cur, *cur.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def _run_git(repo: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _relative_paths(repo: Path, paths: Iterable[Path]) -> list[str]:
    out: list[str] = []
    for path in paths:
        try:
            rel = path.resolve().relative_to(repo)
        except ValueError:
            continue
        out.append(str(rel))
    return out


def record_change(
    paths: Iterable[Path],
    *,
    action: str,
) -> GitBackupResult:
    """Commit and optionally push changed paths when backup is enabled."""
    path_list = [p for p in paths]
    if not autocommit_enabled():
        return _append_result(
            GitBackupResult(
                enabled=False,
                skipped_reason="NBLANE_DATA_GIT_AUTOCOMMIT is disabled",
            )
        )
    if not path_list:
        return _append_result(
            GitBackupResult(enabled=True, skipped_reason="no paths")
        )
    repo = _find_git_root(path_list[0])
    if repo is None:
        return _append_result(
            GitBackupResult(
                enabled=True,
                skipped_reason="no git repository found",
            )
        )
    rels = _relative_paths(repo, path_list)
    if not rels:
        return _append_result(
            GitBackupResult(
                enabled=True,
                skipped_reason="paths are outside git repository",
            )
        )
    status = _run_git(repo, ["status", "--porcelain", "--", *rels])
    if status.returncode != 0:
        return _append_result(
            GitBackupResult(
                enabled=True,
                error=(status.stderr or status.stdout).strip(),
            )
        )
    if not status.stdout.strip():
        return _append_result(
            GitBackupResult(enabled=True, skipped_reason="no git changes")
        )
    add = _run_git(repo, ["add", "--", *rels])
    if add.returncode != 0:
        return _append_result(
            GitBackupResult(
                enabled=True,
                error=(add.stderr or add.stdout).strip(),
            )
        )
    actor = _actor_var.get()
    message = f"nblane: {action} by {actor}"
    commit = _run_git(repo, ["commit", "-m", message, "--", *rels])
    if commit.returncode != 0:
        return _append_result(
            GitBackupResult(
                enabled=True,
                error=(commit.stderr or commit.stdout).strip(),
            )
        )
    rev = _run_git(repo, ["rev-parse", "--short", "HEAD"])
    commit_hash = rev.stdout.strip() if rev.returncode == 0 else ""
    if not autopush_enabled():
        return _append_result(
            GitBackupResult(
                enabled=True,
                committed=True,
                commit_hash=commit_hash,
            )
        )
    push = _run_git(repo, ["push"])
    if push.returncode != 0:
        return _append_result(
            GitBackupResult(
                enabled=True,
                committed=True,
                commit_hash=commit_hash,
                push_error=(push.stderr or push.stdout).strip(),
            )
        )
    return _append_result(
        GitBackupResult(
            enabled=True,
            committed=True,
            pushed=True,
            commit_hash=commit_hash,
        )
    )
