/* Fetches the dedicated starmap aggregation (GET .../starmap) — one shot,
 * server-side semantics (locked schema nodes, guest window/floor, zh
 * category names). Replaces the Phase 3 kickoff's 5-endpoint composition.
 *
 * Home-editing slice (design docs/zh/dev/home-editing-starmap-design.md):
 * useStarmapEditingData merges the goal book (GET .../goals — full detail,
 * ALL statuses, authoritative NorthStarModel) over the aggregation, because
 * the aggregation carries active goals only and a bare north-star string. */
import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';

import { apiGet } from '../api/client';
import { useGoals } from '../api/hooks';
import type { StarmapResponse } from '../api/types';
import { mergeGoalBook, normalizeStarmapResponse, type StarmapSnapshot } from './snapshot';

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

/**
 * Starmap snapshot + goal book merged for the home scene. The goal book
 * gates first render (its is_set/brief/visibility decide the vacant-star
 * look and the inscription edit form), but degrades gracefully: a failed
 * /goals fetch leaves the aggregation-only snapshot (vacant state then
 * derives from the north-star text).
 */
export function useStarmapEditingData(profile: string): StarmapDataResult {
  const starmap = useStarmapData(profile);
  const book = useGoals(profile);

  const snapshot = useMemo(
    () => (starmap.snapshot ? mergeGoalBook(starmap.snapshot, book.data) : undefined),
    [starmap.snapshot, book.data],
  );

  return {
    snapshot,
    isPending: starmap.isPending || (book.isPending && !book.isError),
    isError: starmap.isError,
    error: starmap.error,
  };
}
