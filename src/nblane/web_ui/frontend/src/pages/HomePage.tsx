import { Alert, Center, Loader, Stack } from '@mantine/core';
import { lazy, Suspense } from 'react';
import { useParams } from 'react-router-dom';

import { useStarmapEditingData } from '../starmap/useStarmapData';

// three.js + troika + postprocessing are ~600kB minified — the starmap scene
// loads as its own chunk so other pages never pay for it.
const StarmapView = lazy(() =>
  import('../starmap/StarmapView').then((m) => ({ default: m.StarmapView })),
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
