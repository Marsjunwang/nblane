// Run one content-AI job (POST .../jobs) and resolve with its result.
//
// The content AI kinds (content-rewrite / content-meta / content-cover) are
// long LLM or image calls, so they go through the shared async-job registry
// and its SSE stream instead of a blocking request. The returned handle can
// cancel the subscription (the server-side job keeps running and is GC'd).

import { apiPost } from '../../api/client';
import { streamJob } from '../../api/jobs';
import type { JobCreateResponse } from '../../api/types';

export type ContentJobKind =
  | 'content-rewrite'
  | 'content-meta'
  | 'content-cover'
  // Career workspace kinds share the same runner.
  | 'career-match'
  | 'career-tailor'
  | 'career-structure';

export interface ContentJobHandle<T> {
  result: Promise<T>;
  cancel: () => void;
}

export class ContentJobError extends Error {
  readonly code: string;

  constructor(code: string, message: string) {
    super(message);
    this.name = 'ContentJobError';
    this.code = code;
  }
}

export function runContentJob<T>(
  profile: string,
  kind: ContentJobKind,
  input: Record<string, unknown>,
  onProgress?: (message: string) => void,
): ContentJobHandle<T> {
  let unsubscribe: (() => void) | null = null;
  let cancelled = false;
  const result = new Promise<T>((resolve, reject) => {
    apiPost<JobCreateResponse>(`/profiles/${encodeURIComponent(profile)}/jobs`, { kind, input })
      .then((created) => {
        if (cancelled) return;
        unsubscribe = streamJob(profile, created.job_id, {
          onProgress: (frame) => {
            if (frame.event?.message) onProgress?.(frame.event.message);
          },
          onDone: (frame) => resolve((frame.result ?? {}) as T),
          onError: (frame) => {
            const error = frame?.error ?? frame?.job?.error;
            reject(
              new ContentJobError(
                error?.code ?? 'job_stream_error',
                error?.message ?? 'AI 任务连接中断，请重试。',
              ),
            );
          },
        });
      })
      .catch(reject);
  });
  return {
    result,
    cancel: () => {
      cancelled = true;
      unsubscribe?.();
    },
  };
}
