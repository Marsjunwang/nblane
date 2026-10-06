// Single-paper hooks: overview payload, analysis jobs, and route helpers.
//
// Backend: src/nblane/web_api/research_papers.py. Types alias the generated
// schema.d.ts locally so api/types.ts stays untouched.

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useRef, useState } from 'react';

import { apiGet, apiPost } from './client';
import { streamJob } from './jobs';
import type { components } from './schema';
import type { JobCreateResponse } from './types';

type Schemas = components['schemas'];

/**
 * Pydantic fields with defaults are optional in the OpenAPI schema, but the
 * backend always serializes them; this view makes them required so pages do
 * not need `?? []` on every nested field.
 */
type DeepRequired<T> = T extends (infer U)[]
  ? DeepRequired<U>[]
  : T extends object
    ? { [K in keyof T]-?: DeepRequired<T[K]> }
    : T;

export type PaperOverview = DeepRequired<Schemas['PaperOverviewResponse']>;
export type PaperQuickAnalysis = DeepRequired<Schemas['PaperQuickAnalysisModel']>;
export type PaperDeepRead = DeepRequired<Schemas['PaperDeepReadModel']>;
export type PaperAnalysisItem = DeepRequired<Schemas['PaperAnalysisItemModel']>;
export type PaperRef = DeepRequired<Schemas['PaperRefModel']>;
export type PaperCoverage = DeepRequired<Schemas['PaperCoverageModel']>;
export type PaperNote = DeepRequired<Schemas['PaperNoteModel']>;

export type PaperJobKind = 'paper-quick-analysis' | 'paper-deep-read';

// --- Routes ----------------------------------------------------------------

function profileBase(profile: string): string {
  return `/p/${encodeURIComponent(profile)}/research`;
}

/** SPA route of one paper's overview (the paper landing page). */
export function paperOverviewPath(profile: string, sourceId: string): string {
  return `${profileBase(profile)}/papers/${encodeURIComponent(sourceId)}`;
}

/** SPA route of the Reader for one paper, with optional page / mode. */
export function paperReaderPath(
  profile: string,
  sourceId: string,
  options: { page?: number; mode?: string } = {},
): string {
  const query = new URLSearchParams();
  if (options.mode) query.set('mode', options.mode);
  if (options.page && options.page > 0) query.set('page', String(options.page));
  const search = query.toString();
  return `${paperOverviewPath(profile, sourceId)}/read${search ? `?${search}` : ''}`;
}

export function paperLibraryPath(profile: string): string {
  return `${profileBase(profile)}/library`;
}

export function researchSourcesPath(profile: string): string {
  return `${profileBase(profile)}/sources`;
}

/** Origin a sidecar postMessage must come from ('' base = same origin). */
export function sidecarOrigin(base: string | undefined | null): string {
  if (!base) return window.location.origin;
  try {
    return new URL(base, window.location.href).origin;
  } catch {
    return window.location.origin;
  }
}

// --- Queries ---------------------------------------------------------------

export function paperOverviewKey(profile: string, sourceId: string) {
  return ['profiles', profile, 'research', 'papers', sourceId, 'overview'] as const;
}

export function usePaperOverview(profile: string, sourceId: string) {
  return useQuery({
    queryKey: paperOverviewKey(profile, sourceId),
    queryFn: () =>
      apiGet<PaperOverview>(
        `/profiles/${encodeURIComponent(profile)}/research/papers/${encodeURIComponent(sourceId)}`,
      ),
    enabled: profile.length > 0 && sourceId.length > 0,
  });
}

export function useStartPaperJob(profile: string, sourceId: string) {
  return useMutation({
    mutationFn: (kind: PaperJobKind) =>
      apiPost<JobCreateResponse>(
        `/profiles/${encodeURIComponent(profile)}/research/papers/${encodeURIComponent(sourceId)}/analysis-jobs`,
        { kind },
      ),
  });
}

// --- Job runner ------------------------------------------------------------

export interface PaperJobState {
  status: 'idle' | 'running' | 'done' | 'failed';
  message: string;
  error: { code: string; message: string } | null;
}

const IDLE: PaperJobState = { status: 'idle', message: '', error: null };

/**
 * Start / follow one analysis job kind for a paper over the job SSE stream.
 *
 * `attachJobId` re-attaches to a job the overview reports as already
 * running (page reload mid-run). On done the overview and the research desk
 * are refetched so the new result renders in place.
 */
export function usePaperJob(
  profile: string,
  sourceId: string,
  kind: PaperJobKind,
  attachJobId?: string,
) {
  const queryClient = useQueryClient();
  const start = useStartPaperJob(profile, sourceId);
  const [state, setState] = useState<PaperJobState>(IDLE);
  const stopRef = useRef<(() => void) | null>(null);
  const followedRef = useRef('');

  const follow = useCallback(
    (jobId: string) => {
      if (followedRef.current === jobId) return;
      stopRef.current?.();
      followedRef.current = jobId;
      setState({ status: 'running', message: '已开始…', error: null });
      stopRef.current = streamJob(profile, jobId, {
        onJob: (frame) => {
          if (frame.job?.message) setState((prev) => ({ ...prev, message: frame.job?.message ?? prev.message }));
        },
        onProgress: (frame) => {
          const message = frame.event?.message;
          if (message) setState((prev) => ({ ...prev, message }));
        },
        onDone: () => {
          stopRef.current = null;
          setState({ status: 'done', message: '', error: null });
          void queryClient.invalidateQueries({ queryKey: paperOverviewKey(profile, sourceId) });
          void queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'research'], exact: true });
        },
        onError: (frame) => {
          stopRef.current = null;
          const error = frame?.error ?? frame?.job?.error ?? null;
          setState({
            status: 'failed',
            message: '',
            error: error ?? { code: 'job_stream_error', message: '与任务的连接中断，请重试。' },
          });
        },
      });
    },
    [profile, sourceId, queryClient],
  );

  useEffect(() => {
    if (attachJobId) follow(attachJobId);
  }, [attachJobId, follow]);

  useEffect(
    () => () => {
      stopRef.current?.();
      stopRef.current = null;
    },
    [],
  );

  const run = useCallback(() => {
    followedRef.current = '';
    setState({ status: 'running', message: '正在创建任务…', error: null });
    start.mutate(kind, {
      onSuccess: (created) => follow(created.job_id),
      onError: (error) =>
        setState({ status: 'failed', message: '', error: { code: 'job_create_failed', message: error.message } }),
    });
  }, [follow, kind, start]);

  return { state, run };
}
