import { describe, expect, it } from 'vitest';

import type { ProjectsBoardResponse } from '../../api/types';
import {
  computeScale,
  dateToX,
  daysBetween,
  formatDate,
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

  it('covers project ranges, task bars, milestones and today with padding', () => {
    const scale = computeScale(board, 14);
    expect(scale.dayWidth).toBe(14);
    // Min: the project's 2026-02-23 range start (earlier than today - 7d).
    expect(scale.start).toBe('2026-02-23');
    // Max: today + 14d (nothing extends past it).
    expect(scale.end).toBe('2026-10-07');
  });

  it('pads around today when the board is empty', () => {
    const scale = computeScale(
      { ...board, goals: [], today: '2026-09-23' },
      14,
    );
    expect(scale.start).toBe('2026-09-16');
    expect(scale.end).toBe('2026-10-07');
  });
});
