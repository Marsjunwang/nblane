import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { jsonResponse } from '../test/render';
import { MINI_EXCEPTIONS_POLL_MS } from '../pages/MiniPage';
import { AI_EXCEPTIONS_POLL_MS, useAIExceptions } from './hooks';

function Probe({ pollMs }: { pollMs?: number }) {
  useAIExceptions('alice', pollMs);
  return null;
}

function pollOf(client: QueryClient): unknown {
  return client.getQueryCache().find({ queryKey: ['profiles', 'alice', 'ai-exceptions'] })?.observers[0]?.options
    .refetchInterval;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('useAIExceptions poll interval', () => {
  it('keeps the 30s default for the main window and 2 minutes for the 小窗', () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse(200, { profile: 'alice', total: 0, items: [] })));
    const main = new QueryClient();
    render(
      <QueryClientProvider client={main}>
        <Probe />
      </QueryClientProvider>,
    );
    expect(pollOf(main)).toBe(AI_EXCEPTIONS_POLL_MS);
    expect(AI_EXCEPTIONS_POLL_MS).toBe(30_000);

    const mini = new QueryClient();
    render(
      <QueryClientProvider client={mini}>
        <Probe pollMs={MINI_EXCEPTIONS_POLL_MS} />
      </QueryClientProvider>,
    );
    expect(pollOf(mini)).toBe(120_000);
  });
});
