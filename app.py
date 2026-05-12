"""nblane · Web UI entry point.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml
import streamlit as st

from nblane.core import git_backup
from nblane.core.home_dashboard import (
    dashboard_payload as _dashboard_payload,
    dashboard_health_summary as _dashboard_health_summary,
    dashboard_kanban_summary as _dashboard_kanban_summary,
    dashboard_pending_evidence_summary as _dashboard_pending_evidence_summary,
    dashboard_public_summary as _dashboard_public_summary,
    dashboard_skill_summary as _dashboard_skill_summary,
)
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
    profile_dir,
)
from nblane.core.profile_ingest import (
    ingest_preview_delta,
    merge_ingest_patch,
    run_ingest_patch,
    schema_node_labels,
)
from nblane.core.profile_ingest_llm import ingest_resume_json
from nblane.core.profile_context import (
    GENERATED_BLOCKS,
    IDENTITY_FIELDS,
    LONG_NARRATIVE_SECTIONS,
    apply_profile_context_structured_edits,
    extract_generated_blocks,
    parse_identity_fields,
    parse_skill_md_sections,
    rejoin_sections,
    section_body,
)
from nblane.web_cache import (
    clear_web_cache,
    load_evidence_pool_raw,
    load_goal_book_raw,
    load_skill_md,
    load_skill_tree_raw,
)
from nblane.home_dashboard_component import st_home_dashboard
from nblane.web_i18n import home_ui
from nblane.web_shared import (
    apply_ui_language_from_session,
    assert_files_current,
    drop_streamlit_widget_keys,
    ensure_file_snapshot,
    remember_allow_and_drop_yaml_preview_keys,
    refresh_file_snapshots,
    render_current_goal_strip,
    render_git_backup_notices,
    render_llm_unavailable,
    select_profile,
    stash_git_backup_results,
)
from nblane.web_auth import require_login

apply_ui_language_from_session()

ui = home_ui()

st.set_page_config(
    page_title=ui["app_page_title"],
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

selected = ""
_skill_md_path = Path()
_tree_path = Path()
_pool_path = Path()
_goals_path = Path()


def _prepare_home_state() -> None:
    """Initialize auth, profile selection, and Home file snapshots."""
    global selected
    global _skill_md_path, _tree_path, _pool_path, _goals_path

    require_login()
    selected = select_profile()
    render_git_backup_notices()

    _skill_md_path = profile_dir(selected) / "SKILL.md"
    _tree_path = profile_dir(selected) / "skill-tree.yaml"
    _pool_path = profile_dir(selected) / "evidence-pool.yaml"
    _goals_path = profile_dir(selected) / "goals.yaml"
    for path in (_skill_md_path, _tree_path, _pool_path, _goals_path):
        ensure_file_snapshot(path)


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


def _dashboard_goal_lines(value: object) -> list[str]:
    """Parse dashboard event values as clean goal line lists."""
    if isinstance(value, list):
        return [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]
    return _goal_text_lines(str(value or ""))


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


def dashboard_kanban_summary(profile: str) -> dict:
    """Dashboard read model for kanban.md."""
    return _dashboard_kanban_summary(profile)


def dashboard_skill_summary(profile: str) -> dict:
    """Dashboard read model for skill-tree.yaml and goals.yaml."""
    return _dashboard_skill_summary(profile)


def dashboard_pending_evidence_summary(profile: str) -> dict:
    """Dashboard read model for pending evidence review."""
    return _dashboard_pending_evidence_summary(profile)


def dashboard_health_summary(profile: str) -> dict:
    """Dashboard read model for profile health."""
    return _dashboard_health_summary(profile)


def dashboard_public_summary(profile: str) -> dict:
    """Dashboard read model for the public layer."""
    return _dashboard_public_summary(profile)


def dashboard_payload(profile: str) -> dict:
    """React Home dashboard payload."""
    ai_payload = {
        "configured": llm_client.is_configured(),
        "label": llm_client.model_label() if llm_client.is_configured() else "",
    }
    return _dashboard_payload(profile, ui=ui, ai=ai_payload)


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

    with st.container():
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
    return parse_skill_md_sections(text)


def _rejoin_sections(
    sections: list[tuple[str, str]],
) -> str:
    """Reassemble sections back into a single string."""
    return rejoin_sections(sections)


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


def _save_dashboard_goal(profile: str, payload: dict) -> None:
    """Persist a Current Goal edit submitted by the React dashboard."""
    book = _goal_book_for_home(profile)
    current = book.current()
    existing = current or Goal(
        id=str(payload.get("id") or "").strip() or _goal_default_id(),
        title="",
        label="",
    )
    title = str(payload.get("title") or "").strip()
    if not title:
        st.warning(ui["goal_title_required"])
        st.stop()
    status = str(payload.get("status") or existing.status).strip()
    if status not in GOAL_STATUSES:
        status = existing.status
    ui_visibility = str(
        payload.get("ui_visibility") or existing.ui_visibility
    ).strip()
    if ui_visibility not in GOAL_UI_VISIBILITIES:
        ui_visibility = existing.ui_visibility
    include_agent = bool(payload.get("include_in_agent_context", False))
    if ui_visibility == "private":
        include_agent = False

    next_goal = Goal(
        id=existing.id or _goal_default_id(),
        title=title,
        label=str(payload.get("label") or "").strip(),
        status=status,
        start=str(payload.get("start") or "").strip(),
        target=str(payload.get("target") or "").strip(),
        ui_visibility=ui_visibility,
        include_in_agent_context=include_agent,
        include_in_public_output=False,
        summary=str(payload.get("summary") or "").strip(),
        target_skills=_dashboard_goal_lines(payload.get("target_skills")),
        success_criteria=_dashboard_goal_lines(
            payload.get("success_criteria")
        ),
        focus=_dashboard_goal_lines(payload.get("focus")),
        evidence_refs=_dashboard_goal_lines(payload.get("evidence_refs")),
        task_refs=_dashboard_goal_lines(payload.get("task_refs")),
        output_refs=_dashboard_goal_lines(payload.get("output_refs")),
        notes=str(payload.get("notes") or "").strip(),
    )
    assert_files_current([_goals_path])
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


def _handle_home_dashboard_event(event: dict | None, profile: str) -> None:
    """Handle one event emitted by the React Home dashboard."""
    if not isinstance(event, dict):
        return
    action = str(event.get("action") or "").strip()
    if not action:
        return
    event_id = str(event.get("event_id") or "").strip()
    dedupe_key = f"_home_dashboard_event_{profile}"
    if event_id and st.session_state.get(dedupe_key) == event_id:
        return
    if event_id:
        st.session_state[dedupe_key] = event_id
    payload = event.get("payload")
    payload = payload if isinstance(payload, dict) else {}

    if action == "edit_goal_submit":
        _save_dashboard_goal(profile, payload)
        return
    if action == "navigate":
        path = str(payload.get("path") or "").strip()
        if path:
            st.switch_page(path)
        return
    if action == "open_section":
        section = str(payload.get("section") or "").strip()
        if section == "evidence":
            st.switch_page("pages/1_Skill_Tree.py")


def _page_link(path: str, label: str, *, help_text: str = "") -> None:
    """Render a Streamlit page link with a Markdown fallback."""
    try:
        st.page_link(path, label=label, help=help_text or None)
    except Exception:
        suffix = f" — {help_text}" if help_text else ""
        st.markdown(f"- **{label}** `{path}`{suffix}")


def _section_label(title: str) -> str:
    key_by_title = {
        "Research Fingerprint": "profile_section_research_fingerprint",
        "Thinking & Communication Style": "profile_section_thinking_style",
        "Growth Log": "profile_section_growth_log",
        "Influence & Output": "profile_section_influence_output",
    }
    return ui.get(key_by_title.get(title, ""), title)


def _identity_label(field: str) -> str:
    key_by_field = {
        "Name": "identity_name",
        "Domain": "identity_domain",
        "Journey": "identity_journey",
        "Current Role": "identity_current_role",
        "North Star": "identity_north_star",
    }
    return ui.get(key_by_field.get(field, ""), field)


def _render_dashboard_status_overview(
    kanban_summary: dict,
    skill_summary: dict,
    pending_summary: dict,
    health_summary: dict,
    public_summary: dict,
) -> None:
    st.subheader(ui["dashboard_status_overview"])
    cols = st.columns(5)
    lit = skill_summary.get("lit", 0)
    total = skill_summary.get("total", 0)
    health_counts = health_summary.get("counts") or {}
    health_value = (
        f"{health_counts.get('error', 0)} / "
        f"{health_counts.get('warning', 0)} / "
        f"{health_counts.get('info', 0)}"
    )
    cols[0].metric(
        ui["dashboard_metric_goal"],
        (
            ui["dashboard_goal_set"]
            if _goal_book_for_home(selected).current() is not None
            else ui["dashboard_goal_missing"]
        ),
    )
    cols[1].metric(
        ui["dashboard_metric_skill_lit"],
        f"{lit}/{total}" if total else "—",
    )
    cols[2].metric(
        ui["dashboard_metric_doing"],
        kanban_summary.get("doing_total", 0),
    )
    cols[3].metric(
        ui["dashboard_metric_pending_evidence"],
        (
            pending_summary.get("done_uncrystallized_count", 0)
            + pending_summary.get("unlinked_count", 0)
        ),
    )
    cols[4].metric(
        ui["dashboard_metric_health"],
        health_value,
        help=ui["dashboard_metric_health_help"],
    )

    if total:
        st.progress(
            float(skill_summary.get("lit_rate", 0.0)),
            text=ui["progress_overall"].format(
                pct=float(skill_summary.get("lit_rate", 0.0)),
            ),
        )
    if not public_summary.get("initialized"):
        st.caption(ui["dashboard_public_not_initialized"])


def _render_dashboard_doing(kanban_summary: dict) -> None:
    st.subheader(ui["dashboard_doing_title"])
    if kanban_summary.get("error"):
        st.warning(kanban_summary["error"])
        return
    doing = kanban_summary.get("doing") or []
    if not doing:
        st.info(ui["dashboard_doing_empty"])
        _page_link(
            "pages/3_Kanban.py",
            ui["quick_kanban"],
            help_text=ui["quick_kanban_help"],
        )
        return

    for item in doing:
        with st.container(border=True):
            st.markdown(f"**{item.get('title', '')}**")
            meta: list[str] = []
            if item.get("started_on"):
                meta.append(
                    ui["dashboard_doing_started"].format(
                        date=item["started_on"],
                    )
                )
            if item.get("tags"):
                meta.append(str(item["tags"]))
            if meta:
                st.caption(" · ".join(meta))
            if item.get("blocked_by"):
                st.warning(
                    ui["dashboard_doing_blocked"].format(
                        blocked=item["blocked_by"],
                    )
                )
    if kanban_summary.get("doing_total", 0) > len(doing):
        st.caption(
            ui["dashboard_doing_more"].format(
                n=kanban_summary["doing_total"] - len(doing),
            )
        )


def _render_dashboard_pending_evidence(pending_summary: dict) -> None:
    st.subheader(ui["dashboard_pending_evidence_title"])
    c1, c2 = st.columns(2)
    with c1:
        st.metric(
            ui["dashboard_done_uncrystallized"],
            pending_summary.get("done_uncrystallized_count", 0),
        )
        for item in pending_summary.get("done_uncrystallized") or []:
            st.caption(f"- {item.get('title', '')}")
    with c2:
        st.metric(
            ui["dashboard_unlinked_evidence"],
            pending_summary.get("unlinked_count", 0),
        )
        for item in pending_summary.get("unlinked") or []:
            st.caption(
                f"- `{item.get('id', '')}` · {item.get('title', '')}"
            )
    if (
        pending_summary.get("done_uncrystallized_count", 0) == 0
        and pending_summary.get("unlinked_count", 0) == 0
    ):
        st.success(ui["dashboard_pending_evidence_empty"])


def _render_dashboard_health(health_summary: dict) -> None:
    st.subheader(ui["dashboard_health_title"])
    counts = health_summary.get("counts") or {}
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(ui["dashboard_health_errors"], counts.get("error", 0))
    c2.metric(ui["dashboard_health_warnings"], counts.get("warning", 0))
    c3.metric(ui["dashboard_health_info"], counts.get("info", 0))
    c4.metric(
        ui["dashboard_health_context_ready"],
        (
            ui["dashboard_yes"]
            if health_summary.get("context_ready")
            else ui["dashboard_no"]
        ),
    )
    issues = health_summary.get("issues") or []
    if not issues:
        st.success(ui["dashboard_health_empty"])
    else:
        for issue in issues[:3]:
            st.caption(
                f"{issue.get('severity', '').upper()} · "
                f"{issue.get('category', '')} · {issue.get('title', '')}"
            )
    _page_link(
        "pages/5_Profile_Health.py",
        ui["quick_profile_health"],
        help_text=ui["quick_profile_health_help"],
    )


def _render_dashboard_public(public_summary: dict) -> None:
    st.subheader(ui["dashboard_output_title"])
    if not public_summary.get("initialized"):
        st.info(ui["dashboard_output_empty"])
        _page_link(
            "pages/6_Public_Site.py",
            ui["quick_public_site"],
            help_text=ui["quick_public_site_help"],
        )
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(ui["dashboard_public_drafts"], public_summary["draft_total"])
    c2.metric(
        ui["dashboard_public_published"],
        public_summary["published_total"],
    )
    c3.metric(
        ui["dashboard_public_visibility"],
        public_summary.get("visibility", "private"),
    )
    c4.metric(
        ui["dashboard_public_build"],
        (
            ui["dashboard_public_build_exists"]
            if public_summary.get("build_exists")
            else ui["dashboard_public_build_missing"]
        ),
    )
    st.caption(
        ui["dashboard_public_build_detail"].format(
            pages=public_summary.get("build_pages", 0),
            path=public_summary.get("build_output_dir", ""),
        )
    )
    _page_link(
        "pages/6_Public_Site.py",
        ui["quick_public_site"],
        help_text=ui["quick_public_site_help"],
    )


def _render_quick_entries() -> None:
    st.subheader(ui["dashboard_quick_title"])
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        _page_link(
            "pages/1_Skill_Tree.py",
            ui["quick_skill_tree"],
            help_text=ui["quick_skill_tree_help"],
        )
    with c2:
        _page_link(
            "pages/2_Gap_Analysis.py",
            ui["quick_gap"],
            help_text=ui["quick_gap_help"],
        )
    with c3:
        _page_link(
            "pages/3_Kanban.py",
            ui["quick_kanban"],
            help_text=ui["quick_kanban_help"],
        )
    with c4:
        _page_link(
            "pages/6_Public_Site.py",
            ui["quick_public_site"],
            help_text=ui["quick_public_site_help"],
        )


def _render_resume_ingest(profile: str) -> None:
    with st.expander(ui["profile_evidence_import_expander"], expanded=False):
        st.caption(ui["profile_evidence_import_caption"])
        resume_text = st.text_area(
            ui["resume_placeholder"],
            height=140,
            key=f"resume_txt_{profile}",
        )
        allow_resume = st.checkbox(
            ui["resume_allow_status"],
            value=False,
            key=f"resume_allow_{profile}",
        )
        st.caption(ui["resume_allow_status_help"])
        rgen = st.button(
            ui["resume_generate"],
            key=f"resume_gen_{profile}",
        )
        if rgen and resume_text.strip():
            if not llm_client.is_configured():
                render_llm_unavailable(ui)
            else:
                with st.spinner(ui["resume_spinner"]):
                    patch, err = ingest_resume_json(
                        profile,
                        resume_text,
                    )
                if err is not None:
                    st.error(ui["resume_err"].format(msg=err))
                elif patch is not None:
                    drop_streamlit_widget_keys(
                        [
                            f"rp_pool_{profile}",
                            f"rp_tree_{profile}",
                        ]
                    )
                    st.session_state[
                        f"resume_ingest_patch_{profile}"
                    ] = patch
                    st.rerun()

        rkey = f"resume_ingest_patch_{profile}"
        if rkey not in st.session_state:
            return

        remember_allow_and_drop_yaml_preview_keys(
            allow_resume,
            prev_state_key=f"_resume_allow_prev_{profile}",
            pool_key=f"rp_pool_{profile}",
            tree_key=f"rp_tree_{profile}",
        )
        patch = st.session_state[rkey]
        pool_r = load_evidence_pool_raw(profile)
        tree_r = load_skill_tree_raw(profile)
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
            profile,
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
            return
        if st.button(
            ui["resume_apply"],
            key=f"resume_apply_{profile}",
            type="primary",
        ):
            assert_files_current(
                [_pool_path, _tree_path, _skill_md_path]
            )
            _, apply_r = run_ingest_patch(
                profile,
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


def _render_profile_context(profile: str) -> None:
    skill_path = profile_dir(profile) / "SKILL.md"
    skill_content = load_skill_md(profile)

    with st.expander(ui["profile_context_expander"], expanded=False):
        st.caption(ui["profile_context_caption"])
        if not skill_content:
            st.warning(ui["warning_no_skill_md"])
            return

        identity = parse_identity_fields(skill_content)
        with st.form(f"profile_context_form_{profile}"):
            st.markdown(f"**{ui['profile_context_structured_title']}**")
            identity_updates: dict[str, str] = {}
            field_cols = st.columns(2)
            for idx, field in enumerate(IDENTITY_FIELDS):
                target = field_cols[idx % 2]
                with target:
                    if field == "North Star":
                        identity_updates[field] = st.text_area(
                            _identity_label(field),
                            value=identity.get(field, ""),
                            height=90,
                            key=f"profile_identity_{profile}_{field}",
                        )
                    else:
                        identity_updates[field] = st.text_input(
                            _identity_label(field),
                            value=identity.get(field, ""),
                            key=f"profile_identity_{profile}_{field}",
                        )

            st.markdown(f"**{ui['profile_context_narrative_title']}**")
            st.caption(ui["profile_context_narrative_caption"])
            narrative_updates: dict[str, str] = {}
            for title in LONG_NARRATIVE_SECTIONS:
                body = section_body(skill_content, title)
                narrative_updates[title] = st.text_area(
                    _section_label(title),
                    value=body,
                    height=max(150, min(360, body.count("\n") * 20 + 80)),
                    key=f"profile_narrative_{profile}_{title}",
                )

            submitted = st.form_submit_button(
                ui["save_profile_context"],
                type="primary",
            )

        if submitted:
            updated = apply_profile_context_structured_edits(
                skill_content,
                identity_fields=identity_updates,
                narrative_sections=narrative_updates,
            )
            _save_skill_md(skill_path, updated, ui["home_saved"])

        st.markdown(f"**{ui['generated_block_preview_title']}**")
        st.caption(ui["generated_block_owner_hint"])
        blocks = extract_generated_blocks(skill_content)
        for block in GENERATED_BLOCKS:
            with st.expander(
                ui["generated_block_expander"].format(block=block),
                expanded=False,
            ):
                if block == "skill_tree":
                    _page_link(
                        "pages/1_Skill_Tree.py",
                        ui["quick_skill_tree"],
                        help_text=ui["generated_block_skill_tree_help"],
                    )
                elif block == "current_focus":
                    _page_link(
                        "pages/3_Kanban.py",
                        ui["quick_kanban"],
                        help_text=ui["generated_block_kanban_help"],
                    )
                st.caption(ui["generated_block_sync_hint"])
                st.code(
                    blocks.get(block, ui["generated_block_missing"]),
                    language="markdown",
                )

        with st.expander(ui["raw_markdown_expander"], expanded=False):
            st.warning(ui["raw_drift_warning"])
            edited_raw = st.text_area(
                ui["raw_label"],
                value=skill_content,
                height=500,
                key=f"skill_md_raw_{profile}",
            )
            col_save2, col_hint2 = st.columns([1, 4])
            with col_save2:
                if st.button(
                    ui["save_skill_md"],
                    type="primary",
                    key=f"save_raw_{profile}",
                ):
                    _save_skill_md(
                        skill_path,
                        edited_raw,
                        ui["home_saved"],
                    )
            with col_hint2:
                st.caption(
                    ui["hint_after_save"].format(
                        profile=profile,
                    )
                )


def _render_home_page() -> None:
    """Render the Daily Dashboard page."""
    _prepare_home_state()

    _head_l, _head_goal = st.columns(
        [5, 2],
        gap="medium",
        vertical_alignment="top",
    )
    with _head_l:
        st.title(ui["app_page_title"])
        st.caption(ui["app_caption"].format(profile=selected))
        st.caption(ui["page_context_line"])
    with _head_goal:
        render_current_goal_strip(selected, compact=True, align="right")

    home_dashboard_payload = dashboard_payload(selected)
    home_dashboard_event = st_home_dashboard(
        payload=home_dashboard_payload,
        key=f"home_dashboard_{selected}",
        height=860,
    )
    if home_dashboard_event is None:
        kanban_summary = home_dashboard_payload["kanban"]
        skill_summary = home_dashboard_payload["skills"]
        pending_summary = home_dashboard_payload["pending_evidence"]
        health_summary = home_dashboard_payload["health"]
        public_summary = home_dashboard_payload["public"]

        _render_current_goal_module(selected)
        st.divider()

        _render_dashboard_status_overview(
            kanban_summary,
            skill_summary,
            pending_summary,
            health_summary,
            public_summary,
        )
        st.divider()

        _render_dashboard_doing(kanban_summary)
        st.divider()

        _render_dashboard_pending_evidence(pending_summary)
        st.divider()

        _render_dashboard_health(health_summary)
        st.divider()

        _render_dashboard_public(public_summary)
        st.divider()

        _render_quick_entries()
    else:
        _handle_home_dashboard_event(home_dashboard_event, selected)

    with st.expander(ui["home_nav_expander"], expanded=False):
        st.caption(ui["home_nav_compact"])
        st.markdown(ui["home_nav_detail"])

    _render_resume_ingest(selected)

    st.divider()
    _render_profile_context(selected)


def _navigation_pages() -> dict[str, list[st.Page]]:
    """Return the grouped sidebar navigation."""
    return {
        ui["sidebar_nav_home_group"]: [
            st.Page(
                _render_home_page,
                title=ui["sidebar_nav_dashboard"],
                icon=":material/dashboard:",
                default=True,
            ),
        ],
        ui["sidebar_nav_work_group"]: [
            st.Page(
                "pages/3_Kanban.py",
                title=ui["sidebar_nav_kanban"],
                icon=":material/view_kanban:",
            ),
        ],
        ui["sidebar_nav_growth_group"]: [
            st.Page(
                "pages/1_Skill_Tree.py",
                title=ui["sidebar_nav_skill_map"],
                icon=":material/account_tree:",
            ),
            st.Page(
                "pages/2_Gap_Analysis.py",
                title=ui["sidebar_nav_gap"],
                icon=":material/troubleshoot:",
            ),
            st.Page(
                "pages/5_Profile_Health.py",
                title=ui["sidebar_nav_health"],
                icon=":material/health_and_safety:",
            ),
        ],
        ui["sidebar_nav_output_group"]: [
            st.Page(
                "pages/6_Public_Site.py",
                title=ui["sidebar_nav_public"],
                icon=":material/language:",
            ),
        ],
        ui["sidebar_nav_team_group"]: [
            st.Page(
                "pages/4_Team_View.py",
                title=ui["sidebar_nav_team"],
                icon=":material/groups:",
            ),
        ],
    }


def main() -> None:
    """Run the Streamlit app with product-level navigation."""
    st.session_state["_nblane_native_navigation"] = True
    page = st.navigation(_navigation_pages(), expanded=True)
    page.run()


if __name__ == "__main__":
    main()
