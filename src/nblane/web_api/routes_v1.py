"""v1 routes for the nblane FastAPI backend.

Read routes plus the mutation slices: Agent Activity apply/dismiss and the
Inbox quick-capture loop (capture/clarify/archive/discard).
All routes here require an authenticated session (``require_user``) except
``GET /api/v1/health``, which stays open as a liveness probe.

Mutation concurrency contract (see
``docs/zh/architecture/frontend-spa-migration.md`` §2): activity and inbox
reads carry a weak ETag — ``W/"<sha256>"`` where the sha256 is the
``core.file_state.snapshot_file`` fingerprint of the profile's
``agent-activity.yaml`` / ``inbox.yaml`` / ``kanban.md``. The validator is
weak because the hash covers the source YAML/markdown file, not the JSON
representation bytes. Mutations accept an ``If-Match`` header carrying
that ETag; a mismatch answers ``412 Precondition Failed`` with the current
item in the body. A missing ``If-Match`` proceeds (the SPA always sends
it); the flock-protected core savers still serialize the writes
themselves. Every mutation also passes its request-start snapshot to the
core saver as ``expected_snapshot``: the saver re-checks the fingerprint
inside the write lock and raises ``file_state.FileConflictError`` on
mismatch, which the route maps to the same 412 (``etag_mismatch``) with a
fresh ETag — so a concurrent write landing between the If-Match check and
the lock acquisition can no longer be silently overwritten (no TOCTOU
window). Kanban mutations additionally take the request-start snapshot
as ``expected_snapshot`` for ``save_kanban_with_merge``, which re-checks
inside the lock and 3-way merges instead of failing, reported via
``merged_external`` / ``merge_notices``.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import os
import re
from dataclasses import replace
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Header, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from nblane.core import agent_activity, agent_tasks, file_state, gap, inbox
from nblane.core import evidence_review as evidence_review_core
from nblane.core import activity_log, home_dashboard, jd_match, learning_log, task_intake
from nblane.core import auth as auth_core
from nblane.core import profile_io, schema_io
from nblane.core.ai.gateway import run_ai_action
from nblane.core.claims import accepted_claims_for_profile
from nblane.core.evidence_resolve import resolve_node_evidence_dict
from nblane.core.experience import load_experience_book
from nblane.core.goals import load_goal_book
from nblane.core.kanban_archive import _archive_tasks
from nblane.core.kanban_io import (
    KANBAN_DOING,
    KANBAN_DONE,
    KANBAN_SECTIONS,
    apply_kanban_reorder,
    ensure_kanban_task_ids,
    find_kanban_card,
    kanban_path,
    parse_kanban,
    resolve_kanban_section,
)
from nblane.core.kanban_merge import copy_kanban_sections, save_kanban_with_merge
from nblane.core import llm as llm_client
from nblane.core.models import EVIDENCE_REVIEW_STATUSES, EvidenceRecord, KanbanTask
from nblane.core.growth_review import build_weekly_review
from nblane.core.public_curation import evidence_contexts
from nblane.core.public_site import (
    BLOG_DIRNAME,
    BLOG_TAXONOMY_FILENAME,
    OUTPUTS_FILENAME,
    PROJECTS_FILENAME,
    PUBLIC_LIBRARY_FILENAME,
    PUBLIC_PROFILE_FILENAME,
    PUBLISH_STATUSES,
    RESUME_SOURCE_FILENAME,
    PublicSiteError,
    blog_candidate_from_claims,
    blog_candidate_from_evidence,
    create_blog_draft,
    draft_blog_from_claims,
    draft_blog_from_evidence,
    draft_project_update_from_claims,
    format_blog_document,
    init_public_layer,
    load_blog_post,
    load_blog_posts,
    load_projects,
    markdown_contains_math,
    parse_blog_post,
    project_update_candidate_from_claims,
    publish_blog_text,
    resume_bullet_candidates_from_claims,
    save_blog_post,
    validate_blog_text_for_publish,
)
from nblane.core.project_board import (
    MILESTONE_STATUSES,
    PROJECT_KINDS,
    PROJECT_STATUSES,
    PROJECT_VISIBILITIES,
    ProjectBoard,
    ProjectCase,
    ProjectMilestone,
    add_project_case,
    load_project_board,
    update_project_case,
)
from nblane.core.project_board_events import (
    clean_ref_list,
    timeline_date_range,
    timeline_tasks,
)
from nblane.core.project_board_sync import (
    sync_project_board_from_kanban,
    sync_project_case_workspace,
)
from nblane.core.research_sources import load_research_sources
from nblane.core.research_workspace import (
    load_research_citations,
    load_research_claims,
)
from nblane.core.yaml_io import _load_yaml_dict
from nblane.core.profile_context import (
    normalize_north_star_visibility,
    parse_identity_fields,
)
from nblane.core.profile_health import analyze_profile_health
from nblane.core.review_actions import (
    apply_review_activity_item,
    apply_review_evidence_candidate,
    apply_review_next_action_candidate,
    apply_review_public_draft_candidate,
    normalize_review_window,
    record_writeback_activity,
    review_window_default,
    save_review_candidates_to_activity,
)
from nblane.core.status import count_nodes
from nblane.core.sync import write_generated_blocks
from nblane.web_api.auth import CurrentUser, require_user
from nblane.web_api.schemas import (
    ActivityApplyResponse,
    ActivityDismissRequest,
    ActivityDismissResponse,
    ActivityItemErrorResponse,
    ActivityItemModel,
    ActivityListResponse,
    ActivitySummaryModel,
    AgentTaskListResponse,
    AgentTaskModel,
    ErrorResponse,
    EvidenceEntryDetailModel,
    EvidenceEntryModel,
    EvidenceListResponse,
    EvidenceReviewBulkRequest,
    EvidenceReviewDeprecateRequest,
    EvidenceReviewItemModel,
    EvidenceReviewListResponse,
    EvidenceReviewMutationResponse,
    EvidenceReviewSummaryModel,
    EvidenceSummary,
    GapAnalysisResponse,
    GapAnalyzeRequest,
    GapClosureNodeModel,
    GapIntakeRequest,
    GapTopMatchModel,
    GoalModel,
    GoalSummary,
    GoalsResponse,
    HealthIssueModel,
    HealthReportModel,
    HealthResponse,
    HomeAgentActivityModel,
    HomeClaimsModel,
    HomeEvidenceModel,
    HomeGoalModel,
    HomeHealthModel,
    HomeKanbanModel,
    HomeKanbanTaskModel,
    HomeProjectsModel,
    HomeResponse,
    HomeSkillsModel,
    HomeSourcesModel,
    InboxCaptureRequest,
    InboxClarifyRequest,
    InboxItemErrorResponse,
    InboxItemModel,
    InboxMutationResponse,
    InboxNoteRequest,
    InboxResponse,
    KanbanBoardResponse,
    KanbanCardCreateRequest,
    KanbanCardMoveRequest,
    KanbanMutationResponse,
    KanbanSectionModel,
    KanbanSubtaskModel,
    KanbanSummary,
    KanbanTaskModel,
    NorthStarModel,
    ProfileDetailSummary,
    ProfileSummary,
    ProjectBoardOptionsModel,
    ProjectBoardResponse,
    ProjectBoardSummaryModel,
    ProjectCaseCreateRequest,
    ProjectCaseModel,
    ProjectCaseMutationResponse,
    ProjectCaseUpdateRequest,
    ProjectMilestoneAddRequest,
    ProjectMilestoneModel,
    ProjectMilestoneUpdateRequest,
    ProjectRefOptionModel,
    ProjectSuggestRefsResponse,
    ProjectTaskCreateRequest,
    ProjectTaskModel,
    ProjectTaskMoveRequest,
    ResearchResponse,
    ResearchSourceItemModel,
    ResearchSummaryModel,
    ReviewApplyRequest,
    ReviewApplyResponse,
    ReviewApplyResultModel,
    ReviewCandidateModel,
    ReviewResponse,
    ReviewSaveRequest,
    ReviewSaveResponse,
    ReviewSummaryModel,
    SidecarInfoModel,
    SkillTreeNodeModel,
    SkillTreeResponse,
    SkillTreeSummary,
    StudioCandidateRequest,
    StudioCandidateResponse,
    StudioDraftResponse,
    StudioInitResponse,
    StudioJdMatchRequest,
    StudioJdMatchResponse,
    StudioOptionsModel,
    StudioPostCreateRequest,
    StudioPostDetailModel,
    StudioPostModel,
    StudioPostMutationResponse,
    StudioPostSaveRequest,
    StudioResponse,
    StudioSourceOptionModel,
    StudioSummaryModel,
    StudioValidationResponse,
)

ERROR_RESPONSES = {
    400: {"model": ErrorResponse, "description": "Invalid profile name."},
    403: {"model": ErrorResponse, "description": "Profile access denied."},
    404: {"model": ErrorResponse, "description": "Profile not found."},
}


class ApiError(Exception):
    """Raised by route handlers to produce a structured error response."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def app_version() -> str:
    """Return the installed package version, or a static fallback."""
    try:
        return importlib.metadata.version("nblane")
    except importlib.metadata.PackageNotFoundError:
        return "0.0.0"


router = APIRouter(prefix="/api/v1")


def _resolve_profile(name: str):
    """Validate *name* and return its profile directory.

    Raises ApiError(400) for unsafe names and ApiError(404) for valid
    names that do not correspond to an existing profile.
    """
    try:
        clean = profile_io.validate_profile_name(name)
    except ValueError as exc:
        raise ApiError(400, "invalid_profile_name", str(exc)) from exc
    if clean not in profile_io.list_profiles():
        raise ApiError(404, "profile_not_found", f"Unknown profile: {clean}")
    return profile_io.profile_dir(clean)


def _core_user(user: CurrentUser) -> auth_core.User:
    """Rebuild the core ``User`` view used by the scope helpers."""
    return auth_core.User(
        id=user.id,
        display_name=user.display_name,
        password_hash="",
        role=user.role,
        profiles=tuple(user.profiles),
        teams=tuple(user.teams),
    )


def require_profile_access(
    name: str,
    user: CurrentUser = Depends(require_user),
) -> CurrentUser:
    """Dependency: 403 when the current user may not access profile *name*.

    Delegates to ``nblane.core.auth.can_access_profile`` (admin role or an
    explicit ``profiles`` entry on the user record; the auth-off synthetic
    local admin is allowed everywhere). The scope check runs before the
    handler's 404 lookup so a denied user cannot probe profile existence.
    """
    try:
        clean = profile_io.validate_profile_name(name)
    except ValueError as exc:
        raise ApiError(400, "invalid_profile_name", str(exc)) from exc
    if not auth_core.can_access_profile(_core_user(user), clean):
        raise ApiError(
            403,
            "profile_forbidden",
            f"User {user.id!r} may not access profile: {clean}",
        )
    return user


PROFILE_DEPENDENCY = [Depends(require_profile_access)]


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Liveness probe with the API/package version."""
    return HealthResponse(ok=True, version=app_version())


@router.get("/profiles", response_model=list[ProfileSummary])
def list_profiles(user: CurrentUser = Depends(require_user)) -> list[ProfileSummary]:
    """List known profiles with a few cheap summary fields.

    Scope-filtered with the same rule as ``require_profile_access``: admins
    (and the auth-off synthetic local admin) see every profile, members only
    the profiles granted on their user record — inaccessible profiles are
    omitted entirely rather than answered with 403.
    """
    core_user = _core_user(user)
    out: list[ProfileSummary] = []
    for name in profile_io.list_profiles():
        if not auth_core.can_access_profile(core_user, name):
            continue
        pdir = profile_io.profile_dir(name)
        tree = profile_io.load_skill_tree(pdir)
        book = profile_io.load_goal_book(pdir)
        current = book.current() if book is not None else None
        out.append(
            ProfileSummary(
                name=name,
                skill_schema=tree.schema if tree else "",
                skill_tree_updated=tree.updated if tree else "",
                skill_node_count=len(tree.nodes) if tree else 0,
                current_goal_title=current.title if current else "",
            )
        )
    return out


@router.get(
    "/profiles/{name}/summary",
    response_model=ProfileDetailSummary,
    responses=ERROR_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def get_profile_summary(name: str) -> ProfileDetailSummary:
    """Structured JSON summary for one profile."""
    pdir = _resolve_profile(name)

    tree = profile_io.load_skill_tree(pdir)
    tree_summary = SkillTreeSummary()
    if tree is not None:
        status_counts: dict[str, int] = {}
        for node in tree.nodes:
            if node.status:
                status_counts[node.status] = status_counts.get(node.status, 0) + 1
        tree_summary = SkillTreeSummary(
            skill_schema=tree.schema,
            updated=tree.updated,
            node_count=len(tree.nodes),
            status_counts=status_counts,
        )

    book = profile_io.load_goal_book(pdir)
    current = book.current() if book is not None else None
    goal_summary = (
        GoalSummary(
            id=current.id,
            title=current.title,
            status=current.status,
            target=current.target,
        )
        if current is not None
        else None
    )

    sections = parse_kanban(pdir)
    section_counts = {
        section: len(sections.get(section) or []) for section in KANBAN_SECTIONS
    }
    kanban_summary = KanbanSummary(
        section_counts=section_counts,
        total=sum(section_counts.values()),
    )

    pool = profile_io.load_evidence_pool(pdir)
    evidence_summary = EvidenceSummary(
        entries=len(pool.evidence_entries) if pool else 0,
        claims=len(pool.claims) if pool else 0,
    )

    return ProfileDetailSummary(
        profile=pdir.name,
        skill_tree=tree_summary,
        current_goal=goal_summary,
        kanban=kanban_summary,
        evidence=evidence_summary,
    )


@router.get(
    "/profiles/{name}/skill-tree",
    response_model=SkillTreeResponse,
    responses=ERROR_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def get_profile_skill_tree(name: str) -> SkillTreeResponse:
    """Full skill tree: status counters plus the nested node tree.

    The profile overlay (``skill-tree.yaml``) is a flat list of
    ``{id, status, note, evidence_refs}``; titles and hierarchy come from
    the domain schema it references. ``title`` is the schema ``label``
    (node id as fallback); ``children`` are derived from schema
    ``requires`` edges restricted to overlay nodes (X is a child of Y when
    X requires Y). Overlay nodes with no prerequisite inside the overlay
    become roots; unknown-to-schema nodes keep overlay order at the end.
    A profile without ``skill-tree.yaml`` answers 200 with empty nodes.
    """
    pdir = _resolve_profile(name)
    raw = profile_io.load_skill_tree_raw(pdir) or {}
    schema_name = str(raw.get("schema") or "")
    schema = schema_io.load_schema(schema_name) if schema_name else None
    pool = profile_io.load_evidence_pool(pdir)

    overlay: dict[str, dict] = {}
    for node in raw.get("nodes") or []:
        if isinstance(node, dict) and node.get("id"):
            overlay[str(node["id"])] = node

    schema_index = {sn.id: sn for sn in schema.nodes} if schema else {}
    order = {sn.id: i for i, sn in enumerate(schema.nodes)} if schema else {}
    for i, nid in enumerate(overlay):
        if nid not in order:
            order[nid] = len(schema_index) + i

    children_of: dict[str, list[str]] = {nid: [] for nid in overlay}
    has_parent: set[str] = set()
    for nid in overlay:
        reqs = schema_index[nid].requires if nid in schema_index else []
        for req in reqs:
            if req in overlay and req != nid:
                children_of[req].append(nid)
                has_parent.add(nid)
    for kids in children_of.values():
        kids.sort(key=lambda kid: order.get(kid, 0))
    roots = sorted(
        (nid for nid in overlay if nid not in has_parent),
        key=lambda nid: order.get(nid, 0),
    )

    def build(nid: str, ancestors: frozenset[str]) -> SkillTreeNodeModel:
        node = overlay[nid]
        meta = schema_index.get(nid)
        title = (meta.label if meta else "") or nid
        placed.add(nid)
        return SkillTreeNodeModel(
            id=nid,
            title=title,
            status=str(node.get("status") or "locked"),
            evidence_count=len(resolve_node_evidence_dict(node, pool)),
            children=[
                build(kid, ancestors | {kid})
                for kid in children_of[nid]
                if kid not in ancestors and kid not in placed
            ],
        )

    # DAG diamonds (a node requiring two overlay parents) are rendered under
    # the first parent in schema order; the ``placed`` guard keeps every
    # node in the response exactly once.
    placed: set[str] = set()
    nodes: list[SkillTreeNodeModel] = []
    for nid in roots + [
        n for n in sorted(overlay, key=lambda x: order.get(x, 0)) if n not in roots
    ]:
        if nid not in placed:
            nodes.append(build(nid, frozenset({nid})))

    return SkillTreeResponse(
        profile=pdir.name,
        schema_name=schema_name,
        updated=str(raw.get("updated") or ""),
        status_counts=count_nodes(raw),
        nodes=nodes,
    )


@router.get(
    "/profiles/{name}/health",
    response_model=HealthReportModel,
    responses=ERROR_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def get_profile_health(name: str) -> HealthReportModel:
    """Profile health report (validate/sync/evidence/kanban issues)."""
    _resolve_profile(name)
    report = analyze_profile_health(name)
    return HealthReportModel(
        profile=report.profile,
        can_publish_context=report.can_publish_context,
        summary_counts=report.summary_counts,
        issues=[
            HealthIssueModel(
                severity=issue.severity,
                category=issue.category,
                title=issue.title,
                detail=issue.detail,
                action=issue.action,
            )
            for issue in report.issues
        ],
    )


@router.get(
    "/profiles/{name}/activity",
    response_model=ActivityListResponse,
    responses=ERROR_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def get_profile_activity(
    name: str,
    status: str = Query("pending"),
    kind: str = Query(""),
    limit: int = Query(50, ge=1, le=500),
) -> ActivityListResponse:
    """Agent Activity review queue items plus queue-wide summary counters.

    ``status`` defaults to ``pending``; pass ``all`` to disable the status
    filter. ``kind`` filters on the item kind (candidate/patch/writeback).
    The summary block counts the whole queue, ignoring filters.
    """
    pdir = _resolve_profile(name)
    items = agent_activity.activity_items_for_page(
        pdir, {"status": status, "kind": kind}
    )
    total = len(items)
    summary = agent_activity.activity_summary(pdir)
    return ActivityListResponse(
        profile=pdir.name,
        status=status,
        kind=kind,
        limit=limit,
        total=total,
        items=[ActivityItemModel(**item) for item in items[:limit]],
        summary=ActivitySummaryModel(**summary),
    )


MUTATION_RESPONSES = {
    **ERROR_RESPONSES,
    409: {
        "model": ActivityItemErrorResponse,
        "description": "Item state conflict (not pending/appliable, apply failed).",
    },
    412: {
        "model": ActivityItemErrorResponse,
        "description": "If-Match ETag does not match the current activity file.",
    },
}


def _activity_etag(pdir: Path) -> str:
    """Weak ETag for the profile's agent-activity.yaml (sha256 fingerprint).

    Weak (``W/``) because the hash identifies the source YAML file version,
    not the JSON response bytes. ``empty`` marks a missing file.
    """
    snapshot = file_state.snapshot_file(
        pdir / agent_activity.AGENT_ACTIVITY_FILENAME
    )
    return f'W/"{snapshot.sha256 or "empty"}"'


def _normalize_etag(token: str) -> str:
    """Strip an optional weak prefix and quotes from one ETag token."""
    clean = token.strip()
    if clean.startswith("W/"):
        clean = clean[2:].strip()
    return clean.strip('"')


def _if_match_satisfied(if_match: str | None, current_etag: str) -> bool:
    """True when If-Match is absent, ``*``, or lists the current ETag.

    Comparison is weak (prefix/quotes ignored), so the SPA may send the
    ETag exactly as received. An absent header proceeds by design — the
    SPA always sends it, but the core savers are flock-protected either
    way.
    """
    if if_match is None:
        return True
    candidates = [
        _normalize_etag(part) for part in if_match.split(",") if part.strip()
    ]
    if "*" in candidates:
        return True
    return _normalize_etag(current_etag) in candidates


def _find_activity_item(pdir: Path, item_id: str) -> dict[str, Any]:
    """Return the normalized activity item or raise ApiError(404)."""
    for item in agent_activity.load_agent_activity(pdir).get("items") or []:
        if str(item.get("id") or "").strip() == item_id:
            return item
    raise ApiError(
        404, "activity_item_not_found", f"Unknown activity item: {item_id}"
    )


def _activity_item_error(
    status_code: int,
    code: str,
    message: str,
    item: dict[str, Any] | None,
    etag: str,
) -> JSONResponse:
    """409/412 body carrying the current item plus a fresh ETag header."""
    body = ActivityItemErrorResponse(
        code=code,
        message=message,
        item=ActivityItemModel(**item) if item is not None else None,
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(),
        headers={"ETag": etag},
    )


@router.get(
    "/profiles/{name}/activity/{item_id}",
    response_model=ActivityItemModel,
    responses=ERROR_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def get_profile_activity_item(
    name: str, item_id: str, response: Response
) -> ActivityItemModel:
    """One full Agent Activity item by id (404 when missing).

    The response carries the activity-file ETag (see module docstring) for
    use as ``If-Match`` on the apply/dismiss mutations.
    """
    pdir = _resolve_profile(name)
    item = _find_activity_item(pdir, item_id)
    response.headers["ETag"] = _activity_etag(pdir)
    return ActivityItemModel(**item)


@router.post(
    "/profiles/{name}/activity/{item_id}/apply",
    response_model=ActivityApplyResponse,
    responses=MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def apply_profile_activity_item(
    name: str,
    item_id: str,
    response: Response,
    if_match: str | None = Header(default=None),
) -> ActivityApplyResponse | JSONResponse:
    """Apply one pending Review-origin activity item.

    Outcome mapping: success → 200 ``{"ok": true, item}``; item not
    pending → 409 with the current item; item not appliable (non-Review
    origin, unknown candidate type) → 409; applier failure → 409 with the
    item now in ``failed`` status and the error message. Honors
    ``If-Match`` (412 on mismatch, current item in the body).
    """
    pdir = _resolve_profile(name)
    item = _find_activity_item(pdir, item_id)
    etag = _activity_etag(pdir)
    if not _if_match_satisfied(if_match, etag):
        return _activity_item_error(
            412,
            "etag_mismatch",
            "agent-activity.yaml changed since this item was loaded; "
            "reload before applying.",
            item,
            etag,
        )
    if str(item.get("status") or "").strip() != "pending":
        return _activity_item_error(
            409,
            "activity_item_not_pending",
            f"Activity item {item_id} is not pending "
            f"(status: {item.get('status')}).",
            item,
            etag,
        )
    try:
        result = apply_review_activity_item(
            pdir.name,
            item_id,
            activity_snapshot=file_state.snapshot_file(
                pdir / agent_activity.AGENT_ACTIVITY_FILENAME
            ),
        )
    except KeyError as exc:
        raise ApiError(
            404, "activity_item_not_found", f"Unknown activity item: {item_id}"
        ) from exc
    except file_state.FileConflictError:
        # A concurrent write landed between the If-Match check above and
        # the core saver's in-lock snapshot re-check (TOCTOU closure).
        return _activity_item_error(
            412,
            "etag_mismatch",
            "agent-activity.yaml changed while applying; "
            "reload before retrying.",
            item,
            _activity_etag(pdir),
        )
    except ValueError as exc:
        return _activity_item_error(
            409, "activity_item_not_appliable", str(exc), item, etag
        )
    stored = result.activity_item or item
    new_etag = _activity_etag(pdir)
    if not result.ok:
        return _activity_item_error(
            409,
            "activity_apply_failed",
            "; ".join(result.errors) or "Apply failed.",
            stored,
            new_etag,
        )
    response.headers["ETag"] = new_etag
    return ActivityApplyResponse(
        ok=True,
        item=ActivityItemModel(**stored),
        warnings=list(result.warnings),
        changed_paths=[str(path) for path in result.changed_paths],
    )


@router.post(
    "/profiles/{name}/activity/{item_id}/dismiss",
    response_model=ActivityDismissResponse,
    responses=MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def dismiss_profile_activity_item(
    name: str,
    item_id: str,
    response: Response,
    body: ActivityDismissRequest | None = None,
    if_match: str | None = Header(default=None),
) -> ActivityDismissResponse | JSONResponse:
    """Dismiss one pending or failed activity item (``note`` optional).

    Pending and failed items are dismissable; applied/dismissed/superseded
    items answer 409 with the current item. Honors ``If-Match`` (412 on
    mismatch, current item in the body).
    """
    pdir = _resolve_profile(name)
    item = _find_activity_item(pdir, item_id)
    etag = _activity_etag(pdir)
    if not _if_match_satisfied(if_match, etag):
        return _activity_item_error(
            412,
            "etag_mismatch",
            "agent-activity.yaml changed since this item was loaded; "
            "reload before dismissing.",
            item,
            etag,
        )
    status = str(item.get("status") or "").strip()
    if status not in ("pending", "failed"):
        return _activity_item_error(
            409,
            "activity_item_not_dismissable",
            f"Activity item {item_id} cannot be dismissed "
            f"(status: {status}).",
            item,
            etag,
        )
    note = (body.note or "").strip() if body is not None else ""
    try:
        stored = agent_activity.update_activity_status(
            pdir.name,
            item_id,
            "dismissed",
            extra={"dismiss_note": note} if note else None,
            expected_snapshot=file_state.snapshot_file(
                pdir / agent_activity.AGENT_ACTIVITY_FILENAME
            ),
        )
    except KeyError as exc:
        raise ApiError(
            404, "activity_item_not_found", f"Unknown activity item: {item_id}"
        ) from exc
    except file_state.FileConflictError:
        return _activity_item_error(
            412,
            "etag_mismatch",
            "agent-activity.yaml changed while dismissing; "
            "reload before retrying.",
            item,
            _activity_etag(pdir),
        )
    response.headers["ETag"] = _activity_etag(pdir)
    return ActivityDismissResponse(ok=True, item=ActivityItemModel(**stored))


def _kanban_etag(pdir: Path) -> str:
    """Weak ETag for the profile's kanban.md (sha256 fingerprint).

    Same contract as ``_activity_etag``: weak because the hash identifies
    the source markdown file version, not the JSON response bytes.
    """
    snapshot = file_state.snapshot_file(kanban_path(pdir))
    return f'W/"{snapshot.sha256 or "empty"}"'


def _kanban_task_model(task: KanbanTask) -> KanbanTaskModel:
    """Convert one core kanban task to the API model."""
    return KanbanTaskModel(
        title=task.title,
        done=task.done,
        id=task.id,
        context=task.context,
        why=task.why,
        blocked_by=task.blocked_by,
        outcome=task.outcome,
        started_on=task.started_on,
        completed_on=task.completed_on,
        crystallized=task.crystallized,
        project_id=task.project_id,
        milestone_id=task.milestone_id,
        agent_task_id=task.agent_task_id,
        tags=task.tags,
        subtasks=[
            KanbanSubtaskModel(title=st.title, done=st.done)
            for st in task.subtasks
        ],
        details=list(task.details),
    )


@router.get(
    "/profiles/{name}/kanban",
    response_model=KanbanBoardResponse,
    responses=ERROR_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def get_profile_kanban(name: str, response: Response) -> KanbanBoardResponse:
    """Parsed kanban board (sections + card fields; no markdown body).

    The response carries the kanban.md ETag (see module docstring) for use
    as ``If-Match`` on the card mutations.
    """
    pdir = _resolve_profile(name)
    sections = parse_kanban(pdir)
    ordered = list(KANBAN_SECTIONS)
    ordered.extend(s for s in sections if s not in KANBAN_SECTIONS)
    out: list[KanbanSectionModel] = []
    total = 0
    for section in ordered:
        tasks = [
            _kanban_task_model(task) for task in sections.get(section, [])
        ]
        total += len(tasks)
        out.append(KanbanSectionModel(name=section, tasks=tasks))
    response.headers["ETag"] = _kanban_etag(pdir)
    return KanbanBoardResponse(profile=pdir.name, sections=out, total=total)


KANBAN_MUTATION_RESPONSES = {
    **ERROR_RESPONSES,
    404: {
        "model": ErrorResponse,
        "description": "Profile or kanban card not found.",
    },
    412: {
        "model": ErrorResponse,
        "description": "If-Match ETag does not match the current kanban file.",
    },
    422: {
        "model": ErrorResponse,
        "description": "Blank title, unknown section, or ambiguous card_ref.",
    },
}


def _kanban_error(
    status_code: int,
    code: str,
    message: str,
    etag: str,
) -> JSONResponse:
    """4xx body plus a fresh kanban ETag header for client reloads."""
    body = ErrorResponse(code=code, message=message)
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(),
        headers={"ETag": etag},
    )


def _unknown_kanban_section(raw: str) -> ApiError:
    """422 for a section name that does not map to a board column."""
    return ApiError(
        422,
        "unknown_kanban_section",
        f"Unknown kanban section {raw.strip()!r} "
        f"(expected one of: {', '.join(KANBAN_SECTIONS)}).",
    )


def _merge_notices(result) -> list[str]:
    """Human-readable notices for a kanban save that merged external edits."""
    notices: list[str] = []
    if result.merged_external:
        notices.append(
            "kanban.md changed concurrently; external edits were merged in."
        )
    for change in result.dropped_changes:
        notices.append(
            f"Change to {change.label!r} was dropped: the card no longer "
            "exists on disk."
        )
    return notices


def _find_card_by_id(
    sections: dict[str, list[KanbanTask]],
    task_id: str,
) -> tuple[str, KanbanTask]:
    """Locate a persisted card by id across all sections."""
    for section, tasks in sections.items():
        for task in tasks:
            if task.id == task_id:
                return section, task
    raise ApiError(
        409,
        "kanban_card_lost_in_merge",
        "The card disappeared while merging a concurrent kanban.md edit; "
        "reload the board.",
    )


def _save_kanban_mutation(
    pdir: Path,
    sections: dict[str, list[KanbanTask]],
    base: dict[str, list[KanbanTask]],
    snapshot: file_state.FileSnapshot,
):
    """Persist a kanban mutation with 3-way merge conflict handling.

    *snapshot* is the kanban.md fingerprint taken at request start; when
    the file changed between parse and save, the caller's delta
    (*base* → *sections*) is replayed onto the latest disk state instead
    of overwriting it, and the merge outcome rides back on the response.
    """
    ensured = ensure_kanban_task_ids(sections, pdir.name)
    return save_kanban_with_merge(
        pdir,
        ensured,
        copy_kanban_sections(base),
        expected_snapshot=snapshot,
    )


@router.post(
    "/profiles/{name}/kanban/cards",
    response_model=KanbanMutationResponse,
    status_code=201,
    responses=KANBAN_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def add_profile_kanban_card(
    name: str,
    body: KanbanCardCreateRequest,
    response: Response,
    if_match: str | None = Header(default=None),
) -> KanbanMutationResponse | JSONResponse:
    """Quick-add one card (only ``title`` is required; default Queue).

    Follows the board's column-date idiom: cards added to Doing get
    ``started_on``, cards added to Done get ``done`` + ``completed_on``.
    Honors ``If-Match`` (412 on mismatch); a concurrent write between
    parse and save is 3-way merged, reported via ``merged_external`` /
    ``merge_notices`` instead of failing.
    """
    pdir = _resolve_profile(name)
    title = body.title.strip()
    if not title:
        raise ApiError(
            422, "invalid_kanban_card", "Card title must not be blank."
        )
    target = resolve_kanban_section(body.section)
    if target is None:
        raise _unknown_kanban_section(body.section)
    etag = _kanban_etag(pdir)
    if not _if_match_satisfied(if_match, etag):
        return _kanban_error(
            412,
            "etag_mismatch",
            "kanban.md changed since it was loaded; reload before adding.",
            etag,
        )
    snapshot = file_state.snapshot_file(kanban_path(pdir))
    sections = parse_kanban(pdir)
    base = copy_kanban_sections(sections)
    tags = ", ".join(tag.strip() for tag in body.tags if tag.strip())
    task = KanbanTask(title=title, context=body.context.strip(), tags=tags)
    today = date.today().isoformat()
    if target == KANBAN_DONE:
        task = replace(task, done=True, completed_on=today)
    elif target == KANBAN_DOING:
        task = replace(task, started_on=today)
    sections.setdefault(target, []).append(task)
    ensured = ensure_kanban_task_ids(sections, pdir.name)
    created_id = ensured[target][-1].id
    result = _save_kanban_mutation(pdir, ensured, base, snapshot)
    section, stored = _find_card_by_id(result.sections, created_id)
    response.headers["ETag"] = _kanban_etag(pdir)
    return KanbanMutationResponse(
        ok=True,
        card=_kanban_task_model(stored),
        section=section,
        merged_external=result.merged_external,
        merge_notices=_merge_notices(result),
    )


def _mutate_kanban_card_section(
    name: str,
    card_ref: str,
    target: str,
    response: Response,
    if_match: str | None,
) -> KanbanMutationResponse | JSONResponse:
    """Shared move/done mutation: relocate one card to *target*.

    ``card_ref`` is an exact title or unique substring (same semantics as
    the Review kanban-move candidate). The move reuses
    ``apply_kanban_reorder(auto_dates=True)``, so landing in Done marks the
    card done with ``completed_on`` and leaving Done clears both.
    """
    pdir = _resolve_profile(name)
    etag = _kanban_etag(pdir)
    if not _if_match_satisfied(if_match, etag):
        return _kanban_error(
            412,
            "etag_mismatch",
            "kanban.md changed since it was loaded; reload before mutating.",
            etag,
        )
    snapshot = file_state.snapshot_file(kanban_path(pdir))
    sections = parse_kanban(pdir)
    base = copy_kanban_sections(sections)
    ref = card_ref.strip()
    hit, match_kind, match_error = find_kanban_card(sections, ref)
    if hit is None:
        if match_kind == "ambiguous":
            raise ApiError(422, "kanban_card_ambiguous", match_error)
        raise ApiError(404, "kanban_card_not_found", match_error)
    from_section, _index, task = hit
    warnings: list[str] = []
    if from_section == target:
        warnings.append(
            f"card {task.title.strip()!r} is already in {target!r}; "
            "no move needed"
        )
        moved = sections
    else:
        moved = apply_kanban_reorder(
            sections,
            [{"id": task.id, "to_section": target}],
            auto_dates=True,
        )
    result = _save_kanban_mutation(pdir, moved, base, snapshot)
    section, stored = _find_card_by_id(result.sections, task.id)
    response.headers["ETag"] = _kanban_etag(pdir)
    return KanbanMutationResponse(
        ok=True,
        card=_kanban_task_model(stored),
        section=section,
        warnings=warnings,
        merged_external=result.merged_external,
        merge_notices=_merge_notices(result),
    )


@router.post(
    "/profiles/{name}/kanban/cards/{card_ref}/move",
    response_model=KanbanMutationResponse,
    responses=KANBAN_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def move_profile_kanban_card(
    name: str,
    card_ref: str,
    body: KanbanCardMoveRequest,
    response: Response,
    if_match: str | None = Header(default=None),
) -> KanbanMutationResponse | JSONResponse:
    """Move one card to ``target_section``. Honors ``If-Match`` (412)."""
    target = resolve_kanban_section(body.target_section)
    if target is None:
        raise _unknown_kanban_section(body.target_section)
    return _mutate_kanban_card_section(name, card_ref, target, response, if_match)


@router.post(
    "/profiles/{name}/kanban/cards/{card_ref}/done",
    response_model=KanbanMutationResponse,
    responses=KANBAN_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def done_profile_kanban_card(
    name: str,
    card_ref: str,
    response: Response,
    if_match: str | None = Header(default=None),
) -> KanbanMutationResponse | JSONResponse:
    """Mark one card done by moving it to Done (done flag + completed_on).

    The Done transition is the board's column-move idiom
    (``apply_kanban_reorder`` with ``auto_dates``), so a card already in
    Done answers 200 with an "already there" warning. Honors ``If-Match``.
    """
    return _mutate_kanban_card_section(
        name, card_ref, KANBAN_DONE, response, if_match
    )


@router.get(
    "/profiles/{name}/inbox",
    response_model=InboxResponse,
    responses=ERROR_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def get_profile_inbox(
    name: str,
    response: Response,
    status: str = Query("inbox,captured,clarified"),
) -> InboxResponse:
    """Inbox items; defaults to open statuses, ``status=`` overrides.

    ``status`` accepts a comma-separated list (``all`` disables filtering).
    The response carries the inbox-source ETag (inbox.yaml plus the clarify
    dispatch targets kanban.md / learning-log.yaml / activity-log.yaml) for
    use as ``If-Match`` on the capture/clarify/archive/discard mutations.
    """
    pdir = _resolve_profile(name)
    loaded = inbox.load_inbox(pdir)
    wanted = [s.strip() for s in status.split(",") if s.strip()]
    if any(s == "all" for s in wanted):
        wanted = []
    items = [
        item for item in loaded.items if not wanted or item.status in wanted
    ]
    response.headers["ETag"] = _inbox_etag(pdir)
    return InboxResponse(
        profile=pdir.name,
        statuses=wanted,
        total=len(items),
        items=[_inbox_item_model(item) for item in items],
    )


INBOX_MUTATION_RESPONSES = {
    **ERROR_RESPONSES,
    412: {
        "model": InboxItemErrorResponse,
        "description": "If-Match ETag does not match the current inbox file.",
    },
    422: {
        "model": ErrorResponse,
        "description": "Blank title or unsupported clarify action.",
    },
}


def _inbox_etag(pdir: Path) -> str:
    """Weak ETag over the inbox mutation's source files (sha256 fingerprint).

    Covers inbox.yaml plus every file the clarify dispatch can write
    (kanban.md / learning-log.yaml / activity-log.yaml), so a client
    holding this ETag detects concurrent edits to any clarify target
    (M-API-4 closure). Weak (``W/``) because the hash identifies the
    source file versions, not the JSON response bytes.
    """
    fingerprints = []
    for relative in (
        inbox.INBOX_FILENAME,
        kanban_path(pdir).name,
        learning_log.LEARNING_LOG_FILENAME,
        activity_log.ACTIVITY_LOG_FILENAME,
    ):
        snapshot = file_state.snapshot_file(pdir / relative)
        fingerprints.append(f"{relative}:{snapshot.sha256 or 'empty'}")
    digest = hashlib.sha256("|".join(fingerprints).encode("utf-8")).hexdigest()
    return f'W/"{digest}"'


def _inbox_mutation_snapshots(pdir: Path) -> dict[str, file_state.FileSnapshot]:
    """Request-start fingerprints for the clarify dispatch target files."""
    return {
        "inbox": file_state.snapshot_file(pdir / inbox.INBOX_FILENAME),
        "kanban": file_state.snapshot_file(kanban_path(pdir)),
        "learning_log": file_state.snapshot_file(
            pdir / learning_log.LEARNING_LOG_FILENAME
        ),
        "activity_log": file_state.snapshot_file(
            pdir / activity_log.ACTIVITY_LOG_FILENAME
        ),
    }


def _inbox_item_model(item: inbox.InboxItem) -> InboxItemModel:
    """Convert one core inbox item to the API model."""
    return InboxItemModel(
        id=item.id,
        title=item.title,
        type=item.type,
        source=item.source,
        created_at=item.created_at,
        captured_by=item.captured_by,
        raw_text=item.raw_text,
        tags=list(item.tags),
        visibility=item.visibility,
        status=item.status,
        metadata=dict(item.metadata),
        history=[
            {
                "at": event.at,
                "action": event.action,
                "from_status": event.from_status,
                "to_status": event.to_status,
                "note": event.note,
                "metadata": dict(event.metadata),
            }
            for event in item.history
        ],
    )


def _find_inbox_item_model(pdir: Path, item_id: str) -> InboxItemModel:
    """Return one inbox item as an API model or raise ApiError(404)."""
    clean_id = item_id.strip()
    for item in inbox.load_inbox(pdir).items:
        if item.id == clean_id:
            return _inbox_item_model(item)
    raise ApiError(
        404, "inbox_item_not_found", f"Unknown inbox item: {item_id}"
    )


def _inbox_item_error(
    status_code: int,
    code: str,
    message: str,
    item: InboxItemModel | None,
    etag: str,
) -> JSONResponse:
    """4xx body carrying the current inbox item plus a fresh ETag header."""
    body = InboxItemErrorResponse(code=code, message=message, item=item)
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(),
        headers={"ETag": etag},
    )


@router.post(
    "/profiles/{name}/inbox",
    response_model=InboxMutationResponse,
    status_code=201,
    responses=INBOX_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def capture_profile_inbox_item(
    name: str,
    body: InboxCaptureRequest,
    response: Response,
    if_match: str | None = Header(default=None),
) -> InboxMutationResponse | JSONResponse:
    """Quick-capture one inbox item (only ``title`` is required).

    ``source`` defaults to ``web`` and lands on the item's ``source``
    field; ``captured_by`` is derived as ``human-<source>`` so web captures
    stay distinguishable from agent captures (MCP uses ``openclaw``).
    Honors ``If-Match`` (412 on mismatch).
    """
    pdir = _resolve_profile(name)
    etag = _inbox_etag(pdir)
    if not _if_match_satisfied(if_match, etag):
        return _inbox_item_error(
            412,
            "etag_mismatch",
            "inbox.yaml changed since it was loaded; reload before capturing.",
            None,
            etag,
        )
    source = body.source.strip() or "web"
    captured_by = f"human-{source}"
    try:
        item = inbox.update_inbox(
            pdir,
            lambda doc: inbox.add_inbox_item(
                doc,
                body.title,
                source=source,
                captured_by=captured_by,
                raw_text=body.raw_text,
                tags=body.tags,
            ),
            expected_snapshot=file_state.snapshot_file(
                pdir / inbox.INBOX_FILENAME
            ),
        )
    except ValueError as exc:
        raise ApiError(422, "invalid_inbox_capture", str(exc)) from exc
    except file_state.FileConflictError:
        return _inbox_item_error(
            412,
            "etag_mismatch",
            "inbox.yaml changed while capturing; reload before retrying.",
            None,
            _inbox_etag(pdir),
        )
    response.headers["ETag"] = _inbox_etag(pdir)
    return InboxMutationResponse(ok=True, item=_inbox_item_model(item))


@router.post(
    "/profiles/{name}/inbox/{item_id}/clarify",
    response_model=InboxMutationResponse,
    responses=INBOX_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def clarify_profile_inbox_item(
    name: str,
    item_id: str,
    body: InboxClarifyRequest,
    response: Response,
    if_match: str | None = Header(default=None),
) -> InboxMutationResponse | JSONResponse:
    """Dispatch one clarify action (kanban/learning/habit/evidence/close).

    Unknown actions answer 422, unknown items 404. The dispatch writes to
    kanban.md / learning-log.yaml / activity-log.yaml depending on the
    action; the response ``result`` carries the core dispatch outcome
    (``target_id`` or ``draft``). Honors ``If-Match`` (412 on mismatch,
    current item in the body) — the inbox ETag covers inbox.yaml plus all
    dispatch target files, the kanban write 3-way merges concurrent board
    edits, and the remaining writes re-check their request-start snapshot
    inside the write lock (412 on conflict).
    """
    pdir = _resolve_profile(name)
    if body.action.strip() not in inbox.CLARIFY_ACTIONS:
        raise ApiError(
            422,
            "unsupported_clarify_action",
            f"Unsupported clarify action: {body.action!r}. "
            f"Expected one of: {', '.join(inbox.CLARIFY_ACTIONS)}.",
        )
    current = _find_inbox_item_model(pdir, item_id)
    etag = _inbox_etag(pdir)
    if not _if_match_satisfied(if_match, etag):
        return _inbox_item_error(
            412,
            "etag_mismatch",
            "inbox.yaml changed since this item was loaded; "
            "reload before clarifying.",
            current,
            etag,
        )
    try:
        result = inbox.clarify_inbox_item(
            pdir,
            item_id,
            body.action,
            {"note": body.note},
            expected_snapshots=_inbox_mutation_snapshots(pdir),
        )
    except KeyError as exc:
        raise ApiError(
            404, "inbox_item_not_found", f"Unknown inbox item: {item_id}"
        ) from exc
    except file_state.FileConflictError:
        # A concurrent write to inbox.yaml (or a clarify target file)
        # landed between the If-Match check and the in-lock re-check.
        return _inbox_item_error(
            412,
            "etag_mismatch",
            "Inbox source files changed while clarifying; "
            "reload before retrying.",
            current,
            _inbox_etag(pdir),
        )
    except ValueError as exc:
        raise ApiError(422, "clarify_failed", str(exc)) from exc
    response.headers["ETag"] = _inbox_etag(pdir)
    return InboxMutationResponse(
        ok=True,
        item=_find_inbox_item_model(pdir, item_id),
        result=dict(result),
    )


def _close_profile_inbox_item(
    name: str,
    item_id: str,
    close: str,
    body: InboxNoteRequest | None,
    response: Response,
    if_match: str | None,
) -> InboxMutationResponse | JSONResponse:
    """Shared archive/discard mutation (thin wrappers over core helpers)."""
    pdir = _resolve_profile(name)
    current = _find_inbox_item_model(pdir, item_id)
    etag = _inbox_etag(pdir)
    if not _if_match_satisfied(if_match, etag):
        return _inbox_item_error(
            412,
            "etag_mismatch",
            "inbox.yaml changed since this item was loaded; "
            f"reload before {close}.",
            current,
            etag,
        )
    note = (body.note or "").strip() if body is not None else ""
    fn = (
        inbox.archive_inbox_item if close == "archive"
        else inbox.discard_inbox_item
    )
    try:
        item = inbox.update_inbox(
            pdir,
            lambda doc: fn(doc, item_id, note=note),
            expected_snapshot=file_state.snapshot_file(
                pdir / inbox.INBOX_FILENAME
            ),
        )
    except KeyError as exc:
        raise ApiError(
            404, "inbox_item_not_found", f"Unknown inbox item: {item_id}"
        ) from exc
    except file_state.FileConflictError:
        return _inbox_item_error(
            412,
            "etag_mismatch",
            f"inbox.yaml changed while processing {close}; "
            "reload before retrying.",
            current,
            _inbox_etag(pdir),
        )
    response.headers["ETag"] = _inbox_etag(pdir)
    return InboxMutationResponse(ok=True, item=_inbox_item_model(item))


@router.post(
    "/profiles/{name}/inbox/{item_id}/archive",
    response_model=InboxMutationResponse,
    responses=INBOX_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def archive_profile_inbox_item(
    name: str,
    item_id: str,
    response: Response,
    body: InboxNoteRequest | None = None,
    if_match: str | None = Header(default=None),
) -> InboxMutationResponse | JSONResponse:
    """Archive one inbox item (``note`` optional). Honors ``If-Match``."""
    return _close_profile_inbox_item(
        name, item_id, "archive", body, response, if_match
    )


@router.post(
    "/profiles/{name}/inbox/{item_id}/discard",
    response_model=InboxMutationResponse,
    responses=INBOX_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def discard_profile_inbox_item(
    name: str,
    item_id: str,
    response: Response,
    body: InboxNoteRequest | None = None,
    if_match: str | None = Header(default=None),
) -> InboxMutationResponse | JSONResponse:
    """Discard one inbox item (``note`` optional). Honors ``If-Match``."""
    return _close_profile_inbox_item(
        name, item_id, "discard", body, response, if_match
    )


@router.get(
    "/profiles/{name}/agent-tasks",
    response_model=AgentTaskListResponse,
    responses=ERROR_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def get_profile_agent_tasks(
    name: str,
    status: str = Query(""),
) -> AgentTaskListResponse:
    """External agent handoff tasks; ``status=`` filters (empty = all)."""
    pdir = _resolve_profile(name)
    tasks = agent_tasks.load_agent_tasks(pdir).get("tasks") or []
    clean_status = status.strip()
    if clean_status and clean_status != "all":
        tasks = [
            task
            for task in tasks
            if str(task.get("status") or "").strip() == clean_status
        ]
    return AgentTaskListResponse(
        profile=pdir.name,
        status=clean_status,
        total=len(tasks),
        tasks=[AgentTaskModel(**task) for task in tasks],
    )


@router.get(
    "/profiles/{name}/goals",
    response_model=GoalsResponse,
    responses=ERROR_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def get_profile_goals(name: str) -> GoalsResponse:
    """The goal book as the human owner sees it — full detail, no redaction.

    This API serves the authenticated owner's UI, so private/discreet goals
    and the North Star are returned in full. The agent-facing privacy
    projections (``goal_for_agent_context`` / ``goal_for_ui`` /
    ``north_star_context_from_identity``) stay where agents consume them:
    ``nblane.core.context`` and ``nblane.mcp_server``.
    """
    pdir = _resolve_profile(name)
    book = load_goal_book(pdir)
    identity = parse_identity_fields(profile_io.load_skill_md(pdir.name))
    full = str(identity.get("North Star", "") or "").strip()
    brief = str(identity.get("North Star Brief", "") or "").strip()
    north_star = NorthStarModel(
        visibility=normalize_north_star_visibility(
            identity.get("North Star Visibility")
        ),
        is_set=bool(full or brief),
        full=full,
        brief=brief,
    )
    return GoalsResponse(
        profile=pdir.name,
        current_goal_id=book.current_goal_id,
        north_star=north_star,
        goals=[GoalModel(**goal.to_dict()) for goal in book.goals],
    )


def _evidence_review_status(record: EvidenceRecord) -> str:
    """Normalized review status; empty/unknown means not yet reviewed."""
    raw = record.review_status.strip()
    return raw if raw in EVIDENCE_REVIEW_STATUSES else "needs_review"


def _evidence_item(record: EvidenceRecord) -> EvidenceEntryModel:
    """List-view projection of one pool record."""
    return EvidenceEntryModel(
        id=record.id,
        title=record.title,
        evidence_type=record.type,
        review_status=_evidence_review_status(record),
        date=record.date,
        url=record.url,
        summary=record.summary,
        source_refs=list(record.source_refs),
    )


def _evidence_detail(record: EvidenceRecord) -> EvidenceEntryDetailModel:
    """Full detail projection of one pool record."""
    item = _evidence_item(record)
    return EvidenceEntryDetailModel(
        **item.model_dump(),
        strength=record.strength,
        confidence=record.confidence,
        public_readiness=record.public_readiness,
        project_refs=list(record.project_refs),
        experience_refs=list(record.experience_refs),
        kanban_refs=list(record.kanban_refs),
        source_excerpt=record.source_excerpt,
        origin=record.origin,
        origin_ref=record.origin_ref,
        origin_detail=record.origin_detail,
        original_content=record.original_content,
        formatted_content=record.formatted_content,
        language=record.language,
        original_language=record.original_language,
        original_content_hash=record.original_content_hash,
        source_content_hash=record.source_content_hash,
        deprecated=record.deprecated,
        replaced_by=record.replaced_by,
    )


@router.get(
    "/profiles/{name}/evidence",
    response_model=EvidenceListResponse,
    responses=ERROR_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def list_profile_evidence(
    name: str,
    status: str = Query(
        "",
        description=(
            "Review-status filter. Empty (default) returns all non-deprecated "
            "entries; 'all' includes deprecated; 'deprecated' returns only "
            "deprecated; any other value matches the review_status exactly."
        ),
    ),
    q: str = Query("", description="Case-insensitive title substring filter."),
    limit: int = Query(100, ge=1, le=500),
) -> EvidenceListResponse:
    """Filtered evidence-pool entries (read-only list for the SPA)."""
    pdir = _resolve_profile(name)
    pool = profile_io.load_evidence_pool(pdir)
    entries = list(pool.evidence_entries) if pool else []

    clean_status = status.strip().lower()
    if clean_status == "deprecated":
        entries = [record for record in entries if record.deprecated]
    elif clean_status == "all":
        pass
    elif clean_status:
        entries = [
            record
            for record in entries
            if not record.deprecated
            and _evidence_review_status(record) == clean_status
        ]
    else:
        entries = [record for record in entries if not record.deprecated]

    query = q.strip().lower()
    if query:
        entries = [record for record in entries if query in record.title.lower()]

    return EvidenceListResponse(
        profile=pdir.name,
        status=clean_status,
        q=q.strip(),
        limit=limit,
        total=len(entries),
        items=[_evidence_item(record) for record in entries[:limit]],
    )


@router.get(
    "/profiles/{name}/evidence/{entry_id}",
    response_model=EvidenceEntryDetailModel,
    responses=ERROR_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def get_profile_evidence_entry(name: str, entry_id: str) -> EvidenceEntryDetailModel:
    """Full detail for one evidence-pool entry; 404 when the id is unknown."""
    pdir = _resolve_profile(name)
    pool = profile_io.load_evidence_pool(pdir)
    record = pool.by_id().get(entry_id) if pool else None
    if record is None:
        raise ApiError(
            404,
            "evidence_not_found",
            f"Unknown evidence entry: {entry_id}",
        )
    return _evidence_detail(record)


# --- Evidence Review (M3): triage queue + bulk accept/reject/tag ------------


def _evidence_pool_etag(pdir: Path) -> str:
    """Weak ETag for the profile's evidence-pool.yaml (sha256 fingerprint).

    Same contract as ``_activity_etag``: weak because the hash identifies
    the source YAML file version, not the JSON response bytes.
    """
    snapshot = file_state.snapshot_file(pdir / profile_io.EVIDENCE_POOL_FILENAME)
    return f'W/"{snapshot.sha256 or "empty"}"'


def _review_item_model(
    row: dict[str, Any],
    usage: dict[str, list[dict[str, str]]],
) -> EvidenceReviewItemModel:
    """Triage-view projection of one raw pool row."""
    eid = str(row.get("id", "") or "").strip()
    used_by = usage.get(eid) or []
    return EvidenceReviewItemModel(
        id=eid,
        title=str(row.get("title", "") or ""),
        evidence_type=str(row.get("type", "") or "practice"),
        date=str(row.get("date", "") or ""),
        url=str(row.get("url", "") or ""),
        review_status=evidence_review_core.normalize_review_status(
            row.get("review_status")
        ),
        strength=evidence_review_core.normalize_evidence_strength(
            row.get("strength")
        ),
        confidence=evidence_review_core.normalize_evidence_confidence(
            row.get("confidence")
        ),
        public_readiness=evidence_review_core.normalize_public_readiness(
            row.get("public_readiness")
        ),
        deprecated=bool(row.get("deprecated", False)),
        usage_count=len(used_by),
        skill_refs=[str(item.get("id", "")) for item in used_by],
        review_reason=evidence_review_core.review_reason_for_row(row),
    )


EVIDENCE_REVIEW_MUTATION_RESPONSES = {
    **ERROR_RESPONSES,
    412: {
        "model": ErrorResponse,
        "description": "If-Match ETag does not match the current pool file.",
    },
    422: {
        "model": ErrorResponse,
        "description": "Unknown bulk field or out-of-domain bulk value.",
    },
}


def _evidence_review_error(
    status_code: int,
    code: str,
    message: str,
    etag: str,
) -> JSONResponse:
    """4xx body plus a fresh pool ETag header for client reloads."""
    body = ErrorResponse(code=code, message=message)
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(),
        headers={"ETag": etag},
    )


@router.get(
    "/profiles/{name}/evidence-review",
    response_model=EvidenceReviewListResponse,
    responses=ERROR_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def get_profile_evidence_review(
    name: str,
    response: Response,
    status: str = Query(
        "needs_review",
        description=(
            "Review-status filter. 'needs_review' (default) returns active rows "
            "whose review_status is not reviewed; 'reviewed' returns reviewed "
            "active rows; 'all' returns every row including deprecated; "
            "'deprecated' returns only deprecated rows."
        ),
    ),
    q: str = Query("", description="Case-insensitive id/title substring filter."),
    limit: int = Query(200, ge=1, le=500),
) -> EvidenceReviewListResponse:
    """Evidence Review triage queue plus queue-wide summary counters.

    The response carries the evidence-pool.yaml ETag (see module docstring)
    for use as ``If-Match`` on the bulk/deprecate mutations.
    """
    pdir = _resolve_profile(name)
    raw = profile_io.load_evidence_pool_raw(pdir) or {}
    rows = [
        row
        for row in (raw.get("evidence_entries") or [])
        if isinstance(row, dict) and str(row.get("id", "") or "").strip()
    ]
    usage = evidence_review_core.evidence_usage_index(pdir)
    items = [_review_item_model(row, usage) for row in rows]

    active = [item for item in items if not item.deprecated]
    summary = EvidenceReviewSummaryModel(
        needs_review_count=sum(
            1 for item in active if item.review_status != "reviewed"
        ),
        unlinked_count=sum(1 for item in active if item.usage_count == 0),
        total_entries=len(active),
        deprecated_count=len(items) - len(active),
    )

    clean_status = status.strip().lower()
    if clean_status == "all":
        filtered = items
    elif clean_status == "deprecated":
        filtered = [item for item in items if item.deprecated]
    elif clean_status == "reviewed":
        filtered = [
            item
            for item in items
            if not item.deprecated and item.review_status == "reviewed"
        ]
    else:
        clean_status = "needs_review"
        filtered = [
            item
            for item in items
            if not item.deprecated and item.review_status != "reviewed"
        ]

    query = q.strip().lower()
    if query:
        filtered = [
            item
            for item in filtered
            if query in item.id.lower() or query in item.title.lower()
        ]

    response.headers["ETag"] = _evidence_pool_etag(pdir)
    return EvidenceReviewListResponse(
        profile=pdir.name,
        status=clean_status,
        q=q.strip(),
        limit=limit,
        total=len(filtered),
        items=filtered[:limit],
        summary=summary,
    )


def _mutate_evidence_pool(
    name: str,
    if_match: str | None,
    mutate: Any,
) -> tuple[Path, int, list[str]] | JSONResponse:
    """Shared review-mutation flow: ETag check, apply, save.

    *mutate* receives the raw ``evidence_entries`` list and returns
    ``(changed, missing)``. The load → mutate → write cycle runs inside
    the evidence-pool write lock (``update_evidence_pool``) with the
    request-start snapshot re-checked in-lock, so a concurrent write
    landing between the If-Match check and the lock raises
    ``FileConflictError`` (mapped to 412 by the callers) instead of being
    silently overwritten. Returns the mutation outcome, or a JSONResponse
    when the If-Match precondition fails (412, fresh ETag in the header).
    """
    pdir = _resolve_profile(name)
    etag = _evidence_pool_etag(pdir)
    if not _if_match_satisfied(if_match, etag):
        return _evidence_review_error(
            412,
            "etag_mismatch",
            "evidence-pool.yaml changed since it was loaded; "
            "reload before mutating.",
            etag,
        )
    outcome: dict[str, Any] = {"changed": 0, "missing": []}

    def _apply(raw: dict[str, Any]) -> None:
        entries = [
            row
            for row in (raw.get("evidence_entries") or [])
            if isinstance(row, dict)
        ]
        changed, missing = mutate(entries)
        outcome["changed"] = changed
        outcome["missing"] = missing
        if changed:
            raw["evidence_entries"] = entries
            raw["profile"] = pdir.name

    try:
        profile_io.update_evidence_pool(
            pdir.name,
            _apply,
            expected_snapshot=file_state.snapshot_file(
                pdir / profile_io.EVIDENCE_POOL_FILENAME
            ),
        )
    except file_state.FileConflictError:
        # A concurrent write landed between the If-Match check and the
        # in-lock snapshot re-check (TOCTOU closure).
        return _evidence_review_error(
            412,
            "etag_mismatch",
            "evidence-pool.yaml changed while mutating; "
            "reload before retrying.",
            _evidence_pool_etag(pdir),
        )
    if outcome["changed"] and (pdir / "SKILL.md").exists():
        write_generated_blocks(pdir)
    return pdir, outcome["changed"], outcome["missing"]


@router.post(
    "/profiles/{name}/evidence-review/bulk",
    response_model=EvidenceReviewMutationResponse,
    responses=EVIDENCE_REVIEW_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def bulk_profile_evidence_review(
    name: str,
    body: EvidenceReviewBulkRequest,
    response: Response,
    if_match: str | None = Header(default=None),
) -> EvidenceReviewMutationResponse | JSONResponse:
    """Set one editable field on many pool rows (accept / tag in one call).

    ``field`` is restricted to the core pool-editable whitelist; ``value``
    must be in that field's domain ("" clears). Honors ``If-Match`` (412 on
    mismatch, fresh ETag in the header). Rows already in the target state
    are not counted as changed.
    """
    field = body.field.strip()
    allowed = evidence_review_core.POOL_EDITABLE_FIELDS.get(field)
    if allowed is None:
        raise ApiError(
            422,
            "invalid_review_field",
            f"Unknown bulk field {body.field!r} (expected one of: "
            f"{', '.join(evidence_review_core.POOL_EDITABLE_FIELDS)}).",
        )
    value = body.value.strip()
    if value and value not in allowed:
        raise ApiError(
            422,
            "invalid_review_value",
            f"Value {body.value!r} is not valid for {field} "
            f"(expected one of: {', '.join(allowed)}, or empty to clear).",
        )
    ids = [str(item).strip() for item in body.ids if str(item).strip()]
    if not ids:
        raise ApiError(
            422, "empty_selection", "At least one evidence id is required."
        )

    def _apply(entries: list[dict[str, Any]]) -> tuple[int, list[str]]:
        _, changed = evidence_review_core.bulk_set_pool_field(
            entries, ids, field, value
        )
        present = {
            str(row.get("id", "") or "").strip()
            for row in entries
            if str(row.get("id", "") or "").strip()
        }
        return changed, [item for item in ids if item not in present]

    outcome = _mutate_evidence_pool(name, if_match, _apply)
    if isinstance(outcome, JSONResponse):
        return outcome
    pdir, changed, missing = outcome
    response.headers["ETag"] = _evidence_pool_etag(pdir)
    return EvidenceReviewMutationResponse(ok=True, changed=changed, missing=missing)


@router.post(
    "/profiles/{name}/evidence-review/deprecate",
    response_model=EvidenceReviewMutationResponse,
    responses=EVIDENCE_REVIEW_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def deprecate_profile_evidence_review(
    name: str,
    body: EvidenceReviewDeprecateRequest,
    response: Response,
    if_match: str | None = Header(default=None),
) -> EvidenceReviewMutationResponse | JSONResponse:
    """Reject (deprecate) or restore pool rows by id.

    Rejecting a candidate sets ``deprecated: true`` (the pool keeps the row
    for provenance, mirroring the Streamlit deprecate action); ``deprecated:
    false`` restores it. Honors ``If-Match`` (412 on mismatch).
    """
    ids = [str(item).strip() for item in body.ids if str(item).strip()]
    if not ids:
        raise ApiError(
            422, "empty_selection", "At least one evidence id is required."
        )
    target = set(ids)
    wanted = bool(body.deprecated)

    def _apply(entries: list[dict[str, Any]]) -> tuple[int, list[str]]:
        changed = 0
        seen: set[str] = set()
        for row in entries:
            rid = str(row.get("id", "") or "").strip()
            if rid not in target:
                continue
            seen.add(rid)
            if bool(row.get("deprecated", False)) == wanted:
                continue
            if wanted:
                row["deprecated"] = True
            else:
                row.pop("deprecated", None)
            changed += 1
        return changed, [item for item in ids if item not in seen]

    outcome = _mutate_evidence_pool(name, if_match, _apply)
    if isinstance(outcome, JSONResponse):
        return outcome
    pdir, changed, missing = outcome
    response.headers["ETag"] = _evidence_pool_etag(pdir)
    return EvidenceReviewMutationResponse(ok=True, changed=changed, missing=missing)


GAP_RESPONSES = {
    **ERROR_RESPONSES,
    422: {
        "model": ErrorResponse,
        "description": (
            "Empty/unmatched task, missing skill tree or schema, or "
            "use_llm requested before the async-jobs slice."
        ),
    },
}


@router.post(
    "/profiles/{name}/gap/analyze",
    response_model=GapAnalysisResponse,
    responses=GAP_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def analyze_profile_gap(name: str, body: GapAnalyzeRequest) -> GapAnalysisResponse:
    """Synchronous, rule-only gap analysis for a free-text task description.

    Wraps ``core.gap.analyze`` with rule matching only. ``use_llm=true``
    answers 422: the LLM router performs a live blocking provider call and
    persists learned keywords, which belongs to the async-jobs slice.
    Analysis errors (no matching nodes, missing skill tree/schema) also
    surface as 422 with the core error message.
    """
    pdir = _resolve_profile(name)
    if body.use_llm:
        raise ApiError(
            422,
            "gap_llm_not_supported",
            "LLM gap analysis requires the async-jobs slice (not implemented).",
        )
    result = gap.analyze(pdir.name, body.task)
    if result.error:
        raise ApiError(
            422,
            result.error_key or "gap_analysis_failed",
            result.error,
        )
    closure = [GapClosureNodeModel(**node) for node in result.closure]
    coverage = (
        round(1 - len(result.gaps) / len(closure), 4) if closure else 0.0
    )
    return GapAnalysisResponse(
        profile=pdir.name,
        task=result.task,
        top_matches=[GapTopMatchModel(**m) for m in result.top_matches],
        closure=closure,
        gaps=list(result.gaps),
        strong=list(result.strong),
        can_solve=result.can_solve,
        coverage=coverage,
        next_steps=list(result.next_steps),
        roots_from_rule=list(result.roots_from_rule),
        roots_from_llm=list(result.roots_from_llm),
        learned_merged=result.learned_merged,
    )


@router.post(
    "/profiles/{name}/gap/intake",
    response_model=KanbanMutationResponse,
    status_code=201,
    responses=GAP_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def intake_profile_gap(name: str, body: GapIntakeRequest) -> KanbanMutationResponse:
    """Turn one detected gap into a kanban learning task.

    Thin wrapper over ``core.task_intake.create_learning_task`` (kanban
    append + project-board sync). The gap node id is recorded on the card's
    context line so the task stays traceable to the analysis.
    """
    pdir = _resolve_profile(name)
    node_id = body.node_id.strip()
    context = f"Gap analysis node: {node_id}" if node_id else ""
    tags = list(body.tags)
    if node_id and node_id not in tags:
        tags.append(node_id)
    try:
        task = task_intake.create_learning_task(
            pdir.name,
            title=body.title,
            context=context,
            why=body.why,
            tags=tags,
            section=body.section,
        )
    except ValueError as exc:
        raise ApiError(422, "invalid_gap_intake", str(exc)) from exc
    # Echo the section the card actually landed in, not the request value.
    stored_sections = parse_kanban(pdir)
    section = next(
        (name for name, tasks in stored_sections.items() if task in tasks),
        body.section,
    )
    return KanbanMutationResponse(
        ok=True,
        card=_kanban_task_model(task),
        section=section,
    )


# --- Review (M3): weekly review aggregation + candidate save/apply ----------


PUBLIC_LAYER_ETAG_FILES = (
    PUBLIC_PROFILE_FILENAME,
    RESUME_SOURCE_FILENAME,
    PROJECTS_FILENAME,
    OUTPUTS_FILENAME,
    BLOG_TAXONOMY_FILENAME,
    PUBLIC_LIBRARY_FILENAME,
)


def _public_layer_fingerprints(pdir: Path) -> list[str]:
    """Fingerprint lines for the public-layer YAML files + blog documents."""
    fingerprints = []
    for relative in PUBLIC_LAYER_ETAG_FILES:
        snapshot = file_state.snapshot_file(pdir / relative)
        fingerprints.append(f"{relative}:{snapshot.sha256 or 'empty'}")
    blog_dir = pdir / BLOG_DIRNAME
    if blog_dir.exists():
        for path in sorted(blog_dir.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix not in (".md", ".json"):
                continue
            snapshot = file_state.snapshot_file(path)
            rel = path.relative_to(pdir).as_posix()
            fingerprints.append(f"{rel}:{snapshot.sha256 or 'empty'}")
    return fingerprints


def _review_etag(pdir: Path) -> str:
    """Weak ETag over the review's source files (sha256 fingerprint).

    The review GET aggregates kanban.md plus the optional activity/learning/
    inbox logs; the save mutation writes agent-activity.yaml; the apply
    mutation additionally writes evidence-pool.yaml and (for public_draft
    candidates) the public layer's blog drafts. The ETag therefore covers
    all of them — the five aggregation files, agent-activity.yaml, and the
    public-layer fingerprint (same file set as the studio ETag). Weak
    (``W/``) because the hash identifies the source file versions, not the
    JSON response bytes.
    """
    fingerprints = []
    for filename in (
        kanban_path(pdir).name,
        learning_log.LEARNING_LOG_FILENAME,
        activity_log.ACTIVITY_LOG_FILENAME,
        inbox.INBOX_FILENAME,
        profile_io.EVIDENCE_POOL_FILENAME,
        agent_activity.AGENT_ACTIVITY_FILENAME,
    ):
        snapshot = file_state.snapshot_file(pdir / filename)
        fingerprints.append(f"{filename}:{snapshot.sha256 or 'empty'}")
    fingerprints.extend(_public_layer_fingerprints(pdir))
    digest = hashlib.sha256("|".join(fingerprints).encode("utf-8")).hexdigest()
    return f'W/"{digest}"'


def _review_error(
    status_code: int,
    code: str,
    message: str,
    etag: str,
) -> JSONResponse:
    """4xx body plus a fresh review ETag header for client reloads."""
    body = ErrorResponse(code=code, message=message)
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(),
        headers={"ETag": etag},
    )


def _resolve_review_window(start: str, end: str) -> tuple[str, str]:
    """Normalize the review window query params to an ISO (start, end) pair.

    Both params empty defaults to the current natural week (Monday → today);
    exactly one provided is a 422. Reversed windows are swapped.
    """
    clean_start, clean_end = start.strip(), end.strip()
    if not clean_start and not clean_end:
        default_start, default_end = review_window_default()
        return default_start.isoformat(), default_end.isoformat()
    if not clean_start or not clean_end:
        raise ApiError(
            422,
            "invalid_review_window",
            "Both start and end are required for a custom review window.",
        )
    try:
        start_date, end_date = normalize_review_window(clean_start, clean_end)
    except ValueError as exc:
        raise ApiError(
            422,
            "invalid_review_window",
            f"Invalid review window: {exc}",
        ) from exc
    return start_date.isoformat(), end_date.isoformat()


@router.get(
    "/profiles/{name}/review",
    response_model=ReviewResponse,
    responses=ERROR_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def get_profile_review(
    name: str,
    response: Response,
    start: str = Query("", description="ISO window start; empty = current week."),
    end: str = Query("", description="ISO window end; empty = current week."),
) -> ReviewResponse:
    """Weekly review: Done tasks plus evidence/next-action/public candidates.

    Read-only aggregation (``core.growth_review.build_weekly_review``); the
    response carries the review-source ETag (see module docstring) for use as
    ``If-Match`` on the save/apply mutations. Candidate generation is
    rule-based only — this page has no LLM dependency.
    """
    pdir = _resolve_profile(name)
    window_start, window_end = _resolve_review_window(start, end)
    review = build_weekly_review(
        pdir.name, window_start, window_end, profile_path=pdir
    )
    data = review.to_dict()["review"]
    response.headers["ETag"] = _review_etag(pdir)
    return ReviewResponse(
        profile=pdir.name,
        week_start=str(data["week_start"]),
        week_end=str(data["week_end"]),
        done_task_ids=[str(task_id) for task_id in data["done_task_ids"]],
        activity_summary=dict(data["activity_summary"]),
        learning_summary=dict(data["learning_summary"]),
        inbox_summary=dict(data["inbox_summary"]),
        evidence_candidates=[
            ReviewCandidateModel(**c) for c in data["evidence_candidates"]
        ],
        next_queue_candidates=[
            ReviewCandidateModel(**c) for c in data["next_queue_candidates"]
        ],
        method_candidates=[
            ReviewCandidateModel(**c) for c in data["method_candidates"]
        ],
        public_candidates=[
            ReviewCandidateModel(**c) for c in data["public_candidates"]
        ],
        summary=ReviewSummaryModel(
            done_tasks=len(data["done_task_ids"]),
            evidence_candidates=len(data["evidence_candidates"]),
            next_action_candidates=len(data["next_queue_candidates"]),
            public_draft_candidates=len(data["public_candidates"]),
        ),
    )


REVIEW_CANDIDATE_TYPES = ("evidence", "next_action", "public_draft")

REVIEW_MUTATION_RESPONSES = {
    **ERROR_RESPONSES,
    412: {
        "model": ErrorResponse,
        "description": "If-Match ETag does not match the review source files.",
    },
    422: {
        "model": ErrorResponse,
        "description": "Invalid window, unknown candidate type, or empty selection.",
    },
}


def _check_review_mutation(
    name: str,
    candidate_type: str,
    if_match: str | None,
) -> tuple[Path, str] | JSONResponse:
    """Shared save/apply guards: candidate-type whitelist + If-Match."""
    clean_type = candidate_type.strip()
    if clean_type not in REVIEW_CANDIDATE_TYPES:
        raise ApiError(
            422,
            "invalid_review_candidate_type",
            f"Unknown review candidate type {candidate_type!r} "
            f"(expected one of: {', '.join(REVIEW_CANDIDATE_TYPES)}).",
        )
    pdir = _resolve_profile(name)
    etag = _review_etag(pdir)
    if not _if_match_satisfied(if_match, etag):
        return _review_error(
            412,
            "etag_mismatch",
            "Review source files changed since they were loaded; "
            "reload before mutating.",
            etag,
        )
    return pdir, etag


@router.post(
    "/profiles/{name}/review/save",
    response_model=ReviewSaveResponse,
    responses=REVIEW_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def save_profile_review_candidates(
    name: str,
    body: ReviewSaveRequest,
    response: Response,
    if_match: str | None = Header(default=None),
) -> ReviewSaveResponse | JSONResponse:
    """Persist selected candidates as pending Agent Activity items.

    Thin wrapper over ``core.review_actions.save_review_candidates_to_activity``;
    the review window rides on the activity item's ``source_ref``. Honors
    ``If-Match`` (412 on mismatch, fresh ETag in the header).
    """
    checked = _check_review_mutation(name, body.candidate_type, if_match)
    if isinstance(checked, JSONResponse):
        return checked
    pdir, _etag = checked
    window_start, window_end = _resolve_review_window(body.start, body.end)
    try:
        stored = save_review_candidates_to_activity(
            pdir.name,
            window_start,
            window_end,
            body.candidate_type.strip(),
            [candidate.model_dump(exclude_unset=True) for candidate in body.candidates],
            expected_snapshot=file_state.snapshot_file(
                pdir / agent_activity.AGENT_ACTIVITY_FILENAME
            ),
        )
    except file_state.FileConflictError:
        # A concurrent write landed between the If-Match check and the
        # in-lock snapshot re-check (TOCTOU closure).
        return _review_error(
            412,
            "etag_mismatch",
            "Review source files changed while saving; "
            "reload before retrying.",
            _review_etag(pdir),
        )
    response.headers["ETag"] = _review_etag(pdir)
    return ReviewSaveResponse(
        ok=True,
        saved=len(stored),
        item_ids=[str(item.get("id") or "") for item in stored],
    )


@router.post(
    "/profiles/{name}/review/apply",
    response_model=ReviewApplyResponse,
    responses=REVIEW_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def apply_profile_review_candidates(
    name: str,
    body: ReviewApplyRequest,
    response: Response,
    if_match: str | None = Header(default=None),
) -> ReviewApplyResponse | JSONResponse:
    """Apply selected candidates to their owner files (pool/kanban/blog).

    Dispatches to the ``core.review_actions.apply_review_*`` appliers per
    candidate; per-candidate failures are reported in ``results`` without
    failing the whole request (mirroring the Streamlit one-by-one apply).
    Honors ``If-Match`` (412 on mismatch, fresh ETag in the header).
    """
    checked = _check_review_mutation(name, body.candidate_type, if_match)
    if isinstance(checked, JSONResponse):
        return checked
    pdir, _etag = checked
    window_start, window_end = _resolve_review_window(body.start, body.end)
    candidate_type = body.candidate_type.strip()
    # Request-start fingerprints, threaded into the appliers' first write
    # per file and consumed on first use (later candidates in this request
    # legitimately see the files changed by earlier ones).
    snapshots: dict[str, file_state.FileSnapshot | None] = {
        "activity": file_state.snapshot_file(
            pdir / agent_activity.AGENT_ACTIVITY_FILENAME
        ),
        "pool": file_state.snapshot_file(
            pdir / profile_io.EVIDENCE_POOL_FILENAME
        ),
        "kanban": file_state.snapshot_file(kanban_path(pdir)),
    }
    results: list[ReviewApplyResultModel] = []
    try:
        for candidate in body.candidates:
            raw = candidate.model_dump(exclude_unset=True)
            if candidate_type == "evidence":
                applied = apply_review_evidence_candidate(
                    pdir.name,
                    window_start,
                    window_end,
                    raw,
                    mark_crystallized=body.mark_crystallized,
                    activity_snapshot=snapshots.pop("activity", None),
                    pool_snapshot=snapshots.pop("pool", None),
                    kanban_snapshot=snapshots.pop("kanban", None),
                )
            elif candidate_type == "next_action":
                applied = apply_review_next_action_candidate(
                    pdir.name,
                    window_start,
                    window_end,
                    raw,
                    activity_snapshot=snapshots.pop("activity", None),
                    kanban_snapshot=snapshots.pop("kanban", None),
                )
            else:
                applied = apply_review_public_draft_candidate(
                    pdir.name,
                    window_start,
                    window_end,
                    raw,
                    activity_snapshot=snapshots.pop("activity", None),
                )
            results.append(
                ReviewApplyResultModel(
                    ok=applied.ok,
                    title=str(raw.get("title") or ""),
                    warnings=list(applied.warnings),
                    errors=list(applied.errors),
                    changed_paths=[str(path) for path in applied.changed_paths],
                    output_path=(
                        str(applied.output_path) if applied.output_path else ""
                    ),
                )
            )
    except file_state.FileConflictError:
        # A concurrent write landed between the If-Match check and an
        # applier's in-lock snapshot re-check (TOCTOU closure). Candidates
        # already applied stay applied; the client must reload.
        return _review_error(
            412,
            "etag_mismatch",
            "Review source files changed while applying; "
            "reload before retrying.",
            _review_etag(pdir),
        )
    response.headers["ETag"] = _review_etag(pdir)
    applied_count = sum(1 for result in results if result.ok)
    return ReviewApplyResponse(
        ok=applied_count == len(results),
        applied=applied_count,
        failed=len(results) - applied_count,
        results=results,
    )


# --- Project Board (M3): internal project cases + linked kanban tasks -------


PROJECT_BOARD_ETAG_FILES = (
    "project-board.yaml",
    "kanban.md",
    profile_io.EVIDENCE_POOL_FILENAME,
    "goals.yaml",
    "experience.yaml",
    "outputs.yaml",
    "research/sources.yaml",
)


def _project_board_etag(pdir: Path) -> str:
    """Weak ETag over the project-board source files (sha256 fingerprint).

    Case/milestone mutations write project-board.yaml plus kanban.md,
    evidence-pool.yaml, and research/sources.yaml through
    ``sync_project_case_workspace``; the ref options additionally read
    goals/experience/outputs. Weak (``W/``) because the hash identifies the
    source file versions, not the JSON response bytes.
    """
    fingerprints = []
    for relative in PROJECT_BOARD_ETAG_FILES:
        snapshot = file_state.snapshot_file(pdir / relative)
        fingerprints.append(f"{relative}:{snapshot.sha256 or 'empty'}")
    digest = hashlib.sha256("|".join(fingerprints).encode("utf-8")).hexdigest()
    return f'W/"{digest}"'


def _project_board_error(
    status_code: int,
    code: str,
    message: str,
    etag: str,
) -> JSONResponse:
    """4xx body plus a fresh board ETag header for client reloads."""
    body = ErrorResponse(code=code, message=message)
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(),
        headers={"ETag": etag},
    )


def _task_section_index(pdir: Path) -> dict[str, str]:
    """Map task id -> kanban section name for milestone completion math."""
    index: dict[str, str] = {}
    for section, tasks in parse_kanban(pdir).items():
        for task in tasks:
            if task.id:
                index[task.id] = section
    return index


def _live_section_tasks(pdir: Path) -> list[tuple[str, KanbanTask]]:
    """All live kanban tasks as [(section, task)] for case aggregation."""
    rows: list[tuple[str, KanbanTask]] = []
    for section, tasks in parse_kanban(pdir).items():
        for task in tasks:
            rows.append((section, task))
    return rows


def _case_task_models(
    case: ProjectCase,
    live: list[tuple[str, KanbanTask]],
    archived: list[KanbanTask],
) -> list[ProjectTaskModel]:
    """Owned kanban tasks (live + archived) with their board section.

    Ownership mirrors the Streamlit page: ``task.project_id == case.id`` or
    the task id appears in the case's ``task_refs``. De-duped by task id
    (live wins over archive); unlike the timeline payload, tasks without a
    date anchor are kept so the Tasks tab shows the whole project backlog.
    """
    rows: list[ProjectTaskModel] = []
    seen: set[str] = set()
    owned_refs = set(case.task_refs)

    def add(task: KanbanTask, section: str, is_archived: bool) -> None:
        task_id = str(task.id or "").strip()
        if task.project_id != case.id and not (task_id and task_id in owned_refs):
            return
        if task_id and task_id in seen:
            return
        if task_id:
            seen.add(task_id)
        rows.append(
            ProjectTaskModel(
                id=task_id,
                title=task.title,
                section=section,
                done=task.done,
                milestone_id=task.milestone_id,
                started_on=task.started_on,
                completed_on=task.completed_on,
                archived=is_archived,
            )
        )

    for section, task in live:
        add(task, section, False)
    for task in archived:
        add(task, KANBAN_DONE, True)
    rows.sort(
        key=lambda row: (row.completed_on or row.started_on or "9999-99-99", row.id)
    )
    return rows


def _project_case_model(
    case: ProjectCase,
    task_index: dict[str, str],
    live: list[tuple[str, KanbanTask]],
    archived: list[KanbanTask],
) -> ProjectCaseModel:
    """API projection of one ProjectCase (milestones + owned tasks)."""
    timeline_rows = timeline_tasks(case, live, archived, archived_section=KANBAN_DONE)
    milestones: list[ProjectMilestoneModel] = []
    for milestone in case.milestones:
        refs = [ref for ref in milestone.task_refs if ref]
        done = sum(1 for ref in refs if task_index.get(ref) == KANBAN_DONE)
        milestones.append(
            ProjectMilestoneModel(
                id=milestone.id,
                title=milestone.title,
                status=milestone.status,
                target=milestone.target,
                date=milestone.date,
                summary=milestone.summary,
                task_refs=list(milestone.task_refs),
                evidence_refs=list(milestone.evidence_refs),
                source_refs=list(milestone.source_refs),
                output_refs=list(milestone.output_refs),
                done_count=done,
                total_count=len(refs),
            )
        )
    return ProjectCaseModel(
        id=case.id,
        title=case.title,
        status=case.status,
        kind=case.kind,
        visibility=case.visibility,
        time_range=case.time_range,
        summary=case.summary,
        notes=case.notes,
        goal_refs=list(case.goal_refs),
        task_refs=list(case.task_refs),
        evidence_refs=list(case.evidence_refs),
        source_refs=list(case.source_refs),
        experience_refs=list(case.experience_refs),
        output_refs=list(case.output_refs),
        milestones=milestones,
        tasks=_case_task_models(case, live, archived),
        derived_time_range=timeline_date_range(timeline_rows),
    )


def _goal_ref_options(pdir: Path) -> dict[str, str]:
    book = load_goal_book(pdir)
    return {
        goal.id: f"{goal.title or goal.label or goal.id} · {goal.status}"
        for goal in book.goals
        if goal.id
    }


def _task_ref_options(pdir: Path, case_id: str = "") -> dict[str, str]:
    """Task id -> label; tasks owned by another project are excluded.

    Used by the suggest-refs candidates where only claimable tasks make
    sense. The board GET uses ``_task_ref_option_rows`` instead, which keeps
    every task and exposes the owner for client-side filtering.
    """
    out: dict[str, str] = {}
    for section, tasks in parse_kanban(pdir).items():
        for task in tasks:
            if not task.id:
                continue
            owner = task.project_id
            if owner and owner != case_id:
                continue
            out[task.id] = f"[{section}] {task.title} · {task.id}"
    return out


def _task_ref_option_rows(pdir: Path) -> list[ProjectRefOptionModel]:
    """All kanban tasks as option rows carrying the current owner project."""
    rows: list[ProjectRefOptionModel] = []
    for section, tasks in parse_kanban(pdir).items():
        for task in tasks:
            if not task.id:
                continue
            rows.append(
                ProjectRefOptionModel(
                    id=task.id,
                    label=f"[{section}] {task.title} · {task.id}",
                    owner=task.project_id,
                )
            )
    return rows


def _evidence_ref_options(pdir: Path) -> dict[str, str]:
    raw = profile_io.load_evidence_pool_raw(pdir) or {}
    out: dict[str, str] = {}
    for row in raw.get("evidence_entries") or []:
        if not isinstance(row, dict):
            continue
        eid = str(row.get("id", "") or "").strip()
        if not eid:
            continue
        title = str(row.get("title", "") or eid)
        status = str(row.get("review_status", "") or "")
        out[eid] = f"{title} · {status}" if status else title
    return out


def _source_ref_options(pdir: Path) -> dict[str, str]:
    inbox_sources = load_research_sources(pdir)
    return {
        source.id: f"{source.title or source.id} · {source.status}"
        for source in inbox_sources.sources
        if source.id
    }


def _experience_ref_options(pdir: Path) -> dict[str, str]:
    book = load_experience_book(pdir)
    return {
        case.id: " · ".join(
            item for item in (case.organization, case.role, case.status) if item
        )
        or case.id
        for case in book.experience_cases
        if case.id
    }


def _output_ref_options(pdir: Path) -> dict[str, str]:
    raw = _load_yaml_dict(pdir / "outputs.yaml") or {}
    out: dict[str, str] = {}
    for item in raw.get("outputs") or []:
        if not isinstance(item, dict):
            continue
        oid = str(item.get("id", "") or "").strip()
        if oid:
            out[oid] = str(item.get("title", "") or oid)
    return out


def _option_rows(options: dict[str, str]) -> list[ProjectRefOptionModel]:
    return [ProjectRefOptionModel(id=ref, label=label) for ref, label in options.items()]


def _board_summary(pdir: Path, board: ProjectBoard) -> ProjectBoardSummaryModel:
    """Overview counters (status + ownership gaps), mirroring the Streamlit page."""
    counts = {status: 0 for status in PROJECT_STATUSES}
    for case in board.project_cases:
        counts[case.status] = counts.get(case.status, 0) + 1
    current_goal = load_goal_book(pdir).current_goal_id
    goal_count = sum(
        1
        for case in board.project_cases
        if current_goal and current_goal in case.goal_refs
    )
    unassigned_tasks = 0
    for _section, tasks in parse_kanban(pdir).items():
        unassigned_tasks += sum(1 for task in tasks if task.id and not task.project_id)
    raw = profile_io.load_evidence_pool_raw(pdir) or {}
    unassigned_evidence = 0
    for row in raw.get("evidence_entries") or []:
        if not isinstance(row, dict):
            continue
        if row.get("deprecated"):
            continue
        if str(row.get("review_status", "") or "") == "reviewed" and not row.get(
            "project_refs"
        ):
            unassigned_evidence += 1
    return ProjectBoardSummaryModel(
        status_counts={status: counts.get(status, 0) for status in PROJECT_STATUSES},
        unassigned_tasks=unassigned_tasks,
        unassigned_evidence=unassigned_evidence,
        current_goal_projects=goal_count,
    )


def _find_project_case(board: ProjectBoard, case_id: str) -> ProjectCase:
    """Locate one case by id or raise ApiError(404)."""
    case = board.by_id().get(case_id.strip())
    if case is None:
        raise ApiError(
            404, "project_case_not_found", f"Unknown project case: {case_id}"
        )
    return case


PROJECT_BOARD_MUTATION_RESPONSES = {
    **ERROR_RESPONSES,
    404: {
        "model": ErrorResponse,
        "description": "Profile, project case, or milestone not found.",
    },
    412: {
        "model": ErrorResponse,
        "description": "If-Match ETag does not match the board source files.",
    },
    422: {
        "model": ErrorResponse,
        "description": (
            "Blank title, out-of-domain status/kind/visibility, duplicate id, "
            "unknown section, or AI suggest-refs unavailable."
        ),
    },
}


def _check_board_mutation(
    name: str,
    if_match: str | None,
) -> tuple[Path, ProjectBoard, dict[str, file_state.FileSnapshot]] | JSONResponse:
    """Shared mutation guard: resolve profile + board, verify If-Match.

    Also returns the request-start fingerprints of the files the board
    mutations write (``board`` / ``kanban`` / ``pool`` / ``sources``) so
    the sync layer can re-check them inside each file's write lock; a
    mismatch there raises ``FileConflictError`` → 412 (TOCTOU closure).
    """
    pdir = _resolve_profile(name)
    etag = _project_board_etag(pdir)
    if not _if_match_satisfied(if_match, etag):
        return _project_board_error(
            412,
            "etag_mismatch",
            "Project board source files changed since they were loaded; "
            "reload before mutating.",
            etag,
        )
    snapshots = {
        "board": file_state.snapshot_file(pdir / "project-board.yaml"),
        "kanban": file_state.snapshot_file(kanban_path(pdir)),
        "pool": file_state.snapshot_file(
            pdir / profile_io.EVIDENCE_POOL_FILENAME
        ),
        "sources": file_state.snapshot_file(pdir / "research" / "sources.yaml"),
    }
    return pdir, load_project_board(pdir), snapshots


def _require_board_choice(
    value: str | None,
    allowed: tuple[str, ...],
    field: str,
) -> str | None:
    """Validate an optional enum field; 422 when outside the domain."""
    if value is None:
        return None
    clean = value.strip()
    if clean not in allowed:
        raise ApiError(
            422,
            "invalid_project_field",
            f"Value {value!r} is not valid for {field} "
            f"(expected one of: {', '.join(allowed)}).",
        )
    return clean


def _synced_case_response(
    pdir: Path,
    board: ProjectBoard,
    case_id: str,
    response: Response,
    snapshots: dict[str, file_state.FileSnapshot] | None = None,
) -> ProjectCaseMutationResponse | JSONResponse:
    """Persist one case's workspace sync and answer with the fresh model.

    A ``FileConflictError`` from the sync layer's in-lock snapshot
    re-checks answers 412 with a fresh board ETag (TOCTOU closure).
    """
    try:
        result = sync_project_case_workspace(
            pdir.name, board, case_id, expected_snapshots=snapshots
        )
    except file_state.FileConflictError:
        return _project_board_error(
            412,
            "etag_mismatch",
            "Project board source files changed while syncing; "
            "reload before retrying.",
            _project_board_etag(pdir),
        )
    fresh = load_project_board(pdir)
    case = _find_project_case(fresh, case_id)
    task_index = _task_section_index(pdir)
    live = _live_section_tasks(pdir)
    archived = _archive_tasks(pdir)
    response.headers["ETag"] = _project_board_etag(pdir)
    return ProjectCaseMutationResponse(
        ok=True,
        case=_project_case_model(case, task_index, live, archived),
        warnings=list(result.warnings),
    )


@router.get(
    "/profiles/{name}/project-board",
    response_model=ProjectBoardResponse,
    responses=ERROR_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def get_profile_project_board(name: str, response: Response) -> ProjectBoardResponse:
    """Internal project cases, summary counters, and ref-picker options.

    Aggregates project-board.yaml with kanban/evidence/goals/sources/
    experience/outputs lookups (all through the core ``*_io`` modules). The
    response carries the board-source ETag (see module docstring) for use as
    ``If-Match`` on the case/milestone/task mutations.
    """
    pdir = _resolve_profile(name)
    board = load_project_board(pdir)
    task_index = _task_section_index(pdir)
    live = _live_section_tasks(pdir)
    archived = _archive_tasks(pdir)
    response.headers["ETag"] = _project_board_etag(pdir)
    return ProjectBoardResponse(
        profile=pdir.name,
        updated=board.updated,
        summary=_board_summary(pdir, board),
        cases=[
            _project_case_model(case, task_index, live, archived)
            for case in board.project_cases
        ],
        options=ProjectBoardOptionsModel(
            goals=_option_rows(_goal_ref_options(pdir)),
            tasks=_task_ref_option_rows(pdir),
            evidence=_option_rows(_evidence_ref_options(pdir)),
            sources=_option_rows(_source_ref_options(pdir)),
            experiences=_option_rows(_experience_ref_options(pdir)),
            outputs=_option_rows(_output_ref_options(pdir)),
        ),
    )


@router.post(
    "/profiles/{name}/project-board/cases",
    response_model=ProjectCaseMutationResponse,
    status_code=201,
    responses=PROJECT_BOARD_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def create_profile_project_case(
    name: str,
    body: ProjectCaseCreateRequest,
    response: Response,
    if_match: str | None = Header(default=None),
) -> ProjectCaseMutationResponse | JSONResponse:
    """Create one project case (title required; id auto-slugged when blank).

    Mirrors the Streamlit create form: status/kind/visibility are validated
    against the core domains (422 otherwise), a duplicate id answers 422.
    After creation the case is synced into kanban/pool/sources. Honors
    ``If-Match`` (412 on mismatch, fresh ETag in the header).
    """
    checked = _check_board_mutation(name, if_match)
    if isinstance(checked, JSONResponse):
        return checked
    pdir, board, snapshots = checked
    try:
        case = add_project_case(
            board,
            body.title,
            case_id=body.id.strip(),
            status=_require_board_choice(body.status, PROJECT_STATUSES, "status")
            or PROJECT_STATUSES[0],
            kind=_require_board_choice(body.kind, PROJECT_KINDS, "kind")
            or PROJECT_KINDS[0],
            visibility=_require_board_choice(
                body.visibility, PROJECT_VISIBILITIES, "visibility"
            )
            or PROJECT_VISIBILITIES[0],
            summary=body.summary,
            goal_refs=body.goal_refs,
            evidence_refs=body.evidence_refs,
        )
    except ValueError as exc:
        raise ApiError(422, "invalid_project_case", str(exc)) from exc
    return _synced_case_response(pdir, board, case.id, response, snapshots)


@router.post(
    "/profiles/{name}/project-board/cases/{case_id}/save",
    response_model=ProjectCaseMutationResponse,
    responses=PROJECT_BOARD_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def save_profile_project_case(
    name: str,
    case_id: str,
    body: ProjectCaseUpdateRequest,
    response: Response,
    if_match: str | None = Header(default=None),
) -> ProjectCaseMutationResponse | JSONResponse:
    """Save the project basics + ref lists (``None`` fields keep the value).

    Ref writes flow through ``sync_project_case_workspace``: kanban task
    ``project_id``/``milestone_id`` and evidence-pool ``project_refs`` are
    updated to match, and tasks already owned by another project are dropped
    from the refs with a warning instead of being stolen. Honors
    ``If-Match`` (412 on mismatch).
    """
    checked = _check_board_mutation(name, if_match)
    if isinstance(checked, JSONResponse):
        return checked
    pdir, board, snapshots = checked
    _find_project_case(board, case_id)
    fields: dict[str, Any] = {}
    if body.title is not None:
        if not body.title.strip():
            raise ApiError(
                422, "invalid_project_case", "Project case title must not be blank."
            )
        fields["title"] = body.title
    for field, allowed in (
        ("status", PROJECT_STATUSES),
        ("kind", PROJECT_KINDS),
        ("visibility", PROJECT_VISIBILITIES),
    ):
        value = _require_board_choice(getattr(body, field), allowed, field)
        if value is not None:
            fields[field] = value
    for field in ("time_range", "summary", "notes"):
        value = getattr(body, field)
        if value is not None:
            fields[field] = value
    for field in (
        "goal_refs",
        "task_refs",
        "evidence_refs",
        "source_refs",
        "experience_refs",
        "output_refs",
    ):
        value = getattr(body, field)
        if value is not None:
            fields[field] = clean_ref_list(value)
    try:
        update_project_case(board, case_id, **fields)
    except (KeyError, ValueError) as exc:
        raise ApiError(422, "invalid_project_case", str(exc)) from exc
    return _synced_case_response(pdir, board, case_id, response, snapshots)


@router.post(
    "/profiles/{name}/project-board/cases/{case_id}/archive",
    response_model=ProjectCaseMutationResponse,
    responses=PROJECT_BOARD_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def archive_profile_project_case(
    name: str,
    case_id: str,
    response: Response,
    if_match: str | None = Header(default=None),
) -> ProjectCaseMutationResponse | JSONResponse:
    """Mark one project case archived. Honors ``If-Match`` (412)."""
    checked = _check_board_mutation(name, if_match)
    if isinstance(checked, JSONResponse):
        return checked
    pdir, board, snapshots = checked
    _find_project_case(board, case_id)
    update_project_case(board, case_id, status="archived")
    return _synced_case_response(pdir, board, case_id, response, snapshots)


def _find_milestone(case: ProjectCase, milestone_id: str) -> ProjectMilestone:
    """Locate one milestone inside a case or raise ApiError(404)."""
    for milestone in case.milestones:
        if milestone.id == milestone_id.strip():
            return milestone
    raise ApiError(
        404,
        "project_milestone_not_found",
        f"Unknown milestone {milestone_id} in project {case.id}.",
    )


def _next_milestone_id(case: ProjectCase, title: str) -> str:
    """Slug-based milestone id, suffixed until unique within the case."""
    base = f"milestone:{project_board_slug(title)}"
    existing = {milestone.id for milestone in case.milestones if milestone.id}
    if base not in existing:
        return base
    index = 2
    while f"{base}-{index}" in existing:
        index += 1
    return f"{base}-{index}"


def project_board_slug(value: str, fallback: str = "milestone") -> str:
    """Slugify a title for an auto-generated milestone id."""
    clean = re.sub(
        r"[^a-z0-9一-鿿._~-]+", "-", value.strip().lower()
    ).strip(".-")
    return clean or fallback


@router.post(
    "/profiles/{name}/project-board/cases/{case_id}/milestones",
    response_model=ProjectCaseMutationResponse,
    status_code=201,
    responses=PROJECT_BOARD_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def add_profile_project_milestone(
    name: str,
    case_id: str,
    body: ProjectMilestoneAddRequest,
    response: Response,
    if_match: str | None = Header(default=None),
) -> ProjectCaseMutationResponse | JSONResponse:
    """Add one milestone to a case (title required; duplicate id → 422).

    Honors ``If-Match`` (412 on mismatch, fresh ETag in the header).
    """
    checked = _check_board_mutation(name, if_match)
    if isinstance(checked, JSONResponse):
        return checked
    pdir, board, snapshots = checked
    case = _find_project_case(board, case_id)
    clean_id = body.id.strip() or _next_milestone_id(case, body.title)
    if any(item.id == clean_id for item in case.milestones):
        raise ApiError(
            422,
            "duplicate_milestone",
            f"Milestone id already exists in project {case.id}: {clean_id}",
        )
    case.milestones.append(
        ProjectMilestone(
            id=clean_id,
            title=body.title.strip(),
            target=body.target.strip(),
            date=body.date.strip(),
            summary=body.summary.strip(),
        )
    )
    return _synced_case_response(pdir, board, case.id, response, snapshots)


@router.post(
    "/profiles/{name}/project-board/cases/{case_id}/milestones/{milestone_id}/save",
    response_model=ProjectCaseMutationResponse,
    responses=PROJECT_BOARD_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def save_profile_project_milestone(
    name: str,
    case_id: str,
    milestone_id: str,
    body: ProjectMilestoneUpdateRequest,
    response: Response,
    if_match: str | None = Header(default=None),
) -> ProjectCaseMutationResponse | JSONResponse:
    """Save one milestone (``None`` fields keep the value). Honors If-Match."""
    checked = _check_board_mutation(name, if_match)
    if isinstance(checked, JSONResponse):
        return checked
    pdir, board, snapshots = checked
    case = _find_project_case(board, case_id)
    milestone = _find_milestone(case, milestone_id)
    if body.title is not None:
        if not body.title.strip():
            raise ApiError(
                422, "invalid_project_milestone", "Milestone title must not be blank."
            )
        milestone.title = body.title.strip()
    status = _require_board_choice(body.status, MILESTONE_STATUSES, "status")
    if status is not None:
        milestone.status = status
    for field in ("target", "date", "summary"):
        value = getattr(body, field)
        if value is not None:
            setattr(milestone, field, value.strip())
    for field in ("task_refs", "evidence_refs", "source_refs", "output_refs"):
        value = getattr(body, field)
        if value is not None:
            setattr(milestone, field, clean_ref_list(value))
    return _synced_case_response(pdir, board, case.id, response, snapshots)


@router.post(
    "/profiles/{name}/project-board/cases/{case_id}/milestones/{milestone_id}/delete",
    response_model=ProjectCaseMutationResponse,
    responses=PROJECT_BOARD_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def delete_profile_project_milestone(
    name: str,
    case_id: str,
    milestone_id: str,
    response: Response,
    if_match: str | None = Header(default=None),
) -> ProjectCaseMutationResponse | JSONResponse:
    """Remove one milestone from a case. Honors ``If-Match`` (412)."""
    checked = _check_board_mutation(name, if_match)
    if isinstance(checked, JSONResponse):
        return checked
    pdir, board, snapshots = checked
    case = _find_project_case(board, case_id)
    _find_milestone(case, milestone_id)
    case.milestones = [
        item for item in case.milestones if item.id != milestone_id.strip()
    ]
    return _synced_case_response(pdir, board, case.id, response, snapshots)


@router.post(
    "/profiles/{name}/project-board/cases/{case_id}/tasks",
    response_model=KanbanMutationResponse,
    status_code=201,
    responses=PROJECT_BOARD_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def add_profile_project_task(
    name: str,
    case_id: str,
    body: ProjectTaskCreateRequest,
    response: Response,
    if_match: str | None = Header(default=None),
) -> KanbanMutationResponse | JSONResponse:
    """Quick-add one kanban task owned by this project case.

    Follows the board's column-date idiom like the Streamlit component:
    the chosen (or today's) date is stored as ``started_on`` so the task
    always has a timeline anchor; cards added directly to Done also get
    ``completed_on`` + ``done``. After the kanban save the board's task refs
    are re-synced from kanban metadata. Honors ``If-Match`` (412 on
    mismatch); a concurrent kanban write is 3-way merged.
    """
    checked = _check_board_mutation(name, if_match)
    if isinstance(checked, JSONResponse):
        return checked
    pdir, board, snapshots = checked
    case = _find_project_case(board, case_id)
    target = resolve_kanban_section(body.section)
    if target is None:
        raise _unknown_kanban_section(body.section)
    milestone_id = body.milestone_id.strip()
    if milestone_id and not any(
        milestone.id == milestone_id for milestone in case.milestones
    ):
        raise ApiError(
            422,
            "unknown_milestone",
            f"Unknown milestone {milestone_id!r} in project {case.id}.",
        )
    snapshot = file_state.snapshot_file(kanban_path(pdir))
    sections = parse_kanban(pdir)
    base = copy_kanban_sections(sections)
    anchor = body.date.strip() or date.today().isoformat()
    task = KanbanTask(
        title=body.title.strip(),
        project_id=case.id,
        milestone_id=milestone_id,
        context=body.context.strip(),
    )
    if target == KANBAN_DONE:
        task = replace(task, started_on=anchor, completed_on=anchor, done=True)
    else:
        task = replace(task, started_on=anchor)
    sections.setdefault(target, []).append(task)
    ensured = ensure_kanban_task_ids(sections, pdir.name)
    created_id = ensured[target][-1].id
    result = _save_kanban_mutation(pdir, ensured, base, snapshot)
    section, stored = _find_card_by_id(result.sections, created_id)
    try:
        sync_project_board_from_kanban(
            pdir.name,
            parse_kanban(pdir),
            expected_snapshot=snapshots["board"],
        )
    except file_state.FileConflictError:
        return _project_board_error(
            412,
            "etag_mismatch",
            "Project board source files changed while syncing; "
            "reload before retrying.",
            _project_board_etag(pdir),
        )
    response.headers["ETag"] = _project_board_etag(pdir)
    return KanbanMutationResponse(
        ok=True,
        card=_kanban_task_model(stored),
        section=section,
        merged_external=result.merged_external,
        merge_notices=_merge_notices(result),
    )


@router.post(
    "/profiles/{name}/project-board/tasks/{task_id}/move",
    response_model=KanbanMutationResponse,
    responses=PROJECT_BOARD_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def move_profile_project_task(
    name: str,
    task_id: str,
    body: ProjectTaskMoveRequest,
    response: Response,
    if_match: str | None = Header(default=None),
) -> KanbanMutationResponse | JSONResponse:
    """Move one project task to another kanban section by task id.

    Reuses ``apply_kanban_reorder(auto_dates=True)``: landing in Done marks
    the card done with ``completed_on``, leaving Done clears both. The board
    is re-synced from kanban metadata after the save. Honors ``If-Match``
    (412 on mismatch); unknown task id answers 404.
    """
    checked = _check_board_mutation(name, if_match)
    if isinstance(checked, JSONResponse):
        return checked
    pdir, _board, snapshots = checked
    target = resolve_kanban_section(body.target_section)
    if target is None:
        raise _unknown_kanban_section(body.target_section)
    snapshot = file_state.snapshot_file(kanban_path(pdir))
    sections = parse_kanban(pdir)
    base = copy_kanban_sections(sections)
    task: KanbanTask | None = None
    for _section, tasks in sections.items():
        for candidate in tasks:
            if candidate.id and candidate.id == task_id.strip():
                task = candidate
                break
        if task is not None:
            break
    if task is None:
        raise ApiError(
            404, "kanban_card_not_found", f"Unknown kanban task id: {task_id}"
        )
    moved = apply_kanban_reorder(
        sections,
        [{"id": task.id, "to_section": target}],
        auto_dates=True,
    )
    result = _save_kanban_mutation(pdir, moved, base, snapshot)
    section, stored = _find_card_by_id(result.sections, task.id)
    try:
        sync_project_board_from_kanban(
            pdir.name,
            parse_kanban(pdir),
            expected_snapshot=snapshots["board"],
        )
    except file_state.FileConflictError:
        return _project_board_error(
            412,
            "etag_mismatch",
            "Project board source files changed while syncing; "
            "reload before retrying.",
            _project_board_etag(pdir),
        )
    response.headers["ETag"] = _project_board_etag(pdir)
    return KanbanMutationResponse(
        ok=True,
        card=_kanban_task_model(stored),
        section=section,
        merged_external=result.merged_external,
        merge_notices=_merge_notices(result),
    )


PROJECT_SUGGEST_REF_FIELDS = (
    "goal_refs",
    "task_refs",
    "evidence_refs",
    "source_refs",
    "output_refs",
)


@router.post(
    "/profiles/{name}/project-board/cases/{case_id}/suggest-refs",
    response_model=ProjectSuggestRefsResponse,
    responses=PROJECT_BOARD_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def suggest_profile_project_refs(
    name: str,
    case_id: str,
) -> ProjectSuggestRefsResponse:
    """AI-suggest goal/task/evidence/source/output refs for one case.

    Runs the ``project.suggest_refs`` AI action through the gateway
    (``require_review=True``, so the run is recorded to Agent Activity).
    Suggestions are validated against the current option rows and returned
    for confirm-not-fill review — nothing is persisted by this endpoint.
    When no LLM backend is configured or the run fails, answers 422
    (``project_suggest_refs_failed``) so the SPA can show a degradation card.
    """
    pdir = _resolve_profile(name)
    board = load_project_board(pdir)
    case = _find_project_case(board, case_id)
    option_maps: dict[str, dict[str, str]] = {
        "goal_refs": _goal_ref_options(pdir),
        "task_refs": _task_ref_options(pdir, case.id),
        "evidence_refs": _evidence_ref_options(pdir),
        "source_refs": _source_ref_options(pdir),
        "output_refs": _output_ref_options(pdir),
    }
    payload = {
        "reply_language": llm_client.reply_language(),
        "project": {
            "id": case.id,
            "title": case.title,
            "status": case.status,
            "kind": case.kind,
            "summary": case.summary,
            "notes": case.notes,
        },
        "current_refs": {
            field: list(getattr(case, field)) for field in PROJECT_SUGGEST_REF_FIELDS
        },
        "candidates": {
            field: [
                {"id": ref, "label": label}
                for ref, label in list(options.items())[:80]
            ]
            for field, options in option_maps.items()
        },
    }
    result = run_ai_action(
        "project.suggest_refs",
        payload,
        profile=pdir.name,
        context_refs=[case.id],
        require_review=True,
    )
    if not result.ok:
        raise ApiError(
            422,
            "project_suggest_refs_failed",
            result.error or result.content or "AI ref suggestion failed.",
        )
    data = result.structured if isinstance(result.structured, dict) else {}
    suggestions = {
        field: [
            ref
            for ref in clean_ref_list(data.get(field))
            if ref in option_maps.get(field, {})
        ]
        for field in PROJECT_SUGGEST_REF_FIELDS
    }
    return ProjectSuggestRefsResponse(
        ok=True,
        backend=result.backend,
        suggestions=suggestions,
        rationale=str(data.get("rationale") or "").strip(),
        warnings=clean_ref_list(data.get("warnings")) + list(result.warnings),
    )


# --- Output Studio (M4): public blog drafts + evidence/claim-first drafts ---


def _studio_etag(pdir: Path) -> str:
    """Weak ETag over the profile's public-layer files (sha256 fingerprint).

    Covers the public-layer YAML files plus every blog Markdown/sidecar
    document, so the create/init mutations can detect concurrent edits.
    Weak (``W/``) because the hash identifies the source file versions,
    not the JSON response bytes.
    """
    digest = hashlib.sha256(
        "|".join(_public_layer_fingerprints(pdir)).encode("utf-8")
    ).hexdigest()
    return f'W/"{digest}"'


def _studio_post_etag(post) -> str:
    """Weak ETag for one blog post (Markdown file + BlockNote sidecar)."""
    paths = [post.path]
    if post.sidecar_path is not None:
        paths.append(post.sidecar_path)
    fingerprints = []
    for path in paths:
        snapshot = file_state.snapshot_file(path)
        fingerprints.append(f"{path.name}:{snapshot.sha256 or 'empty'}")
    digest = hashlib.sha256("|".join(fingerprints).encode("utf-8")).hexdigest()
    return f'W/"{digest}"'


def _studio_error(
    status_code: int,
    code: str,
    message: str,
    etag: str,
) -> JSONResponse:
    """4xx body plus a fresh studio ETag header for client reloads."""
    body = ErrorResponse(code=code, message=message)
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(),
        headers={"ETag": etag},
    )


def _string_list(value: object) -> list[str]:
    """Coerce a front-matter list value into a clean string list."""
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _studio_post_model(post) -> StudioPostModel:
    """List-row projection of one core BlogPost."""
    return StudioPostModel(
        slug=post.slug,
        title=post.title,
        date=post.date,
        status=post.status,
        summary=post.summary,
        cover=str(post.meta.get("cover") or ""),
        tags=_string_list(post.meta.get("tags")),
        category_path=[str(part) for part in post.category_path],
    )


def _studio_post_detail(post) -> StudioPostDetailModel:
    """Editor projection of one core BlogPost (meta + body)."""
    base = _studio_post_model(post)
    return StudioPostDetailModel(
        **base.model_dump(),
        meta=dict(post.meta),
        body=post.body,
        has_math=markdown_contains_math(post.body),
        related_evidence=_string_list(post.meta.get("related_evidence")),
        related_kanban=_string_list(post.meta.get("related_kanban")),
        related_claims=_string_list(post.meta.get("related_claims")),
        related_sources=_string_list(post.meta.get("related_sources")),
        related_research_claims=_string_list(
            post.meta.get("related_research_claims")
        ),
        related_citations=_string_list(post.meta.get("related_citations")),
    )


def _load_studio_post(pdir: Path, slug: str):
    """Load one blog post by slug/route or raise a structured ApiError."""
    try:
        return load_blog_post(pdir.name, slug)
    except PublicSiteError as exc:
        message = str(exc)
        if "Ambiguous" in message:
            raise ApiError(422, "blog_slug_ambiguous", message) from exc
        raise ApiError(404, "blog_post_not_found", message) from exc


def _studio_claim_options(name: str) -> list[StudioSourceOptionModel]:
    options: list[StudioSourceOptionModel] = []
    for claim in accepted_claims_for_profile(name):
        claim_id = str(claim.get("id", "") or "").strip()
        if not claim_id:
            continue
        text = str(claim.get("text", "") or "").strip()
        label = f"{claim_id} - {text[:80]}" if text else claim_id
        options.append(StudioSourceOptionModel(id=claim_id, label=label))
    return options


def _studio_evidence_options(name: str) -> list[StudioSourceOptionModel]:
    return [
        StudioSourceOptionModel(
            id=ctx.id,
            label=f"{ctx.id} - {ctx.title}" if ctx.title else ctx.id,
        )
        for ctx in evidence_contexts(name)
    ]


def _studio_project_options(name: str) -> list[StudioSourceOptionModel]:
    options: list[StudioSourceOptionModel] = []
    for project in load_projects(name):
        project_id = str(project.get("id", "") or "").strip()
        if not project_id:
            continue
        title = str(project.get("title", "") or "").strip()
        options.append(
            StudioSourceOptionModel(
                id=project_id,
                label=f"{project_id} - {title}" if title else project_id,
            )
        )
    return options


@router.get(
    "/profiles/{name}/studio",
    response_model=StudioResponse,
    responses=ERROR_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def get_profile_studio(name: str, response: Response) -> StudioResponse:
    """Output Studio overview: blog posts, counters, and generation options.

    Lists every blog post (drafts and archived included; trashed excluded,
    mirroring the Streamlit blog tab). ``initialized`` is false until the
    profile's public layer exists (POST ``/studio/init`` creates it).
    ``options`` feeds the evidence/claim-first candidate form. The response
    carries the public-layer ETag (see module docstring) for use as
    ``If-Match`` on the init/create mutations.
    """
    pdir = _resolve_profile(name)
    initialized = all(
        (pdir / filename).exists()
        for filename in (
            PUBLIC_PROFILE_FILENAME,
            RESUME_SOURCE_FILENAME,
            PROJECTS_FILENAME,
            OUTPUTS_FILENAME,
        )
    )
    posts: list[StudioPostModel] = []
    if (pdir / BLOG_DIRNAME).exists():
        posts = [
            _studio_post_model(post)
            for post in load_blog_posts(
                pdir.name, include_drafts=True, include_archived=True
            )
        ]
    status_counts: dict[str, int] = {}
    for post in posts:
        status_counts[post.status] = status_counts.get(post.status, 0) + 1
    response.headers["ETag"] = _studio_etag(pdir)
    return StudioResponse(
        profile=pdir.name,
        initialized=initialized,
        summary=StudioSummaryModel(
            status_counts=status_counts,
            total_posts=len(posts),
        ),
        posts=posts,
        options=StudioOptionsModel(
            claims=_studio_claim_options(pdir.name),
            evidence=_studio_evidence_options(pdir.name),
            projects=_studio_project_options(pdir.name),
        ),
    )


STUDIO_MUTATION_RESPONSES = {
    **ERROR_RESPONSES,
    404: {
        "model": ErrorResponse,
        "description": "Profile or blog post not found.",
    },
    412: {
        "model": ErrorResponse,
        "description": "If-Match ETag does not match the studio source files.",
    },
    422: {
        "model": ErrorResponse,
        "description": (
            "Blank title, out-of-domain status, publish-readiness failure, "
            "invalid candidate target/source, or LLM-backed feature "
            "unavailable."
        ),
    },
}


@router.post(
    "/profiles/{name}/studio/init",
    response_model=StudioInitResponse,
    responses=STUDIO_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def init_profile_studio(
    name: str,
    response: Response,
    if_match: str | None = Header(default=None),
) -> StudioInitResponse | JSONResponse:
    """Initialize the profile's public layer (idempotent).

    Thin wrapper over ``core.public_site.init_public_layer``: existing
    files are never overwritten; ``created_paths`` lists what was actually
    created. Honors ``If-Match`` (412 on mismatch).
    """
    pdir = _resolve_profile(name)
    etag = _studio_etag(pdir)
    if not _if_match_satisfied(if_match, etag):
        return _studio_error(
            412,
            "etag_mismatch",
            "Public layer files changed since they were loaded; "
            "reload before initializing.",
            etag,
        )
    created = init_public_layer(pdir.name)
    response.headers["ETag"] = _studio_etag(pdir)
    return StudioInitResponse(ok=True, created_paths=[str(p) for p in created])


@router.get(
    "/profiles/{name}/studio/blog/{slug:path}",
    response_model=StudioPostDetailModel,
    responses=ERROR_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def get_profile_studio_post(
    name: str, slug: str, response: Response
) -> StudioPostDetailModel:
    """One blog post for the editor (meta + Markdown body).

    ``slug`` accepts the full route (``category/leaf``) or an unambiguous
    legacy leaf slug (same resolution as the core). The response carries the
    per-post ETag (Markdown + sidecar) for use as ``If-Match`` on save and
    publish.
    """
    pdir = _resolve_profile(name)
    post = _load_studio_post(pdir, slug)
    response.headers["ETag"] = _studio_post_etag(post)
    return _studio_post_detail(post)


def _apply_post_save(meta: dict, body: StudioPostSaveRequest) -> dict:
    """Merge the save-form fields onto the post's current front matter."""
    merged = dict(meta)
    for key, value in (
        ("title", body.title),
        ("date", body.date),
        ("status", body.status),
        ("summary", body.summary),
        ("cover", body.cover),
    ):
        if value is not None:
            merged[key] = value.strip()
    for key, value in (
        ("tags", body.tags),
        ("related_evidence", body.related_evidence),
        ("related_kanban", body.related_kanban),
        ("related_claims", body.related_claims),
        ("related_sources", body.related_sources),
        ("related_research_claims", body.related_research_claims),
        ("related_citations", body.related_citations),
    ):
        if value is not None:
            merged[key] = _string_list(value)
    return merged


def _require_post_status(value: str | None) -> str | None:
    """Validate the optional front-matter status against PUBLISH_STATUSES."""
    if value is None:
        return None
    clean = value.strip()
    if clean not in PUBLISH_STATUSES:
        raise ApiError(
            422,
            "invalid_blog_status",
            f"Status {value!r} is not valid "
            f"(expected one of: {', '.join(sorted(PUBLISH_STATUSES))}).",
        )
    return clean


@router.post(
    "/profiles/{name}/studio/blog",
    response_model=StudioPostMutationResponse,
    status_code=201,
    responses=STUDIO_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def create_profile_studio_post(
    name: str,
    body: StudioPostCreateRequest,
    response: Response,
    if_match: str | None = Header(default=None),
) -> StudioPostMutationResponse | JSONResponse:
    """Create one blog draft from a title (status starts as ``draft``).

    Mirrors the Streamlit "new blog draft" form: the slug is derived from
    today's date plus the title, with a taxonomy category prefix when the
    taxonomy is enabled. Honors ``If-Match`` (412 on mismatch).
    """
    pdir = _resolve_profile(name)
    etag = _studio_etag(pdir)
    if not _if_match_satisfied(if_match, etag):
        return _studio_error(
            412,
            "etag_mismatch",
            "Public layer files changed since they were loaded; "
            "reload before creating.",
            etag,
        )
    title = body.title.strip()
    if not title:
        raise ApiError(
            422, "invalid_blog_post", "Blog post title must not be blank."
        )
    try:
        path = create_blog_draft(
            pdir.name,
            title=title,
            body=body.body,
            tags=[tag.strip() for tag in body.tags if tag.strip()],
            summary=body.summary.strip(),
        )
    except PublicSiteError as exc:
        raise ApiError(422, "studio_create_failed", str(exc)) from exc
    post = parse_blog_post(path)
    response.headers["ETag"] = _studio_etag(pdir)
    return StudioPostMutationResponse(
        ok=True,
        post=_studio_post_detail(post),
        changed_paths=[str(path)],
    )


@router.post(
    "/profiles/{name}/studio/blog/{slug:path}/save",
    response_model=StudioPostMutationResponse,
    responses=STUDIO_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def save_profile_studio_post(
    name: str,
    slug: str,
    body: StudioPostSaveRequest,
    response: Response,
    if_match: str | None = Header(default=None),
) -> StudioPostMutationResponse | JSONResponse:
    """Save one blog post's front matter + Markdown body.

    ``None`` fields keep the current value; unknown front-matter keys are
    preserved. ``blocks_json`` is intentionally not accepted: the Markdown
    body is the source of truth in this slice and the BlockNote sidecar
    keeps its existing blocks (the BlockNote editor slice will write them).
    Honors ``If-Match`` (412 on mismatch, fresh ETag in the header).
    """
    pdir = _resolve_profile(name)
    post = _load_studio_post(pdir, slug)
    etag = _studio_post_etag(post)
    if not _if_match_satisfied(if_match, etag):
        return _studio_error(
            412,
            "etag_mismatch",
            "This blog post changed since it was loaded; reload before saving.",
            etag,
        )
    _require_post_status(body.status)
    if body.title is not None and not body.title.strip():
        raise ApiError(
            422, "invalid_blog_post", "Blog post title must not be blank."
        )
    meta = _apply_post_save(post.meta, body)
    text_body = post.body if body.body is None else body.body
    try:
        path, changed = save_blog_post(
            pdir.name,
            post.slug,
            meta,
            text_body,
            expected_snapshot=file_state.snapshot_file(post.path),
            expected_sidecar_snapshot=(
                file_state.snapshot_file(post.sidecar_path)
                if post.sidecar_path is not None
                else None
            ),
        )
    except file_state.FileConflictError:
        # A concurrent edit landed between the If-Match check and the
        # in-lock snapshot re-check (TOCTOU closure).
        return _studio_error(
            412,
            "etag_mismatch",
            "This blog post changed while saving; reload before retrying.",
            _studio_post_etag(post),
        )
    except PublicSiteError as exc:
        raise ApiError(422, "studio_save_failed", str(exc)) from exc
    fresh = parse_blog_post(path)
    response.headers["ETag"] = _studio_post_etag(fresh)
    return StudioPostMutationResponse(
        ok=True,
        post=_studio_post_detail(fresh),
        changed_paths=[str(path), *[str(item) for item in changed]],
    )


@router.post(
    "/profiles/{name}/studio/blog/{slug:path}/check",
    response_model=StudioValidationResponse,
    responses=STUDIO_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def check_profile_studio_post(
    name: str,
    slug: str,
    body: StudioPostSaveRequest | None = None,
) -> StudioValidationResponse:
    """Run the publish-readiness check on the (optionally edited) post.

    Accepts the same partial-save body so the SPA can validate unsaved
    edits; absent fields fall back to the on-disk document. Read-only —
    nothing is persisted.
    """
    pdir = _resolve_profile(name)
    post = _load_studio_post(pdir, slug)
    meta = dict(post.meta) if body is None else _apply_post_save(post.meta, body)
    text_body = post.body if body is None or body.body is None else body.body
    result = validate_blog_text_for_publish(
        pdir.name, post.path, format_blog_document(meta, text_body)
    )
    return StudioValidationResponse(
        ok=result.ok,
        errors=list(result.errors),
        warnings=list(result.warnings),
    )


@router.post(
    "/profiles/{name}/studio/blog/{slug:path}/publish",
    response_model=StudioPostMutationResponse,
    responses=STUDIO_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def publish_profile_studio_post(
    name: str,
    slug: str,
    response: Response,
    body: StudioPostSaveRequest | None = None,
    if_match: str | None = Header(default=None),
) -> StudioPostMutationResponse | JSONResponse:
    """Publish one blog post (full publish-readiness validation gate).

    Accepts the same partial-save body so unsaved editor content can be
    published in one call; validation failures answer 422
    (``blog_publish_blocked``) with the checker messages and write nothing.
    Honors ``If-Match`` (412 on mismatch, fresh ETag in the header).
    """
    pdir = _resolve_profile(name)
    post = _load_studio_post(pdir, slug)
    etag = _studio_post_etag(post)
    if not _if_match_satisfied(if_match, etag):
        return _studio_error(
            412,
            "etag_mismatch",
            "This blog post changed since it was loaded; "
            "reload before publishing.",
            etag,
        )
    meta = dict(post.meta) if body is None else _apply_post_save(post.meta, body)
    text_body = post.body if body is None or body.body is None else body.body
    try:
        path = publish_blog_text(
            pdir.name,
            post.slug,
            meta,
            text_body,
            expected_snapshot=file_state.snapshot_file(post.path),
            expected_sidecar_snapshot=(
                file_state.snapshot_file(post.sidecar_path)
                if post.sidecar_path is not None
                else None
            ),
        )
    except file_state.FileConflictError:
        # A concurrent edit landed between the If-Match check and the
        # in-lock snapshot re-check (TOCTOU closure).
        return _studio_error(
            412,
            "etag_mismatch",
            "This blog post changed while publishing; "
            "reload before retrying.",
            _studio_post_etag(post),
        )
    except PublicSiteError as exc:
        return _studio_error(
            422, "blog_publish_blocked", str(exc), _studio_post_etag(post)
        )
    fresh = parse_blog_post(path)
    response.headers["ETag"] = _studio_post_etag(fresh)
    return StudioPostMutationResponse(
        ok=True,
        post=_studio_post_detail(fresh),
        changed_paths=[str(path)],
    )


STUDIO_CANDIDATE_TARGETS = ("blog", "resume", "project")
STUDIO_CANDIDATE_SOURCES = ("claims", "evidence")


def _studio_candidate(name: str, body: StudioCandidateRequest) -> tuple[str, dict]:
    """Generate one candidate preview (rule-based with optional LLM polish).

    The core generators fall back to deterministic scaffolding when no LLM
    is configured, so this endpoint never requires a provider. Target/source
    combinations mirror the Streamlit form rules.
    """
    target = body.target.strip()
    source = body.source.strip()
    if target not in STUDIO_CANDIDATE_TARGETS:
        raise ApiError(
            422,
            "invalid_studio_target",
            f"Unknown output target {body.target!r} "
            f"(expected one of: {', '.join(STUDIO_CANDIDATE_TARGETS)}).",
        )
    if source not in STUDIO_CANDIDATE_SOURCES:
        raise ApiError(
            422,
            "invalid_studio_source",
            f"Unknown source {body.source!r} "
            f"(expected one of: {', '.join(STUDIO_CANDIDATE_SOURCES)}).",
        )
    claim_ids = [str(item).strip() for item in body.claim_ids if str(item).strip()]
    if target == "blog":
        if source == "claims":
            candidate = blog_candidate_from_claims(name, claim_ids)
        else:
            evidence_id = body.evidence_id.strip()
            if not evidence_id:
                raise ApiError(
                    422,
                    "invalid_studio_candidate",
                    "An evidence id is required for evidence-sourced drafts.",
                )
            candidate = blog_candidate_from_evidence(name, evidence_id)
        return "blog", candidate.to_dict()
    if source != "claims":
        raise ApiError(
            422,
            "invalid_studio_candidate",
            f"The {target} target only supports accepted claims as source.",
        )
    if target == "resume":
        bullets = resume_bullet_candidates_from_claims(name, claim_ids)
        return "resume", {
            "body": "\n".join(f"- {bullet.text}" for bullet in bullets),
            "bullets": [bullet.to_dict() for bullet in bullets],
        }
    project_id = body.project_id.strip()
    if not project_id:
        raise ApiError(
            422,
            "invalid_studio_candidate",
            "A project id is required for project update drafts.",
        )
    candidate = project_update_candidate_from_claims(name, project_id, claim_ids)
    return "project_update", candidate.to_dict()


@router.post(
    "/profiles/{name}/studio/candidates/preview",
    response_model=StudioCandidateResponse,
    responses=STUDIO_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def preview_profile_studio_candidate(
    name: str, body: StudioCandidateRequest
) -> StudioCandidateResponse:
    """Generate a candidate preview without writing anything.

    Mirrors the Streamlit "generate preview" step: the SPA shows the
    candidate and only the explicit create call persists a draft.
    """
    pdir = _resolve_profile(name)
    try:
        kind, candidate = _studio_candidate(pdir.name, body)
    except PublicSiteError as exc:
        raise ApiError(422, "studio_candidate_failed", str(exc)) from exc
    return StudioCandidateResponse(ok=True, kind=kind, candidate=candidate)


@router.post(
    "/profiles/{name}/studio/candidates/create",
    response_model=StudioDraftResponse,
    status_code=201,
    responses=STUDIO_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def create_profile_studio_draft(
    name: str,
    body: StudioCandidateRequest,
    response: Response,
    if_match: str | None = Header(default=None),
) -> StudioDraftResponse | JSONResponse:
    """Confirm a candidate into a persisted draft (blog or project update).

    Resume bullets are preview-only (they are pasted into resume-source.yaml
    by hand, same as the Streamlit page). The write is recorded to Agent
    Activity as a provenance writeback, mirroring the Streamlit flow.
    Honors ``If-Match`` (412 on mismatch).
    """
    pdir = _resolve_profile(name)
    etag = _studio_etag(pdir)
    if not _if_match_satisfied(if_match, etag):
        return _studio_error(
            412,
            "etag_mismatch",
            "Public layer files changed since they were loaded; "
            "reload before creating a draft.",
            etag,
        )
    try:
        kind, candidate = _studio_candidate(pdir.name, body)
    except PublicSiteError as exc:
        raise ApiError(422, "studio_candidate_failed", str(exc)) from exc
    if kind == "resume":
        raise ApiError(
            422,
            "studio_draft_preview_only",
            "Resume bullets are preview-only; paste them into "
            "resume-source.yaml manually.",
        )
    claim_ids = [str(item).strip() for item in body.claim_ids if str(item).strip()]
    try:
        if kind == "blog":
            if body.source.strip() == "claims":
                path = draft_blog_from_claims(pdir.name, claim_ids)
                refs = {"claim_refs": claim_ids}
                source_ref = "output_studio:blog_from_claims"
            else:
                evidence_id = body.evidence_id.strip()
                path = draft_blog_from_evidence(pdir.name, evidence_id)
                refs = {"evidence_refs": [evidence_id]}
                source_ref = "output_studio:blog_from_evidence"
        else:
            path = draft_project_update_from_claims(
                pdir.name, body.project_id.strip(), claim_ids
            )
            refs = {"claim_refs": claim_ids}
            source_ref = "output_studio:project_update_from_claims"
    except PublicSiteError as exc:
        raise ApiError(422, "studio_candidate_failed", str(exc)) from exc
    refs["files"] = [str(path)]
    record_writeback_activity(
        pdir.name,
        source_page="Output Studio",
        target_owner="public_site",
        candidate_type="public_draft",
        source_ref=source_ref,
        title="Output Studio blog draft"
        if kind == "blog"
        else "Output Studio project update",
        refs=refs,
        payload={"kind": kind, "candidate": candidate},
        changed_paths=[path],
        status="applied",
    )
    slug = parse_blog_post(path).slug if kind == "blog" else ""
    response.headers["ETag"] = _studio_etag(pdir)
    return StudioDraftResponse(
        ok=True,
        kind=kind,
        path=str(path),
        slug=slug,
        warnings=_string_list(candidate.get("warnings")),
    )


@router.post(
    "/profiles/{name}/studio/jd-match",
    response_model=StudioJdMatchResponse,
    responses=STUDIO_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def analyze_profile_studio_jd_match(
    name: str, body: StudioJdMatchRequest
) -> StudioJdMatchResponse:
    """JD match analysis for one resume text (LLM-backed, synchronous).

    Answers 422 (``studio_jd_match_unavailable``) when no LLM backend is
    configured, so the SPA can show a degradation card instead of the
    analysis — same degradation contract as the other LLM slices. A failed
    provider call (core returns an error string, never raises) answers 422
    ``studio_jd_match_failed``. Nothing is persisted.
    """
    pdir = _resolve_profile(name)
    if not llm_client.is_configured():
        raise ApiError(
            422,
            "studio_jd_match_unavailable",
            "JD match analysis requires a configured LLM backend "
            "(set LLM_API_KEY / LLM_BASE_URL); the rest of the studio "
            "works without it.",
        )
    resume_md = body.resume_md.strip()
    jd_text = body.jd_text.strip()
    if not resume_md or not jd_text:
        raise ApiError(
            422,
            "invalid_jd_match_request",
            "Both resume_md and jd_text are required.",
        )
    analysis = jd_match.analyze_jd(pdir.name, resume_md=resume_md, jd_text=jd_text)
    if analysis.startswith(("LLM error:", "AI features")):
        raise ApiError(422, "studio_jd_match_failed", analysis)
    return StudioJdMatchResponse(ok=True, analysis=analysis)


# --- Home + Research (M4): overview reads and sidecar cohesion ----------------


_SIDECAR_DISABLE_SENTINELS = {"0", "false", "off", "none"}
_SIDECAR_DEFAULT_BASE = "http://127.0.0.1:8502"

# Statuses that count as "in flight" on the research source inbox (mirrors
# core.home_dashboard.dashboard_source_summary).
_RESEARCH_ACTIVE_STATUSES = ("inbox", "reading", "summarized", "candidate_ready")


def _sidecar_info(name: str, user: CurrentUser) -> SidecarInfoModel:
    """Resolve the browser-facing Reader API sidecar coordinates.

    Mirrors ``research_ui._helpers._reader_api_base``: env override
    (``NBLANE_READER_API_BASE`` / ``NBLANE_PAPER_LIBRARY_BASE``), the
    same-origin sentinel values resolving to an empty base (production
    single-port deployment), and the ``http://127.0.0.1:8502`` default. The
    handoff token bootstraps the sidecar session cookie for iframe embeds
    when auth is on; it stays empty in the default auth-off local mode.

    Token hygiene: a fresh 60s token is minted per response (only when
    sidecar auth is on) and the SPA exchanges it via a hidden form POST to
    the sidecar's ``/auth/session``. Residual risk, deferred to the sidecar:
    tokens are replayable within their TTL and the sidecar still accepts the
    token via URL query (which lands in proxy access logs and browser
    history) — the one-time, POST-only exchange is sidecar-side follow-up
    work.
    """
    raw = (
        os.getenv("NBLANE_READER_API_BASE", "").strip()
        or os.getenv("NBLANE_PAPER_LIBRARY_BASE", "").strip()
    )
    configured = bool(raw)
    if raw.lower() in _SIDECAR_DISABLE_SENTINELS:
        base = ""
    else:
        base = (raw or _SIDECAR_DEFAULT_BASE).rstrip("/")
    auth_on = auth_core.auth_configured()
    handoff = ""
    if auth_on:
        try:
            handoff = auth_core.mint_auth_handoff_token(user.id)
        except auth_core.AuthConfigError:
            handoff = ""
    query = urlencode({"profile": name})
    return SidecarInfoModel(
        base=base,
        configured=configured,
        auth_enabled=auth_on,
        handoff_token=handoff,
        paper_library_url=f"{base}/paper-library?{query}",
        dashboard_url=f"{base}/dashboard?{query}&embed=1",
    )


def _north_star_model(pdir: Path) -> NorthStarModel:
    """Owner-facing North Star (same projection as the goals endpoint)."""
    identity = parse_identity_fields(profile_io.load_skill_md(pdir.name))
    full = str(identity.get("North Star", "") or "").strip()
    brief = str(identity.get("North Star Brief", "") or "").strip()
    return NorthStarModel(
        visibility=normalize_north_star_visibility(
            identity.get("North Star Visibility")
        ),
        is_set=bool(full or brief),
        full=full,
        brief=brief,
    )


@router.get(
    "/profiles/{name}/home",
    response_model=HomeResponse,
    responses=ERROR_RESPONSES,
)
def get_profile_home(
    name: str, user: CurrentUser = Depends(require_profile_access)
) -> HomeResponse:
    """Home dashboard overview: aggregated profile snapshot (read-only).

    Composes the ``core.home_dashboard`` sub-summaries — the same pure-read
    aggregation behind the sidecar 3D dashboard payload — without the
    payload builder's snapshot-recording side effect, so this GET never
    writes. Goal progress comes from ``dashboard_goal_progress`` (Goal →
    Project → Task completion, zero manual entry). ``sidecar`` carries the
    coordinates for the optional embedded 3D dashboard iframe.
    ``sidecar.handoff_token`` is a fresh 60s bootstrap token minted per
    response (empty when sidecar auth is off); it is replayable within its
    TTL and the sidecar still accepts it via URL query — see
    ``_sidecar_info`` for the residual-risk note.
    """
    pdir = _resolve_profile(name)
    kanban = home_dashboard.dashboard_kanban_summary(pdir)
    skills = home_dashboard.dashboard_skill_summary(pdir)
    pending = home_dashboard.dashboard_pending_evidence_summary(pdir)
    sources = home_dashboard.dashboard_source_summary(pdir)
    projects = home_dashboard.dashboard_project_summary(pdir)
    claims = home_dashboard.dashboard_claim_summary(pdir)
    health = home_dashboard.dashboard_health_summary(pdir)
    activity = home_dashboard.dashboard_agent_activity_summary(pdir)
    progress_map = home_dashboard.dashboard_goal_progress(pdir, kanban=kanban)

    book = load_goal_book(pdir)
    primary = book.primary()
    primary_goal: HomeGoalModel | None = None
    if primary is not None:
        progress = progress_map.get(primary.id) or {}
        primary_goal = HomeGoalModel(
            id=primary.id,
            title=primary.title,
            label=primary.label,
            status=primary.status,
            target=primary.target,
            progress=progress.get("progress"),
            stalled=bool(progress.get("stalled", False)),
            project_count=int(progress.get("project_count", 0) or 0),
        )

    project_status_counts: dict[str, int] = {}
    for case in projects.get("cases") or []:
        status = str(case.get("status") or "")
        project_status_counts[status] = project_status_counts.get(status, 0) + 1

    return HomeResponse(
        profile=pdir.name,
        north_star=_north_star_model(pdir),
        primary_goal=primary_goal,
        goal_counts={"active": len(book.active_goals()), "total": len(book.goals)},
        skills=HomeSkillsModel(
            has_tree=bool(skills.get("has_tree")),
            schema_name=str(skills.get("schema") or ""),
            total=int(skills.get("total", 0) or 0),
            lit=int(skills.get("lit", 0) or 0),
            lit_rate=float(skills.get("lit_rate", 0.0) or 0.0),
            counts=dict(skills.get("counts") or {}),
            evidence_risk_count=int(skills.get("evidence_risk_count", 0) or 0),
        ),
        kanban=HomeKanbanModel(
            counts=dict(kanban.get("counts") or {}),
            doing_total=int(kanban.get("doing_total", 0) or 0),
            done_uncrystallized_count=int(
                kanban.get("done_uncrystallized_count", 0) or 0
            ),
            doing=[
                HomeKanbanTaskModel(
                    id=str(item.get("id") or ""),
                    title=str(item.get("title") or ""),
                    started_on=str(item.get("started_on") or ""),
                )
                for item in kanban.get("doing") or []
            ],
        ),
        evidence=HomeEvidenceModel(
            total_entries=int(pending.get("total_entries", 0) or 0),
            unlinked_count=int(pending.get("unlinked_count", 0) or 0),
            needs_review_count=int(pending.get("needs_review_count", 0) or 0),
            status_risk_count=int(pending.get("status_risk_count", 0) or 0),
            done_uncrystallized_count=int(
                pending.get("done_uncrystallized_count", 0) or 0
            ),
        ),
        sources=HomeSourcesModel(
            implemented=bool(sources.get("implemented")),
            total=int(sources.get("source_inbox_total", 0) or 0),
            active_total=int(sources.get("active_total", 0) or 0),
            status_counts=dict(sources.get("status_counts") or {}),
            active_titles=[str(t) for t in sources.get("active_titles") or []],
        ),
        projects=HomeProjectsModel(
            total=len(projects.get("cases") or []),
            status_counts=project_status_counts,
        ),
        claims=HomeClaimsModel(
            total=int(claims.get("total", 0) or 0),
            accepted_count=int(claims.get("accepted_count", 0) or 0),
            draft_count=int(claims.get("draft_count", 0) or 0),
            needs_refresh_count=int(claims.get("needs_refresh_count", 0) or 0),
        ),
        agent_activity=HomeAgentActivityModel(
            total=int(activity.get("total", 0) or 0),
            pending_total=int(activity.get("pending_total", 0) or 0),
            pending_titles=[str(t) for t in activity.get("pending_titles") or []],
        ),
        health=HomeHealthModel(
            counts=dict(health.get("counts") or {}),
            context_ready=bool(health.get("context_ready", True)),
        ),
        sidecar=_sidecar_info(pdir.name, user),
    )


@router.get(
    "/profiles/{name}/research",
    response_model=ResearchResponse,
    responses=ERROR_RESPONSES,
)
def get_profile_research(
    name: str, user: CurrentUser = Depends(require_profile_access)
) -> ResearchResponse:
    """Research overview: source-inbox summary plus sidecar entry points.

    The PDF reader and Paper Library stay on the Reader API sidecar; this
    endpoint gives the SPA Research page its summary data (source counts by
    status/kind, research claims/citations counters, recent sources) and
    the sidecar coordinates for the link/iframe entries. Read-only.
    ``sidecar.handoff_token`` is a fresh 60s bootstrap token minted per
    response (empty when sidecar auth is off); it is replayable within its
    TTL and the sidecar still accepts it via URL query — see
    ``_sidecar_info`` for the residual-risk note.
    """
    pdir = _resolve_profile(name)
    inbox = load_research_sources(pdir)
    claims = load_research_claims(pdir)
    citations = load_research_citations(pdir)

    status_counts: dict[str, int] = {}
    kind_counts: dict[str, int] = {}
    for source in inbox.sources:
        status_counts[source.status] = status_counts.get(source.status, 0) + 1
        kind_counts[source.kind] = kind_counts.get(source.kind, 0) + 1
    active_total = sum(status_counts.get(s, 0) for s in _RESEARCH_ACTIVE_STATUSES)

    recent = sorted(
        (s for s in inbox.sources if s.id),
        key=lambda s: (s.captured_at, s.id),
        reverse=True,
    )[:8]

    return ResearchResponse(
        profile=pdir.name,
        summary=ResearchSummaryModel(
            total=len(inbox.sources),
            active_total=active_total,
            status_counts=status_counts,
            kind_counts=kind_counts,
            claims_total=len(claims),
            citations_total=len(citations),
        ),
        sources=[
            ResearchSourceItemModel(
                id=source.id,
                title=source.title,
                kind=source.kind,
                status=source.status,
                url=source.url,
                captured_at=source.captured_at,
                tags=list(source.tags),
                summary=source.summary,
            )
            for source in recent
        ],
        sidecar=_sidecar_info(pdir.name, user),
    )


async def api_error_handler(_request: Request, exc: ApiError) -> JSONResponse:
    """Serialize ApiError into the ErrorResponse model."""
    body = ErrorResponse(code=exc.code, message=exc.message)
    return JSONResponse(status_code=exc.status_code, content=body.model_dump())


async def validation_error_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Serialize pydantic request-validation failures as ErrorResponse.

    Keeps the 422 body shape identical to ApiError responses
    (``{code, message}``) instead of FastAPI's default ``{"detail": [...]}``.
    """
    details: list[str] = []
    for error in exc.errors()[:5]:
        loc = ".".join(
            str(part)
            for part in error.get("loc", ())
            if part not in ("body", "query", "path")
        )
        details.append(f"{loc or 'request'}: {error.get('msg', 'invalid')}")
    message = "; ".join(details) or "Request validation failed."
    body = ErrorResponse(code="validation_error", message=message)
    return JSONResponse(status_code=422, content=body.model_dump())
