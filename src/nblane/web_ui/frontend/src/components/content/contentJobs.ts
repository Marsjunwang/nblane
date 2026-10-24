// Follow async jobs (GET .../jobs/{id}/stream) robustly, and run content-AI
// jobs on top of that.
//
// followJob: a dropped stream (phone backgrounded, flaky network) is not a
// failed job — the server keeps running it, so we poll GET .../jobs/{id} and
// re-subscribe with backoff instead of reporting 「连接中断」 and losing the
// result. cancel() requests a stop (DELETE), waits for the server's actual
// terminal state, and forwards stopping / retained-partial-write messages;
// detach() only stops listening, for jobs whose result the server persists
// and a later visit can re-attach to.
//
// runContentJob: POST .../jobs, then followJob.

import { ApiError, apiDelete, apiGet, apiPost } from '../../api/client';
import { streamJob } from '../../api/jobs';
import type { JobCreateResponse, JobModel, JobStatusResponse } from '../../api/types';

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
  cancel: () => void | Promise<void>;
}

export interface FollowedJob<T> extends ContentJobHandle<T> {
  /** Stop listening without ending the server-side job. */
  detach: () => void;
}

export interface FollowJobHandlers {
  /** One call per progress event (message may be empty, phase may not). */
  onProgress?: (message: string, phase: string) => void;
  /** Initial job snapshot from the stream (also on every reconnect). */
  onSnapshot?: (job: JobModel) => void;
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

const jobsBase = (profile: string) => `/profiles/${encodeURIComponent(profile)}/jobs`;

type JobLifecycleModel = JobModel & {
  cancel_requested?: boolean;
  write_committed?: boolean;
  commit_summary?: string;
};

function lifecycleMessage(job: JobLifecycleModel, fallback: string): string {
  const message = job.message || fallback;
  if (!job.write_committed || message.includes('部分写入')) return message;
  return `${message} 已有部分写入：${job.commit_summary || '已完成的提交段'}。`;
}

/** Follow an existing job until it is done or failed. */
export function followJob<T>(profile: string, jobId: string, handlers: FollowJobHandlers = {}): FollowedJob<T> {
  const base = jobsBase(profile);
  let unsubscribe: (() => void) | null = null;
  let timer: ReturnType<typeof setTimeout> | null = null;
  let settled = false;
  let stopped = false;
  let subscribe = () => undefined;
  let settleFromStatus = (_status: JobStatusResponse) => undefined;

  const stop = () => {
    stopped = true;
    if (timer) clearTimeout(timer);
    unsubscribe?.();
  };

  const result = new Promise<T>((resolve, reject) => {
    const finish = (fn: () => void) => {
      if (settled || stopped) return;
      settled = true;
      if (timer) clearTimeout(timer);
      unsubscribe?.();
      fn();
    };
    const fail = (code: string, message: string) => {
      if (code === 'job_cancelled' || code === 'job_timeout' || message.includes('部分写入')) {
        handlers.onProgress?.(message, 'failed');
      }
      finish(() => reject(new ContentJobError(code, message)));
    };

    let attempt = 0;
    let lostAt = 0;

    settleFromStatus = (status: JobStatusResponse) => {
      if (settled || stopped) return;
      const job = status.job as JobLifecycleModel;
      handlers.onSnapshot?.(job);
      if (job.status === 'done') {
        finish(() => resolve((status.result ?? {}) as T));
      } else if (job.status === 'failed') {
        const error = job.error;
        fail(error?.code ?? 'job_failed', error?.message ?? 'AI 任务失败，请重试。');
      } else if (job.cancel_requested || job.write_committed) {
        handlers.onProgress?.(lifecycleMessage(job, '正在停止…'), job.phase || 'cancelling');
      }
    };

    const reconnect = () => {
      if (settled || stopped) return;
      if (!lostAt) lostAt = Date.now();
      if (Date.now() - lostAt > RECONNECT_GIVE_UP_MS) {
        fail('job_stream_error', DISCONNECTED_MESSAGE);
        return;
      }
      const delay = RECONNECT_DELAYS_MS[Math.min(attempt, RECONNECT_DELAYS_MS.length - 1)];
      attempt += 1;
      timer = setTimeout(() => {
        timer = null;
        apiGet<JobStatusResponse>(`${base}/${encodeURIComponent(jobId)}`)
          .then((status) => {
            if (settled || stopped) return;
            settleFromStatus(status);
            if (!settled && !stopped) subscribe();
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

    subscribe = () => {
      if (settled || stopped) return;
      unsubscribe?.();
      unsubscribe = streamJob(profile, jobId, {
        onJob: (frame) => {
          attempt = 0;
          lostAt = 0;
          if (frame.job) handlers.onSnapshot?.(frame.job);
        },
        onProgress: (frame) => {
          const message = frame.event?.message ?? '';
          const phase = frame.event?.phase ?? frame.job?.phase ?? '';
          if (message || phase) handlers.onProgress?.(message, phase);
        },
        onDone: (frame) => finish(() => resolve((frame.result ?? {}) as T)),
        onError: (frame) => {
          const error = frame?.error ?? frame?.job?.error;
          if (error) {
            fail(error.code ?? 'job_failed', error.message ?? 'AI 任务失败，请重试。');
          } else {
            reconnect();
          }
        },
      });
    };

    subscribe();
  });

  let cancelPromise: Promise<void> | null = null;
  const cancel = (): Promise<void> => {
    if (cancelPromise) return cancelPromise;
    if (settled || stopped) return Promise.resolve();
    cancelPromise = (async () => {
      try {
        const status = await apiDelete<JobStatusResponse>(`${base}/${encodeURIComponent(jobId)}`);
        settleFromStatus(status);
        if (!settled && !stopped) subscribe();
      } catch (error: unknown) {
        if (error instanceof ApiError && error.status === 404) {
          settleFromStatus({
            ok: false,
            job: {
              job_id: jobId,
              status: 'failed',
              error: { code: 'job_not_found', message: '任务已不存在（服务可能重启过），请重试。' },
            },
          } as JobStatusResponse);
        } else {
          handlers.onProgress?.('取消请求失败，任务可能仍在运行；继续等待服务端状态。', 'cancelling');
          if (!settled && !stopped) subscribe();
        }
      }
      await result.then(() => undefined, () => undefined);
    })();
    return cancelPromise;
  };

  return {
    result,
    detach: () => {
      if (settled || stopped) return;
      stop();
    },
    cancel,
  };
}

export function runContentJob<T>(
  profile: string,
  kind: ContentJobKind,
  input: Record<string, unknown>,
  onProgress?: (message: string) => void,
): ContentJobHandle<T> {
  let cancelled = false;
  const ready = apiPost<JobCreateResponse>(jobsBase(profile), { kind, input }).then((created) =>
    followJob<T>(profile, created.job_id, {
      onProgress: (message) => {
        if (message) onProgress?.(message);
      },
    }),
  );
  const result = ready.then(async (followed) => {
    if (cancelled) await followed.cancel();
    return followed.result;
  });

  return {
    result,
    cancel: () => {
      cancelled = true;
      return ready.then((followed) => followed.cancel()).then(() => undefined, () => undefined);
    },
  };
}
