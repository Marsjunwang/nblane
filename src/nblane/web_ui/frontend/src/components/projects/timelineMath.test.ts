import { describe, expect, it, vi } from 'vitest';

import type { ProjectsBoardResponse } from '../../api/types';
import {
  barStatus,
  clampDayWidth,
  clampRangeToScale,
  computeScale,
  dateToX,
  daysBetween,
  DAY_WIDTH_MAX,
  DAY_WIDTH_MIN,
  estimateLabelWidth,
  filterGroupsBySelection,
  focusWindowForProject,
  formatDate,
  groundBandHeight,
  historyBarRange,
  isOverdue,
  labelPlacement,
  labelsVisible,
  layoutLane,
  loadProjectFilter,
  monthTicks,
  parseDate,
  projectRange,
  rightSpaces,
  saveProjectFilter,
  scaleWidth,
  shiftDate,
  taskBarRange,
  thinTicks,
  TIMELINE_FILTER_KEY,
  xToDate,
  HISTORY_LANE_HEIGHT,
  TASK_LANE_HEIGHT,
  LANE_GAP,
  ROW_PAD_Y,
  MIN_ROW_HEIGHT,
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

  it('fixed presets pin an exact span with today at ~75%', () => {
    // 月 preset: 30-day window, today at 75% (back 23d, forward 7d).
    const month = computeScale(board, { dayWidth: 14, zoom: 'month' });
    expect(month.start).toBe('2026-08-31');
    expect(month.end).toBe('2026-09-30');
    // 周 preset: 7-day window (back 5d, forward 2d).
    const week = computeScale(board, { dayWidth: 14, zoom: 'week' });
    expect(week.start).toBe('2026-09-18');
    expect(week.end).toBe('2026-09-25');
    // 季 preset: 90 days; 半年: 181 days (the default).
    const quarter = computeScale(board, { dayWidth: 14, zoom: 'quarter' });
    expect(daysBetween(quarter.start, quarter.end)).toBe(90);
    const half = computeScale(board, 14);
    expect(half.start).toBe('2026-05-10');
    expect(daysBetween(half.start, half.end)).toBe(181);
  });

  it('preset windows extend right for overlapping items but never pull left', () => {
    const project = board.goals![0].projects![0];
    const future: ProjectsBoardResponse = {
      ...board,
      goals: [
        {
          ...board.goals![0],
          projects: [{ ...project, time_range: '2026-08-01/2026-12-31' }],
        },
      ],
    };
    const scale = computeScale(future, { dayWidth: 14, zoom: 'month' });
    expect(scale.start).toBe('2026-08-31');
    expect(scale.end).toBe('2026-12-31');
  });

  it('all zoom restores the full historical extent', () => {
    const scale = computeScale(board, { dayWidth: 14, zoom: 'all' });
    // Min: the project's 2026-02-23 range start (earlier than today - 7d).
    expect(scale.start).toBe('2026-02-23');
    expect(scale.end).toBe('2026-10-07');
  });

  it('derives dayWidth from fitWidth when no explicit override is given', () => {
    // 月 window = 31 days (inclusive): 620 / 31 = 20px/day.
    const fit = computeScale(board, { zoom: 'month', fitWidth: 620 });
    expect(fit.dayWidth).toBe(20);
    // 全部 over the whole extent at a narrow viewport clamps to the floor.
    const tiny = computeScale(board, { zoom: 'all', fitWidth: 50 });
    expect(tiny.dayWidth).toBe(DAY_WIDTH_MIN);
    // 周 window at a wide viewport clamps to the ceiling.
    const huge = computeScale(board, { zoom: 'week', fitWidth: 100000 });
    expect(huge.dayWidth).toBe(DAY_WIDTH_MAX);
  });

  it('clamps an explicit dayWidth override to the stepless range', () => {
    expect(computeScale(board, { zoom: 'month', dayWidth: 0.01 }).dayWidth).toBe(DAY_WIDTH_MIN);
    expect(computeScale(board, { zoom: 'month', dayWidth: 999 }).dayWidth).toBe(DAY_WIDTH_MAX);
    expect(clampDayWidth(3.5)).toBe(3.5);
  });

  it('an explicit focus window becomes the exact domain (项目聚焦)', () => {
    const scale = computeScale(board, {
      zoom: 'month',
      window: { start: '2026-04-01', end: '2026-05-15' },
      dayWidth: 10,
    });
    expect(scale.start).toBe('2026-04-01');
    expect(scale.end).toBe('2026-05-15');
  });

  it('labels hide below the semantic-density threshold', () => {
    expect(labelsVisible({ start: '2026-09-01', end: '2026-09-30', dayWidth: 2.9 })).toBe(false);
    expect(labelsVisible({ start: '2026-09-01', end: '2026-09-30', dayWidth: 3 })).toBe(true);
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
    // Default (半年) preset: a 2026-05 history bar is inside the window, no extension.
    const recent = computeScale(board, { dayWidth: 14, history });
    expect(recent.start).toBe('2026-05-10');
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

describe('timelineMath thinTicks (语义密度)', () => {
  it('keeps adjacent tick labels at least minPx apart', () => {
    // 2 years at 1px/day: month ticks are ~30px apart → most drop out.
    const scale = { start: '2026-01-01', end: '2027-12-31', dayWidth: 1 };
    const ticks = thinTicks(monthTicks(scale), 56);
    expect(ticks.length).toBeGreaterThan(0);
    expect(ticks.length).toBeLessThan(24);
    for (let i = 1; i < ticks.length; i += 1) {
      expect(ticks[i].x - ticks[i - 1].x).toBeGreaterThanOrEqual(56);
    }
    // At month-level zoom every month label survives.
    const roomy = { start: '2026-01-01', end: '2026-06-30', dayWidth: 20 };
    expect(thinTicks(monthTicks(roomy), 56)).toHaveLength(monthTicks(roomy).length);
  });
});

describe('timelineMath groundBandHeight (time_range 衬底细带)', () => {
  it('stays a thin 4–6px band regardless of stacked row height', () => {
    expect(groundBandHeight(30)).toBe(6);
    expect(groundBandHeight(110)).toBe(6);
    expect(groundBandHeight(16)).toBe(4);
    expect(groundBandHeight(10)).toBe(4);
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

describe('timelineMath layoutLane (行内错峰)', () => {
  const item = (id: string, start: string, end: string, tall = true) => ({
    item: id,
    range: { start, end },
    tall,
  });

  it('shares one sub-lane for non-overlapping bars', () => {
    const layout = layoutLane([
      item('a', '2026-09-01', '2026-09-05'),
      item('b', '2026-09-05', '2026-09-10'),
      item('c', '2026-09-06', '2026-09-08'),
    ]);
    // a/b touch (end == start, no inclusive-day overlap); c overlaps b only.
    expect(layout.laneCount).toBe(2);
    const lanes = Object.fromEntries(layout.entries.map((e) => [e.item, e.lane]));
    expect(lanes.a).toBe(0);
    expect(lanes.b).toBe(1);
    expect(lanes.c).toBe(0);
  });

  it('reuses a freed sub-lane once its last bar ends before the next starts', () => {
    const layout = layoutLane([
      item('late', '2026-09-05', '2026-09-20'),
      item('early', '2026-09-01', '2026-09-30'),
      item('mid', '2026-09-03', '2026-09-04', false),
    ]);
    // mid (09-03→09-04) takes lane 1; late (09-05→…) fits lane 1 again.
    expect(layout.laneCount).toBe(2);
    const lanes = Object.fromEntries(layout.entries.map((e) => [e.item, e.lane]));
    expect(lanes.early).toBe(0);
    expect(lanes.mid).toBe(1);
    expect(lanes.late).toBe(1);
    // Lane 1 holds a task bar (late), so it stays tall despite the 刻痕.
    expect(layout.entries.find((e) => e.item === 'mid')!.laneHeight).toBe(TASK_LANE_HEIGHT);
  });

  it('adapts row height: 刻痕-only lanes compress, task lanes stay tall', () => {
    const tasksOnly = layoutLane([item('a', '2026-09-01', '2026-09-05')]);
    expect(tasksOnly.rowHeight).toBe(ROW_PAD_Y * 2 + TASK_LANE_HEIGHT);
    const mixed = layoutLane([
      item('a', '2026-09-01', '2026-09-05'),
      item('h', '2026-09-02', '2026-09-04', false),
    ]);
    expect(mixed.rowHeight).toBe(ROW_PAD_Y * 2 + TASK_LANE_HEIGHT + HISTORY_LANE_HEIGHT + LANE_GAP);
    // 刻痕 bar centers inside its compressed lane.
    const history = mixed.entries.find((e) => e.item === 'h')!;
    expect(history.laneHeight).toBe(HISTORY_LANE_HEIGHT);
    expect(history.top).toBeCloseTo(ROW_PAD_Y + TASK_LANE_HEIGHT + LANE_GAP + (HISTORY_LANE_HEIGHT - 7) / 2);
  });

  it('keeps a minimum row height when the lane is empty', () => {
    expect(layoutLane([]).rowHeight).toBe(MIN_ROW_HEIGHT);
  });
});

describe('timelineMath rightSpaces', () => {
  const scale = { start: '2026-09-01', end: '2026-09-30', dayWidth: 10 };
  it('measures free px to the next bar in the same sub-lane or the axis end', () => {
    const layout = layoutLane([
      { item: 'a', range: { start: '2026-09-01', end: '2026-09-05' }, tall: true },
      { item: 'b', range: { start: '2026-09-20', end: '2026-09-25' }, tall: true },
    ]);
    const spaces = rightSpaces(layout.entries, scale);
    // a ends at x=50 (end 09-05 → 4*10+10); b starts at x=190 → 140px free.
    expect(spaces[0]).toBe(140);
    // b ends at x=250; axis width = 300 → 50px free.
    expect(spaces[1]).toBe(50);
  });
});

describe('timelineMath label rules', () => {
  it('embeds labels in bars ≥60px wide', () => {
    expect(labelPlacement(60, 200, 0)).toBe('inside');
    expect(labelPlacement(59.9, 30, 1000)).toBe('right');
  });

  it('hangs labels right only when they fit before the next bar', () => {
    expect(labelPlacement(20, 60, 66)).toBe('right');
    expect(labelPlacement(20, 60, 65)).toBe('none');
    expect(labelPlacement(20, 60, 0)).toBe('none');
  });

  it('estimates CJK titles wider than ASCII at the same length', () => {
    const cjk = estimateLabelWidth('技能树重构');
    const ascii = estimateLabelWidth('abcde');
    expect(cjk).toBeGreaterThan(ascii);
    expect(estimateLabelWidth('')).toBe(4);
  });
});

describe('timelineMath status strokes (状态即笔法)', () => {
  it('maps columns to queue/doing/done', () => {
    expect(barStatus({ column: 'queue' })).toBe('queue');
    expect(barStatus({ column: 'someday' })).toBe('queue');
    expect(barStatus({ column: 'doing' })).toBe('doing');
    expect(barStatus({ column: 'done' })).toBe('done');
    expect(barStatus({ column: 'doing', done: true })).toBe('done');
  });

  it('flags overdue only for unfinished tasks past planned_end', () => {
    const today = '2026-09-25';
    expect(isOverdue({ column: 'doing', planned_end: '2026-09-24' }, today)).toBe(true);
    expect(isOverdue({ column: 'queue', planned_end: '2026-09-01' }, today)).toBe(true);
    expect(isOverdue({ column: 'doing', planned_end: '2026-09-25' }, today)).toBe(false);
    expect(isOverdue({ column: 'doing', planned_end: '2026-10-01' }, today)).toBe(false);
    expect(isOverdue({ column: 'done', done: true, planned_end: '2026-09-01' }, today)).toBe(false);
    expect(isOverdue({ column: 'doing', planned_end: null }, today)).toBe(false);
    expect(isOverdue({ column: 'doing', planned_end: 'bad' }, today)).toBe(false);
  });
});

describe('timelineMath project filter', () => {
  const groups = [
    { id: 'g1', projects: [{ id: 'p1' }, { id: 'p2' }] },
    { id: 'g2', projects: [{ id: 'p3' }] },
  ];

  it('hides unchecked project rows and empties their group headers', () => {
    const visible = filterGroupsBySelection(groups, new Set(['p1']));
    expect(visible).toHaveLength(1);
    expect(visible[0].id).toBe('g1');
    expect(visible[0].projects.map((p) => p.id)).toEqual(['p1']);
  });

  it('selecting everything keeps all groups', () => {
    expect(filterGroupsBySelection(groups, new Set(['p1', 'p2', 'p3']))).toHaveLength(2);
  });

  it('defaults to 全选 when storage is empty and prunes stale ids', () => {
    const storage = window.localStorage;
    storage.removeItem(TIMELINE_FILTER_KEY);
    expect([...loadProjectFilter(storage, ['p1', 'p2'])]).toEqual(['p1', 'p2']);
    saveProjectFilter(storage, new Set(['p2', 'gone']));
    expect([...loadProjectFilter(storage, ['p1', 'p2'])]).toEqual(['p2']);
    storage.setItem(TIMELINE_FILTER_KEY, '{not json');
    expect([...loadProjectFilter(storage, ['p1'])]).toEqual(['p1']);
    storage.removeItem(TIMELINE_FILTER_KEY);
  });
});

describe('timelineMath focusWindowForProject (聚焦)', () => {
  const task = (planned_start: string | null, planned_end: string | null) => ({
    id: '',
    title: '',
    section: 'Queue',
    column: 'queue',
    done: false,
    context: '',
    why: '',
    started_on: null,
    completed_on: null,
    planned_start,
    planned_end,
    project_id: 'p1',
    milestone_id: '',
    tags: '',
  });

  it('pads the project time_range by 5% on both ends', () => {
    // 2026-09-01 → 2026-09-30 = 30 days, pad = round(30*0.05) = 2.
    const window = focusWindowForProject(
      { time_range: '2026-09-01/2026-09-30', queue: [], doing: [], someday: [] },
      '2026-09-25',
    );
    expect(window).toEqual({ start: '2026-08-30', end: '2026-10-02' });
  });

  it('falls back to the task min~max span when no time_range exists', () => {
    const window = focusWindowForProject(
      {
        time_range: '',
        queue: [task('2026-09-10', '2026-09-12')],
        doing: [task('2026-09-01', '2026-09-20')],
        someday: [task(null, null)],
      },
      '2026-09-25',
    );
    // span 09-01 → 09-20 = 20 days, pad 1.
    expect(window).toEqual({ start: '2026-08-31', end: '2026-09-21' });
  });

  it('returns null when nothing is dated', () => {
    expect(
      focusWindowForProject(
        { time_range: '', queue: [task(null, null)], doing: [], someday: [] },
        '2026-09-25',
      ),
    ).toBeNull();
  });
});
