"""Privacy-safe workspace graph read model."""

from __future__ import annotations

from typing import Any

from nblane.core.evidence_review import EVIDENCE_REVIEW_PAGE
from nblane.core.goals import Goal, GoalSkillLink, goal_for_ui

WORKSPACE_GRAPH_LAYERS: tuple[str, ...] = (
    "direction",
    "objective",
    "work_context",
    "activity",
    "source",
    "evidence",
    "claim",
    "capability",
    "output",
    "feedback",
    "governance",
)

WORKSPACE_GRAPH_NODE_TYPES: tuple[str, ...] = (
    "north_star",
    "goal",
    "project_case",
    "task",
    "daily_work",
    "research",
    "agent_run",
    "source",
    "evidence_candidate",
    "atomic_evidence",
    "composite_evidence",
    "claim",
    "skill",
    "gap",
    "next_action",
    "output",
    "feedback",
    "capacity",
    "health",
)

WORKSPACE_GRAPH_EDGE_TYPES: tuple[str, ...] = (
    "alignment",
    "contains",
    "generated_by",
    "source_to_candidate",
    "review",
    "derives",
    "supports",
    "drives",
    "produces",
    "feedback",
    "watches",
)


def workspace_graph_layers() -> tuple[str, ...]:
    """Return the stable Growth Graph layer order."""
    return WORKSPACE_GRAPH_LAYERS


def workspace_graph_node_types() -> tuple[str, ...]:
    """Return supported workspace graph node types."""
    return WORKSPACE_GRAPH_NODE_TYPES


def workspace_graph_edge_types() -> tuple[str, ...]:
    """Return supported workspace graph edge types."""
    return WORKSPACE_GRAPH_EDGE_TYPES


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
    **extra: object,
) -> dict[str, object]:
    return {
        "id": id,
        "type": type,
        "layer": layer,
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
        **extra,
    }


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
    ui: dict[str, str] | None = None,
    view: str = "context",
) -> dict[str, Any]:
    """Build a privacy-safe Growth Graph context payload."""
    nodes: list[dict[str, object]] = []
    edges: list[dict[str, object]] = []

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
    shown_goals = [goal for goal in active_goals if goal.id]
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
    ][:3]
    project_node_ids: list[str] = []
    if project_cases:
        for case in project_cases:
            record_id = str(case.get("id") or "").strip()
            node_id = record_id
            project_node_ids.append(node_id)
            is_private = str(case.get("visibility") or "private") == "private"
            nodes.append(
                _node(
                    id=node_id,
                    type="project_case",
                    layer="work_context",
                    label=(
                        _ui_text(ui, "dashboard_private_project_case", "Private project case")
                        if is_private
                        else str(case.get("title") or record_id)
                    ),
                    metric=str(case.get("kind") or ""),
                    record_id=record_id,
                    status=str(case.get("status") or ""),
                    locked=is_private,
                    owner_path="pages/2_Evidence_Review.py",
                    implemented=True,
                )
            )
            edges.append(_edge(primary_node_id, node_id, "contains"))
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

    for idx, item in enumerate((kanban.get("doing") or [])[:3]):
        if not isinstance(item, dict):
            continue
        node_id = f"task:{idx}"
        nodes.append(
            _node(
                id=node_id,
                type="task",
                layer="activity",
                label=str(item.get("title") or ""),
                metric=(
                    _ui_text(ui, "dashboard_graph_blocked", "blocked")
                    if item.get("blocked_by")
                    else _ui_text(ui, "dashboard_metric_doing", "Doing")
                ),
                status="risk" if item.get("blocked_by") else "active",
                owner_path="pages/3_Kanban.py",
            )
        )
        edges.append(_edge(primary_node_id, node_id, "drives"))
        edges.append(
            _edge(
                project_anchor_id,
                node_id,
                "contains",
                placeholder=project_anchor_id == "project_case:planned",
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
        )
    )
    edges.append(_edge(primary_node_id, "source:inbox", "contains"))
    for idx in range(min(len(kanban.get("doing") or []), 3)):
        edges.append(_edge(f"task:{idx}", "source:inbox", "generated_by"))
    for activity_id in ("daily_work:planned", "research:planned", "agent_run:planned"):
        edges.append(
            _edge(activity_id, "source:inbox", "generated_by", placeholder=True, suggested=True)
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

    nodes.append(
        _node(
            id="claim:planned",
            type="claim",
            layer="claim",
            label=_ui_text(ui, "dashboard_node_claim", "Claims"),
            metric=_ui_text(ui, "dashboard_placeholder_metric", "planned"),
            status="planned",
            implemented=False,
            placeholder=True,
            suggested=True,
        )
    )
    edges.append(
        _edge(
            "composite_evidence:planned",
            "claim:planned",
            "supports",
            placeholder=True,
            suggested=True,
        )
    )

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

    for node_id in list(skill_nodes)[:4]:
        edges.append(_edge("claim:planned", node_id, "supports", placeholder=True, suggested=True))
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

    nodes.append(
        _node(
            id="output",
            type="output",
            layer="output",
            label=_ui_text(ui, "dashboard_output_title", "Output"),
            metric=str(public.get("draft_total", 0)),
            status="draft" if public.get("draft_total") else "clear",
            owner_path="pages/6_Public_Site.py",
        )
    )
    edges.append(_edge("claim:planned", "output", "produces", placeholder=True, suggested=True))
    edges.append(_edge("atomic_evidence:pool", "output", "produces"))

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
        "claim:planned",
        "output",
    ):
        edges.append(_edge("health", watch_id, "watches", suggested=True))
    for node_id in list(skill_nodes)[:4]:
        edges.append(_edge(node_id, "capacity:planned", "supports", suggested=True))
    edges.append(_edge("capacity:planned", "north_star", "supports", placeholder=True, suggested=True))

    nodes = _dedupe_nodes(nodes)
    edges = _filter_edges(edges, nodes)
    return {
        "schema_version": "1.0",
        "view": view,
        "layers": list(WORKSPACE_GRAPH_LAYERS),
        "nodes": nodes,
        "edges": edges,
    }


__all__ = [
    "workspace_graph_edge_types",
    "workspace_graph_layers",
    "workspace_graph_node_types",
    "workspace_graph_payload",
]
