"""Optional Git backup hook for file-backed nblane data.

Commits are always local and synchronous so every recorded write has a
history entry. Pushing is the slow part (a network round trip of seconds):
long-lived web processes call :func:`enable_background_push` so a push runs
on a worker thread, coalesced per repository, and a save request never
waits on the network. CLI runs keep the synchronous push.
"""

from __future__ import annotations

import contextvars
from contextlib import contextmanager
from collections.abc import Iterator
import os
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

GIT_TIMEOUT_SECONDS = 30
PUSH_TIMEOUT_SECONDS = 60

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
    # The push was handed to the background worker (see push_status()).
    push_queued: bool = False

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


def _run_git(
    repo: Path,
    args: list[str],
    *,
    timeout: float = GIT_TIMEOUT_SECONDS,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            ["git", *args], 124, "", f"git {args[0]} timed out after {timeout:.0f}s"
        )


# --- background push ----------------------------------------------------------

_background_push = False
_push_lock = threading.Lock()
_push_state: dict[str, dict[str, Any]] = {}


def enable_background_push(root: Path | None = None) -> None:
    """Push commits on a worker thread from now on (web processes only).

    When *root* is a data repository and autopush is on, schedule one push
    right away so commits left unpushed by a previous process (restart,
    network outage) catch up.
    """
    global _background_push
    _background_push = True
    if root is None or not autopush_enabled():
        return
    repo = _find_git_root(root) if root.exists() else None
    if repo is not None:
        _schedule_push(repo)


def disable_background_push() -> None:
    """Return to synchronous pushes (test helper)."""
    global _background_push
    _background_push = False


def push_status() -> dict[str, dict[str, Any]]:
    """Per-repository state of the background pusher (for status pages)."""
    with _push_lock:
        return {
            repo: {key: value for key, value in state.items() if key != "thread"}
            for repo, state in _push_state.items()
        }


def wait_for_pushes(timeout: float = 10.0) -> bool:
    """Block until no background push is running or pending (test helper)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with _push_lock:
            busy = any(state.get("running") for state in _push_state.values())
        if not busy:
            return True
        time.sleep(0.01)
    return False


def _schedule_push(repo: Path) -> None:
    """Ask for a push of *repo*; concurrent requests coalesce into one."""
    key = str(repo)
    with _push_lock:
        state = _push_state.setdefault(key, {"running": False, "pending": False})
        state["pending"] = True
        if state["running"]:
            return
        state["running"] = True
    worker = threading.Thread(
        target=_push_worker, args=(repo,), name="nblane-git-push", daemon=True
    )
    worker.start()


def _push_worker(repo: Path) -> None:
    key = str(repo)
    while True:
        with _push_lock:
            state = _push_state[key]
            if not state["pending"]:
                state["running"] = False
                return
            state["pending"] = False
        started = time.time()
        try:
            push = _run_git(repo, ["push"], timeout=PUSH_TIMEOUT_SECONDS)
            error = "" if push.returncode == 0 else (push.stderr or push.stdout).strip()
        except Exception as exc:  # never let the worker die with running=True
            error = str(exc)
        with _push_lock:
            state = _push_state[key]
            state["last_attempt_at"] = started
            if error:
                state["last_error"] = error[-500:]
            else:
                state["last_error"] = ""
                state["last_ok_at"] = time.time()


def _relative_paths(repo: Path, paths: Iterable[Path]) -> list[str]:
    out: list[str] = []
    for path in paths:
        try:
            rel = path.resolve().relative_to(repo)
        except ValueError:
            continue
        out.append(str(rel))
    return out


_deferred_changes: contextvars.ContextVar[list[Path] | None] = contextvars.ContextVar(
    "nblane_deferred_backup", default=None,
)


@contextmanager
def defer_changes(action: str) -> Iterator[None]:
    """Back up a multi-file operation only after it fully succeeds."""
    if _deferred_changes.get() is not None:
        yield
        return
    paths: list[Path] = []
    token = _deferred_changes.set(paths)
    try:
        yield
    except BaseException:
        raise
    else:
        _deferred_changes.reset(token)
        token = None
        if paths:
            record_change(list(dict.fromkeys(paths)), action=action)
    finally:
        if token is not None:
            _deferred_changes.reset(token)


@contextmanager
def skip_changes() -> Iterator[None]:
    """Suppress backups for writes inside the block (e.g. editor autosave).

    Nothing is lost: the files stay modified in the working tree, so the next
    recorded change of the same paths commits the accumulated diff.
    """
    token = _deferred_changes.set([])
    try:
        yield
    finally:
        _deferred_changes.reset(token)


def record_change(
    paths: Iterable[Path],
    *,
    action: str,
) -> GitBackupResult:
    """Commit and optionally push changed paths when backup is enabled."""
    path_list = [p for p in paths]
    deferred = _deferred_changes.get()
    if deferred is not None:
        deferred.extend(path_list)
        return GitBackupResult(enabled=autocommit_enabled(), skipped_reason="deferred")
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
    if _background_push:
        _schedule_push(repo)
        return _append_result(
            GitBackupResult(
                enabled=True,
                committed=True,
                commit_hash=commit_hash,
                push_queued=True,
            )
        )
    push = _run_git(repo, ["push"], timeout=PUSH_TIMEOUT_SECONDS)
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
