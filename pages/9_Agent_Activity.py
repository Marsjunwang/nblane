"""Agent Activity -- review cross-page candidates and writebacks."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import streamlit as st
import streamlit.components.v1 as components
import yaml

from nblane.core import codex_adapter
from nblane.core.agent_activity import (
    ACTIVITY_KINDS,
    ACTIVITY_STATUSES,
    ACTIVITY_TARGET_OWNERS,
    activity_items_for_page,
    activity_summary,
    delete_activity_items,
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


def _format_local_time(value: object) -> str:
    """Render a stored UTC ISO timestamp in the user's local display timezone."""

    text = str(value or "").strip()
    if not text:
        return ""
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(ZoneInfo("Asia/Shanghai")).strftime(
        "%Y-%m-%d %H:%M:%S %Z"
    )


def _short_display(value: object, limit: int = 320) -> str:
    """Collapse long values for card-level display."""

    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def _readable_error_text(value: object) -> str:
    """Extract the useful part of a noisy agent/Codex error."""

    text = str(value or "").strip()
    if not text:
        return ""
    patterns = (
        r"No file descriptors available \(os error \d+\)",
        r"config(?:uration)?[^.\n]{0,120}(?:failed|error)",
        r"model [`'\"]?[^`'\"\n]+[`'\"]? does not exist[^.\n]*",
        r"authentication required[^.\n]*",
        r"api key auth is not supported",
        r"Error code:\s*\d+[^.\n]*",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return _short_display(match.group(0), 500)
    for line in text.splitlines():
        clean = _short_display(line, 500)
        if not clean:
            continue
        if clean.startswith("OpenAI Codex ") or clean.startswith("--------"):
            continue
        if clean in {"user", "assistant"}:
            continue
        if " WARN " in clean and "failed" not in clean.casefold():
            continue
        return clean
    return _short_display(text, 500)


def _truncate_for_details(value: object, limit: int = 1200) -> object:
    """Recursively cap large technical values before rendering them."""

    if isinstance(value, dict):
        return {
            str(key): _truncate_for_details(child, limit=600)
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [_truncate_for_details(child, limit=limit) for child in value[:60]]
    if isinstance(value, tuple):
        return [_truncate_for_details(child, limit=limit) for child in value[:60]]
    if isinstance(value, str):
        return _short_display(value, limit)
    return value


def _module_scope(module: str) -> str:
    clean = str(module or "all").strip() or "all"
    if clean == "all":
        return "all"
    digest = hashlib.sha1(clean.encode("utf-8")).hexdigest()[:8]
    return f"source_{digest}"


def _module_label(module: str, all_items: list[dict]) -> str:
    clean = str(module or "all").strip() or "all"
    if clean == "all":
        label = ui.get("all_modules", "All modules")
        count = len(all_items)
    else:
        label = clean
        count = sum(
            1
            for item in all_items
            if str(item.get("source_page") or "").strip() == clean
        )
    return f"{label} ({count})"


def _focus_anchor_id(item_id: str, scope: str = "all") -> str:
    seed = f"{scope}:{item_id}"
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]
    return f"agent-activity-item-{digest}"


def _render_focus_scroll(item_id: str, scope: str = "all") -> None:
    """Scroll the focused Activity item into view after Streamlit renders."""

    anchor = _focus_anchor_id(item_id, scope)
    components.html(
        f"""
        <script>
        const target = window.parent.document.getElementById("{anchor}");
        if (target) {{
          setTimeout(() => target.scrollIntoView({{block: "center", behavior: "smooth"}}), 120);
        }}
        </script>
        """,
        height=0,
    )


def _source_for_item(items: list[dict], item_id: str) -> str:
    for item in items:
        if str(item.get("id") or "") == item_id:
            return str(item.get("source_page") or "").strip()
    return ""


def _delete_and_rerun(item_ids: list[str]) -> None:
    """Delete Activity rows and reload the page."""

    clean_ids = [item_id for item_id in item_ids if str(item_id or "").strip()]
    if not clean_ids:
        st.warning(ui.get("delete_none", "No matching Activity items to delete."))
        return
    try:
        target_files = [PROFILES_DIR / selected / "agent-activity.yaml"]
        assert_files_current(target_files)
        removed = delete_activity_items(selected, clean_ids)
        if not removed:
            st.warning(ui.get("delete_none", "No matching Activity items to delete."))
            return
        refresh_file_snapshots(target_files)
        stash_git_backup_results()
        clear_web_cache()
        st.success(
            ui.get("deleted_items", "Deleted {count} Activity item(s).").format(
                count=removed
            )
        )
        st.rerun()
    except Exception as exc:
        st.error(str(exc))


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


def _render_codex_cloud_controls(
    item: dict,
    agent_result: dict,
    *,
    key_scope: str = "",
) -> None:
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
            key=f"codex_cloud_refresh:{key_scope}:{item.get('id')}",
        ):
            _run_codex_cloud_refresh(task_id, include_diff=False)
    with c2:
        if st.button(
            ui.get("codex_cloud_diff", "Pull diff candidate"),
            key=f"codex_cloud_diff:{key_scope}:{item.get('id')}",
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


def _render_activity_module(
    *,
    source_module: str,
    source_pages: list[str],
    summary: dict[str, dict[str, int]],
    target_activity_item: str,
    target_source_page: str,
    focus_module: str,
) -> bool:
    """Render one source-page Activity subpage and return focused visibility."""

    module_scope = _module_scope(source_module)
    focus_active = bool(target_activity_item) and source_module == focus_module
    if focus_active:
        for key_name in (
            "status",
            "kind",
            "candidate_type",
            "target_owner",
            "agent_harness_filter",
            "source_page_filter",
        ):
            st.session_state[_session_key(f"{module_scope}:{key_name}")] = "all"

    source_filter_key = _session_key(f"{module_scope}:source_page_filter")
    source_filter_options = ["all", *source_pages]
    if st.session_state.get(source_filter_key) not in source_filter_options:
        st.session_state[source_filter_key] = "all"

    sort_options = ["updated_desc", "updated_asc", "queue"]
    sort_key = _session_key(f"{module_scope}:sort")
    if st.session_state.get(sort_key) not in sort_options:
        st.session_state[sort_key] = "updated_desc"
    sort_mode = st.selectbox(
        ui.get("sort", "Sort"),
        sort_options,
        format_func=lambda value: ui.get(f"sort_{value}", value),
        key=sort_key,
    )

    with st.expander(ui.get("advanced_filters", "Advanced filters"), expanded=False):
        f1, f2, f3, f4, f5 = st.columns(5)
        with f1:
            status_filter = st.selectbox(
                ui["status"],
                _option_values(ACTIVITY_STATUSES),
                format_func=lambda value: ui["all"] if value == "all" else _label(value),
                key=_session_key(f"{module_scope}:status"),
            )
        with f2:
            kind_filter = st.selectbox(
                ui["kind"],
                _option_values(ACTIVITY_KINDS),
                format_func=lambda value: ui["all"] if value == "all" else value,
                key=_session_key(f"{module_scope}:kind"),
            )
        candidate_types = sorted(
            key for key, count in summary["candidate_type"].items() if key and count
        )
        with f3:
            candidate_filter = st.selectbox(
                ui["candidate_type"],
                ["all", *candidate_types],
                format_func=lambda value: ui["all"] if value == "all" else value,
                key=_session_key(f"{module_scope}:candidate_type"),
            )
        with f4:
            if source_module == "all":
                source_filter = st.selectbox(
                    ui["source_page"],
                    source_filter_options,
                    format_func=lambda value: ui["all"] if value == "all" else value,
                    key=source_filter_key,
                )
            else:
                st.caption(ui["source_page"])
                st.write(source_module)
                source_filter = source_module
        with f5:
            owner_filter = st.selectbox(
                ui["target_owner"],
                _option_values(ACTIVITY_TARGET_OWNERS),
                format_func=lambda value: ui["all"] if value == "all" else value,
                key=_session_key(f"{module_scope}:target_owner"),
            )

        agent_filter_options = [
            "all",
            "agent_tasks",
            "codex",
            "local_codex",
            "codex_cloud",
            "opencode",
        ]
        agent_filter = st.selectbox(
            ui.get("agent_harness_filter", "Harness result"),
            agent_filter_options,
            format_func=lambda value: ui.get(f"agent_harness_filter_{value}", value),
            key=_session_key(f"{module_scope}:agent_harness_filter"),
        )

    filters = {
        "status": status_filter,
        "kind": kind_filter,
        "candidate_type": candidate_filter,
        "target_owner": owner_filter,
    }
    if source_filter and source_filter != "all":
        filters["source_page"] = source_filter

    items = activity_items_for_page(selected, filters, sort=sort_mode)
    items = [item for item in items if _agent_harness_matches(item, agent_filter)]

    module_filter = {} if source_module == "all" else {"source_page": source_module}
    module_items = activity_items_for_page(selected, module_filter, sort="updated_desc")
    stale_module_ids = [
        str(item.get("id") or "")
        for item in module_items
        if str(item.get("status") or "") in {"failed", "dismissed"}
    ]

    with st.expander(ui.get("manage_activity", "Manage Activity"), expanded=False):
        st.caption(f"{ui.get('visible_items', 'Visible items')}: {len(items)}")
        m1, m2 = st.columns(2)
        with m1:
            confirm_visible = st.checkbox(
                ui.get("delete_visible_confirm", "Confirm delete all visible items"),
                key=_session_key(f"{module_scope}:delete_visible_confirm"),
            )
            if st.button(
                ui.get("delete_visible", "Delete current view"),
                key=_session_key(f"{module_scope}:delete_visible"),
                disabled=not confirm_visible or not items,
            ):
                _delete_and_rerun([str(item.get("id") or "") for item in items])
        with m2:
            confirm_stale = st.checkbox(
                ui.get(
                    "delete_failed_dismissed_confirm",
                    "Confirm delete failed and dismissed items in this module",
                ),
                key=_session_key(f"{module_scope}:delete_failed_dismissed_confirm"),
            )
            if st.button(
                ui.get(
                    "delete_failed_dismissed",
                    "Delete failed/dismissed in this module",
                ),
                key=_session_key(f"{module_scope}:delete_failed_dismissed"),
                disabled=not confirm_stale or not stale_module_ids,
            ):
                _delete_and_rerun(stale_module_ids)

    st.subheader(ui["items"])
    target_visible = focus_active and any(
        str(item.get("id") or "") == target_activity_item for item in items
    )
    if focus_active:
        if target_visible:
            st.info(
                ui.get("focused_item_notice", "Focused Activity item: {id}").format(
                    id=target_activity_item
                )
            )
        else:
            st.warning(
                ui.get(
                    "focused_item_missing",
                    "The focused Activity item is not visible with the current filters.",
                )
            )

    if not items:
        st.caption(ui["no_items"])
        return False

    for source_page, source_items in _group_items_by_source(items):
        if source_module == "all":
            st.markdown(f"**{ui.get('source_group', 'Source')}: {source_page}**")
        for item in source_items:
            item_id = str(item.get("id") or "")
            title = str(item.get("title", "") or item_id)
            status = str(item.get("status", "") or "")
            candidate_type = str(item.get("candidate_type", "") or "")
            owner = str(item.get("target_owner", "") or "")
            is_target = focus_active and item_id == target_activity_item
            if is_target:
                st.markdown(
                    f'<span id="{_focus_anchor_id(item_id, module_scope)}"></span>',
                    unsafe_allow_html=True,
                )
            with st.container(border=True):
                if is_target:
                    st.success(
                        ui.get("focused_item_highlight", "Opened from {source}.").format(
                            source=target_source_page or source_page
                        )
                    )
                h1, h2, h3, h4 = st.columns([5, 1.4, 1.7, 1.8])
                with h1:
                    st.markdown(f"**{title}**")
                    summary_source = item.get("summary") or item.get("source_ref") or ""
                    if status == "failed":
                        summary_source = item.get("source_ref") or _readable_error_text(
                            item.get("error") or item.get("summary") or ""
                        )
                    summary_text = _short_display(summary_source, 360)
                    if summary_text:
                        st.caption(summary_text)
                with h2:
                    st.caption(ui["status"])
                    st.write(_label(status))
                with h3:
                    st.caption(ui["target_owner"])
                    st.write(owner)
                with h4:
                    st.caption(ui["candidate_type"])
                    st.write(candidate_type)

                time_bits = []
                created = _format_local_time(item.get("created"))
                updated = _format_local_time(item.get("updated"))
                applied_at = _format_local_time(item.get("applied_at"))
                if created:
                    time_bits.append(f"{ui.get('created', 'Created')}: {created}")
                if updated:
                    time_bits.append(f"{ui.get('updated', 'Updated')}: {updated}")
                if applied_at:
                    time_bits.append(
                        f"{ui.get('applied_at', 'Applied')}: {applied_at}"
                    )
                if time_bits:
                    st.caption(" | ".join(time_bits))

                error_text = _readable_error_text(
                    item.get("error")
                    or (item.get("summary") if status == "failed" else "")
                )
                if error_text:
                    st.error(f"{ui.get('error_summary', 'Error')}: {error_text}")

                warnings = (
                    item.get("warnings") if isinstance(item.get("warnings"), list) else []
                )
                for warning in warnings:
                    st.warning(_short_display(warning, 500))

                agent_result = _agent_task_result(item)
                with st.expander(ui.get("technical_details", "Technical details")):
                    meta = {
                        "id": item_id,
                        "kind": item.get("kind"),
                        "candidate_type": candidate_type,
                        "source_page": item.get("source_page"),
                        "source_ref": item.get("source_ref"),
                        "target_owner": owner,
                        "status": status,
                        "created": created,
                        "updated": updated,
                        "applied_at": applied_at,
                        "error": error_text or item.get("error"),
                    }
                    meta.update(_agent_task_meta(item))
                    st.code(
                        yaml.dump(
                            _truncate_for_details(meta),
                            allow_unicode=True,
                            default_flow_style=False,
                            sort_keys=False,
                        ),
                        language="yaml",
                    )
                    tab_labels = [
                        ui["preview"],
                        ui["payload"],
                        ui["refs"],
                        ui["changed_paths"],
                    ]
                    if agent_result:
                        tab_labels.append(ui.get("agent_task_result", "Agent task result"))
                    tabs = st.tabs(tab_labels)
                    d1, d2, d3, d4 = tabs[:4]
                    d5 = tabs[4] if len(tabs) > 4 else None
                    with d1:
                        st.code(
                            _short_display(item.get("preview") or "-", 1200),
                            language="yaml",
                        )
                    with d2:
                        st.code(
                            yaml.dump(
                                _truncate_for_details(item.get("payload") or {}),
                                allow_unicode=True,
                                default_flow_style=False,
                                sort_keys=False,
                            ),
                            language="yaml",
                        )
                    with d3:
                        st.code(
                            yaml.dump(
                                _truncate_for_details(item.get("refs") or {}),
                                allow_unicode=True,
                                default_flow_style=False,
                                sort_keys=False,
                            ),
                            language="yaml",
                        )
                    with d4:
                        st.write(_truncate_for_details(item.get("changed_paths") or []))
                    if d5 is not None:
                        with d5:
                            st.code(
                                yaml.dump(
                                    _truncate_for_details(agent_result),
                                    allow_unicode=True,
                                    default_flow_style=False,
                                    sort_keys=False,
                                ),
                                language="yaml",
                            )
                            _render_codex_cloud_controls(
                                item,
                                agent_result,
                                key_scope=module_scope,
                            )

                a1, a2, a3, a4, a5 = st.columns(5)
                with a1:
                    if st.button(
                        ui["apply"],
                        key=f"activity_apply:{module_scope}:{item_id}",
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
                            result = apply_review_activity_item(selected, item_id)
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
                        key=f"activity_dismiss:{module_scope}:{item_id}",
                    ):
                        update_activity_status(selected, item_id, "dismissed")
                        stash_git_backup_results()
                        clear_web_cache()
                        st.success(ui["saved"])
                        st.rerun()
                with a3:
                    if status in {"dismissed", "failed"} and st.button(
                        ui["reopen"],
                        key=f"activity_reopen:{module_scope}:{item_id}",
                    ):
                        update_activity_status(selected, item_id, "pending")
                        stash_git_backup_results()
                        clear_web_cache()
                        st.success(ui["saved"])
                        st.rerun()
                with a4:
                    _safe_page_link(_owner_page(owner), ui["open_owner"])
                with a5:
                    confirm_item_delete = st.checkbox(
                        ui.get("delete_item_confirm", "Confirm delete this item"),
                        key=f"activity_delete_confirm:{module_scope}:{item_id}",
                    )
                    if st.button(
                        ui.get("delete_item", "Delete item"),
                        key=f"activity_delete:{module_scope}:{item_id}",
                        disabled=not confirm_item_delete,
                    ):
                        _delete_and_rerun([item_id])
                if not _can_apply_here(item):
                    st.caption(ui["apply_unavailable"])
    return target_visible


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
all_items = activity_items_for_page(selected, sort="updated_desc")
inferred_target_source = _source_for_item(all_items, target_activity_item)
target_module = target_source_page or inferred_target_source

source_pages = sorted(
    key for key in {str(item.get("source_page") or "").strip() for item in all_items}
    if key
)
if target_module and target_module not in source_pages:
    source_pages.append(target_module)
    source_pages = sorted(source_pages)
module_options = [target_module] if target_module else []
module_options.extend(["all", *source_pages])
module_options = list(dict.fromkeys(module_options))
focus_module = target_module or "all"
module_tabs = st.tabs([_module_label(module, all_items) for module in module_options])
focused_visible = False
for source_module, module_tab in zip(module_options, module_tabs):
    with module_tab:
        focused_visible = (
            _render_activity_module(
                source_module=source_module,
                source_pages=source_pages,
                summary=summary,
                target_activity_item=target_activity_item,
                target_source_page=target_source_page,
                focus_module=focus_module,
            )
            or focused_visible
        )

if focused_visible and target_activity_item:
    _render_focus_scroll(target_activity_item, _module_scope(focus_module))
