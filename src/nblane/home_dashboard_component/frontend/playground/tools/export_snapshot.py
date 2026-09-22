#!/usr/bin/env python3
"""One-off exporter: read the real profile 王军 (READ-ONLY) and emit a static
snapshot.json for the growth-galaxy playground.

Sources (all read-only):
  - schemas/robotics-engineer.yaml   (node catalog: id, label, level, category)
  - profiles/王军/skill-tree.yaml     (per-node status: locked|learning|solid|expert)
  - profiles/王军/goals.yaml          (goal titles/status; no progress field exists)
  - profiles/王军/SKILL.md            (North Star line)
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[6]
SCHEMA = ROOT / "schemas" / "robotics-engineer.yaml"
PROFILE = ROOT / "profiles" / "王军"
OUT = Path(__file__).parent / ".." / "data" / "snapshot.json"

TODAY = date.today()
GUEST_WINDOW_DAYS = 30
GUEST_MIN = 4  # display density floor: newest dated entries fly even if older

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
DONE_SECTION = "done"


def parse_evidence_date(raw):
    """Tolerant parse: '2026-09-08' | '2026-06' | '2025' | ''. Returns date or None."""
    s = str(raw or "").strip()
    if not s:
        return None
    m = re.match(r"^(\d{4})(?:-(\d{1,2}))?(?:-(\d{1,2}))?", s)
    if not m:
        return None
    y = int(m.group(1))
    mo = int(m.group(2) or 7)
    d = int(m.group(3) or 15)
    try:
        return date(y, mo, d)
    except ValueError:
        return None


def parse_kanban(path: Path):
    """Parse kanban.md sections into task dicts."""
    tasks = []
    section = None
    current = None
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            name = m.group(1).strip().lower()
            section = {"doing": "doing", "done": "done", "queue": "queue"}.get(
                name.split()[0] if name else "", "someday")
            continue
        m = re.match(r"^- \[[ x]\]\s*(.+)$", line) or re.match(r"^-\s+(.+)$", line)
        if m and section:
            current = {"title": m.group(1).strip(), "status": section,
                       "id": None, "project_id": None, "started_on": None}
            tasks.append(current)
            continue
        m = re.match(r"^\s+-\s+(id|project_id|started_on|completed_on):\s*(.+)$", line)
        if m and current is not None:
            key, val = m.group(1), m.group(2).strip()
            if key == "id":
                current["id"] = val
            elif key == "project_id":
                current["project_id"] = val
            elif key == "started_on":
                current["started_on"] = val
    return [t for t in tasks if t["id"]]


def derive_progress(case, tasks_by_id):
    """Progress 0..1 or None. task_refs completion first, then milestones."""
    refs = case.get("task_refs") or []
    if refs:
        states = [tasks_by_id.get(r, {}).get("status") for r in refs]
        known = [s for s in states if s]
        if known:
            return round(sum(1 for s in known if s == DONE_SECTION) / len(known), 3)
    ms = case.get("milestones") or []
    if ms:
        done = sum(1 for m in ms if str(m.get("status", "")).lower() in DONE_MILESTONE)
        return round(done / len(ms), 3)
    return None


def main() -> int:
    schema = yaml.safe_load(SCHEMA.read_text(encoding="utf-8"))
    tree = yaml.safe_load((PROFILE / "skill-tree.yaml").read_text(encoding="utf-8"))
    goals_doc = yaml.safe_load((PROFILE / "goals.yaml").read_text(encoding="utf-8"))
    skill_md = (PROFILE / "SKILL.md").read_text(encoding="utf-8")

    status_by_id = {n["id"]: n.get("status", "locked") for n in tree.get("nodes", [])}

    skills = []
    for node in schema.get("nodes", []):
        status = status_by_id.get(node["id"], "locked")
        skills.append({
            "id": node["id"],
            "label": node.get("label", node["id"]),
            "category": node.get("category", "misc"),
            "level": node.get("level", 1),
            "status": status,
            "lit": status in LIT_STATUSES,
        })

    cat_order = []
    for s in skills:
        if s["category"] not in cat_order:
            cat_order.append(s["category"])
    categories = []
    for cat in cat_order:
        members = [s for s in skills if s["category"] == cat]
        categories.append({
            "id": cat,
            "name": CATEGORY_ZH.get(cat, cat),
            "count": len(members),
            "lit_count": sum(1 for s in members if s["lit"]),
            "learning_count": sum(1 for s in members if s["status"] == "learning"),
        })

    goals = [
        {
            "id": g["id"],
            "title": g.get("title") or g["id"],
            "status": g.get("status", "active"),
            "progress": None,  # goals.yaml has no progress field
            "summary": (g.get("summary") or "").strip(),
            "start": str(g.get("start") or ""),
            "target": str(g.get("target") or ""),
        }
        for g in goals_doc.get("goals", [])
        if g.get("status") == "active"
    ]

    m = re.search(r"\*\*North Star\*\*:\s*(.+)", skill_md)
    north_star = m.group(1).strip() if m else "（SKILL.md 中未找到 North Star）"

    # ---- snapshot v2: projects / tasks / evidence ----
    board = yaml.safe_load((PROFILE / "project-board.yaml").read_text(encoding="utf-8"))
    kanban_tasks = parse_kanban(PROFILE / "kanban.md")
    tasks_by_id = {t["id"]: t for t in kanban_tasks}
    pool = yaml.safe_load((PROFILE / "evidence-pool.yaml").read_text(encoding="utf-8"))

    skill_refs_by_ev = {}
    for n in tree.get("nodes", []):
        for ref in n.get("evidence_refs") or []:
            skill_refs_by_ev.setdefault(ref, []).append(n["id"])

    projects = []
    for case in board.get("project_cases", []):
        projects.append({
            "id": case["id"],
            "title": case.get("title") or case["id"],
            "status": case.get("status", "active"),
            "kind": case.get("kind", "work"),
            "goal_ids": case.get("goal_refs") or [],
            "progress": derive_progress(case, tasks_by_id),
            "task_count": len(case.get("task_refs") or []),
            "evidence_count": len(case.get("evidence_refs") or []),
            "time_range": case.get("time_range") or "",
        })

    tasks = [{
        "id": t["id"], "title": t["title"], "status": t["status"],
        "project_id": t["project_id"],
    } for t in kanban_tasks]

    evidence = []
    for e in pool.get("evidence_entries", []):
        if e.get("deprecated"):
            continue
        dt = parse_evidence_date(e.get("date"))
        age = (TODAY - dt).days if dt else None
        evidence.append({
            "id": e["id"],
            "type": e.get("type", "practice"),
            "title": (e.get("title") or e["id"])[:40],
            "date": str(e.get("date") or ""),
            "age_days": age,
            "strength": e.get("strength", "unrated"),
            "review_status": e.get("review_status", "needs_review"),
            "summary": (e.get("summary") or "").strip()[:140],
            "skill_ids": skill_refs_by_ev.get(e["id"], []),
            "project_refs": e.get("project_refs") or [],
        })
    dated = sorted([e for e in evidence if e["age_days"] is not None],
                   key=lambda e: e["age_days"])
    flying_ids = {e["id"] for e in evidence
                  if e["age_days"] is not None and e["age_days"] <= GUEST_WINDOW_DAYS}
    for e in dated[:GUEST_MIN]:  # density floor: newest few always fly
        flying_ids.add(e["id"])
    for e in evidence:
        e["flying"] = e["id"] in flying_ids

    counts = {
        "evidence": len(evidence),
        "evidence_needs_review": sum(1 for e in evidence if e["review_status"] == "needs_review"),
        "evidence_flying": sum(1 for e in evidence if e["flying"]),
        "projects_active": sum(1 for p in projects if p["status"] == "active"),
        "tasks": len(tasks),
        "tasks_done": sum(1 for t in tasks if t["status"] == "done"),
        "skills_lit": sum(1 for s in skills if s["lit"]),
    }

    snapshot = {
        "profile": "王军",
        "snapshot_version": 2,
        "generated_on": TODAY.isoformat(),
        "generated_from": [
            "schemas/robotics-engineer.yaml",
            "profiles/王军/skill-tree.yaml",
            "profiles/王军/goals.yaml",
            "profiles/王军/SKILL.md",
            "profiles/王军/project-board.yaml",
            "profiles/王军/kanban.md",
            "profiles/王军/evidence-pool.yaml",
        ],
        "north_star": north_star,
        "goals": goals,
        "categories": categories,
        "skills": skills,
        "projects": projects,
        "tasks": tasks,
        "evidence": evidence,
        "counts": counts,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    lit = sum(1 for s in skills if s["lit"])
    learning = sum(1 for s in skills if s["status"] == "learning")
    print(f"skills={len(skills)} lit={lit} learning={learning} "
          f"categories={len(categories)} goals={len(goals)}")
    print(f"projects={len(projects)} active={counts['projects_active']} tasks={len(tasks)} "
          f"evidence={counts['evidence']} flying={counts['evidence_flying']} "
          f"needs_review={counts['evidence_needs_review']}")
    print(f"progress: " + ", ".join(f"{p['id']}={p['progress']}" for p in projects))
    print(f"north_star={north_star[:40]}...")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
