"""Human-admin profile initialization, independent of account creation."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from nblane.core import profile_setup
from nblane.web_api.auth import CurrentUser
from nblane.web_api.routes_v1 import ApiError, require_admin
from nblane.web_api.schemas import ErrorResponse

router = APIRouter(prefix="/api/v1/profiles", tags=["profiles"])


class ProfileCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    schema_name: str = Field(alias="schema", min_length=1, max_length=120)
    north_star: str = Field(default="", max_length=2000)
    goal_title: str = Field(default="", max_length=200)
    project_title: str = Field(default="", max_length=200)
    task_title: str = Field(default="", max_length=300)


class ProfileCreateResponse(BaseModel):
    name: str
    has_first_plan: bool


@router.post("", response_model=ProfileCreateResponse, status_code=201,
             responses={code: {"model": ErrorResponse} for code in (401, 403, 409, 422)})
def create_profile(
    body: ProfileCreateRequest,
    admin: CurrentUser = Depends(require_admin),
) -> ProfileCreateResponse:
    """Create a fully initialized private profile; admins automatically have access."""
    # Also defend direct handler reuse; the app-level guard rejects agents first.
    if admin.agent:
        raise ApiError(403, "web_only", "请由本人在网页中创建档案。")
    try:
        destination = profile_setup.create_profile(
            body.name, schema=body.schema_name, north_star=body.north_star,
            goal_title=body.goal_title, project_title=body.project_title, task_title=body.task_title,
        )
    except FileExistsError as exc:
        raise ApiError(409, "profile_exists", str(exc)) from exc
    except ValueError as exc:
        raise ApiError(422, "invalid_profile", str(exc)) from exc
    return ProfileCreateResponse(name=destination.name, has_first_plan=bool(body.goal_title.strip()))
