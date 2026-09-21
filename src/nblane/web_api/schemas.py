"""Pydantic v2 response models for the nblane FastAPI backend."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    """Structured error body returned for 4xx responses."""

    code: str
    message: str


class HealthResponse(BaseModel):
    """Liveness probe payload."""

    ok: bool = True
    version: str


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


class SkillTreeNodeModel(BaseModel):
    """One node in the recursive skill-tree view.

    ``title`` comes from the domain schema ``label`` (node id as fallback);
    ``children`` are derived from schema ``requires`` edges restricted to
    the profile overlay; ``evidence_count`` counts resolved evidence (pool
    refs plus inline rows, deprecated/missing refs excluded).
    """

    id: str
    title: str = ""
    status: str = "locked"
    evidence_count: int = 0
    children: list[SkillTreeNodeModel] = Field(default_factory=list)


class SkillTreeResponse(BaseModel):
    """Full skill tree: queue-wide status counters plus the nested nodes."""

    profile: str
    schema_name: str = ""
    updated: str = ""
    status_counts: dict[str, int] = Field(default_factory=dict)
    nodes: list[SkillTreeNodeModel] = Field(default_factory=list)


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


class ActivityItemErrorResponse(ErrorResponse):
    """Error body that also carries the current activity item."""

    item: ActivityItemModel | None = None


class KanbanSubtaskModel(BaseModel):
    """One checkbox sub-item under a kanban card."""

    title: str
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
    crystallized: bool = False
    project_id: str = ""
    milestone_id: str = ""
    agent_task_id: str = ""
    tags: str = ""
    subtasks: list[KanbanSubtaskModel] = Field(default_factory=list)
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


class KanbanCardCreateRequest(BaseModel):
    """Quick-add body for POST .../kanban/cards."""

    title: str = Field(min_length=1, max_length=200)
    section: str = "Queue"
    context: str = ""
    tags: list[str] = Field(default_factory=list)


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
    returned verbatim; ``visibility`` is informational for the UI badge.
    """

    visibility: str = "discreet"
    is_set: bool = False
    full: str = ""
    brief: str = ""


class GoalsResponse(BaseModel):
    """The profile's goal book as the human owner sees it."""

    profile: str
    current_goal_id: str = ""
    north_star: NorthStarModel = Field(default_factory=NorthStarModel)
    goals: list[GoalModel] = Field(default_factory=list)


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
    ``project-suggest-refs`` takes ``{case_id: str}`` (non-blank).
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
    limit: int = 100
    total: int = 0
    items: list[EvidenceEntryModel] = Field(default_factory=list)


class EvidenceReviewItemModel(BaseModel):
    """One evidence-pool row in the Evidence Review triage view.

    ``review_reason`` mirrors the Streamlit page rule: a row needs review
    when its strength is unrated and/or its review_status is not reviewed.
    ``skill_refs`` / ``usage_count`` count skill-tree nodes citing the row.
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


class ReviewCandidateModel(BaseModel):
    """One weekly-review candidate (evidence/next_action/method/public_draft).

    Mirrors the dicts produced by ``core.growth_review.build_weekly_review``;
    extension keys (e.g. ``tags``) are preserved so the SPA can round-trip a
    candidate from the GET response into the save/apply mutations unchanged.
    """

    model_config = ConfigDict(extra="allow")

    source: str = ""
    task_id: str = ""
    resource_id: str = ""
    title: str = ""
    summary: str = ""
    notes: list[str] = Field(default_factory=list)
    visibility: str = ""
    draft: bool = True


class ReviewSummaryModel(BaseModel):
    """Candidate counters for the weekly review header."""

    done_tasks: int = 0
    evidence_candidates: int = 0
    next_action_candidates: int = 0
    public_draft_candidates: int = 0


class ReviewResponse(BaseModel):
    """Candidate-only weekly review payload (``GrowthReview`` projection).

    Read-only aggregation over kanban.md Done cards plus the optional
    activity/learning/inbox logs; no LLM involvement in this slice.
    """

    profile: str
    week_start: str
    week_end: str
    done_task_ids: list[str] = Field(default_factory=list)
    activity_summary: dict[str, Any] = Field(default_factory=dict)
    learning_summary: dict[str, Any] = Field(default_factory=dict)
    inbox_summary: dict[str, Any] = Field(default_factory=dict)
    evidence_candidates: list[ReviewCandidateModel] = Field(default_factory=list)
    next_queue_candidates: list[ReviewCandidateModel] = Field(default_factory=list)
    method_candidates: list[ReviewCandidateModel] = Field(default_factory=list)
    public_candidates: list[ReviewCandidateModel] = Field(default_factory=list)
    summary: ReviewSummaryModel = Field(default_factory=ReviewSummaryModel)


class ReviewSaveRequest(BaseModel):
    """Body for saving selected candidates to Agent Activity.

    ``candidate_type`` is one of ``evidence`` / ``next_action`` /
    ``public_draft``; ``start``/``end`` are the ISO review window the
    candidates were generated from (recorded as the activity source_ref).
    """

    start: str = Field(min_length=1)
    end: str = Field(min_length=1)
    candidate_type: str
    candidates: list[ReviewCandidateModel] = Field(min_length=1)


class ReviewSaveResponse(BaseModel):
    """Result of persisting candidates as pending Activity items."""

    ok: bool = True
    saved: int = 0
    item_ids: list[str] = Field(default_factory=list)


class ReviewApplyRequest(ReviewSaveRequest):
    """Body for applying selected candidates to their owner files.

    ``mark_crystallized`` only affects evidence candidates: the source Done
    kanban card is marked crystallized after a successful pool writeback.
    """

    mark_crystallized: bool = True


class ReviewApplyResultModel(BaseModel):
    """Per-candidate outcome of one apply call (mirrors ReviewApplyResult)."""

    ok: bool
    title: str = ""
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    changed_paths: list[str] = Field(default_factory=list)
    output_path: str = ""


class ReviewApplyResponse(BaseModel):
    """Aggregate outcome of applying the selected candidates.

    Apply is per-candidate: individual failures (e.g. pool merge conflict)
    land in ``results`` with ``ok=false`` and do not fail the whole request,
    mirroring the Streamlit page which applies candidates one by one.
    """

    ok: bool = True
    applied: int = 0
    failed: int = 0
    results: list[ReviewApplyResultModel] = Field(default_factory=list)


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


class ProjectCaseUpdateRequest(BaseModel):
    """Body for the project-basics save (``None`` fields keep the value)."""

    title: str | None = Field(default=None, max_length=200)
    status: str | None = None
    kind: str | None = None
    visibility: str | None = None
    time_range: str | None = Field(default=None, max_length=100)
    summary: str | None = Field(default=None, max_length=4000)
    notes: str | None = Field(default=None, max_length=8000)
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


# --- Public Build (M5): validate / build / publish-and-build the static site --


class PublicBuildValidationModel(BaseModel):
    """Public-layer validation outcome (mirrors core PublicValidationResult)."""

    ok: bool = True
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class PublicBuildDraftModel(BaseModel):
    """One unpublished blog draft offered by the publish-and-build section."""

    slug: str
    title: str = ""
    date: str = ""


class PublicBuildArtifactModel(BaseModel):
    """One file under the build output directory (relative path + stat)."""

    path: str
    size: int = 0
    modified: str = ""


class PublicBuildStateModel(BaseModel):
    """Observed state of the static-site output directory.

    Derived from the directory itself (no separate build log): ``exists``
    reports whether a build has ever landed, ``built_at`` is the newest
    artifact mtime, and ``artifacts`` is the capped flat listing.
    """

    output_dir: str
    exists: bool = False
    built_at: str = ""
    total_files: int = 0
    total_bytes: int = 0
    artifacts_truncated: bool = False
    artifacts: list[PublicBuildArtifactModel] = Field(default_factory=list)


class PublicBuildResponse(BaseModel):
    """Public Build overview: init gate, validation, drafts, output state.

    ``validation``/``drafts`` are null/empty until the profile's public
    layer is initialized (POST ``/studio/init`` creates it).
    """

    profile: str
    initialized: bool = False
    validation: PublicBuildValidationModel | None = None
    drafts: list[PublicBuildDraftModel] = Field(default_factory=list)
    build: PublicBuildStateModel


class PublicBuildRequest(BaseModel):
    """Body for the static-site build (synchronous, no LLM).

    ``base_url`` is the production site URL (optional sub-path) used for
    canonical/sitemap links, mirroring the Streamlit form. The output
    directory is pinned server-side (``dist/public/<name>`` under the data
    root) — the Streamlit page's free-form output path is not exposed for
    path safety.
    """

    include_drafts: bool = False
    base_url: str = Field(default="", max_length=500)


class PublicBuildPublishRequest(PublicBuildRequest):
    """Body for publish-and-build: draft slugs to publish, then build."""

    slugs: list[str] = Field(default_factory=list)


class PublicBuildResultResponse(BaseModel):
    """Result of one build / publish-and-build run."""

    ok: bool = True
    output_dir: str
    page_count: int = 0
    pages: list[str] = Field(default_factory=list)
    published: list[str] = Field(default_factory=list)


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
    sidecar: SidecarInfoModel = Field(default_factory=SidecarInfoModel)
