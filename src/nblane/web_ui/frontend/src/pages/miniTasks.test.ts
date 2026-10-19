import { describe, expect, it } from 'vitest';

import { byDue, dueState, reapplyToggle, toggleAt } from './miniTasks';

describe('miniTasks', () => {
  it('toggles one todo by index', () => {
    expect(toggleAt([{ text: 'a', done: false }, { text: 'b', done: false }], 1)).toEqual([
      { text: 'a', done: false },
      { text: 'b', done: true },
    ]);
  });

  it('re-applies a toggle by text on a list changed elsewhere, keeping new items', () => {
    const fresh = [
      { text: '新加的', done: false },
      { text: 'a', done: false },
    ];
    expect(reapplyToggle(fresh, { text: 'a', done: false })).toEqual([
      { text: '新加的', done: false },
      { text: 'a', done: true },
    ]);
  });

  it('refuses to re-apply when the item is gone or already flipped', () => {
    expect(reapplyToggle([{ text: 'b', done: false }], { text: 'a', done: false })).toBeNull();
    expect(reapplyToggle([{ text: 'a', done: true }], { text: 'a', done: false })).toBeNull();
  });

  it('labels and orders by due date', () => {
    expect(dueState('2026-10-18', '2026-10-19')).toBe('overdue');
    expect(dueState('2026-10-19', '2026-10-19')).toBe('today');
    expect(dueState('2026-10-20', '2026-10-19')).toBe('');
    expect(dueState(null, '2026-10-19')).toBe('');
    const items = [{ id: 'later', end: '2026-10-25' }, { id: 'today', end: '2026-10-19' }, { id: 'late', end: '2026-10-01' }];
    expect(byDue(items, (item) => dueState(item.end, '2026-10-19')).map((item) => item.id)).toEqual(['late', 'today', 'later']);
  });
});
