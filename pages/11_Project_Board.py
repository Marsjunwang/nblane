"""Project Board -- internal project cases and execution links."""

from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import replace
from datetime import date
from html import escape

import streamlit as st
import yaml

from nblane.core import llm as llm_client
from nblane.core.ai.gateway import run_ai_action
from nblane.core.experience import load_experience_book
from nblane.core.goals import load_goal_book
from nblane.core.kanban_events import split_kanban_details
from nblane.core.io import (
    KANBAN_DOING,
    KANBAN_DONE,
    KANBAN_QUEUE,
    KANBAN_SECTIONS,
    KanbanTask,
    parse_kanban,
    profile_dir,
    save_kanban,
)
from nblane.core.project_board import (
    MILESTONE_STATUSES,
    PROJECT_KINDS,
    PROJECT_STATUSES,
    PROJECT_VISIBILITIES,
    ProjectBoard,
    ProjectMilestone,
    add_project_case,
    load_project_board,
)
from nblane.core.project_board_events import (
    case_from_event,
    case_payload,
    count_no_anchor_tasks,
    format_date_range,
    milestone_from_event,
    milestone_payload,
    timeline_date_range,
    timeline_tasks,
)
from nblane.core.project_board_sync import (
    sync_project_board_from_kanban,
    sync_project_case_workspace,
)
from nblane.core.web_preferences import (
    load_web_preferences,
    update_web_preferences,
)
from nblane.project_board_component import (
    project_board_component_available,
    st_project_board,
)
from nblane.project_timeline_component import (
    project_timeline_component_available,
    st_project_timeline,
)
from nblane.core.kanban_archive import _archive_tasks
from nblane.web_auth import require_login
from nblane.web_cache import clear_web_cache, load_evidence_pool_raw, load_research_sources
from nblane.web_i18n import kanban_section_label, project_board_ui
from nblane.web_shared import (
    apply_ui_language_from_session,
    assert_files_current,
    ensure_file_snapshot,
    refresh_file_snapshots,
    render_current_goal_strip,
    render_git_backup_notices,
    render_page_help,
    select_profile,
    stash_git_backup_results,
)

apply_ui_language_from_session()

ui = project_board_ui()
st.set_page_config(page_title=ui["page_title"], layout="wide")
require_login()
selected = select_profile()
ui = project_board_ui()
render_git_backup_notices()

_pdir = profile_dir(selected)
_project_path = _pdir / "project-board.yaml"
_kanban_path = _pdir / "kanban.md"
_pool_path = _pdir / "evidence-pool.yaml"
_goals_path = _pdir / "goals.yaml"
_experience_path = _pdir / "experience.yaml"
_outputs_path = _pdir / "outputs.yaml"
_research_sources_path = _pdir / "research" / "sources.yaml"

for _path in (
    _project_path,
    _kanban_path,
    _pool_path,
    _goals_path,
    _experience_path,
    _outputs_path,
    _research_sources_path,
):
    ensure_file_snapshot(_path)


def _state_key(name: str) -> str:
    return f"project_board:{selected}:{name}"


def _clean_list(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        clean = str(value or "").strip()
        if clean and clean not in seen:
            seen.add(clean)
            out.append(clean)
    return out


def _time_range_dates(value: object) -> tuple[date | None, date | None]:
    dates: list[date] = []
    for raw in re.findall(r"\d{4}-\d{2}-\d{2}", str(value or "")):
        try:
            dates.append(date.fromisoformat(raw))
        except ValueError:
            continue
        if len(dates) >= 2:
            break
    if not dates:
        return None, None
    if len(dates) == 1:
        return dates[0], None
    start, end = dates[0], dates[1]
    if end < start:
        start, end = end, start
    return start, end


def _date_input_value(value: date | None):
    return value if value is not None else None


def _slug(value: str, fallback: str = "milestone") -> str:
    clean = value.strip().lower()
    clean = re.sub(r"[^a-z0-9\u4e00-\u9fff._~-]+", "-", clean)
    clean = clean.strip(".-")
    return clean or fallback


def _next_milestone_id(case, title: str) -> str:
    base = f"milestone:{_slug(title)}"
    existing = {milestone.id for milestone in case.milestones if milestone.id}
    if base not in existing:
        return base
    index = 2
    while f"{base}-{index}" in existing:
        index += 1
    return f"{base}-{index}"


def _option_label(options: dict[str, str], value: str) -> str:
    return options.get(value, value)


def _with_unknown_options(
    refs: list[str],
    options: dict[str, str],
) -> dict[str, str]:
    out = dict(options)
    for ref in refs:
        if ref and ref not in out:
            out[ref] = f"{ref} ({ui['missing_ref']})"
    return out


def _goal_options() -> dict[str, str]:
    book = load_goal_book(selected)
    return {
        goal.id: f"{goal.title or goal.label or goal.id} · {goal.status}"
        for goal in book.goals
        if goal.id
    }


def _task_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    sections = parse_kanban(selected)
    for section, tasks in sections.items():
        for task in tasks:
            if not task.id:
                continue
            rows.append(
                {
                    "id": task.id,
                    "label": (
                        f"[{kanban_section_label(section)}] "
                        f"{task.title} · {task.id}"
                    ),
                    "project_id": task.project_id,
                    "milestone_id": task.milestone_id,
                }
            )
    return rows


def _task_section_index() -> dict[str, str]:
    """Map task id -> kanban section label key for completion math."""
    index: dict[str, str] = {}
    sections = parse_kanban(selected)
    for section, tasks in sections.items():
        for task in tasks:
            if task.id:
                index[task.id] = section
    return index


def _milestone_completion(milestone, task_index: dict[str, str]) -> tuple[int, int]:
    """Return (done, total) for a milestone's linked kanban tasks."""
    refs = [ref for ref in milestone.task_refs if ref]
    if not refs:
        return 0, 0
    done = sum(1 for ref in refs if task_index.get(ref) == KANBAN_DONE)
    return done, len(refs)


def _case_task_ids(case) -> set[str]:
    """Task ids owned by this project (via project_id or the case task_refs)."""
    owned = {row["id"] for row in _task_rows() if row.get("project_id") == case.id}
    owned.update(ref for ref in case.task_refs if ref)
    return owned


def _case_tasks_by_section() -> dict[str, list[tuple[str, KanbanTask]]]:
    """Map kanban section -> [(section, task)] preserving board order."""
    out: dict[str, list[tuple[str, KanbanTask]]] = {}
    for section, tasks in parse_kanban(selected).items():
        for task in tasks:
            out.setdefault(section, []).append((section, task))
    return out


def _move_task_section_and_refresh(task_id: str, target_section: str) -> None:
    """Move a task to another kanban column (last-write-wins, no hard guard)."""
    sections = parse_kanban(selected)
    found: KanbanTask | None = None
    for name, tasks in sections.items():
        for idx, task in enumerate(tasks):
            if task.id and task.id == task_id:
                found = tasks.pop(idx)
                break
        if found is not None:
            break
    if found is None:
        return
    if target_section == KANBAN_DOING and not found.started_on:
        found = replace(found, started_on=date.today().isoformat())
    if target_section == KANBAN_DONE and not found.completed_on:
        found = replace(found, completed_on=date.today().isoformat(), done=True)
    if target_section != KANBAN_DONE and found.done:
        found = replace(found, done=False)
    sections.setdefault(target_section, []).append(found)
    save_kanban(selected, sections)
    sync_project_board_from_kanban(selected, parse_kanban(selected))
    stash_git_backup_results()
    clear_web_cache()
    refresh_file_snapshots([_kanban_path, _project_path])
    st.toast(ui["task_row_saved"])
    st.rerun(scope="fragment")


def _task_options_for_case(case_id: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for row in _task_rows():
        owner = row.get("project_id", "")
        if owner and owner != case_id:
            continue
        out[row["id"]] = row["label"]
    return out


def _claimed_elsewhere_count(case_id: str) -> int:
    return sum(
        1
        for row in _task_rows()
        if row.get("project_id") and row.get("project_id") != case_id
    )


def _evidence_options() -> dict[str, str]:
    raw = load_evidence_pool_raw(selected) or {}
    out: dict[str, str] = {}
    for row in raw.get("evidence_entries") or []:
        if not isinstance(row, dict):
            continue
        eid = str(row.get("id", "") or "").strip()
        if not eid:
            continue
        title = str(row.get("title", "") or eid)
        status = str(row.get("review_status", "") or "")
        out[eid] = f"{title} · {status}" if status else title
    return out


def _source_options() -> dict[str, str]:
    inbox = load_research_sources(selected)
    return {
        source.id: f"{source.title or source.id} · {source.status}"
        for source in inbox.sources
        if source.id
    }


def _experience_options() -> dict[str, str]:
    book = load_experience_book(selected)
    return {
        case.id: " · ".join(
            item
            for item in (case.organization, case.role, case.status)
            if item
        )
        or case.id
        for case in book.experience_cases
        if case.id
    }


def _output_options() -> dict[str, str]:
    if not _outputs_path.exists():
        return {}
    raw = yaml.safe_load(_outputs_path.read_text(encoding="utf-8")) or {}
    out: dict[str, str] = {}
    for item in raw.get("outputs") or []:
        if not isinstance(item, dict):
            continue
        oid = str(item.get("id", "") or "").strip()
        if oid:
            out[oid] = str(item.get("title", "") or oid)
    return out


def _multiselect_refs(
    label: str,
    refs: list[str],
    options: dict[str, str],
    *,
    key: str,
    help_text: str = "",
) -> list[str]:
    merged = _with_unknown_options(refs, options)
    return st.multiselect(
        label,
        options=list(merged),
        default=[ref for ref in refs if ref in merged],
        format_func=lambda ref: _option_label(merged, ref),
        key=key,
        help=help_text or None,
    )


def _candidate_rows(options: dict[str, str]) -> list[dict[str, str]]:
    return [
        {"id": ref, "label": label}
        for ref, label in list(options.items())[:80]
    ]


def _valid_suggested_refs(raw: object, options: dict[str, str]) -> list[str]:
    values = _clean_list(raw)
    return [ref for ref in values if ref in options]


def _project_ai_payload(case, option_maps: dict[str, dict[str, str]]) -> dict:
    return {
        "reply_language": llm_client.reply_language(),
        "project": {
            "id": case.id,
            "title": case.title,
            "status": case.status,
            "kind": case.kind,
            "summary": case.summary,
            "notes": case.notes,
        },
        "current_refs": {
            "goal_refs": list(case.goal_refs),
            "task_refs": list(case.task_refs),
            "evidence_refs": list(case.evidence_refs),
            "source_refs": list(case.source_refs),
            "output_refs": list(case.output_refs),
        },
        "candidates": {
            field: _candidate_rows(options)
            for field, options in option_maps.items()
        },
    }


def _suggest_project_refs(case, option_maps: dict[str, dict[str, str]]) -> dict:
    result = run_ai_action(
        "project.suggest_refs",
        _project_ai_payload(case, option_maps),
        profile=selected,
        context_refs=[case.id],
        require_review=True,
    )
    if not result.ok:
        return {
            "ok": False,
            "error": result.error or result.content or ui["project_ai_suggest_failed"],
            "warnings": list(result.warnings),
        }
    data = result.structured if isinstance(result.structured, dict) else {}
    suggestions = {
        field: _valid_suggested_refs(data.get(field), option_maps.get(field, {}))
        for field in option_maps
    }
    return {
        "ok": True,
        "backend": result.backend,
        "suggestions": suggestions,
        "rationale": str(data.get("rationale") or "").strip(),
        "warnings": _clean_list(data.get("warnings")) + list(result.warnings),
    }


def _apply_project_ref_suggestions(case, suggestions: dict[str, list[str]]) -> int:
    field_to_key = {
        "goal_refs": "goals",
        "task_refs": "tasks",
        "evidence_refs": "evidence",
        "source_refs": "sources",
        "output_refs": "outputs",
    }
    total_added = 0
    for field, key_name in field_to_key.items():
        current = _clean_list(list(getattr(case, field, [])))
        merged = _clean_list([*current, *suggestions.get(field, [])])
        total_added += max(0, len(merged) - len(current))
        st.session_state[_state_key(f"{key_name}:{case.id}")] = merged
    return total_added


def _render_project_ref_suggestion_state(case) -> None:
    state = st.session_state.get(_state_key(f"ai_ref_suggestions:{case.id}"))
    if not isinstance(state, dict) or not state.get("ok"):
        return
    suggestions = state.get("suggestions") if isinstance(state.get("suggestions"), dict) else {}
    total = sum(len(value) for value in suggestions.values() if isinstance(value, list))
    if total <= 0:
        st.caption(ui["project_ai_suggest_none"])
        return
    st.caption(ui["project_ai_suggest_summary"].format(count=total))
    if state.get("rationale"):
        st.caption(str(state["rationale"]))
    warnings = _clean_list(state.get("warnings"))
    if warnings:
        st.caption(" / ".join(warnings[:3]))


def _case_by_id(board: ProjectBoard, case_id: str):
    return board.by_id().get(case_id)


def _milestone_by_id(case, milestone_id: str):
    for milestone in case.milestones:
        if milestone.id == milestone_id:
            return milestone
    return None


def _clone(value):
    return deepcopy(value)


def _apply_changed_case_fields(latest_case, original_case, submitted_case) -> None:
    simple_fields = (
        "title",
        "status",
        "kind",
        "visibility",
        "time_range",
        "summary",
        "notes",
    )
    list_fields = (
        "goal_refs",
        "task_refs",
        "evidence_refs",
        "source_refs",
        "experience_refs",
        "output_refs",
    )
    for field in simple_fields + list_fields:
        submitted_value = getattr(submitted_case, field)
        if submitted_value != getattr(original_case, field):
            setattr(latest_case, field, _clone(submitted_value))


def _apply_changed_milestone_fields(
    latest_milestone,
    original_milestone,
    submitted_milestone,
) -> None:
    for field in (
        "title",
        "status",
        "target",
        "summary",
        "task_refs",
        "evidence_refs",
        "source_refs",
        "output_refs",
    ):
        submitted_value = getattr(submitted_milestone, field)
        if submitted_value != getattr(original_milestone, field):
            setattr(latest_milestone, field, _clone(submitted_value))


def _sync_latest_and_refresh(board: ProjectBoard, project_id: str) -> None:
    refresh_file_snapshots([_project_path])
    assert_files_current(
        [
            _kanban_path,
            _pool_path,
            _research_sources_path,
        ]
    )
    result = sync_project_case_workspace(selected, board, project_id)
    stash_git_backup_results()
    clear_web_cache()
    refresh_file_snapshots(
        [
            _project_path,
            _kanban_path,
            _pool_path,
            _research_sources_path,
        ]
    )
    for warning in result.warnings:
        st.warning(warning)
    st.success(ui["saved"])


def _sync_case_update_and_refresh(
    original_case,
    submitted_case,
) -> None:
    latest_board = load_project_board(selected)
    latest_case = _case_by_id(latest_board, submitted_case.id)
    if latest_case is None:
        st.error(ui["project_missing_reload"].format(id=submitted_case.id))
        refresh_file_snapshots([_project_path])
        st.stop()
    _apply_changed_case_fields(latest_case, original_case, submitted_case)
    _sync_latest_and_refresh(latest_board, latest_case.id)


def _sync_new_case_and_refresh(
    *,
    title: str,
    case_id: str,
    status: str,
    kind: str,
    visibility: str,
    summary: str,
    goal_refs: list[str],
    evidence_refs: list[str] | None = None,
):
    latest_board = load_project_board(selected)
    try:
        case = add_project_case(
            latest_board,
            title,
            case_id=case_id,
            status=status,
            kind=kind,
            visibility=visibility,
            summary=summary,
            goal_refs=goal_refs,
            evidence_refs=evidence_refs or None,
        )
    except ValueError as exc:
        st.error(str(exc))
        return None
    _sync_latest_and_refresh(latest_board, case.id)
    return case


def _sync_milestone_update_and_refresh(
    case_id: str,
    original_milestone: ProjectMilestone,
    submitted_milestone: ProjectMilestone,
) -> None:
    latest_board = load_project_board(selected)
    latest_case = _case_by_id(latest_board, case_id)
    if latest_case is None:
        st.error(ui["project_missing_reload"].format(id=case_id))
        refresh_file_snapshots([_project_path])
        st.stop()
    latest_milestone = _milestone_by_id(latest_case, submitted_milestone.id)
    if latest_milestone is None:
        st.error(ui["milestone_missing_reload"].format(id=submitted_milestone.id))
        refresh_file_snapshots([_project_path])
        st.stop()
    _apply_changed_milestone_fields(
        latest_milestone,
        original_milestone,
        submitted_milestone,
    )
    _sync_latest_and_refresh(latest_board, case_id)


def _sync_milestone_add_and_refresh(case_id: str, milestone: ProjectMilestone) -> None:
    latest_board = load_project_board(selected)
    latest_case = _case_by_id(latest_board, case_id)
    if latest_case is None:
        st.error(ui["project_missing_reload"].format(id=case_id))
        refresh_file_snapshots([_project_path])
        st.stop()
    if _milestone_by_id(latest_case, milestone.id) is not None:
        st.error(ui["duplicate_milestone"].format(id=milestone.id))
        return
    latest_case.milestones.append(_clone(milestone))
    _sync_latest_and_refresh(latest_board, case_id)


def _summary_chip(label: str, value: int, *, tone: str = "default") -> str:
    return (
        f'<span class="pb-summary-chip pb-summary-chip--{tone}">'
        f'<span class="pb-summary-label">{escape(str(label))}</span>'
        f'<strong>{escape(str(value))}</strong>'
        "</span>"
    )


def _summary_metrics(board: ProjectBoard) -> None:
    counts = {status: 0 for status in PROJECT_STATUSES}
    for case in board.project_cases:
        counts[case.status] = counts.get(case.status, 0) + 1
    current_goal = load_goal_book(selected).current_goal_id
    goal_count = sum(
        1
        for case in board.project_cases
        if current_goal and current_goal in case.goal_refs
    )
    unassigned_tasks = sum(1 for row in _task_rows() if not row.get("project_id"))
    raw = load_evidence_pool_raw(selected) or {}
    unassigned_evidence = 0
    for row in raw.get("evidence_entries") or []:
        if not isinstance(row, dict):
            continue
        if row.get("deprecated"):
            continue
        if str(row.get("review_status", "") or "") == "reviewed" and not row.get(
            "project_refs"
        ):
            unassigned_evidence += 1

    status_html = "".join(
        _summary_chip(ui[f"status_{status}"], counts.get(status, 0))
        for status in PROJECT_STATUSES
    )
    gap_html = "".join(
        (
            _summary_chip(
                ui["metric_unassigned_tasks"],
                unassigned_tasks,
                tone="risk" if unassigned_tasks else "quiet",
            ),
            _summary_chip(
                ui["metric_unassigned_evidence"],
                unassigned_evidence,
                tone="risk" if unassigned_evidence else "quiet",
            ),
            _summary_chip(
                ui["metric_current_goal_projects"],
                goal_count,
                tone="goal",
            ),
        )
    )
    evidence_hint = (
        f'<span class="pb-summary-note">'
        f'{escape(ui["unassigned_evidence_hint"].format(count=unassigned_evidence))}'
        "</span>"
        if unassigned_evidence
        else ""
    )
    st.markdown(
        f"""
<style>
.pb-summary {{
  align-items: center;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: .35rem .45rem;
  margin: .35rem 0 .7rem;
  padding: .35rem .45rem;
}}
.pb-summary-group {{
  align-items: center;
  display: inline-flex;
  flex-wrap: wrap;
  gap: .35rem;
}}
.pb-summary-group + .pb-summary-group {{
  border-left: 1px solid #e2e8f0;
  padding-left: .45rem;
}}
.pb-summary-chip {{
  align-items: baseline;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 999px;
  color: #0f172a;
  display: inline-flex;
  gap: .32rem;
  min-height: 1.65rem;
  padding: .12rem .52rem;
}}
.pb-summary-chip--quiet {{
  background: #ffffff;
}}
.pb-summary-chip--risk {{
  background: #fff7ed;
  border-color: #fed7aa;
}}
.pb-summary-chip--goal {{
  background: #eff6ff;
  border-color: #bfdbfe;
}}
.pb-summary-label {{
  color: #64748b;
  font-size: .76rem;
  line-height: 1.15;
  white-space: nowrap;
}}
.pb-summary-chip strong {{
  font-size: .95rem;
  line-height: 1;
}}
.pb-summary-note {{
  color: #9a3412;
  font-size: .76rem;
  line-height: 1.2;
  padding: 0 .25rem;
}}
@media (max-width: 760px) {{
  .pb-summary {{
    gap: .3rem;
  }}
  .pb-summary-group + .pb-summary-group {{
    border-left: 0;
    padding-left: 0;
  }}
}}
</style>
<div class="pb-summary">
  <span class="pb-summary-group">{status_html}</span>
  <span class="pb-summary-group">{gap_html}</span>
  {evidence_hint}
</div>
""",
        unsafe_allow_html=True,
    )


def _render_create_project(board: ProjectBoard) -> None:
    # Prefill from an Evidence Review "create project from evidence" suggestion.
    prefill = st.session_state.get("project_board_create_prefill") or {}
    prefill_evidence = list(prefill.get("evidence_ids") or [])
    with st.expander(
        ui["create_project"], expanded=bool(prefill) or not board.project_cases
    ):
        if prefill:
            st.info(
                ui.get(
                    "create_from_evidence_hint",
                    "Prefilled from {n} evidence row(s). Confirm to create and link.",
                ).format(n=len(prefill_evidence))
            )
        with st.form(_state_key("create_project")):
            title = st.text_input(
                ui["field_title"], value=str(prefill.get("title", "") or "")
            )
            case_id = st.text_input(
                ui["field_id"],
                value=str(prefill.get("id", "") or ""),
                help=ui["id_help"],
            )
            c1, c2, c3 = st.columns(3)
            with c1:
                status = st.selectbox(ui["field_status"], PROJECT_STATUSES)
            with c2:
                _kind_default = str(prefill.get("kind", "") or "")
                kind = st.selectbox(
                    ui["field_kind"],
                    PROJECT_KINDS,
                    index=(
                        PROJECT_KINDS.index(_kind_default)
                        if _kind_default in PROJECT_KINDS
                        else 0
                    ),
                )
            with c3:
                _vis_default = str(prefill.get("visibility", "") or "")
                visibility = st.selectbox(
                    ui["field_visibility"],
                    PROJECT_VISIBILITIES,
                    index=(
                        PROJECT_VISIBILITIES.index(_vis_default)
                        if _vis_default in PROJECT_VISIBILITIES
                        else 0
                    ),
                )
            summary = st.text_area(
                ui["field_summary"],
                height=80,
                value=str(prefill.get("summary", "") or ""),
            )
            goals = _multiselect_refs(
                ui["field_goal_refs"],
                [],
                _goal_options(),
                key=_state_key("create_goals"),
                help_text=ui["field_goal_refs_help"],
            )
            submitted = st.form_submit_button(
                ui["create_project"],
                type="primary",
            )
        if not submitted:
            return
        case = _sync_new_case_and_refresh(
            title=title,
            case_id=case_id,
            status=status,
            kind=kind,
            visibility=visibility,
            summary=summary,
            goal_refs=goals,
            evidence_refs=prefill_evidence,
        )
        if case is None:
            return
        # One-shot prefill: clear so a normal create next time starts blank.
        st.session_state.pop("project_board_create_prefill", None)
        st.session_state[_state_key("selected_project_active")] = case.id
        st.rerun()


def _render_project_board(board: ProjectBoard) -> None:
    active_id = st.session_state.get(_state_key("selected_project_active"))
    status_tabs = st.tabs([ui[f"status_{status}"] for status in PROJECT_STATUSES])
    for tab, status in zip(status_tabs, PROJECT_STATUSES):
        with tab:
            rows = [case for case in board.project_cases if case.status == status]
            if not rows:
                st.caption(ui["empty_status"])
                continue
            for case in rows:
                is_active = case.id == active_id
                with st.container(border=True):
                    c1, c2 = st.columns([5, 1])
                    with c1:
                        badge = (
                            f"{ui['card_selected_badge']} " if is_active else ""
                        )
                        st.markdown(f"**{badge}{case.title or case.id}**")
                        st.caption(
                            " · ".join(
                                item
                                for item in (
                                    case.id,
                                    case.kind,
                                    case.visibility,
                                    case.time_range,
                                )
                                if item
                            )
                        )
                        st.caption(
                            ui["card_counts"].format(
                                goals=len(case.goal_refs),
                                tasks=len(case.task_refs),
                                evidence=len(case.evidence_refs),
                                sources=len(case.source_refs),
                                milestones=len(case.milestones),
                            )
                        )
                    with c2:
                        if st.button(
                            ui["select"],
                            key=_state_key(f"select:{case.id}"),
                            use_container_width=True,
                            type="primary" if is_active else "secondary",
                            disabled=is_active,
                        ):
                            st.session_state[
                                _state_key("selected_project_active")
                            ] = case.id
                            st.rerun()


def _ref_rows(options: dict[str, str], selected: list[str]) -> list[dict[str, str]]:
    """Build [{id,label}] option rows, including any selected-but-missing ids."""
    merged = _with_unknown_options([s for s in selected if s], options)
    return [{"id": rid, "label": rlabel} for rid, rlabel in merged.items()]


def _case_option_maps(case) -> dict[str, list[dict[str, str]]]:
    return {
        "goal_refs": _ref_rows(_goal_options(), case.goal_refs),
        "task_refs": _ref_rows(_task_options_for_case(case.id), case.task_refs),
        "evidence_refs": _ref_rows(_evidence_options(), case.evidence_refs),
        "source_refs": _ref_rows(_source_options(), case.source_refs),
        "experience_refs": _ref_rows(_experience_options(), case.experience_refs),
        "output_refs": _ref_rows(_output_options(), case.output_refs),
    }


def _component_labels() -> dict[str, str]:
    keys = (
        "tab_basic", "field_id", "field_title", "field_status", "field_kind",
        "field_visibility", "field_time_range", "field_summary", "field_notes",
        "field_target", "field_goal_refs", "field_task_refs", "field_evidence_refs",
        "field_source_refs", "field_experience_refs", "field_output_refs",
        "links_section", "save_project", "save_milestone", "add_milestone",
        "archive_project", "milestones", "missing_ref", "title_required",
        "status_active", "status_paused", "status_completed", "status_archived",
        "status_planned", "milestone_id_help", "duplicate_milestone",
        "tl_range_start", "tl_range_end",
    )
    out = {key: ui[key] for key in keys if key in ui}
    extra = {
        "no_options": "pb_no_options",
        "pick_placeholder": "pb_pick_placeholder",
        "saving": "pb_saving",
        "completion": "pb_completion",
        "new_milestone": "pb_new_milestone",
    }
    for front_key, ui_key in extra.items():
        if ui_key in ui:
            out[front_key] = ui[ui_key]
    return out


def _milestones_payload(case) -> list[dict]:
    task_index = _task_section_index()
    out: list[dict] = []
    for m in case.milestones:
        done, total = _milestone_completion(m, task_index)
        out.append(milestone_payload(m, done=done, total=total))
    return out


def _case_payload(case) -> dict:
    return case_payload(case)


def _event_seen(event_id: str) -> bool:
    """Dedup component events by id (frontend resends the last value on rerun)."""
    if not event_id:
        return False
    key = _state_key("pb_event_id")
    if st.session_state.get(key) == event_id:
        return True
    st.session_state[key] = event_id
    return False


def _apply_basics_event(case, fields: dict) -> None:
    original_case = _clone(case)
    try:
        submitted = case_from_event(original_case, fields)
    except ValueError:
        st.error(ui["title_required"])
        return
    _sync_case_update_and_refresh(original_case, submitted)


def _apply_milestone_save_event(case, milestone_id: str, fields: dict) -> None:
    original = _milestone_by_id(case, milestone_id)
    if original is None:
        st.error(ui["milestone_missing_reload"].format(id=milestone_id))
        return
    try:
        updated = milestone_from_event(_clone(original), fields)
    except ValueError:
        st.error(ui["title_required"])
        return
    _sync_milestone_update_and_refresh(case.id, _clone(original), updated)


def _apply_milestone_add_event(case, fields: dict) -> None:
    title = str(fields.get("title", "") or "").strip()
    if not title:
        st.error(ui["title_required"])
        return
    clean_id = str(fields.get("id", "") or "").strip() or _next_milestone_id(case, title)
    if any(item.id == clean_id for item in case.milestones):
        st.error(ui["duplicate_milestone"].format(id=clean_id))
        return
    _sync_milestone_add_and_refresh(
        case.id,
        ProjectMilestone(
            id=clean_id,
            title=title,
            target=str(fields.get("target", "") or "").strip(),
            date=str(fields.get("date", "") or "").strip(),
            summary=str(fields.get("summary", "") or "").strip(),
        ),
    )


def _apply_milestone_delete_event(case, milestone_id: str) -> None:
    latest_board = load_project_board(selected)
    latest_case = _case_by_id(latest_board, case.id)
    if latest_case is None:
        st.error(ui["project_missing_reload"].format(id=case.id))
        refresh_file_snapshots([_project_path])
        return
    before = len(latest_case.milestones)
    latest_case.milestones = [
        m for m in latest_case.milestones if m.id != milestone_id
    ]
    if len(latest_case.milestones) == before:
        return
    _sync_latest_and_refresh(latest_board, latest_case.id)


def _apply_task_add_event(case, fields: dict) -> None:
    title = str(fields.get("title", "") or "").strip()
    if not title:
        st.error(ui["title_required"])
        return
    latest_board = load_project_board(selected)
    if _case_by_id(latest_board, case.id) is None:
        st.error(ui["project_missing_reload"].format(id=case.id))
        refresh_file_snapshots([_project_path])
        return
    section = str(fields.get("section") or KANBAN_QUEUE)
    if section not in KANBAN_SECTIONS:
        section = KANBAN_QUEUE
    anchor = str(fields.get("date", "") or "").strip() or date.today().isoformat()
    task = KanbanTask(
        title=title,
        project_id=case.id,
        milestone_id=str(fields.get("milestone_id", "") or ""),
        context=str(fields.get("context", "") or "").strip(),
    )
    if section == KANBAN_DONE:
        task = replace(task, started_on=anchor, completed_on=anchor, done=True)
    else:
        # Queue / Doing / Someday: store the chosen date as started_on so the
        # task always has a timeline anchor and shows up immediately.
        task = replace(task, started_on=anchor)
    sections = parse_kanban(selected)
    sections.setdefault(section, []).append(task)
    _save_kanban_and_refresh(sections, ui["task_created"])


def _apply_task_save_event(case, task_id: str, fields: dict) -> None:
    title = str(fields.get("title", "") or "").strip()
    if not title:
        st.error(ui["title_required"])
        return
    sections = parse_kanban(selected)
    for _name, tasks in sections.items():
        for idx, task in enumerate(tasks):
            if task.id and task.id == task_id:
                tasks[idx] = replace(
                    task,
                    title=title,
                    context=str(fields.get("context", "") or "").strip(),
                    milestone_id=str(
                        fields.get("milestone_id", task.milestone_id) or ""
                    ),
                )
                _save_kanban_and_refresh(sections, ui["task_row_saved"])
                return


def _apply_task_delete_event(case, task_id: str) -> None:
    sections = parse_kanban(selected)
    removed = False
    for _name, tasks in sections.items():
        for idx, task in enumerate(tasks):
            if task.id and task.id == task_id:
                tasks.pop(idx)
                removed = True
                break
        if removed:
            break
    if removed:
        _save_kanban_and_refresh(sections, ui["task_row_saved"])


def _save_kanban_and_refresh(sections, toast_msg: str) -> None:
    """Persist kanban edits (last-write-wins) and sync the project board."""
    save_kanban(selected, sections)
    sync_project_board_from_kanban(selected, parse_kanban(selected))
    stash_git_backup_results()
    clear_web_cache()
    refresh_file_snapshots([_kanban_path, _project_path])
    st.toast(toast_msg)


def _open_evidence_for_task(task_id: str) -> None:
    """Jump to Evidence Review carrying the task ref (distill-to-evidence flow)."""
    if not task_id:
        return
    st.query_params["kanban_task"] = task_id
    st.query_params["source_page"] = "Project Board"
    try:
        st.switch_page("pages/2_Evidence_Review.py")
    except Exception:
        st.info(ui.get("tl_to_evidence", "Distill to evidence"))


def _timeline_range_pref() -> dict[str, str]:
    """Read the persisted timeline date range ({start,end}) from web-preferences."""
    prefs = load_web_preferences(selected).get("project_board", {})
    rng = prefs.get("timeline_range", {}) if isinstance(prefs, dict) else {}
    if not isinstance(rng, dict):
        return {"start": "", "end": ""}
    return {
        "start": str(rng.get("start", "") or ""),
        "end": str(rng.get("end", "") or ""),
    }


def _apply_set_range_event(payload: dict) -> None:
    """Persist a user-chosen timeline start/end (empty values reset to default)."""
    start = str(payload.get("start", "") or "").strip()
    end = str(payload.get("end", "") or "").strip()
    update_web_preferences(
        selected,
        {"project_board": {"timeline_range": {"start": start, "end": end}}},
    )
    clear_web_cache()


def _apply_suggest_refs_event(case) -> None:
    """Run the LLM ref suggester and stash results for confirm-not-fill overlay."""
    option_maps = {
        "goal_refs": _goal_options(),
        "task_refs": _task_options_for_case(case.id),
        "evidence_refs": _evidence_options(),
        "source_refs": _source_options(),
        "output_refs": _output_options(),
    }
    with st.spinner(ui["project_ai_suggest_running"]):
        state = _suggest_project_refs(case, option_maps)
    st.session_state[_state_key(f"ai_ref_suggestions:{case.id}")] = state
    if state.get("ok"):
        added = _apply_project_ref_suggestions(
            case,
            state.get("suggestions") if isinstance(state.get("suggestions"), dict) else {},
        )
        if added:
            st.toast(ui["project_ai_suggest_applied"].format(count=added))
        else:
            st.toast(ui["project_ai_suggest_none"])
    else:
        st.error(str(state.get("error") or ui["project_ai_suggest_failed"]))


def _handle_project_event(event: dict | None, case=None) -> bool:
    """Apply one event from the custom project board / timeline component.

    Multi-project timeline events carry the project id in the payload; when
    ``case`` is omitted we resolve it from ``payload["id"]`` / ``["project_id"]``
    against the latest board. Returns True if the event was handled.
    """
    if not isinstance(event, dict):
        return False
    action = str(event.get("action") or "")
    if not action or _event_seen(str(event.get("event_id") or "")):
        return False
    payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
    fields = payload.get("fields") if isinstance(payload.get("fields"), dict) else {}

    # set_range carries no project id -- persist the timeline range preference.
    if action == "set_range":
        _apply_set_range_event(payload)
        return True

    # Resolve the target case from the payload when not passed in explicitly.
    if case is None:
        project_id = str(payload.get("id") or payload.get("project_id") or "")
        case = _case_by_id(load_project_board(selected), project_id)
        if case is None:
            return False

    if action == "save_basics":
        _apply_basics_event(case, fields)
    elif action == "suggest_refs":
        _apply_suggest_refs_event(case)
    elif action == "archive_project":
        original_case = _clone(case)
        _sync_case_update_and_refresh(original_case, replace(original_case, status="archived"))
    elif action == "save_milestone":
        _apply_milestone_save_event(case, str(payload.get("milestone_id") or ""), fields)
    elif action == "add_milestone":
        _apply_milestone_add_event(case, fields)
    elif action == "delete_milestone":
        _apply_milestone_delete_event(case, str(payload.get("milestone_id") or ""))
    elif action == "add_task":
        _apply_task_add_event(case, fields)
    elif action == "save_task":
        _apply_task_save_event(case, str(payload.get("task_id") or ""), fields)
    elif action == "delete_task":
        _apply_task_delete_event(case, str(payload.get("task_id") or ""))
    elif action == "move_task_section":
        _move_task_section_and_refresh(
            str(payload.get("task_id") or ""), str(payload.get("section") or "")
        )
    elif action == "open_evidence_for_task":
        _open_evidence_for_task(str(payload.get("task_id") or ""))
    else:
        return False
    return True


def _live_section_tasks() -> list:
    """All live kanban tasks as [(section, task)] for timeline aggregation."""
    rows = []
    for section, tasks in parse_kanban(selected).items():
        for task in tasks:
            rows.append((section, task))
    return rows


def _timeline_payload(case) -> dict:
    live = _live_section_tasks()
    archived = _archive_tasks(selected)
    rows = timeline_tasks(case, live, archived, archived_section=KANBAN_DONE)
    task_index = _task_section_index()
    milestones = []
    for m in case.milestones:
        done, total = _milestone_completion(m, task_index)
        milestones.append(milestone_payload(m, done=done, total=total))
    payload = _case_payload(case)
    payload["derived_time_range"] = timeline_date_range(rows)
    return {
        "case": payload,
        "tasks": rows,
        "milestones": milestones,
        "no_date_count": count_no_anchor_tasks(case, live),
        "labels": _timeline_labels(),
        "settings": {
            "lang": llm_client.ui_language(),
            "today": date.today().isoformat(),
        },
    }


def _timeline_labels() -> dict[str, str]:
    keys = (
        "field_id", "field_title", "field_status", "field_kind", "field_visibility",
        "field_time_range", "field_target", "field_date", "field_summary", "field_notes",
        "field_goal_refs", "field_task_refs", "field_evidence_refs", "field_source_refs",
        "field_experience_refs", "field_output_refs", "links_section",
        "task_title", "task_section", "task_field_context", "milestones",
        "edit", "cancel", "save", "save_project", "archive_project", "delete_task",
        "status_active", "status_paused", "status_completed", "status_archived",
        "status_planned",
        "kind_internal", "kind_research", "kind_work", "kind_side_project", "kind_learning",
        "visibility_private", "visibility_public",
        "project_ai_suggest_refs", "project_ai_suggest_help",
        "tl_date", "tl_today", "tl_add_task", "tl_add_milestone", "tl_zoom_hint",
        "tl_delete_confirm", "tl_no_date_tasks", "tl_to_evidence",
        "tl_full_info", "tl_show_archived", "tl_select_hint",
        "tl_range_start", "tl_range_end", "tl_range_reset",
        "tl_legend_title", "tl_legend_doing", "tl_legend_done",
        "tl_legend_archived", "tl_legend_milestone", "tl_legend_today",
        "section_Queue", "section_Doing", "section_Done", "section_Someday / Maybe",
    )
    return {key: ui[key] for key in keys if key in ui}


def _project_timeline_entry(case, live, archived, task_index) -> dict:
    """Build one project's {case, tasks, milestones, no_date_count, option_maps}."""
    rows = timeline_tasks(case, live, archived, archived_section=KANBAN_DONE)
    milestones = []
    for m in case.milestones:
        done, total = _milestone_completion(m, task_index)
        milestones.append(milestone_payload(m, done=done, total=total))
    payload = _case_payload(case)
    payload.update(_pending_ref_overlay(case))
    payload["derived_time_range"] = timeline_date_range(rows)
    return {
        "case": payload,
        "tasks": rows,
        "milestones": milestones,
        "no_date_count": count_no_anchor_tasks(case, live),
        "option_maps": _case_option_maps(case),
    }


def _multi_timeline_payload(board: ProjectBoard, *, show_archived: bool) -> dict:
    """Payload for the multi-project timeline: one entry per (filtered) project."""
    live = _live_section_tasks()
    archived = _archive_tasks(selected)
    task_index = _task_section_index()
    projects = [
        _project_timeline_entry(case, live, archived, task_index)
        for case in board.project_cases
        if show_archived or case.status != "archived"
    ]
    return {
        "projects": projects,
        "range": _timeline_range_pref(),
        "labels": _timeline_labels(),
        "settings": {
            "lang": llm_client.ui_language(),
            "today": date.today().isoformat(),
        },
    }


def _render_multi_timeline(board: ProjectBoard) -> None:
    show_archived = bool(
        st.session_state.get(_state_key("tl_show_archived"), False)
    )
    st.checkbox(
        ui["tl_show_archived"],
        key=_state_key("tl_show_archived"),
    )
    event = st_project_timeline(
        payload=_multi_timeline_payload(board, show_archived=show_archived),
        key=_state_key("pt_multi"),
        height=720,
    )
    if _handle_project_event(event):
        st.rerun()


def _render_timeline_component(case) -> None:
    event = st_project_timeline(
        payload=_timeline_payload(case),
        key=_state_key(f"pt:{case.id}"),
        height=640,
    )
    if _handle_project_event(event, case):
        st.rerun(scope="fragment")


def _render_ref_suggest_strip(case) -> None:
    """AI suggest-refs button + summary, shared by the component basics path."""
    option_maps = {
        "goal_refs": _goal_options(),
        "task_refs": _task_options_for_case(case.id),
        "evidence_refs": _evidence_options(),
        "source_refs": _source_options(),
        "output_refs": _output_options(),
    }
    blocked = _claimed_elsewhere_count(case.id)
    if blocked:
        st.caption(ui["claimed_elsewhere_hint"].format(count=blocked))
    st.caption(ui["project_refs_hint"])
    suggest_cols = st.columns([1, 2.5])
    with suggest_cols[0]:
        if st.button(
            ui["project_ai_suggest_refs"],
            key=_state_key(f"ai_suggest_refs:{case.id}"),
            help=ui["project_ai_suggest_help"],
            use_container_width=True,
        ):
            with st.spinner(ui["project_ai_suggest_running"]):
                state = _suggest_project_refs(case, option_maps)
            st.session_state[_state_key(f"ai_ref_suggestions:{case.id}")] = state
            if state.get("ok"):
                added = _apply_project_ref_suggestions(
                    case,
                    state.get("suggestions") if isinstance(state.get("suggestions"), dict) else {},
                )
                if added:
                    st.success(ui["project_ai_suggest_applied"].format(count=added))
                    st.rerun()
                st.info(ui["project_ai_suggest_none"])
            else:
                st.error(str(state.get("error") or ui["project_ai_suggest_failed"]))
    with suggest_cols[1]:
        _render_project_ref_suggestion_state(case)


def _pending_ref_overlay(case) -> dict[str, list[str]]:
    """Merge AI-suggested refs stored in session_state over the saved refs.

    Suggestions are pre-filled (not yet persisted); the component shows them as
    chips so the user confirms with Save -- keeps confirm-not-fill semantics.
    """
    field_to_key = {
        "goal_refs": "goals",
        "task_refs": "tasks",
        "evidence_refs": "evidence",
        "source_refs": "sources",
        "experience_refs": "experiences",
        "output_refs": "outputs",
    }
    out: dict[str, list[str]] = {}
    for field, key_name in field_to_key.items():
        pending = st.session_state.get(_state_key(f"{key_name}:{case.id}"))
        if isinstance(pending, list):
            out[field] = _clean_list(pending)
    return out


def _render_basics_component(case) -> None:
    _render_ref_suggest_strip(case)
    payload = _case_payload(case)
    payload.update(_pending_ref_overlay(case))
    rows = timeline_tasks(
        case,
        _live_section_tasks(),
        _archive_tasks(selected),
        archived_section=KANBAN_DONE,
    )
    payload["derived_time_range"] = timeline_date_range(rows)
    event = st_project_board(
        case=payload,
        option_maps=_case_option_maps(case),
        milestones=[],
        labels=_component_labels(),
        settings={"sections": ["basics"], "lang": llm_client.ui_language()},
        key=_state_key(f"pb_basics:{case.id}"),
        height=720,
    )
    if _handle_project_event(event, case):
        st.rerun()


def _render_milestones_component(case) -> None:
    event = st_project_board(
        case=_case_payload(case),
        option_maps=_case_option_maps(case),
        milestones=_milestones_payload(case),
        labels=_component_labels(),
        settings={"sections": ["milestones"], "lang": llm_client.ui_language()},
        key=_state_key(f"pb_milestones:{case.id}"),
        height=560,
    )
    if _handle_project_event(event, case):
        st.rerun(scope="fragment")


def _render_project_form(board: ProjectBoard, case) -> None:
    original_case = _clone(case)
    task_options = _task_options_for_case(case.id)
    option_maps = {
        "goal_refs": _goal_options(),
        "task_refs": task_options,
        "evidence_refs": _evidence_options(),
        "source_refs": _source_options(),
        "output_refs": _output_options(),
    }
    blocked = _claimed_elsewhere_count(case.id)
    if blocked:
        st.caption(ui["claimed_elsewhere_hint"].format(count=blocked))
    st.caption(ui["project_refs_hint"])
    suggest_cols = st.columns([1, 2.5])
    with suggest_cols[0]:
        if st.button(
            ui["project_ai_suggest_refs"],
            key=_state_key(f"ai_suggest_refs:{case.id}"),
            help=ui["project_ai_suggest_help"],
            use_container_width=True,
        ):
            with st.spinner(ui["project_ai_suggest_running"]):
                state = _suggest_project_refs(case, option_maps)
            st.session_state[_state_key(f"ai_ref_suggestions:{case.id}")] = state
            if state.get("ok"):
                added = _apply_project_ref_suggestions(
                    case,
                    state.get("suggestions") if isinstance(state.get("suggestions"), dict) else {},
                )
                if added:
                    st.success(ui["project_ai_suggest_applied"].format(count=added))
                    st.rerun()
                st.info(ui["project_ai_suggest_none"])
            else:
                st.error(str(state.get("error") or ui["project_ai_suggest_failed"]))
    with suggest_cols[1]:
        _render_project_ref_suggestion_state(case)

    with st.form(_state_key(f"project_form:{case.id}")):
        st.text_input(ui["field_id"], value=case.id, disabled=True)
        title = st.text_input(ui["field_title"], value=case.title)
        c1, c2, c3 = st.columns(3)
        with c1:
            status = st.selectbox(
                ui["field_status"],
                PROJECT_STATUSES,
                index=PROJECT_STATUSES.index(case.status)
                if case.status in PROJECT_STATUSES
                else 0,
            )
        with c2:
            kind = st.selectbox(
                ui["field_kind"],
                PROJECT_KINDS,
                index=PROJECT_KINDS.index(case.kind)
                if case.kind in PROJECT_KINDS
                else 0,
            )
        with c3:
            visibility = st.selectbox(
                ui["field_visibility"],
                PROJECT_VISIBILITIES,
                index=PROJECT_VISIBILITIES.index(case.visibility)
                if case.visibility in PROJECT_VISIBILITIES
                else 0,
            )
        start_date, end_date = _time_range_dates(case.time_range)
        st.caption(ui["field_time_range"])
        tc1, tc2 = st.columns(2)
        with tc1:
            time_start = st.date_input(
                ui["tl_range_start"],
                value=_date_input_value(start_date),
                key=_state_key(f"time_start:{case.id}"),
            )
        with tc2:
            time_end = st.date_input(
                ui["tl_range_end"],
                value=_date_input_value(end_date),
                key=_state_key(f"time_end:{case.id}"),
            )
        summary = st.text_area(ui["field_summary"], value=case.summary, height=90)
        notes = st.text_area(ui["field_notes"], value=case.notes, height=90)
        with st.expander(ui["links_section"], expanded=False):
            goal_refs = _multiselect_refs(
                ui["field_goal_refs"],
                case.goal_refs,
                option_maps["goal_refs"],
                key=_state_key(f"goals:{case.id}"),
                help_text=ui["field_goal_refs_help"],
            )
            task_refs = _multiselect_refs(
                ui["field_task_refs"],
                case.task_refs,
                option_maps["task_refs"],
                key=_state_key(f"tasks:{case.id}"),
                help_text=ui["field_task_refs_help"],
            )
            evidence_refs = _multiselect_refs(
                ui["field_evidence_refs"],
                case.evidence_refs,
                option_maps["evidence_refs"],
                key=_state_key(f"evidence:{case.id}"),
                help_text=ui["field_evidence_refs_help"],
            )
            source_refs = _multiselect_refs(
                ui["field_source_refs"],
                case.source_refs,
                option_maps["source_refs"],
                key=_state_key(f"sources:{case.id}"),
                help_text=ui["field_source_refs_help"],
            )
            experience_refs = _multiselect_refs(
                ui["field_experience_refs"],
                case.experience_refs,
                _experience_options(),
                key=_state_key(f"experiences:{case.id}"),
                help_text=ui.get("field_experience_refs_help", ""),
            )
            output_refs = _multiselect_refs(
                ui["field_output_refs"],
                case.output_refs,
                option_maps["output_refs"],
                key=_state_key(f"outputs:{case.id}"),
                help_text=ui.get("field_output_refs_help", ""),
            )
        submitted = st.form_submit_button(ui["save_project"], type="primary")
    if submitted:
        clean_title = title.strip()
        if not clean_title:
            st.error(ui["title_required"])
            return
        submitted_case = replace(
            original_case,
            title=clean_title,
            status=status,
            kind=kind,
            visibility=visibility,
            time_range=format_date_range(
                time_start.isoformat() if isinstance(time_start, date) else "",
                time_end.isoformat() if isinstance(time_end, date) else "",
            ),
            summary=summary.strip(),
            notes=notes.strip(),
            goal_refs=goal_refs,
            task_refs=task_refs,
            evidence_refs=evidence_refs,
            source_refs=source_refs,
            experience_refs=experience_refs,
            output_refs=output_refs,
        )
        _sync_case_update_and_refresh(original_case, submitted_case)
        st.rerun()


def _render_milestones(board: ProjectBoard, case) -> None:
    st.subheader(ui["milestones"])
    task_index = _task_section_index()
    for milestone in case.milestones:
        original_milestone = _clone(milestone)
        _done, _total = _milestone_completion(milestone, task_index)
        if _total:
            _pct = round(_done / _total * 100)
            _progress = ui["milestone_completion"].format(
                done=_done, total=_total, pct=_pct
            )
            _label = (
                f"{milestone.title or milestone.id} · "
                f"{milestone.status} · {_progress}"
            )
        else:
            _label = f"{milestone.title or milestone.id} · {milestone.status}"
        with st.expander(_label):
            if _total:
                st.progress(_done / _total, text=_progress)
            with st.form(_state_key(f"milestone:{case.id}:{milestone.id}")):
                title = st.text_input(ui["field_title"], value=milestone.title)
                status = st.selectbox(
                    ui["field_status"],
                    MILESTONE_STATUSES,
                    index=MILESTONE_STATUSES.index(milestone.status)
                    if milestone.status in MILESTONE_STATUSES
                    else 0,
                )
                target = st.text_input(ui["field_target"], value=milestone.target)
                summary = st.text_area(
                    ui["field_summary"],
                    value=milestone.summary,
                    height=70,
                )
                task_refs = _multiselect_refs(
                    ui["field_task_refs"],
                    milestone.task_refs,
                    _task_options_for_case(case.id),
                    key=_state_key(f"milestone_tasks:{case.id}:{milestone.id}"),
                    help_text=ui["field_task_refs_help"],
                )
                evidence_refs = _multiselect_refs(
                    ui["field_evidence_refs"],
                    milestone.evidence_refs,
                    _evidence_options(),
                    key=_state_key(f"milestone_evidence:{case.id}:{milestone.id}"),
                    help_text=ui["field_evidence_refs_help"],
                )
                source_refs = _multiselect_refs(
                    ui["field_source_refs"],
                    milestone.source_refs,
                    _source_options(),
                    key=_state_key(f"milestone_sources:{case.id}:{milestone.id}"),
                    help_text=ui["field_source_refs_help"],
                )
                output_refs = _multiselect_refs(
                    ui["field_output_refs"],
                    milestone.output_refs,
                    _output_options(),
                    key=_state_key(f"milestone_outputs:{case.id}:{milestone.id}"),
                    help_text=ui.get("field_output_refs_help", ""),
                )
                submitted = st.form_submit_button(ui["save_milestone"])
            if submitted:
                clean_title = title.strip()
                if not clean_title:
                    st.error(ui["title_required"])
                    return
                updated = replace(
                    original_milestone,
                    title=clean_title,
                    status=status,
                    target=target.strip(),
                    summary=summary.strip(),
                    task_refs=task_refs,
                    evidence_refs=evidence_refs,
                    source_refs=source_refs,
                    output_refs=output_refs,
                )
                _sync_milestone_update_and_refresh(
                    case.id,
                    original_milestone,
                    updated,
                )
                st.rerun(scope="fragment")

    with st.expander(ui["add_milestone"], expanded=not case.milestones):
        with st.form(_state_key(f"add_milestone:{case.id}")):
            title = st.text_input(ui["field_title"])
            milestone_id = st.text_input(ui["field_id"], help=ui["milestone_id_help"])
            target = st.text_input(ui["field_target"])
            summary = st.text_area(ui["field_summary"], height=70)
            submitted = st.form_submit_button(ui["add_milestone"], type="primary")
        if submitted:
            clean_title = title.strip()
            if not clean_title:
                st.error(ui["title_required"])
                return
            clean_id = milestone_id.strip() or _next_milestone_id(case, clean_title)
            if any(item.id == clean_id for item in case.milestones):
                st.error(ui["duplicate_milestone"].format(id=clean_id))
                return
            _sync_milestone_add_and_refresh(
                case.id,
                ProjectMilestone(
                    id=clean_id,
                    title=clean_title,
                    target=target.strip(),
                    summary=summary.strip(),
                ),
            )
            st.rerun(scope="fragment")


def _render_project_tasks(board: ProjectBoard, case) -> None:
    st.subheader(ui["project_tasks"])
    owned_ids = _case_task_ids(case)
    if not owned_ids:
        st.caption(ui["project_tasks_empty"])
        return
    st.caption(ui["task_move_help"])
    milestone_label = {"": ui["no_milestone"]}
    for milestone in case.milestones:
        if milestone.id:
            milestone_label[milestone.id] = milestone.title or milestone.id
    by_section = _case_tasks_by_section()
    rows: list[tuple[str, KanbanTask]] = []
    for section in KANBAN_SECTIONS:
        for sec, task in by_section.get(section, []):
            if task.id and task.id in owned_ids:
                rows.append((sec, task))
    if not rows:
        st.caption(ui["project_tasks_empty"])
        return
    for section, task in rows:
        c_title, c_section = st.columns([3, 2])
        with c_title:
            mid = task.milestone_id or ""
            tag = milestone_label.get(mid, mid) if mid else ""
            label = f"**{task.title or task.id}**"
            if tag:
                label += f"  ·  {tag}"
            st.markdown(label)
        with c_section:
            choice = st.selectbox(
                ui["task_section"],
                list(KANBAN_SECTIONS),
                index=KANBAN_SECTIONS.index(section)
                if section in KANBAN_SECTIONS
                else 0,
                format_func=kanban_section_label,
                key=_state_key(f"task_move:{task.id}"),
                label_visibility="collapsed",
            )
        if choice != section:
            _move_task_section_and_refresh(task.id, choice)


def _render_create_task(board: ProjectBoard, case) -> None:
    has_tasks = bool(_case_task_ids(case))
    with st.expander(ui["create_task"], expanded=not has_tasks):
        with st.form(_state_key(f"create_task:{case.id}")):
            title = st.text_input(ui["task_title"])
            col_section, col_milestone = st.columns(2)
            with col_section:
                section = st.selectbox(
                    ui["task_section"],
                    [KANBAN_QUEUE, KANBAN_DOING],
                    format_func=kanban_section_label,
                )
            milestone_options = {
                "": ui["no_milestone"],
                **{
                    milestone.id: milestone.title or milestone.id
                    for milestone in case.milestones
                    if milestone.id
                },
            }
            with col_milestone:
                milestone_id = st.selectbox(
                    ui["field_milestone"],
                    list(milestone_options),
                    format_func=lambda mid: milestone_options[mid],
                )
            context = st.text_area(
                ui["task_field_context"],
                height=70,
                help=ui["task_field_context_help"],
            )
            why = st.text_area(
                ui["task_field_why"],
                height=70,
                help=ui["task_field_why_help"],
            )
            notes = st.text_area(
                ui["task_field_notes"],
                height=90,
                help=ui["task_field_notes_help"],
            )
            tags = st.text_input(
                ui["task_field_tags"],
                help=ui["task_field_tags_help"],
            )
            st.caption(ui["task_started_hint"])
            submitted = st.form_submit_button(ui["create_task"], type="primary")
        if not submitted:
            return
        clean_title = title.strip()
        if not clean_title:
            st.error(ui["title_required"])
            return
        latest_board = load_project_board(selected)
        if _case_by_id(latest_board, case.id) is None:
            st.error(ui["project_missing_reload"].format(id=case.id))
            refresh_file_snapshots([_project_path])
            st.stop()
        sections = parse_kanban(selected)
        task = KanbanTask(
            title=clean_title,
            project_id=case.id,
            milestone_id=milestone_id,
            context=context.strip(),
            why=why.strip(),
            tags=tags.strip(),
        )
        if notes.strip():
            task = replace(task, details=split_kanban_details(notes))
        if section == KANBAN_DOING:
            task = replace(task, started_on=date.today().isoformat())
        sections.setdefault(section, []).append(task)
        save_kanban(selected, sections)
        sync_project_board_from_kanban(selected, parse_kanban(selected))
        stash_git_backup_results()
        clear_web_cache()
        refresh_file_snapshots([_kanban_path, _project_path])
        st.toast(ui["task_created"])
        st.rerun(scope="fragment")


def _resolve_selected_project(board: ProjectBoard) -> str | None:
    active = st.session_state.get(_state_key("selected_project_active"))
    if active and active in board.by_id():
        return active
    return None


@st.fragment
def _milestones_tasks_fragment(case_id: str) -> None:
    """Isolated rerun region for the Milestones & tasks tab.

    Reloads board/case fresh on each fragment rerun so create-task,
    the task list, and milestone edits reflect the latest disk state
    without a full-page rerun (keeps scroll position and other tabs).
    """
    board = load_project_board(selected)
    case = _case_by_id(board, case_id)
    if case is None:
        st.warning(ui["project_missing_reload"].format(id=case_id))
        return
    if project_timeline_component_available():
        _render_timeline_component(case)
        return
    _render_create_task(board, case)
    _render_project_tasks(board, case)
    st.divider()
    if project_board_component_available():
        _render_milestones_component(case)
    else:
        _render_milestones(board, case)


def _render_project_detail(board: ProjectBoard, case) -> None:
    tabs = st.tabs([ui["tab_basic"], ui["tab_milestones_tasks"]])
    with tabs[0]:
        if project_board_component_available():
            _render_basics_component(case)
        else:
            _render_project_form(board, case)
            if case.status != "archived":
                if st.button(ui["archive_project"], type="secondary"):
                    original_case = _clone(case)
                    submitted_case = replace(original_case, status="archived")
                    _sync_case_update_and_refresh(original_case, submitted_case)
                    st.rerun()
    with tabs[1]:
        _milestones_tasks_fragment(case.id)


def main() -> None:
    board = load_project_board(selected)
    head_l, head_goal = st.columns([5, 2], gap="medium", vertical_alignment="top")
    with head_l:
        st.title(ui["title"])
        st.caption(ui["page_context_line"])
    with head_goal:
        render_current_goal_strip(selected, compact=True, align="right")
    render_page_help(
        ui,
        key=f"project_board_help:{selected}",
        docs_path=f"docs/{llm_client.ui_language()}/guides/project-board.md",
    )

    _summary_metrics(board)
    st.divider()
    _render_create_project(board)

    if not board.project_cases:
        st.info(ui["empty_board"])
        return

    if project_timeline_component_available():
        _render_multi_timeline(board)
        return

    # Fallback: legacy list + detail layout when the component bundle is absent.
    left, right = st.columns([2, 3], gap="large")
    with left:
        _render_project_board(board)
    with right:
        selected_id = _resolve_selected_project(board)
        if selected_id is None:
            st.info(ui["select_project_hint"])
        else:
            case = board.by_id()[selected_id]
            _render_project_detail(board, case)


if __name__ == "__main__":
    main()
