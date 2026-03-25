"""Streamlit layout for the Kanban board (columns, task cards, new-task form)."""

from __future__ import annotations

import html
from dataclasses import replace
from datetime import date

import streamlit as st

from nblane.core.io import (
    KANBAN_SECTIONS,
    KanbanSubtask,
    KanbanTask,
    save_kanban,
)
from nblane.web_i18n import kanban_section_label
from nblane.web_linkify import linkify_plain_to_html, text_contains_linkified_url
from nblane.web_shared import kanban_section_emoji

_BOARD_ORDER = ("Doing", "Queue", "Done", "Someday / Maybe")
_COL_WEIGHTS = [2.2, 1.0, 1.0, 1.0]
_WIP_HINT_THRESHOLD = 5

_SECTION_COLOR = {
    "Doing": "#fbbc04",
    "Queue": "#1a73e8",
    "Done": "#34a853",
    "Someday / Maybe": "#9aa0a6",
}


def _auto_save(
    profile: str,
    sections: dict[str, list[KanbanTask]],
) -> None:
    """Persist kanban to disk."""
    save_kanban(profile, sections)


def _apply_column_move(
    task: KanbanTask,
    from_sec: str,
    to_sec: str,
    auto_dates: bool,
) -> KanbanTask:
    """Adjust done flag and optional dates when moving between columns."""
    t = task
    if to_sec == "Done":
        t = replace(t, done=True)
        if auto_dates:
            co = (t.completed_on or "").strip() if t.completed_on else ""
            if not co:
                t = replace(
                    t,
                    completed_on=date.today().isoformat(),
                )
    elif from_sec == "Done":
        t = replace(t, done=False)
        if auto_dates:
            t = replace(t, completed_on=None)
    if to_sec == "Doing" and from_sec != "Doing":
        if auto_dates:
            so = (t.started_on or "").strip() if t.started_on else ""
            if not so:
                t = replace(
                    t,
                    started_on=date.today().isoformat(),
                )
    return t


def _kb_more_expanded(section: str, task: KanbanTask) -> bool:
    """Open legacy 'more fields' when folded slots hold data (Done / Queue)."""
    if section == "Queue":
        return bool(
            task.context.strip()
            or (task.started_on or "").strip()
            or (task.completed_on or "").strip()
        )
    if section == "Done":
        return bool(
            (task.started_on or "").strip()
            or (task.completed_on or "").strip()
            or task.why.strip()
            or task.blocked_by.strip()
        )
    return False


def _doing_body_expanded(task: KanbanTask) -> bool:
    """Expand Doing task body when it already has content."""
    return bool(
        task.context.strip()
        or (task.started_on or "").strip()
        or task.why.strip()
        or task.blocked_by.strip()
        or (task.completed_on or "").strip()
        or task.subtasks
        or task.details
    )


def _queue_compact_body_expanded(task: KanbanTask) -> bool:
    """Expand Queue compact body when secondary fields exist."""
    return bool(
        task.context.strip()
        or (task.started_on or "").strip()
        or (task.completed_on or "").strip()
        or task.subtasks
        or task.details
    )


def _someday_body_expanded(task: KanbanTask) -> bool:
    """Expand Someday card when subtasks or details exist."""
    return bool(task.subtasks or task.details)


def _task_editing_key(profile: str, section: str, idx: int) -> str:
    """Session state flag: task card shows form widgets vs compact read view."""
    return f"kanban_editing_{profile}_{section}_{idx}"


def _read_title_label(full: str, max_len: int = 72) -> str:
    """Truncate title for the tertiary title button."""
    t = (full or "").strip()
    if not t:
        return "·"
    if len(t) <= max_len:
        return t
    return t[: max_len - 1] + "…"


def _render_compact_body(
    task: KanbanTask,
    section: str,
    ui: dict[str, str],
) -> None:
    """Dense read-only body (no title; no subtasks — those use widgets)."""
    esc = html.escape
    wrap = (
        "line-height:1.32;font-size:0.92rem;margin:0;padding:0.05em 0;"
    )
    chunks: list[str] = [f"<div style=\"{wrap}\">"]

    if section == "Doing":
        if task.context.strip():
            chunks.append(
                "<p style=\"margin:0.1em 0;opacity:0.92\">"
                f"{esc(task.context.strip())}</p>"
            )
        so = (task.started_on or "").strip()
        co = (task.completed_on or "").strip()
        if so or co:
            bits: list[str] = []
            if so:
                bits.append(
                    f"{esc(ui['field_started'])} {esc(so)}"
                )
            if co:
                bits.append(
                    f"{esc(ui['field_completed'])} {esc(co)}"
                )
            chunks.append(
                "<p style=\"margin:0.1em 0;font-size:0.86rem;opacity:0.85\">"
                + " · ".join(bits)
                + "</p>"
            )
        if task.why.strip():
            chunks.append(
                "<p style=\"margin:0.1em 0;font-size:0.88rem\">"
                f"<em>{esc(ui['field_why'])}</em> "
                f"{esc(task.why.strip())}</p>"
            )
        if task.blocked_by.strip():
            chunks.append(
                "<p style=\"margin:0.1em 0;font-size:0.88rem\">"
                f"<em>{esc(ui['field_blocked'])}</em> "
                f"{esc(task.blocked_by.strip())}</p>"
            )
        if task.subtasks:
            nd = sum(1 for x in task.subtasks if x.done)
            na = len(task.subtasks)
            chunks.append(
                "<p style=\"margin:0.08em 0;font-size:0.85rem;opacity:0.9\">"
                + esc(
                    ui["kb_subtask_progress"].format(done=nd, total=na),
                )
                + "</p>"
            )
        joined = "\n".join(task.details).strip()
        if joined:
            prev = joined if len(joined) <= 220 else joined[:217] + "…"
            chunks.append(
                "<p style=\"margin:0.15em 0 0 0;font-size:0.84rem;"
                "opacity:0.88;white-space:pre-wrap\">"
                f"{esc(prev)}</p>"
            )

    elif section == "Queue":
        if task.blocked_by.strip() or task.why.strip():
            one = (task.blocked_by or task.why or "").strip()
            cap = one if len(one) <= 160 else one[:157] + "…"
            chunks.append(
                "<p style=\"margin:0.1em 0;font-size:0.88rem;opacity:0.9\">"
                f"{esc(cap)}</p>"
            )
        if task.context.strip():
            chunks.append(
                "<p style=\"margin:0.1em 0;opacity:0.92\">"
                f"{esc(task.context.strip())}</p>"
            )
        so = (task.started_on or "").strip()
        co = (task.completed_on or "").strip()
        if so or co:
            bits2: list[str] = []
            if so:
                bits2.append(
                    f"{esc(ui['field_started'])} {esc(so)}"
                )
            if co:
                bits2.append(
                    f"{esc(ui['field_completed'])} {esc(co)}"
                )
            chunks.append(
                "<p style=\"margin:0.1em 0;font-size:0.86rem;opacity:0.85\">"
                + " · ".join(bits2)
                + "</p>"
            )
        joined_q = "\n".join(task.details).strip()
        if joined_q:
            pq = joined_q if len(joined_q) <= 220 else joined_q[:217] + "…"
            chunks.append(
                "<p style=\"margin:0.12em 0 0 0;font-size:0.84rem;"
                "opacity:0.88;white-space:pre-wrap\">"
                f"{esc(pq)}</p>"
            )

    elif section == "Done":
        if task.context.strip():
            chunks.append(
                "<p style=\"margin:0.1em 0;opacity:0.92\">"
                f"{esc(task.context.strip())}</p>"
            )
        if task.outcome.strip():
            chunks.append(
                "<p style=\"margin:0.1em 0;font-size:0.88rem\">"
                f"<em>{esc(ui['field_outcome'])}</em> "
                f"{esc(task.outcome.strip())}</p>"
            )
        so = (task.started_on or "").strip()
        co = (task.completed_on or "").strip()
        if so or co:
            bits3: list[str] = []
            if so:
                bits3.append(
                    f"{esc(ui['field_started'])} {esc(so)}"
                )
            if co:
                bits3.append(
                    f"{esc(ui['field_completed'])} {esc(co)}"
                )
            chunks.append(
                "<p style=\"margin:0.1em 0;font-size:0.86rem;opacity:0.85\">"
                + " · ".join(bits3)
                + "</p>"
            )
        if task.why.strip():
            chunks.append(
                "<p style=\"margin:0.1em 0;font-size:0.88rem\">"
                f"<em>{esc(ui['field_why'])}</em> "
                f"{esc(task.why.strip())}</p>"
            )
        if task.blocked_by.strip():
            chunks.append(
                "<p style=\"margin:0.1em 0;font-size:0.88rem\">"
                f"<em>{esc(ui['field_blocked'])}</em> "
                f"{esc(task.blocked_by.strip())}</p>"
            )
        joined_d = "\n".join(task.details).strip()
        if joined_d:
            pd = joined_d if len(joined_d) <= 220 else joined_d[:217] + "…"
            chunks.append(
                "<p style=\"margin:0.12em 0 0 0;font-size:0.84rem;"
                "opacity:0.88;white-space:pre-wrap\">"
                f"{esc(pd)}</p>"
            )

    else:
        joined_s = "\n".join(task.details).strip()
        if joined_s:
            ps = joined_s if len(joined_s) <= 280 else joined_s[:277] + "…"
            chunks.append(
                "<p style=\"margin:0.12em 0 0 0;font-size:0.84rem;"
                "opacity:0.88;white-space:pre-wrap\">"
                f"{esc(ps)}</p>"
            )

    chunks.append("</div>")
    st.markdown("".join(chunks), unsafe_allow_html=True)


def _render_read_subtasks(
    profile: str,
    section: str,
    idx: int,
    task: KanbanTask,
    tasks: list[KanbanTask],
    sections: dict[str, list[KanbanTask]],
    ui: dict[str, str],
) -> KanbanTask:
    """Read-mode subtask checkboxes; persist when done flags change."""
    st.caption(ui["kb_read_subtasks_hint"])
    new_subs: list[KanbanSubtask] = []
    for si, st_item in enumerate(task.subtasks):
        lab = st_item.title.strip() or "·"
        if len(lab) > 52:
            lab = lab[:49] + "…"
        done = st.checkbox(
            lab,
            value=st_item.done,
            key=f"rd_std_{profile}_{section}_{idx}_{si}",
        )
        new_subs.append(
            KanbanSubtask(title=st_item.title, done=done)
        )
    if new_subs != list(task.subtasks):
        task = replace(task, subtasks=new_subs)
        tasks[idx] = task
        sections[section] = tasks
        _auto_save(profile, sections)
    return task


def _read_mode_card_actions(
    section: str,
    idx: int,
    tasks: list[KanbanTask],
    sections: dict[str, list[KanbanTask]],
    profile: str,
    auto_dates: bool,
    ui: dict[str, str],
    to_delete: list[int],
) -> None:
    """Popover: delete and move (compact read-mode chrome)."""
    with st.popover(ui["kb_card_actions"]):
        st.caption(ui["kb_card_delete_hint"])
        if st.button(
            ui["kb_delete_card"],
            key=f"rd_del_{profile}_{section}_{idx}",
            type="secondary",
        ):
            to_delete.append(idx)
        st.divider()
        others = [s for s in KANBAN_SECTIONS if s != section]
        if others:
            pick = st.selectbox(
                ui["kb_move_to_label"],
                options=list(range(len(others))),
                format_func=lambda i: kanban_section_label(others[i]),
                key=f"rd_mvsb_{profile}_{section}_{idx}",
                label_visibility="visible",
            )
            if st.button(
                ui["kb_confirm_move"],
                key=f"rd_mvb_{profile}_{section}_{idx}",
                type="primary",
            ):
                dest = others[int(pick)]
                moved = tasks.pop(idx)
                moved = _apply_column_move(
                    moved,
                    section,
                    dest,
                    auto_dates,
                )
                sections[section] = tasks
                sections.setdefault(dest, []).append(moved)
                _auto_save(profile, sections)
                st.rerun()


def _render_kanban_link_preview(
    ui: dict[str, str],
    section: str,
    task: KanbanTask,
) -> None:
    """Render clickable URL previews for task fields."""
    pairs: list[tuple[str, str]] = [
        (ui["task_field_title"], task.title),
    ]
    if section == "Doing":
        pairs.extend(
            [
                (ui["field_context"], task.context),
                (ui["field_why"], task.why),
                (ui["field_blocked"], task.blocked_by),
            ]
        )
    elif section == "Queue":
        pairs.extend(
            [
                (ui["field_why"], task.why),
                (ui["field_blocked"], task.blocked_by),
                (ui["field_context"], task.context),
            ]
        )
    elif section == "Done":
        pairs.extend(
            [
                (ui["field_context"], task.context),
                (ui["field_outcome"], task.outcome),
                (ui["field_why"], task.why),
                (ui["field_blocked"], task.blocked_by),
            ]
        )
    else:
        pairs.append((ui["details"], "\n".join(task.details)))

    blocks: list[str] = []
    for label, raw in pairs:
        if raw is None or not str(raw).strip():
            continue
        text = str(raw).strip()
        if not text_contains_linkified_url(text):
            continue
        inner = linkify_plain_to_html(text)
        lab = html.escape(label)
        blocks.append(
            "<p style='margin:0.15em 0;font-size:0.9em'>"
            "<strong>"
            + lab
            + "</strong><br>"
            + inner
            + "</p>"
        )
    if blocks:
        st.caption(ui["kb_links_preview"])
        st.markdown(
            "<div>"
            + "".join(blocks)
            + "</div>",
            unsafe_allow_html=True,
        )


def _column_header(section: str, ui: dict[str, str], n_tasks: int) -> None:
    """Section title and item count."""
    emoji = kanban_section_emoji(section)
    color = _SECTION_COLOR.get(section, "#9aa0a6")
    sec_disp = kanban_section_label(section)
    head_txt = f"{emoji} {sec_disp}" if emoji else sec_disp
    st.markdown(
        f"<h4 style='color:{color}'>{head_txt}</h4>",
        unsafe_allow_html=True,
    )
    st.caption(ui["items_count"].format(n=n_tasks))


def _render_new_task_form(
    section: str,
    sections: dict[str, list[KanbanTask]],
    profile: str,
    auto_dates: bool,
    ui: dict[str, str],
) -> None:
    """Inline form to add a task to *section*."""
    with st.container(border=True):
        new_title = st.text_input(
            ui["new_task"],
            key=f"new_title_{section}",
            placeholder=ui["new_task_ph"],
            label_visibility="collapsed",
        )
        ctx = why = blk = out = ""
        ds_new = dc_new = ""
        if new_title.strip():
            if section == "Doing":
                ctx = st.text_input(
                    ui["new_context"],
                    key=f"new_ctx_{section}",
                    placeholder=ui["new_context_ph"],
                    label_visibility="collapsed",
                )
                ds_new = st.text_input(
                    ui["field_started"],
                    value="",
                    key=f"new_so_{section}",
                    label_visibility="collapsed",
                )
                with st.expander(
                    ui["kb_more_fields"],
                    expanded=False,
                ):
                    st.caption(ui["kb_more_fields_help"])
                    why = st.text_input(
                        ui["new_why"],
                        key=f"new_why_{section}",
                        placeholder=ui["new_why_ph"],
                        label_visibility="collapsed",
                    )
                    blk = st.text_input(
                        ui["new_blocked"],
                        key=f"new_blk_{section}",
                        placeholder=ui["new_blocked_ph"],
                        label_visibility="collapsed",
                    )
                    dc_new = st.text_input(
                        ui["field_completed"],
                        value="",
                        key=f"new_co_{section}",
                        label_visibility="collapsed",
                    )
            elif section == "Queue":
                why = st.text_input(
                    ui["new_why"],
                    key=f"new_why_{section}",
                    placeholder=ui["new_why_ph"],
                    label_visibility="collapsed",
                )
                blk = st.text_input(
                    ui["new_blocked"],
                    key=f"new_blk_{section}",
                    placeholder=ui["new_blocked_ph"],
                    label_visibility="collapsed",
                )
                with st.expander(
                    ui["kb_more_fields"],
                    expanded=False,
                ):
                    st.caption(ui["kb_more_fields_help"])
                    ctx = st.text_input(
                        ui["new_context"],
                        key=f"new_ctx_{section}",
                        placeholder=ui["new_context_ph"],
                        label_visibility="collapsed",
                    )
                    ds_new = st.text_input(
                        ui["field_started"],
                        value="",
                        key=f"new_so_{section}",
                        label_visibility="collapsed",
                    )
                    dc_new = st.text_input(
                        ui["field_completed"],
                        value="",
                        key=f"new_co_{section}",
                        label_visibility="collapsed",
                    )
            elif section == "Done":
                out = st.text_input(
                    ui["new_outcome"],
                    key=f"new_out_{section}",
                    placeholder=ui["new_outcome_ph"],
                    label_visibility="collapsed",
                )
                with st.expander(
                    ui["kb_more_fields"],
                    expanded=False,
                ):
                    st.caption(ui["kb_more_fields_help"])
                    ctx = st.text_input(
                        ui["new_context"],
                        key=f"new_ctx_{section}",
                        placeholder=ui["new_context_ph"],
                        label_visibility="collapsed",
                    )
                    ds_new = st.text_input(
                        ui["field_started"],
                        value="",
                        key=f"new_so_{section}",
                        label_visibility="collapsed",
                    )
                    dc_new = st.text_input(
                        ui["field_completed"],
                        value="",
                        key=f"new_co_{section}",
                        label_visibility="collapsed",
                    )
                    why = st.text_input(
                        ui["new_why"],
                        key=f"new_why_{section}",
                        placeholder=ui["new_why_ph"],
                        label_visibility="collapsed",
                    )
                    blk = st.text_input(
                        ui["new_blocked"],
                        key=f"new_blk_{section}",
                        placeholder=ui["new_blocked_ph"],
                        label_visibility="collapsed",
                    )
        if st.button(
            ui["add"],
            key=f"add_{section}",
            type="primary",
        ):
            nt = KanbanTask(title=new_title.strip())
            if ctx.strip():
                nt = replace(nt, context=ctx.strip())
            if why.strip():
                nt = replace(nt, why=why.strip())
            if blk.strip():
                nt = replace(nt, blocked_by=blk.strip())
            if out.strip():
                nt = replace(nt, outcome=out.strip())
            if ds_new.strip():
                nt = replace(
                    nt,
                    started_on=ds_new.strip(),
                )
            if dc_new.strip():
                nt = replace(
                    nt,
                    completed_on=dc_new.strip(),
                )
            if section == "Done":
                nt = replace(nt, done=True)
                if auto_dates and not dc_new.strip():
                    nt = replace(
                        nt,
                        completed_on=date.today().isoformat(),
                    )
            if section == "Doing" and auto_dates:
                if not ds_new.strip():
                    nt = replace(
                        nt,
                        started_on=date.today().isoformat(),
                    )
            sections[section].append(nt)
            _auto_save(profile, sections)
            st.rerun()


def _move_buttons(
    section: str,
    idx: int,
    tasks: list[KanbanTask],
    sections: dict[str, list[KanbanTask]],
    profile: str,
    auto_dates: bool,
    ui: dict[str, str],
) -> None:
    """Render move-to-column buttons for the task at *idx*."""
    other_sections = [s for s in KANBAN_SECTIONS if s != section]
    st.caption(ui["kb_move_help"])
    ncols = len(other_sections)
    btn_cols = st.columns(ncols)
    for bi, dest in enumerate(other_sections):
        with btn_cols[bi]:
            lbl = kanban_section_label(dest)
            if st.button(
                lbl,
                key=f"mvbtn_{section}_{idx}_{dest}",
            ):
                moved = tasks.pop(idx)
                moved = _apply_column_move(
                    moved,
                    section,
                    dest,
                    auto_dates,
                )
                sections[section] = tasks
                sections.setdefault(dest, []).append(moved)
                _auto_save(profile, sections)
                st.rerun()


def _render_subtasks_and_details(
    section: str,
    idx: int,
    task: KanbanTask,
    tasks: list[KanbanTask],
    sections: dict[str, list[KanbanTask]],
    profile: str,
    ui: dict[str, str],
) -> KanbanTask:
    """Subtask editors, add-subtask, and details textarea; returns updated task."""
    st.markdown(f"*{ui['subtasks_label']}*")
    new_subs: list[KanbanSubtask] = []
    for si, st_item in enumerate(task.subtasks):
        sc1, sc2 = st.columns([1, 6])
        with sc1:
            sd = st.checkbox(
                "done",
                value=st_item.done,
                key=f"std_{section}_{idx}_{si}",
                label_visibility="collapsed",
            )
        with sc2:
            tt = st.text_input(
                "st",
                value=st_item.title,
                key=f"stt_{section}_{idx}_{si}",
                label_visibility="collapsed",
            )
        new_subs.append(
            KanbanSubtask(title=tt.strip(), done=sd)
        )
    task = replace(task, subtasks=new_subs)
    if st.button(
        ui["add_subtask"],
        key=f"addst_{section}_{idx}",
    ):
        task = replace(
            task,
            subtasks=task.subtasks
            + [KanbanSubtask(title="", done=False)],
        )
        tasks[idx] = task
        sections[section] = tasks
        _auto_save(profile, sections)
        st.rerun()

    existing_notes = "\n".join(task.details)
    new_notes = st.text_area(
        ui["details"],
        value=existing_notes,
        key=f"det_{section}_{idx}",
        label_visibility="collapsed",
        height=60,
        placeholder=ui["details_ph"],
    )
    if new_notes != existing_notes:
        task = replace(
            task,
            details=[
                d.strip()
                for d in new_notes.splitlines()
                if d.strip()
            ],
        )
    return task


def _render_task_cards(
    section: str,
    sections: dict[str, list[KanbanTask]],
    profile: str,
    auto_dates: bool,
    ui: dict[str, str],
) -> None:
    """Render all task cards for one section."""
    tasks = sections.get(section, [])
    to_delete: list[int] = []

    if section == "Doing" and len(tasks) > _WIP_HINT_THRESHOLD:
        st.caption(ui["kb_wip_hint"].format(n=len(tasks)))

    for idx, task in enumerate(tasks):
        ek = _task_editing_key(profile, section, idx)
        editing = bool(st.session_state.get(ek, False))

        with st.container(border=True):
            if not editing:
                task = tasks[idx]
                if st.button(
                    _read_title_label(task.title),
                    key=f"kb_title_{profile}_{section}_{idx}",
                    type="tertiary",
                    use_container_width=True,
                    help=ui["kb_tap_title_to_edit"],
                ):
                    st.session_state[ek] = True
                    st.rerun()
                _render_compact_body(task, section, ui)
                _render_kanban_link_preview(ui, section, task)
                if task.crystallized:
                    st.caption(ui["crystallized"])
                task = _render_read_subtasks(
                    profile,
                    section,
                    idx,
                    task,
                    tasks,
                    sections,
                    ui,
                )
                ns_key = f"rd_newst_{profile}_{section}_{idx}"
                r1, r2 = st.columns([6, 1])
                with r1:
                    st.text_input(
                        "sub",
                        key=ns_key,
                        placeholder=ui["kb_read_new_subtask_ph"],
                        label_visibility="collapsed",
                    )
                with r2:
                    if st.button(
                        "＋",
                        key=f"rd_addst_{profile}_{section}_{idx}",
                        type="secondary",
                        help=ui["add_subtask"],
                    ):
                        raw = st.session_state.get(ns_key, "")
                        title = str(raw).strip()
                        task = replace(
                            task,
                            subtasks=task.subtasks
                            + [KanbanSubtask(title=title, done=False)],
                        )
                        tasks[idx] = task
                        sections[section] = tasks
                        if ns_key in st.session_state:
                            del st.session_state[ns_key]
                        _auto_save(profile, sections)
                        st.rerun()
                tasks[idx] = task
                _read_mode_card_actions(
                    section,
                    idx,
                    tasks,
                    sections,
                    profile,
                    auto_dates,
                    ui,
                    to_delete,
                )
                continue

            hdr1, hdr2 = st.columns([8, 1])
            with hdr1:
                new_title_val = st.text_input(
                    ui["task_field_title"],
                    value=task.title,
                    key=f"title_{section}_{idx}",
                    label_visibility="collapsed",
                )
            with hdr2:
                if st.button("✕", key=f"del_{section}_{idx}"):
                    to_delete.append(idx)
            task = replace(task, title=new_title_val)
            st.caption(ui["kb_edit_exit_hint"])

            if section == "Someday / Maybe":
                _render_kanban_link_preview(ui, section, task)
                with st.expander(
                    ui["kb_task_details"],
                    expanded=_someday_body_expanded(task),
                ):
                    task = _render_subtasks_and_details(
                        section,
                        idx,
                        task,
                        tasks,
                        sections,
                        profile,
                        ui,
                    )
                if task.crystallized:
                    st.caption(ui["crystallized"])
                tasks[idx] = task
                if st.button(
                    ui["kb_done_editing"],
                    key=f"kb_eoff_{profile}_{section}_{idx}_sd",
                ):
                    st.session_state[ek] = False
                    st.rerun()
                _move_buttons(
                    section, idx, tasks, sections, profile, auto_dates, ui,
                )
                continue

            if section == "Doing":
                n_done = sum(1 for s in task.subtasks if s.done)
                n_all = len(task.subtasks)
                if n_all > 0:
                    st.progress(float(n_done) / float(n_all))
                    st.caption(
                        ui["kb_subtask_progress"].format(
                            done=n_done,
                            total=n_all,
                        )
                    )
                _render_kanban_link_preview(ui, section, task)
                with st.expander(
                    ui["kb_task_details"],
                    expanded=_doing_body_expanded(task),
                ):
                    c_ctx = st.text_input(
                        ui["field_context"],
                        value=task.context,
                        key=f"ctx_{section}_{idx}",
                        label_visibility="collapsed",
                    )
                    task = replace(task, context=c_ctx)
                    ds = st.text_input(
                        ui["field_started"],
                        value=task.started_on or "",
                        key=f"so_{section}_{idx}",
                        label_visibility="collapsed",
                    )
                    task = replace(
                        task,
                        started_on=ds.strip() or None,
                    )
                    st.caption(ui["kb_more_fields_help"])
                    c_why = st.text_input(
                        ui["field_why"],
                        value=task.why,
                        key=f"why_{section}_{idx}",
                        label_visibility="collapsed",
                    )
                    c_blk = st.text_input(
                        ui["field_blocked"],
                        value=task.blocked_by,
                        key=f"blk_{section}_{idx}",
                        label_visibility="collapsed",
                    )
                    dc = st.text_input(
                        ui["field_completed"],
                        value=task.completed_on or "",
                        key=f"co_{section}_{idx}",
                        label_visibility="collapsed",
                    )
                    task = replace(
                        task,
                        why=c_why,
                        blocked_by=c_blk,
                        completed_on=dc.strip() or None,
                    )
                    task = _render_subtasks_and_details(
                        section,
                        idx,
                        task,
                        tasks,
                        sections,
                        profile,
                        ui,
                    )
                if task.crystallized:
                    st.caption(ui["crystallized"])
                tasks[idx] = task
                if st.button(
                    ui["kb_done_editing"],
                    key=f"kb_eoff_{profile}_{section}_{idx}_do",
                ):
                    st.session_state[ek] = False
                    st.rerun()
                _move_buttons(
                    section, idx, tasks, sections, profile, auto_dates, ui,
                )
                continue

            if section == "Queue":
                _render_kanban_link_preview(ui, section, task)
                with st.expander(
                    ui["kb_task_details"],
                    expanded=_queue_compact_body_expanded(task),
                ):
                    c_why = st.text_input(
                        ui["field_why"],
                        value=task.why,
                        key=f"why_{section}_{idx}",
                        label_visibility="collapsed",
                    )
                    c_blk = st.text_input(
                        ui["field_blocked"],
                        value=task.blocked_by,
                        key=f"blk_{section}_{idx}",
                        label_visibility="collapsed",
                    )
                    task = replace(
                        task,
                        why=c_why,
                        blocked_by=c_blk,
                    )
                    st.caption(ui["kb_more_fields_help"])
                    c_ctx = st.text_input(
                        ui["field_context"],
                        value=task.context,
                        key=f"ctx_{section}_{idx}",
                        label_visibility="collapsed",
                    )
                    ds = st.text_input(
                        ui["field_started"],
                        value=task.started_on or "",
                        key=f"so_{section}_{idx}",
                        label_visibility="collapsed",
                    )
                    dc = st.text_input(
                        ui["field_completed"],
                        value=task.completed_on or "",
                        key=f"co_{section}_{idx}",
                        label_visibility="collapsed",
                    )
                    task = replace(
                        task,
                        context=c_ctx,
                        started_on=ds.strip() or None,
                        completed_on=dc.strip() or None,
                    )
                    task = _render_subtasks_and_details(
                        section,
                        idx,
                        task,
                        tasks,
                        sections,
                        profile,
                        ui,
                    )
                if task.crystallized:
                    st.caption(ui["crystallized"])
                tasks[idx] = task
                if st.button(
                    ui["kb_done_editing"],
                    key=f"kb_eoff_{profile}_{section}_{idx}_qu",
                ):
                    st.session_state[ek] = False
                    st.rerun()
                _move_buttons(
                    section, idx, tasks, sections, profile, auto_dates, ui,
                )
                continue

            if section == "Done":
                c_ctx = st.text_input(
                    ui["field_context"],
                    value=task.context,
                    key=f"ctx_{section}_{idx}",
                    label_visibility="collapsed",
                )
                c_out = st.text_input(
                    ui["field_outcome"],
                    value=task.outcome,
                    key=f"out_{section}_{idx}",
                    label_visibility="collapsed",
                )
                task = replace(
                    task,
                    context=c_ctx,
                    outcome=c_out,
                )
                _render_kanban_link_preview(ui, section, task)
                with st.expander(
                    ui["kb_more_fields"],
                    expanded=_kb_more_expanded(section, task),
                ):
                    st.caption(ui["kb_more_fields_help"])
                    ds = st.text_input(
                        ui["field_started"],
                        value=task.started_on or "",
                        key=f"so_{section}_{idx}",
                        label_visibility="collapsed",
                    )
                    dc = st.text_input(
                        ui["field_completed"],
                        value=task.completed_on or "",
                        key=f"co_{section}_{idx}",
                        label_visibility="collapsed",
                    )
                    c_why = st.text_input(
                        ui["field_why"],
                        value=task.why,
                        key=f"why_{section}_{idx}",
                        label_visibility="collapsed",
                    )
                    c_blk = st.text_input(
                        ui["field_blocked"],
                        value=task.blocked_by,
                        key=f"blk_{section}_{idx}",
                        label_visibility="collapsed",
                    )
                    task = replace(
                        task,
                        started_on=ds.strip() or None,
                        completed_on=dc.strip() or None,
                        why=c_why,
                        blocked_by=c_blk,
                    )
                if task.crystallized:
                    st.caption(ui["crystallized"])
                st.markdown(f"*{ui['subtasks_label']}*")
                new_subs_d: list[KanbanSubtask] = []
                for si, st_item in enumerate(task.subtasks):
                    sc1, sc2 = st.columns([1, 6])
                    with sc1:
                        sd = st.checkbox(
                            "done",
                            value=st_item.done,
                            key=f"std_{section}_{idx}_{si}",
                            label_visibility="collapsed",
                        )
                    with sc2:
                        tt = st.text_input(
                            "st",
                            value=st_item.title,
                            key=f"stt_{section}_{idx}_{si}",
                            label_visibility="collapsed",
                        )
                    new_subs_d.append(
                        KanbanSubtask(title=tt.strip(), done=sd)
                    )
                task = replace(task, subtasks=new_subs_d)
                if st.button(
                    ui["add_subtask"],
                    key=f"addst_{section}_{idx}",
                ):
                    task = replace(
                        task,
                        subtasks=task.subtasks
                        + [KanbanSubtask(title="", done=False)],
                    )
                    tasks[idx] = task
                    sections[section] = tasks
                    _auto_save(profile, sections)
                    st.rerun()

                existing_notes = "\n".join(task.details)
                new_notes = st.text_area(
                    ui["details"],
                    value=existing_notes,
                    key=f"det_{section}_{idx}",
                    label_visibility="collapsed",
                    height=60,
                    placeholder=ui["details_ph"],
                )
                if new_notes != existing_notes:
                    task = replace(
                        task,
                        details=[
                            d.strip()
                            for d in new_notes.splitlines()
                            if d.strip()
                        ],
                    )
                tasks[idx] = task
                if st.button(
                    ui["kb_done_editing"],
                    key=f"kb_eoff_{profile}_{section}_{idx}_dn",
                ):
                    st.session_state[ek] = False
                    st.rerun()
                _move_buttons(
                    section, idx, tasks, sections, profile, auto_dates, ui,
                )

    for jdx in reversed(to_delete):
        tasks.pop(jdx)
        _auto_save(profile, sections)
        st.rerun()

    sections[section] = tasks



def _render_section_column(
    section: str,
    sections: dict[str, list[KanbanTask]],
    profile: str,
    auto_dates: bool,
    ui: dict[str, str],
    *,
    wrap_done_in_expander: bool,
) -> None:
    """One board column: header, optional Done wrapper, new task, cards."""
    tasks = sections.get(section, [])
    _column_header(section, ui, len(tasks))

    if section == "Done" and wrap_done_in_expander:
        st.caption(ui["kb_done_column_hint"])
        with st.expander(
            ui["kb_done_column_expander"].format(n=len(tasks)),
            expanded=False,
        ):
            _render_new_task_form(
                section, sections, profile, auto_dates, ui,
            )
            _render_task_cards(
                section, sections, profile, auto_dates, ui,
            )
        return

    _render_new_task_form(section, sections, profile, auto_dates, ui)
    _render_task_cards(section, sections, profile, auto_dates, ui)


def render_kanban_board(
    sections: dict[str, list[KanbanTask]],
    profile: str,
    auto_dates: bool,
    ui: dict[str, str],
    focus_mode: bool,
) -> None:
    """Render the full board (weighted columns or focus layout)."""
    if focus_mode:
        doing_sec = "Doing"
        _column_header(doing_sec, ui, len(sections.get(doing_sec, [])))
        _render_new_task_form(
            doing_sec, sections, profile, auto_dates, ui,
        )
        _render_task_cards(
            doing_sec, sections, profile, auto_dates, ui,
        )

        tab_labels = [
            kanban_section_label("Queue"),
            kanban_section_label("Done"),
            kanban_section_label("Someday / Maybe"),
        ]
        tq, td, ts = st.tabs(tab_labels)
        with tq:
            _render_section_column(
                "Queue",
                sections,
                profile,
                auto_dates,
                ui,
                wrap_done_in_expander=False,
            )
        with td:
            _render_section_column(
                "Done",
                sections,
                profile,
                auto_dates,
                ui,
                wrap_done_in_expander=False,
            )
        with ts:
            _render_section_column(
                "Someday / Maybe",
                sections,
                profile,
                auto_dates,
                ui,
                wrap_done_in_expander=False,
            )
        return

    cols = st.columns(_COL_WEIGHTS)
    for col_widget, section in zip(cols, _BOARD_ORDER):
        with col_widget:
            _render_section_column(
                section,
                sections,
                profile,
                auto_dates,
                ui,
                wrap_done_in_expander=(section == "Done"),
            )
