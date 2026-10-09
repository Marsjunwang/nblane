// TanStack Query hooks over the API client.

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { QueryClient } from '@tanstack/react-query';

import { ApiError, apiBase, apiDelete, apiDeleteWithHeaders, apiGet, apiGetWithHeaders, apiPatch, apiPatchWithHeaders, apiPost, apiPostWithHeaders, apiPostForm, apiPut, apiPutWithHeaders, ifMatch } from './client';
import type {
  AccountCreate,
  AccountInfo,
  AccountPatch,
  AccountsOk,
  SchemaInfo,
  ChangePasswordRequest,
  TokenCreateResult,
  AIExceptionBulkDismissResponse,
  AIExceptionsResponse,
  AssistantStatus,
  CheckinCreateRequest,
  CheckinDeleteResponse,
  CheckinMutationResponse,
  ChronicleResponse,
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
  GoalCreateRequest,
  GoalMutationResponse,
  GoalPatchRequest,
  GoalsResponse,
  HabitArchiveRequest,
  HabitArchiveResponse,
  HabitDeleteRequest,
  HabitDeleteResponse,
  HabitPlan,
  HabitPlanCreateRequest,
  HabitPlanDeleteRequest,
  HabitPlanDeleteResponse,
  HabitPlanListResponse,
  HabitPlanMutationResponse,
  HabitPlanPatchRequest,
  HomeResponse,
  JobCreateRequest,
  JobCreateResponse,
  KanbanBoard,
  KanbanBoardResult,
  KanbanCardCreateRequest,
  KanbanCardDeleteRequest,
  KanbanCardDeleteResponse,
  KanbanCardPatchRequest,
  KanbanCardScheduleRequest,
  KanbanMutationResponse,
  NorthStarMutationResponse,
  NorthStarPatchRequest,
  OkResponse,
  PlanTemplateInstantiateRequest,
  PlanTemplateInstantiateResponse,
  PlanTemplateListResponse,
  PlanTemplateListResult,
  ProfileSummary,
  ProjectBoard,
  ProjectBoardResult,
  ProjectCaseCreateRequest,
  ProjectCaseDeleteRequest,
  ProjectCaseDeleteResponse,
  ProjectCaseMutationResponse,
  ProjectCaseUpdateRequest,
  ProjectMilestoneAddRequest,
  ProjectMilestoneUpdateRequest,
  ProjectTaskCreateRequest,
  ProjectsBoardHabit,
  ProjectsBoardResponse,
  ProjectsBoardResult,
  PublicBuildPreviewResponse,
  PublicSiteDeployResponse,
  PublicSiteMediaResponse,
  PublicSiteResponse,
  PublicSiteSettingsUpdate,
  PublicSiteWork,
  ResearchResponse,
  ResearchReaderResponse,
  SkillNodePatchRequest,
  SkillNodePatchResponse,
  SkillTreeResponse,
  StudioInitResponse,
  StudioPostCreateRequest,
  StudioPostDetail,
  StudioPostMutationResponse,
  StudioPostResult,
  StudioPostSaveRequest,
  StudioValidationResponse,
  ContentAIStatus,
  ContentMedia,
  ContentMediaUploadResponse,
  ContentWorkspaceResponse,
  CareerWorkspaceResponse,
  CareerDraft,
  CareerImportPreview,
  CareerPhotoResponse,
  CareerPreviewResponse,
  ResumeDoc,
  WorkshopStatus,
  WorkshopLogs,
  WorkshopServiceStatus,
  WorkshopSettingsPatch,
  CodexSettings,
  CodexSettingsPatch,
  CodexStatus,
  LlmConnection,
  LlmConnectionUpdate,
  LlmConnectionVerify,
  GrobidLogs,
  GrobidStatus,
  BackupKey,
  BackupRemoteTest,
  BackupRun,
  BackupStatus,
  OpenClawSetupStatus,
  AgentTokenStatus,
  LocalModels,
  LocalModelTestResult,
  ProfileSettings,
  ProfileSettingsPatch,
  AgentJournal,
  AgentJournalUndo,
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

/** Change your own password; the server reissues this session's cookie. */
export function useChangePassword() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: ChangePasswordRequest) =>
      apiPost<CurrentUser>('/auth/password', body),
    onSuccess: (user) => {
      queryClient.setQueryData(['auth', 'me'], user);
    },
  });
}

/** Sign out every session of this account (including this one). */
export function useLogoutAll() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiPost<AccountsOk>('/auth/logout-all'),
    onSuccess: () => {
      queryClient.clear();
    },
  });
}

const ACCOUNTS_KEY = ['accounts'] as const;

/** Admin-only account list (Settings → 账号管理). */
export function useAccounts(enabled = true) {
  return useQuery({
    queryKey: ACCOUNTS_KEY,
    queryFn: () => apiGet<AccountInfo[]>('/accounts'),
    enabled,
  });
}

function useAccountMutation<TVars, TResult>(fn: (vars: TVars) => Promise<TResult>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: fn,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ACCOUNTS_KEY });
      // Creating a user may also create a profile.
      void queryClient.invalidateQueries({ queryKey: ['profiles'] });
    },
  });
}

const accountPath = (id: string) => `/accounts/${encodeURIComponent(id)}`;

export function useCreateAccount() {
  return useAccountMutation((body: AccountCreate) => apiPost<AccountInfo>('/accounts', body));
}

export function useUpdateAccount() {
  return useAccountMutation(({ id, patch }: { id: string; patch: AccountPatch }) =>
    apiPatch<AccountInfo>(accountPath(id), patch));
}

export function useResetAccountPassword() {
  return useAccountMutation(({ id, password }: { id: string; password: string }) =>
    apiPost<AccountInfo>(`${accountPath(id)}/reset-password`, { password }));
}

/** The plaintext token is only in this response; never cached. */
export function useCreateAccountToken() {
  return useAccountMutation(({ id, name }: { id: string; name: string }) =>
    apiPost<TokenCreateResult>(`${accountPath(id)}/tokens`, { name }));
}

export function useRevokeAccountToken() {
  return useAccountMutation(({ id, tokenId }: { id: string; tokenId: string }) =>
    apiDelete<AccountsOk>(`${accountPath(id)}/tokens/${encodeURIComponent(tokenId)}`));
}

/** Available domain schemas (data dir ∪ built-in) for profile creation. */
export function useSchemas(enabled = true) {
  return useQuery({
    queryKey: ['schemas'],
    queryFn: () => apiGet<SchemaInfo[]>('/schemas'),
    enabled,
    staleTime: 60_000,
  });
}

export function useProfiles() {
  return useQuery({
    queryKey: ['profiles'],
    queryFn: () => apiGet<ProfileSummary[]>('/profiles'),
  });
}

/** Deployment-wide LLM connection (the API key is never returned). */
export function useSettingsConnection(enabled = true) {
  return useQuery({
    queryKey: ['settings', 'connection'],
    queryFn: () => apiGet<LlmConnection>('/settings/connection'),
    enabled,
  });
}

export function useUpdateSettingsConnection() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: LlmConnectionUpdate) =>
      apiPut<LlmConnection>('/settings/connection', body),
    onSuccess: (value) => {
      queryClient.setQueryData(['settings', 'connection'], value);
    },
  });
}

const LOCAL_MODELS_KEY = ['settings', 'local-models'] as const;

/** Admin-only local model catalog; polls while an install is running. */
export function useLocalModels(enabled = true) {
  return useQuery({
    queryKey: LOCAL_MODELS_KEY,
    queryFn: () => apiGet<LocalModels>('/settings/local-models'),
    enabled,
    refetchInterval: (query) =>
      query.state.data?.models.some((model) => model.install.status === 'running') ? 1500 : false,
  });
}

function useLocalModelMutation<TVars>(request: (vars: TVars) => Promise<LocalModels>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: request,
    onSuccess: (value) => queryClient.setQueryData(LOCAL_MODELS_KEY, value),
  });
}

export function useInstallLocalModel() {
  return useLocalModelMutation((id: string) =>
    apiPost<LocalModels>(`/settings/local-models/${encodeURIComponent(id)}/install`, {}),
  );
}

export function useCancelLocalModelInstall() {
  return useLocalModelMutation((id: string) =>
    apiPost<LocalModels>(`/settings/local-models/${encodeURIComponent(id)}/cancel`, {}),
  );
}

export function useDeleteLocalModel() {
  return useLocalModelMutation((id: string) =>
    apiDelete<LocalModels>(`/settings/local-models/${encodeURIComponent(id)}`),
  );
}

export function useSetActiveLocalModel() {
  return useLocalModelMutation((modelId: string) =>
    apiPut<LocalModels>('/settings/local-models/active', { model_id: modelId }),
  );
}

export function useTestLocalModel() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { model_id: string; text: string; target_lang?: string }) =>
      apiPost<LocalModelTestResult>('/settings/local-models/test', body),
    onSettled: () => queryClient.invalidateQueries({ queryKey: LOCAL_MODELS_KEY }),
  });
}

const GROBID_KEY = ['settings', 'grobid'] as const;

/** Admin-only GROBID status; polls while installing or the JVM is starting. */
export function useGrobidStatus(enabled = true) {
  return useQuery({
    queryKey: GROBID_KEY,
    queryFn: () => apiGet<GrobidStatus>('/settings/grobid'),
    enabled,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return false;
      return data.install.status === 'running' || data.state === 'starting' ? 3000 : 30000;
    },
  });
}

function useGrobidMutation<TVars>(request: (vars: TVars) => Promise<GrobidStatus>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: request,
    onSuccess: (value) => queryClient.setQueryData(GROBID_KEY, value),
  });
}

export function useGrobidAction() {
  return useGrobidMutation((action: 'install' | 'start' | 'stop' | 'restart') =>
    apiPost<GrobidStatus>(`/settings/grobid/${action}`, {}),
  );
}

export function useUninstallGrobid() {
  return useGrobidMutation(() => apiDelete<GrobidStatus>('/settings/grobid'));
}

export function useSetGrobidBackend() {
  return useGrobidMutation((backend: string) => apiPut<GrobidStatus>('/settings/grobid/backend', { backend }));
}

export function useGrobidLogs(enabled: boolean) {
  return useQuery({
    queryKey: [...GROBID_KEY, 'logs'],
    queryFn: () => apiGet<GrobidLogs>('/settings/grobid/logs'),
    enabled,
  });
}

const BACKUP_KEY = ['settings', 'backup'] as const;

/** Admin-only backup targets (data repo + agent workspaces) and the daily timer. */
export function useBackupStatus(enabled = true) {
  return useQuery({ queryKey: BACKUP_KEY, queryFn: () => apiGet<BackupStatus>('/settings/backup'), enabled });
}

function useBackupMutation<TVars>(request: (vars: TVars) => Promise<BackupStatus>) {
  const queryClient = useQueryClient();
  return useMutation({ mutationFn: request, onSuccess: (value) => queryClient.setQueryData(BACKUP_KEY, value) });
}

export function useInitBackupTarget() {
  return useBackupMutation((targetId: string) => apiPost<BackupStatus>(`/settings/backup/targets/${encodeURIComponent(targetId)}/init`, {}));
}

export function useGenerateBackupKey() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (targetId: string) => apiPost<BackupKey>(`/settings/backup/targets/${encodeURIComponent(targetId)}/key`, {}),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: BACKUP_KEY }),
  });
}

export function useTestBackupRemote() {
  return useMutation({
    mutationFn: ({ targetId, url }: { targetId: string; url: string }) =>
      apiPost<BackupRemoteTest>(`/settings/backup/targets/${encodeURIComponent(targetId)}/remote/test`, { url }),
  });
}

export function useSaveBackupRemote() {
  return useBackupMutation(({ targetId, url }: { targetId: string; url: string }) =>
    apiPut<BackupStatus>(`/settings/backup/targets/${encodeURIComponent(targetId)}/remote`, { url }));
}

export function useRunBackup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (targetId?: string) =>
      apiPost<BackupRun>(`/settings/backup/run${targetId ? `?target_id=${encodeURIComponent(targetId)}` : ''}`, {}),
    onSuccess: (value) => queryClient.setQueryData(BACKUP_KEY, value.status),
  });
}

export function useSetBackupTimer() {
  return useBackupMutation((enabled: boolean) => apiPut<BackupStatus>('/settings/backup/timer', { enabled }));
}

const OPENCLAW_SETUP_KEY = ['settings', 'agents', 'openclaw'] as const;

/** Admin-only OpenClaw install/wiring state; polls while a setup job runs. */
export function useOpenClawSetup(enabled = true) {
  const queryClient = useQueryClient();
  return useQuery({
    queryKey: OPENCLAW_SETUP_KEY,
    queryFn: async () => {
      const value = await apiGet<OpenClawSetupStatus>('/settings/agents/openclaw');
      // A finished job may have created a new backup target (workspace).
      if (value.job?.status && value.job.status !== 'running') void queryClient.invalidateQueries({ queryKey: BACKUP_KEY });
      return value;
    },
    enabled,
    refetchInterval: (query) => (query.state.data?.job?.status === 'running' ? 2000 : false),
  });
}

export function useStartOpenClawJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ kind, profile, reuseLlm }: { kind: 'install' | 'connect' | 'migrate' | 'weixin'; profile?: string; reuseLlm?: boolean }) =>
      apiPost<OpenClawSetupStatus>(`/settings/agents/openclaw/${kind}`, { profile: profile ?? '', reuse_llm: reuseLlm ?? true }),
    onSuccess: (value) => queryClient.setQueryData(OPENCLAW_SETUP_KEY, value),
  });
}

export function useOpenClawGateway() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (action: 'start' | 'stop' | 'restart') => apiPost<OpenClawSetupStatus>('/settings/agents/openclaw-gateway', { action }),
    onSuccess: (value) => queryClient.setQueryData(OPENCLAW_SETUP_KEY, value),
  });
}

const AGENT_TOKEN_KEY = ['settings', 'agents', 'token'] as const;

/** Admin-only: does the assistant's server-side api.env hold a valid token. */
export function useAgentToken(enabled = true) {
  return useQuery({
    queryKey: AGENT_TOKEN_KEY,
    queryFn: () => apiGet<AgentTokenStatus>('/settings/agents/token'),
    enabled,
  });
}

/** Mint + write the assistant token server-side (plaintext never reaches the browser). */
export function useConfigureAgentToken() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiPost<AgentTokenStatus>('/settings/agents/token', {}),
    onSuccess: (value) => {
      queryClient.setQueryData(AGENT_TOKEN_KEY, value);
      void queryClient.invalidateQueries({ queryKey: ACCOUNTS_KEY });
    },
  });
}

export function useVerifySettingsConnection() {
  return useMutation({
    mutationFn: () =>
      apiPost<LlmConnectionVerify>('/settings/connection/verify', {}),
  });
}

export function useProfileSettings(profile: string) {
  return useQuery({
    queryKey: ['profiles', profile, 'settings'],
    queryFn: () =>
      apiGet<ProfileSettings>(`/profiles/${encodeURIComponent(profile)}/settings`),
    enabled: profile.length > 0,
  });
}

export function usePatchProfileSettings(profile: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: ProfileSettingsPatch) =>
      apiPatch<ProfileSettings>(
        `/profiles/${encodeURIComponent(profile)}/settings`,
        body,
      ),
    onSuccess: (value, body) => {
      queryClient.setQueryData(['profiles', profile, 'settings'], value);
      // Progression rules change every node's progress readout.
      if (body.skill_progression) {
        void queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'skill-tree'] });
      }
    },
  });
}

export function useCodexStatus() {
  return useQuery({
    queryKey: ['settings', 'codex', 'status'],
    queryFn: () => apiGet<CodexStatus>('/settings/codex/status'),
  });
}

export function useProfileCodexSettings(profile: string) {
  return useQuery({
    queryKey: ['profiles', profile, 'settings', 'codex'],
    queryFn: () =>
      apiGet<CodexSettings>(
        `/profiles/${encodeURIComponent(profile)}/settings/codex`,
      ),
    enabled: profile.length > 0,
  });
}

export function usePatchProfileCodexSettings(profile: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CodexSettingsPatch) =>
      apiPatch<CodexSettings>(
        `/profiles/${encodeURIComponent(profile)}/settings/codex`,
        body,
      ),
    onSuccess: (value) => {
      queryClient.setQueryData(['profiles', profile, 'settings', 'codex'], value);
    },
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

/** Recent agent writes (undo journal) for one profile, newest first. */
export function useAgentJournal(profile: string, limit = 20) {
  return useQuery({
    queryKey: ['profiles', profile, 'agent-journal', limit],
    queryFn: () =>
      apiGet<AgentJournal>(
        `/profiles/${encodeURIComponent(profile)}/agent/journal?limit=${limit}`,
      ),
    enabled: Boolean(profile),
  });
}

/** Undo one agent write; refreshes every query of the profile. */
export function useUndoAgentJournal(profile: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (entryId: string) =>
      apiPost<AgentJournalUndo>(
        `/profiles/${encodeURIComponent(profile)}/agent/journal/${encodeURIComponent(entryId)}/undo`,
      ),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles', profile] });
    },
  });
}

/** Workshop (ttyd terminal) URL + liveness; server caches 60s as well. */
export function useWorkshopStatus() {
  return useQuery({
    queryKey: ['system', 'workshop'],
    queryFn: () => apiGet<WorkshopStatus>('/system/workshop'),
    staleTime: 60_000,
  });
}

/** Workshop key bar: whitelisted key names (see core/workshop_service.KEYS). */
export function useWorkshopKeys() {
  return useMutation({
    mutationFn: (keys: string[]) => apiPost<{ ok: boolean }>('/system/workshop/keys', { keys }),
  });
}

/** Workshop input box: paste text into the terminal, optionally followed by Enter. */
export function useWorkshopInput() {
  return useMutation({
    mutationFn: (body: { text: string; submit: boolean }) => apiPost<{ ok: boolean }>('/system/workshop/input', body),
  });
}

const WORKSHOP_SERVICE_KEY = ['settings', 'workshop'] as const;

/** Admin-only ttyd/tmux service status; polls while installing or starting. */
export function useWorkshopService(enabled = true) {
  return useQuery({
    queryKey: WORKSHOP_SERVICE_KEY,
    queryFn: () => apiGet<WorkshopServiceStatus>('/settings/workshop'),
    enabled,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return false;
      return data.install.status === 'running' || data.state === 'starting' ? 2000 : 30000;
    },
  });
}

function useWorkshopServiceMutation<TVars>(request: (vars: TVars) => Promise<WorkshopServiceStatus>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: request,
    onSuccess: (value) => {
      queryClient.setQueryData(WORKSHOP_SERVICE_KEY, value);
      void queryClient.invalidateQueries({ queryKey: ['system', 'workshop'] });
    },
  });
}

export function useWorkshopServiceAction() {
  return useWorkshopServiceMutation((action: 'install' | 'start' | 'stop' | 'restart') =>
    apiPost<WorkshopServiceStatus>(`/settings/workshop/${action}`, {}),
  );
}

export function useUpdateWorkshopSettings() {
  return useWorkshopServiceMutation((patch: WorkshopSettingsPatch) => apiPut<WorkshopServiceStatus>('/settings/workshop', patch));
}

export function useUninstallWorkshop() {
  return useWorkshopServiceMutation((endSessions: boolean) =>
    apiDelete<WorkshopServiceStatus>(`/settings/workshop${endSessions ? '?end_sessions=true' : ''}`),
  );
}

export function useWorkshopLogs(enabled: boolean) {
  return useQuery({
    queryKey: [...WORKSHOP_SERVICE_KEY, 'logs'],
    queryFn: () => apiGet<WorkshopLogs>('/settings/workshop/logs'),
    enabled,
  });
}

export interface SkillTreeResult {
  tree: SkillTreeResponse;
  /** skill-tree.yaml ETag for If-Match on node-status mutations. */
  etag: string;
}

/** Skill tree fetch that captures the tree-file ETag for If-Match. */
export function useSkillTree(profile: string) {
  return useQuery({
    queryKey: ['profiles', profile, 'skill-tree'],
    queryFn: async (): Promise<SkillTreeResult> => {
      const { data, headers } = await apiGetWithHeaders<SkillTreeResponse>(
        `/profiles/${encodeURIComponent(profile)}/skill-tree`,
      );
      return { tree: data, etag: headers.get('ETag') ?? '' };
    },
    enabled: profile.length > 0,
  });
}

/** Evidence rows linked to one skill node (skill-tree.yaml evidence_refs). */
export function useSkillEvidence(profile: string, skillId: string) {
  return useQuery({
    queryKey: ['profiles', profile, 'evidence', 'skill', skillId],
    queryFn: () => {
      const params = new URLSearchParams({ skill_id: skillId, limit: '200' });
      return apiGet<EvidenceListResponse>(
        `/profiles/${encodeURIComponent(profile)}/evidence?${params.toString()}`,
      );
    },
    enabled: profile.length > 0 && skillId.length > 0,
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

/** Board fetch that captures the kanban.md ETag for If-Match mutations and
 * the full section order (lane-local drag indices must be translated to
 * section-global ones — the backend's to_index spans ALL cards in a
 * section, not just the lane's filtered subset). */
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

/**
 * Just the kanban.md ETag, selected out of the shared kanban query (same
 * cache entry as useKanbanBoard — one fetch serves both). Kanban mutations
 * validate the single-file kanban ETag, NOT the 6-file projects-board ETag —
 * mixing them 412s reliably.
 */
export function useKanbanEtag(profile: string) {
  return useQuery({
    queryKey: ['profiles', profile, 'kanban'],
    queryFn: async (): Promise<KanbanBoardResult> => {
      const { data, headers } = await apiGetWithHeaders<KanbanBoard>(kanbanBase(profile));
      return { board: data, etag: headers.get('ETag') ?? '' };
    },
    enabled: profile.length > 0,
    select: (result) => result.etag,
  });
}

/** Refresh the kanban.md ETag straight from the server (post-412). */
async function refreshKanbanEtag(profile: string): Promise<string> {
  const { headers } = await apiGetWithHeaders<KanbanBoard>(kanbanBase(profile));
  return headers.get('ETag') ?? '';
}

/** Write the post-mutation kanban ETag into the cached kanban board. */
function writeKanbanEtag(queryClient: QueryClient, profile: string, etag: string) {
  if (!etag) return;
  queryClient.setQueryData(
    ['profiles', profile, 'kanban'],
    (old: KanbanBoardResult | undefined) => (old ? { ...old, etag } : old),
  );
}

function useInvalidateKanban(profile: string) {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'kanban'] });
    // Kanban mutations change the projects-board aggregation too.
    queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'projects-board'] });
  };
}

export function useAddKanbanCard(profile: string) {
  const invalidate = useInvalidateKanban(profile);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ body, etag }: { body: KanbanCardCreateRequest; etag: string }) =>
      postEtagMutation<KanbanMutationResponse>(
        `${kanbanBase(profile)}/cards`,
        body,
        etag,
        () => refreshKanbanEtag(profile),
      ),
    onSuccess: ({ etag }) => {
      writeKanbanEtag(queryClient, profile, etag);
      invalidate();
    },
  });
}

export function useMoveKanbanCard(profile: string) {
  const invalidate = useInvalidateKanban(profile);
  const queryClient = useQueryClient();
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
      postEtagMutation<KanbanMutationResponse>(
        `${kanbanBase(profile)}/cards/${encodeURIComponent(cardRef)}/move`,
        { target_section: targetSection, ...(toIndex === undefined ? {} : { to_index: toIndex }) },
        etag,
        () => refreshKanbanEtag(profile),
      ),
    onSuccess: ({ etag }) => {
      writeKanbanEtag(queryClient, profile, etag);
      invalidate();
    },
  });
}

export function useDoneKanbanCard(profile: string) {
  const invalidate = useInvalidateKanban(profile);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ cardRef, etag }: { cardRef: string; etag: string }) =>
      postEtagMutation<KanbanMutationResponse>(
        `${kanbanBase(profile)}/cards/${encodeURIComponent(cardRef)}/done`,
        undefined,
        etag,
        () => refreshKanbanEtag(profile),
      ),
    onSuccess: ({ etag }) => {
      writeKanbanEtag(queryClient, profile, etag);
      invalidate();
    },
  });
}

/** Schedule one card's planned dates ("" clears; null/undefined keeps). */
export function useScheduleKanbanCard(profile: string) {
  const invalidate = useInvalidateKanban(profile);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      cardRef,
      body,
      etag,
    }: {
      cardRef: string;
      body: KanbanCardScheduleRequest;
      etag: string;
    }) =>
      postEtagMutation<KanbanMutationResponse>(
        `${kanbanBase(profile)}/cards/${encodeURIComponent(cardRef)}/schedule`,
        body,
        etag,
        () => refreshKanbanEtag(profile),
      ),
    onSuccess: ({ etag }) => {
      writeKanbanEtag(queryClient, profile, etag);
      invalidate();
    },
  });
}

/**
 * Edit one card's whitelist fields (title/context/why/project_id/
 * milestone_id/tags). `project_id: ''` unassigns the card from its lane.
 */
/** A card PATCH that replaces a whole list field (server semantics: tags /
 * todos are full-replace) must not be auto-retried after a 412. */
export function kanbanPatchReplacesList(body: KanbanCardPatchRequest): boolean {
  return body.tags != null || body.todos != null;
}

export function usePatchKanbanCard(profile: string) {
  const invalidate = useInvalidateKanban(profile);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      cardRef,
      body,
      etag,
    }: {
      cardRef: string;
      body: KanbanCardPatchRequest;
      etag: string;
    }) =>
      patchEtagMutation<KanbanMutationResponse>(
        `${kanbanBase(profile)}/cards/${encodeURIComponent(cardRef)}`,
        body,
        etag,
        () => refreshKanbanEtag(profile),
        { retryOn412: !kanbanPatchReplacesList(body) },
      ),
    onSuccess: ({ etag }) => {
      writeKanbanEtag(queryClient, profile, etag);
      invalidate();
      // Lane assignment re-syncs project-board.yaml on the server.
      queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'project-board'] });
    },
  });
}

/**
 * Delete one kanban card for good (detail-card danger action).
 * `record_chronicle` (default off) appends a task.deleted chronicle entry.
 */
export function useDeleteKanbanCard(profile: string) {
  const invalidate = useInvalidateKanban(profile);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      cardRef,
      body,
      etag,
    }: {
      cardRef: string;
      body: KanbanCardDeleteRequest;
      etag: string;
    }) =>
      deleteEtagMutation<KanbanCardDeleteResponse>(
        `${kanbanBase(profile)}/cards/${encodeURIComponent(cardRef)}`,
        body,
        etag,
        () => refreshKanbanEtag(profile),
      ),
    onSuccess: ({ etag }) => {
      writeKanbanEtag(queryClient, profile, etag);
      invalidate();
    },
  });
}

// --- Phase 2 unified /projects ----------------------------------------------

function projectsBoardBase(profile: string): string {
  return `/profiles/${encodeURIComponent(profile)}/projects-board`;
}

/** Projects-board fetch that captures the 6-file board ETag (display only —
 * kanban mutations must use the kanban ETag from useKanbanEtag instead). */
export function useProjectsBoard(profile: string) {
  return useQuery({
    queryKey: ['profiles', profile, 'projects-board'],
    queryFn: async (): Promise<ProjectsBoardResult> => {
      const { data, headers } = await apiGetWithHeaders<ProjectsBoardResponse>(
        projectsBoardBase(profile),
      );
      return { board: data, etag: headers.get('ETag') ?? '' };
    },
    enabled: profile.length > 0,
  });
}

/** Invalidate only the projects-board aggregation (check-ins touch it). */
export function useInvalidateProjectsBoard(profile: string) {
  const queryClient = useQueryClient();
  return () =>
    queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'projects-board'] });
}

/**
 * Server-side archived habits (projects-board ?include_archived=true, rows
 * flagged `archived: true`). Fetched lazily by the 日课栏 显示已归档 toggle;
 * shares the projects-board key prefix so lifecycle mutations invalidate it.
 */
export function useArchivedBoardHabits(profile: string, enabled: boolean) {
  return useQuery({
    queryKey: ['profiles', profile, 'projects-board', 'archived-habits'],
    queryFn: async (): Promise<ProjectsBoardHabit[]> => {
      const { data } = await apiGetWithHeaders<ProjectsBoardResponse>(
        `${projectsBoardBase(profile)}?include_archived=true`,
      );
      return (data.habits ?? []).filter((habit) => habit.archived);
    },
    enabled: enabled && profile.length > 0,
  });
}

/**
 * Append one habit check-in. No GET endpoint exposes the activity-log ETag,
 * so the first check-in goes out without If-Match (the server still
 * re-checks an in-lock snapshot); the response ETag is cached for
 * consecutive check-ins, and a 412 degrades to one retry without If-Match.
 */
export function useAddCheckin(profile: string) {
  const queryClient = useQueryClient();
  const invalidateBoard = useInvalidateProjectsBoard(profile);
  const cacheKey = ['profiles', profile, 'checkin-etag'];
  return useMutation({
    mutationFn: async (body: CheckinCreateRequest) => {
      const path = `/profiles/${encodeURIComponent(profile)}/checkins`;
      const cached = queryClient.getQueryData<string>(cacheKey) ?? '';
      try {
        const res = await apiPostWithHeaders<CheckinMutationResponse>(path, body, {
          headers: ifMatch(cached),
        });
        return { data: res.data, etag: res.headers.get('ETag') ?? cached };
      } catch (error) {
        if (!(error instanceof ApiError) || error.status !== 412) {
          throw error;
        }
        // Retry with the fresh ETag (never without If-Match — that would
        // bypass the concurrency check entirely).
        const fresh = error.etag;
        if (!fresh) {
          throw error;
        }
        const res = await apiPostWithHeaders<CheckinMutationResponse>(path, body, {
          headers: ifMatch(fresh),
        });
        return { data: res.data, etag: res.headers.get('ETag') ?? fresh };
      }
    },
    onSuccess: ({ etag }) => {
      if (etag) {
        queryClient.setQueryData(cacheKey, etag);
      }
      invalidateBoard();
      queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'activity'] });
      // A plan-bound check-in moves the plan's progress counters.
      queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'habit-plans'] });
    },
  });
}

/**
 * Remove one check-in row (销印). Shares the cached activity-log ETag with
 * useAddCheckin; the first call may go out without If-Match, and a 412
 * degrades to one retry without If-Match (same contract as the POST).
 */
export function useDeleteCheckin(profile: string) {
  const queryClient = useQueryClient();
  const invalidateBoard = useInvalidateProjectsBoard(profile);
  const cacheKey = ['profiles', profile, 'checkin-etag'];
  return useMutation({
    mutationFn: async ({ checkinId }: { checkinId: string }) => {
      const path = `/profiles/${encodeURIComponent(profile)}/checkins/${encodeURIComponent(checkinId)}`;
      const cached = queryClient.getQueryData<string>(cacheKey) ?? '';
      try {
        const res = await apiDeleteWithHeaders<CheckinDeleteResponse>(path, undefined, {
          headers: ifMatch(cached),
        });
        return { data: res.data, etag: res.headers.get('ETag') ?? cached };
      } catch (error) {
        if (!(error instanceof ApiError) || error.status !== 412) {
          throw error;
        }
        // Retry with the fresh ETag the 412 carried — never without If-Match.
        if (!error.etag) {
          throw error;
        }
        const res = await apiDeleteWithHeaders<CheckinDeleteResponse>(path, undefined, {
          headers: ifMatch(error.etag),
        });
        return { data: res.data, etag: res.headers.get('ETag') ?? error.etag };
      }
    },
    onSuccess: ({ etag }) => {
      if (etag) {
        queryClient.setQueryData(cacheKey, etag);
      }
      invalidateBoard();
      queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'activity'] });
      // 销印 of a plan-bound check-in moves the plan's progress counters.
      queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'habit-plans'] });
    },
  });
}

// --- Habit lifecycle (日课栏 gear menu) ---------------------------------------

function habitPath(profile: string, habitId: string): string {
  return `/profiles/${encodeURIComponent(profile)}/habits/${encodeURIComponent(habitId)}`;
}

/**
 * Archive (or restore) one habit: POST .../habits/{id}/archive {archived}.
 * The projects-board aggregation owns the habit strip, so it invalidates;
 * the activity log keeps the habit's check-in history either way.
 */
export function useArchiveHabit(profile: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ habitId, archived }: { habitId: string; archived: boolean }) =>
      apiPost<HabitArchiveResponse>(`${habitPath(profile, habitId)}/archive`, {
        archived,
      } satisfies HabitArchiveRequest),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'projects-board'] });
      queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'activity'] });
    },
  });
}

/**
 * Delete one habit for good (type-the-name confirm): DELETE .../habits/{id}
 * with {confirm_title, record_chronicle} → {ok, deleted_id, checkins_removed}.
 * 422 `habit_delete_confirm_mismatch` means the typed title differs.
 */
export function useDeleteHabit(profile: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ habitId, body }: { habitId: string; body: HabitDeleteRequest }) =>
      apiDelete<HabitDeleteResponse>(habitPath(profile, habitId), body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'projects-board'] });
      queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'activity'] });
      queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'chronicle'] });
    },
  });
}

// --- Habit phase plans (习惯阶段计划) -----------------------------------------

function habitPlansBase(profile: string): string {
  return `/profiles/${encodeURIComponent(profile)}/habit-plans`;
}

export interface HabitPlanFilters {
  habitId?: string;
  status?: string;
}

/** Habit-plan list (each item carries computed progress: current_week,
 * days_done/days_total, completion_rate, weekly breakdown). */
export function useHabitPlans(profile: string, filters: HabitPlanFilters = {}) {
  return useQuery({
    queryKey: ['profiles', profile, 'habit-plans', filters],
    queryFn: async (): Promise<HabitPlan[]> => {
      const params = new URLSearchParams();
      if (filters.habitId) {
        params.set('habit_id', filters.habitId);
      }
      if (filters.status) {
        params.set('status', filters.status);
      }
      const query = params.toString();
      const data = await apiGet<HabitPlanListResponse>(
        `${habitPlansBase(profile)}${query ? `?${query}` : ''}`,
      );
      return data.plans ?? [];
    },
    enabled: profile.length > 0,
  });
}

/** Active plans only — the 日课栏 badge / check-in binding / lane section all
 * read this one cached list (same query key, one fetch). */
export function useActiveHabitPlans(profile: string) {
  return useHabitPlans(profile, { status: 'active' });
}

function useInvalidateHabitPlans(profile: string) {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'habit-plans'] });
    // Create generates weekly Queue kanban cards; plan progress feeds the
    // projects-board habit strip, and check-ins touch the activity log.
    queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'projects-board'] });
    queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'project-board'] });
    queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'kanban'] });
  };
}

/** Create one phase plan (201; response carries kanban_card_ids). */
export function useCreateHabitPlan(profile: string) {
  const invalidate = useInvalidateHabitPlans(profile);
  return useMutation({
    mutationFn: (body: HabitPlanCreateRequest) =>
      apiPost<HabitPlanMutationResponse>(habitPlansBase(profile), body),
    onSuccess: invalidate,
  });
}

/** Partial edit: title/weekly_tasks, or status forward (active →
 * completed/archived). */
export function usePatchHabitPlan(profile: string) {
  const invalidate = useInvalidateHabitPlans(profile);
  return useMutation({
    mutationFn: ({ planId, body }: { planId: string; body: HabitPlanPatchRequest }) =>
      apiPatch<HabitPlanMutationResponse>(
        `${habitPlansBase(profile)}/${encodeURIComponent(planId)}`,
        body,
      ),
    onSuccess: invalidate,
  });
}

/**
 * Delete one phase plan for good (type-the-name confirm): DELETE
 * .../habit-plans/{id} with {confirm_title, delete_open_cards,
 * record_chronicle} → {ok, deleted_id, cards_removed}. 422
 * `habit_plan_delete_confirm_mismatch` means the typed title differs;
 * check-in rows are never touched server-side.
 */
export function useDeleteHabitPlan(profile: string) {
  const invalidate = useInvalidateHabitPlans(profile);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ planId, body }: { planId: string; body: HabitPlanDeleteRequest }) =>
      apiDelete<HabitPlanDeleteResponse>(
        `${habitPlansBase(profile)}/${encodeURIComponent(planId)}`,
        body,
      ),
    onSuccess: () => {
      invalidate();
      // record_chronicle=true appends a habit_plan.deleted entry.
      queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'chronicle'] });
    },
  });
}

function planTemplatesBase(profile: string): string {
  return `/profiles/${encodeURIComponent(profile)}/plan-templates`;
}

/** Plan-template list fetch that captures the plan-source ETag. */
export function usePlanTemplates(profile: string) {
  return useQuery({
    queryKey: ['profiles', profile, 'plan-templates'],
    queryFn: async (): Promise<PlanTemplateListResult> => {
      const { data, headers } = await apiGetWithHeaders<PlanTemplateListResponse>(
        planTemplatesBase(profile),
      );
      return { data, etag: headers.get('ETag') ?? '' };
    },
    enabled: profile.length > 0,
  });
}

/** Refresh the plan-templates ETag straight from the server (post-412). */
async function refreshPlanTemplatesEtag(profile: string): Promise<string> {
  const { headers } = await apiGetWithHeaders<PlanTemplateListResponse>(
    planTemplatesBase(profile),
  );
  return headers.get('ETag') ?? '';
}

/** Instantiate one habit-plan template into a project case + habit. */
export function useInstantiatePlanTemplate(profile: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ body, etag }: { body: PlanTemplateInstantiateRequest; etag: string }) =>
      postEtagMutation<PlanTemplateInstantiateResponse>(
        `${planTemplatesBase(profile)}/instantiate`,
        body,
        etag,
        () => refreshPlanTemplatesEtag(profile),
      ),
    onSuccess: ({ etag }) => {
      if (etag) {
        queryClient.setQueryData(
          ['profiles', profile, 'plan-templates'],
          (old: PlanTemplateListResult | undefined) => (old ? { ...old, etag } : old),
        );
      }
      queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'plan-templates'] });
      queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'projects-board'] });
      queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'project-board'] });
    },
  });
}

export interface ActivityFilters {
  status: string;
  kind: string;
}

/** Unresolved failures from all profile-scoped AI surfaces. */
export function useAIExceptions(profile: string) {
  return useQuery({
    queryKey: ['profiles', profile, 'ai-exceptions'],
    queryFn: () =>
      apiGet<AIExceptionsResponse>(
        `/profiles/${encodeURIComponent(profile)}/ai-exceptions?limit=50`,
      ),
    enabled: profile.length > 0,
    staleTime: 15_000,
    refetchInterval: 30_000,
  });
}

export function useDismissAIExceptions(profile: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (ids: string[]) =>
      apiPost<AIExceptionBulkDismissResponse>(
        `/profiles/${encodeURIComponent(profile)}/ai-exceptions/dismiss`,
        { ids },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'ai-exceptions'] });
      queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'activity'] });
    },
  });
}

export function useGoals(profile: string) {
  return useQuery({
    queryKey: ['profiles', profile, 'goals'],
    queryFn: () => apiGet<GoalsResponse>(`/profiles/${encodeURIComponent(profile)}/goals`),
    enabled: profile.length > 0,
  });
}

// --- Home starmap editing (design: docs/zh/guides/home.md) ---
// The starmap GET ETag covers SKILL.md + goals.yaml, so every north-star /
// goal mutation invalidates the starmap snapshot (in-place refresh), the
// goal book, and the chronicle (briefing-line flavor).

function useInvalidateStarmapEditing(profile: string) {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'starmap'] });
    queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'goals'] });
    queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'chronicle'] });
  };
}

/**
 * Surgically rewrite the North Star (full / brief / visibility). No If-Match:
 * GET /goals carries no SKILL.md ETag and the contract makes it optional;
 * the server re-checks an in-lock snapshot either way. A no-op patch is a
 * server-side no-write (changed=false).
 */
export function usePatchNorthStar(profile: string) {
  const invalidate = useInvalidateStarmapEditing(profile);
  return useMutation({
    mutationFn: (body: NorthStarPatchRequest) =>
      apiPatch<NorthStarMutationResponse>(
        `/profiles/${encodeURIComponent(profile)}/north-star`,
        body,
      ),
    onSuccess: invalidate,
  });
}

/** Create one goal (title required; target ISO date; status active default). */
export function useCreateGoal(profile: string) {
  const invalidate = useInvalidateStarmapEditing(profile);
  return useMutation({
    mutationFn: (body: GoalCreateRequest) =>
      apiPost<GoalMutationResponse>(`/profiles/${encodeURIComponent(profile)}/goals`, body),
    onSuccess: invalidate,
  });
}

/** Edit one goal's title/summary/target/status (404 goal_not_found). */
export function usePatchGoal(profile: string) {
  const invalidate = useInvalidateStarmapEditing(profile);
  return useMutation({
    mutationFn: ({ goalId, body }: { goalId: string; body: GoalPatchRequest }) =>
      apiPatch<GoalMutationResponse>(
        `/profiles/${encodeURIComponent(profile)}/goals/${encodeURIComponent(goalId)}`,
        body,
      ),
    onSuccess: invalidate,
  });
}

/** Append-only chronicle, newest first (briefing-line flavor). */
export function useChronicle(profile: string, limit = 40) {
  return useQuery({
    queryKey: ['profiles', profile, 'chronicle', limit],
    queryFn: () =>
      apiGet<ChronicleResponse>(
        `/profiles/${encodeURIComponent(profile)}/chronicle?limit=${limit}`,
      ),
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

const CRYSTALLIZE_READ_MODEL_KEYS = [
  'evidence',
  'evidence-review',
  'evidence-stages',
  'kanban',
  'skill-tree',
  'starmap',
  'home',
  'project-board',
  'projects-board',
  'crystallize-candidates',
] as const;

/** Invalidate every read model affected by a successful crystallization. */
export function invalidateCrystallizeReadModels(
  queryClient: QueryClient,
  profile: string,
): void {
  for (const key of CRYSTALLIZE_READ_MODEL_KEYS) {
    queryClient.invalidateQueries({ queryKey: ['profiles', profile, key] });
  }
}

function useInvalidateEvidenceReview(profile: string) {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'evidence-review'] });
    queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'evidence'] });
    queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'evidence-stages'] });
    // Evidence grading/linking changes derived growth and project projections.
    for (const key of ['skill-tree', 'starmap', 'home', 'project-board', 'projects-board']) {
      queryClient.invalidateQueries({ queryKey: ['profiles', profile, key] });
    }
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

/** PATCH twin of postEtagMutation (kanban card field edits).
 * `retryOn412: false` surfaces the 412 instead of blindly re-sending — for
 * bodies that replace a whole list (tags / todos), where a retry would
 * silently drop the concurrent writer's items. */
async function patchEtagMutation<T>(
  path: string,
  body: unknown,
  etag: string,
  refreshEtag: () => Promise<string>,
  { retryOn412 = true }: { retryOn412?: boolean } = {},
): Promise<{ data: T; etag: string }> {
  try {
    const res = await apiPatchWithHeaders<T>(path, body, { headers: ifMatch(etag) });
    return { data: res.data, etag: res.headers.get('ETag') ?? etag };
  } catch (error) {
    if (!(error instanceof ApiError) || error.status !== 412 || !retryOn412) {
      throw error;
    }
    const fresh = await refreshEtag();
    const res = await apiPatchWithHeaders<T>(path, body, { headers: ifMatch(fresh) });
    return { data: res.data, etag: res.headers.get('ETag') ?? fresh };
  }
}

/** DELETE twin of postEtagMutation (kanban card delete). */
async function deleteEtagMutation<T>(
  path: string,
  body: unknown,
  etag: string,
  refreshEtag: () => Promise<string>,
): Promise<{ data: T; etag: string }> {
  try {
    const res = await apiDeleteWithHeaders<T>(path, body, { headers: ifMatch(etag) });
    return { data: res.data, etag: res.headers.get('ETag') ?? etag };
  } catch (error) {
    if (!(error instanceof ApiError) || error.status !== 412) {
      throw error;
    }
    const fresh = await refreshEtag();
    const res = await apiDeleteWithHeaders<T>(path, body, { headers: ifMatch(fresh) });
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

/** Write the post-mutation tree ETag into the cached skill-tree reads. */
function writeTreeEtag(queryClient: QueryClient, profile: string, etag: string) {
  if (!etag) return;
  queryClient.setQueryData(
    ['profiles', profile, 'skill-tree', 'flat'],
    (old: SkillTreeFlatResult | undefined) => (old ? { ...old, etag } : old),
  );
  queryClient.setQueryData(
    ['profiles', profile, 'skill-tree'],
    (old: SkillTreeResult | undefined) => (old ? { ...old, etag } : old),
  );
}

/** Optimistically rewrite one node's status inside the cached tree. */
function patchCachedNodeStatus(
  queryClient: QueryClient,
  profile: string,
  nodeId: string,
  yamlStatus: string,
): SkillTreeResult | undefined {
  const previous = queryClient.getQueryData<SkillTreeResult>([
    'profiles',
    profile,
    'skill-tree',
  ]);
  if (!previous) return undefined;
  const walk = (nodes: SkillTreeResponse['nodes']): SkillTreeResponse['nodes'] =>
    (nodes ?? []).map((node) =>
      node.id === nodeId
        ? { ...node, status: yamlStatus }
        : { ...node, children: walk(node.children ?? []) },
    );
  const next = {
    ...previous,
    tree: { ...previous.tree, nodes: walk(previous.tree.nodes ?? []) },
  };
  queryClient.setQueryData(['profiles', profile, 'skill-tree'], next);
  return previous;
}

/** 三态 write (G3): PATCH one node's status; lit lands as YAML `solid`. */
export function usePatchSkillNodeStatus(profile: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ nodeId, status, etag }: { nodeId: string; status: string; etag: string }) =>
      patchEtagMutation<SkillNodePatchResponse>(
        `/profiles/${encodeURIComponent(profile)}/skill-tree/nodes/${encodeURIComponent(nodeId)}`,
        { status } satisfies SkillNodePatchRequest,
        etag,
        () => refreshTreeEtag(profile),
      ),
    onMutate: ({ nodeId, status }) => {
      queryClient.cancelQueries({ queryKey: ['profiles', profile, 'skill-tree'] });
      const yamlStatus = status === 'lit' ? 'solid' : status;
      const previous = patchCachedNodeStatus(queryClient, profile, nodeId, yamlStatus);
      return { previous };
    },
    onError: (_error, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(['profiles', profile, 'skill-tree'], context.previous);
      }
    },
    onSuccess: ({ etag }) => {
      writeTreeEtag(queryClient, profile, etag);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'skill-tree'] });
      // The home starmap + projects boards read skill statuses too.
      queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'projects-board'] });
      queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'starmap'] });
      queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'home'] });
    },
  });
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
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CrystallizeApplyRequest) =>
      apiPost<CrystallizeApplyResponse>(
        `/profiles/${encodeURIComponent(profile)}/crystallize/apply`,
        body,
      ),
    onSuccess: () => {
      invalidateCrystallizeReadModels(queryClient, profile);
    },
  });
}


/**
 * Generic async-job creation (LLM long tasks:
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
    // Case sync and task mutations also write kanban.md / evidence-pool.yaml,
    // and every case change reshapes the projects-board aggregation.
    queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'kanban'] });
    queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'projects-board'] });
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

/**
 * Delete one project case for good (type-the-name confirm). The board ETag
 * (covers kanban.md + project-board.yaml) goes out as If-Match; 422 with
 * code `project_delete_confirm_mismatch` means the typed title differs.
 */
export function useDeleteProjectCase(profile: string) {
  const invalidate = useInvalidateProjectBoard(profile);
  return useMutation({
    mutationFn: ({
      caseId,
      body,
      etag,
    }: {
      caseId: string;
      body: ProjectCaseDeleteRequest;
      etag: string;
    }) =>
      apiDelete<ProjectCaseDeleteResponse>(
        `${projectBoardBase(profile)}/cases/${encodeURIComponent(caseId)}`,
        body,
        { headers: ifMatch(etag) },
      ),
    onSuccess: invalidate,
  });
}

function studioBase(profile: string): string {
  return `/profiles/${encodeURIComponent(profile)}/studio`;
}

/** Content workspace projection (blog list only; never evidence/claims). */
export function useContentWorkspace(profile: string) {
  return useQuery({
    queryKey: ['profiles', profile, 'content'],
    queryFn: () => apiGetWithHeaders<ContentWorkspaceResponse>(`/profiles/${encodeURIComponent(profile)}/content`),
    enabled: profile.length > 0,
  });
}

function contentBlogPath(profile: string, slug: string): string {
  const encoded = slug.split('/').map(encodeURIComponent).join('/');
  return `/profiles/${encodeURIComponent(profile)}/content/blog/${encoded}`;
}

/** Absolute API URL of one post (for keepalive saves outside react-query). */
export function contentBlogApiUrl(profile: string, slug: string): string {
  return `${apiBase()}${contentBlogPath(profile, slug)}`;
}

/**
 * Browser URL for a profile-relative media path (``media/blog/<slug>/x.png``).
 * Absolute URLs and data URIs pass through unchanged.
 */
export function contentMediaUrl(profile: string, path: string): string {
  const clean = path.trim();
  if (!clean || /^([a-z][a-z0-9+.-]*:|\/\/)/i.test(clean)) return clean;
  const encoded = clean.replace(/^\/+/, '').split('/').map(encodeURIComponent).join('/');
  return `/api/v1/profiles/${encodeURIComponent(profile)}/content/media-file/${encoded}`;
}

function useInvalidateContentList(profile: string) {
  const queryClient = useQueryClient();
  // exact: refreshing the list must not refetch the open post's detail query,
  // or the editor would see a "new" server copy right after its own save.
  return () => void queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'content'], exact: true });
}

export function useContentPost(profile: string, slug: string) {
  return useQuery({
    queryKey: ['profiles', profile, 'content', 'post', slug],
    queryFn: async (): Promise<StudioPostResult> => {
      const { data, headers } = await apiGetWithHeaders<StudioPostDetail>(contentBlogPath(profile, slug));
      return { post: data, etag: headers.get('ETag') ?? '' };
    },
    enabled: profile.length > 0 && slug.length > 0,
    staleTime: Infinity,
  });
}

/** Mutation result for content writes: the fresh post plus its new ETag. */
export interface ContentPostWriteResult {
  post: StudioPostDetail;
  etag: string;
}

export function useCreateContentPost(profile: string) {
  const invalidate = useInvalidateContentList(profile);
  return useMutation({
    mutationFn: async ({ body, etag }: { body: StudioPostCreateRequest; etag: string }): Promise<ContentPostWriteResult> => {
      const { data, headers } = await apiPostWithHeaders<StudioPostMutationResponse>(
        `/profiles/${encodeURIComponent(profile)}/content/blog`,
        body,
        { headers: ifMatch(etag) },
      );
      return { post: data.post, etag: headers.get('ETag') ?? '' };
    },
    onSuccess: invalidate,
  });
}

export function useSaveContentPost(profile: string) {
  const invalidate = useInvalidateContentList(profile);
  return useMutation({
    mutationFn: async ({
      slug,
      body,
      etag,
      autosave = false,
    }: {
      slug: string;
      body: StudioPostSaveRequest;
      etag: string;
      /** Debounced editor save: written to disk, no Git backup commit. */
      autosave?: boolean;
    }): Promise<ContentPostWriteResult> => {
      const path = `${contentBlogPath(profile, slug)}${autosave ? '?autosave=1' : ''}`;
      const { data, headers } = await apiPutWithHeaders<StudioPostMutationResponse>(path, body, {
        headers: ifMatch(etag),
      });
      return { post: data.post, etag: headers.get('ETag') ?? '' };
    },
    onSuccess: invalidate,
  });
}

export function useCheckContentPost(profile: string) {
  return useMutation({
    mutationFn: ({ slug, body }: { slug: string; body: StudioPostSaveRequest }) =>
      apiPost<StudioValidationResponse>(`${contentBlogPath(profile, slug)}/check`, body),
  });
}

export function usePublishContentPost(profile: string) {
  const invalidate = useInvalidateContentList(profile);
  return useMutation({
    mutationFn: async ({ slug, body, etag }: { slug: string; body?: StudioPostSaveRequest; etag: string }): Promise<ContentPostWriteResult> => {
      const { data, headers } = await apiPostWithHeaders<StudioPostMutationResponse>(`${contentBlogPath(profile, slug)}/publish`, body, {
        headers: ifMatch(etag),
      });
      return { post: data.post, etag: headers.get('ETag') ?? '' };
    },
    onSuccess: invalidate,
  });
}

/** One post's media directory (files only; the editor loads them by URL). */
export function useContentPostMedia(profile: string, slug: string) {
  return useQuery({
    queryKey: ['profiles', profile, 'content', 'media', slug],
    queryFn: () => apiGet<ContentMedia[]>(`${contentBlogPath(profile, slug)}/media`),
    enabled: profile.length > 0 && slug.length > 0,
  });
}

/** Store a media file for a post; the post itself is not rewritten. */
export function useUploadContentMedia(profile: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ slug, file }: { slug: string; file: File }) => {
      const kind = file.type.startsWith('video/') ? 'video' : 'image';
      const form = new FormData();
      form.append('file', file);
      return apiPostForm<ContentMediaUploadResponse>(
        `${contentBlogPath(profile, slug)}/media?${new URLSearchParams({ kind })}`,
        form,
      );
    },
    onSuccess: (_result, { slug }) =>
      void queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'content', 'media', slug] }),
  });
}

/** Which content-AI features are configured on the server. */
export function useContentAIStatus(profile: string) {
  return useQuery({
    queryKey: ['profiles', profile, 'content', 'ai-status'],
    queryFn: () => apiGet<ContentAIStatus>(`/profiles/${encodeURIComponent(profile)}/content/ai/status`),
    enabled: profile.length > 0,
    staleTime: 5 * 60_000,
  });
}

/** Browser URL of one staged cover candidate image. */
export function contentCoverCandidateUrl(profile: string, candidatePath: string): string {
  const params = new URLSearchParams({ path: candidatePath });
  return `${apiBase()}/profiles/${encodeURIComponent(profile)}/content/cover-candidates/file?${params}`;
}

export function usePromoteCoverCandidate(profile: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ slug, candidatePath }: { slug: string; candidatePath: string }) =>
      apiPost<{ ok: boolean; path: string }>(`${contentBlogPath(profile, slug)}/cover-candidates/promote`, {
        candidate_path: candidatePath,
      }),
    onSuccess: (_result, { slug }) =>
      void queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'content', 'media', slug] }),
  });
}

export function discardCoverCandidate(profile: string, candidatePath: string): Promise<unknown> {
  return apiPost(`/profiles/${encodeURIComponent(profile)}/content/cover-candidates/discard`, {
    candidate_path: candidatePath,
  });
}

const careerPath = (profile: string, rest = '') => `/profiles/${encodeURIComponent(profile)}/career${rest}`;

/** Career workspace overview: master resume (+ETag), drafts, AI/PDF availability. */
export function useCareerWorkspace(profile: string) {
  return useQuery({
    queryKey: ['profiles', profile, 'career'],
    queryFn: () => apiGet<CareerWorkspaceResponse>(careerPath(profile)),
    enabled: profile.length > 0,
    // The resume editor owns its draft; avoid refetches clobbering the form.
    staleTime: Infinity,
  });
}

/** Conflict-safe resume save; `autosave` skips the Git backup commit server-side. */
export function saveCareerResume(
  profile: string,
  resume: ResumeDoc,
  etag: string,
  autosave: boolean,
): Promise<CareerWorkspaceResponse> {
  return apiPut<CareerWorkspaceResponse>(
    careerPath(profile, `/resume${autosave ? '?autosave=1' : ''}`),
    { resume },
    { headers: ifMatch(etag) },
  );
}

export function careerResumeApiUrl(profile: string): string {
  return `${apiBase()}${careerPath(profile, '/resume')}`;
}

export function uploadCareerPhoto(profile: string, file: File): Promise<CareerPhotoResponse> {
  const form = new FormData();
  form.append('file', file);
  return apiPostForm<CareerPhotoResponse>(careerPath(profile, '/resume/photo'), form);
}

export function importCareerFile(profile: string, file: File): Promise<CareerImportPreview> {
  const form = new FormData();
  form.append('file', file);
  return apiPostForm<CareerImportPreview>(careerPath(profile, '/import'), form);
}

export function importCareerText(profile: string, text: string): Promise<CareerImportPreview> {
  return apiPost<CareerImportPreview>(careerPath(profile, '/import/text'), { text });
}

export function previewCareer(
  profile: string,
  body: { resume?: ResumeDoc; markdown?: string; include_photo?: boolean },
): Promise<CareerPreviewResponse> {
  return apiPost<CareerPreviewResponse>(careerPath(profile, '/preview'), body);
}

export function createCareerDraft(
  profile: string,
  body: { target: string; markdown: string; jd_text?: string; notes?: string; overwrite?: boolean },
): Promise<CareerDraft> {
  return apiPost<CareerDraft>(careerPath(profile, '/drafts'), body);
}

export function updateCareerDraft(
  profile: string,
  draftId: string,
  body: { markdown?: string; jd_text?: string; notes?: string; analysis?: unknown },
  etag: string,
  autosave = false,
): Promise<CareerDraft> {
  return apiPut<CareerDraft>(
    careerPath(profile, `/drafts/${encodeURIComponent(draftId)}${autosave ? '?autosave=1' : ''}`),
    body,
    { headers: ifMatch(etag) },
  );
}

export function deleteCareerDraft(profile: string, draftId: string): Promise<unknown> {
  return apiDelete(careerPath(profile, `/drafts/${encodeURIComponent(draftId)}`));
}

/**
 * Download md / html / pdf. Rendering happens server-side in memory; the
 * browser receives the file as an attachment (nothing is written).
 */
export async function downloadCareerExport(
  profile: string,
  body: { format: 'md' | 'html' | 'pdf'; draft_id?: string; markdown?: string; include_photo?: boolean },
): Promise<void> {
  const res = await fetch(`${apiBase()}${careerPath(profile, '/export')}`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let message = `导出失败（${res.status}）`;
    try {
      const data = (await res.json()) as { message?: string };
      if (data.message) message = data.message;
    } catch {
      // keep the status message
    }
    throw new Error(message);
  }
  const disposition = res.headers.get('Content-Disposition') ?? '';
  const match = /filename\*=UTF-8''([^;]+)/i.exec(disposition);
  const filename = match ? decodeURIComponent(match[1]) : `resume.${body.format}`;
  const url = URL.createObjectURL(await res.blob());
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
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

function publicSiteBase(profile: string): string {
  return `/profiles/${encodeURIComponent(profile)}/public-site`;
}

/** Public-site console overview: switches, intro, posts, works, live diff. */
export function usePublicSite(profile: string) {
  return useQuery({
    queryKey: ['profiles', profile, 'public-site'],
    queryFn: () => apiGet<PublicSiteResponse>(publicSiteBase(profile)),
    enabled: profile.length > 0,
  });
}

/** Preview page list; `includeDrafts` false = exactly what would go live. */
export function usePublicSitePreview(profile: string, includeDrafts: boolean) {
  return useQuery({
    queryKey: ['profiles', profile, 'public-site', 'preview', includeDrafts],
    queryFn: () => {
      const params = new URLSearchParams({ include_drafts: includeDrafts ? '1' : '0' });
      return apiGet<PublicBuildPreviewResponse>(`${publicSiteBase(profile)}/preview?${params}`);
    },
    enabled: profile.length > 0,
  });
}

/** Mutations answer the fresh overview; write it into the cache directly. */
function usePublicSiteMutation<TVars>(profile: string, run: (vars: TVars) => Promise<PublicSiteResponse>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: run,
    onSuccess: (data) => {
      queryClient.setQueryData(['profiles', profile, 'public-site'], data);
      queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'public-site', 'preview'] });
      // Post toggles change blog statuses shown in the content workspace.
      queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'content'] });
    },
  });
}

export function useUpdatePublicSiteSettings(profile: string) {
  return usePublicSiteMutation(profile, (body: PublicSiteSettingsUpdate) =>
    apiPatch<PublicSiteResponse>(`${publicSiteBase(profile)}/settings`, body),
  );
}

export function useSetPublicSitePost(profile: string) {
  return usePublicSiteMutation(profile, ({ slug, isPublic }: { slug: string; isPublic: boolean }) =>
    apiPut<PublicSiteResponse>(
      `${publicSiteBase(profile)}/posts/${slug.split('/').map(encodeURIComponent).join('/')}`,
      { public: isPublic },
    ),
  );
}

export function useSavePublicSiteWorks(profile: string) {
  return usePublicSiteMutation(profile, ({ works, etag }: { works: PublicSiteWork[]; etag: string }) =>
    apiPut<PublicSiteResponse>(`${publicSiteBase(profile)}/works`, { works }, { headers: ifMatch(etag) }),
  );
}

export function uploadPublicSiteWorkMedia(profile: string, file: File): Promise<PublicSiteMediaResponse> {
  const form = new FormData();
  form.append('file', file);
  return apiPostForm<PublicSiteMediaResponse>(`${publicSiteBase(profile)}/works/media`, form);
}

function usePublicSiteLiveMutation(profile: string, action: 'deploy' | 'rollback') {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiPost<PublicSiteDeployResponse>(`${publicSiteBase(profile)}/${action}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'public-site'] }),
  });
}

/** Build published content straight into the live site (previous build kept). */
export function useDeployPublicSite(profile: string) {
  return usePublicSiteLiveMutation(profile, 'deploy');
}

export function useRollbackPublicSite(profile: string) {
  return usePublicSiteLiveMutation(profile, 'rollback');
}

/** Same-origin URL of one self-contained preview page (iframe src). */
export function publicSitePreviewPageUrl(profile: string, path: string, includeDrafts: boolean): string {
  const params = new URLSearchParams({
    path,
    include_drafts: includeDrafts ? '1' : '0',
  });
  return `/api/v1${publicSiteBase(profile)}/preview/page?${params}`;
}

/** Same-origin URL of a profile media file (``media/...``) for thumbnails. */
export function profileMediaUrl(profile: string, rel: string): string {
  const encoded = rel.replace(/^\/+/, '').split('/').map(encodeURIComponent).join('/');
  return `/api/v1/profiles/${encodeURIComponent(profile)}/content/media-file/${encoded}`;
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

export function useResearchReader(profile: string, sourceId: string) {
  return useQuery({
    queryKey: ['profiles', profile, 'research', 'papers', sourceId, 'reader'],
    queryFn: () => apiGet<ResearchReaderResponse>(`/profiles/${encodeURIComponent(profile)}/research/papers/${encodeURIComponent(sourceId)}/reader`),
    enabled: profile.length > 0 && sourceId.length > 0,
  });
}
