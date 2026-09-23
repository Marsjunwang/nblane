import { describe, expect, it } from 'vitest';

import type { ProjectsBoardHabit } from '../../api/types';
import { buildHeatmapWeeks, habitCountMap, heatmapCellColor } from './habitHeatmap';

function makeHabit(overrides: Partial<ProjectsBoardHabit>): ProjectsBoardHabit {
  return {
    id: 'exercise',
    title: '保持锻炼',
    kind: 'health',
    cadence: 'daily',
    project_id: '',
    week: [],
    recent_days: [],
    streak: 0,
    total_checkins: 0,
    last_checkin: '',
    ...overrides,
  };
}

describe('habitHeatmap buildHeatmapWeeks', () => {
  const today = '2026-09-23'; // a Wednesday

  it('spans the trailing 90 days aligned to Monday-first weeks', () => {
    const weeks = buildHeatmapWeeks(makeHabit({}), today);
    const first = weeks[0][0];
    const last = weeks.at(-1)!.at(-1)!;
    // Grid starts on a Monday covering 2026-06-25 (90 days back).
    expect(new Date(first.date + 'T00:00').getDay()).toBe(1);
    expect(first.date <= '2026-06-25').toBe(true);
    // Ends at the week containing today (future cells trail it).
    expect(last.date >= today).toBe(true);
    const all = weeks.flat();
    expect(all.find((cell) => cell.date === today)?.future).toBe(false);
    expect(all.filter((cell) => cell.date > today).every((cell) => cell.future)).toBe(true);
    expect(all.filter((cell) => cell.date < first.date)).toHaveLength(0);
  });

  it('merges recent_days counts with authoritative week dots', () => {
    const habit = makeHabit({
      recent_days: [
        { date: '2026-09-01', count: 2 },
        { date: '2026-09-02', count: 1 },
      ],
      week: [{ date: '2026-09-23', done: true, future: false }],
    });
    const counts = habitCountMap(habit);
    expect(counts.get('2026-09-01')).toBe(2);
    // A just-posted check-in that has not landed in recent_days yet.
    expect(counts.get('2026-09-23')).toBe(1);
    const weeks = buildHeatmapWeeks(habit, today);
    const cell = weeks.flat().find((entry) => entry.date === '2026-09-01');
    expect(cell?.count).toBe(2);
  });

  it('returns no grid when today is malformed', () => {
    expect(buildHeatmapWeeks(makeHabit({}), 'not-a-date')).toEqual([]);
  });
});

describe('habitHeatmap heatmapCellColor (月白→泥金)', () => {
  it('ramps from the faint 月白 ground to full 泥金', () => {
    expect(heatmapCellColor(0, 3)).toBe('rgba(242, 237, 224, 0.07)');
    expect(heatmapCellColor(3, 3)).toBe('rgba(220, 174, 85, 1.00)');
    // Mid-intensity sits between the two.
    const mid = heatmapCellColor(1, 3);
    expect(mid.startsWith('rgba(220, 174, 85,')).toBe(true);
    expect(Number(mid.match(/([\d.]+)\)$/)?.[1])).toBeLessThan(1);
  });
});
