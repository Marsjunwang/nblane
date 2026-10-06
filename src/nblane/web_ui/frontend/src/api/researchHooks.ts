// Research source intake hooks (SPA research desk: 来源收件箱 / 连接器 / 研究 AI).
//
// Backend: src/nblane/web_api/research.py. Types alias the generated
// schema.d.ts (kept local to this module so api/types.ts stays untouched).

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiGetWithHeaders, apiPatch, apiPost, apiPut, apiGet, ifMatch } from './client';
import type { components } from './schema';
import type { JobCreateResponse } from './types';

type Schemas = components['schemas'];

export type ResearchSourceDetail = Schemas['ResearchSourceDetailModel'];
export type ResearchSourcesResponse = Schemas['ResearchSourcesResponse'];
export type ResearchSourceCreateRequest = Schemas['ResearchSourceCreateRequest'];
export type ResearchSourcePatchRequest = Schemas['ResearchSourcePatchRequest'];
export type ResearchSourceMutationResponse = Schemas['ResearchSourceMutationResponse'];
export type ResearchSourceTaskResponse = Schemas['ResearchSourceTaskResponse'];
export type ResearchConnector = Schemas['ResearchConnectorModel'];
export type ResearchConnectorsResponse = Schemas['ResearchConnectorsResponse'];
export type ResearchConnectorUpsertRequest = Schemas['ResearchConnectorUpsertRequest'];
export type ResearchConnectorPreview = Schemas['ResearchConnectorPreviewModel'];
export type ResearchConnectorCandidate = Schemas['ResearchConnectorCandidateModel'];
export type ResearchConnectorImportResult = Schemas['ResearchConnectorImportResultModel'];
export type ResearchImportTarget = Schemas['ResearchImportTargetModel'];
export type ResearchManualPreviewRequest = Schemas['ResearchManualPreviewRequest'];
export type ResearchManualImportRequest = Schemas['ResearchManualImportRequest'];
export type ResearchAIAction = Schemas['ResearchAIActionModel'];
export type ResearchAIConfig = Schemas['ResearchAIConfigResponse'];
export type ResearchAIConfigUpdate = Schemas['ResearchAIConfigUpdateRequest'];

/** Source list plus the file-level ETag (rows carry their own `etag`). */
export interface ResearchSourcesResult {
  data: ResearchSourcesResponse;
  etag: string;
}

function researchBase(profile: string): string {
  return `/profiles/${encodeURIComponent(profile)}/research`;
}

const sourcesKey = (profile: string) => ['profiles', profile, 'research', 'sources'] as const;
const connectorsKey = (profile: string) => ['profiles', profile, 'research', 'connectors'] as const;
const aiConfigKey = (profile: string) => ['profiles', profile, 'research', 'ai-config'] as const;

/** Invalidate everything research-scoped (sources list + desk overview). */
function useInvalidateResearch(profile: string) {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'research'] });
}

export function useResearchSources(
  profile: string,
  filters: { status?: string; kind?: string; q?: string } = {},
) {
  const status = filters.status ?? '';
  const kind = filters.kind ?? '';
  const q = filters.q ?? '';
  return useQuery({
    queryKey: [...sourcesKey(profile), { status, kind, q }],
    queryFn: async (): Promise<ResearchSourcesResult> => {
      const params = new URLSearchParams();
      if (status) params.set('status', status);
      if (kind) params.set('kind', kind);
      if (q) params.set('q', q);
      const query = params.toString();
      const { data, headers } = await apiGetWithHeaders<ResearchSourcesResponse>(
        `${researchBase(profile)}/sources${query ? `?${query}` : ''}`,
      );
      return { data, etag: headers.get('ETag') ?? '' };
    },
    enabled: profile.length > 0,
  });
}

export function useCreateResearchSource(profile: string) {
  const invalidate = useInvalidateResearch(profile);
  return useMutation({
    mutationFn: (body: ResearchSourceCreateRequest) =>
      apiPost<ResearchSourceMutationResponse>(`${researchBase(profile)}/sources`, body),
    onSuccess: invalidate,
  });
}

export function usePatchResearchSource(profile: string) {
  const invalidate = useInvalidateResearch(profile);
  return useMutation({
    mutationFn: ({ sourceId, body, etag }: { sourceId: string; body: ResearchSourcePatchRequest; etag: string }) =>
      apiPatch<ResearchSourceMutationResponse>(
        `${researchBase(profile)}/sources/${encodeURIComponent(sourceId)}`,
        body,
        { headers: ifMatch(etag) },
      ),
    onSuccess: invalidate,
  });
}

export function useCreateResearchSourceTask(profile: string) {
  return useMutation({
    mutationFn: (sourceId: string) =>
      apiPost<ResearchSourceTaskResponse>(
        `${researchBase(profile)}/sources/${encodeURIComponent(sourceId)}/task`,
      ),
  });
}

export function useResearchConnectors(profile: string) {
  return useQuery({
    queryKey: connectorsKey(profile),
    queryFn: () => apiGet<ResearchConnectorsResponse>(`${researchBase(profile)}/connectors`),
    enabled: profile.length > 0,
  });
}

export function useUpsertResearchConnector(profile: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: ResearchConnectorUpsertRequest) =>
      apiPut<ResearchConnectorsResponse>(`${researchBase(profile)}/connectors`, body),
    onSuccess: (value) => queryClient.setQueryData(connectorsKey(profile), value),
  });
}

/** Starts the dry-run discovery job (202); stream it with `streamJob`. */
export function usePreviewResearchConnector(profile: string) {
  return useMutation({
    mutationFn: (connectorId: string) =>
      apiPost<JobCreateResponse>(
        `${researchBase(profile)}/connectors/${encodeURIComponent(connectorId)}/preview`,
      ),
  });
}

/** Starts the import job (202); empty `fingerprints` runs the whole connector. */
export function useImportResearchConnector(profile: string) {
  return useMutation({
    mutationFn: ({ connectorId, fingerprints, target }: { connectorId: string; fingerprints: string[]; target: ResearchImportTarget }) =>
      apiPost<JobCreateResponse>(
        `${researchBase(profile)}/connectors/${encodeURIComponent(connectorId)}/import`,
        { fingerprints, target },
      ),
  });
}

export function usePreviewManualItems(profile: string) {
  return useMutation({
    mutationFn: (body: ResearchManualPreviewRequest) =>
      apiPost<ResearchConnectorPreview>(`${researchBase(profile)}/connectors/manual/preview`, body),
  });
}

export function useImportManualItems(profile: string) {
  const invalidate = useInvalidateResearch(profile);
  return useMutation({
    mutationFn: (body: ResearchManualImportRequest) =>
      apiPost<ResearchConnectorImportResult>(`${researchBase(profile)}/connectors/manual/import`, body),
    onSuccess: invalidate,
  });
}

/** Call after a connector job finishes so lists and statuses refresh. */
export function useRefreshAfterConnectorJob(profile: string) {
  return useInvalidateResearch(profile);
}

export function useResearchAIConfig(profile: string) {
  return useQuery({
    queryKey: aiConfigKey(profile),
    queryFn: () => apiGet<ResearchAIConfig>(`${researchBase(profile)}/ai-config`),
    enabled: profile.length > 0,
  });
}

export function useSaveResearchAIConfig(profile: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: ResearchAIConfigUpdate) =>
      apiPut<ResearchAIConfig>(`${researchBase(profile)}/ai-config`, body),
    onSuccess: (value) => {
      queryClient.setQueryData(aiConfigKey(profile), value);
      // The Settings page reads the same ai.actions block.
      void queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'settings'] });
    },
  });
}
