"""Kanban -- visual task board editor for kanban.md.

Primary persist actions use the toolbar **Reload** / **Save** pattern.
Skill Tree uses a title-row **Save** instead; see docs/zh/web-ui-product.md.
"""

from __future__ import annotations

from dataclasses import replace

import streamlit as st
import yaml

from nblane.core import llm as llm_client
from nblane.core.io import (
    KANBAN_DOING,
    KANBAN_DONE,
    KanbanTask,
    append_kanban_archive,
    parse_kanban,
    profile_dir,
    save_kanban,
)
from nblane.kanban_ui import render_kanban_board
from nblane.core.profile_ingest import (
    filter_ingest_patch,
    ingest_preview_delta,
    merge_ingest_patch,
    parse_ingest_patch,
    run_ingest_patch,
    schema_node_labels,
)
from nblane.core.profile_ingest_llm import ingest_kanban_done_json
from nblane.web_cache import (
    clear_web_cache,
    load_evidence_pool_raw,
    load_skill_tree_raw,
)
from nblane.web_i18n import (
    kanban_section_label,
    kanban_ui,
)
from nblane.web_auth import require_login
from nblane.web_shared import (
    assert_files_current,
    drop_streamlit_widget_keys,
    ensure_file_snapshot,
    remember_allow_and_drop_yaml_preview_keys,
    refresh_file_snapshots,
    render_git_backup_notices,
    render_llm_unavailable,
    select_profile,
    stash_git_backup_results,
    ui_emoji_enabled,
)


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
    path = profile_dir(profile) / "kanban.md"
    assert_files_current([path])
    save_kanban(profile, sections)
    refresh_file_snapshots([path])
    stash_git_backup_results()
    clear_web_cache()


def _mark_done_crystallized(
    sections: dict[str, list[KanbanTask]],
    titles: set[str],
) -> None:
    """Set crystallized on Done tasks whose titles are in *titles*."""
    done_list = sections.get(KANBAN_DONE) or []
    for i, t in enumerate(done_list):
        if t.title in titles:
            done_list[i] = replace(t, crystallized=True)


# -- Page --------------------------------------------------------

ui = kanban_ui()
st.set_page_config(
    page_title=ui["page_title"],
    layout="wide",
)

require_login()
selected = select_profile()
render_git_backup_notices()
_pdir = profile_dir(selected)
_kanban_path = _pdir / "kanban.md"
_archive_path = _pdir / "kanban-archive.md"
_pool_path = _pdir / "evidence-pool.yaml"
_tree_path = _pdir / "skill-tree.yaml"
_skill_path = _pdir / "SKILL.md"
for _path in (
    _kanban_path,
    _archive_path,
    _pool_path,
    _tree_path,
    _skill_path,
):
    ensure_file_snapshot(_path)

st.title(ui["title"])
st.caption(ui["page_context_line"])

auto_dates = st.checkbox(
    ui["kb_auto_dates"],
    value=True,
    key=f"kanban_auto_dates_{selected}",
    help=ui["kb_auto_dates_help"],
)
focus_mode = st.checkbox(
    ui["kb_focus_mode"],
    value=False,
    key=f"kanban_focus_{selected}",
    help=ui["kb_focus_mode_help"],
)

# -- Toolbar -----------------------------------------------------

tb1, tb2, tb3 = st.columns([1, 1, 3])
with tb1:
    if st.button(ui["reload"]):
        _load_into_state(selected)
        refresh_file_snapshots([_kanban_path])
        st.rerun()
with tb2:
    if st.button(ui["save"], type="primary"):
        sections = _get_sections(selected)
        _auto_save(selected, sections)
        st.success(ui["saved"])

sections = _get_sections(selected)

total_tasks = sum(len(tasks) for tasks in sections.values())
doing_count = len(sections.get(KANBAN_DOING, []))
done_count = len(sections.get(KANBAN_DONE, []))

mc1, mc2, mc3 = st.columns(3)
use_emoji = ui_emoji_enabled()
mc1.metric(ui["metric_total"], total_tasks)
mc2.metric(
    ui["metric_doing"] if use_emoji else kanban_section_label(KANBAN_DOING),
    doing_count,
)
mc3.metric(
    ui["metric_done"] if use_emoji else kanban_section_label(KANBAN_DONE),
    done_count,
)

st.divider()

# -- Done bulk ---------------------------------------------------

with st.expander(ui["done_bulk_title"], expanded=False):
    done_tasks_bulk = sections.get(KANBAN_DONE) or []
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
                    assert_files_current([_archive_path, _kanban_path])
                    to_arc = [done_tasks_bulk[i] for i in pick_bulk]
                    append_kanban_archive(selected, to_arc)
                    refresh_file_snapshots([_archive_path])
                    stash_git_backup_results()
                    for j in sorted(pick_bulk, reverse=True):
                        done_tasks_bulk.pop(j)
                    sections[KANBAN_DONE] = done_tasks_bulk
                    _auto_save(selected, sections)
                    st.rerun()
        with b2:
            if st.button(ui["delete_done"], key=f"delbulk_{selected}"):
                if pick_bulk:
                    for j in sorted(pick_bulk, reverse=True):
                        done_tasks_bulk.pop(j)
                    sections[KANBAN_DONE] = done_tasks_bulk
                    _auto_save(selected, sections)
                    st.rerun()

# -- Board columns -----------------------------------------------

render_kanban_board(
    sections,
    selected,
    auto_dates,
    ui,
    focus_mode,
)

# -- Done → evidence (AI ingest) ---------------------------------

st.divider()
with st.expander(ui["ingest_expander"], expanded=False):
    done_tasks = sections.get(KANBAN_DONE) or []
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
                    assert_files_current(
                        [_pool_path, _tree_path, _skill_path]
                    )
                    _, apply = run_ingest_patch(
                        selected,
                        filtered,
                        allow_status_change=allow_st,
                        bump_locked_with_evidence=True,
                        dry_run=False,
                    )
                    if apply.ok:
                        clear_web_cache()
                        refresh_file_snapshots(
                            [_pool_path, _tree_path, _skill_path]
                        )
                        stash_git_backup_results()
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
                    assert_files_current(
                        [_pool_path, _tree_path, _skill_path]
                    )
                    _, apply = run_ingest_patch(
                        selected,
                        raw_patch,
                        allow_status_change=allow_st,
                        bump_locked_with_evidence=True,
                        dry_run=False,
                    )
                    if apply.ok:
                        clear_web_cache()
                        refresh_file_snapshots(
                            [_pool_path, _tree_path, _skill_path]
                        )
                        stash_git_backup_results()
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
