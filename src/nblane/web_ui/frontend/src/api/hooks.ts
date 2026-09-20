// TanStack Query hooks over the API client.

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiGet, apiGetWithHeaders, apiPost, ifMatch } from './client';
import type {
  ActivityApplyResponse,
  ActivityDismissResponse,
  ActivityItem,
  ActivityItemDetail,
  ActivityListResponse,
  AssistantStatus,
  CurrentUser,
  EvidenceEntryDetail,
  EvidenceListResponse,
  EvidenceReviewBulkRequest,
  EvidenceReviewDeprecateRequest,
  EvidenceReviewListResponse,
  EvidenceReviewListResult,
  EvidenceReviewMutationResponse,
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
  ProjectSuggestRefsResponse,
  ProjectTaskCreateRequest,
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
  StudioJdMatchRequest,
  StudioJdMatchResponse,
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
      etag,
    }: {
      cardRef: string;
      targetSection: string;
      etag: string;
    }) =>
      apiPost<KanbanMutationResponse>(
        `${kanbanBase(profile)}/cards/${encodeURIComponent(cardRef)}/move`,
        { target_section: targetSection },
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
  };
}

/** Bulk accept/tag: set one pool-editable field on the selected rows. */
export function useEvidenceReviewBulk(profile: string) {
  const invalidate = useInvalidateEvidenceReview(profile);
  return useMutation({
    mutationFn: ({ body, etag }: { body: EvidenceReviewBulkRequest; etag: string }) =>
      apiPost<EvidenceReviewMutationResponse>(`${evidenceReviewBase(profile)}/bulk`, body, {
        headers: ifMatch(etag),
      }),
    onSuccess: invalidate,
  });
}

/** Reject (deprecate) or restore the selected rows. */
export function useEvidenceReviewDeprecate(profile: string) {
  const invalidate = useInvalidateEvidenceReview(profile);
  return useMutation({
    mutationFn: ({ body, etag }: { body: EvidenceReviewDeprecateRequest; etag: string }) =>
      apiPost<EvidenceReviewMutationResponse>(
        `${evidenceReviewBase(profile)}/deprecate`,
        body,
        { headers: ifMatch(etag) },
      ),
    onSuccess: invalidate,
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

/** AI suggest-refs (confirm-not-fill): nothing is persisted server-side. */
export function useSuggestProjectRefs(profile: string) {
  return useMutation({
    mutationFn: ({ caseId }: { caseId: string }) =>
      apiPost<ProjectSuggestRefsResponse>(
        `${projectBoardBase(profile)}/cases/${encodeURIComponent(caseId)}/suggest-refs`,
        undefined,
      ),
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

/** JD match analysis (LLM-backed; 422 degradation when unconfigured). */
export function useJdMatch(profile: string) {
  return useMutation({
    mutationFn: (body: StudioJdMatchRequest) =>
      apiPost<StudioJdMatchResponse>(`${studioBase(profile)}/jd-match`, body),
  });
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
