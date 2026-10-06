import { QueryClient } from '@tanstack/react-query';
import { describe, expect, it, vi } from 'vitest';

import { invalidateCrystallizeReadModels, kanbanPatchReplacesList } from './hooks';

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

describe('kanbanPatchReplacesList', () => {
  it('flags full-replace list bodies (no blind 412 retry) and leaves scalar edits retryable', () => {
    expect(kanbanPatchReplacesList({ todos: [] })).toBe(true);
    expect(kanbanPatchReplacesList({ tags: ['a'] })).toBe(true);
    expect(kanbanPatchReplacesList({ project_id: 'p1' })).toBe(false);
    expect(kanbanPatchReplacesList({ title: 'x', context: '' })).toBe(false);
  });
});
