"""Undo journal for agent writes (``profiles/<name>/agent-journal.yaml``).

A journaled agent write is recorded as entity-level ``before`` / ``after``
states, found by diffing snapshots of the entity kinds the operation may
touch (``snapshot`` before, ``snapshot`` after, ``diff``). Undo writes each
``before`` back through the owning domain writer, but only when every
entity still equals its ``after`` — if a human or another write touched it
since, the undo is refused instead of clobbering newer edits.

This file is deliberately separate from ``agent-activity.yaml`` (review
candidates / AI run traces): it is a short-lived operational log — entries
older than ``RETENTION_DAYS`` or beyond ``MAX_ENTRIES`` are pruned.

Entity kinds (``ENTITY_KINDS``):

- ``kanban_card`` — ``{"section", "index", "task"}`` in kanban.md
- ``checkin`` / ``habit_plan`` / ``habit`` — rows in activity-log.yaml
- ``goal`` / ``project_case`` / ``evidence`` / ``skill_node`` /
  ``inbox_item`` / ``research_source`` / ``learning_resource`` — rows
  (``{"index", "item"}``) in their YAML list documents
- ``north_star`` — the three North Star identity bullets in SKILL.md
- ``file:<relative path>`` — one whole text file (``{"item": {"text"}}``),
  for writers without row-level structure (Growth Log table, method drafts)

Narrative side effects (chronicle.yaml entries, plan-template usage
history) are append-only and are not reverted.
"""

from __future__ import annotations

import json
import secrets
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

import yaml

from nblane.core import activity_log, file_state, git_backup
from nblane.core.file_lock import locked_profile_write
from nblane.core.file_write import atomic_write_text, rollback_profile_files
from nblane.core.kanban_io import kanban_path, parse_kanban
from nblane.core.kanban_merge import copy_kanban_sections, save_kanban_with_merge
from nblane.core.models import KanbanSubtask, KanbanTask, KanbanTodo

JOURNAL_FILENAME = "agent-journal.yaml"
RETENTION_DAYS = 30
MAX_ENTRIES = 500

State = dict[str, Any]
Snapshot = dict[str, dict[str, State]]

_ACTIVITY_LISTS = {
    "checkin": "checkins",
    "habit_plan": "habit_plans",
    "habit": "habits",
}


class UndoError(Exception):
    """Undo refused; ``code`` is the API error code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


# ------------------------------------------------------------ list documents


@dataclass(frozen=True)
class _ListDoc:
    """One YAML document holding a list of id-keyed rows."""

    filename: str
    key: str
    load: Callable[[Path], dict[str, Any]]
    save: Callable[[Path, dict[str, Any]], None]


def _goals_load(pdir: Path) -> dict[str, Any]:
    from nblane.core.goals import load_goal_book_raw

    return load_goal_book_raw(pdir)


def _goals_save(pdir: Path, raw: dict[str, Any]) -> None:
    from nblane.core.goals import save_goal_book

    save_goal_book(pdir, raw)


def _board_load(pdir: Path) -> dict[str, Any]:
    from nblane.core.project_board import load_project_board_raw

    return load_project_board_raw(pdir) or {}


def _board_save(pdir: Path, raw: dict[str, Any]) -> None:
    from nblane.core.project_board import save_project_board

    save_project_board(pdir, raw)


def _pool_load(pdir: Path) -> dict[str, Any]:
    from nblane.core import profile_io

    return profile_io.load_evidence_pool_raw(pdir) or {}


def _pool_save(pdir: Path, raw: dict[str, Any]) -> None:
    from nblane.core import profile_io

    raw.setdefault("profile", pdir.name)
    profile_io.save_evidence_pool(pdir.name, raw)


def _tree_load(pdir: Path) -> dict[str, Any]:
    from nblane.core import profile_io

    return profile_io.load_skill_tree_raw(pdir) or {}


def _tree_save(pdir: Path, raw: dict[str, Any]) -> None:
    from nblane.core import profile_io

    raw.setdefault("profile", pdir.name)
    profile_io.save_skill_tree(pdir.name, raw)


def _inbox_load(pdir: Path) -> dict[str, Any]:
    from nblane.core import inbox

    return inbox.load_inbox_raw(pdir) or {}


def _inbox_save(pdir: Path, raw: dict[str, Any]) -> None:
    from nblane.core import inbox

    inbox.save_inbox(pdir, raw)


def _sources_load(pdir: Path) -> dict[str, Any]:
    from nblane.core.research_sources import load_research_sources_raw

    return load_research_sources_raw(pdir) or {}


def _sources_save(pdir: Path, raw: dict[str, Any]) -> None:
    from nblane.core.research_sources import save_research_sources

    save_research_sources(pdir, raw)


def _learning_load(pdir: Path) -> dict[str, Any]:
    from nblane.core.learning_log import load_learning_log_raw

    return load_learning_log_raw(pdir) or {}


def _learning_save(pdir: Path, raw: dict[str, Any]) -> None:
    from nblane.core.learning_log import save_learning_log

    save_learning_log(pdir, raw)


_LIST_DOCS: dict[str, _ListDoc] = {
    "goal": _ListDoc("goals.yaml", "goals", _goals_load, _goals_save),
    "project_case": _ListDoc("project-board.yaml", "project_cases", _board_load, _board_save),
    "evidence": _ListDoc("evidence-pool.yaml", "evidence_entries", _pool_load, _pool_save),
    "skill_node": _ListDoc("skill-tree.yaml", "nodes", _tree_load, _tree_save),
    "inbox_item": _ListDoc("inbox.yaml", "items", _inbox_load, _inbox_save),
    "research_source": _ListDoc("research/sources.yaml", "sources", _sources_load, _sources_save),
    "learning_resource": _ListDoc("learning-log.yaml", "resources", _learning_load, _learning_save),
}

ENTITY_KINDS = ("kanban_card", *_ACTIVITY_LISTS, *_LIST_DOCS, "north_star")

# Files an undo may rewrite, per kind (rollback set on failure).
_KIND_FILES: dict[str, tuple[str, ...]] = {
    "kanban_card": ("kanban.md", "project-board.yaml"),
    **{kind: (activity_log.ACTIVITY_LOG_FILENAME,) for kind in _ACTIVITY_LISTS},
    **{kind: (doc.filename,) for kind, doc in _LIST_DOCS.items()},
    "north_star": ("SKILL.md",),
}
_KIND_FILES["skill_node"] = ("skill-tree.yaml", "SKILL.md")
_KIND_FILES["evidence"] = ("evidence-pool.yaml", "SKILL.md")


FILE_KIND_PREFIX = "file:"


def file_kind(relative: str) -> str:
    return FILE_KIND_PREFIX + relative


def _file_target(pdir: Path, kind: str) -> tuple[str, Path]:
    """``(relative, absolute)`` for a ``file:`` kind, confined to *pdir*."""
    relative = kind[len(FILE_KIND_PREFIX):].strip()
    root = pdir.resolve()
    target = (root / relative).resolve()
    if not relative or target == root or root not in target.parents:
        raise ValueError(f"unsupported journal file: {relative!r}")
    return relative, target


def kind_files(pdir: Path, kind: str) -> tuple[str, ...]:
    """Files an undo of *kind* may rewrite (relative to *pdir*)."""
    if kind.startswith(FILE_KIND_PREFIX):
        return (_file_target(pdir, kind)[0],)
    return _KIND_FILES[kind]


def _rows(raw: dict[str, Any], key: str) -> list[dict[str, Any]]:
    rows = raw.get(key)
    if rows is None and key == "resources":
        rows = raw.get("entries")
    return [row for row in rows or [] if isinstance(row, dict)]


# ------------------------------------------------------------ snapshots


def _task_from_dict(raw: dict[str, Any]) -> KanbanTask:
    data = dict(raw)
    data["subtasks"] = [KanbanSubtask(**item) for item in data.get("subtasks") or []]
    data["todos"] = [KanbanTodo(**item) for item in data.get("todos") or []]
    data["details"] = list(data.get("details") or [])
    known = KanbanTask.__dataclass_fields__
    return KanbanTask(**{k: v for k, v in data.items() if k in known})


def kanban_states(pdir: Path) -> dict[str, State]:
    """Every card with a persisted id: ``{"section", "index", "task"}``.

    Parses the raw file: ``parse_kanban`` would mint random ids for cards
    lacking an id bullet, making two snapshots of the same file differ.
    """
    from nblane.core.kanban_io import _parse_kanban_sections

    out: dict[str, State] = {}
    path = kanban_path(pdir)
    if not path.exists():
        return out
    for section, tasks in _parse_kanban_sections(path.read_text(encoding="utf-8")).items():
        for index, task in enumerate(tasks):
            if task.id and task.id not in out:
                out[task.id] = {"section": section, "index": index, "task": asdict(task)}
    return out


def _north_star_state(pdir: Path) -> dict[str, State]:
    from nblane.core.profile_context import parse_identity_fields

    path = pdir / "SKILL.md"
    if not path.exists():
        return {}
    fields = parse_identity_fields(path.read_text(encoding="utf-8"))
    return {
        "identity": {
            "item": {
                "full": fields.get("North Star", ""),
                "brief": fields.get("North Star Brief", ""),
                "visibility": fields.get("North Star Visibility", ""),
            }
        }
    }


def _kind_states(pdir: Path, kind: str, log: activity_log.ActivityLog | None = None) -> dict[str, State]:
    if kind == "kanban_card":
        return kanban_states(pdir)
    if kind == "north_star":
        return _north_star_state(pdir)
    if kind.startswith(FILE_KIND_PREFIX):
        relative, target = _file_target(pdir, kind)
        if not target.is_file():
            return {}
        return {relative: {"item": {"text": target.read_text(encoding="utf-8")}}}
    if kind in _ACTIVITY_LISTS:
        log = log or activity_log.load(pdir)
        return {
            item.id: {"index": index, "item": item.to_dict()}
            for index, item in enumerate(getattr(log, _ACTIVITY_LISTS[kind]))
            if item.id
        }
    doc = _LIST_DOCS.get(kind)
    if doc is None:
        raise ValueError(f"unsupported journal entity: {kind}")
    out: dict[str, State] = {}
    for index, row in enumerate(_rows(doc.load(pdir), doc.key)):
        row_id = str(row.get("id", "") or "").strip()
        if row_id and row_id not in out:
            out[row_id] = {"index": index, "item": row}
    return out


def prepare(pdir: Path, kinds: tuple[str, ...] | list[str]) -> None:
    """Make every entity of *kinds* addressable before the first snapshot.

    Kanban cards without a persisted id are invisible to ``kanban_states``;
    the write itself would mint their ids, and the diff would then read
    those cards as created by the agent (undo would delete them). Writing
    the ids first keeps the snapshot honest.
    """
    if "kanban_card" in kinds:
        from nblane.core.kanban_io import materialize_kanban_task_ids

        materialize_kanban_task_ids(pdir)


def snapshot(pdir: Path, kinds: tuple[str, ...] | list[str]) -> Snapshot:
    """Current state of every entity of *kinds* (one read per file)."""
    log = activity_log.load(pdir) if any(kind in _ACTIVITY_LISTS for kind in kinds) else None
    return {kind: _kind_states(pdir, kind, log) for kind in dict.fromkeys(kinds)}


def _comparable(entity: str, state: State | None) -> str:
    """State without positional noise (index) for equality checks."""
    if state is None:
        return "null"
    if entity == "kanban_card":
        body = {"section": state.get("section"), "task": state.get("task")}
    else:
        body = state.get("item")
    return json.dumps(body, sort_keys=True, ensure_ascii=False, default=str)


def same_state(entity: str, left: State | None, right: State | None) -> bool:
    return _comparable(entity, left) == _comparable(entity, right)


def diff(before: Snapshot, after: Snapshot) -> list[dict[str, Any]]:
    """Entities whose state differs between two snapshots."""
    changes: list[dict[str, Any]] = []
    for kind, old in before.items():
        new = after.get(kind, {})
        for entity_id in dict.fromkeys([*old, *new]):
            if not same_state(kind, old.get(entity_id), new.get(entity_id)):
                changes.append(
                    {"entity": kind, "id": entity_id, "before": old.get(entity_id), "after": new.get(entity_id)}
                )
    return changes


# ------------------------------------------------------------ restore


def _restore_kanban(pdir: Path, targets: list[tuple[str, State | None]]) -> None:
    """Set each card to its target state.

    All target cards are removed first, then the surviving states are
    re-inserted by ascending original index so multi-card restores land in
    their original order. Project-board task refs are re-synced afterwards.
    """
    snap = file_state.snapshot_file(kanban_path(pdir))
    sections = parse_kanban(pdir)
    base = copy_kanban_sections(sections)
    ids = {card_id for card_id, _state in targets}
    touched_project = False
    for section, tasks in sections.items():
        touched_project |= any(t.project_id for t in tasks if t.id in ids)
        sections[section] = [t for t in tasks if t.id not in ids]
    restores = sorted(
        (state for _card_id, state in targets if state is not None),
        key=lambda state: int(state.get("index") or 0),
    )
    for state in restores:
        task = _task_from_dict(state["task"])
        touched_project |= bool(task.project_id)
        column = sections.setdefault(str(state["section"]), [])
        index = max(0, min(int(state.get("index") or 0), len(column)))
        column.insert(index, task)
    save_kanban_with_merge(pdir, sections, base, expected_snapshot=snap)
    if touched_project:
        from nblane.core.project_board_sync import sync_project_board_from_kanban

        sync_project_board_from_kanban(pdir.name, parse_kanban(pdir))


def _insert_by_index(items: list[Any], states: list[State], build: Callable[[Any], Any]) -> None:
    for state in sorted(states, key=lambda s: int(s.get("index") or 0)):
        index = max(0, min(int(state.get("index") or 0), len(items)))
        items.insert(index, build(state["item"]))


def _restore_activity(pdir: Path, targets: list[tuple[str, str, State | None]]) -> None:
    path = pdir / activity_log.ACTIVITY_LOG_FILENAME
    snap = file_state.snapshot_file(path)
    log = activity_log.load(pdir)
    factories = {
        "checkin": activity_log.Checkin.from_dict,
        "habit_plan": activity_log.HabitPlan.from_dict,
        "habit": activity_log.Habit.from_dict,
    }
    for entity, attr in _ACTIVITY_LISTS.items():
        ids = {entity_id for kind, entity_id, _state in targets if kind == entity}
        if not ids:
            continue
        items = getattr(log, attr)
        items[:] = [item for item in items if item.id not in ids]
        states = [state for kind, _id, state in targets if kind == entity and state is not None]
        _insert_by_index(items, states, factories[entity])
    activity_log.save(pdir, log, expected_snapshot=snap)


def _restore_list(pdir: Path, kind: str, targets: list[tuple[str, State | None]]) -> None:
    doc = _LIST_DOCS[kind]
    raw = doc.load(pdir)
    ids = {entity_id for entity_id, _state in targets}
    rows = [row for row in _rows(raw, doc.key) if str(row.get("id", "") or "").strip() not in ids]
    _insert_by_index(rows, [state for _id, state in targets if state is not None], dict)
    raw[doc.key] = rows
    doc.save(pdir, raw)


def _restore_north_star(pdir: Path, state: State | None) -> None:
    from nblane.core import north_star as north_star_core

    if state is None:
        return
    item = state.get("item") or {}
    north_star_core.update_north_star(
        pdir,
        full=str(item.get("full", "")),
        brief=str(item.get("brief", "")),
        visibility=str(item.get("visibility", "")) or None,
    )


def _restore_file(pdir: Path, kind: str, state: State | None) -> None:
    from nblane.core.file_lock import locked_profile_write

    _relative, target = _file_target(pdir, kind)
    with locked_profile_write(target.parent, target.name):
        if state is None:
            target.unlink(missing_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_text(target, str((state.get("item") or {}).get("text", "")))
    git_backup.record_change([target], action=f"undo agent write to {target.name}")


def _apply_restore(pdir: Path, changes: list[dict[str, Any]]) -> None:
    """Write every change's ``before`` back, kind by kind."""
    by_kind: dict[str, list[tuple[str, State | None]]] = {}
    for change in reversed(changes):
        by_kind.setdefault(change["entity"], []).append((change["id"], change.get("before")))
    activity_targets = [
        (kind, entity_id, state)
        for kind in _ACTIVITY_LISTS
        for entity_id, state in by_kind.get(kind, [])
    ]
    if activity_targets:
        _restore_activity(pdir, activity_targets)
    if "kanban_card" in by_kind:
        _restore_kanban(pdir, by_kind["kanban_card"])
    # Lists after kanban: a restored project case (with its own task refs)
    # wins over the refs the kanban re-sync just derived.
    for kind in _LIST_DOCS:
        if kind in by_kind:
            _restore_list(pdir, kind, by_kind[kind])
    if "north_star" in by_kind:
        for _id, state in by_kind["north_star"]:
            _restore_north_star(pdir, state)
    for kind, targets in by_kind.items():
        if kind.startswith(FILE_KIND_PREFIX):
            for _id, state in targets:
                _restore_file(pdir, kind, state)
    if ({"skill_node", "evidence"} & by_kind.keys()) and (pdir / "SKILL.md").exists():
        from nblane.core.sync import write_generated_blocks

        write_generated_blocks(pdir)


# ------------------------------------------------------------ journal file


def journal_path(pdir: Path) -> Path:
    return pdir / JOURNAL_FILENAME


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def load_entries(pdir: Path) -> list[dict[str, Any]]:
    path = journal_path(pdir)
    if not path.exists():
        return []
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return []
    entries = raw.get("entries") if isinstance(raw, dict) else None
    return [item for item in entries or [] if isinstance(item, dict)]


def _prune(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cutoff = (_now() - timedelta(days=RETENTION_DAYS)).isoformat()
    kept = [item for item in entries if str(item.get("at") or "") >= cutoff]
    return kept[-MAX_ENTRIES:]


def _write(pdir: Path, entries: list[dict[str, Any]], action: str) -> None:
    path = journal_path(pdir)
    header = (
        f"# Agent write journal for {pdir.name} (undo log; kept "
        f"{RETENTION_DAYS} days / {MAX_ENTRIES} entries)\n"
    )
    body = yaml.safe_dump(
        {"entries": entries}, allow_unicode=True, sort_keys=False, default_flow_style=False
    )
    atomic_write_text(path, header + body)
    git_backup.record_change([path], action=action)


def record(
    pdir: Path,
    *,
    actor: str,
    action: str,
    tier: str,
    summary: str,
    changes: list[dict[str, Any]],
    confirm_id: str = "",
) -> dict[str, Any] | None:
    """Append one entry; nothing is written when *changes* is empty."""
    effective = [
        change
        for change in changes
        if not same_state(change["entity"], change.get("before"), change.get("after"))
    ]
    if not effective:
        return None
    entry = {
        "id": "aj_" + _now().strftime("%Y%m%d%H%M%S") + "_" + secrets.token_hex(3),
        "at": _now().isoformat(),
        "actor": actor,
        "action": action,
        "tier": tier,
        "summary": summary,
        "confirm_id": confirm_id,
        "changes": effective,
        "undone_at": "",
        "undone_by": "",
    }
    with locked_profile_write(pdir, JOURNAL_FILENAME):
        entries = _prune(load_entries(pdir))
        entries.append(entry)
        _write(pdir, entries, f"agent journal {action}")
    return entry


def _first_conflict(pdir: Path, changes: list[dict[str, Any]], cache: Snapshot | None = None) -> bool:
    """Whether any entity no longer equals its recorded ``after``."""
    kinds = [change["entity"] for change in changes]
    current = cache if cache is not None else {}
    missing = [kind for kind in dict.fromkeys(kinds) if kind not in current]
    if missing:
        current.update(snapshot(pdir, missing))
    return any(
        not same_state(change["entity"], current[change["entity"]].get(change["id"]), change.get("after"))
        for change in changes
    )


def recent(pdir: Path, limit: int = 20) -> list[dict[str, Any]]:
    """Newest-first entries inside the retention window.

    Each entry gains ``status``: ``undone``, ``undoable`` or ``conflict``
    (an entity changed since, so undo would be refused).
    """
    entries = list(reversed(_prune(load_entries(pdir))))[: max(1, limit)]
    cache: Snapshot = {}
    for entry in entries:
        if entry.get("undone_at"):
            entry["status"] = "undone"
            continue
        changes = list(entry.get("changes") or [])
        entry["status"] = "conflict" if _first_conflict(pdir, changes, cache) else "undoable"
    return entries


def undo(pdir: Path, entry_id: str, *, actor: str) -> dict[str, Any]:
    """Revert one entry; raises ``UndoError`` when refused."""
    with locked_profile_write(pdir, JOURNAL_FILENAME):
        entries = _prune(load_entries(pdir))
        entry = next((item for item in entries if item.get("id") == entry_id), None)
        if entry is None:
            raise UndoError("journal_entry_not_found", f"找不到操作记录 {entry_id}（可能已超过 {RETENTION_DAYS} 天）。")
        if entry.get("undone_at"):
            raise UndoError("journal_entry_already_undone", "这条操作已经撤销过了。")
        changes = list(entry.get("changes") or [])
        if _first_conflict(pdir, changes):
            raise UndoError(
                "journal_undo_conflict",
                "之后又有人改过这条内容，自动撤销会覆盖新的修改，请到页面上手动处理。",
            )
        files = tuple(dict.fromkeys(name for change in changes for name in kind_files(pdir, change["entity"])))
        with git_backup.defer_changes(f"undo agent {entry.get('action')}"), rollback_profile_files(pdir, files):
            _apply_restore(pdir, changes)
        entry["undone_at"] = _now().isoformat()
        entry["undone_by"] = actor
        _write(pdir, entries, f"agent journal undo {entry.get('action')}")
    return entry
