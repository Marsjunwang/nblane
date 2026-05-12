"""Read models for the Home dashboard."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from nblane.core import io as io_facade
from nblane.core import profile_health
from nblane.core.evidence_resolve import resolved_evidence_count
from nblane.core.goals import (
    GOAL_STATUSES,
    GOAL_UI_VISIBILITIES,
    Goal,
    GoalBook,
    goal_for_ui,
)
from nblane.core.io import (
    KANBAN_DOING,
    KANBAN_DONE,
    KANBAN_QUEUE,
    KANBAN_SECTIONS,
    STATUSES,
    schema_node_index,
)
from nblane.core.paths import REPO_ROOT

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


def _current_goal(profile: ProfileRef):
    raw = io_facade.load_goal_book_raw(profile)
    book = GoalBook.from_dict(raw, profile=_profile_name(profile))
    return book.current()


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
            "target_skills": [],
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
        "target_skills": list(goal.target_skills),
        "success_criteria": list(goal.success_criteria),
        "focus": list(goal.focus),
        "evidence_refs": list(goal.evidence_refs),
        "task_refs": list(goal.task_refs),
        "output_refs": list(goal.output_refs),
        "notes": goal.notes,
    }


def _goal_payload(profile: ProfileRef) -> dict:
    """Return privacy-safe goal display plus editable fields when allowed."""
    goal = _current_goal(profile)
    projection = goal_for_ui(goal)
    locked = goal is not None and projection is None
    return {
        "is_set": goal is not None,
        "locked": locked,
        "projection": projection,
        "editor": {} if locked else _goal_editor_payload(goal),
        "status_options": list(GOAL_STATUSES),
        "visibility_options": list(GOAL_UI_VISIBILITIES),
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
    goal = _current_goal(profile)
    targets = list(goal.target_skills) if goal is not None else []
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
    pool = io_facade.load_evidence_pool(profile)
    risk_nodes: list[dict[str, str]] = []
    for node in _as_list(tree_raw.get("nodes")):
        if not isinstance(node, dict) or not node.get("id"):
            continue
        status = str(node.get("status", "locked") or "locked")
        if status not in ("solid", "expert"):
            continue
        if resolved_evidence_count(node, pool) > 0:
            continue
        node_id = str(node.get("id"))
        risk_nodes.append(
            {
                "id": node_id,
                "label": _node_label(index, node_id),
                "status": status,
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
    pdir = _profile_path(profile)
    pool_raw = _read_yaml_mapping(pdir / "evidence-pool.yaml")
    tree_raw = io_facade.load_skill_tree_raw(profile)
    refs: set[str] = set()
    if isinstance(tree_raw, dict):
        for node in _as_list(tree_raw.get("nodes")):
            if not isinstance(node, dict):
                continue
            for ref in _as_list(node.get("evidence_refs")):
                text = str(ref).strip()
                if text:
                    refs.add(text)

    entries = [
        entry
        for entry in _as_list(pool_raw.get("evidence_entries"))
        if isinstance(entry, dict) and not bool(entry.get("deprecated", False))
    ]
    unlinked: list[dict[str, str]] = []
    for entry in entries:
        eid = str(entry.get("id", "") or "").strip()
        if not eid or eid in refs:
            continue
        unlinked.append(
            {
                "id": eid,
                "title": str(entry.get("title", "") or eid),
                "type": str(entry.get("type", "") or ""),
            }
        )

    kanban = dashboard_kanban_summary(profile)
    return {
        "total_entries": len(entries),
        "unlinked_count": len(unlinked),
        "unlinked": unlinked[:5],
        "done_uncrystallized_count": kanban["done_uncrystallized_count"],
        "done_uncrystallized": kanban["done_uncrystallized"],
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


def _graph_payload(
    *,
    goal: dict,
    kanban: dict,
    skills: dict,
    pending: dict,
    public: dict,
    health: dict,
    ui: dict[str, str] | None,
) -> dict:
    """Build a compact fixed-layout relation graph for the React dashboard."""
    projection = goal.get("projection")
    goal_label = _ui_text(ui, "dashboard_graph_goal_missing", "Set goal")
    if isinstance(projection, dict):
        goal_label = str(
            projection.get("title")
            or projection.get("label")
            or _ui_text(ui, "goal_strip_hidden", "Goal set")
        )
    elif goal.get("locked"):
        goal_label = _ui_text(ui, "goal_private_locked", "Private goal")

    nodes: list[dict[str, object]] = [
        {
            "id": "goal",
            "type": "goal",
            "label": goal_label,
            "metric": _ui_text(ui, "dashboard_metric_goal", "Current goal"),
        }
    ]
    edges: list[dict[str, str]] = []

    skill_nodes = list(skills.get("target_learning_locked") or [])
    if not skill_nodes:
        skill_nodes = list(skills.get("evidence_risk_nodes") or [])
    if not skill_nodes:
        skill_nodes = [
            {
                "id": "skill_lit",
                "label": _ui_text(ui, "dashboard_metric_skill_lit", "Skill lit"),
                "status": f"{skills.get('lit', 0)}/{skills.get('total', 0)}",
            }
        ]
    for idx, node in enumerate(skill_nodes[:3]):
        node_id = f"skill_{idx}"
        nodes.append(
            {
                "id": node_id,
                "type": "skill",
                "label": str(node.get("label") or node.get("id") or ""),
                "metric": str(node.get("status") or ""),
            }
        )
        edges.append({"from": "goal", "to": node_id})

    for idx, item in enumerate((kanban.get("doing") or [])[:3]):
        node_id = f"task_{idx}"
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
            }
        )
        edges.append({"from": "goal", "to": node_id})

    evidence_count = (
        int(pending.get("done_uncrystallized_count") or 0)
        + int(pending.get("unlinked_count") or 0)
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
        }
    )
    nodes.append(
        {
            "id": "output",
            "type": "output",
            "label": _ui_text(ui, "dashboard_output_title", "Output"),
            "metric": str(public.get("draft_total", 0)),
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
        }
    )
    for idx in range(min(len(skill_nodes), 3)):
        edges.append({"from": f"skill_{idx}", "to": "evidence"})
    for idx in range(min(len(kanban.get("doing") or []), 3)):
        edges.append({"from": f"task_{idx}", "to": "evidence"})
    edges.append({"from": "evidence", "to": "output"})
    edges.append({"from": "health", "to": "goal"})
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


def dashboard_payload(
    profile: ProfileRef,
    *,
    ui: dict[str, str] | None = None,
    ai: dict[str, object] | None = None,
) -> dict:
    """Return the stable JSON payload consumed by the React Home dashboard."""
    kanban = dashboard_kanban_summary(profile)
    skills = dashboard_skill_summary(profile)
    pending = dashboard_pending_evidence_summary(profile)
    health = dashboard_health_summary(profile)
    public = dashboard_public_summary(profile)
    goal = _goal_payload(profile)
    return {
        "profile": _profile_name(profile),
        "goal": goal,
        "kanban": kanban,
        "skills": skills,
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
            },
            "public": {
                "draft": public.get("draft_total", 0),
                "published": public.get("published_total", 0),
            },
        },
        "graph": _graph_payload(
            goal=goal,
            kanban=kanban,
            skills=skills,
            pending=pending,
            public=public,
            health=health,
            ui=ui,
        ),
        "quick_links": _quick_links_payload(ui),
        "ai": dict(ai or {}),
        "ui": dict(ui or {}),
    }
