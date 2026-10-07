"""One agent write under the policy: tier → confirm → apply → journal.

Shared by the HTTP guard (``web_api/agent_guard.py``) and the MCP tools
(``mcp_server.py``) so both enforce ``core/agent_policy`` the same way:

1. ``begin`` resolves the tier (T3 raises ``AgentForbidden``), snapshots the
   entity kinds the action may touch and, for T2, spends a matching
   confirmation or raises ``ConfirmationRequired`` with a fresh one.
2. The caller applies the write.
3. ``finish`` snapshots again and journals the diff; a write that changed
   nothing refunds a spent confirmation. ``abort`` refunds after a failure.

``guarded`` wraps the three steps for synchronous callers.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

from nblane.core import agent_journal, agent_policy

_logger = logging.getLogger(__name__)
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
    """Check the policy and snapshot; raises before anything is written."""
    tier = agent_policy.tier_for(action, count)
    if tier == agent_policy.T3:
        raise AgentForbidden(action)
    before: agent_journal.Snapshot | None = None
    if kinds:
        try:
            agent_journal.prepare(pdir, kinds)
            before = agent_journal.snapshot(pdir, kinds)
        except Exception:
            _logger.warning("agent journal snapshot failed on %s", pdir.name, exc_info=True)
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
    return AgentWrite(pdir, actor, action, tier, tuple(kinds), before, summary, spent, store)


def abort(write: AgentWrite) -> None:
    """The write failed: give a spent confirmation back."""
    if write.spent is not None:
        agent_policy.refund(write.spent, write.store)


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


def finish(write: AgentWrite) -> dict[str, Any] | None:
    """Journal what the write changed; returns the entry (or None)."""
    changes: list[dict[str, Any]] = []
    if write.before is not None:
        try:
            after = agent_journal.snapshot(write.pdir, write.kinds)
            changes = agent_journal.diff(write.before, after)
        except Exception:
            _logger.warning("agent journal diff failed on %s", write.pdir.name, exc_info=True)
    if not changes:
        abort(write)
        return None
    try:
        return agent_journal.record(
            write.pdir,
            actor=write.actor,
            action=write.action,
            tier=write.tier,
            summary=_with_created_title(write.summary, changes),
            changes=changes,
            confirm_id=write.spent.confirm_id if write.spent else "",
        )
    except Exception:
        _logger.warning("agent journal write failed for %s on %s", write.action, write.pdir.name, exc_info=True)
        return None


def guarded(
    pdir: Path,
    apply: Callable[[], _T],
    **kwargs: Any,
) -> tuple[_T, AgentWrite, dict[str, Any] | None]:
    """``begin`` → *apply* → ``finish`` for synchronous callers."""
    write = begin(pdir, **kwargs)
    try:
        value = apply()
    except BaseException:
        abort(write)
        raise
    return value, write, finish(write)
