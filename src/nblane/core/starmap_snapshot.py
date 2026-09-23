"""Growth-starmap snapshot aggregation (one shot for the SPA home scene).

Ports the reference semantics of
``home_dashboard_component/frontend/playground/tools/export_snapshot.py``
onto the live read paths: SKILL.md (North Star), goals.yaml, skill-tree.yaml
overlay + domain schema (locked schema nodes included), the projects-board
aggregation (goal grouping + progress), and the evidence pool (guest stars
with the 30-day window + newest-4 density floor, seated stars with
``project_refs``). Pure read; the web layer computes the source-file ETag.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from nblane.core import profile_io, schema_io
from nblane.core import evidence_review as evidence_review_core
from nblane.core import projects_board
from nblane.core.models import EVIDENCE_REVIEW_STATUSES
from nblane.core.profile_context import parse_identity_fields

GUEST_WINDOW_DAYS = 30
GUEST_MIN = 4  # display density floor: newest dated entries fly even if older

# Category display names (zh) for the sector band. The domain schemas do not
# carry per-category labels, so this table is the single server-side source
# (moved from the playground exporter / SPA snapshot.ts).
CATEGORY_ZH = {
    "foundations": "基础",
    "control": "控制",
    "influence": "影响力",
    "leadership": "领导力",
    "learning": "学习力",
    "locomotion": "运动",
    "manipulation": "操作",
    "middleware": "中间件",
    "navigation": "导航",
    "perception": "感知",
    "research": "研究",
    "simulation": "仿真",
    "strategy": "战略",
    "systems": "系统",
}

LIT_STATUSES = {"solid", "expert"}
DONE_MILESTONE = {"done", "completed", "complete", "achieved", "shipped"}

_DATE_RE = re.compile(r"^(\d{4})(?:-(\d{1,2}))?(?:-(\d{1,2}))?")


def parse_evidence_date(raw: object) -> date | None:
    """Tolerant parse: '2026-09-08' | '2026-06' | '2025' | ''. None on junk."""
    text = str(raw or "").strip()
    if not text:
        return None
    match = _DATE_RE.match(text)
    if not match:
        return None
    year = int(match.group(1))
    month = int(match.group(2) or 7)
    day = int(match.group(3) or 15)
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _review_status(raw: str) -> str:
    """Normalized review status; empty/unknown means not yet reviewed."""
    clean = raw.strip()
    return clean if clean in EVIDENCE_REVIEW_STATUSES else "needs_review"


def _project_progress(
    column_counts: dict[str, int],
    done_count: int,
    milestones: list,
) -> float | None:
    """Progress 0..1 or None: task completion first, then milestones."""
    total = sum(column_counts.values())
    if total > 0:
        return round(done_count / total, 3)
    if milestones:
        done = sum(
            1
            for milestone in milestones
            if str(getattr(milestone, "status", "") or "").lower() in DONE_MILESTONE
        )
        return round(done / len(milestones), 3)
    return None


def _task_count(column_counts: dict[str, int]) -> int:
    return sum(column_counts.values())


def build_starmap_snapshot(pdir: Path, today: date | None = None) -> dict:
    """Assemble the full starmap payload for one profile directory.

    Returns a plain dict matching ``StarmapResponse`` (web_api/schemas.py):
    ``profile``/``generated_on``/``north_star``/``goals``/``categories``/
    ``skills``/``projects``/``evidence``/``counts``. Missing optional files
    degrade to empty sections; a missing schema yields an empty skill field.
    """
    today = today or date.today()

    identity = parse_identity_fields(profile_io.load_skill_md(pdir.name))
    north_star = (
        str(identity.get("North Star", "") or "").strip()
        or str(identity.get("North Star Brief", "") or "").strip()
    )

    # ---- skill field: schema nodes first (locked underlay included), then
    # overlay-only nodes unknown to the schema (misc sector, overlay order).
    raw_tree = profile_io.load_skill_tree_raw(pdir) or {}
    schema_name = str(raw_tree.get("schema") or "")
    schema = schema_io.load_schema(schema_name) if schema_name else None
    overlay: dict[str, dict] = {}
    for node in raw_tree.get("nodes") or []:
        if isinstance(node, dict) and node.get("id"):
            overlay[str(node["id"])] = node

    skills: list[dict] = []
    seen: set[str] = set()
    if schema is not None:
        for node in schema.nodes:
            status = str(overlay.get(node.id, {}).get("status") or "locked")
            skills.append(
                {
                    "id": node.id,
                    "label": node.label or node.id,
                    "category": node.category or "misc",
                    "status": status,
                    "lit": status in LIT_STATUSES,
                }
            )
            seen.add(node.id)
    for nid, node in overlay.items():
        if nid in seen:
            continue
        status = str(node.get("status") or "locked")
        skills.append(
            {
                "id": nid,
                "label": nid,
                "category": "misc",
                "status": status,
                "lit": status in LIT_STATUSES,
            }
        )

    cat_order: list[str] = []
    for skill in skills:
        if skill["category"] not in cat_order:
            cat_order.append(skill["category"])
    categories = []
    for cat in cat_order:
        members = [s for s in skills if s["category"] == cat]
        categories.append(
            {
                "id": cat,
                "name": CATEGORY_ZH.get(cat, cat),
                "count": len(members),
                "lit_count": sum(1 for s in members if s["lit"]),
                "learning_count": sum(1 for s in members if s["status"] == "learning"),
            }
        )

    # ---- goals (active only, book order) ----
    book = profile_io.load_goal_book(pdir)
    goals = [
        {
            "id": goal.id,
            "title": goal.title or goal.id,
            "status": goal.status or "active",
            "summary": goal.summary.strip(),
            "start": goal.start,
            "target": goal.target,
        }
        for goal in book.goals
        if (goal.status or "active") == "active"
    ]

    # ---- projects: the board's first-goal grouping, planets beside goals ----
    board = projects_board.build_projects_board(pdir)
    projects: list[dict] = []

    def _push_project(project, goal_ids: list[str]) -> None:
        projects.append(
            {
                "id": project.id,
                "title": project.title or project.id,
                "status": project.status or "active",
                "kind": project.kind or "internal",
                "goal_ids": goal_ids,
                "progress": _project_progress(
                    dict(project.column_counts), project.done_count, project.milestones
                ),
                "task_count": _task_count(dict(project.column_counts)),
                "time_range": project.time_range or "",
            }
        )

    for goal in board.goals:
        for project in goal.projects:
            _push_project(project, [goal.id])
    for project in board.ungrouped_projects:
        _push_project(project, list(project.goal_refs))

    # ---- evidence: guests (flying) + seated + dust, all one list ----
    pool = profile_io.load_evidence_pool(pdir)
    usage = evidence_review_core.evidence_usage_index(pdir)
    evidence: list[dict] = []
    for record in pool.evidence_entries if pool else []:
        if record.deprecated:
            continue
        parsed = parse_evidence_date(record.date)
        age_days = (today - parsed).days if parsed else None
        evidence.append(
            {
                "id": record.id,
                "type": record.type or "practice",
                "title": (record.title or record.id)[:40],
                "date": record.date,
                "age_days": age_days,
                "strength": record.strength or "unrated",
                "review_status": _review_status(record.review_status),
                "summary": record.summary.strip()[:140],
                "skill_ids": [entry["id"] for entry in usage.get(record.id, [])],
                "project_refs": list(record.project_refs),
                "flying": False,
            }
        )
    dated = sorted(
        (e for e in evidence if e["age_days"] is not None),
        key=lambda e: e["age_days"],
    )
    flying_ids = {
        e["id"]
        for e in evidence
        if e["age_days"] is not None and e["age_days"] <= GUEST_WINDOW_DAYS
    }
    for entry in dated[:GUEST_MIN]:  # density floor: newest few always fly
        flying_ids.add(entry["id"])
    for entry in evidence:
        entry["flying"] = entry["id"] in flying_ids
        entry.pop("age_days", None)

    counts = {
        "evidence": len(evidence),
        "evidence_needs_review": sum(
            1 for e in evidence if e["review_status"] == "needs_review"
        ),
        "evidence_flying": sum(1 for e in evidence if e["flying"]),
        "projects_active": sum(1 for p in projects if p["status"] == "active"),
        "skills_lit": sum(1 for s in skills if s["lit"]),
    }

    return {
        "profile": pdir.name,
        "generated_on": today.isoformat(),
        "schema_name": schema_name,
        "north_star": north_star,
        "goals": goals,
        "categories": categories,
        "skills": skills,
        "projects": projects,
        "evidence": evidence,
        "counts": counts,
    }
