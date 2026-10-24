"""Shared commit and cooperative-cancellation primitives for Reader writes."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import nullcontext
from typing import Any, TypeVar

from nblane.core import agent_journal, agent_ops

_T = TypeVar("_T")
Commit = Callable[..., Any]


class ReaderCancelled(RuntimeError):
    """A worker observed cancellation before its next commit segment."""


def checkpoint(cancel_callback: Callable[[], bool] | None) -> None:
    if cancel_callback is not None and cancel_callback():
        raise ReaderCancelled("Reader action cancelled.")


def direct_commit(apply: Callable[[], _T], kinds: tuple[str, ...] | None = None) -> _T:
    return apply()


def synchronous_commit(write: agent_ops.AgentWrite) -> Commit:
    """Refresh every kind immediately before its first synchronous commit."""
    base_kinds = tuple(write.kinds)
    captured: set[str] = set()

    def commit(apply: Callable[[], _T], kinds: tuple[str, ...] | None = None) -> _T:
        selected = tuple(dict.fromkeys((*base_kinds, *(kinds or ()))))
        additional = tuple(kind for kind in selected if kind not in captured)
        if additional:
            try:
                agent_journal.prepare(write.pdir, additional)
                extra = agent_journal.snapshot(write.pdir, additional)
            except Exception as exc:
                raise agent_ops.AgentJournalError(
                    f"Agent journal dynamic pre-write snapshot failed for {write.action}."
                ) from exc
            if write.before is None:
                write.before = {}
            write.before.update(extra)
            write.kinds = tuple(dict.fromkeys((*write.kinds, *additional)))
            captured.update(additional)
        return apply()

    return commit


def worker_commit(
    write: agent_ops.AgentWrite,
    cancel_callback: Callable[[], bool] | None,
    *,
    boundary_lock: Any | None = None,
    set_committing: Callable[[bool], None] | None = None,
) -> Commit:
    """Linearize cancellation and each short worker-side write segment."""
    base_kinds = tuple(write.kinds)

    def commit(apply: Callable[[], _T], kinds: tuple[str, ...] | None = None) -> _T:
        with boundary_lock or nullcontext():
            checkpoint(cancel_callback)
            if set_committing is not None:
                set_committing(True)
        try:
            agent_ops.capture_before(write, tuple(kinds) if kinds is not None else base_kinds)
            prior_committed = write.write_committed
            try:
                value = apply()
            except BaseException:
                try:
                    agent_ops.finish(write, refund_noop=False)
                except agent_ops.AgentJournalError:
                    write.write_committed = True
                raise
            write.write_committed = True
            entry = agent_ops.finish(write, refund_noop=False)
            if entry is None:
                write.write_committed = prior_committed
            return value
        finally:
            if set_committing is not None:
                with boundary_lock or nullcontext():
                    set_committing(False)

    return commit


def commit_or_direct(commit: Commit | None) -> Commit:
    return commit if commit is not None else direct_commit


__all__ = [
    "Commit",
    "ReaderCancelled",
    "checkpoint",
    "commit_or_direct",
    "direct_commit",
    "synchronous_commit",
    "worker_commit",
]
