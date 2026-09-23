/* Fetches the dedicated starmap aggregation (GET .../starmap) — one shot,
 * server-side semantics (locked schema nodes, guest window/floor, zh
 * category names). Replaces the Phase 3 kickoff's 5-endpoint composition. */
import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';

import { apiGet } from '../api/client';
import type { StarmapResponse } from '../api/types';
import { normalizeStarmapResponse, type StarmapSnapshot } from './snapshot';

export interface StarmapDataResult {
  snapshot: StarmapSnapshot | undefined;
  isPending: boolean;
  isError: boolean;
  error: Error | null;
}

export function useStarmapData(profile: string): StarmapDataResult {
  const query = useQuery({
    queryKey: ['profiles', profile, 'starmap'],
    queryFn: () =>
      apiGet<StarmapResponse>(`/profiles/${encodeURIComponent(profile)}/starmap`),
    enabled: profile.length > 0,
  });

  const snapshot = useMemo(
    () => (query.data ? normalizeStarmapResponse(query.data) : undefined),
    [query.data],
  );

  return {
    snapshot,
    isPending: query.isPending,
    isError: query.isError,
    error: (query.error as Error | undefined) ?? null,
  };
}
