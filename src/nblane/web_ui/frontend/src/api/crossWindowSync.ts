// Keep the 小窗 and the main window in step without waiting for a poll.
//
// Both run the same app on the same origin (the PiP window holds the mini
// page in an iframe), so a BroadcastChannel reaches every open nblane window.
// After any successful mutation a window announces "changed"; the others
// refetch the daily-work queries they have mounted (kanban, projects board,
// habit plans). Receiving only invalidates, so there is no echo loop.

import type { Query, QueryClient } from '@tanstack/react-query';

export const SYNC_CHANNEL = 'nblane-sync';
const SYNCED = new Set(['kanban', 'projects-board', 'project-board', 'habit-plans']);

export function isDailyWorkQuery(query: Pick<Query, 'queryKey'>): boolean {
  const [scope, , kind] = query.queryKey as unknown[];
  return scope === 'profiles' && typeof kind === 'string' && SYNCED.has(kind);
}

export function installCrossWindowSync(queryClient: QueryClient): () => void {
  if (typeof BroadcastChannel === 'undefined') return () => undefined;
  const channel = new BroadcastChannel(SYNC_CHANNEL);
  channel.onmessage = (event: MessageEvent) => {
    if (event.data?.type === 'changed') {
      void queryClient.invalidateQueries({ predicate: isDailyWorkQuery });
    }
  };
  const unsubscribe = queryClient.getMutationCache().subscribe((event) => {
    if (event.type === 'updated' && event.action.type === 'success') {
      channel.postMessage({ type: 'changed' });
    }
  });
  return () => {
    unsubscribe();
    channel.close();
  };
}
