import { Alert, Center, Loader, Stack } from '@mantine/core';
import { lazy, Suspense, useEffect } from 'react';
import { useParams } from 'react-router-dom';

import { useStarmapEditingData } from '../starmap/useStarmapData';

// three.js + troika + postprocessing are ~600kB minified — the starmap scene
// loads as its own chunk so other pages never pay for it.
// Start fetching the chunk when HomePage mounts, in parallel with the
// starmap data request, instead of only after the data has arrived.
let starmapChunk: Promise<typeof import('../starmap/StarmapView')> | null = null;
function loadStarmapChunk() {
  starmapChunk ??= import('../starmap/StarmapView').catch((err: unknown) => {
    starmapChunk = null; // let the next mount retry a failed fetch
    throw err;
  });
  return starmapChunk;
}
const StarmapView = lazy(() =>
  loadStarmapChunk().then((m) => ({ default: m.StarmapView })),
);

/**
 * SPA 首页 = 成长星图 (Phase 3: replaces the Phase-1 dashboard cards and the
 * sidecar 3D iframe). Data comes from the dedicated aggregation endpoint
 * GET /api/v1/profiles/{name}/starmap merged with the goal book (editing
 * slice: vacant-star state + 刻痕星); see src/starmap/useStarmapData.ts.
 */
export function HomePage() {
  const { name = '' } = useParams();
  const { snapshot, isPending, isError, error } = useStarmapEditingData(name);
  useEffect(() => {
    void loadStarmapChunk().catch(() => undefined);
  }, []);

  if (isPending) {
    return (
      <Center py="xl">
        <Loader />
      </Center>
    );
  }
  if (isError || !snapshot) {
    return (
      <Stack gap="md" py="md">
        <Alert color="red" title="加载失败" data-testid="starmap-error">
          {error?.message ?? '星图数据缺失'}
        </Alert>
      </Stack>
    );
  }

  return (
    <Suspense
      fallback={
        <Center py="xl">
          <Loader />
        </Center>
      }
    >
      <StarmapView snapshot={snapshot} />
    </Suspense>
  );
}
