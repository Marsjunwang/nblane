// Run one content-AI job (POST .../jobs) and resolve with its result.
//
// The content AI kinds (content-rewrite / content-meta / content-cover) are
// long LLM or image calls, so they go through the shared async-job registry
// and its SSE stream instead of a blocking request.
//
// A dropped stream (phone backgrounded, flaky network) is not a failed job:
// the server keeps running it, so we poll GET .../jobs/{id} and re-subscribe
// with backoff instead of reporting 「连接中断」 and losing a 30-90s result.
// cancel() also asks the server to end the job (DELETE .../jobs/{id}) so a
// cancelled run is not applied or kept billing in the background.

import { ApiError, apiDelete, apiGet, apiPost } from '../../api/client';
import { streamJob } from '../../api/jobs';
import type { JobCreateResponse, JobStatusResponse } from '../../api/types';

export type ContentJobKind =
  | 'content-rewrite'
  | 'content-meta'
  | 'content-cover'
  | 'content-social'
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

/** Reconnect delays after a dropped stream (ms); the last one repeats. */
export const RECONNECT_DELAYS_MS = [1000, 2000, 4000, 8000];
/** Give up re-attaching after this long without reaching the server. */
export const RECONNECT_GIVE_UP_MS = 120_000;

const DISCONNECTED_MESSAGE = '与服务器的连接中断，任务可能仍在后台运行，请稍后重试。';

export function runContentJob<T>(
  profile: string,
  kind: ContentJobKind,
  input: Record<string, unknown>,
  onProgress?: (message: string) => void,
): ContentJobHandle<T> {
  const base = `/profiles/${encodeURIComponent(profile)}/jobs`;
  let unsubscribe: (() => void) | null = null;
  let timer: ReturnType<typeof setTimeout> | null = null;
  let jobId = '';
  let settled = false;
  let cancelled = false;

  const result = new Promise<T>((resolve, reject) => {
    const finish = (fn: () => void) => {
      if (settled || cancelled) return;
      settled = true;
      if (timer) clearTimeout(timer);
      unsubscribe?.();
      fn();
    };
    const fail = (code: string, message: string) => finish(() => reject(new ContentJobError(code, message)));

    let attempt = 0;
    let lostAt = 0;

    const reconnect = () => {
      if (settled || cancelled) return;
      if (!lostAt) lostAt = Date.now();
      if (Date.now() - lostAt > RECONNECT_GIVE_UP_MS) {
        fail('job_stream_error', DISCONNECTED_MESSAGE);
        return;
      }
      const delay = RECONNECT_DELAYS_MS[Math.min(attempt, RECONNECT_DELAYS_MS.length - 1)];
      attempt += 1;
      timer = setTimeout(() => {
        timer = null;
        // Ask the server before re-subscribing: the job may have finished
        // while we were offline, or may be gone (process restart / GC).
        apiGet<JobStatusResponse>(`${base}/${encodeURIComponent(jobId)}`)
          .then((status) => {
            if (settled || cancelled) return;
            if (status.job.status === 'done') {
              finish(() => resolve((status.result ?? {}) as T));
            } else if (status.job.status === 'failed') {
              const error = status.job.error;
              fail(error?.code ?? 'job_failed', error?.message ?? 'AI 任务失败，请重试。');
            } else {
              subscribe();
            }
          })
          .catch((error: unknown) => {
            if (error instanceof ApiError && error.status === 404) {
              fail('job_not_found', '任务已不存在（服务可能重启过），请重试。');
            } else if (error instanceof ApiError && error.status === 401) {
              fail('unauthorized', '登录已过期，请重新登录后重试。');
            } else {
              reconnect();
            }
          });
      }, delay);
    };

    const subscribe = () => {
      unsubscribe?.();
      unsubscribe = streamJob(profile, jobId, {
        onJob: () => {
          attempt = 0;
          lostAt = 0;
        },
        onProgress: (frame) => {
          if (frame.event?.message) onProgress?.(frame.event.message);
        },
        onDone: (frame) => finish(() => resolve((frame.result ?? {}) as T)),
        onError: (frame) => {
          const error = frame?.error ?? frame?.job?.error;
          if (error) {
            fail(error.code ?? 'job_failed', error.message ?? 'AI 任务失败，请重试。');
          } else {
            // Transport error without a server frame: re-attach, don't fail.
            reconnect();
          }
        },
      });
    };

    apiPost<JobCreateResponse>(base, { kind, input })
      .then((created) => {
        jobId = created.job_id;
        if (cancelled) {
          void apiDelete(`${base}/${encodeURIComponent(jobId)}`).catch(() => undefined);
          return;
        }
        subscribe();
      })
      .catch((error: unknown) => finish(() => reject(error)));
  });

  return {
    result,
    cancel: () => {
      if (cancelled || settled) return;
      cancelled = true;
      if (timer) clearTimeout(timer);
      unsubscribe?.();
      if (jobId) void apiDelete(`${base}/${encodeURIComponent(jobId)}`).catch(() => undefined);
    },
  };
}
