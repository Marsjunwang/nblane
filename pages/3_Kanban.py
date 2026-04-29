"""Kanban -- visual task board editor for kanban.md.

Primary persist actions use the toolbar **Reload** / **Save** pattern.
Skill Tree uses a title-row **Save** instead; see docs/zh/web-ui-product.md.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from html import escape
from urllib.parse import urlencode

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
from nblane.core.kanban_events import (
    alignment_context_from_payload as _alignment_context_from_payload,
    apply_kanban_card_update as _apply_task_update,
    discard_subtask_proposal_at as _discard_subtask_proposal_at,
    discard_task_ai_state as _discard_task_ai_state,
    event_subtask_index as _event_subtask_index,
    subtask_proposals_from_payload as _subtask_proposals_from_payload,
)
from nblane.core.kanban_ai import (
    KanbanTaskAlignment,
    KanbanSubtaskGenerationResult,
    KanbanSubtaskProposal,
    analyze_kanban_task_gap,
    apply_kanban_subtask_proposals,
    generate_kanban_task_alignment_options,
    generate_kanban_subtask_proposals_detailed,
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
from nblane.kanban_ui.personal_workspace import (
    checkin_month_payload,
    delete_workspace_checkin,
    record_exercise_checkin,
    record_learning_checkin,
)
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
    apply_ui_language_from_session,
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

apply_ui_language_from_session()


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


def _subtask_alignments_key(profile: str) -> str:
    """Session key for per-task task-understanding alignment options."""
    return f"kanban_subtask_alignments_{profile}"


def _subtask_errors_key(profile: str) -> str:
    """Session key for per-task AI subtask generation diagnostics."""
    return f"kanban_subtask_errors_{profile}"


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


def _proposal_payload(proposal: KanbanSubtaskProposal) -> dict[str, str]:
    """Serialize an AI subtask proposal for inline card review."""
    draft_id = proposal.gap_node_id or proposal.title
    return {
        "id": draft_id,
        "draft_id": draft_id,
        "title": proposal.title,
        "reason": proposal.reason,
        "gap_node_id": proposal.gap_node_id,
        "task_id": proposal.task_id,
        "artifact": proposal.artifact,
        "verification": proposal.verification,
        "granularity": "milestone",
    }


def _subtask_error_message(
    result: KanbanSubtaskGenerationResult,
    ui: dict[str, str],
) -> str:
    """Return localized text for a subtask generation diagnostic."""
    key = f"kb_subtask_error_{result.error_key or 'generic'}"
    fallback = result.message or ui.get(
        "kb_no_subtask_proposals",
        "No usable subtask draft was generated.",
    )
    return ui.get(key, fallback)


def _subtask_error_payload(
    result: KanbanSubtaskGenerationResult,
    ui: dict[str, str],
) -> dict[str, object]:
    """Serialize subtask generation diagnostics for card display."""
    return {
        "error_key": result.error_key,
        "message": _subtask_error_message(result, ui),
        "raw_count": result.raw_count,
        "accepted_count": result.accepted_count,
        "filtered_count": result.filtered_count,
    }


def _alignment_payload(alignment: KanbanTaskAlignment) -> dict:
    """Serialize a task-understanding alignment candidate."""
    return {
        "label": alignment.label,
        "goal": alignment.goal,
        "assumptions": list(alignment.assumptions),
        "subtask_style": alignment.subtask_style,
        "task_id": alignment.task_id,
    }


def _gap_payload(result) -> dict:
    """Serialize a GapResult for inline card preview."""
    if result is None:
        return {}
    if getattr(result, "error", None):
        return {"error": result.error}
    return {
        "task": result.task,
        "can_solve": result.can_solve,
        "gaps": list(result.gaps),
        "next_steps": list(result.next_steps),
        "top_matches": [
            {
                "id": m.get("id", ""),
                "label": m.get("label", ""),
                "score": m.get("score", 0),
                "source": m.get("source", ""),
            }
            for m in result.top_matches
        ],
    }


def _board_ai_state(profile: str, ui: dict[str, str]) -> dict:
    """Return AI previews for the unified board component."""
    proposals = st.session_state.get(_subtask_proposals_key(profile), {})
    alignments = st.session_state.get(_subtask_alignments_key(profile), {})
    errors = st.session_state.get(_subtask_errors_key(profile), {})
    gaps = st.session_state.get(_gap_results_key(profile), {})
    return {
        "status": (
            ui["llm_configured"].format(label=llm_client.model_label())
            if llm_client.is_configured()
            else ui["ai_not_configured"]
        ),
        "proposals_by_task": {
            task_id: [
                _proposal_payload(proposal)
                for proposal in task_proposals
                if isinstance(proposal, KanbanSubtaskProposal)
            ]
            for task_id, task_proposals in (
                proposals.items()
                if isinstance(proposals, dict)
                else []
            )
        },
        "gaps_by_task": {
            task_id: _gap_payload(result)
            for task_id, result in (
                gaps.items() if isinstance(gaps, dict) else []
            )
        },
        "alignment_by_task": {
            task_id: [
                _alignment_payload(alignment)
                for alignment in task_alignments
                if isinstance(alignment, KanbanTaskAlignment)
            ]
            for task_id, task_alignments in (
                alignments.items()
                if isinstance(alignments, dict)
                else []
            )
        },
        "subtask_errors_by_task": {
            task_id: _subtask_error_payload(result, ui)
            for task_id, result in (
                errors.items() if isinstance(errors, dict) else []
            )
            if isinstance(result, KanbanSubtaskGenerationResult)
        },
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
            "ai_done_short": ui.get("kb_ai_done_short", "Evd"),
            "ai_gap_short": ui.get("kb_ai_gap_short", "Gap"),
            "ai_subtasks_short": ui.get("kb_ai_subtasks_short", "Sub"),
            "ai_subtasks": ui.get("kb_ai_subtasks", "Draft subtasks"),
            "alignment_other": ui.get("kb_alignment_other", "Other"),
            "alignment_other_hint": ui.get(
                "kb_alignment_other_hint",
                "Use only my note below",
            ),
            "alignment_title": ui.get(
                "kb_alignment_title",
                "Confirm task understanding",
            ),
            "alignment_custom": ui.get(
                "kb_alignment_custom",
                "Add detail or correction",
            ),
            "alignment_confirm": ui.get(
                "kb_alignment_confirm",
                "Use this understanding",
            ),
            "alignment_custom_only": ui.get(
                "kb_alignment_custom_only",
                "Use only my supplement",
            ),
            "alignment_assumptions": ui.get(
                "kb_alignment_assumptions",
                "Assumptions",
            ),
            "alignment_style": ui.get(
                "kb_alignment_style",
                "Subtask style",
            ),
            "alignment_goal": ui.get("kb_alignment_goal", "Goal"),
            "alignment_label": ui.get("kb_alignment_label", "Label"),
            "alignment_required": ui.get(
                "kb_alignment_required",
                "Choose an understanding or add a clarification.",
            ),
            "alignment_cancel": ui.get("cancel", "Cancel"),
            "blocked_by": ui["field_blocked"],
            "completed_on": ui["field_completed"],
            "context": ui["field_context"],
            "crystallize": ui.get("kb_mark_crystallized", "Mark crystallized"),
            "crystallize_short": ui.get("kb_crystallize_short", "Cry"),
            "crystallized": ui["crystallized"],
            "cancel": ui.get("cancel", "Cancel"),
            "cancel_short": ui.get("kb_cancel_short", "Cancel"),
            "delete_confirm": ui.get(
                "kb_delete_confirm",
                "Delete this task?",
            ),
            "delete_short": ui.get("kb_delete_short", "x"),
            "delete_task": ui["kb_delete_card"],
            "delete_subtask": ui.get("kb_delete_subtask", "Delete subtask"),
            "details": ui["details"],
            "done_uncrystallized": ui.get(
                "kb_done_uncrystallized",
                "Done, not crystallized",
            ),
            "edit": ui.get("kb_edit_task", "Edit"),
            "edit_short": ui.get("kb_edit_short", "Edit"),
            "empty": ui.get("ingest_no_done", "No tasks."),
            "error": ui.get("error", "Error"),
            "links": ui["kb_links_preview"],
            "new_subtask": ui["kb_read_new_subtask_ph"],
            "outcome": ui["field_outcome"],
            "proposals": ui.get("kb_subtask_proposals_title", "AI subtask drafts"),
            "apply_subtasks": ui.get("kb_apply_subtasks", "Apply selected"),
            "discard_draft": ui.get("kb_discard_draft", "Discard draft"),
            "discard_all_drafts": ui.get(
                "kb_discard_all_drafts",
                "Discard all",
            ),
            "no_selected_drafts": ui.get(
                "kb_no_selected_drafts",
                "Select at least one draft to apply.",
            ),
            "draft_status": ui.get("kb_draft_status", "{count} drafts"),
            "alignment_status": ui.get(
                "kb_alignment_status",
                "Understanding ready",
            ),
            "ai_error_status": ui.get("kb_ai_error_status", "AI error"),
            "granularity": ui.get("kb_granularity", "Granularity"),
            "granularity_milestone": ui.get(
                "kb_granularity_milestone",
                "Milestone",
            ),
            "granularity_checklist": ui.get(
                "kb_granularity_checklist",
                "Checklist",
            ),
            "granularity_implementation": ui.get(
                "kb_granularity_implementation",
                "Implementation",
            ),
            "artifact": ui.get("kb_artifact", "Artifact"),
            "gap_preview": ui.get("kb_gap_preview_title", "Task gap preview"),
            "gap_next": ui.get("subheader_next", "Next steps"),
            "gap_ok": ui.get("verdict_ok", "Can solve"),
            "gap_missing": ui.get("verdict_gap", "Gaps remain"),
            "quick_add": ui.get("kb_quick_add", "+ Add task"),
            "save": ui["save"],
            "save_short": ui.get("kb_save_short", "Save"),
            "started_on": ui["field_started"],
            "subtasks": ui["subtasks_label"],
            "title": ui["task_field_title"],
            "untitled": ui.get("kb_title_required", "Untitled"),
            "verification": ui.get("kb_verification", "Verification"),
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
                if proposal.artifact:
                    st.caption(
                        f"{ui.get('kb_artifact', 'Artifact')}: "
                        f"{proposal.artifact}"
                    )
                if proposal.verification:
                    st.caption(
                        f"{ui.get('kb_verification', 'Verification')}: "
                        f"{proposal.verification}"
                    )
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


def _checkin_lines(value: object) -> list[str]:
    """Return non-empty unique lines from text input."""
    out: list[str] = []
    seen: set[str] = set()
    for line in str(value or "").splitlines():
        clean = line.strip()
        if not clean:
            continue
        key = clean.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(clean)
    return out


def _shift_month(year: int, month: int, offset: int) -> tuple[int, int]:
    """Return year/month shifted by whole months."""
    total = year * 12 + (month - 1) + offset
    return total // 12, total % 12 + 1


def _month_state(profile: str) -> tuple[int, int]:
    """Return the toolbar calendar month from session state."""
    today = date.today()
    raw = str(
        st.session_state.get(
            f"kb_toolbar_checkin_month_{profile}",
            f"{today.year:04d}-{today.month:02d}",
        )
    )
    try:
        year_text, month_text = raw[:7].split("-", 1)
        year = int(year_text)
        month = int(month_text)
        date(year, month, 1)
    except (TypeError, ValueError):
        year, month = today.year, today.month
    st.session_state[f"kb_toolbar_checkin_month_{profile}"] = (
        f"{year:04d}-{month:02d}"
    )
    return year, month


def _set_month_state(profile: str, year: int, month: int) -> None:
    """Store the toolbar calendar month."""
    st.session_state[f"kb_toolbar_checkin_month_{profile}"] = (
        f"{year:04d}-{month:02d}"
    )


def _selected_checkin_day(profile: str, payload: dict) -> date:
    """Return the selected toolbar calendar day."""
    day_map = {
        str(day["date"]): day
        for day in payload.get("days", [])
        if isinstance(day, dict)
    }
    selected_key = f"kb_toolbar_checkin_day_{profile}"
    selected_raw = str(st.session_state.get(selected_key, "")).strip()
    today = date.today()
    fallback = (
        today.isoformat()
        if today.isoformat() in day_map
        else next(iter(day_map), today.isoformat())
    )
    selected_iso = selected_raw if selected_raw in day_map else fallback
    st.session_state[selected_key] = selected_iso
    return date.fromisoformat(selected_iso)


def _day_payload(payload: dict, day: date) -> dict:
    """Return one day payload from a month payload."""
    for item in payload.get("days", []):
        if isinstance(item, dict) and item.get("date") == day.isoformat():
            return item
    return {
        "date": day.isoformat(),
        "day": day.day,
        "counts": {"learning": 0, "exercise": 0},
        "records": [],
        "summary": "",
    }


def _month_marker_html(counts: dict, ui: dict[str, str]) -> str:
    """Return compact colored HTML markers for one date cell."""
    learning = int(counts.get("learning") or 0)
    exercise = int(counts.get("exercise") or 0)
    badges: list[str] = []
    if learning:
        text = ui.get("kb_checkin_month_learning_short", "学{count}").format(
            count=learning
        )
        badges.append(
            f'<span class="kb-cal-badge learning">{escape(text)}</span>'
        )
    if exercise:
        text = ui.get("kb_checkin_month_exercise_short", "练{count}").format(
            count=exercise
        )
        badges.append(
            f'<span class="kb-cal-badge exercise">{escape(text)}</span>'
        )
    return "".join(badges)


def _checkin_query_value(name: str) -> str:
    """Return one toolbar check-in query parameter value."""
    try:
        raw = st.query_params.get(name)
    except Exception:
        return ""
    if isinstance(raw, list):
        raw = raw[-1] if raw else ""
    return str(raw or "").strip()


def _checkin_query_href(**updates: str) -> str:
    """Build a same-page link that updates toolbar check-in state."""
    try:
        params = dict(st.query_params)
    except Exception:
        params = {}
    for key in ("kb_ci_month", "kb_ci_day", "kb_ci_open"):
        params.pop(key, None)
    params.update({key: value for key, value in updates.items() if value})
    query = urlencode(params, doseq=True)
    return f"?{query}" if query else "?"


def _sync_checkin_query_state(profile: str) -> None:
    """Apply toolbar check-in query parameters to session state."""
    raw_month = _checkin_query_value("kb_ci_month")
    if raw_month:
        try:
            year_text, month_text = raw_month[:7].split("-", 1)
            year = int(year_text)
            month = int(month_text)
            date(year, month, 1)
        except (TypeError, ValueError):
            pass
        else:
            _set_month_state(profile, year, month)

    raw_day = _checkin_query_value("kb_ci_day")
    if raw_day:
        try:
            selected = date.fromisoformat(raw_day)
        except ValueError:
            pass
        else:
            st.session_state[f"kb_toolbar_checkin_day_{profile}"] = (
                selected.isoformat()
            )

    raw_open = _checkin_query_value("kb_ci_open")
    if raw_open:
        st.session_state[f"kb_toolbar_checkin_detail_open_{profile}"] = (
            raw_open == "1"
        )


def _month_calendar_html(
    profile: str,
    payload: dict,
    selected_day: date,
    today: date,
    ui: dict[str, str],
) -> str:
    """Return the compact toolbar month calendar HTML."""
    year = int(payload["year"])
    month = int(payload["month"])
    prev_year, prev_month = _shift_month(year, month, -1)
    next_year, next_month = _shift_month(year, month, 1)
    prev_month_label = f"{prev_year:04d}-{prev_month:02d}"
    next_month_label = f"{next_year:04d}-{next_month:02d}"
    today_month_label = f"{today.year:04d}-{today.month:02d}"
    prev_href = _checkin_query_href(
        kb_ci_month=prev_month_label,
        kb_ci_day=f"{prev_month_label}-01",
        kb_ci_open="0",
    )
    next_href = _checkin_query_href(
        kb_ci_month=next_month_label,
        kb_ci_day=f"{next_month_label}-01",
        kb_ci_open="0",
    )
    today_href = _checkin_query_href(
        kb_ci_month=today_month_label,
        kb_ci_day=today.isoformat(),
        kb_ci_open="0",
    )
    title = escape(str(payload.get("month_label") or f"{year:04d}-{month:02d}"))
    profile_label = escape(profile)

    weekday_cells = "".join(
        f'<span class="kb-cal-weekday">{escape(str(weekday))}</span>'
        for weekday in payload.get("weekdays", [])
    )
    day_cells: list[str] = []
    selected_iso = selected_day.isoformat()
    for item in payload.get("days", []):
        if not isinstance(item, dict):
            day_cells.append('<span class="kb-cal-cell kb-cal-empty"></span>')
            continue
        day_iso = str(item.get("date") or "")
        day_href = _checkin_query_href(
            kb_ci_month=f"{year:04d}-{month:02d}",
            kb_ci_day=day_iso,
            kb_ci_open="1",
        )
        classes = ["kb-cal-cell", "kb-cal-day"]
        if day_iso == selected_iso:
            classes.append("selected")
        if item.get("is_today"):
            classes.append("today")
        counts = item.get("counts") or {}
        if int(counts.get("learning") or 0):
            classes.append("has-learning")
        if int(counts.get("exercise") or 0):
            classes.append("has-exercise")
        marker_html = _month_marker_html(counts, ui)
        count_title = escape(str(item.get("summary") or ""))
        day_title = escape(
            f"{day_iso} {item.get('summary') or ''}".strip()
        )
        day_cells.append(
            '<a class="'
            + " ".join(classes)
            + f'" href="{escape(day_href, quote=True)}"'
            + f' title="{day_title}" aria-label="{day_title}">'
            + f'<span class="kb-cal-num">{escape(str(item.get("day") or ""))}</span>'
            + f'<span class="kb-cal-badges" title="{count_title}">'
            + marker_html
            + "</span></a>"
        )

    return (
        f'<div class="kb-cal-mini" data-profile="{profile_label}">'
        '<div class="kb-cal-nav">'
        f'<a class="kb-cal-nav-btn" href="{escape(prev_href, quote=True)}" '
        'aria-label="Previous month">‹</a>'
        f'<a class="kb-cal-title" href="{escape(today_href, quote=True)}" '
        f'title="{escape(ui.get("kb_checkin_today_short", "Today"))}" '
        f'aria-label="{escape(ui.get("kb_checkin_today_short", "Today"))}">'
        f"{title}</a>"
        f'<a class="kb-cal-nav-btn" href="{escape(next_href, quote=True)}" '
        'aria-label="Next month">›</a>'
        "</div>"
        f'<div class="kb-cal-grid kb-cal-weekdays">{weekday_cells}</div>'
        '<div class="kb-cal-grid kb-cal-days">'
        + "".join(day_cells)
        + "</div></div>"
    )


def _render_month_calendar_styles() -> None:
    """Inject compact styles for the toolbar month calendar."""
    st.markdown(
        """
        <style>
        .kb-cal-mini {
          aspect-ratio: 2 / 1;
          box-sizing: border-box;
          display: grid;
          gap: 2px;
          grid-template-rows: 1.55rem 1.05rem minmax(0, 1fr);
          margin: 0;
          min-height: 0;
          overflow: hidden;
          width: 100%;
        }
        .kb-cal-nav {
          align-items: center;
          display: grid;
          gap: 2px;
          grid-template-columns: 2rem minmax(0, 1fr) 2rem;
          min-height: 0;
        }
        .kb-cal-nav-btn {
          align-items: center;
          background: #f8fafc;
          border: 1px solid #e2e8f0;
          border-radius: 5px;
          color: #334155;
          display: flex;
          font-size: 2rem;
          font-weight: 900;
          height: 1.45rem;
          justify-content: center;
          line-height: 0.75;
          overflow: hidden;
          text-decoration: none;
          white-space: nowrap;
        }
        .kb-cal-nav-btn:hover {
          background: #eef2ff;
          border-color: #c7d2fe;
          color: #1d4ed8;
          text-decoration: none;
        }
        .kb-cal-title {
          color: #0f172a;
          font-size: 1.08rem;
          font-weight: 900;
          line-height: 1.55rem;
          overflow: hidden;
          text-align: center;
          text-overflow: ellipsis;
          text-decoration: none;
          white-space: nowrap;
        }
        .kb-cal-title:hover {
          color: #1d4ed8;
          text-decoration: none;
        }
        .kb-cal-grid {
          display: grid;
          gap: 1px;
          grid-template-columns: repeat(7, minmax(0, 1fr));
          min-height: 0;
        }
        .kb-cal-weekday {
          color: #64748b;
          font-size: 1rem;
          font-weight: 900;
          line-height: 1.05rem;
          min-width: 0;
          overflow: hidden;
          text-align: center;
        }
        .kb-cal-days {
          grid-template-rows: repeat(6, minmax(0, 1fr));
        }
        .kb-cal-cell {
          min-height: 0;
          min-width: 0;
        }
        .kb-cal-day {
          background: #ffffff;
          border: 1px solid #e5e7eb;
          border-radius: 3px;
          color: #334155;
          display: block;
          overflow: hidden;
          position: relative;
          text-decoration: none;
        }
        .kb-cal-day:hover {
          background: #f8fafc;
          border-color: #94a3b8;
          color: #0f172a;
          text-decoration: none;
        }
        .kb-cal-day.selected {
          background: #eef2ff;
          border-color: #4f46e5;
          color: #312e81;
        }
        .kb-cal-day.today .kb-cal-num {
          color: #be123c;
          font-weight: 900;
        }
        .kb-cal-day.has-learning,
        .kb-cal-day.has-exercise {
          background: #fbfdff;
          border-color: #cbd5e1;
        }
        .kb-cal-day.has-learning.has-exercise {
          background: linear-gradient(135deg, #eff6ff 0%, #f0fdf4 100%);
        }
        .kb-cal-day.selected.has-learning,
        .kb-cal-day.selected.has-exercise {
          background: #eef2ff;
          border-color: #4f46e5;
        }
        .kb-cal-num {
          align-items: center;
          display: flex;
          font-size: 0.78rem;
          font-weight: 900;
          height: 50%;
          justify-content: center;
          left: 0;
          line-height: 1;
          position: absolute;
          top: 0;
          width: 50%;
        }
        .kb-cal-badges {
          inset: 0;
          min-height: 0;
          pointer-events: none;
          position: absolute;
        }
        .kb-cal-badge {
          align-items: center;
          border: 1px solid transparent;
          border-radius: 0;
          box-sizing: border-box;
          display: flex;
          font-size: 0.62rem;
          font-weight: 900;
          height: 50%;
          justify-content: center;
          line-height: 1;
          max-width: none;
          overflow: hidden;
          padding: 0;
          position: absolute;
          text-overflow: clip;
          white-space: nowrap;
          width: 50%;
        }
        .kb-cal-badge.learning {
          background: #bfdbfe;
          border-color: #93c5fd;
          color: #1e40af;
          right: 0;
          top: 0;
        }
        .kb-cal-badge.exercise {
          background: #bbf7d0;
          border-color: #86efac;
          color: #166534;
          bottom: 0;
          right: 0;
        }
        .st-key-kb_toolbar_checkin_calendar {
          container-type: inline-size;
          margin: 0;
          min-height: 0;
          overflow: hidden;
          padding: 0;
        }
        .st-key-kb_toolbar_checkin_calendar [data-testid="stElementContainer"],
        .st-key-kb_toolbar_checkin_calendar [data-testid="stMarkdownContainer"],
        .st-key-kb_toolbar_checkin_calendar [data-testid="stVerticalBlock"] {
          gap: 0;
          margin: 0;
          min-height: 0;
          padding: 0;
        }
        .st-key-kb_toolbar_checkin_calendar [data-testid="stMarkdownContainer"] p {
          margin: 0;
        }
        .st-key-kb_toolbar_checkin_detail {
          margin-top: 0.25rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_checkin_records(
    profile: str,
    profile_path,
    selected_payload: dict,
    ui: dict[str, str],
) -> None:
    """Render records for the selected calendar day."""
    records = selected_payload.get("records") or []
    st.caption(
        selected_payload.get("summary")
        or ui.get("kb_checkin_no_marks", "No marks")
    )
    if not records:
        st.caption(
            ui.get(
                "kb_checkin_day_records_empty",
                "No learning/exercise records on this day.",
            )
        )
        return

    for index, record in enumerate(records):
        item = record if isinstance(record, dict) else {}
        cols = st.columns([0.85, 2.2, 0.55], gap="small")
        cols[0].caption(str(item.get("label") or ""))
        cols[1].caption(str(item.get("detail") or ""))
        can_delete = bool(item.get("can_delete") and item.get("id"))
        if cols[2].button(
            "x",
            key=(
                f"kb_toolbar_checkin_delete_{profile}_"
                f"{item.get('id') or index}"
            ),
            help=ui.get("kb_checkin_delete", "Delete"),
            disabled=not can_delete,
        ):
            deleted = delete_workspace_checkin(profile_path, str(item["id"]))
            if not deleted:
                st.warning(
                    ui.get(
                        "kb_checkin_delete_missing",
                        "That check-in was already gone.",
                    )
                )
                return
            st.rerun()


def _render_add_learning_form(
    profile: str,
    profile_path,
    selected_day: date,
    ui: dict[str, str],
) -> None:
    """Render the selected-day learning check-in form."""
    with st.form(
        f"kb_toolbar_learning_form_{profile}_{selected_day.isoformat()}",
        clear_on_submit=True,
    ):
        note = st.text_area(
            ui.get("kb_learning_checkin_note", "Learning note"),
            key=f"kb_toolbar_learning_note_{profile}_{selected_day.isoformat()}",
            height=76,
            placeholder=ui.get(
                "kb_learning_checkin_note_placeholder",
                "What did you study, and what is worth remembering?",
            ),
        )
        links_text = st.text_area(
            ui.get("kb_learning_checkin_links", "Links"),
            key=f"kb_toolbar_learning_links_{profile}_{selected_day.isoformat()}",
            height=58,
            placeholder=ui.get(
                "kb_learning_checkin_links_placeholder",
                "One link per line.",
            ),
        )
        submitted = st.form_submit_button(
            ui.get("kb_checkin_add_learning", "Add learning"),
            type="primary",
            use_container_width=True,
        )
    if not submitted:
        return
    links = _checkin_lines(links_text)
    if not str(note or "").strip() and not links:
        st.warning(
            ui.get(
                "kb_learning_checkin_required",
                "Add a note or at least one link.",
            )
        )
        return
    record_learning_checkin(
        profile_path,
        when=selected_day,
        note=str(note or "").strip(),
        links=links,
    )
    st.rerun()


def _render_add_exercise_form(
    profile: str,
    profile_path,
    selected_day: date,
    ui: dict[str, str],
) -> None:
    """Render the selected-day exercise check-in form."""
    with st.form(
        f"kb_toolbar_exercise_form_{profile}_{selected_day.isoformat()}",
        clear_on_submit=True,
    ):
        duration_min = st.number_input(
            ui.get("kb_exercise_duration", "Duration (min)"),
            key=f"kb_toolbar_exercise_duration_{profile}_{selected_day.isoformat()}",
            min_value=0.0,
            step=5.0,
            value=0.0,
        )
        note = st.text_area(
            ui.get("kb_capture_note", "Note"),
            key=f"kb_toolbar_exercise_note_{profile}_{selected_day.isoformat()}",
            height=58,
        )
        submitted = st.form_submit_button(
            ui.get("kb_checkin_add_exercise", "Add exercise"),
            type="primary",
            use_container_width=True,
        )
    if not submitted:
        return
    record_exercise_checkin(
        profile_path,
        when=selected_day,
        workout_type="other",
        duration_min=float(duration_min or 0.0),
        intensity="moderate",
        note=str(note or "").strip(),
    )
    st.rerun()


def _render_toolbar_checkin(
    profile: str,
    profile_path,
    ui: dict[str, str],
) -> None:
    """Render the compact top-right month check-in calendar."""
    _render_month_calendar_styles()
    _sync_checkin_query_state(profile)
    today = date.today()
    year, month = _month_state(profile)
    payload = checkin_month_payload(
        profile,
        profile_path,
        ui,
        year=year,
        month=month,
    )
    selected_day = _selected_checkin_day(profile, payload)
    selected_payload = _day_payload(payload, selected_day)
    detail_key = f"kb_toolbar_checkin_detail_open_{profile}"

    with st.container(key="kb_toolbar_checkin_calendar"):
        st.markdown(
            _month_calendar_html(profile, payload, selected_day, today, ui),
            unsafe_allow_html=True,
        )

    if not st.session_state.get(detail_key):
        return

    with st.container(key="kb_toolbar_checkin_detail"):
        title_col, close_col = st.columns(
            [1, 0.28],
            gap="small",
            vertical_alignment="center",
        )
        title_col.markdown(f"**{selected_day.isoformat()}**")
        if close_col.button(
            "x",
            key=f"kb_toolbar_checkin_close_{profile}",
            help=ui.get("kb_checkin_close_detail", "Hide details"),
            use_container_width=True,
        ):
            st.session_state[detail_key] = False
            try:
                st.query_params["kb_ci_open"] = "0"
            except Exception:
                pass
            st.rerun()
        _render_checkin_records(profile, profile_path, selected_payload, ui)
        with st.expander(
            ui.get("kb_checkin_add_learning", "Add learning"),
            expanded=False,
        ):
            _render_add_learning_form(profile, profile_path, selected_day, ui)
        with st.expander(
            ui.get("kb_checkin_add_exercise", "Add exercise"),
            expanded=False,
        ):
            _render_add_exercise_form(profile, profile_path, selected_day, ui)


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
            if auto_dates:
                task = replace(task, completed_on=date.today().isoformat())
        if section == KANBAN_DOING and auto_dates:
            task = replace(task, started_on=date.today().isoformat())
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
        subtask_index = _event_subtask_index(payload, task)
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

    if action == "delete_subtask":
        if found is None:
            st.warning(ui["kb_drag_stale"])
            return
        section, idx, task = found
        subtask_index = _event_subtask_index(payload, task)
        if not 0 <= subtask_index < len(task.subtasks):
            return
        next_subtasks = list(task.subtasks)
        next_subtasks.pop(subtask_index)
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
        st.rerun()
        return

    if action in ("request_subtasks", "ai_subtask_ingest"):
        if found is None:
            st.warning(ui["kb_drag_stale"])
            return
        if not llm_client.is_configured():
            render_llm_unavailable(ui)
            return
        with st.spinner(ui.get("spinner_ai", "AI reasoning...")):
            alignments = generate_kanban_task_alignment_options(
                sections,
                task_id,
                profile_name=profile,
            )
        if not alignments:
            st.warning(
                ui.get(
                    "kb_no_alignment_options",
                    "No task understanding options were generated.",
                )
            )
            return
        alignments_by_task = st.session_state.setdefault(
            _subtask_alignments_key(profile),
            {},
        )
        alignments_by_task[task_id] = alignments
        proposals_by_task = st.session_state.get(
            _subtask_proposals_key(profile),
            {},
        )
        errors_by_task = st.session_state.get(
            _subtask_errors_key(profile),
            {},
        )
        _discard_task_ai_state(
            proposals_by_task,
            None,
            errors_by_task,
            task_id,
            scope="drafts",
        )
        if isinstance(errors_by_task, dict):
            errors_by_task.pop(task_id, None)
        st.rerun()
        return

    if action == "confirm_subtask_alignment":
        if found is None:
            st.warning(ui["kb_drag_stale"])
            return
        if not llm_client.is_configured():
            render_llm_unavailable(ui)
            return
        alignment_context = _alignment_context_from_payload(payload)
        if not alignment_context:
            st.warning(
                ui.get(
                    "kb_alignment_required",
                    "Choose an understanding or add a clarification.",
                )
            )
            return
        with st.spinner(ui.get("spinner_ai", "AI reasoning...")):
            result = generate_kanban_subtask_proposals_detailed(
                profile,
                sections,
                task_id,
                use_rule_match=True,
                use_llm_router=True,
                persist_router_keywords=False,
                alignment_context=alignment_context,
                granularity=str(payload.get("granularity") or "milestone"),
            )
        if not result.proposals:
            state = st.session_state.setdefault(_subtask_errors_key(profile), {})
            state[task_id] = result
            st.warning(_subtask_error_message(result, ui))
            st.rerun()
            return
        state = st.session_state.setdefault(
            _subtask_proposals_key(profile),
            {},
        )
        state[task_id] = result.proposals
        errors_by_task = st.session_state.get(
            _subtask_errors_key(profile),
            {},
        )
        if isinstance(errors_by_task, dict):
            errors_by_task.pop(task_id, None)
        alignments_by_task = st.session_state.get(
            _subtask_alignments_key(profile),
            {},
        )
        if isinstance(alignments_by_task, dict):
            alignments_by_task.pop(task_id, None)
        st.rerun()
        return

    if action == "cancel_subtask_alignment":
        alignments_by_task = st.session_state.get(
            _subtask_alignments_key(profile),
            {},
        )
        if isinstance(alignments_by_task, dict):
            alignments_by_task.pop(task_id, None)
        st.rerun()
        return

    if action == "discard_subtask_draft":
        proposals_by_task = st.session_state.get(
            _subtask_proposals_key(profile),
            {},
        )
        try:
            index = int(payload.get("index", payload.get("draft_index", -1)))
        except (TypeError, ValueError):
            index = -1
        if isinstance(proposals_by_task, dict):
            _discard_subtask_proposal_at(proposals_by_task, task_id, index)
        st.rerun()
        return

    if action == "discard_subtask_drafts":
        proposals_by_task = st.session_state.get(
            _subtask_proposals_key(profile),
            {},
        )
        errors_by_task = st.session_state.get(
            _subtask_errors_key(profile),
            {},
        )
        _discard_task_ai_state(
            proposals_by_task,
            None,
            errors_by_task,
            task_id,
            scope="drafts",
        )
        st.rerun()
        return

    if action == "discard_ai_generation":
        proposals_by_task = st.session_state.get(
            _subtask_proposals_key(profile),
            {},
        )
        alignments_by_task = st.session_state.get(
            _subtask_alignments_key(profile),
            {},
        )
        errors_by_task = st.session_state.get(
            _subtask_errors_key(profile),
            {},
        )
        _discard_task_ai_state(
            proposals_by_task,
            alignments_by_task,
            errors_by_task,
            task_id,
            scope="all",
        )
        st.rerun()
        return

    if action == "apply_subtasks":
        if found is None:
            st.warning(ui["kb_drag_stale"])
            return
        section, idx, task = found
        proposals = _subtask_proposals_from_payload(payload, task_id)
        if not proposals:
            st.warning(
                ui.get(
                    "kb_no_selected_drafts",
                    "Select at least one draft to apply.",
                )
            )
            return
        card = payload.get("card")
        if isinstance(card, dict):
            updated_task = _apply_task_update(task, card)
            if updated_task is None:
                st.warning(ui["kb_title_required"])
                return
            sections[section][idx] = updated_task
        updated = apply_kanban_subtask_proposals(
            sections,
            task_id,
            proposals,
        )
        sections.clear()
        sections.update(updated)
        _auto_save(profile, sections)
        proposals_by_task = st.session_state.get(
            _subtask_proposals_key(profile),
            {},
        )
        if isinstance(proposals_by_task, dict):
            proposals_by_task.pop(task_id, None)
        alignments_by_task = st.session_state.get(
            _subtask_alignments_key(profile),
            {},
        )
        if isinstance(alignments_by_task, dict):
            alignments_by_task.pop(task_id, None)
        errors_by_task = st.session_state.get(
            _subtask_errors_key(profile),
            {},
        )
        _discard_task_ai_state(
            proposals_by_task,
            alignments_by_task,
            errors_by_task,
            task_id,
            scope="all",
        )
        st.rerun()
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
_activity_path = _pdir / "activity-log.yaml"
for _path in (
    _kanban_path,
    _archive_path,
    _pool_path,
    _tree_path,
    _skill_path,
    _activity_path,
):
    ensure_file_snapshot(_path)

# -- Header / Toolbar -------------------------------------------

header_left, header_calendar = st.columns(
    [3, 1],
    gap="medium",
    vertical_alignment="top",
)
with header_left:
    st.title(ui["title"])
    st.caption(ui["page_context_line"])
    settings_col, _spacer_col = st.columns(
        [2, 1],
        gap="small",
        vertical_alignment="bottom",
    )
    with settings_col:
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
        actions_col, _actions_spacer = st.columns(
            [1, 2],
            gap="small",
            vertical_alignment="bottom",
        )
        with actions_col:
            reload_col, save_col = st.columns(
                [1, 1],
                gap="small",
                vertical_alignment="bottom",
            )
            with reload_col:
                if st.button(ui["reload"], use_container_width=True):
                    _load_into_state(selected)
                    _clear_kanban_dirty(selected)
                    _bump_kanban_widget_epoch(selected)
                    refresh_file_snapshots([_kanban_path, _activity_path])
                    st.rerun()
            with save_col:
                if st.button(
                    ui["save"],
                    type="primary",
                    use_container_width=True,
                ):
                    sections = _get_sections(selected)
                    _auto_save(selected, sections)
                    st.success(ui["saved"])
        if _kanban_is_dirty(selected):
            st.caption(ui["kb_unsaved_subtasks"])
with header_calendar:
    _render_toolbar_checkin(selected, _pdir, ui)

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
    ai_state=_board_ai_state(selected, ui),
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
