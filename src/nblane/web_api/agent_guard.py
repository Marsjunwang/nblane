"""Agent write guard: one app-level dependency enforcing core/agent_policy.

Instead of wiring every mutation route by hand, every mutating ``/api/v1``
request from an agent account passes through ``agent_write_guard``:

1. The route template (``request.scope["route"].path``) + method map to an
   action (``ROUTE_ACTIONS``); unmapped routes count as ``unknown`` (T2).
2. T0 passes untouched; T3 answers 403.
3. For T1/T2 the entity kinds the action may touch (``ACTION_KINDS``) are
   snapshotted. T2 then requires the chat confirmation handshake
   (428 → ``X-Nblane-Confirm``).
4. After the handler returns, the same kinds are snapshotted again; the
   diff becomes one undo-journal entry. A request that changed nothing
   (412, 422, no-op) records nothing and refunds a spent confirmation.

Human accounts never reach steps 2–4. The before/after diff is
attribution by time window: a human edit landing in the same few
milliseconds would be journaled with the agent's write (undo would then
see it as part of the agent's change). Single-user deployments make this
practically moot; it is the price of not threading snapshots through
every domain writer.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, AsyncIterator

from fastapi import Request
from starlette.requests import HTTPConnection
from starlette.concurrency import run_in_threadpool

from nblane.core import agent_journal, agent_ops, agent_policy, profile_io


MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
P = "/api/v1/profiles/{name}"

# (method, route template) -> action. Settings/auth/system routes are T3 by
# prefix (see ``action_for``).
ROUTE_ACTIONS: dict[tuple[str, str], str] = {
    # kanban
    ("POST", f"{P}/kanban/cards"): "kanban.card.add",
    ("POST", f"{P}/kanban/cards/{{card_ref}}/move"): "kanban.card.move",
    ("POST", f"{P}/kanban/cards/{{card_ref}}/done"): "kanban.card.done",
    ("POST", f"{P}/kanban/cards/{{card_ref}}/schedule"): "kanban.card.schedule",
    ("PATCH", f"{P}/kanban/cards/{{card_ref}}"): "kanban.card.patch",
    ("DELETE", f"{P}/kanban/cards/{{card_ref}}"): "kanban.card.delete",
    ("POST", f"{P}/divination/intake"): "kanban.card.add",
    # habits / check-ins / plans
    ("POST", f"{P}/checkins"): "checkin.add",
    ("DELETE", f"{P}/checkins/{{checkin_id}}"): "checkin.delete",
    ("POST", f"{P}/habits/{{habit_id}}/archive"): "habit.archive",
    ("DELETE", f"{P}/habits/{{habit_id}}"): "habit.delete",
    ("POST", f"{P}/habit-plans"): "habit_plan.add",
    ("PATCH", f"{P}/habit-plans/{{plan_id}}"): "habit_plan.update",
    ("DELETE", f"{P}/habit-plans/{{plan_id}}"): "habit_plan.delete",
    ("POST", f"{P}/plan-templates/instantiate"): "plan_template.instantiate",
    # goals / identity / skills
    ("POST", f"{P}/goals"): "goal.add",
    ("PATCH", f"{P}/goals/{{goal_id}}"): "goal.patch",
    ("PATCH", f"{P}/north-star"): "north_star.patch",
    ("PATCH", f"{P}/skill-tree/nodes/{{node_id}}"): "skill_node.patch",
    # evidence
    ("POST", f"{P}/evidence/{{entry_id}}/edit"): "evidence.edit",
    ("POST", f"{P}/evidence/{{entry_id}}/review"): "evidence.review",
    ("POST", f"{P}/evidence/{{entry_id}}/skill-links"): "evidence.skill_links",
    ("POST", f"{P}/evidence-review/bulk"): "evidence.bulk",
    ("POST", f"{P}/evidence-review/deprecate"): "evidence.deprecate",
    ("POST", f"{P}/crystallize/apply"): "crystallize.apply",
    # projects
    ("POST", f"{P}/project-board/cases"): "project_case.add",
    ("POST", f"{P}/project-board/cases/{{case_id}}/save"): "project_case.save",
    ("POST", f"{P}/project-board/cases/{{case_id}}/archive"): "project_case.archive",
    ("DELETE", f"{P}/project-board/cases/{{case_id}}"): "project_case.delete",
    ("POST", f"{P}/project-board/cases/{{case_id}}/milestones"): "project_case.save",
    ("POST", f"{P}/project-board/cases/{{case_id}}/milestones/{{milestone_id}}/save"): "project_case.save",
    ("POST", f"{P}/project-board/cases/{{case_id}}/milestones/{{milestone_id}}/delete"): "project_milestone.delete",
    ("POST", f"{P}/project-board/cases/{{case_id}}/tasks"): "kanban.card.add",
    ("POST", f"{P}/project-board/tasks/{{task_id}}/move"): "kanban.card.move",
    # research
    ("POST", f"{P}/research/sources"): "research_source.add",
    ("PATCH", f"{P}/research/sources/{{source_id}}"): "research_source.patch",
    ("POST", f"{P}/research/sources/{{source_id}}/task"): "research_source.patch",
    ("POST", f"{P}/research/connectors/manual/import"): "research.import",
    ("POST", f"{P}/research/connectors/{{connector_id}}/import"): "research.import",
    # growth log
    ("POST", f"{P}/growth-log"): "growth_log.append",
    # read-like: casts, AI drafts, the undo endpoint itself
    ("POST", f"{P}/divination"): "divination.cast",
    ("POST", f"{P}/jobs"): "ai.draft",
    ("POST", f"{P}/crystallize/draft"): "ai.draft",
    ("POST", f"{P}/project-board/cases/{{case_id}}/suggest-refs"): "ai.draft",
    ("POST", f"{P}/research/connectors/manual/preview"): "ai.draft",
    ("POST", f"{P}/research/connectors/{{connector_id}}/preview"): "ai.draft",
    ("POST", f"{P}/research/papers/{{source_id}}/analysis-jobs"): "ai.draft",
    ("POST", f"{P}/agent/journal/{{entry_id}}/undo"): "journal.undo",
    # AI exception triage
    ("POST", f"{P}/ai-exceptions/dismiss"): "review.decide",
}

# Profile-scoped prefixes that stay in the web UI: publishing, résumé,
# public-layer init and per-profile settings are not undoable here.
WEB_ONLY_PREFIXES = (
    f"{P}/public-site",
    f"{P}/content",
    f"{P}/career",
    f"{P}/studio/init",
    f"{P}/settings",
    f"{P}/research/connectors",
    f"{P}/research/ai-config",
)

# Auth routes are skipped by the guard (login/logout must work for
# everyone) except credential changes: an agent may not change its own
# password or sign its owner out. ``/api/v1/accounts*`` is outside the
# profile prefix and therefore T3 via ``action_for`` already.
AGENT_FORBIDDEN_AUTH_ROUTES = frozenset({
    "/api/v1/auth/password",
    "/api/v1/auth/logout-all",
})

_KANBAN = ("kanban_card", "project_case")
_PROJECT = ("project_case", "kanban_card", "evidence", "research_source")
ACTION_KINDS: dict[str, tuple[str, ...]] = {
    "kanban.card.add": _KANBAN,
    "kanban.card.move": _KANBAN,
    "kanban.card.done": _KANBAN,
    "kanban.card.schedule": _KANBAN,
    "kanban.card.patch": _KANBAN,
    "kanban.card.delete": _KANBAN,
    "checkin.add": ("checkin",),
    "checkin.delete": ("checkin",),
    "habit.archive": ("habit",),
    "habit.delete": ("habit", "checkin"),
    "habit_plan.add": ("habit_plan", *_KANBAN),
    "habit_plan.update": ("habit_plan",),
    "habit_plan.delete": ("habit_plan", *_KANBAN),
    "plan_template.instantiate": ("habit", "project_case"),
    "goal.add": ("goal",),
    "goal.patch": ("goal",),
    "north_star.patch": ("north_star",),
    "skill_node.patch": ("skill_node",),
    "evidence.edit": ("evidence",),
    "evidence.review": ("evidence",),
    "evidence.skill_links": ("skill_node",),
    "evidence.bulk": ("evidence",),
    "evidence.deprecate": ("evidence",),
    "crystallize.apply": ("evidence", "skill_node", "kanban_card"),
    "project_case.add": _PROJECT,
    "project_case.save": _PROJECT,
    "project_case.archive": _PROJECT,
    "project_case.delete": _PROJECT,
    "project_milestone.delete": _PROJECT,
    "research_source.add": ("research_source",),
    "research_source.patch": ("research_source", "kanban_card"),
    "research.import": ("research_source",),
    "growth_log.append": (agent_journal.file_kind("SKILL.md"),),
}

ACTION_LABELS = agent_policy.ACTION_LABELS

# Path parameter -> entity kind whose title names the target.
_PARAM_KINDS = {
    "card_ref": "kanban_card",
    "task_id": "kanban_card",
    "checkin_id": "checkin",
    "habit_id": "habit",
    "plan_id": "habit_plan",
    "goal_id": "goal",
    "node_id": "skill_node",
    "entry_id": "evidence",
    "case_id": "project_case",
    "source_id": "research_source",
}

_BATCH_KEYS = ("ids", "task_ids", "items", "cards", "entries")


def action_for(method: str, template: str) -> str:
    action = ROUTE_ACTIONS.get((method, template))
    if action:
        return action
    if not template.startswith(P) or template.startswith(WEB_ONLY_PREFIXES):
        return "settings.system"
    return "unknown"


async def _read_body(request: Request) -> Any:
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type or "x-www-form-urlencoded" in content_type:
        form = await request.form()
        return {key: str(value) for key, value in form.items()}
    raw = await request.body()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except ValueError:
        return raw.decode("utf-8", errors="replace")


def _batch_count(body: Any) -> int:
    if not isinstance(body, dict):
        return 1
    sizes = [len(body[key]) for key in _BATCH_KEYS if isinstance(body.get(key), list)]
    return max([1, *sizes])


def _target_title(path_params: dict[str, str], before: agent_journal.Snapshot) -> str:
    for param, kind in _PARAM_KINDS.items():
        ref = str(path_params.get(param, "") or "").strip()
        if not ref:
            continue
        states = before.get(kind, {})
        state = states.get(ref)
        if state is None:
            state = next((s for s in states.values() if agent_ops.entity_title(s) == ref), None)
        return agent_ops.entity_title(state) or ref
    return ""


def describe(action: str, path_params: dict[str, str], before: agent_journal.Snapshot, body: Any, count: int) -> str:
    """Human-readable one-liner for confirmations and journal rows."""
    label = ACTION_LABELS.get(action, action)
    title = _target_title(path_params, before)
    if not title and isinstance(body, dict):
        title = str(body.get("title") or body.get("habit") or "").strip()
    text = f"{label}「{title}」" if title else label
    if count > 1:
        text += f"（{count} 条）"
    return text


def _profile_dir(name: str) -> Path | None:
    try:
        clean = profile_io.validate_profile_name(name)
    except ValueError:
        return None
    if clean not in profile_io.list_profiles():
        return None
    return profile_io.profile_dir(clean)


async def agent_write_guard(connection: HTTPConnection) -> AsyncIterator[None]:
    """App-level dependency; a no-op for humans, reads and WebSockets.

    Typed as ``HTTPConnection`` because app-level dependencies also run on
    WebSocket routes (the workshop terminal), where ``Request`` cannot be
    injected.
    """
    if not isinstance(connection, Request) or connection.method not in MUTATING_METHODS:
        yield
        return
    request = connection
    route = request.scope.get("route")
    template = str(getattr(route, "path", "") or "")
    if not template.startswith("/api/v1/") or (
        template.startswith("/api/v1/auth/") and template not in AGENT_FORBIDDEN_AUTH_ROUTES
    ):
        yield
        return
    # Local import: auth imports routes_v1 helpers indirectly.
    from nblane.web_api.auth import _resolve_request_user
    from nblane.web_api.routes_v1 import ApiError

    user = _resolve_request_user(request)
    if user is None or not agent_policy.is_agent(user):
        yield
        return
    action = action_for(request.method, template)
    tier = agent_policy.tier_for(action)
    if tier == agent_policy.T0:
        yield
        return
    if tier == agent_policy.T3:
        raise ApiError(
            403,
            "agent_forbidden",
            "这个操作只能由用户在 nblane 页面上完成，助手不能代办。",
        )
    pdir = _profile_dir(str(request.path_params.get("name", "")))
    if pdir is None:
        # Let the route answer 400/404 itself.
        yield
        return
    body = await _read_body(request)
    path_params = dict(request.path_params)
    count = _batch_count(body)
    try:
        write = await run_in_threadpool(
            lambda: agent_ops.begin(
                pdir,
                actor=user.id,
                action=action,
                kinds=ACTION_KINDS.get(action, ()),
                fingerprint=agent_policy.fingerprint(request.method, request.url.path, body),
                describe=lambda before: describe(action, path_params, before, body, count),
                count=count,
                confirm_id=request.headers.get(agent_policy.CONFIRM_HEADER, ""),
            )
        )
    except agent_ops.ConfirmationRequired as exc:
        pending = exc.pending
        raise ApiError(
            428,
            "confirmation_invalid" if exc.invalid else "confirmation_required",
            (
                ("确认码无效或已过期，请重新确认。" if exc.invalid else "")
                + f"这一步需要用户在聊天里确认：{pending.summary}。用户同意后，在同一请求上加 "
                f"{agent_policy.CONFIRM_HEADER}: {pending.confirm_id} 重发（10 分钟内有效）。"
            ),
            extra={"confirmation": pending.public()},
        ) from None

    try:
        yield
    except Exception:
        agent_ops.abort(write)
        raise
    await run_in_threadpool(agent_ops.finish, write)
