"""Project Board -- internal project cases and execution links."""

from __future__ import annotations

import re
from dataclasses import replace

import streamlit as st
import yaml

from nblane.core.experience import load_experience_book
from nblane.core.goals import load_goal_book
from nblane.core.io import (
    KANBAN_DOING,
    KANBAN_QUEUE,
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
    update_project_case,
)
from nblane.core.project_board_sync import (
    sync_project_board_from_kanban,
    sync_project_case_workspace,
)
from nblane.core.research_sources import load_research_sources
from nblane.web_auth import require_login
from nblane.web_cache import clear_web_cache, load_evidence_pool_raw
from nblane.web_i18n import kanban_section_label, project_board_ui
from nblane.web_shared import (
    apply_ui_language_from_session,
    assert_files_current,
    ensure_file_snapshot,
    refresh_file_snapshots,
    render_current_goal_strip,
    render_git_backup_notices,
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
) -> list[str]:
    merged = _with_unknown_options(refs, options)
    return st.multiselect(
        label,
        options=list(merged),
        default=[ref for ref in refs if ref in merged],
        format_func=lambda ref: _option_label(merged, ref),
        key=key,
    )


def _sync_and_refresh(board: ProjectBoard, project_id: str) -> None:
    assert_files_current(
        [
            _project_path,
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

    cols = st.columns(7)
    for idx, status in enumerate(PROJECT_STATUSES):
        cols[idx].metric(ui[f"status_{status}"], counts.get(status, 0))
    cols[4].metric(ui["metric_unassigned_tasks"], unassigned_tasks)
    cols[5].metric(ui["metric_unassigned_evidence"], unassigned_evidence)
    cols[6].metric(ui["metric_current_goal_projects"], goal_count)
    if unassigned_evidence:
        st.info(
            ui["unassigned_evidence_hint"].format(count=unassigned_evidence)
        )


def _render_create_project(board: ProjectBoard) -> None:
    with st.expander(ui["create_project"], expanded=not board.project_cases):
        with st.form(_state_key("create_project")):
            title = st.text_input(ui["field_title"])
            case_id = st.text_input(ui["field_id"], help=ui["id_help"])
            c1, c2, c3 = st.columns(3)
            with c1:
                status = st.selectbox(ui["field_status"], PROJECT_STATUSES)
            with c2:
                kind = st.selectbox(ui["field_kind"], PROJECT_KINDS)
            with c3:
                visibility = st.selectbox(
                    ui["field_visibility"],
                    PROJECT_VISIBILITIES,
                )
            summary = st.text_area(ui["field_summary"], height=80)
            goals = _multiselect_refs(
                ui["field_goal_refs"],
                [],
                _goal_options(),
                key=_state_key("create_goals"),
            )
            submitted = st.form_submit_button(
                ui["create_project"],
                type="primary",
            )
        if not submitted:
            return
        try:
            case = add_project_case(
                board,
                title,
                case_id=case_id,
                status=status,
                kind=kind,
                visibility=visibility,
                summary=summary,
                goal_refs=goals,
            )
        except ValueError as exc:
            st.error(str(exc))
            return
        _sync_and_refresh(board, case.id)
        st.session_state[_state_key("selected_project")] = case.id
        st.rerun()


def _render_project_board(board: ProjectBoard) -> None:
    status_tabs = st.tabs([ui[f"status_{status}"] for status in PROJECT_STATUSES])
    for tab, status in zip(status_tabs, PROJECT_STATUSES):
        with tab:
            rows = [case for case in board.project_cases if case.status == status]
            if not rows:
                st.caption(ui["empty_status"])
                continue
            for case in rows:
                with st.container(border=True):
                    c1, c2 = st.columns([5, 1])
                    with c1:
                        st.markdown(f"**{case.title or case.id}**")
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
                            ui["edit"],
                            key=_state_key(f"edit:{case.id}"),
                            use_container_width=True,
                        ):
                            st.session_state[
                                _state_key("selected_project")
                            ] = case.id
                            st.rerun()


def _render_project_form(board: ProjectBoard, case) -> None:
    st.subheader(ui["project_detail"])
    task_options = _task_options_for_case(case.id)
    blocked = _claimed_elsewhere_count(case.id)
    if blocked:
        st.caption(ui["claimed_elsewhere_hint"].format(count=blocked))

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
        time_range = st.text_input(ui["field_time_range"], value=case.time_range)
        summary = st.text_area(ui["field_summary"], value=case.summary, height=90)
        notes = st.text_area(ui["field_notes"], value=case.notes, height=90)
        goal_refs = _multiselect_refs(
            ui["field_goal_refs"],
            case.goal_refs,
            _goal_options(),
            key=_state_key(f"goals:{case.id}"),
        )
        task_refs = _multiselect_refs(
            ui["field_task_refs"],
            case.task_refs,
            task_options,
            key=_state_key(f"tasks:{case.id}"),
        )
        evidence_refs = _multiselect_refs(
            ui["field_evidence_refs"],
            case.evidence_refs,
            _evidence_options(),
            key=_state_key(f"evidence:{case.id}"),
        )
        source_refs = _multiselect_refs(
            ui["field_source_refs"],
            case.source_refs,
            _source_options(),
            key=_state_key(f"sources:{case.id}"),
        )
        experience_refs = _multiselect_refs(
            ui["field_experience_refs"],
            case.experience_refs,
            _experience_options(),
            key=_state_key(f"experiences:{case.id}"),
        )
        output_refs = _multiselect_refs(
            ui["field_output_refs"],
            case.output_refs,
            _output_options(),
            key=_state_key(f"outputs:{case.id}"),
        )
        submitted = st.form_submit_button(ui["save_project"], type="primary")
    if submitted:
        try:
            update_project_case(
                board,
                case.id,
                title=title,
                status=status,
                kind=kind,
                visibility=visibility,
                time_range=time_range,
                summary=summary,
                notes=notes,
                goal_refs=goal_refs,
                task_refs=task_refs,
                evidence_refs=evidence_refs,
                source_refs=source_refs,
                experience_refs=experience_refs,
                output_refs=output_refs,
                milestones=case.milestones,
            )
        except ValueError as exc:
            st.error(str(exc))
            return
        _sync_and_refresh(board, case.id)
        st.rerun()


def _render_milestones(board: ProjectBoard, case) -> None:
    st.subheader(ui["milestones"])
    for milestone in case.milestones:
        with st.expander(f"{milestone.title or milestone.id} · {milestone.status}"):
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
                )
                evidence_refs = _multiselect_refs(
                    ui["field_evidence_refs"],
                    milestone.evidence_refs,
                    _evidence_options(),
                    key=_state_key(f"milestone_evidence:{case.id}:{milestone.id}"),
                )
                source_refs = _multiselect_refs(
                    ui["field_source_refs"],
                    milestone.source_refs,
                    _source_options(),
                    key=_state_key(f"milestone_sources:{case.id}:{milestone.id}"),
                )
                output_refs = _multiselect_refs(
                    ui["field_output_refs"],
                    milestone.output_refs,
                    _output_options(),
                    key=_state_key(f"milestone_outputs:{case.id}:{milestone.id}"),
                )
                submitted = st.form_submit_button(ui["save_milestone"])
            if submitted:
                updated = replace(
                    milestone,
                    title=title,
                    status=status,
                    target=target,
                    summary=summary,
                    task_refs=task_refs,
                    evidence_refs=evidence_refs,
                    source_refs=source_refs,
                    output_refs=output_refs,
                )
                case.milestones = [
                    updated if item.id == milestone.id else item
                    for item in case.milestones
                ]
                _sync_and_refresh(board, case.id)
                st.rerun()

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
            case.milestones.append(
                ProjectMilestone(
                    id=clean_id,
                    title=clean_title,
                    target=target,
                    summary=summary,
                )
            )
            _sync_and_refresh(board, case.id)
            st.rerun()


def _render_create_task(board: ProjectBoard, case) -> None:
    with st.expander(ui["create_task"]):
        with st.form(_state_key(f"create_task:{case.id}")):
            title = st.text_input(ui["task_title"])
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
            milestone_id = st.selectbox(
                ui["field_milestone"],
                list(milestone_options),
                format_func=lambda mid: milestone_options[mid],
            )
            submitted = st.form_submit_button(ui["create_task"], type="primary")
        if not submitted:
            return
        clean_title = title.strip()
        if not clean_title:
            st.error(ui["title_required"])
            return
        assert_files_current([_kanban_path, _project_path])
        sections = parse_kanban(selected)
        sections.setdefault(section, []).append(
            KanbanTask(
                title=clean_title,
                project_id=case.id,
                milestone_id=milestone_id,
            )
        )
        save_kanban(selected, sections)
        sync_project_board_from_kanban(selected, parse_kanban(selected))
        stash_git_backup_results()
        clear_web_cache()
        refresh_file_snapshots([_kanban_path, _project_path])
        st.success(ui["task_created"])
        st.rerun()


def main() -> None:
    board = load_project_board(selected)
    head_l, head_goal = st.columns([5, 2], gap="medium", vertical_alignment="top")
    with head_l:
        st.title(ui["title"])
        st.caption(ui["page_context_line"])
    with head_goal:
        render_current_goal_strip(selected, compact=True, align="right")

    _summary_metrics(board)
    st.divider()
    _render_create_project(board)

    if not board.project_cases:
        st.info(ui["empty_board"])
        return

    _render_project_board(board)
    st.divider()

    options = {case.id: case.title or case.id for case in board.project_cases if case.id}
    selected_id = st.session_state.get(_state_key("selected_project"))
    if selected_id not in options:
        selected_id = next(iter(options))
    selected_id = st.selectbox(
        ui["select_project"],
        list(options),
        index=list(options).index(selected_id),
        format_func=lambda pid: options[pid],
        key=_state_key("selected_project"),
    )
    case = next(case for case in board.project_cases if case.id == selected_id)
    _render_project_form(board, case)
    _render_milestones(board, case)
    _render_create_task(board, case)

    if case.status != "archived":
        if st.button(ui["archive_project"], type="secondary"):
            update_project_case(board, case.id, status="archived")
            _sync_and_refresh(board, case.id)
            st.rerun()


if __name__ == "__main__":
    main()
