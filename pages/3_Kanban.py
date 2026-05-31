"""Kanban -- visual task board editor for kanban.md.

Primary persist actions use the toolbar **Reload** / **Save** pattern.
Skill Tree uses a title-row **Save** instead; see docs/zh/product/web-experience.md.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from html import escape
from urllib.parse import urlparse

import streamlit as st
from nblane.checkin_calendar_component import st_checkin_calendar
from nblane.core import codex_adapter
from nblane.core import gap as gap_engine
from nblane.core import llm as llm_client
from nblane.core.file_state import (
    FileConflictError,
    assert_unchanged,
    snapshot_file,
)
from nblane.core.kanban_io import (
    KANBAN_BOARD_SECTIONS,
    apply_kanban_reorder,
    ensure_kanban_task_ids,
    kanban_snapshot_to_moves,
)
from nblane.core.kanban_events import (
    alignment_context_from_payload as _alignment_context_from_payload,
    append_ai_proposal_details as _append_ai_proposal_details,
    apply_kanban_card_update as _apply_task_update,
    discard_subtask_proposal_at as _discard_subtask_proposal_at,
    discard_task_ai_state as _discard_task_ai_state,
    event_subtask_index as _event_subtask_index,
    invalid_kanban_card_date_fields as _invalid_card_date_fields,
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
    archive_kanban_done_tasks,
    parse_kanban,
    profile_dir,
    save_kanban,
)
from nblane.kanban_board_component import st_kanban_board
from nblane.kanban_ui import render_kanban_board
from nblane.kanban_ui.personal_workspace import (
    EXERCISE_INTENSITIES,
    EXERCISE_TYPES,
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
from nblane.core.project_board import load_project_board
from nblane.core.project_board_sync import (
    sync_project_board_from_kanban,
)
from nblane.web_cache import (
    clear_web_cache,
)
from nblane.core.web_preferences import (
    AI_ACTION_DEFAULT_BACKENDS,
    load_web_preferences,
    update_web_preferences,
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
    current_goal_agent_context,
    ensure_file_snapshot,
    refresh_file_snapshots,
    render_current_goal_strip,
    render_git_backup_notices,
    render_page_help,
    kanban_ai_backend,
    kanban_ai_backend_key,
    kanban_ai_suffix,
    select_profile,
    stash_git_backup_results,
    ui_emoji_enabled,
)

apply_ui_language_from_session()

_KANBAN_AI_ACTIONS: tuple[tuple[str, str, str], ...] = (
    (
        "kanban.task_alignment",
        "kb_ai_action_task_alignment",
        "kb_ai_action_task_alignment_help",
    ),
    (
        "kanban.subtasks",
        "kb_ai_action_subtasks",
        "kb_ai_action_subtasks_help",
    ),
)
_KANBAN_AI_BACKENDS = ("llm", "codex")


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
    project_path = profile_dir(profile) / "project-board.yaml"
    assert_files_current([path, project_path])
    ensured = ensure_kanban_task_ids(sections, profile)
    sections.clear()
    sections.update(ensured)
    save_kanban(profile, sections)
    sync_project_board_from_kanban(profile, sections)
    refresh_file_snapshots([path, project_path])
    stash_git_backup_results()
    clear_web_cache()
    _clear_kanban_dirty(profile)


def _sync_kanban_sections_state(
    profile: str,
    sections: dict[str, list[KanbanTask]],
    latest_sections: dict[str, list[KanbanTask]],
) -> None:
    """Replace in-memory board state with the supplied latest sections."""
    ensured = ensure_kanban_task_ids(latest_sections, profile)
    sections.clear()
    sections.update(ensured)
    st.session_state[_state_key(profile)] = sections


def _copy_task_for_subtask_toggle(task: KanbanTask) -> KanbanTask:
    """Return a task copy with child lists detached for local merging."""
    return replace(
        task,
        subtasks=[replace(item) for item in task.subtasks],
        details=list(task.details),
    )


def _apply_subtask_toggle_for_page(
    sections: dict[str, list[KanbanTask]],
    task_id: str,
    subtask_index: int,
    subtask_title: str,
    done: bool,
) -> tuple[dict[str, list[KanbanTask]], bool]:
    """Merge one subtask checkbox without requiring a freshly reloaded module."""
    out = {
        section: [_copy_task_for_subtask_toggle(task) for task in tasks]
        for section, tasks in sections.items()
    }
    wanted_task_id = str(task_id or "").strip()
    wanted_title = str(subtask_title or "").strip()
    if not wanted_task_id or not wanted_title:
        return out, False

    for section, tasks in out.items():
        for task_pos, task in enumerate(tasks):
            if str(task.id or "").strip() != wanted_task_id:
                continue

            target_index = -1
            if 0 <= subtask_index < len(task.subtasks):
                current = task.subtasks[subtask_index]
                if str(current.title or "").strip() == wanted_title:
                    target_index = subtask_index

            if target_index < 0:
                matches = [
                    idx
                    for idx, item in enumerate(task.subtasks)
                    if str(item.title or "").strip() == wanted_title
                ]
                if len(matches) == 1:
                    target_index = matches[0]

            if target_index < 0:
                return out, False

            next_subtasks = list(task.subtasks)
            next_subtasks[target_index] = replace(
                next_subtasks[target_index],
                done=bool(done),
            )
            tasks[task_pos] = replace(task, subtasks=next_subtasks)
            out[section] = tasks
            return out, True

    return out, False


def _auto_save_subtask_toggle(
    profile: str,
    sections: dict[str, list[KanbanTask]],
    task_id: str,
    subtask_index: object,
    subtask_title: str,
    done: bool,
    ui: dict[str, str],
) -> bool:
    """Persist one read-mode subtask checkbox against latest kanban.md."""
    path = profile_dir(profile) / "kanban.md"
    for attempt in range(2):
        before = snapshot_file(path)
        latest_sections = ensure_kanban_task_ids(
            parse_kanban(profile),
            profile,
        )
        try:
            index = int(subtask_index)
        except (TypeError, ValueError):
            index = -1
        updated_sections, ok = _apply_subtask_toggle_for_page(
            latest_sections,
            task_id,
            index,
            subtask_title,
            done,
        )
        if not ok:
            _sync_kanban_sections_state(profile, sections, latest_sections)
            refresh_file_snapshots([path])
            st.warning(ui["kb_drag_stale"])
            return False
        if updated_sections == latest_sections:
            _sync_kanban_sections_state(profile, sections, latest_sections)
            refresh_file_snapshots([path])
            clear_web_cache()
            _clear_kanban_dirty(profile)
            return True
        try:
            assert_unchanged(path, before, label=path.name)
        except FileConflictError:
            if attempt == 0:
                continue
            latest_sections = ensure_kanban_task_ids(
                parse_kanban(profile),
                profile,
            )
            _sync_kanban_sections_state(profile, sections, latest_sections)
            refresh_file_snapshots([path])
            st.warning(ui["kb_drag_stale"])
            return False

        save_kanban(profile, updated_sections)
        refresh_file_snapshots([path])
        stash_git_backup_results()
        clear_web_cache()
        _clear_kanban_dirty(profile)
        _sync_kanban_sections_state(profile, sections, updated_sections)
        return True
    return False


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
    return f"kanban_subtask_proposals_{profile}_{kanban_ai_suffix(profile)}"


def _subtask_alignments_key(profile: str) -> str:
    """Session key for per-task task-understanding alignment options."""
    return f"kanban_subtask_alignments_{profile}_{kanban_ai_suffix(profile)}"


def _subtask_errors_key(profile: str) -> str:
    """Session key for per-task AI subtask generation diagnostics."""
    return f"kanban_subtask_errors_{profile}_{kanban_ai_suffix(profile)}"


def _kanban_preferences(profile: str) -> dict:
    """Return normalized Kanban Web preferences."""
    prefs = load_web_preferences(profile)
    kanban = prefs.get("kanban") if isinstance(prefs.get("kanban"), dict) else {}
    return kanban if isinstance(kanban, dict) else {}


def _kanban_subtask_granularity(profile: str) -> str:
    """Return the remembered subtask draft granularity for this profile."""
    value = str(
        _kanban_preferences(profile).get("subtask_granularity") or "milestone"
    ).strip()
    return value if value in {"milestone", "checklist", "implementation"} else "milestone"


def _kanban_subtask_style_hint(profile: str) -> str:
    """Return the remembered subtask style hint for this profile."""
    return str(_kanban_preferences(profile).get("subtask_style_hint") or "").strip()


def _persist_kanban_subtask_preferences(
    profile: str,
    *,
    granularity: str,
    style_hint: str,
) -> None:
    """Persist non-secret Kanban AI drafting preferences."""
    update_web_preferences(
        profile,
        {
            "kanban": {
                "subtask_granularity": granularity,
                "subtask_style_hint": style_hint,
            }
        },
    )


def _kanban_ai_action_prefs(profile: str) -> dict[str, dict[str, str]]:
    """Return profile-scoped Kanban AI action preferences."""

    prefs = load_web_preferences(profile)
    ai = prefs.get("ai") if isinstance(prefs.get("ai"), dict) else {}
    actions = ai.get("actions") if isinstance(ai.get("actions"), dict) else {}
    return {
        name: dict(value)
        for name, value in actions.items()
        if isinstance(value, dict)
    }


def _kanban_backend_label(value: str, ui: dict[str, str]) -> str:
    return ui.get(f"kb_ai_backend_{value}", value.upper())


def _kanban_effective_backend(action_name: str, config: dict[str, str]) -> str:
    configured = str(config.get("backend") or "").strip()
    if configured in _KANBAN_AI_BACKENDS:
        return configured
    default = AI_ACTION_DEFAULT_BACKENDS.get(action_name, "llm")
    return default if default in _KANBAN_AI_BACKENDS else "llm"


def _render_kanban_ai_settings(profile: str, ui: dict[str, str]) -> None:
    """Render page-level Kanban AI routing and model preferences."""

    prefs = _kanban_ai_action_prefs(profile)
    llm_cfg = llm_client.current_config(mask_key=True)
    llm_default = str(llm_cfg.get("model") or "").strip()
    codex_cfg = codex_adapter.current_config(profile=profile)
    codex_default = str(codex_cfg.model or "").strip()
    codex_status = codex_adapter.codex_status(
        replace(
            codex_cfg,
            timeout_seconds=min(float(codex_cfg.timeout_seconds or 8.0), 8.0),
        )
    )

    st.caption(
        ui.get(
            "kb_ai_settings_caption",
            "These preferences only affect Kanban AI actions for the current profile.",
        )
    )
    status_cols = st.columns(2)
    with status_cols[0]:
        st.caption(
            ui.get("kb_ai_llm_status", "LLM: {status} · {model}").format(
                status=ui.get("kb_ai_configured", "configured")
                if llm_cfg.get("configured")
                else ui.get("kb_ai_missing_key", "missing key"),
                model=llm_default or ui.get("missing", "missing"),
            )
        )
    with status_cols[1]:
        codex_bits = [
            ui.get("kb_ai_installed", "installed")
            if codex_status.installed
            else ui.get("kb_ai_missing", "missing"),
            ui.get("kb_ai_logged_in", "logged in")
            if codex_status.logged_in
            else ui.get("kb_ai_login_unknown", "login unknown"),
            codex_default or ui.get("kb_ai_codex_default", "Codex CLI default"),
        ]
        st.caption(
            ui.get("kb_ai_codex_status", "Codex: {status}").format(
                status=" · ".join(codex_bits)
            )
        )
        if codex_status.error:
            st.caption(codex_status.error)

    next_actions: dict[str, dict[str, str]] = {}
    with st.form(f"kanban_ai_settings:{profile}", border=False):
        for action_name, label_key, help_key in _KANBAN_AI_ACTIONS:
            current = prefs.get(action_name, {})
            default_backend = _kanban_effective_backend(action_name, current)
            st.markdown(f"**{ui.get(label_key, action_name)}**")
            st.caption(ui.get(help_key, "Choose the engine and optional model override."))
            cols = st.columns([1, 1.25, 1.25], gap="small")
            with cols[0]:
                backend = st.selectbox(
                    ui.get("kb_ai_config_backend", "Backend"),
                    list(_KANBAN_AI_BACKENDS),
                    index=list(_KANBAN_AI_BACKENDS).index(default_backend),
                    format_func=lambda value: _kanban_backend_label(value, ui),
                    key=f"kanban_ai:{profile}:{action_name}:backend",
                )
            with cols[1]:
                llm_model = st.text_input(
                    ui.get("kb_ai_config_llm_model", "LLM model override"),
                    value=str(current.get("llm_model") or ""),
                    placeholder=llm_default or ui.get("kb_ai_app_default", "app default"),
                    help=ui.get(
                        "kb_ai_config_model_help",
                        "Leave blank to use the global/default model.",
                    ),
                    key=f"kanban_ai:{profile}:{action_name}:llm_model",
                ).strip()
            with cols[2]:
                codex_model = st.text_input(
                    ui.get("kb_ai_config_codex_model", "Codex model override"),
                    value=str(current.get("codex_model") or ""),
                    placeholder=codex_default
                    or ui.get("kb_ai_codex_default", "Codex CLI default"),
                    help=ui.get(
                        "kb_ai_config_model_help",
                        "Leave blank to use the global/default model.",
                    ),
                    key=f"kanban_ai:{profile}:{action_name}:codex_model",
                ).strip()
            if backend == "codex":
                effective_model = codex_model or codex_default
            else:
                effective_model = llm_model or llm_default
            st.caption(
                ui.get(
                    "kb_ai_effective_config",
                    "Effective: {backend} · {model}",
                ).format(
                    backend=_kanban_backend_label(backend, ui),
                    model=effective_model
                    or ui.get("kb_ai_app_default", "app default"),
                )
            )
            next_actions[action_name] = {
                "backend": backend,
                "llm_model": llm_model,
                "codex_model": codex_model,
            }

        if st.form_submit_button(
            ui.get("kb_ai_save", "Save AI preferences"),
            type="primary",
            use_container_width=True,
        ):
            kanban_backend = next_actions.get("kanban.subtasks", {}).get("backend") or "llm"
            st.session_state[kanban_ai_backend_key(profile)] = kanban_backend
            update_web_preferences(
                profile,
                {
                    "ai": {
                        "kanban_backend": kanban_backend,
                        "actions": next_actions,
                    }
                },
            )
            clear_web_cache()
            st.success(ui.get("kb_ai_saved", "Kanban AI preferences saved."))
            st.rerun()


def _style_hint_from_alignment_payload(payload: dict) -> str:
    """Extract a compact reusable style hint from an alignment event."""
    hints: list[str] = []
    for item in payload.get("selected_alignments") or []:
        if not isinstance(item, dict):
            continue
        for key in ("subtask_style", "goal"):
            value = str(item.get(key) or "").strip()
            if value and value not in hints:
                hints.append(value)
    custom = str(payload.get("custom_context") or "").strip()
    if custom and custom not in hints:
        hints.append(custom)
    return "\n".join(hints)[:1000]


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
        "tags": task.tags,
        "started_on": task.started_on or "",
        "completed_on": task.completed_on or "",
        "crystallized": task.crystallized,
        "project_id": task.project_id,
        "milestone_id": task.milestone_id,
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
        "activity_item_id": result.activity_item_id,
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
    ai_backend = kanban_ai_backend(profile)
    if ai_backend == "codex":
        status = ui.get("kb_ai_backend_codex_status", "Codex: read-only local")
    else:
        status = (
            ui["llm_configured"].format(label=llm_client.model_label())
            if llm_client.is_configured()
            else ui["ai_not_configured"]
        )
    return {
        "status": status,
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


def _project_options_payload(profile: str) -> list[dict]:
    """Return active/paused project choices for the board editor."""
    board = load_project_board(profile)
    options: list[dict] = []
    for case in board.project_cases:
        if not case.id or case.status not in ("active", "paused"):
            continue
        options.append(
            {
                "id": case.id,
                "label": case.title or case.id,
                "status": case.status,
                "milestones": [
                    {
                        "id": milestone.id,
                        "label": milestone.title or milestone.id,
                        "status": milestone.status,
                    }
                    for milestone in case.milestones
                    if milestone.id
                    and milestone.status in ("planned", "active")
                ],
            }
        )
    return options


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
            "archive_done": ui.get("kb_archive_card", "Archive"),
            "archive_short": ui.get("kb_archive_short", "Archive"),
            "archive_confirm": ui.get(
                "kb_archive_confirm",
                "Archive this Done task?",
            ),
            "delete_subtask": ui.get("kb_delete_subtask", "Delete subtask"),
            "details": ui["details"],
            "done_uncrystallized": ui.get(
                "kb_done_uncrystallized",
                "Done, not crystallized",
            ),
            "done_pending_badge": ui.get(
                "kb_done_pending_badge",
                "⚡ {n} done, awaiting crystallization",
            ),
            "kb_card_actions": ui.get("kb_card_actions", "⋯"),
            "kb_more_fields": ui.get("kb_more_fields", "More fields"),
            "kb_wip_hint": ui.get(
                "kb_wip_hint",
                "Doing has {n} tasks — consider limiting work in progress.",
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
            "open_activity": ui.get(
                "kb_open_activity_detail",
                "Open Activity details",
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
            "html_lang": llm_client.ui_language(),
            "quick_add": ui.get("kb_quick_add", "+ Add task"),
            "move_to": ui.get("kb_move_to_label", ui.get("move_to", "Move to")),
            "project": ui.get("kb_project", "Project"),
            "milestone": ui.get("kb_milestone", "Milestone"),
            "no_project": ui.get("kb_no_project", "No project"),
            "no_milestone": ui.get("kb_no_milestone", "No milestone"),
            "confirm_move": ui.get("kb_confirm_move", "Move"),
            "save": ui["save"],
            "save_short": ui.get("kb_save_short", "Save"),
            "started_on": ui["field_started"],
            "subtasks": ui["subtasks_label"],
            "tags": ui.get("kb_tags", ui.get("task_tags", "Tags")),
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


def _card_date_error_message(fields: list[str], ui: dict[str, str]) -> str:
    """Return a localized invalid date warning."""
    labels = {
        "started_on": ui.get("field_started", "started_on"),
        "completed_on": ui.get("field_completed", "completed_on"),
    }
    field_list = ", ".join(labels.get(field, field) for field in fields)
    fallback = "Use YYYY-MM-DD for date fields: {fields}."
    return ui.get("kb_invalid_date", fallback).format(fields=field_list)


def _normalize_card_project_fields(profile: str, card: dict) -> dict:
    """Clear stale milestone values when a card changes project."""
    if "project_id" not in card and "milestone_id" not in card:
        return card
    normalized = dict(card)
    project_id = str(normalized.get("project_id", "") or "").strip()
    milestone_id = str(normalized.get("milestone_id", "") or "").strip()
    normalized["project_id"] = project_id
    normalized["milestone_id"] = milestone_id
    if not project_id:
        normalized["milestone_id"] = ""
        return normalized
    board = load_project_board(profile)
    case = board.by_id().get(project_id)
    if case is None:
        normalized["milestone_id"] = ""
        return normalized
    valid_milestones = {milestone.id for milestone in case.milestones}
    if milestone_id and milestone_id not in valid_milestones:
        normalized["milestone_id"] = ""
    return normalized


def _apply_board_card_payload(
    *,
    profile: str,
    card: dict | None,
    found: tuple[str, int, KanbanTask] | None,
    sections: dict[str, list[KanbanTask]],
    ui: dict[str, str],
) -> tuple[tuple[str, int, KanbanTask] | None, bool, bool]:
    """Apply an optional card payload and return found/applied/ok flags."""
    if not isinstance(card, dict):
        return found, False, True
    if found is None:
        st.warning(ui["kb_drag_stale"])
        return found, False, False
    invalid_dates = _invalid_card_date_fields(card)
    if invalid_dates:
        st.warning(_card_date_error_message(invalid_dates, ui))
        return found, False, False
    section, idx, task = found
    card = _normalize_card_project_fields(profile, card)
    updated_task = _apply_task_update(task, card)
    if updated_task is None:
        st.warning(ui["kb_title_required"])
        return found, False, False
    sections[section][idx] = updated_task
    return (section, idx, updated_task), True, True


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


def _checkin_query_value(name: str) -> str:
    """Return one toolbar check-in query parameter value."""
    try:
        raw = st.query_params.get(name)
    except Exception:
        return ""
    if isinstance(raw, list):
        raw = raw[-1] if raw else ""
    return str(raw or "").strip()


def _set_checkin_query_params(
    *,
    month_label: str,
    day_iso: str,
    open_detail: bool,
) -> None:
    """Mirror toolbar check-in state into URL query parameters."""
    try:
        st.query_params["kb_ci_month"] = month_label
        st.query_params["kb_ci_day"] = day_iso
        st.query_params["kb_ci_open"] = "1" if open_detail else "0"
    except Exception:
        pass


def _store_checkin_calendar_state(
    profile: str,
    *,
    month_label: str,
    day_iso: str,
    open_detail: bool,
) -> None:
    """Update toolbar check-in state without leaving the current session."""
    st.session_state[f"kb_toolbar_checkin_month_{profile}"] = month_label
    st.session_state[f"kb_toolbar_checkin_day_{profile}"] = day_iso
    st.session_state[f"kb_toolbar_checkin_detail_open_{profile}"] = (
        open_detail
    )
    _set_checkin_query_params(
        month_label=month_label,
        day_iso=day_iso,
        open_detail=open_detail,
    )


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


def _checkin_calendar_event_key(profile: str) -> str:
    """Session key for the latest toolbar calendar component event."""
    return f"kb_toolbar_checkin_event_id_{profile}"


def _handle_checkin_calendar_event(profile: str, event: dict | None) -> bool:
    """Apply one calendar component event to toolbar check-in state."""
    if not isinstance(event, dict):
        return False
    action = str(event.get("action") or "")
    if action not in {"select_day", "prev_month", "next_month", "today"}:
        return False
    event_id = str(event.get("event_id") or "")
    event_key = _checkin_calendar_event_key(profile)
    if event_id and st.session_state.get(event_key) == event_id:
        return False

    month_label = str(event.get("month") or "").strip()[:7]
    day_iso = str(event.get("day") or "").strip()[:10]
    try:
        year_text, month_text = month_label.split("-", 1)
        date(int(year_text), int(month_text), 1)
        parsed_day = date.fromisoformat(day_iso)
    except (TypeError, ValueError):
        return False

    if event_id:
        st.session_state[event_key] = event_id
    _store_checkin_calendar_state(
        profile,
        month_label=month_label,
        day_iso=parsed_day.isoformat(),
        open_detail=bool(event.get("open")),
    )
    return True


def _render_month_calendar(
    profile: str,
    payload: dict,
    selected_day: date,
    today: date,
    ui: dict[str, str],
) -> None:
    """Render the compact toolbar month calendar via component events."""
    event = st_checkin_calendar(
        payload=payload,
        selected_day=selected_day.isoformat(),
        today=today.isoformat(),
        ui={
            "kb_checkin_today_short": ui.get("kb_checkin_today_short", "Today"),
            "kb_checkin_strip_learning_short": ui.get(
                "kb_checkin_strip_learning_short",
                ui.get("kb_calendar_learning_short", "L{count}"),
            ),
            "kb_checkin_strip_exercise_short": ui.get(
                "kb_checkin_strip_exercise_short",
                ui.get("kb_calendar_exercise_short", "E{count}"),
            ),
            "previous_month": ui.get("kb_checkin_prev_month", "Previous month"),
            "next_month": ui.get("kb_checkin_next_month", "Next month"),
        },
        key=f"kb_toolbar_checkin_calendar_{profile}",
    )
    if _handle_checkin_calendar_event(profile, event):
        st.rerun()


def _render_toolbar_checkin_styles() -> None:
    """Inject compact styles for toolbar check-in details."""
    st.markdown(
        """
        <style>
        .st-key-kb_toolbar_checkin_detail {
          margin-top: 0.25rem;
        }
        .kb-checkin-links {
          display: flex;
          flex-wrap: wrap;
          gap: 0.25rem;
          margin-top: 0.16rem;
        }
        .kb-checkin-link {
          background: #f8fafc;
          border: 1px solid #dbeafe;
          border-radius: 4px;
          color: #1d4ed8;
          display: inline-flex;
          font-size: 0.72rem;
          font-weight: 700;
          line-height: 1;
          max-width: 100%;
          overflow: hidden;
          padding: 0.18rem 0.32rem;
          text-decoration: none;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .kb-checkin-link:hover {
          background: #eff6ff;
          border-color: #93c5fd;
          text-decoration: none;
        }
        .kb-checkin-link-text {
          color: #475569;
          display: inline-block;
          font-size: 0.72rem;
          line-height: 1.1;
          overflow-wrap: anywhere;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _safe_record_link(url: object) -> str:
    """Return a safe absolute learning link for rendering."""
    clean = str(url or "").strip()
    if not clean:
        return ""
    parsed = urlparse(clean)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    return clean


def _record_links_html(links: object) -> str:
    """Return compact HTML for a check-in record's learning links."""
    raw_links = links if isinstance(links, list) else []
    chips: list[str] = []
    text_bits: list[str] = []
    for index, raw in enumerate(raw_links, start=1):
        clean = str(raw or "").strip()
        if not clean:
            continue
        safe = _safe_record_link(clean)
        label = f"Link {index}"
        if safe:
            chips.append(
                '<a class="kb-checkin-link" '
                f'href="{escape(safe, quote=True)}" '
                'target="_blank" rel="noopener noreferrer">'
                f"{escape(label)}</a>"
            )
        else:
            text_bits.append(
                f'<span class="kb-checkin-link-text">{escape(clean)}</span>'
            )
    if not chips and not text_bits:
        return ""
    return '<div class="kb-checkin-links">' + "".join(chips + text_bits) + "</div>"


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
        link_html = _record_links_html(item.get("links"))
        if link_html:
            cols[1].markdown(link_html, unsafe_allow_html=True)
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
        workout_type = st.selectbox(
            ui.get("kb_exercise_type", "Type"),
            list(EXERCISE_TYPES),
            index=list(EXERCISE_TYPES).index("other"),
            key=f"kb_toolbar_exercise_type_{profile}_{selected_day.isoformat()}",
            format_func=lambda value: ui.get(
                f"kb_exercise_type_{value}",
                str(value).replace("_", " ").title(),
            ),
        )
        duration_min = st.number_input(
            ui.get("kb_exercise_duration", "Duration (min)"),
            key=f"kb_toolbar_exercise_duration_{profile}_{selected_day.isoformat()}",
            min_value=0.0,
            step=5.0,
            value=0.0,
        )
        intensity = st.selectbox(
            ui.get("kb_exercise_intensity", "Intensity"),
            list(EXERCISE_INTENSITIES),
            index=list(EXERCISE_INTENSITIES).index("moderate"),
            key=f"kb_toolbar_exercise_intensity_{profile}_{selected_day.isoformat()}",
            format_func=lambda value: ui.get(
                f"kb_exercise_intensity_{value}",
                str(value).title(),
            ),
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
        workout_type=str(workout_type or "other"),
        duration_min=float(duration_min or 0.0),
        intensity=str(intensity or "moderate"),
        note=str(note or "").strip(),
    )
    st.rerun()


def _render_toolbar_checkin(
    profile: str,
    profile_path,
    ui: dict[str, str],
) -> None:
    """Render the compact top-right month check-in calendar."""
    _render_toolbar_checkin_styles()
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

    _render_month_calendar(profile, payload, selected_day, today, ui)

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
    ai_backend: str,
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

    task_id = _event_task_id(event, payload)
    found = _find_task_ref(sections, task_id)

    if action == "open_activity_item":
        activity_item_id = str(payload.get("activity_item_id") or "").strip()
        if not activity_item_id:
            return
        st.query_params["activity_item"] = activity_item_id
        st.query_params["source_page"] = "Kanban"
        try:
            st.switch_page("pages/9_Agent_Activity.py")
        except Exception:
            st.info(ui.get("kb_open_activity_detail", "Open Activity details"))
        return

    if action in ("move_card", "reorder"):
        found, card_applied, ok = _apply_board_card_payload(
            profile=profile,
            card=payload.get("card"),
            found=found,
            sections=sections,
            ui=ui,
        )
        if not ok:
            return
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
        if card_applied:
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

    if action == "edit_card":
        card = payload.get("card")
        if not isinstance(card, dict):
            card = payload
        _found, _card_applied, ok = _apply_board_card_payload(
            profile=profile,
            card=card,
            found=found,
            sections=sections,
            ui=ui,
        )
        if not ok:
            return
        _auto_save(profile, sections)
        st.rerun()

    if action == "toggle_subtask":
        _auto_save_subtask_toggle(
            profile,
            sections,
            task_id,
            payload.get("subtask_index", -1),
            str(payload.get("subtask_title") or ""),
            bool(payload.get("done")),
            ui,
        )
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

    if action == "archive_done_card":
        if found is None:
            st.warning(ui["kb_drag_stale"])
            return
        found, card_applied, ok = _apply_board_card_payload(
            profile=profile,
            card=payload.get("card"),
            found=found,
            sections=sections,
            ui=ui,
        )
        if not ok or found is None:
            return
        section, idx, _task = found
        if section != KANBAN_DONE:
            if card_applied:
                _auto_save(profile, sections)
            st.warning(
                ui.get(
                    "kb_archive_done_only",
                    "Only Done tasks can be archived from the board.",
                )
            )
            return
        pdir = profile_dir(profile)
        kanban_path = pdir / "kanban.md"
        archive_path = pdir / "kanban-archive.md"
        project_path = pdir / "project-board.yaml"
        assert_files_current([archive_path, kanban_path, project_path])
        updated = archive_kanban_done_tasks(profile, sections, [idx])
        sync_project_board_from_kanban(profile, updated)
        refresh_file_snapshots([archive_path, kanban_path, project_path])
        stash_git_backup_results()
        clear_web_cache()
        sections.clear()
        sections.update(updated)
        st.rerun()

    if action == "crystallize_card":
        if found is None:
            st.warning(ui["kb_drag_stale"])
            return
        found, card_applied, ok = _apply_board_card_payload(
            profile=profile,
            card=payload.get("card"),
            found=found,
            sections=sections,
            ui=ui,
        )
        if not ok or found is None:
            return
        section, idx, task = found
        if section != KANBAN_DONE:
            if card_applied:
                _auto_save(profile, sections)
            st.warning(
                ui.get(
                    "kb_crystallize_done_only",
                    "Only Done tasks can be crystallized.",
                )
            )
            return
        sections[section][idx] = replace(task, crystallized=True)
        _auto_save(profile, sections)
        st.rerun()

    if action in ("request_gap", "ai_gap_ingest"):
        if found is None:
            st.warning(ui["kb_drag_stale"])
            return
        found, card_applied, ok = _apply_board_card_payload(
            profile=profile,
            card=payload.get("card"),
            found=found,
            sections=sections,
            ui=ui,
        )
        if not ok:
            return
        if card_applied:
            _auto_save(profile, sections)
        with st.spinner(ui.get("spinner_gap", "Running gap analysis...")):
            result = analyze_kanban_task_gap(
                profile,
                sections,
                task_id,
                use_rule_match=True,
                use_llm_router=(
                    ai_backend == "codex"
                    or (ai_backend == "llm" and llm_client.is_configured())
                ),
                ai_backend=ai_backend,
                persist_router_keywords=False,
                goal_context=current_goal_agent_context(profile),
            )
        state = st.session_state.setdefault(_gap_results_key(profile), {})
        state[task_id] = result
        st.rerun()
        return

    if action in ("request_subtasks", "ai_subtask_ingest"):
        if found is None:
            st.warning(ui["kb_drag_stale"])
            return
        found, card_applied, ok = _apply_board_card_payload(
            profile=profile,
            card=payload.get("card"),
            found=found,
            sections=sections,
            ui=ui,
        )
        if not ok:
            return
        if card_applied:
            _auto_save(profile, sections)
        with st.spinner(ui.get("spinner_ai", "AI reasoning...")):
            alignments = generate_kanban_task_alignment_options(
                sections,
                task_id,
                profile_name=profile,
                record_activity=True,
                ai_backend=ai_backend,
                goal_context=current_goal_agent_context(profile),
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
            granularity = str(
                payload.get("granularity")
                or _kanban_subtask_granularity(profile)
            ).strip()
            if granularity not in {"milestone", "checklist", "implementation"}:
                granularity = "milestone"
            style_hint = _style_hint_from_alignment_payload(payload)
            if not style_hint:
                style_hint = _kanban_subtask_style_hint(profile)
            _persist_kanban_subtask_preferences(
                profile,
                granularity=granularity,
                style_hint=style_hint,
            )
            result = generate_kanban_subtask_proposals_detailed(
                profile,
                sections,
                task_id,
                use_rule_match=True,
                use_llm_router=(
                    ai_backend == "llm" and llm_client.is_configured()
                ),
                persist_router_keywords=False,
                alignment_context=alignment_context,
                granularity=granularity,
                record_activity=ai_backend == "llm",
                ai_backend=ai_backend,
                goal_context=current_goal_agent_context(profile),
                subtask_style_hint=style_hint,
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
        found, _card_applied, ok = _apply_board_card_payload(
            profile=profile,
            card=card if isinstance(card, dict) else None,
            found=found,
            sections=sections,
            ui=ui,
        )
        if not ok:
            return
        updated = apply_kanban_subtask_proposals(
            sections,
            task_id,
            proposals,
        )
        sections.clear()
        sections.update(updated)
        applied_found = _find_task_ref(sections, task_id)
        if applied_found is not None:
            applied_section, applied_idx, applied_task = applied_found
            sections[applied_section][applied_idx] = (
                _append_ai_proposal_details(applied_task, proposals)
            )
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

# -- Page --------------------------------------------------------

ui = kanban_ui()
require_login()
selected = select_profile()
ui = kanban_ui()
render_git_backup_notices()

_pdir = profile_dir(selected)
_kanban_path = _pdir / "kanban.md"
_archive_path = _pdir / "kanban-archive.md"
_pool_path = _pdir / "evidence-pool.yaml"
_tree_path = _pdir / "skill-tree.yaml"
_skill_path = _pdir / "SKILL.md"
_activity_path = _pdir / "activity-log.yaml"
_agent_activity_path = _pdir / "agent-activity.yaml"
_ai_runs_path = _pdir / "ai-runs.yaml"
_goals_path = _pdir / "goals.yaml"
_project_path = _pdir / "project-board.yaml"
for _path in (
    _kanban_path,
    _archive_path,
    _pool_path,
    _tree_path,
    _skill_path,
    _activity_path,
    _agent_activity_path,
    _ai_runs_path,
    _goals_path,
    _project_path,
):
    ensure_file_snapshot(_path)

ai_backend = kanban_ai_backend(selected)

# -- Header / Toolbar -------------------------------------------

header_left, header_calendar = st.columns(
    [3, 1],
    gap="medium",
    vertical_alignment="top",
)
with header_left:
    title_col, goal_col = st.columns(
        [5, 2],
        gap="medium",
        vertical_alignment="top",
    )
    with title_col:
        st.title(ui["title"])
        st.caption(ui["page_context_line"])
    with goal_col:
        render_current_goal_strip(
            selected,
            compact=True,
            align="right",
        )
    help_col, ai_col = st.columns(
        [1, 1],
        gap="small",
        vertical_alignment="top",
    )
    with help_col:
        render_page_help(
            ui,
            key=f"kanban_help:{selected}",
            docs_path="docs/zh/guides/kanban.md",
        )
    with ai_col:
        with st.popover(
            ui.get("kb_ai_settings_title", "Kanban AI Config"),
            key=f"kanban_ai_settings:{selected}",
        ):
            _render_kanban_ai_settings(selected, ui)
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
                    refresh_file_snapshots(
                        [
                            _kanban_path,
                            _activity_path,
                            _agent_activity_path,
                            _ai_runs_path,
                        ]
                    )
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
        "lang": llm_client.ui_language(),
        "project_options": _project_options_payload(selected),
        "subtask_granularity": _kanban_subtask_granularity(selected),
        "subtask_style_hint": _kanban_subtask_style_hint(selected),
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
        ai_backend=ai_backend,
        ui=ui,
    )

st.divider()

done_entry_l, done_entry_r = st.columns(
    [4, 1],
    gap="medium",
    vertical_alignment="center",
)
with done_entry_l:
    st.caption(
        ui.get(
            "kb_done_review_hint",
            "Use Evidence Review for Done -> evidence drafts and batch cleanup.",
        )
    )
with done_entry_r:
    st.page_link(
        "pages/2_Evidence_Review.py",
        label=ui.get("kb_open_evidence_review", "Open Evidence Review"),
        use_container_width=True,
    )
