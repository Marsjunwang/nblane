import { describe, expect, it, vi } from 'vitest';

import type { ProjectsBoardResponse } from '../../api/types';
import {
  clampRangeToScale,
  computeScale,
  dateToX,
  daysBetween,
  formatDate,
  historyBarRange,
  monthTicks,
  parseDate,
  projectRange,
  scaleWidth,
  shiftDate,
  taskBarRange,
  xToDate,
} from './timelineMath';

describe('timelineMath date primitives', () => {
  it('round-trips ISO dates through epoch ms', () => {
    expect(formatDate(parseDate('2026-09-23'))).toBe('2026-09-23');
    expect(parseDate('not-a-date')).toBeNaN();
    expect(parseDate('2026-9-3')).toBeNaN();
  });

  it('shifts dates across month and year boundaries', () => {
    expect(shiftDate('2026-09-30', 1)).toBe('2026-10-01');
    expect(shiftDate('2026-01-01', -1)).toBe('2025-12-31');
    expect(shiftDate('2026-02-28', 1)).toBe('2026-03-01');
  });

  it('counts whole days between dates', () => {
    expect(daysBetween('2026-09-01', '2026-09-23')).toBe(22);
    expect(daysBetween('2026-09-23', '2026-09-01')).toBe(-22);
  });
});

describe('timelineMath scale mapping', () => {
  const scale = { start: '2026-09-01', end: '2026-09-30', dayWidth: 10 };

  it('maps dates to x at day granularity', () => {
    expect(dateToX('2026-09-01', scale)).toBe(0);
    expect(dateToX('2026-09-11', scale)).toBe(100);
  });

  it('snaps x back down to whole days and clamps to the axis', () => {
    expect(xToDate(0, scale)).toBe('2026-09-01');
    expect(xToDate(105, scale)).toBe('2026-09-11');
    expect(xToDate(-50, scale)).toBe('2026-09-01');
    expect(xToDate(9999, scale)).toBe('2026-09-30');
  });

  it('spans both endpoints inclusively in the total width', () => {
    expect(scaleWidth(scale)).toBe(300);
  });
});

describe('timelineMath monthTicks', () => {
  it('emits month boundaries inside the scale', () => {
    const scale = { start: '2026-08-20', end: '2026-10-05', dayWidth: 10 };
    const ticks = monthTicks(scale);
    expect(ticks.map((tick) => tick.date)).toEqual(['2026-09-01', '2026-10-01']);
    expect(ticks[0].label).toBe('2026-9');
    expect(ticks[0].x).toBe(dateToX('2026-09-01', scale));
  });

  it('includes the first of the start month when the scale starts on it', () => {
    const scale = { start: '2026-09-01', end: '2026-09-30', dayWidth: 10 };
    expect(monthTicks(scale).map((tick) => tick.date)).toEqual(['2026-09-01']);
  });
});

describe('timelineMath taskBarRange', () => {
  const today = '2026-09-23';

  it('prefers planned dates over column dates', () => {
    expect(
      taskBarRange(
        {
          planned_start: '2026-09-01',
          planned_end: '2026-09-10',
          started_on: '2026-08-01',
          completed_on: null,
        },
        today,
      ),
    ).toEqual({ start: '2026-09-01', end: '2026-09-10' });
  });

  it('falls back to started_on → today for live tasks', () => {
    expect(
      taskBarRange(
        { planned_start: null, planned_end: null, started_on: '2026-09-10', completed_on: null },
        today,
      ),
    ).toEqual({ start: '2026-09-10', end: '2026-09-23' });
  });

  it('uses completed_on for done tasks', () => {
    expect(
      taskBarRange(
        { planned_start: null, planned_end: null, started_on: '2026-09-01', completed_on: '2026-09-05' },
        today,
      ),
    ).toEqual({ start: '2026-09-01', end: '2026-09-05' });
  });

  it('returns null when the task has no anchor date (未排期)', () => {
    expect(
      taskBarRange(
        { planned_start: null, planned_end: null, started_on: null, completed_on: null },
        today,
      ),
    ).toBeNull();
    expect(
      taskBarRange(
        { planned_start: 'bad-date', planned_end: null, started_on: null, completed_on: null },
        today,
      ),
    ).toBeNull();
  });

  it('clamps an inverted end back to the start', () => {
    expect(
      taskBarRange(
        { planned_start: '2026-09-10', planned_end: '2026-09-01', started_on: null, completed_on: null },
        today,
      ),
    ).toEqual({ start: '2026-09-10', end: '2026-09-10' });
  });
});

describe('timelineMath projectRange', () => {
  it('parses the YYYY-MM-DD/YYYY-MM-DD form', () => {
    expect(projectRange('2026-02-23/2026-06-20')).toEqual({
      start: '2026-02-23',
      end: '2026-06-20',
    });
  });

  it('returns null for empty or malformed ranges', () => {
    expect(projectRange('')).toBeNull();
    expect(projectRange('2026-02-23')).toBeNull();
    expect(projectRange('soon/later')).toBeNull();
  });
});

describe('timelineMath computeScale', () => {
  const board: ProjectsBoardResponse = {
    profile: 'dev',
    today: '2026-09-23',
    north_star: '',
    goals: [
      {
        id: 'g1',
        title: '目标',
        status: 'active',
        summary: '',
        target: '',
        projects: [
          {
            id: 'p1',
            title: 'nblane',
            status: 'active',
            kind: 'internal',
            visibility: 'private',
            summary: '',
            time_range: '2026-02-23/2026-06-20',
            goal_refs: ['g1'],
            milestones: [
              { id: 'm1', title: '45h', status: 'planned', target: '', date: '2026-05-01', done_count: 0, total_count: 0 },
            ],
            queue: [
              {
                id: 't1',
                title: '任务',
                section: 'Queue',
                column: 'queue',
                done: false,
                context: '',
                why: '',
                started_on: '2026-09-10',
                completed_on: null,
                planned_start: null,
                planned_end: null,
                project_id: 'p1',
                milestone_id: '',
                tags: '',
              },
            ],
            doing: [],
            someday: [],
            column_counts: {},
            done_count: 0,
            archived_done_count: 0,
            evidence_ref_count: 0,
            last_activity: '',
            habit_id: '',
          },
        ],
      },
    ],
    ungrouped_projects: [],
    unassigned_tasks: [],
    habits: [],
    stats: {},
  };

  it('recent zoom (default) windows to the trailing 6 months', () => {
    const scale = computeScale(board, 14);
    expect(scale.dayWidth).toBe(14);
    // Default window: trailing 6 months from 2026-09-23, padded 7d left.
    expect(scale.start).toBe('2026-03-16');
    // In-window items still extend the right edge (task 2026-09-10 → today+14d wins).
    expect(scale.end).toBe('2026-10-07');
  });

  it('all zoom restores the full historical extent', () => {
    const scale = computeScale(board, { dayWidth: 14, zoom: 'all' });
    // Min: the project's 2026-02-23 range start (earlier than today - 7d).
    expect(scale.start).toBe('2026-02-23');
    expect(scale.end).toBe('2026-10-07');
  });

  it('pads the 6-month window when the board is empty', () => {
    const scale = computeScale({ ...board, goals: [], today: '2026-09-23' }, 14);
    expect(scale.start).toBe('2026-03-16');
    expect(scale.end).toBe('2026-10-07');
  });

  it('clamps dirty dates instead of letting them flatten the axis', () => {
    const project = board.goals![0].projects![0];
    const dirty: ProjectsBoardResponse = {
      ...board,
      goals: [{ ...board.goals![0], projects: [{ ...project, time_range: '2012-01-01/2040-01-01' }] }],
    };
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const scale = computeScale(dirty, { dayWidth: 14, zoom: 'all' });
    expect(scale.start >= '2015-01-01').toBe(true);
    expect(scale.end <= '2028-10-07').toBe(true);
    expect(warn).toHaveBeenCalled();
    warn.mockRestore();
  });

  it('includes done history in the data source (裁决5)', () => {
    const history = [
      {
        id: 'kb_done',
        title: '已完成',
        project_id: 'p1',
        completed_on: '2026-05-10',
        started_on: '2026-05-01',
      },
    ];
    // Recent zoom: a 2026-05 history bar is inside the window, no extension.
    const recent = computeScale(board, { dayWidth: 14, history });
    expect(recent.start).toBe('2026-03-16');
    // All zoom with an older history bar extends the domain left.
    const older = [{ ...history[0], completed_on: '2025-11-10', started_on: '2025-11-01' }];
    const all = computeScale(board, { dayWidth: 14, history: older, zoom: 'all' });
    expect(all.start).toBe('2025-11-01');
  });
});

describe('timelineMath historyBarRange', () => {
  it('anchors on completed_on with started_on/planned_start fallbacks', () => {
    expect(
      historyBarRange({ id: 'a', title: '', completed_on: '2026-09-05', started_on: '2026-09-01' }),
    ).toEqual({ start: '2026-09-01', end: '2026-09-05' });
    expect(historyBarRange({ id: 'b', title: '', completed_on: '2026-09-05' })).toEqual({
      start: '2026-09-05',
      end: '2026-09-05',
    });
    expect(historyBarRange({ id: 'c', title: '' })).toBeNull();
  });
});

describe('timelineMath clampRangeToScale', () => {
  const scale = { start: '2026-04-01', end: '2026-09-30', dayWidth: 10 };
  it('clips overlapping bars to the domain', () => {
    expect(clampRangeToScale({ start: '2026-03-01', end: '2026-05-01' }, scale)).toEqual({
      start: '2026-04-01',
      end: '2026-05-01',
    });
  });
  it('drops bars fully outside the domain', () => {
    expect(clampRangeToScale({ start: '2026-01-01', end: '2026-02-01' }, scale)).toBeNull();
    expect(clampRangeToScale({ start: '2026-10-01', end: '2026-11-01' }, scale)).toBeNull();
  });
});
