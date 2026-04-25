"""Kanban markdown parsing and rendering."""

from __future__ import annotations

import re
from datetime import date

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
KANBAN_ARCHIVE_FILENAME = "kanban-archive.md"


def _normalize_kanban_meta_key(raw_key: str) -> str | None:
    """Map a detail key label to a KanbanTask field name."""
    k = raw_key.strip().lower().replace(" ", "_")
    if k in ("context", "why", "outcome", "started_on", "completed_on"):
        return k
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
    if field == "context" and isinstance(val, str):
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


def _kanban_skip_placeholder_title(title: str) -> bool:
    """True if this task line is the empty-column placeholder."""
    return title.strip() == "(empty)"


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

    return sections


def _render_kanban_task_lines(
    section: str,
    task: KanbanTask,
) -> list[str]:
    """Emit markdown lines for one task under *section*."""
    lines: list[str] = []
    if section == KANBAN_SOMEDAY:
        lines.append(f"- {task.title}")
        return lines
    check = "[x]" if task.done else "[ ]"
    lines.append(f"- {check} {task.title}")
    meta_pairs: list[tuple[str, str]] = []
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
        tasks = sections.get(section, [])
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
    for task in tasks:
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
