import { describe, expect, it } from 'vitest';

import type { KanbanSection, KanbanTask, ProjectsBoardProject, ProjectsBoardTask } from '../../api/types';
import {
  BREAK_MIN_GAP_DAYS,
  BREAK_WIDTH_PX,
  buildChronicleRows,
  buildRowScale,
  chronicleDateToX,
  chronicleLabelWidth,
  chronicleRowsForHeight,
  chronicleXToDate,
  clampChronicleSpan,
  clipRangeToRow,
  collectChronicleEvents,
  CHRONICLE_DEFAULT_SPAN,
  CHRONICLE_ELBOW_HEIGHT,
  CHRONICLE_ROW_HEIGHT,
  CHRONICLE_SPAN_MAX,
  CHRONICLE_SPAN_MIN,
  decodeChronicleParams,
  defaultChronicleAnchor,
  detectBreaks,
  encodeChronicleParams,
  filterChronicleEvents,
  layoutChronicleLabels,
  panChronicle,
  projectBadge,
  projectGlyph,
  PROJECT_GLYPHS,
  sameDayFanOffsets,
  zoomChronicle,
  type ChronicleEvent,
  type ChronicleLabelItem,
  type ChronicleLabelLayout,
} from './chronicleMath';
import { daysBetween, shiftDate } from './timelineMath';

const TODAY = '2026-09-25';

function boardTask(partial: Partial<ProjectsBoardTask> & { id: string }): ProjectsBoardTask {
  return {
    column: 'queue',
    context: '',
    done: false,
    milestone_id: '',
    project_id: '',
    section: '',
    tags: '',
    title: partial.id,
    why: '',
    ...partial,
  } as ProjectsBoardTask;
}

function project(partial: Partial<ProjectsBoardProject> & { id: string }): ProjectsBoardProject {
  return {
    archived_done_count: 0,
    done_count: 0,
    habit_id: '',
    kind: 'internal',
    last_activity: '',
    status: 'active',
    summary: '',
    time_range: '',
    title: partial.id,
    visibility: '',
    ...partial,
  } as ProjectsBoardProject;
}

function kanbanTask(partial: Partial<KanbanTask> & { id: string }): KanbanTask {
  return { done: true, project_id: '', title: partial.id, ...partial } as KanbanTask;
}

describe('chronicleMath row tiling', () => {
  it('tiles contiguous rows downward from the anchor, alternating direction', () => {
    const rows = buildChronicleRows('2026-09-25', 30, 3);
    expect(rows).toHaveLength(3);
    expect(rows[0]).toMatchObject({ index: 0, start: '2026-08-27', end: '2026-09-25', ltr: false });
    expect(rows[1]).toMatchObject({ index: 1, start: '2026-07-28', end: '2026-08-26', ltr: true });
    expect(rows[2]).toMatchObject({ index: 2, start: '2026-06-28', end: '2026-07-27', ltr: false });
    // Contiguous: row i+1's newest day is the day before row i's oldest day.
    expect(shiftDate(rows[1].end, 1)).toBe(rows[0].start);
    expect(shiftDate(rows[2].end, 1)).toBe(rows[1].start);
    for (const row of rows) {
      expect(daysBetween(row.start, row.end) + 1).toBe(30);
    }
  });

  it('clamps the span and derives the default anchor with future room', () => {
    expect(clampChronicleSpan(3)).toBe(CHRONICLE_SPAN_MIN);
    expect(clampChronicleSpan(9999)).toBe(CHRONICLE_SPAN_MAX);
    expect(clampChronicleSpan(Number.NaN)).toBe(CHRONICLE_DEFAULT_SPAN);
    const anchor = defaultChronicleAnchor(TODAY, 90);
    expect(daysBetween(TODAY, anchor)).toBe(23); // round(90 × 0.25) ahead of today
    const rows = buildChronicleRows(anchor, 90, 1);
    expect(TODAY >= rows[0].start && TODAY <= rows[0].end).toBe(true);
  });

  it('pans the anchor by whole days with loose clamping', () => {
    expect(panChronicle('2026-09-25', -30, TODAY)).toBe('2026-08-26');
    expect(panChronicle('2026-09-25', 0, TODAY)).toBe('2026-09-25');
    expect(panChronicle('2015-01-02', -30, TODAY)).toBe('2015-01-01');
    expect(panChronicle('2028-12-01', 30, TODAY)).toBe('2028-09-26'); // today + 2y (2028 闰年)
  });

  it('keeps the focus date at its row and fraction across a zoom', () => {
    // Row 2, halfway through a 90-day span: focus sits 45 + 2*90 days back.
    const anchor = '2026-09-25';
    const focusDate = shiftDate(anchor, -(2 * 90 + 45));
    const newAnchor = zoomChronicle({ newSpan: 14, focusDate, focusRow: 2, focusFrac: 45 / 89 });
    const rows = buildChronicleRows(newAnchor, 14, 3);
    expect(focusDate >= rows[2].start && focusDate <= rows[2].end).toBe(true);
    const frac = daysBetween(focusDate, rows[2].end) / 13;
    expect(Math.abs(frac - 45 / 89)).toBeLessThan(0.1);
  });
});

describe('chronicleMath event collection', () => {
  const sections: KanbanSection[] = [
    { name: 'Queue', tasks: [] } as unknown as KanbanSection,
    {
      name: 'Done',
      tasks: [
        kanbanTask({ id: 'done-1', title: '刻点任务', completed_on: '2026-09-12', project_id: 'p1' }),
        kanbanTask({ id: 'done-2', title: '仅planned', planned_end: '2026-09-01', project_id: 'p2' }),
        kanbanTask({ id: 'done-3', title: '无日期' }),
      ],
    } as unknown as KanbanSection,
  ];
  const archive: KanbanTask[] = [
    kanbanTask({ id: 'arch-1', title: '归档任务', completed_on: '2026-08-20', project_id: 'p1' }),
  ];
  const projects = [
    project({
      id: 'p1',
      title: 'VLA 攻坚',
      queue: [
        boardTask({ id: 'q1', planned_start: '2026-09-28', planned_end: '2026-10-04', column: 'queue' }),
        boardTask({ id: 'q-noanchor', column: 'queue' }),
      ],
      doing: [
        boardTask({ id: 'd1', started_on: '2026-09-08', column: 'doing' }),
        boardTask({ id: 'd2', planned_start: '2026-09-10', column: 'doing' }),
      ],
      someday: [
        boardTask({ id: 's1', planned_start: '2026-11-01', column: 'someday' }),
        boardTask({ id: 's2', planned_start: '2026-05-25', column: 'someday' }),
        boardTask({ id: 's-noanchor', column: 'someday' }),
      ],
    }),
    project({ id: 'p2', title: '学习', status: 'archived' }),
  ];
  const unassigned = [
    boardTask({ id: 'u1', title: '未归属', started_on: '2026-09-20', column: 'doing' }),
  ];

  const events = collectChronicleEvents({ projects, unassigned, kanbanSections: sections, kanbanArchive: archive, today: TODAY });
  const byId = new Map(events.map((event) => [event.id, event]));

  it('collects all five strokes from board + kanban + archive', () => {
    expect(byId.get('q1')).toMatchObject({ kind: 'queue', start: '2026-09-28', end: '2026-10-04', dateLabel: '09-28 → 10-04' });
    expect(byId.get('d1')).toMatchObject({ kind: 'doing', start: '2026-09-08', end: TODAY });
    expect(byId.get('d2')).toMatchObject({ kind: 'doing', start: '2026-09-10', end: TODAY });
    expect(byId.get('s1')).toMatchObject({ kind: 'someday', start: '2026-11-01', overdue: false });
    expect(byId.get('done-1')).toMatchObject({ kind: 'done', start: '2026-09-12', archived: false });
    expect(byId.get('arch-1')).toMatchObject({ kind: 'done', archived: true });
    expect(byId.get('u1')).toMatchObject({ kind: 'doing', projectId: '', badge: '', glyph: '' });
    expect(byId.get('d1')).toMatchObject({ startedOn: '2026-09-08', glyph: projectGlyph('p1') });
    expect(byId.get('done-1')!.glyph).toBe(projectGlyph('p1'));
  });

  it('flips someday to 朱砂 once planned_start has arrived', () => {
    expect(byId.get('s2')).toMatchObject({ kind: 'someday', overdue: true });
  });

  it('skips tasks with no anchor date', () => {
    expect(byId.has('q-noanchor')).toBe(false);
    expect(byId.has('s-noanchor')).toBe(false);
    expect(byId.has('done-3')).toBe(false);
  });

  it('fades events of archived projects and caps badges at 4 chars', () => {
    expect(byId.get('done-2')).toMatchObject({ projectId: 'p2', archived: true, badge: '学习' });
    expect(projectBadge('VLA 攻坚')).toBe('VLA ');
    expect(projectBadge('一个超长项目名')).toBe('一个超长');
    expect(byId.get('q1')!.badge.length).toBeLessThanOrEqual(4);
  });

  it('filters by project selection; unassigned events are immune', () => {
    expect(filterChronicleEvents(events, null)).toHaveLength(events.length);
    const only = filterChronicleEvents(events, new Set(['p1']));
    expect(only.every((event) => event.projectId === 'p1' || event.projectId === '')).toBe(true);
    expect(only.some((event) => event.id === 'u1')).toBe(true);
    expect(only.some((event) => event.id === 'done-2')).toBe(false);
    expect(filterChronicleEvents(events, new Set()).some((event) => event.id === 'u1')).toBe(true);
  });
});

describe('chronicleMath break detection', () => {
  const ev = (id: string, start: string, end = start): ChronicleEvent => ({
    id,
    kind: 'done',
    title: id,
    projectId: '',
    badge: '',
    archived: false,
    start,
    end,
    overdue: false,
    dateLabel: start,
    startedOn: null,
    glyph: '',
  });

  it('returns nothing when the whole domain fits under the threshold', () => {
    expect(detectBreaks([], { start: '2026-09-01', end: '2026-09-20' })).toEqual([]);
  });

  it('collapses a legally empty domain into one break (全空窗口)', () => {
    const breaks = detectBreaks([], { start: '2026-01-01', end: '2026-12-31' });
    expect(breaks).toHaveLength(1);
    expect(breaks[0]).toMatchObject({ start: '2026-01-01', end: '2026-12-31', days: 365 });
  });

  it('compresses interior gaps longer than the threshold', () => {
    const breaks = detectBreaks(
      [ev('a', '2026-05-04'), ev('b', '2026-06-16')],
      { start: '2026-05-01', end: '2026-06-20' },
    );
    expect(breaks).toHaveLength(1);
    expect(breaks[0]).toMatchObject({ start: '2026-05-05', end: '2026-06-15', days: 42 });
    expect(breaks[0].days).toBeGreaterThan(BREAK_MIN_GAP_DAYS);
  });

  it('merges overlapping/adjacent spans before measuring gaps', () => {
    const breaks = detectBreaks(
      [
        ev('a', '2026-05-01', '2026-05-10'),
        ev('b', '2026-05-10', '2026-05-20'), // adjacent — no break between
        ev('c', '2026-08-01'),
      ],
      { start: '2026-05-01', end: '2026-08-05' },
    );
    expect(breaks).toHaveLength(1);
    expect(breaks[0]).toMatchObject({ start: '2026-05-21', end: '2026-07-31' });
  });

  it('breaks leading and trailing emptiness against the domain', () => {
    const breaks = detectBreaks(
      [ev('a', '2026-09-10'), ev('b', '2026-09-15')],
      { start: '2026-06-01', end: '2026-12-31' },
    );
    expect(breaks).toHaveLength(2);
    expect(breaks[0]).toMatchObject({ start: '2026-06-01', end: '2026-09-09' });
    expect(breaks[1]).toMatchObject({ start: '2026-09-16', end: '2026-12-31' });
  });

  it('leaves edge stretches at or under the threshold unbroken', () => {
    const breaks = detectBreaks(
      [ev('a', '2026-09-01'), ev('b', '2026-09-20')],
      { start: '2026-08-15', end: '2026-10-05' },
    );
    expect(breaks).toEqual([]); // 17/18/15-day stretches all ≤ 21
  });

  it('clips event spans to the domain before measuring edges', () => {
    const breaks = detectBreaks(
      [ev('a', '2025-12-01', '2026-02-01'), ev('b', '2026-06-25')],
      { start: '2026-01-01', end: '2026-06-30' },
    );
    expect(breaks).toHaveLength(1);
    expect(breaks[0]).toMatchObject({ start: '2026-02-02', end: '2026-06-24' });
  });
});

describe('chronicleMath row scale (date ↔ x)', () => {
  const rows = buildChronicleRows('2026-09-25', 10, 2);
  const plain = { plotX: 30, plotW: 1000 };

  it('maps every day to x and back exactly, in both directions', () => {
    for (const row of rows) {
      const scale = buildRowScale(row, [], plain);
      expect(scale.dayWidth).toBe(100);
      for (let i = 0; i < 10; i += 1) {
        const date = shiftDate(row.start, i);
        const x = chronicleDateToX(scale, date);
        expect(x).not.toBeNull();
        expect(chronicleXToDate(scale, x!)).toBe(date);
      }
      expect(chronicleDateToX(scale, shiftDate(row.end, 1))).toBeNull();
    }
  });

  it('mirrors even rows: newest at the left edge', () => {
    const scale0 = buildRowScale(rows[0], [], plain); // mirrored
    const scale1 = buildRowScale(rows[1], [], plain); // ltr
    expect(chronicleDateToX(scale0, rows[0].end)).toBeLessThan(chronicleDateToX(scale0, rows[0].start)!);
    expect(chronicleDateToX(scale1, rows[1].start)).toBeLessThan(chronicleDateToX(scale1, rows[1].end)!);
    expect(chronicleDateToX(scale1, rows[1].start)).toBe(30);
    expect(chronicleDateToX(scale0, rows[0].start)).toBe(1030);
  });

  const spanRows = buildChronicleRows('2026-09-25', 30, 3);
  const breakEvents = [
    { start: '2026-07-01', end: '2026-07-01' },
    { start: '2026-09-20', end: '2026-09-20' },
  ];
  const [longBreak] = detectBreaks(breakEvents, { start: '2026-06-29', end: '2026-09-25' });

  it('compresses breaks into fixed-width blocks with a sane inverse', () => {
    expect(longBreak).toMatchObject({ start: '2026-07-02', end: '2026-09-19' });
    const scale = buildRowScale(spanRows[0], [longBreak], plain);
    const gaps = scale.segments.filter((seg) => seg.gap);
    expect(gaps).toHaveLength(1);
    // Row 0 (08-27..09-25) clips the break to 08-27..09-19.
    expect(gaps[0]).toMatchObject({ start: '2026-08-27', end: '2026-09-19' });
    expect(gaps[0].x1 - gaps[0].x0).toBe(BREAK_WIDTH_PX);
    // A date inside the compressed block maps into it and back.
    const gapX = chronicleDateToX(scale, '2026-09-10');
    expect(gapX).not.toBeNull();
    const inside = chronicleXToDate(scale, gapX!);
    expect(inside >= gaps[0].start && inside <= gaps[0].end).toBe(true);
    // Days after the break still round-trip.
    expect(chronicleXToDate(scale, chronicleDateToX(scale, '2026-09-20')!)).toBe('2026-09-20');
    expect(chronicleXToDate(scale, chronicleDateToX(scale, '2026-09-25')!)).toBe('2026-09-25');
  });

  it('splits a long break across every row it spans', () => {
    const clipped = spanRows.map((row) => buildRowScale(row, [longBreak], plain));
    expect(clipped[0].segments.find((seg) => seg.gap)).toMatchObject({ start: '2026-08-27', end: '2026-09-19' });
    expect(clipped[1].segments.find((seg) => seg.gap)).toMatchObject({ start: '2026-07-28', end: '2026-08-26' });
    expect(clipped[2].segments.find((seg) => seg.gap)).toMatchObject({ start: '2026-07-02', end: '2026-07-27' });
  });

  it('renders expanded breaks uncompressed', () => {
    const scale = buildRowScale(spanRows[0], [longBreak], { ...plain, expandedKeys: new Set([longBreak.key]) });
    expect(scale.segments.every((seg) => !seg.gap)).toBe(true);
    expect(scale.dayWidth).toBeCloseTo(1000 / 30);
  });

  it('clips event ranges to rows', () => {
    expect(clipRangeToRow({ start: '2026-09-20', end: '2026-10-05' }, spanRows[0])).toEqual({
      start: '2026-09-20',
      end: '2026-09-25',
    });
    expect(clipRangeToRow({ start: '2026-10-01', end: '2026-10-05' }, spanRows[0])).toBeNull();
  });
});

describe('chronicleMath adaptive row count', () => {
  it('fits rows by height with a floor of one', () => {
    const unit = CHRONICLE_ROW_HEIGHT + CHRONICLE_ELBOW_HEIGHT;
    expect(chronicleRowsForHeight(0)).toBe(1);
    expect(chronicleRowsForHeight(unit)).toBe(1);
    expect(chronicleRowsForHeight(unit * 3 - 1)).toBe(3); // last row needs no elbow
    expect(chronicleRowsForHeight(unit * 4)).toBe(4);
  });
});

describe('chronicleMath label collision layout v2', () => {
  const opts = { plotX: 0, plotW: 1000, pad: 6 };
  const item = (
    id: string,
    x: number,
    width = 100,
    extra: Partial<ChronicleLabelItem> = {},
  ): ChronicleLabelItem => ({
    id,
    x,
    width,
    title: id,
    badge: '',
    dateLabel: '06-16',
    ...extra,
  });
  const byId = (layout: ChronicleLabelLayout, id: string) =>
    layout.placements.find((p) => p.id === id);

  it('places sparse labels on the near above tier at full size', () => {
    const layout = layoutChronicleLabels([item('a', 100), item('b', 500)], opts);
    expect(byId(layout, 'a')).toMatchObject({ cx: 100, side: 'above', tier: 0, size: 'normal', truncated: false });
    expect(byId(layout, 'b')).toMatchObject({ side: 'above', tier: 0 });
    expect(layout.chips).toEqual([]);
  });

  it('walks all four tiers before degrading the label', () => {
    const layout = layoutChronicleLabels(
      [item('a', 100), item('b', 100), item('c', 100), item('d', 100)],
      opts,
    );
    expect(byId(layout, 'a')).toMatchObject({ side: 'above', tier: 0 });
    expect(byId(layout, 'b')).toMatchObject({ side: 'below', tier: 0 });
    expect(byId(layout, 'c')).toMatchObject({ side: 'above', tier: 1 });
    expect(byId(layout, 'd')).toMatchObject({ side: 'below', tier: 1 });
  });

  it('truncates a long title (≥6 字保首) before shrinking the font', () => {
    // Four narrow sentries fill every tier around x=100; the wide candidate
    // only fits once its 13-char title truncates to 6+… (full width would
    // still overlap the sentry intervals).
    const sentries = ['s1', 's2', 's3', 's4'].map((id) => item(id, 100, 60));
    const longTitle = '这是一个非常长的任务标题啊';
    const wide = item('w', 190, chronicleLabelWidth(longTitle, '', '06-16'), { title: longTitle });
    const layout = layoutChronicleLabels([...sentries, wide], opts);
    expect(byId(layout, 'w')).toMatchObject({ truncated: true, size: 'normal' });
  });

  it('shrinks one font notch when even the truncated title collides', () => {
    const sentries = ['s1', 's2', 's3', 's4'].map((id) => item(id, 100, 60));
    const longTitle = '这是一个非常长的任务标题啊';
    const wide = item('w', 178, chronicleLabelWidth(longTitle, '', '06-16'), { title: longTitle });
    const layout = layoutChronicleLabels([...sentries, wide], opts);
    expect(byId(layout, 'w')).toMatchObject({ truncated: true, size: 'small' });
  });

  it('clusters the overflow into +N chips instead of hiding names', () => {
    const items = Array.from({ length: 8 }, (_, i) => item(`l${i}`, 300 + i * 4, 100));
    const layout = layoutChronicleLabels(items, opts);
    expect(layout.placements).toHaveLength(4);
    expect(layout.chips).toHaveLength(1);
    expect(layout.chips[0].memberIds).toEqual(['l4', 'l5', 'l6', 'l7']);
  });

  it('keeps the pinned today marker above and routes others around it', () => {
    const layout = layoutChronicleLabels(
      [item('today', 400, 90, { pinnedSide: 'above' }), item('x', 410)],
      opts,
    );
    expect(byId(layout, 'today')).toMatchObject({ side: 'above', tier: 0, size: 'normal' });
    expect(byId(layout, 'x')).toMatchObject({ side: 'below', tier: 0 });
  });

  it('clamps edge labels inside the plot', () => {
    const layout = layoutChronicleLabels([item('a', 0), item('b', 1000)], opts);
    expect(byId(layout, 'a')!.cx).toBeGreaterThanOrEqual(50);
    expect(byId(layout, 'b')!.cx).toBeLessThanOrEqual(950);
  });

  it('estimates label width from the longer of title and date lines', () => {
    const wide = chronicleLabelWidth('整理机器人架构', '学习', '05-04');
    const narrow = chronicleLabelWidth('ok', '', '09-08 → 09-25');
    expect(wide).toBeGreaterThan(narrow);
  });
});

describe('chronicleMath project glyphs', () => {
  it('assigns a deterministic glyph from the fixed set', () => {
    expect(PROJECT_GLYPHS).toContain(projectGlyph('project:vla'));
    expect(projectGlyph('project:vla')).toBe(projectGlyph('project:vla'));
    expect(projectGlyph('')).toBe('');
    // The hash actually spreads across the set.
    const distinct = new Set(['a', 'b', 'c', 'd', 'e', 'f'].map(projectGlyph));
    expect(distinct.size).toBeGreaterThan(3);
  });
});

describe('chronicleMath same-day done fan', () => {
  const trio = () => [
    { id: 'b', date: '2026-06-16', startedOn: '2026-06-05' },
    { id: 'a', date: '2026-06-16', startedOn: '2026-06-01' },
    { id: 'c', date: '2026-06-16', startedOn: null },
  ];

  it('orders the fan by started_on, earliest at the point, missing dates last', () => {
    const offsets = sameDayFanOffsets(trio(), { mirror: false, step: 10 });
    expect(offsets.get('a')).toBe(0);
    expect(offsets.get('b')).toBe(10);
    expect(offsets.get('c')).toBe(-10);
  });

  it('mirrors the fan on mirrored rows', () => {
    const offsets = sameDayFanOffsets(trio(), { mirror: true, step: 10 });
    expect(offsets.get('a')).toBe(0);
    expect(offsets.get('b')).toBe(-10);
    expect(offsets.get('c')).toBe(10);
  });

  it('leaves singleton days untouched and breaks started_on ties by id', () => {
    expect(
      sameDayFanOffsets([{ id: 'x', date: '2026-06-16', startedOn: null }], { mirror: false }).size,
    ).toBe(0);
    const ties = sameDayFanOffsets(
      [
        { id: 'b', date: '2026-06-16', startedOn: '2026-06-01' },
        { id: 'a', date: '2026-06-16', startedOn: '2026-06-01' },
      ],
      { mirror: false, step: 10 },
    );
    expect(ties.get('a')).toBe(0);
    expect(ties.get('b')).toBe(10);
  });
});

describe('chronicleMath URL state', () => {
  it('round-trips span, top date and the project filter', () => {
    const encoded = encodeChronicleParams({ span: 45, top: '2026-09-20', selectedProjects: new Set(['b', 'a']) });
    expect(encoded).toEqual({ cspan: '45', ctop: '2026-09-20', cproj: 'a,b' });
    const decoded = decodeChronicleParams(new URLSearchParams('cspan=45&ctop=2026-09-20&cproj=a,b'));
    expect(decoded.span).toBe(45);
    expect(decoded.top).toBe('2026-09-20');
    expect(decoded.projects).toEqual(new Set(['a', 'b']));
  });

  it('omits the filter at 全选 and treats an explicit empty filter as empty', () => {
    expect(encodeChronicleParams({ span: 90, top: '2026-09-25', selectedProjects: null }).cproj).toBeNull();
    const decoded = decodeChronicleParams(new URLSearchParams('cproj='));
    expect(decoded.projects).toEqual(new Set());
  });

  it('ignores junk params', () => {
    const decoded = decodeChronicleParams(new URLSearchParams('cspan=abc&ctop=not-a-date'));
    expect(decoded.span).toBeUndefined();
    expect(decoded.top).toBeUndefined();
    expect(decoded.projects).toBeUndefined();
  });
});
