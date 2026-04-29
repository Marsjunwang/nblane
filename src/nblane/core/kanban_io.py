"""Kanban markdown parsing and rendering."""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from collections.abc import Mapping
from dataclasses import replace
from datetime import date

from nblane.core import git_backup
from nblane.core.models import KanbanSubtask, KanbanTask
from nblane.core.profile_io import profile_dir

KANBAN_DOING = "Doing"
KANBAN_DONE = "Done"
KANBAN_QUEUE = "Queue"
KANBAN_SOMEDAY = "Someday / Maybe"
KANBAN_SECTIONS = (
    KANBAN_DOING,
    KANBAN_DONE,
    KANBAN_QUEUE,
    KANBAN_SOMEDAY,
)
KANBAN_BOARD_SECTIONS = (
    KANBAN_DOING,
    KANBAN_QUEUE,
    KANBAN_DONE,
    KANBAN_SOMEDAY,
)
KANBAN_ARCHIVE_FILENAME = "kanban-archive.md"


def _normalize_kanban_meta_key(raw_key: str) -> str | None:
    """Map a detail key label to a KanbanTask field name."""
    k = raw_key.strip().lower().replace(" ", "_")
    if k in ("id", "task_id"):
        return "id"
    if k in ("context", "why", "outcome", "started_on", "completed_on"):
        return k
    if k == "tags":
        return "tags"
    if k in ("blocked_by", "blockedby"):
        return "blocked_by"
    if raw_key.strip().lower() == "blocked by":
        return "blocked_by"
    if k == "crystallized":
        return "crystallized"
    return None


def _parse_kanban_meta_value(field: str, val: str) -> object:
    """Return typed value for a meta field (for crystallized)."""
    if field == "crystallized":
        v = val.strip().lower()
        return v in ("true", "yes", "1", "y")
    return val.strip()


def _kanban_apply_meta(task: KanbanTask, field: str, val: object) -> None:
    """Write a parsed meta key into *task*."""
    if field == "id" and isinstance(val, str):
        task.id = val.strip()
    elif field == "context" and isinstance(val, str):
        task.context = val
    elif field == "why" and isinstance(val, str):
        task.why = val
    elif field == "outcome" and isinstance(val, str):
        task.outcome = val
    elif field == "blocked_by" and isinstance(val, str):
        task.blocked_by = val
    elif field == "started_on" and isinstance(val, str) and val:
        task.started_on = val
    elif field == "completed_on" and isinstance(val, str) and val:
        task.completed_on = val
    elif field == "crystallized" and isinstance(val, bool):
        task.crystallized = val
    elif field == "tags" and isinstance(val, str):
        task.tags = val.strip()


def _kanban_skip_placeholder_title(title: str) -> bool:
    """True if this task line is the empty-column placeholder."""
    return title.strip() == "(empty)"


def _clean_task_text(value: object) -> str:
    """Return a stripped string for id hashing and comparisons."""
    return str(value or "").strip()


def _copy_kanban_task(
    task: KanbanTask,
    **changes: object,
) -> KanbanTask:
    """Return a shallow task copy with independent child lists."""
    copied = replace(
        task,
        subtasks=[replace(st) for st in task.subtasks],
        details=list(task.details),
    )
    if changes:
        copied = replace(copied, **changes)
    return copied


def _iter_kanban_section_names(
    sections: dict[str, list[KanbanTask]],
) -> list[str]:
    """Known kanban sections first, then any extension sections."""
    ordered = list(KANBAN_SECTIONS)
    ordered.extend(s for s in sections if s not in KANBAN_SECTIONS)
    return ordered


def _kanban_task_id_payload(
    profile: str,
    section: str,
    task: KanbanTask,
) -> str:
    """Canonical task content used for deterministic legacy ids."""
    parts = [
        _clean_task_text(profile),
        section,
        _clean_task_text(task.title),
        "1" if task.done else "0",
        _clean_task_text(task.context),
        _clean_task_text(task.why),
        _clean_task_text(task.blocked_by),
        _clean_task_text(task.outcome),
        _clean_task_text(task.started_on),
        _clean_task_text(task.completed_on),
        "1" if task.crystallized else "0",
    ]
    for subtask in task.subtasks:
        parts.extend(
            [
                "subtask",
                "1" if subtask.done else "0",
                _clean_task_text(subtask.title),
            ]
        )
    for detail in task.details:
        parts.extend(["detail", _clean_task_text(detail)])
    return "\x1f".join(parts)


def _generated_kanban_task_id(
    profile: str,
    section: str,
    task: KanbanTask,
) -> str:
    """Generate a deterministic compact id for a legacy task."""
    payload = _kanban_task_id_payload(profile, section, task)
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]
    return f"kb_{digest}"


def _unique_kanban_task_id(base: str, used: set[str]) -> str:
    """Return *base* or a deterministic suffixed variant not in *used*."""
    candidate = base
    suffix = 2
    while candidate in used:
        candidate = f"{base}_{suffix}"
        suffix += 1
    return candidate


def ensure_kanban_task_ids(
    sections: dict[str, list[KanbanTask]],
    profile: str,
) -> dict[str, list[KanbanTask]]:
    """Return a copy of *sections* where every task has a stable id.

    Existing non-empty ids are preserved, except duplicate ids after the
    first occurrence are replaced with deterministic generated ids.
    """
    out: dict[str, list[KanbanTask]] = {}
    used: set[str] = set()
    for section in _iter_kanban_section_names(sections):
        next_tasks: list[KanbanTask] = []
        for task in sections.get(section, []):
            raw_id = getattr(task, "id", "")
            task_id = _clean_task_text(raw_id)
            if not task_id or task_id in used:
                generated = _generated_kanban_task_id(
                    profile,
                    section,
                    task,
                )
                task_id = _unique_kanban_task_id(generated, used)
            if task_id == raw_id:
                task = _copy_kanban_task(task)
            else:
                task = _copy_kanban_task(task, id=task_id)
            used.add(task_id)
            next_tasks.append(task)
        out[section] = next_tasks
    return out


def _apply_kanban_column_move(
    task: KanbanTask,
    from_section: str,
    to_section: str,
    auto_dates: bool,
) -> KanbanTask:
    """Adjust done flag and dates when a task moves between columns."""
    moved = task
    if to_section == KANBAN_DONE:
        moved = replace(moved, done=True)
        if auto_dates:
            completed = _clean_task_text(moved.completed_on)
            if not completed:
                moved = replace(
                    moved,
                    completed_on=date.today().isoformat(),
                )
    elif from_section == KANBAN_DONE:
        moved = replace(moved, done=False)
        if auto_dates:
            moved = replace(moved, completed_on=None)
    if to_section == KANBAN_DOING and from_section != KANBAN_DOING:
        if auto_dates:
            started = _clean_task_text(moved.started_on)
            if not started:
                moved = replace(
                    moved,
                    started_on=date.today().isoformat(),
                )
    return moved


def _move_value(
    move: Mapping[str, object],
    *keys: str,
) -> object | None:
    """Return the first present value in a move mapping."""
    for key in keys:
        if key in move:
            return move[key]
    return None


def _move_string(
    move: Mapping[str, object],
    *keys: str,
) -> str:
    """Return a stripped string field from a move mapping."""
    value = _move_value(move, *keys)
    if value is None:
        return ""
    return str(value).strip()


def _move_int(
    move: Mapping[str, object],
    *keys: str,
) -> int | None:
    """Return an int field from a move mapping, or None."""
    value = _move_value(move, *keys)
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _find_move_source(
    sections: dict[str, list[KanbanTask]],
    move: Mapping[str, object],
) -> tuple[str, int] | None:
    """Resolve a move source by task id or by section/index."""
    from_section = _move_string(
        move,
        "from_section",
        "source_section",
        "from",
        "source",
    )
    task_id = _move_string(move, "task_id", "id")
    if task_id:
        section_names = (
            [from_section] if from_section in sections else list(sections)
        )
        for section in section_names:
            for idx, task in enumerate(sections.get(section, [])):
                if _clean_task_text(task.id) == task_id:
                    return section, idx

    from_index = _move_int(move, "from_index", "source_index")
    if from_section and from_index is not None:
        tasks = sections.get(from_section, [])
        if 0 <= from_index < len(tasks):
            return from_section, from_index
    return None


def apply_kanban_reorder(
    sections: dict[str, list[KanbanTask]],
    moves: list[Mapping[str, object]],
    auto_dates: bool,
) -> dict[str, list[KanbanTask]]:
    """Apply task moves without mutating *sections*.

    Each move maps either ``id``/``task_id`` or
    ``from_section`` + ``from_index`` to a destination ``to_section``.
    ``to_index`` is optional and means the post-removal insertion index;
    when absent, the task is appended. Stale or malformed moves are
    ignored.
    """
    out: dict[str, list[KanbanTask]] = {}
    for section, tasks in sections.items():
        out[section] = [_copy_kanban_task(task) for task in tasks]
    for section in KANBAN_SECTIONS:
        out.setdefault(section, [])

    for move in moves:
        source = _find_move_source(out, move)
        if source is None:
            continue
        from_section, from_index = source
        to_section = _move_string(
            move,
            "to_section",
            "destination_section",
            "dest_section",
            "to",
            "destination",
            "dest",
        )
        if not to_section:
            to_section = from_section
        if to_section not in KANBAN_SECTIONS:
            continue
        to_tasks = out.setdefault(to_section, [])
        moved = out[from_section].pop(from_index)
        moved = _apply_kanban_column_move(
            moved,
            from_section,
            to_section,
            auto_dates,
        )
        to_index = _move_int(
            move,
            "to_index",
            "destination_index",
            "dest_index",
            "position",
        )
        if to_index is None:
            to_index = len(to_tasks)
        to_index = max(0, min(to_index, len(to_tasks)))
        to_tasks.insert(to_index, moved)
    return out


def kanban_order_signature(
    sections: dict[str, list[KanbanTask]],
    section_order: tuple[str, ...] = KANBAN_BOARD_SECTIONS,
) -> dict[str, tuple[str, ...]]:
    """Return a stable section -> task-id order signature."""
    return {
        section: tuple(
            task.id
            for task in sections.get(section, [])
            if _clean_task_text(task.id)
        )
        for section in section_order
    }


def kanban_snapshot_to_moves(
    snapshot: Mapping[str, object],
    sections: dict[str, list[KanbanTask]],
    section_order: tuple[str, ...] = KANBAN_BOARD_SECTIONS,
) -> list[dict[str, object]] | None:
    """Convert a drag-board full-order snapshot into reorder moves.

    Returns ``None`` for stale/malformed snapshots, ``[]`` when the snapshot
    is current but does not change order, and a full list of id-based moves
    otherwise.
    """
    raw_columns = snapshot.get("columns")
    if not isinstance(raw_columns, list):
        return None

    expected_sections = set(section_order)
    seen_sections: list[str] = []
    known_ids = [
        task.id
        for section in section_order
        for task in sections.get(section, [])
        if _clean_task_text(task.id)
    ]
    known_counts = Counter(known_ids)
    if any(count != 1 for count in known_counts.values()):
        return None

    next_sig: dict[str, tuple[str, ...]] = {}
    seen_ids: list[str] = []
    for raw_col in raw_columns:
        if not isinstance(raw_col, Mapping):
            return None
        section = _clean_task_text(raw_col.get("section", ""))
        if section not in expected_sections or section in seen_sections:
            return None
        seen_sections.append(section)
        raw_ids = raw_col.get("task_ids")
        if not isinstance(raw_ids, list):
            return None
        task_ids: list[str] = []
        for raw_id in raw_ids:
            task_id = _clean_task_text(raw_id)
            if not task_id:
                return None
            task_ids.append(task_id)
            seen_ids.append(task_id)
        next_sig[section] = tuple(task_ids)

    if set(seen_sections) != expected_sections:
        return None
    if Counter(seen_ids) != known_counts:
        return None

    current_sig = kanban_order_signature(sections, section_order)
    ordered_next_sig = {
        section: next_sig.get(section, ())
        for section in section_order
    }
    if ordered_next_sig == current_sig:
        return []

    return [
        {
            "id": task_id,
            "to_section": section,
            "to_index": index,
        }
        for section in section_order
        for index, task_id in enumerate(ordered_next_sig[section])
    ]


def parse_kanban(name: str) -> dict[str, list[KanbanTask]]:
    """Parse kanban.md into section -> task list."""
    path = profile_dir(name) / "kanban.md"
    sections: dict[str, list[KanbanTask]] = {
        s: [] for s in KANBAN_SECTIONS
    }
    if not path.exists():
        return sections

    content = path.read_text(encoding="utf-8")
    current_section = ""
    current_task: KanbanTask | None = None

    meta_bullet = re.compile(
        r"^-\s+([a-zA-Z][^:]*?):\s*(.*)$"
    )

    for line in content.splitlines():
        stripped = line.strip()
        lead = len(line) - len(line.lstrip(" \t"))
        slim = line.lstrip(" \t")

        if stripped.startswith("## "):
            if (
                current_task is not None
                and current_section in sections
            ):
                sections[current_section].append(current_task)
                current_task = None
            current_section = stripped[3:].strip()
            continue

        if stripped in ("---", "") or stripped.startswith(">"):
            continue

        if lead == 0:
            top_cb = re.match(
                r"^-\s+\[([ xX])\]\s+(.+)$", slim
            )
            if top_cb:
                if (
                    current_task is not None
                    and current_section in sections
                ):
                    sections[current_section].append(current_task)
                t_title = top_cb.group(2).strip()
                if _kanban_skip_placeholder_title(t_title):
                    current_task = None
                    continue
                done = top_cb.group(1).lower() == "x"
                current_task = KanbanTask(
                    title=t_title,
                    done=done,
                )
                continue
            top_plain = re.match(r"^-\s+(.+)$", slim)
            if top_plain:
                text = top_plain.group(1).strip()
                if current_section != KANBAN_SOMEDAY:
                    continue
                if current_task is not None:
                    sections[current_section].append(
                        current_task
                    )
                if _kanban_skip_placeholder_title(text):
                    current_task = None
                    continue
                current_task = KanbanTask(title=text)
                continue
            continue

        sub_cb = re.match(
            r"^-\s+\[([ xX])\]\s+(.+)$", slim
        )
        if sub_cb and current_task is not None:
            sd = sub_cb.group(1).lower() == "x"
            current_task.subtasks.append(
                KanbanSubtask(
                    title=sub_cb.group(2).strip(),
                    done=sd,
                )
            )
            continue

        ind_bullet = re.match(r"^-\s+(.+)$", slim)
        if ind_bullet and current_task is not None:
            rest = ind_bullet.group(1).strip()
            mb = meta_bullet.match(slim)
            if mb:
                raw_key = mb.group(1).strip()
                val_part = mb.group(2).strip()
                nk = _normalize_kanban_meta_key(raw_key)
                if nk is not None:
                    typed = _parse_kanban_meta_value(nk, val_part)
                    _kanban_apply_meta(current_task, nk, typed)
                    continue
            current_task.details.append(rest)
            continue

    if current_task is not None and current_section in sections:
        sections[current_section].append(current_task)

    return ensure_kanban_task_ids(sections, name)


def _render_kanban_task_lines(
    section: str,
    task: KanbanTask,
) -> list[str]:
    """Emit markdown lines for one task under *section*."""
    lines: list[str] = []
    if section == KANBAN_SOMEDAY:
        lines.append(f"- {task.title}")
    else:
        check = "[x]" if task.done else "[ ]"
        lines.append(f"- {check} {task.title}")
    meta_pairs: list[tuple[str, str]] = []
    if task.id.strip():
        meta_pairs.append(("id", task.id.strip()))
    if task.context.strip():
        meta_pairs.append(("context", task.context.strip()))
    if task.why.strip():
        meta_pairs.append(("why", task.why.strip()))
    if task.blocked_by.strip():
        meta_pairs.append(("blocked by", task.blocked_by.strip()))
    if task.outcome.strip():
        meta_pairs.append(("outcome", task.outcome.strip()))
    if task.started_on:
        meta_pairs.append(("started_on", task.started_on.strip()))
    if task.completed_on:
        meta_pairs.append(("completed_on", task.completed_on.strip()))
    if task.crystallized:
        meta_pairs.append(("crystallized", "true"))
    if task.tags.strip():
        meta_pairs.append(("tags", task.tags.strip()))
    for mk, mv in meta_pairs:
        lines.append(f"  - {mk}: {mv}")
    for st in task.subtasks:
        if not st.title.strip():
            continue
        ch = "[x]" if st.done else "[ ]"
        lines.append(f"  - {ch} {st.title}")
    for detail in task.details:
        lines.append(f"  - {detail}")
    return lines


def render_kanban(
    name: str,
    sections: dict[str, list[KanbanTask]],
) -> str:
    """Render structured sections back to kanban.md text."""
    render_sections = ensure_kanban_task_ids(sections, name)
    today = date.today().isoformat()
    lines = [
        f"# {name} · Kanban",
        "",
        f"> Updated: {today}",
        "> Rule: nothing lives in \"doing\" for more than"
        " 2 weeks. Move it or break it down.",
        "",
        "---",
    ]
    for section in KANBAN_SECTIONS:
        lines += ["", f"## {section}", ""]
        tasks = render_sections.get(section, [])
        if not tasks:
            lines.append("- (empty)")
        else:
            for task in tasks:
                lines.extend(
                    _render_kanban_task_lines(section, task)
                )
        lines += ["", "---"]
    return "\n".join(lines) + "\n"


def save_kanban(
    name: str,
    sections: dict[str, list[KanbanTask]],
) -> None:
    """Write kanban.md back from structured sections."""
    path = profile_dir(name) / "kanban.md"
    path.write_text(
        render_kanban(name, sections), encoding="utf-8"
    )
    git_backup.record_change(
        [path],
        action=f"update {name}/kanban.md",
    )


def append_kanban_archive(
    name: str,
    tasks: list[KanbanTask],
) -> None:
    """Append Done tasks to kanban-archive.md under today's heading."""
    if not tasks:
        return
    path = profile_dir(name) / KANBAN_ARCHIVE_FILENAME
    today = date.today().isoformat()
    body_lines: list[str] = [f"\n## Archived · {today}\n"]
    archive_tasks = ensure_kanban_task_ids(
        {KANBAN_DONE: tasks},
        name,
    )[KANBAN_DONE]
    for task in archive_tasks:
        body_lines.extend(
            _render_kanban_task_lines(KANBAN_DONE, task)
        )
        body_lines.append("")
    block = "\n".join(body_lines)
    if path.exists():
        prev = path.read_text(encoding="utf-8")
        path.write_text(prev + block, encoding="utf-8")
    else:
        header = (
            f"# {name} · Kanban archive\n\n"
            "> Tasks moved here from kanban.md (Done column).\n\n"
            "---\n"
        )
        path.write_text(header + block, encoding="utf-8")
    git_backup.record_change(
        [path],
        action=f"append {name}/kanban-archive.md",
    )
