"""Evidence Review -- triage Done work, pool rows, links, and risks."""

from __future__ import annotations

from datetime import date
from dataclasses import replace

import pandas as pd
import streamlit as st
import yaml

from nblane.core import llm as llm_client
from nblane.core.claims import (
    apply_claim_candidates_to_book,
    claim_book_path,
    generate_claim_candidates,
    generate_claim_candidates_for_scope,
    legacy_claims,
    load_claim_book,
    migrate_legacy_claims,
    refresh_claim_statuses,
    save_claim_book,
)
from nblane.core.evidence_pool_id import new_evidence_id
from nblane.core.kanban_archive import (
    add_kanban_refs_to_ingest_patch,
    find_kanban_tasks_by_ref,
    kanban_ref_id,
    kanban_refs_for_tasks,
)
from nblane.core.evidence_review import (
    apply_pool_edits,
    apply_project_ref_inferences,
    build_evidence_review,
    bulk_set_pool_field,
    link_skill_to_evidence_nodes,
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
from nblane.core.profile_ingest_llm import (
    ingest_kanban_done_json,
    reformat_evidence,
)
from nblane.core.evidence_migrate import (
    backfill_row,
    migrate_evidence_pool,
    refresh_from_crystallized_tasks,
)
from nblane.core.evidence_from_output import evidence_row_from_output
from nblane.core.evidence_dedup import (
    apply_merge_or_deprecate,
    find_duplicate_candidates,
    suggest_duplicates_ai,
)
from nblane.evidence_editor_component import (
    evidence_editor_component_available,
)
from nblane.evidence_editor_host import (
    EvidenceEditorHost,
    compact_evidence_row,
)
from nblane.core.project_board_sync import (
    add_project_refs_to_ingest_patch,
    project_refs_for_tasks,
    sync_project_board_from_kanban,
)
from nblane.core.review_actions import record_writeback_activity
from nblane.core.sync import write_generated_blocks
from nblane.core.web_preferences import (
    AI_ACTION_DEFAULT_BACKENDS,
    load_web_preferences,
    update_web_preferences,
)
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
    kanban_ai_backend,
    render_action_ai_settings,
    render_current_goal_strip,
    render_git_backup_notices,
    render_llm_unavailable,
    select_profile,
    stash_git_backup_results,
)

_EVIDENCE_AI_ACTIONS = ("kanban.subtasks", "kanban.task_alignment")

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


def _render_evidence_review_help() -> None:
    st.markdown(ui.get("evidence_help_body", ""))


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
    """Drop empty optional fields before writing YAML.

    Thin wrapper over the shared host helper so the fallback Python sections and
    the React editor host stay in lockstep (single source of truth).
    """
    return compact_evidence_row(row)


def _row_label(row: dict) -> str:
    eid = str(row.get("id", "") or "").strip()
    title = str(row.get("title", "") or "").strip()
    return f"{eid} - {title}" if title else eid


def _render_kanban_source(row: dict, *, key: str) -> None:
    """Show the originating kanban task(s) for one evidence row.

    Resolves ``kanban_refs`` live from kanban.md / kanban-archive.md so the
    reviewer can recall what was actually done, with the AI ``source_excerpt``
    quote as a fallback when the task can no longer be found.
    """
    refs = [
        str(r).strip()
        for r in (row.get("kanban_refs") or [])
        if str(r).strip()
    ]
    excerpt = str(row.get("source_excerpt", "") or "").strip()
    if not refs and not excerpt:
        return
    with st.expander(ui.get("kanban_source_title", "Kanban source"), expanded=False):
        tasks = find_kanban_tasks_by_ref(selected, refs) if refs else []
        found_ids = {str(getattr(t, "id", "") or "").strip() for t in tasks}
        for task in tasks:
            title = str(getattr(task, "title", "") or "").strip()
            st.markdown(f"**{title}**")
            meta_bits = []
            context = str(getattr(task, "context", "") or "").strip()
            outcome = str(getattr(task, "outcome", "") or "").strip()
            if context:
                meta_bits.append(f"context: {context}")
            if outcome:
                meta_bits.append(f"outcome: {outcome}")
            for bit in meta_bits:
                st.caption(bit)
            started = str(getattr(task, "started_on", "") or "").strip()
            completed = str(getattr(task, "completed_on", "") or "").strip()
            if started or completed:
                st.caption(
                    ui.get(
                        "kanban_source_meta",
                        "started {started} · completed {completed}",
                    ).format(started=started or "—", completed=completed or "—")
                )
            subtasks = [
                st_item
                for st_item in (getattr(task, "subtasks", []) or [])
                if str(getattr(st_item, "title", "") or "").strip()
            ]
            for st_item in subtasks:
                mark = "x" if getattr(st_item, "done", False) else " "
                st.caption(f"- [{mark}] {st_item.title}")
        for ref in refs:
            rid = kanban_ref_id(ref)
            if rid and rid not in found_ids:
                st.caption(
                    ui.get(
                        "kanban_source_missing",
                        "No kanban task found for {ref}.",
                    ).format(ref=rid)
                )
        if excerpt:
            st.caption(f"{ui.get('kanban_source_excerpt', 'Excerpt')}: {excerpt}")
        if not refs and not tasks and not excerpt:
            st.caption(ui.get("kanban_source_empty", "No kanban task linked."))


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


def _active_evidence_task_ids() -> set[str]:
    """Task ids referenced by active evidence provenance."""
    out: set[str] = set()
    for row in _pool_entries():
        if bool(row.get("deprecated", False)):
            continue
        if str(row.get("origin", "") or "").strip() == "kanban_task":
            rid = kanban_ref_id(str(row.get("origin_ref", "") or ""))
            if rid:
                out.add(rid)
        for ref in row.get("kanban_refs") or []:
            rid = kanban_ref_id(str(ref or ""))
            if rid:
                out.add(rid)
    return out


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
        protected_task_ids = _active_evidence_task_ids()
        blocked = [
            str(getattr(done_tasks[index], "id", "") or "").strip()
            for index in picked
            if str(getattr(done_tasks[index], "id", "") or "").strip()
            in protected_task_ids
        ]
        if blocked:
            st.error(
                ui.get(
                    "done_housekeeping_delete_blocked_evidence",
                    "Delete blocked: active evidence references task(s): {ids}. Archive instead.",
                ).format(ids=", ".join(blocked))
            )
            return
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


def _link_skill_to_evidence(skill_id: str, evidence_ids: list[str]) -> None:
    """Attach several evidence refs to a single skill node."""
    tree = load_skill_tree_raw(selected)
    if not isinstance(tree, dict):
        st.error("skill-tree.yaml not found.")
        return
    nodes = [
        dict(node)
        for node in (tree.get("nodes") or [])
        if isinstance(node, dict)
    ]
    tree["nodes"] = link_skill_to_evidence_nodes(nodes, skill_id, evidence_ids)
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
        with st.form(f"evidence_review_done_form_{selected}", clear_on_submit=False):
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
            generate_clicked = st.form_submit_button(ui["done_generate"])
        if generate_clicked and pick:
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
                    patch = add_kanban_refs_to_ingest_patch(
                        patch, kanban_refs_for_tasks(chosen)
                    )
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
    # Collected human-confirmed grades, written back to raw_patch before apply
    # so the merge preview and the saved pool reflect what the reviewer chose.
    graded_evidence: list[tuple[int, str, str]] = []

    node_labels = schema_node_labels(load_skill_tree_raw(selected))

    strength_options = ["", *EVIDENCE_STRENGTHS]
    confidence_options = ["", *EVIDENCE_CONFIDENCES]

    st.markdown(f"**{ui['review_rows_title']}**")
    st.caption(ui.get("done_grade_hint", ""))
    if parsed.evidence_entries:
        h1, h2, h3 = st.columns([6, 2, 2])
        h1.caption(ui.get("done_col_evidence", "证据"))
        h2.caption(ui["pool_strength"])
        h3.caption(ui["pool_confidence"])
    for idx, row in enumerate(parsed.evidence_entries):
        title = str(row.get("title", "") or "")[:90]
        c1, c2, c3 = st.columns([6, 2, 2], vertical_alignment="center")
        with c1:
            include_evidence.append(
                st.checkbox(
                    title or f"evidence {idx + 1}",
                    value=True,
                    key=f"evidence_review_ev_{selected}_{idx}",
                )
            )
        ai_strength = str(row.get("strength", "") or "")
        if ai_strength not in strength_options:
            ai_strength = ""
        ai_confidence = str(row.get("confidence", "") or "")
        if ai_confidence not in confidence_options:
            ai_confidence = ""
        with c2:
            chosen_strength = st.selectbox(
                ui["pool_strength"],
                strength_options,
                index=strength_options.index(ai_strength),
                format_func=_strength_label,
                key=f"evidence_review_ev_strength_{selected}_{idx}",
                label_visibility="collapsed",
            )
        with c3:
            chosen_confidence = st.selectbox(
                ui["pool_confidence"],
                confidence_options,
                index=confidence_options.index(ai_confidence),
                format_func=_confidence_label,
                key=f"evidence_review_ev_confidence_{selected}_{idx}",
                label_visibility="collapsed",
            )
        graded_evidence.append((idx, chosen_strength, chosen_confidence))
        _render_kanban_source(row, key=f"done_kanban_src_{selected}_{idx}")

    for idx, row in enumerate(parsed.node_updates):
        node_id = str(row.get("id", "") or "")
        label = node_labels.get(node_id, node_id)
        status = str(row.get("status", "") or "")
        refs = row.get("evidence_refs") or []
        ref_text = ", ".join(str(r) for r in refs) if isinstance(refs, list) else ""
        c1, c2 = st.columns([1, 8], vertical_alignment="center")
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
            meta = f"`{node_id}`"
            if status:
                meta += f" · {status}"
            if ref_text:
                meta += f" · {ui.get('done_node_refs', 'evidence')}: {ref_text}"
            st.caption(f"{label}  —  {meta}")

    # Write human-confirmed grades back to the patch so filter/merge/apply use
    # them. Reviewing means confirming the AI grade, not refilling it later.
    raw_entries = raw_patch.get("evidence_entries")
    if isinstance(raw_entries, list):
        for idx, strength_value, confidence_value in graded_evidence:
            if idx >= len(raw_entries) or not isinstance(raw_entries[idx], dict):
                continue
            if strength_value:
                raw_entries[idx]["strength"] = strength_value
            else:
                raw_entries[idx].pop("strength", None)
            if confidence_value:
                raw_entries[idx]["confidence"] = confidence_value
            else:
                raw_entries[idx].pop("confidence", None)

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


def _paginated_show(items: list, *, key: str, page_size: int = 20) -> list:
    """Return a slice of `items` based on session_state[`key`] page count.

    Renders a "Show more" / "Show less" pair below the rendered slice (call site
    is responsible for the actual rendering of the slice). Use after the slice
    is already rendered.
    """

    total = len(items)
    pages = max(1, int(st.session_state.get(key, 1) or 1))
    visible = pages * page_size
    return items[: min(visible, total)]


def _paginated_controls(items: list, *, key: str, page_size: int = 20) -> None:
    total = len(items)
    pages = max(1, int(st.session_state.get(key, 1) or 1))
    shown = min(pages * page_size, total)
    if total <= page_size:
        return
    cols = st.columns([1, 1, 6])
    with cols[0]:
        if shown < total and st.button(
            f"Show more ({shown}/{total})",
            key=f"{key}__more",
            use_container_width=True,
        ):
            st.session_state[key] = pages + 1
            st.rerun()
    with cols[1]:
        if pages > 1 and st.button("Reset", key=f"{key}__reset", use_container_width=True):
            st.session_state[key] = 1
            st.rerun()


def _render_review_lists(review: dict) -> None:
    needs_review = list(review.get("needs_review") or [])
    st.markdown(f"**{ui['review_rows_title']}**")
    if not needs_review:
        st.caption(ui["review_rows_empty"])
    needs_key = f"evidence_review_needs_pages_{selected}"
    for row in _paginated_show(needs_review, key=needs_key):
        st.caption(
            f"- `{row['id']}` {row['title']} - "
            f"{row.get('review_reason', '')}"
        )
    _paginated_controls(needs_review, key=needs_key)

    unlinked = list(review.get("unlinked") or [])
    st.markdown(f"**{ui['unlinked_rows_title']}**")
    if not unlinked:
        st.caption(ui["unlinked_rows_empty"])
    unlinked_key = f"evidence_review_unlinked_pages_{selected}"
    for row in _paginated_show(unlinked, key=unlinked_key):
        st.caption(f"- `{row['id']}` {row['title']}")
    _paginated_controls(unlinked, key=unlinked_key)


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
    toast_key = "evidence_review_pool_added_toast"
    if st.session_state.pop(toast_key, False):
        st.toast(ui["pool_added"], icon="✅")
    with st.expander(ui["pool_add_title"], expanded=False):
        new_row, add_submitted, _ = _render_pool_form(
            entries,
            prefix=f"evidence_review_add_{selected}",
        )
        if add_submitted and new_row is not None:
            entries.append(new_row)
            _save_pool(entries, ui["pool_added"])
            st.session_state[toast_key] = True
            st.rerun()

    st.subheader(ui["pool_edit_title"])
    if not entries:
        st.caption(ui["pool_empty"])
        return
    search_key = f"evidence_review_pool_search_{selected}"
    sort_key = f"evidence_review_pool_sort_{selected}"
    show_deprecated_key = f"evidence_review_pool_show_deprecated_{selected}"
    f1, f2, f3 = st.columns([3, 2, 2])
    with f1:
        query = st.text_input(
            ui.get("pool_search", "Search id / title / claim"),
            key=search_key,
        ).strip().lower()
    with f2:
        sort_choice = st.selectbox(
            ui.get("pool_sort", "Sort by"),
            options=["title", "id", "status", "updated_at"],
            format_func=lambda v: ui.get(f"pool_sort_{v}", v.replace("_", " ").title()),
            key=sort_key,
        )
    with f3:
        show_deprecated = st.checkbox(
            ui.get("pool_show_deprecated", "Include deprecated"),
            value=False,
            key=show_deprecated_key,
        )

    def _matches(row: dict) -> bool:
        if not show_deprecated and bool(row.get("deprecated", False)):
            return False
        if not query:
            return True
        haystacks = [
            str(row.get(field, "") or "").lower()
            for field in (
                "id",
                "title",
                "claim",
                "summary",
                "status",
                "review_status",
                "public_readiness",
            )
        ]
        return any(query in piece for piece in haystacks)

    indexed_entries = [(index, row) for index, row in enumerate(entries) if _matches(row)]

    sort_funcs = {
        "title": lambda pair: str(pair[1].get("title", "") or "").lower(),
        "id": lambda pair: str(pair[1].get("id", "") or "").lower(),
        "status": lambda pair: (
            str(pair[1].get("review_status", "") or "").lower(),
            str(pair[1].get("public_readiness", "") or "").lower(),
            str(pair[1].get("status", "") or "").lower(),
        ),
        "updated_at": lambda pair: str(pair[1].get("updated_at", "") or ""),
    }
    indexed_entries.sort(key=sort_funcs.get(sort_choice, sort_funcs["title"]))

    if not indexed_entries:
        st.caption(ui.get("pool_search_empty", "No evidence matches the current filters."))
        return

    pages_key = f"evidence_review_pool_pages_{selected}"
    visible_pairs = _paginated_show(indexed_entries, key=pages_key, page_size=20)

    st.caption(ui.get("pool_inline_hint", ""))

    # Quick-select toggles the table's _pick column for the visible page in one
    # click. Because st.data_editor keeps its own widget state, applying a new
    # default requires a fresh editor key, so each quick-select bumps a revision
    # counter; manual toggles between bumps are preserved.
    pick_mode_key = f"evidence_review_pool_pickmode_{selected}"
    editor_rev_key = f"evidence_review_pool_editor_rev_{selected}"
    pick_mode = st.session_state.get(pick_mode_key)
    editor_rev = int(st.session_state.get(editor_rev_key, 0))

    qs1, qs2, qs3, _qs_spacer = st.columns([2, 2, 2, 3])
    with qs1:
        if st.button(
            ui.get("pool_pick_page_all", "Select page"),
            key=f"evidence_review_pool_pick_all_{selected}",
            use_container_width=True,
        ):
            st.session_state[pick_mode_key] = "all"
            st.session_state[editor_rev_key] = editor_rev + 1
            st.rerun()
    with qs2:
        if st.button(
            ui.get("pool_pick_page_needs", "Select needs-review"),
            key=f"evidence_review_pool_pick_needs_{selected}",
            use_container_width=True,
        ):
            st.session_state[pick_mode_key] = "needs_review"
            st.session_state[editor_rev_key] = editor_rev + 1
            st.rerun()
    with qs3:
        if st.button(
            ui.get("pool_pick_clear", "Clear selection"),
            key=f"evidence_review_pool_pick_clear_{selected}",
            use_container_width=True,
        ):
            st.session_state[pick_mode_key] = "none"
            st.session_state[editor_rev_key] = editor_rev + 1
            st.rerun()

    def _default_pick(row: dict) -> bool:
        if pick_mode == "all":
            return True
        if pick_mode == "needs_review":
            return (
                str(row.get("review_status", "needs_review") or "needs_review")
                == "needs_review"
            )
        return False

    # Build the editable table from the visible page. Edits are matched back to
    # entries by id (not row position), so pagination/sort can't misroute them.
    strength_opts = ["", *EVIDENCE_STRENGTHS]
    confidence_opts = ["", *EVIDENCE_CONFIDENCES]
    review_opts = list(EVIDENCE_REVIEW_STATUSES)
    readiness_opts = list(EVIDENCE_PUBLIC_READINESS)

    table_rows = []
    for _index, row in visible_pairs:
        rid = str(row.get("id", "") or "")
        title = _row_label(row)
        if bool(row.get("deprecated", False)):
            title = f"{title} ⚠"
        table_rows.append(
            {
                "_pick": _default_pick(row),
                "id": rid,
                "title": title,
                "strength": str(row.get("strength", "") or ""),
                "confidence": str(row.get("confidence", "") or ""),
                "review_status": str(
                    row.get("review_status", "needs_review") or "needs_review"
                ),
                "public_readiness": str(
                    row.get("public_readiness", "private") or "private"
                ),
            }
        )
    df = pd.DataFrame(
        table_rows,
        columns=[
            "_pick",
            "id",
            "title",
            "strength",
            "confidence",
            "review_status",
            "public_readiness",
        ],
    )

    editor_key = f"evidence_review_pool_editor_{selected}_{editor_rev}"
    edited = st.data_editor(
        df,
        key=editor_key,
        hide_index=True,
        use_container_width=True,
        column_config={
            "_pick": st.column_config.CheckboxColumn(
                ui.get("pool_pick", "✓"), default=False, width="small"
            ),
            "id": st.column_config.TextColumn(ui["pool_id"], disabled=True),
            "title": st.column_config.TextColumn(
                ui["pool_title"], disabled=True, width="large"
            ),
            "strength": st.column_config.SelectboxColumn(
                ui["pool_strength"], options=strength_opts
            ),
            "confidence": st.column_config.SelectboxColumn(
                ui["pool_confidence"], options=confidence_opts
            ),
            "review_status": st.column_config.SelectboxColumn(
                ui["pool_review_status"], options=review_opts
            ),
            "public_readiness": st.column_config.SelectboxColumn(
                ui["pool_public_readiness"], options=readiness_opts
            ),
        },
        column_order=[
            "_pick",
            "title",
            "strength",
            "confidence",
            "review_status",
            "public_readiness",
            "id",
        ],
    )

    # --- Bulk apply to picked rows ---
    picked_ids = [
        str(r["id"])
        for r in edited.to_dict("records")
        if r.get("_pick") and str(r.get("id", ""))
    ]
    b1, b2, b3 = st.columns([2, 3, 2])
    with b1:
        bulk_field = st.selectbox(
            ui.get("pool_bulk_field", "Bulk field"),
            options=["review_status", "strength", "confidence", "public_readiness"],
            format_func=lambda f: ui.get(f"pool_{f}", f),
            key=f"evidence_review_pool_bulk_field_{selected}",
        )
    with b2:
        bulk_value_opts = {
            "review_status": review_opts,
            "strength": strength_opts,
            "confidence": confidence_opts,
            "public_readiness": readiness_opts,
        }[bulk_field]
        bulk_value = st.selectbox(
            ui.get("pool_bulk_value", "Set to"),
            options=bulk_value_opts,
            key=f"evidence_review_pool_bulk_value_{selected}",
        )
    with b3:
        bulk_label = ui.get("pool_bulk_apply", "Apply to selected ({n})")
        if st.button(
            bulk_label.format(n=len(picked_ids)),
            disabled=not picked_ids,
            key=f"evidence_review_pool_bulk_btn_{selected}",
        ):
            _, changed = bulk_set_pool_field(
                entries, picked_ids, bulk_field, bulk_value
            )
            _save_pool(entries, ui.get("pool_edits_saved", "Saved."))
            st.toast(
                ui.get("pool_bulk_done", "Updated {n} rows").format(n=changed),
                icon="✅",
            )
            st.rerun()

    # --- Apply bulk field to ALL filtered entries (across pages, ignoring the
    # per-page _pick checkboxes). This is the "do it in one shot" path: filter
    # with the search box, then set every match without paging through 20 at a
    # time. Picks above only cover the visible page.
    all_filtered_ids = [
        str(row.get("id", "") or "")
        for _i, row in indexed_entries
        if str(row.get("id", "") or "")
    ]
    all_label = ui.get("pool_bulk_apply_all", "Apply to ALL filtered ({n})")
    if st.button(
        all_label.format(n=len(all_filtered_ids)),
        disabled=not all_filtered_ids,
        key=f"evidence_review_pool_bulk_all_btn_{selected}",
    ):
        _, changed = bulk_set_pool_field(
            entries, all_filtered_ids, bulk_field, bulk_value
        )
        _save_pool(entries, ui.get("pool_edits_saved", "Saved."))
        st.toast(
            ui.get("pool_bulk_done", "Updated {n} rows").format(n=changed),
            icon="✅",
        )
        st.rerun()
    st.caption(ui.get("pool_bulk_all_hint", ""))

    # --- Save inline edits (batched, no per-cell rerun) ---
    if st.button(
        ui.get("pool_save_edits", "Save table edits"),
        type="primary",
        key=f"evidence_review_pool_save_edits_{selected}",
    ):
        edits: dict[str, dict[str, str]] = {}
        for rec in edited.to_dict("records"):
            rid = str(rec.get("id", ""))
            if not rid:
                continue
            edits[rid] = {
                "strength": str(rec.get("strength", "") or ""),
                "confidence": str(rec.get("confidence", "") or ""),
                "review_status": str(rec.get("review_status", "") or ""),
                "public_readiness": str(rec.get("public_readiness", "") or ""),
            }
        _, changed = apply_pool_edits(entries, edits)
        if changed:
            _save_pool(entries, ui.get("pool_edits_saved", "Saved."))
            st.toast(
                ui.get("pool_edits_done", "Saved {n} rows").format(n=changed),
                icon="✅",
            )
            st.rerun()
        else:
            st.toast(ui.get("pool_no_changes", "No changes"), icon="ℹ️")

    _paginated_controls(indexed_entries, key=pages_key, page_size=20)

    # --- Deep edit one row (summary / url / refs / deprecate) ---
    with st.expander(ui.get("pool_edit_detail", "Edit full details of one row"), expanded=False):
        id_to_index = {
            str(row.get("id", "")): index for index, row in indexed_entries
        }
        detail_id = st.selectbox(
            ui.get("pool_detail_pick", "Pick a row"),
            options=[str(row.get("id", "")) for _i, row in visible_pairs],
            format_func=lambda rid: next(
                (_row_label(row) for _i, row in visible_pairs if str(row.get("id", "")) == rid),
                rid,
            ),
            key=f"evidence_review_pool_detail_{selected}",
        )
        if detail_id and detail_id in id_to_index:
            target_index = id_to_index[detail_id]
            _render_kanban_source(
                entries[target_index],
                key=f"pool_kanban_src_{selected}_{target_index}",
            )
            next_row, updated, deprecated = _render_pool_form(
                entries,
                row=entries[target_index],
                prefix=f"evidence_review_edit_{selected}_{target_index}",
            )
            if next_row is not None:
                entries[target_index] = next_row
                _save_pool(
                    entries,
                    ui["pool_deprecated"] if deprecated else ui["pool_updated"],
                )
                st.rerun()


def _render_links(review: dict) -> None:
    rows = list(review.get("evidence_rows") or [])
    st.subheader(ui["link_title"])
    if not rows:
        st.caption(ui["link_empty"])
        return
    by_skill_tab, by_evidence_tab = st.tabs(
        [
            ui.get("link_by_skill", "By skill"),
            ui.get("link_by_evidence", "By evidence"),
        ]
    )
    with by_skill_tab:
        _render_links_by_skill(review)
    with by_evidence_tab:
        _render_links_by_evidence(review)


def _render_links_by_skill(review: dict) -> None:
    """Skill-centric view: pick a skill, see its gap, bulk-attach evidence."""
    summaries = list(review.get("skill_summaries") or [])
    all_rows = list(review.get("all_evidence_rows") or review.get("evidence_rows") or [])
    if not summaries:
        st.caption(ui.get("link_skill_empty", "No skills in the tree yet."))
        return

    # Gaps first: skills claiming a status their evidence can't support.
    def _gap_sort(s: dict) -> tuple:
        return (0 if s.get("risk_level") else 1, -int(s.get("evidence_count") or 0))

    ordered = sorted(summaries, key=_gap_sort)
    risky = [s for s in ordered if s.get("risk_level")]
    if risky:
        st.caption(
            ui.get("link_skill_gap", "⚠ {n} skills claim a status above their evidence").format(
                n=len(risky)
            )
        )

    def _skill_opt_label(sid: str) -> str:
        s = next((x for x in ordered if str(x.get("id", "")) == sid), None)
        if not s:
            return sid
        flag = "⚠ " if s.get("risk_level") else ""
        return (
            f"{flag}{s.get('label', sid)} · {s.get('status', '')} · "
            f"{ui.get('link_skill_col_evidence', 'evidence')}={s.get('evidence_count', 0)}"
        )

    skill_id = st.selectbox(
        ui.get("link_skill_pick", "Pick a skill"),
        options=[str(s.get("id", "")) for s in ordered],
        format_func=_skill_opt_label,
        key=f"evidence_review_link_skill_pick_{selected}",
    )
    chosen = next((s for s in ordered if str(s.get("id", "")) == skill_id), {})
    if chosen.get("risk_reason"):
        st.warning(chosen["risk_reason"])

    already = {str(r) for r in (chosen.get("active_evidence_refs") or [])}
    candidates = [
        row for row in all_rows if str(row.get("id", "")) not in already
    ]
    if already:
        st.caption(
            ui.get("link_skill_current", "Already linked: {ids}").format(
                ids=", ".join(sorted(already))
            )
        )
    evidence_ids = st.multiselect(
        ui.get("link_skill_evidence_pick", "Evidence to attach"),
        options=[str(row.get("id", "")) for row in candidates],
        format_func=lambda eid: next(
            (_row_label(row) for row in candidates if str(row.get("id", "")) == eid),
            eid,
        ),
        key=f"evidence_review_link_skill_ev_{selected}",
    )
    if st.button(
        ui.get("link_attach_to_skill", "Attach to skill"),
        type="primary",
        disabled=not (skill_id and evidence_ids),
        key=f"evidence_review_link_skill_btn_{selected}",
    ):
        _link_skill_to_evidence(skill_id, evidence_ids)
        st.rerun()


def _render_links_by_evidence(review: dict) -> None:
    """Evidence-centric view (original) + in-place unlinked actions."""
    rows = list(review.get("evidence_rows") or [])
    skill_options = list(review.get("skill_options") or [])
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
    skill_opt_ids = [str(option.get("id", "")) for option in skill_options]

    def _skill_fmt(sid: str) -> str:
        return next(
            (
                _skill_label(option)
                for option in skill_options
                if str(option.get("id", "")) == sid
            ),
            sid,
        )

    unlinked_links_key = f"evidence_review_links_unlinked_pages_{selected}"
    for row in _paginated_show(unlinked, key=unlinked_links_key):
        rid = str(row["id"])
        uc1, uc2, uc3 = st.columns([3, 4, 1], vertical_alignment="center")
        with uc1:
            st.caption(f"`{rid}` {row['title']}")
        with uc2:
            picks = st.multiselect(
                ui.get("link_inline_skills", "Skills"),
                options=skill_opt_ids,
                format_func=_skill_fmt,
                key=f"evidence_review_unlinked_skills_{selected}_{rid}",
                label_visibility="collapsed",
                placeholder=ui.get("link_inline_placeholder", "Attach to skills…"),
            )
        with uc3:
            if st.button(
                ui.get("link_inline_attach", "Link"),
                disabled=not picks,
                key=f"evidence_review_unlinked_btn_{selected}_{rid}",
            ):
                _link_evidence_to_skills(rid, picks)
                st.rerun()
    _paginated_controls(unlinked, key=unlinked_links_key)


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


def _claim_candidate_key(scope: str = "manual") -> str:
    return f"evidence_review_claim_candidates_{selected}_{scope}"


def _claim_meta(candidate: dict) -> list[str]:
    return [
        f"`{candidate.get('type', '')}`",
        f"`{candidate.get('status', 'accepted')}`",
        f"`{candidate.get('refresh_status', 'current')}`",
        ui["claim_evidence_refs"].format(
            refs=", ".join(candidate.get("evidence_refs") or []) or "-"
        ),
        ui["claim_skill_refs"].format(
            refs=", ".join(candidate.get("skill_refs") or []) or "-"
        ),
        ui.get("claim_project_refs", "Projects: {refs}").format(
            refs=", ".join(candidate.get("project_refs") or []) or "-"
        ),
        ui.get("claim_goal_refs", "Goals: {refs}").format(
            refs=", ".join(candidate.get("goal_refs") or []) or "-"
        ),
        ui["claim_public_readiness"].format(
            value=_public_readiness_label(
                str(candidate.get("public_readiness", "") or "private")
            )
        ),
        ui["claim_confidence"].format(
            value=_confidence_label(str(candidate.get("confidence", "") or "medium"))
        ),
    ]


def _apply_claim_candidates(candidates: list[dict], review: dict) -> None:
    skill_ids = {
        str(option.get("id", "") or "")
        for option in (review.get("skill_options") or [])
        if str(option.get("id", "") or "")
    }
    _, applied, warnings = apply_claim_candidates_to_book(
        selected,
        candidates,
        known_skill_ids=skill_ids,
    )
    for warning in warnings:
        st.warning(warning)
    if not applied:
        st.warning(ui["claim_apply_empty"])
        return
    clear_web_cache()
    stash_git_backup_results()
    st.success(ui["claim_applied"].format(n=len(applied)))
    st.rerun()


def _render_claim_candidate_preview(scope: str, review: dict) -> None:
    candidates = st.session_state.get(_claim_candidate_key(scope), [])
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
                        key=f"evidence_review_claim_include_{selected}_{scope}_{idx}",
                        label_visibility="collapsed",
                    )
                )
            with c2:
                st.markdown(str(candidate.get("text", "") or ""))
                st.caption(" · ".join(_claim_meta(candidate)))
                warnings = candidate.get("warnings") or []
                if isinstance(warnings, list):
                    for warning in warnings:
                        st.caption(f"- {warning}")
    selected_candidates = [
        candidate
        for candidate, selected_flag in zip(candidates, include, strict=False)
        if selected_flag and isinstance(candidate, dict)
    ]
    if st.button(
        ui["claim_apply_selected"].format(n=len(selected_candidates)),
        type="primary",
        disabled=not selected_candidates,
        key=f"evidence_review_claim_apply_{selected}_{scope}",
    ):
        _apply_claim_candidates(selected_candidates, review)


def _render_claim_overview(review: dict) -> None:
    legacy_rows = list(review.get("legacy_claim_rows") or [])
    st.caption(
        ui.get("claim_studio_caption", "Claims are stored in {path}.").format(
            path=str(claim_book_path(selected))
        )
    )
    if legacy_rows:
        st.warning(
            ui.get(
                "claim_legacy_warning",
                "Legacy claims still exist in evidence-pool.yaml.",
            )
        )
        if st.button(
            ui.get("claim_migrate_legacy", "Migrate legacy claims"),
            key=f"claim_migrate_legacy_{selected}",
        ):
            moved = migrate_legacy_claims(selected)
            clear_web_cache()
            stash_git_backup_results()
            st.success(
                ui.get("claim_migrated", "Migrated {n} claim(s).").format(n=moved)
            )
            st.rerun()
    claims = [
        item
        for item in (review.get("claim_rows") or [])
        if isinstance(item, dict)
    ]
    accepted = [claim for claim in claims if claim.get("status") == "accepted"]
    drafts = [claim for claim in claims if claim.get("status") == "draft"]
    stale = [
        claim for claim in claims if claim.get("refresh_status") == "needs_refresh"
    ]
    unsupported = [claim for claim in claims if not claim.get("evidence_refs")]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(ui.get("claim_metric_accepted", "Accepted"), len(accepted))
    m2.metric(ui.get("claim_metric_draft", "Draft"), len(drafts))
    m3.metric(ui.get("claim_metric_refresh", "Needs refresh"), len(stale))
    m4.metric(ui.get("claim_metric_unsupported", "Unsupported"), len(unsupported))
    if st.button(
        ui.get("claim_refresh_statuses", "Refresh claim statuses"),
        key=f"claim_refresh_statuses_{selected}",
    ):
        refresh_claim_statuses(selected)
        clear_web_cache()
        stash_git_backup_results()
        st.rerun()
    if not claims:
        st.caption(ui["claim_candidates_empty"])
        return
    for claim in claims[:30]:
        claim_id = str(claim.get("id", "") or "")
        with st.expander(
            f"{claim_id} · {claim.get('status', '')} · {claim.get('refresh_status', '')}",
            expanded=claim.get("refresh_status") == "needs_refresh",
        ):
            new_text = st.text_area(
                ui.get("claim_text", "Claim text"),
                value=str(claim.get("text", "") or ""),
                key=f"claim_text_{selected}_{claim_id}",
                height=90,
            )
            status_options = ["draft", "accepted", "deprecated", "dismissed"]
            current_status = str(claim.get("status", "accepted") or "accepted")
            if current_status not in status_options:
                current_status = "accepted"
            new_status = st.selectbox(
                ui.get("claim_status", "Claim status"),
                status_options,
                index=status_options.index(current_status),
                key=f"claim_status_{selected}_{claim_id}",
            )
            st.caption(" · ".join(_claim_meta(claim)))
            if claim.get("stale_reason"):
                st.warning(str(claim.get("stale_reason")))
            if st.button(
                ui.get("claim_save", "Save claim"),
                key=f"claim_save_{selected}_{claim_id}",
            ):
                book = load_claim_book(selected)
                updated_claims = []
                for item in book.get("claims") or []:
                    if not isinstance(item, dict):
                        continue
                    if str(item.get("id", "") or "") == claim_id:
                        item = dict(item)
                        if str(item.get("text", "") or "") != new_text:
                            history = list(item.get("history") or [])
                            history.append(
                                {
                                    "text": str(item.get("text", "") or ""),
                                    "evidence_refs": list(item.get("evidence_refs") or []),
                                    "updated": str(item.get("updated", "") or ""),
                                    "captured": date.today().isoformat(),
                                }
                            )
                            item["history"] = history
                        item["text"] = new_text.strip()
                        item["status"] = new_status
                        item["updated"] = date.today().isoformat()
                    updated_claims.append(item)
                book["claims"] = updated_claims
                save_claim_book(selected, book)
                clear_web_cache()
                stash_git_backup_results()
                st.rerun()


def _render_claim_scope_generator(review: dict, scope: str) -> None:
    scope_id = ""
    options: list[str] = []
    labels: dict[str, str] = {}
    if scope == "project":
        for option in review.get("project_options") or []:
            option_id = str(option.get("id", "") or "")
            if option_id:
                options.append(option_id)
                labels[option_id] = str(option.get("label", "") or option_id)
    elif scope == "skill":
        for option in review.get("skill_options") or []:
            option_id = str(option.get("id", "") or "")
            if option_id:
                options.append(option_id)
                labels[option_id] = str(option.get("label", "") or option_id)
    elif scope == "goal":
        from nblane.core.goals import load_goal_book

        book = load_goal_book(selected)
        for goal in book.goals:
            if goal.id:
                options.append(goal.id)
                labels[goal.id] = goal.title or goal.label or goal.id
    if scope in {"project", "skill", "goal"}:
        if not options:
            st.caption(ui.get("claim_scope_empty", "No scope options yet."))
            return
        scope_id = st.selectbox(
            ui.get(f"claim_scope_{scope}", scope.title()),
            options,
            format_func=lambda value: f"{labels.get(value, value)} ({value})",
            key=f"claim_scope_{scope}_{selected}",
        )
    if st.button(
        ui["claim_generate"],
        type="primary",
        key=f"claim_generate_{scope}_{selected}",
    ):
        candidates = generate_claim_candidates_for_scope(
            selected,
            scope,
            scope_id=scope_id,
        )
        st.session_state[_claim_candidate_key(scope)] = candidates
        if not candidates:
            st.warning(ui["claim_candidates_empty"])
        else:
            st.rerun()
    _render_claim_candidate_preview(scope, review)


def _render_claim_manual(review: dict) -> None:
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
            (_row_label(row) for row in rows if str(row.get("id", "")) == eid),
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
        st.session_state[_claim_candidate_key("manual")] = candidates
        if not candidates:
            st.warning(ui["claim_candidates_empty"])
        else:
            st.rerun()
    _render_claim_candidate_preview("manual", review)


def _render_claim_studio(review: dict) -> None:
    """Generate, refresh, and manage profile-level public claims."""
    st.subheader(ui.get("claim_studio_title", "Claim Studio"))
    st.caption(
        ui.get(
            "claim_studio_intro",
            "Generate reusable public claims from reviewed evidence by project, "
            "goal, skill, or manual selection.",
        )
    )
    claim_tabs = st.tabs(
        [
            ui.get("claim_tab_overview", "Overview"),
            ui.get("claim_generate_tab", "Generate"),
            ui.get("claim_tab_refresh", "Needs Refresh"),
        ]
    )
    with claim_tabs[0]:
        _render_claim_overview(review)
    with claim_tabs[1]:
        scope = st.segmented_control(
            ui.get("claim_generate_scope_label", "Generate scope"),
            options=["project", "goal", "skill", "all", "manual"],
            format_func=lambda s: ui.get(f"claim_tab_{s}", s.title()),
            default="project",
            key=f"claim_gen_scope_{selected}",
        )
        scope = scope or "project"
        if scope == "manual":
            _render_claim_manual(review)
        else:
            _render_claim_scope_generator(review, scope)
    with claim_tabs[2]:
        stale = [
            claim
            for claim in (review.get("claim_rows") or [])
            if isinstance(claim, dict)
            and claim.get("refresh_status") == "needs_refresh"
        ]
        if not stale:
            st.success(ui.get("claim_refresh_empty", "No claims need refresh."))
        for claim in stale:
            with st.container(border=True):
                st.markdown(str(claim.get("text", "") or ""))
                st.caption(" · ".join(_claim_meta(claim)))
                if claim.get("stale_reason"):
                    st.warning(str(claim.get("stale_reason")))


def _render_claim_candidates(review: dict) -> None:
    """Backward-compatible wrapper for the Claim Studio tab."""
    _render_claim_studio(review)


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


def _project_ref_option_label(project_id: str, options: list[dict]) -> str:
    for option in options:
        if str(option.get("id", "") or "") == project_id:
            return _option_label(option)
    return project_id


def _project_backfill_task_text(candidate: dict) -> str:
    tasks = (
        candidate.get("tasks")
        if isinstance(candidate.get("tasks"), list)
        else []
    )
    pieces: list[str] = []
    for task in tasks:
        if not isinstance(task, dict):
            continue
        title = str(task.get("title", "") or task.get("id", "") or "").strip()
        project_id = str(task.get("project_id", "") or "").strip()
        if project_id:
            pieces.append(f"{title} -> {project_id}")
        elif title:
            pieces.append(title)
    missing = [
        str(ref).strip()
        for ref in (candidate.get("missing_task_refs") or [])
        if str(ref).strip()
    ]
    for ref in missing:
        pieces.append(f"{ref} (?)")
    return " / ".join(pieces)


def _render_project_ref_backfill(review: dict) -> None:
    """Backfill evidence project refs from linked Kanban task ownership."""
    candidates = [
        item
        for item in (review.get("project_ref_candidates") or [])
        if isinstance(item, dict)
    ]
    st.subheader(ui["refs_project_backfill_title"])
    st.caption(ui["refs_project_backfill_caption"])
    if not candidates:
        st.caption(ui["refs_project_backfill_empty"])
        return

    project_options = list(review.get("project_options") or [])
    auto_candidates = [item for item in candidates if bool(item.get("can_apply"))]
    manual_candidates = [
        item for item in candidates if not bool(item.get("can_apply"))
    ]

    if auto_candidates:
        candidate_ids = [str(item.get("id", "") or "") for item in auto_candidates]
        by_id = {str(item.get("id", "") or ""): item for item in auto_candidates}
        selected_ids = st.multiselect(
            ui["refs_project_backfill_pick"],
            options=candidate_ids,
            default=candidate_ids,
            format_func=lambda eid: _row_label(by_id.get(eid, {})),
            key=f"evidence_review_project_backfill_pick_{selected}",
        )
        rows = []
        for item in auto_candidates:
            eid = str(item.get("id", "") or "")
            if eid not in set(selected_ids):
                continue
            inferred = [
                str(ref).strip()
                for ref in (item.get("inferred_project_refs") or [])
                if str(ref).strip()
            ]
            rows.append(
                {
                    ui.get("refs_project_backfill_col_evidence", "Evidence"): (
                        _row_label(item)
                    ),
                    ui.get("refs_project_backfill_col_project", "Project"): ", ".join(
                        _project_ref_option_label(ref, project_options)
                        for ref in inferred
                    ),
                    ui.get("refs_project_backfill_col_tasks", "Kanban tasks"): (
                        _project_backfill_task_text(item)
                    ),
                }
            )
        if rows:
            st.dataframe(
                pd.DataFrame(rows),
                hide_index=True,
                use_container_width=True,
            )
        if st.button(
            ui["refs_project_backfill_apply"],
            type="primary",
            disabled=not selected_ids,
            key=f"evidence_review_project_backfill_apply_{selected}",
        ):
            entries = _pool_entries()
            entries, changed = apply_project_ref_inferences(
                entries,
                candidates,
                list(selected_ids),
            )
            if changed:
                _save_pool(
                    entries,
                    ui["refs_project_backfill_saved"].format(n=changed),
                )
                st.rerun()
            st.info(ui["pool_no_changes"])
    else:
        st.caption(ui["refs_project_backfill_no_auto"])

    if manual_candidates:
        with st.expander(
            ui["refs_project_backfill_manual_title"].format(
                n=len(manual_candidates)
            ),
            expanded=False,
        ):
            rows = []
            for item in manual_candidates:
                inferred = [
                    str(ref).strip()
                    for ref in (item.get("inferred_project_refs") or [])
                    if str(ref).strip()
                ]
                rows.append(
                    {
                        ui.get("refs_project_backfill_col_evidence", "Evidence"): (
                            _row_label(item)
                        ),
                        ui.get("refs_project_backfill_col_status", "Status"): ui.get(
                            f"refs_project_backfill_status_{item.get('status', '')}",
                            str(item.get("status", "")),
                        ),
                        ui.get("refs_project_backfill_col_project", "Project"): (
                            ", ".join(inferred) or "-"
                        ),
                        ui.get("refs_project_backfill_col_tasks", "Kanban tasks"): (
                            _project_backfill_task_text(item) or "-"
                        ),
                    }
                )
            st.dataframe(
                pd.DataFrame(rows),
                hide_index=True,
                use_container_width=True,
            )


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
    _render_project_ref_backfill(review)
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


# --- Evidence v2 React editor: event handling + section render --------------


# -- React evidence editor: delegate to the shared host ----------------
# The event layer (handlers, dispatch, dup/reformat state, render) lives in
# ``nblane.evidence_editor_host`` so it can be embedded on other pages too.
# The default key prefix reproduces this page's prior session keys, so behavior
# is unchanged.
_evidence_host = EvidenceEditorHost(selected, ui=ui)


@st.fragment
def _render_evidence_editor(review: dict) -> None:
    """Render the unified React editor via the shared host (fragment-scoped).

    Wrapped in a fragment so an editor event reruns only this region — the page
    no longer scrolls to the top and the segmented-control section is kept (same
    pattern as the Project Board component).
    """
    _evidence_host.render()


review_payload = build_evidence_review(selected)
summary = review_payload.get("summary") or {}

head_l, head_goal = st.columns([5, 2], gap="medium", vertical_alignment="top")
with head_l:
    st.title(ui["title"])
    st.caption(ui["page_context_line"])
with head_goal:
    render_current_goal_strip(selected, compact=True, align="right")
    _help_col, _ai_col = st.columns(2, gap="small")
    with _help_col:
        with st.popover(
            ui.get("page_help_short", "Guide"),
            key=f"evidence_help_popover:{selected}",
            use_container_width=True,
        ):
            _render_evidence_review_help()
    with _ai_col:
        with st.popover(
            ui.get("ai_config_short", "AI"),
            key=f"evidence_ai_config_popover:{selected}",
            use_container_width=True,
        ):
            render_action_ai_settings(
                selected,
                _EVIDENCE_AI_ACTIONS,
                ui=ui,
                key_prefix="evidence",
            )

if not evidence_editor_component_available():
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(
        ui["metric_done_uncrystallized"],
        summary.get("done_uncrystallized_count", 0),
    )
    m2.metric(ui["metric_unlinked"], summary.get("unlinked_count", 0))
    m3.metric(ui["metric_needs_review"], summary.get("needs_review_count", 0))
    m4.metric(ui["metric_status_risk"], summary.get("status_risk_count", 0))

# A session-state-backed segmented control replaces st.tabs here: st.tabs is
# client-only and resets to the first tab on every st.rerun() (which the pool's
# bulk/save buttons trigger), snapping the reviewer back to the Done Queue. The
# segmented control persists the active section across reruns via its key.
_NAV_SECTIONS = [
    ("queue", ui["tab_queue"], _render_done_ingest),
    ("claims", ui["tab_claims"], _render_claim_candidates),
    ("pool", ui["tab_pool"], _render_pool_editor),
    ("links", ui["tab_links"], _render_links),
    ("refs", ui["tab_refs"], _render_refs),
    ("risks", ui["tab_risks"], _render_risks),
]
# When the built React editor bundle is present, surface it as the default
# section and retire the legacy LLM Done-queue, pool, links, and housekeeping
# tabs: Done->evidence, the evidence pool (list/detail/batch), skill links, and
# Done archive/delete all now live inside the editor. The other Python tabs
# remain as a full fallback for when the component bundle is unavailable.
if evidence_editor_component_available():
    _NAV_SECTIONS = [
        ("editor", ui.get("tab_editor", "Editor"), _render_evidence_editor),
        *[s for s in _NAV_SECTIONS if s[0] in ("claims", "risks")],
    ]
_default_section = _NAV_SECTIONS[0][0]
_nav_labels = {key: label for key, label, _ in _NAV_SECTIONS}
_active_section = st.segmented_control(
    ui.get("nav_section_label", "Workspace"),
    options=[key for key, _, _ in _NAV_SECTIONS],
    format_func=lambda key: _nav_labels.get(key, key),
    default=_default_section,
    key=f"evidence_review_active_section_{selected}",
    label_visibility="collapsed",
)
_active_section = _active_section or _default_section
for _section_key, _section_label, _section_render in _NAV_SECTIONS:
    if _section_key == _active_section:
        _section_render(review_payload)
        break
