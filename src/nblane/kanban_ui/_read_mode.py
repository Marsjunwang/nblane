"""Read-mode rendering for Kanban cards."""

from __future__ import annotations

import html
from dataclasses import replace

import streamlit as st

from nblane.core.kanban_io import (
    KANBAN_DOING,
    KANBAN_DONE,
    KANBAN_QUEUE,
    KANBAN_SECTIONS,
    KANBAN_SOMEDAY,
)
from nblane.core.models import KanbanSubtask, KanbanTask
from nblane.web_i18n import kanban_section_label
from nblane.web_linkify import linkify_plain_to_html, text_contains_linkified_url
from nblane.web_shared import kanban_section_emoji

from ._helpers import (
    _SECTION_COLOR,
    _apply_column_move,
    _auto_save,
    _kanban_widget_epoch,
    _mark_kanban_dirty,
    _read_title_label,
    _task_editing_key,
)

def _render_compact_body(
    task: KanbanTask,
    section: str,
    ui: dict[str, str],
) -> None:
    """Dense read-only body (no title; no subtasks — those use widgets)."""
    esc = html.escape
    wrap = (
        "line-height:1.28;font-size:0.92rem;margin:0;padding:0.02em 0;"
    )
    chunks: list[str] = [f"<div style=\"{wrap}\">"]

    if section == KANBAN_DOING:
        if task.context.strip():
            chunks.append(
                "<p style=\"margin:0.05em 0;opacity:0.92\">"
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
                "<p style=\"margin:0.05em 0;font-size:0.86rem;opacity:0.85\">"
                + " · ".join(bits)
                + "</p>"
            )
        if task.why.strip():
            chunks.append(
                "<p style=\"margin:0.05em 0;font-size:0.88rem\">"
                f"<em>{esc(ui['field_why'])}</em> "
                f"{esc(task.why.strip())}</p>"
            )
        if task.blocked_by.strip():
            chunks.append(
                "<p style=\"margin:0.05em 0;font-size:0.88rem\">"
                f"<em>{esc(ui['field_blocked'])}</em> "
                f"{esc(task.blocked_by.strip())}</p>"
            )
        if task.subtasks:
            nd = sum(1 for x in task.subtasks if x.done)
            na = len(task.subtasks)
            chunks.append(
                "<p style=\"margin:0.04em 0;font-size:0.85rem;opacity:0.9\">"
                + esc(
                    ui["kb_subtask_progress"].format(done=nd, total=na),
                )
                + "</p>"
            )
        joined = "\n".join(task.details).strip()
        if joined:
            prev = joined if len(joined) <= 220 else joined[:217] + "…"
            chunks.append(
                "<p style=\"margin:0.08em 0 0 0;font-size:0.84rem;"
                "opacity:0.88;white-space:pre-wrap\">"
                f"{esc(prev)}</p>"
            )

    elif section == KANBAN_QUEUE:
        if task.blocked_by.strip() or task.why.strip():
            one = (task.blocked_by or task.why or "").strip()
            cap = one if len(one) <= 160 else one[:157] + "…"
            chunks.append(
                "<p style=\"margin:0.05em 0;font-size:0.88rem;opacity:0.9\">"
                f"{esc(cap)}</p>"
            )
        if task.context.strip():
            chunks.append(
                "<p style=\"margin:0.05em 0;opacity:0.92\">"
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
                "<p style=\"margin:0.05em 0;font-size:0.86rem;opacity:0.85\">"
                + " · ".join(bits2)
                + "</p>"
            )
        joined_q = "\n".join(task.details).strip()
        if joined_q:
            pq = joined_q if len(joined_q) <= 220 else joined_q[:217] + "…"
            chunks.append(
                "<p style=\"margin:0.06em 0 0 0;font-size:0.84rem;"
                "opacity:0.88;white-space:pre-wrap\">"
                f"{esc(pq)}</p>"
            )

    elif section == KANBAN_DONE:
        if task.context.strip():
            chunks.append(
                "<p style=\"margin:0.05em 0;opacity:0.92\">"
                f"{esc(task.context.strip())}</p>"
            )
        if task.outcome.strip():
            chunks.append(
                "<p style=\"margin:0.05em 0;font-size:0.88rem\">"
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
                "<p style=\"margin:0.05em 0;font-size:0.86rem;opacity:0.85\">"
                + " · ".join(bits3)
                + "</p>"
            )
        if task.why.strip():
            chunks.append(
                "<p style=\"margin:0.05em 0;font-size:0.88rem\">"
                f"<em>{esc(ui['field_why'])}</em> "
                f"{esc(task.why.strip())}</p>"
            )
        if task.blocked_by.strip():
            chunks.append(
                "<p style=\"margin:0.05em 0;font-size:0.88rem\">"
                f"<em>{esc(ui['field_blocked'])}</em> "
                f"{esc(task.blocked_by.strip())}</p>"
            )
        joined_d = "\n".join(task.details).strip()
        if joined_d:
            pd = joined_d if len(joined_d) <= 220 else joined_d[:217] + "…"
            chunks.append(
                "<p style=\"margin:0.06em 0 0 0;font-size:0.84rem;"
                "opacity:0.88;white-space:pre-wrap\">"
                f"{esc(pd)}</p>"
            )

    else:
        joined_s = "\n".join(task.details).strip()
        if joined_s:
            ps = joined_s if len(joined_s) <= 280 else joined_s[:277] + "…"
            chunks.append(
                "<p style=\"margin:0.06em 0 0 0;font-size:0.84rem;"
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
    *,
    show_section_hint: bool = True,
) -> KanbanTask:
    """Read-mode subtask checkboxes; keep changes in memory until Save."""
    if show_section_hint:
        st.caption(ui["kb_read_subtasks_hint"])
    epoch = _kanban_widget_epoch(profile)
    new_subs: list[KanbanSubtask] = []
    for si, st_item in enumerate(task.subtasks):
        lab = st_item.title.strip() or "·"
        if len(lab) > 52:
            lab = lab[:49] + "…"
        done = st.checkbox(
            lab,
            value=st_item.done,
            key=f"rd_std_{profile}_{section}_{idx}_{si}_{epoch}",
        )
        new_subs.append(
            KanbanSubtask(title=st_item.title, done=done)
        )
    if new_subs != list(task.subtasks):
        task = replace(task, subtasks=new_subs)
        tasks[idx] = task
        sections[section] = tasks
        _mark_kanban_dirty(profile)
    return task


def _render_move_in_popover(
    section: str,
    idx: int,
    tasks: list[KanbanTask],
    sections: dict[str, list[KanbanTask]],
    profile: str,
    auto_dates: bool,
    ui: dict[str, str],
    key_prefix: str,
) -> None:
    """Select column and confirm move (used inside popovers)."""
    others = [s for s in KANBAN_SECTIONS if s != section]
    if not others:
        return
    pick = st.selectbox(
        ui["kb_move_to_label"],
        options=list(range(len(others))),
        format_func=lambda i: kanban_section_label(others[i]),
        key=f"{key_prefix}mvsb_{profile}_{section}_{idx}",
        label_visibility="visible",
    )
    if st.button(
        ui["kb_confirm_move"],
        key=f"{key_prefix}mvb_{profile}_{section}_{idx}",
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


def _read_mode_popover_body(
    section: str,
    idx: int,
    tasks: list[KanbanTask],
    sections: dict[str, list[KanbanTask]],
    profile: str,
    auto_dates: bool,
    ui: dict[str, str],
    to_delete: list[int],
) -> None:
    """Delete + move inside read-mode ⋯ popover."""
    st.caption(ui["kb_card_delete_hint"])
    if st.button(
        ui["kb_delete_card"],
        key=f"rd_del_{profile}_{section}_{idx}",
        type="secondary",
    ):
        to_delete.append(idx)
    st.divider()
    _render_move_in_popover(
        section,
        idx,
        tasks,
        sections,
        profile,
        auto_dates,
        ui,
        key_prefix="rd_",
    )


def _render_kanban_link_preview(
    ui: dict[str, str],
    section: str,
    task: KanbanTask,
) -> None:
    """Render clickable URL previews for task fields."""
    pairs: list[tuple[str, str]] = [
        (ui["task_field_title"], task.title),
    ]
    if section == KANBAN_DOING:
        pairs.extend(
            [
                (ui["field_context"], task.context),
                (ui["field_why"], task.why),
                (ui["field_blocked"], task.blocked_by),
            ]
        )
    elif section == KANBAN_QUEUE:
        pairs.extend(
            [
                (ui["field_why"], task.why),
                (ui["field_blocked"], task.blocked_by),
                (ui["field_context"], task.context),
            ]
        )
    elif section == KANBAN_DONE:
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
            "<p style='margin:0.08em 0;font-size:0.9em'>"
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



def render_read_card(
    section: str,
    idx: int,
    task: KanbanTask,
    tasks: list[KanbanTask],
    sections: dict[str, list[KanbanTask]],
    profile: str,
    auto_dates: bool,
    ui: dict[str, str],
    to_delete: list[int],
    *,
    show_section_hint: bool,
) -> KanbanTask:
    """Render a task card in compact read mode."""
    ek = _task_editing_key(profile, section, idx)
    t1, t2 = st.columns([7, 1])
    with t1:
        if st.button(
            _read_title_label(task.title),
            key=f"kb_title_{profile}_{section}_{idx}",
            type="tertiary",
            use_container_width=True,
            help=ui["kb_tap_title_to_edit"],
        ):
            st.session_state[ek] = True
            st.rerun()
    with t2:
        with st.popover(
            ui["kb_card_actions"],
            help=ui["kb_card_actions_help"],
        ):
            _read_mode_popover_body(
                section,
                idx,
                tasks,
                sections,
                profile,
                auto_dates,
                ui,
                to_delete,
            )
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
        show_section_hint=show_section_hint,
    )
    epoch = _kanban_widget_epoch(profile)
    ns_key = f"rd_newst_{profile}_{section}_{idx}_{epoch}"
    with st.expander(
        ui["kb_read_add_subtask_expander"],
        expanded=False,
    ):
        r1, r2 = st.columns([14, 1])
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
                type="tertiary",
                use_container_width=True,
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
                _mark_kanban_dirty(profile)
                st.rerun()
    tasks[idx] = task
    return task
