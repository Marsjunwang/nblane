"""Review -- generate evidence, next-action, and public-draft candidates."""

from __future__ import annotations

from datetime import date

import streamlit as st
import yaml

from nblane.core.growth_review import build_weekly_review
from nblane.core.paths import PROFILES_DIR
from nblane.core.review_actions import (
    apply_review_evidence_candidate,
    apply_review_next_action_candidate,
    apply_review_public_draft_candidate,
    review_window_default,
    review_window_for_preset,
    save_review_candidates_to_activity,
)
from nblane.web_auth import require_login
from nblane.web_cache import clear_web_cache
from nblane.web_i18n import review_ui
from nblane.web_shared import (
    apply_ui_language_from_session,
    assert_files_current,
    refresh_file_snapshots,
    render_current_goal_strip,
    render_git_backup_notices,
    select_profile,
    stash_git_backup_results,
)

apply_ui_language_from_session()

ui = review_ui()

st.set_page_config(page_title=ui["page_title"], layout="wide")
require_login()
selected = select_profile()
render_git_backup_notices()


def _session_key(name: str) -> str:
    return f"review:{selected}:{name}"


def _candidate_rows(candidates: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for index, item in enumerate(candidates):
        rows.append(
            {
                "select": False,
                "index": index,
                "source": str(item.get("source", "") or ""),
                "title": str(item.get("title", "") or ""),
                "summary": str(item.get("summary", "") or item.get("notes", "") or ""),
                "ref": str(item.get("task_id", "") or item.get("resource_id", "") or ""),
            }
        )
    return rows


def _selected_candidates(candidates: list[dict], edited: object) -> list[dict]:
    if not isinstance(edited, list):
        return []
    out: list[dict] = []
    for row in edited:
        if not isinstance(row, dict) or not row.get("select"):
            continue
        try:
            index = int(row.get("index"))
        except (TypeError, ValueError):
            continue
        if 0 <= index < len(candidates):
            out.append(candidates[index])
    return out


def _render_candidate_table(
    label: str,
    candidates: list[dict],
    *,
    key: str,
) -> list[dict]:
    st.subheader(label)
    if not candidates:
        st.caption(ui["no_candidates"])
        return []
    rows = _candidate_rows(candidates)
    edited = st.data_editor(
        rows,
        hide_index=True,
        use_container_width=True,
        key=key,
        column_config={
            "select": st.column_config.CheckboxColumn(ui["select_rows"]),
            "index": None,
        },
        disabled=["source", "title", "summary", "ref"],
    )
    selected_rows = _selected_candidates(candidates, edited)
    with st.expander(ui["candidate_preview"], expanded=False):
        st.code(
            yaml.dump(
                selected_rows or candidates[:3],
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            ),
            language="yaml",
        )
    return selected_rows


def _show_result(result) -> None:
    if result.ok:
        st.success(ui["applied"])
        if result.output_path is not None:
            st.caption(str(result.output_path))
        for warning in result.warnings:
            st.warning(warning)
        return
    st.error(ui["failed"])
    for error in result.errors:
        st.error(error)
    for warning in result.warnings:
        st.warning(warning)


_head_l, _head_goal = st.columns([5, 2], gap="medium", vertical_alignment="top")
with _head_l:
    st.title(ui["title"])
    st.caption(ui["page_context_line"])
with _head_goal:
    render_current_goal_strip(selected, compact=True, align="right")

presets = {
    ui["preset_current_week"]: "current_week",
    ui["preset_previous_week"]: "previous_week",
    ui["preset_last_30_days"]: "last_30_days",
    ui["preset_custom"]: "custom",
}
default_start, default_end = review_window_default()
c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
with c1:
    preset_label = st.selectbox(ui["preset"], list(presets.keys()))
preset = presets[preset_label]
if preset == "custom":
    start_raw = st.session_state.get(_session_key("start"), default_start)
    end_raw = st.session_state.get(_session_key("end"), default_end)
    start_value = (
        start_raw
        if isinstance(start_raw, date)
        else date.fromisoformat(str(start_raw)[:10])
    )
    end_value = (
        end_raw
        if isinstance(end_raw, date)
        else date.fromisoformat(str(end_raw)[:10])
    )
else:
    start_value, end_value = review_window_for_preset(preset)
with c2:
    start = st.date_input(ui["start_date"], value=start_value)
with c3:
    end = st.date_input(ui["end_date"], value=end_value)
with c4:
    st.write("")
    generate = st.button(ui["generate"], type="primary", use_container_width=True)

if generate or _session_key("payload") not in st.session_state:
    review = build_weekly_review(
        selected,
        start,
        end,
        profile_path=PROFILES_DIR / selected,
    )
    st.session_state[_session_key("payload")] = review.to_dict()["review"]
    st.session_state[_session_key("start")] = review.week_start
    st.session_state[_session_key("end")] = review.week_end

payload = st.session_state.get(_session_key("payload")) or {}
start_text = str(payload.get("week_start") or start)
end_text = str(payload.get("week_end") or end)

summary = {
    ui["done_tasks"]: len(payload.get("done_task_ids") or []),
    ui["evidence_candidates"]: len(payload.get("evidence_candidates") or []),
    ui["next_action_candidates"]: len(payload.get("next_queue_candidates") or []),
    ui["public_draft_candidates"]: len(payload.get("public_candidates") or []),
}
st.subheader(ui["summary"])
m1, m2, m3, m4 = st.columns(4)
for col, (label, value) in zip((m1, m2, m3, m4), summary.items()):
    col.metric(label, value)

with st.expander(ui["summary"], expanded=False):
    st.code(
        yaml.dump(
            {
                "activity_summary": payload.get("activity_summary") or {},
                "learning_summary": payload.get("learning_summary") or {},
                "inbox_summary": payload.get("inbox_summary") or {},
            },
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        ),
        language="yaml",
    )

tab_ev, tab_next, tab_public, tab_method, tab_activity = st.tabs(
    [
        ui["evidence_candidates"],
        ui["next_action_candidates"],
        ui["public_draft_candidates"],
        ui["method_notes"],
        ui["agent_activity"],
    ]
)

with tab_ev:
    evidence_candidates = list(payload.get("evidence_candidates") or [])
    selected_evidence = _render_candidate_table(
        ui["evidence_candidates"],
        evidence_candidates,
        key=_session_key("evidence_table"),
    )
    mark_crystallized = st.checkbox(ui["mark_crystallized"], value=True)
    b1, b2 = st.columns(2)
    with b1:
        if st.button(ui["save_to_activity"], key=_session_key("save_evidence"), disabled=not selected_evidence):
            save_review_candidates_to_activity(
                selected,
                start_text,
                end_text,
                "evidence",
                selected_evidence,
            )
            stash_git_backup_results()
            clear_web_cache()
            st.success(ui["saved"])
            st.rerun()
    with b2:
        if st.button(ui["apply_selected"], key=_session_key("apply_evidence"), disabled=not selected_evidence, type="primary"):
            paths = [
                PROFILES_DIR / selected / "evidence-pool.yaml",
                PROFILES_DIR / selected / "kanban.md",
            ]
            assert_files_current(paths)
            for candidate in selected_evidence:
                result = apply_review_evidence_candidate(
                    selected,
                    start_text,
                    end_text,
                    candidate,
                    mark_crystallized=mark_crystallized,
                )
                _show_result(result)
            refresh_file_snapshots(paths)
            stash_git_backup_results()
            clear_web_cache()
            st.rerun()

with tab_next:
    next_candidates = list(payload.get("next_queue_candidates") or [])
    selected_next = _render_candidate_table(
        ui["next_action_candidates"],
        next_candidates,
        key=_session_key("next_table"),
    )
    b1, b2 = st.columns(2)
    with b1:
        if st.button(ui["save_to_activity"], key=_session_key("save_next"), disabled=not selected_next):
            save_review_candidates_to_activity(
                selected,
                start_text,
                end_text,
                "next_action",
                selected_next,
            )
            stash_git_backup_results()
            clear_web_cache()
            st.success(ui["saved"])
            st.rerun()
    with b2:
        if st.button(ui["apply_selected"], key=_session_key("apply_next"), disabled=not selected_next, type="primary"):
            paths = [PROFILES_DIR / selected / "kanban.md"]
            assert_files_current(paths)
            for candidate in selected_next:
                result = apply_review_next_action_candidate(
                    selected,
                    start_text,
                    end_text,
                    candidate,
                )
                _show_result(result)
            refresh_file_snapshots(paths)
            stash_git_backup_results()
            clear_web_cache()
            st.rerun()

with tab_public:
    st.caption(ui["public_draft_note"])
    public_candidates = list(payload.get("public_candidates") or [])
    selected_public = _render_candidate_table(
        ui["public_draft_candidates"],
        public_candidates,
        key=_session_key("public_table"),
    )
    b1, b2 = st.columns(2)
    with b1:
        if st.button(ui["save_to_activity"], key=_session_key("save_public"), disabled=not selected_public):
            save_review_candidates_to_activity(
                selected,
                start_text,
                end_text,
                "public_draft",
                selected_public,
            )
            stash_git_backup_results()
            clear_web_cache()
            st.success(ui["saved"])
            st.rerun()
    with b2:
        if st.button(ui["create_public_drafts"], key=_session_key("apply_public"), disabled=not selected_public, type="primary"):
            for candidate in selected_public:
                result = apply_review_public_draft_candidate(
                    selected,
                    start_text,
                    end_text,
                    candidate,
                )
                _show_result(result)
            stash_git_backup_results()
            clear_web_cache()
            st.rerun()

with tab_method:
    method_candidates = list(payload.get("method_candidates") or [])
    if not method_candidates:
        st.caption(ui["no_candidates"])
    else:
        st.code(
            yaml.dump(
                method_candidates,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            ),
            language="yaml",
        )

with tab_activity:
    st.page_link("pages/9_Agent_Activity.py", label=ui["open_activity"])
