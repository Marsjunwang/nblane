import { act, renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { ContentJobHandle } from './contentJobs';
import { combineJobs, useContentJob } from './useContentJob';

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

function handle<T>() {
  const d = deferred<T>();
  const cancel = vi.fn();
  return { job: { result: d.promise, cancel } as ContentJobHandle<T>, ...d, cancel };
}

describe('useContentJob', () => {
  it('tracks running and progress, then resolves done', async () => {
    const { result } = renderHook(() => useContentJob<string>());
    const h = handle<string>();
    let report!: (message: string) => void;
    let outcome!: Promise<unknown>;
    act(() => {
      outcome = result.current.start((onProgress) => {
        report = onProgress;
        return h.job;
      });
    });
    expect(result.current.running).toBe(true);
    act(() => report('正在改写'));
    expect(result.current.progress).toBe('正在改写');
    await act(async () => h.resolve('ok'));
    await expect(outcome).resolves.toEqual({ status: 'done', value: 'ok' });
    expect(result.current.running).toBe(false);
    expect(result.current.progress).toBe('');
  });

  it('a newer start cancels the old job and the old result is stale', async () => {
    const { result } = renderHook(() => useContentJob<string>());
    const first = handle<string>();
    const second = handle<string>();
    let a!: Promise<unknown>;
    let b!: Promise<unknown>;
    act(() => {
      a = result.current.start(() => first.job);
    });
    act(() => {
      b = result.current.start(() => second.job);
    });
    expect(first.cancel).toHaveBeenCalled();
    await act(async () => first.resolve('old'));
    await expect(a).resolves.toEqual({ status: 'stale' });
    expect(result.current.running).toBe(true);
    await act(async () => second.resolve('new'));
    await expect(b).resolves.toEqual({ status: 'done', value: 'new' });
  });

  it('records the error message', async () => {
    const { result } = renderHook(() => useContentJob<string>());
    const h = handle<string>();
    let outcome!: Promise<unknown>;
    act(() => {
      outcome = result.current.start(() => h.job);
    });
    await act(async () => h.reject(new Error('模型失败')));
    await expect(outcome).resolves.toEqual({ status: 'error', error: '模型失败' });
    expect(result.current.error).toBe('模型失败');
  });

  it('cancels the running job on unmount', () => {
    const { result, unmount } = renderHook(() => useContentJob<string>());
    const h = handle<string>();
    act(() => {
      void result.current.start(() => h.job);
    });
    unmount();
    expect(h.cancel).toHaveBeenCalled();
  });

  it('cancel() stops the job and drops its result', async () => {
    const { result } = renderHook(() => useContentJob<string>());
    const h = handle<string>();
    let outcome!: Promise<unknown>;
    act(() => {
      outcome = result.current.start(() => h.job);
    });
    act(() => result.current.cancel());
    expect(h.cancel).toHaveBeenCalled();
    expect(result.current.running).toBe(false);
    await act(async () => h.resolve('late'));
    await expect(outcome).resolves.toEqual({ status: 'stale' });
  });
});

describe('combineJobs', () => {
  it('cancels the remaining jobs when one fails', async () => {
    const a = handle<string>();
    const b = handle<string>();
    const combined = combineJobs([a.job, b.job]);
    a.reject(new Error('区域 1 失败'));
    await expect(combined.result).rejects.toThrow('区域 1 失败');
    expect(b.cancel).toHaveBeenCalled();
  });

  it('resolves all results in order', async () => {
    const a = handle<string>();
    const b = handle<string>();
    const combined = combineJobs([a.job, b.job]);
    b.resolve('二');
    a.resolve('一');
    await expect(combined.result).resolves.toEqual(['一', '二']);
  });
});
