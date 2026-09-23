import { describe, expect, it } from 'vitest';

import { chronicleFlavor, withChronicleFlavor } from './briefing';
import type { ChronicleEntry } from '../api/types';

const TODAY = new Date(2026, 8, 23); // 2026-09-23 local

describe('chronicleFlavor', () => {
  it('counts this-month goal adds / completions / rewrites', () => {
    const entries: ChronicleEntry[] = [
      { date: '2026-09-21', kind: 'goal.added', ref: 'goal-a', note: '' },
      { date: '2026-09-03', kind: 'goal.completed', ref: 'goal-b', note: '' },
      { date: '2026-09-03', kind: 'goal.completed', ref: 'goal-c', note: '' },
      { date: '2026-09-01', kind: 'north_star.rewritten', ref: '', note: '' },
      { date: '2026-08-31', kind: 'goal.added', ref: 'goal-old', note: '' }, // last month
    ];
    expect(chronicleFlavor(entries, TODAY)).toBe('本月新立目标 1，新镌 2 星，北极星已重刻');
  });

  it('stays silent when nothing happened this month', () => {
    expect(chronicleFlavor([], TODAY)).toBe('');
    expect(
      chronicleFlavor([{ date: '2026-08-01', kind: 'goal.added', ref: '', note: '' }], TODAY),
    ).toBe('');
  });

  it('ignores unknown kinds', () => {
    expect(
      chronicleFlavor([{ date: '2026-09-02', kind: 'milestone.reached', ref: '', note: '' }], TODAY),
    ).toBe('');
  });
});

describe('withChronicleFlavor', () => {
  it('appends the coda inside the closing bracket', () => {
    expect(withChronicleFlavor('「3 条客星待评审。」', '本月新立目标 1')).toBe(
      '「3 条客星待评审，本月新立目标 1。」',
    );
  });

  it('keeps the base text untouched without a coda', () => {
    expect(withChronicleFlavor('「…。」', '')).toBe('「…。」');
  });
});
