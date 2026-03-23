"""Kanban -- visual task board editor for kanban.md.

Primary persist actions use the toolbar **Reload** / **Save** pattern.
Skill Tree uses a title-row **Save** instead; see docs/zh/web-ui-product.md.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date

import streamlit as st
import yaml

from nblane.core import llm as llm_client
from nblane.core.io import (
    KANBAN_SECTIONS,
    KanbanSubtask,
    KanbanTask,
    append_kanban_archive,
    load_evidence_pool_raw,
    load_skill_tree_raw,
    parse_kanban,
    save_kanban,
)
from nblane.core.profile_ingest import (
    filter_ingest_patch,
    ingest_preview_delta,
    merge_ingest_patch,
    parse_ingest_patch,
    run_ingest_patch,
    schema_node_labels,
)
from nblane.core.profile_ingest_llm import ingest_kanban_done_json
from nblane.web_i18n import (
    kanban_section_label,
    kanban_ui,
)
from nblane.web_shared import (
    drop_streamlit_widget_keys,
    kanban_section_emoji,
    remember_allow_and_drop_yaml_preview_keys,
    render_llm_unavailable,
    select_profile,
    ui_emoji_enabled,
)

_SECTION_COLOR = {
    "Doing": "#fbbc04",
    "Queue": "#1a73e8",
    "Done": "#34a853",
    "Someday / Maybe": "#9aa0a6",
}


def _state_key(profile: str) -> str:
    """Session state key for kanban data."""
    return f"kanban_{profile}"


def _load_into_state(profile: str) -> None:
    """Load kanban from file into session state."""
    st.session_state[_state_key(profile)] = parse_kanban(profile)


def _get_sections(profile: str) -> dict[str, list[KanbanTask]]:
    """Get kanban sections from session state."""
    key = _state_key(profile)
    if key not in st.session_state:
        _load_into_state(profile)
    return st.session_state[key]


def _auto_save(
    profile: str,
    sections: dict[str, list[KanbanTask]],
) -> None:
    """Persist changes to kanban.md."""
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


def _mark_done_crystallized(
    sections: dict[str, list[KanbanTask]],
    titles: set[str],
) -> None:
    """Set crystallized on Done tasks whose titles are in *titles*."""
    done_list = sections.get("Done") or []
    for i, t in enumerate(done_list):
        if t.title in titles:
            done_list[i] = replace(t, crystallized=True)


def _kb_more_expanded(section: str, task: KanbanTask) -> bool:
    """Open 'more fields' when folded slots already hold data."""
    if section == "Doing":
        return bool(
            task.why.strip()
            or task.blocked_by.strip()
            or (task.completed_on or "").strip()
        )
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


# -- Page --------------------------------------------------------

ui = kanban_ui()
st.set_page_config(
    page_title=ui["page_title"],
    layout="wide",
)

selected = select_profile()

st.title(ui["title"])
st.caption(ui["page_context_line"])

auto_dates = st.checkbox(
    ui["kb_auto_dates"],
    value=True,
    key=f"kanban_auto_dates_{selected}",
    help=ui["kb_auto_dates_help"],
)

# -- Toolbar -----------------------------------------------------

tb1, tb2, tb3 = st.columns([1, 1, 3])
with tb1:
    if st.button(ui["reload"]):
        _load_into_state(selected)
        st.rerun()
with tb2:
    if st.button(ui["save"], type="primary"):
        sections = _get_sections(selected)
        save_kanban(selected, sections)
        st.success(ui["saved"])

sections = _get_sections(selected)

total_tasks = sum(len(tasks) for tasks in sections.values())
doing_count = len(sections.get("Doing", []))
done_count = len(sections.get("Done", []))

mc1, mc2, mc3 = st.columns(3)
use_emoji = ui_emoji_enabled()
mc1.metric(ui["metric_total"], total_tasks)
mc2.metric(
    ui["metric_doing"] if use_emoji else kanban_section_label("Doing"),
    doing_count,
)
mc3.metric(
    ui["metric_done"] if use_emoji else kanban_section_label("Done"),
    done_count,
)

st.divider()

# -- Done bulk ---------------------------------------------------

with st.expander(ui["done_bulk_title"], expanded=False):
    done_tasks_bulk = sections.get("Done") or []
    if not done_tasks_bulk:
        st.caption(ui["ingest_no_done"])
    else:
        pick_bulk = st.multiselect(
            ui["done_bulk_pick"],
            options=list(range(len(done_tasks_bulk))),
            format_func=lambda i: done_tasks_bulk[i].title,
            key=f"bulk_pick_{selected}",
        )
        b1, b2 = st.columns(2)
        with b1:
            if st.button(ui["archive_done"], key=f"arch_{selected}"):
                if pick_bulk:
                    to_arc = [done_tasks_bulk[i] for i in pick_bulk]
                    append_kanban_archive(selected, to_arc)
                    for j in sorted(pick_bulk, reverse=True):
                        done_tasks_bulk.pop(j)
                    sections["Done"] = done_tasks_bulk
                    _auto_save(selected, sections)
                    st.rerun()
        with b2:
            if st.button(ui["delete_done"], key=f"delbulk_{selected}"):
                if pick_bulk:
                    for j in sorted(pick_bulk, reverse=True):
                        done_tasks_bulk.pop(j)
                    sections["Done"] = done_tasks_bulk
                    _auto_save(selected, sections)
                    st.rerun()

# -- Board columns -----------------------------------------------

board_cols = st.columns(len(KANBAN_SECTIONS))

for col_widget, section in zip(board_cols, KANBAN_SECTIONS):
    emoji = kanban_section_emoji(section)
    color = _SECTION_COLOR.get(section, "#9aa0a6")
    tasks = sections.get(section, [])
    sec_disp = kanban_section_label(section)
    head_txt = f"{emoji} {sec_disp}" if emoji else sec_disp

    with col_widget:
        st.markdown(
            f"<h4 style='color:{color}'>{head_txt}</h4>",
            unsafe_allow_html=True,
        )
        st.caption(ui["items_count"].format(n=len(tasks)))

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
                    _auto_save(selected, sections)
                    st.rerun()

        to_delete: list[int] = []
        for idx, task in enumerate(tasks):
            with st.container(border=True):
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

                if section == "Someday / Maybe":
                    pass
                elif section == "Doing":
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
                    with st.expander(
                        ui["kb_more_fields"],
                        expanded=_kb_more_expanded(section, task),
                    ):
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
                    if task.crystallized:
                        st.caption(ui["crystallized"])
                elif section == "Queue":
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
                    with st.expander(
                        ui["kb_more_fields"],
                        expanded=_kb_more_expanded(section, task),
                    ):
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
                    if task.crystallized:
                        st.caption(ui["crystallized"])
                elif section == "Done":
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
                    _auto_save(selected, sections)
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
                            _auto_save(selected, sections)
                            st.rerun()

        for jdx in reversed(to_delete):
            tasks.pop(jdx)
            _auto_save(selected, sections)
            st.rerun()

        sections[section] = tasks

# -- Done → evidence (AI ingest) ---------------------------------

st.divider()
with st.expander(ui["ingest_expander"], expanded=False):
    done_tasks = sections.get("Done") or []
    if not done_tasks:
        st.caption(ui["ingest_no_done"])
    else:
        pick = st.multiselect(
            ui["ingest_pick_done"],
            options=list(range(len(done_tasks))),
            format_func=lambda i: done_tasks[i].title,
            key=f"ingest_done_pick_{selected}",
        )
        allow_st = st.checkbox(
            ui["ingest_allow_status"],
            value=False,
            key=f"ingest_allow_{selected}",
        )
        st.caption(ui["ingest_allow_status_help"])
        gen = st.button(
            ui["ingest_generate"],
            key=f"ingest_gen_{selected}",
        )
        if gen and pick:
            chosen = [done_tasks[i] for i in pick]
            if not llm_client.is_configured():
                render_llm_unavailable(ui)
            else:
                with st.spinner(ui["ingest_spinner"]):
                    patch, err = ingest_kanban_done_json(
                        selected,
                        chosen,
                    )
                if err is not None:
                    st.error(ui["ingest_err"].format(msg=err))
                elif patch is not None:
                    drop_streamlit_widget_keys(
                        [
                            f"pv_pool_{selected}",
                            f"pv_tree_{selected}",
                        ]
                    )
                    st.session_state[
                        f"kanban_ingest_source_done_{selected}"
                    ] = [t.title for t in chosen]
                    st.session_state[
                        f"kanban_ingest_patch_{selected}"
                    ] = patch
                    st.rerun()

        patch_key = f"kanban_ingest_patch_{selected}"
        if patch_key in st.session_state:
            remember_allow_and_drop_yaml_preview_keys(
                allow_st,
                prev_state_key=f"_kanban_allow_prev_{selected}",
                pool_key=f"pv_pool_{selected}",
                tree_key=f"pv_tree_{selected}",
            )
            raw_patch = st.session_state[patch_key]
            parsed = parse_ingest_patch(raw_patch)
            ev_rows = parsed.evidence_entries
            no_rows = parsed.node_updates

            st.markdown(f"**{ui['ingest_select_rows']}**")
            include_ev: list[bool] = []
            for ei, er in enumerate(ev_rows):
                title = str(er.get("title", "") or "")[:80]
                ex = str(er.get("source_excerpt", "") or "")[:120]
                c1, c2 = st.columns([1, 5])
                with c1:
                    include_ev.append(
                        st.checkbox(
                            ui["ingest_adopt_evidence"],
                            value=True,
                            key=f"k_ev_{selected}_{ei}",
                        )
                    )
                with c2:
                    st.caption(f"{title}")
                    if ex:
                        st.caption(
                            f"{ui['ingest_excerpt']}: {ex}"
                        )
            include_no: list[bool] = []
            for nj, nr in enumerate(no_rows):
                nid = str(nr.get("id", "") or "")
                rat = str(nr.get("rationale", "") or "")[:200]
                c1, c2 = st.columns([1, 5])
                with c1:
                    include_no.append(
                        st.checkbox(
                            ui["ingest_adopt_node"],
                            value=True,
                            key=f"k_no_{selected}_{nj}",
                        )
                    )
                with c2:
                    st.caption(f"`{nid}`")
                    if rat:
                        st.caption(
                            f"{ui['ingest_rationale']}: {rat}"
                        )

            filtered, fw = filter_ingest_patch(
                raw_patch,
                include_evidence=include_ev if ev_rows else None,
                include_nodes=include_no if no_rows else None,
            )
            if fw:
                st.caption(ui["ingest_filter_warn"])
                for w in fw:
                    st.caption(f"- {w}")

            mark_cryst = st.checkbox(
                ui["ingest_mark_crystallized"],
                value=False,
                key=f"ingest_cryst_{selected}",
            )

            pool_raw = load_evidence_pool_raw(selected)
            tree_raw = load_skill_tree_raw(selected)
            src_done = st.session_state.get(
                f"kanban_ingest_source_done_{selected}"
            )
            if isinstance(src_done, list) and src_done:
                st.caption(
                    ui["ingest_preview_source_done"].format(
                        sources="; ".join(str(x) for x in src_done),
                    )
                )
            st.caption(
                ui["merge_preview_llm_status_line"].format(
                    mode=(
                        ui["merge_llm_status_applied"]
                        if allow_st
                        else ui["merge_llm_status_ignored"]
                    ),
                )
            )
            merge = merge_ingest_patch(
                selected,
                pool_raw,
                tree_raw,
                filtered,
                allow_status_change=allow_st,
                bump_locked_with_evidence=True,
            )
            if merge.warnings:
                st.caption(ui["ingest_warn"])
                for w in merge.warnings:
                    st.caption(f"- {w}")
            if merge.ok and (
                merge.merged_pool is not None
                or merge.merged_tree is not None
            ):
                lab = schema_node_labels(tree_raw)
                new_ev, tree_delta = ingest_preview_delta(
                    pool_raw,
                    tree_raw,
                    merge.merged_pool,
                    merge.merged_tree,
                    lab,
                )
                with st.expander(
                    ui["merge_preview_delta_title"],
                    expanded=True,
                ):
                    if new_ev:
                        st.markdown(
                            f"**{ui['merge_preview_delta_new_evidence']}**"
                        )
                        for line in new_ev:
                            st.markdown(f"- {line}")
                    if tree_delta:
                        st.markdown(
                            f"**{ui['merge_preview_delta_tree']}**"
                        )
                        for line in tree_delta:
                            st.markdown(f"- {line}")
                    if not new_ev and not tree_delta:
                        st.caption(ui["merge_preview_delta_none"])
            if merge.ok and (
                merge.merged_pool is not None
                or merge.merged_tree is not None
            ):
                st.caption(ui["merge_preview_yaml_readonly_caption"])
            if merge.ok and merge.merged_pool:
                st.markdown(f"**{ui['ingest_preview_pool']}**")
                st.code(
                    yaml.dump(
                        merge.merged_pool,
                        allow_unicode=True,
                        default_flow_style=False,
                        sort_keys=False,
                    ),
                    language="yaml",
                )
            if merge.ok and merge.merged_tree:
                st.markdown(f"**{ui['ingest_preview_tree']}**")
                st.code(
                    yaml.dump(
                        merge.merged_tree,
                        allow_unicode=True,
                        default_flow_style=False,
                        sort_keys=False,
                    ),
                    language="yaml",
                )
            if not merge.ok:
                for e in merge.errors:
                    st.error(e)
            else:
                ac1, ac2 = st.columns(2)
                with ac1:
                    apply_sel = st.button(
                        ui["ingest_apply_selected"],
                        key=f"ingest_apply_sel_{selected}",
                        type="primary",
                    )
                with ac2:
                    apply_all = st.button(
                        ui["ingest_apply_all"],
                        key=f"ingest_apply_all_{selected}",
                    )
                if apply_sel:
                    _, apply = run_ingest_patch(
                        selected,
                        filtered,
                        allow_status_change=allow_st,
                        bump_locked_with_evidence=True,
                        dry_run=False,
                    )
                    if apply.ok:
                        st.success(ui["ingest_applied"])
                        if mark_cryst and isinstance(src_done, list):
                            titles = {str(x) for x in src_done}
                            secs = _get_sections(selected)
                            _mark_done_crystallized(secs, titles)
                            _auto_save(selected, secs)
                        del st.session_state[patch_key]
                        sk = f"kanban_ingest_source_done_{selected}"
                        if sk in st.session_state:
                            del st.session_state[sk]
                        st.rerun()
                    else:
                        for e in apply.errors:
                            st.error(e)
                        for w in apply.warnings:
                            st.warning(w)
                if apply_all:
                    _, apply = run_ingest_patch(
                        selected,
                        raw_patch,
                        allow_status_change=allow_st,
                        bump_locked_with_evidence=True,
                        dry_run=False,
                    )
                    if apply.ok:
                        st.success(ui["ingest_applied"])
                        if mark_cryst and isinstance(src_done, list):
                            titles = {str(x) for x in src_done}
                            secs = _get_sections(selected)
                            _mark_done_crystallized(secs, titles)
                            _auto_save(selected, secs)
                        del st.session_state[patch_key]
                        sk = f"kanban_ingest_source_done_{selected}"
                        if sk in st.session_state:
                            del st.session_state[sk]
                        st.rerun()
                    else:
                        for e in apply.errors:
                            st.error(e)
                        for w in apply.warnings:
                            st.warning(w)
