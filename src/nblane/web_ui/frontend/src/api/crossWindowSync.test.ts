import { QueryClient } from '@tanstack/react-query';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { SYNC_CHANNEL, installCrossWindowSync, isDailyWorkQuery } from './crossWindowSync';

const cleanups: Array<() => void> = [];
afterEach(() => {
  cleanups.splice(0).forEach((fn) => fn());
});

describe('crossWindowSync', () => {
  it('only targets daily-work queries', () => {
    expect(isDailyWorkQuery({ queryKey: ['profiles', 'alice', 'kanban'] })).toBe(true);
    expect(isDailyWorkQuery({ queryKey: ['profiles', 'alice', 'habit-plans', {}] })).toBe(true);
    expect(isDailyWorkQuery({ queryKey: ['profiles', 'alice', 'content', 'images'] })).toBe(false);
    expect(isDailyWorkQuery({ queryKey: ['me'] })).toBe(false);
  });

  it('announces a successful mutation and refetches on a peer message', async () => {
    const client = new QueryClient();
    const invalidate = vi.spyOn(client, 'invalidateQueries');
    cleanups.push(installCrossWindowSync(client));
    const peer = new BroadcastChannel(SYNC_CHANNEL);
    cleanups.push(() => peer.close());
    const heard = new Promise<unknown>((resolve) => {
      peer.onmessage = (event) => resolve(event.data);
    });

    await client.getMutationCache().build(client, { mutationFn: async () => 'ok' }).execute(undefined);
    await expect(heard).resolves.toEqual({ type: 'changed' });

    peer.postMessage({ type: 'changed' });
    await vi.waitFor(() => expect(invalidate).toHaveBeenCalledWith({ predicate: isDailyWorkQuery }));
  });
});
