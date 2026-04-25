"""Streamlit authentication and authorization helpers."""

from __future__ import annotations

import streamlit as st

from nblane.core import auth as auth_core
from nblane.core import git_backup
from nblane.core.profile_io import list_profiles
from nblane.core.team_io import list_teams

_SESSION_USER_ID = "_nblane_auth_user_id"


def _local_user() -> auth_core.User:
    """Development user when no auth file is configured."""
    return auth_core.User(
        id="local",
        display_name="Local",
        password_hash="",
        role="admin",
        teams=("*",),
    )


def auth_enabled() -> bool:
    """Whether Streamlit login is enabled for this process."""
    return auth_core.auth_configured()


def _load_users_or_stop() -> dict[str, auth_core.User]:
    try:
        return auth_core.load_users()
    except auth_core.AuthConfigError as exc:
        st.error(f"Auth configuration error: {exc}")
        st.stop()


def current_user() -> auth_core.User | None:
    """Return the current logged-in user, or local admin when auth is off."""
    if not auth_enabled():
        return _local_user()
    users = _load_users_or_stop()
    user_id = st.session_state.get(_SESSION_USER_ID)
    if not isinstance(user_id, str):
        return None
    return users.get(user_id)


def logout() -> None:
    """Clear the active login session."""
    st.session_state.pop(_SESSION_USER_ID, None)


def _render_login(users: dict[str, auth_core.User]) -> None:
    """Render password login and stop the current page."""
    st.title("nblane")
    st.caption("Sign in to continue.")
    with st.form("nblane_login_form"):
        user_id = st.text_input("User ID")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", type="primary")
    if submitted:
        user = users.get(user_id.strip())
        if user and auth_core.verify_password(password, user.password_hash):
            st.session_state[_SESSION_USER_ID] = user.id
            git_backup.set_actor(user.id)
            st.rerun()
        st.error("Invalid user ID or password.")
    st.stop()


def require_login() -> auth_core.User:
    """Require a logged-in user and return it."""
    if not auth_enabled():
        user = _local_user()
        git_backup.start_operation(user.id)
        return user
    users = _load_users_or_stop()
    user = current_user()
    if user is None:
        _render_login(users)
    assert user is not None
    git_backup.start_operation(user.id)
    with st.sidebar:
        st.caption(f"Signed in as {user.display_name}")
        if st.button("Sign out", key="_nblane_sign_out"):
            logout()
            st.rerun()
    return user


def can_create_profiles() -> bool:
    """Whether the current user can create new profiles."""
    user = current_user()
    return bool(user and user.is_admin)


def allowed_profiles() -> list[str]:
    """Return profile names visible to the current user."""
    profiles = list_profiles()
    user = current_user()
    if user is None:
        return []
    if user.is_admin:
        return profiles
    allowed = set(user.profiles)
    return [name for name in profiles if name in allowed]


def allowed_teams() -> list[str]:
    """Return team IDs visible to the current user."""
    teams = list_teams()
    user = current_user()
    if user is None:
        return []
    if user.is_admin or "*" in user.teams:
        return teams
    allowed = set(user.teams)
    return [team for team in teams if team in allowed]
