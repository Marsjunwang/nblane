"""nblane · Web UI entry point.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import yaml
import streamlit as st

from nblane.core import git_backup
from nblane.core import llm as llm_client
from nblane.core.goals import (
    GOAL_STATUSES,
    GOAL_UI_VISIBILITIES,
    Goal,
    GoalBook,
    goal_for_ui,
    save_goal_book,
)
from nblane.core.io import (
    STATUSES,
    profile_dir,
    schema_node_index,
)
from nblane.core.profile_ingest import (
    ingest_preview_delta,
    merge_ingest_patch,
    run_ingest_patch,
    schema_node_labels,
)
from nblane.core.profile_ingest_llm import ingest_resume_json
from nblane.web_cache import (
    clear_web_cache,
    load_evidence_pool_raw,
    load_goal_book_raw,
    load_schema_raw,
    load_skill_md,
    load_skill_tree_raw,
)
from nblane.web_i18n import home_ui
from nblane.web_shared import (
    assert_files_current,
    drop_streamlit_widget_keys,
    ensure_file_snapshot,
    remember_allow_and_drop_yaml_preview_keys,
    refresh_file_snapshots,
    render_current_goal_strip,
    render_git_backup_notices,
    render_llm_unavailable,
    select_profile,
    skill_status_emoji,
    stash_git_backup_results,
    ui_emoji_enabled,
)
from nblane.web_auth import require_login

ui = home_ui()

st.set_page_config(
    page_title=ui["app_page_title"],
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

require_login()
selected = select_profile()
render_git_backup_notices()

_skill_md_path = profile_dir(selected) / "SKILL.md"
_tree_path = profile_dir(selected) / "skill-tree.yaml"
_pool_path = profile_dir(selected) / "evidence-pool.yaml"
_goals_path = profile_dir(selected) / "goals.yaml"
for _path in (_skill_md_path, _tree_path, _pool_path, _goals_path):
    ensure_file_snapshot(_path)


def _goal_lines_text(items: list[str]) -> str:
    """Render list fields as one item per line."""
    return "\n".join(items or [])


def _goal_text_lines(value: str) -> list[str]:
    """Parse one-item-per-line goal fields."""
    return [
        line.strip()
        for line in value.splitlines()
        if line.strip()
    ]


def _goal_status_label(status: str) -> str:
    return ui.get(f"goal_status_{status}", status)


def _goal_visibility_label(visibility: str) -> str:
    return ui.get(f"goal_visibility_{visibility}", visibility)


def _goal_book_for_home(profile: str) -> GoalBook:
    """Load the current goal book through the Streamlit cache."""
    return GoalBook.from_dict(
        load_goal_book_raw(profile),
        profile=profile,
    )


def _goal_form_key(profile: str, field: str) -> str:
    """Stable widget key for the Home goal form."""
    return f"home_goal_{profile}_{field}"


def _goal_default_id() -> str:
    """Return a stable id shape for the first current goal."""
    return f"goal_{date.today().strftime('%Y%m%d')}_current"


def _render_goal_preview(goal: Goal) -> None:
    """Render the Home module's privacy-safe current goal preview."""
    payload = goal_for_ui(goal)
    st.caption(ui["goal_preview"])
    if payload is None:
        st.info(ui["goal_private_locked"])
        return
    visibility = str(payload.get("visibility") or "")
    if visibility == "hidden":
        st.markdown(f"**{ui['goal_strip_hidden']}**")
        return
    if visibility == "discreet":
        label = str(
            payload.get("label") or ui["goal_strip_default_label"]
        )
        status = _goal_status_label(str(payload.get("status") or ""))
        target = str(payload.get("target") or "")
        text = f"**{label}** · {ui['goal_strip_status']}: {status}"
        if target:
            text += f" · {ui['goal_strip_target']}: {target}"
        st.markdown(text)
        return
    title = str(payload.get("title") or payload.get("label") or "")
    status = _goal_status_label(str(payload.get("status") or ""))
    target = str(payload.get("target") or "")
    text = f"**{title or ui['goal_strip_default_label']}**"
    if status:
        text += f" · {ui['goal_strip_status']}: {status}"
    if target:
        text += f" · {ui['goal_strip_target']}: {target}"
    st.markdown(text)
    summary = str(payload.get("summary") or "")
    if summary:
        st.caption(summary)
    focus = payload.get("focus")
    if isinstance(focus, list) and focus:
        st.caption(
            f"{ui['goal_strip_focus']}: "
            + " · ".join(str(item) for item in focus[:3] if item)
        )


def _render_current_goal_module(profile: str) -> None:
    """Render the lightweight Current Goal editor on Home."""
    book = _goal_book_for_home(profile)
    goal = book.current()

    with st.container(border=True):
        st.subheader(ui["goal_module_title"])
        st.caption(ui["goal_module_caption"])

        reveal_private = True
        if goal is None:
            st.info(ui["goal_no_current"])
        elif goal.ui_visibility == "private":
            reveal_private = st.checkbox(
                ui["goal_reveal_private"],
                value=False,
                key=_goal_form_key(profile, "reveal_private"),
            )
            if not reveal_private:
                st.info(ui["goal_private_locked"])
        else:
            _render_goal_preview(goal)

        if goal is not None and goal.ui_visibility == "private" and not reveal_private:
            return

        form_title = (
            ui["goal_edit_title"]
            if goal is not None
            else ui["goal_create_title"]
        )
        with st.expander(form_title, expanded=goal is None):
            existing = goal or Goal(
                id=_goal_default_id(),
                title="",
                label="",
            )
            with st.form(_goal_form_key(profile, "form")):
                title = st.text_input(
                    ui["goal_field_title"],
                    value=existing.title,
                    key=_goal_form_key(profile, "title"),
                )
                label = st.text_input(
                    ui["goal_field_label"],
                    value=existing.label,
                    key=_goal_form_key(profile, "label"),
                )
                c1, c2, c3 = st.columns(3)
                with c1:
                    status = st.selectbox(
                        ui["goal_field_status"],
                        GOAL_STATUSES,
                        index=GOAL_STATUSES.index(existing.status)
                        if existing.status in GOAL_STATUSES
                        else 0,
                        format_func=_goal_status_label,
                        key=_goal_form_key(profile, "status"),
                    )
                with c2:
                    start = st.text_input(
                        ui["goal_field_start"],
                        value=existing.start,
                        key=_goal_form_key(profile, "start"),
                    )
                with c3:
                    target = st.text_input(
                        ui["goal_field_target"],
                        value=existing.target,
                        key=_goal_form_key(profile, "target"),
                    )
                ui_visibility = st.selectbox(
                    ui["goal_field_ui_visibility"],
                    GOAL_UI_VISIBILITIES,
                    index=GOAL_UI_VISIBILITIES.index(
                        existing.ui_visibility
                    )
                    if existing.ui_visibility in GOAL_UI_VISIBILITIES
                    else 1,
                    format_func=_goal_visibility_label,
                    key=_goal_form_key(profile, "ui_visibility"),
                )
                include_agent = st.checkbox(
                    ui["goal_field_agent_context"],
                    value=(
                        existing.include_in_agent_context
                        and ui_visibility != "private"
                    ),
                    disabled=ui_visibility == "private",
                    key=_goal_form_key(profile, "agent_context"),
                )
                _include_public = st.checkbox(
                    ui["goal_field_public_output"],
                    value=False,
                    disabled=True,
                    key=_goal_form_key(profile, "public_output"),
                )
                st.caption(ui["goal_public_disabled_caption"])
                summary = st.text_area(
                    ui["goal_field_summary"],
                    value=existing.summary,
                    key=_goal_form_key(profile, "summary"),
                )
                target_skills = st.text_area(
                    ui["goal_field_target_skills"],
                    value=_goal_lines_text(existing.target_skills),
                    key=_goal_form_key(profile, "target_skills"),
                )
                success_criteria = st.text_area(
                    ui["goal_field_success_criteria"],
                    value=_goal_lines_text(existing.success_criteria),
                    key=_goal_form_key(profile, "success_criteria"),
                )
                focus = st.text_area(
                    ui["goal_field_focus"],
                    value=_goal_lines_text(existing.focus),
                    key=_goal_form_key(profile, "focus"),
                )
                evidence_refs = st.text_area(
                    ui["goal_field_evidence_refs"],
                    value=_goal_lines_text(existing.evidence_refs),
                    key=_goal_form_key(profile, "evidence_refs"),
                )
                task_refs = st.text_area(
                    ui["goal_field_task_refs"],
                    value=_goal_lines_text(existing.task_refs),
                    key=_goal_form_key(profile, "task_refs"),
                )
                output_refs = st.text_area(
                    ui["goal_field_output_refs"],
                    value=_goal_lines_text(existing.output_refs),
                    key=_goal_form_key(profile, "output_refs"),
                )
                notes = st.text_area(
                    ui["goal_field_notes"],
                    value=existing.notes,
                    key=_goal_form_key(profile, "notes"),
                )
                submitted = st.form_submit_button(
                    ui["goal_save"],
                    type="primary",
                )
            if submitted:
                if not title.strip():
                    st.warning(ui["goal_title_required"])
                    st.stop()
                assert_files_current([_goals_path])
                next_goal = Goal(
                    id=existing.id or _goal_default_id(),
                    title=title.strip(),
                    label=label.strip(),
                    status=status,
                    start=start.strip(),
                    target=target.strip(),
                    ui_visibility=ui_visibility,
                    include_in_agent_context=include_agent,
                    include_in_public_output=False,
                    summary=summary.strip(),
                    target_skills=_goal_text_lines(target_skills),
                    success_criteria=_goal_text_lines(success_criteria),
                    focus=_goal_text_lines(focus),
                    evidence_refs=_goal_text_lines(evidence_refs),
                    task_refs=_goal_text_lines(task_refs),
                    output_refs=_goal_text_lines(output_refs),
                    notes=notes.strip(),
                )
                by_id = book.by_id()
                by_id[next_goal.id] = next_goal
                book.goals = list(by_id.values())
                book.current_goal_id = next_goal.id
                book.profile = profile
                save_goal_book(profile, book)
                refresh_file_snapshots([_goals_path])
                stash_git_backup_results()
                clear_web_cache()
                st.success(ui["goal_saved"])
                st.rerun()

def _parse_skill_md_sections(
    text: str,
) -> list[tuple[str, str]]:
    """Split SKILL.md into (heading, body) pairs.

    Returns a list of tuples: first element is the section
    heading (e.g. '## Identity'), second is the body text
    under that heading. Content before the first heading
    is captured as '(header)'.
    """
    parts: list[tuple[str, str]] = []
    current_heading = "(header)"
    buf: list[str] = []

    for line in text.splitlines(keepends=True):
        if re.match(r"^#{1,3}\s", line):
            parts.append(
                (current_heading, "".join(buf))
            )
            current_heading = line.strip()
            buf = []
        else:
            buf.append(line)

    parts.append((current_heading, "".join(buf)))
    return parts


def _rejoin_sections(
    sections: list[tuple[str, str]],
) -> str:
    """Reassemble sections back into a single string."""
    parts: list[str] = []
    for heading, body in sections:
        if heading != "(header)":
            parts.append(heading + "\n")
        parts.append(body)
    return "".join(parts)


def _save_skill_md(
    path: Path,
    content: str,
    success_message: str,
) -> None:
    """Persist SKILL.md edits and refresh cached web reads."""
    assert_files_current([path])
    path.write_text(content, encoding="utf-8")
    git_backup.record_change(
        [path],
        action=f"update {path.parent.name}/SKILL.md",
    )
    refresh_file_snapshots([path])
    stash_git_backup_results()
    clear_web_cache()
    st.success(success_message)
    st.rerun()


# -- Page header -----------------------------------------------

st.title(ui["app_page_title"])
st.caption(ui["app_caption"].format(profile=selected))
st.caption(ui["page_context_line"])
render_current_goal_strip(selected, compact=True)

# -- Tabs: Overview | Editor | Raw ----------------------------

tab_overview, tab_editor, tab_raw = st.tabs(
    [
        ui["tab_overview"],
        ui["tab_editor"],
        ui["tab_raw"],
    ]
)

# ── TAB 1: Overview ──────────────────────────────────────────

tree = load_skill_tree_raw(selected)

with tab_overview:
    _render_current_goal_module(selected)
    st.divider()

    if tree is not None:
        schema_name = tree.get("schema", "")
        schema = (
            load_schema_raw(schema_name)
            if schema_name
            else None
        )
        index = (
            schema_node_index(schema) if schema else {}
        )

        node_status = {
            n["id"]: n.get("status", "locked")
            for n in (tree.get("nodes") or [])
            if "id" in n
        }

        # Count over the same universe as the category breakdown: every
        # schema node defaults to locked if absent from skill-tree.yaml.
        counts: dict[str, int] = {s: 0 for s in STATUSES}
        if index:
            for nid in index:
                st_val = node_status.get(nid, "locked")
                counts[st_val] = counts.get(st_val, 0) + 1
        else:
            for n in tree.get("nodes") or []:
                if "id" not in n:
                    continue
                st_val = n.get("status", "locked")
                counts[st_val] = counts.get(st_val, 0) + 1
        total = sum(counts.values())
        lit = counts["expert"] + counts["solid"]

        st.subheader(ui["sub_overview"])
        c1, c2, c3, c4, c5 = st.columns(5)
        use_emoji = ui_emoji_enabled()
        c1.metric(
            (
                ui["metric_expert"]
                if use_emoji
                else ui["status_expert"]
            ),
            counts["expert"],
        )
        c2.metric(
            (
                ui["metric_solid"]
                if use_emoji
                else ui["status_solid"]
            ),
            counts["solid"],
        )
        c3.metric(
            (
                ui["metric_learning"]
                if use_emoji
                else ui["status_learning"]
            ),
            counts["learning"],
        )
        c4.metric(
            (
                ui["metric_locked"]
                if use_emoji
                else ui["status_locked"]
            ),
            counts["locked"],
        )
        c5.metric(
            ui["metric_lit_rate"],
            f"{lit}/{total}" if total else "—",
        )

        if total > 0:
            progress_val = lit / total
            st.progress(
                progress_val,
                text=ui["progress_overall"].format(
                    pct=progress_val,
                ),
            )

        st.divider()

        cats: dict[str, list[dict]] = {}
        for nid, meta in index.items():
            cat = meta.get("category", "other")
            status = node_status.get(nid, "locked")
            cats.setdefault(cat, []).append(
                {
                    "id": nid,
                    "label": meta.get("label", nid),
                    "status": status,
                }
            )

        st.subheader(ui["sub_category"])
        for cat in sorted(cats):
            nodes = cats[cat]
            cat_lit = sum(
                1
                for n in nodes
                if n["status"] in ("expert", "solid")
            )
            cat_total = len(nodes)
            frac = (
                cat_lit / cat_total
                if cat_total
                else 0
            )

            col_name, col_bar = st.columns([1, 3])
            with col_name:
                st.markdown(
                    f"**{cat}** "
                    f"({cat_lit}/{cat_total})"
                )
            with col_bar:
                st.progress(frac)

            with st.expander(
                ui["home_expander_cat"].format(
                    cat=cat,
                    total=cat_total,
                )
            ):
                for n in nodes:
                    em = skill_status_emoji(n["status"])
                    prefix = f"{em} " if em else ""
                    st.markdown(
                        f"{prefix}**{n['label']}** "
                        f"`{n['id']}`"
                    )
    else:
        st.info(
            ui["info_no_skill_tree"].format(
                profile=selected,
            )
        )

    with st.expander(ui["resume_expander"], expanded=False):
        resume_text = st.text_area(
            ui["resume_placeholder"],
            height=140,
            key=f"resume_txt_{selected}",
        )
        allow_resume = st.checkbox(
            ui["resume_allow_status"],
            value=False,
            key=f"resume_allow_{selected}",
        )
        st.caption(ui["resume_allow_status_help"])
        rgen = st.button(
            ui["resume_generate"],
            key=f"resume_gen_{selected}",
        )
        if rgen and resume_text.strip():
            if not llm_client.is_configured():
                render_llm_unavailable(ui)
            else:
                with st.spinner(ui["resume_spinner"]):
                    patch, err = ingest_resume_json(
                        selected,
                        resume_text,
                    )
                if err is not None:
                    st.error(ui["resume_err"].format(msg=err))
                elif patch is not None:
                    drop_streamlit_widget_keys(
                        [
                            f"rp_pool_{selected}",
                            f"rp_tree_{selected}",
                        ]
                    )
                    st.session_state[
                        f"resume_ingest_patch_{selected}"
                    ] = patch
                    st.rerun()

        rkey = f"resume_ingest_patch_{selected}"
        if rkey in st.session_state:
            remember_allow_and_drop_yaml_preview_keys(
                allow_resume,
                prev_state_key=f"_resume_allow_prev_{selected}",
                pool_key=f"rp_pool_{selected}",
                tree_key=f"rp_tree_{selected}",
            )
            patch = st.session_state[rkey]
            pool_r = load_evidence_pool_raw(selected)
            tree_r = load_skill_tree_raw(selected)
            st.caption(
                ui["merge_preview_llm_status_line"].format(
                    mode=(
                        ui["merge_llm_status_applied"]
                        if allow_resume
                        else ui["merge_llm_status_ignored"]
                    ),
                )
            )
            rmerge = merge_ingest_patch(
                selected,
                pool_r,
                tree_r,
                patch,
                allow_status_change=allow_resume,
                bump_locked_with_evidence=True,
            )
            if rmerge.warnings:
                st.caption(ui["resume_warn"])
                for w in rmerge.warnings:
                    st.caption(f"- {w}")
            if rmerge.ok and (
                rmerge.merged_pool is not None
                or rmerge.merged_tree is not None
            ):
                lab = schema_node_labels(tree_r)
                new_ev, tree_delta = ingest_preview_delta(
                    pool_r,
                    tree_r,
                    rmerge.merged_pool,
                    rmerge.merged_tree,
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
            if rmerge.ok and (
                rmerge.merged_pool is not None
                or rmerge.merged_tree is not None
            ):
                st.caption(ui["merge_preview_yaml_readonly_caption"])
            if rmerge.ok and rmerge.merged_pool:
                st.markdown(f"**{ui['resume_preview_pool']}**")
                st.code(
                    yaml.dump(
                        rmerge.merged_pool,
                        allow_unicode=True,
                        default_flow_style=False,
                        sort_keys=False,
                    ),
                    language="yaml",
                )
            if rmerge.ok and rmerge.merged_tree:
                st.markdown(f"**{ui['resume_preview_tree']}**")
                st.code(
                    yaml.dump(
                        rmerge.merged_tree,
                        allow_unicode=True,
                        default_flow_style=False,
                        sort_keys=False,
                    ),
                    language="yaml",
                )
            if not rmerge.ok:
                for e in rmerge.errors:
                    st.error(e)
            else:
                if st.button(
                    ui["resume_apply"],
                    key=f"resume_apply_{selected}",
                    type="primary",
                ):
                    assert_files_current(
                        [_pool_path, _tree_path, _skill_md_path]
                    )
                    _, apply_r = run_ingest_patch(
                        selected,
                        patch,
                        allow_status_change=allow_resume,
                        bump_locked_with_evidence=True,
                        dry_run=False,
                    )
                    if apply_r.ok:
                        clear_web_cache()
                        refresh_file_snapshots(
                            [_pool_path, _tree_path, _skill_md_path]
                        )
                        stash_git_backup_results()
                        st.success(ui["resume_applied"])
                        del st.session_state[rkey]
                        render_git_backup_notices()
                    else:
                        for e in apply_r.errors:
                            st.error(e)
                        for w in apply_r.warnings:
                            st.warning(w)

    st.divider()
    st.info(ui["home_nav_compact"])
    with st.expander(ui["home_nav_expander"], expanded=False):
        st.markdown(ui["home_nav_detail"])


# ── TAB 2: Structured SKILL.md editor ────────────────────────

with tab_editor:
    skill_path = profile_dir(selected) / "SKILL.md"
    skill_content = load_skill_md(selected)

    if not skill_content:
        st.warning(ui["warning_no_skill_md"])
    else:
        sections = _parse_skill_md_sections(
            skill_content
        )

        edited_sections: list[tuple[str, str]] = []
        for i, (heading, body) in enumerate(sections):
            if heading == "(header)":
                edited_sections.append((heading, body))
                continue

            is_generated = (
                "BEGIN GENERATED" in body
            )
            with st.expander(
                heading
                + (
                    ui["gen_suffix"]
                    if is_generated
                    else ""
                ),
                expanded=(i <= 2),
            ):
                if is_generated:
                    st.caption(ui["gen_caption"])
                    st.code(body.strip(), language="markdown")
                    edited_sections.append(
                        (heading, body)
                    )
                else:
                    new_body = st.text_area(
                        heading,
                        value=body,
                        height=max(
                            120,
                            body.count("\n") * 22 + 60,
                        ),
                        key=f"sec_{i}",
                        label_visibility="collapsed",
                    )
                    edited_sections.append(
                        (heading, new_body)
                    )

        col_save, col_hint = st.columns([1, 4])
        with col_save:
            if st.button(
                ui["save_skill_md"],
                type="primary",
                key="save_structured",
            ):
                merged = _rejoin_sections(
                    edited_sections
                )
                _save_skill_md(
                    skill_path,
                    merged,
                    ui["home_saved"],
                )
        with col_hint:
            st.caption(
                ui["hint_after_save"].format(
                    profile=selected,
                )
            )

# ── TAB 3: Raw editor ────────────────────────────────────────

with tab_raw:
    skill_path = profile_dir(selected) / "SKILL.md"
    raw_content = load_skill_md(selected)

    if not raw_content:
        st.warning(ui["warning_no_skill_md"])
    else:
        edited_raw = st.text_area(
            ui["raw_label"],
            value=raw_content,
            height=500,
            key="skill_md_raw",
        )

        col_save2, col_hint2 = st.columns([1, 4])
        with col_save2:
            if st.button(
                ui["save_skill_md"],
                type="primary",
                key="save_raw",
            ):
                _save_skill_md(
                    skill_path,
                    edited_raw,
                    ui["home_saved"],
                )
        with col_hint2:
            st.caption(
                ui["hint_after_save"].format(
                    profile=selected,
                )
            )
