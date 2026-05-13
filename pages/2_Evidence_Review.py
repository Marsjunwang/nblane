"""Evidence Review -- triage Done work, pool rows, links, and risks."""

from __future__ import annotations

from dataclasses import replace

import streamlit as st
import yaml

from nblane.core import llm as llm_client
from nblane.core.evidence_pool_id import new_evidence_id
from nblane.core.evidence_review import (
    build_evidence_review,
    normalize_evidence_strength,
)
from nblane.core.io import (
    EVIDENCE_POOL_FILENAME,
    KANBAN_DONE,
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
    select_profile,
    stash_git_backup_results,
)

apply_ui_language_from_session()

ui = evidence_review_ui()
require_login()
selected = select_profile()
render_git_backup_notices()

_pdir = profile_dir(selected)
_pool_path = _pdir / EVIDENCE_POOL_FILENAME
_tree_path = _pdir / "skill-tree.yaml"
_skill_path = _pdir / "SKILL.md"
_kanban_path = _pdir / "kanban.md"
_goals_path = _pdir / "goals.yaml"
for _path in (_pool_path, _tree_path, _skill_path, _kanban_path, _goals_path):
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
    save_evidence_pool(
        selected,
        {
            "profile": selected,
            "evidence_entries": entries,
        },
    )
    if _skill_path.exists():
        write_generated_blocks(_pdir)
    refresh_file_snapshots([_pool_path, _skill_path])
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
    source_refs = row.get("source_refs") or []
    if isinstance(source_refs, list):
        refs = [str(item).strip() for item in source_refs if str(item).strip()]
        if refs:
            out["source_refs"] = refs
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
    if not pending_done:
        st.caption(ui["done_queue_empty"])
        return

    pick = st.multiselect(
        ui["done_pick"],
        options=list(range(len(pending_done))),
        format_func=lambda i: pending_done[i].title,
        key=f"evidence_review_done_pick_{selected}",
    )
    allow_status = st.checkbox(
        ui["done_allow_status"],
        value=False,
        key=f"evidence_review_allow_status_{selected}",
    )
    st.caption(ui["done_allow_status_help"])
    if st.button(
        ui["done_generate"],
        key=f"evidence_review_done_generate_{selected}",
    ) and pick:
        chosen = [pending_done[i] for i in pick]
        if not llm_client.is_configured():
            render_llm_unavailable(ui)
        else:
            with st.spinner(ui["done_spinner"]):
                patch, err = ingest_kanban_done_json(
                    selected,
                    chosen,
                    goal_context=current_goal_agent_context(selected),
                )
            if err is not None:
                st.error(err)
            elif patch is not None:
                st.session_state[f"evidence_review_patch_{selected}"] = patch
                st.session_state[f"evidence_review_done_titles_{selected}"] = [
                    task.title for task in chosen
                ]
                st.session_state[f"evidence_review_done_ids_{selected}"] = [
                    task.id for task in chosen if task.id
                ]
                st.rerun()

    patch_key = f"evidence_review_patch_{selected}"
    if patch_key not in st.session_state:
        _render_review_lists(review)
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
    if isinstance(source_titles, list) and source_titles:
        st.caption(
            ui["done_preview_source"].format(
                sources="; ".join(str(item) for item in source_titles),
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
    if not applied.ok:
        for error in applied.errors:
            st.error(error)
        for warning in applied.warnings:
            st.warning(warning)
        return
    if mark_crystallized and isinstance(source_titles, list):
        _mark_done_crystallized(
            {str(item) for item in source_ids}
            if isinstance(source_ids, list)
            else set(),
            {str(item) for item in source_titles},
        )
    refresh_file_snapshots([_pool_path, _tree_path, _skill_path])
    stash_git_backup_results()
    clear_web_cache()
    st.success(ui["done_applied"])
    for key in (
        patch_key,
        f"evidence_review_done_titles_{selected}",
        f"evidence_review_done_ids_{selected}",
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
        ui["tab_pool"],
        ui["tab_links"],
        ui["tab_risks"],
    ]
)
with tabs[0]:
    _render_done_ingest(review_payload)
with tabs[1]:
    _render_pool_editor(review_payload)
with tabs[2]:
    _render_links(review_payload)
with tabs[3]:
    _render_risks(review_payload)
