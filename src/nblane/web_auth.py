"""Streamlit authentication and authorization helpers."""

from __future__ import annotations

import html
import os
import time
from urllib.parse import urlparse

import streamlit as st

from nblane.core import auth as auth_core
from nblane.core import git_backup
from nblane.core.profile_io import list_profiles
from nblane.core.team_io import list_teams
from nblane.web_page_shell import ensure_wide_page_shell

_SESSION_USER_ID = "_nblane_auth_user_id"
_SIDECAR_AUTH_SYNC_KEY = "_nblane_sidecar_auth_sync"
_SIDECAR_AUTH_LOGOUT_KEY = "_nblane_sidecar_auth_logout"


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


def _sidecar_auth_base() -> str:
    """Return the browser-facing sidecar base for auth handoff if known."""

    raw = (
        os.getenv("NBLANE_READER_API_BASE", "").strip()
        or os.getenv("NBLANE_PAPER_LIBRARY_BASE", "").strip()
        or "http://127.0.0.1:8502"
    )
    if raw.lower() in {"0", "false", "off", "none"}:
        return _sidecar_base_for_same_origin_mode()
    return raw.rstrip("/")


def _sidecar_base_for_same_origin_mode() -> str:
    try:
        current_url = str(getattr(st.context, "url", "") or "").strip()
    except Exception:
        current_url = ""
    if current_url:
        parsed = urlparse(current_url)
        host = (parsed.hostname or "").strip().lower()
        if parsed.scheme in {"http", "https"} and host in {"localhost", "127.0.0.1"}:
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            sidecar_port = {8501: 8502, 8503: 8502, 18503: 18502}.get(port)
            if sidecar_port:
                return f"{parsed.scheme}://{parsed.hostname}:{sidecar_port}"
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
    return os.getenv("NBLANE_STREAMLIT_BASE_URL", "").strip().rstrip("/")


def _sidecar_auth_url(path: str) -> str:
    base = _sidecar_auth_base()
    clean_path = path if path.startswith("/") else f"/{path}"
    return f"{base}{clean_path}" if base else clean_path


def sidecar_auth_handoff_token(user: auth_core.User | None = None) -> str:
    """Return a short-lived token that lets 8502 set its own auth cookie."""

    if not auth_enabled():
        return ""
    active_user = user or current_user()
    if active_user is None:
        return ""
    try:
        return auth_core.mint_auth_handoff_token(active_user.id)
    except auth_core.AuthConfigError as exc:
        st.error(f"Auth configuration error: {exc}")
        st.stop()


def _render_sidecar_frame(src: str) -> None:
    escaped = html.escape(src, quote=True)
    st.components.v1.html(
        (
            '<iframe title="nblane auth" '
            f'src="{escaped}" '
            'style="display:none;width:0;height:0;border:0" '
            'aria-hidden="true"></iframe>'
        ),
        height=0,
    )


def _render_sidecar_auth_post(token: str) -> None:
    action = html.escape(_sidecar_auth_url("/auth/session"), quote=True)
    escaped_token = html.escape(token, quote=True)
    st.components.v1.html(
        (
            '<iframe title="nblane auth" name="nblane_auth_target" '
            'style="display:none;width:0;height:0;border:0" '
            'aria-hidden="true"></iframe>'
            f'<form id="nblane-auth-form" action="{action}" method="post" '
            'target="nblane_auth_target" style="display:none">'
            f'<input type="hidden" name="token" value="{escaped_token}">'
            "</form>"
            "<script>"
            "const form=document.getElementById('nblane-auth-form');"
            "if(form){form.submit();}"
            "</script>"
        ),
        height=0,
    )


def _render_sidecar_auth_bridge(user: auth_core.User) -> None:
    token = sidecar_auth_handoff_token(user)
    if not token:
        return
    now = time.time()
    state = st.session_state.get(_SIDECAR_AUTH_SYNC_KEY)
    if (
        isinstance(state, dict)
        and state.get("user_id") == user.id
        and now - float(state.get("synced_at") or 0) < 60
    ):
        return
    _render_sidecar_auth_post(token)
    st.session_state[_SIDECAR_AUTH_SYNC_KEY] = {
        "user_id": user.id,
        "synced_at": now,
    }


def _render_sidecar_logout_bridge() -> None:
    if not st.session_state.pop(_SIDECAR_AUTH_LOGOUT_KEY, False):
        return
    st.session_state.pop(_SIDECAR_AUTH_SYNC_KEY, None)
    _render_sidecar_frame(_sidecar_auth_url("/auth/logout"))


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
    st.session_state[_SIDECAR_AUTH_LOGOUT_KEY] = True
    st.session_state.pop(_SIDECAR_AUTH_SYNC_KEY, None)


def _render_login(users: dict[str, auth_core.User]) -> None:
    """Render password login and stop the current page."""
    _render_sidecar_logout_bridge()
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
    ensure_wide_page_shell()
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
    _render_sidecar_auth_bridge(user)
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
