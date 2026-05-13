"""Read models for the Home dashboard."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from nblane.core import io as io_facade
from nblane.core import profile_health
from nblane.core.evidence_review import (
    EVIDENCE_REVIEW_PAGE,
    build_evidence_review,
    evidence_status_risks,
)
from nblane.core.goals import (
    GOAL_STATUSES,
    GOAL_UI_VISIBILITIES,
    Goal,
    GoalBook,
    GoalSkillLink,
    goal_for_ui,
)
from nblane.core.goal_alignment import skill_node_options
from nblane.core.inbox import load_inbox, summarize_inbox
from nblane.core.io import (
    KANBAN_DOING,
    KANBAN_DONE,
    KANBAN_QUEUE,
    KANBAN_SECTIONS,
    STATUSES,
    schema_node_index,
)
from nblane.core.paths import REPO_ROOT
from nblane.core.profile_context import (
    north_star_payload_from_identity,
    parse_identity_fields,
)
from nblane.core.workspace_graph import workspace_graph_payload

ProfileRef = str | Path

QUICK_LINKS: tuple[dict[str, str], ...] = (
    {
        "id": "kanban",
        "path": "pages/3_Kanban.py",
        "label_key": "quick_kanban",
        "help_key": "quick_kanban_help",
        "kind": "work",
    },
    {
        "id": "evidence_review",
        "path": EVIDENCE_REVIEW_PAGE,
        "label_key": "quick_evidence_review",
        "help_key": "quick_evidence_review_help",
        "kind": "growth",
    },
    {
        "id": "skill_tree",
        "path": "pages/1_Skill_Tree.py",
        "label_key": "quick_skill_tree",
        "help_key": "quick_skill_tree_help",
        "kind": "growth",
    },
    {
        "id": "gap",
        "path": "pages/2_Gap_Analysis.py",
        "label_key": "quick_gap",
        "help_key": "quick_gap_help",
        "kind": "growth",
    },
    {
        "id": "public_site",
        "path": "pages/6_Public_Site.py",
        "label_key": "quick_public_site",
        "help_key": "quick_public_site_help",
        "kind": "output",
    },
    {
        "id": "profile_health",
        "path": "pages/5_Profile_Health.py",
        "label_key": "quick_profile_health",
        "help_key": "quick_profile_health_help",
        "kind": "growth",
    },
)


def _profile_path(profile: ProfileRef) -> Path:
    if isinstance(profile, Path):
        return profile
    return io_facade.profile_dir(profile)


def _profile_name(profile: ProfileRef) -> str:
    if isinstance(profile, Path):
        return profile.name
    return str(profile)


def _read_yaml_mapping(path: Path) -> dict:
    if not path.exists():
        return {}
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {}


def _as_list(raw: object) -> list:
    return raw if isinstance(raw, list) else []


def _status_counts(
    tree_raw: dict | None,
    schema_raw: dict | None,
) -> tuple[dict[str, int], int, dict[str, dict[str, Any]]]:
    counts: dict[str, int] = {status: 0 for status in STATUSES}
    index = schema_node_index(schema_raw) if schema_raw else {}
    nodes = _as_list(tree_raw.get("nodes")) if isinstance(tree_raw, dict) else []
    node_status = {
        str(node.get("id")): str(node.get("status", "locked") or "locked")
        for node in nodes
        if isinstance(node, dict) and node.get("id")
    }
    if index:
        for node_id in index:
            status = node_status.get(node_id, "locked")
            counts[status] = counts.get(status, 0) + 1
        return counts, sum(counts.values()), index

    fallback_index: dict[str, dict[str, Any]] = {}
    for node in nodes:
        if not isinstance(node, dict) or not node.get("id"):
            continue
        node_id = str(node.get("id"))
        status = str(node.get("status", "locked") or "locked")
        counts[status] = counts.get(status, 0) + 1
        fallback_index[node_id] = {
            "id": node_id,
            "label": node_id,
            "category": "",
        }
    return counts, sum(counts.values()), fallback_index


def _goal_book(profile: ProfileRef) -> GoalBook:
    raw = io_facade.load_goal_book_raw(profile)
    return GoalBook.from_dict(raw, profile=_profile_name(profile))


def _current_goal(profile: ProfileRef):
    return _goal_book(profile).current()


def _profile_identity(profile: ProfileRef) -> dict[str, str]:
    path = _profile_path(profile) / "SKILL.md"
    if not path.exists():
        return parse_identity_fields("")
    try:
        return parse_identity_fields(path.read_text(encoding="utf-8"))
    except OSError:
        return parse_identity_fields("")


def _goal_editor_payload(goal: Goal | None) -> dict:
    """Return the editable goal fields used by the Home dashboard."""
    if goal is None:
        return {
            "id": "",
            "title": "",
            "label": "",
            "status": "active",
            "start": "",
            "target": "",
            "ui_visibility": "discreet",
            "include_in_agent_context": True,
            "summary": "",
            "alignment": "",
            "target_skills": [],
            "skill_links": [],
            "success_criteria": [],
            "focus": [],
            "evidence_refs": [],
            "task_refs": [],
            "output_refs": [],
            "notes": "",
        }
    return {
        "id": goal.id,
        "title": goal.title,
        "label": goal.label,
        "status": goal.status,
        "start": goal.start,
        "target": goal.target,
        "ui_visibility": goal.ui_visibility,
        "include_in_agent_context": goal.include_in_agent_context,
        "summary": goal.summary,
        "alignment": goal.alignment,
        "target_skills": list(goal.target_skills),
        "skill_links": [link.to_dict() for link in goal.skill_links],
        "success_criteria": list(goal.success_criteria),
        "focus": list(goal.focus),
        "evidence_refs": list(goal.evidence_refs),
        "task_refs": list(goal.task_refs),
        "output_refs": list(goal.output_refs),
        "notes": goal.notes,
    }


def _goal_payload_from_goal(goal: Goal | None, *, editable: bool = True) -> dict:
    """Return privacy-safe goal display plus editable fields when allowed."""
    projection = goal_for_ui(goal)
    locked = goal is not None and projection is None
    return {
        "is_set": goal is not None,
        "locked": locked,
        "projection": projection,
        "editor": {} if locked or not editable else _goal_editor_payload(goal),
        "status_options": list(GOAL_STATUSES),
        "visibility_options": list(GOAL_UI_VISIBILITIES),
    }


def _goal_payload(profile: ProfileRef) -> dict:
    """Return the primary goal payload for compatibility callers."""
    return _goal_payload_from_goal(_current_goal(profile))


def _goal_card_payload(goal: Goal, primary_id: str = "") -> dict:
    """Return compact active-goal display metadata."""
    return {
        **_goal_payload_from_goal(goal, editable=True),
        "id": goal.id,
        "is_primary": bool(goal.id and goal.id == primary_id),
    }


def _node_label(index: dict[str, dict[str, Any]], node_id: str) -> str:
    meta = index.get(node_id) or {}
    return str(meta.get("label") or node_id)


def _ui_text(ui: dict[str, str] | None, key: str, fallback: str = "") -> str:
    if not ui:
        return fallback or key
    return str(ui.get(key, fallback or key))


def _target_skill_hits(
    profile: ProfileRef,
    tree_raw: dict | None,
    index: dict[str, dict[str, Any]],
) -> tuple[list[str], list[dict[str, str]]]:
    book = _goal_book(profile)
    targets: list[str] = []
    seen_targets: set[str] = set()
    for goal in book.active_goals():
        if goal.ui_visibility == "private":
            continue
        for target in goal.target_skills:
            clean = str(target).strip()
            if not clean or clean in seen_targets:
                continue
            seen_targets.add(clean)
            targets.append(clean)
    if not targets or not isinstance(tree_raw, dict):
        return targets, []

    wanted = [str(item).strip().lower() for item in targets if str(item).strip()]
    if not wanted:
        return targets, []
    hits: list[dict[str, str]] = []
    seen: set[str] = set()
    for node in _as_list(tree_raw.get("nodes")):
        if not isinstance(node, dict) or not node.get("id"):
            continue
        node_id = str(node.get("id"))
        label = _node_label(index, node_id)
        haystack = f"{node_id} {label}".lower()
        if not any(target in haystack or haystack in target for target in wanted):
            continue
        status = str(node.get("status", "locked") or "locked")
        if status not in ("learning", "locked"):
            continue
        if node_id in seen:
            continue
        seen.add(node_id)
        hits.append(
            {
                "id": node_id,
                "label": label,
                "status": status,
            }
        )
    return targets, hits


def dashboard_kanban_summary(profile: ProfileRef) -> dict:
    """Return Doing and crystallization summary for ``kanban.md``."""
    try:
        sections = io_facade.parse_kanban(profile)
        error = ""
    except OSError as exc:
        sections = {section: [] for section in KANBAN_SECTIONS}
        error = str(exc)

    doing = sections.get(KANBAN_DOING) or []
    done = sections.get(KANBAN_DONE) or []
    pending_done = [
        task
        for task in done
        if not getattr(task, "crystallized", False)
    ]
    return {
        "error": error,
        "counts": {
            section: len(sections.get(section) or [])
            for section in KANBAN_SECTIONS
        },
        "doing": [
            {
                "title": task.title,
                "blocked_by": task.blocked_by,
                "tags": task.tags,
                "started_on": task.started_on or "",
            }
            for task in doing[:5]
        ],
        "doing_total": len(doing),
        "done_uncrystallized_count": len(pending_done),
        "done_uncrystallized": [
            {"title": task.title, "completed_on": task.completed_on or ""}
            for task in pending_done[:5]
        ],
    }


def dashboard_skill_summary(profile: ProfileRef) -> dict:
    """Return skill-tree status and evidence-risk summary."""
    tree_raw = io_facade.load_skill_tree_raw(profile)
    if not isinstance(tree_raw, dict):
        return {
            "has_tree": False,
            "schema": "",
            "counts": {status: 0 for status in STATUSES},
            "total": 0,
            "lit": 0,
            "lit_rate": 0.0,
            "evidence_risk_count": 0,
            "evidence_risk_nodes": [],
            "target_skills": [],
            "target_learning_locked": [],
        }

    schema_name = str(tree_raw.get("schema", "") or "")
    schema_raw = io_facade.load_schema_raw(schema_name) if schema_name else None
    counts, total, index = _status_counts(tree_raw, schema_raw)
    lit = counts.get("expert", 0) + counts.get("solid", 0)
    risk_nodes: list[dict[str, str]] = []
    for risk in evidence_status_risks(profile):
        node_id = str(risk.get("id", "") or "")
        risk_nodes.append(
            {
                "id": node_id,
                "label": str(risk.get("label") or _node_label(index, node_id)),
                "status": str(risk.get("status", "") or ""),
                "risk_level": str(risk.get("risk_level", "") or ""),
                "highest_strength": str(
                    risk.get("highest_strength", "") or "unrated"
                ),
                "required_strength": str(
                    risk.get("required_strength", "") or ""
                ),
            }
        )

    targets, target_hits = _target_skill_hits(profile, tree_raw, index)
    return {
        "has_tree": True,
        "schema": schema_name,
        "counts": counts,
        "total": total,
        "lit": lit,
        "lit_rate": (lit / total) if total else 0.0,
        "evidence_risk_count": len(risk_nodes),
        "evidence_risk_nodes": risk_nodes[:5],
        "target_skills": targets,
        "target_learning_locked": target_hits[:5],
    }


def dashboard_pending_evidence_summary(profile: ProfileRef) -> dict:
    """Return lightweight evidence items that need review or linking."""
    review = build_evidence_review(profile)
    summary = review.get("summary") or {}
    return {
        "total_entries": int(summary.get("total_entries", 0) or 0),
        "unlinked_count": int(summary.get("unlinked_count", 0) or 0),
        "unlinked": list(review.get("unlinked") or [])[:5],
        "needs_review_count": int(summary.get("needs_review_count", 0) or 0),
        "needs_review": list(review.get("needs_review") or [])[:5],
        "status_risk_count": int(summary.get("status_risk_count", 0) or 0),
        "status_risks": list(review.get("status_risks") or [])[:5],
        "done_uncrystallized_count": int(
            summary.get("done_uncrystallized_count", 0) or 0
        ),
        "done_uncrystallized": list(
            review.get("done_uncrystallized") or []
        )[:5],
    }


def dashboard_source_summary(profile: ProfileRef) -> dict:
    """Return privacy-safe source inbox counts for the Home dashboard."""
    path = _profile_path(profile) / "inbox.yaml"
    try:
        inbox = load_inbox(profile)
        summary = summarize_inbox(inbox)
        error = ""
    except OSError as exc:
        return {
            "error": str(exc),
            "implemented": False,
            "inbox_total": 0,
            "active_total": 0,
            "status_counts": {},
            "active_titles": [],
        }

    status_counts = summary.status_counts
    active_total = sum(
        int(status_counts.get(status, 0) or 0)
        for status in ("inbox", "captured", "clarified", "active")
    )
    return {
        "error": error,
        "implemented": path.exists() or summary.total_items > 0,
        "inbox_total": summary.total_items,
        "active_total": active_total,
        "status_counts": status_counts,
        "active_titles": summary.active_titles[:5],
    }


def dashboard_health_summary(profile: ProfileRef) -> dict:
    """Return profile-health counts and the first actionable issues."""
    if isinstance(profile, Path):
        old_profile_dir = profile_health.profile_dir
        try:
            profile_health.profile_dir = lambda _name: profile
            report = profile_health.analyze_profile_health(profile.name)
        finally:
            profile_health.profile_dir = old_profile_dir
    else:
        report = profile_health.analyze_profile_health(profile)
    counts = report.summary_counts
    return {
        "counts": counts,
        "context_ready": report.can_publish_context,
        "issues": [
            {
                "severity": issue.severity,
                "category": issue.category,
                "title": issue.title,
                "detail": issue.detail,
                "action": issue.action,
            }
            for issue in report.issues[:5]
        ],
    }


def _status_counts_from_items(items: list) -> dict[str, int]:
    counts = {"draft": 0, "published": 0, "archived": 0, "other": 0}
    for item in items:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status", "draft") or "draft")
        if status not in counts:
            status = "other"
        counts[status] += 1
    return counts


def _blog_post_status(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return "draft"
    end = text.find("\n---", 4)
    if end == -1:
        return "draft"
    raw = yaml.safe_load(text[4:end]) or {}
    if not isinstance(raw, dict):
        return "draft"
    return str(raw.get("status", "draft") or "draft")


def dashboard_public_summary(profile: ProfileRef) -> dict:
    """Return public-layer draft and build status without generating output."""
    pdir = _profile_path(profile)
    name = _profile_name(profile)
    public_profile = _read_yaml_mapping(pdir / "public-profile.yaml")
    projects = _as_list(_read_yaml_mapping(pdir / "projects.yaml").get("projects"))
    outputs = _as_list(_read_yaml_mapping(pdir / "outputs.yaml").get("outputs"))

    blog_items: list[dict[str, str]] = []
    blog_dir = pdir / "blog"
    if blog_dir.exists():
        for path in sorted(blog_dir.rglob("*.md")):
            if any(part.startswith(".") for part in path.relative_to(blog_dir).parts):
                continue
            blog_items.append({"status": _blog_post_status(path)})

    output_dir = REPO_ROOT / "dist" / "public" / name
    initialized = any(
        (pdir / rel).exists()
        for rel in (
            "public-profile.yaml",
            "projects.yaml",
            "outputs.yaml",
            "blog",
        )
    )
    project_counts = _status_counts_from_items(projects)
    output_counts = _status_counts_from_items(outputs)
    blog_counts = _status_counts_from_items(blog_items)
    return {
        "initialized": initialized,
        "visibility": str(public_profile.get("visibility", "private") or "private"),
        "public_name": str(public_profile.get("public_name", "") or ""),
        "project_counts": project_counts,
        "output_counts": output_counts,
        "blog_counts": blog_counts,
        "draft_total": (
            project_counts["draft"]
            + output_counts["draft"]
            + blog_counts["draft"]
        ),
        "published_total": (
            project_counts["published"]
            + output_counts["published"]
            + blog_counts["published"]
        ),
        "build_exists": (output_dir / "index.html").exists(),
        "build_output_dir": str(output_dir),
        "build_pages": (
            len(list(output_dir.rglob("*.html"))) if output_dir.exists() else 0
        ),
    }


def _goal_graph_label(
    goal_payload: dict,
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


def _safe_goal_skill_links(goal: Goal | None) -> list[GoalSkillLink]:
    if goal is None or goal.ui_visibility == "private":
        return []
    return list(goal.skill_links)


def _suggested_skill_nodes(
    skills: dict,
) -> list[dict[str, object]]:
    skill_nodes = list(skills.get("target_learning_locked") or [])
    if not skill_nodes:
        skill_nodes = list(skills.get("evidence_risk_nodes") or [])
    return [
        {
            "node_id": str(node.get("id") or ""),
            "label": str(node.get("label") or node.get("id") or ""),
            "metric": str(node.get("status") or ""),
            "suggested": True,
        }
        for node in skill_nodes
        if isinstance(node, dict)
    ]


def _graph_payload(
    *,
    north_star: dict,
    primary_goal: dict,
    primary_goal_id: str,
    active_goals: list[Goal],
    kanban: dict,
    skills: dict,
    pending: dict,
    public: dict,
    health: dict,
    ui: dict[str, str] | None,
) -> dict:
    """Build a compact relation graph for the React dashboard canvas."""
    nodes: list[dict[str, object]] = []
    edges: list[dict[str, object]] = []

    if north_star.get("is_set"):
        if north_star.get("locked"):
            label = _ui_text(ui, "north_star_private_display", "Private North Star")
        else:
            label = str(
                north_star.get("display_text")
                or _ui_text(ui, "north_star_hidden_display", "North Star set")
            )
        nodes.append(
            {
                "id": "north_star",
                "type": "north_star",
                "label": label,
                "metric": _ui_text(ui, "north_star_strip_title", "North Star"),
                "locked": bool(north_star.get("locked")),
                "suggested": False,
                "owner_path": "profile_context",
            }
        )

    goal_node_ids: dict[str, str] = {}
    shown_goals = [goal for goal in active_goals if goal.id]
    if not shown_goals:
        nodes.append(
            {
                "id": "goal:missing",
                "type": "goal",
                "label": _goal_graph_label(primary_goal, ui),
                "metric": _ui_text(ui, "dashboard_primary_goal", "Primary goal"),
                "record_id": "",
                "status": "",
                "locked": False,
                "suggested": True,
                "owner_path": "",
                "is_primary": True,
            }
        )
        if north_star.get("is_set"):
            edges.append(
                {
                    "from": "north_star",
                    "to": "goal:missing",
                    "type": "alignment",
                    "suggested": True,
                }
            )

    for goal_obj in shown_goals:
        payload = _goal_payload_from_goal(goal_obj, editable=False)
        node_id = f"goal:{goal_obj.id}"
        goal_node_ids[goal_obj.id] = node_id
        is_primary = bool(goal_obj.id and goal_obj.id == primary_goal_id)
        nodes.append(
            {
                "id": node_id,
                "type": "goal",
                "label": _goal_graph_label(
                    payload,
                    ui,
                    fallback_key=(
                        "dashboard_primary_goal"
                        if is_primary
                        else "dashboard_active_goal"
                    ),
                ),
                "metric": _ui_text(
                    ui,
                    "dashboard_primary_goal" if is_primary else "dashboard_active_goal",
                    "Primary goal" if is_primary else "Active goal",
                ),
                "record_id": goal_obj.id,
                "status": goal_obj.status,
                "locked": bool(payload.get("locked")),
                "suggested": False,
                "owner_path": "",
                "is_primary": is_primary,
            }
        )
        if north_star.get("is_set"):
            edges.append(
                {
                    "from": "north_star",
                    "to": node_id,
                    "type": "alignment",
                    "suggested": False,
                }
            )

    skill_nodes: dict[str, dict[str, object]] = {}
    for goal_obj in shown_goals:
        goal_node_id = goal_node_ids.get(goal_obj.id)
        if not goal_node_id:
            continue
        for link in _safe_goal_skill_links(goal_obj):
            if not link.node_id:
                continue
            skill_node_id = f"skill:{link.node_id}"
            skill_nodes.setdefault(
                skill_node_id,
                {
                    "id": skill_node_id,
                    "type": "skill",
                    "label": link.label or link.node_id,
                    "metric": link.source,
                    "record_id": link.node_id,
                    "status": "",
                    "locked": False,
                    "suggested": False,
                    "owner_path": "pages/1_Skill_Tree.py",
                },
            )
            edges.append(
                {
                    "from": goal_node_id,
                    "to": skill_node_id,
                    "type": "skill_link",
                    "suggested": False,
                }
            )

    if not skill_nodes:
        for idx, node in enumerate(_suggested_skill_nodes(skills)[:4]):
            node_id = f"skill:suggested:{idx}"
            skill_nodes[node_id] = {
                "id": node_id,
                "type": "skill",
                "label": str(node.get("label") or node.get("node_id") or ""),
                "metric": _ui_text(ui, "skill_alignment_suggested", "suggested"),
                "record_id": str(node.get("node_id") or ""),
                "status": str(node.get("metric") or ""),
                "locked": False,
                "suggested": True,
                "owner_path": "pages/1_Skill_Tree.py",
            }
            if primary_goal_id and primary_goal_id in goal_node_ids:
                edges.append(
                    {
                        "from": goal_node_ids[primary_goal_id],
                        "to": node_id,
                        "type": "skill_link",
                        "suggested": True,
                    }
                )

    if not skill_nodes:
        node_id = "skill:lit"
        skill_nodes[node_id] = {
            "id": node_id,
            "type": "skill",
            "label": _ui_text(ui, "dashboard_metric_skill_lit", "Skill lit"),
            "metric": f"{skills.get('lit', 0)}/{skills.get('total', 0)}",
            "record_id": "",
            "status": "",
            "locked": False,
            "suggested": True,
            "owner_path": "pages/1_Skill_Tree.py",
        }
    nodes.extend(skill_nodes.values())

    primary_node_id = (
        goal_node_ids.get(primary_goal_id)
        if primary_goal_id
        else next(iter(goal_node_ids.values()), "goal:missing")
    )
    if "skill:lit" in skill_nodes and primary_node_id:
        edges.append(
            {
                "from": primary_node_id,
                "to": "skill:lit",
                "type": "skill_link",
                "suggested": True,
            }
        )
    for idx, item in enumerate((kanban.get("doing") or [])[:3]):
        node_id = f"task:{idx}"
        nodes.append(
            {
                "id": node_id,
                "type": "task",
                "label": str(item.get("title") or ""),
                "metric": (
                    _ui_text(ui, "dashboard_graph_blocked", "blocked")
                    if item.get("blocked_by")
                    else _ui_text(ui, "dashboard_metric_doing", "Doing")
                ),
                "record_id": "",
                "status": "blocked" if item.get("blocked_by") else "doing",
                "locked": False,
                "suggested": False,
                "owner_path": "pages/3_Kanban.py",
            }
        )
        edges.append(
            {
                "from": primary_node_id,
                "to": node_id,
                "type": "task_ref",
                "suggested": False,
            }
        )

    evidence_count = (
        int(pending.get("done_uncrystallized_count") or 0)
        + int(pending.get("unlinked_count") or 0)
        + int(pending.get("needs_review_count") or 0)
        + int(pending.get("status_risk_count") or 0)
    )
    nodes.append(
        {
            "id": "evidence",
            "type": "evidence",
            "label": _ui_text(
                ui,
                "dashboard_pending_evidence_title",
                "Evidence to organize",
            ),
            "metric": str(evidence_count),
            "record_id": "",
            "status": "pending" if evidence_count else "clear",
            "locked": False,
            "suggested": False,
            "owner_path": EVIDENCE_REVIEW_PAGE,
        }
    )
    nodes.append(
        {
            "id": "output",
            "type": "output",
            "label": _ui_text(ui, "dashboard_output_title", "Output"),
            "metric": str(public.get("draft_total", 0)),
            "record_id": "",
            "status": "draft",
            "locked": False,
            "suggested": False,
            "owner_path": "pages/6_Public_Site.py",
        }
    )
    health_counts = health.get("counts") or {}
    nodes.append(
        {
            "id": "health",
            "type": "health",
            "label": _ui_text(ui, "dashboard_health_title", "Health"),
            "metric": (
                f"{health_counts.get('error', 0)}/"
                f"{health_counts.get('warning', 0)}/"
                f"{health_counts.get('info', 0)}"
            ),
            "record_id": "",
            "status": "warning" if health_counts.get("warning", 0) else "ok",
            "locked": False,
            "suggested": False,
            "owner_path": "pages/5_Profile_Health.py",
        }
    )
    for node_id in list(skill_nodes)[:4]:
        edges.append(
            {
                "from": node_id,
                "to": "evidence",
                "type": "evidence_ref",
                "suggested": False,
            }
        )
    for idx in range(min(len(kanban.get("doing") or []), 3)):
        edges.append(
            {
                "from": f"task:{idx}",
                "to": "evidence",
                "type": "crystallize",
                "suggested": False,
            }
        )
    edges.append(
        {
            "from": "evidence",
            "to": "output",
            "type": "output_ref",
            "suggested": False,
        }
    )
    edges.append(
        {
            "from": primary_node_id,
            "to": "health",
            "type": "readiness",
            "suggested": False,
        }
    )
    return {"nodes": nodes, "edges": edges}


def _quick_links_payload(ui: dict[str, str] | None) -> list[dict[str, str]]:
    """Return stable quick links with UI labels."""
    return [
        {
            "id": item["id"],
            "path": item["path"],
            "kind": item["kind"],
            "label": _ui_text(ui, item["label_key"], item["id"]),
            "help": _ui_text(ui, item["help_key"], ""),
        }
        for item in QUICK_LINKS
    ]


def _candidate_dicts(value: object) -> list[dict[str, object]]:
    """Normalize pending alignment candidates for JSON payloads."""
    if not isinstance(value, list):
        return []
    out: list[dict[str, object]] = []
    seen: set[str] = set()
    for item in value:
        if isinstance(item, GoalSkillLink):
            link = item
        else:
            link = GoalSkillLink.from_dict(item)
        if link is None or link.node_id in seen:
            continue
        seen.add(link.node_id)
        out.append(link.to_dict())
    return out


def _goal_skill_alignment_payload(
    profile: ProfileRef,
    active_goals: list[Goal],
    primary_goal_id: str,
    pending_candidates: dict[str, list[dict[str, object]]] | None,
) -> dict[str, object]:
    by_goal: dict[str, dict[str, object]] = {}
    for goal in active_goals:
        if not goal.id:
            continue
        confirmed = []
        if goal.ui_visibility != "private":
            confirmed = [link.to_dict() for link in goal.skill_links]
        by_goal[goal.id] = {
            "confirmed": confirmed,
            "candidates": _candidate_dicts(
                (pending_candidates or {}).get(goal.id, [])
            ),
        }
    return {
        "primary_goal_id": primary_goal_id,
        "by_goal": by_goal,
        "candidates": by_goal.get(primary_goal_id, {}).get("candidates", []),
        "confirmed_links": by_goal.get(primary_goal_id, {}).get("confirmed", []),
        "skill_options": skill_node_options(profile),
    }


def dashboard_payload(
    profile: ProfileRef,
    *,
    ui: dict[str, str] | None = None,
    ai: dict[str, object] | None = None,
    skill_alignment_candidates: dict[str, list[dict[str, object]]] | None = None,
) -> dict:
    """Return the stable JSON payload consumed by the React Home dashboard."""
    kanban = dashboard_kanban_summary(profile)
    skills = dashboard_skill_summary(profile)
    pending = dashboard_pending_evidence_summary(profile)
    sources = dashboard_source_summary(profile)
    health = dashboard_health_summary(profile)
    public = dashboard_public_summary(profile)
    book = _goal_book(profile)
    primary = book.primary()
    primary_goal_id = primary.id if primary is not None else ""
    primary_goal = _goal_payload_from_goal(primary)
    active_goal_models = book.active_goals()
    active_goal_payloads = [
        _goal_card_payload(goal, primary_goal_id)
        for goal in active_goal_models
    ]
    north_star = north_star_payload_from_identity(
        _profile_identity(profile),
        ui=ui,
    )
    skill_alignment = _goal_skill_alignment_payload(
        profile,
        active_goal_models,
        primary_goal_id,
        skill_alignment_candidates,
    )
    return {
        "profile": _profile_name(profile),
        "north_star": north_star,
        "goal": primary_goal,
        "primary_goal": primary_goal,
        "active_goals": active_goal_payloads,
        "goal_counts": {
            "active": len(active_goal_models),
            "total": len(book.goals),
        },
        "skill_alignment": skill_alignment,
        "kanban": kanban,
        "skills": skills,
        "sources": sources,
        "pending_evidence": pending,
        "health": health,
        "public": public,
        "charts": {
            "skills": {
                "counts": skills.get("counts", {}),
                "total": skills.get("total", 0),
                "lit": skills.get("lit", 0),
                "lit_rate": skills.get("lit_rate", 0.0),
            },
            "health": health.get("counts", {}),
            "evidence": {
                "done_uncrystallized": pending.get("done_uncrystallized_count", 0),
                "unlinked": pending.get("unlinked_count", 0),
                "needs_review": pending.get("needs_review_count", 0),
                "status_risk": pending.get("status_risk_count", 0),
            },
            "public": {
                "draft": public.get("draft_total", 0),
                "published": public.get("published_total", 0),
            },
        },
        "graph": workspace_graph_payload(
            north_star=north_star,
            primary_goal=primary_goal,
            primary_goal_id=primary_goal_id,
            active_goals=active_goal_models,
            kanban=kanban,
            skills=skills,
            pending=pending,
            sources=sources,
            public=public,
            health=health,
            ui=ui,
        ),
        "quick_links": _quick_links_payload(ui),
        "ai": dict(ai or {}),
        "ui": dict(ui or {}),
    }
