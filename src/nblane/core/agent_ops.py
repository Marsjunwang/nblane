"""One agent write under the policy: tier → confirm → apply → journal.

Shared by the HTTP guard (``web_api/agent_guard.py``) and the MCP tools
(``mcp_server.py``) so both enforce ``core/agent_policy`` the same way:

1. ``begin`` resolves the tier (T3 raises ``AgentForbidden``), snapshots the
   entity kinds the action may touch and, for T2, spends a matching
   confirmation or raises ``ConfirmationRequired`` with a fresh one.
2. The caller applies the write.
3. ``finish`` strictly snapshots again and journals the diff; a write that
   changed nothing refunds a spent confirmation. Snapshot/journal failures
   raise ``AgentJournalError`` instead of silently claiming a safe write.

``reserve`` defers snapshots to async workers. ``guarded`` wraps the three
steps for synchronous callers.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

from nblane.core import agent_journal, agent_policy

_T = TypeVar("_T")

Describe = Callable[[agent_journal.Snapshot], str]


class AgentForbidden(Exception):
    """The action is web-UI only (T3)."""

    def __init__(self, action: str) -> None:
        super().__init__(action)
        self.action = action


class ConfirmationRequired(Exception):
    """T2 without a valid confirmation; nothing was written."""

    def __init__(self, pending: agent_policy.PendingConfirmation, *, invalid: bool) -> None:
        super().__init__(pending.summary)
        self.pending = pending
        self.invalid = invalid


class AgentJournalError(RuntimeError):
    """A snapshot or journal operation failed; the write is not claimed safe."""


@dataclass
class AgentWrite:
    pdir: Path
    actor: str
    action: str
    tier: str
    kinds: tuple[str, ...]
    before: agent_journal.Snapshot | None
    summary: str
    spent: agent_policy.PendingConfirmation | None
    store: agent_policy.ConfirmStore | None
    write_committed: bool = False
    snapshot_taken: bool = False


def _authorize(
    pdir: Path,
    *,
    actor: str,
    action: str,
    kinds: tuple[str, ...],
    fingerprint: str,
    describe: Describe,
    count: int = 1,
    confirm_id: str = "",
    store: agent_policy.ConfirmStore | None = None,
    snapshot: bool,
) -> AgentWrite:
    tier = agent_policy.tier_for(action, count)
    if tier == agent_policy.T3:
        raise AgentForbidden(action)
    before: agent_journal.Snapshot | None = None
    if snapshot and kinds:
        try:
            agent_journal.prepare(pdir, kinds)
            before = agent_journal.snapshot(pdir, kinds)
        except Exception as exc:
            raise AgentJournalError(
                f"Agent journal pre-write snapshot failed for {action}."
            ) from exc
    summary = describe(before or {})
    spent: agent_policy.PendingConfirmation | None = None
    if tier == agent_policy.T2:
        supplied = str(confirm_id or "").strip()
        spent = (
            agent_policy.take(supplied, actor=actor, fingerprint=fingerprint, store=store)
            if supplied
            else None
        )
        if spent is None:
            pending = agent_policy.issue(
                actor=actor,
                profile=pdir.name,
                action=action,
                summary=summary,
                fingerprint=fingerprint,
                store=store,
            )
            raise ConfirmationRequired(pending, invalid=bool(supplied))
    return AgentWrite(
        pdir,
        actor,
        action,
        tier,
        tuple(kinds),
        before,
        summary,
        spent,
        store,
        snapshot_taken=snapshot,
    )


def begin(
    pdir: Path,
    *,
    actor: str,
    action: str,
    kinds: tuple[str, ...],
    fingerprint: str,
    describe: Describe,
    count: int = 1,
    confirm_id: str = "",
    store: agent_policy.ConfirmStore | None = None,
) -> AgentWrite:
    """Check the policy and take the synchronous pre-write snapshot."""
    return _authorize(
        pdir,
        actor=actor,
        action=action,
        kinds=kinds,
        fingerprint=fingerprint,
        describe=describe,
        count=count,
        confirm_id=confirm_id,
        store=store,
        snapshot=True,
    )


def reserve(
    pdir: Path,
    *,
    actor: str,
    action: str,
    kinds: tuple[str, ...],
    fingerprint: str,
    describe: Describe,
    count: int = 1,
    confirm_id: str = "",
    store: agent_policy.ConfirmStore | None = None,
) -> AgentWrite:
    """Authorize an async job without taking its snapshot on the request thread."""
    return _authorize(
        pdir,
        actor=actor,
        action=action,
        kinds=kinds,
        fingerprint=fingerprint,
        describe=describe,
        count=count,
        confirm_id=confirm_id,
        store=store,
        snapshot=False,
    )


def capture_before(write: AgentWrite, kinds: tuple[str, ...] | None = None) -> None:
    """Capture the worker-local snapshot immediately before one commit segment."""
    selected = tuple(kinds) if kinds is not None else write.kinds
    try:
        if selected:
            agent_journal.prepare(write.pdir, selected)
        before = agent_journal.snapshot(write.pdir, selected) if selected else {}
    except Exception as exc:
        raise AgentJournalError(
            f"Agent journal pre-commit snapshot failed for {write.action}."
        ) from exc
    write.kinds = selected
    write.before = before
    write.snapshot_taken = True


def abort(write: AgentWrite) -> None:
    """Release an unused reservation; committed work never refunds confirmation."""
    if write.spent is not None and not write.write_committed:
        agent_policy.refund(write.spent, write.store)
    write.spent = None


def _with_created_title(base: str, changes: list[dict[str, Any]]) -> str:
    """Append the created entity's title when the summary named none."""
    if "「" in base:
        return base
    created = next((c for c in changes if c.get("before") is None and c.get("after")), None)
    title = entity_title(created.get("after")) if created else ""
    return f"{base}「{title}」" if title else base


def entity_title(state: dict[str, Any] | None) -> str:
    if not state:
        return ""
    item = state.get("task") or state.get("item") or {}
    for key in ("title", "label", "summary", "habit_id", "date"):
        value = str(item.get(key, "") or "").strip()
        if value:
            return value
    return ""


def finish(write: AgentWrite, *, refund_noop: bool = True) -> dict[str, Any] | None:
    """Strictly diff and journal one completed write; never hide journaling errors."""
    if not write.snapshot_taken:
        if write.kinds:
            raise AgentJournalError(
                f"Agent journal pre-commit snapshot is missing for {write.action}."
            )
        abort(write)
        return None
    try:
        after = agent_journal.snapshot(write.pdir, write.kinds) if write.kinds else {}
        changes = agent_journal.diff(write.before or {}, after)
    except Exception as exc:
        raise AgentJournalError(
            f"Agent journal post-commit diff failed for {write.action}."
        ) from exc
    if not changes:
        if refund_noop:
            abort(write)
        return None
    write.write_committed = True
    confirm_id = write.spent.confirm_id if write.spent else ""
    try:
        entry = agent_journal.record(
            write.pdir,
            actor=write.actor,
            action=write.action,
            tier=write.tier,
            summary=_with_created_title(write.summary, changes),
            changes=changes,
            confirm_id=confirm_id,
        )
    except Exception as exc:
        raise AgentJournalError(
            f"Agent journal record failed after the write for {write.action}."
        ) from exc
    write.spent = None
    return entry


def finish_after_failure(write: AgentWrite) -> None:
    """Journal partial changes from a failed write before releasing its reservation."""
    try:
        finish(write, refund_noop=False)
    except AgentJournalError:
        write.write_committed = True
        abort(write)
        raise
    abort(write)


def guarded(
    pdir: Path,
    apply: Callable[[], _T],
    **kwargs: Any,
) -> tuple[_T, AgentWrite, dict[str, Any] | None]:
    """``begin`` → *apply* → strict ``finish`` for synchronous callers."""
    write = begin(pdir, **kwargs)
    try:
        value = apply()
    except BaseException:
        finish_after_failure(write)
        raise
    return value, write, finish(write)
