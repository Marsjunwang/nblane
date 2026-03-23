"""Kanban -- visual task board editor for kanban.md."""

from __future__ import annotations

import yaml
import streamlit as st

from nblane.core import llm as llm_client
from nblane.core.io import (
    KANBAN_SECTIONS,
    KanbanTask,
    load_evidence_pool_raw,
    load_skill_tree_raw,
    parse_kanban,
    save_kanban,
)
from nblane.core.profile_ingest import (
    ingest_preview_delta,
    merge_ingest_patch,
    run_ingest_patch,
    schema_node_labels,
)
from nblane.core.profile_ingest_llm import ingest_kanban_done_json
from nblane.web_i18n import (
    kanban_move_option_label,
    kanban_section_label,
    kanban_ui,
)
from nblane.web_shared import (
    drop_streamlit_widget_keys,
    remember_allow_and_drop_yaml_preview_keys,
    select_profile,
)

_SECTION_EMOJI = {
    "Doing": "🔄",
    "Queue": "📋",
    "Done": "✅",
    "Someday / Maybe": "💡",
}

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
    st.session_state[_state_key(profile)] = (
        parse_kanban(profile)
    )


def _get_sections(
    profile: str,
) -> dict[str, list[KanbanTask]]:
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


# -- Page --------------------------------------------------------

ui = kanban_ui()
st.set_page_config(
    page_title=ui["page_title"], layout="wide"
)

st.title(ui["title"])

selected = select_profile()

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

total_tasks = sum(
    len(tasks) for tasks in sections.values()
)
doing_count = len(sections.get("Doing", []))
done_count = len(sections.get("Done", []))

mc1, mc2, mc3 = st.columns(3)
mc1.metric(ui["metric_total"], total_tasks)
mc2.metric(ui["metric_doing"], doing_count)
mc3.metric(ui["metric_done"], done_count)

st.divider()

# -- Board columns -----------------------------------------------

board_cols = st.columns(len(KANBAN_SECTIONS))

for col_widget, section in zip(
    board_cols, KANBAN_SECTIONS
):
    emoji = _SECTION_EMOJI.get(section, "")
    color = _SECTION_COLOR.get(section, "#9aa0a6")
    tasks = sections.get(section, [])
    sec_disp = kanban_section_label(section)

    with col_widget:
        st.markdown(
            f"<h4 style='color:{color}'>"
            f"{emoji} {sec_disp}</h4>",
            unsafe_allow_html=True,
        )
        st.caption(
            ui["items_count"].format(n=len(tasks))
        )

        # -- Add task (always visible) --
        with st.container(border=True):
            new_title = st.text_input(
                ui["new_task"],
                key=f"new_title_{section}",
                placeholder=ui["new_task_ph"],
                label_visibility="collapsed",
            )
            if new_title.strip():
                ac1, ac2 = st.columns([3, 1])
                with ac1:
                    new_detail = st.text_input(
                        ui["detail"],
                        key=f"new_detail_{section}",
                        placeholder=ui["detail_ph"],
                        label_visibility="collapsed",
                    )
                with ac2:
                    if st.button(
                        ui["add"],
                        key=f"add_{section}",
                        type="primary",
                    ):
                        t = KanbanTask(
                            title=new_title.strip(),
                            details=(
                                [new_detail.strip()]
                                if new_detail.strip()
                                else []
                            ),
                        )
                        sections[section].append(t)
                        _auto_save(selected, sections)
                        st.rerun()

        # -- Existing tasks --
        to_delete: list[int] = []
        for idx, task in enumerate(tasks):
            with st.container(border=True):
                hdr1, hdr2 = st.columns([8, 1])

                with hdr1:
                    if section != "Someday / Maybe":
                        done = st.checkbox(
                            task.title,
                            value=task.done,
                            key=(
                                f"done_{section}_{idx}"
                            ),
                        )
                        if done != task.done:
                            tasks[idx] = KanbanTask(
                                title=task.title,
                                done=done,
                                details=task.details,
                            )
                    else:
                        st.markdown(
                            f"**{task.title}**"
                        )

                with hdr2:
                    if st.button(
                        "✕",
                        key=f"del_{section}_{idx}",
                    ):
                        to_delete.append(idx)

                new_title_val = st.text_input(
                    ui["title"],
                    value=task.title,
                    key=f"title_{section}_{idx}",
                    label_visibility="collapsed",
                )
                if new_title_val != task.title:
                    tasks[idx] = KanbanTask(
                        title=new_title_val,
                        done=tasks[idx].done,
                        details=tasks[idx].details,
                    )

                existing_details = "\n".join(
                    task.details
                )
                new_details = st.text_area(
                    ui["details"],
                    value=existing_details,
                    key=f"det_{section}_{idx}",
                    label_visibility="collapsed",
                    height=60,
                    placeholder=ui["details_ph"],
                )
                if new_details != existing_details:
                    tasks[idx] = KanbanTask(
                        title=tasks[idx].title,
                        done=tasks[idx].done,
                        details=[
                            d.strip()
                            for d in (
                                new_details.splitlines()
                            )
                            if d.strip()
                        ],
                    )

                # -- Move to another column --
                other_sections = [
                    s
                    for s in KANBAN_SECTIONS
                    if s != section
                ]
                move_opts = ["(stay)"] + list(
                    other_sections
                )
                move_to = st.selectbox(
                    ui["move_to"],
                    move_opts,
                    key=f"mv_{section}_{idx}",
                    label_visibility="collapsed",
                    format_func=lambda x, u=ui: (
                        kanban_move_option_label(x, u)
                    ),
                )
                if move_to != "(stay)":
                    moved = tasks.pop(idx)
                    sections[section] = tasks
                    sections.setdefault(
                        move_to, []
                    ).append(moved)
                    _auto_save(selected, sections)
                    st.rerun()

        for idx in reversed(to_delete):
            tasks.pop(idx)
            _auto_save(selected, sections)
            st.rerun()

        sections[section] = tasks


# -- Done → evidence (AI ingest) --------------------------------

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
                st.warning(ui["ingest_no_ai"])
            else:
                with st.spinner(ui["ingest_spinner"]):
                    patch, err = ingest_kanban_done_json(
                        selected,
                        chosen,
                    )
                if err is not None:
                    st.error(
                        ui["ingest_err"].format(msg=err)
                    )
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
            patch = st.session_state[patch_key]
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
                patch,
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
                if st.button(
                    ui["ingest_apply"],
                    key=f"ingest_apply_{selected}",
                    type="primary",
                ):
                    _, apply = run_ingest_patch(
                        selected,
                        patch,
                        allow_status_change=allow_st,
                        bump_locked_with_evidence=True,
                        dry_run=False,
                    )
                    if apply.ok:
                        st.success(ui["ingest_applied"])
                        del st.session_state[patch_key]
                        sk = f"kanban_ingest_source_done_{selected}"
                        if sk in st.session_state:
                            del st.session_state[sk]
                    else:
                        for e in apply.errors:
                            st.error(e)
                        for w in apply.warnings:
                            st.warning(w)
