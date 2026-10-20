import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { jsonResponse } from '../../test/render';
import { ContentJobError, RECONNECT_GIVE_UP_MS, followJob, runContentJob } from './contentJobs';

type Listener = (event: Event) => void;

/** Minimal EventSource stand-in for jsdom (which has no EventSource). */
class MockEventSource {
  static instances: MockEventSource[] = [];
  readonly url: string;
  closed = false;
  private listeners = new Map<string, Listener[]>();

  constructor(url: string) {
    this.url = url;
    MockEventSource.instances.push(this);
  }

  addEventListener(type: string, listener: Listener) {
    this.listeners.set(type, [...(this.listeners.get(type) ?? []), listener]);
  }

  close() {
    this.closed = true;
  }

  emit(type: string, data?: unknown) {
    const event = data === undefined ? new Event(type) : new MessageEvent(type, { data: JSON.stringify(data) });
    for (const listener of this.listeners.get(type) ?? []) listener(event);
  }
}

type Call = { url: string; method: string };

function mockFetch(statusReplies: Array<() => Response>) {
  const calls: Call[] = [];
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const method = init?.method ?? 'GET';
      calls.push({ url, method });
      if (method === 'POST') return jsonResponse(202, { job_id: 'job-1', job: { job_id: 'job-1', status: 'queued' } });
      if (method === 'DELETE') return jsonResponse(200, { job: { job_id: 'job-1', status: 'failed' }, result: null });
      const reply = statusReplies.shift();
      return reply ? reply() : jsonResponse(200, { job: { job_id: 'job-1', status: 'running' }, result: null });
    }),
  );
  return calls;
}

const flush = async () => {
  for (let i = 0; i < 5; i += 1) await Promise.resolve();
};

beforeEach(() => {
  vi.useFakeTimers();
  MockEventSource.instances = [];
  vi.stubGlobal('EventSource', MockEventSource);
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe('runContentJob', () => {
  it('resolves with the done frame result', async () => {
    mockFetch([]);
    const job = runContentJob<{ text: string }>('alice', 'content-rewrite', { selection: 'x' });
    await flush();
    MockEventSource.instances[0].emit('done', { ok: true, result: { text: '新文' } });
    await expect(job.result).resolves.toEqual({ text: '新文' });
  });

  it('rejects with the server error frame (a real job failure)', async () => {
    mockFetch([]);
    const job = runContentJob('alice', 'content-meta', {});
    await flush();
    MockEventSource.instances[0].emit('error', { ok: false, error: { code: 'content_ai_failed', message: '模型失败' } });
    await expect(job.result).rejects.toMatchObject({ code: 'content_ai_failed', message: '模型失败' });
  });

  it('a dropped stream polls status and picks up a result finished offline', async () => {
    const calls = mockFetch([() => jsonResponse(200, { job: { job_id: 'job-1', status: 'done' }, result: { text: '离线完成' } })]);
    const job = runContentJob<{ text: string }>('alice', 'content-rewrite', {});
    await flush();
    MockEventSource.instances[0].emit('error');
    await vi.advanceTimersByTimeAsync(1000);
    await expect(job.result).resolves.toEqual({ text: '离线完成' });
    expect(calls.some((call) => call.method === 'GET' && call.url.endsWith('/jobs/job-1'))).toBe(true);
  });

  it('a dropped stream re-subscribes while the job is still running', async () => {
    mockFetch([]);
    const job = runContentJob<{ text: string }>('alice', 'content-rewrite', {});
    await flush();
    MockEventSource.instances[0].emit('error');
    await vi.advanceTimersByTimeAsync(1000);
    expect(MockEventSource.instances).toHaveLength(2);
    MockEventSource.instances[1].emit('done', { ok: true, result: { text: '重连后完成' } });
    await expect(job.result).resolves.toEqual({ text: '重连后完成' });
  });

  it('a job gone from the server (404) fails with a clear message', async () => {
    mockFetch([() => jsonResponse(404, { code: 'job_not_found', message: 'Unknown job' })]);
    const job = runContentJob('alice', 'content-social', {});
    const outcome = job.result.catch((error: unknown) => error);
    await flush();
    MockEventSource.instances[0].emit('error');
    await vi.advanceTimersByTimeAsync(1000);
    const error = await outcome;
    expect(error).toBeInstanceOf(ContentJobError);
    expect((error as ContentJobError).code).toBe('job_not_found');
  });

  it('gives up after the reconnect window when the server stays unreachable', async () => {
    vi.stubGlobal('fetch', vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
      if ((init?.method ?? 'GET') === 'POST') return jsonResponse(202, { job_id: 'job-1', job: { job_id: 'job-1', status: 'queued' } });
      throw new TypeError('network down');
    }));
    const job = runContentJob('alice', 'content-rewrite', {});
    const outcome = job.result.catch((error: unknown) => error);
    await flush();
    MockEventSource.instances[0].emit('error');
    await vi.advanceTimersByTimeAsync(RECONNECT_GIVE_UP_MS + 10_000);
    expect((await outcome as ContentJobError).code).toBe('job_stream_error');
  });

  it('cancel closes the stream and asks the server to end the job', async () => {
    const calls = mockFetch([]);
    const job = runContentJob('alice', 'content-rewrite', {});
    await flush();
    job.cancel();
    await flush();
    expect(MockEventSource.instances[0].closed).toBe(true);
    expect(calls.some((call) => call.method === 'DELETE' && call.url.endsWith('/jobs/job-1'))).toBe(true);
  });

  it('cancel before the job is created still deletes it once the id arrives', async () => {
    const calls = mockFetch([]);
    const job = runContentJob('alice', 'content-rewrite', {});
    job.cancel();
    await flush();
    expect(MockEventSource.instances).toHaveLength(0);
    expect(calls.some((call) => call.method === 'DELETE')).toBe(true);
  });
});

describe('followJob', () => {
  it('follows an existing job and reports message and phase', async () => {
    const calls = mockFetch([]);
    const onProgress = vi.fn();
    const job = followJob<{ ok: boolean }>('alice', 'job-9', { onProgress });
    expect(MockEventSource.instances[0].url).toContain('/jobs/job-9/stream');
    MockEventSource.instances[0].emit('progress', { ok: true, event: { message: '正在分析', phase: 'suggesting' } });
    expect(onProgress).toHaveBeenCalledWith('正在分析', 'suggesting');
    MockEventSource.instances[0].emit('done', { ok: true, result: { ok: true } });
    await expect(job.result).resolves.toEqual({ ok: true });
    expect(calls.some((call) => call.method === 'POST')).toBe(false);
  });

  it('detach stops listening without deleting the server job', async () => {
    const calls = mockFetch([]);
    const job = followJob('alice', 'job-9');
    job.detach();
    await flush();
    expect(MockEventSource.instances[0].closed).toBe(true);
    expect(calls.some((call) => call.method === 'DELETE')).toBe(false);
  });

  it('cancel deletes the server job', async () => {
    const calls = mockFetch([]);
    const job = followJob('alice', 'job-9');
    job.cancel();
    await flush();
    expect(calls.some((call) => call.method === 'DELETE' && call.url.endsWith('/jobs/job-9'))).toBe(true);
  });

  it('re-attaches after a dropped stream like runContentJob', async () => {
    mockFetch([() => jsonResponse(200, { job: { job_id: 'job-9', status: 'done' }, result: { text: '离线完成' } })]);
    const job = followJob<{ text: string }>('alice', 'job-9');
    MockEventSource.instances[0].emit('error');
    await vi.advanceTimersByTimeAsync(1000);
    await expect(job.result).resolves.toEqual({ text: '离线完成' });
  });
});
