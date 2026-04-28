"""Team View -- editable product pool and team config."""

from __future__ import annotations

import streamlit as st

from nblane.core.io import (
    save_product_pool,
    save_team,
)
from nblane.core.paths import TEAMS_DIR
from nblane.web_cache import (
    clear_web_cache,
    load_product_pool,
    load_team,
)
from nblane.web_i18n import all_pool_keys, pool_label, team_ui
from nblane.web_auth import allowed_teams, require_login
from nblane.web_shared import (
    apply_ui_language_from_session,
    assert_files_current,
    ensure_file_snapshot,
    refresh_file_snapshots,
    render_git_backup_notices,
    select_profile,
    stash_git_backup_results,
    ui_emoji_enabled,
)

_POOL_EMOJI = {
    "problem_pool": "🔍",
    "project_pool": "🚀",
    "evidence_pool": "📄",
    "method_pool": "🔧",
    "decision_pool": "⚖️",
}


# -- Page --------------------------------------------------------

apply_ui_language_from_session()

ui = team_ui()
st.set_page_config(
    page_title=ui["page_title"], layout="wide"
)

require_login()
selected_profile = select_profile()
render_git_backup_notices()

st.title(ui["title"])
st.caption(ui["page_context_line"])
st.caption(
    ui["team_profile_scope"].format(profile=selected_profile)
)

teams = allowed_teams()
if not teams:
    st.warning(ui["no_teams"])
    st.stop()

selected_team = st.selectbox(ui["team_select"], teams)
_team_path = TEAMS_DIR / selected_team / "team.yaml"
_pool_path = TEAMS_DIR / selected_team / "product-pool.yaml"
ensure_file_snapshot(_team_path)
ensure_file_snapshot(_pool_path)

team_data = load_team(selected_team) or {}
pool_data = load_product_pool(selected_team) or {}

# -- Team info (editable) ---------------------------------------

st.subheader(ui["sub_team"])

with st.container(border=True):
    c_name, c_mission = st.columns(2)
    with c_name:
        team_name = st.text_input(
            ui["team_name"],
            value=team_data.get(
                "name",
                team_data.get(
                    "team_name", selected_team
                ),
            ),
            key="team_name_input",
        )
    with c_mission:
        mission = st.text_input(
            ui["mission"],
            value=(
                team_data.get("mission", "")
                or ", ".join(
                    team_data.get("shared_focus", [])
                )
            ),
            key="team_mission_input",
        )

    members_raw = team_data.get("members") or []
    members_str = st.text_input(
        ui["members"],
        value=", ".join(str(m) for m in members_raw),
        key="team_members_input",
    )

    rules_raw = team_data.get("shared_rules") or []
    rules_str = st.text_area(
        ui["rules"],
        value="\n".join(rules_raw),
        height=80,
        key="team_rules_input",
    )

    priorities_raw = (
        team_data.get("current_priorities") or []
    )
    priorities_str = st.text_area(
        ui["priorities"],
        value="\n".join(priorities_raw),
        height=80,
        key="team_priorities_input",
    )

    if st.button(
        ui["save_team"], type="primary"
    ):
        assert_files_current([_team_path])
        new_team = {
            "schema_version": team_data.get(
                "schema_version", "1.0"
            ),
            "team_name": team_name,
            "shared_focus": [
                s.strip()
                for s in mission.split(",")
                if s.strip()
            ],
            "members": [
                m.strip()
                for m in members_str.split(",")
                if m.strip()
            ],
            "shared_rules": [
                r.strip()
                for r in rules_str.splitlines()
                if r.strip()
            ],
            "current_priorities": [
                p.strip()
                for p in priorities_str.splitlines()
                if p.strip()
            ],
        }
        save_team(selected_team, new_team)
        clear_web_cache()
        refresh_file_snapshots([_team_path])
        stash_git_backup_results()
        st.success(ui["team_saved"])
        st.rerun()

st.divider()

# -- Product pool (editable) ------------------------------------

st.subheader(ui["sub_pool"])

pool_keys = all_pool_keys()
pool_state_key = f"pool_{selected_team}"
if pool_state_key not in st.session_state:
    st.session_state[pool_state_key] = {
        k: list(pool_data.get(k, []))
        for k in pool_keys
    }
pool_state = st.session_state[pool_state_key]

pool_tabs = st.tabs(
    [
        (
            f"{_POOL_EMOJI.get(k, '📦')} {pool_label(k)}"
            if ui_emoji_enabled()
            else pool_label(k)
        )
        for k in pool_keys
    ]
)

for tab, pool_key in zip(pool_tabs, pool_keys):
    with tab:
        items = pool_state.get(pool_key, [])
        label = pool_label(pool_key)

        st.caption(
            ui["items_count"].format(n=len(items))
        )

        to_delete: list[int] = []
        for idx, item in enumerate(items):
            with st.container(border=True):
                ic1, ic2 = st.columns([9, 1])

                with ic1:
                    if isinstance(item, dict):
                        title = (
                            item.get("title")
                            or item.get("name")
                            or item.get("id")
                            or ""
                        )
                        new_title = st.text_input(
                            ui["field_title"],
                            value=title,
                            key=(
                                f"pt_{pool_key}_{idx}"
                            ),
                            label_visibility=(
                                "collapsed"
                            ),
                        )
                        skip = {
                            "title",
                            "name",
                            "id",
                        }
                        other_fields = {
                            k: v
                            for k, v in item.items()
                            if k not in skip
                            and v is not None
                        }
                        if other_fields:
                            for fk, fv in (
                                other_fields.items()
                            ):
                                if isinstance(
                                    fv, list
                                ):
                                    st.caption(
                                        f"{fk}: "
                                        + ", ".join(
                                            str(x)
                                            for x in fv
                                        )
                                    )
                                else:
                                    st.caption(
                                        f"{fk}: {fv}"
                                    )
                        items[idx] = new_title
                    else:
                        new_val = st.text_input(
                            ui["field_item"],
                            value=str(item),
                            key=(
                                f"pt_{pool_key}_{idx}"
                            ),
                            label_visibility=(
                                "collapsed"
                            ),
                        )
                        items[idx] = new_val

                with ic2:
                    if st.button(
                        "✕",
                        key=f"pdel_{pool_key}_{idx}",
                    ):
                        to_delete.append(idx)

        for idx in reversed(to_delete):
            items.pop(idx)

        pool_state[pool_key] = items

        new_item = st.text_input(
            ui["add_pool"].format(label=label),
            key=f"new_{pool_key}",
            placeholder=ui["add_pool_ph"].format(
                label=label
            ),
        )
        if new_item.strip() and st.button(
            ui["add"], key=f"add_{pool_key}"
        ):
            items.append(new_item.strip())
            pool_state[pool_key] = items
            st.rerun()

st.divider()

if st.button(
    ui["save_pool"], type="primary"
):
    assert_files_current([_pool_path])
    save_data = {
        "schema_version": pool_data.get(
            "schema_version", "1.0"
        )
    }
    for pk in pool_keys:
        save_data[pk] = [
            item
            for item in pool_state.get(pk, [])
            if item
        ]
    save_product_pool(selected_team, save_data)
    clear_web_cache()
    refresh_file_snapshots([_pool_path])
    stash_git_backup_results()
    st.success(ui["pool_saved"])
    st.rerun()
