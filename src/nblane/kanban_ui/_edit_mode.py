"""Edit-mode rendering for Kanban cards and new-task forms."""

from __future__ import annotations

from dataclasses import replace
from datetime import date

import streamlit as st

from nblane.core.kanban_io import (
    KANBAN_DOING,
    KANBAN_DONE,
    KANBAN_QUEUE,
    KANBAN_SECTIONS,
    KANBAN_SOMEDAY,
)
from nblane.core.models import KanbanSubtask, KanbanTask

from ._helpers import (
    _apply_column_move,
    _auto_save,
    _doing_body_expanded,
    _kb_more_expanded,
    _queue_compact_body_expanded,
    _someday_body_expanded,
    _task_editing_key,
)
from ._read_mode import _render_kanban_link_preview, _render_move_in_popover

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
            if section == KANBAN_DOING:
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
            elif section == KANBAN_QUEUE:
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
            elif section == KANBAN_DONE:
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
            if section == KANBAN_DONE:
                nt = replace(nt, done=True)
                if auto_dates and not dc_new.strip():
                    nt = replace(
                        nt,
                        completed_on=date.today().isoformat(),
                    )
            if section == KANBAN_DOING and auto_dates:
                if not ds_new.strip():
                    nt = replace(
                        nt,
                        started_on=date.today().isoformat(),
                    )
            sections[section].append(nt)
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
        type="tertiary",
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





def _edit_card_header(
    section: str,
    idx: int,
    task: KanbanTask,
    tasks: list[KanbanTask],
    sections: dict[str, list[KanbanTask]],
    profile: str,
    auto_dates: bool,
    ui: dict[str, str],
    to_delete: list[int],
) -> KanbanTask:
    """Render edit header controls and return the title-updated task."""
    hdr1, hdr2, hdr3 = st.columns([6, 1, 1])
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
    with hdr3:
        with st.popover(
            ui["kb_edit_move"],
            help=ui["kb_edit_move_help"],
        ):
            _render_move_in_popover(
                section,
                idx,
                tasks,
                sections,
                profile,
                auto_dates,
                ui,
                key_prefix="ed_",
            )
    task = replace(task, title=new_title_val)
    st.caption(ui["kb_edit_exit_hint"])
    return task


def _edit_card_footer(
    profile: str,
    section: str,
    idx: int,
    suffix: str,
    task: KanbanTask,
    tasks: list[KanbanTask],
    ui: dict[str, str],
) -> None:
    """Persist edited task and render the shared done-editing button."""
    ek = _task_editing_key(profile, section, idx)
    if task.crystallized:
        st.caption(ui["crystallized"])
    tasks[idx] = task
    done_clicked = False
    if suffix == "sd":
        done_clicked = st.button(
            ui["kb_done_editing"],
            key=f"kb_eoff_{profile}_{section}_{idx}_sd",
        )
    elif suffix == "do":
        done_clicked = st.button(
            ui["kb_done_editing"],
            key=f"kb_eoff_{profile}_{section}_{idx}_do",
        )
    elif suffix == "qu":
        done_clicked = st.button(
            ui["kb_done_editing"],
            key=f"kb_eoff_{profile}_{section}_{idx}_qu",
        )
    elif suffix == "dn":
        done_clicked = st.button(
            ui["kb_done_editing"],
            key=f"kb_eoff_{profile}_{section}_{idx}_dn",
        )
    if done_clicked:
        st.session_state[ek] = False
        st.rerun()


def _render_someday_body(
    section: str,
    idx: int,
    task: KanbanTask,
    tasks: list[KanbanTask],
    sections: dict[str, list[KanbanTask]],
    profile: str,
    ui: dict[str, str],
) -> KanbanTask:
    """Render Someday edit body."""
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
    return task


def _render_doing_body(
    section: str,
    idx: int,
    task: KanbanTask,
    tasks: list[KanbanTask],
    sections: dict[str, list[KanbanTask]],
    profile: str,
    ui: dict[str, str],
) -> KanbanTask:
    """Render Doing edit body."""
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
    return task


def _render_queue_body(
    section: str,
    idx: int,
    task: KanbanTask,
    tasks: list[KanbanTask],
    sections: dict[str, list[KanbanTask]],
    profile: str,
    ui: dict[str, str],
) -> KanbanTask:
    """Render Queue edit body."""
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
    return task


def _render_done_body(
    section: str,
    idx: int,
    task: KanbanTask,
    tasks: list[KanbanTask],
    sections: dict[str, list[KanbanTask]],
    profile: str,
    ui: dict[str, str],
) -> KanbanTask:
    """Render Done edit body."""
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
        type="tertiary",
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


def render_edit_card(
    section: str,
    idx: int,
    task: KanbanTask,
    tasks: list[KanbanTask],
    sections: dict[str, list[KanbanTask]],
    profile: str,
    auto_dates: bool,
    ui: dict[str, str],
    to_delete: list[int],
) -> None:
    """Render a task card in edit mode."""
    task = _edit_card_header(
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
    if section == KANBAN_SOMEDAY:
        task = _render_someday_body(
            section, idx, task, tasks, sections, profile, ui,
        )
        _edit_card_footer(profile, section, idx, "sd", task, tasks, ui)
        return
    if section == KANBAN_DOING:
        task = _render_doing_body(
            section, idx, task, tasks, sections, profile, ui,
        )
        _edit_card_footer(profile, section, idx, "do", task, tasks, ui)
        return
    if section == KANBAN_QUEUE:
        task = _render_queue_body(
            section, idx, task, tasks, sections, profile, ui,
        )
        _edit_card_footer(profile, section, idx, "qu", task, tasks, ui)
        return
    if section == KANBAN_DONE:
        task = _render_done_body(
            section, idx, task, tasks, sections, profile, ui,
        )
        _edit_card_footer(profile, section, idx, "dn", task, tasks, ui)
