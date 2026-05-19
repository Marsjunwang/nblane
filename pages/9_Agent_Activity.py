"""Agent Activity -- review cross-page candidates and writebacks."""

from __future__ import annotations

import streamlit as st
import yaml

from nblane.core import codex_adapter
from nblane.core.agent_activity import (
    ACTIVITY_KINDS,
    ACTIVITY_STATUSES,
    ACTIVITY_TARGET_OWNERS,
    activity_items_for_page,
    activity_summary,
    update_activity_status,
)
from nblane.core.paths import PROFILES_DIR
from nblane.core.review_actions import apply_review_activity_item
from nblane.web_auth import require_login
from nblane.web_cache import clear_web_cache
from nblane.web_i18n import agent_activity_ui
from nblane.web_shared import (
    _safe_page_link,
    apply_ui_language_from_session,
    assert_files_current,
    refresh_file_snapshots,
    render_current_goal_strip,
    render_git_backup_notices,
    select_profile,
    stash_git_backup_results,
)

apply_ui_language_from_session()

ui = agent_activity_ui()

st.set_page_config(page_title=ui["page_title"], layout="wide")
require_login()
selected = select_profile()
ui = agent_activity_ui()
render_git_backup_notices()


def _session_key(name: str) -> str:
    return f"agent_activity:{selected}:{name}"


def _query_value(name: str) -> str:
    """Return a single query parameter value."""
    try:
        raw = st.query_params.get(name)
    except Exception:
        return ""
    if isinstance(raw, list):
        raw = raw[-1] if raw else ""
    return str(raw or "").strip()


def _option_values(values: list[str] | tuple[str, ...]) -> list[str]:
    return ["all", *list(values)]


def _label(value: str) -> str:
    return ui.get(value, value)


def _owner_page(target_owner: str) -> str:
    return {
        "evidence_pool": "pages/2_Evidence_Review.py",
        "kanban": "pages/3_Kanban.py",
        "public_site": "pages/6_Public_Site.py",
        "skill_tree": "pages/1_Skill_Tree.py",
        "research": "pages/7_Research.py",
        "work": "pages/3_Kanban.py",
        "team": "pages/4_Team_View.py",
        "profile_context": "app.py",
    }.get(target_owner, "app.py")


def _agent_task_meta(item: dict) -> dict:
    """Return compact external-agent metadata for display."""

    payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
    action_result = (
        payload.get("action_result")
        if isinstance(payload.get("action_result"), dict)
        else {}
    )
    agent_result = (
        payload.get("agent_task_result")
        if isinstance(payload.get("agent_task_result"), dict)
        else {}
    )
    meta = {
        "action_name": item.get("action_name"),
        "backend": item.get("backend"),
        "run_id": item.get("run_id"),
        "input_refs": item.get("input_refs") or [],
    }
    for key in ("task_id", "target_harness", "role", "status"):
        value = agent_result.get(key) or action_result.get(key)
        if value:
            meta[f"agent_{key}"] = value
    return {key: value for key, value in meta.items() if value not in ("", [], None)}


def _agent_task_result(item: dict) -> dict:
    """Return the synced external-agent result payload if present."""

    payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
    result = payload.get("agent_task_result")
    return result if isinstance(result, dict) else {}


def _agent_harness_value(item: dict) -> str:
    """Return the best filter value for an external-agent result."""

    agent_result = _agent_task_result(item)
    if not agent_result:
        return ""
    result_payload = (
        agent_result.get("result_payload")
        if isinstance(agent_result.get("result_payload"), dict)
        else {}
    )
    remote = (
        agent_result.get("remote")
        if isinstance(agent_result.get("remote"), dict)
        else {}
    )
    provider = str(result_payload.get("provider") or remote.get("provider") or "").strip()
    if provider:
        return provider
    return str(agent_result.get("target_harness") or "").strip()


def _agent_harness_matches(item: dict, value: str) -> bool:
    clean = str(value or "").strip()
    if not clean or clean == "all":
        return True
    agent_result = _agent_task_result(item)
    if clean == "agent_tasks":
        return bool(agent_result)
    harness = str(agent_result.get("target_harness") or "").strip()
    provider = _agent_harness_value(item)
    if clean == "codex":
        return harness == "codex" or provider in {"local_codex", "codex_cloud"}
    return harness == clean or provider == clean


def _codex_cloud_remote(agent_result: dict) -> dict:
    """Return Codex Cloud remote metadata from an agent task result."""

    remote = agent_result.get("remote")
    if not isinstance(remote, dict):
        return {}
    if str(remote.get("provider") or "") != "codex_cloud":
        return {}
    return remote


def _render_codex_cloud_controls(item: dict, agent_result: dict) -> None:
    """Render Codex Cloud status/diff controls for a remote task."""

    remote = _codex_cloud_remote(agent_result)
    cloud_task_id = str(remote.get("cloud_task_id") or "").strip()
    task_id = str(agent_result.get("task_id") or "").strip()
    if not cloud_task_id or not task_id:
        return
    st.markdown(f"**{ui.get('codex_cloud_title', 'Codex Cloud')}**")
    st.caption(
        f"{ui.get('codex_cloud_task', 'Cloud task')}: {cloud_task_id}"
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button(
            ui.get("codex_cloud_refresh", "Refresh status"),
            key=f"codex_cloud_refresh:{item.get('id')}",
        ):
            _run_codex_cloud_refresh(task_id, include_diff=False)
    with c2:
        if st.button(
            ui.get("codex_cloud_diff", "Pull diff candidate"),
            key=f"codex_cloud_diff:{item.get('id')}",
        ):
            _run_codex_cloud_refresh(task_id, include_diff=True)


def _run_codex_cloud_refresh(task_id: str, *, include_diff: bool) -> None:
    """Refresh one Codex Cloud task and rerun the page on success."""

    try:
        target_files = [
            PROFILES_DIR / selected / "agent-tasks.yaml",
            PROFILES_DIR / selected / "agent-activity.yaml",
        ]
        assert_files_current(target_files)
        with st.spinner(
            ui.get(
                "codex_cloud_diffing" if include_diff else "codex_cloud_refreshing",
                "Refreshing Codex Cloud...",
            )
        ):
            result = codex_adapter.refresh_codex_cloud_task(
                selected,
                task_id,
                include_diff=include_diff,
            )
    except Exception as exc:
        st.error(str(exc))
        return
    if not result.ok:
        st.error(result.error)
        if result.output:
            st.code(result.output, language="text")
        return
    refresh_file_snapshots(target_files)
    stash_git_backup_results()
    clear_web_cache()
    st.success(
        ui.get(
            "codex_cloud_diff_ready" if include_diff else "codex_cloud_refreshed",
            "Codex Cloud updated.",
        )
    )
    st.rerun()


def _can_apply_here(item: dict) -> bool:
    return (
        item.get("status") == "pending"
        and item.get("source_page") == "Review"
        and item.get("target_owner") in {"evidence_pool", "kanban", "public_site"}
    )


def _group_items_by_source(items: list[dict]) -> list[tuple[str, list[dict]]]:
    """Group filtered activity items by source page, preserving item order."""
    groups: list[tuple[str, list[dict]]] = []
    index: dict[str, int] = {}
    for item in items:
        source = str(item.get("source_page") or "").strip() or "Unknown"
        if source not in index:
            index[source] = len(groups)
            groups.append((source, []))
        groups[index[source]][1].append(item)
    return groups


_head_l, _head_goal = st.columns([5, 2], gap="medium", vertical_alignment="top")
with _head_l:
    st.title(ui["title"])
    st.caption(ui["page_context_line"])
with _head_goal:
    render_current_goal_strip(selected, compact=True, align="right")

summary = activity_summary(selected)
c1, c2, c3, c4 = st.columns(4)
c1.metric(ui["pending"], summary["status"].get("pending", 0))
c2.metric(ui["applied"], summary["status"].get("applied", 0))
c3.metric(ui["failed"], summary["status"].get("failed", 0))
c4.metric(ui["items"], sum(summary["status"].values()))

target_activity_item = _query_value("activity_item")
target_source_page = _query_value("source_page")
if target_activity_item:
    for key_name in (
        "status",
        "kind",
        "candidate_type",
        "target_owner",
        "agent_harness_filter",
    ):
        st.session_state[_session_key(key_name)] = "all"
if target_source_page:
    st.session_state[_session_key("source_page")] = target_source_page

f1, f2, f3, f4, f5 = st.columns(5)
with f1:
    status_filter = st.selectbox(
        ui["status"],
        _option_values(ACTIVITY_STATUSES),
        format_func=lambda value: ui["all"] if value == "all" else _label(value),
        key=_session_key("status"),
    )
with f2:
    kind_filter = st.selectbox(
        ui["kind"],
        _option_values(ACTIVITY_KINDS),
        format_func=lambda value: ui["all"] if value == "all" else value,
        key=_session_key("kind"),
    )
candidate_types = sorted(
    key for key, count in summary["candidate_type"].items() if key and count
)
with f3:
    candidate_filter = st.selectbox(
        ui["candidate_type"],
        ["all", *candidate_types],
        format_func=lambda value: ui["all"] if value == "all" else value,
        key=_session_key("candidate_type"),
    )
source_pages = sorted(
    key for key in {item.get("source_page", "") for item in activity_items_for_page(selected)}
    if key
)
if target_source_page and target_source_page not in source_pages:
    source_pages.append(target_source_page)
with f4:
    source_filter = st.selectbox(
        ui["source_page"],
        ["all", *source_pages],
        format_func=lambda value: ui["all"] if value == "all" else value,
        key=_session_key("source_page"),
    )
with f5:
    owner_filter = st.selectbox(
        ui["target_owner"],
        _option_values(ACTIVITY_TARGET_OWNERS),
        format_func=lambda value: ui["all"] if value == "all" else value,
        key=_session_key("target_owner"),
    )

agent_filter_options = ["all", "agent_tasks", "codex", "local_codex", "codex_cloud", "opencode"]
agent_filter = st.selectbox(
    ui.get("agent_harness_filter", "Harness result"),
    agent_filter_options,
    format_func=lambda value: ui.get(f"agent_harness_filter_{value}", value),
    key=_session_key("agent_harness_filter"),
)

items = activity_items_for_page(
    selected,
    {
        "status": status_filter,
        "kind": kind_filter,
        "candidate_type": candidate_filter,
        "source_page": source_filter,
        "target_owner": owner_filter,
    },
)
items = [item for item in items if _agent_harness_matches(item, agent_filter)]
if target_activity_item:
    items = sorted(
        items,
        key=lambda item: 0 if str(item.get("id") or "") == target_activity_item else 1,
    )

st.subheader(ui["items"])
if not items:
    st.caption(ui["no_items"])
    st.stop()

if target_activity_item:
    st.info(
        ui.get("focused_item_notice", "Focused Activity item: {id}").format(
            id=target_activity_item
        )
    )

for source_page, source_items in _group_items_by_source(items):
    st.markdown(
        f"**{ui.get('source_group', 'Source')}: {source_page}**"
    )
    for item in source_items:
        title = str(item.get("title", "") or item.get("id", ""))
        status = str(item.get("status", "") or "")
        candidate_type = str(item.get("candidate_type", "") or "")
        owner = str(item.get("target_owner", "") or "")
        is_target = str(item.get("id") or "") == target_activity_item
        with st.container(border=True):
            if is_target:
                st.success(
                    ui.get("focused_item_highlight", "Opened from {source}.").format(
                        source=target_source_page or source_page
                    )
                )
            h1, h2, h3 = st.columns([5, 2, 2])
            with h1:
                st.markdown(f"**{title}**")
                st.caption(str(item.get("summary", "") or item.get("source_ref", "") or ""))
            with h2:
                st.caption(ui["status"])
                st.write(_label(status))
            with h3:
                st.caption(ui["target_owner"])
                st.write(owner)
            meta = {
                "id": item.get("id"),
                "kind": item.get("kind"),
                "candidate_type": candidate_type,
                "source_page": item.get("source_page"),
                "source_ref": item.get("source_ref"),
                "created": item.get("created"),
                "updated": item.get("updated"),
                "applied_at": item.get("applied_at"),
                "error": item.get("error"),
            }
            meta.update(_agent_task_meta(item))
            st.code(
                yaml.dump(meta, allow_unicode=True, default_flow_style=False, sort_keys=False),
                language="yaml",
            )
            agent_result = _agent_task_result(item)
            tab_labels = [ui["preview"], ui["payload"], ui["refs"], ui["changed_paths"]]
            if agent_result:
                tab_labels.append(ui.get("agent_task_result", "Agent task result"))
            tabs = st.tabs(tab_labels)
            d1, d2, d3, d4 = tabs[:4]
            d5 = tabs[4] if len(tabs) > 4 else None
            with d1:
                st.code(str(item.get("preview", "") or "-"), language="yaml")
            with d2:
                st.code(
                    yaml.dump(
                        item.get("payload") or {},
                        allow_unicode=True,
                        default_flow_style=False,
                        sort_keys=False,
                    ),
                    language="yaml",
                )
            with d3:
                st.code(
                    yaml.dump(
                        item.get("refs") or {},
                        allow_unicode=True,
                        default_flow_style=False,
                        sort_keys=False,
                    ),
                    language="yaml",
                )
            with d4:
                st.write(item.get("changed_paths") or [])
            if d5 is not None:
                with d5:
                    st.code(
                        yaml.dump(
                            agent_result,
                            allow_unicode=True,
                            default_flow_style=False,
                            sort_keys=False,
                        ),
                        language="yaml",
                    )
                    _render_codex_cloud_controls(item, agent_result)
            warnings = item.get("warnings") if isinstance(item.get("warnings"), list) else []
            for warning in warnings:
                st.warning(str(warning))
            a1, a2, a3, a4 = st.columns(4)
            with a1:
                if st.button(
                    ui["apply"],
                    key=f"activity_apply:{item.get('id')}",
                    disabled=not _can_apply_here(item),
                    type="primary",
                ):
                    try:
                        target_files = [
                            PROFILES_DIR / selected / "agent-activity.yaml",
                        ]
                        if owner == "evidence_pool":
                            target_files.extend(
                                [
                                    PROFILES_DIR / selected / "evidence-pool.yaml",
                                    PROFILES_DIR / selected / "kanban.md",
                                ]
                            )
                        elif owner == "kanban":
                            target_files.append(PROFILES_DIR / selected / "kanban.md")
                        assert_files_current(target_files)
                        result = apply_review_activity_item(selected, str(item.get("id")))
                        if result.ok:
                            refresh_file_snapshots(target_files)
                            stash_git_backup_results()
                            clear_web_cache()
                            st.success(ui["applied_message"])
                            st.rerun()
                        for error in result.errors:
                            st.error(error)
                        for warning in result.warnings:
                            st.warning(warning)
                    except Exception as exc:
                        st.error(str(exc))
            with a2:
                if status != "dismissed" and st.button(
                    ui["dismiss"],
                    key=f"activity_dismiss:{item.get('id')}",
                ):
                    update_activity_status(selected, str(item.get("id")), "dismissed")
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(ui["saved"])
                    st.rerun()
            with a3:
                if status in {"dismissed", "failed"} and st.button(
                    ui["reopen"],
                    key=f"activity_reopen:{item.get('id')}",
                ):
                    update_activity_status(selected, str(item.get("id")), "pending")
                    stash_git_backup_results()
                    clear_web_cache()
                    st.success(ui["saved"])
                    st.rerun()
            with a4:
                _safe_page_link(_owner_page(owner), ui["open_owner"])
            if not _can_apply_here(item):
                st.caption(ui["apply_unavailable"])
