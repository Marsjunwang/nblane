// Pure date<->pixel math for the /projects timeline view. Day granularity:
// every coordinate snaps to whole days. All dates are ISO `YYYY-MM-DD`
// interpreted as LOCAL midnight (the board's `today` is server-local too).

import type {
  ProjectsBoardMilestone,
  ProjectsBoardProject,
  ProjectsBoardResponse,
  ProjectsBoardTask,
} from '../../api/types';

const DAY_MS = 86_400_000;

/** Local-midnight epoch ms for an ISO date; NaN for malformed input. */
export function parseDate(date: string): number {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(date.trim());
  if (!match) {
    return Number.NaN;
  }
  return new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3])).getTime();
}

/** ISO `YYYY-MM-DD` for a local-midnight epoch ms. */
export function formatDate(ms: number): string {
  const d = new Date(ms);
  const pad = (value: number) => String(value).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

/** Shift an ISO date by whole days. */
export function shiftDate(date: string, days: number): string {
  return formatDate(parseDate(date) + days * DAY_MS);
}

/** Whole days from `from` to `to` (to - from). */
export function daysBetween(from: string, to: string): number {
  return Math.round((parseDate(to) - parseDate(from)) / DAY_MS);
}

export interface TimelineScale {
  /** First day on the axis (ISO). */
  start: string;
  /** Last day on the axis (ISO, inclusive). */
  end: string;
  /** Pixels per day. */
  dayWidth: number;
}

/** X offset (px) of a day's left edge within the scale. */
export function dateToX(date: string, scale: TimelineScale): number {
  return daysBetween(scale.start, date) * scale.dayWidth;
}

/** Date at an X offset, snapped down to whole days and clamped to the axis. */
export function xToDate(x: number, scale: TimelineScale): string {
  const max = daysBetween(scale.start, scale.end);
  const days = Math.min(Math.max(Math.floor(x / scale.dayWidth), 0), max);
  return shiftDate(scale.start, days);
}

export interface MonthTick {
  /** First of the month (ISO). */
  date: string;
  x: number;
  /** `YYYY-M` label, e.g. `2026-9`. */
  label: string;
}

/** Month boundaries inside the scale, for the axis row. */
export function monthTicks(scale: TimelineScale): MonthTick[] {
  const ticks: MonthTick[] = [];
  const start = new Date(parseDate(scale.start));
  let cursor = new Date(start.getFullYear(), start.getMonth(), 1);
  if (cursor.getTime() < parseDate(scale.start)) {
    cursor = new Date(cursor.getFullYear(), cursor.getMonth() + 1, 1);
  }
  const endMs = parseDate(scale.end);
  while (cursor.getTime() <= endMs) {
    const date = formatDate(cursor.getTime());
    ticks.push({ date, x: dateToX(date, scale), label: `${cursor.getFullYear()}-${cursor.getMonth() + 1}` });
    cursor = new Date(cursor.getFullYear(), cursor.getMonth() + 1, 1);
  }
  return ticks;
}

export interface BarRange {
  start: string;
  end: string;
}

/** Done/archived task from kanban.md sections — the timeline history layer. */
export interface TimelineHistoryTask {
  id: string;
  title: string;
  project_id?: string | null;
  planned_start?: string | null;
  planned_end?: string | null;
  started_on?: string | null;
  completed_on?: string | null;
}

/**
 * Dirty-date clamp (裁决5): dates before 2015 or more than 2 years past today
 * are obviously bogus (they used to drag the scale domain back to 2022 and
 * flatten everything) — clamp to the boundary and warn once per value.
 */
const DIRTY_MIN = '2015-01-01';
const dirtyWarned = new Set<string>();

export function clampDirtyDate(date: string, today: string): string {
  const max = formatDate(parseDate(today) + 366 * 2 * DAY_MS);
  if (date < DIRTY_MIN || date > max) {
    const clamped = date < DIRTY_MIN ? DIRTY_MIN : max;
    if (!dirtyWarned.has(date)) {
      dirtyWarned.add(date);
      // eslint-disable-next-line no-console
      console.warn(`[timeline] 脏日期钳制: ${date} → ${clamped}`);
    }
    return clamped;
  }
  return date;
}

/** Clamp both ends of a range; returns null when either date is malformed. */
function clampRange(range: BarRange, today: string): BarRange | null {
  if (Number.isNaN(parseDate(range.start)) || Number.isNaN(parseDate(range.end))) {
    return null;
  }
  const start = clampDirtyDate(range.start, today);
  const end = clampDirtyDate(range.end, today);
  return parseDate(end) < parseDate(start) ? { start, end: start } : { start, end };
}

/**
 * A done task's 刻痕 span: `planned_start ?? started_on ?? completed_on` →
 * `completed_on ?? planned_end`. No anchor at all → null (not rendered).
 */
export function historyBarRange(task: TimelineHistoryTask): BarRange | null {
  const end = task.completed_on || task.planned_end || '';
  if (!end || Number.isNaN(parseDate(end))) {
    return null;
  }
  const start = task.planned_start || task.started_on || end;
  if (!start || Number.isNaN(parseDate(start)) || parseDate(start) > parseDate(end)) {
    return { start: end, end };
  }
  return { start, end };
}

/** Clip a bar to the visible scale domain; null when fully outside. */
export function clampRangeToScale(range: BarRange, scale: TimelineScale): BarRange | null {
  if (parseDate(range.end) < parseDate(scale.start) || parseDate(range.start) > parseDate(scale.end)) {
    return null;
  }
  return {
    start: range.start < scale.start ? scale.start : range.start,
    end: range.end > scale.end ? scale.end : range.end,
  };
}

/**
 * A task's timeline span: `planned_start ?? started_on` →
 * `planned_end ?? completed_on ?? today`. Tasks with no anchor date at all
 * return null and render in the row's 未排期 list instead of on the axis.
 */
export function taskBarRange(
  task: Pick<
    ProjectsBoardTask,
    'planned_start' | 'planned_end' | 'started_on' | 'completed_on'
  >,
  today: string,
): BarRange | null {
  const start = task.planned_start || task.started_on || '';
  if (!start || Number.isNaN(parseDate(start))) {
    return null;
  }
  let end = task.planned_end || task.completed_on || today;
  if (!end || Number.isNaN(parseDate(end)) || parseDate(end) < parseDate(start)) {
    end = start;
  }
  return { start, end };
}

/** Parse a project `time_range` (`YYYY-MM-DD/YYYY-MM-DD`) into a span. */
export function projectRange(timeRange: string): BarRange | null {
  const [rawStart, rawEnd] = (timeRange ?? '').split('/');
  const start = (rawStart ?? '').trim();
  const end = (rawEnd ?? '').trim();
  if (!start || !end || Number.isNaN(parseDate(start)) || Number.isNaN(parseDate(end))) {
    return null;
  }
  return parseDate(end) < parseDate(start) ? { start, end: start } : { start, end };
}

/** Axis zoom: 'recent' = trailing 6 months (default); 'all' = full extent. */
export type TimelineZoom = 'recent' | 'all';

export interface ComputeScaleOptions {
  dayWidth?: number;
  /** Done/archived kanban tasks — the history layer (裁决5:进数据源). */
  history?: TimelineHistoryTask[];
  zoom?: TimelineZoom;
}

/** today minus `months` calendar months (ISO). */
function monthsAgo(today: string, months: number): string {
  const d = new Date(parseDate(today));
  d.setMonth(d.getMonth() - months);
  return formatDate(d.getTime());
}

/**
 * Axis bounds over everything the timeline draws: today, task bars, project
 * time ranges, milestone dates, habit week strips, and the done/archived
 * history layer — padded one week left and two weeks right so the today line
 * never hugs an edge.
 *
 * zoom 'recent' (default): the domain is the trailing-6-month window, extended
 * only by items that overlap it (older history renders clipped at the left
 * edge — 平移/「全部」 zoom reveals it). Dirty dates are clamped with a
 * console warning so they can never flatten the axis again.
 */
export function computeScale(
  board: ProjectsBoardResponse,
  options: ComputeScaleOptions | number = {},
): TimelineScale {
  const opts: ComputeScaleOptions = typeof options === 'number' ? { dayWidth: options } : options;
  const dayWidth = opts.dayWidth ?? 14;
  const zoom = opts.zoom ?? 'recent';
  const today = board.today || formatDate(Date.now());
  const windowStart = monthsAgo(today, 6);
  let min = parseDate(zoom === 'all' ? today : windowStart) - 7 * DAY_MS;
  let max = parseDate(today) + 14 * DAY_MS;
  const visit = (range: BarRange | null) => {
    const clamped = range ? clampRange(range, today) : null;
    if (!clamped) {
      return;
    }
    // In the recent window, history older than 6 months cannot pull the
    // domain left; overlapping items are clipped to the window edge.
    if (zoom === 'recent' && parseDate(clamped.end) < parseDate(windowStart)) {
      return;
    }
    const startMs =
      zoom === 'recent'
        ? Math.max(parseDate(clamped.start), parseDate(windowStart) - 7 * DAY_MS)
        : parseDate(clamped.start);
    min = Math.min(min, startMs);
    max = Math.max(max, parseDate(clamped.end));
  };
  const visitProject = (project: ProjectsBoardProject) => {
    visit(projectRange(project.time_range ?? ''));
    for (const list of [project.queue, project.doing, project.someday]) {
      for (const task of list ?? []) {
        visit(taskBarRange(task, today));
      }
    }
    for (const milestone of project.milestones ?? []) {
      visitMilestone(milestone);
    }
  };
  const visitMilestone = (milestone: ProjectsBoardMilestone) => {
    if (milestone.date && !Number.isNaN(parseDate(milestone.date))) {
      visit({ start: milestone.date, end: milestone.date });
    }
  };
  for (const goal of board.goals ?? []) {
    for (const project of goal.projects ?? []) {
      visitProject(project);
    }
  }
  for (const project of board.ungrouped_projects ?? []) {
    visitProject(project);
  }
  for (const task of board.unassigned_tasks ?? []) {
    visit(taskBarRange(task, today));
  }
  for (const habit of board.habits ?? []) {
    const week = habit.week ?? [];
    if (week.length > 0) {
      visit({ start: week[0].date, end: week[week.length - 1].date });
    }
  }
  for (const task of opts.history ?? []) {
    visit(historyBarRange(task));
  }
  return { start: formatDate(min), end: formatDate(max), dayWidth };
}

/** Total axis width in px (both endpoints inclusive). */
export function scaleWidth(scale: TimelineScale): number {
  return (daysBetween(scale.start, scale.end) + 1) * scale.dayWidth;
}
