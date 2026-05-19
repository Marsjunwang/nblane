"""Evidence Review -- triage Done work, pool rows, links, and risks."""

from __future__ import annotations

from dataclasses import replace

import streamlit as st
import yaml

from nblane.core import llm as llm_client
from nblane.core.claims import apply_claim_candidates, generate_claim_candidates
from nblane.core.evidence_pool_id import new_evidence_id
from nblane.core.evidence_review import (
    build_evidence_review,
    normalize_evidence_strength,
)
from nblane.core.experience import (
    EXPERIENCE_STATUSES,
    EXPERIENCE_VISIBILITIES,
    add_experience_case,
    load_experience_book,
    save_experience_book,
    update_experience_case,
)
from nblane.core.io import (
    EVIDENCE_POOL_FILENAME,
    KANBAN_DONE,
    archive_kanban_done_tasks,
    parse_kanban,
    profile_dir,
    save_evidence_pool,
    save_kanban,
    save_skill_tree,
)
from nblane.core.models import (
    EVIDENCE_CONFIDENCES,
    EVIDENCE_PUBLIC_READINESS,
    EVIDENCE_REVIEW_STATUSES,
    EVIDENCE_STRENGTHS,
    EVIDENCE_TYPES,
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
from nblane.core.project_board_sync import (
    add_project_refs_to_ingest_patch,
    project_refs_for_tasks,
    sync_project_board_from_kanban,
)
from nblane.core.review_actions import record_writeback_activity
from nblane.core.sync import write_generated_blocks
from nblane.web_auth import require_login
from nblane.web_cache import (
    clear_web_cache,
    load_evidence_pool_raw,
    load_skill_tree_raw,
)
from nblane.web_i18n import evidence_review_ui
from nblane.web_shared import (
    apply_ui_language_from_session,
    assert_files_current,
    current_goal_agent_context,
    ensure_file_snapshot,
    refresh_file_snapshots,
    render_current_goal_strip,
    render_git_backup_notices,
    render_llm_unavailable,
    kanban_ai_backend,
    select_profile,
    stash_git_backup_results,
)

apply_ui_language_from_session()

ui = evidence_review_ui()
require_login()
selected = select_profile()
ui = evidence_review_ui()
render_git_backup_notices()

_pdir = profile_dir(selected)
_pool_path = _pdir / EVIDENCE_POOL_FILENAME
_tree_path = _pdir / "skill-tree.yaml"
_skill_path = _pdir / "SKILL.md"
_kanban_path = _pdir / "kanban.md"
_archive_path = _pdir / "kanban-archive.md"
_goals_path = _pdir / "goals.yaml"
_project_path = _pdir / "project-board.yaml"
_experience_path = _pdir / "experience.yaml"
_research_sources_path = _pdir / "research" / "sources.yaml"
for _path in (
    _pool_path,
    _tree_path,
    _skill_path,
    _kanban_path,
    _archive_path,
    _goals_path,
    _project_path,
    _experience_path,
    _research_sources_path,
):
    ensure_file_snapshot(_path)


def _text_lines(value: str) -> list[str]:
    """Parse one non-empty item per line."""
    return [line.strip() for line in value.splitlines() if line.strip()]


def _lines_text(values: object) -> str:
    """Render source_refs as one line per item."""
    if not isinstance(values, list):
        return ""
    return "\n".join(str(item).strip() for item in values if str(item).strip())


def _label(prefix: str, value: str, *, empty: str = "empty") -> str:
    key = f"{prefix}_{value or empty}"
    return ui.get(key, value or ui.get(key, ""))


def _strength_label(value: object) -> str:
    strength = normalize_evidence_strength(value)
    return _label("strength", "" if strength == "unrated" else strength)


def _review_status_label(value: str) -> str:
    return _label("review_status", value)


def _public_readiness_label(value: str) -> str:
    return _label("public_readiness", value)


def _confidence_label(value: str) -> str:
    return _label("confidence", value)


def _pool_entries() -> list[dict]:
    raw = load_evidence_pool_raw(selected) or {
        "profile": selected,
        "evidence_entries": [],
    }
    return [
        dict(item)
        for item in (raw.get("evidence_entries") or [])
        if isinstance(item, dict)
    ]


def _save_pool(entries: list[dict], message: str) -> None:
    """Persist evidence-pool.yaml and refresh generated context blocks."""
    assert_files_current([_pool_path, _skill_path])
    pool_raw = load_evidence_pool_raw(selected) or {}
    pool_raw["profile"] = selected
    pool_raw["evidence_entries"] = entries
    save_evidence_pool(
        selected,
        pool_raw,
    )
    if _skill_path.exists():
        write_generated_blocks(_pdir)
    refresh_file_snapshots([_pool_path, _skill_path])
    stash_git_backup_results()
    clear_web_cache()
    st.success(message)


def _save_pool_raw(pool_raw: dict, message: str) -> None:
    """Persist a full evidence-pool mapping without dropping top-level claims."""
    assert_files_current([_pool_path])
    pool = dict(pool_raw or {})
    pool["profile"] = selected
    save_evidence_pool(selected, pool)
    refresh_file_snapshots([_pool_path])
    stash_git_backup_results()
    clear_web_cache()
    st.success(message)


def _save_tree(tree: dict, message: str) -> None:
    """Persist skill-tree.yaml and refresh generated context blocks."""
    assert_files_current([_tree_path, _skill_path])
    save_skill_tree(selected, tree)
    if _skill_path.exists():
        write_generated_blocks(_pdir)
    refresh_file_snapshots([_tree_path, _skill_path])
    stash_git_backup_results()
    clear_web_cache()
    st.success(message)


def _record_done_ingest_activity(
    *,
    title: str,
    source_ids: set[str],
    source_titles: set[str],
    warnings: list[str] | None = None,
    error: str = "",
    status: str = "applied",
) -> None:
    """Record Done -> Evidence writeback from Evidence Review."""
    record_writeback_activity(
        selected,
        source_page="Evidence Review",
        target_owner="evidence_pool",
        candidate_type="evidence",
        source_ref="kanban:done_to_evidence",
        title=title,
        summary="Done -> Evidence writeback",
        refs={
            "task_refs": sorted(source_ids),
            "task_titles": sorted(source_titles),
            "files": [
                str(_pool_path),
                str(_tree_path),
                str(_kanban_path),
            ],
        },
        payload={"source": "evidence_review_done_to_evidence"},
        warnings=list(warnings or []),
        error=error,
        changed_paths=[
            _pool_path,
            _tree_path,
            _skill_path,
            _kanban_path,
        ]
        if status == "applied"
        else [],
        status=status,
    )


def _compact_row(row: dict) -> dict:
    """Drop empty optional fields before writing YAML."""
    out = {
        "id": str(row.get("id", "") or "").strip(),
        "type": str(row.get("type", "practice") or "practice").strip(),
        "title": str(row.get("title", "") or "").strip(),
    }
    for key in ("date", "url", "summary", "strength", "confidence"):
        value = str(row.get(key, "") or "").strip()
        if value:
            out[key] = value
    review_status = str(row.get("review_status", "") or "").strip()
    if review_status:
        out["review_status"] = review_status
    public_readiness = str(row.get("public_readiness", "") or "").strip()
    if public_readiness:
        out["public_readiness"] = public_readiness
    for ref_key in ("source_refs", "project_refs", "experience_refs"):
        raw_refs = row.get(ref_key) or []
        if not isinstance(raw_refs, list):
            continue
        refs = [str(item).strip() for item in raw_refs if str(item).strip()]
        if refs:
            out[ref_key] = refs
    if bool(row.get("deprecated", False)):
        out["deprecated"] = True
    replaced_by = str(row.get("replaced_by", "") or "").strip()
    if replaced_by:
        out["replaced_by"] = replaced_by
    return out


def _row_label(row: dict) -> str:
    eid = str(row.get("id", "") or "").strip()
    title = str(row.get("title", "") or "").strip()
    return f"{eid} - {title}" if title else eid


def _skill_label(option: dict) -> str:
    status = str(option.get("status", "") or "")
    label = str(option.get("label", "") or option.get("id", ""))
    node_id = str(option.get("id", "") or "")
    suffix = f" · {status}" if status else ""
    return f"{label} ({node_id}){suffix}"


def _mark_done_crystallized(
    done_ids: set[str],
    done_titles: set[str],
) -> None:
    """Set crystallized on selected Done tasks."""
    sections = parse_kanban(selected)
    done_tasks = sections.get(KANBAN_DONE) or []
    for index, task in enumerate(done_tasks):
        task_id = str(getattr(task, "id", "") or "")
        title = str(getattr(task, "title", "") or "")
        if (task_id and task_id in done_ids) or title in done_titles:
            done_tasks[index] = replace(task, crystallized=True)
    sections[KANBAN_DONE] = done_tasks
    assert_files_current([_kanban_path])
    save_kanban(selected, sections)
    refresh_file_snapshots([_kanban_path])
    stash_git_backup_results()
    clear_web_cache()


def _done_housekeeping_label(task: object, index: int) -> str:
    """Render a stable label for one Done housekeeping option."""
    title = str(getattr(task, "title", "") or "").strip() or f"Done {index + 1}"
    status = (
        ui.get("done_crystallized_label", "crystallized")
        if bool(getattr(task, "crystallized", False))
        else ui.get("done_uncrystallized_label", "uncrystallized")
    )
    refs = [
        str(getattr(task, "project_id", "") or "").strip(),
        str(getattr(task, "milestone_id", "") or "").strip(),
    ]
    refs = [ref for ref in refs if ref]
    suffix = f" - {' / '.join(refs)}" if refs else ""
    return f"{index + 1}. {title} [{status}]{suffix}"


def _render_done_housekeeping(sections: dict[str, list]) -> None:
    """Archive or delete Done tasks from the Evidence Review workbench."""
    st.subheader(ui["done_housekeeping_title"])
    st.caption(ui["done_housekeeping_caption"])
    done_tasks = list(sections.get(KANBAN_DONE) or [])
    if not done_tasks:
        st.caption(ui["done_housekeeping_empty"])
        return

    done_indexes = list(range(len(done_tasks)))
    default_indexes = [
        index
        for index, task in enumerate(done_tasks)
        if bool(getattr(task, "crystallized", False))
    ]
    picked = st.multiselect(
        ui["done_housekeeping_pick"],
        options=done_indexes,
        default=default_indexes,
        format_func=lambda index: _done_housekeeping_label(
            done_tasks[index],
            index,
        ),
        key=f"evidence_review_done_housekeeping_pick_{selected}",
    )
    picked = sorted(
        {
            int(index)
            for index in picked
            if 0 <= int(index) < len(done_tasks)
        }
    )
    contains_uncrystallized = any(
        not bool(getattr(done_tasks[index], "crystallized", False))
        for index in picked
    )
    uncrystallized_confirmed = True
    if contains_uncrystallized:
        st.warning(ui["done_housekeeping_uncrystallized_warning"])
        uncrystallized_confirmed = st.checkbox(
            ui["done_housekeeping_confirm_uncrystallized"],
            value=False,
            key=f"evidence_review_done_housekeeping_uncrystallized_{selected}",
        )

    c1, c2 = st.columns(2)
    with c1:
        confirm_archive = st.checkbox(
            ui["done_housekeeping_confirm_archive"],
            value=False,
            key=f"evidence_review_done_housekeeping_confirm_archive_{selected}",
        )
        archive_clicked = st.button(
            ui["done_housekeeping_archive"],
            disabled=not picked or not confirm_archive or not uncrystallized_confirmed,
            key=f"evidence_review_done_housekeeping_archive_{selected}",
            use_container_width=True,
        )
    with c2:
        confirm_delete = st.checkbox(
            ui["done_housekeeping_confirm_delete"],
            value=False,
            key=f"evidence_review_done_housekeeping_confirm_delete_{selected}",
        )
        delete_clicked = st.button(
            ui["done_housekeeping_delete"],
            disabled=not picked or not confirm_delete or not uncrystallized_confirmed,
            key=f"evidence_review_done_housekeeping_delete_{selected}",
            use_container_width=True,
        )

    if archive_clicked:
        assert_files_current([_archive_path, _kanban_path, _project_path])
        updated = archive_kanban_done_tasks(selected, sections, picked)
        sync_project_board_from_kanban(selected, updated)
        refresh_file_snapshots([_archive_path, _kanban_path, _project_path])
        stash_git_backup_results()
        clear_web_cache()
        st.success(ui["done_housekeeping_archived"].format(n=len(picked)))
        st.rerun()

    if delete_clicked:
        assert_files_current([_kanban_path, _project_path])
        updated = {
            section: list(tasks)
            for section, tasks in sections.items()
        }
        remaining_done = list(done_tasks)
        for index in sorted(picked, reverse=True):
            remaining_done.pop(index)
        updated[KANBAN_DONE] = remaining_done
        save_kanban(selected, updated)
        sync_project_board_from_kanban(selected, updated)
        refresh_file_snapshots([_kanban_path, _project_path])
        stash_git_backup_results()
        clear_web_cache()
        st.success(ui["done_housekeeping_deleted"].format(n=len(picked)))
        st.rerun()


def _link_evidence_to_skills(evidence_id: str, skill_ids: list[str]) -> None:
    """Append an evidence ref to selected skill nodes."""
    tree = load_skill_tree_raw(selected)
    if not isinstance(tree, dict):
        st.error("skill-tree.yaml not found.")
        return
    nodes = [
        dict(node)
        for node in (tree.get("nodes") or [])
        if isinstance(node, dict)
    ]
    by_id: dict[str, dict] = {}
    for node in nodes:
        node_id = str(node.get("id", "") or "").strip()
        if node_id:
            by_id[node_id] = node
    for skill_id in skill_ids:
        if skill_id not in by_id:
            node = {
                "id": skill_id,
                "status": "learning",
                "evidence_refs": [evidence_id],
            }
            nodes.append(node)
            by_id[skill_id] = node
            continue
        node = by_id[skill_id]
        refs = [
            str(ref).strip()
            for ref in (node.get("evidence_refs") or [])
            if str(ref).strip()
        ]
        if evidence_id not in refs:
            refs.append(evidence_id)
        node["evidence_refs"] = refs
    tree["nodes"] = nodes
    _save_tree(tree, ui["link_done"])


def _render_done_ingest(review: dict) -> None:
    st.subheader(ui["done_queue_title"])
    sections = parse_kanban(selected)
    pending_done = [
        task
        for task in (sections.get(KANBAN_DONE) or [])
        if not getattr(task, "crystallized", False)
    ]
    allow_status_key = f"evidence_review_allow_status_{selected}"
    allow_status = bool(st.session_state.get(allow_status_key, False))
    if not pending_done:
        st.caption(ui["done_queue_empty"])
    else:
        pick = st.multiselect(
            ui["done_pick"],
            options=list(range(len(pending_done))),
            format_func=lambda i: pending_done[i].title,
            key=f"evidence_review_done_pick_{selected}",
        )
        allow_status = st.checkbox(
            ui["done_allow_status"],
            value=False,
            key=allow_status_key,
        )
        st.caption(ui["done_allow_status_help"])
        if st.button(
            ui["done_generate"],
            key=f"evidence_review_done_generate_{selected}",
        ) and pick:
            chosen = [pending_done[i] for i in pick]
            ai_backend = kanban_ai_backend(selected)
            if ai_backend == "llm" and not llm_client.is_configured():
                render_llm_unavailable(ui)
            else:
                with st.spinner(ui["done_spinner"]):
                    patch, err = ingest_kanban_done_json(
                        selected,
                        chosen,
                        goal_context=current_goal_agent_context(selected),
                        ai_backend=ai_backend,
                    )
                if err is not None:
                    st.error(err)
                elif patch is not None:
                    source_projects = project_refs_for_tasks(chosen)
                    patch = add_project_refs_to_ingest_patch(patch, source_projects)
                    st.session_state[f"evidence_review_patch_{selected}"] = patch
                    st.session_state[f"evidence_review_done_titles_{selected}"] = [
                        task.title for task in chosen
                    ]
                    st.session_state[f"evidence_review_done_ids_{selected}"] = [
                        task.id for task in chosen if task.id
                    ]
                    st.session_state[f"evidence_review_done_projects_{selected}"] = (
                        source_projects
                    )
                    st.rerun()

    patch_key = f"evidence_review_patch_{selected}"
    if patch_key not in st.session_state:
        _render_review_lists(review)
        st.divider()
        _render_done_housekeeping(sections)
        return

    raw_patch = st.session_state[patch_key]
    parsed = parse_ingest_patch(raw_patch)
    include_evidence: list[bool] = []
    include_nodes: list[bool] = []

    st.markdown(f"**{ui['review_rows_title']}**")
    for idx, row in enumerate(parsed.evidence_entries):
        title = str(row.get("title", "") or "")[:90]
        c1, c2 = st.columns([1, 5])
        with c1:
            include_evidence.append(
                st.checkbox(
                    "Adopt",
                    value=True,
                    key=f"evidence_review_ev_{selected}_{idx}",
                    label_visibility="collapsed",
                )
            )
        with c2:
            st.caption(title or f"evidence {idx + 1}")

    for idx, row in enumerate(parsed.node_updates):
        node_id = str(row.get("id", "") or "")
        c1, c2 = st.columns([1, 5])
        with c1:
            include_nodes.append(
                st.checkbox(
                    "Adopt",
                    value=True,
                    key=f"evidence_review_node_{selected}_{idx}",
                    label_visibility="collapsed",
                )
            )
        with c2:
            st.caption(f"`{node_id}`")

    filtered, warnings = filter_ingest_patch(
        raw_patch,
        include_evidence=include_evidence if parsed.evidence_entries else None,
        include_nodes=include_nodes if parsed.node_updates else None,
    )
    for warning in warnings:
        st.caption(f"- {warning}")

    mark_crystallized = st.checkbox(
        ui["done_mark_crystallized"],
        value=True,
        key=f"evidence_review_mark_crystallized_{selected}",
    )
    source_titles = st.session_state.get(
        f"evidence_review_done_titles_{selected}",
        [],
    )
    source_ids = st.session_state.get(
        f"evidence_review_done_ids_{selected}",
        [],
    )
    source_projects = st.session_state.get(
        f"evidence_review_done_projects_{selected}",
        [],
    )
    if isinstance(source_titles, list) and source_titles:
        st.caption(
            ui["done_preview_source"].format(
                sources="; ".join(str(item) for item in source_titles),
            )
        )
    if isinstance(source_projects, list) and source_projects:
        st.caption(
            ui.get("ingest_preview_projects", "Projects: {projects}").format(
                projects=", ".join(str(item) for item in source_projects),
            )
        )

    pool_raw = load_evidence_pool_raw(selected)
    tree_raw = load_skill_tree_raw(selected)
    merged = merge_ingest_patch(
        selected,
        pool_raw,
        tree_raw,
        filtered,
        allow_status_change=allow_status,
        bump_locked_with_evidence=True,
    )
    if not merged.ok:
        for error in merged.errors:
            st.error(error)
        return
    for warning in merged.warnings:
        st.caption(f"- {warning}")

    labels = schema_node_labels(tree_raw)
    new_ev, tree_delta = ingest_preview_delta(
        pool_raw,
        tree_raw,
        merged.merged_pool,
        merged.merged_tree,
        labels,
    )
    with st.expander(ui["merge_preview_title"], expanded=True):
        for line in new_ev:
            st.markdown(f"- {line}")
        for line in tree_delta:
            st.markdown(f"- {line}")

    if merged.merged_pool:
        with st.expander(ui["merge_preview_pool"], expanded=False):
            st.code(
                yaml.dump(
                    merged.merged_pool,
                    allow_unicode=True,
                    default_flow_style=False,
                    sort_keys=False,
                ),
                language="yaml",
            )
    if merged.merged_tree:
        with st.expander(ui["merge_preview_tree"], expanded=False):
            st.code(
                yaml.dump(
                    merged.merged_tree,
                    allow_unicode=True,
                    default_flow_style=False,
                    sort_keys=False,
                ),
                language="yaml",
            )

    ac1, ac2 = st.columns(2)
    with ac1:
        apply_selected = st.button(
            ui["done_apply_selected"],
            type="primary",
            key=f"evidence_review_apply_selected_{selected}",
        )
    with ac2:
        apply_all = st.button(
            ui["done_apply_all"],
            key=f"evidence_review_apply_all_{selected}",
        )
    if not (apply_selected or apply_all):
        return
    assert_files_current([_pool_path, _tree_path, _skill_path])
    patch_to_apply = filtered if apply_selected else raw_patch
    _, applied = run_ingest_patch(
        selected,
        patch_to_apply,
        allow_status_change=allow_status,
        bump_locked_with_evidence=True,
        dry_run=False,
    )
    source_title_set = (
        {str(item) for item in source_titles}
        if isinstance(source_titles, list)
        else set()
    )
    source_id_set = (
        {str(item) for item in source_ids}
        if isinstance(source_ids, list)
        else set()
    )
    if not applied.ok:
        _record_done_ingest_activity(
            title=(
                "Failed selected Done -> Evidence candidates"
                if apply_selected
                else "Failed all Done -> Evidence candidates"
            ),
            source_ids=source_id_set,
            source_titles=source_title_set,
            warnings=list(applied.warnings),
            error="; ".join(applied.errors),
            status="failed",
        )
        for error in applied.errors:
            st.error(error)
        for warning in applied.warnings:
            st.warning(warning)
        return
    if mark_crystallized and isinstance(source_titles, list):
        _mark_done_crystallized(
            source_id_set,
            source_title_set,
        )
    refresh_file_snapshots([_pool_path, _tree_path, _skill_path])
    _record_done_ingest_activity(
        title=(
            "Applied selected Done -> Evidence candidates"
            if apply_selected
            else "Applied all Done -> Evidence candidates"
        ),
        source_ids=source_id_set,
        source_titles=source_title_set,
        warnings=list(applied.warnings),
    )
    stash_git_backup_results()
    clear_web_cache()
    st.success(ui["done_applied"])
    for key in (
        patch_key,
        f"evidence_review_done_titles_{selected}",
        f"evidence_review_done_ids_{selected}",
        f"evidence_review_done_projects_{selected}",
    ):
        st.session_state.pop(key, None)
    st.rerun()


def _render_review_lists(review: dict) -> None:
    needs_review = list(review.get("needs_review") or [])
    st.markdown(f"**{ui['review_rows_title']}**")
    if not needs_review:
        st.caption(ui["review_rows_empty"])
    for row in needs_review[:8]:
        st.caption(
            f"- `{row['id']}` {row['title']} - "
            f"{row.get('review_reason', '')}"
        )

    unlinked = list(review.get("unlinked") or [])
    st.markdown(f"**{ui['unlinked_rows_title']}**")
    if not unlinked:
        st.caption(ui["unlinked_rows_empty"])
    for row in unlinked[:8]:
        st.caption(f"- `{row['id']}` {row['title']}")


def _render_pool_form(
    entries: list[dict],
    *,
    row: dict | None = None,
    prefix: str,
) -> tuple[dict | None, bool, bool]:
    """Render one add/edit form and return row, update, deprecate flags."""
    existing = row or {}
    with st.form(prefix):
        c1, c2 = st.columns(2)
        with c1:
            evidence_id = st.text_input(
                ui["pool_id"],
                value=str(existing.get("id", "") or ""),
                disabled=row is not None,
            )
        with c2:
            ev_types = sorted(EVIDENCE_TYPES)
            current_type = str(existing.get("type", "practice") or "practice")
            if current_type not in ev_types:
                current_type = "practice"
            ev_type = st.selectbox(
                ui["pool_type"],
                ev_types,
                index=ev_types.index(current_type),
            )
        title = st.text_input(
            ui["pool_title"],
            value=str(existing.get("title", "") or ""),
        )
        c3, c4 = st.columns(2)
        with c3:
            date_value = st.text_input(
                ui["pool_date"],
                value=str(existing.get("date", "") or ""),
            )
        with c4:
            url = st.text_input(
                ui["pool_url"],
                value=str(existing.get("url", "") or ""),
            )
        summary = st.text_area(
            ui["pool_summary"],
            value=str(existing.get("summary", "") or ""),
            height=80,
        )
        c5, c6, c7, c8 = st.columns(4)
        with c5:
            strength_options = ["", *EVIDENCE_STRENGTHS]
            current_strength = str(existing.get("strength", "") or "")
            if current_strength not in strength_options:
                current_strength = ""
            strength = st.selectbox(
                ui["pool_strength"],
                strength_options,
                index=strength_options.index(current_strength),
                format_func=_strength_label,
            )
        with c6:
            confidence_options = ["", *EVIDENCE_CONFIDENCES]
            current_confidence = str(existing.get("confidence", "") or "")
            if current_confidence not in confidence_options:
                current_confidence = ""
            confidence = st.selectbox(
                ui["pool_confidence"],
                confidence_options,
                index=confidence_options.index(current_confidence),
                format_func=_confidence_label,
            )
        with c7:
            current_review = str(
                existing.get("review_status", "needs_review")
                or "needs_review"
            )
            if current_review not in EVIDENCE_REVIEW_STATUSES:
                current_review = "needs_review"
            review_status = st.selectbox(
                ui["pool_review_status"],
                list(EVIDENCE_REVIEW_STATUSES),
                index=list(EVIDENCE_REVIEW_STATUSES).index(current_review),
                format_func=_review_status_label,
            )
        with c8:
            current_public = str(
                existing.get("public_readiness", "private") or "private"
            )
            if current_public not in EVIDENCE_PUBLIC_READINESS:
                current_public = "private"
            public_readiness = st.selectbox(
                ui["pool_public_readiness"],
                list(EVIDENCE_PUBLIC_READINESS),
                index=list(EVIDENCE_PUBLIC_READINESS).index(current_public),
                format_func=_public_readiness_label,
            )
        source_refs = st.text_area(
            ui["pool_source_refs"],
            value=_lines_text(existing.get("source_refs")),
            height=70,
        )
        c_refs1, c_refs2 = st.columns(2)
        with c_refs1:
            project_refs = st.text_area(
                ui["pool_project_refs"],
                value=_lines_text(existing.get("project_refs")),
                height=70,
            )
        with c_refs2:
            experience_refs = st.text_area(
                ui["pool_experience_refs"],
                value=_lines_text(existing.get("experience_refs")),
                height=70,
            )
        replaced_by = ""
        if row is not None:
            replaced_by = st.text_input(
                ui["pool_replaced_by"],
                value=str(existing.get("replaced_by", "") or ""),
            )
        c9, c10 = st.columns(2)
        with c9:
            submitted = st.form_submit_button(
                ui["pool_update"] if row is not None else ui["pool_add"],
                type="primary",
            )
        with c10:
            deprecated = False
            if row is not None:
                deprecated = st.form_submit_button(ui["pool_deprecate"])
    if not (submitted or deprecated):
        return None, False, False

    clean_id = str(evidence_id or "").strip()
    clean_title = str(title or "").strip()
    if not clean_title:
        st.error(ui["pool_title_required"])
        return None, False, False
    existing_ids = {
        str(item.get("id", "") or "").strip()
        for item in entries
        if str(item.get("id", "") or "").strip()
    }
    if row is None:
        if clean_id and clean_id in existing_ids:
            st.error(ui["pool_id_exists"].format(id=clean_id))
            return None, False, False
        if not clean_id:
            clean_id = new_evidence_id(clean_title, existing_ids)
    next_row = _compact_row(
        {
            "id": clean_id,
            "type": ev_type,
            "title": clean_title,
            "date": date_value,
            "url": url,
            "summary": summary,
            "strength": strength,
            "confidence": confidence,
            "review_status": review_status,
            "public_readiness": public_readiness,
            "source_refs": _text_lines(source_refs),
            "project_refs": _text_lines(project_refs),
            "experience_refs": _text_lines(experience_refs),
            "deprecated": bool(existing.get("deprecated", False)),
            "replaced_by": replaced_by,
        }
    )
    if deprecated:
        next_row["deprecated"] = True
    return next_row, submitted, deprecated


def _render_pool_editor(review: dict) -> None:
    entries = _pool_entries()
    st.subheader(ui["pool_add_title"])
    new_row, add_submitted, _ = _render_pool_form(
        entries,
        prefix=f"evidence_review_add_{selected}",
    )
    if add_submitted and new_row is not None:
        entries.append(new_row)
        _save_pool(entries, ui["pool_added"])
        st.rerun()

    st.subheader(ui["pool_edit_title"])
    if not entries:
        st.caption(ui["pool_empty"])
        return
    for index, row in enumerate(entries):
        title = _row_label(row)
        if bool(row.get("deprecated", False)):
            title = f"{title} (deprecated)"
        with st.expander(title, expanded=False):
            next_row, updated, deprecated = _render_pool_form(
                entries,
                row=row,
                prefix=f"evidence_review_edit_{selected}_{index}",
            )
            if next_row is None:
                continue
            entries[index] = next_row
            _save_pool(
                entries,
                ui["pool_deprecated"] if deprecated else ui["pool_updated"],
            )
            st.rerun()


def _render_links(review: dict) -> None:
    rows = list(review.get("evidence_rows") or [])
    skill_options = list(review.get("skill_options") or [])
    st.subheader(ui["link_title"])
    if not rows:
        st.caption(ui["link_empty"])
        return
    evidence_id = st.selectbox(
        ui["link_pick_evidence"],
        options=[str(row.get("id", "")) for row in rows],
        format_func=lambda eid: next(
            (
                _row_label(row)
                for row in rows
                if str(row.get("id", "")) == eid
            ),
            eid,
        ),
        key=f"evidence_review_link_eid_{selected}",
    )
    current_row = next(
        (row for row in rows if str(row.get("id", "")) == evidence_id),
        {},
    )
    current_refs = set(current_row.get("skill_refs") or [])
    skill_ids = st.multiselect(
        ui["link_pick_skills"],
        options=[str(option.get("id", "")) for option in skill_options],
        default=[sid for sid in current_refs if sid],
        format_func=lambda sid: next(
            (
                _skill_label(option)
                for option in skill_options
                if str(option.get("id", "")) == sid
            ),
            sid,
        ),
        key=f"evidence_review_link_skills_{selected}",
    )
    if st.button(ui["link_button"], type="primary") and evidence_id:
        _link_evidence_to_skills(evidence_id, skill_ids)
        st.rerun()

    st.markdown(f"**{ui['unlinked_rows_title']}**")
    unlinked = list(review.get("unlinked") or [])
    if not unlinked:
        st.caption(ui["unlinked_rows_empty"])
    for row in unlinked[:12]:
        st.caption(f"- `{row['id']}` {row['title']}")


def _claim_source_score(row: dict) -> tuple[int, str]:
    """Sort better claim sources first."""
    score = 0
    if row.get("review_status") == "reviewed":
        score += 4
    if row.get("public_readiness") in ("draftable", "public_ready", "published"):
        score += 3
    for ref_key in ("skill_refs", "project_refs", "experience_refs", "source_refs"):
        if row.get(ref_key):
            score += 1
    return (-score, str(row.get("id", "")))


def _claim_candidate_key() -> str:
    return f"evidence_review_claim_candidates_{selected}"


def _render_claim_candidates(review: dict) -> None:
    """Generate and accept evidence-backed claim candidates."""
    st.subheader(ui["claim_candidates_title"])
    rows = sorted(list(review.get("evidence_rows") or []), key=_claim_source_score)
    if not rows:
        st.caption(ui["link_empty"])
        return

    default_ids = [str(row.get("id", "")) for row in rows[:3] if row.get("id")]
    picked = st.multiselect(
        ui["claim_pick_evidence"],
        options=[str(row.get("id", "")) for row in rows],
        default=default_ids,
        format_func=lambda eid: next(
            (
                _row_label(row)
                for row in rows
                if str(row.get("id", "")) == eid
            ),
            eid,
        ),
        key=f"evidence_review_claim_pick_{selected}",
    )
    if st.button(
        ui["claim_generate"],
        type="primary",
        disabled=not picked,
        key=f"evidence_review_claim_generate_{selected}",
    ):
        candidates = generate_claim_candidates(selected, picked)
        st.session_state[_claim_candidate_key()] = candidates
        if not candidates:
            st.warning(ui["claim_candidates_empty"])
        else:
            st.rerun()

    claims = [
        item
        for item in (review.get("claim_rows") or [])
        if isinstance(item, dict) and str(item.get("status", "accepted")) == "accepted"
    ]
    if claims:
        with st.expander(ui["claim_existing_title"], expanded=False):
            for claim in claims[:20]:
                st.caption(
                    f"- `{claim.get('id', '')}` "
                    f"{claim.get('text', '')}"
                )

    candidates = st.session_state.get(_claim_candidate_key(), [])
    if not isinstance(candidates, list) or not candidates:
        st.caption(ui["claim_candidates_empty"])
        return

    include: list[bool] = []
    st.markdown(f"**{ui['claim_candidates_preview']}**")
    for idx, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            include.append(False)
            continue
        with st.container(border=True):
            c1, c2 = st.columns([1, 6])
            with c1:
                include.append(
                    st.checkbox(
                        ui["claim_adopt"],
                        value=True,
                        key=f"evidence_review_claim_include_{selected}_{idx}",
                        label_visibility="collapsed",
                    )
                )
            with c2:
                st.markdown(str(candidate.get("text", "") or ""))
                meta = [
                    f"`{candidate.get('type', '')}`",
                    ui["claim_evidence_refs"].format(
                        refs=", ".join(candidate.get("evidence_refs") or []) or "-"
                    ),
                    ui["claim_skill_refs"].format(
                        refs=", ".join(candidate.get("skill_refs") or []) or "-"
                    ),
                    ui["claim_public_readiness"].format(
                        value=_public_readiness_label(
                            str(candidate.get("public_readiness", "") or "private")
                        )
                    ),
                    ui["claim_confidence"].format(
                        value=_confidence_label(
                            str(candidate.get("confidence", "") or "medium")
                        )
                    ),
                ]
                st.caption(" · ".join(meta))
                warnings = candidate.get("warnings") or []
                if isinstance(warnings, list):
                    for warning in warnings:
                        st.caption(f"- {warning}")

    selected_candidates = [
        candidate
        for candidate, selected_flag in zip(candidates, include, strict=False)
        if selected_flag and isinstance(candidate, dict)
    ]
    if not st.button(
        ui["claim_apply_selected"].format(n=len(selected_candidates)),
        type="primary",
        disabled=not selected_candidates,
        key=f"evidence_review_claim_apply_{selected}",
    ):
        return

    pool_raw = load_evidence_pool_raw(selected) or {
        "profile": selected,
        "evidence_entries": _pool_entries(),
    }
    skill_ids = {
        str(option.get("id", "") or "")
        for option in (review.get("skill_options") or [])
        if str(option.get("id", "") or "")
    }
    merged_pool, applied, warnings = apply_claim_candidates(
        pool_raw,
        selected_candidates,
        known_skill_ids=skill_ids,
    )
    for warning in warnings:
        st.warning(warning)
    if not applied:
        st.warning(ui["claim_apply_empty"])
        return
    _save_pool_raw(merged_pool, ui["claim_applied"].format(n=len(applied)))
    st.session_state.pop(_claim_candidate_key(), None)
    st.rerun()


def _option_label(option: dict) -> str:
    """Render a compact id/status option label."""
    label = str(option.get("label", "") or option.get("id", ""))
    option_id = str(option.get("id", "") or "")
    status = str(option.get("status", "") or "")
    suffix = f" · {status}" if status else ""
    return f"{label} ({option_id}){suffix}"


def _existing_ref_defaults(refs: object, options: list[str]) -> list[str]:
    """Keep defaults valid for Streamlit multiselect options."""
    allowed = set(options)
    return [ref for ref in _clean_refs(refs) if ref in allowed]


def _clean_refs(refs: object) -> list[str]:
    """Normalize ref values to unique non-empty strings."""
    if not isinstance(refs, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for ref in refs:
        clean = str(ref).strip()
        if clean and clean not in seen:
            seen.add(clean)
            out.append(clean)
    return out


def _save_experience_book_for_page(book, message: str) -> None:
    """Persist experience.yaml from Evidence Review."""
    assert_files_current([_experience_path])
    save_experience_book(selected, book)
    refresh_file_snapshots([_experience_path])
    stash_git_backup_results()
    clear_web_cache()
    st.success(message)


def _render_case_options(review: dict) -> None:
    """Display currently available refs targets."""
    st.subheader(ui["refs_options_title"])
    c1, c2, c3 = st.columns(3)
    option_sets = (
        (c1, ui["refs_projects"], review.get("project_options") or []),
        (c2, ui["refs_experiences"], review.get("experience_options") or []),
        (c3, ui["refs_sources"], review.get("source_options") or []),
    )
    for column, title, options in option_sets:
        with column:
            st.markdown(f"**{title}**")
            if not options:
                st.caption(ui["refs_options_empty"])
                continue
            for option in options[:12]:
                st.caption(f"- `{option.get('id', '')}` {option.get('label', '')}")


def _render_evidence_ref_linker(review: dict) -> None:
    """Edit evidence row refs to project, experience, and source records."""
    rows = list(review.get("evidence_rows") or [])
    if not rows:
        st.caption(ui["link_empty"])
        return
    project_options = list(review.get("project_options") or [])
    experience_options = list(review.get("experience_options") or [])
    source_options = list(review.get("source_options") or [])
    project_ids = [str(option.get("id", "")) for option in project_options]
    experience_ids = [str(option.get("id", "")) for option in experience_options]
    source_ids = [str(option.get("id", "")) for option in source_options]

    st.subheader(ui["refs_linker_title"])
    evidence_id = st.selectbox(
        ui["link_pick_evidence"],
        options=[str(row.get("id", "")) for row in rows],
        format_func=lambda eid: next(
            (
                _row_label(row)
                for row in rows
                if str(row.get("id", "")) == eid
            ),
            eid,
        ),
        key=f"evidence_review_refs_eid_{selected}",
    )
    current = next(
        (row for row in rows if str(row.get("id", "")) == evidence_id),
        {},
    )
    project_refs = st.multiselect(
        ui["pool_project_refs"],
        options=project_ids,
        default=_existing_ref_defaults(current.get("project_refs"), project_ids),
        format_func=lambda pid: next(
            (
                _option_label(option)
                for option in project_options
                if str(option.get("id", "")) == pid
            ),
            pid,
        ),
        key=f"evidence_review_refs_projects_{selected}",
    )
    experience_refs = st.multiselect(
        ui["pool_experience_refs"],
        options=experience_ids,
        default=_existing_ref_defaults(
            current.get("experience_refs"),
            experience_ids,
        ),
        format_func=lambda eid: next(
            (
                _option_label(option)
                for option in experience_options
                if str(option.get("id", "")) == eid
            ),
            eid,
        ),
        key=f"evidence_review_refs_experiences_{selected}",
    )
    source_refs = st.multiselect(
        ui["pool_source_refs"],
        options=source_ids,
        default=_existing_ref_defaults(current.get("source_refs"), source_ids),
        format_func=lambda sid: next(
            (
                _option_label(option)
                for option in source_options
                if str(option.get("id", "")) == sid
            ),
            sid,
        ),
        key=f"evidence_review_refs_sources_{selected}",
    )
    manual_refs = st.text_area(
        ui["refs_manual_source_refs"],
        value="\n".join(
            ref
            for ref in _clean_refs(current.get("source_refs"))
            if ref not in set(source_ids)
        ),
        height=70,
    )
    if not st.button(ui["refs_save"], type="primary"):
        return

    entries = _pool_entries()
    for index, row in enumerate(entries):
        if str(row.get("id", "") or "") != evidence_id:
            continue
        updated = dict(row)
        updated["project_refs"] = project_refs
        updated["experience_refs"] = experience_refs
        updated["source_refs"] = [*source_refs, *_text_lines(manual_refs)]
        entries[index] = _compact_row(updated)
        _save_pool(entries, ui["refs_saved"])
        st.rerun()
    st.error(ui["refs_evidence_missing"])


def _render_experience_case_form(book, *, case=None, prefix: str) -> None:
    """Render an add/edit form for one experience case."""
    existing = case
    with st.form(prefix):
        case_id = st.text_input(
            ui["refs_case_id"],
            value=getattr(existing, "id", ""),
            disabled=existing is not None,
        )
        organization = st.text_input(
            ui["refs_experience_organization"],
            value=getattr(existing, "organization", ""),
        )
        role = st.text_input(
            ui["refs_experience_role"],
            value=getattr(existing, "role", ""),
        )
        location = st.text_input(
            ui["refs_experience_location"],
            value=getattr(existing, "location", ""),
        )
        c1, c2 = st.columns(2)
        with c1:
            current_status = getattr(existing, "status", "active")
            status = st.selectbox(
                ui["refs_status"],
                EXPERIENCE_STATUSES,
                index=EXPERIENCE_STATUSES.index(current_status)
                if current_status in EXPERIENCE_STATUSES
                else 0,
            )
        with c2:
            current_visibility = getattr(existing, "visibility", "private")
            visibility = st.selectbox(
                ui["refs_visibility"],
                EXPERIENCE_VISIBILITIES,
                index=EXPERIENCE_VISIBILITIES.index(current_visibility)
                if current_visibility in EXPERIENCE_VISIBILITIES
                else 0,
            )
        time_range = st.text_input(
            ui["refs_time_range"],
            value=getattr(existing, "time_range", ""),
        )
        summary = st.text_area(
            ui["refs_summary"],
            value=getattr(existing, "summary", ""),
            height=80,
        )
        c3, c4 = st.columns(2)
        with c3:
            project_refs = st.text_area(
                ui["pool_project_refs"],
                value=_lines_text(getattr(existing, "project_refs", [])),
                height=70,
            )
        with c4:
            source_refs = st.text_area(
                ui["pool_source_refs"],
                value=_lines_text(getattr(existing, "source_refs", [])),
                height=70,
            )
        notes = st.text_area(
            ui["refs_notes"],
            value=getattr(existing, "notes", ""),
            height=80,
        )
        submitted = st.form_submit_button(
            ui["pool_update"] if existing is not None else ui["refs_add_experience"],
            type="primary",
        )
    if not submitted:
        return
    try:
        if existing is None:
            add_experience_case(
                book,
                organization,
                case_id=case_id,
                role=role,
                location=location,
                status=status,
                time_range=time_range,
                summary=summary,
                project_refs=_text_lines(project_refs),
                source_refs=_text_lines(source_refs),
                visibility=visibility,
                notes=notes,
            )
        else:
            update_experience_case(
                book,
                existing.id,
                organization=organization,
                role=role,
                location=location,
                status=status,
                time_range=time_range,
                summary=summary,
                project_refs=_text_lines(project_refs),
                source_refs=_text_lines(source_refs),
                visibility=visibility,
                notes=notes,
            )
    except ValueError as exc:
        st.error(str(exc))
        return
    _save_experience_book_for_page(book, ui["refs_case_saved"])
    st.rerun()


def _render_case_editor() -> None:
    """Render project-board handoff and minimal experience case editor."""
    st.subheader(ui["refs_case_editor_title"])
    book = load_experience_book(selected)
    st.page_link(
        "pages/11_Project_Board.py",
        label=ui["refs_open_project_board"],
    )
    with st.expander(
        ui["refs_add_experience"],
        expanded=not book.experience_cases,
    ):
        _render_experience_case_form(
            book,
            prefix=f"evidence_review_experience_add_{selected}",
        )
    for case in book.experience_cases:
        label = " · ".join(
            item for item in (case.organization, case.role) if item
        )
        with st.expander(f"{label or case.id} · {case.status}"):
            _render_experience_case_form(
                book,
                case=case,
                prefix=f"evidence_review_experience_{selected}_{case.id}",
            )


def _render_refs(review: dict) -> None:
    """Render project/experience/source refs tooling."""
    _render_case_options(review)
    st.divider()
    _render_evidence_ref_linker(review)
    st.divider()
    _render_case_editor()


def _render_risks(review: dict) -> None:
    risks = list(review.get("status_risks") or [])
    if not risks:
        st.success(ui["risk_empty"])
        return
    for risk in risks:
        label = str(risk.get("label", "") or risk.get("id", ""))
        st.warning(
            ui["risk_line"].format(
                label=label,
                status=risk.get("status", ""),
                highest=_strength_label(risk.get("highest_strength", "")),
                required=_strength_label(risk.get("required_strength", "")),
            )
        )
    st.page_link("pages/1_Skill_Tree.py", label=ui["open_skill_tree"])


review_payload = build_evidence_review(selected)
summary = review_payload.get("summary") or {}

head_l, head_goal = st.columns([5, 2], gap="medium", vertical_alignment="top")
with head_l:
    st.title(ui["title"])
    st.caption(ui["page_context_line"])
with head_goal:
    render_current_goal_strip(selected, compact=True, align="right")

m1, m2, m3, m4 = st.columns(4)
m1.metric(
    ui["metric_done_uncrystallized"],
    summary.get("done_uncrystallized_count", 0),
)
m2.metric(ui["metric_unlinked"], summary.get("unlinked_count", 0))
m3.metric(ui["metric_needs_review"], summary.get("needs_review_count", 0))
m4.metric(ui["metric_status_risk"], summary.get("status_risk_count", 0))

tabs = st.tabs(
    [
        ui["tab_queue"],
        ui["tab_claims"],
        ui["tab_pool"],
        ui["tab_links"],
        ui["tab_refs"],
        ui["tab_risks"],
    ]
)
with tabs[0]:
    _render_done_ingest(review_payload)
with tabs[1]:
    _render_claim_candidates(review_payload)
with tabs[2]:
    _render_pool_editor(review_payload)
with tabs[3]:
    _render_links(review_payload)
with tabs[4]:
    _render_refs(review_payload)
with tabs[5]:
    _render_risks(review_payload)
