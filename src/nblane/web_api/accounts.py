"""Account management (admin only): list, create, edit, reset, API tokens.

All writes go through ``core/auth_store.py``; responses never carry
password or token hashes. A plaintext API token is returned exactly once,
by the create-token endpoint. Agent accounts get 403 from the agent
guard (``/api/v1/accounts*`` is outside the profile prefix → T3).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from nblane.core import auth as auth_core
from nblane.core import auth_store, profile_io, schema_io
from nblane.web_api.auth import CurrentUser
from nblane.web_api.routes_v1 import ApiError, require_admin
from nblane.web_api.schemas import ErrorResponse

router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])
_RESPONSES = {
    400: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
}

# AccountError code -> HTTP status.
_STATUS = {
    "auth_not_configured": 400,
    "auth_file_invalid": 500,
    "user_not_found": 404,
    "token_not_found": 404,
    "user_exists": 409,
    "profile_exists": 409,
    "cannot_disable_self": 409,
    "cannot_demote_self": 409,
    "last_admin": 409,
}


class ApiTokenInfo(BaseModel):
    """One API token without its hash."""

    id: str
    name: str = ""
    created: str = ""


class AccountInfo(BaseModel):
    """One account as shown in Settings → 账号管理."""

    id: str
    display_name: str
    role: str
    profiles: list[str] = Field(default_factory=list)
    agent: bool = False
    disabled: bool = False
    must_change_password: bool = False
    tokens: list[ApiTokenInfo] = Field(default_factory=list)


class AccountCreateRequest(BaseModel):
    id: str
    display_name: str = ""
    role: str = "member"
    password: str
    profiles: list[str] = Field(default_factory=list)
    # Create a profile named after the user id (409 profile_exists if taken).
    create_profile: bool = False
    # Domain schema for the new profile (empty = template default);
    # only used with create_profile. 422 unknown_schema if not found.
    schema_name: str = Field(default="", alias="schema")

    model_config = {"populate_by_name": True}


class AccountPatchRequest(BaseModel):
    display_name: str | None = None
    role: str | None = None
    profiles: list[str] | None = None
    disabled: bool | None = None


class ResetPasswordRequest(BaseModel):
    password: str


class TokenCreateRequest(BaseModel):
    name: str


class TokenCreateResponse(BaseModel):
    """The plaintext token is only ever returned here."""

    token: str
    id: str
    name: str
    created: str


class AccountsOk(BaseModel):
    ok: bool = True


def _raise(exc: auth_store.AccountError) -> ApiError:
    return ApiError(_STATUS.get(exc.code, 422), exc.code, exc.message)


def _require_auth() -> None:
    if not auth_core.auth_configured():
        raise ApiError(400, "auth_not_configured", "Auth is not configured.")


def _users() -> dict[str, auth_core.User]:
    try:
        return auth_core.load_users()
    except auth_core.AuthConfigError as exc:
        raise ApiError(500, "auth_file_invalid", str(exc)) from exc


def _info(user: auth_core.User) -> AccountInfo:
    return AccountInfo(
        id=user.id,
        display_name=user.display_name,
        role=user.role,
        profiles=list(user.profiles),
        agent=user.agent,
        disabled=user.disabled,
        must_change_password=user.must_change_password,
        tokens=[ApiTokenInfo(id=t.id, name=t.name, created=t.created) for t in user.api_tokens],
    )


def _account(user_id: str) -> AccountInfo:
    user = _users().get(user_id)
    if user is None:
        raise ApiError(404, "user_not_found", f"Unknown user: {user_id}")
    return _info(user)


@router.get("", response_model=list[AccountInfo], responses=_RESPONSES)
def list_accounts(_admin: CurrentUser = Depends(require_admin)) -> list[AccountInfo]:
    _require_auth()
    return [_info(u) for u in sorted(_users().values(), key=lambda u: u.id)]


@router.post("", response_model=AccountInfo, responses=_RESPONSES)
def create_account(
    payload: AccountCreateRequest,
    _admin: CurrentUser = Depends(require_admin),
) -> AccountInfo:
    _require_auth()
    profiles = list(payload.profiles)
    user_id = payload.id.strip()
    schema_name = payload.schema_name.strip()
    # Validate everything before creating a profile on disk.
    try:
        auth_store.validate_password(payload.password)
    except auth_store.AccountError as exc:
        raise _raise(exc) from exc
    if user_id in _users():
        raise ApiError(409, "user_exists", f"User already exists: {user_id}")
    if payload.create_profile:
        try:
            clean = profile_io.validate_profile_name(user_id)
        except ValueError as exc:
            raise ApiError(422, "invalid_user_id", str(exc)) from exc
        if clean in profile_io.list_profiles():
            raise ApiError(409, "profile_exists", f"Profile already exists: {clean}")
        if schema_name and schema_io.schema_path(schema_name) is None:
            raise ApiError(
                422, "unknown_schema", f"Unknown domain schema: {schema_name}"
            )
    try:
        auth_store.create_user(
            user_id,
            display_name=payload.display_name,
            role=payload.role,
            password=payload.password,
            profiles=profiles,
            must_change_password=True,
        )
    except auth_store.AccountError as exc:
        raise _raise(exc) from exc
    if payload.create_profile:
        try:
            profile_io.init_profile(user_id, schema=schema_name or None)
        except FileExistsError as exc:
            raise ApiError(409, "profile_exists", str(exc)) from exc
        except ValueError as exc:
            raise ApiError(422, "unknown_schema", str(exc)) from exc
        if user_id not in profiles:
            try:
                auth_store.update_user(
                    user_id, actor_id=_admin.id, profiles=[*profiles, user_id]
                )
            except auth_store.AccountError as exc:
                raise _raise(exc) from exc
    return _account(user_id)


@router.patch("/{user_id}", response_model=AccountInfo, responses=_RESPONSES)
def patch_account(
    user_id: str,
    payload: AccountPatchRequest,
    admin: CurrentUser = Depends(require_admin),
) -> AccountInfo:
    _require_auth()
    try:
        if payload.display_name is not None or payload.role is not None or payload.profiles is not None:
            auth_store.update_user(
                user_id,
                actor_id=admin.id,
                display_name=payload.display_name,
                role=payload.role,
                profiles=payload.profiles,
            )
        if payload.disabled is not None:
            auth_store.set_disabled(user_id, payload.disabled, actor_id=admin.id)
    except auth_store.AccountError as exc:
        raise _raise(exc) from exc
    return _account(user_id)


@router.post("/{user_id}/reset-password", response_model=AccountInfo, responses=_RESPONSES)
def reset_password(
    user_id: str,
    payload: ResetPasswordRequest,
    _admin: CurrentUser = Depends(require_admin),
) -> AccountInfo:
    """Set a temporary password; the user must change it at next login."""
    _require_auth()
    try:
        auth_store.set_password(user_id, payload.password, must_change=True)
    except auth_store.AccountError as exc:
        raise _raise(exc) from exc
    return _account(user_id)


@router.post("/{user_id}/tokens", response_model=TokenCreateResponse, responses=_RESPONSES)
def create_token(
    user_id: str,
    payload: TokenCreateRequest,
    _admin: CurrentUser = Depends(require_admin),
) -> TokenCreateResponse:
    _require_auth()
    try:
        plaintext, record = auth_store.create_api_token(user_id, payload.name)
    except auth_store.AccountError as exc:
        raise _raise(exc) from exc
    return TokenCreateResponse(
        token=plaintext, id=record.id, name=record.name, created=record.created
    )


@router.delete("/{user_id}/tokens/{token_id}", response_model=AccountsOk, responses=_RESPONSES)
def revoke_token(
    user_id: str,
    token_id: str,
    _admin: CurrentUser = Depends(require_admin),
) -> AccountsOk:
    _require_auth()
    try:
        auth_store.revoke_api_token(user_id, token_id)
    except auth_store.AccountError as exc:
        raise _raise(exc) from exc
    return AccountsOk()
