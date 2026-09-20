import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { ReactNode } from 'react';

import { jsonResponse } from '../test/render';
import { useGapAnalyze } from './hooks';

const ANALYSIS = {
  profile: 'alice',
  task: '部署机械臂 demo',
  can_solve: false,
  coverage: 0.4,
  learned_merged: false,
  closure: [],
  gaps: ['ros2'],
  strong: [],
  next_steps: [],
  top_matches: [],
};

function makeWrapper(client: QueryClient) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  };
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('useGapAnalyze', () => {
  it('exposes the analysis via mutation state and writes no dead cache key', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      expect(String(input)).toBe('/api/v1/profiles/alice/gap/analyze');
      expect(init?.method).toBe('POST');
      expect(JSON.parse(String(init?.body))).toEqual({
        task: '部署机械臂 demo',
        use_llm: false,
      });
      return jsonResponse(200, ANALYSIS);
    });
    vi.stubGlobal('fetch', fetchMock);

    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const { result } = renderHook(() => useGapAnalyze('alice'), {
      wrapper: makeWrapper(client),
    });

    result.current.mutate({ task: '部署机械臂 demo', use_llm: false });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // The page renders mutation.data directly.
    expect(result.current.data?.task).toBe('部署机械臂 demo');
    // No reader consumes ['profiles', name, 'gap', 'last'] — it must not be
    // written (dead cache key removed).
    expect(client.getQueryData(['profiles', 'alice', 'gap', 'last'])).toBeUndefined();
    expect(client.getQueryCache().findAll()).toHaveLength(0);
  });
});
