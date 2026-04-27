"""Kanban -- visual task board editor for kanban.md.

Primary persist actions use the toolbar **Reload** / **Save** pattern.
Skill Tree uses a title-row **Save** instead; see docs/zh/web-ui-product.md.
"""

from __future__ import annotations

from dataclasses import replace

import streamlit as st
import yaml

from nblane.core import gap as gap_engine
from nblane.core import llm as llm_client
from nblane.core.kanban_io import (
    KANBAN_BOARD_SECTIONS,
    apply_kanban_reorder,
    ensure_kanban_task_ids,
    kanban_snapshot_to_moves,
)
from nblane.core.kanban_ai import (
    KanbanSubtaskProposal,
    analyze_kanban_task_gap,
    apply_kanban_subtask_proposals,
    generate_kanban_subtask_proposals,
)
from nblane.core.io import (
    KANBAN_DOING,
    KANBAN_DONE,
    KANBAN_QUEUE,
    KanbanSubtask,
    KanbanTask,
    append_kanban_archive,
    parse_kanban,
    profile_dir,
    save_kanban,
)
from nblane.kanban_board_component import st_kanban_board
from nblane.kanban_ui import render_kanban_board
from nblane.kanban_ui._helpers import (
    _bump_kanban_widget_epoch,
    _clear_kanban_dirty,
    _kanban_is_dirty,
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
from nblane.web_cache import (
    clear_web_cache,
    load_evidence_pool_raw,
    load_skill_tree_raw,
)
from nblane.web_i18n import (
    kanban_section_label,
    kanban_ui,
)
from nblane.web_linkify import extract_plain_urls
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
    st.session_state[_state_key(profile)] = ensure_kanban_task_ids(
        parse_kanban(profile),
        profile,
    )


def _get_sections(profile: str) -> dict[str, list[KanbanTask]]:
    """Get kanban sections from session state."""
    key = _state_key(profile)
    if key not in st.session_state:
        _load_into_state(profile)
    st.session_state[key] = ensure_kanban_task_ids(
        st.session_state[key],
        profile,
    )
    return st.session_state[key]


def _auto_save(
    profile: str,
    sections: dict[str, list[KanbanTask]],
) -> None:
    """Persist changes to kanban.md."""
    path = profile_dir(profile) / "kanban.md"
    assert_files_current([path])
    ensured = ensure_kanban_task_ids(sections, profile)
    sections.clear()
    sections.update(ensured)
    save_kanban(profile, sections)
    refresh_file_snapshots([path])
    stash_git_backup_results()
    clear_web_cache()
    _clear_kanban_dirty(profile)


def _mark_done_crystallized(
    sections: dict[str, list[KanbanTask]],
    task_ids: set[str],
    titles: set[str] | None = None,
) -> None:
    """Set crystallized on Done tasks by stable ids, with title fallback."""
    done_list = sections.get(KANBAN_DONE) or []
    fallback_titles = titles or set()
    for i, t in enumerate(done_list):
        if (t.id and t.id in task_ids) or (
            not task_ids and t.title in fallback_titles
        ):
            done_list[i] = replace(t, crystallized=True)


def _board_event_key(profile: str) -> str:
    """Session key for the latest consumed unified-board event."""
    return f"kanban_board_event_id_{profile}"


def _gap_results_key(profile: str) -> str:
    """Session key for per-task gap analysis previews."""
    return f"kanban_gap_results_{profile}"


def _subtask_proposals_key(profile: str) -> str:
    """Session key for per-task AI subtask proposals."""
    return f"kanban_subtask_proposals_{profile}"


def _task_text_fields(task: KanbanTask) -> list[str]:
    """Text fields used to extract task links."""
    fields = [
        task.title,
        task.context,
        task.why,
        task.blocked_by,
        task.outcome,
        "\n".join(task.details),
    ]
    fields.extend(subtask.title for subtask in task.subtasks)
    return fields


def _task_links(task: KanbanTask) -> list[dict[str, str]]:
    """Return URL chips extracted from a task."""
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for field in _task_text_fields(task):
        for url in extract_plain_urls(field):
            if url in seen:
                continue
            seen.add(url)
            out.append({"label": url, "url": url})
    return out


def _task_payload(task: KanbanTask) -> dict:
    """Serialize a KanbanTask for the unified board component."""
    return {
        "id": task.id,
        "title": task.title,
        "done": task.done,
        "context": task.context,
        "why": task.why,
        "blocked_by": task.blocked_by,
        "outcome": task.outcome,
        "started_on": task.started_on or "",
        "completed_on": task.completed_on or "",
        "crystallized": task.crystallized,
        "subtasks": [
            {
                "id": f"subtask-{i}",
                "index": i,
                "title": subtask.title,
                "done": subtask.done,
            }
            for i, subtask in enumerate(task.subtasks)
        ],
        "details": list(task.details),
        "links": _task_links(task),
    }


def _sections_payload(
    sections: dict[str, list[KanbanTask]],
) -> dict[str, list[dict]]:
    """Serialize all board sections for the unified board component."""
    return {
        section: [
            _task_payload(task)
            for task in sections.get(section, [])
            if task.id
        ]
        for section in KANBAN_BOARD_SECTIONS
    }


def _board_labels(ui: dict[str, str]) -> dict[str, str]:
    """Labels consumed by the unified board component."""
    labels = {
        section: kanban_section_label(section)
        for section in KANBAN_BOARD_SECTIONS
    }
    labels.update(
        {
            "add": ui["add"],
            "ai_done": ui["ingest_generate"],
            "ai_gap": ui.get("kb_ai_gap", "Analyze gap"),
            "ai_subtasks": ui.get("kb_ai_subtasks", "Draft subtasks"),
            "blocked_by": ui["field_blocked"],
            "completed_on": ui["field_completed"],
            "context": ui["field_context"],
            "crystallize": ui.get("kb_mark_crystallized", "Mark crystallized"),
            "crystallized": ui["crystallized"],
            "delete_task": ui["kb_delete_card"],
            "details": ui["details"],
            "done_uncrystallized": ui.get(
                "kb_done_uncrystallized",
                "Done, not crystallized",
            ),
            "empty": ui.get("ingest_no_done", "No tasks."),
            "links": ui["kb_links_preview"],
            "new_subtask": ui["kb_read_new_subtask_ph"],
            "outcome": ui["field_outcome"],
            "quick_add": ui.get("kb_quick_add", "+ Add task"),
            "save": ui["save"],
            "started_on": ui["field_started"],
            "subtasks": ui["subtasks_label"],
            "title": ui["task_field_title"],
            "untitled": ui.get("kb_title_required", "Untitled"),
            "why": ui["field_why"],
        }
    )
    return labels


def _find_task_ref(
    sections: dict[str, list[KanbanTask]],
    task_id: str,
) -> tuple[str, int, KanbanTask] | None:
    """Find a task by id in session sections."""
    wanted = str(task_id or "").strip()
    if not wanted:
        return None
    for section, tasks in sections.items():
        for idx, task in enumerate(tasks):
            if task.id == wanted:
                return section, idx, task
    return None


def _event_task_id(event: dict, payload: dict) -> str:
    """Return task id from an event payload or selected UI state."""
    for key in ("card_id", "task_id", "id"):
        value = payload.get(key)
        if value:
            return str(value)
    ui_state = event.get("ui")
    if isinstance(ui_state, dict):
        value = ui_state.get("selected_card_id")
        if value:
            return str(value)
    return ""


def _split_details(value: object) -> list[str]:
    """Split a textarea value into kanban detail bullet lines."""
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    text_value = str(value or "")
    return [
        line.strip()
        for line in text_value.splitlines()
        if line.strip()
    ]


def _apply_task_update(
    task: KanbanTask,
    card: dict,
) -> KanbanTask | None:
    """Return updated task or None when title is invalid."""
    changes: dict[str, object] = {}
    if "title" in card:
        title = str(card.get("title") or "").strip()
        if not title:
            return None
        changes["title"] = title
    for field in ("context", "why", "blocked_by", "outcome"):
        if field in card:
            changes[field] = str(card.get(field) or "").strip()
    if "started_on" in card:
        changes["started_on"] = (
            str(card.get("started_on") or "").strip() or None
        )
    if "completed_on" in card:
        changes["completed_on"] = (
            str(card.get("completed_on") or "").strip() or None
        )
    if "notes" in card:
        changes["details"] = _split_details(card.get("notes"))
    elif "details" in card:
        changes["details"] = _split_details(card.get("details"))
    return replace(task, **changes) if changes else task


def _render_gap_previews(profile: str, ui: dict[str, str]) -> None:
    """Render stored task-level gap results below the board."""
    results = st.session_state.get(_gap_results_key(profile), {})
    if not isinstance(results, dict) or not results:
        return
    with st.expander(ui.get("kb_gap_preview_title", "Task gap previews")):
        for task_id, result in list(results.items()):
            if getattr(result, "error", None):
                st.error(f"{task_id}: {result.error}")
                continue
            st.markdown(f"**{result.task or task_id}**")
            c1, c2, c3 = st.columns(3)
            c1.metric(ui.get("metric_matches", "Matches"), len(result.top_matches))
            c2.metric(ui.get("metric_gaps", "Gaps"), len(result.gaps))
            c3.metric(
                ui.get("metric_verdict", "Verdict"),
                ui.get("verdict_ok", "OK")
                if result.can_solve
                else ui.get("verdict_gap", "Gaps remain"),
            )
            if result.top_matches:
                st.caption("Matches: " + ", ".join(
                    f"{m.get('id', '')}" for m in result.top_matches
                ))
            if result.gaps:
                st.caption("Gaps: " + ", ".join(result.gaps))
            if result.next_steps:
                st.markdown(gap_engine.format_text(result))


def _render_subtask_proposals(
    profile: str,
    sections: dict[str, list[KanbanTask]],
    ui: dict[str, str],
) -> None:
    """Render AI subtask proposals and apply selected rows."""
    proposals_by_task = st.session_state.get(
        _subtask_proposals_key(profile),
        {},
    )
    if not isinstance(proposals_by_task, dict) or not proposals_by_task:
        return
    with st.expander(
        ui.get("kb_subtask_proposals_title", "AI subtask drafts"),
        expanded=True,
    ):
        for task_id, proposals in list(proposals_by_task.items()):
            if not isinstance(proposals, list) or not proposals:
                continue
            found = _find_task_ref(sections, task_id)
            task_title = found[2].title if found else task_id
            st.markdown(f"**{task_title}**")
            include: list[bool] = []
            for idx, proposal in enumerate(proposals):
                if not isinstance(proposal, KanbanSubtaskProposal):
                    continue
                include.append(
                    st.checkbox(
                        proposal.title,
                        value=True,
                        key=f"kb_ai_sub_{profile}_{task_id}_{idx}",
                    )
                )
                if proposal.reason:
                    st.caption(proposal.reason)
            if st.button(
                ui.get("kb_apply_subtasks", "Apply selected subtasks"),
                key=f"kb_ai_sub_apply_{profile}_{task_id}",
                type="primary",
            ):
                selected_props = [
                    proposal
                    for proposal, ok in zip(proposals, include)
                    if ok
                ]
                updated = apply_kanban_subtask_proposals(
                    sections,
                    task_id,
                    selected_props,
                )
                sections.clear()
                sections.update(updated)
                _auto_save(profile, sections)
                proposals_by_task.pop(task_id, None)
                st.rerun()


def _handle_board_event(
    event: dict | None,
    *,
    profile: str,
    sections: dict[str, list[KanbanTask]],
    auto_dates: bool,
    ui: dict[str, str],
) -> None:
    """Apply one event emitted by the unified board component."""
    if not isinstance(event, dict):
        return
    action = str(event.get("action") or "")
    if not action:
        return
    event_id = str(event.get("event_id") or "")
    event_key = _board_event_key(profile)
    if event_id and st.session_state.get(event_key) == event_id:
        return
    if event_id:
        st.session_state[event_key] = event_id
    payload = event.get("payload")
    if not isinstance(payload, dict):
        payload = {}

    if action in ("move_card", "reorder"):
        snapshot = {"columns": event.get("sections") or []}
        moves = kanban_snapshot_to_moves(
            snapshot,
            sections,
            section_order=KANBAN_BOARD_SECTIONS,
        )
        if moves is None:
            st.warning(ui["kb_drag_stale"])
            return
        if moves:
            updated = apply_kanban_reorder(
                sections,
                moves,
                auto_dates=auto_dates,
            )
            sections.clear()
            sections.update(updated)
            _auto_save(profile, sections)
            st.rerun()
        return

    if action == "quick_add":
        title = str(payload.get("title") or "").strip()
        section = str(payload.get("section") or KANBAN_QUEUE)
        if not title:
            st.warning(ui["kb_title_required"])
            return
        if section not in KANBAN_BOARD_SECTIONS:
            section = KANBAN_QUEUE
        task = KanbanTask(title=title)
        if section == KANBAN_DONE:
            task = replace(task, done=True)
        sections.setdefault(section, []).append(task)
        _auto_save(profile, sections)
        st.rerun()

    task_id = _event_task_id(event, payload)
    found = _find_task_ref(sections, task_id)

    if action == "edit_card":
        if found is None:
            st.warning(ui["kb_drag_stale"])
            return
        section, idx, task = found
        card = payload.get("card")
        if not isinstance(card, dict):
            card = payload
        updated_task = _apply_task_update(task, card)
        if updated_task is None:
            st.warning(ui["kb_title_required"])
            return
        sections[section][idx] = updated_task
        _auto_save(profile, sections)
        st.rerun()

    if action == "toggle_subtask":
        if found is None:
            st.warning(ui["kb_drag_stale"])
            return
        section, idx, task = found
        try:
            subtask_index = int(payload.get("subtask_index", -1))
        except (TypeError, ValueError):
            subtask_index = -1
        if not 0 <= subtask_index < len(task.subtasks):
            return
        next_subtasks = list(task.subtasks)
        next_subtasks[subtask_index] = replace(
            next_subtasks[subtask_index],
            done=bool(payload.get("done")),
        )
        sections[section][idx] = replace(task, subtasks=next_subtasks)
        _auto_save(profile, sections)
        st.rerun()

    if action == "add_subtask":
        if found is None:
            st.warning(ui["kb_drag_stale"])
            return
        section, idx, task = found
        title = str(payload.get("title") or "").strip()
        if not title:
            return
        sections[section][idx] = replace(
            task,
            subtasks=task.subtasks + [KanbanSubtask(title=title)],
        )
        _auto_save(profile, sections)
        st.rerun()

    if action == "delete_task":
        if found is None:
            st.warning(ui["kb_drag_stale"])
            return
        section, idx, _task = found
        sections[section].pop(idx)
        _auto_save(profile, sections)
        st.rerun()

    if action == "crystallize_card":
        if found is None:
            st.warning(ui["kb_drag_stale"])
            return
        section, idx, task = found
        sections[section][idx] = replace(task, crystallized=True)
        _auto_save(profile, sections)
        st.rerun()

    if action in ("request_gap", "ai_gap_ingest"):
        if found is None:
            st.warning(ui["kb_drag_stale"])
            return
        with st.spinner(ui.get("spinner_gap", "Running gap analysis...")):
            result = analyze_kanban_task_gap(
                profile,
                sections,
                task_id,
                use_rule_match=True,
                use_llm_router=llm_client.is_configured(),
                persist_router_keywords=False,
            )
        state = st.session_state.setdefault(_gap_results_key(profile), {})
        state[task_id] = result
        return

    if action in ("request_subtasks", "ai_subtask_ingest"):
        if found is None:
            st.warning(ui["kb_drag_stale"])
            return
        if not llm_client.is_configured():
            render_llm_unavailable(ui)
            return
        with st.spinner(ui.get("spinner_ai", "AI reasoning...")):
            proposals = generate_kanban_subtask_proposals(
                profile,
                sections,
                task_id,
                use_rule_match=True,
                use_llm_router=True,
                persist_router_keywords=False,
            )
        if not proposals:
            st.warning(ui.get("kb_no_subtask_proposals", "No subtask draft was generated."))
            return
        state = st.session_state.setdefault(
            _subtask_proposals_key(profile),
            {},
        )
        state[task_id] = proposals
        return

    if action in ("request_done_ingest", "ai_done_ingest"):
        if found is None:
            st.warning(ui["kb_drag_stale"])
            return
        _section, _idx, task = found
        if not llm_client.is_configured():
            render_llm_unavailable(ui)
            return
        with st.spinner(ui["ingest_spinner"]):
            patch, err = ingest_kanban_done_json(profile, [task])
        if err is not None:
            st.error(ui["ingest_err"].format(msg=err))
            return
        if patch is not None:
            drop_streamlit_widget_keys(
                [
                    f"pv_pool_{profile}",
                    f"pv_tree_{profile}",
                ]
            )
            st.session_state[f"kanban_ingest_source_done_{profile}"] = [
                task.title
            ]
            st.session_state[f"kanban_ingest_source_done_ids_{profile}"] = [
                task.id
            ]
            st.session_state[f"kanban_ingest_patch_{profile}"] = patch
            st.rerun()


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
        _clear_kanban_dirty(selected)
        _bump_kanban_widget_epoch(selected)
        refresh_file_snapshots([_kanban_path])
        st.rerun()
with tb2:
    if st.button(ui["save"], type="primary"):
        sections = _get_sections(selected)
        _auto_save(selected, sections)
        st.success(ui["saved"])
with tb3:
    if _kanban_is_dirty(selected):
        st.caption(ui["kb_unsaved_subtasks"])

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

# -- Unified board -----------------------------------------------

board_event = st_kanban_board(
    sections=_sections_payload(sections),
    labels=_board_labels(ui),
    settings={
        "section_order": list(KANBAN_BOARD_SECTIONS),
        "auto_dates": auto_dates,
        "focus_mode": focus_mode,
    },
    ai_state={
        "status": (
            ui["llm_configured"].format(label=llm_client.model_label())
            if llm_client.is_configured()
            else ui["ai_not_configured"]
        )
    },
    key=f"kanban_board_{selected}",
    height=820,
)
if board_event is None:
    st.warning(
        ui.get(
            "kb_board_component_missing",
            "Unified board component is unavailable; using the legacy editor.",
        )
    )
    render_kanban_board(
        sections,
        selected,
        auto_dates,
        ui,
        focus_mode,
    )
else:
    _handle_board_event(
        board_event,
        profile=selected,
        sections=sections,
        auto_dates=auto_dates,
        ui=ui,
    )
    _render_gap_previews(selected, ui)
    _render_subtask_proposals(selected, sections, ui)

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
                        f"kanban_ingest_source_done_ids_{selected}"
                    ] = [t.id for t in chosen if t.id]
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
            src_done_ids = st.session_state.get(
                f"kanban_ingest_source_done_ids_{selected}"
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
                            ids = (
                                {str(x) for x in src_done_ids}
                                if isinstance(src_done_ids, list)
                                else set()
                            )
                            secs = _get_sections(selected)
                            _mark_done_crystallized(secs, ids, titles)
                            _auto_save(selected, secs)
                        del st.session_state[patch_key]
                        for sk in (
                            f"kanban_ingest_source_done_{selected}",
                            f"kanban_ingest_source_done_ids_{selected}",
                        ):
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
                            ids = (
                                {str(x) for x in src_done_ids}
                                if isinstance(src_done_ids, list)
                                else set()
                            )
                            secs = _get_sections(selected)
                            _mark_done_crystallized(secs, ids, titles)
                            _auto_save(selected, secs)
                        del st.session_state[patch_key]
                        for sk in (
                            f"kanban_ingest_source_done_{selected}",
                            f"kanban_ingest_source_done_ids_{selected}",
                        ):
                            if sk in st.session_state:
                                del st.session_state[sk]
                        st.rerun()
                    else:
                        for e in apply.errors:
                            st.error(e)
                        for w in apply.warnings:
                            st.warning(w)
