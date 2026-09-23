import { describe, expect, it } from 'vitest';

import type { ProjectsBoardTask } from '../../api/types';
import { laneDropToGlobalIndex } from './ProjectLane';

function task(id: string): ProjectsBoardTask {
  return { id } as ProjectsBoardTask;
}

describe('laneDropToGlobalIndex (lane-local drop → section-global to_index)', () => {
  // Global Queue: [a1, other1, a2, other2, a3] — the lane sees [a1, a2, a3].
  // Indices are PRE-removal (the backend removes the dragged card first).
  const section = [{ id: 'a1' }, { id: 'other1' }, { id: 'a2' }, { id: 'other2' }, { id: 'a3' }];
  const lane = [task('a1'), task('a2'), task('a3')];

  it('drop on a lane card takes that card\'s pre-removal slot', () => {
    // Drag a1 onto a3 → to_index 4; backend: remove a1 → [other1,a2,other2,a3],
    // insert at min(4, 4) → a1 lands right after a3 (lane order a2, a3, a1).
    expect(laneDropToGlobalIndex(section, lane, 'a1', 'a3')).toBe(4);
    // Cross-section drags (dragged card absent here) insert before the over card.
    expect(laneDropToGlobalIndex(section, lane, 'kb_x', 'a2')).toBe(2);
  });

  it('lane-tail drops land after the lane\'s last card in the section', () => {
    // Drag a1 to the lane tail → after a3 (pre-removal index 4) + 1 = 5;
    // the backend clamps to the post-removal tail.
    expect(laneDropToGlobalIndex(section, lane, 'a1', null)).toBe(5);
    // Cross-section tail: after the lane's last card (a3 at 4) → 5.
    expect(laneDropToGlobalIndex(section, lane, 'kb_x', null)).toBe(5);
  });

  it('empty lane columns (or unloaded boards) fall back to the section tail', () => {
    expect(laneDropToGlobalIndex(section, [], 'kb_x', null)).toBeUndefined();
    expect(laneDropToGlobalIndex(undefined, lane, 'a1', 'a3')).toBeUndefined();
    // Over card missing from the section (stale) → tail.
    expect(laneDropToGlobalIndex(section, lane, 'a1', 'ghost')).toBeUndefined();
  });
});
