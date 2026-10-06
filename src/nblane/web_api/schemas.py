"""Pydantic v2 response models for the nblane FastAPI backend."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    """Structured error body returned for 4xx responses."""

    code: str
    message: str


class HealthResponse(BaseModel):
    """Liveness probe payload."""

    ok: bool = True
    version: str


class LlmConnectionResponse(BaseModel):
    """Deployment-wide LLM connection with the API key always redacted."""

    base_url: str = ""
    model: str = ""
    api_key_set: bool = False
    configured: bool = False


class LlmConnectionUpdateRequest(BaseModel):
    """Update the deployment LLM connection.

    An omitted/empty ``api_key`` keeps the current key.  ``clear_api_key`` is
    the explicit operation for removing it.
    """

    base_url: str | None = None
    model: str | None = None
    api_key: str = ""
    clear_api_key: bool = False


class LlmConnectionVerifyResponse(BaseModel):
    """Result of a minimal provider connection check."""

    ok: bool
    detail: str = ""


class ProfileSettingsPatch(BaseModel):
    """Safe profile-scoped preferences patch.

    The nested mappings are intentionally flexible because action names are
    an extensible registry.  The core normalizer remains the whitelist and
    strips secret-looking keys before anything is written.
    """

    ai: dict[str, Any] | None = None
    kanban: dict[str, Any] | None = None
    evidence_review: dict[str, Any] | None = None
    project_board: dict[str, Any] | None = None
    research: dict[str, Any] | None = None


class ProfileSettingsResponse(BaseModel):
    """Normalized non-secret settings for one profile."""

    profile: str
    preferences: dict[str, Any] = Field(default_factory=dict)


class CodexStatusResponse(BaseModel):
    """Non-secret Codex CLI readiness information."""

    installed: bool = False
    bin_path: str = ""
    resolved_path: str = ""
    version: str = ""
    logged_in: bool = False
    login_status: str = ""
    cloud_env_id: str = ""
    cloud_env_configured: bool = False
    install_command: str = ""
    upgrade_command: str = ""
    error: str = ""


class CodexSettingsPatch(BaseModel):
    """Non-auth Codex profile settings."""

    bin_path: str | None = None
    cloud_env_id: str | None = None
    model: str | None = None
    attempts: int | None = Field(default=None, ge=1)
    branch: str | None = None
    timeout_seconds: float | None = Field(default=None, ge=5)


class CodexSettingsResponse(BaseModel):
    """Codex profile settings with no authentication material."""

    profile: str
    settings: dict[str, str | int | float] = Field(default_factory=dict)


class ProfileSummary(BaseModel):
    """One row of the profile list endpoint."""

    name: str
    skill_schema: str = ""
    skill_tree_updated: str = ""
    skill_node_count: int = 0
    current_goal_title: str = ""


class SkillTreeSummary(BaseModel):
    """Skill-tree statistics for one profile."""

    skill_schema: str = ""
    updated: str = ""
    node_count: int = 0
    status_counts: dict[str, int] = Field(default_factory=dict)


class SkillNodeProgressModel(BaseModel):
    """Progression readout for one skill node (core.skill_progression).

    ``score`` sums the node's non-deprecated evidence_refs (weak/medium/
    strong = 1/10/100, plus 1000 per breakthrough row); ``next_rung`` /
    ``threshold_next`` describe the rung above the current YAML status
    (both null at expert); ``eligible`` means the node qualifies for a
    rung-up prompt (score threshold met, or at least one breakthrough).
    """

    score: int = 0
    next_rung: str | None = None
    threshold_next: int | None = None
    breakthrough_count: int = 0
    eligible: bool = False


class SkillTreeNodeModel(BaseModel):
    """One node in the recursive skill-tree view.

    ``title`` comes from the domain schema ``label`` (node id as fallback);
    ``children`` are derived from schema ``requires`` edges restricted to
    the profile overlay; ``evidence_count`` counts resolved evidence (pool
    refs plus inline rows, deprecated/missing refs excluded). ``category``
    is the schema grouping (empty for nodes unknown to the schema) — the
    home starmap uses it to size its sector band. ``progress`` is the
    tunable rung-up readout (see ``SkillNodeProgressModel``).
    """

    id: str
    title: str = ""
    status: str = "locked"
    category: str = ""
    evidence_count: int = 0
    progress: SkillNodeProgressModel = Field(
        default_factory=SkillNodeProgressModel
    )
    children: list[SkillTreeNodeModel] = Field(default_factory=list)


class SkillTreeCategoryModel(BaseModel):
    """Per-category rollup for the category banner headers.

    ``name`` is the zh display name (``core.starmap_snapshot.CATEGORY_ZH``,
    id as fallback) — the same source the home starmap sector band uses, so
    the skill-tree banners and the starmap agree on 官名 lookup keys.
    ``lit_count`` folds solid+expert (the 点亮 tier); locked = count − lit −
    learning.
    """

    id: str
    name: str = ""
    count: int = 0
    lit_count: int = 0
    learning_count: int = 0


class SkillTreeResponse(BaseModel):
    """Full skill tree: queue-wide status counters plus the nested nodes."""

    profile: str
    schema_name: str = ""
    updated: str = ""
    status_counts: dict[str, int] = Field(default_factory=dict)
    nodes: list[SkillTreeNodeModel] = Field(default_factory=list)
    categories: list[SkillTreeCategoryModel] = Field(default_factory=list)


class SkillNodePatchRequest(BaseModel):
    """Body for the skill-node status mutation (G3, 三态 write).

    The UI vocabulary is the starmap 三态 — ``locked`` / ``learning`` /
    ``lit``; the endpoint maps ``lit`` onto the YAML status ``solid`` (the
    精通 rung ``expert`` is review-earned and not settable here)."""

    status: str


class SkillNodePatchResponse(BaseModel):
    """Result of the skill-node status mutation (``status`` is post-map YAML)."""

    ok: bool = True
    node_id: str
    status: str = ""
    previous_status: str = ""
    changed: bool = False


class GoalSummary(BaseModel):
    """The profile's primary (current) goal, if any."""

    id: str
    title: str = ""
    status: str = ""
    target: str = ""


class KanbanSummary(BaseModel):
    """Kanban task counts per board section."""

    section_counts: dict[str, int] = Field(default_factory=dict)
    total: int = 0


class EvidenceSummary(BaseModel):
    """Evidence-pool entry and claim counts."""

    entries: int = 0
    claims: int = 0


class ProfileDetailSummary(BaseModel):
    """Structured profile summary (JSON counterpart of profile-summary.md)."""

    profile: str
    skill_tree: SkillTreeSummary = Field(default_factory=SkillTreeSummary)
    current_goal: GoalSummary | None = None
    kanban: KanbanSummary = Field(default_factory=KanbanSummary)
    evidence: EvidenceSummary = Field(default_factory=EvidenceSummary)


class HealthIssueModel(BaseModel):
    """One actionable profile health finding."""

    severity: str
    category: str
    title: str
    detail: str = ""
    action: str = ""


class HealthReportModel(BaseModel):
    """Health report for one profile (mirrors core HealthReport)."""

    profile: str
    can_publish_context: bool
    summary_counts: dict[str, int] = Field(default_factory=dict)
    issues: list[HealthIssueModel] = Field(default_factory=list)


class ActivitySummaryModel(BaseModel):
    """Counters over the whole Agent Activity queue (unfiltered)."""

    status: dict[str, int] = Field(default_factory=dict)
    kind: dict[str, int] = Field(default_factory=dict)
    target_owner: dict[str, int] = Field(default_factory=dict)
    candidate_type: dict[str, int] = Field(default_factory=dict)


class ActivityItemModel(BaseModel):
    """One normalized Agent Activity item (extension keys preserved)."""

    model_config = ConfigDict(extra="allow")

    id: str
    kind: str = "candidate"
    candidate_type: str = "unknown"
    source_page: str = ""
    source_ref: str = ""
    target_owner: str = ""
    status: str = "pending"
    title: str = ""
    summary: str = ""
    refs: dict[str, Any] = Field(default_factory=dict)
    payload: dict[str, Any] = Field(default_factory=dict)
    preview: str = ""
    warnings: list[str] = Field(default_factory=list)
    error: str = ""
    changed_paths: list[str] = Field(default_factory=list)
    created: str = ""
    updated: str = ""
    applied_at: str = ""


class ActivityListResponse(BaseModel):
    """Filtered activity items plus queue-wide summary counters."""

    profile: str
    status: str = "pending"
    kind: str = ""
    limit: int = 50
    total: int = 0
    items: list[ActivityItemModel] = Field(default_factory=list)
    summary: ActivitySummaryModel = Field(default_factory=ActivitySummaryModel)


class ActivityDismissRequest(BaseModel):
    """Optional body for the dismiss mutation."""

    note: str = ""


class ActivityApplyResponse(BaseModel):
    """Success body for the apply mutation."""

    ok: bool = True
    item: ActivityItemModel
    warnings: list[str] = Field(default_factory=list)
    changed_paths: list[str] = Field(default_factory=list)


class ActivityDismissResponse(BaseModel):
    """Success body for the dismiss mutation."""

    ok: bool = True
    item: ActivityItemModel


class AIExceptionBulkDismissRequest(BaseModel):
    """Activity-backed exception ids to dismiss in one write."""

    ids: list[str] = Field(default_factory=list, min_length=1, max_length=200)
    note: str = ""


class AIExceptionBulkDismissResponse(BaseModel):
    """Result of dismissing activity-backed AI exceptions."""

    ok: bool = True
    dismissed: int = 0
    skipped: list[str] = Field(default_factory=list)


class ActivityItemErrorResponse(ErrorResponse):
    """Error body that also carries the current activity item."""

    item: ActivityItemModel | None = None


class AIExceptionModel(BaseModel):
    """One unresolved failure that needs attention from the profile owner."""

    id: str
    source: str = ""
    title: str = ""
    message: str = ""
    action: str = ""
    source_ref: str = ""
    created: str = ""
    severity: str = "error"
    retryable: bool = True
    href: str = ""


class AIExceptionsResponse(BaseModel):
    """Profile-scoped AI failures from gateway, agents, jobs, and writebacks."""

    profile: str
    total: int = 0
    items: list[AIExceptionModel] = Field(default_factory=list)


class KanbanSubtaskModel(BaseModel):
    """One checkbox sub-item under a kanban card."""

    title: str
    done: bool = False


class KanbanTodoModel(BaseModel):
    """One lightweight checklist item (``todo:`` meta bullet) on a card.

    Distinct from ``KanbanSubtaskModel`` (the AI-drafted milestone
    breakdown stored as nested checkboxes): todos are the user's own
    checklist, managed via ``PATCH .../kanban/cards/{ref}``.
    """

    model_config = ConfigDict(from_attributes=True)

    text: str = Field(min_length=1, max_length=500)
    done: bool = False


class KanbanTaskModel(BaseModel):
    """One parsed kanban card (mirrors core KanbanTask)."""

    title: str
    done: bool = False
    id: str = ""
    context: str = ""
    why: str = ""
    blocked_by: str = ""
    outcome: str = ""
    started_on: str | None = None
    completed_on: str | None = None
    planned_start: str | None = None
    planned_end: str | None = None
    crystallized: bool = False
    project_id: str = ""
    milestone_id: str = ""
    agent_task_id: str = ""
    tags: str = ""
    subtasks: list[KanbanSubtaskModel] = Field(default_factory=list)
    todos: list[KanbanTodoModel] = Field(default_factory=list)
    details: list[str] = Field(default_factory=list)


class KanbanSectionModel(BaseModel):
    """One kanban board section with its cards."""

    name: str
    tasks: list[KanbanTaskModel] = Field(default_factory=list)


class KanbanBoardResponse(BaseModel):
    """Parsed kanban board structure (no markdown body)."""

    profile: str
    sections: list[KanbanSectionModel] = Field(default_factory=list)
    total: int = 0
    # Done tasks archived to kanban-archive.md (not part of `total`; the
    # response ETag covers kanban.md only, not the archive file).
    archive: list[KanbanTaskModel] = Field(default_factory=list)


class KanbanCardCreateRequest(BaseModel):
    """Quick-add body for POST .../kanban/cards."""

    title: str = Field(min_length=1, max_length=200)
    section: str = "Queue"
    context: str = ""
    tags: list[str] = Field(default_factory=list)
    planned_start: str = ""
    planned_end: str = ""
    project_id: str = ""


class KanbanCardScheduleRequest(BaseModel):
    """Schedule body for POST .../kanban/cards/{card_ref}/schedule.

    ``None`` keeps the current value, ``""`` clears it, an ISO ``YYYY-MM-DD``
    date sets it. When both dates end up set, start must not be after end.
    """

    planned_start: str | None = None
    planned_end: str | None = None


class KanbanCardPatchRequest(BaseModel):
    """Edit body for PATCH .../kanban/cards/{card_ref}.

    ``None`` keeps the current value; ``""`` clears text fields
    (``context``/``why``/``project_id``/``milestone_id``); ``tags``
    replaces the whole tag list when given. ``title`` must not be blank
    when given. ``todos`` fully replaces the checklist when given
    (``[]`` clears it). Section moves (incl. Someday, which is a section,
    not a flag) stay on the move endpoint.
    """

    title: str | None = Field(default=None, max_length=200)
    context: str | None = Field(default=None, max_length=4000)
    why: str | None = Field(default=None, max_length=4000)
    project_id: str | None = Field(default=None, max_length=200)
    milestone_id: str | None = Field(default=None, max_length=200)
    tags: list[str] | None = None
    todos: list[KanbanTodoModel] | None = None


class KanbanCardMoveRequest(BaseModel):
    """Move body for POST .../kanban/cards/{card_ref}/move.

    ``to_index`` is the 0-based insertion index inside the target column
    (post-removal, matching ``apply_kanban_reorder``); when omitted the
    card is appended to the column tail. Out-of-range values clamp like
    the core reorder: negative to the column head, beyond-end to the tail.
    """

    target_section: str
    to_index: int | None = None


class KanbanMutationResponse(BaseModel):
    """Result of one kanban card mutation (add/move/done).

    ``merged_external`` / ``merge_notices`` surface the 3-way merge outcome
    when kanban.md changed between the request's parse and save.
    """

    ok: bool
    card: KanbanTaskModel
    section: str = ""
    warnings: list[str] = Field(default_factory=list)
    merged_external: bool = False
    merge_notices: list[str] = Field(default_factory=list)


class KanbanCardDeleteRequest(BaseModel):
    """Body for DELETE .../kanban/cards/{card_ref}.

    ``record_chronicle`` opts into a ``task.deleted`` chronicle entry
    (default off: routine task pruning is not a narrative event).
    """

    record_chronicle: bool = False


class KanbanCardDeleteResponse(BaseModel):
    """Result of one kanban card delete.

    ``deleted_ref`` is the deleted card's task id (falling back to the
    title for legacy id-less cards); ``deleted_title`` echoes the matched
    card title. Evidence-pool ``kanban_refs`` are NOT touched — the
    tombstone mechanism handles references to the deleted task.
    """

    ok: bool = True
    deleted_ref: str
    deleted_title: str


class InboxHistoryEventModel(BaseModel):
    """One transition recorded against an inbox item."""

    at: str = ""
    action: str = ""
    from_status: str = ""
    to_status: str = ""
    note: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class InboxItemModel(BaseModel):
    """One inbox item (mirrors core InboxItem)."""

    id: str
    title: str
    type: str = "note"
    source: str = ""
    created_at: str = ""
    captured_by: str = "human"
    raw_text: str = ""
    tags: list[str] = Field(default_factory=list)
    visibility: str = "private"
    status: str = "inbox"
    metadata: dict[str, Any] = Field(default_factory=dict)
    history: list[InboxHistoryEventModel] = Field(default_factory=list)


class InboxResponse(BaseModel):
    """Inbox items filtered to the requested statuses."""

    profile: str
    statuses: list[str] = Field(default_factory=list)
    total: int = 0
    items: list[InboxItemModel] = Field(default_factory=list)


class InboxCaptureRequest(BaseModel):
    """Body for the quick-capture mutation (only ``title`` is required)."""

    title: str
    raw_text: str = ""
    source: str = "web"
    tags: list[str] = Field(default_factory=list)


class InboxClarifyRequest(BaseModel):
    """Body for the clarify mutation (``action`` in CLARIFY_ACTIONS)."""

    action: str
    note: str = ""


class InboxNoteRequest(BaseModel):
    """Optional body for the archive/discard mutations."""

    note: str = ""


class InboxMutationResponse(BaseModel):
    """Success body for inbox mutations.

    ``result`` carries the clarify dispatch outcome (action, target_id,
    draft) for the clarify endpoint; it stays empty for capture and the
    archive/discard wrappers.
    """

    ok: bool = True
    item: InboxItemModel
    result: dict[str, Any] = Field(default_factory=dict)


class InboxItemErrorResponse(ErrorResponse):
    """Error body that also carries the current inbox item."""

    item: InboxItemModel | None = None


class AgentTaskModel(BaseModel):
    """One external agent handoff task (extension keys preserved)."""

    model_config = ConfigDict(extra="allow")

    id: str
    target_harness: str = "codex"
    role: str = "researcher"
    title: str = ""
    status: str = "ready"
    input_refs: list[str] = Field(default_factory=list)
    expected_outputs: list[str] = Field(default_factory=list)
    related: dict[str, Any] = Field(default_factory=dict)
    payload: dict[str, Any] = Field(default_factory=dict)
    activity_item_id: str = ""
    action_name: str = ""
    run_id: str = ""
    result_summary: str = ""
    changed_paths: list[str] = Field(default_factory=list)
    result_payload: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    error: str = ""
    created: str = ""
    updated: str = ""


class AgentTaskListResponse(BaseModel):
    """Agent task list, optionally filtered by status."""

    profile: str
    status: str = ""
    total: int = 0
    tasks: list[AgentTaskModel] = Field(default_factory=list)


class GoalSkillLinkModel(BaseModel):
    """One confirmed goal-to-skill-node link."""

    node_id: str
    label: str = ""
    source: str = "manual"
    score: int = 0
    rationale: str = ""


class GoalModel(BaseModel):
    """One goal in full owner-facing detail (no agent redaction)."""

    id: str
    title: str = ""
    label: str = ""
    status: str = "active"
    start: str = ""
    target: str = ""
    ui_visibility: str = "discreet"
    include_in_agent_context: bool = True
    include_in_public_output: bool = False
    summary: str = ""
    alignment: str = ""
    target_skills: list[str] = Field(default_factory=list)
    skill_links: list[GoalSkillLinkModel] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    focus: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    task_refs: list[str] = Field(default_factory=list)
    output_refs: list[str] = Field(default_factory=list)
    notes: str = ""


class NorthStarModel(BaseModel):
    """Owner-facing North Star from SKILL.md identity (no redaction here).

    This API serves the authenticated owner's UI, so ``full``/``brief`` are
    returned verbatim; ``visibility`` is the binary public-output flag
    (``public``/``private``; legacy ``discreet``/``hidden``/``visible`` map
    on read) and is informational for the UI badge.
    """

    visibility: str = "private"
    is_set: bool = False
    full: str = ""
    brief: str = ""


class NorthStarPatchRequest(BaseModel):
    """Body for PATCH .../north-star; at least one field is required.

    ``visibility`` accepts only the canonical binary values
    (``public``/``private``).
    """

    full: str | None = None
    brief: str | None = None
    visibility: str | None = None


class NorthStarMutationResponse(BaseModel):
    """Result of the surgical North Star rewrite."""

    ok: bool = True
    changed: bool = False
    changed_keys: list[str] = Field(default_factory=list)
    north_star: NorthStarModel = Field(default_factory=NorthStarModel)


class GoalsResponse(BaseModel):
    """The profile's goal book as the human owner sees it."""

    profile: str
    current_goal_id: str = ""
    north_star: NorthStarModel = Field(default_factory=NorthStarModel)
    goals: list[GoalModel] = Field(default_factory=list)


class GoalCreateRequest(BaseModel):
    """Body for POST .../goals (only ``title`` is required).

    ``start``/``target`` must be ISO dates (YYYY-MM-DD) when given; an
    empty ``start`` defaults to today server-side (立项日). ``status``
    accepts ``active``/``paused``/``completed`` (default ``active``).
    """

    title: str
    summary: str = ""
    start: str = ""
    target: str = ""
    status: str = "active"


class GoalPatchRequest(BaseModel):
    """Body for PATCH .../goals/{goal_id}; at least one field is required."""

    title: str | None = None
    summary: str | None = None
    start: str | None = None
    target: str | None = None
    status: str | None = None


class GoalMutationResponse(BaseModel):
    """Result of one goal create/patch mutation.

    ``changed_keys`` lists the fields whose values actually changed (empty
    for a no-op patch, which also skips the chronicle entry).
    """

    ok: bool = True
    changed: bool = False
    changed_keys: list[str] = Field(default_factory=list)
    goal: GoalModel


class ChronicleEntryModel(BaseModel):
    """One append-only chronicle entry (date, kind, ref, note)."""

    date: str
    kind: str
    ref: str = ""
    note: str = ""


class ChronicleResponse(BaseModel):
    """Chronicle entries, newest first, capped by the ``limit`` query."""

    profile: str
    total: int = 0
    entries: list[ChronicleEntryModel] = Field(default_factory=list)


class ProvenanceRefModel(BaseModel):
    """One kanban provenance ref with its resolution state.

    Dead refs (task archived or deleted) report ``status="archived"`` so the
    UI renders a tombstone instead of a hard error (design: kanban_refs stay
    a provenance chain, never a 404).
    """

    ref: str
    task_id: str = ""
    title: str = ""
    status: str = "archived"  # "linked" | "archived"


class EvidenceEntryModel(BaseModel):
    """One evidence-pool entry, list view."""

    id: str
    title: str = ""
    evidence_type: str = "practice"
    review_status: str = "needs_review"
    date: str = ""
    url: str = ""
    summary: str = ""
    source_refs: list[str] = Field(default_factory=list)
    breakthrough: bool = False


class EvidenceEntryDetailModel(EvidenceEntryModel):
    """One evidence-pool entry, full detail view."""

    strength: str = ""
    confidence: str = ""
    public_readiness: str = ""
    project_refs: list[str] = Field(default_factory=list)
    experience_refs: list[str] = Field(default_factory=list)
    kanban_refs: list[str] = Field(default_factory=list)
    source_excerpt: str = ""
    origin: str = ""
    origin_ref: str = ""
    origin_detail: str = ""
    original_content: str = ""
    formatted_content: str = ""
    language: str = ""
    original_language: str = ""
    original_content_hash: str = ""
    source_content_hash: str = ""
    deprecated: bool = False
    replaced_by: str = ""
    skill_refs: list[str] = Field(default_factory=list)
    kanban_ref_details: list[ProvenanceRefModel] = Field(default_factory=list)


class GapAnalyzeRequest(BaseModel):
    """Body for the gap-analysis mutation.

    ``use_llm=False`` runs the synchronous rule-only analysis (200).
    ``use_llm=True`` creates an async ``gap-analysis`` job (202, see
    ``JobCreateResponse``); poll ``GET .../jobs/{job_id}`` or subscribe to
    ``GET .../jobs/{job_id}/stream`` for progress and the final result.
    """

    task: str = Field(min_length=1, max_length=2000)
    use_llm: bool = False


class GapTopMatchModel(BaseModel):
    """One rule/LLM-matched schema node from ``GapResult.top_matches``."""

    id: str
    label: str = ""
    score: int = 0
    source: str = "rule"


class GapClosureNodeModel(BaseModel):
    """One node of the requires-closure from ``GapResult.closure``.

    ``is_gap`` mirrors the core rule: status ``locked``/``learning`` counts
    as a gap, ``solid``/``expert`` as strong.
    """

    id: str
    label: str = ""
    status: str = "locked"
    is_gap: bool = False
    evidence_count: int = 0


class GapAnalysisResponse(BaseModel):
    """Faithful projection of ``core.models.GapResult``.

    ``coverage`` is a derived convenience: share of closure nodes that are
    not gaps (0.0 when the closure is empty), so the SPA can render a
    coverage indicator without re-deriving it. ``analysis_mode`` records
    which matchers ran (``rule`` for the sync endpoint, ``rule+llm`` for the
    async deep-analysis job); ``llm_router_error`` carries the degradation
    reason when the LLM router failed but rule roots still produced an
    analysis (``null`` when no LLM path ran or it succeeded).
    """

    profile: str
    task: str = ""
    top_matches: list[GapTopMatchModel] = Field(default_factory=list)
    closure: list[GapClosureNodeModel] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    strong: list[str] = Field(default_factory=list)
    can_solve: bool = False
    coverage: float = 0.0
    next_steps: list[str] = Field(default_factory=list)
    roots_from_rule: list[str] = Field(default_factory=list)
    roots_from_llm: list[str] = Field(default_factory=list)
    learned_merged: bool = False
    analysis_mode: str = "rule"
    llm_router_error: str | None = None


class JobErrorModel(BaseModel):
    """Structured terminal failure of an async job."""

    code: str
    message: str


class JobModel(BaseModel):
    """Public snapshot of one async job (no result payload, no event log).

    Statuses follow ``queued`` -> ``running`` -> ``done`` | ``failed``;
    ``phase`` is the kind-specific coarse stage (gap-analysis: queued /
    starting / routing / merging / done / failed; studio-jd-match:
    analyzing / generating; project-suggest-refs: collecting / suggesting).
    """

    job_id: str
    profile: str
    kind: str
    status: str
    phase: str = ""
    message: str = ""
    created_at: float = 0.0
    started_at: float = 0.0
    finished_at: float = 0.0
    elapsed_ms: int = 0
    error: JobErrorModel | None = None


class JobCreateRequest(BaseModel):
    """Generic async-job creation body (dispatched by ``kind``).

    ``input`` is validated per kind: ``gap-analysis`` takes ``{task: str}``
    (1–2000 non-blank chars), ``studio-jd-match`` takes ``{resume_md,
    jd_text}`` (both non-blank, ≤ 50000 chars each) and
    ``project-suggest-refs`` takes ``{case_id: str}`` (non-blank);
    content-workspace AI kinds ``content-rewrite`` (``{operation, selection,
    title?, context?, instruction?}``), ``content-meta`` (``{title, summary,
    tags, body}``) and ``content-cover`` (``{slug, brief?, style?, title?,
    summary?, tags?, body?}``) return candidates only and never write posts.
    Validation failures answer 422 with the kind's error code
    (``empty_task`` / ``invalid_jd_match_request`` / ``empty_case_id`` /
    ``invalid_job_input``).
    """

    kind: str = Field(min_length=1, max_length=64)
    input: dict[str, Any] = Field(default_factory=dict)


class JobCreateResponse(BaseModel):
    """202 answer of the job-creation endpoints."""

    ok: bool = True
    job_id: str
    job: JobModel


class JobStatusResponse(BaseModel):
    """Current job snapshot plus the result payload once done."""

    ok: bool = True
    job: JobModel
    result: dict[str, Any] | None = None


class GapIntakeRequest(BaseModel):
    """Body for turning one detected gap into a kanban learning task.

    ``title`` is required (the SPA pre-fills it from the gap node label);
    ``node_id`` is recorded as context so the card stays traceable to the
    analysis.
    """

    title: str = Field(min_length=1, max_length=200)
    node_id: str = Field(default="", max_length=200)
    why: str = Field(default="", max_length=2000)
    tags: list[str] = Field(default_factory=list)
    section: str = "Queue"


class EvidenceListResponse(BaseModel):
    """Filtered evidence-pool entries for one profile."""

    profile: str
    status: str = ""
    q: str = ""
    skill_id: str = ""
    limit: int = 100
    total: int = 0
    items: list[EvidenceEntryModel] = Field(default_factory=list)


class EvidenceReviewItemModel(BaseModel):
    """One evidence-pool row in the Evidence Review triage view.

    ``review_reason`` mirrors the Streamlit page rule: a row needs review
    when its strength is unrated and/or its review_status is not reviewed.
    ``skill_refs`` / ``usage_count`` count skill-tree nodes citing the row.
    ``breakthrough`` mirrors the raw row's 突破 flag (extra progression
    weight); the review list renders a small badge for it.
    """

    id: str
    title: str = ""
    evidence_type: str = "practice"
    date: str = ""
    url: str = ""
    review_status: str = "needs_review"
    strength: str = "unrated"
    confidence: str = ""
    public_readiness: str = "private"
    deprecated: bool = False
    breakthrough: bool = False
    usage_count: int = 0
    skill_refs: list[str] = Field(default_factory=list)
    review_reason: str = ""


class EvidenceReviewSummaryModel(BaseModel):
    """Queue-wide counters over the whole pool (unfiltered)."""

    needs_review_count: int = 0
    unlinked_count: int = 0
    total_entries: int = 0
    deprecated_count: int = 0


class EvidenceReviewListResponse(BaseModel):
    """Filtered review rows plus queue-wide summary counters."""

    profile: str
    status: str = "needs_review"
    q: str = ""
    limit: int = 200
    total: int = 0
    items: list[EvidenceReviewItemModel] = Field(default_factory=list)
    summary: EvidenceReviewSummaryModel = Field(
        default_factory=EvidenceReviewSummaryModel
    )


class EvidenceReviewBulkRequest(BaseModel):
    """Body for the bulk tag/accept mutation.

    ``field`` must be one of the pool-editable fields
    (``review_status``/``strength``/``confidence``/``public_readiness``);
    ``value`` must be inside that field's whitelist ("" clears the field).
    Accept = ``review_status`` -> ``reviewed``; tagging = the grade fields.
    """

    ids: list[str] = Field(min_length=1)
    field: str
    value: str = ""


class EvidenceReviewDeprecateRequest(BaseModel):
    """Body for the reject (deprecate) / restore mutation."""

    ids: list[str] = Field(min_length=1)
    deprecated: bool = True


class EvidenceReviewMutationResponse(BaseModel):
    """Result of one evidence-review mutation (bulk set / deprecate).

    ``missing`` lists requested ids that no pool row matches; ``changed``
    counts rows actually modified (already-in-state rows do not count).
    """

    ok: bool = True
    changed: int = 0
    missing: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class EvidenceEditRequest(BaseModel):
    """Body for the single-entry edit mutation.

    ``fields`` maps field name -> new value. Allowed keys: the review
    whitelist (``review_status``/``strength``/``confidence``/
    ``public_readiness``, domain-validated, "" clears) plus the text fields
    ``title``/``summary``/``date``/``url`` and ``type`` (domain-validated),
    plus the bool flag ``breakthrough`` ("true"/"false", "" clears).
    Unknown keys answer 422; provenance fields (``origin*``, refs,
    ``original_content``) are not editable here — the original snapshot is
    immutable once crystallized.
    """

    fields: dict[str, str] = Field(min_length=1)


class EvidenceEntryActionRequest(BaseModel):
    """Body for the single-entry review action.

    ``action``: ``accept`` (mark reviewed, optionally grading in the same
    call), ``reject`` (deprecate; the row is kept for provenance) or
    ``restore`` (un-deprecate). Grade fields are only applied on ``accept``
    and must be in their domain ("" clears).
    """

    action: str = Field(min_length=1, max_length=16)
    strength: str = ""
    confidence: str = ""
    public_readiness: str = ""


class EvidenceSkillLinksRequest(BaseModel):
    """Body for the skill link/unlink mutation (chip-save semantics).

    ``skill_ids`` is the full desired set of skill nodes citing this
    evidence row: ids not currently linked are added, currently-linked ids
    missing from the list are removed (core
    ``set_evidence_skill_refs``). The write lands only on the skill nodes'
    ``evidence_refs`` — the single write side; the reverse direction is
    computed on read.
    """

    skill_ids: list[str] = Field(default_factory=list)


class EvidenceSkillLinksResponse(BaseModel):
    """Result of the skill link/unlink mutation."""

    ok: bool = True
    entry_id: str
    skill_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class EvidenceSkillSuggestionModel(BaseModel):
    """One suggested skill node for an evidence row."""

    id: str
    label: str = ""
    category: str = ""
    level: int = 0
    score: float = 0.0
    source: str = "rule"


class EvidenceSkillSuggestionsResponse(BaseModel):
    """Ranked skill-link suggestions for one evidence entry.

    ``backend`` records which tier produced the ranking: ``embedding``
    (LLM_EMBEDDING_MODEL configured), ``llm`` (chat ranking fallback) or
    ``rule`` (deterministic keyword overlap; always available).
    """

    profile: str
    entry_id: str
    backend: str = "rule"
    suggestions: list[EvidenceSkillSuggestionModel] = Field(default_factory=list)


class EvidenceStageRiskModel(BaseModel):
    """One 待补强 row: a solid/expert skill whose evidence is missing/weak."""

    skill_id: str
    label: str = ""
    status: str = ""
    risk_level: str = ""
    risk_reason: str = ""
    required_strength: str = ""
    highest_strength: str = ""
    evidence_refs: list[str] = Field(default_factory=list)


class EvidenceStagesResponse(BaseModel):
    """Five-stage pipeline counters for the single Evidence page.

    Stages: 待结晶 (uncrystallized Done tasks) -> 待评审 -> 已入座 (reviewed
    and linked to at least one skill) -> 已废弃; 待补强 (risks) hangs off
    已入座. Counts are queue-wide (unfiltered).
    """

    profile: str
    pending_crystallize_count: int = 0
    needs_review_count: int = 0
    seated_count: int = 0
    strengthen_count: int = 0
    deprecated_count: int = 0
    risks: list[EvidenceStageRiskModel] = Field(default_factory=list)


class CrystallizeCandidateModel(BaseModel):
    """One uncrystallized Done task (结晶向导 step 1 option).

    ``context``/``why``/``outcome`` feed the candidate inscription card;
    ``snapshot`` is the full原文 block (``render_kanban_task_source``) that
    crystallization would embed into the evidence row — the card shows it
    as a preview so the human sees exactly what gets snapshotted.
    """

    id: str
    title: str = ""
    completed_on: str = ""
    project_id: str = ""
    tags: str = ""
    context: str = ""
    why: str = ""
    outcome: str = ""
    snapshot: str = ""
    blockers: list[str] = Field(default_factory=list)


class CrystallizeCandidatesResponse(BaseModel):
    """Uncrystallized Done tasks plus their crystallization blockers."""

    profile: str
    items: list[CrystallizeCandidateModel] = Field(default_factory=list)


class CrystallizeDraftRequest(BaseModel):
    """Body for the crystallize-draft endpoint.

    Rule mode (``use_llm=false``, default) answers 200 with a deterministic
    one-row-per-task draft. ``use_llm=true`` creates an async
    ``evidence-crystallize`` job (202) whose result carries the same
    ``CrystallizeDraftResponse`` payload shape.
    """

    task_ids: list[str] = Field(default_factory=list)
    titles: list[str] = Field(default_factory=list)
    use_llm: bool = False


class CrystallizeTaskModel(BaseModel):
    """Resolved source task echo in a crystallize draft."""

    id: str = ""
    title: str = ""
    kanban_ref: str = ""
    project_id: str = ""
    completed_on: str = ""


class CrystallizeDraftResponse(BaseModel):
    """Crystallize draft: an ingest patch plus the resolved source tasks.

    ``patch`` is an ingest-patch dict (``evidence_entries`` /
    ``node_updates``) the client edits (grading, deselecting rows) and posts
    back to ``.../crystallize/apply``. ``backend`` is ``rule`` or ``llm``.
    """

    ok: bool = True
    profile: str
    backend: str = "rule"
    patch: dict[str, Any] = Field(default_factory=dict)
    tasks: list[CrystallizeTaskModel] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)


class CrystallizeApplyRequest(BaseModel):
    """Body for the crystallize-apply endpoint.

    ``patch`` is the (possibly human-edited) draft from the draft endpoint;
    ``include_evidence`` / ``include_nodes`` are the wizard's per-row
    checkboxes (null = keep all). On success the source tasks are marked
    ``crystallized`` in kanban.md.
    """

    patch: dict[str, Any] = Field(default_factory=dict)
    task_ids: list[str] = Field(default_factory=list)
    titles: list[str] = Field(default_factory=list)
    include_evidence: list[bool] | None = None
    include_nodes: list[bool] | None = None
    allow_status_change: bool = False


class CrystallizeTaskResult(BaseModel):
    """Stable evidence references for a successfully crystallized task."""

    task_id: str
    evidence_ids: list[str] = Field(default_factory=list)


class CrystallizeApplyResponse(BaseModel):
    """Result of the crystallize apply."""

    ok: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    new_evidence_ids: list[str] = Field(default_factory=list)
    crystallized_count: int = 0
    items: list[CrystallizeTaskResult] = Field(default_factory=list)


class ProjectMilestoneModel(BaseModel):
    """One project milestone (mirrors core ProjectMilestone + completion)."""

    id: str
    title: str = ""
    status: str = "planned"
    target: str = ""
    date: str = ""
    summary: str = ""
    task_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    output_refs: list[str] = Field(default_factory=list)
    done_count: int = 0
    total_count: int = 0


class ProjectTaskModel(BaseModel):
    """One kanban task owned by a project case (list/timeline row)."""

    id: str
    title: str = ""
    section: str = ""
    done: bool = False
    milestone_id: str = ""
    started_on: str | None = None
    completed_on: str | None = None
    archived: bool = False


class ProjectCaseModel(BaseModel):
    """One internal project case (mirrors core ProjectCase).

    ``derived_time_range`` is inferred from the owned kanban tasks'
    started/completed dates; ``tasks`` lists the owned live+archived kanban
    tasks with their board section for the detail page's task tab.
    """

    id: str
    title: str = ""
    status: str = "active"
    kind: str = "internal"
    visibility: str = "private"
    time_range: str = ""
    summary: str = ""
    notes: str = ""
    goal_refs: list[str] = Field(default_factory=list)
    task_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    experience_refs: list[str] = Field(default_factory=list)
    output_refs: list[str] = Field(default_factory=list)
    milestones: list[ProjectMilestoneModel] = Field(default_factory=list)
    tasks: list[ProjectTaskModel] = Field(default_factory=list)
    derived_time_range: str = ""
    habit_id: str = ""


class ProjectBoardSummaryModel(BaseModel):
    """Overview counters for the project board header strip."""

    status_counts: dict[str, int] = Field(default_factory=dict)
    unassigned_tasks: int = 0
    unassigned_evidence: int = 0
    current_goal_projects: int = 0


class ProjectRefOptionModel(BaseModel):
    """One {id, label} option row for the ref pickers.

    ``owner`` is only set for task options: the kanban task's current
    ``project_id``. The SPA offers a task to case X when owner is empty or
    equals X (mirroring the Streamlit per-case task option filter).
    """

    id: str
    label: str = ""
    owner: str = ""


class ProjectBoardOptionsModel(BaseModel):
    """Ref-picker option rows for the create/edit forms.

    ``tasks`` lists every kanban task with its current owner project id; the
    SPA offers a task to case X when the owner is empty or equals X
    (mirroring the Streamlit per-case task option filter).
    """

    goals: list[ProjectRefOptionModel] = Field(default_factory=list)
    tasks: list[ProjectRefOptionModel] = Field(default_factory=list)
    evidence: list[ProjectRefOptionModel] = Field(default_factory=list)
    sources: list[ProjectRefOptionModel] = Field(default_factory=list)
    experiences: list[ProjectRefOptionModel] = Field(default_factory=list)
    outputs: list[ProjectRefOptionModel] = Field(default_factory=list)


class ProjectBoardResponse(BaseModel):
    """Full project board: cases, summary counters, and ref-picker options."""

    profile: str
    updated: str = ""
    summary: ProjectBoardSummaryModel = Field(
        default_factory=ProjectBoardSummaryModel
    )
    cases: list[ProjectCaseModel] = Field(default_factory=list)
    options: ProjectBoardOptionsModel = Field(default_factory=ProjectBoardOptionsModel)


# --- Projects Board (Phase 2 unified /projects page aggregation) ----------


class ProjectsBoardTaskModel(BaseModel):
    """One kanban task flattened for a projects-board lane."""

    id: str = ""
    title: str = ""
    section: str = ""
    column: str = "queue"
    done: bool = False
    context: str = ""
    why: str = ""
    started_on: str | None = None
    completed_on: str | None = None
    planned_start: str | None = None
    planned_end: str | None = None
    project_id: str = ""
    milestone_id: str = ""
    tags: str = ""
    todos: list[KanbanTodoModel] = Field(default_factory=list)


class ProjectsBoardMilestoneModel(BaseModel):
    """One milestone with task completion progress.

    The data model has no dedicated "completed milestone" workflow; real
    profiles keep ``planned`` even for past dates, so overdue-vs-done is a
    display concern derived from ``date`` and ``status``.
    """

    id: str = ""
    title: str = ""
    status: str = "planned"
    target: str = ""
    date: str = ""
    done_count: int = 0
    total_count: int = 0


class ProjectsBoardProjectModel(BaseModel):
    """One project swimlane: case facts plus owned kanban tasks.

    ``queue``/``doing`` hold the live task cards; ``someday`` is a badge
    list (not a column); Done tasks are folded into ``done_count``, which
    includes tasks archived to kanban-archive.md (``archived_done_count``
    breaks out the archived share). ``column_counts`` keys are
    queue/doing/someday/done; together with ``evidence_ref_count`` they
    power the delete dialog's consequence preview ("N tasks back to
    unassigned · M evidence refs kept"). ``habit_id`` links to a ``habits``
    entry: the case's explicit ``habit_id`` field wins, otherwise the
    habit<->project name heuristic applies.
    """

    id: str
    title: str = ""
    status: str = "active"
    kind: str = "internal"
    visibility: str = "private"
    summary: str = ""
    time_range: str = ""
    goal_refs: list[str] = Field(default_factory=list)
    milestones: list[ProjectsBoardMilestoneModel] = Field(default_factory=list)
    queue: list[ProjectsBoardTaskModel] = Field(default_factory=list)
    doing: list[ProjectsBoardTaskModel] = Field(default_factory=list)
    someday: list[ProjectsBoardTaskModel] = Field(default_factory=list)
    column_counts: dict[str, int] = Field(default_factory=dict)
    done_count: int = 0
    archived_done_count: int = 0
    evidence_ref_count: int = 0
    last_activity: str = ""
    habit_id: str = ""


class ProjectsBoardGoalModel(BaseModel):
    """One goal grouping row with its projects (first-goal grouping)."""

    id: str
    title: str = ""
    status: str = ""
    summary: str = ""
    target: str = ""
    projects: list[ProjectsBoardProjectModel] = Field(default_factory=list)


class ProjectsBoardHabitDayModel(BaseModel):
    """One day of the current ISO week check-in strip."""

    date: str
    done: bool = False
    future: bool = False


class ProjectsBoardHabitRecentDayModel(BaseModel):
    """One checked day in the trailing 90-day heatmap window."""

    date: str
    count: float = 1.0
    checkin_ids: list[str] = Field(default_factory=list)


class ProjectsBoardHabitModel(BaseModel):
    """Habit check-in aggregation for continuous (habit) lanes.

    ``week`` is the current ISO week (Monday..Sunday); ``streak`` counts
    consecutive checked days ending today (0 when today has no check-in
    yet); ``total_checkins`` counts distinct checked days overall.
    ``recent_days`` is the heatmap source: checked days within the trailing
    90-day window ending today (oldest first, same-day rows summed into
    ``count``). ``project_id`` links to a project lane when the name
    heuristic matches.
    """

    id: str
    title: str = ""
    kind: str = ""
    cadence: str = ""
    week: list[ProjectsBoardHabitDayModel] = Field(default_factory=list)
    streak: int = 0
    total_checkins: int = 0
    last_checkin: str = ""
    project_id: str = ""
    recent_days: list[ProjectsBoardHabitRecentDayModel] = Field(
        default_factory=list
    )
    archived: bool = False


class ProjectsBoardResponse(BaseModel):
    """Aggregated /projects payload: goal-grouped lanes, tasks, habits.

    Full data, no display caps (caps are a frontend concern). Projects
    appear under the first of their ``goal_refs`` that names a known goal;
    projects without a known goal land in ``ungrouped_projects``; live
    kanban tasks owned by no project land in ``unassigned_tasks``.
    """

    profile: str
    today: str = ""
    north_star: str = ""
    goals: list[ProjectsBoardGoalModel] = Field(default_factory=list)
    ungrouped_projects: list[ProjectsBoardProjectModel] = Field(
        default_factory=list
    )
    unassigned_tasks: list[ProjectsBoardTaskModel] = Field(default_factory=list)
    habits: list[ProjectsBoardHabitModel] = Field(default_factory=list)
    stats: dict[str, int] = Field(default_factory=dict)


# --- Starmap (Phase 3): one-shot home-scene snapshot -------------------------


class StarmapCategoryModel(BaseModel):
    """One skill category (starmap sector band) with status counters.

    ``name`` is the server-provided zh display name (category id as fallback
    for ids outside the known table).
    """

    id: str
    name: str = ""
    count: int = 0
    lit_count: int = 0
    learning_count: int = 0


class StarmapSkillModel(BaseModel):
    """One skill-tree node for the starmap (三态: locked/learning/lit).

    Unlike the /skill-tree overlay view, this projection includes every
    schema node — locked schema nodes (the 未解锁空圈 underlay) ride with
    ``status="locked"`` even when the profile overlay never mentions them.
    """

    id: str
    label: str = ""
    category: str = "misc"
    status: str = "locked"
    lit: bool = False


class StarmapGoalModel(BaseModel):
    """One active stage goal (starmap goal star)."""

    id: str
    title: str = ""
    status: str = "active"
    summary: str = ""
    start: str = ""
    target: str = ""


class StarmapProjectModel(BaseModel):
    """One project case (starmap planet) with progress and goal grouping."""

    id: str
    title: str = ""
    status: str = "active"
    kind: str = "internal"
    goal_ids: list[str] = Field(default_factory=list)
    progress: float | None = None
    task_count: int = 0
    time_range: str = ""


class StarmapEvidenceModel(BaseModel):
    """One non-deprecated evidence entry (guest star / seated star / dust).

    ``flying`` marks guest stars (客星): entries inside the 30-day window
    plus the newest-4 density floor. ``project_refs`` place seated stars by
    their project planet when present (skill-sector fallback otherwise).
    """

    id: str
    type: str = "practice"
    title: str = ""
    date: str = ""
    strength: str = "unrated"
    review_status: str = "needs_review"
    summary: str = ""
    skill_ids: list[str] = Field(default_factory=list)
    project_refs: list[str] = Field(default_factory=list)
    flying: bool = False


class StarmapCountsModel(BaseModel):
    """Briefing counters for the starmap chrome."""

    evidence: int = 0
    evidence_needs_review: int = 0
    evidence_flying: int = 0
    projects_active: int = 0
    skills_lit: int = 0


class StarmapResponse(BaseModel):
    """One-shot growth-starmap snapshot for the SPA home scene.

    Aggregates SKILL.md (North Star), goals.yaml (active goals),
    skill-tree.yaml + the domain schema (locked schema nodes included),
    the projects-board aggregation (goal grouping + progress), and the
    evidence pool (30-day guest window + newest-4 floor). Built by
    ``core.starmap_snapshot.build_starmap_snapshot``; the response carries
    a weak ETag over the source files (same pattern as /projects-board).
    """

    profile: str
    generated_on: str = ""
    schema_name: str = ""
    north_star: str = ""
    goals: list[StarmapGoalModel] = Field(default_factory=list)
    categories: list[StarmapCategoryModel] = Field(default_factory=list)
    skills: list[StarmapSkillModel] = Field(default_factory=list)
    projects: list[StarmapProjectModel] = Field(default_factory=list)
    evidence: list[StarmapEvidenceModel] = Field(default_factory=list)
    counts: StarmapCountsModel = Field(default_factory=StarmapCountsModel)


class DivinationRequest(BaseModel):
    """Body for POST .../divination (占卜; design §5).

    ``mode=play`` (戏占, default) needs no input; ``mode=serious`` (正占)
    requires a non-empty ``question`` (the route answers 422
    ``question_required`` otherwise). The question is length-capped.
    """

    mode: Literal["play", "serious"] = "play"
    question: str = Field(default="", max_length=500)


class DivinationHexagramModel(BaseModel):
    """One cast hexagram: name, six yao, and the 卦辞 judgment.

    ``symbol_lines`` are the six yao bottom-to-top (初爻→上爻);
    1 = yang (⚊), 0 = yin (⚋).
    """

    name: str
    symbol_lines: list[int] = Field(default_factory=list)
    judgment: str = ""


class DivinationResponse(BaseModel):
    """Single-consumption divination result (nothing is persisted).

    ``anchors`` carries the real starmap data points the reading quotes
    (counts, in-orbit projects, pending reviews, habit streaks; plus the
    real gap-analysis summary for serious mode). ``source`` is ``"llm"``
    when the AI gateway produced the texts, ``"rule"`` for the
    deterministic data-anchored fallback (unconfigured/error/timeout).
    """

    profile: str
    mode: str = "play"
    question: str = ""
    hexagram: DivinationHexagramModel
    reading: str = ""
    anchors: dict[str, Any] = Field(default_factory=dict)
    source: str = "rule"
    generated_on: str = ""


class CheckinCreateRequest(BaseModel):
    """Body for POST .../checkins (append one habit check-in).

    ``habit`` accepts a habit id or title (resolved like the core helpers);
    ``project_id`` is an alternative entry point that resolves through the
    habit<->project link. ``date`` defaults to today; ``count`` must be
    greater than zero. ``plan_id`` optionally binds the check-in to an
    active habit plan of the same habit; the backend then derives and
    stores the plan-relative ``week_number`` (clients never send it).
    """

    habit: str = ""
    project_id: str = ""
    plan_id: str = ""
    date: str = ""
    summary: str = ""
    note: str = ""
    count: float = 1.0
    unit: str = ""
    tags: list[str] = Field(default_factory=list)
    related_kanban: list[str] = Field(default_factory=list)
    workout_type: str = ""
    duration_min: float = 0.0
    intensity: str = ""


class CheckinModel(BaseModel):
    """One stored activity-log check-in (mirrors core Checkin)."""

    id: str = ""
    date: str = ""
    habit_id: str = ""
    habits: list[str] = Field(default_factory=list)
    plan_id: str = ""
    week_number: int = 0
    day_number: int = 0
    summary: str = ""
    notes: str = ""
    count: float = 1.0
    unit: str = ""
    workout_type: str = ""
    duration_min: float = 0.0
    intensity: str = ""
    tags: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    related_learning: list[str] = Field(default_factory=list)
    related_kanban: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)


class CheckinMutationResponse(BaseModel):
    """Result of the check-in append mutation."""

    ok: bool
    checkin: CheckinModel


class CheckinDeleteResponse(BaseModel):
    """Result of the check-in delete mutation (销印)."""

    ok: bool
    checkin_id: str


# --- Habit lifecycle (archive / confirmed delete) ----------------------------


class HabitArchiveRequest(BaseModel):
    """Body for POST .../habits/{habit_id}/archive (archive or restore)."""

    archived: bool


class HabitArchiveResponse(BaseModel):
    """Result of the habit archive mutation.

    ``changed`` is false when the habit was already in the requested state
    (a no-op writes nothing)."""

    ok: bool = True
    habit_id: str
    archived: bool = False
    changed: bool = False


class HabitDeleteRequest(BaseModel):
    """Body for DELETE .../habits/{habit_id} (confirmed destructive delete).

    ``confirm_title`` must equal the habit's title exactly, else 422
    ``habit_delete_confirm_mismatch`` — the typed-name guard against
    fat-finger deletes. ``record_chronicle`` opts into a ``habit.deleted``
    chronicle entry (default off: routine catalog pruning is not a
    narrative event)."""

    confirm_title: str = ""
    record_chronicle: bool = False


class HabitDeleteResponse(BaseModel):
    """Result of the habit delete mutation.

    ``checkins_removed`` counts every check-in row purged with the habit."""

    ok: bool = True
    deleted_id: str
    checkins_removed: int = 0


# --- Habit plans (阶段计划: short-range phase plans under one habit) --------


class HabitPlanWeeklyTasksModel(BaseModel):
    """Task list for one plan week (1-based ``week``)."""

    week: int
    tasks: list[str] = Field(default_factory=list)


class HabitPlanDailyTasksModel(BaseModel):
    """Task list for one plan day (1-based ``day``; sparse coverage)."""

    day: int
    tasks: list[str] = Field(default_factory=list)


class HabitPlanCreateRequest(BaseModel):
    """Body for POST .../habit-plans (create one phase plan).

    ``habit_id`` must resolve to an existing habit; ``start_date`` /
    ``end_date`` are inclusive ISO dates. ``weekly_tasks`` (when given)
    must cover exactly ``ceil(days / 7)`` weeks, numbered 1..N in order
    (a partial tail week is fine); ``daily_tasks`` (when given) carries
    sparse 1-based day entries bounded by the inclusive plan length — a
    day without an entry is a rest day. At least one of the two must be
    non-empty. ``generate_weekly_cards`` (default on) also writes one
    Queue kanban card per week; with ``daily_tasks`` the card todos are
    per-day lines (``D<day> <task>``). ``project_id`` is tri-state: a
    value mounts the cards on that case (422 ``project_not_found`` when
    unknown), an empty string keeps them project-less, and omitted falls
    back to the habit's first active case.
    """

    title: str
    habit_id: str
    start_date: str
    end_date: str
    weekly_tasks: list[HabitPlanWeeklyTasksModel] = Field(
        default_factory=list
    )
    daily_tasks: list[HabitPlanDailyTasksModel] = Field(
        default_factory=list
    )
    project_id: str | None = None
    generate_weekly_cards: bool = True


class HabitPlanPatchRequest(BaseModel):
    """Body for PATCH .../habit-plans/{plan_id} (partial edit).

    ``status`` moves the plan forward (active -> completed/archived);
    ``title`` / ``weekly_tasks`` replace the stored values. All fields
    are optional; omitted fields stay unchanged.
    """

    status: str | None = None
    title: str | None = None
    weekly_tasks: list[HabitPlanWeeklyTasksModel] | None = None


class HabitPlanWeekProgressModel(BaseModel):
    """Check-in coverage for one week of a habit plan."""

    week: int
    start: str = ""
    end: str = ""
    days_done: int = 0
    days_total: int = 0


class HabitPlanModel(BaseModel):
    """One stored habit plan plus its computed progress."""

    id: str
    title: str = ""
    habit_id: str = ""
    start_date: str = ""
    end_date: str = ""
    status: str = "active"
    weekly_tasks: list[HabitPlanWeeklyTasksModel] = Field(
        default_factory=list
    )
    daily_tasks: list[HabitPlanDailyTasksModel] = Field(
        default_factory=list
    )
    current_week: int = 0
    current_day: int = 0
    today_tasks: list[str] = Field(default_factory=list)
    days_done: int = 0
    days_total: int = 0
    completion_rate: float = 0.0
    weeks: list[HabitPlanWeekProgressModel] = Field(default_factory=list)


class HabitPlanListResponse(BaseModel):
    """List of one profile's habit plans with computed progress."""

    ok: bool = True
    profile: str = ""
    plans: list[HabitPlanModel] = Field(default_factory=list)


class HabitPlanMutationResponse(BaseModel):
    """Result of the habit-plan create/patch mutations.

    ``kanban_card_ids`` lists the weekly Queue cards generated on create
    (empty when ``generate_weekly_cards`` was false)."""

    ok: bool
    plan: HabitPlanModel
    kanban_card_ids: list[str] = Field(default_factory=list)


class HabitPlanDeleteRequest(BaseModel):
    """Body for DELETE .../habit-plans/{plan_id} (confirmed delete).

    ``confirm_title`` must equal the plan's title exactly, else 422
    ``habit_plan_delete_confirm_mismatch`` — the typed-name guard against
    fat-finger deletes. ``delete_open_cards`` (default on) also removes
    the plan's generated week cards still sitting in Queue/Doing (Done
    cards are kept as history); check-in rows are never touched. Opt into
    a ``habit_plan.deleted`` chronicle entry with ``record_chronicle``.
    """

    confirm_title: str = ""
    delete_open_cards: bool = True
    record_chronicle: bool = False


class HabitPlanDeleteResponse(BaseModel):
    """Result of the habit-plan delete mutation.

    ``cards_removed`` counts the generated week cards pruned from
    Queue/Doing (0 when ``delete_open_cards`` was false)."""

    ok: bool = True
    deleted_id: str
    cards_removed: int = 0


# --- Habit-plan templates (Phase 2 click-to-instantiate plans) -------------


class PlanTemplateHabitModel(BaseModel):
    """The habit a plan template suggests (created when missing)."""

    title: str = ""
    kind: str = "health"
    cadence: str = "daily"
    target_count: float = 1.0
    target_unit: str = ""


class PlanTemplateMilestoneModel(BaseModel):
    """One template milestone hint, dated as start + offset_days."""

    title: str
    offset_days: int = 0


class PlanTemplateModel(BaseModel):
    """One habit-plan template (built-in or inline)."""

    id: str
    title: str = ""
    summary: str = ""
    duration_days: int = 30
    habit: PlanTemplateHabitModel = Field(default_factory=PlanTemplateHabitModel)
    milestones: list[PlanTemplateMilestoneModel] = Field(default_factory=list)
    builtin: bool = False


class PlanTemplateUsageModel(BaseModel):
    """One remembered template instantiation (profile history row)."""

    template_id: str
    title: str = ""
    used_at: str = ""
    project_id: str = ""
    habit_id: str = ""


class PlanTemplateListResponse(BaseModel):
    """Built-in templates plus the profile's usage history.

    Profile-scoped (not global) because the history half only exists per
    profile; history is de-duplicated by template id, most recent first.
    """

    profile: str
    builtin: list[PlanTemplateModel] = Field(default_factory=list)
    history: list[PlanTemplateUsageModel] = Field(default_factory=list)


class PlanTemplateInstantiateRequest(BaseModel):
    """Body for POST .../plan-templates/instantiate.

    ``template_id`` names a built-in (or previously used) template;
    ``template`` carries an inline template object instead (same shape as
    ``PlanTemplateModel``). ``title``/``start``/``habit_id`` override the
    template's plan title, start date (ISO, default today), and habit link.
    """

    template_id: str = ""
    template: dict[str, Any] | None = None
    title: str = Field(default="", max_length=200)
    start: str = ""
    habit_id: str = Field(default="", max_length=200)
    goal_refs: list[str] = Field(default_factory=list)


class PlanTemplateInstantiateResponse(BaseModel):
    """Result of instantiating one habit-plan template."""

    ok: bool
    case: ProjectCaseModel
    template_id: str = ""
    habit_id: str = ""
    created_habit: bool = False
    warnings: list[str] = Field(default_factory=list)


class ProjectCaseCreateRequest(BaseModel):
    """Body for creating one project case (only ``title`` is required)."""

    title: str = Field(min_length=1, max_length=200)
    id: str = Field(default="", max_length=200)
    status: str = "active"
    kind: str = "internal"
    visibility: str = "private"
    summary: str = Field(default="", max_length=4000)
    goal_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    habit_id: str = Field(default="", max_length=200)


class ProjectCaseUpdateRequest(BaseModel):
    """Body for the project-basics save (``None`` fields keep the value)."""

    title: str | None = Field(default=None, max_length=200)
    status: str | None = None
    kind: str | None = None
    visibility: str | None = None
    time_range: str | None = Field(default=None, max_length=100)
    summary: str | None = Field(default=None, max_length=4000)
    notes: str | None = Field(default=None, max_length=8000)
    habit_id: str | None = Field(default=None, max_length=200)
    goal_refs: list[str] | None = None
    task_refs: list[str] | None = None
    evidence_refs: list[str] | None = None
    source_refs: list[str] | None = None
    experience_refs: list[str] | None = None
    output_refs: list[str] | None = None


class ProjectCaseMutationResponse(BaseModel):
    """Result of one project-case mutation (create/save/archive)."""

    ok: bool = True
    case: ProjectCaseModel
    warnings: list[str] = Field(default_factory=list)


class ProjectCaseDeleteRequest(BaseModel):
    """Body for the user-decided project case delete.

    ``confirm_title`` must equal the case title exactly (422
    ``project_delete_confirm_mismatch`` otherwise) — the type-the-name
    confirmation. ``record_chronicle`` opts into a ``project.deleted``
    chronicle entry (default off: household deletes stay out of the
    narrative).
    """

    confirm_title: str = Field(default="", max_length=200)
    record_chronicle: bool = False


class ProjectCaseDeleteResponse(BaseModel):
    """Result of one project case delete.

    ``tasks_unassigned`` counts live kanban.md tasks whose ``project_id``
    was cleared back to unassigned; ``evidence_refs_kept`` counts
    evidence-pool entries still referencing the deleted case (tombstone
    mechanism handles their display).
    """

    ok: bool = True
    deleted_id: str
    tasks_unassigned: int = 0
    evidence_refs_kept: int = 0


class ProjectMilestoneAddRequest(BaseModel):
    """Body for adding one milestone (only ``title`` is required)."""

    title: str = Field(min_length=1, max_length=200)
    id: str = Field(default="", max_length=200)
    target: str = Field(default="", max_length=500)
    date: str = Field(default="", max_length=40)
    summary: str = Field(default="", max_length=4000)


class ProjectMilestoneUpdateRequest(BaseModel):
    """Body for the milestone save (``None`` fields keep the value)."""

    title: str | None = Field(default=None, max_length=200)
    status: str | None = None
    target: str | None = Field(default=None, max_length=500)
    date: str | None = Field(default=None, max_length=40)
    summary: str | None = Field(default=None, max_length=4000)
    task_refs: list[str] | None = None
    evidence_refs: list[str] | None = None
    source_refs: list[str] | None = None
    output_refs: list[str] | None = None


class ProjectTaskCreateRequest(BaseModel):
    """Body for adding one project-linked kanban task."""

    title: str = Field(min_length=1, max_length=200)
    section: str = "Queue"
    milestone_id: str = Field(default="", max_length=200)
    context: str = Field(default="", max_length=2000)
    date: str = Field(default="", max_length=40)


class ProjectTaskMoveRequest(BaseModel):
    """Body for moving one project task to another kanban section."""

    target_section: str


class ProjectSuggestRefsResponse(BaseModel):
    """AI-suggested refs for one project case (confirm-not-fill payload).

    Suggestions are validated against the current option rows; the SPA shows
    them for review and merges them into the edit form only on user confirm.
    """

    ok: bool = True
    backend: str = ""
    suggestions: dict[str, list[str]] = Field(default_factory=dict)
    rationale: str = ""
    warnings: list[str] = Field(default_factory=list)


# --- Output Studio (M4): public blog drafts + candidate generation ----------


class StudioPostModel(BaseModel):
    """One public blog post, list view (mirrors core BlogPost meta)."""

    slug: str
    title: str = ""
    date: str = ""
    status: str = "draft"
    summary: str = ""
    cover: str = ""
    tags: list[str] = Field(default_factory=list)
    category_path: list[str] = Field(default_factory=list)


class StudioSourceOptionModel(BaseModel):
    """One {id, label} option row for the candidate-generation pickers."""

    id: str
    label: str = ""


class StudioOptionsModel(BaseModel):
    """Source pickers for the evidence/claim-first generation form."""

    claims: list[StudioSourceOptionModel] = Field(default_factory=list)
    evidence: list[StudioSourceOptionModel] = Field(default_factory=list)
    projects: list[StudioSourceOptionModel] = Field(default_factory=list)


class StudioSummaryModel(BaseModel):
    """Blog status counters for the studio header strip."""

    status_counts: dict[str, int] = Field(default_factory=dict)
    total_posts: int = 0


class StudioResponse(BaseModel):
    """Output Studio overview: posts, counters, and generation options."""

    profile: str
    initialized: bool = False
    summary: StudioSummaryModel = Field(default_factory=StudioSummaryModel)
    posts: list[StudioPostModel] = Field(default_factory=list)
    options: StudioOptionsModel = Field(default_factory=StudioOptionsModel)


class StudioInitResponse(BaseModel):
    """Result of initializing the profile's public layer (idempotent)."""

    ok: bool = True
    created_paths: list[str] = Field(default_factory=list)


class StudioPostDetailModel(StudioPostModel):
    """One public blog post, editor view (meta + Markdown body).

    ``meta`` carries the full front matter for round-trip fidelity (editor
    fields are whitelisted on save; unknown keys survive untouched).
    ``has_math`` mirrors the Streamlit math-safe rule: bodies containing
    LaTeX stay on the Markdown source editor.
    """

    meta: dict[str, Any] = Field(default_factory=dict)
    body: str = ""
    has_math: bool = False
    related_evidence: list[str] = Field(default_factory=list)
    related_kanban: list[str] = Field(default_factory=list)
    related_claims: list[str] = Field(default_factory=list)
    related_sources: list[str] = Field(default_factory=list)
    related_research_claims: list[str] = Field(default_factory=list)
    related_citations: list[str] = Field(default_factory=list)
    blocks_json: list[dict[str, Any]] = Field(default_factory=list)


class StudioPostCreateRequest(BaseModel):
    """Body for creating one blog draft (only ``title`` is required)."""

    title: str = Field(min_length=1, max_length=300)
    summary: str = Field(default="", max_length=1000)
    tags: list[str] = Field(default_factory=list)
    body: str = Field(default="", max_length=200_000)


class StudioPostSaveRequest(BaseModel):
    """Body for the blog save (``None`` fields keep the current value)."""

    title: str | None = Field(default=None, max_length=300)
    date: str | None = Field(default=None, max_length=40)
    status: str | None = None
    summary: str | None = Field(default=None, max_length=1000)
    cover: str | None = Field(default=None, max_length=500)
    tags: list[str] | None = None
    related_evidence: list[str] | None = None
    related_kanban: list[str] | None = None
    related_claims: list[str] | None = None
    related_sources: list[str] | None = None
    related_research_claims: list[str] | None = None
    related_citations: list[str] | None = None
    body: str | None = Field(default=None, max_length=200_000)
    blocks_json: list[dict[str, Any]] | None = None


class StudioValidationResponse(BaseModel):
    """Publish-readiness check outcome for one blog document."""

    ok: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class StudioPostMutationResponse(BaseModel):
    """Result of one blog post mutation (create/save/publish)."""

    ok: bool = True
    post: StudioPostDetailModel
    changed_paths: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class StudioCandidateRequest(BaseModel):
    """Body for candidate preview / draft creation from evidence or claims.

    ``target`` is ``blog`` / ``resume`` / ``project``; ``source`` is
    ``claims`` / ``evidence``. Resume bullets and project updates only make
    sense from claims (mirroring the Streamlit form rules); the project
    target additionally requires ``project_id``.
    """

    target: str = "blog"
    source: str = "claims"
    claim_ids: list[str] = Field(default_factory=list)
    evidence_id: str = ""
    project_id: str = ""


class StudioCandidateResponse(BaseModel):
    """Generated candidate preview (nothing persisted).

    ``kind`` is ``blog`` / ``resume`` / ``project_update``; ``candidate`` is
    the core candidate's ``to_dict()`` payload (blog/project) or
    ``{body, bullets}`` for resume bullets.
    """

    ok: bool = True
    kind: str
    candidate: dict[str, Any] = Field(default_factory=dict)


class StudioDraftResponse(BaseModel):
    """Result of confirming a candidate into a persisted draft."""

    ok: bool = True
    kind: str
    path: str
    slug: str = ""
    warnings: list[str] = Field(default_factory=list)


class StudioJdMatchRequest(BaseModel):
    """Body for the JD match analysis (LLM-backed; 422 when unconfigured)."""

    resume_md: str = Field(default="", max_length=50_000)
    jd_text: str = Field(default="", max_length=50_000)


class StudioJdMatchResponse(BaseModel):
    """JD match analysis Markdown (generated; review before use)."""

    ok: bool = True
    analysis: str


# --- Content / Career workspaces -------------------------------------------


class ContentMediaModel(BaseModel):
    """One file in a post's media directory (profile-relative path)."""

    path: str
    name: str = ""
    size: int = 0
    kind: str = ""
    referenced: bool = False
    cover: bool = False


class ContentMediaUploadResponse(BaseModel):
    ok: bool = True
    path: str
    kind: str
    size: int = 0
    snippet: str = ""


class ContentAIStatusResponse(BaseModel):
    """Configured content-AI features (text = LLM, cover = image provider)."""

    text: bool = False
    cover: bool = False


class ContentCoverCandidateRequest(BaseModel):
    candidate_path: str = Field(min_length=1, max_length=500)


class ContentCoverPromoteResponse(BaseModel):
    ok: bool = True
    path: str


class ContentWorkspaceResponse(BaseModel):
    profile: str
    posts: list[StudioPostModel] = Field(default_factory=list)
    summary: StudioSummaryModel = Field(default_factory=StudioSummaryModel)


class CareerResumeUpdateRequest(BaseModel):
    """Structured resume replacement (normalized server-side; unknown keys kept)."""

    resume: dict[str, Any] = Field(default_factory=dict)


class CareerDraftModel(BaseModel):
    """One tailored resume draft under ``resumes/generated/<id>.md``."""

    id: str
    target: str = ""
    path: str = ""
    markdown: str = ""
    etag: str = ""
    updated_at: float = 0.0
    jd_text: str = ""
    notes: str = ""
    analysis: dict[str, Any] | None = None


class CareerWorkspaceResponse(BaseModel):
    profile: str
    resume: dict[str, Any] = Field(default_factory=dict)
    resume_markdown: str = ""
    resume_etag: str = ""
    has_resume: bool = False
    photo_url: str = ""
    drafts: list[CareerDraftModel] = Field(default_factory=list)
    ai_available: bool = False
    pdf_available: bool = False


class CareerImportPreviewResponse(BaseModel):
    """Upload / paste preview. Nothing is written until the user picks a target."""

    ok: bool = True
    filename: str = ""
    text: str = ""
    markdown: str = ""
    resume: dict[str, Any] | None = None
    method: str = "text"
    error: str = ""


class CareerImportTextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=200_000)
    filename: str = ""


class CareerPhotoResponse(BaseModel):
    ok: bool = True
    path: str
    url: str


class CareerDraftRequest(BaseModel):
    target: str = Field(min_length=1, max_length=120)
    markdown: str = Field(min_length=1, max_length=200_000)
    overwrite: bool = False
    jd_text: str = Field(default="", max_length=50_000)
    notes: str = Field(default="", max_length=5_000)


class CareerDraftUpdateRequest(BaseModel):
    """Any subset: draft text and/or the JD / notes / last analysis sidecar."""

    markdown: str | None = Field(default=None, min_length=1, max_length=200_000)
    jd_text: str | None = Field(default=None, max_length=50_000)
    notes: str | None = Field(default=None, max_length=5_000)
    analysis: dict[str, Any] | None = None


class CareerPreviewRequest(BaseModel):
    """Live preview: render an (unsaved) resume mapping or a Markdown draft."""

    resume: dict[str, Any] | None = None
    markdown: str | None = Field(default=None, max_length=200_000)
    include_photo: bool = True


class CareerPreviewResponse(BaseModel):
    markdown: str
    html: str


class CareerExportRequest(BaseModel):
    """Render Markdown (a draft or the master resume) to md / html / pdf bytes."""

    format: str = Field(default="pdf", pattern="^(md|html|pdf)$")
    markdown: str = Field(default="", max_length=200_000)
    draft_id: str = ""
    include_photo: bool = True
    filename: str = ""


# --- Public site console: settings, post toggles, works, go-live -----------------


class PublicSiteSettingsModel(BaseModel):
    """``public-profile.yaml: site`` display switches."""

    show_photo: bool = True
    show_email: bool = False
    show_phone: bool = False
    resume_pdf: bool = False
    show_projects: bool = False
    base_url: str = ""


class PublicSiteSettingsUpdateRequest(BaseModel):
    """Partial settings update; ``visibility`` flips the whole site public/private."""

    show_photo: bool | None = None
    show_email: bool | None = None
    show_phone: bool | None = None
    resume_pdf: bool | None = None
    show_projects: bool | None = None
    base_url: str | None = Field(default=None, max_length=500)
    visibility: str | None = Field(default=None, pattern="^(public|private)$")


class PublicSiteIntroModel(BaseModel):
    """Home hero inputs, read from the master resume (career workspace)."""

    name: str = ""
    english_name: str = ""
    title: str = ""
    summary: str = ""
    photo: str = ""
    photo_url: str = ""
    phone: str = ""
    email: str = ""
    has_resume: bool = False


class PublicSitePostModel(BaseModel):
    """One blog post row with its public toggle and live state."""

    slug: str
    title: str = ""
    date: str = ""
    status: str = "draft"
    summary: str = ""
    library_hidden: bool = False
    public: bool = False
    live: bool = False


class PublicSiteWorkLinkModel(BaseModel):
    label: str = Field(default="", max_length=40)
    url: str = Field(max_length=1000)


class PublicSiteWorkModel(BaseModel):
    """One work (``outputs.yaml`` row): video, cover, links, publish switch."""

    id: str = Field(default="", max_length=80)
    title: str = Field(default="", max_length=200)
    type: str = "other"
    year: str = Field(default="", max_length=20)
    summary: str = Field(default="", max_length=2000)
    video: str = Field(default="", max_length=1000)
    video_mode: str = Field(default="embed", pattern="^(embed|link)$")
    cover: str = Field(default="", max_length=1000)
    links: list[PublicSiteWorkLinkModel] = Field(default_factory=list)
    status: str = Field(default="draft", pattern="^(draft|published)$")
    featured: bool = False


class PublicSiteWorksUpdateRequest(BaseModel):
    works: list[PublicSiteWorkModel] = Field(default_factory=list, max_length=60)


class PublicSitePageRefModel(BaseModel):
    path: str
    title: str = ""


class PublicSiteLiveModel(BaseModel):
    """Live directory state plus the diff against the current files."""

    output_dir: str
    exists: bool = False
    built_at: str = ""
    page_count: int = 0
    has_previous: bool = False
    previous_built_at: str = ""
    added: list[PublicSitePageRefModel] = Field(default_factory=list)
    changed: list[PublicSitePageRefModel] = Field(default_factory=list)
    removed: list[PublicSitePageRefModel] = Field(default_factory=list)
    pdf_live: bool = False
    pdf_pending: bool = False
    in_sync: bool = False


class PublicSiteResponse(BaseModel):
    """Public-site console overview (``initialized`` false until the public layer exists)."""

    profile: str
    initialized: bool = False
    visibility: str = "private"
    settings: PublicSiteSettingsModel = Field(default_factory=PublicSiteSettingsModel)
    intro: PublicSiteIntroModel = Field(default_factory=PublicSiteIntroModel)
    posts: list[PublicSitePostModel] = Field(default_factory=list)
    works: list[PublicSiteWorkModel] = Field(default_factory=list)
    works_etag: str = ""
    projects_count: int = 0
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    live: PublicSiteLiveModel | None = None
    pdf_available: bool = False


class PublicSitePostUpdateRequest(BaseModel):
    public: bool


class PublicSiteMediaResponse(BaseModel):
    path: str
    url: str = ""


class PublicSiteDeployResponse(BaseModel):
    ok: bool = True
    page_count: int = 0
    warnings: list[str] = Field(default_factory=list)


class PublicBuildPreviewPageModel(BaseModel):
    """One renderable site page in the in-memory preview."""

    path: str
    title: str = ""


class PublicBuildPreviewResponse(BaseModel):
    """In-memory site preview page list (HTML served per page)."""

    ok: bool = True
    include_drafts: bool = True
    pages: list[PublicBuildPreviewPageModel] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


# --- Sidecar info shared by Home / Research (M4) -----------------------------


class SidecarInfoModel(BaseModel):
    """Browser-facing Reader API sidecar coordinates for iframe/link entries.

    ``base`` is the resolved sidecar origin: ``NBLANE_READER_API_BASE`` (or
    ``NBLANE_PAPER_LIBRARY_BASE``), defaulting to ``http://127.0.0.1:8502``;
    the ``0``/``false``/``off``/``none`` sentinel resolves to ``""``, meaning
    same-origin (production single-port deployment) — the SPA then uses the
    relative ``*_url`` paths as-is. ``handoff_token`` is a short-lived
    ``core.auth`` handoff token for the sidecar's ``POST /auth/session``
    cookie bootstrap; it is empty when auth is off (the default single-user
    local mode), in which case the sidecar pages need no session at all.
    """

    base: str = ""
    configured: bool = False
    auth_enabled: bool = False
    handoff_token: str = ""
    paper_library_url: str = ""
    dashboard_url: str = ""


# --- Home (M4): profile dashboard overview -----------------------------------


class HomeGoalModel(BaseModel):
    """Primary-goal card data with derived progress.

    ``progress`` is the mean completion of the goal's projects (None when
    the goal has no projects); ``stalled`` mirrors the core 30-day
    no-activity rule. Both come from ``core.home_dashboard``'s pure-read
    goal-progress derivation.
    """

    id: str
    title: str = ""
    label: str = ""
    status: str = "active"
    target: str = ""
    progress: float | None = None
    stalled: bool = False
    project_count: int = 0


class HomeSkillsModel(BaseModel):
    """Skill-tree overview counters (subset of the dashboard skill summary)."""

    has_tree: bool = False
    schema_name: str = ""
    total: int = 0
    lit: int = 0
    lit_rate: float = 0.0
    counts: dict[str, int] = Field(default_factory=dict)
    evidence_risk_count: int = 0


class HomeKanbanTaskModel(BaseModel):
    """One Doing card row for the Home overview strip."""

    id: str = ""
    title: str = ""
    started_on: str = ""


class HomeKanbanModel(BaseModel):
    """Kanban overview: per-section counts plus the Doing strip."""

    counts: dict[str, int] = Field(default_factory=dict)
    doing_total: int = 0
    done_uncrystallized_count: int = 0
    doing: list[HomeKanbanTaskModel] = Field(default_factory=list)


class HomeEvidenceModel(BaseModel):
    """Evidence-pool attention counters for the Home overview."""

    total_entries: int = 0
    unlinked_count: int = 0
    needs_review_count: int = 0
    status_risk_count: int = 0
    done_uncrystallized_count: int = 0


class HomeSourcesModel(BaseModel):
    """Research source-inbox counters for the Home overview."""

    implemented: bool = False
    total: int = 0
    active_total: int = 0
    status_counts: dict[str, int] = Field(default_factory=dict)
    active_titles: list[str] = Field(default_factory=list)


class HomeProjectsModel(BaseModel):
    """Project-case counters for the Home overview."""

    total: int = 0
    status_counts: dict[str, int] = Field(default_factory=dict)


class HomeClaimsModel(BaseModel):
    """Profile claim counters for the Home overview."""

    total: int = 0
    accepted_count: int = 0
    draft_count: int = 0
    needs_refresh_count: int = 0


class HomeAgentActivityModel(BaseModel):
    """Agent Activity queue counters for the Home overview."""

    total: int = 0
    pending_total: int = 0
    pending_titles: list[str] = Field(default_factory=list)


class HomeHealthModel(BaseModel):
    """Profile-health counters for the Home overview."""

    counts: dict[str, int] = Field(default_factory=dict)
    context_ready: bool = True


class HomeResponse(BaseModel):
    """Home dashboard overview (M4): aggregated profile snapshot.

    Composed from the ``core.home_dashboard`` sub-summaries — the same
    pure-read aggregation the sidecar 3D dashboard consumes — but without
    the sidecar payload's snapshot-recording side effect (this GET never
    writes). ``sidecar`` carries the coordinates for the optional embedded
    3D dashboard iframe.
    """

    profile: str
    north_star: NorthStarModel = Field(default_factory=NorthStarModel)
    primary_goal: HomeGoalModel | None = None
    goal_counts: dict[str, int] = Field(default_factory=dict)
    skills: HomeSkillsModel = Field(default_factory=HomeSkillsModel)
    kanban: HomeKanbanModel = Field(default_factory=HomeKanbanModel)
    evidence: HomeEvidenceModel = Field(default_factory=HomeEvidenceModel)
    sources: HomeSourcesModel = Field(default_factory=HomeSourcesModel)
    projects: HomeProjectsModel = Field(default_factory=HomeProjectsModel)
    claims: HomeClaimsModel = Field(default_factory=HomeClaimsModel)
    agent_activity: HomeAgentActivityModel = Field(
        default_factory=HomeAgentActivityModel
    )
    health: HomeHealthModel = Field(default_factory=HomeHealthModel)
    sidecar: SidecarInfoModel = Field(default_factory=SidecarInfoModel)


# --- Research (M4): sidecar-cohesive research overview -----------------------


class ResearchSourceItemModel(BaseModel):
    """One research source row for the SPA overview list."""

    id: str
    title: str = ""
    kind: str = "web"
    status: str = "inbox"
    url: str = ""
    captured_at: str = ""
    tags: list[str] = Field(default_factory=list)
    summary: str = ""


class ResearchSummaryModel(BaseModel):
    """Research workspace counters for the SPA overview header."""

    total: int = 0
    active_total: int = 0
    status_counts: dict[str, int] = Field(default_factory=dict)
    kind_counts: dict[str, int] = Field(default_factory=dict)
    claims_total: int = 0
    citations_total: int = 0


class ResearchPaperItemModel(BaseModel):
    """Paper library projection used by the SPA research workbench."""

    id: str
    title: str = ""
    status: str = "inbox"
    captured_at: str = ""
    tags: list[str] = Field(default_factory=list)
    summary: str = ""
    analysis: dict[str, object] = Field(default_factory=dict)
    pdf_available: bool = False
    page_count: int = 0
    extraction_status: str = ""
    segment_count: int = 0
    annotation_count: int = 0
    translated_count: int = 0
    missing_count: int = 0
    stale_count: int = 0
    failed_count: int = 0
    translation_status: str = "missing"
    last_page: int = 0
    last_read_at: str = ""
    target_lang: str = "zh"


class ResearchResponse(BaseModel):
    """Research overview (M4): source-inbox summary plus sidecar entry.

    The PDF reader and Paper Library stay on the Reader API sidecar; this
    response gives the SPA page its summary data (sources / claims /
    citations) and the sidecar coordinates (links + iframe embed bootstrap).
    ``sources`` lists the most recently captured sources (capped).
    """

    profile: str
    summary: ResearchSummaryModel = Field(default_factory=ResearchSummaryModel)
    sources: list[ResearchSourceItemModel] = Field(default_factory=list)
    papers: list[ResearchPaperItemModel] = Field(default_factory=list)
    sidecar: SidecarInfoModel = Field(default_factory=SidecarInfoModel)


class ResearchReaderResponse(BaseModel):
    """Reader deep link minted for one profile paper."""

    profile: str
    source_id: str
    reader_url: str
    token: str = ""


# --- Research source intake (SPA research desk: inbox / connectors / AI) -----


class ResearchSourceDetailModel(BaseModel):
    """One research source row for the SPA source inbox (no reading/claims)."""

    id: str
    title: str = ""
    kind: str = "web"
    status: str = "inbox"
    url: str = ""
    captured_at: str = ""
    authors: list[str] = Field(default_factory=list)
    published: str = ""
    tags: list[str] = Field(default_factory=list)
    summary: str = ""
    notes: str = ""
    visibility: str = "private"
    origin: str = "manual"
    library_node_refs: list[str] = Field(default_factory=list)
    provider: str = ""
    pdf_available: bool = False
    etag: str = ""


class ResearchSourceOptionsModel(BaseModel):
    """Allowed enum values for source forms (from core.research_sources)."""

    kinds: list[str] = Field(default_factory=list)
    statuses: list[str] = Field(default_factory=list)
    visibilities: list[str] = Field(default_factory=list)


class ResearchSourcesResponse(BaseModel):
    """Source inbox list. ``total``/counts cover the whole inbox, unfiltered."""

    profile: str
    total: int = 0
    status_counts: dict[str, int] = Field(default_factory=dict)
    kind_counts: dict[str, int] = Field(default_factory=dict)
    sources: list[ResearchSourceDetailModel] = Field(default_factory=list)
    options: ResearchSourceOptionsModel = Field(default_factory=ResearchSourceOptionsModel)


class ResearchSourceCreateRequest(BaseModel):
    """Manually add one source; deduped by canonical URL."""

    title: str = Field(min_length=1, max_length=500)
    url: str = Field(default="", max_length=2000)
    kind: str = "web"
    status: str = "inbox"
    visibility: str = "private"
    tags: list[str] = Field(default_factory=list)
    authors: list[str] = Field(default_factory=list)
    published: str = Field(default="", max_length=64)
    summary: str = Field(default="", max_length=20_000)
    notes: str = Field(default="", max_length=20_000)


class ResearchSourcePatchRequest(BaseModel):
    """Partial source update; omitted (null) fields are left unchanged."""

    title: str | None = Field(default=None, max_length=500)
    url: str | None = Field(default=None, max_length=2000)
    kind: str | None = None
    status: str | None = None
    visibility: str | None = None
    tags: list[str] | None = None
    authors: list[str] | None = None
    published: str | None = Field(default=None, max_length=64)
    summary: str | None = Field(default=None, max_length=20_000)
    notes: str | None = Field(default=None, max_length=20_000)


class ResearchSourceMutationResponse(BaseModel):
    """Answer of the source create/update endpoints."""

    ok: bool = True
    source: ResearchSourceDetailModel


class ResearchSourceErrorResponse(ErrorResponse):
    """409/412 body: the current source (if any) and the duplicate it hit."""

    source: ResearchSourceDetailModel | None = None
    duplicate_source_id: str = ""


class ResearchSourceTaskResponse(BaseModel):
    """A kanban Queue task created from one source."""

    ok: bool = True
    task_id: str = ""
    title: str = ""


class ResearchConnectorModel(BaseModel):
    """One saved connector config (secret-looking keys are always stripped)."""

    id: str
    provider: str
    enabled: bool = True
    query: str = ""
    privacy_default: str = "private"
    status: str = "idle"
    last_run: str = ""
    options: dict[str, Any] = Field(default_factory=dict)
    rate_limit: dict[str, Any] = Field(default_factory=dict)
    last_result: dict[str, Any] = Field(default_factory=dict)


class ResearchLibraryNodeModel(BaseModel):
    """One Paper Library collection usable as a connector import target."""

    id: str
    path: str


class ResearchConnectorsResponse(BaseModel):
    """Connector configs plus provider metadata and import targets."""

    profile: str
    providers: list[str] = Field(default_factory=list)
    auto_providers: list[str] = Field(default_factory=list)
    connectors: list[ResearchConnectorModel] = Field(default_factory=list)
    library_nodes: list[ResearchLibraryNodeModel] = Field(default_factory=list)


class ResearchConnectorUpsertRequest(BaseModel):
    """Create/update one connector. Never carries tokens/cookies/API keys."""

    provider: str
    connector_id: str = Field(default="", max_length=200)
    query: str = Field(default="", max_length=1000)
    enabled: bool = True
    privacy_default: str = "private"
    options: dict[str, Any] = Field(default_factory=dict)


class ResearchImportTargetModel(BaseModel):
    """Where imported candidates land: inbox, metadata only, or a collection."""

    kind: Literal["source_inbox", "metadata_only", "collection"] = "source_inbox"
    node_id: str = ""


class ResearchConnectorCandidateModel(BaseModel):
    """One discovered candidate with its duplicate verdict."""

    fingerprint: str
    canonical_url: str = ""
    selected: bool = False
    duplicate: dict[str, Any] = Field(default_factory=dict)
    item: dict[str, Any] = Field(default_factory=dict)


class ResearchConnectorPreviewModel(BaseModel):
    """Dry-run discovery result (no source facts written)."""

    connector_id: str = ""
    provider: str = ""
    query: str = ""
    discovered: int = 0
    importable: int = 0
    skipped: int = 0
    candidates: list[ResearchConnectorCandidateModel] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ResearchConnectorImportResultModel(BaseModel):
    """Outcome of importing selected candidates (or a full connector run)."""

    connector_id: str = ""
    provider: str = ""
    discovered: int = 0
    imported: int = 0
    skipped: int = 0
    imported_source_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    error: str = ""


class ResearchManualPreviewRequest(BaseModel):
    """Pasted URLs / CSV / JSON list to preview without a saved connector."""

    provider: str
    raw_items: str = Field(min_length=1, max_length=200_000)


class ResearchManualImportRequest(ResearchManualPreviewRequest):
    """Import selected fingerprints from a pasted manual list."""

    fingerprints: list[str] = Field(default_factory=list)
    privacy_default: str = "private"
    target: ResearchImportTargetModel = Field(default_factory=ResearchImportTargetModel)


class ResearchConnectorImportRequest(BaseModel):
    """Import selected candidates of a saved connector (async job).

    An empty ``fingerprints`` list runs the whole connector (every
    non-duplicate discovery is imported), like the Streamlit "run now".
    """

    fingerprints: list[str] = Field(default_factory=list)
    target: ResearchImportTargetModel = Field(default_factory=ResearchImportTargetModel)


class ResearchAIActionModel(BaseModel):
    """One research AI action's effective routing preference."""

    action: str
    default_backend: str = "llm"
    backend: str = ""
    llm_model: str = ""
    codex_model: str = ""


class ResearchAIConfigResponse(BaseModel):
    """Research-scoped slice of ``web-preferences.yaml`` ``ai.actions``."""

    profile: str
    actions: list[ResearchAIActionModel] = Field(default_factory=list)
    llm_default_model: str = ""
    codex_default_model: str = ""
    codex_model_suggestions: list[str] = Field(default_factory=list)


class ResearchAIActionUpdate(BaseModel):
    """Backend/model choice for one action; empty strings mean app default."""

    backend: Literal["", "llm", "codex"] = ""
    llm_model: str = Field(default="", max_length=200)
    codex_model: str = Field(default="", max_length=200)


class ResearchAIConfigUpdateRequest(BaseModel):
    """Only research actions are accepted; unknown keys answer 422."""

    actions: dict[str, ResearchAIActionUpdate] = Field(default_factory=dict)
