// TanStack Query hooks over the API client.

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { QueryClient } from '@tanstack/react-query';

import { ApiError, apiGet, apiGetWithHeaders, apiPost, apiPostWithHeaders, ifMatch } from './client';
import type {
  ActivityApplyResponse,
  ActivityDismissResponse,
  ActivityItem,
  ActivityItemDetail,
  ActivityListResponse,
  AssistantStatus,
  CurrentUser,
  EvidenceEntryDetail,
  EvidenceEditRequest,
  EvidenceEntryActionRequest,
  EvidenceListResponse,
  EvidenceReviewBulkRequest,
  EvidenceReviewDeprecateRequest,
  EvidenceReviewListResponse,
  EvidenceReviewListResult,
  EvidenceReviewMutationResponse,
  EvidenceSkillLinksResponse,
  EvidenceSkillSuggestionsResponse,
  EvidenceStagesResponse,
  CrystallizeApplyRequest,
  CrystallizeApplyResponse,
  CrystallizeCandidatesResponse,
  CrystallizeDraftRequest,
  CrystallizeDraftResponse,
  GapAnalysisResult,
  GapAnalyzeRequest,
  GapIntakeRequest,
  GoalsResponse,
  HealthReport,
  HomeResponse,
  InboxCaptureRequest,
  InboxClarifyAction,
  InboxListResult,
  InboxMutationResponse,
  InboxResponse,
  JobCreateRequest,
  JobCreateResponse,
  KanbanBoard,
  KanbanBoardResult,
  KanbanCardCreateRequest,
  KanbanMutationResponse,
  OkResponse,
  ProfileSummary,
  ProjectBoard,
  ProjectBoardResult,
  ProjectCaseCreateRequest,
  ProjectCaseMutationResponse,
  ProjectCaseUpdateRequest,
  ProjectMilestoneAddRequest,
  ProjectMilestoneUpdateRequest,
  ProjectTaskCreateRequest,
  PublicBuildPreviewResponse,
  PublicBuildPublishRequest,
  PublicBuildRequest,
  PublicBuildResponse,
  PublicBuildResult,
  PublicBuildResultResponse,
  ResearchResponse,
  ReviewApplyRequest,
  ReviewApplyResponse,
  ReviewResponse,
  ReviewSaveRequest,
  ReviewSaveResponse,
  SkillTreeResponse,
  StudioCandidateRequest,
  StudioCandidateResponse,
  StudioDraftResponse,
  StudioInitResponse,
  StudioPostCreateRequest,
  StudioPostDetail,
  StudioPostMutationResponse,
  StudioPostResult,
  StudioPostSaveRequest,
  StudioResponse,
  StudioResult,
  StudioValidationResponse,
  WeeklyReviewResult,
} from './types';

export function useMe() {
  return useQuery({
    queryKey: ['auth', 'me'],
    queryFn: () => apiGet<CurrentUser>('/auth/me'),
    retry: false,
    staleTime: 60_000,
  });
}

export function useLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (credentials: { username: string; password: string }) =>
      apiPost<CurrentUser>('/auth/login', credentials),
    onSuccess: (user) => {
      queryClient.setQueryData(['auth', 'me'], user);
    },
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiPost<OkResponse>('/auth/logout'),
    onSettled: () => {
      queryClient.clear();
    },
  });
}

export function useProfiles() {
  return useQuery({
    queryKey: ['profiles'],
    queryFn: () => apiGet<ProfileSummary[]>('/profiles'),
  });
}

/** Cross-profile assistant (OpenClaw) status; server caches 60s as well. */
export function useAssistantStatus() {
  return useQuery({
    queryKey: ['system', 'assistant'],
    queryFn: () => apiGet<AssistantStatus>('/system/assistant'),
    staleTime: 60_000,
  });
}

export function useHealthReport(profile: string) {
  return useQuery({
    queryKey: ['profiles', profile, 'health'],
    queryFn: () => apiGet<HealthReport>(`/profiles/${encodeURIComponent(profile)}/health`),
    enabled: profile.length > 0,
  });
}

export function useSkillTree(profile: string) {
  return useQuery({
    queryKey: ['profiles', profile, 'skill-tree'],
    queryFn: () =>
      apiGet<SkillTreeResponse>(`/profiles/${encodeURIComponent(profile)}/skill-tree`),
    enabled: profile.length > 0,
  });
}

export interface FlatSkillNode {
  id: string;
  title: string;
  status: string;
}

export interface SkillTreeFlatResult {
  nodes: FlatSkillNode[];
  /** skill-tree.yaml ETag for If-Match on the skill-links mutation. */
  etag: string;
}

/** Skill tree as a flat node list plus the tree-file ETag. */
export function useSkillTreeFlat(profile: string) {
  return useQuery({
    queryKey: ['profiles', profile, 'skill-tree', 'flat'],
    queryFn: async (): Promise<SkillTreeFlatResult> => {
      const { data, headers } = await apiGetWithHeaders<SkillTreeResponse>(
        `/profiles/${encodeURIComponent(profile)}/skill-tree`,
      );
      const flat: FlatSkillNode[] = [];
      const walk = (nodes: SkillTreeResponse['nodes'] | undefined) => {
        for (const node of nodes ?? []) {
          flat.push({ id: node.id, title: node.title, status: node.status });
          walk(node.children ?? []);
        }
      };
      walk(data.nodes ?? []);
      return { nodes: flat, etag: headers.get('ETag') ?? '' };
    },
    enabled: profile.length > 0,
  });
}

function kanbanBase(profile: string): string {
  return `/profiles/${encodeURIComponent(profile)}/kanban`;
}

/** Board fetch that captures the response ETag for If-Match mutations. */
export function useKanbanBoard(profile: string) {
  return useQuery({
    queryKey: ['profiles', profile, 'kanban'],
    queryFn: async (): Promise<KanbanBoardResult> => {
      const { data, headers } = await apiGetWithHeaders<KanbanBoard>(kanbanBase(profile));
      return { board: data, etag: headers.get('ETag') ?? '' };
    },
    enabled: profile.length > 0,
  });
}

function useInvalidateKanban(profile: string) {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'kanban'] });
}

export function useAddKanbanCard(profile: string) {
  const invalidate = useInvalidateKanban(profile);
  return useMutation({
    mutationFn: ({ body, etag }: { body: KanbanCardCreateRequest; etag: string }) =>
      apiPost<KanbanMutationResponse>(`${kanbanBase(profile)}/cards`, body, {
        headers: ifMatch(etag),
      }),
    onSuccess: invalidate,
  });
}

export function useMoveKanbanCard(profile: string) {
  const invalidate = useInvalidateKanban(profile);
  return useMutation({
    mutationFn: ({
      cardRef,
      targetSection,
      toIndex,
      etag,
    }: {
      cardRef: string;
      targetSection: string;
      /** 0-based post-removal index in the target column; omitted = tail. */
      toIndex?: number;
      etag: string;
    }) =>
      apiPost<KanbanMutationResponse>(
        `${kanbanBase(profile)}/cards/${encodeURIComponent(cardRef)}/move`,
        { target_section: targetSection, ...(toIndex === undefined ? {} : { to_index: toIndex }) },
        { headers: ifMatch(etag) },
      ),
    onSuccess: invalidate,
  });
}

export function useDoneKanbanCard(profile: string) {
  const invalidate = useInvalidateKanban(profile);
  return useMutation({
    mutationFn: ({ cardRef, etag }: { cardRef: string; etag: string }) =>
      apiPost<KanbanMutationResponse>(
        `${kanbanBase(profile)}/cards/${encodeURIComponent(cardRef)}/done`,
        undefined,
        { headers: ifMatch(etag) },
      ),
    onSuccess: invalidate,
  });
}

export interface ActivityFilters {
  status: string;
  kind: string;
}

function activityBase(profile: string): string {
  return `/profiles/${encodeURIComponent(profile)}/activity`;
}

export function useActivityList(profile: string, filters: ActivityFilters) {
  return useQuery({
    queryKey: ['profiles', profile, 'activity', filters],
    queryFn: () => {
      const params = new URLSearchParams({ status: filters.status, limit: '200' });
      if (filters.kind) {
        params.set('kind', filters.kind);
      }
      return apiGet<ActivityListResponse>(`${activityBase(profile)}?${params.toString()}`);
    },
    enabled: profile.length > 0,
  });
}

/** Detail fetch that captures the response ETag for If-Match mutations. */
export function useActivityItem(profile: string, itemId: string) {
  return useQuery({
    queryKey: ['profiles', profile, 'activity', 'item', itemId],
    queryFn: async (): Promise<ActivityItemDetail> => {
      const { data, headers } = await apiGetWithHeaders<ActivityItem>(
        `${activityBase(profile)}/${encodeURIComponent(itemId)}`,
      );
      return { item: data, etag: headers.get('ETag') ?? '' };
    },
    enabled: profile.length > 0 && itemId.length > 0,
  });
}

function useInvalidateActivity(profile: string) {
  const queryClient = useQueryClient();
  return () =>
    queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'activity'] });
}

export function useApplyActivity(profile: string) {
  const invalidate = useInvalidateActivity(profile);
  return useMutation({
    mutationFn: ({ itemId, etag }: { itemId: string; etag: string }) =>
      apiPost<ActivityApplyResponse>(
        `${activityBase(profile)}/${encodeURIComponent(itemId)}/apply`,
        undefined,
        { headers: ifMatch(etag) },
      ),
    onSuccess: invalidate,
  });
}

export function useDismissActivity(profile: string) {
  const invalidate = useInvalidateActivity(profile);
  return useMutation({
    mutationFn: ({ itemId, etag, note }: { itemId: string; etag: string; note: string }) =>
      apiPost<ActivityDismissResponse>(
        `${activityBase(profile)}/${encodeURIComponent(itemId)}/dismiss`,
        { note },
        { headers: ifMatch(etag) },
      ),
    onSuccess: invalidate,
  });
}

function inboxBase(profile: string): string {
  return `/profiles/${encodeURIComponent(profile)}/inbox`;
}

/** Inbox list fetch that captures the response ETag for If-Match mutations. */
export function useInboxList(profile: string, status: string) {
  return useQuery({
    queryKey: ['profiles', profile, 'inbox', status],
    queryFn: async (): Promise<InboxListResult> => {
      const params = new URLSearchParams({ status });
      const { data, headers } = await apiGetWithHeaders<InboxResponse>(
        `${inboxBase(profile)}?${params.toString()}`,
      );
      return { data, etag: headers.get('ETag') ?? '' };
    },
    enabled: profile.length > 0,
  });
}

function useInvalidateInbox(profile: string) {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'inbox'] });
}

export function useCaptureInbox(profile: string) {
  const invalidate = useInvalidateInbox(profile);
  return useMutation({
    mutationFn: ({ body, etag }: { body: InboxCaptureRequest; etag: string }) =>
      apiPost<InboxMutationResponse>(inboxBase(profile), body, {
        headers: ifMatch(etag),
      }),
    onSuccess: invalidate,
  });
}

export function useClarifyInbox(profile: string) {
  const invalidate = useInvalidateInbox(profile);
  return useMutation({
    mutationFn: ({
      itemId,
      action,
      note,
      etag,
    }: {
      itemId: string;
      action: InboxClarifyAction;
      note: string;
      etag: string;
    }) =>
      apiPost<InboxMutationResponse>(
        `${inboxBase(profile)}/${encodeURIComponent(itemId)}/clarify`,
        { action, note },
        { headers: ifMatch(etag) },
      ),
    onSuccess: invalidate,
  });
}

export function useArchiveInboxItem(profile: string) {
  const invalidate = useInvalidateInbox(profile);
  return useMutation({
    mutationFn: ({ itemId, note, etag }: { itemId: string; note: string; etag: string }) =>
      apiPost<InboxMutationResponse>(
        `${inboxBase(profile)}/${encodeURIComponent(itemId)}/archive`,
        { note },
        { headers: ifMatch(etag) },
      ),
    onSuccess: invalidate,
  });
}

export function useDiscardInboxItem(profile: string) {
  const invalidate = useInvalidateInbox(profile);
  return useMutation({
    mutationFn: ({ itemId, note, etag }: { itemId: string; note: string; etag: string }) =>
      apiPost<InboxMutationResponse>(
        `${inboxBase(profile)}/${encodeURIComponent(itemId)}/discard`,
        { note },
        { headers: ifMatch(etag) },
      ),
    onSuccess: invalidate,
  });
}

export function useGoals(profile: string) {
  return useQuery({
    queryKey: ['profiles', profile, 'goals'],
    queryFn: () => apiGet<GoalsResponse>(`/profiles/${encodeURIComponent(profile)}/goals`),
    enabled: profile.length > 0,
  });
}

export interface EvidenceFilters {
  /** '' = all non-deprecated; 'all' includes deprecated; else review_status. */
  status: string;
  q: string;
  limit: number;
}

function evidenceBase(profile: string): string {
  return `/profiles/${encodeURIComponent(profile)}/evidence`;
}

export function useEvidenceList(profile: string, filters: EvidenceFilters) {
  return useQuery({
    queryKey: ['profiles', profile, 'evidence', filters],
    queryFn: () => {
      const params = new URLSearchParams({ limit: String(filters.limit) });
      if (filters.status) {
        params.set('status', filters.status);
      }
      if (filters.q.trim()) {
        params.set('q', filters.q.trim());
      }
      return apiGet<EvidenceListResponse>(`${evidenceBase(profile)}?${params.toString()}`);
    },
    enabled: profile.length > 0,
  });
}

export function useEvidenceEntry(profile: string, entryId: string) {
  return useQuery({
    queryKey: ['profiles', profile, 'evidence', 'entry', entryId],
    queryFn: () =>
      apiGet<EvidenceEntryDetail>(`${evidenceBase(profile)}/${encodeURIComponent(entryId)}`),
    enabled: profile.length > 0 && entryId.length > 0,
  });
}

export interface EvidenceReviewFilters {
  /** 'needs_review' (default) | 'reviewed' | 'deprecated' | 'all'. */
  status: string;
  q: string;
}

function evidenceReviewBase(profile: string): string {
  return `/profiles/${encodeURIComponent(profile)}/evidence-review`;
}

/** Review queue fetch that captures the pool ETag for If-Match mutations. */
export function useEvidenceReviewList(profile: string, filters: EvidenceReviewFilters) {
  return useQuery({
    queryKey: ['profiles', profile, 'evidence-review', filters],
    queryFn: async (): Promise<EvidenceReviewListResult> => {
      const params = new URLSearchParams({ status: filters.status, limit: '500' });
      if (filters.q.trim()) {
        params.set('q', filters.q.trim());
      }
      const { data, headers } = await apiGetWithHeaders<EvidenceReviewListResponse>(
        `${evidenceReviewBase(profile)}?${params.toString()}`,
      );
      return { data, etag: headers.get('ETag') ?? '' };
    },
    enabled: profile.length > 0,
  });
}

function useInvalidateEvidenceReview(profile: string) {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'evidence-review'] });
    queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'evidence'] });
    queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'evidence-stages'] });
  };
}

/**
 * ETag mutation helper: POST with If-Match; on 412 (someone else — or our
 * own previous mutation whose fresh ETag had not landed yet — changed the
 * file) refetch the current ETag and retry exactly once. The fresh ETag
 * from the success response is returned so callers can write it back into
 * the query cache, keeping consecutive mutations reload-free.
 */
async function postEtagMutation<T>(
  path: string,
  body: unknown,
  etag: string,
  refreshEtag: () => Promise<string>,
): Promise<{ data: T; etag: string }> {
  try {
    const res = await apiPostWithHeaders<T>(path, body, { headers: ifMatch(etag) });
    return { data: res.data, etag: res.headers.get('ETag') ?? etag };
  } catch (error) {
    if (!(error instanceof ApiError) || error.status !== 412) {
      throw error;
    }
    const fresh = await refreshEtag();
    const res = await apiPostWithHeaders<T>(path, body, { headers: ifMatch(fresh) });
    return { data: res.data, etag: res.headers.get('ETag') ?? fresh };
  }
}

/** Refresh the evidence-pool ETag straight from the server (post-412). */
async function refreshPoolEtag(profile: string): Promise<string> {
  const { headers } = await apiGetWithHeaders<EvidenceReviewListResponse>(
    `${evidenceReviewBase(profile)}?status=all&limit=1`,
  );
  return headers.get('ETag') ?? '';
}

/** Refresh the skill-tree ETag straight from the server (post-412). */
async function refreshTreeEtag(profile: string): Promise<string> {
  const { headers } = await apiGetWithHeaders<SkillTreeResponse>(
    `/profiles/${encodeURIComponent(profile)}/skill-tree`,
  );
  return headers.get('ETag') ?? '';
}

/** Write the post-mutation pool ETag into every cached review-list variant. */
function writePoolEtag(queryClient: QueryClient, profile: string, etag: string) {
  if (!etag) return;
  queryClient.setQueriesData(
    { queryKey: ['profiles', profile, 'evidence-review'] },
    (old: EvidenceReviewListResult | undefined) => (old ? { ...old, etag } : old),
  );
}

/** Write the post-mutation tree ETag into the cached flat skill tree. */
function writeTreeEtag(queryClient: QueryClient, profile: string, etag: string) {
  if (!etag) return;
  queryClient.setQueryData(
    ['profiles', profile, 'skill-tree', 'flat'],
    (old: SkillTreeFlatResult | undefined) => (old ? { ...old, etag } : old),
  );
}

/** Bulk accept/tag: set one pool-editable field on the selected rows. */
export function useEvidenceReviewBulk(profile: string) {
  const invalidate = useInvalidateEvidenceReview(profile);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ body, etag }: { body: EvidenceReviewBulkRequest; etag: string }) =>
      postEtagMutation<EvidenceReviewMutationResponse>(
        `${evidenceReviewBase(profile)}/bulk`,
        body,
        etag,
        () => refreshPoolEtag(profile),
      ),
    onSuccess: ({ etag }) => {
      writePoolEtag(queryClient, profile, etag);
      invalidate();
    },
  });
}

/** Reject (deprecate) or restore the selected rows. */
export function useEvidenceReviewDeprecate(profile: string) {
  const invalidate = useInvalidateEvidenceReview(profile);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ body, etag }: { body: EvidenceReviewDeprecateRequest; etag: string }) =>
      postEtagMutation<EvidenceReviewMutationResponse>(
        `${evidenceReviewBase(profile)}/deprecate`,
        body,
        etag,
        () => refreshPoolEtag(profile),
      ),
    onSuccess: ({ etag }) => {
      writePoolEtag(queryClient, profile, etag);
      invalidate();
    },
  });
}

// --- Phase 1 single Evidence page -------------------------------------------

/** Five-stage pipeline counters (待结晶/待评审/已入座/待补强/已废弃). */
export function useEvidenceStages(profile: string) {
  return useQuery({
    queryKey: ['profiles', profile, 'evidence-stages'],
    queryFn: () =>
      apiGet<EvidenceStagesResponse>(
        `/profiles/${encodeURIComponent(profile)}/evidence-stages`,
      ),
    enabled: profile.length > 0,
  });
}

/** Edit whitelist fields on one evidence entry (If-Match = pool ETag). */
export function useEditEvidenceEntry(profile: string) {
  const invalidate = useInvalidateEvidenceReview(profile);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      entryId,
      body,
      etag,
    }: {
      entryId: string;
      body: EvidenceEditRequest;
      etag: string;
    }) =>
      postEtagMutation<EvidenceReviewMutationResponse>(
        `${evidenceBase(profile)}/${encodeURIComponent(entryId)}/edit`,
        body,
        etag,
        () => refreshPoolEtag(profile),
      ),
    onSuccess: ({ etag }) => {
      writePoolEtag(queryClient, profile, etag);
      invalidate();
    },
  });
}

/** Single-entry review action: accept (with grades) / reject / restore. */
export function useReviewEvidenceEntry(profile: string) {
  const invalidate = useInvalidateEvidenceReview(profile);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      entryId,
      body,
      etag,
    }: {
      entryId: string;
      body: EvidenceEntryActionRequest;
      etag: string;
    }) =>
      postEtagMutation<EvidenceReviewMutationResponse>(
        `${evidenceBase(profile)}/${encodeURIComponent(entryId)}/review`,
        body,
        etag,
        () => refreshPoolEtag(profile),
      ),
    onSuccess: ({ etag }) => {
      writePoolEtag(queryClient, profile, etag);
      invalidate();
    },
  });
}

/** Reconcile the skill nodes citing one entry (chip-save semantics). */
export function useSetEvidenceSkillLinks(profile: string) {
  const invalidate = useInvalidateEvidenceReview(profile);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      entryId,
      skillIds,
      etag,
    }: {
      entryId: string;
      skillIds: string[];
      etag: string;
    }) =>
      postEtagMutation<EvidenceSkillLinksResponse>(
        `${evidenceBase(profile)}/${encodeURIComponent(entryId)}/skill-links`,
        { skill_ids: skillIds },
        etag,
        () => refreshTreeEtag(profile),
      ),
    onSuccess: ({ etag }) => {
      writeTreeEtag(queryClient, profile, etag);
      invalidate();
      queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'skill-tree'] });
    },
  });
}

/** Tiered skill-link suggestions (embedding -> llm -> rule) for one entry. */
export function useEvidenceSkillSuggestions(profile: string, entryId: string) {
  return useQuery({
    queryKey: ['profiles', profile, 'evidence', 'skill-suggestions', entryId],
    queryFn: () =>
      apiGet<EvidenceSkillSuggestionsResponse>(
        `${evidenceBase(profile)}/${encodeURIComponent(entryId)}/skill-suggestions`,
      ),
    enabled: profile.length > 0 && entryId.length > 0,
  });
}

/** Uncrystallized Done tasks with advisory blockers (wizard step 1). */
export function useCrystallizeCandidates(profile: string) {
  return useQuery({
    queryKey: ['profiles', profile, 'crystallize-candidates'],
    queryFn: () =>
      apiGet<CrystallizeCandidatesResponse>(
        `/profiles/${encodeURIComponent(profile)}/crystallize/candidates`,
      ),
    enabled: profile.length > 0,
  });
}

/**
 * Crystallize draft: rule mode answers 200 with the draft; `use_llm: true`
 * answers 202 with a job handle (subscribe via streamJob for the same
 * CrystallizeDraftResponse payload in the job result).
 */
export function useCrystallizeDraft(profile: string) {
  return useMutation({
    mutationFn: (body: CrystallizeDraftRequest) =>
      apiPost<CrystallizeDraftResponse | JobCreateResponse>(
        `/profiles/${encodeURIComponent(profile)}/crystallize/draft`,
        body,
      ),
  });
}

/** Apply a confirmed crystallize draft; marks the source tasks crystallized. */
export function useCrystallizeApply(profile: string) {
  const invalidate = useInvalidateEvidenceReview(profile);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CrystallizeApplyRequest) =>
      apiPost<CrystallizeApplyResponse>(
        `/profiles/${encodeURIComponent(profile)}/crystallize/apply`,
        body,
      ),
    onSuccess: () => {
      invalidate();
      queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'kanban'] });
      queryClient.invalidateQueries({
        queryKey: ['profiles', profile, 'crystallize-candidates'],
      });
      queryClient.invalidateQueries({
        queryKey: ['profiles', profile, 'evidence-stages'],
      });
    },
  });
}


function gapBase(profile: string): string {
  return `/profiles/${encodeURIComponent(profile)}/gap`;
}

/** Gap analysis runs as a plain mutation; the page renders mutation.data. */
export function useGapAnalyze(profile: string) {
  return useMutation({
    mutationFn: (body: GapAnalyzeRequest) =>
      apiPost<GapAnalysisResult>(`${gapBase(profile)}/analyze`, body),
  });
}

/**
 * Deep (LLM) gap analysis: the same endpoint with `use_llm: true` answers
 * 202 with a job handle; the page then subscribes to the job's SSE stream
 * (see api/jobs.ts) for progress phases and the final GapAnalysisResult.
 */
export function useGapDeepAnalyze(profile: string) {
  return useMutation({
    mutationFn: (body: GapAnalyzeRequest) =>
      apiPost<JobCreateResponse>(`${gapBase(profile)}/analyze`, body),
  });
}

/**
 * Generic async-job creation (LLM long tasks: `studio-jd-match`,
 * `project-suggest-refs`, ...). Answers 202 with a job handle; the page
 * then subscribes to the job's SSE stream (see api/jobs.ts) for progress
 * phases and the kind-specific result payload.
 */
export function useCreateJob(profile: string) {
  return useMutation({
    mutationFn: (body: JobCreateRequest) =>
      apiPost<JobCreateResponse>(`/profiles/${encodeURIComponent(profile)}/jobs`, body),
  });
}

export function useGapIntake(profile: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: GapIntakeRequest) =>
      apiPost<KanbanMutationResponse>(`${gapBase(profile)}/intake`, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'kanban'] });
    },
  });
}

function reviewBase(profile: string): string {
  return `/profiles/${encodeURIComponent(profile)}/review`;
}

/** Weekly review fetch that captures the review-source ETag for If-Match. */
export function useWeeklyReview(profile: string, window: { start: string; end: string }) {
  return useQuery({
    queryKey: ['profiles', profile, 'review', window],
    queryFn: async (): Promise<WeeklyReviewResult> => {
      const params = new URLSearchParams({ start: window.start, end: window.end });
      const { data, headers } = await apiGetWithHeaders<ReviewResponse>(
        `${reviewBase(profile)}?${params.toString()}`,
      );
      return { data, etag: headers.get('ETag') ?? '' };
    },
    enabled: profile.length > 0,
  });
}

function useInvalidateReview(profile: string) {
  const queryClient = useQueryClient();
  return (includeOwners: boolean) => {
    queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'activity'] });
    if (includeOwners) {
      queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'review'] });
      queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'kanban'] });
      queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'evidence'] });
      queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'evidence-review'] });
    }
  };
}

/** Save selected candidates as pending Agent Activity items. */
export function useReviewSaveCandidates(profile: string) {
  const invalidate = useInvalidateReview(profile);
  return useMutation({
    mutationFn: ({ body, etag }: { body: ReviewSaveRequest; etag: string }) =>
      apiPost<ReviewSaveResponse>(`${reviewBase(profile)}/save`, body, {
        headers: ifMatch(etag),
      }),
    onSuccess: () => invalidate(false),
  });
}

/** Apply selected candidates to their owner files (pool/kanban/blog). */
export function useReviewApplyCandidates(profile: string) {
  const invalidate = useInvalidateReview(profile);
  return useMutation({
    mutationFn: ({ body, etag }: { body: ReviewApplyRequest; etag: string }) =>
      apiPost<ReviewApplyResponse>(`${reviewBase(profile)}/apply`, body, {
        headers: ifMatch(etag),
      }),
    onSuccess: () => invalidate(true),
  });
}

function projectBoardBase(profile: string): string {
  return `/profiles/${encodeURIComponent(profile)}/project-board`;
}

/** Project board fetch that captures the board-source ETag for If-Match. */
export function useProjectBoard(profile: string) {
  return useQuery({
    queryKey: ['profiles', profile, 'project-board'],
    queryFn: async (): Promise<ProjectBoardResult> => {
      const { data, headers } = await apiGetWithHeaders<ProjectBoard>(projectBoardBase(profile));
      return { data, etag: headers.get('ETag') ?? '' };
    },
    enabled: profile.length > 0,
  });
}

function useInvalidateProjectBoard(profile: string) {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'project-board'] });
    // Case sync and task mutations also write kanban.md / evidence-pool.yaml.
    queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'kanban'] });
    queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'evidence'] });
    queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'evidence-review'] });
  };
}

export function useCreateProjectCase(profile: string) {
  const invalidate = useInvalidateProjectBoard(profile);
  return useMutation({
    mutationFn: ({ body, etag }: { body: ProjectCaseCreateRequest; etag: string }) =>
      apiPost<ProjectCaseMutationResponse>(`${projectBoardBase(profile)}/cases`, body, {
        headers: ifMatch(etag),
      }),
    onSuccess: invalidate,
  });
}

export function useSaveProjectCase(profile: string) {
  const invalidate = useInvalidateProjectBoard(profile);
  return useMutation({
    mutationFn: ({
      caseId,
      body,
      etag,
    }: {
      caseId: string;
      body: ProjectCaseUpdateRequest;
      etag: string;
    }) =>
      apiPost<ProjectCaseMutationResponse>(
        `${projectBoardBase(profile)}/cases/${encodeURIComponent(caseId)}/save`,
        body,
        { headers: ifMatch(etag) },
      ),
    onSuccess: invalidate,
  });
}

export function useArchiveProjectCase(profile: string) {
  const invalidate = useInvalidateProjectBoard(profile);
  return useMutation({
    mutationFn: ({ caseId, etag }: { caseId: string; etag: string }) =>
      apiPost<ProjectCaseMutationResponse>(
        `${projectBoardBase(profile)}/cases/${encodeURIComponent(caseId)}/archive`,
        undefined,
        { headers: ifMatch(etag) },
      ),
    onSuccess: invalidate,
  });
}

export function useAddProjectMilestone(profile: string) {
  const invalidate = useInvalidateProjectBoard(profile);
  return useMutation({
    mutationFn: ({
      caseId,
      body,
      etag,
    }: {
      caseId: string;
      body: ProjectMilestoneAddRequest;
      etag: string;
    }) =>
      apiPost<ProjectCaseMutationResponse>(
        `${projectBoardBase(profile)}/cases/${encodeURIComponent(caseId)}/milestones`,
        body,
        { headers: ifMatch(etag) },
      ),
    onSuccess: invalidate,
  });
}

export function useSaveProjectMilestone(profile: string) {
  const invalidate = useInvalidateProjectBoard(profile);
  return useMutation({
    mutationFn: ({
      caseId,
      milestoneId,
      body,
      etag,
    }: {
      caseId: string;
      milestoneId: string;
      body: ProjectMilestoneUpdateRequest;
      etag: string;
    }) =>
      apiPost<ProjectCaseMutationResponse>(
        `${projectBoardBase(profile)}/cases/${encodeURIComponent(caseId)}` +
          `/milestones/${encodeURIComponent(milestoneId)}/save`,
        body,
        { headers: ifMatch(etag) },
      ),
    onSuccess: invalidate,
  });
}

export function useDeleteProjectMilestone(profile: string) {
  const invalidate = useInvalidateProjectBoard(profile);
  return useMutation({
    mutationFn: ({
      caseId,
      milestoneId,
      etag,
    }: {
      caseId: string;
      milestoneId: string;
      etag: string;
    }) =>
      apiPost<ProjectCaseMutationResponse>(
        `${projectBoardBase(profile)}/cases/${encodeURIComponent(caseId)}` +
          `/milestones/${encodeURIComponent(milestoneId)}/delete`,
        undefined,
        { headers: ifMatch(etag) },
      ),
    onSuccess: invalidate,
  });
}

export function useAddProjectTask(profile: string) {
  const invalidate = useInvalidateProjectBoard(profile);
  return useMutation({
    mutationFn: ({
      caseId,
      body,
      etag,
    }: {
      caseId: string;
      body: ProjectTaskCreateRequest;
      etag: string;
    }) =>
      apiPost<KanbanMutationResponse>(
        `${projectBoardBase(profile)}/cases/${encodeURIComponent(caseId)}/tasks`,
        body,
        { headers: ifMatch(etag) },
      ),
    onSuccess: invalidate,
  });
}

export function useMoveProjectTask(profile: string) {
  const invalidate = useInvalidateProjectBoard(profile);
  return useMutation({
    mutationFn: ({
      taskId,
      targetSection,
      etag,
    }: {
      taskId: string;
      targetSection: string;
      etag: string;
    }) =>
      apiPost<KanbanMutationResponse>(
        `${projectBoardBase(profile)}/tasks/${encodeURIComponent(taskId)}/move`,
        { target_section: targetSection },
        { headers: ifMatch(etag) },
      ),
    onSuccess: invalidate,
  });
}

function studioBase(profile: string): string {
  return `/profiles/${encodeURIComponent(profile)}/studio`;
}

function studioPostPath(profile: string, slug: string): string {
  // Slugs may be categorized routes (category/leaf); keep the slashes.
  const encoded = slug.split('/').map(encodeURIComponent).join('/');
  return `${studioBase(profile)}/blog/${encoded}`;
}

/** Studio overview fetch that captures the public-layer ETag for If-Match. */
export function useStudio(profile: string) {
  return useQuery({
    queryKey: ['profiles', profile, 'studio'],
    queryFn: async (): Promise<StudioResult> => {
      const { data, headers } = await apiGetWithHeaders<StudioResponse>(studioBase(profile));
      return { data, etag: headers.get('ETag') ?? '' };
    },
    enabled: profile.length > 0,
  });
}

/** Blog detail fetch that captures the per-post ETag for If-Match. */
export function useStudioPost(profile: string, slug: string) {
  return useQuery({
    queryKey: ['profiles', profile, 'studio', 'post', slug],
    queryFn: async (): Promise<StudioPostResult> => {
      const { data, headers } = await apiGetWithHeaders<StudioPostDetail>(
        studioPostPath(profile, slug),
      );
      return { post: data, etag: headers.get('ETag') ?? '' };
    },
    enabled: profile.length > 0 && slug.length > 0,
  });
}

function useInvalidateStudio(profile: string) {
  const queryClient = useQueryClient();
  return () =>
    queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'studio'] });
}

/** Initialize the profile's public layer (idempotent). */
export function useInitStudio(profile: string) {
  const invalidate = useInvalidateStudio(profile);
  return useMutation({
    mutationFn: ({ etag }: { etag: string }) =>
      apiPost<StudioInitResponse>(`${studioBase(profile)}/init`, undefined, {
        headers: ifMatch(etag),
      }),
    onSuccess: invalidate,
  });
}

export function useCreateStudioPost(profile: string) {
  const invalidate = useInvalidateStudio(profile);
  return useMutation({
    mutationFn: ({ body, etag }: { body: StudioPostCreateRequest; etag: string }) =>
      apiPost<StudioPostMutationResponse>(`${studioBase(profile)}/blog`, body, {
        headers: ifMatch(etag),
      }),
    onSuccess: invalidate,
  });
}

export function useSaveStudioPost(profile: string) {
  const invalidate = useInvalidateStudio(profile);
  return useMutation({
    mutationFn: ({
      slug,
      body,
      etag,
    }: {
      slug: string;
      body: StudioPostSaveRequest;
      etag: string;
    }) =>
      apiPost<StudioPostMutationResponse>(
        `${studioPostPath(profile, slug)}/save`,
        body,
        { headers: ifMatch(etag) },
      ),
    onSuccess: invalidate,
  });
}

/** Publish-readiness check on the (optionally edited) post; read-only. */
export function useCheckStudioPost(profile: string) {
  return useMutation({
    mutationFn: ({ slug, body }: { slug: string; body: StudioPostSaveRequest }) =>
      apiPost<StudioValidationResponse>(`${studioPostPath(profile, slug)}/check`, body),
  });
}

export function usePublishStudioPost(profile: string) {
  const invalidate = useInvalidateStudio(profile);
  return useMutation({
    mutationFn: ({
      slug,
      body,
      etag,
    }: {
      slug: string;
      body: StudioPostSaveRequest;
      etag: string;
    }) =>
      apiPost<StudioPostMutationResponse>(
        `${studioPostPath(profile, slug)}/publish`,
        body,
        { headers: ifMatch(etag) },
      ),
    onSuccess: invalidate,
  });
}

/** Candidate preview (rule fallback when no LLM); nothing is persisted. */
export function usePreviewStudioCandidate(profile: string) {
  return useMutation({
    mutationFn: (body: StudioCandidateRequest) =>
      apiPost<StudioCandidateResponse>(`${studioBase(profile)}/candidates/preview`, body),
  });
}

/** Confirm a candidate into a persisted draft (blog or project update). */
export function useCreateStudioDraft(profile: string) {
  const invalidate = useInvalidateStudio(profile);
  return useMutation({
    mutationFn: ({ body, etag }: { body: StudioCandidateRequest; etag: string }) =>
      apiPost<StudioDraftResponse>(`${studioBase(profile)}/candidates/create`, body, {
        headers: ifMatch(etag),
      }),
    onSuccess: invalidate,
  });
}

function publicBuildBase(profile: string): string {
  return `/profiles/${encodeURIComponent(profile)}/public-build`;
}

/** Public-build overview fetch that captures the public-layer ETag. */
export function usePublicBuild(profile: string) {
  return useQuery({
    queryKey: ['profiles', profile, 'public-build'],
    queryFn: async (): Promise<PublicBuildResult> => {
      const { data, headers } = await apiGetWithHeaders<PublicBuildResponse>(
        publicBuildBase(profile),
      );
      return { data, etag: headers.get('ETag') ?? '' };
    },
    enabled: profile.length > 0,
  });
}

/** Preview page list for the in-memory site preview picker. */
export function usePublicBuildPreview(profile: string, includeDrafts: boolean) {
  return useQuery({
    queryKey: ['profiles', profile, 'public-build', 'preview', includeDrafts],
    queryFn: () => {
      const params = new URLSearchParams({ include_drafts: includeDrafts ? '1' : '0' });
      return apiGet<PublicBuildPreviewResponse>(`${publicBuildBase(profile)}/preview?${params}`);
    },
    enabled: profile.length > 0,
  });
}

function useInvalidatePublicBuild(profile: string) {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'public-build'] });
    // Publishing drafts also changes the studio blog list.
    queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'studio'] });
  };
}

/** Build the static site (synchronous; server-pinned output dir). */
export function useBuildPublicSite(profile: string) {
  const invalidate = useInvalidatePublicBuild(profile);
  return useMutation({
    mutationFn: ({ body, etag }: { body: PublicBuildRequest; etag: string }) =>
      apiPost<PublicBuildResultResponse>(`${publicBuildBase(profile)}/build`, body, {
        headers: ifMatch(etag),
      }),
    onSuccess: invalidate,
  });
}

/** Publish the selected drafts, then build the static site. */
export function usePublishAndBuildPublicSite(profile: string) {
  const invalidate = useInvalidatePublicBuild(profile);
  return useMutation({
    mutationFn: ({ body, etag }: { body: PublicBuildPublishRequest; etag: string }) =>
      apiPost<PublicBuildResultResponse>(
        `${publicBuildBase(profile)}/publish-and-build`,
        body,
        { headers: ifMatch(etag) },
      ),
    onSuccess: invalidate,
  });
}

/** Same-origin URL of one built artifact (anchor href / iframe src). */
export function publicBuildArtifactUrl(profile: string, path: string): string {
  const encoded = path.split('/').map(encodeURIComponent).join('/');
  // Same API_BASE as client.ts ('/api/v1'), which is not exported.
  return `/api/v1${publicBuildBase(profile)}/artifacts/${encoded}`;
}

/** Same-origin URL of one self-contained preview page (iframe src). */
export function publicBuildPreviewPageUrl(
  profile: string,
  path: string,
  includeDrafts: boolean,
): string {
  const params = new URLSearchParams({
    path,
    include_drafts: includeDrafts ? '1' : '0',
  });
  return `/api/v1${publicBuildBase(profile)}/preview/page?${params}`;
}

/** Home dashboard overview (M4): aggregated profile snapshot, read-only. */
export function useHome(profile: string) {
  return useQuery({
    queryKey: ['profiles', profile, 'home'],
    queryFn: () => apiGet<HomeResponse>(`/profiles/${encodeURIComponent(profile)}/home`),
    enabled: profile.length > 0,
  });
}

/** Research overview (M4): source-inbox summary plus sidecar entry points. */
export function useResearch(profile: string) {
  return useQuery({
    queryKey: ['profiles', profile, 'research'],
    queryFn: () =>
      apiGet<ResearchResponse>(`/profiles/${encodeURIComponent(profile)}/research`),
    enabled: profile.length > 0,
  });
}
