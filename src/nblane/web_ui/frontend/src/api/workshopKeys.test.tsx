import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { useWorkshopKeys } from './hooks';
import { jsonResponse } from '../test/render';

function wrapper({ children }: { children: ReactNode }) {
  const queryClient = new QueryClient();
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('useWorkshopKeys', () => {
  it('sends taps in order even when they are fired rapidly', async () => {
    const seen: string[][] = [];
    vi.stubGlobal(
      'fetch',
      vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
        seen.push(JSON.parse(String(init?.body)).keys);
        return jsonResponse(200, { ok: true });
      }),
    );
    const { result } = renderHook(() => useWorkshopKeys(), { wrapper });

    act(() => {
      result.current.mutate(['up']);
      result.current.mutate(['up']);
      result.current.mutate(['enter']);
    });
    await waitFor(() => expect(seen).toEqual([['up'], ['up'], ['enter']]));
  });

  it('times a hung request out instead of jamming every later key', async () => {
    let calls = 0;
    vi.stubGlobal(
      'fetch',
      vi.fn((_input: RequestInfo | URL, init?: RequestInit) => {
        calls += 1;
        // First send never answers until the abort signal fires; later sends
        // answer immediately.
        if (calls === 1) {
          return new Promise<Response>((_, reject) => {
            init?.signal?.addEventListener('abort', () => reject(new DOMException('timed out', 'TimeoutError')));
          });
        }
        return Promise.resolve(jsonResponse(200, { ok: true }));
      }),
    );
    vi.useFakeTimers();
    try {
      const { result } = renderHook(() => useWorkshopKeys(), { wrapper });

      const errors: Error[] = [];
      act(() => {
        result.current.mutate(['esc'], { onError: (error) => errors.push(error) });
      });
      await act(async () => {
        await vi.advanceTimersByTimeAsync(9000);
      });
      expect(errors[0]?.message).toBe('发送超时：网络没有响应，请再点一次');

      // The queue drained: the very next tap goes out normally.
      const second = result.current.mutateAsync(['enter']);
      await act(async () => {
        await vi.runAllTimersAsync();
      });
      await expect(second).resolves.toEqual({ ok: true });
    } finally {
      vi.useRealTimers();
    }
  });
});
