"""Kanban markdown parsing and rendering."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import replace
from datetime import date
from pathlib import Path
from typing import TypeVar
from uuid import uuid4

from nblane.core import git_backup
from nblane.core.file_lock import locked_profile_write
from nblane.core.file_state import FileSnapshot, assert_unchanged
from nblane.core.file_write import atomic_write_text
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

_T = TypeVar("_T")
_KANBAN_MULTILINE_META_FIELDS = frozenset(
    {"context", "why", "blocked_by", "outcome"}
)
_KANBAN_META_BULLET_RE = re.compile(
    r"^-\s+([a-zA-Z][^:]*?):\s*(.*)$"
)
_KANBAN_DETAIL_PREFIX_RE = re.compile(
    r"^([a-zA-Z][^:]*?):\s*(.*)$"
)


def _normalize_kanban_meta_key(raw_key: str) -> str | None:
    """Map a detail key label to a KanbanTask field name."""
    k = raw_key.strip().lower().replace(" ", "_")
    if k in ("id", "task_id"):
        return "id"
    if k in ("project_id", "project"):
        return "project_id"
    if k in ("milestone_id", "milestone"):
        return "milestone_id"
    if k in ("agent_task_id", "agent_task"):
        return "agent_task_id"
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
    elif field == "project_id" and isinstance(val, str):
        task.project_id = val.strip()
    elif field == "milestone_id" and isinstance(val, str):
        task.milestone_id = val.strip()
    elif field == "agent_task_id" and isinstance(val, str):
        task.agent_task_id = val.strip()
    elif field == "tags" and isinstance(val, str):
        task.tags = val.strip()


def _kanban_tags_text(value: object) -> str:
    """Return canonical comma-separated tag text for render-time compatibility."""
    if isinstance(value, (list, tuple, set)):
        tags: list[str] = []
        seen: set[str] = set()
        for item in value:
            tag = _clean_task_text(item)
            key = tag.casefold()
            if not tag or key in seen:
                continue
            seen.add(key)
            tags.append(tag)
        return ", ".join(tags)
    return _clean_task_text(value)


def _looks_like_kanban_detail_escape_payload(text: str) -> bool:
    """True when *text* starts with a key that needs detail escaping."""
    mb = _KANBAN_DETAIL_PREFIX_RE.match(text.strip())
    if not mb:
        return False
    raw_key = mb.group(1).strip()
    if raw_key.lower() == "detail":
        return True
    return _normalize_kanban_meta_key(raw_key) is not None


def _parse_kanban_detail_escape(value: str) -> str | None:
    """Return the original detail text from a detail escape if present."""
    text = value.strip()
    if _looks_like_kanban_detail_escape_payload(text):
        return text
    return None


def _kanban_detail_needs_escape(detail: str) -> bool:
    """True if rendering *detail* directly could be parsed as metadata."""
    text = detail.strip()
    mb = _KANBAN_DETAIL_PREFIX_RE.match(text)
    if not mb:
        return False
    raw_key = mb.group(1).strip()
    if _normalize_kanban_meta_key(raw_key) is not None:
        return True
    if raw_key.lower() == "detail":
        return _looks_like_kanban_detail_escape_payload(mb.group(2))
    return False


def _dedent_kanban_block_line(line: str, bullet_indent: int) -> str:
    """Remove the expected content indent for a Kanban literal block."""
    content_indent = bullet_indent + 2
    lead = len(line) - len(line.lstrip(" \t"))
    if lead >= content_indent:
        return line[content_indent:]
    return line[lead:]


def _collect_kanban_literal_block(
    lines: list[str],
    start_index: int,
    bullet_indent: int,
) -> tuple[str, int]:
    """Collect lines following a ``- key: |`` metadata bullet."""
    block_lines: list[str] = []
    index = start_index
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if stripped:
            lead = len(line) - len(line.lstrip(" \t"))
            if lead <= bullet_indent:
                break
        if not stripped:
            block_lines.append("")
        else:
            block_lines.append(
                _dedent_kanban_block_line(line, bullet_indent)
            )
        index += 1
    while block_lines and block_lines[-1] == "":
        block_lines.pop()
    return "\n".join(block_lines), index


def _kanban_skip_placeholder_title(title: str) -> bool:
    """True if this task line is the empty-column placeholder."""
    return title.strip() == "(empty)"


def _clean_task_text(value: object) -> str:
    """Return a stripped string for id handling and comparisons."""
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


def _new_kanban_task_id(used: set[str]) -> str:
    """Return a fresh random task id not present in *used*.

    Ids are random (``kb_`` + 12 hex chars), not content-derived, so editing
    a task never changes its id. The id becomes stable once it is rendered
    back into kanban.md (first save).
    """
    while True:
        candidate = f"kb_{uuid4().hex[:12]}"
        if candidate not in used:
            return candidate


def ensure_kanban_task_ids(
    sections: dict[str, list[KanbanTask]],
    profile: str,
) -> dict[str, list[KanbanTask]]:
    """Return a copy of *sections* where every task has a stable id.

    Existing non-empty ids are preserved verbatim, except duplicate ids
    after the first occurrence, which are replaced with fresh random ids.
    Tasks without an id receive a random ``kb_`` id that is unique within
    the board; the *profile* argument is kept for call-site compatibility
    and no longer influences generation.
    """
    out: dict[str, list[KanbanTask]] = {}
    used: set[str] = set()
    for section in _iter_kanban_section_names(sections):
        next_tasks: list[KanbanTask] = []
        for task in sections.get(section, []):
            raw_id = getattr(task, "id", "")
            task_id = _clean_task_text(raw_id)
            if not task_id or task_id in used:
                task_id = _new_kanban_task_id(used)
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


def resolve_kanban_section(raw: object) -> str | None:
    """Map user/agent text to a canonical kanban section name, or None."""
    clean = _clean_task_text(raw)
    for section in KANBAN_SECTIONS:
        if section == clean or section.casefold() == clean.casefold():
            return section
    return None


def find_kanban_card(
    sections: dict[str, list[KanbanTask]],
    card_ref: str,
) -> tuple[tuple[str, int, KanbanTask] | None, str, str]:
    """Locate one card by exact title or unique substring of the title.

    Returns ``((section, index, task), "", "")`` on a unique hit, otherwise
    ``(None, kind, message)`` where *kind* is ``"ambiguous"`` when several
    cards match or ``"not_found"`` when none do.
    """
    exact = [
        (section, index, task)
        for section, tasks in sections.items()
        for index, task in enumerate(tasks)
        if task.title.strip() == card_ref
    ]
    if len(exact) == 1:
        return exact[0], "", ""
    if len(exact) > 1:
        hits = ", ".join(sorted({section for section, _, _ in exact}))
        return (
            None,
            "ambiguous",
            f"card_ref {card_ref!r} matches {len(exact)} cards exactly "
            f"(sections: {hits}); use a more specific ref",
        )
    lowered = card_ref.casefold()
    partial = [
        (section, index, task)
        for section, tasks in sections.items()
        for index, task in enumerate(tasks)
        if lowered in task.title.casefold()
    ]
    if len(partial) == 1:
        return partial[0], "", ""
    if not partial:
        return None, "not_found", f"no kanban card matches card_ref {card_ref!r}"
    titles = "; ".join(
        f"{section}: {task.title.strip()}"
        for section, _, task in partial[:5]
    )
    return (
        None,
        "ambiguous",
        f"card_ref {card_ref!r} is ambiguous: matches {len(partial)} "
        f"cards ({titles})",
    )


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


def _parse_kanban_sections(
    content: str,
) -> dict[str, list[KanbanTask]]:
    """Parse raw kanban markdown into section -> task list (no id fill)."""
    sections: dict[str, list[KanbanTask]] = {
        s: [] for s in KANBAN_SECTIONS
    }
    current_section = ""
    current_task: KanbanTask | None = None

    lines = content.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        index += 1
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
            mb = _KANBAN_META_BULLET_RE.match(slim)
            if mb:
                raw_key = mb.group(1).strip()
                val_part = mb.group(2).strip()
                if raw_key.lower() == "detail":
                    detail = _parse_kanban_detail_escape(val_part)
                    if detail is not None:
                        current_task.details.append(detail)
                        continue
                nk = _normalize_kanban_meta_key(raw_key)
                if nk is not None:
                    is_literal_block = False
                    if (
                        nk in _KANBAN_MULTILINE_META_FIELDS
                        and val_part == "|"
                    ):
                        val_part, index = _collect_kanban_literal_block(
                            lines,
                            index,
                            lead,
                        )
                        is_literal_block = True
                    if is_literal_block:
                        typed = val_part
                    else:
                        typed = _parse_kanban_meta_value(nk, val_part)
                    _kanban_apply_meta(current_task, nk, typed)
                    continue
            current_task.details.append(rest)
            continue

    if current_task is not None and current_section in sections:
        sections[current_section].append(current_task)

    return sections


def parse_kanban_text(
    content: str,
    profile: str,
) -> dict[str, list[KanbanTask]]:
    """Parse raw kanban markdown into section -> task list.

    Tasks without an id bullet receive a freshly generated random id; the id
    only becomes stable once the board is saved back to kanban.md.
    """
    return ensure_kanban_task_ids(_parse_kanban_sections(content), profile)


def kanban_path(profile: str | Path) -> Path:
    """Return the kanban.md path for a profile name or profile directory."""
    if isinstance(profile, Path):
        return profile / "kanban.md"
    return profile_dir(profile) / "kanban.md"


def parse_kanban(name: str | Path) -> dict[str, list[KanbanTask]]:
    """Parse kanban.md into section -> task list."""
    path = kanban_path(name)
    if not path.exists():
        return {s: [] for s in KANBAN_SECTIONS}
    content = path.read_text(encoding="utf-8")
    profile_name = path.parent.name if isinstance(name, Path) else name
    return parse_kanban_text(content, profile_name)


def materialize_kanban_task_ids(profile: str | Path) -> bool:
    """Persist generated ids for kanban tasks that have none on disk.

    Generated ids are random, so they only stay stable across parses once
    they are written back to kanban.md. Flows that match tasks by id across
    separate parses (Done -> evidence picker, crystallized refresh) call
    this first so a legacy id-less file gains persisted ids up front.
    Returns True when kanban.md was rewritten.
    """
    path = kanban_path(profile)
    if not path.exists():
        return False
    name = path.parent.name
    sections = _parse_kanban_sections(path.read_text(encoding="utf-8"))
    missing = any(
        not _clean_task_text(getattr(task, "id", ""))
        for tasks in sections.values()
        for task in tasks
    )
    if not missing:
        return False
    ensured = ensure_kanban_task_ids(sections, name)
    atomic_write_text(path, render_kanban(name, ensured))
    git_backup.record_change(
        [path],
        action=f"materialize {name}/kanban.md task ids",
    )
    return True


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
    if task.project_id.strip():
        meta_pairs.append(("project_id", task.project_id.strip()))
    if task.milestone_id.strip():
        meta_pairs.append(("milestone_id", task.milestone_id.strip()))
    if task.agent_task_id.strip():
        meta_pairs.append(("agent_task_id", task.agent_task_id.strip()))
    tags_text = _kanban_tags_text(task.tags)
    if tags_text:
        meta_pairs.append(("tags", tags_text))
    for mk, mv in meta_pairs:
        field = _normalize_kanban_meta_key(mk)
        if field in _KANBAN_MULTILINE_META_FIELDS and "\n" in mv:
            lines.append(f"  - {mk}: |")
            for block_line in mv.splitlines():
                lines.append(f"    {block_line}")
        else:
            lines.append(f"  - {mk}: {mv}")
    for st in task.subtasks:
        if not st.title.strip():
            continue
        ch = "[x]" if st.done else "[ ]"
        lines.append(f"  - {ch} {st.title}")
    for detail in task.details:
        text = detail.strip()
        if _kanban_detail_needs_escape(text):
            text = f"detail: {text}"
        lines.append(f"  - {text}")
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
    name: str | Path,
    sections: dict[str, list[KanbanTask]],
    *,
    expected_snapshot: FileSnapshot | None = None,
) -> None:
    """Write kanban.md back from structured sections.

    The write is serialized via the kanban.md sidecar lock; the UI's
    3-way merge (kanban_merge) handles content conflicts, the lock
    prevents torn or interleaved writes from concurrent processes.
    When *expected_snapshot* is given, the file is re-checked against
    it after the lock is acquired; a mismatch raises
    ``file_state.FileConflictError`` so a concurrent write landing
    between the caller's parse and this save is never silently
    overwritten.
    """
    profile_name = name.name if isinstance(name, Path) else name
    path = kanban_path(name)
    text = render_kanban(profile_name, sections)
    with locked_profile_write(path.parent, "kanban.md"):
        if expected_snapshot is not None:
            assert_unchanged(path, expected_snapshot, label="kanban.md")
        atomic_write_text(path, text)
    git_backup.record_change(
        [path],
        action=f"update {profile_name}/kanban.md",
    )


def update_kanban(
    name_or_dir: str | Path,
    fn: Callable[[dict[str, list[KanbanTask]]], _T],
    *,
    expected_snapshot: FileSnapshot | None = None,
) -> _T:
    """Parse kanban.md, apply *fn*, and persist — under one lock.

    Same contract as ``inbox.update_inbox``: the whole parse → mutate →
    write cycle holds the kanban.md write lock, so read-modify-write
    flows (e.g. the Review kanban-move applier) cannot lose a concurrent
    writer's change. *fn* receives the parsed sections and mutates them
    in place; its return value is passed through. When *fn* leaves the
    board unchanged, no write or backup happens. *fn* must not call
    ``save_kanban``/``update_kanban``/``save_kanban_with_merge`` for the
    same profile (the lock is not reentrant for the same file).
    """
    profile_name = (
        name_or_dir.name if isinstance(name_or_dir, Path) else name_or_dir
    )
    path = kanban_path(name_or_dir)
    with locked_profile_write(path.parent, "kanban.md"):
        if expected_snapshot is not None:
            assert_unchanged(path, expected_snapshot, label="kanban.md")
        sections = parse_kanban(name_or_dir)
        before = {
            section: [_copy_kanban_task(task) for task in tasks]
            for section, tasks in sections.items()
        }
        result = fn(sections)
        changed = sections != before
        if changed:
            atomic_write_text(path, render_kanban(profile_name, sections))
    if changed:
        git_backup.record_change(
            [path],
            action=f"update {profile_name}/kanban.md",
        )
    return result


def _render_kanban_archive_append(
    name: str,
    tasks: list[KanbanTask],
) -> str:
    """Render an archive block for Done tasks."""
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
    return "\n".join(body_lines)


def _render_kanban_archive_text(
    name: str,
    path,
    tasks: list[KanbanTask],
) -> str:
    """Return full archive file text with *tasks* appended."""
    block = _render_kanban_archive_append(name, tasks)
    if path.exists():
        return path.read_text(encoding="utf-8") + block
    header = (
        f"# {name} · Kanban archive\n\n"
        "> Tasks moved here from kanban.md (Done column).\n\n"
        "---\n"
    )
    return header + block


def append_kanban_archive(
    name: str,
    tasks: list[KanbanTask],
) -> None:
    """Append Done tasks to kanban-archive.md under today's heading."""
    if not tasks:
        return
    path = profile_dir(name) / KANBAN_ARCHIVE_FILENAME
    atomic_write_text(path, _render_kanban_archive_text(name, path, tasks))
    git_backup.record_change(
        [path],
        action=f"append {name}/kanban-archive.md",
    )


def archive_kanban_done_tasks(
    name: str,
    sections: dict[str, list[KanbanTask]],
    done_indexes: list[int],
) -> dict[str, list[KanbanTask]]:
    """Archive selected Done tasks and remove them from kanban.md.

    The archive and kanban file contents are both computed before writing.
    The kanban file is only replaced after the archive write succeeds, so a
    failed archive append cannot silently delete Done tasks.
    """
    normalized = ensure_kanban_task_ids(sections, name)
    done_tasks = list(normalized.get(KANBAN_DONE, []))
    valid_indexes: list[int] = []
    for raw_index in done_indexes:
        try:
            index = int(raw_index)
        except (TypeError, ValueError):
            continue
        if 0 <= index < len(done_tasks) and index not in valid_indexes:
            valid_indexes.append(index)
    if not valid_indexes:
        return normalized

    index_set = set(valid_indexes)
    to_archive = [done_tasks[i] for i in sorted(index_set)]
    updated_sections = {
        section: list(normalized.get(section, []))
        for section in KANBAN_SECTIONS
    }
    updated_sections[KANBAN_DONE] = [
        task
        for i, task in enumerate(done_tasks)
        if i not in index_set
    ]

    profile_path = profile_dir(name)
    archive_path = profile_path / KANBAN_ARCHIVE_FILENAME
    kanban_path = profile_path / "kanban.md"
    archive_text = _render_kanban_archive_text(
        name,
        archive_path,
        to_archive,
    )
    kanban_text = render_kanban(name, updated_sections)

    atomic_write_text(archive_path, archive_text)
    atomic_write_text(kanban_path, kanban_text)
    git_backup.record_change(
        [archive_path, kanban_path],
        action=f"archive {name}/Done tasks",
    )
    return updated_sections
