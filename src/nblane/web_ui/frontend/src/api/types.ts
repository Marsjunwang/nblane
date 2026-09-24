// API types for the SPA, generated from the backend OpenAPI contract.
//
// The interfaces below are aliases over `schema.d.ts`, which is produced by
// `npm run gen:api` (openapi-typescript) from the committed contract snapshot
// `openapi.json` (see scripts/dump-openapi.sh). Backend schema models are the
// source of truth (src/nblane/web_api/schemas.py, auth.py, assistant.py).
//
// Only frontend-only composite types (ETag wrappers, clarify-action enum) are
// still hand-written at the bottom.

import type { components } from './schema';

type Schemas = components['schemas'];

/** CurrentUser from web_api/auth.py. */
export type CurrentUser = Schemas['CurrentUser'];

/** Generic acknowledgement body (web_api/auth.py OkResponse). */
export type OkResponse = Schemas['OkResponse'];

/** ProfileSummary from web_api/schemas.py. */
export type ProfileSummary = Schemas['ProfileSummary'];

/** SkillTreeNodeModel from web_api/schemas.py (recursive tree node). */
export type SkillTreeNode = Schemas['SkillTreeNodeModel'];

/** SkillTreeResponse from web_api/schemas.py. */
export type SkillTreeResponse = Schemas['SkillTreeResponse'];

/** SkillTreeCategoryModel from web_api/schemas.py (banner rollup). */
export type SkillTreeCategory = Schemas['SkillTreeCategoryModel'];

/** SkillNodePatchRequest from web_api/schemas.py (三态 status write). */
export type SkillNodePatchRequest = Schemas['SkillNodePatchRequest'];

/** SkillNodePatchResponse from web_api/schemas.py (post-map YAML status). */
export type SkillNodePatchResponse = Schemas['SkillNodePatchResponse'];

/** HealthIssueModel from web_api/schemas.py. */
export type HealthIssue = Schemas['HealthIssueModel'];

/** HealthReportModel from web_api/schemas.py. */
export type HealthReport = Schemas['HealthReportModel'];

/** Structured error body (web_api/schemas.py ErrorResponse, via ApiError). */
export type ErrorResponseBody = Schemas['ErrorResponse'];

/** ActivityItemModel from web_api/schemas.py (extension keys allowed). */
export type ActivityItem = Schemas['ActivityItemModel'];

/** ActivitySummaryModel — queue-wide counters, ignoring list filters. */
export type ActivitySummary = Schemas['ActivitySummaryModel'];

/** ActivityListResponse from web_api/schemas.py. */
export type ActivityListResponse = Schemas['ActivityListResponse'];

/** ActivityApplyResponse from web_api/schemas.py. */
export type ActivityApplyResponse = Schemas['ActivityApplyResponse'];

/** ActivityDismissResponse from web_api/schemas.py. */
export type ActivityDismissResponse = Schemas['ActivityDismissResponse'];

/** KanbanSubtaskModel from web_api/schemas.py. */
export type KanbanSubtask = Schemas['KanbanSubtaskModel'];

/** KanbanTodoModel from web_api/schemas.py (detail-card checklist item). */
export type KanbanTodo = Schemas['KanbanTodoModel'];

/** KanbanTaskModel from web_api/schemas.py. */
export type KanbanTask = Schemas['KanbanTaskModel'];

/** KanbanSectionModel from web_api/schemas.py. */
export type KanbanSection = Schemas['KanbanSectionModel'];

/** KanbanBoardResponse from web_api/schemas.py. */
export type KanbanBoard = Schemas['KanbanBoardResponse'];

/** KanbanCardCreateRequest from web_api/schemas.py (only title required; the
 * other fields are server-defaulted but the OpenAPI snapshot marks them required). */
export type KanbanCardCreateRequest = { title: string } & Partial<
  Omit<Schemas['KanbanCardCreateRequest'], 'title'>
>;

/** KanbanMutationResponse from web_api/schemas.py. */
export type KanbanMutationResponse = Schemas['KanbanMutationResponse'];

/** InboxHistoryEventModel from web_api/schemas.py. */
export type InboxHistoryEvent = Schemas['InboxHistoryEventModel'];

/** InboxItemModel from web_api/schemas.py. */
export type InboxItem = Schemas['InboxItemModel'];

/** InboxResponse from web_api/schemas.py. */
export type InboxResponse = Schemas['InboxResponse'];

/** InboxCaptureRequest from web_api/schemas.py. */
export type InboxCaptureRequest = Schemas['InboxCaptureRequest'];

/** InboxMutationResponse from web_api/schemas.py. */
export type InboxMutationResponse = Schemas['InboxMutationResponse'];

/** GoalSkillLinkModel from web_api/schemas.py. */
export type GoalSkillLink = Schemas['GoalSkillLinkModel'];

/** GoalModel from web_api/schemas.py (owner-facing, no redaction). */
export type Goal = Schemas['GoalModel'];

/** NorthStarModel from web_api/schemas.py (owner-facing, no redaction). */
export type NorthStar = Schemas['NorthStarModel'];

/** GoalsResponse from web_api/schemas.py. */
export type GoalsResponse = Schemas['GoalsResponse'];

/** NorthStarPatchRequest from web_api/schemas.py (all fields optional). */
export type NorthStarPatchRequest = Schemas['NorthStarPatchRequest'];

/** NorthStarMutationResponse from web_api/schemas.py. */
export type NorthStarMutationResponse = Schemas['NorthStarMutationResponse'];

/** GoalCreateRequest from web_api/schemas.py (only title required; the other
 * fields are server-defaulted but the OpenAPI snapshot marks them required). */
export type GoalCreateRequest = { title: string } & Partial<
  Omit<Schemas['GoalCreateRequest'], 'title'>
>;

/** GoalPatchRequest from web_api/schemas.py (at least one field). */
export type GoalPatchRequest = Schemas['GoalPatchRequest'];

/** GoalMutationResponse from web_api/schemas.py. */
export type GoalMutationResponse = Schemas['GoalMutationResponse'];

/** ChronicleEntryModel from web_api/schemas.py (append-only entry). */
export type ChronicleEntry = Schemas['ChronicleEntryModel'];

/** ChronicleResponse from web_api/schemas.py (newest first). */
export type ChronicleResponse = Schemas['ChronicleResponse'];

/** EvidenceEntryModel from web_api/schemas.py (list view). */
export type EvidenceEntry = Schemas['EvidenceEntryModel'];

/** EvidenceEntryDetailModel from web_api/schemas.py (detail view). */
export type EvidenceEntryDetail = Schemas['EvidenceEntryDetailModel'];

/** EvidenceListResponse from web_api/schemas.py. */
export type EvidenceListResponse = Schemas['EvidenceListResponse'];

/** EvidenceReviewItemModel from web_api/schemas.py (triage row). */
export type EvidenceReviewItem = Schemas['EvidenceReviewItemModel'];

/** EvidenceReviewSummaryModel — queue-wide counters, ignoring list filters. */
export type EvidenceReviewSummary = Schemas['EvidenceReviewSummaryModel'];

/** EvidenceReviewListResponse from web_api/schemas.py. */
export type EvidenceReviewListResponse = Schemas['EvidenceReviewListResponse'];

/** EvidenceReviewBulkRequest from web_api/schemas.py (accept/tag mutation). */
export type EvidenceReviewBulkRequest = Schemas['EvidenceReviewBulkRequest'];

/** EvidenceReviewDeprecateRequest from web_api/schemas.py (reject/restore). */
export type EvidenceReviewDeprecateRequest = Schemas['EvidenceReviewDeprecateRequest'];

/** EvidenceReviewMutationResponse from web_api/schemas.py. */
export type EvidenceReviewMutationResponse = Schemas['EvidenceReviewMutationResponse'];

/** EvidenceEditRequest from web_api/schemas.py (whitelist field edit). */
export type EvidenceEditRequest = Schemas['EvidenceEditRequest'];

/** EvidenceEntryActionRequest from web_api/schemas.py (accept/reject/restore). */
export type EvidenceEntryActionRequest = Schemas['EvidenceEntryActionRequest'];

/** EvidenceSkillLinksRequest from web_api/schemas.py (chip-save link set). */
export type EvidenceSkillLinksRequest = Schemas['EvidenceSkillLinksRequest'];

/** EvidenceSkillLinksResponse from web_api/schemas.py. */
export type EvidenceSkillLinksResponse = Schemas['EvidenceSkillLinksResponse'];

/** EvidenceSkillSuggestionModel from web_api/schemas.py. */
export type EvidenceSkillSuggestion = Schemas['EvidenceSkillSuggestionModel'];

/** EvidenceSkillSuggestionsResponse from web_api/schemas.py. */
export type EvidenceSkillSuggestionsResponse = Schemas['EvidenceSkillSuggestionsResponse'];

/** EvidenceStageRiskModel from web_api/schemas.py (待补强 row). */
export type EvidenceStageRisk = Schemas['EvidenceStageRiskModel'];

/** EvidenceStagesResponse from web_api/schemas.py (five-stage counters). */
export type EvidenceStagesResponse = Schemas['EvidenceStagesResponse'];

/** ProvenanceRefModel from web_api/schemas.py (kanban ref + tombstone). */
export type ProvenanceRef = Schemas['ProvenanceRefModel'];

/** CrystallizeCandidateModel from web_api/schemas.py (wizard step 1 row). */
export type CrystallizeCandidate = Schemas['CrystallizeCandidateModel'];

/** CrystallizeCandidatesResponse from web_api/schemas.py. */
export type CrystallizeCandidatesResponse = Schemas['CrystallizeCandidatesResponse'];

/** CrystallizeDraftRequest from web_api/schemas.py. */
export type CrystallizeDraftRequest = Schemas['CrystallizeDraftRequest'];

/** CrystallizeDraftResponse from web_api/schemas.py (rule 200 / job result). */
export type CrystallizeDraftResponse = Schemas['CrystallizeDraftResponse'];

/** CrystallizeApplyRequest from web_api/schemas.py. */
export type CrystallizeApplyRequest = Schemas['CrystallizeApplyRequest'];

/** CrystallizeApplyResponse from web_api/schemas.py. */
export type CrystallizeApplyResponse = Schemas['CrystallizeApplyResponse'];

/** GapAnalyzeRequest from web_api/schemas.py (sync rule / async LLM dispatch). */
export type GapAnalyzeRequest = Schemas['GapAnalyzeRequest'];

/** GapTopMatchModel from web_api/schemas.py. */
export type GapTopMatch = Schemas['GapTopMatchModel'];

/** GapClosureNodeModel from web_api/schemas.py. */
export type GapClosureNode = Schemas['GapClosureNodeModel'];

/** GapAnalysisResponse from web_api/schemas.py (GapResult projection). */
export type GapAnalysisResult = Schemas['GapAnalysisResponse'];

/** JobModel from web_api/schemas.py (async-job snapshot). */
export type JobModel = Schemas['JobModel'];

/** JobCreateRequest from web_api/schemas.py (kind + validated input). */
export type JobCreateRequest = Schemas['JobCreateRequest'];

/** JobCreateResponse from web_api/schemas.py (202 of the job endpoints). */
export type JobCreateResponse = Schemas['JobCreateResponse'];

/** JobStatusResponse from web_api/schemas.py (poll: snapshot + result). */
export type JobStatusResponse = Schemas['JobStatusResponse'];

/** One progress event replayed over the job SSE stream (seq-ordered). */
export interface JobProgressEvent {
  event?: string;
  phase?: string;
  message?: string;
  seq?: number;
  created_at?: number;
  elapsed_ms?: number;
}

/** SSE frame payloads of GET .../jobs/{id}/stream (web_api/jobs.py). */
export interface JobStreamFrame {
  ok: boolean;
  job?: JobModel;
  event?: JobProgressEvent;
  result?: Record<string, unknown> | null;
  error?: { code: string; message: string } | null;
}

/** GapIntakeRequest from web_api/schemas.py. */
export type GapIntakeRequest = Schemas['GapIntakeRequest'];

/** ReviewCandidateModel from web_api/schemas.py (round-trippable candidate). */
export type ReviewCandidate = Schemas['ReviewCandidateModel'];

/** ReviewSummaryModel — candidate counters for the review header. */
export type ReviewSummary = Schemas['ReviewSummaryModel'];

/** ReviewResponse from web_api/schemas.py (GrowthReview projection). */
export type ReviewResponse = Schemas['ReviewResponse'];

/** ReviewSaveRequest from web_api/schemas.py (save-to-activity mutation). */
export type ReviewSaveRequest = Schemas['ReviewSaveRequest'];

/** ReviewSaveResponse from web_api/schemas.py. */
export type ReviewSaveResponse = Schemas['ReviewSaveResponse'];

/** ReviewApplyRequest from web_api/schemas.py (apply mutation). */
export type ReviewApplyRequest = Schemas['ReviewApplyRequest'];

/** ReviewApplyResultModel from web_api/schemas.py (per-candidate outcome). */
export type ReviewApplyResultItem = Schemas['ReviewApplyResultModel'];

/** ReviewApplyResponse from web_api/schemas.py. */
export type ReviewApplyResponse = Schemas['ReviewApplyResponse'];

/** AssistantGatewayStatus from web_api/assistant.py. */
export type AssistantGatewayStatus = Schemas['AssistantGatewayStatus'];

/** AssistantAutomationsStatus from web_api/assistant.py. */
export type AssistantAutomationsStatus = Schemas['AssistantAutomationsStatus'];

/** AssistantStatusResponse from web_api/assistant.py. */
export type AssistantStatus = Schemas['AssistantStatusResponse'];

/** WorkshopStatusResponse from web_api/workshop.py. */
export type WorkshopStatus = Schemas['WorkshopStatusResponse'];

/** ProjectMilestoneModel from web_api/schemas.py (with completion counts). */
export type ProjectMilestone = Schemas['ProjectMilestoneModel'];

/** ProjectTaskModel from web_api/schemas.py (owned kanban task row). */
export type ProjectTask = Schemas['ProjectTaskModel'];

/** ProjectCaseModel from web_api/schemas.py (case + milestones + tasks). */
export type ProjectCase = Schemas['ProjectCaseModel'];

/** ProjectBoardSummaryModel — overview counters for the board header. */
export type ProjectBoardSummary = Schemas['ProjectBoardSummaryModel'];

/** ProjectRefOptionModel from web_api/schemas.py ({id, label, owner}). */
export type ProjectRefOption = Schemas['ProjectRefOptionModel'];

/** ProjectBoardOptionsModel from web_api/schemas.py (ref-picker rows). */
export type ProjectBoardOptions = Schemas['ProjectBoardOptionsModel'];

/** ProjectBoardResponse from web_api/schemas.py. */
export type ProjectBoard = Schemas['ProjectBoardResponse'];

/** ProjectCaseCreateRequest from web_api/schemas.py. */
export type ProjectCaseCreateRequest = Schemas['ProjectCaseCreateRequest'];

/** ProjectCaseUpdateRequest from web_api/schemas.py. */
export type ProjectCaseUpdateRequest = Schemas['ProjectCaseUpdateRequest'];

/** ProjectCaseMutationResponse from web_api/schemas.py. */
export type ProjectCaseMutationResponse = Schemas['ProjectCaseMutationResponse'];

/** ProjectMilestoneAddRequest from web_api/schemas.py. */
export type ProjectMilestoneAddRequest = Schemas['ProjectMilestoneAddRequest'];

/** ProjectMilestoneUpdateRequest from web_api/schemas.py. */
export type ProjectMilestoneUpdateRequest = Schemas['ProjectMilestoneUpdateRequest'];

/** ProjectTaskCreateRequest from web_api/schemas.py. */
export type ProjectTaskCreateRequest = Schemas['ProjectTaskCreateRequest'];

/** ProjectSuggestRefsResponse from web_api/schemas.py. */
export type ProjectSuggestRefsResponse = Schemas['ProjectSuggestRefsResponse'];

/** StudioPostModel from web_api/schemas.py (blog list row). */
export type StudioPost = Schemas['StudioPostModel'];

/** StudioPostDetailModel from web_api/schemas.py (editor view). */
export type StudioPostDetail = Schemas['StudioPostDetailModel'];

/** StudioSourceOptionModel from web_api/schemas.py ({id, label} picker row). */
export type StudioSourceOption = Schemas['StudioSourceOptionModel'];

/** StudioOptionsModel from web_api/schemas.py (generation form pickers). */
export type StudioOptions = Schemas['StudioOptionsModel'];

/** StudioSummaryModel from web_api/schemas.py (blog status counters). */
export type StudioSummary = Schemas['StudioSummaryModel'];

/** StudioResponse from web_api/schemas.py (studio overview). */
export type StudioResponse = Schemas['StudioResponse'];

/** StudioInitResponse from web_api/schemas.py. */
export type StudioInitResponse = Schemas['StudioInitResponse'];

/** StudioPostCreateRequest from web_api/schemas.py. */
export type StudioPostCreateRequest = Schemas['StudioPostCreateRequest'];

/** StudioPostSaveRequest from web_api/schemas.py (None fields keep values). */
export type StudioPostSaveRequest = Schemas['StudioPostSaveRequest'];

/** StudioValidationResponse from web_api/schemas.py (publish check). */
export type StudioValidationResponse = Schemas['StudioValidationResponse'];

/** StudioPostMutationResponse from web_api/schemas.py. */
export type StudioPostMutationResponse = Schemas['StudioPostMutationResponse'];

/** StudioCandidateRequest from web_api/schemas.py. */
export type StudioCandidateRequest = Schemas['StudioCandidateRequest'];

/** StudioCandidateResponse from web_api/schemas.py (preview, no write). */
export type StudioCandidateResponse = Schemas['StudioCandidateResponse'];

/** StudioDraftResponse from web_api/schemas.py (confirmed draft write). */
export type StudioDraftResponse = Schemas['StudioDraftResponse'];

/** StudioJdMatchRequest from web_api/schemas.py. */
export type StudioJdMatchRequest = Schemas['StudioJdMatchRequest'];

/** StudioJdMatchResponse from web_api/schemas.py. */
export type StudioJdMatchResponse = Schemas['StudioJdMatchResponse'];

/** PublicBuildValidationModel from web_api/schemas.py (public-layer check). */
export type PublicBuildValidation = Schemas['PublicBuildValidationModel'];

/** PublicBuildDraftModel from web_api/schemas.py (unpublished draft row). */
export type PublicBuildDraft = Schemas['PublicBuildDraftModel'];

/** PublicBuildArtifactModel from web_api/schemas.py (output file row). */
export type PublicBuildArtifact = Schemas['PublicBuildArtifactModel'];

/** PublicBuildStateModel from web_api/schemas.py (output-dir state). */
export type PublicBuildState = Schemas['PublicBuildStateModel'];

/** PublicBuildResponse from web_api/schemas.py (public-build overview). */
export type PublicBuildResponse = Schemas['PublicBuildResponse'];

/** PublicBuildRequest from web_api/schemas.py (build body). */
export type PublicBuildRequest = Schemas['PublicBuildRequest'];

/** PublicBuildPublishRequest from web_api/schemas.py (publish+build body). */
export type PublicBuildPublishRequest = Schemas['PublicBuildPublishRequest'];

/** PublicBuildResultResponse from web_api/schemas.py (one build run). */
export type PublicBuildResultResponse = Schemas['PublicBuildResultResponse'];

/** PublicBuildPreviewPageModel from web_api/schemas.py (preview picker row). */
export type PublicBuildPreviewPage = Schemas['PublicBuildPreviewPageModel'];

/** PublicBuildPreviewResponse from web_api/schemas.py (preview page list). */
export type PublicBuildPreviewResponse = Schemas['PublicBuildPreviewResponse'];

/** SidecarInfoModel from web_api/schemas.py (Reader API sidecar coordinates). */
export type SidecarInfo = Schemas['SidecarInfoModel'];

/** HomeGoalModel from web_api/schemas.py (primary-goal card data). */
export type HomeGoal = Schemas['HomeGoalModel'];

/** HomeResponse from web_api/schemas.py (M4 Home dashboard overview). */
export type HomeResponse = Schemas['HomeResponse'];

/** ResearchSummaryModel from web_api/schemas.py (research counters). */
export type ResearchSummary = Schemas['ResearchSummaryModel'];

/** ResearchSourceItemModel from web_api/schemas.py (source list row). */
export type ResearchSourceItem = Schemas['ResearchSourceItemModel'];

/** ResearchResponse from web_api/schemas.py (M4 Research overview). */
export type ResearchResponse = Schemas['ResearchResponse'];

// --- Phase 2 unified /projects ------------------------------------------------

/** ProjectsBoardTaskModel from web_api/schemas.py (flattened lane task). */
export type ProjectsBoardTask = Schemas['ProjectsBoardTaskModel'];

/** ProjectsBoardMilestoneModel from web_api/schemas.py (with progress). */
export type ProjectsBoardMilestone = Schemas['ProjectsBoardMilestoneModel'];

/** ProjectsBoardProjectModel from web_api/schemas.py (one swimlane). */
export type ProjectsBoardProject = Schemas['ProjectsBoardProjectModel'];

/** ProjectsBoardGoalModel from web_api/schemas.py (goal grouping row). */
export type ProjectsBoardGoal = Schemas['ProjectsBoardGoalModel'];

/** ProjectsBoardHabitDayModel from web_api/schemas.py (one week dot). */
export type ProjectsBoardHabitDay = Schemas['ProjectsBoardHabitDayModel'];

/** ProjectsBoardHabitModel from web_api/schemas.py (habit check-in strip). */
export type ProjectsBoardHabit = Schemas['ProjectsBoardHabitModel'];

/** ProjectsBoardResponse from web_api/schemas.py (unified /projects payload). */
export type ProjectsBoardResponse = Schemas['ProjectsBoardResponse'];

/** StarmapResponse from web_api/schemas.py (one-shot home starmap snapshot). */
export type StarmapResponse = Schemas['StarmapResponse'];

/** DivinationRequest / DivinationResponse from web_api/schemas.py (占卜 §5). */
export type DivinationRequest = Schemas['DivinationRequest'];
export type DivinationResponse = Schemas['DivinationResponse'];

/** KanbanCardScheduleRequest from web_api/schemas.py (planned dates).
 * Partial: `undefined` keeps the value, `""` clears it. */
export type KanbanCardScheduleRequest = Partial<Schemas['KanbanCardScheduleRequest']>;

/** KanbanCardPatchRequest from web_api/schemas.py (field edit incl. lane). */
export type KanbanCardPatchRequest = Schemas['KanbanCardPatchRequest'];

/** CheckinCreateRequest from web_api/schemas.py (all fields server-defaulted). */
export type CheckinCreateRequest = Partial<Schemas['CheckinCreateRequest']>;

/** CheckinMutationResponse from web_api/schemas.py. */
export type CheckinMutationResponse = Schemas['CheckinMutationResponse'];

/** CheckinDeleteResponse from web_api/schemas.py ({ok, checkin_id}). */
export type CheckinDeleteResponse = Schemas['CheckinDeleteResponse'];

/** PlanTemplateModel from web_api/schemas.py (built-in or inline plan). */
export type PlanTemplate = Schemas['PlanTemplateModel'];

/** PlanTemplateUsageModel from web_api/schemas.py (history row). */
export type PlanTemplateUsage = Schemas['PlanTemplateUsageModel'];

/** PlanTemplateListResponse from web_api/schemas.py. */
export type PlanTemplateListResponse = Schemas['PlanTemplateListResponse'];

/** PlanTemplateInstantiateRequest from web_api/schemas.py
 * (template_id OR inline template; title/start/habit_id overrides). */
export type PlanTemplateInstantiateRequest = Partial<Schemas['PlanTemplateInstantiateRequest']>;

/** PlanTemplateInstantiateResponse from web_api/schemas.py. */
export type PlanTemplateInstantiateResponse = Schemas['PlanTemplateInstantiateResponse'];

/** ProjectCaseDeleteRequest from web_api/schemas.py (type-the-name confirm). */
export type ProjectCaseDeleteRequest = Schemas['ProjectCaseDeleteRequest'];

/** ProjectCaseDeleteResponse from web_api/schemas.py ({ok, deleted_id, …}). */
export type ProjectCaseDeleteResponse = Schemas['ProjectCaseDeleteResponse'];

/** ProjectsBoardHabitRecentDayModel — one trailing-90-day heatmap cell. */
export type ProjectsBoardHabitRecentDay = Schemas['ProjectsBoardHabitRecentDayModel'];

// ---------------------------------------------------------------------------
// Frontend-only composite types (not part of the OpenAPI contract).

/** Detail GET result: the item plus its activity-file ETag (W/"<sha256>"). */
export interface ActivityItemDetail {
  item: ActivityItem;
  etag: string;
}

/** Board GET result: the payload plus the kanban.md ETag (W/"<sha256>"). */
export interface KanbanBoardResult {
  board: KanbanBoard;
  etag: string;
}

/** List GET result: the payload plus the inbox-file ETag (W/"<sha256>"). */
export interface InboxListResult {
  data: InboxResponse;
  etag: string;
}

/** Review GET result: the payload plus the evidence-pool ETag (W/"<sha256>"). */
export interface EvidenceReviewListResult {
  data: EvidenceReviewListResponse;
  etag: string;
}

/** Review GET result: the payload plus the review-source ETag (W/"<sha256>"). */
export interface WeeklyReviewResult {
  data: ReviewResponse;
  etag: string;
}

/** Board GET result: the payload plus the board-source ETag (W/"<sha256>"). */
export interface ProjectBoardResult {
  data: ProjectBoard;
  etag: string;
}

/** Studio GET result: the payload plus the public-layer ETag (W/"<sha256>"). */
export interface StudioResult {
  data: StudioResponse;
  etag: string;
}

/** Blog detail GET result: the post plus its per-post ETag (W/"<sha256>"). */
export interface StudioPostResult {
  post: StudioPostDetail;
  etag: string;
}

/** Public-build GET result: the payload plus the public-layer ETag. */
export interface PublicBuildResult {
  data: PublicBuildResponse;
  etag: string;
}

/** Projects-board GET result: the payload plus the 6-file board ETag. */
export interface ProjectsBoardResult {
  board: ProjectsBoardResponse;
  etag: string;
}

/** Plan-templates GET result: the payload plus the plan-source ETag. */
export interface PlanTemplateListResult {
  data: PlanTemplateListResponse;
  etag: string;
}

/** Clarify actions accepted by POST .../inbox/{id}/clarify (CLARIFY_ACTIONS). */
export type InboxClarifyAction =
  | 'to_kanban_queue'
  | 'to_learning_resource'
  | 'to_activity_habit'
  | 'to_evidence_draft'
  | 'discard'
  | 'archive';
