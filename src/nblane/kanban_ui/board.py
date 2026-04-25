"""Streamlit layout for the Kanban board columns."""

from __future__ import annotations

import streamlit as st

from nblane.core.kanban_io import (
    KANBAN_DOING,
    KANBAN_DONE,
    KANBAN_QUEUE,
    KANBAN_SOMEDAY,
)
from nblane.core.models import KanbanTask
from nblane.web_i18n import kanban_section_label

from ._edit_mode import _render_new_task_form, render_edit_card
from ._helpers import (
    _BOARD_ORDER,
    _COL_WEIGHTS,
    _WIP_HINT_THRESHOLD,
    _auto_save,
    _task_editing_key,
)
from ._read_mode import _column_header, render_read_card

def _render_task_cards(
    section: str,
    sections: dict[str, list[KanbanTask]],
    profile: str,
    auto_dates: bool,
    ui: dict[str, str],
    *,
    doing_focus_two_col: bool = False,
) -> None:
    """Render all task cards for one section."""
    tasks = sections.get(section, [])
    to_delete: list[int] = []

    if section == KANBAN_DOING and len(tasks) > _WIP_HINT_THRESHOLD:
        st.caption(ui["kb_wip_hint"].format(n=len(tasks)))

    n_tasks = len(tasks)
    if doing_focus_two_col and section == KANBAN_DOING and n_tasks > 0:
        mid = (n_tasks + 1) // 2
        index_batches = [list(range(mid)), list(range(mid, n_tasks))]
        c_left, c_right = st.columns(2)
        with c_left:
            _render_task_index_batch(
                index_batches[0],
                section,
                tasks,
                sections,
                profile,
                auto_dates,
                ui,
                to_delete,
            )
        with c_right:
            _render_task_index_batch(
                index_batches[1],
                section,
                tasks,
                sections,
                profile,
                auto_dates,
                ui,
                to_delete,
            )
    else:
        _render_task_index_batch(
            list(range(n_tasks)),
            section,
            tasks,
            sections,
            profile,
            auto_dates,
            ui,
            to_delete,
        )

    for jdx in reversed(to_delete):
        tasks.pop(jdx)
        _auto_save(profile, sections)
        st.rerun()

    sections[section] = tasks





def _render_task_index_batch(
    indices: list[int],
    section: str,
    tasks: list[KanbanTask],
    sections: dict[str, list[KanbanTask]],
    profile: str,
    auto_dates: bool,
    ui: dict[str, str],
    to_delete: list[int],
) -> None:
    """Render cards for global indices *indices* within *tasks*."""
    first_idx = indices[0] if indices else None
    for idx in indices:
        show_read_subtask_hint = idx == first_idx
        ek = _task_editing_key(profile, section, idx)
        editing = bool(st.session_state.get(ek, False))
        task = tasks[idx]

        with st.container(border=True):
            if not editing:
                render_read_card(
                    section,
                    idx,
                    task,
                    tasks,
                    sections,
                    profile,
                    auto_dates,
                    ui,
                    to_delete,
                    show_section_hint=show_read_subtask_hint,
                )
                continue

            render_edit_card(
                section,
                idx,
                task,
                tasks,
                sections,
                profile,
                auto_dates,
                ui,
                to_delete,
            )

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

    if section == KANBAN_DONE and wrap_done_in_expander:
        st.caption(ui["kb_done_column_hint"])
        with st.expander(
            ui["kb_done_column_expander"].format(n=len(tasks)),
            expanded=False,
        ):
            _render_task_cards(
                section, sections, profile, auto_dates, ui,
            )
            _render_new_task_form(
                section, sections, profile, auto_dates, ui,
            )
        return

    _render_task_cards(section, sections, profile, auto_dates, ui)
    _render_new_task_form(section, sections, profile, auto_dates, ui)


def render_kanban_board(
    sections: dict[str, list[KanbanTask]],
    profile: str,
    auto_dates: bool,
    ui: dict[str, str],
    focus_mode: bool,
) -> None:
    """Render the full board (weighted columns or focus layout)."""
    if focus_mode:
        doing_sec = KANBAN_DOING
        _column_header(doing_sec, ui, len(sections.get(doing_sec, [])))
        _render_task_cards(
            doing_sec,
            sections,
            profile,
            auto_dates,
            ui,
            doing_focus_two_col=True,
        )
        _render_new_task_form(
            doing_sec, sections, profile, auto_dates, ui,
        )

        tab_labels = [
            kanban_section_label(KANBAN_QUEUE),
            kanban_section_label(KANBAN_DONE),
            kanban_section_label(KANBAN_SOMEDAY),
        ]
        tq, td, ts = st.tabs(tab_labels)
        with tq:
            _render_section_column(
                KANBAN_QUEUE,
                sections,
                profile,
                auto_dates,
                ui,
                wrap_done_in_expander=False,
            )
        with td:
            _render_section_column(
                KANBAN_DONE,
                sections,
                profile,
                auto_dates,
                ui,
                wrap_done_in_expander=False,
            )
        with ts:
            _render_section_column(
                KANBAN_SOMEDAY,
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
                wrap_done_in_expander=(section == KANBAN_DONE),
            )
