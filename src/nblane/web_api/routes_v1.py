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

import asyncio
import hashlib
import importlib.metadata
import logging
import os
import re
import uuid
from dataclasses import replace
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Header, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse

from nblane.core import agent_activity, agent_tasks, file_state, gap, inbox
from nblane.core import chronicle as chronicle_core
from nblane.core import north_star as north_star_core
from nblane.core import evidence_review as evidence_review_core
from nblane.core import activity_log, home_dashboard, jd_match, learning_log, task_intake
from nblane.core import auth as auth_core
from nblane.core import plan_templates, profile_io, project_suggest, projects_board, schema_io
from nblane.core import skill_progression as skill_progression_core
from nblane.core import starmap_snapshot as starmap_snapshot_core
from nblane.core import divination as divination_core
from nblane.core.claims import accepted_claims_for_profile
from nblane.core.evidence_resolve import resolve_node_evidence_dict
from nblane.core.experience import load_experience_book
from nblane.core.goals import (
    Goal,
    load_goal_book,
    next_goal_id,
    save_goal_book,
)
from nblane.core.kanban_archive import _archive_tasks, find_kanban_tasks_by_ref
from nblane.core.kanban_io import (
    KANBAN_ARCHIVE_FILENAME,
    KANBAN_DOING,
    KANBAN_DONE,
    KANBAN_QUEUE,
    KANBAN_SECTIONS,
    apply_kanban_reorder,
    ensure_kanban_task_ids,
    find_kanban_card,
    find_kanban_card_by_id,
    kanban_path,
    parse_kanban,
    parse_kanban_archive,
    resolve_kanban_section,
    update_kanban,
)
from nblane.core.kanban_merge import copy_kanban_sections, save_kanban_with_merge
from nblane.core import llm as llm_client
from nblane.core import crystallize as crystallize_core
from nblane.core.ai import skill_suggest
from nblane.core.models import (
    EVIDENCE_CONFIDENCES,
    EVIDENCE_PUBLIC_READINESS,
    EVIDENCE_REVIEW_STATUSES,
    EVIDENCE_STRENGTHS,
    EVIDENCE_TYPES,
    EvidenceRecord,
    KanbanTask,
    KanbanTodo,
)
from nblane.core.growth_review import build_weekly_review
from nblane.core.public_curation import evidence_contexts
from nblane.core.paths import REPO_ROOT, SCHEMAS_DIR
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
    build_public_site,
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
    publish_blog_post,
    publish_blog_text,
    render_public_site_pages,
    render_public_site_preview,
    resume_bullet_candidates_from_claims,
    save_blog_post,
    validate_blog_text_for_publish,
    validate_public_layer,
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
    update_project_board,
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
from nblane.web_api import jobs
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
    CheckinCreateRequest,
    CheckinDeleteResponse,
    CheckinModel,
    CheckinMutationResponse,
    ChronicleEntryModel,
    ChronicleResponse,
    ErrorResponse,
    EvidenceEntryDetailModel,
    EvidenceEntryModel,
    EvidenceEditRequest,
    EvidenceEntryActionRequest,
    EvidenceListResponse,
    EvidenceReviewBulkRequest,
    EvidenceReviewDeprecateRequest,
    EvidenceReviewItemModel,
    EvidenceReviewListResponse,
    EvidenceReviewMutationResponse,
    EvidenceReviewSummaryModel,
    EvidenceSkillLinksRequest,
    EvidenceSkillLinksResponse,
    EvidenceSkillSuggestionModel,
    EvidenceSkillSuggestionsResponse,
    EvidenceStageRiskModel,
    EvidenceStagesResponse,
    CrystallizeApplyRequest,
    CrystallizeApplyResponse,
    CrystallizeCandidatesResponse,
    CrystallizeCandidateModel,
    CrystallizeDraftRequest,
    CrystallizeDraftResponse,
    CrystallizeTaskModel,
    DivinationRequest,
    DivinationResponse,
    ProvenanceRefModel,
    EvidenceSummary,
    GapAnalysisResponse,
    GapAnalyzeRequest,
    GapIntakeRequest,
    GoalModel,
    GoalCreateRequest,
    GoalMutationResponse,
    GoalPatchRequest,
    GoalSummary,
    GoalsResponse,
    HabitArchiveRequest,
    HabitArchiveResponse,
    HabitDeleteRequest,
    HabitDeleteResponse,
    HabitPlanCreateRequest,
    HabitPlanListResponse,
    HabitPlanModel,
    HabitPlanMutationResponse,
    HabitPlanPatchRequest,
    HabitPlanWeekProgressModel,
    HabitPlanWeeklyTasksModel,
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
    JobCreateRequest,
    JobCreateResponse,
    JobModel,
    JobStatusResponse,
    KanbanBoardResponse,
    KanbanCardCreateRequest,
    KanbanCardDeleteRequest,
    KanbanCardDeleteResponse,
    KanbanCardMoveRequest,
    KanbanCardPatchRequest,
    KanbanCardScheduleRequest,
    KanbanMutationResponse,
    KanbanSectionModel,
    KanbanSubtaskModel,
    KanbanTodoModel,
    KanbanSummary,
    KanbanTaskModel,
    NorthStarModel,
    NorthStarMutationResponse,
    NorthStarPatchRequest,
    PlanTemplateHabitModel,
    PlanTemplateInstantiateRequest,
    PlanTemplateInstantiateResponse,
    PlanTemplateListResponse,
    PlanTemplateMilestoneModel,
    PlanTemplateModel,
    PlanTemplateUsageModel,
    ProfileDetailSummary,
    ProfileSummary,
    ProjectBoardOptionsModel,
    ProjectBoardResponse,
    ProjectBoardSummaryModel,
    ProjectCaseCreateRequest,
    ProjectCaseDeleteRequest,
    ProjectCaseDeleteResponse,
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
    ProjectsBoardGoalModel,
    ProjectsBoardHabitDayModel,
    ProjectsBoardHabitModel,
    ProjectsBoardHabitRecentDayModel,
    ProjectsBoardMilestoneModel,
    ProjectsBoardProjectModel,
    ProjectsBoardResponse,
    ProjectsBoardTaskModel,
    PublicBuildArtifactModel,
    PublicBuildDraftModel,
    PublicBuildPreviewPageModel,
    PublicBuildPreviewResponse,
    PublicBuildPublishRequest,
    PublicBuildRequest,
    PublicBuildResponse,
    PublicBuildResultResponse,
    PublicBuildStateModel,
    PublicBuildValidationModel,
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
    SkillNodePatchRequest,
    SkillNodePatchResponse,
    SkillNodeProgressModel,
    SkillTreeCategoryModel,
    SkillTreeNodeModel,
    SkillTreeResponse,
    SkillTreeSummary,
    StarmapCategoryModel,
    StarmapCountsModel,
    StarmapEvidenceModel,
    StarmapGoalModel,
    StarmapProjectModel,
    StarmapResponse,
    StarmapSkillModel,
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

_logger = logging.getLogger(__name__)


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


AGENT_ACCOUNT_ID = "openclaw"


def _record_agent_writeback(
    user: CurrentUser,
    profile: str,
    *,
    action: str,
    note: str,
    target_owner: str = "profile_context",
    refs: dict[str, Any] | None = None,
    changed_paths: list[str | Path] | None = None,
) -> None:
    """Trace one completed agent-account mutation in agent-activity.yaml (G1).

    Fires only when the caller is the ``openclaw`` service account — the
    agent write contract (home-editing-starmap-design §7) makes
    agent-activity.yaml the audit book for agent writes, and direct API
    mutations would otherwise leave no trace. Extension path for further
    non-human accounts: widen the id check (e.g. a role/member predicate).

    Callers invoke this only on the path where the mutation actually
    changed something (the routes keep their no-op discipline). The trace
    is best-effort: the mutation's own writes already landed, so a trace
    failure is logged, never raised into a completed mutation's response.
    """
    if user.id != AGENT_ACCOUNT_ID:
        return
    try:
        record_writeback_activity(
            profile,
            source_page=AGENT_ACCOUNT_ID,
            target_owner=target_owner,
            candidate_type=action,
            # A unique suffix keeps each mutation a distinct entry (the
            # writeback id is a digest of these fields; Review/Studio flows
            # rely on digest stability for idempotent re-recording, agent
            # mutations need the opposite).
            source_ref=f"{AGENT_ACCOUNT_ID}:{action}:{uuid.uuid4().hex[:10]}",
            title=note,
            refs=refs,
            changed_paths=changed_paths,
            status="applied",
        )
    except Exception:
        _logger.warning(
            "agent writeback trace failed for %s on %s",
            action,
            profile,
            exc_info=True,
        )


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
def get_profile_skill_tree(name: str, response: Response) -> SkillTreeResponse:
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
            category=str(meta.category if meta else ""),
            evidence_count=len(resolve_node_evidence_dict(node, pool)),
            progress=SkillNodeProgressModel(
                **skill_progression_core.node_progress(node, pool).to_dict()
            ),
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

    # Per-category rollup for the banner headers: zh display name from the
    # same CATEGORY_ZH table the starmap sector band uses (so the SPA's
    # 官名 lookup keys match), 点亮 = solid+expert (LIT_STATUSES), locked is
    # derived client-side as count − lit − learning.
    category_of: dict[str, str] = {
        nid: str(schema_index[nid].category or "") if nid in schema_index else ""
        for nid in overlay
    }
    cat_order: list[str] = []
    for nid in sorted(overlay, key=lambda x: order.get(x, 0)):
        cat = category_of[nid]
        if cat not in cat_order:
            cat_order.append(cat)
    categories: list[SkillTreeCategoryModel] = []
    for cat in cat_order:
        members = [nid for nid in overlay if category_of[nid] == cat]
        statuses = [str(overlay[nid].get("status") or "locked") for nid in members]
        categories.append(
            SkillTreeCategoryModel(
                id=cat,
                name=starmap_snapshot_core.CATEGORY_ZH.get(cat, cat),
                count=len(members),
                lit_count=sum(1 for s in statuses if s in starmap_snapshot_core.LIT_STATUSES),
                learning_count=sum(1 for s in statuses if s == "learning"),
            )
        )

    response.headers["ETag"] = _skill_tree_etag(pdir)
    return SkillTreeResponse(
        profile=pdir.name,
        schema_name=schema_name,
        updated=str(raw.get("updated") or ""),
        status_counts=count_nodes(raw),
        nodes=nodes,
        categories=categories,
    )


# 三态 (UI/starmap) → skill-tree.yaml status mapping. locked=空圈 → locked,
# learning=实点 → learning, lit=点套圈 → solid. The YAML also knows `expert`
# (精通) — a review-earned rung above 点亮 that this endpoint never writes;
# patching an expert node to "lit" steps it down to solid.
SKILL_NODE_EDIT_STATUSES = ("locked", "learning", "lit")
_SKILL_NODE_STATUS_TO_YAML = {"locked": "locked", "learning": "learning", "lit": "solid"}

SKILL_NODE_MUTATION_RESPONSES = {
    **ERROR_RESPONSES,
    404: {
        "model": ErrorResponse,
        "description": "Profile or skill node not found.",
    },
    412: {
        "model": ErrorResponse,
        "description": "If-Match ETag does not match skill-tree.yaml.",
    },
    422: {
        "model": ErrorResponse,
        "description": "Status outside the 三态 vocabulary (locked/learning/lit).",
    },
}


@router.patch(
    "/profiles/{name}/skill-tree/nodes/{node_id}",
    response_model=SkillNodePatchResponse,
    responses=SKILL_NODE_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def patch_profile_skill_node(
    name: str,
    node_id: str,
    body: SkillNodePatchRequest,
    response: Response,
    if_match: str | None = Header(default=None),
    user: CurrentUser = Depends(require_user),
) -> SkillNodePatchResponse | JSONResponse:
    """Set one skill node's 三态 status in skill-tree.yaml (G3 write).

    Body vocabulary is the UI 三态 (``locked`` / ``learning`` / ``lit``);
    ``lit`` lands as the YAML status ``solid`` (see
    ``SKILL_NODE_EDIT_STATUSES``). ``If-Match`` carries the skill-tree.yaml
    ETag from the tree read (412 on mismatch); the write goes through
    ``profile_io.update_skill_tree`` with an in-lock snapshot re-check, and
    the SKILL.md generated block is re-synced after a real change. A no-op
    patch writes nothing (``changed=false``).
    """
    pdir = _resolve_profile(name)
    etag = _skill_tree_etag(pdir)
    if not _if_match_satisfied(if_match, etag):
        return _evidence_review_error(
            412,
            "etag_mismatch",
            "技能树已被其他改动更新,正在为你刷新;请重试。",
            etag,
        )
    clean = body.status.strip().lower()
    if clean not in _SKILL_NODE_STATUS_TO_YAML:
        raise ApiError(
            422,
            "invalid_skill_status",
            f"status must be one of {', '.join(SKILL_NODE_EDIT_STATUSES)}, "
            f"got {body.status!r}.",
        )
    yaml_status = _SKILL_NODE_STATUS_TO_YAML[clean]
    nid = node_id.strip()
    raw = profile_io.load_skill_tree_raw(pdir) or {}
    node = next(
        (
            item
            for item in (raw.get("nodes") or [])
            if isinstance(item, dict) and str(item.get("id", "") or "").strip() == nid
        ),
        None,
    )
    if node is None:
        raise ApiError(
            404, "skill_node_not_found", f"Unknown skill node: {nid}"
        )
    previous = str(node.get("status") or "locked")
    changed = previous != yaml_status
    if changed:

        def _apply(doc: dict[str, Any]) -> None:
            for item in doc.get("nodes") or []:
                if (
                    isinstance(item, dict)
                    and str(item.get("id", "") or "").strip() == nid
                ):
                    item["status"] = yaml_status
            doc["profile"] = pdir.name

        try:
            profile_io.update_skill_tree(
                pdir.name,
                _apply,
                expected_snapshot=file_state.snapshot_file(
                    pdir / profile_io.SKILL_TREE_FILENAME
                ),
            )
        except file_state.FileConflictError:
            return _evidence_review_error(
                412,
                "etag_mismatch",
                "技能树在写入期间被其他改动更新,请重试。",
                _skill_tree_etag(pdir),
            )
        if (pdir / "SKILL.md").exists():
            write_generated_blocks(pdir)
        # Rung-ups are narrative events; downgrades/no-ops are not. The
        # note carries the schema label (id as fallback) for the briefing
        # line and rubbings.
        if skill_progression_core.rung_index(
            yaml_status
        ) > skill_progression_core.rung_index(previous):
            note = nid
            schema = (
                schema_io.load_schema(schema_name)
                if (schema_name := str(raw.get("schema") or ""))
                else None
            )
            if schema is not None and nid in schema.node_index():
                note = schema.node_index()[nid].label or nid
            _append_chronicle_entry(
                pdir,
                "skill.lit",
                ref=nid,
                note=note,
                snapshot=file_state.snapshot_file(
                    pdir / chronicle_core.CHRONICLE_FILENAME
                ),
            )
        trace_paths = [pdir / profile_io.SKILL_TREE_FILENAME]
        if (pdir / "SKILL.md").exists():
            trace_paths.append(pdir / "SKILL.md")
        _record_agent_writeback(
            user,
            pdir.name,
            action="skill_node.patch",
            target_owner="skill_tree",
            note=f"skill node {nid}: {previous} → {yaml_status}",
            refs={
                "node_id": nid,
                "previous_status": previous,
                "status": yaml_status,
            },
            changed_paths=trace_paths,
        )
    response.headers["ETag"] = _skill_tree_etag(pdir)
    return SkillNodePatchResponse(
        ok=True,
        node_id=nid,
        status=yaml_status,
        previous_status=previous,
        changed=changed,
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
        planned_start=task.planned_start,
        planned_end=task.planned_end,
        crystallized=task.crystallized,
        project_id=task.project_id,
        milestone_id=task.milestone_id,
        agent_task_id=task.agent_task_id,
        tags=task.tags,
        subtasks=[
            KanbanSubtaskModel(title=st.title, done=st.done)
            for st in task.subtasks
        ],
        todos=[
            KanbanTodoModel(text=todo.text, done=todo.done)
            for todo in task.todos
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
    as ``If-Match`` on the card mutations. The ``archive`` field lists Done
    tasks archived to kanban-archive.md; the archive file is intentionally
    outside the ETag fingerprint (it is append-only and never mutated via
    If-Match), so archiving does not invalidate a client's kanban.md ETag.
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
    archive = [
        _kanban_task_model(task) for task in parse_kanban_archive(pdir)
    ]
    response.headers["ETag"] = _kanban_etag(pdir)
    return KanbanBoardResponse(
        profile=pdir.name,
        sections=out,
        total=total,
        archive=archive,
    )


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


def _validate_planned_date(value: str, field: str) -> str:
    """Return a clean ISO date or raise ApiError(422) for bad input."""
    clean = value.strip()
    if not clean:
        return ""
    try:
        return date.fromisoformat(clean).isoformat()
    except ValueError:
        raise ApiError(
            422,
            "invalid_planned_date",
            f"Field {field} must be an ISO date (YYYY-MM-DD), got "
            f"{value!r}.",
        ) from None


def _check_planned_range(start: str, end: str) -> None:
    """422 when both planned dates are set and start is after end."""
    if start and end and start > end:
        raise ApiError(
            422,
            "invalid_planned_range",
            f"planned_start {start} is after planned_end {end}.",
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


def _resolve_kanban_card(
    sections: dict[str, list[KanbanTask]],
    card_ref: str,
) -> tuple[tuple[str, int, KanbanTask] | None, str, str]:
    """Resolve a ``card_ref`` path segment: task id first, then title.

    Card ids (``kb_`` + hex) are URL-safe, so id addressing survives titles
    containing ``/`` — a title-only ref would be split by route parsing and
    never reach the endpoint (405). When the ref is not an existing id the
    lookup falls back to ``find_kanban_card`` (exact title or unique
    substring), keeping the documented title semantics intact.
    """
    by_id = find_kanban_card_by_id(sections, card_ref)
    if by_id is not None:
        return by_id, "", ""
    return find_kanban_card(sections, card_ref)


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
    user: CurrentUser = Depends(require_user),
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
    planned_start = _validate_planned_date(body.planned_start, "planned_start")
    planned_end = _validate_planned_date(body.planned_end, "planned_end")
    _check_planned_range(planned_start, planned_end)
    task = KanbanTask(
        title=title,
        context=body.context.strip(),
        tags=tags,
        planned_start=planned_start or None,
        planned_end=planned_end or None,
    )
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
    _record_agent_writeback(
        user,
        pdir.name,
        action="kanban.card.add",
        target_owner="kanban",
        note=f"kanban add: {title!r} → {section}",
        refs={"card_id": stored.id, "section": section},
        changed_paths=[kanban_path(pdir)],
    )
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
    user: CurrentUser,
    action: str,
    to_index: int | None = None,
) -> KanbanMutationResponse | JSONResponse:
    """Shared move/done mutation: relocate one card to *target*.

    ``card_ref`` is the card's task id (preferred — URL-safe even when the
    title contains ``/``), falling back to an exact title or unique
    substring (same semantics as the Review kanban-move candidate). The
    move reuses
    ``apply_kanban_reorder(auto_dates=True)``, so landing in Done marks the
    card done with ``completed_on`` and leaving Done clears both.
    ``to_index`` (0-based, post-removal) positions the card inside the
    target column; ``None`` appends to the tail. Out-of-range values clamp
    to the column head/tail (core reorder semantics, never a 422). A move
    to the current section without ``to_index`` is an idempotent no-op.
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
    hit, match_kind, match_error = _resolve_kanban_card(sections, ref)
    if hit is None:
        if match_kind == "ambiguous":
            raise ApiError(422, "kanban_card_ambiguous", match_error)
        raise ApiError(404, "kanban_card_not_found", match_error)
    from_section, _index, task = hit
    warnings: list[str] = []
    no_op = from_section == target and to_index is None
    if no_op:
        warnings.append(
            f"card {task.title.strip()!r} is already in {target!r}; "
            "no move needed"
        )
        moved = sections
    else:
        moved = apply_kanban_reorder(
            sections,
            [{"id": task.id, "to_section": target, "to_index": to_index}],
            auto_dates=True,
        )
    result = _save_kanban_mutation(pdir, moved, base, snapshot)
    section, stored = _find_card_by_id(result.sections, task.id)
    if not no_op:
        _record_agent_writeback(
            user,
            pdir.name,
            action=action,
            target_owner="kanban",
            note=f"{action}: {task.title.strip()!r} → {section}",
            refs={"card_id": task.id, "from_section": from_section,
                  "section": section},
            changed_paths=[kanban_path(pdir)],
        )
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
    user: CurrentUser = Depends(require_user),
) -> KanbanMutationResponse | JSONResponse:
    """Move one card to ``target_section``. Honors ``If-Match`` (412).

    ``to_index`` (optional, 0-based, post-removal) positions the card
    inside the target column — including in-column reorders when
    ``target_section`` is the card's current section. Omitting it appends
    to the column tail; out-of-range values clamp (never a 422).
    """
    target = resolve_kanban_section(body.target_section)
    if target is None:
        raise _unknown_kanban_section(body.target_section)
    return _mutate_kanban_card_section(
        name, card_ref, target, response, if_match, user, "kanban.card.move",
        body.to_index,
    )


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
    user: CurrentUser = Depends(require_user),
) -> KanbanMutationResponse | JSONResponse:
    """Mark one card done by moving it to Done (done flag + completed_on).

    The Done transition is the board's column-move idiom
    (``apply_kanban_reorder`` with ``auto_dates``), so a card already in
    Done answers 200 with an "already there" warning. Honors ``If-Match``.
    """
    return _mutate_kanban_card_section(
        name, card_ref, KANBAN_DONE, response, if_match, user,
        "kanban.card.done",
    )


@router.post(
    "/profiles/{name}/kanban/cards/{card_ref}/schedule",
    response_model=KanbanMutationResponse,
    responses=KANBAN_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def schedule_profile_kanban_card(
    name: str,
    card_ref: str,
    body: KanbanCardScheduleRequest,
    response: Response,
    if_match: str | None = Header(default=None),
    user: CurrentUser = Depends(require_user),
) -> KanbanMutationResponse | JSONResponse:
    """Set or clear one card's planned date range (timeline drag-to-reschedule).

    ``planned_start`` / ``planned_end`` accept an ISO ``YYYY-MM-DD`` date to
    set, ``""`` to clear, or are omitted (``null``) to keep the current
    value; both set means start must not be after end (422 otherwise). The
    fields persist as kanban.md metadata bullets, orthogonal to the
    column-date idiom (``started_on`` / ``completed_on``). ``card_ref``
    is the task id first (URL-safe; survives titles containing ``/``),
    then the move/done fallback semantics: exact card title or unique
    title substring. Honors
    ``If-Match`` (412 on mismatch); a concurrent write between parse and
    save is 3-way merged.
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
    updates: dict[str, str | None] = {}
    for field_name in ("planned_start", "planned_end"):
        raw = getattr(body, field_name)
        if raw is None:
            continue
        updates[field_name] = _validate_planned_date(raw, field_name) or None
    if not updates:
        raise ApiError(
            422,
            "invalid_kanban_schedule",
            "At least one of planned_start / planned_end is required "
            "(use an empty string to clear).",
        )
    snapshot = file_state.snapshot_file(kanban_path(pdir))
    sections = parse_kanban(pdir)
    base = copy_kanban_sections(sections)
    ref = card_ref.strip()
    hit, match_kind, match_error = _resolve_kanban_card(sections, ref)
    if hit is None:
        if match_kind == "ambiguous":
            raise ApiError(422, "kanban_card_ambiguous", match_error)
        raise ApiError(404, "kanban_card_not_found", match_error)
    from_section, _index, task = hit
    scheduled = replace(task, **updates)
    _check_planned_range(
        scheduled.planned_start or "", scheduled.planned_end or ""
    )
    sections[from_section][_index] = scheduled
    result = _save_kanban_mutation(pdir, sections, base, snapshot)
    section, stored = _find_card_by_id(result.sections, task.id)
    _record_agent_writeback(
        user,
        pdir.name,
        action="kanban.card.schedule",
        target_owner="kanban",
        note=(
            f"kanban schedule: {task.title.strip()!r} "
            f"{stored.planned_start or '—'}..{stored.planned_end or '—'}"
        ),
        refs={"card_id": task.id, "section": section},
        changed_paths=[kanban_path(pdir)],
    )
    response.headers["ETag"] = _kanban_etag(pdir)
    return KanbanMutationResponse(
        ok=True,
        card=_kanban_task_model(stored),
        section=section,
        merged_external=result.merged_external,
        merge_notices=_merge_notices(result),
    )


@router.patch(
    "/profiles/{name}/kanban/cards/{card_ref}",
    response_model=KanbanMutationResponse,
    responses=KANBAN_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def patch_profile_kanban_card(
    name: str,
    card_ref: str,
    body: KanbanCardPatchRequest,
    response: Response,
    if_match: str | None = Header(default=None),
    user: CurrentUser = Depends(require_user),
) -> KanbanMutationResponse | JSONResponse:
    """Edit one card's fields (lane assignment, title, context, why, tags, todos).

    ``None`` fields keep the current value; ``""`` clears
    ``context``/``why``/``project_id``/``milestone_id`` (``project_id``
    clearing unassigns the card from its lane); ``tags`` replaces the
    whole tag list when given; ``todos`` fully replaces the checklist
    when given (``[]`` clears it). ``title`` must not be blank when given.
    Section moves stay on the move endpoint — Someday is a section, not a
    flag. When ``project_id`` changed, project-board.yaml task refs are
    re-synced from kanban metadata (task side is authoritative), same as
    the project-task move endpoint. ``card_ref`` is the task id first
    (URL-safe; survives titles containing ``/``), then the move/done
    fallback semantics (exact title or unique substring). Honors ``If-Match``
    (412 on mismatch); a concurrent kanban write is 3-way merged.
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
    updates: dict[str, Any] = {}
    if body.title is not None:
        title = body.title.strip()
        if not title:
            raise ApiError(
                422, "invalid_kanban_card", "Card title must not be blank."
            )
        updates["title"] = title
    for field_name in ("context", "why", "project_id", "milestone_id"):
        value = getattr(body, field_name)
        if value is not None:
            updates[field_name] = value.strip()
    if body.tags is not None:
        updates["tags"] = ", ".join(
            tag.strip() for tag in body.tags if tag.strip()
        )
    if body.todos is not None:
        # Full-replace semantics: [] clears the checklist.
        updates["todos"] = [
            KanbanTodo(text=todo.text.strip(), done=todo.done)
            for todo in body.todos
            if todo.text.strip()
        ]
    if not updates:
        raise ApiError(
            422,
            "invalid_kanban_patch",
            "At least one editable field is required.",
        )
    board_snapshot = file_state.snapshot_file(pdir / "project-board.yaml")
    snapshot = file_state.snapshot_file(kanban_path(pdir))
    sections = parse_kanban(pdir)
    base = copy_kanban_sections(sections)
    ref = card_ref.strip()
    hit, match_kind, match_error = _resolve_kanban_card(sections, ref)
    if hit is None:
        if match_kind == "ambiguous":
            raise ApiError(422, "kanban_card_ambiguous", match_error)
        raise ApiError(404, "kanban_card_not_found", match_error)
    from_section, _index, task = hit
    sections[from_section][_index] = replace(task, **updates)
    result = _save_kanban_mutation(pdir, sections, base, snapshot)
    section, stored = _find_card_by_id(result.sections, task.id)
    if "project_id" in updates:
        try:
            sync_project_board_from_kanban(
                pdir.name,
                parse_kanban(pdir),
                expected_snapshot=board_snapshot,
            )
        except file_state.FileConflictError:
            return _kanban_error(
                412,
                "etag_mismatch",
                "project-board.yaml changed while syncing lane assignment; "
                "reload before retrying.",
                _kanban_etag(pdir),
            )
    trace_paths = [kanban_path(pdir)]
    if "project_id" in updates:
        trace_paths.append(pdir / "project-board.yaml")
    _record_agent_writeback(
        user,
        pdir.name,
        action="kanban.card.patch",
        target_owner="kanban",
        note=f"kanban patch: {task.title.strip()!r} [{', '.join(updates)}]",
        refs={"card_id": task.id, "section": section},
        changed_paths=trace_paths,
    )
    response.headers["ETag"] = _kanban_etag(pdir)
    return KanbanMutationResponse(
        ok=True,
        card=_kanban_task_model(stored),
        section=section,
        merged_external=result.merged_external,
        merge_notices=_merge_notices(result),
    )


@router.delete(
    "/profiles/{name}/kanban/cards/{card_ref}",
    response_model=KanbanCardDeleteResponse,
    responses=KANBAN_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def delete_profile_kanban_card(
    name: str,
    card_ref: str,
    response: Response,
    body: KanbanCardDeleteRequest | None = None,
    if_match: str | None = Header(default=None),
    user: CurrentUser = Depends(require_user),
) -> KanbanCardDeleteResponse | JSONResponse:
    """Delete one kanban card for good (detail-card danger action).

    ``card_ref`` is the task id first (URL-safe; survives titles containing
    ``/``), then the move/done fallback semantics (exact title or unique
    substring; ambiguous → 422, unknown → 404). The card's todos, subtasks,
    and metadata bullets die with it. Evidence-pool ``kanban_refs`` are NOT
    touched — the tombstone mechanism handles references to the deleted
    task. With ``record_chronicle`` (default off) a ``task.deleted`` entry
    is appended to chronicle.yaml (ref = task id, note = title). Honors
    ``If-Match`` (412 on stale); a concurrent kanban write between parse
    and save is 3-way merged like the other card mutations.
    """
    pdir = _resolve_profile(name)
    etag = _kanban_etag(pdir)
    if not _if_match_satisfied(if_match, etag):
        return _kanban_error(
            412,
            "etag_mismatch",
            "kanban.md changed since it was loaded; reload before deleting.",
            etag,
        )
    snapshot = file_state.snapshot_file(kanban_path(pdir))
    sections = parse_kanban(pdir)
    base = copy_kanban_sections(sections)
    ref = card_ref.strip()
    hit, match_kind, match_error = _resolve_kanban_card(sections, ref)
    if hit is None:
        if match_kind == "ambiguous":
            raise ApiError(422, "kanban_card_ambiguous", match_error)
        raise ApiError(404, "kanban_card_not_found", match_error)
    from_section, _index, task = hit
    deleted_title = task.title.strip()
    deleted_ref = task.id or deleted_title
    del sections[from_section][_index]
    _save_kanban_mutation(pdir, sections, base, snapshot)
    if body is not None and body.record_chronicle:
        _append_chronicle_entry(
            pdir,
            "task.deleted",
            ref=deleted_ref,
            note=deleted_title,
            snapshot=file_state.snapshot_file(
                pdir / chronicle_core.CHRONICLE_FILENAME
            ),
        )
    trace_paths = [kanban_path(pdir)]
    if body is not None and body.record_chronicle:
        trace_paths.append(pdir / chronicle_core.CHRONICLE_FILENAME)
    _record_agent_writeback(
        user,
        pdir.name,
        action="kanban.card.delete",
        target_owner="kanban",
        note=f"kanban delete: {deleted_title!r}",
        refs={"card_id": deleted_ref, "section": from_section},
        changed_paths=trace_paths,
    )
    response.headers["ETag"] = _kanban_etag(pdir)
    return KanbanCardDeleteResponse(
        ok=True, deleted_ref=deleted_ref, deleted_title=deleted_title
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
    north_star = _north_star_from_identity(identity)
    return GoalsResponse(
        profile=pdir.name,
        current_goal_id=book.current_goal_id,
        north_star=north_star,
        goals=[GoalModel(**goal.to_dict()) for goal in book.goals],
    )


# --- Home starmap editing (design: docs/zh/dev/home-editing-starmap-design.md
# §8/§9): surgical North Star rewrite, goals CRUD, and the append-only
# chronicle. All mutations follow the ETag/If-Match + 412 + in-lock snapshot
# discipline and append chronicle entries only for real changes.


def _skill_md_etag(pdir: Path) -> str:
    """Weak ETag for the profile's SKILL.md (sha256 fingerprint)."""
    snapshot = file_state.snapshot_file(pdir / "SKILL.md")
    return f'W/"{snapshot.sha256 or "empty"}"'


def _goals_etag(pdir: Path) -> str:
    """Weak ETag for the profile's goals.yaml (sha256 fingerprint)."""
    snapshot = file_state.snapshot_file(pdir / "goals.yaml")
    return f'W/"{snapshot.sha256 or "empty"}"'


def _chronicle_etag(pdir: Path) -> str:
    """Weak ETag for the profile's chronicle.yaml (sha256 fingerprint)."""
    snapshot = file_state.snapshot_file(
        pdir / chronicle_core.CHRONICLE_FILENAME
    )
    return f'W/"{snapshot.sha256 or "empty"}"'


def _append_chronicle_entry(
    pdir: Path,
    kind: str,
    *,
    ref: str = "",
    note: str = "",
    snapshot: file_state.FileSnapshot | None = None,
) -> None:
    """Append one chronicle entry, tolerating a concurrent append once.

    chronicle.yaml is append-only and ``append_chronicle`` reloads inside
    the lock, so a snapshot conflict can only mean another writer appended
    meanwhile — the retry with a fresh snapshot is a safe locked merge.
    """
    try:
        chronicle_core.append_chronicle(
            pdir,
            kind,
            ref=ref,
            note=note,
            expected_snapshot=snapshot,
        )
    except file_state.FileConflictError:
        chronicle_core.append_chronicle(
            pdir,
            kind,
            ref=ref,
            note=note,
            expected_snapshot=file_state.snapshot_file(
                pdir / chronicle_core.CHRONICLE_FILENAME
            ),
        )


def _north_star_from_identity(identity: dict[str, str]) -> NorthStarModel:
    """Owner-facing North Star model from parsed identity fields."""
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


NORTH_STAR_MUTATION_RESPONSES = {
    **ERROR_RESPONSES,
    412: {
        "model": ErrorResponse,
        "description": "If-Match ETag does not match SKILL.md.",
    },
    422: {
        "model": ErrorResponse,
        "description": (
            "No field provided, or visibility is not public/private."
        ),
    },
}


@router.patch(
    "/profiles/{name}/north-star",
    response_model=NorthStarMutationResponse,
    responses=NORTH_STAR_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def patch_profile_north_star(
    name: str,
    body: NorthStarPatchRequest,
    response: Response,
    if_match: str | None = Header(default=None),
    user: CurrentUser = Depends(require_user),
) -> NorthStarMutationResponse | JSONResponse:
    """Surgically rewrite the North Star in SKILL.md's Identity section.

    Only the ``- **North Star**`` / ``- **North Star Brief**`` /
    ``- **North Star Visibility**`` bullet lines are touched; generated
    blocks and every other byte of the living document stay identical
    (core.north_star.update_north_star). ``visibility`` is binary going
    forward (``public``/``private``) and gates only public artifacts.
    Honors ``If-Match`` against the SKILL.md ETag (412 on mismatch). A
    no-op patch writes nothing and logs no chronicle entry; a real rewrite
    of the full text appends ``north_star.rewritten``.
    """
    pdir = _resolve_profile(name)
    etag = _skill_md_etag(pdir)
    if not _if_match_satisfied(if_match, etag):
        return _kanban_error(
            412,
            "etag_mismatch",
            "SKILL.md changed since it was loaded; reload before editing.",
            etag,
        )
    if (
        body.full is None
        and body.brief is None
        and body.visibility is None
    ):
        raise ApiError(
            422,
            "north_star_field_required",
            "Provide at least one of full, brief, or visibility.",
        )
    visibility = body.visibility
    if visibility is not None:
        clean_visibility = visibility.strip().lower()
        if clean_visibility not in ("public", "private"):
            raise ApiError(
                422,
                "invalid_north_star_visibility",
                f"visibility must be 'public' or 'private', got "
                f"{visibility!r}.",
            )
        visibility = clean_visibility
    try:
        outcome = north_star_core.update_north_star(
            pdir,
            full=body.full,
            brief=body.brief,
            visibility=visibility,
            expected_snapshot=file_state.snapshot_file(pdir / "SKILL.md"),
        )
    except FileNotFoundError:
        raise ApiError(
            404,
            "skill_md_not_found",
            f"Profile {pdir.name} has no SKILL.md to edit.",
        ) from None
    except file_state.FileConflictError:
        # A concurrent write landed between the If-Match check and the
        # in-lock snapshot re-check (TOCTOU closure).
        return _kanban_error(
            412,
            "etag_mismatch",
            "SKILL.md changed while saving; reload before retrying.",
            _skill_md_etag(pdir),
        )
    if "full" in outcome.changed_keys:
        note = outcome.identity.get("North Star Brief", "").strip()
        if not note:
            note = outcome.identity.get("North Star", "").strip()[:80]
        _append_chronicle_entry(
            pdir,
            "north_star.rewritten",
            note=note,
            snapshot=file_state.snapshot_file(
                pdir / chronicle_core.CHRONICLE_FILENAME
            ),
        )
    if outcome.changed:
        trace_paths = [pdir / "SKILL.md"]
        if "full" in outcome.changed_keys:
            trace_paths.append(pdir / chronicle_core.CHRONICLE_FILENAME)
        _record_agent_writeback(
            user,
            pdir.name,
            action="north_star.patch",
            note=f"north-star update [{', '.join(outcome.changed_keys)}]",
            refs={"changed_keys": list(outcome.changed_keys)},
            changed_paths=trace_paths,
        )
    response.headers["ETag"] = _skill_md_etag(pdir)
    return NorthStarMutationResponse(
        ok=True,
        changed=outcome.changed,
        changed_keys=outcome.changed_keys,
        north_star=_north_star_from_identity(outcome.identity),
    )


GOAL_MUTATION_RESPONSES = {
    **ERROR_RESPONSES,
    412: {
        "model": ErrorResponse,
        "description": "If-Match ETag does not match goals.yaml.",
    },
    422: {
        "model": ErrorResponse,
        "description": (
            "Blank title, non-ISO target date, or unknown status."
        ),
    },
}

GOAL_EDIT_STATUSES = ("active", "paused", "completed")


def _validate_goal_status(value: str) -> str:
    """422 unless *value* is an editable goal status."""
    clean = value.strip().lower()
    if clean not in GOAL_EDIT_STATUSES:
        raise ApiError(
            422,
            "invalid_goal_status",
            f"status must be one of {', '.join(GOAL_EDIT_STATUSES)}, "
            f"got {value!r}.",
        )
    return clean


def _validate_goal_target(value: str) -> str:
    """422 unless *value* is empty or an ISO date (YYYY-MM-DD)."""
    return _validate_goal_date(value, field="target")


def _validate_goal_start(value: str) -> str:
    """422 unless *value* is empty or an ISO date (YYYY-MM-DD)."""
    return _validate_goal_date(value, field="start")


def _validate_goal_date(value: str, *, field: str) -> str:
    """422 unless *value* is empty or an ISO date (YYYY-MM-DD)."""
    clean = value.strip()
    if not clean:
        return ""
    try:
        return date.fromisoformat(clean).isoformat()
    except ValueError:
        raise ApiError(
            422,
            f"invalid_goal_{field}",
            f"{field} must be an ISO date (YYYY-MM-DD), got {value!r}.",
        ) from None


@router.post(
    "/profiles/{name}/goals",
    response_model=GoalMutationResponse,
    status_code=201,
    responses=GOAL_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def create_profile_goal(
    name: str,
    body: GoalCreateRequest,
    response: Response,
    if_match: str | None = Header(default=None),
    user: CurrentUser = Depends(require_user),
) -> GoalMutationResponse | JSONResponse:
    """Create one goal in goals.yaml and append ``goal.added`` to chronicle.

    The id is a deterministic slug from the title (``goal-<slug>``).
    Honors ``If-Match`` against the goals.yaml ETag (412 on mismatch).
    """
    pdir = _resolve_profile(name)
    etag = _goals_etag(pdir)
    if not _if_match_satisfied(if_match, etag):
        return _kanban_error(
            412,
            "etag_mismatch",
            "goals.yaml changed since it was loaded; reload before adding.",
            etag,
        )
    title = body.title.strip()
    if not title:
        raise ApiError(422, "invalid_goal_title", "title must not be blank.")
    status = _validate_goal_status(body.status)
    # 立项日 (design home-starmap-enhancements §3): auto-stamp today when the
    # caller leaves start empty; history with empty start is not backfilled.
    start = _validate_goal_start(body.start) or date.today().isoformat()
    target = _validate_goal_target(body.target)
    book = load_goal_book(pdir)
    goal = Goal(
        id=next_goal_id(book, title),
        title=title,
        status=status,
        start=start,
        target=target,
        summary=body.summary.strip(),
    )
    book.goals.append(goal)
    try:
        save_goal_book(
            pdir,
            book,
            expected_snapshot=file_state.snapshot_file(pdir / "goals.yaml"),
        )
    except file_state.FileConflictError:
        return _kanban_error(
            412,
            "etag_mismatch",
            "goals.yaml changed while saving; reload before retrying.",
            _goals_etag(pdir),
        )
    _append_chronicle_entry(
        pdir,
        "goal.added",
        ref=goal.id,
        note=goal.title,
        snapshot=file_state.snapshot_file(
            pdir / chronicle_core.CHRONICLE_FILENAME
        ),
    )
    _record_agent_writeback(
        user,
        pdir.name,
        action="goal.add",
        note=f"goal add: {goal.title!r} ({goal.id})",
        refs={"goal_id": goal.id},
        changed_paths=[
            pdir / "goals.yaml",
            pdir / chronicle_core.CHRONICLE_FILENAME,
        ],
    )
    response.headers["ETag"] = _goals_etag(pdir)
    return GoalMutationResponse(
        ok=True,
        changed=True,
        changed_keys=["id", "title", "status", "start", "target", "summary"],
        goal=GoalModel(**goal.to_dict()),
    )


@router.patch(
    "/profiles/{name}/goals/{goal_id}",
    response_model=GoalMutationResponse,
    responses={
        **GOAL_MUTATION_RESPONSES,
        404: {
            "model": ErrorResponse,
            "description": "Profile or goal not found.",
        },
    },
    dependencies=PROFILE_DEPENDENCY,
)
def patch_profile_goal(
    name: str,
    goal_id: str,
    body: GoalPatchRequest,
    response: Response,
    if_match: str | None = Header(default=None),
    user: CurrentUser = Depends(require_user),
) -> GoalMutationResponse | JSONResponse:
    """Edit a goal's title/summary/start/target/status in goals.yaml.

    Chronicle entries fire only for meaningful changes: ``goal.renamed``
    when the title changed and ``goal.completed`` when the status moved to
    ``completed`` — a no-op patch writes nothing and logs nothing. Honors
    ``If-Match`` against the goals.yaml ETag (412 on mismatch).
    """
    pdir = _resolve_profile(name)
    etag = _goals_etag(pdir)
    if not _if_match_satisfied(if_match, etag):
        return _kanban_error(
            412,
            "etag_mismatch",
            "goals.yaml changed since it was loaded; reload before editing.",
            etag,
        )
    if (
        body.title is None
        and body.summary is None
        and body.start is None
        and body.target is None
        and body.status is None
    ):
        raise ApiError(
            422,
            "goal_field_required",
            "Provide at least one of title, summary, start, target, or status.",
        )
    book = load_goal_book(pdir)
    goal = book.by_id().get(goal_id.strip())
    if goal is None:
        raise ApiError(
            404, "goal_not_found", f"Unknown goal: {goal_id.strip()}"
        )

    updates: dict[str, str] = {}
    if body.title is not None:
        title = body.title.strip()
        if not title:
            raise ApiError(
                422, "invalid_goal_title", "title must not be blank."
            )
        updates["title"] = title
    if body.summary is not None:
        updates["summary"] = body.summary.strip()
    if body.start is not None:
        updates["start"] = _validate_goal_start(body.start)
    if body.target is not None:
        updates["target"] = _validate_goal_target(body.target)
    if body.status is not None:
        updates["status"] = _validate_goal_status(body.status)

    old_status = goal.status
    old_title = goal.title
    changed_keys = [
        key for key, value in updates.items()
        if str(getattr(goal, key)) != value
    ]
    if changed_keys:
        for key, value in updates.items():
            setattr(goal, key, value)
        try:
            save_goal_book(
                pdir,
                book,
                expected_snapshot=file_state.snapshot_file(
                    pdir / "goals.yaml"
                ),
            )
        except file_state.FileConflictError:
            return _kanban_error(
                412,
                "etag_mismatch",
                "goals.yaml changed while saving; reload before retrying.",
                _goals_etag(pdir),
            )
        chronicle_snapshot = file_state.snapshot_file(
            pdir / chronicle_core.CHRONICLE_FILENAME
        )
        if "title" in changed_keys:
            _append_chronicle_entry(
                pdir,
                "goal.renamed",
                ref=goal.id,
                note=goal.title,
                snapshot=chronicle_snapshot,
            )
        if "status" in changed_keys and goal.status == "completed":
            _append_chronicle_entry(
                pdir,
                "goal.completed",
                ref=goal.id,
                note=goal.title,
                snapshot=chronicle_snapshot,
            )
        _record_agent_writeback(
            user,
            pdir.name,
            action="goal.patch",
            note=f"goal patch: {goal.title!r} [{', '.join(changed_keys)}]",
            refs={"goal_id": goal.id, "changed_keys": list(changed_keys)},
            changed_paths=[
                pdir / "goals.yaml",
                pdir / chronicle_core.CHRONICLE_FILENAME,
            ],
        )
    response.headers["ETag"] = _goals_etag(pdir)
    return GoalMutationResponse(
        ok=True,
        changed=bool(changed_keys),
        changed_keys=changed_keys,
        goal=GoalModel(**goal.to_dict()),
    )


@router.get(
    "/profiles/{name}/chronicle",
    response_model=ChronicleResponse,
    responses=ERROR_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def get_profile_chronicle(
    name: str,
    response: Response,
    limit: int = Query(50, ge=1, le=500),
) -> ChronicleResponse:
    """Chronicle entries, newest first (home briefing line / 拓片 / openclaw).

    Read-only; carries a weak ETag of chronicle.yaml so consumers can poll
    for new entries cheaply.
    """
    pdir = _resolve_profile(name)
    entries = chronicle_core.load_chronicle(pdir)
    response.headers["ETag"] = _chronicle_etag(pdir)
    return ChronicleResponse(
        profile=pdir.name,
        total=len(entries),
        entries=[
            ChronicleEntryModel(**entry.to_dict())
            for entry in reversed(entries[-limit:])
        ],
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
        breakthrough=record.breakthrough,
    )


def _evidence_detail(
    record: EvidenceRecord, pdir: Path | None = None
) -> EvidenceEntryDetailModel:
    """Full detail projection of one pool record.

    With *pdir* the projection also carries the reverse skill links
    (``skill_refs`` via ``evidence_usage_index``) and the resolved kanban
    provenance chain (``kanban_ref_details``; unresolvable refs are
    ``status="archived"`` tombstones, never errors).
    """
    item = _evidence_item(record)
    skill_refs: list[str] = []
    kanban_details: list[ProvenanceRefModel] = []
    if pdir is not None:
        usage = evidence_review_core.evidence_usage_index(pdir)
        skill_refs = [entry["id"] for entry in usage.get(record.id, [])]
        refs = [ref for ref in record.kanban_refs if str(ref).strip()]
        if refs:
            found: dict[str, str] = {}
            try:
                for task in find_kanban_tasks_by_ref(pdir, refs):
                    tid = str(getattr(task, "id", "") or "").strip()
                    if tid:
                        found[tid] = str(getattr(task, "title", "") or "")
            except Exception:  # noqa: BLE001 - provenance is best-effort
                found = {}
            from nblane.core.kanban_archive import kanban_ref_id

            for ref in refs:
                tid = kanban_ref_id(str(ref))
                if tid and tid in found:
                    kanban_details.append(
                        ProvenanceRefModel(
                            ref=str(ref),
                            task_id=tid,
                            title=found[tid],
                            status="linked",
                        )
                    )
                else:
                    kanban_details.append(
                        ProvenanceRefModel(
                            ref=str(ref), task_id=tid, status="archived"
                        )
                    )
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
        skill_refs=skill_refs,
        kanban_ref_details=kanban_details,
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
    skill_id: str = Query(
        "",
        description=(
            "Skill-node filter: only entries cited by this node's "
            "evidence_refs in skill-tree.yaml (the reverse of "
            "evidence_usage_index). Combines with status/q (AND)."
        ),
    ),
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

    clean_skill = skill_id.strip()
    if clean_skill:
        usage = evidence_review_core.evidence_usage_index(pdir)
        linked = {
            eid
            for eid, refs in usage.items()
            if any(ref.get("id") == clean_skill for ref in refs)
        }
        entries = [record for record in entries if record.id in linked]

    return EvidenceListResponse(
        profile=pdir.name,
        status=clean_status,
        q=q.strip(),
        skill_id=clean_skill,
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
    return _evidence_detail(record, pdir)


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
        breakthrough=bool(row.get("breakthrough", False)),
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
            "证据池已被其他改动更新,正在为你刷新;请重试。",
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
            "证据池在写入期间被其他改动更新,请重试。",
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


# --- Evidence single-entry mutations + crystallize (Phase 1 single page) ----

# Fields the single-entry editor may touch: the review whitelist plus plain
# text fields. Provenance (origin*, refs, original_content) is immutable —
# the crystallize snapshot is the audit trail.
_EVIDENCE_TEXT_EDITABLE_FIELDS = ("title", "summary", "date", "url")
_EVIDENCE_ENUM_EDITABLE_FIELDS: dict[str, tuple[str, ...]] = {
    **evidence_review_core.POOL_EDITABLE_FIELDS,
    "type": tuple(sorted(EVIDENCE_TYPES)),
}
# Bool flags take "true"/"false" ("" clears, i.e. removes the key — the
# YAML round-trip only writes true flags). ``breakthrough`` marks a
# landmark proof (core.skill_progression.BREAKTHROUGH_WEIGHT).
_EVIDENCE_BOOL_EDITABLE_FIELDS = ("breakthrough",)


@router.post(
    "/profiles/{name}/evidence/{entry_id}/edit",
    response_model=EvidenceReviewMutationResponse,
    responses=EVIDENCE_REVIEW_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def edit_profile_evidence_entry(
    name: str,
    entry_id: str,
    body: EvidenceEditRequest,
    response: Response,
    if_match: str | None = Header(default=None),
    user: CurrentUser = Depends(require_user),
) -> EvidenceReviewMutationResponse | JSONResponse:
    """Edit whitelist fields on one pool row.

    Text fields (``title``/``summary``/``date``/``url``) take any string
    ("" clears all but ``title``); enum fields (``type`` plus the review
    whitelist) must be in their domain ("" clears); bool flags
    (``breakthrough``) take ``"true"``/``"false"`` ("" or ``"false"``
    clears the flag). Honors ``If-Match`` (412 on mismatch, fresh ETag in
    the header).
    """
    eid = entry_id.strip()
    cleaned: dict[str, str] = {}
    bool_flags: dict[str, bool] = {}
    for field, raw_value in body.fields.items():
        field = field.strip()
        value = str(raw_value or "").strip()
        if field in _EVIDENCE_TEXT_EDITABLE_FIELDS:
            if field == "title" and not value:
                raise ApiError(422, "invalid_edit_value", "title cannot be empty.")
            cleaned[field] = value
            continue
        if field in _EVIDENCE_BOOL_EDITABLE_FIELDS:
            lowered = value.lower()
            if lowered in ("", "false"):
                bool_flags[field] = False
            elif lowered == "true":
                bool_flags[field] = True
            else:
                raise ApiError(
                    422,
                    "invalid_edit_value",
                    f"Value {value!r} is not valid for {field} "
                    "(expected true/false, or empty to clear).",
                )
            continue
        allowed = _EVIDENCE_ENUM_EDITABLE_FIELDS.get(field)
        if allowed is None:
            raise ApiError(
                422,
                "invalid_edit_field",
                f"Field {field!r} is not editable (expected one of: "
                f"{', '.join(sorted([*_EVIDENCE_ENUM_EDITABLE_FIELDS, *_EVIDENCE_TEXT_EDITABLE_FIELDS, *_EVIDENCE_BOOL_EDITABLE_FIELDS]))}).",
            )
        if value and value not in allowed:
            raise ApiError(
                422,
                "invalid_edit_value",
                f"Value {value!r} is not valid for {field} "
                f"(expected one of: {', '.join(allowed)}, or empty to clear).",
            )
        cleaned[field] = value

    def _apply(entries: list[dict[str, Any]]) -> tuple[int, list[str]]:
        for row in entries:
            if str(row.get("id", "") or "").strip() != eid:
                continue
            for field, value in cleaned.items():
                if value:
                    row[field] = value
                else:
                    row.pop(field, None)
            for field, flag in bool_flags.items():
                if flag:
                    row[field] = True
                else:
                    row.pop(field, None)
            return 1, []
        return 0, [eid]

    outcome = _mutate_evidence_pool(name, if_match, _apply)
    if isinstance(outcome, JSONResponse):
        return outcome
    pdir, changed, missing = outcome
    if missing:
        raise ApiError(
            404, "evidence_not_found", f"Unknown evidence entry: {eid}"
        )
    if changed:
        trace_paths = [pdir / profile_io.EVIDENCE_POOL_FILENAME]
        if (pdir / "SKILL.md").exists():
            trace_paths.append(pdir / "SKILL.md")
        _record_agent_writeback(
            user,
            pdir.name,
            action="evidence.edit",
            target_owner="evidence_pool",
            note=(
                f"evidence edit: {eid} "
                f"[{', '.join(sorted([*cleaned, *bool_flags]))}]"
            ),
            refs={"entry_id": eid},
            changed_paths=trace_paths,
        )
    response.headers["ETag"] = _evidence_pool_etag(pdir)
    return EvidenceReviewMutationResponse(ok=True, changed=changed, missing=[])


@router.post(
    "/profiles/{name}/evidence/{entry_id}/review",
    response_model=EvidenceReviewMutationResponse,
    responses=EVIDENCE_REVIEW_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def review_profile_evidence_entry(
    name: str,
    entry_id: str,
    body: EvidenceEntryActionRequest,
    response: Response,
    if_match: str | None = Header(default=None),
    user: CurrentUser = Depends(require_user),
) -> EvidenceReviewMutationResponse | JSONResponse:
    """Single-entry review action: accept / reject (deprecate) / restore.

    ``accept`` sets ``review_status=reviewed`` and applies the optional
    grade fields in the same locked write; ``reject`` sets
    ``deprecated: true`` (kept for provenance); ``restore`` clears it.
    Honors ``If-Match`` (412 on mismatch).
    """
    eid = entry_id.strip()
    action = body.action.strip().lower()
    if action not in ("accept", "reject", "restore"):
        raise ApiError(
            422,
            "invalid_review_action",
            f"Unknown action {body.action!r} (expected accept|reject|restore).",
        )
    grades: dict[str, str] = {}
    if action == "accept":
        for field, allowed in evidence_review_core.POOL_EDITABLE_FIELDS.items():
            if field == "review_status":
                continue
            value = str(getattr(body, field, "") or "").strip()
            if value and value not in allowed:
                raise ApiError(
                    422,
                    "invalid_review_value",
                    f"Value {value!r} is not valid for {field} "
                    f"(expected one of: {', '.join(allowed)}, or empty to clear).",
                )
            if value:
                grades[field] = value

    def _apply(entries: list[dict[str, Any]]) -> tuple[int, list[str]]:
        for row in entries:
            if str(row.get("id", "") or "").strip() != eid:
                continue
            if action == "accept":
                row["review_status"] = "reviewed"
                for field, value in grades.items():
                    row[field] = value
                # 置信度按 origin 自动推导(评审只评「分量」);已有值保留。
                if not str(row.get("confidence", "") or "").strip():
                    derived = evidence_review_core.confidence_for_origin(
                        row.get("origin")
                    )
                    if derived:
                        row["confidence"] = derived
            elif action == "reject":
                if bool(row.get("deprecated", False)):
                    return 0, []
                row["deprecated"] = True
            else:  # restore
                if not bool(row.get("deprecated", False)):
                    return 0, []
                row.pop("deprecated", None)
            return 1, []
        return 0, [eid]

    outcome = _mutate_evidence_pool(name, if_match, _apply)
    if isinstance(outcome, JSONResponse):
        return outcome
    pdir, changed, missing = outcome
    if missing:
        raise ApiError(
            404, "evidence_not_found", f"Unknown evidence entry: {eid}"
        )
    if changed:
        trace_paths = [pdir / profile_io.EVIDENCE_POOL_FILENAME]
        if (pdir / "SKILL.md").exists():
            trace_paths.append(pdir / "SKILL.md")
        _record_agent_writeback(
            user,
            pdir.name,
            action="evidence.review",
            target_owner="evidence_pool",
            note=f"evidence review: {action} {eid}",
            refs={"entry_id": eid, "review_action": action},
            changed_paths=trace_paths,
        )
    response.headers["ETag"] = _evidence_pool_etag(pdir)
    return EvidenceReviewMutationResponse(ok=True, changed=changed, missing=[])


def _skill_tree_etag(pdir: Path) -> str:
    """Weak ETag for skill-tree.yaml (same contract as the pool ETag)."""
    snapshot = file_state.snapshot_file(pdir / profile_io.SKILL_TREE_FILENAME)
    return f'W/"{snapshot.sha256 or "empty"}"'


@router.post(
    "/profiles/{name}/evidence/{entry_id}/skill-links",
    response_model=EvidenceSkillLinksResponse,
    responses=EVIDENCE_REVIEW_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def set_profile_evidence_skill_links(
    name: str,
    entry_id: str,
    body: EvidenceSkillLinksRequest,
    response: Response,
    if_match: str | None = Header(default=None),
    user: CurrentUser = Depends(require_user),
) -> EvidenceSkillLinksResponse | JSONResponse:
    """Reconcile the skill nodes citing one evidence row (link/unlink).

    Chip-save semantics: ``skill_ids`` is the desired final set (core
    ``set_evidence_skill_refs`` adds missing / removes absent, creates
    unknown nodes as ``learning``). The write lands on skill-tree.yaml only
    — the pool never stores the reverse direction. ``If-Match`` carries the
    skill-tree.yaml ETag from the stages/tree reads (412 on mismatch).
    """
    pdir = _resolve_profile(name)
    eid = entry_id.strip()
    raw_pool = profile_io.load_evidence_pool_raw(pdir) or {}
    pool_ids = {
        str(row.get("id", "") or "").strip()
        for row in (raw_pool.get("evidence_entries") or [])
        if isinstance(row, dict)
    }
    if eid not in pool_ids:
        raise ApiError(
            404, "evidence_not_found", f"Unknown evidence entry: {eid}"
        )
    etag = _skill_tree_etag(pdir)
    if not _if_match_satisfied(if_match, etag):
        return _evidence_review_error(
            412,
            "etag_mismatch",
            "技能树已被其他改动更新,正在为你刷新;请重试。",
            etag,
        )
    skill_ids = [str(item).strip() for item in body.skill_ids if str(item).strip()]
    link_state: dict[str, list[str]] = {"before": []}

    def _apply(raw: dict[str, Any]) -> None:
        nodes = [
            node
            for node in (raw.get("nodes") or [])
            if isinstance(node, dict)
        ]
        link_state["before"] = sorted(
            str(node.get("id", "") or "").strip()
            for node in nodes
            if eid
            in [
                str(ref).strip()
                for ref in (node.get("evidence_refs") or [])
                if str(ref).strip()
            ]
        )
        raw["nodes"] = evidence_review_core.set_evidence_skill_refs(
            nodes, eid, skill_ids
        )
        raw["profile"] = pdir.name

    try:
        profile_io.update_skill_tree(
            pdir.name,
            _apply,
            expected_snapshot=file_state.snapshot_file(
                pdir / profile_io.SKILL_TREE_FILENAME
            ),
        )
    except file_state.FileConflictError:
        return _evidence_review_error(
            412,
            "etag_mismatch",
            "技能树在写入期间被其他改动更新,请重试。",
            _skill_tree_etag(pdir),
        )
    if (pdir / "SKILL.md").exists():
        write_generated_blocks(pdir)
    if link_state["before"] != sorted(skill_ids):
        trace_paths = [pdir / profile_io.SKILL_TREE_FILENAME]
        if (pdir / "SKILL.md").exists():
            trace_paths.append(pdir / "SKILL.md")
        _record_agent_writeback(
            user,
            pdir.name,
            action="evidence.skill_links",
            target_owner="evidence_pool",
            note=f"evidence skill-links: {eid} → [{', '.join(skill_ids)}]",
            refs={"entry_id": eid, "skill_ids": list(skill_ids)},
            changed_paths=trace_paths,
        )
    response.headers["ETag"] = _skill_tree_etag(pdir)
    return EvidenceSkillLinksResponse(ok=True, entry_id=eid, skill_ids=skill_ids)


@router.get(
    "/profiles/{name}/evidence/{entry_id}/skill-suggestions",
    response_model=EvidenceSkillSuggestionsResponse,
    responses=ERROR_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def get_profile_evidence_skill_suggestions(
    name: str,
    entry_id: str,
    top_n: int = Query(5, ge=1, le=20),
) -> EvidenceSkillSuggestionsResponse:
    """Ranked skill-link suggestions for one pool row.

    Tiered backend (``backend`` field): ``embedding`` when
    ``LLM_EMBEDDING_MODEL`` is configured (skill label/category embeddings
    cached under the profile's ``.cache/``), else a single LLM ranking call,
    else the deterministic rule matcher. Already-linked nodes are excluded.
    """
    pdir = _resolve_profile(name)
    raw = profile_io.load_evidence_pool_raw(pdir) or {}
    row = next(
        (
            item
            for item in (raw.get("evidence_entries") or [])
            if isinstance(item, dict)
            and str(item.get("id", "") or "").strip() == entry_id.strip()
        ),
        None,
    )
    if row is None:
        raise ApiError(
            404,
            "evidence_not_found",
            f"Unknown evidence entry: {entry_id}",
        )
    result = skill_suggest.suggest_skills_for_evidence(pdir, row, top_n=top_n)
    return EvidenceSkillSuggestionsResponse(
        profile=pdir.name,
        entry_id=entry_id.strip(),
        backend=str(result.get("backend") or "none"),
        suggestions=[
            EvidenceSkillSuggestionModel(**item)
            for item in result.get("suggestions") or []
        ],
    )


@router.get(
    "/profiles/{name}/evidence-stages",
    response_model=EvidenceStagesResponse,
    responses=ERROR_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def get_profile_evidence_stages(name: str) -> EvidenceStagesResponse:
    """Five-stage pipeline counters for the single Evidence page.

    待结晶 = uncrystallized Done tasks; 待评审 = active rows not yet
    reviewed; 已入座 = reviewed rows linked to at least one skill node;
    待补强 = solid/expert skills with missing/weak evidence
    (``core.evidence_review.evidence_status_risks``); 已废弃 = deprecated
    rows. Counts are queue-wide (unfiltered).
    """
    pdir = _resolve_profile(name)
    raw = profile_io.load_evidence_pool_raw(pdir) or {}
    rows = [
        row
        for row in (raw.get("evidence_entries") or [])
        if isinstance(row, dict) and str(row.get("id", "") or "").strip()
    ]
    usage = evidence_review_core.evidence_usage_index(pdir)
    active = [row for row in rows if not row.get("deprecated")]
    needs_review = sum(
        1
        for row in active
        if evidence_review_core.normalize_review_status(row.get("review_status"))
        != "reviewed"
    )
    seated = sum(
        1
        for row in active
        if evidence_review_core.normalize_review_status(row.get("review_status"))
        == "reviewed"
        and usage.get(str(row.get("id", "") or "").strip())
    )
    sections = parse_kanban(pdir)
    pending_crystallize = sum(
        1
        for task in (sections.get(KANBAN_DONE) or [])
        if not getattr(task, "crystallized", False)
    )
    risks = [
        EvidenceStageRiskModel(
            skill_id=str(item.get("id", "") or ""),
            label=str(item.get("label", "") or ""),
            status=str(item.get("status", "") or ""),
            risk_level=str(item.get("risk_level", "") or ""),
            risk_reason=str(item.get("risk_reason", "") or ""),
            required_strength=str(item.get("required_strength", "") or ""),
            highest_strength=str(item.get("highest_strength", "") or ""),
            evidence_refs=[
                str(ref) for ref in (item.get("active_evidence_refs") or [])
            ],
        )
        for item in evidence_review_core.evidence_status_risks(pdir)
    ]
    return EvidenceStagesResponse(
        profile=pdir.name,
        pending_crystallize_count=pending_crystallize,
        needs_review_count=needs_review,
        seated_count=seated,
        strengthen_count=len(risks),
        deprecated_count=len(rows) - len(active),
        risks=risks,
    )


@router.get(
    "/profiles/{name}/crystallize/candidates",
    response_model=CrystallizeCandidatesResponse,
    responses=ERROR_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def get_profile_crystallize_candidates(name: str) -> CrystallizeCandidatesResponse:
    """Uncrystallized Done tasks plus advisory blockers (wizard step 1).

    Task ids are materialized to kanban.md first so refs captured during
    crystallization resolve against later parses.
    """
    from nblane.core.kanban_io import materialize_kanban_task_ids

    pdir = _resolve_profile(name)
    materialize_kanban_task_ids(pdir)
    sections = parse_kanban(pdir)
    project_index = evidence_review_core.internal_project_goal_index(pdir)
    items = []
    for task in sections.get(KANBAN_DONE) or []:
        if getattr(task, "crystallized", False):
            continue
        items.append(
            CrystallizeCandidateModel(
                id=str(getattr(task, "id", "") or ""),
                title=str(getattr(task, "title", "") or ""),
                completed_on=str(getattr(task, "completed_on", "") or ""),
                project_id=str(getattr(task, "project_id", "") or ""),
                tags=str(getattr(task, "tags", "") or ""),
                context=str(getattr(task, "context", "") or ""),
                why=str(getattr(task, "why", "") or ""),
                outcome=str(getattr(task, "outcome", "") or ""),
                snapshot=crystallize_core.task_snapshot(task)["original_content"],
                blockers=evidence_review_core.done_task_evidence_blockers(
                    task, project_index
                ),
            )
        )
    return CrystallizeCandidatesResponse(profile=pdir.name, items=items)


@router.post(
    "/profiles/{name}/crystallize/draft",
    response_model=CrystallizeDraftResponse,
    responses={**ERROR_RESPONSES, 202: {"model": JobCreateResponse}},
    dependencies=PROFILE_DEPENDENCY,
)
def draft_profile_crystallize(
    name: str, body: CrystallizeDraftRequest
) -> CrystallizeDraftResponse | JSONResponse:
    """Draft evidence from selected Done tasks (wizard step 2).

    Rule mode (default) answers 200 with a deterministic one-row-per-task
    draft — each row already carries the task原文 snapshot in
    ``original_content`` + hash. ``use_llm=true`` creates an async
    ``evidence-crystallize`` job (202; poll/stream ``.../jobs/{job_id}``)
    whose result carries the same payload shape with ``backend="llm"``.
    """
    from nblane.core.kanban_io import materialize_kanban_task_ids

    pdir = _resolve_profile(name)
    if body.use_llm:
        try:
            snapshot = jobs.create_job(
                pdir.name,
                jobs.KIND_EVIDENCE_CRYSTALLIZE,
                {"task_ids": body.task_ids, "titles": body.titles},
            )
        except jobs.JobInputError as exc:
            raise ApiError(422, exc.code, exc.message) from exc
        payload = JobCreateResponse(
            job_id=snapshot["job_id"], job=JobModel(**snapshot)
        )
        return JSONResponse(
            status_code=202, content=payload.model_dump(mode="json")
        )
    materialize_kanban_task_ids(pdir)
    tasks, missing = crystallize_core.resolve_done_tasks(
        pdir, body.task_ids, body.titles
    )
    if not tasks:
        raise ApiError(
            422,
            "empty_selection",
            "None of the selected Done tasks could be resolved.",
        )
    patch = crystallize_core.rule_crystallize_patch(tasks)
    return CrystallizeDraftResponse(
        profile=pdir.name,
        backend="rule",
        patch=patch,
        tasks=[
            CrystallizeTaskModel(
                id=str(getattr(task, "id", "") or ""),
                title=str(getattr(task, "title", "") or ""),
                kanban_ref=(
                    f"kanban:{getattr(task, 'id', '')}"
                    if getattr(task, "id", "")
                    else ""
                ),
                project_id=str(getattr(task, "project_id", "") or ""),
                completed_on=str(getattr(task, "completed_on", "") or ""),
            )
            for task in tasks
        ],
        missing=missing,
    )


@router.post(
    "/profiles/{name}/crystallize/apply",
    response_model=CrystallizeApplyResponse,
    responses=ERROR_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def apply_profile_crystallize(
    name: str,
    body: CrystallizeApplyRequest,
    user: CurrentUser = Depends(require_user),
) -> CrystallizeApplyResponse:
    """Apply a confirmed crystallize draft (wizard step 3).

    Unlike the pool-field mutations this flow is merge-based: the draft is
    re-merged against the *current* pool/tree at apply time
    (``run_ingest_patch`` with validate + SKILL.md sync + rollback), so no
    If-Match precondition is needed — concurrent pool writes merge instead
    of clobbering. Only on success are the source Done tasks marked
    ``crystallized``.
    """
    pdir = _resolve_profile(name)
    result = crystallize_core.apply_crystallization(
        pdir.name,
        body.patch,
        task_ids=body.task_ids,
        titles=body.titles,
        include_evidence=body.include_evidence,
        include_nodes=body.include_nodes,
        allow_status_change=body.allow_status_change,
    )
    if not result["ok"]:
        raise ApiError(
            422,
            "crystallize_apply_failed",
            "; ".join(result["errors"]) or "Crystallize apply failed.",
        )
    _record_agent_writeback(
        user,
        pdir.name,
        action="crystallize.apply",
        target_owner="evidence_pool",
        note=(
            f"crystallize apply: {result['crystallized_count']} task(s), "
            f"new evidence {result['new_evidence_ids']}"
        ),
        refs={
            "task_ids": list(body.task_ids),
            "new_evidence_ids": list(result["new_evidence_ids"]),
        },
        changed_paths=[
            pdir / profile_io.EVIDENCE_POOL_FILENAME,
            pdir / profile_io.SKILL_TREE_FILENAME,
            kanban_path(pdir),
        ],
    )
    return CrystallizeApplyResponse(
        ok=True,
        warnings=result["warnings"],
        new_evidence_ids=result["new_evidence_ids"],
        crystallized_count=result["crystallized_count"],
    )


JOB_RESPONSES = {
    **ERROR_RESPONSES,
    404: {
        "model": ErrorResponse,
        "description": "Job not found for this profile.",
    },
    422: {
        "model": ErrorResponse,
        "description": "Unknown job kind or invalid job input.",
    },
}


@router.post(
    "/profiles/{name}/jobs",
    response_model=JobCreateResponse,
    status_code=202,
    responses=JOB_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def create_profile_job(name: str, body: JobCreateRequest) -> JobCreateResponse:
    """Create an async job for one profile (LLM long tasks).

    Kinds are registered in ``nblane.web_api.jobs``: ``gap-analysis``
    (also wired into ``POST .../gap/analyze`` with ``use_llm=true``),
    ``studio-jd-match`` and ``project-suggest-refs`` (the SPA's async
    paths for the sync studio/jd-match and suggest-refs endpoints, which
    stay unchanged for backward compatibility). The job runs on a daemon
    thread inside this single-worker process, tracked by the in-memory
    registry (same design as the reader sidecar's paper-library search
    jobs): poll ``GET .../jobs/{job_id}`` or subscribe to
    ``GET .../jobs/{job_id}/stream`` (SSE) for progress and the result.
    """
    pdir = _resolve_profile(name)
    try:
        snapshot = jobs.create_job(pdir.name, body.kind, body.input)
    except jobs.UnknownJobKindError as exc:
        raise ApiError(422, "unknown_job_kind", str(exc)) from exc
    except jobs.JobInputError as exc:
        raise ApiError(422, exc.code, exc.message) from exc
    return JobCreateResponse(job_id=snapshot["job_id"], job=JobModel(**snapshot))


def _resolve_profile_job(name: str, job_id: str) -> tuple[str, dict[str, Any]]:
    """Resolve ``(profile_name, job bundle)`` or 404.

    Unknown ids and jobs owned by a *different* profile answer the same
    404 so job ids cannot be probed across profiles.
    """
    pdir = _resolve_profile(name)
    bundle = jobs.read_job(job_id)
    if bundle is None or bundle["snapshot"].get("profile") != pdir.name:
        raise ApiError(
            404,
            "job_not_found",
            f"Unknown job for profile {pdir.name}: {job_id}",
        )
    return pdir.name, bundle


@router.get(
    "/profiles/{name}/jobs/{job_id}",
    response_model=JobStatusResponse,
    responses=JOB_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def get_profile_job(name: str, job_id: str) -> JobStatusResponse:
    """Poll one job's status; the result payload appears once done."""
    _, bundle = _resolve_profile_job(name, job_id)
    return JobStatusResponse(
        job=JobModel(**bundle["snapshot"]),
        result=bundle["result"],
    )


@router.get(
    "/profiles/{name}/jobs/{job_id}/stream",
    responses=JOB_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
async def stream_profile_job(
    request: Request, name: str, job_id: str
) -> StreamingResponse:
    """SSE stream of one job's progress (reader-sidecar wire design).

    Frames: ``job`` (initial snapshot, replay-safe for late subscribers),
    ``progress`` (one per logged phase event; phases are kind-specific —
    gap-analysis: starting/routing/merging, studio-jd-match:
    analyzing/generating, project-suggest-refs: collecting/suggesting),
    then a terminal ``done`` (carries the result payload) or ``error``
    (carries the structured ``{code, message}``). Terminal frames are
    re-derivable on reconnect — a late subscriber still receives the full
    event log plus the outcome.
    """
    profile_name, _ = _resolve_profile_job(name, job_id)

    async def event_generator():
        last_seq = 0
        sent_initial = False
        while True:
            bundle = jobs.read_job(job_id)
            if bundle is None or bundle["snapshot"].get("profile") != profile_name:
                yield jobs.sse_event(
                    "error",
                    {
                        "ok": False,
                        "error": {
                            "code": "job_not_found",
                            "message": "Job not found.",
                        },
                    },
                )
                break
            snapshot = bundle["snapshot"]
            if not sent_initial:
                yield jobs.sse_event("job", {"ok": True, "job": snapshot})
                sent_initial = True
            for event in bundle["events"]:
                if not isinstance(event, dict):
                    continue
                seq = int(event.get("seq") or 0)
                if seq <= last_seq:
                    continue
                yield jobs.sse_event(
                    "progress", {"ok": True, "job": snapshot, "event": event}
                )
                last_seq = seq
            status = str(snapshot.get("status") or "")
            if status == "done":
                yield jobs.sse_event(
                    "done",
                    {"ok": True, "job": snapshot, "result": bundle["result"]},
                )
                break
            if status == "failed":
                yield jobs.sse_event(
                    "error",
                    {"ok": False, "job": snapshot, "error": snapshot.get("error")},
                )
                break
            if await request.is_disconnected():
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


GAP_RESPONSES = {
    **ERROR_RESPONSES,
    202: {
        "model": JobCreateResponse,
        "description": (
            "use_llm=true: the deep analysis runs as an async "
            "gap-analysis job; poll or stream the returned job_id."
        ),
    },
    422: {
        "model": ErrorResponse,
        "description": (
            "Empty/unmatched task, missing skill tree or schema."
        ),
    },
}


@router.post(
    "/profiles/{name}/gap/analyze",
    response_model=GapAnalysisResponse,
    responses=GAP_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def analyze_profile_gap(
    name: str, body: GapAnalyzeRequest
) -> GapAnalysisResponse | JSONResponse:
    """Gap analysis for a free-text task description.

    ``use_llm=false`` (default) wraps ``core.gap.analyze`` with rule
    matching only and answers 200 synchronously. ``use_llm=true`` runs the
    same analysis plus the LLM router (a live blocking provider call that
    also persists learned keywords under ``schemas/.learned/``), so it is
    dispatched as an async ``gap-analysis`` job answering 202 — subscribe
    to the job's SSE stream for 路由中/合并中/完成 phases and the final
    ``GapAnalysisResponse`` payload (``analysis_mode == "rule+llm"``; when
    the LLM router fails but rule roots suffice, the job still completes
    with ``llm_router_error`` set). Analysis errors (no matching nodes,
    missing skill tree/schema) surface as 422 sync, or as a failed job
    with the same error code async.
    """
    pdir = _resolve_profile(name)
    if body.use_llm:
        try:
            snapshot = jobs.create_job(
                pdir.name, jobs.KIND_GAP_ANALYSIS, {"task": body.task}
            )
        except jobs.JobInputError as exc:
            raise ApiError(422, exc.code, exc.message) from exc
        payload = JobCreateResponse(
            job_id=snapshot["job_id"], job=JobModel(**snapshot)
        )
        return JSONResponse(status_code=202, content=payload.model_dump(mode="json"))
    result = gap.analyze(pdir.name, body.task)
    if result.error:
        raise ApiError(
            422,
            result.error_key or "gap_analysis_failed",
            result.error,
        )
    return GapAnalysisResponse(
        **jobs.build_gap_analysis_payload(pdir.name, result, analysis_mode="rule")
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
        habit_id=case.habit_id,
    )


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
            "unknown section, delete confirmation title mismatch, or AI "
            "suggest-refs unavailable."
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
            goals=_option_rows(project_suggest.goal_ref_options(pdir)),
            tasks=_task_ref_option_rows(pdir),
            evidence=_option_rows(project_suggest.evidence_ref_options(pdir)),
            sources=_option_rows(project_suggest.source_ref_options(pdir)),
            experiences=_option_rows(_experience_ref_options(pdir)),
            outputs=_option_rows(project_suggest.output_ref_options(pdir)),
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
            habit_id=body.habit_id,
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
    user: CurrentUser = Depends(require_user),
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
    for field in ("time_range", "summary", "notes", "habit_id"):
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
    saved = _synced_case_response(pdir, board, case_id, response, snapshots)
    if not isinstance(saved, JSONResponse):
        _record_agent_writeback(
            user,
            pdir.name,
            action="project_case.save",
            target_owner="work",
            note=f"project save: {case_id} [{', '.join(sorted(fields))}]",
            refs={"project_id": case_id},
            changed_paths=[
                pdir / "project-board.yaml",
                kanban_path(pdir),
                pdir / profile_io.EVIDENCE_POOL_FILENAME,
            ],
        )
    return saved


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
    user: CurrentUser = Depends(require_user),
) -> ProjectCaseMutationResponse | JSONResponse:
    """Mark one project case archived. Honors ``If-Match`` (412)."""
    checked = _check_board_mutation(name, if_match)
    if isinstance(checked, JSONResponse):
        return checked
    pdir, board, snapshots = checked
    _find_project_case(board, case_id)
    update_project_case(board, case_id, status="archived")
    saved = _synced_case_response(pdir, board, case_id, response, snapshots)
    if not isinstance(saved, JSONResponse):
        _record_agent_writeback(
            user,
            pdir.name,
            action="project_case.archive",
            target_owner="work",
            note=f"project archive: {case_id}",
            refs={"project_id": case_id},
            changed_paths=[
                pdir / "project-board.yaml",
                kanban_path(pdir),
            ],
        )
    return saved


@router.delete(
    "/profiles/{name}/project-board/cases/{case_id}",
    response_model=ProjectCaseDeleteResponse,
    responses=PROJECT_BOARD_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def delete_profile_project_case(
    name: str,
    case_id: str,
    body: ProjectCaseDeleteRequest,
    response: Response,
    if_match: str | None = Header(default=None),
    user: CurrentUser = Depends(require_user),
) -> ProjectCaseDeleteResponse | JSONResponse:
    """Delete one project case for good (user-decided, type-the-name confirm).

    ``confirm_title`` must equal the case title exactly, else 422
    ``project_delete_confirm_mismatch``. Consequences, in write order:

    1. Live kanban.md tasks owned via ``project_id`` are cleared back to
       unassigned (their ``milestone_id`` is cleared too when it named one
       of the case's milestones); kanban-archive.md history is untouched.
    2. The case is removed from project-board.yaml.
    3. Evidence-pool ``project_refs`` are NOT touched — the tombstone
       mechanism handles display of references to the deleted case.

    With ``record_chronicle`` (default off) a ``project.deleted`` entry is
    appended to chronicle.yaml with the case title as the note. Both file
    writes re-check their request-start snapshots inside the write locks;
    a mismatch answers 412 with a fresh board ETag (which covers
    kanban.md + project-board.yaml). Honors ``If-Match`` (412 on stale).
    """
    checked = _check_board_mutation(name, if_match)
    if isinstance(checked, JSONResponse):
        return checked
    pdir, _board, snapshots = checked
    case = _find_project_case(_board, case_id)
    if body.confirm_title.strip() != case.title:
        raise ApiError(
            422,
            "project_delete_confirm_mismatch",
            "Confirmation title does not match the project case title; "
            f"type {case.title!r} exactly to delete.",
        )
    milestone_ids = {
        milestone.id for milestone in case.milestones if milestone.id
    }
    raw_pool = profile_io.load_evidence_pool_raw(pdir) or {}
    evidence_refs_kept = sum(
        1
        for row in raw_pool.get("evidence_entries") or []
        if isinstance(row, dict) and case.id in (row.get("project_refs") or [])
    )

    def _unassign(sections: dict[str, list[KanbanTask]]) -> int:
        cleared = 0
        for tasks in sections.values():
            for task in tasks:
                if task.project_id != case.id:
                    continue
                task.project_id = ""
                if task.milestone_id in milestone_ids:
                    task.milestone_id = ""
                cleared += 1
        return cleared

    def _remove(board: ProjectBoard) -> None:
        board.project_cases = [
            item for item in board.project_cases if item.id != case.id
        ]

    try:
        tasks_unassigned = update_kanban(
            pdir, _unassign, expected_snapshot=snapshots["kanban"]
        )
        update_project_board(
            pdir, _remove, expected_snapshot=snapshots["board"]
        )
    except file_state.FileConflictError:
        return _project_board_error(
            412,
            "etag_mismatch",
            "Project board source files changed while deleting; "
            "reload before retrying.",
            _project_board_etag(pdir),
        )
    if body.record_chronicle:
        _append_chronicle_entry(
            pdir,
            "project.deleted",
            ref=case.id,
            note=case.title,
            snapshot=file_state.snapshot_file(
                pdir / chronicle_core.CHRONICLE_FILENAME
            ),
        )
    trace_paths = [kanban_path(pdir), pdir / "project-board.yaml"]
    if body.record_chronicle:
        trace_paths.append(pdir / chronicle_core.CHRONICLE_FILENAME)
    _record_agent_writeback(
        user,
        pdir.name,
        action="project_case.delete",
        target_owner="work",
        note=(
            f"project delete: {case.title!r} "
            f"({tasks_unassigned} task(s) unassigned)"
        ),
        refs={
            "project_id": case.id,
            "tasks_unassigned": tasks_unassigned,
            "evidence_refs_kept": evidence_refs_kept,
        },
        changed_paths=trace_paths,
    )
    response.headers["ETag"] = _project_board_etag(pdir)
    return ProjectCaseDeleteResponse(
        ok=True,
        deleted_id=case.id,
        tasks_unassigned=tasks_unassigned,
        evidence_refs_kept=evidence_refs_kept,
    )


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

    Kept as the synchronous contract for backward compatibility; the SPA
    now dispatches this LLM long task as an async ``project-suggest-refs``
    job (``POST /profiles/{name}/jobs``, progress over SSE) instead. Both
    paths share ``core.project_suggest.suggest_case_refs``.
    """
    pdir = _resolve_profile(name)
    board = load_project_board(pdir)
    case = _find_project_case(board, case_id)
    try:
        result = project_suggest.suggest_case_refs(pdir, case)
    except project_suggest.SuggestRefsError as exc:
        raise ApiError(422, exc.code, exc.message) from exc
    return ProjectSuggestRefsResponse(
        ok=True,
        backend=result.backend,
        suggestions=result.suggestions,
        rationale=result.rationale,
        warnings=result.warnings,
    )


# --- Projects Board (Phase 2): unified /projects aggregation + check-ins -----


def _projects_board_etag(pdir: Path) -> str:
    """Weak ETag over the projects-board source files (sha256 fingerprint).

    Covers every file the aggregation reads: SKILL.md (North Star),
    goals.yaml, project-board.yaml, kanban.md, kanban-archive.md, and
    activity-log.yaml. Weak (``W/``) because the hash identifies the source
    file versions, not the JSON response bytes.
    """
    fingerprints = []
    for relative in (
        "SKILL.md",
        "goals.yaml",
        "project-board.yaml",
        kanban_path(pdir).name,
        KANBAN_ARCHIVE_FILENAME,
        activity_log.ACTIVITY_LOG_FILENAME,
    ):
        snapshot = file_state.snapshot_file(pdir / relative)
        fingerprints.append(f"{relative}:{snapshot.sha256 or 'empty'}")
    digest = hashlib.sha256("|".join(fingerprints).encode("utf-8")).hexdigest()
    return f'W/"{digest}"'


def _projects_board_project_model(
    project: projects_board.BoardProject,
) -> ProjectsBoardProjectModel:
    """Convert one core board project to the API model."""
    return ProjectsBoardProjectModel(
        id=project.id,
        title=project.title,
        status=project.status,
        kind=project.kind,
        visibility=project.visibility,
        summary=project.summary,
        time_range=project.time_range,
        goal_refs=list(project.goal_refs),
        milestones=[
            ProjectsBoardMilestoneModel(**vars(milestone))
            for milestone in project.milestones
        ],
        queue=[ProjectsBoardTaskModel(**vars(task)) for task in project.queue],
        doing=[ProjectsBoardTaskModel(**vars(task)) for task in project.doing],
        someday=[
            ProjectsBoardTaskModel(**vars(task)) for task in project.someday
        ],
        column_counts=dict(project.column_counts),
        done_count=project.done_count,
        archived_done_count=project.archived_done_count,
        evidence_ref_count=project.evidence_ref_count,
        last_activity=project.last_activity,
        habit_id=project.habit_id,
    )


@router.get(
    "/profiles/{name}/projects-board",
    response_model=ProjectsBoardResponse,
    responses=ERROR_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def get_profile_projects_board(
    name: str,
    response: Response,
    include_archived: bool = Query(
        default=False,
        description=(
            "Include archived habits in habits[] (flagged archived=true). "
            "By default archived habits are excluded."
        ),
    ),
) -> ProjectsBoardResponse:
    """Aggregated projects board for the unified /projects SPA page.

    One shot for both views (kanban swimlanes + timeline): goals with their
    projects (a project groups under the first of its ``goal_refs`` naming a
    known goal; the rest land in ``ungrouped_projects``), per-project
    milestones with progress, Done counts that include kanban-archive.md,
    live tasks grouped by column (``someday`` as a badge list, not a
    column), an ``unassigned_tasks`` lane for tasks owned by no project, and
    habit check-in strips (current ISO week dots + streak ending today +
    total + ``recent_days`` heatmap window over the trailing 90 days).
    Archived habits stay out of ``habits`` unless ``include_archived`` is
    set. Full data, no display caps. The response carries the
    board-source ETag (see module docstring pattern) for use as ``If-Match``
    on the kanban/check-in mutations.
    """
    pdir = _resolve_profile(name)
    board = projects_board.build_projects_board(
        pdir, include_archived=include_archived
    )
    identity = parse_identity_fields(profile_io.load_skill_md(pdir.name))
    north_star = str(identity.get("North Star", "") or "").strip()
    response.headers["ETag"] = _projects_board_etag(pdir)
    return ProjectsBoardResponse(
        profile=board.profile,
        today=board.today,
        north_star=north_star,
        goals=[
            ProjectsBoardGoalModel(
                id=goal.id,
                title=goal.title,
                status=goal.status,
                summary=goal.summary,
                target=goal.target,
                projects=[
                    _projects_board_project_model(project)
                    for project in goal.projects
                ],
            )
            for goal in board.goals
        ],
        ungrouped_projects=[
            _projects_board_project_model(project)
            for project in board.ungrouped_projects
        ],
        unassigned_tasks=[
            ProjectsBoardTaskModel(**vars(task))
            for task in board.unassigned_tasks
        ],
        habits=[
            ProjectsBoardHabitModel(
                id=habit.id,
                title=habit.title,
                kind=habit.kind,
                cadence=habit.cadence,
                week=[
                    ProjectsBoardHabitDayModel(**vars(day))
                    for day in habit.week
                ],
                streak=habit.streak,
                total_checkins=habit.total_checkins,
                last_checkin=habit.last_checkin,
                project_id=habit.project_id,
                recent_days=[
                    ProjectsBoardHabitRecentDayModel(**vars(day))
                    for day in habit.recent_days
                ],
                archived=habit.archived,
            )
            for habit in board.habits
        ],
        stats=dict(board.stats),
    )


# --- Starmap (Phase 3): one-shot home-scene snapshot -------------------------


def _starmap_etag(pdir: Path) -> str:
    """Weak ETag over the starmap source files (sha256 fingerprint).

    Covers every file the aggregation reads: SKILL.md (North Star),
    goals.yaml, skill-tree.yaml (+ the domain schema it references),
    project-board.yaml, kanban.md, kanban-archive.md, activity-log.yaml
    (board done-counts/progress), and evidence-pool.yaml. Weak (``W/``)
    because the hash identifies the source file versions, not the JSON
    response bytes.
    """
    fingerprints = []
    relatives = [
        "SKILL.md",
        "goals.yaml",
        profile_io.SKILL_TREE_FILENAME,
        "project-board.yaml",
        kanban_path(pdir).name,
        KANBAN_ARCHIVE_FILENAME,
        activity_log.ACTIVITY_LOG_FILENAME,
        profile_io.EVIDENCE_POOL_FILENAME,
    ]
    raw_tree = profile_io.load_skill_tree_raw(pdir) or {}
    schema_name = str(raw_tree.get("schema") or "")
    schema_path = SCHEMAS_DIR / f"{schema_name}.yaml" if schema_name else None
    for relative in relatives:
        snapshot = file_state.snapshot_file(pdir / relative)
        fingerprints.append(f"{relative}:{snapshot.sha256 or 'empty'}")
    if schema_path is not None:
        snapshot = file_state.snapshot_file(schema_path)
        fingerprints.append(f"schema:{snapshot.sha256 or 'empty'}")
    digest = hashlib.sha256("|".join(fingerprints).encode("utf-8")).hexdigest()
    return f'W/"{digest}"'


@router.get(
    "/profiles/{name}/starmap",
    response_model=StarmapResponse,
    responses=ERROR_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def get_profile_starmap(name: str, response: Response) -> StarmapResponse:
    """One-shot growth-starmap snapshot for the SPA home scene (read-only).

    Everything the scene needs in a single call: the North Star, active
    goals, the skill field WITH locked schema nodes (三态
    locked/learning/lit) plus zh category display names, projects with
    progress and goal grouping, and the evidence pool with guest/seated
    split (30-day window + newest-4 density floor), strength, summary, and
    ``project_refs``. The response carries the starmap-source ETag (same
    weak-ETag pattern as /projects-board) for client-side staleness checks.
    """
    pdir = _resolve_profile(name)
    payload = starmap_snapshot_core.build_starmap_snapshot(pdir)
    response.headers["ETag"] = _starmap_etag(pdir)
    return StarmapResponse(
        profile=payload["profile"],
        generated_on=payload["generated_on"],
        schema_name=payload["schema_name"],
        north_star=payload["north_star"],
        goals=[StarmapGoalModel(**goal) for goal in payload["goals"]],
        categories=[
            StarmapCategoryModel(**category)
            for category in payload["categories"]
        ],
        skills=[StarmapSkillModel(**skill) for skill in payload["skills"]],
        projects=[
            StarmapProjectModel(**project) for project in payload["projects"]
        ],
        evidence=[
            StarmapEvidenceModel(**entry) for entry in payload["evidence"]
        ],
        counts=StarmapCountsModel(**payload["counts"]),
    )


# --- Divination (占卜; design home-starmap-enhancements §5) -------------------

DIVINATION_RESPONSES = {
    **ERROR_RESPONSES,
    422: {
        "model": ErrorResponse,
        "description": (
            "Serious mode (正占) requires a non-empty question; also raised "
            "for request-body validation failures."
        ),
    },
}


@router.post(
    "/profiles/{name}/divination",
    response_model=DivinationResponse,
    responses=DIVINATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def cast_profile_divination(name: str, body: DivinationRequest) -> DivinationResponse:
    """Cast one 卦 anchored in the profile's REAL starmap data.

    戏占 (``play``, default): playful reading (大富大贵彩头) whose every
    number comes from the live snapshot anchors. 正占 (``serious``): the
    question runs through the real rule gap analysis (``core.gap``) and
    the reading wraps its gaps/strong nodes in 卦辞 language. Texts are
    LLM-polished via the AI gateway action ``divination.cast`` when
    configured (``source="llm"``); otherwise a deterministic
    data-anchored rule reading answers (``source="rule"``). The hexagram
    itself is deterministic for (profile state, day, mode, question).
    The result is single-consumption: nothing is persisted.
    """
    pdir = _resolve_profile(name)
    question = body.question.strip()
    if body.mode == "serious" and not question:
        raise ApiError(
            422,
            "question_required",
            "正占需提供所问之事 (question)。",
        )
    outcome = divination_core.cast_divination(
        pdir, mode=body.mode, question=question
    )
    return DivinationResponse(**outcome)


def _activity_log_etag(pdir: Path) -> str:
    """Weak ETag for the profile's activity-log.yaml (sha256 fingerprint)."""
    snapshot = file_state.snapshot_file(
        pdir / activity_log.ACTIVITY_LOG_FILENAME
    )
    return f'W/"{snapshot.sha256 or "empty"}"'
CHECKIN_MUTATION_RESPONSES = {
    **ERROR_RESPONSES,
    412: {
        "model": ErrorResponse,
        "description": "If-Match ETag does not match the activity log file.",
    },
    422: {
        "model": ErrorResponse,
        "description": (
            "Missing/unknown habit, unlinked project, invalid date, "
            "non-positive count, or an invalid habit-plan binding "
            "(unknown plan, habit mismatch, inactive plan, or a date "
            "outside the plan window)."
        ),
    },
}


def _resolve_checkin_habit(pdir: Path, body: CheckinCreateRequest) -> str:
    """Resolve the target habit id from the request's habit/project ref."""
    habit_ref = body.habit.strip()
    if habit_ref:
        return habit_ref
    project_id = body.project_id.strip()
    if not project_id:
        raise ApiError(
            422,
            "checkin_habit_required",
            "A habit (id or title) or a habit-linked project_id is required.",
        )
    board = load_project_board(pdir)
    case = board.by_id().get(project_id)
    if case is None:
        raise ApiError(
            422,
            "checkin_project_not_found",
            f"Unknown project case: {project_id}",
        )
    explicit = str(getattr(case, "habit_id", "") or "").strip()
    if explicit:
        return explicit
    log = activity_log.load(pdir)
    for habit in log.habits:
        if projects_board.link_habit_to_project(habit.id, habit.title, case):
            return habit.id
    raise ApiError(
        422,
        "checkin_project_unlinked",
        f"Project {project_id} is not linked to any habit "
        "(habit id/title must match the project title or id tail); "
        "pass an explicit habit instead.",
    )


@router.post(
    "/profiles/{name}/checkins",
    response_model=CheckinMutationResponse,
    status_code=201,
    responses=CHECKIN_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def add_profile_checkin(
    name: str,
    body: CheckinCreateRequest,
    response: Response,
    if_match: str | None = Header(default=None),
    user: CurrentUser = Depends(require_user),
) -> CheckinMutationResponse | JSONResponse:
    """Append one habit check-in to the activity log (agent-facing hook).

    ``habit`` accepts a habit id or title (core resolution); ``project_id``
    is an alternative that resolves through the habit<->project name link.
    ``date`` defaults to today and must be an ISO date when given.
    ``plan_id`` optionally binds the check-in to an active habit plan of the
    same habit (422 when the plan is unknown, belongs to another habit, is
    not active, or the date falls outside the plan window); the backend
    derives and stores the plan-relative ``week_number``. The write
    goes through ``core.activity_log.add_activity_checkin`` under the
    activity-log write lock. Honors ``If-Match`` (412 on mismatch, fresh
    ETag in the header).
    """
    pdir = _resolve_profile(name)
    etag = _activity_log_etag(pdir)
    if not _if_match_satisfied(if_match, etag):
        return _kanban_error(
            412,
            "etag_mismatch",
            "activity-log.yaml changed since it was loaded; "
            "reload before checking in.",
            etag,
        )
    habit_ref = _resolve_checkin_habit(pdir, body)
    when = body.date.strip()
    if when:
        try:
            when = date.fromisoformat(when).isoformat()
        except ValueError:
            raise ApiError(
                422,
                "invalid_checkin_date",
                f"date must be an ISO date (YYYY-MM-DD), got {body.date!r}.",
            ) from None
    plan_id = body.plan_id.strip()
    week_number = 0
    if plan_id:
        week_number = _validate_checkin_plan(pdir, habit_ref, plan_id, when)
    try:
        entry = activity_log.add_activity_checkin(
            pdir,
            habit_ref,
            when=when or None,
            count=body.count,
            unit=body.unit.strip(),
            summary=body.summary.strip(),
            note=body.note.strip(),
            tags=body.tags,
            related_kanban=body.related_kanban,
            workout_type=body.workout_type.strip(),
            duration_min=body.duration_min,
            intensity=body.intensity.strip(),
            plan_id=plan_id,
            week_number=week_number,
            expected_snapshot=file_state.snapshot_file(
                pdir / activity_log.ACTIVITY_LOG_FILENAME
            ),
        )
    except ValueError as exc:
        raise ApiError(422, "invalid_checkin", str(exc)) from exc
    except file_state.FileConflictError:
        # A concurrent write landed between the If-Match check and the
        # in-lock snapshot re-check (TOCTOU closure).
        return _kanban_error(
            412,
            "etag_mismatch",
            "activity-log.yaml changed while checking in; "
            "reload before retrying.",
            _activity_log_etag(pdir),
        )
    response.headers["ETag"] = _activity_log_etag(pdir)
    entry_dict = entry.to_dict()
    _record_agent_writeback(
        user,
        pdir.name,
        action="checkin.add",
        target_owner="work",
        note=f"checkin: {habit_ref} ({entry_dict.get('date', '')})",
        refs={
            "checkin_id": str(entry_dict.get("id", "") or ""),
            "habit": habit_ref,
        },
        changed_paths=[pdir / activity_log.ACTIVITY_LOG_FILENAME],
    )
    return CheckinMutationResponse(
        ok=True, checkin=CheckinModel(**entry_dict)
    )


@router.delete(
    "/profiles/{name}/checkins/{checkin_id}",
    response_model=CheckinDeleteResponse,
    responses=CHECKIN_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def delete_profile_checkin(
    name: str,
    checkin_id: str,
    response: Response,
    if_match: str | None = Header(default=None),
    user: CurrentUser = Depends(require_user),
) -> CheckinDeleteResponse | JSONResponse:
    """Remove one check-in row from the activity log (销印).

    Pure housekeeping: nothing is recorded in chronicle.yaml. Check-ins
    without an ``id`` (legacy rows) are not addressable and answer 404.
    The write goes through ``core.activity_log.delete_checkin`` under the
    activity-log write lock. Honors ``If-Match`` (412 on mismatch, fresh
    ETag in the header).
    """
    pdir = _resolve_profile(name)
    etag = _activity_log_etag(pdir)
    if not _if_match_satisfied(if_match, etag):
        return _kanban_error(
            412,
            "etag_mismatch",
            "activity-log.yaml changed since it was loaded; "
            "reload before deleting the check-in.",
            etag,
        )
    try:
        deleted = activity_log.delete_checkin(
            pdir,
            checkin_id,
            expected_snapshot=file_state.snapshot_file(
                pdir / activity_log.ACTIVITY_LOG_FILENAME
            ),
        )
    except file_state.FileConflictError:
        # A concurrent write landed between the If-Match check and the
        # in-lock snapshot re-check (TOCTOU closure).
        return _kanban_error(
            412,
            "etag_mismatch",
            "activity-log.yaml changed while deleting the check-in; "
            "reload before retrying.",
            _activity_log_etag(pdir),
        )
    if not deleted:
        raise ApiError(
            404,
            "checkin_not_found",
            f"Unknown check-in id for profile {pdir.name}: {checkin_id}",
        )
    _record_agent_writeback(
        user,
        pdir.name,
        action="checkin.delete",
        target_owner="work",
        note=f"checkin delete: {checkin_id}",
        refs={"checkin_id": checkin_id},
        changed_paths=[pdir / activity_log.ACTIVITY_LOG_FILENAME],
    )
    response.headers["ETag"] = _activity_log_etag(pdir)
    return CheckinDeleteResponse(ok=True, checkin_id=checkin_id)


# --- Habit lifecycle: archive (reversible) and confirmed delete --------------


HABIT_MUTATION_RESPONSES = {
    **CHECKIN_MUTATION_RESPONSES,
    404: {
        "model": ErrorResponse,
        "description": "Profile or habit not found.",
    },
}


def _resolve_habit_or_404(pdir: Path, habit_ref: str) -> activity_log.Habit:
    """Resolve a habit id/title to the catalog habit or raise ApiError(404)."""
    log = activity_log.load(pdir)
    resolved_id = activity_log.resolve_habit_id(log, habit_ref)
    habit = log.habit_index().get(resolved_id) if resolved_id else None
    if habit is None:
        raise ApiError(
            404,
            "habit_not_found",
            f"Unknown habit for profile {pdir.name}: {habit_ref.strip()}",
        )
    return habit


@router.post(
    "/profiles/{name}/habits/{habit_id}/archive",
    response_model=HabitArchiveResponse,
    responses=HABIT_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def archive_profile_habit(
    name: str,
    habit_id: str,
    body: HabitArchiveRequest,
    response: Response,
    if_match: str | None = Header(default=None),
    user: CurrentUser = Depends(require_user),
) -> HabitArchiveResponse | JSONResponse:
    """Archive or unarchive one habit (``archived`` flag in activity-log.yaml).

    Archiving is reversible housekeeping: the habit entry and its whole
    check-in history stay on disk, and the habit leaves the active catalog
    (the projects-board ``habits`` list excludes it unless
    ``include_archived`` is set). A request matching the current state is a
    no-op (``changed=false``, nothing written). Honors ``If-Match`` against
    the activity-log.yaml ETag (412 on mismatch, fresh ETag in the header).
    """
    pdir = _resolve_profile(name)
    etag = _activity_log_etag(pdir)
    if not _if_match_satisfied(if_match, etag):
        return _kanban_error(
            412,
            "etag_mismatch",
            "activity-log.yaml changed since it was loaded; "
            "reload before archiving the habit.",
            etag,
        )
    habit = _resolve_habit_or_404(pdir, habit_id)
    changed = habit.archived != body.archived
    if changed:
        try:
            activity_log.set_habit_archived(
                pdir,
                habit.id,
                body.archived,
                expected_snapshot=file_state.snapshot_file(
                    pdir / activity_log.ACTIVITY_LOG_FILENAME
                ),
            )
        except file_state.FileConflictError:
            # TOCTOU closure: a concurrent write landed between the If-Match
            # check and the in-lock snapshot re-check.
            return _kanban_error(
                412,
                "etag_mismatch",
                "activity-log.yaml changed while archiving the habit; "
                "reload before retrying.",
                _activity_log_etag(pdir),
            )
        _record_agent_writeback(
            user,
            pdir.name,
            action="habit.archive",
            target_owner="work",
            note=(
                f"habit {'archive' if body.archived else 'unarchive'}: "
                f"{habit.title!r}"
            ),
            refs={"habit_id": habit.id, "archived": body.archived},
            changed_paths=[pdir / activity_log.ACTIVITY_LOG_FILENAME],
        )
    response.headers["ETag"] = _activity_log_etag(pdir)
    return HabitArchiveResponse(
        ok=True,
        habit_id=habit.id,
        archived=body.archived,
        changed=changed,
    )


@router.delete(
    "/profiles/{name}/habits/{habit_id}",
    response_model=HabitDeleteResponse,
    responses={
        **HABIT_MUTATION_RESPONSES,
        422: {
            "model": ErrorResponse,
            "description": "confirm_title does not match the habit title.",
        },
    },
    dependencies=PROFILE_DEPENDENCY,
)
def delete_profile_habit(
    name: str,
    habit_id: str,
    response: Response,
    body: HabitDeleteRequest | None = None,
    if_match: str | None = Header(default=None),
    user: CurrentUser = Depends(require_user),
) -> HabitDeleteResponse | JSONResponse:
    """Delete one habit and every check-in referencing it (confirmed).

    ``confirm_title`` must equal the habit's title exactly, else 422
    ``habit_delete_confirm_mismatch`` and nothing is written. The purge
    removes the catalog entry plus all its check-in rows and answers the
    removed count. ``record_chronicle=true`` appends a ``habit.deleted``
    chronicle entry (default off). Honors ``If-Match`` against the
    activity-log.yaml ETag (412 on mismatch, fresh ETag in the header).
    """
    pdir = _resolve_profile(name)
    etag = _activity_log_etag(pdir)
    if not _if_match_satisfied(if_match, etag):
        return _kanban_error(
            412,
            "etag_mismatch",
            "activity-log.yaml changed since it was loaded; "
            "reload before deleting the habit.",
            etag,
        )
    habit = _resolve_habit_or_404(pdir, habit_id)
    confirm = (body.confirm_title if body else "") or ""
    if confirm != habit.title:
        raise ApiError(
            422,
            "habit_delete_confirm_mismatch",
            "confirm_title must match the habit title exactly "
            f"({habit.title!r}).",
        )
    try:
        outcome = activity_log.delete_habit(
            pdir,
            habit.id,
            expected_snapshot=file_state.snapshot_file(
                pdir / activity_log.ACTIVITY_LOG_FILENAME
            ),
        )
    except file_state.FileConflictError:
        return _kanban_error(
            412,
            "etag_mismatch",
            "activity-log.yaml changed while deleting the habit; "
            "reload before retrying.",
            _activity_log_etag(pdir),
        )
    if outcome is None:
        # Vanished between the resolve and the locked delete.
        raise ApiError(
            404,
            "habit_not_found",
            f"Unknown habit for profile {pdir.name}: {habit_id.strip()}",
        )
    _habit, checkins_removed = outcome
    if body is not None and body.record_chronicle:
        _append_chronicle_entry(
            pdir,
            "habit.deleted",
            ref=habit.id,
            note=habit.title,
            snapshot=file_state.snapshot_file(
                pdir / chronicle_core.CHRONICLE_FILENAME
            ),
        )
    trace_paths = [pdir / activity_log.ACTIVITY_LOG_FILENAME]
    if body is not None and body.record_chronicle:
        trace_paths.append(pdir / chronicle_core.CHRONICLE_FILENAME)
    _record_agent_writeback(
        user,
        pdir.name,
        action="habit.delete",
        target_owner="work",
        note=(
            f"habit delete: {habit.title!r} "
            f"({checkins_removed} check-ins removed)"
        ),
        refs={"habit_id": habit.id, "checkins_removed": checkins_removed},
        changed_paths=trace_paths,
    )
    response.headers["ETag"] = _activity_log_etag(pdir)
    return HabitDeleteResponse(
        ok=True,
        deleted_id=habit.id,
        checkins_removed=checkins_removed,
    )


# --- Habit plans (阶段计划): short-range phase plans under one habit ---------


HABIT_PLAN_RESPONSES = {
    **ERROR_RESPONSES,
    404: {
        "model": ErrorResponse,
        "description": "Profile or habit plan not found.",
    },
    412: {
        "model": ErrorResponse,
        "description": "If-Match ETag does not match the activity log file.",
    },
    422: {
        "model": ErrorResponse,
        "description": (
            "Unknown habit, invalid date range, weekly_tasks not matching "
            "the plan's week count, or an illegal status transition."
        ),
    },
}


def _resolve_habit_plan_or_404(
    log: activity_log.ActivityLog,
    plan_id: str,
) -> activity_log.HabitPlan:
    """Look up a habit plan by id or raise ApiError(404)."""
    plan = log.habit_plan_index().get(plan_id.strip())
    if plan is None:
        raise ApiError(
            404,
            "habit_plan_not_found",
            f"Unknown habit plan for profile {log.profile}: "
            f"{plan_id.strip()}",
        )
    return plan


def _habit_plan_model(
    plan: activity_log.HabitPlan,
    log: activity_log.ActivityLog,
) -> HabitPlanModel:
    """Build the API model: stored fields plus computed progress."""
    progress = activity_log.habit_plan_progress(plan, log.checkins)
    return HabitPlanModel(
        id=plan.id,
        title=plan.title,
        habit_id=plan.habit_id,
        start_date=plan.start_date,
        end_date=plan.end_date,
        status=plan.status,
        weekly_tasks=[
            HabitPlanWeeklyTasksModel(week=entry.week, tasks=entry.tasks)
            for entry in plan.weekly_tasks
        ],
        current_week=progress.current_week,
        days_done=progress.days_done,
        days_total=progress.days_total,
        completion_rate=progress.completion_rate,
        weeks=[
            HabitPlanWeekProgressModel(**week.to_dict())
            for week in progress.weeks
        ],
    )


def _validate_plan_dates(start_raw: str, end_raw: str) -> tuple[str, str]:
    """Return clean inclusive ISO dates or raise ApiError(422)."""
    try:
        start = date.fromisoformat(start_raw.strip()).isoformat()
        end = date.fromisoformat(end_raw.strip()).isoformat()
    except ValueError:
        raise ApiError(
            422,
            "invalid_plan_dates",
            "start_date/end_date must be ISO dates (YYYY-MM-DD), got "
            f"{start_raw!r} / {end_raw!r}.",
        ) from None
    if end < start:
        raise ApiError(
            422,
            "invalid_plan_range",
            f"end_date {end} is before start_date {start}.",
        )
    return start, end


def _validate_plan_weekly_tasks(
    weekly_tasks: list[HabitPlanWeeklyTasksModel],
    start: str,
    end: str,
) -> list[activity_log.WeeklyTasks]:
    """Validate week coverage against the plan range (422 on mismatch).

    The plan range spans exactly ``ceil(days / 7)`` weeks; the request
    must carry those weeks numbered 1..N in order (tasks may be empty).
    """
    expected = activity_log.plan_week_count(
        activity_log.HabitPlan(id="", start_date=start, end_date=end)
    )
    numbers = [entry.week for entry in weekly_tasks]
    if numbers != list(range(1, expected + 1)):
        raise ApiError(
            422,
            "invalid_weekly_tasks",
            f"weekly_tasks must cover weeks 1..{expected} in order for "
            f"the range {start}..{end}; got weeks {numbers}.",
        )
    return [
        activity_log.WeeklyTasks(
            week=entry.week,
            tasks=[task.strip() for task in entry.tasks if task.strip()],
        )
        for entry in weekly_tasks
    ]


def _generate_plan_weekly_cards(
    pdir: Path,
    plan: activity_log.HabitPlan,
) -> list[str]:
    """Create one Queue kanban card per plan week; return the card ids.

    Each card is titled ``"<plan title> W<n>"`` with ``planned_start`` /
    ``planned_end`` set to the week window and the week's tasks as todos.
    ``project_id`` links to the first active project-board case whose
    ``habit_id`` matches the plan's habit; when no case qualifies the
    cards stay project-less. The write goes through
    ``save_kanban_with_merge`` so a concurrent kanban.md edit is merged,
    never overwritten.
    """
    board = load_project_board(pdir)
    project_id = ""
    for case in board.project_cases:
        if case.habit_id == plan.habit_id and case.status == "active":
            project_id = case.id
            break
    snapshot = file_state.snapshot_file(kanban_path(pdir))
    sections = parse_kanban(pdir)
    base = copy_kanban_sections(sections)
    added = 0
    for entry in plan.weekly_tasks:
        week_start, week_end = activity_log.plan_week_bounds(
            plan, entry.week
        )
        if not week_start:
            continue
        sections.setdefault(KANBAN_QUEUE, []).append(
            KanbanTask(
                title=f"{plan.title} W{entry.week}",
                planned_start=week_start,
                planned_end=week_end,
                todos=[
                    KanbanTodo(text=task)
                    for task in entry.tasks
                    if task.strip()
                ],
                project_id=project_id,
            )
        )
        added += 1
    if not added:
        return []
    ensured = ensure_kanban_task_ids(sections, pdir.name)
    result = save_kanban_with_merge(
        pdir,
        ensured,
        base,
        expected_snapshot=snapshot,
    )
    queue = result.sections.get(KANBAN_QUEUE) or []
    return [task.id for task in queue[-added:] if task.id]


def _validate_checkin_plan(
    pdir: Path,
    habit_ref: str,
    plan_id: str,
    when: str,
) -> int:
    """Validate a check-in's plan binding; return the plan week number.

    422 when the plan is unknown, belongs to another habit, is not
    ``active``, or the check-in date (default today) falls outside the
    plan window. On success the returned 1-based week number is stored on
    the check-in row.
    """
    log = activity_log.load(pdir)
    plan = log.habit_plan_index().get(plan_id)
    if plan is None:
        raise ApiError(
            422,
            "habit_plan_not_found",
            f"Unknown habit plan for profile {pdir.name}: {plan_id}",
        )
    canonical_habit = activity_log.resolve_habit_id(log, habit_ref)
    if canonical_habit is None or plan.habit_id != canonical_habit:
        raise ApiError(
            422,
            "habit_plan_habit_mismatch",
            f"Habit plan {plan_id} belongs to habit {plan.habit_id!r}, "
            f"not {habit_ref.strip()!r}.",
        )
    if plan.status != "active":
        raise ApiError(
            422,
            "habit_plan_not_active",
            f"Habit plan {plan_id} is {plan.status}; "
            "check-ins require an active plan.",
        )
    week_number = activity_log.plan_week_number(
        plan, when or date.today().isoformat()
    )
    if week_number is None:
        raise ApiError(
            422,
            "checkin_outside_plan_range",
            f"Check-in date {when or date.today().isoformat()} falls "
            f"outside habit plan {plan_id} "
            f"({plan.start_date}..{plan.end_date}).",
        )
    return week_number


@router.get(
    "/profiles/{name}/habit-plans",
    response_model=HabitPlanListResponse,
    responses=ERROR_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def list_profile_habit_plans(
    name: str,
    response: Response,
    habit_id: str = "",
    status: str = "",
) -> HabitPlanListResponse:
    """List the profile's habit plans with computed progress.

    Each entry carries ``current_week``, ``days_done`` / ``days_total``
    and a per-week breakdown (check-ins matching the plan id + habit
    within each week window). ``habit_id`` / ``status`` query params
    filter the list. The activity-log ETag rides the response header so
    clients can chain an If-Match mutation.
    """
    pdir = _resolve_profile(name)
    log = activity_log.load(pdir)
    plans = log.habit_plans
    habit_filter = habit_id.strip()
    if habit_filter:
        resolved = activity_log.resolve_habit_id(log, habit_filter)
        plans = [
            plan
            for plan in plans
            if plan.habit_id in {habit_filter, resolved or ""}
        ]
    status_filter = status.strip()
    if status_filter:
        plans = [plan for plan in plans if plan.status == status_filter]
    response.headers["ETag"] = _activity_log_etag(pdir)
    return HabitPlanListResponse(
        ok=True,
        profile=log.profile or pdir.name,
        plans=[_habit_plan_model(plan, log) for plan in plans],
    )


@router.post(
    "/profiles/{name}/habit-plans",
    response_model=HabitPlanMutationResponse,
    status_code=201,
    responses=HABIT_PLAN_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def create_profile_habit_plan(
    name: str,
    body: HabitPlanCreateRequest,
    response: Response,
    if_match: str | None = Header(default=None),
    user: CurrentUser = Depends(require_user),
) -> HabitPlanMutationResponse | JSONResponse:
    """Create one habit plan (阶段计划) under an existing habit.

    The plan stores only ``habit_id`` — project/goal context is derived
    through ``case.habit_id``. ``weekly_tasks`` must cover exactly
    ``ceil(days / 7)`` weeks numbered 1..N (the tail week may be
    partial). With ``generate_weekly_cards`` (default) each week also
    gets a Queue kanban card (``"<title> W<n>"``, week window as
    planned dates, tasks as todos, linked to the habit's first active
    project case when one exists). Honors ``If-Match`` against the
    activity-log.yaml ETag (412 on mismatch, fresh ETag in the header).
    """
    pdir = _resolve_profile(name)
    etag = _activity_log_etag(pdir)
    if not _if_match_satisfied(if_match, etag):
        return _kanban_error(
            412,
            "etag_mismatch",
            "activity-log.yaml changed since it was loaded; "
            "reload before creating the habit plan.",
            etag,
        )
    title = body.title.strip()
    if not title:
        raise ApiError(
            422, "invalid_habit_plan", "Habit plan title must not be blank."
        )
    log = activity_log.load(pdir)
    habit_id = activity_log.resolve_habit_id(log, body.habit_id)
    if habit_id is None:
        raise ApiError(
            422,
            "habit_plan_habit_not_found",
            f"Unknown habit for profile {pdir.name}: "
            f"{body.habit_id.strip()!r}.",
        )
    start, end = _validate_plan_dates(body.start_date, body.end_date)
    weekly_tasks = _validate_plan_weekly_tasks(
        body.weekly_tasks, start, end
    )
    plan = activity_log.HabitPlan(
        id="",
        title=title,
        habit_id=habit_id,
        start_date=start,
        end_date=end,
        status="active",
        weekly_tasks=weekly_tasks,
    )
    try:
        stored = activity_log.add_habit_plan(
            pdir,
            plan,
            expected_snapshot=file_state.snapshot_file(
                pdir / activity_log.ACTIVITY_LOG_FILENAME
            ),
        )
    except file_state.FileConflictError:
        # TOCTOU closure: a concurrent write landed between the If-Match
        # check and the in-lock snapshot re-check.
        return _kanban_error(
            412,
            "etag_mismatch",
            "activity-log.yaml changed while creating the habit plan; "
            "reload before retrying.",
            _activity_log_etag(pdir),
        )
    card_ids: list[str] = []
    if body.generate_weekly_cards:
        card_ids = _generate_plan_weekly_cards(pdir, stored)
    changed_paths = [pdir / activity_log.ACTIVITY_LOG_FILENAME]
    if card_ids:
        changed_paths.append(kanban_path(pdir))
    _record_agent_writeback(
        user,
        pdir.name,
        action="habit_plan.add",
        target_owner="work",
        note=f"habit plan add: {stored.title!r} ({habit_id})",
        refs={"plan_id": stored.id, "habit_id": habit_id},
        changed_paths=changed_paths,
    )
    response.headers["ETag"] = _activity_log_etag(pdir)
    fresh = activity_log.load(pdir)
    return HabitPlanMutationResponse(
        ok=True,
        plan=_habit_plan_model(stored, fresh),
        kanban_card_ids=card_ids,
    )


@router.patch(
    "/profiles/{name}/habit-plans/{plan_id}",
    response_model=HabitPlanMutationResponse,
    responses=HABIT_PLAN_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def patch_profile_habit_plan(
    name: str,
    plan_id: str,
    body: HabitPlanPatchRequest,
    response: Response,
    if_match: str | None = Header(default=None),
    user: CurrentUser = Depends(require_user),
) -> HabitPlanMutationResponse | JSONResponse:
    """Edit one habit plan: forward status flow plus title/weekly_tasks.

    ``status`` only moves forward: active -> completed/archived (a
    request naming the current status is a no-op; anything else is 422
    ``invalid_plan_status_transition``). ``weekly_tasks`` edits are
    re-validated against the plan's date range. Honors ``If-Match``
    against the activity-log.yaml ETag (412 on mismatch, fresh ETag in
    the header).
    """
    pdir = _resolve_profile(name)
    etag = _activity_log_etag(pdir)
    if not _if_match_satisfied(if_match, etag):
        return _kanban_error(
            412,
            "etag_mismatch",
            "activity-log.yaml changed since it was loaded; "
            "reload before updating the habit plan.",
            etag,
        )
    log = activity_log.load(pdir)
    plan = _resolve_habit_plan_or_404(log, plan_id)
    new_status: str | None = None
    if body.status is not None:
        candidate = body.status.strip()
        if candidate not in activity_log.HABIT_PLAN_STATUSES:
            raise ApiError(
                422,
                "invalid_plan_status",
                f"status must be one of "
                f"{', '.join(activity_log.HABIT_PLAN_STATUSES)}; "
                f"got {body.status!r}.",
            )
        if candidate != plan.status:
            allowed = activity_log.HABIT_PLAN_TRANSITIONS.get(
                plan.status, ()
            )
            if candidate not in allowed:
                raise ApiError(
                    422,
                    "invalid_plan_status_transition",
                    f"Cannot move habit plan {plan.id} from "
                    f"{plan.status} to {candidate}.",
                )
            new_status = candidate
    new_title: str | None = None
    if body.title is not None:
        if not body.title.strip():
            raise ApiError(
                422,
                "invalid_habit_plan",
                "Habit plan title must not be blank.",
            )
        new_title = body.title.strip()
    new_weekly: list[activity_log.WeeklyTasks] | None = None
    if body.weekly_tasks is not None:
        new_weekly = _validate_plan_weekly_tasks(
            body.weekly_tasks, plan.start_date, plan.end_date
        )
    if new_status is None and new_title is None and new_weekly is None:
        response.headers["ETag"] = _activity_log_etag(pdir)
        return HabitPlanMutationResponse(
            ok=True, plan=_habit_plan_model(plan, log)
        )
    try:
        updated = activity_log.update_habit_plan(
            pdir,
            plan.id,
            status=new_status,
            title=new_title,
            weekly_tasks=new_weekly,
            expected_snapshot=file_state.snapshot_file(
                pdir / activity_log.ACTIVITY_LOG_FILENAME
            ),
        )
    except file_state.FileConflictError:
        # TOCTOU closure: a concurrent write landed between the If-Match
        # check and the in-lock snapshot re-check.
        return _kanban_error(
            412,
            "etag_mismatch",
            "activity-log.yaml changed while updating the habit plan; "
            "reload before retrying.",
            _activity_log_etag(pdir),
        )
    if updated is None:
        # Vanished between the resolve and the locked update.
        raise ApiError(
            404,
            "habit_plan_not_found",
            f"Unknown habit plan for profile {pdir.name}: {plan_id.strip()}",
        )
    _record_agent_writeback(
        user,
        pdir.name,
        action="habit_plan.update",
        target_owner="work",
        note=f"habit plan update: {updated.title!r} ({updated.status})",
        refs={"plan_id": updated.id, "status": updated.status},
        changed_paths=[pdir / activity_log.ACTIVITY_LOG_FILENAME],
    )
    response.headers["ETag"] = _activity_log_etag(pdir)
    fresh = activity_log.load(pdir)
    return HabitPlanMutationResponse(
        ok=True, plan=_habit_plan_model(updated, fresh)
    )


# --- Habit-plan templates (Phase 2): click-to-instantiate plans -------------


def _plan_templates_etag(pdir: Path) -> str:
    """Weak ETag over the plan-template mutation's source files.

    Covers plan-templates.yaml (usage history), project-board.yaml, and
    activity-log.yaml — the three files instantiate writes. Weak (``W/``)
    because the hash identifies the source file versions, not the JSON
    response bytes.
    """
    fingerprints = []
    for relative in (
        plan_templates.PLAN_TEMPLATES_FILENAME,
        "project-board.yaml",
        activity_log.ACTIVITY_LOG_FILENAME,
    ):
        snapshot = file_state.snapshot_file(pdir / relative)
        fingerprints.append(f"{relative}:{snapshot.sha256 or 'empty'}")
    digest = hashlib.sha256("|".join(fingerprints).encode("utf-8")).hexdigest()
    return f'W/"{digest}"'


def _plan_templates_error(
    status_code: int,
    code: str,
    message: str,
    etag: str,
) -> JSONResponse:
    """4xx body plus a fresh plan-templates ETag header."""
    body = ErrorResponse(code=code, message=message)
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(),
        headers={"ETag": etag},
    )


def _plan_template_model(
    template: plan_templates.PlanTemplate,
) -> PlanTemplateModel:
    """Convert one core plan template to the API model."""
    return PlanTemplateModel(
        id=template.id,
        title=template.title,
        summary=template.summary,
        duration_days=template.duration_days,
        habit=PlanTemplateHabitModel(
            title=template.habit_title,
            kind=template.habit_kind,
            cadence=template.cadence,
            target_count=template.target.count,
            target_unit=template.target.unit,
        ),
        milestones=[
            PlanTemplateMilestoneModel(
                title=milestone.title, offset_days=milestone.offset_days
            )
            for milestone in template.milestones
        ],
        builtin=template.builtin,
    )


@router.get(
    "/profiles/{name}/plan-templates",
    response_model=PlanTemplateListResponse,
    responses=ERROR_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def get_profile_plan_templates(
    name: str, response: Response
) -> PlanTemplateListResponse:
    """Built-in habit-plan templates plus the profile's usage history.

    Profile-scoped (rather than a global ``/plan-templates``) because the
    history half only exists per profile; history comes from the profile's
    plan-templates.yaml, de-duplicated by template id, most recent first.
    The response carries the plan-templates ETag for use as ``If-Match`` on
    instantiate.
    """
    pdir = _resolve_profile(name)
    response.headers["ETag"] = _plan_templates_etag(pdir)
    return PlanTemplateListResponse(
        profile=pdir.name,
        builtin=[
            _plan_template_model(template)
            for template in plan_templates.load_builtin_templates()
        ],
        history=[
            PlanTemplateUsageModel(
                template_id=str(entry.get("template_id") or ""),
                title=str(entry.get("title") or ""),
                used_at=str(entry.get("used_at") or ""),
                project_id=str(entry.get("project_id") or ""),
                habit_id=str(entry.get("habit_id") or ""),
            )
            for entry in plan_templates.load_plan_history(pdir)
        ],
    )


PLAN_TEMPLATE_MUTATION_RESPONSES = {
    **ERROR_RESPONSES,
    412: {
        "model": ErrorResponse,
        "description": "If-Match ETag does not match the plan source files.",
    },
    422: {
        "model": ErrorResponse,
        "description": (
            "Unknown template id, missing template, invalid start date, "
            "or duplicate/invalid project case."
        ),
    },
}


def _resolve_plan_template(
    body: PlanTemplateInstantiateRequest,
) -> plan_templates.PlanTemplate:
    """Resolve the request's template (built-in by id, or inline)."""
    if body.template is not None:
        template = plan_templates.PlanTemplate.from_dict(body.template)
        if not template.title:
            raise ApiError(
                422,
                "invalid_plan_template",
                "An inline template needs at least a title.",
            )
        return template
    template_id = body.template_id.strip()
    if not template_id:
        raise ApiError(
            422,
            "plan_template_required",
            "A template_id (built-in) or an inline template is required.",
        )
    template = plan_templates.builtin_template_index().get(template_id)
    if template is None:
        raise ApiError(
            422,
            "unknown_plan_template",
            f"Unknown built-in plan template: {template_id} "
            "(pass an inline template object for custom plans).",
        )
    return template


@router.post(
    "/profiles/{name}/plan-templates/instantiate",
    response_model=PlanTemplateInstantiateResponse,
    status_code=201,
    responses=PLAN_TEMPLATE_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def instantiate_profile_plan_template(
    name: str,
    body: PlanTemplateInstantiateRequest,
    response: Response,
    if_match: str | None = Header(default=None),
    user: CurrentUser = Depends(require_user),
) -> PlanTemplateInstantiateResponse | JSONResponse:
    """Instantiate one habit-plan template into a project case + habit.

    Creates a ``kind=habit-plan`` case in project-board.yaml (time_range
    from ``start`` + ``duration_days``, milestone dates from the template's
    offsets, explicit ``habit_id`` link), ensures the suggested habit
    exists in activity-log.yaml (created when missing, reused by
    id/title otherwise), and remembers the usage in the profile's
    plan-templates.yaml. The projects-board aggregation renders the new
    case as a habit lane immediately. Honors ``If-Match`` (412 on
    mismatch, fresh ETag in the header); each file write re-checks its
    request-start snapshot inside its write lock.
    """
    pdir = _resolve_profile(name)
    etag = _plan_templates_etag(pdir)
    if not _if_match_satisfied(if_match, etag):
        return _plan_templates_error(
            412,
            "etag_mismatch",
            "Plan source files changed since they were loaded; "
            "reload before instantiating.",
            etag,
        )
    template = _resolve_plan_template(body)
    start_text = body.start.strip()
    if start_text:
        try:
            start = date.fromisoformat(start_text)
        except ValueError:
            raise ApiError(
                422,
                "invalid_plan_start",
                f"start must be an ISO date (YYYY-MM-DD), got "
                f"{body.start!r}.",
            ) from None
    else:
        start = date.today()
    snapshots = {
        "board": file_state.snapshot_file(pdir / "project-board.yaml"),
        "activity_log": file_state.snapshot_file(
            pdir / activity_log.ACTIVITY_LOG_FILENAME
        ),
        "history": file_state.snapshot_file(
            pdir / plan_templates.PLAN_TEMPLATES_FILENAME
        ),
    }
    try:
        # Habit first: explicit override wins, else the template's title;
        # an existing habit (id or title) is reused, otherwise created.
        log = activity_log.load(pdir)
        habit_ref = body.habit_id.strip() or template.habit_title
        resolved = activity_log.resolve_habit_id(log, habit_ref)
        created_habit = resolved is None
        habit = activity_log.add_habit(
            pdir,
            habit_ref,
            kind=template.habit_kind,
            cadence=template.cadence,
            target=template.target,
            expected_snapshot=snapshots["activity_log"],
        )
        case_fields = plan_templates.plan_case_fields(
            template, title=body.title, start=start
        )

        def _add_case(board: ProjectBoard) -> ProjectCase:
            return add_project_case(
                board,
                case_fields["title"],
                kind=case_fields["kind"],
                time_range=case_fields["time_range"],
                summary=case_fields["summary"],
                goal_refs=body.goal_refs,
                milestones=case_fields["milestones"],
                habit_id=habit.id,
            )

        case = update_project_board(
            pdir, _add_case, expected_snapshot=snapshots["board"]
        )
        template_id = template.id or f"inline:{case.id}"
        plan_templates.record_plan_usage(
            pdir,
            {
                "template_id": template_id,
                "title": case.title,
                "project_id": case.id,
                "habit_id": habit.id,
            },
            expected_snapshot=snapshots["history"],
        )
    except ValueError as exc:
        raise ApiError(422, "invalid_plan_instantiate", str(exc)) from exc
    except file_state.FileConflictError:
        # A concurrent write landed between the If-Match check and one of
        # the in-lock snapshot re-checks (TOCTOU closure).
        return _plan_templates_error(
            412,
            "etag_mismatch",
            "Plan source files changed while instantiating; "
            "reload before retrying.",
            _plan_templates_etag(pdir),
        )
    fresh_case = _project_case_model(
        case,
        _task_section_index(pdir),
        _live_section_tasks(pdir),
        _archive_tasks(pdir),
    )
    _record_agent_writeback(
        user,
        pdir.name,
        action="plan_template.instantiate",
        note=(
            f"plan instantiate: {case.title!r} "
            f"(template {template_id}, habit {habit.id})"
        ),
        refs={
            "template_id": template_id,
            "project_id": case.id,
            "habit_id": habit.id,
            "created_habit": created_habit,
        },
        changed_paths=[
            pdir / "project-board.yaml",
            pdir / activity_log.ACTIVITY_LOG_FILENAME,
            pdir / plan_templates.PLAN_TEMPLATES_FILENAME,
        ],
    )
    response.headers["ETag"] = _plan_templates_etag(pdir)
    return PlanTemplateInstantiateResponse(
        ok=True,
        case=fresh_case,
        template_id=template_id,
        habit_id=habit.id,
        created_habit=created_habit,
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

    Kept as the synchronous contract for backward compatibility; the SPA
    now dispatches this LLM long task as an async ``studio-jd-match`` job
    (``POST /profiles/{name}/jobs``, 分析中/生成中 phases over SSE) instead,
    with the same error codes surfaced as the job's structured error.
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


# --- Public Build (M5): validate / build / publish the static public site -----

# Cap on the flat artifact listing in the overview; totals stay accurate.
_PUBLIC_BUILD_ARTIFACT_LIMIT = 300

PUBLIC_BUILD_MUTATION_RESPONSES = {
    **ERROR_RESPONSES,
    404: {
        "model": ErrorResponse,
        "description": "Profile, build artifact, or preview page not found.",
    },
    412: {
        "model": ErrorResponse,
        "description": "If-Match ETag does not match the public-layer files.",
    },
    422: {
        "model": ErrorResponse,
        "description": (
            "Public layer not initialized, validation/visibility gate "
            "failed, invalid base URL, no drafts selected, or a draft "
            "failed publish-readiness validation."
        ),
    },
}


def _public_build_output_dir(name: str) -> Path:
    """Server-pinned static-site output directory.

    Same default as ``core.public_site.build_public_site`` (``dist/public/
    <name>`` under the data root — the sandbox root on the isolated dev
    stack). Pinned server-side: unlike the Streamlit form, the API does not
    accept a free-form output path.
    """
    return (REPO_ROOT / "dist" / "public" / name).resolve()


def _public_build_initialized(pdir: Path) -> bool:
    """Same four-file public-layer gate as the Streamlit page / studio."""
    return all(
        (pdir / filename).exists()
        for filename in (
            PUBLIC_PROFILE_FILENAME,
            RESUME_SOURCE_FILENAME,
            PROJECTS_FILENAME,
            OUTPUTS_FILENAME,
        )
    )


def _public_build_state(output_dir: Path) -> PublicBuildStateModel:
    """Derive the build-state card from the output directory itself.

    No build log is kept anywhere (Streamlit parity): the newest artifact
    mtime stands in for the last build time, and the flat listing (capped
    at ``_PUBLIC_BUILD_ARTIFACT_LIMIT``) feeds the artifact links.
    """
    state = PublicBuildStateModel(output_dir=str(output_dir))
    if not output_dir.is_dir():
        return state
    newest = 0.0
    artifacts: list[PublicBuildArtifactModel] = []
    for path in sorted(output_dir.rglob("*")):
        if not path.is_file():
            continue
        stat = path.stat()
        state.total_files += 1
        state.total_bytes += stat.st_size
        newest = max(newest, stat.st_mtime)
        if len(artifacts) < _PUBLIC_BUILD_ARTIFACT_LIMIT:
            artifacts.append(
                PublicBuildArtifactModel(
                    path=path.relative_to(output_dir).as_posix(),
                    size=stat.st_size,
                    modified=datetime.fromtimestamp(stat.st_mtime).isoformat(
                        timespec="seconds"
                    ),
                )
            )
    state.exists = state.total_files > 0
    state.artifacts_truncated = state.total_files > len(artifacts)
    state.artifacts = artifacts
    if newest:
        state.built_at = datetime.fromtimestamp(newest).isoformat(timespec="seconds")
    return state


@router.get(
    "/profiles/{name}/public-build",
    response_model=PublicBuildResponse,
    responses=ERROR_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def get_profile_public_build(name: str, response: Response) -> PublicBuildResponse:
    """Public Build overview: init gate, validation, drafts, output state.

    Read-only aggregation of the Streamlit page's status surface: the
    four-file public-layer gate, the ``validate_public_layer`` outcome
    (errors block a build), the unpublished blog drafts offered by the
    publish-and-build section, and the observed output-directory state.
    Carries the public-layer ETag (same fingerprint as the studio) for
    ``If-Match`` on the build mutations.
    """
    pdir = _resolve_profile(name)
    initialized = _public_build_initialized(pdir)
    validation: PublicBuildValidationModel | None = None
    drafts: list[PublicBuildDraftModel] = []
    if initialized:
        result = validate_public_layer(pdir.name, include_drafts=False)
        validation = PublicBuildValidationModel(
            ok=result.ok,
            errors=list(result.errors),
            warnings=list(result.warnings),
        )
        drafts = [
            PublicBuildDraftModel(slug=post.slug, title=post.title, date=post.date)
            for post in load_blog_posts(pdir.name, include_drafts=True)
            if post.status == "draft"
        ]
    response.headers["ETag"] = _studio_etag(pdir)
    return PublicBuildResponse(
        profile=pdir.name,
        initialized=initialized,
        validation=validation,
        drafts=drafts,
        build=_public_build_state(_public_build_output_dir(pdir.name)),
    )


def _run_public_build(
    pdir: Path,
    body: PublicBuildRequest,
    *,
    published: list[str],
) -> PublicBuildResultResponse | JSONResponse:
    """Shared synchronous build step for build / publish-and-build.

    The core builder is deterministic file rendering (no LLM, no network),
    so it runs inline like the Streamlit button. Validation and visibility
    failures surface as 422 ``public_build_blocked`` with the core message
    and write nothing (the core validates before touching the output dir).
    """
    try:
        result = build_public_site(
            pdir.name,
            out_dir=_public_build_output_dir(pdir.name),
            include_drafts=body.include_drafts,
            base_url=body.base_url,
        )
    except PublicSiteError as exc:
        return _studio_error(
            422, "public_build_blocked", str(exc), _studio_etag(pdir)
        )
    return PublicBuildResultResponse(
        output_dir=str(result.output_dir),
        page_count=len(result.pages),
        pages=[
            page.relative_to(result.output_dir).as_posix() for page in result.pages
        ],
        published=published,
    )


@router.post(
    "/profiles/{name}/public-build/build",
    response_model=PublicBuildResultResponse,
    responses=PUBLIC_BUILD_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def build_profile_public_site(
    name: str,
    body: PublicBuildRequest,
    response: Response,
    if_match: str | None = Header(default=None),
) -> PublicBuildResultResponse | JSONResponse:
    """Build the static public site into the server-pinned output dir.

    Thin wrapper over ``core.public_site.build_public_site``: the core
    validates first (errors → 422 ``public_build_blocked``) and requires
    ``visibility: public`` unless ``include_drafts`` is set (preview mode).
    Honors ``If-Match`` against the public-layer ETag (412 on mismatch).
    """
    pdir = _resolve_profile(name)
    etag = _studio_etag(pdir)
    if not _if_match_satisfied(if_match, etag):
        return _studio_error(
            412,
            "etag_mismatch",
            "Public layer files changed since they were loaded; "
            "reload before building.",
            etag,
        )
    if not _public_build_initialized(pdir):
        raise ApiError(
            422,
            "public_layer_not_initialized",
            "Initialize the public layer first (POST /studio/init).",
        )
    result = _run_public_build(pdir, body, published=[])
    if isinstance(result, PublicBuildResultResponse):
        response.headers["ETag"] = _studio_etag(pdir)
    return result


@router.post(
    "/profiles/{name}/public-build/publish-and-build",
    response_model=PublicBuildResultResponse,
    responses=PUBLIC_BUILD_MUTATION_RESPONSES,
    dependencies=PROFILE_DEPENDENCY,
)
def publish_and_build_profile_public_site(
    name: str,
    body: PublicBuildPublishRequest,
    response: Response,
    if_match: str | None = Header(default=None),
) -> PublicBuildResultResponse | JSONResponse:
    """Publish the selected blog drafts, then build the static site.

    Mirrors the Streamlit "发布草稿并构建" section: each slug goes through
    ``publish_blog_post`` (full publish-readiness gate); the first failure
    answers 422 ``public_publish_failed`` naming the slug, earlier slugs
    stay published, and nothing is built. Honors ``If-Match`` against the
    public-layer ETag (412 on mismatch) — publishing flips blog statuses.
    """
    pdir = _resolve_profile(name)
    etag = _studio_etag(pdir)
    if not _if_match_satisfied(if_match, etag):
        return _studio_error(
            412,
            "etag_mismatch",
            "Public layer files changed since they were loaded; "
            "reload before publishing.",
            etag,
        )
    if not _public_build_initialized(pdir):
        raise ApiError(
            422,
            "public_layer_not_initialized",
            "Initialize the public layer first (POST /studio/init).",
        )
    slugs = [slug.strip() for slug in body.slugs if slug.strip()]
    if not slugs:
        raise ApiError(
            422,
            "invalid_public_publish",
            "Select at least one draft to publish.",
        )
    published: list[str] = []
    for slug in slugs:
        try:
            publish_blog_post(pdir.name, slug)
        except PublicSiteError as exc:
            return _studio_error(
                422,
                "public_publish_failed",
                f"Failed to publish {slug}: {exc}",
                _studio_etag(pdir),
            )
        published.append(slug)
    result = _run_public_build(pdir, body, published=published)
    if isinstance(result, PublicBuildResultResponse):
        response.headers["ETag"] = _studio_etag(pdir)
    return result


@router.get(
    "/profiles/{name}/public-build/artifacts/{path:path}",
    responses={
        **ERROR_RESPONSES,
        404: {
            "model": ErrorResponse,
            "description": "Profile not found, or artifact missing/escapes the output dir.",
        },
    },
    dependencies=PROFILE_DEPENDENCY,
)
def get_profile_public_build_artifact(name: str, path: str) -> FileResponse:
    """Serve one file from the build output directory (preview/download).

    Path-traversal guarded: anything resolving outside the pinned output
    directory answers 404, same as a missing file. Auth follows the same
    profile scope as every other route — a preview build may contain
    drafts/private content, so artifacts are not public here.
    """
    pdir = _resolve_profile(name)
    output_dir = _public_build_output_dir(pdir.name)
    target = (output_dir / path).resolve()
    try:
        target.relative_to(output_dir)
    except ValueError as exc:
        raise ApiError(
            404, "public_build_artifact_not_found", f"Unknown artifact: {path}"
        ) from exc
    if not target.is_file():
        raise ApiError(
            404, "public_build_artifact_not_found", f"Unknown artifact: {path}"
        )
    return FileResponse(target)


@router.get(
    "/profiles/{name}/public-build/preview",
    response_model=PublicBuildPreviewResponse,
    responses={
        **ERROR_RESPONSES,
        422: {
            "model": ErrorResponse,
            "description": "Public layer not initialized.",
        },
    },
    dependencies=PROFILE_DEPENDENCY,
)
def get_profile_public_build_preview(
    name: str, include_drafts: bool = Query(default=True)
) -> PublicBuildPreviewResponse:
    """List the renderable site pages for the in-memory preview picker.

    Warnings mirror ``render_public_site_preview``: validation warnings
    plus each validation error prefixed ``preview validation:`` (the
    preview renders even when a production build would be blocked). The
    per-page HTML comes from ``GET .../preview/page?path=<rel>``.
    """
    pdir = _resolve_profile(name)
    if not _public_build_initialized(pdir):
        raise ApiError(
            422,
            "public_layer_not_initialized",
            "Initialize the public layer first (POST /studio/init).",
        )
    rendered = render_public_site_pages(pdir.name, include_drafts=include_drafts)
    validation = validate_public_layer(pdir.name, include_drafts=include_drafts)
    warnings = list(validation.warnings)
    warnings.extend(f"preview validation: {error}" for error in validation.errors)
    return PublicBuildPreviewResponse(
        include_drafts=include_drafts,
        pages=[
            PublicBuildPreviewPageModel(
                path=rel, title=rendered.page_titles.get(rel, rel)
            )
            for rel in rendered.pages
        ],
        warnings=warnings,
    )


@router.get(
    "/profiles/{name}/public-build/preview/page",
    responses={
        **ERROR_RESPONSES,
        404: {
            "model": ErrorResponse,
            "description": "Profile or preview page not found.",
        },
        422: {
            "model": ErrorResponse,
            "description": "Public layer not initialized.",
        },
    },
    dependencies=PROFILE_DEPENDENCY,
    response_class=HTMLResponse,
)
def get_profile_public_build_preview_page(
    name: str,
    path: str = Query(default="index.html"),
    include_drafts: bool = Query(default=True),
) -> HTMLResponse:
    """Render one preview page as self-contained HTML (inline CSS/media).

    Same payload the Streamlit page iframes via ``components.html``: CSS
    and local media are inlined as data URIs, so the page renders stand-
    alone in the SPA iframe. Unknown page paths answer 404.
    """
    pdir = _resolve_profile(name)
    if not _public_build_initialized(pdir):
        raise ApiError(
            422,
            "public_layer_not_initialized",
            "Initialize the public layer first (POST /studio/init).",
        )
    preview = render_public_site_preview(pdir.name, include_drafts=include_drafts)
    html = preview.pages.get(path)
    if html is None:
        raise ApiError(
            404, "public_preview_page_not_found", f"Unknown preview page: {path}"
        )
    return HTMLResponse(content=html)


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
    # compact=1: the embedded dashboard drops its permanent inspector rail in
    # favour of an on-demand drawer (implemented in the home_dashboard
    # component), so the 3D galaxy keeps the full iframe width at hero sizes.
    return SidecarInfoModel(
        base=base,
        configured=configured,
        auth_enabled=auth_on,
        handoff_token=handoff,
        paper_library_url=f"{base}/paper-library?{query}",
        dashboard_url=f"{base}/dashboard?{query}&embed=1&view=3d&compact=1",
    )


def _north_star_model(pdir: Path) -> NorthStarModel:
    """Owner-facing North Star (same projection as the goals endpoint)."""
    identity = parse_identity_fields(profile_io.load_skill_md(pdir.name))
    return _north_star_from_identity(identity)


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
