import { QueryClient } from '@tanstack/react-query';
import { describe, expect, it, vi } from 'vitest';

import { invalidateCrystallizeReadModels } from './hooks';

describe('crystallize read-model invalidation', () => {
  it('invalidates every read model affected by a successful apply', () => {
    const queryClient = new QueryClient();
    const invalidate = vi.spyOn(queryClient, 'invalidateQueries');

    invalidateCrystallizeReadModels(queryClient, 'alice');

    expect(invalidate.mock.calls.map((call) => call[0]?.queryKey)).toEqual([
      ['profiles', 'alice', 'evidence'],
      ['profiles', 'alice', 'evidence-review'],
      ['profiles', 'alice', 'evidence-stages'],
      ['profiles', 'alice', 'kanban'],
      ['profiles', 'alice', 'skill-tree'],
      ['profiles', 'alice', 'starmap'],
      ['profiles', 'alice', 'home'],
      ['profiles', 'alice', 'project-board'],
      ['profiles', 'alice', 'projects-board'],
      ['profiles', 'alice', 'crystallize-candidates'],
    ]);
  });
});
