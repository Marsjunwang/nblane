"""Privacy-safe workspace graph read model."""

from __future__ import annotations

from typing import Any

from nblane.core.evidence_review import EVIDENCE_REVIEW_PAGE
from nblane.core.growth_graph_contract import (
    growth_graph_edge_types,
    growth_graph_layers,
    growth_graph_node_type_roles,
    growth_graph_node_types,
    growth_graph_payload as growth_graph_contract_payload,
)
from nblane.core.goals import Goal, GoalSkillLink, goal_for_ui

WORKSPACE_GRAPH_LAYERS: tuple[str, ...] = growth_graph_layers()
WORKSPACE_GRAPH_NODE_TYPES: tuple[str, ...] = growth_graph_node_types()
WORKSPACE_GRAPH_EDGE_TYPES: tuple[str, ...] = growth_graph_edge_types()
_NODE_TYPE_ROLES: dict[str, str] = growth_graph_node_type_roles()


def workspace_graph_layers() -> tuple[str, ...]:
    """Return the stable Growth Graph layer order."""
    return growth_graph_layers()


def workspace_graph_node_types() -> tuple[str, ...]:
    """Return supported workspace graph node types."""
    return growth_graph_node_types()


def workspace_graph_edge_types() -> tuple[str, ...]:
    """Return supported workspace graph edge types."""
    return growth_graph_edge_types()


def workspace_graph_node_type_roles() -> dict[str, str]:
    """Return node type -> visual role mapping (star-tree prototypes)."""
    return growth_graph_node_type_roles()


def _role_for_type(node_type: str) -> str:
    """Return the contract visual role for a node type ("" when out of tree)."""
    return _NODE_TYPE_ROLES.get(str(node_type or ""), "")


def _ui_text(ui: dict[str, str] | None, key: str, fallback: str = "") -> str:
    if not ui:
        return fallback or key
    return str(ui.get(key, fallback or key))


def _node(
    *,
    id: str,
    type: str,
    layer: str,
    label: str,
    metric: str = "",
    status: str = "",
    record_id: str = "",
    owner_path: str = "",
    implemented: bool = True,
    placeholder: bool = False,
    locked: bool = False,
    suggested: bool = False,
    is_primary: bool = False,
    summary: str = "",
    description: str = "",
    role: str = "",
    primary_action: dict[str, object] | None = None,
    secondary_actions: list[dict[str, object]] | None = None,
    **extra: object,
) -> dict[str, object]:
    node = {
        "id": id,
        "type": type,
        "layer": layer,
        "role": role or _role_for_type(type),
        "label": label,
        "metric": metric,
        "status": status,
        "record_id": record_id,
        "owner_path": owner_path,
        "implemented": implemented,
        "placeholder": placeholder,
        "locked": locked,
        "suggested": suggested,
        "is_primary": is_primary,
        "summary": summary,
        "description": description,
        "primary_action": primary_action or {},
        "secondary_actions": list(secondary_actions or []),
        **extra,
    }
    if not node["primary_action"]:
        action = _default_node_action(node)
        if action:
            node["primary_action"] = action
    return node


def _edge(
    from_id: str,
    to_id: str,
    type: str,
    *,
    suggested: bool = False,
    placeholder: bool = False,
    relation: str = "",
    **extra: object,
) -> dict[str, object]:
    return {
        "from": from_id,
        "to": to_id,
        "type": type,
        "relation": relation or type,
        "suggested": suggested,
        "placeholder": placeholder,
        **extra,
    }


def _navigate_action(
    *,
    id: str,
    label: str,
    path: str,
    kind: str = "navigate",
) -> dict[str, object]:
    return {
        "id": id,
        "label": label,
        "event": {
            "action": "navigate" if kind == "navigate" else kind,
            "payload": {"path": path},
        },
    }


def _default_node_action(node: dict[str, object]) -> dict[str, object]:
    owner_path = str(node.get("owner_path") or "")
    if owner_path == "profile_context":
        return {
            "id": "open_profile_context",
            "label": "Edit Profile Context",
            "event": {
                "action": "set_north_star_display_open_profile_context",
                "payload": {},
            },
        }
    if owner_path and node.get("implemented") is not False:
        return _navigate_action(
            id=f"open:{owner_path}",
            label="Open",
            path=owner_path,
        )
    return {}


def _graph_action(
    *,
    id: str,
    node_id: str,
    label: str,
    path: str = "",
    action: str = "navigate",
    payload: dict[str, object] | None = None,
    severity: str = "",
) -> dict[str, object]:
    event_payload = dict(payload or {})
    if path and "path" not in event_payload:
        event_payload["path"] = path
    return {
        "id": id,
        "node_id": node_id,
        "label": label,
        "severity": severity,
        "event": {
            "action": action,
            "payload": event_payload,
        },
    }


def _goal_graph_label(
    goal_payload: dict[str, Any],
    ui: dict[str, str] | None,
    *,
    fallback_key: str = "dashboard_graph_goal_missing",
) -> str:
    projection = goal_payload.get("projection")
    if isinstance(projection, dict):
        return str(
            projection.get("title")
            or projection.get("label")
            or _ui_text(ui, "goal_strip_hidden", "Goal set")
        )
    if goal_payload.get("locked"):
        return _ui_text(ui, "goal_private_locked", "Private goal")
    return _ui_text(ui, fallback_key, "Set current goal")


def _goal_payload_from_goal(goal: Goal | None) -> dict[str, object]:
    projection = goal_for_ui(goal)
    locked = goal is not None and projection is None
    return {
        "is_set": goal is not None,
        "locked": locked,
        "projection": projection,
    }


def _safe_goal_skill_links(goal: Goal | None) -> list[GoalSkillLink]:
    if goal is None or goal.ui_visibility == "private":
        return []
    return list(goal.skill_links)


def _suggested_skill_nodes(skills: dict[str, Any]) -> list[dict[str, object]]:
    skill_nodes = list(skills.get("target_learning_locked") or [])
    if not skill_nodes:
        skill_nodes = list(skills.get("evidence_risk_nodes") or [])
    out: list[dict[str, object]] = []
    for node in skill_nodes:
        if not isinstance(node, dict):
            continue
        out.append(
            {
                "node_id": str(node.get("id") or ""),
                "label": str(node.get("label") or node.get("id") or ""),
                "metric": str(node.get("status") or ""),
                "suggested": True,
            }
        )
    return out


def _clean_string_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        raw_items = [
            item
            for chunk in value.splitlines()
            for item in chunk.split(",")
        ]
    elif isinstance(value, (list, tuple, set)):
        raw_items = list(value)
    else:
        raw_items = []
    out: list[str] = []
    seen: set[str] = set()
    for item in raw_items:
        text = str(item or "").strip()
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _node_id_part(value: object, fallback: str = "item") -> str:
    text = "_".join(str(value or "").strip().split())
    if not text:
        return fallback
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789:._-")
    cleaned = "".join(ch if ch in allowed else "_" for ch in text).strip("_")
    return cleaned or fallback


def _ref_node(mapping: dict[str, str], ref: object) -> str:
    text = str(ref or "").strip()
    if not text:
        return ""
    candidates = [text]
    if text.startswith("kanban:"):
        candidates.append(text.split(":", 1)[1])
    else:
        candidates.append(f"kanban:{text}")
    for candidate in candidates:
        found = mapping.get(candidate)
        if found:
            return found
    return ""


def _non_draft_status(value: object) -> bool:
    status = str(value or "").strip().lower()
    return bool(status and status != "draft")


def _runtime_placeholder_needed(current: int, minimum: int) -> int:
    return max(0, int(minimum) - max(0, int(current)))


def _task_lifecycle_label(lifecycle: str, ui: dict[str, str] | None) -> str:
    clean = str(lifecycle or "").strip().lower()
    labels = {
        "active": _ui_text(ui, "dashboard_metric_doing", "Doing"),
        "queued": _ui_text(ui, "dashboard_metric_queue", "Queue"),
        "done": _ui_text(ui, "dashboard_metric_done", "Done"),
        "someday": _ui_text(ui, "dashboard_metric_someday", "Someday"),
        "archived": _ui_text(ui, "dashboard_metric_archived", "archived"),
    }
    return labels.get(clean, clean or _ui_text(ui, "dashboard_metric_doing", "Doing"))


def _task_status(item: dict[str, Any]) -> str:
    if item.get("blocked_by"):
        return "risk"
    lifecycle = str(item.get("lifecycle") or "").strip().lower()
    if lifecycle == "active":
        return "active"
    if lifecycle in {"queued", "done", "someday", "archived"}:
        return lifecycle
    return lifecycle or "active"


def _clean_item_rows(value: object, *, limit: int = 120) -> list[dict[str, Any]]:
    rows = value if isinstance(value, list) else []
    out: list[dict[str, Any]] = []
    for item in rows:
        if isinstance(item, dict):
            out.append(item)
        if len(out) >= limit:
            break
    return out


def _short_text(value: object, fallback: str = "", *, max_len: int = 92) -> str:
    text = " ".join(str(value or "").split())
    if not text:
        text = fallback
    if len(text) <= max_len:
        return text
    return f"{text[: max_len - 1].rstrip()}..."


def _private_label(
    ui: dict[str, str] | None,
    key: str,
    fallback: str,
    record_id: str = "",
) -> str:
    base = _ui_text(ui, key, fallback)
    if not record_id:
        return base
    tail = record_id.rsplit(":", 1)[-1]
    return f"{base} · {tail}" if tail else base


def _dedupe_nodes(nodes: list[dict[str, object]]) -> list[dict[str, object]]:
    seen: set[str] = set()
    out: list[dict[str, object]] = []
    for node in nodes:
        node_id = str(node.get("id") or "").strip()
        if not node_id or node_id in seen:
            continue
        seen.add(node_id)
        out.append(node)
    return out


def _filter_edges(
    edges: list[dict[str, object]],
    nodes: list[dict[str, object]],
) -> list[dict[str, object]]:
    node_ids = {str(node.get("id") or "") for node in nodes}
    out: list[dict[str, object]] = []
    seen: set[tuple[str, str, str]] = set()
    for edge in edges:
        from_id = str(edge.get("from") or "")
        to_id = str(edge.get("to") or "")
        edge_type = str(edge.get("type") or "")
        key = (from_id, to_id, edge_type)
        if not from_id or not to_id or from_id not in node_ids or to_id not in node_ids:
            continue
        if key in seen:
            continue
        seen.add(key)
        out.append(edge)
    return out


def _primary_goal_node_id(
    goal_node_ids: dict[str, str],
    primary_goal_id: str,
) -> str:
    if primary_goal_id and primary_goal_id in goal_node_ids:
        return goal_node_ids[primary_goal_id]
    if goal_node_ids:
        return next(iter(goal_node_ids.values()))
    return "goal:missing"


def workspace_graph_payload(
    *,
    north_star: dict[str, Any],
    primary_goal: dict[str, Any],
    primary_goal_id: str,
    active_goals: list[Goal],
    kanban: dict[str, Any],
    skills: dict[str, Any],
    pending: dict[str, Any],
    public: dict[str, Any],
    health: dict[str, Any],
    sources: dict[str, Any] | None = None,
    projects: dict[str, Any] | None = None,
    claims: dict[str, Any] | None = None,
    ui: dict[str, str] | None = None,
    all_goals: list[Goal] | None = None,
    view: str = "context",
) -> dict[str, Any]:
    """Build a privacy-safe Growth Graph context payload."""
    nodes: list[dict[str, object]] = []
    edges: list[dict[str, object]] = []
    graph_actions: list[dict[str, object]] = []
    attention_nodes: list[dict[str, object]] = []

    if north_star.get("locked"):
        label = _ui_text(ui, "north_star_private_display", "Private North Star")
    elif north_star.get("is_set"):
        label = str(
            north_star.get("display_text")
            or _ui_text(ui, "north_star_hidden_display", "North Star set")
        )
    else:
        label = _ui_text(ui, "north_star_empty", "No North Star set")
    nodes.append(
        _node(
            id="north_star",
            type="north_star",
            layer="direction",
            label=label,
            metric=_ui_text(ui, "north_star_strip_title", "North Star"),
            status=(
                "private"
                if north_star.get("locked")
                else "active"
                if north_star.get("is_set")
                else "missing"
            ),
            locked=bool(north_star.get("locked")),
            owner_path="profile_context",
            implemented=bool(north_star.get("is_set")),
            placeholder=not bool(north_star.get("is_set")),
            suggested=not bool(north_star.get("is_set")),
        )
    )

    goal_node_ids: dict[str, str] = {}
    shown_goals = [goal for goal in (all_goals or active_goals) if goal.id]
    if not shown_goals:
        nodes.append(
            _node(
                id="goal:missing",
                type="goal",
                layer="objective",
                label=_goal_graph_label(primary_goal, ui),
                metric=_ui_text(ui, "dashboard_primary_goal", "Primary goal"),
                status="missing",
                placeholder=True,
                implemented=False,
                suggested=True,
                is_primary=True,
            )
        )
        edges.append(
            _edge(
                "north_star",
                "goal:missing",
                "alignment",
                suggested=True,
                placeholder=True,
            )
        )

    for goal_obj in shown_goals:
        payload = _goal_payload_from_goal(goal_obj)
        node_id = f"goal:{goal_obj.id}"
        goal_node_ids[goal_obj.id] = node_id
        is_primary = bool(goal_obj.id and goal_obj.id == primary_goal_id)
        nodes.append(
            _node(
                id=node_id,
                type="goal",
                layer="objective",
                label=_goal_graph_label(
                    payload,
                    ui,
                    fallback_key=(
                        "dashboard_primary_goal"
                        if is_primary
                        else "dashboard_active_goal"
                    ),
                ),
                metric=_ui_text(
                    ui,
                    "dashboard_primary_goal" if is_primary else "dashboard_active_goal",
                    "Primary goal" if is_primary else "Active goal",
                ),
                record_id=goal_obj.id,
                status="private" if payload.get("locked") else goal_obj.status,
                locked=bool(payload.get("locked")),
                is_primary=is_primary,
            )
        )
        edges.append(_edge("north_star", node_id, "alignment"))

    primary_node_id = _primary_goal_node_id(goal_node_ids, primary_goal_id)

    project_summary = projects or {}
    project_cases = [
        item
        for item in list(project_summary.get("cases") or [])
        if isinstance(item, dict) and str(item.get("id") or "").strip()
    ][:40]
    project_node_ids: list[str] = []
    project_node_by_id: dict[str, str] = {}
    if project_cases:
        for case in project_cases:
            record_id = str(case.get("id") or "").strip()
            node_id = record_id
            project_node_ids.append(node_id)
            project_node_by_id[record_id] = node_id
            is_private = str(case.get("visibility") or "private") == "private"
            nodes.append(
                _node(
                    id=node_id,
                    type="project_case",
                    layer="work_context",
                    # Owner-facing graph: show the real title (the dashboard is the
                    # user's own operating view). `locked` still carries privacy so
                    # downstream styling/badges can mark it.
                    label=str(case.get("title") or record_id),
                    metric=str(case.get("kind") or ""),
                    record_id=record_id,
                    status=str(case.get("status") or ""),
                    locked=is_private,
                    owner_path="pages/11_Project_Board.py",
                    implemented=True,
                )
            )
            goal_refs = [
                str(ref or "").strip()
                for ref in (case.get("goal_refs") or [])
                if str(ref or "").strip()
            ]
            linked_goals = [
                goal_node_ids[ref]
                for ref in goal_refs
                if ref in goal_node_ids
            ]
            if not linked_goals:
                linked_goals = [primary_node_id]
            for goal_node_id in linked_goals:
                edges.append(_edge(goal_node_id, node_id, "contains"))
    else:
        project_node_ids.append("project_case:planned")
        nodes.append(
            _node(
                id="project_case:planned",
                type="project_case",
                layer="work_context",
                label=_ui_text(ui, "dashboard_node_project_case", "Project Cases"),
                metric=_ui_text(ui, "dashboard_placeholder_metric", "planned"),
                status="planned",
                implemented=False,
                placeholder=True,
                suggested=True,
            )
        )
        edges.append(
            _edge(
                primary_node_id,
                "project_case:planned",
                "contains",
                placeholder=True,
            )
        )

    placeholder_chain = (
        (
            "daily_work:planned",
            "daily_work",
            "activity",
            _ui_text(ui, "dashboard_node_daily_work", "Daily Work"),
            "planned",
        ),
        (
            "research:planned",
            "research",
            "activity",
            _ui_text(ui, "dashboard_node_research", "Research"),
            "planned",
        ),
        (
            "agent_run:planned",
            "agent_run",
            "activity",
            _ui_text(ui, "dashboard_node_agent_run", "Agent Runs"),
            "planned",
        ),
    )
    for node_id, node_type, layer, label, status in placeholder_chain:
        nodes.append(
            _node(
                id=node_id,
                type=node_type,
                layer=layer,
                label=label,
                metric=_ui_text(ui, "dashboard_placeholder_metric", "planned"),
                status=status,
                implemented=False,
                placeholder=True,
                suggested=True,
            )
        )

    project_anchor_id = project_node_ids[0]
    for activity_id in ("daily_work:planned", "research:planned", "agent_run:planned"):
        edges.append(
            _edge(
                project_anchor_id,
                activity_id,
                "contains",
                suggested=True,
                placeholder=project_anchor_id == "project_case:planned",
            )
        )

    task_node_ids: list[str] = []
    task_node_by_ref: dict[str, str] = {}
    task_items = _clean_item_rows(kanban.get("tasks"), limit=260)
    if not task_items:
        task_items = _clean_item_rows(kanban.get("doing"), limit=40)
        for item in task_items:
            item.setdefault("lifecycle", "active")
            item.setdefault("archived", False)
    for idx, item in enumerate(task_items):
        if not isinstance(item, dict):
            continue
        task_id = str(item.get("id") or "").strip()
        node_id = f"task:{_node_id_part(task_id, str(idx))}"
        if node_id in task_node_ids:
            node_id = f"task:{_node_id_part(task_id, str(idx))}:{idx}"
        lifecycle = str(item.get("lifecycle") or "active").strip().lower()
        status = _task_status(item)
        task_node_ids.append(node_id)
        if task_id:
            task_node_by_ref[task_id] = node_id
            task_node_by_ref[f"kanban:{task_id}"] = node_id
        nodes.append(
            _node(
                id=node_id,
                type="task",
                layer="activity",
                label=str(item.get("title") or ""),
                metric=(
                    _ui_text(ui, "dashboard_graph_blocked", "blocked")
                    if item.get("blocked_by")
                    else _task_lifecycle_label(lifecycle, ui)
                ),
                status=status,
                record_id=task_id,
                owner_path="pages/3_Kanban.py",
                lifecycle=lifecycle,
                archived=bool(item.get("archived")),
                meta={
                    "project_id": str(item.get("project_id") or "").strip(),
                    "kanban_ref": f"kanban:{task_id}" if task_id else "",
                },
            )
        )
        edges.append(_edge(primary_node_id, node_id, "drives"))
        project_id = str(item.get("project_id") or "").strip()
        task_project_id = project_node_by_id.get(project_id, project_anchor_id)
        edges.append(
            _edge(
                task_project_id,
                node_id,
                "contains",
                placeholder=task_project_id == "project_case:planned",
            )
        )

    source_summary = sources or {}
    source_active = int(source_summary.get("active_total") or 0)
    source_total = int(source_summary.get("inbox_total") or 0)
    source_implemented = source_total > 0 or bool(source_summary.get("implemented"))
    nodes.append(
        _node(
            id="source:inbox",
            type="source",
            layer="source",
            label=_ui_text(ui, "dashboard_source_inbox_title", "Inbox sources"),
            metric=str(source_active),
            status="pending" if source_active else "clear",
            owner_path="pages/7_Research.py",
            implemented=source_implemented,
            placeholder=not source_implemented,
            suggested=not source_implemented,
            primary_action=_navigate_action(
                id="review_source_inbox" if source_active else "capture_source_inbox",
                label=(
                    _ui_text(ui, "dashboard_action_review_source", "Review source")
                    if source_active
                    else _ui_text(ui, "dashboard_action_capture_source", "Capture source")
                ),
                path="pages/7_Research.py",
            ),
            secondary_actions=[
                _navigate_action(
                    id="open_research",
                    label=_ui_text(ui, "dashboard_open_research", "Open Research"),
                    path="pages/7_Research.py",
                )
            ],
        )
    )
    edges.append(_edge(primary_node_id, "source:inbox", "contains"))
    for node_id in task_node_ids[:8]:
        edges.append(_edge(node_id, "source:inbox", "generated_by", suggested=True))
    for activity_id in ("daily_work:planned", "research:planned", "agent_run:planned"):
        edges.append(
            _edge(activity_id, "source:inbox", "generated_by", placeholder=True, suggested=True)
        )

    source_node_by_ref: dict[str, str] = {}
    source_items = _clean_item_rows(source_summary.get("items"), limit=120)
    for source in source_items:
        source_id = str(source.get("id") or "").strip()
        if not source_id:
            continue
        node_id = source_id if source_id != "source:inbox" else f"source:item:{len(source_node_by_ref) + 1}"
        source_node_by_ref[source_id] = node_id
        private = str(source.get("visibility") or "private") == "private"
        nodes.append(
            _node(
                id=node_id,
                type="source",
                layer="source",
                # Owner-facing: show the real source title (privacy kept in `locked`).
                label=_short_text(source.get("title"), source_id),
                metric=str(source.get("kind") or source.get("origin") or ""),
                record_id=source_id,
                status=str(source.get("status") or ""),
                locked=private,
                owner_path="pages/7_Research.py",
                summary=_short_text(source.get("summary"), max_len=180),
                item_kind="source",
                meta={
                    "tags": _clean_string_list(source.get("tags")),
                    "goal_refs": _clean_string_list(source.get("goal_refs")),
                    "project_refs": _clean_string_list(source.get("project_refs")),
                    "evidence_refs": _clean_string_list(source.get("evidence_refs")),
                },
            )
        )
        edges.append(_edge("source:inbox", node_id, "contains"))
        for goal_ref in _clean_string_list(source.get("goal_refs")):
            goal_node_id = goal_node_ids.get(goal_ref)
            if goal_node_id:
                edges.append(_edge(goal_node_id, node_id, "contains"))
        for project_ref in _clean_string_list(source.get("project_refs")):
            project_node_id = project_node_by_id.get(project_ref)
            if project_node_id:
                edges.append(_edge(project_node_id, node_id, "contains"))

    sand_count = sum(1 for node in nodes if str(node.get("role") or "") == "sand")
    for idx in range(_runtime_placeholder_needed(sand_count, 36)):
        placeholder_id = f"source:placeholder:{idx + 1}"
        nodes.append(
            _node(
                id=placeholder_id,
                type="source",
                layer="source",
                role="sand",
                label=_ui_text(ui, "dashboard_source_ambient", "Ambient source"),
                metric=_ui_text(ui, "dashboard_placeholder_metric", "planned"),
                status="planned",
                implemented=False,
                placeholder=True,
                suggested=True,
                synthetic=True,
                item_kind="runtime_sand",
                meta={
                    "tags": ["runtime-placeholder"],
                    "synthetic": True,
                    "source_counts_excluded": True,
                },
            )
        )
        edges.append(
            _edge(
                "source:inbox",
                placeholder_id,
                "contains",
                placeholder=True,
                suggested=True,
            )
        )

    candidate_count = int(pending.get("done_uncrystallized_count") or 0)
    unlinked_count = int(pending.get("unlinked_count") or 0)
    needs_review_count = int(pending.get("needs_review_count") or 0)
    status_risk_count = int(pending.get("status_risk_count") or 0)
    atomic_attention_count = (
        unlinked_count + needs_review_count + status_risk_count
    )
    nodes.append(
        _node(
            id="evidence_candidate:pending",
            type="evidence_candidate",
            layer="evidence",
            label=_ui_text(ui, "dashboard_evidence_candidate_title", "Evidence candidates"),
            metric=str(candidate_count),
            status="pending" if candidate_count else "clear",
            owner_path=EVIDENCE_REVIEW_PAGE,
            placeholder=False,
        )
    )
    nodes.append(
        _node(
            id="atomic_evidence:pool",
            type="atomic_evidence",
            layer="evidence",
            label=_ui_text(ui, "dashboard_atomic_evidence_title", "Atomic evidence"),
            metric=str(atomic_attention_count),
            status="pending" if atomic_attention_count else "clear",
            owner_path=EVIDENCE_REVIEW_PAGE,
        )
    )
    nodes.append(
        _node(
            id="composite_evidence:planned",
            type="composite_evidence",
            layer="evidence",
            label=_ui_text(ui, "dashboard_node_composite_evidence", "Composite Evidence"),
            metric=_ui_text(ui, "dashboard_placeholder_metric", "planned"),
            status="planned",
            implemented=False,
            placeholder=True,
            suggested=True,
        )
    )
    edges.append(
        _edge(
            "source:inbox",
            "evidence_candidate:pending",
            "source_to_candidate",
            suggested=not bool(candidate_count),
        )
    )
    edges.append(
        _edge(
            "evidence_candidate:pending",
            "atomic_evidence:pool",
            "review",
            suggested=not bool(candidate_count),
        )
    )
    edges.append(
        _edge(
            "atomic_evidence:pool",
            "composite_evidence:planned",
            "derives",
            placeholder=True,
            suggested=True,
        )
    )
    evidence_by_project = project_summary.get("evidence_by_project") or {}
    if isinstance(evidence_by_project, dict):
        for node_id in project_node_ids:
            if not node_id.startswith("project:"):
                continue
            if evidence_by_project.get(node_id):
                edges.append(_edge(node_id, "atomic_evidence:pool", "supports"))
    source_by_project = project_summary.get("source_by_project") or {}
    if isinstance(source_by_project, dict):
        for node_id in project_node_ids:
            if not node_id.startswith("project:"):
                continue
            if source_by_project.get(node_id):
                edges.append(_edge(node_id, "source:inbox", "contains"))

    evidence_node_by_ref: dict[str, str] = {}
    evidence_items = _clean_item_rows(pending.get("evidence_rows"), limit=160)
    for evidence in evidence_items:
        evidence_id = str(evidence.get("id") or "").strip()
        if not evidence_id:
            continue
        node_id = f"atomic_evidence:{evidence_id}"
        evidence_node_by_ref[evidence_id] = node_id
        private = str(evidence.get("public_readiness") or "private") == "private"
        review_status = str(evidence.get("review_status") or "")
        nodes.append(
            _node(
                id=node_id,
                type="atomic_evidence",
                layer="evidence",
                # Owner-facing: real evidence title (privacy kept in `locked`).
                label=_short_text(evidence.get("title"), evidence_id),
                metric=str(evidence.get("strength") or evidence.get("type") or ""),
                record_id=evidence_id,
                status=review_status or str(evidence.get("confidence") or ""),
                locked=private,
                owner_path=EVIDENCE_REVIEW_PAGE,
                summary=_short_text(evidence.get("summary"), max_len=220),
                item_kind="evidence",
                meta={
                    "source_refs": _clean_string_list(evidence.get("source_refs")),
                    "project_refs": _clean_string_list(evidence.get("project_refs")),
                    "skill_refs": _clean_string_list(evidence.get("skill_refs")),
                    "kanban_refs": _clean_string_list(evidence.get("kanban_refs")),
                },
            )
        )
        edges.append(_edge("atomic_evidence:pool", node_id, "contains"))
        if review_status != "reviewed":
            edges.append(_edge("evidence_candidate:pending", node_id, "review", suggested=True))
        for source_ref in _clean_string_list(evidence.get("source_refs")):
            source_node_id = source_node_by_ref.get(source_ref)
            if source_node_id:
                edges.append(_edge(source_node_id, node_id, "source_to_candidate"))
        for project_ref in _clean_string_list(evidence.get("project_refs")):
            project_node_id = project_node_by_id.get(project_ref)
            if project_node_id:
                edges.append(_edge(project_node_id, node_id, "supports"))
        for task_ref in _clean_string_list(evidence.get("kanban_refs")):
            task_node_id = _ref_node(task_node_by_ref, task_ref)
            if task_node_id:
                edges.append(_edge(task_node_id, node_id, "generated_by"))

    for source in source_items:
        source_id = str(source.get("id") or "").strip()
        source_node_id = source_node_by_ref.get(source_id)
        if not source_node_id:
            continue
        for evidence_ref in _clean_string_list(source.get("evidence_refs")):
            evidence_node_id = evidence_node_by_ref.get(evidence_ref)
            if evidence_node_id:
                edges.append(_edge(source_node_id, evidence_node_id, "source_to_candidate"))

    for case in project_cases:
        project_ref = str(case.get("id") or "").strip()
        project_node_id = project_node_by_id.get(project_ref)
        if not project_node_id:
            continue
        for task_ref in _clean_string_list(case.get("task_refs")):
            task_node_id = _ref_node(task_node_by_ref, task_ref)
            if task_node_id:
                edges.append(_edge(project_node_id, task_node_id, "contains"))
        for source_ref in _clean_string_list(case.get("source_refs")):
            source_node_id = source_node_by_ref.get(source_ref)
            if source_node_id:
                edges.append(_edge(project_node_id, source_node_id, "contains"))
        for evidence_ref in _clean_string_list(case.get("evidence_refs")):
            evidence_node_id = evidence_node_by_ref.get(evidence_ref)
            if evidence_node_id:
                edges.append(_edge(project_node_id, evidence_node_id, "supports"))

    claim_summary = claims or {}
    accepted_claims = int(claim_summary.get("accepted_count") or 0)
    draft_claims = int(claim_summary.get("draft_count") or 0)
    needs_refresh_claims = int(claim_summary.get("needs_refresh_count") or 0)
    claim_node_id = "claim:accepted" if accepted_claims or draft_claims else "claim:planned"
    nodes.append(
        _node(
            id=claim_node_id,
            type="claim",
            layer="claim",
            label=_ui_text(ui, "dashboard_node_claim", "Claims"),
            metric=(
                str(accepted_claims)
                if accepted_claims or draft_claims
                else _ui_text(ui, "dashboard_placeholder_metric", "planned")
            ),
            status=(
                "risk"
                if needs_refresh_claims
                else "draft"
                if draft_claims
                else "accepted"
                if accepted_claims
                else "planned"
            ),
            owner_path=EVIDENCE_REVIEW_PAGE,
            implemented=bool(accepted_claims or draft_claims),
            placeholder=not bool(accepted_claims or draft_claims),
            suggested=not bool(accepted_claims or draft_claims),
            summary=_ui_text(
                ui,
                "dashboard_claim_summary",
                "Claims translate reviewed evidence into skill and output assertions.",
            ),
        )
    )
    edges.append(
        _edge(
            "composite_evidence:planned",
            claim_node_id,
            "supports",
            placeholder=True,
            suggested=True,
        )
    )

    claim_node_by_ref: dict[str, str] = {}
    claim_items = _clean_item_rows(claim_summary.get("items"), limit=140)
    for claim in claim_items:
        claim_id = str(claim.get("id") or "").strip()
        if not claim_id:
            continue
        node_id = f"claim:item:{claim_id}"
        claim_node_by_ref[claim_id] = node_id
        private = str(claim.get("public_readiness") or "private") == "private"
        nodes.append(
            _node(
                id=node_id,
                type="claim",
                layer="claim",
                # Owner-facing: real claim text (privacy kept in `locked`).
                label=_short_text(claim.get("text"), claim_id, max_len=82),
                metric=str(claim.get("type") or ""),
                record_id=claim_id,
                status=str(claim.get("refresh_status") or claim.get("status") or ""),
                locked=private,
                owner_path=EVIDENCE_REVIEW_PAGE,
                summary=_short_text(claim.get("text"), max_len=220),
                item_kind="claim",
            )
        )
        edges.append(_edge(claim_node_id, node_id, "contains"))
        for evidence_ref in _clean_string_list(claim.get("evidence_refs")):
            evidence_node_id = evidence_node_by_ref.get(evidence_ref)
            if evidence_node_id:
                edges.append(_edge(evidence_node_id, node_id, "supports"))
        for source_ref in _clean_string_list(claim.get("source_refs")):
            source_node_id = source_node_by_ref.get(source_ref)
            if source_node_id:
                edges.append(_edge(source_node_id, node_id, "source_to_candidate"))
        for project_ref in _clean_string_list(claim.get("project_refs")):
            project_node_id = project_node_by_id.get(project_ref)
            if project_node_id:
                edges.append(_edge(project_node_id, node_id, "supports"))
        for goal_ref in _clean_string_list(claim.get("goal_refs")):
            goal_node_id = goal_node_ids.get(goal_ref)
            if goal_node_id:
                edges.append(_edge(goal_node_id, node_id, "supports"))

    skill_nodes: dict[str, dict[str, object]] = {}
    for goal_obj in shown_goals:
        for link in _safe_goal_skill_links(goal_obj):
            if not link.node_id:
                continue
            skill_node_id = f"skill:{link.node_id}"
            skill_nodes.setdefault(
                skill_node_id,
                _node(
                    id=skill_node_id,
                    type="skill",
                    layer="capability",
                    label=link.label or link.node_id,
                    metric=link.source,
                    record_id=link.node_id,
                    owner_path="pages/1_Skill_Tree.py",
                ),
            )
            goal_node_id = goal_node_ids.get(goal_obj.id)
            if goal_node_id:
                edges.append(_edge(goal_node_id, skill_node_id, "drives"))
    skill_items = _clean_item_rows(skills.get("items"), limit=260)
    for item in skill_items:
        skill_id = str(item.get("id") or "").strip()
        if not skill_id:
            continue
        skill_node_id = f"skill:{skill_id}"
        skill_nodes.setdefault(
            skill_node_id,
            _node(
                id=skill_node_id,
                type="skill",
                layer="capability",
                label=str(item.get("label") or skill_id),
                metric=str(item.get("category") or ""),
                record_id=skill_id,
                status=str(item.get("status") or ""),
                owner_path="pages/1_Skill_Tree.py",
                meta={
                    "category": str(item.get("category") or ""),
                    "evidence_refs": _clean_string_list(item.get("evidence_refs")),
                },
            ),
        )
    if not skill_nodes:
        for idx, item in enumerate(_suggested_skill_nodes(skills)[:4]):
            node_id = f"skill:suggested:{idx}"
            skill_nodes[node_id] = _node(
                id=node_id,
                type="skill",
                layer="capability",
                label=str(item.get("label") or item.get("node_id") or ""),
                metric=_ui_text(ui, "skill_alignment_suggested", "suggested"),
                record_id=str(item.get("node_id") or ""),
                status=str(item.get("metric") or ""),
                owner_path="pages/1_Skill_Tree.py",
                placeholder=True,
                suggested=True,
            )
            edges.append(_edge(primary_node_id, node_id, "drives", suggested=True))
    if not skill_nodes:
        node_id = "skill:lit"
        skill_nodes[node_id] = _node(
            id=node_id,
            type="skill",
            layer="capability",
            label=_ui_text(ui, "dashboard_metric_skill_lit", "Skill lit"),
            metric=f"{skills.get('lit', 0)}/{skills.get('total', 0)}",
            owner_path="pages/1_Skill_Tree.py",
            placeholder=True,
            suggested=True,
        )
        edges.append(_edge(primary_node_id, node_id, "drives", suggested=True))
    nodes.extend(skill_nodes.values())
    skill_node_by_ref = {
        str(node.get("record_id") or "").strip(): node_id
        for node_id, node in skill_nodes.items()
        if str(node.get("record_id") or "").strip()
    }

    for evidence in evidence_items:
        evidence_node_id = evidence_node_by_ref.get(str(evidence.get("id") or "").strip())
        if not evidence_node_id:
            continue
        for skill_ref in _clean_string_list(evidence.get("skill_refs")):
            skill_node_id = skill_node_by_ref.get(skill_ref) or f"skill:{skill_ref}"
            if skill_node_id in skill_nodes:
                edges.append(_edge(evidence_node_id, skill_node_id, "supports"))

    for item in skill_items:
        skill_ref = str(item.get("id") or "").strip()
        skill_node_id = skill_node_by_ref.get(skill_ref) or f"skill:{skill_ref}"
        if skill_node_id not in skill_nodes:
            continue
        for evidence_ref in _clean_string_list(item.get("evidence_refs")):
            evidence_node_id = evidence_node_by_ref.get(evidence_ref)
            if evidence_node_id:
                edges.append(_edge(evidence_node_id, skill_node_id, "supports"))

    for claim in claim_items:
        claim_node_id_for_item = claim_node_by_ref.get(str(claim.get("id") or "").strip())
        if not claim_node_id_for_item:
            continue
        claim_evidence_node_ids = [
            evidence_node_by_ref[ref]
            for ref in _clean_string_list(claim.get("evidence_refs"))
            if ref in evidence_node_by_ref
        ]
        claim_skill_node_ids: list[str] = []
        for skill_ref in _clean_string_list(claim.get("skill_refs")):
            skill_node_id = skill_node_by_ref.get(skill_ref) or f"skill:{skill_ref}"
            if skill_node_id in skill_nodes:
                claim_skill_node_ids.append(skill_node_id)
                edges.append(_edge(claim_node_id_for_item, skill_node_id, "supports"))
        for evidence_node_id in claim_evidence_node_ids:
            for skill_node_id in claim_skill_node_ids:
                edges.append(
                    _edge(
                        evidence_node_id,
                        skill_node_id,
                        "supports",
                        suggested=True,
                        relation="claim_evidence_skill",
                    )
                )

    for node_id in list(skill_nodes)[:4]:
        edges.append(_edge(claim_node_id, node_id, "supports", placeholder=claim_node_id == "claim:planned", suggested=True))
        edges.append(_edge("atomic_evidence:pool", node_id, "supports"))

    gap_count = int(skills.get("evidence_risk_count") or 0) + len(
        list(skills.get("target_learning_locked") or [])
    )
    nodes.append(
        _node(
            id="gap:risk",
            type="gap",
            layer="capability",
            label=_ui_text(ui, "dashboard_gap_risk_title", "Gap risk"),
            metric=str(gap_count),
            status="risk" if gap_count else "clear",
            owner_path="pages/2_Gap_Analysis.py",
        )
    )
    nodes.append(
        _node(
            id="next_action:planned",
            type="next_action",
            layer="capability",
            label=_ui_text(ui, "dashboard_node_next_action", "Next Action"),
            metric=_ui_text(ui, "dashboard_placeholder_metric", "planned"),
            status="planned",
            owner_path="pages/2_Gap_Analysis.py",
            placeholder=True,
            suggested=True,
        )
    )
    edges.append(_edge("gap:risk", "next_action:planned", "drives", suggested=True))
    edges.append(_edge("next_action:planned", primary_node_id, "drives", suggested=True))

    raw_output_items = [
        *(_clean_item_rows(public.get("items"), limit=100)),
        *(_clean_item_rows(public.get("blog_items"), limit=100)),
        *(_clean_item_rows(public.get("project_items"), limit=100)),
    ]
    output_items = [
        item
        for item in raw_output_items
        if _non_draft_status(item.get("status"))
    ]
    real_output_count = len(output_items)
    output_implemented = bool(real_output_count or public.get("initialized"))
    nodes.append(
        _node(
            id="output",
            type="output",
            layer="output",
            label=_ui_text(ui, "dashboard_output_title", "Output"),
            metric=str(real_output_count or public.get("draft_total", 0)),
            status=(
                "published"
                if real_output_count
                else "draft"
                if public.get("draft_total")
                else "planned"
            ),
            owner_path="pages/6_Output_Studio.py",
            implemented=output_implemented,
            placeholder=not output_implemented,
            suggested=not bool(real_output_count),
        )
    )
    edges.append(_edge(claim_node_id, "output", "produces", placeholder=claim_node_id == "claim:planned", suggested=True))
    edges.append(_edge("atomic_evidence:pool", "output", "produces", suggested=not bool(real_output_count)))

    output_node_by_ref: dict[str, str] = {}
    output_refs_by_evidence: dict[str, list[str]] = {}
    output_leaf_ids: list[str] = []
    for idx, output_item in enumerate(output_items):
        output_id = str(output_item.get("id") or "").strip()
        if not output_id:
            continue
        node_id = f"output:item:{_node_id_part(output_id, str(idx))}"
        if node_id in output_leaf_ids:
            node_id = f"{node_id}:{idx}"
        output_node_by_ref[output_id] = node_id
        output_leaf_ids.append(node_id)
        nodes.append(
            _node(
                id=node_id,
                type="output",
                layer="output",
                label=_short_text(output_item.get("title"), output_id),
                metric=str(output_item.get("kind") or ""),
                record_id=output_id,
                status=str(output_item.get("status") or ""),
                owner_path="pages/6_Output_Studio.py",
                summary=_short_text(output_item.get("summary"), max_len=220),
                item_kind=str(output_item.get("kind") or "output"),
                meta={
                    "route": str(output_item.get("route") or ""),
                    "evidence_refs": _clean_string_list(output_item.get("evidence_refs")),
                    "claim_refs": _clean_string_list(output_item.get("claim_refs")),
                    "skill_refs": _clean_string_list(output_item.get("skill_refs")),
                    "project_refs": _clean_string_list(output_item.get("project_refs")),
                    "kanban_refs": _clean_string_list(output_item.get("kanban_refs")),
                },
            )
        )
        edges.append(_edge("output", node_id, "contains"))
        for evidence_ref in _clean_string_list(output_item.get("evidence_refs")):
            evidence_node_id = evidence_node_by_ref.get(evidence_ref)
            if evidence_node_id:
                output_refs_by_evidence.setdefault(evidence_ref, []).append(node_id)
                edges.append(_edge(evidence_node_id, node_id, "produces"))
        for claim_ref in _clean_string_list(output_item.get("claim_refs")):
            claim_item_node_id = claim_node_by_ref.get(claim_ref)
            if claim_item_node_id:
                edges.append(_edge(claim_item_node_id, node_id, "produces"))
        for skill_ref in _clean_string_list(output_item.get("skill_refs")):
            skill_node_id = skill_node_by_ref.get(skill_ref) or f"skill:{skill_ref}"
            if skill_node_id in skill_nodes:
                edges.append(_edge(skill_node_id, node_id, "supports"))
        for project_ref in _clean_string_list(output_item.get("project_refs")):
            project_node_id = project_node_by_id.get(project_ref)
            if project_node_id:
                edges.append(_edge(project_node_id, node_id, "produces"))
        for task_ref in _clean_string_list(output_item.get("kanban_refs")):
            task_node_id = _ref_node(task_node_by_ref, task_ref)
            if task_node_id:
                edges.append(_edge(task_node_id, node_id, "produces"))

    if not output_leaf_ids:
        for idx in range(3):
            node_id = f"output:placeholder:{idx + 1}"
            output_leaf_ids.append(node_id)
            nodes.append(
                _node(
                    id=node_id,
                    type="output",
                    layer="output",
                    label=f"{_ui_text(ui, 'dashboard_output_title', 'Output')} {idx + 1}",
                    metric=_ui_text(ui, "dashboard_placeholder_metric", "planned"),
                    status="planned",
                    implemented=False,
                    placeholder=True,
                    suggested=True,
                    synthetic=True,
                    item_kind="runtime_output",
                    meta={"synthetic": True, "runtime_placeholder": True},
                )
            )
            edges.append(_edge("output", node_id, "contains", placeholder=True, suggested=True))
            edges.append(
                _edge(
                    claim_node_id,
                    node_id,
                    "produces",
                    placeholder=True,
                    suggested=True,
                )
            )

    for claim in claim_items:
        claim_item_node_id = claim_node_by_ref.get(str(claim.get("id") or "").strip())
        if not claim_item_node_id:
            continue
        for output_ref in _clean_string_list(claim.get("output_refs")):
            output_item_node_id = output_node_by_ref.get(output_ref)
            if output_item_node_id:
                edges.append(_edge(claim_item_node_id, output_item_node_id, "produces"))

    layout_anchor_sources = (
        set(project_node_by_id.values())
        | set(task_node_by_ref.values())
        | set(output_leaf_ids)
        | {"output"}
    )
    for evidence in evidence_items:
        evidence_id = str(evidence.get("id") or "").strip()
        evidence_node_id = evidence_node_by_ref.get(evidence_id)
        if not evidence_node_id:
            continue
        has_layout_parent = any(
            str(edge.get("to") or "") == evidence_node_id
            and str(edge.get("from") or "") in layout_anchor_sources
            for edge in edges
        )
        if has_layout_parent:
            continue
        anchor_id = ""
        for project_ref in _clean_string_list(evidence.get("project_refs")):
            anchor_id = project_node_by_id.get(project_ref, "")
            if anchor_id:
                break
        if not anchor_id:
            for task_ref in _clean_string_list(evidence.get("kanban_refs")):
                anchor_id = _ref_node(task_node_by_ref, task_ref)
                if anchor_id:
                    break
        if not anchor_id:
            anchor_id = next(iter(output_refs_by_evidence.get(evidence_id, [])), "")
        if not anchor_id:
            anchor_id = "atomic_evidence:pool"
        edges.append(
            _edge(
                anchor_id,
                evidence_node_id,
                "supports",
                suggested=True,
                placeholder=anchor_id == "atomic_evidence:pool",
                relation="layout_anchor",
                layout_only=True,
            )
        )

    nodes.append(
        _node(
            id="feedback:planned",
            type="feedback",
            layer="feedback",
            label=_ui_text(ui, "dashboard_node_feedback", "Feedback"),
            metric=_ui_text(ui, "dashboard_placeholder_metric", "planned"),
            status="planned",
            implemented=False,
            placeholder=True,
            suggested=True,
        )
    )
    edges.append(_edge("output", "feedback:planned", "feedback", placeholder=True, suggested=True))
    edges.append(
        _edge(
            "feedback:planned",
            "source:inbox",
            "source_to_candidate",
            placeholder=True,
            suggested=True,
        )
    )

    health_counts = health.get("counts") or {}
    health_warning = int(health_counts.get("warning", 0) or 0)
    health_error = int(health_counts.get("error", 0) or 0)
    nodes.append(
        _node(
            id="health",
            type="health",
            layer="governance",
            label=_ui_text(ui, "dashboard_health_title", "Health"),
            metric=(
                f"{health_counts.get('error', 0)}/"
                f"{health_counts.get('warning', 0)}/"
                f"{health_counts.get('info', 0)}"
            ),
            status="risk" if health_error or health_warning else "ok",
            owner_path="pages/5_Profile_Health.py",
        )
    )
    nodes.append(
        _node(
            id="capacity:planned",
            type="capacity",
            layer="governance",
            label=_ui_text(ui, "dashboard_node_capacity", "North Star Capacity"),
            metric=_ui_text(ui, "dashboard_placeholder_metric", "planned"),
            status="planned",
            implemented=False,
            placeholder=True,
            suggested=True,
        )
    )
    for watch_id in (
        "source:inbox",
        "evidence_candidate:pending",
        "atomic_evidence:pool",
        "composite_evidence:planned",
        claim_node_id,
        "output",
    ):
        edges.append(_edge("health", watch_id, "watches", suggested=True))
    for node_id in list(skill_nodes)[:4]:
        edges.append(_edge(node_id, "capacity:planned", "supports", suggested=True))
    edges.append(_edge("capacity:planned", "north_star", "supports", placeholder=True, suggested=True))

    graph_actions.extend(
        [
            _graph_action(
                id="capture_source",
                node_id="source:inbox",
                label=_ui_text(ui, "dashboard_capture_submit", "Capture"),
                action="noop",
                payload={"section": "capture"},
            ),
            _graph_action(
                id="review_evidence",
                node_id="evidence_candidate:pending",
                label=_ui_text(ui, "quick_evidence_review", "Evidence Review"),
                path=EVIDENCE_REVIEW_PAGE,
            ),
            _graph_action(
                id="review_claims",
                node_id=claim_node_id,
                label=_ui_text(ui, "quick_evidence_review", "Evidence Review"),
                path=EVIDENCE_REVIEW_PAGE,
            ),
            _graph_action(
                id="open_gap",
                node_id="gap:risk",
                label=_ui_text(ui, "quick_gap", "Gap Analysis"),
                path="pages/2_Gap_Analysis.py",
            ),
            _graph_action(
                id="open_output",
                node_id="output",
                label=_ui_text(ui, "quick_public_site", "Output Studio"),
                path="pages/6_Output_Studio.py",
            ),
        ]
    )
    attention_counts = {
        "sources_active": source_active,
        "evidence_pending": candidate_count + atomic_attention_count,
        "claims_ready": draft_claims + needs_refresh_claims,
        "skill_risks": gap_count,
        "output_opportunities": int(public.get("draft_total", 0) or 0),
        "health_risks": health_error + health_warning,
    }
    if source_active:
        attention_nodes.append(
            {
                "id": "source:inbox",
                "reason": _ui_text(ui, "dashboard_source_to_evidence_hint", "Captured sources need review."),
                "severity": "info",
            }
        )
    if candidate_count or atomic_attention_count:
        attention_nodes.append(
            {
                "id": "evidence_candidate:pending",
                "reason": _ui_text(ui, "dashboard_pending_evidence_title", "Evidence to organize"),
                "severity": "warning",
            }
        )
    if draft_claims or needs_refresh_claims:
        attention_nodes.append(
            {
                "id": claim_node_id,
                "reason": _ui_text(ui, "dashboard_node_claim", "Claims"),
                "severity": "warning" if needs_refresh_claims else "info",
            }
        )
    if gap_count:
        attention_nodes.append(
            {
                "id": "gap:risk",
                "reason": _ui_text(ui, "dashboard_gap_risk_title", "Gap risk"),
                "severity": "warning",
            }
        )
    if health_error or health_warning:
        attention_nodes.append(
            {
                "id": "health",
                "reason": _ui_text(ui, "dashboard_health_title", "Health"),
                "severity": "error" if health_error else "warning",
            }
        )

    nodes = _dedupe_nodes(nodes)
    edges = _filter_edges(edges, nodes)
    focus_path = [
        node_id
        for node_id in (
            "north_star",
            primary_node_id,
            project_node_ids[0] if project_node_ids else "",
            "source:inbox",
            "evidence_candidate:pending",
            "atomic_evidence:pool",
            claim_node_id,
            next(iter(skill_nodes), ""),
            "output",
            "health",
        )
        if node_id
    ]
    return {
        "schema_version": "1.1",
        "view": view,
        "contract": growth_graph_contract_payload(),
        "layers": list(workspace_graph_layers()),
        "nodes": nodes,
        "edges": edges,
        "focus_path": focus_path,
        "attention": {
            "counts": attention_counts,
            "nodes": attention_nodes,
        },
        "actions": graph_actions,
    }


__all__ = [
    "workspace_graph_edge_types",
    "workspace_graph_layers",
    "workspace_graph_node_type_roles",
    "workspace_graph_node_types",
    "workspace_graph_payload",
]
