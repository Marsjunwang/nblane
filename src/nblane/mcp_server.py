"""MCP server: expose nblane profile context and policy-checked writes (stdio).

Resources are read-only. Every write tool runs through the same agent write
policy as the HTTP API (``core/agent_policy`` via ``core/agent_ops``):

- T1 daily ops (add/move a card, check in, capture to the inbox, growth log)
  apply directly and land in the undo journal (``recent_actions`` /
  ``undo_action``).
- T2 tools (``delete_kanban_card``, ``log_skill_evidence``) answer
  ``confirmation_required`` with a ``confirm_id`` first; the agent relays the
  summary, and only after the user agrees in the chat repeats the identical
  call with ``confirm_id``. Confirmations are shared across MCP processes
  (``FileConfirmStore``), so a sibling session can redeem them.
- ``submit_*_candidate`` still queue review items; ``run_validate`` /
  ``run_sync_check`` are read-only self-checks.

New tools return structured dicts and carry ``ToolAnnotations``; the
legacy tools keep their ``OK:``/``ERROR:`` string contract.

Environment:
  NBLANE_PROFILE — default profile name (optional if exactly one profile exists).
  NBLANE_MCP_ACTOR — journal / confirmation actor id (default ``mcp``).
  NBLANE_AGENT_STATE_DIR — where MCP confirmations live (see agent_policy).
  NBLANE_ROOT — repo root override (see nblane.core.paths).
  NBLANE_CONTEXT_MODE — chat | review | write | plan for profile://context.
  NBLANE_GAP_USE_LLM — if ``1`` / ``true``, enable LLM routing in gap analysis.
"""

from __future__ import annotations

import os
import urllib.parse
from collections import Counter
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from nblane.core import agent_journal, agent_ops, agent_policy
from nblane.core.agent_activity import (
    activity_items_for_page,
    activity_summary,
    append_activity_item,
)
from nblane.core.context import generate
from nblane.core.crystallize import write_method_draft
from nblane.core.agent_tasks import (
    AGENT_TASK_STATUSES,
    get_agent_task,
    load_agent_tasks,
    render_agent_handoff,
    submit_agent_task_candidate,
    update_agent_task_status,
)
from nblane.core.gap import analyze, format_text
from nblane.core.goals import (
    GOAL_STATUSES,
    current_goal,
    goal_for_agent_context,
    load_goal_book,
)
from nblane.core.growth_log import append_growth_log_row
from nblane.core.inbox import (
    Inbox,
    InboxItem,
    add_inbox_item,
    load_inbox,
    update_inbox,
)
from nblane.core.interaction import append_interaction_record
from nblane.core.io import (
    KANBAN_DOING,
    KANBAN_DONE,
    list_profiles,
    load_skill_tree_raw,
    parse_kanban,
    profile_dir,
)
from nblane.core.kanban_io import (
    KANBAN_QUEUE,
    KANBAN_SECTIONS,
    apply_kanban_reorder,
    ensure_kanban_task_ids,
    find_kanban_card,
    find_kanban_card_by_id,
    resolve_kanban_section,
    update_kanban,
)
from nblane.core.learning_log import load_learning_log, summarize_learning_log
from nblane.core import activity_log
from nblane.core.crystallize import _slug as _method_slug
from nblane.core.models import EVIDENCE_TYPES, KanbanTask
from nblane.core.paths import PROFILES_DIR
from nblane.core.profile_context import (
    north_star_context_from_identity,
    parse_identity_fields,
)
from nblane.core.profile_io import load_evidence_pool
from nblane.core.review_actions import (
    activity_item_from_review_candidate,
)
from nblane.core.skill_evidence_inline import add_inline_evidence
from nblane.core.status import STATUS_ICONS, count_nodes, lit_fraction
from nblane.core.sync import get_drifted_blocks
from nblane.core.validate import validate_one

_PROFILE_ENV_KEYS = ("NBLANE_PROFILE", "NBLANE_MCP_PROFILE")


def _truthy_env(name: str) -> bool:
    """Return True if env *name* is set to a truthy string."""
    v = os.getenv(name)
    if v is None:
        return False
    return v.strip().lower() in ("1", "true", "yes", "on")


def resolve_active_profile() -> tuple[str | None, str | None]:
    """Return ``(profile_name, None)`` or ``(None, error_message)``."""
    for key in _PROFILE_ENV_KEYS:
        raw = os.getenv(key)
        if raw is None or not str(raw).strip():
            continue
        name = str(raw).strip()
        p = profile_dir(name)
        if not p.is_dir():
            return (
                None,
                f"Profile {name!r} not found under {PROFILES_DIR}.",
            )
        return (name, None)

    names = list_profiles()
    if len(names) == 1:
        return (names[0], None)
    if not names:
        return (
            None,
            f"No profiles under {PROFILES_DIR}. "
            "Create one or set NBLANE_PROFILE.",
        )
    return (
        None,
        "Set NBLANE_PROFILE to choose a profile "
        f"(found: {', '.join(names)}).",
    )


def _load_agent_profile_dict(pdir: Path) -> dict:
    """Load agent-profile.yaml as a dict, or empty dict."""
    path = pdir / "agent-profile.yaml"
    if not path.exists():
        return {}
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {}


def build_summary_text(profile_name: str) -> str:
    """Tree summary, focus, and working-style preferences for MCP."""
    pdir = profile_dir(profile_name)
    lines: list[str] = [
        f"# Profile summary: {profile_name}",
        "",
    ]

    goal_text = goal_for_agent_context(current_goal(profile_name))
    if goal_text:
        lines.append("## Current Goal")
        lines.append(goal_text)
        lines.append("")

    tree = load_skill_tree_raw(pdir)
    if tree is None:
        lines.append("## Skill tree")
        lines.append("Not initialized (no skill-tree.yaml).")
    else:
        counts = count_nodes(tree)
        lines.append("## Skill tree")
        lines.append(f"- Lit: **{lit_fraction(counts)}**")
        for status, icon in STATUS_ICONS.items():
            n = counts.get(status, 0)
            if n > 0:
                lines.append(f"  - {icon} {status}: {n}")
    lines.append("")

    ap = _load_agent_profile_dict(pdir)
    uou = ap.get("understanding_of_user")
    if isinstance(uou, dict):
        focus = uou.get("current_focus")
        if isinstance(focus, list) and focus:
            lines.append("## Focus (agent-profile)")
            for item in focus:
                lines.append(f"- {item}")
            lines.append("")

    ws = ap.get("working_style")
    if isinstance(ws, dict):
        prefers = ws.get("prefers")
        avoids = ws.get("avoids")
        if (isinstance(prefers, list) and prefers) or (
            isinstance(avoids, list) and avoids
        ):
            lines.append("## Preferences (working_style)")
            if isinstance(prefers, list) and prefers:
                lines.append("**Prefers**")
                for item in prefers:
                    lines.append(f"- {item}")
            if isinstance(avoids, list) and avoids:
                lines.append("**Avoids**")
                for item in avoids:
                    lines.append(f"- {item}")
            lines.append("")

    sections = parse_kanban(profile_name)
    doing = sections.get(KANBAN_DOING) or []
    titles = [
        t.title.strip()
        for t in doing
        if t.title and t.title.strip() not in ("(empty)",)
    ]
    lines.append("## Kanban · Doing")
    if titles:
        for t in titles:
            lines.append(f"- {t}")
    else:
        lines.append("(none)")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _profile_text_resource(
    getter: str,
    builder: Callable[[str], str],
) -> str:
    """Shared error handling for profile-scoped resources."""
    name, err = resolve_active_profile()
    if err is not None:
        return f"ERROR [{getter}]: {err}\n"
    try:
        return builder(name)
    except FileNotFoundError as exc:
        return f"ERROR [{getter}]: {exc}\n"


def build_agent_tasks_text(profile_name: str) -> str:
    """Return a readable agent task queue for MCP clients."""

    doc = load_agent_tasks(profile_name)
    tasks = list(doc.get("tasks") or [])
    lines = [
        f"# Agent tasks: {profile_name}",
        "",
    ]
    if not tasks:
        lines.append("No agent tasks are queued for this profile.")
        return "\n".join(lines).rstrip() + "\n"
    for task in tasks:
        task_id = str(task.get("id") or "").strip()
        lines.extend(
            [
                f"## {task.get('title') or task_id}",
                f"- Task id: {task_id}",
                f"- Status: {task.get('status') or 'ready'}",
                f"- Target harness: {task.get('target_harness') or 'codex'}",
                f"- Role: {task.get('role') or 'researcher'}",
                f"- Activity item: {task.get('activity_item_id') or '(pending)'}",
                "",
            ]
        )
    lines.extend(
        [
            "Read one task with `agent://task/{task_id}` before working.",
            "Submit results with `submit_agent_task_candidate`.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def build_agent_task_handoff_text(profile_name: str, task_id: str) -> str:
    """Return one canonical agent task handoff for MCP clients."""

    task = get_agent_task(profile_name, task_id)
    if task is None:
        return f"ERROR [agent://task]: unknown agent task {task_id!r}\n"
    body = render_agent_handoff(task, profile=profile_name)
    task_yaml = yaml.dump(
        task,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    return (
        body.rstrip()
        + "\n\n## Agent Task YAML\n"
        + "```yaml\n"
        + task_yaml.rstrip()
        + "\n```\n"
    )


_INBOX_OPEN_STATUSES = ("inbox", "captured", "clarified")
_EVIDENCE_RECENT_LIMIT = 20
_ACTIVITY_PENDING_LIMIT = 10
_LEARNING_RECENT_LIMIT = 10


def build_goals_text(profile_name: str) -> str:
    """Goals summary with the same privacy contract as agent context."""
    pdir = profile_dir(profile_name)
    lines: list[str] = [f"# Goals: {profile_name}", ""]

    identity: dict[str, str] = {}
    skill_md = pdir / "SKILL.md"
    if skill_md.exists():
        identity = parse_identity_fields(
            skill_md.read_text(encoding="utf-8")
        )
    north_star = north_star_context_from_identity(identity, for_agent=True)
    lines.append("## North Star")
    if north_star:
        lines.append(north_star)
    else:
        lines.append("(not set)")
    lines.append("")

    book = load_goal_book(pdir)
    if not book.goals:
        lines.append("No goals recorded (goals.yaml missing or empty).")
        return "\n".join(lines).rstrip() + "\n"

    counts = Counter(goal.status for goal in book.goals)
    lines.append("## Status counts")
    for status in GOAL_STATUSES:
        count = counts.get(status, 0)
        if count:
            lines.append(f"- {status}: {count}")
    lines.append("")

    primary = book.primary()
    primary_text = goal_for_agent_context(primary)
    lines.append("## Primary goal")
    lines.append(
        primary_text if primary_text else "(none visible to agent context)"
    )
    lines.append("")

    primary_id = primary.id if primary is not None else ""
    visible_others: list[tuple[Any, str]] = []
    hidden = 0 if primary_text else (1 if primary is not None else 0)
    for goal in book.goals:
        if goal.id == primary_id:
            continue
        text = goal_for_agent_context(goal)
        if not text:
            hidden += 1
            continue
        visible_others.append((goal, text))
    if visible_others:
        lines.append("## Other goals visible to agent context")
        for goal, text in visible_others:
            heading = goal.title or goal.label or goal.id
            lines.append(f"### {heading} [{goal.status}]")
            lines.append(text)
            lines.append("")
    if hidden:
        lines.append(
            f"({hidden} goal(s) hidden by visibility / "
            "include_in_agent_context settings.)"
        )
    return "\n".join(lines).rstrip() + "\n"


def build_evidence_text(profile_name: str) -> str:
    """Evidence pool summary: counts by review status + most recent rows."""
    pdir = profile_dir(profile_name)
    lines: list[str] = [f"# Evidence pool: {profile_name}", ""]
    pool = load_evidence_pool(pdir)
    if pool is None:
        lines.append("(no evidence-pool.yaml for this profile)")
        return "\n".join(lines).rstrip() + "\n"

    entries = list(pool.evidence_entries)
    active = [entry for entry in entries if not entry.deprecated]
    lines.append(f"Total entries: {len(active)}")
    if len(entries) != len(active):
        lines.append(f"Deprecated (hidden below): {len(entries) - len(active)}")
    lines.append("")

    counts = Counter((entry.review_status or "unset") for entry in active)
    lines.append("## Counts by review status")
    if counts:
        for status, count in sorted(counts.items()):
            lines.append(f"- {status}: {count}")
    else:
        lines.append("- (empty pool)")
    lines.append("")

    recent = sorted(
        active,
        key=lambda entry: (entry.date or "", entry.id),
        reverse=True,
    )[:_EVIDENCE_RECENT_LIMIT]
    lines.append(f"## Most recent ({len(recent)} shown)")
    if not recent:
        lines.append("- (none)")
    for entry in recent:
        date_part = f" — {entry.date}" if entry.date else ""
        lines.append(
            f"- `{entry.id}` [{entry.type}] {entry.title}{date_part}"
            f" — {entry.review_status or 'unset'}"
        )
    return "\n".join(lines).rstrip() + "\n"


def build_inbox_text(profile_name: str) -> str:
    """Open inbox items (status inbox / captured / clarified)."""
    pdir = profile_dir(profile_name)
    inbox = load_inbox(pdir)
    open_items = [
        item for item in inbox.items if item.status in _INBOX_OPEN_STATUSES
    ]
    lines: list[str] = [
        f"# Inbox: {profile_name}",
        "",
        f"Open items: {len(open_items)} (total: {len(inbox.items)})",
        "",
    ]
    if not open_items:
        lines.append("(no open inbox items)")
        return "\n".join(lines).rstrip() + "\n"
    for item in open_items:
        tags = f" tags: {', '.join(item.tags)}" if item.tags else ""
        created = f" — {item.created_at}" if item.created_at else ""
        lines.append(
            f"- `{item.id}` [{item.type}/{item.status}] "
            f"{item.title}{tags}{created}"
        )
    return "\n".join(lines).rstrip() + "\n"


def build_learning_text(profile_name: str) -> str:
    """Learning-log summary: active (reading) resources + recent entries."""
    pdir = profile_dir(profile_name)
    log = load_learning_log(pdir)
    summary = summarize_learning_log(log)
    lines: list[str] = [
        f"# Learning log: {profile_name}",
        "",
        f"Total resources: {summary.total_entries}",
        "",
        "## Status counts",
    ]
    if summary.status_counts:
        for status, count in summary.status_counts.items():
            lines.append(f"- {status}: {count}")
    else:
        lines.append("- (empty log)")
    lines.append("")

    reading = [
        resource for resource in log.resources if resource.status == "reading"
    ]
    lines.append(f"## Active (reading) — {len(reading)}")
    if reading:
        for resource in reading:
            lines.append(f"- [{resource.kind}] {resource.title}")
    else:
        lines.append("- (none)")
    lines.append("")

    recent = sorted(
        log.resources,
        key=lambda resource: (resource.added_at or "", resource.id),
        reverse=True,
    )[:_LEARNING_RECENT_LIMIT]
    lines.append(f"## Recent entries ({len(recent)} shown)")
    if not recent:
        lines.append("- (none)")
    for resource in recent:
        when = resource.added_at or "undated"
        lines.append(
            f"- {when} [{resource.kind}/{resource.status}] {resource.title}"
        )
    return "\n".join(lines).rstrip() + "\n"


def build_agent_activity_text(profile_name: str) -> str:
    """Pending Agent Activity review queue summary."""
    pdir = profile_dir(profile_name)
    summary = activity_summary(pdir)
    pending = activity_items_for_page(pdir, {"status": "pending"})
    lines: list[str] = [f"# Agent activity: {profile_name}", ""]

    status_counts = summary.get("status") or {}
    lines.append("## Status counts")
    if status_counts:
        for status, count in sorted(status_counts.items()):
            lines.append(f"- {status}: {count}")
    else:
        lines.append("- (empty queue)")

    kind_counts = summary.get("kind") or {}
    if kind_counts:
        lines.append("")
        lines.append("## Kind counts")
        for kind, count in sorted(kind_counts.items()):
            lines.append(f"- {kind}: {count}")
    lines.append("")

    shown = pending[:_ACTIVITY_PENDING_LIMIT]
    lines.append(
        f"## Pending review ({len(pending)} total, {len(shown)} shown)"
    )
    if not shown:
        lines.append("- (nothing pending)")
    for item in shown:
        created = str(item.get("created") or "")[:10]
        lines.append(
            f"- `{item.get('id')}` "
            f"[{item.get('kind')}/{item.get('candidate_type')}] "
            f"{item.get('title')} — created {created}"
        )
    lines.append("")
    lines.append(
        "Apply or dismiss pending items in the web UI (Agent Activity page)."
    )
    return "\n".join(lines).rstrip() + "\n"


mcp = FastMCP("nblane")


@mcp.resource(
    "profile://summary",
    mime_type="text/markdown",
)
def resource_summary() -> str:
    """Skill tree counts, focus, preferences, and Doing kanban."""
    return _profile_text_resource(
        "profile://summary",
        build_summary_text,
    )


@mcp.resource(
    "profile://kanban",
    mime_type="text/markdown",
)
def resource_kanban() -> str:
    """Raw kanban.md for the active profile."""
    def _read(name: str) -> str:
        """Return kanban.md text or a short placeholder."""
        path = profile_dir(name) / "kanban.md"
        if not path.exists():
            return f"(no kanban.md for profile {name!r})\n"
        return path.read_text(encoding="utf-8")

    return _profile_text_resource("profile://kanban", _read)


@mcp.resource(
    "profile://context",
    mime_type="text/plain",
)
def resource_context() -> str:
    """Full agent system prompt (SKILL.md + evidence + kanban + mode)."""
    mode = os.getenv("NBLANE_CONTEXT_MODE", "chat")
    if mode not in ("chat", "review", "write", "plan"):
        mode = "chat"

    def _gen(name: str) -> str:
        """Build system prompt for *name* at ``mode``."""
        return generate(
            name,
            mode=mode,
            include_kanban=True,
        )

    return _profile_text_resource("profile://context", _gen)


@mcp.resource(
    "profile://gap/{task}",
    mime_type="text/plain",
)
def resource_gap(task: str) -> str:
    """Gap analysis for a natural-language task (URL-encode spaces in *task*)."""
    name, err = resolve_active_profile()
    if err is not None:
        return f"ERROR [profile://gap]: {err}\n"

    decoded = urllib.parse.unquote(task)
    if not decoded.strip():
        return (
            "ERROR [profile://gap]: Empty task. "
            "Use a non-empty path segment, e.g. "
            "profile://gap/VLM%20robot%20control\n"
        )

    use_llm = _truthy_env("NBLANE_GAP_USE_LLM")
    result = analyze(
        name,
        decoded.strip(),
        explicit_node=None,
        use_rule_match=True,
        use_llm_router=use_llm,
        persist_router_keywords=False,
    )
    if result.error:
        return f"ERROR [profile://gap]: {result.error}\n"
    return format_text(result) + "\n"


@mcp.resource(
    "agent://tasks",
    mime_type="text/markdown",
)
def resource_agent_tasks() -> str:
    """List current profile agent handoff tasks."""

    return _profile_text_resource("agent://tasks", build_agent_tasks_text)


@mcp.resource(
    "agent://task/{task_id}",
    mime_type="text/markdown",
)
def resource_agent_task(task_id: str) -> str:
    """One agent task handoff packet for an external harness."""

    name, err = resolve_active_profile()
    if err is not None or name is None:
        return f"ERROR [agent://task]: {err}\n"
    decoded = urllib.parse.unquote(str(task_id or "")).strip()
    if not decoded:
        return "ERROR [agent://task]: Empty task id.\n"
    return build_agent_task_handoff_text(name, decoded)


@mcp.resource(
    "profile://goals",
    mime_type="text/markdown",
)
def resource_goals() -> str:
    """Goals summary; private North Star / goals redacted as in agent context."""
    return _profile_text_resource("profile://goals", build_goals_text)


@mcp.resource(
    "profile://evidence",
    mime_type="text/markdown",
)
def resource_evidence() -> str:
    """Evidence pool counts by review status plus the 20 most recent rows."""
    return _profile_text_resource("profile://evidence", build_evidence_text)


@mcp.resource(
    "profile://inbox",
    mime_type="text/markdown",
)
def resource_inbox() -> str:
    """Open inbox items (status inbox / captured / clarified)."""
    return _profile_text_resource("profile://inbox", build_inbox_text)


@mcp.resource(
    "profile://learning",
    mime_type="text/markdown",
)
def resource_learning() -> str:
    """Learning-log summary: active (reading) resources and recent entries."""
    return _profile_text_resource("profile://learning", build_learning_text)


@mcp.resource(
    "agent://activity",
    mime_type="text/markdown",
)
def resource_agent_activity() -> str:
    """Pending Agent Activity review queue summary."""
    return _profile_text_resource("agent://activity", build_agent_activity_text)


def _tool_profile_or_error() -> tuple[str | None, str | None]:
    """Return ``(name, None)`` or ``(None, error)`` for MCP tools."""
    return resolve_active_profile()


def _mcp_actor() -> str:
    return os.getenv("NBLANE_MCP_ACTOR", "").strip() or "mcp"


def _confirm_store() -> agent_policy.FileConfirmStore:
    return agent_policy.FileConfirmStore(
        agent_policy.state_dir() / "mcp-confirmations.json"
    )


class _NeedsConfirmation(Exception):
    def __init__(self, payload: dict[str, Any]) -> None:
        super().__init__(payload.get("summary", ""))
        self.payload = payload


def _policy_write(
    name: str,
    tool: str,
    action: str,
    apply: Callable[[], Any],
    *,
    args: dict[str, Any],
    kinds: tuple[str, ...] = (),
    describe: Callable[[agent_journal.Snapshot], str] | None = None,
    confirm_id: str = "",
    count: int = 1,
) -> tuple[Any, dict[str, Any] | None]:
    """Run *apply* under the agent write policy.

    Returns ``(value, journal_entry)``. Raises ``_NeedsConfirmation`` for an
    unconfirmed T2 call (nothing written). *args* are the tool arguments
    that define the request; a confirmation only redeems the identical call.
    """
    label = agent_policy.ACTION_LABELS.get(action, action)
    try:
        value, _write, entry = agent_ops.guarded(
            profile_dir(name),
            apply,
            actor=_mcp_actor(),
            action=action,
            kinds=kinds,
            fingerprint=agent_policy.fingerprint("MCP", f"{name}/{tool}", args),
            describe=describe or (lambda _before: label),
            count=count,
            confirm_id=confirm_id,
            store=_confirm_store(),
        )
    except agent_ops.ConfirmationRequired as exc:
        pending = exc.pending.public()
        raise _NeedsConfirmation(
            {
                "ok": False,
                "confirmation_required": True,
                "invalid_confirm_id": exc.invalid,
                **pending,
                "next": (
                    f"Ask the user in the chat: {pending['summary']}? Only after "
                    f"they agree, call {tool} again with the same arguments and "
                    f"confirm_id={pending['confirm_id']!r} (valid 10 minutes). "
                    "Never confirm on the user's behalf."
                ),
            }
        ) from None
    return value, entry


def _journal_fields(entry: dict[str, Any] | None) -> dict[str, Any]:
    if not entry:
        return {"journal_id": ""}
    return {"journal_id": entry.get("id", ""), "undo_hint": "undo_action(journal_id)"}


def _legacy_suffix(entry: dict[str, Any] | None) -> str:
    return f" Undo with undo_action({entry['id']!r})." if entry else ""


def _legacy_confirmation(payload: dict[str, Any]) -> str:
    return (
        f"CONFIRM REQUIRED: {payload['summary']}. confirm_id={payload['confirm_id']} "
        f"— {payload['next']}\n"
    )


@mcp.tool(name="append_growth_log")
def tool_append_growth_log(event: str) -> str:
    """Append one row to the Growth Log table in SKILL.md (undoable)."""
    name, err = _tool_profile_or_error()
    if err is not None or name is None:
        return f"ERROR: {err}\n"
    clean = event.strip()
    try:
        _value, entry = _policy_write(
            name,
            "append_growth_log",
            "growth_log.append",
            lambda: append_growth_log_row(profile_dir(name), clean),
            args={"event": clean},
            kinds=(agent_journal.file_kind("SKILL.md"),),
            describe=lambda _before: f"记一条成长日志「{clean}」",
        )
    except _TOOL_STORE_ERRORS as exc:
        return f"ERROR: {exc}\n"
    return f"OK: growth log updated for profile {name!r}.{_legacy_suffix(entry)}\n"


@mcp.tool(name="log_skill_evidence")
def tool_log_skill_evidence(
    skill_id: str,
    title: str,
    evidence_type: str = "practice",
    date: str = "",
    url: str = "",
    summary: str = "",
    confirm_id: str = "",
) -> str:
    """Add one inline evidence item to a skill-tree node.

    Needs the user's confirmation in the chat: the first call answers
    ``CONFIRM REQUIRED`` with a ``confirm_id``; repeat the identical call
    with that ``confirm_id`` only after the user agrees.
    """
    name, err = _tool_profile_or_error()
    if err is not None or name is None:
        return f"ERROR: {err}\n"
    clean_skill = skill_id.strip()
    clean_type = evidence_type.strip() or "practice"
    args = {
        "skill_id": clean_skill,
        "title": title.strip(),
        "evidence_type": clean_type,
        "date": date.strip(),
        "url": url.strip(),
        "summary": summary.strip(),
    }
    try:
        _value, entry = _policy_write(
            name,
            "log_skill_evidence",
            "skill_evidence.add",
            lambda: add_inline_evidence(
                name,
                clean_skill,
                type_=clean_type,
                title=title,
                date=date,
                url=url,
                summary=summary,
            ),
            args=args,
            kinds=("skill_node",),
            describe=lambda _before: f"给技能点 {clean_skill} 添加证据「{title.strip()}」",
            confirm_id=confirm_id,
        )
    except _NeedsConfirmation as exc:
        return _legacy_confirmation(exc.payload)
    except _TOOL_STORE_ERRORS as exc:
        return f"ERROR: {exc}\n"
    return (
        f"OK: evidence on {skill_id!r} "
        f"({title.strip()!r}) for {name!r}.{_legacy_suffix(entry)}\n"
    )


@mcp.tool(name="log_interaction")
def tool_log_interaction(
    question: str,
    answer: str,
    skill_ids: list[str] | None = None,
) -> str:
    """Append Q/A JSONL under profiles/<name>/interactions/."""
    name, err = _tool_profile_or_error()
    if err is not None or name is None:
        return f"ERROR: {err}\n"
    ids = skill_ids if skill_ids is not None else []
    # Append-only Q/A log: policy-checked, not journaled (nothing to undo).
    path, _entry = _policy_write(
        name,
        "log_interaction",
        "interaction.log",
        lambda: append_interaction_record(
            name,
            question=question,
            answer=answer,
            skill_ids=ids,
        ),
        args={"question": question, "answer": answer, "skill_ids": ids},
    )
    return f"OK: appended to {path}\n"


@mcp.tool(name="suggest_skill_upgrade")
def tool_suggest_skill_upgrade(
    skill_id: str,
    proposed_status: str,
    rationale: str,
) -> str:
    """Suggest a status change (does not write YAML)."""
    name, err = _tool_profile_or_error()
    if err is not None or name is None:
        return f"ERROR: {err}\n"
    return (
        f"SUGGESTION only (no write) for profile {name!r}: "
        f"set {skill_id!r} -> {proposed_status!r}. "
        f"Reason: {rationale.strip()}\n"
    )


@mcp.tool(name="crystallize_method_draft")
def tool_crystallize_method_draft(
    project: str,
    body: str,
) -> str:
    """Write a human-editable method draft under profiles/.../methods/."""
    name, err = _tool_profile_or_error()
    if err is not None or name is None:
        return f"ERROR: {err}\n"
    relative = f"methods/{_method_slug(project)}_draft.md"
    try:
        path, entry = _policy_write(
            name,
            "crystallize_method_draft",
            "method_draft.write",
            lambda: write_method_draft(name, project, body),
            args={"project": project, "body": body},
            kinds=(agent_journal.file_kind(relative),),
            describe=lambda _before: f"写方法草稿「{project.strip()}」",
        )
    except _TOOL_STORE_ERRORS as exc:
        return f"ERROR: {exc}\n"
    return f"OK: wrote {path}{_legacy_suffix(entry)}\n"


@mcp.tool(name="submit_agent_task_candidate")
def tool_submit_agent_task_candidate(
    task_id: str,
    summary: str,
    changed_paths: list[str] | None = None,
    warnings: list[str] | None = None,
    result_payload: dict | None = None,
) -> str:
    """Submit external-agent output to the review queue, not facts."""

    name, err = _tool_profile_or_error()
    if err is not None or name is None:
        return f"ERROR: {err}\n"
    try:
        task, _entry = _policy_write(
            name,
            "submit_agent_task_candidate",
            "agent_task.report",
            lambda: submit_agent_task_candidate(
                name,
                task_id,
                summary=summary,
                changed_paths=changed_paths or [],
                warnings=warnings or [],
                result_payload=result_payload or {},
            ),
            args={"task_id": task_id},
        )
    except _TOOL_STORE_ERRORS as exc:
        return f"ERROR: {exc}\n"
    if task is None:
        return f"ERROR: unknown agent task {task_id!r}\n"
    activity = task.get("activity_item_id") or "(pending)"
    return (
        "OK: candidate submitted for "
        f"{task.get('id')} with Activity item {activity}.\n"
    )


@mcp.tool(name="update_agent_task_status")
def tool_update_agent_task_status(
    task_id: str,
    status: str,
    error: str = "",
    warnings: list[str] | None = None,
) -> str:
    """Update agent task status and mirror safe review metadata."""

    name, err = _tool_profile_or_error()
    if err is not None or name is None:
        return f"ERROR: {err}\n"
    clean_status = str(status or "").strip().lower()
    if clean_status not in AGENT_TASK_STATUSES:
        return f"ERROR: unknown agent task status {status!r}\n"
    try:
        task, _entry = _policy_write(
            name,
            "update_agent_task_status",
            "agent_task.report",
            lambda: update_agent_task_status(
                name,
                task_id,
                clean_status,
                error=error,
                warnings=warnings or [],
            ),
            args={"task_id": task_id, "status": clean_status},
        )
    except _TOOL_STORE_ERRORS as exc:
        return f"ERROR: {exc}\n"
    if task is None:
        return f"ERROR: unknown agent task {task_id!r}\n"
    return f"OK: agent task {task.get('id')} status is {task.get('status')}.\n"


def _today_iso() -> str:
    """Return today's date in ISO format (for Review-window source refs)."""
    return date.today().isoformat()


def _tool_error_payload(message: str) -> dict[str, Any]:
    """Structured error payload for dict-returning MCP tools."""
    return {"ok": False, "error": message}


# Store-layer failures the tools report as payload errors instead of letting
# them escape as protocol-level exceptions. ``yaml.YAMLError`` covers
# corrupted profile YAML (it is not an ``OSError``/``ValueError`` subclass).
_TOOL_STORE_ERRORS = (OSError, ValueError, yaml.YAMLError)


@mcp.tool(
    name="capture_inbox",
    annotations=ToolAnnotations(
        title="Capture an inbox item",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
    structured_output=True,
)
def tool_capture_inbox(
    title: str,
    raw_text: str = "",
    source: str = "openclaw",
    tags: list[str] | None = None,
    note: str = "",
) -> dict[str, Any]:
    """Capture a quick note/link into the profile inbox (direct append).

    This is the low-risk fast-capture path (e.g. a chat message worth
    triaging later). The item lands with status ``inbox`` and is processed
    by the human during review; nothing else in the profile is touched.
    """
    name, err = _tool_profile_or_error()
    if err is not None or name is None:
        return _tool_error_payload(err or "no active profile")
    clean_title = str(title or "").strip()
    if not clean_title:
        return _tool_error_payload("title must not be empty")
    clean_source = str(source or "").strip() or "openclaw"

    def _capture(inbox: Inbox) -> InboxItem:
        return add_inbox_item(
            inbox,
            clean_title,
            source=clean_source,
            captured_by=clean_source,
            raw_text=raw_text,
            tags=tags or [],
            status="inbox",
            note=note,
        )

    try:
        item, entry = _policy_write(
            name,
            "capture_inbox",
            "inbox.capture",
            lambda: update_inbox(profile_dir(name), _capture),
            args={"title": clean_title, "raw_text": raw_text, "tags": tags or []},
            kinds=("inbox_item",),
            describe=lambda _before: f"记入收件箱「{clean_title}」",
        )
    except _TOOL_STORE_ERRORS as exc:
        return _tool_error_payload(str(exc))
    return {
        "ok": True,
        "profile": name,
        "item_id": item.id,
        "status": item.status,
        "captured_by": item.captured_by,
        **_journal_fields(entry),
    }


@mcp.tool(
    name="submit_evidence_candidate",
    annotations=ToolAnnotations(
        title="Submit an evidence candidate for human review",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
    structured_output=True,
)
def tool_submit_evidence_candidate(
    skill_id: str,
    title: str,
    evidence_type: str,
    date: str,
    url: str = "",
    summary: str = "",
) -> dict[str, Any]:
    """Queue one evidence candidate for human review (no direct pool write).

    The item appears in Agent Activity as a pending Review candidate; only
    when the human applies it does the evidence land in evidence-pool.yaml
    (linked to ``skill_id`` via a ``skill:<id>`` source ref for later
    wiring in Evidence Review).
    """
    name, err = _tool_profile_or_error()
    if err is not None or name is None:
        return _tool_error_payload(err or "no active profile")
    clean_skill = str(skill_id or "").strip()
    clean_title = str(title or "").strip()
    if not clean_skill:
        return _tool_error_payload("skill_id must not be empty")
    if not clean_title:
        return _tool_error_payload("title must not be empty")
    clean_type = str(evidence_type or "").strip() or "practice"
    if clean_type not in EVIDENCE_TYPES:
        return _tool_error_payload(
            f"unknown evidence_type {evidence_type!r} "
            f"(expected one of {sorted(EVIDENCE_TYPES)})"
        )
    today = _today_iso()
    candidate = {
        "source": "mcp_agent",
        "skill_id": clean_skill,
        "type": clean_type,
        "title": clean_title,
        "date": str(date or "").strip(),
        "url": str(url or "").strip(),
        "summary": str(summary or "").strip(),
    }
    try:
        item = activity_item_from_review_candidate(
            name,
            today,
            today,
            "evidence",
            candidate,
        )
        stored, _entry = _policy_write(
            name,
            "submit_evidence_candidate",
            "review.submit",
            lambda: append_activity_item(name, item),
            args=candidate,
        )
    except _TOOL_STORE_ERRORS as exc:
        return _tool_error_payload(str(exc))
    return {
        "ok": True,
        "profile": name,
        "item_id": stored.get("id"),
        "status": stored.get("status"),
        "candidate_type": stored.get("candidate_type"),
        "target_owner": stored.get("target_owner"),
    }


@mcp.tool(
    name="submit_profile_model_candidate",
    annotations=ToolAnnotations(
        title="Submit a profile-model candidate for human review",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
    structured_output=True,
)
def tool_submit_profile_model_candidate(
    field: str,
    proposed_value: str,
    rationale: str,
) -> dict[str, Any]:
    """Queue a proposed agent-profile.yaml field update for manual review.

    There is intentionally no auto-applier: the human reads the
    self-describing payload in Agent Activity and edits the profile by
    hand. Use this for stable, durable facts or preferences about the
    user — not for session state.
    """
    name, err = _tool_profile_or_error()
    if err is not None or name is None:
        return _tool_error_payload(err or "no active profile")
    clean_field = str(field or "").strip()
    clean_value = str(proposed_value or "").strip()
    clean_rationale = str(rationale or "").strip()
    if not clean_field:
        return _tool_error_payload("field must not be empty")
    if not clean_value:
        return _tool_error_payload("proposed_value must not be empty")
    payload = {
        "field": clean_field,
        "proposed_value": clean_value,
        "rationale": clean_rationale,
        "target_file": "agent-profile.yaml",
    }
    item = {
        "kind": "candidate",
        "candidate_type": "profile_model",
        "source_page": "Review",
        "source_ref": f"review:{_today_iso()}:{_today_iso()}",
        "target_owner": "profile_context",
        "status": "pending",
        "title": f"Profile model update: {clean_field}",
        "summary": clean_rationale,
        "payload": payload,
        "preview": yaml.dump(
            payload,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        ).strip(),
    }
    try:
        stored, _entry = _policy_write(
            name,
            "submit_profile_model_candidate",
            "review.submit",
            lambda: append_activity_item(name, item),
            args=payload,
        )
    except _TOOL_STORE_ERRORS as exc:
        return _tool_error_payload(str(exc))
    return {
        "ok": True,
        "profile": name,
        "item_id": stored.get("id"),
        "status": stored.get("status"),
        "candidate_type": stored.get("candidate_type"),
        "target_owner": stored.get("target_owner"),
    }


def _write_annotations(title: str, *, destructive: bool = False) -> ToolAnnotations:
    return ToolAnnotations(
        title=title,
        readOnlyHint=False,
        destructiveHint=destructive,
        idempotentHint=False,
        openWorldHint=False,
    )


def _resolve_card(sections: dict[str, list[KanbanTask]], card_ref: str) -> tuple[str, int, KanbanTask]:
    """Card by id, then exact title / unique substring; ValueError otherwise."""
    hit = find_kanban_card_by_id(sections, card_ref)
    if hit is not None:
        return hit
    found, _kind, message = find_kanban_card(sections, card_ref)
    if found is None:
        raise ValueError(message)
    return found


def _card_title(before: agent_journal.Snapshot, card_ref: str) -> str:
    states = before.get("kanban_card", {})
    state = states.get(card_ref) or next(
        (s for s in states.values() if agent_ops.entity_title(s) == card_ref), None
    )
    return agent_ops.entity_title(state) or card_ref


def _section_or_error(raw: str) -> str:
    resolved = resolve_kanban_section(raw)
    if resolved is None:
        raise ValueError(
            f"unknown section {raw!r} (expected one of: {', '.join(KANBAN_SECTIONS)})"
        )
    return resolved


def _policy_payload(name: str, fn: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    """Run one dict tool body, mapping policy/store failures to payloads."""
    try:
        return fn()
    except _NeedsConfirmation as exc:
        return {"profile": name, **exc.payload}
    except _TOOL_STORE_ERRORS as exc:
        return _tool_error_payload(str(exc))


@mcp.tool(
    name="add_kanban_card",
    annotations=_write_annotations("Add a kanban card"),
    structured_output=True,
)
def tool_add_kanban_card(
    title: str,
    section: str = KANBAN_QUEUE,
    context: str = "",
    tags: list[str] | None = None,
    planned_start: str = "",
    planned_end: str = "",
) -> dict[str, Any]:
    """Add one card to the board (applies directly; undo with ``undo_action``).

    ``section`` is ``Queue`` (default), ``Doing``, ``Done`` or
    ``Someday / Maybe``. Cards added to Doing get ``started_on`` today,
    cards added to Done get ``completed_on`` today.
    """
    name, err = _tool_profile_or_error()
    if err is not None or name is None:
        return _tool_error_payload(err or "no active profile")
    clean_title = str(title or "").strip()
    if not clean_title:
        return _tool_error_payload("title must not be empty")

    def _run() -> dict[str, Any]:
        target = _section_or_error(section or KANBAN_QUEUE)
        today = _today_iso()
        task = KanbanTask(
            title=clean_title,
            context=str(context or "").strip(),
            tags=", ".join(t.strip() for t in tags or [] if t.strip()),
            planned_start=str(planned_start or "").strip() or None,
            planned_end=str(planned_end or "").strip() or None,
        )
        if target == KANBAN_DONE:
            task.done, task.completed_on = True, today
        elif target == KANBAN_DOING:
            task.started_on = today

        def _append(sections: dict[str, list[KanbanTask]]) -> str:
            sections.setdefault(target, []).append(task)
            ensured = ensure_kanban_task_ids(sections, name)
            sections.clear()
            sections.update(ensured)
            return ensured[target][-1].id

        card_id, entry = _policy_write(
            name,
            "add_kanban_card",
            "kanban.card.add",
            lambda: update_kanban(profile_dir(name), _append),
            args={"title": clean_title, "section": target},
            kinds=("kanban_card",),
            describe=lambda _before: f"新建任务「{clean_title}」",
        )
        return {
            "ok": True,
            "profile": name,
            "card_id": card_id,
            "section": target,
            **_journal_fields(entry),
        }

    return _policy_payload(name, _run)


def _move_card(name: str, tool: str, card_ref: str, target_section: str) -> dict[str, Any]:
    clean_ref = str(card_ref or "").strip()
    if not clean_ref:
        return _tool_error_payload("card_ref must not be empty")
    if not str(target_section or "").strip():
        return _tool_error_payload(
            "target_section is required (moves apply directly; "
            f"one of: {', '.join(KANBAN_SECTIONS)})"
        )

    def _run() -> dict[str, Any]:
        target = _section_or_error(target_section)

        def _move(sections: dict[str, list[KanbanTask]]) -> tuple[str, str, str]:
            from_section, _index, task = _resolve_card(sections, clean_ref)
            if from_section != target:
                moved = apply_kanban_reorder(
                    sections,
                    [{"id": task.id, "to_section": target}],
                    auto_dates=True,
                )
                sections.clear()
                sections.update(moved)
            return task.id, task.title, from_section

        (card_id, title, from_section), entry = _policy_write(
            name,
            tool,
            "kanban.card.move",
            lambda: update_kanban(profile_dir(name), _move),
            args={"card_ref": clean_ref, "target_section": target},
            kinds=("kanban_card",),
            describe=lambda before: f"移动任务「{_card_title(before, clean_ref)}」到 {target}",
        )
        out: dict[str, Any] = {
            "ok": True,
            "profile": name,
            "card_id": card_id,
            "title": title,
            "from_section": from_section,
            "section": target,
            **_journal_fields(entry),
        }
        if from_section == target:
            out["warnings"] = [f"card {title!r} is already in {target!r}; no move needed"]
        return out

    return _policy_payload(name, _run)


@mcp.tool(
    name="move_kanban_card",
    annotations=_write_annotations("Move a kanban card"),
    structured_output=True,
)
def tool_move_kanban_card(card_ref: str, target_section: str) -> dict[str, Any]:
    """Move one card to another column (applies directly; undoable).

    ``card_ref`` is the card id (``kb_…``), the exact title, or a unique
    substring of the title. Landing in Done marks the card done with
    ``completed_on``; leaving Done clears both.
    """
    name, err = _tool_profile_or_error()
    if err is not None or name is None:
        return _tool_error_payload(err or "no active profile")
    return _move_card(name, "move_kanban_card", card_ref, target_section)


@mcp.tool(
    name="submit_kanban_candidate",
    annotations=_write_annotations("Move a kanban card (legacy name)"),
    structured_output=True,
)
def tool_submit_kanban_candidate(
    action: str,
    card_ref: str,
    target_section: str = "",
    note: str = "",
) -> dict[str, Any]:
    """Legacy alias of ``move_kanban_card``: the move now applies directly.

    Kept so older prompts keep working; there is no review step anymore
    (undo with ``undo_action``). ``note`` is ignored.
    """
    name, err = _tool_profile_or_error()
    if err is not None or name is None:
        return _tool_error_payload(err or "no active profile")
    clean_action = str(action or "").strip().lower() or "move"
    if clean_action != "move":
        return _tool_error_payload(
            f"unsupported action {action!r} (only 'move' is supported)"
        )
    return _move_card(name, "move_kanban_card", card_ref, target_section)


@mcp.tool(
    name="delete_kanban_card",
    annotations=_write_annotations("Delete a kanban card", destructive=True),
    structured_output=True,
)
def tool_delete_kanban_card(card_ref: str, confirm_id: str = "") -> dict[str, Any]:
    """Delete one card. Needs the user's confirmation in the chat.

    The first call answers ``confirmation_required`` with a ``summary`` and
    a ``confirm_id`` and changes nothing. Relay the summary; only after the
    user agrees, call again with the same ``card_ref`` and ``confirm_id``.
    The delete stays undoable via ``undo_action``.
    """
    name, err = _tool_profile_or_error()
    if err is not None or name is None:
        return _tool_error_payload(err or "no active profile")
    clean_ref = str(card_ref or "").strip()
    if not clean_ref:
        return _tool_error_payload("card_ref must not be empty")

    def _run() -> dict[str, Any]:
        def _delete(sections: dict[str, list[KanbanTask]]) -> tuple[str, str]:
            section, index, task = _resolve_card(sections, clean_ref)
            del sections[section][index]
            return task.id, task.title

        (card_id, title), entry = _policy_write(
            name,
            "delete_kanban_card",
            "kanban.card.delete",
            lambda: update_kanban(profile_dir(name), _delete),
            args={"card_ref": clean_ref},
            kinds=("kanban_card",),
            describe=lambda before: f"删除任务「{_card_title(before, clean_ref)}」",
            confirm_id=confirm_id,
        )
        return {
            "ok": True,
            "profile": name,
            "deleted_id": card_id,
            "deleted_title": title,
            **_journal_fields(entry),
        }

    return _policy_payload(name, _run)


@mcp.tool(
    name="add_checkin",
    annotations=_write_annotations("Check in a habit"),
    structured_output=True,
)
def tool_add_checkin(
    habit: str,
    date: str = "",
    count: float = 1.0,
    unit: str = "",
    summary: str = "",
    note: str = "",
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Record one habit check-in (applies directly; undoable).

    ``habit`` is a habit id or title; ``date`` defaults to today (ISO).
    """
    name, err = _tool_profile_or_error()
    if err is not None or name is None:
        return _tool_error_payload(err or "no active profile")
    clean_habit = str(habit or "").strip()
    if not clean_habit:
        return _tool_error_payload("habit must not be empty")

    def _run() -> dict[str, Any]:
        when = str(date or "").strip() or _today_iso()
        entry_value, entry = _policy_write(
            name,
            "add_checkin",
            "checkin.add",
            lambda: activity_log.add_activity_checkin(
                profile_dir(name),
                clean_habit,
                when=when,
                count=count,
                unit=str(unit or "").strip(),
                summary=str(summary or "").strip(),
                note=str(note or "").strip(),
                tags=tags or [],
            ),
            args={"habit": clean_habit, "date": when, "summary": summary},
            kinds=("checkin",),
            describe=lambda _before: f"打卡「{clean_habit}」（{when}）",
        )
        return {
            "ok": True,
            "profile": name,
            "checkin_id": entry_value.id,
            "habit": entry_value.habit_id,
            "date": entry_value.date,
            **_journal_fields(entry),
        }

    return _policy_payload(name, _run)


@mcp.tool(
    name="recent_actions",
    annotations=ToolAnnotations(
        title="List recent agent writes (undo journal)",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
    structured_output=True,
)
def tool_recent_actions(limit: int = 10) -> dict[str, Any]:
    """Newest-first agent writes from the undo journal (HTTP and MCP).

    ``status`` is ``undoable``, ``conflict`` (changed since, undo refused)
    or ``undone``.
    """
    name, err = _tool_profile_or_error()
    if err is not None or name is None:
        return _tool_error_payload(err or "no active profile")
    try:
        entries = agent_journal.recent(profile_dir(name), max(1, min(int(limit), 50)))
    except _TOOL_STORE_ERRORS as exc:
        return _tool_error_payload(str(exc))
    return {
        "ok": True,
        "profile": name,
        "retention_days": agent_journal.RETENTION_DAYS,
        "entries": [
            {
                "id": e.get("id", ""),
                "at": e.get("at", ""),
                "actor": e.get("actor", ""),
                "action": e.get("action", ""),
                "tier": e.get("tier", ""),
                "summary": e.get("summary", ""),
                "status": e.get("status", ""),
            }
            for e in entries
        ],
    }


@mcp.tool(
    name="undo_action",
    annotations=_write_annotations("Undo one agent write"),
    structured_output=True,
)
def tool_undo_action(journal_id: str) -> dict[str, Any]:
    """Revert one journaled agent write (id from ``recent_actions``).

    Refused when the entity changed since (someone edited it afterwards):
    then the user has to fix it in the nblane web UI.
    """
    name, err = _tool_profile_or_error()
    if err is not None or name is None:
        return _tool_error_payload(err or "no active profile")
    try:
        entry = agent_journal.undo(profile_dir(name), str(journal_id or "").strip(), actor=_mcp_actor())
    except agent_journal.UndoError as exc:
        return {"ok": False, "code": exc.code, "error": exc.message}
    except _TOOL_STORE_ERRORS as exc:
        return _tool_error_payload(str(exc))
    return {
        "ok": True,
        "profile": name,
        "journal_id": entry.get("id", ""),
        "summary": entry.get("summary", ""),
        "undone_at": entry.get("undone_at", ""),
    }


_VALIDATE_REPORT_LIMIT = 50


@mcp.tool(
    name="run_validate",
    annotations=ToolAnnotations(
        title="Validate the active profile",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
    structured_output=True,
)
def tool_run_validate() -> dict[str, Any]:
    """Validate the active profile against its schema (read-only)."""
    name, err = _tool_profile_or_error()
    if err is not None or name is None:
        return _tool_error_payload(err or "no active profile")
    try:
        errors, warnings = validate_one(profile_dir(name), check_sync=False)
    except _TOOL_STORE_ERRORS as exc:
        return _tool_error_payload(str(exc))
    return {
        "ok": not errors,
        "profile": name,
        "errors": errors[:_VALIDATE_REPORT_LIMIT],
        "warnings": warnings[:_VALIDATE_REPORT_LIMIT],
        "error_count": len(errors),
        "warning_count": len(warnings),
        "truncated": (
            len(errors) > _VALIDATE_REPORT_LIMIT
            or len(warnings) > _VALIDATE_REPORT_LIMIT
        ),
    }


@mcp.tool(
    name="run_sync_check",
    annotations=ToolAnnotations(
        title="Check SKILL.md generated-block drift",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
    structured_output=True,
)
def tool_run_sync_check() -> dict[str, Any]:
    """Report drifted generated blocks in SKILL.md (read-only, never writes)."""
    name, err = _tool_profile_or_error()
    if err is not None or name is None:
        return _tool_error_payload(err or "no active profile")
    try:
        drifted = get_drifted_blocks(profile_dir(name))
    except _TOOL_STORE_ERRORS as exc:
        return _tool_error_payload(str(exc))
    return {
        "ok": True,
        "profile": name,
        "in_sync": not drifted,
        "drifted_blocks": list(drifted),
    }


def main() -> None:
    """Run the MCP server on stdio (default)."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
