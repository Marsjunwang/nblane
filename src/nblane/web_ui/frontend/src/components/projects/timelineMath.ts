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

/**
 * Thin axis ticks so adjacent labels keep at least `minPx` between them
 * (语义密度: at year-level zoom the month labels would mash into a band).
 * The first tick is always kept.
 */
export function thinTicks<T extends { x: number }>(ticks: T[], minPx: number): T[] {
  const kept: T[] = [];
  let lastX = Number.NEGATIVE_INFINITY;
  for (const tick of ticks) {
    if (tick.x - lastX >= minPx) {
      kept.push(tick);
      lastX = tick.x;
    }
  }
  return kept;
}

export interface BarRange {
  start: string;
  end: string;
}

/** Done/archived task from kanban.md sections or kanban-archive.md — the timeline history layer. */
export interface TimelineHistoryTask {
  id: string;
  title: string;
  project_id?: string | null;
  planned_start?: string | null;
  planned_end?: string | null;
  started_on?: string | null;
  completed_on?: string | null;
  /** True for kanban-archive.md entries (rendered 淡月白, fainter than Done 刻痕). */
  archived?: boolean;
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

/**
 * Axis zoom presets: 周/月/季/半年 pin a fixed day span ending just past
 * today (today sits at ~75% of the window); 'all' covers the full extent of
 * the data. Between presets the day width is continuous (Ctrl+wheel).
 */
export type TimelineZoom = 'week' | 'month' | 'quarter' | 'half' | 'all';

/** Window span in days for each fixed preset. */
export const ZOOM_SPAN_DAYS: Record<Exclude<TimelineZoom, 'all'>, number> = {
  week: 7,
  month: 30,
  quarter: 90,
  half: 181,
};

/** Continuous day-width bounds (无级缩放). */
export const DAY_WIDTH_MIN = 1;
export const DAY_WIDTH_MAX = 40;
export const DEFAULT_DAY_WIDTH = 14;

export function clampDayWidth(width: number): number {
  return Math.min(Math.max(width, DAY_WIDTH_MIN), DAY_WIDTH_MAX);
}

/** Below this day width (季/年级别) task labels hide; bars/刻痕 only. */
export const LABEL_DAY_WIDTH_MIN = 3;

export function labelsVisible(scale: TimelineScale): boolean {
  return scale.dayWidth >= LABEL_DAY_WIDTH_MIN;
}

export interface ComputeScaleOptions {
  /** Explicit px/day (wheel zoom); clamped to DAY_WIDTH_MIN..MAX. */
  dayWidth?: number;
  /** Viewport px available for the axis — derives dayWidth when no explicit override. */
  fitWidth?: number;
  /** Done/archived kanban tasks — the history layer (裁决5:进数据源). */
  history?: TimelineHistoryTask[];
  zoom?: TimelineZoom;
  /** Explicit focus window (项目聚焦): exact domain, no data-driven extension. */
  window?: BarRange;
}

/**
 * Axis bounds over everything the timeline draws: today, task bars, project
 * time ranges, milestone dates, habit week strips, and the done/archived
 * history layer.
 *
 * - Fixed presets (周/月/季/半年): the window is exactly the preset span with
 *   today at ~75%; items overlapping the window extend only the right edge,
 *   older ones clip at the left (Ctrl+wheel out / 全部 reveals them).
 * - 'all': the domain extends over the full data extent, padded 7d left and
 *   14d right around today.
 * - `window` (项目聚焦): the domain is exactly the given range.
 *
 * Dirty dates are clamped with a console warning so they can never flatten
 * the axis again. dayWidth comes from the explicit override (clamped), else
 * derived from fitWidth, else the default.
 */
export function computeScale(
  board: ProjectsBoardResponse,
  options: ComputeScaleOptions | number = {},
): TimelineScale {
  const opts: ComputeScaleOptions = typeof options === 'number' ? { dayWidth: options } : options;
  const zoom = opts.zoom ?? 'half';
  const today = board.today || formatDate(Date.now());
  const focus = opts.window ? clampRange(opts.window, today) : null;
  const presetDays = zoom === 'all' ? 0 : ZOOM_SPAN_DAYS[zoom];
  const windowStart =
    zoom === 'all' ? '' : shiftDate(today, -Math.round(presetDays * 0.75));
  let min: number;
  let max: number;
  if (focus) {
    min = parseDate(focus.start);
    max = parseDate(focus.end);
  } else if (zoom === 'all') {
    min = parseDate(today) - 7 * DAY_MS;
    max = parseDate(today) + 14 * DAY_MS;
  } else {
    min = parseDate(windowStart);
    max = parseDate(shiftDate(windowStart, presetDays));
  }
  const visit = (range: BarRange | null) => {
    const clamped = range ? clampRange(range, today) : null;
    if (!clamped || focus) {
      return;
    }
    // Fixed presets: items older than the window cannot pull the domain left;
    // overlapping items extend only the right edge.
    if (zoom !== 'all') {
      if (parseDate(clamped.end) < min) {
        return;
      }
      max = Math.max(max, parseDate(clamped.end));
      return;
    }
    min = Math.min(min, parseDate(clamped.start));
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
  const start = formatDate(min);
  const end = formatDate(max);
  const spanDays = daysBetween(start, end) + 1;
  const dayWidth =
    opts.dayWidth != null
      ? clampDayWidth(opts.dayWidth)
      : opts.fitWidth && opts.fitWidth > 0
        ? clampDayWidth(opts.fitWidth / spanDays)
        : DEFAULT_DAY_WIDTH;
  return { start, end, dayWidth };
}

/** Total axis width in px (both endpoints inclusive). */
export function scaleWidth(scale: TimelineScale): number {
  return (daysBetween(scale.start, scale.end) + 1) * scale.dayWidth;
}

// ---------------------------------------------------------------------------
// 行内错峰 (sub-lane stacking)
// ---------------------------------------------------------------------------

export const TASK_BAR_HEIGHT = 14;
export const HISTORY_BAR_HEIGHT = 7;
/** Sub-lane heights: 刻痕-only lanes compress; task lanes keep breathing room. */
export const TASK_LANE_HEIGHT = 24;
export const HISTORY_LANE_HEIGHT = 14;
export const LANE_GAP = 2;
export const ROW_PAD_Y = 4;
export const MIN_ROW_HEIGHT = 30;

export interface LaneLayoutInput<T> {
  item: T;
  range: BarRange;
  /** Task bars are tall; history 刻痕 are short. */
  tall: boolean;
}

export interface LaneLayoutEntry<T> extends LaneLayoutInput<T> {
  /** Sub-lane index (0 = top). */
  lane: number;
  /** Bar top offset (px) within the row, centering the bar in its sub-lane. */
  top: number;
  /** Height (px) of this entry's sub-lane. */
  laneHeight: number;
}

export interface LaneLayout<T> {
  entries: LaneLayoutEntry<T>[];
  laneCount: number;
  rowHeight: number;
}

/**
 * Interval-graph coloring over one swimlane row: sort by start, greedily
 * assign the first sub-lane whose last bar ends before this one starts
 * (inclusive day overlap counts as collision). Row height adapts to the
 * sub-lane count; 刻痕-only lanes compress to HISTORY_LANE_HEIGHT.
 */
export function layoutLane<T>(items: LaneLayoutInput<T>[]): LaneLayout<T> {
  const sorted = items
    .map((entry, index) => ({ entry, index }))
    .sort((a, b) => {
      const d = parseDate(a.entry.range.start) - parseDate(b.entry.range.start);
      if (d !== 0) {
        return d;
      }
      const e = parseDate(a.entry.range.end) - parseDate(b.entry.range.end);
      return e !== 0 ? e : a.index - b.index;
    });
  const laneEnds: number[] = [];
  const laneTall: boolean[] = [];
  const assignments: { input: LaneLayoutInput<T>; lane: number }[] = [];
  for (const { entry } of sorted) {
    const startMs = parseDate(entry.range.start);
    const endMs = parseDate(entry.range.end);
    let lane = laneEnds.findIndex((lastEnd) => lastEnd < startMs);
    if (lane < 0) {
      lane = laneEnds.length;
      laneEnds.push(endMs);
      laneTall.push(false);
    } else {
      laneEnds[lane] = endMs;
    }
    laneTall[lane] = laneTall[lane] || entry.tall;
    assignments.push({ input: entry, lane });
  }
  const laneHeights = laneTall.map((tall) => (tall ? TASK_LANE_HEIGHT : HISTORY_LANE_HEIGHT));
  const laneTops: number[] = [];
  let cursor = ROW_PAD_Y;
  for (const height of laneHeights) {
    laneTops.push(cursor);
    cursor += height + LANE_GAP;
  }
  const contentHeight = laneHeights.reduce((sum, h) => sum + h, 0);
  const rowHeight = Math.max(
    MIN_ROW_HEIGHT,
    ROW_PAD_Y * 2 + contentHeight + LANE_GAP * Math.max(laneHeights.length - 1, 0),
  );
  const entries: LaneLayoutEntry<T>[] = assignments.map(({ input, lane }) => {
    const laneHeight = laneHeights[lane];
    const barHeight = input.tall ? TASK_BAR_HEIGHT : HISTORY_BAR_HEIGHT;
    return {
      ...input,
      lane,
      laneHeight,
      top: laneTops[lane] + (laneHeight - barHeight) / 2,
    };
  });
  return { entries, laneCount: laneHeights.length, rowHeight };
}

/**
 * Free px to the right of each laid-out bar before the next bar in the same
 * sub-lane (or the axis end). Entries must come from layoutLane (sorted by
 * start). Feeds the right-hang label rule.
 */
export function rightSpaces<T>(entries: LaneLayoutEntry<T>[], scale: TimelineScale): number[] {
  const total = scaleWidth(scale);
  return entries.map((entry, index) => {
    const endX = dateToX(entry.range.end, scale) + scale.dayWidth;
    for (let j = index + 1; j < entries.length; j += 1) {
      const next = entries[j];
      if (next.lane === entry.lane) {
        return Math.max(0, dateToX(next.range.start, scale) - endX);
      }
    }
    return Math.max(0, total - endX);
  });
}

/**
 * 项目 time_range 地色带的高度:贴着行基线的一条细带,不再随错峰行高
 * 撑成整块 — 4–6px,且不超过行高的 25%(衬底角色,不是色块).
 */
export function groundBandHeight(rowHeight: number): number {
  return Math.max(4, Math.min(6, Math.floor(rowHeight * 0.25)));
}

// ---------------------------------------------------------------------------
// 任务名标签 (label placement)
// ---------------------------------------------------------------------------

/** Bars at least this wide embed their label inside (left-aligned, ellipsis). */
export const LABEL_INSIDE_MIN_WIDTH = 60;

/** Rough px width of a task title at the timeline label size (CJK ≈ 2× ASCII). */
export function estimateLabelWidth(title: string): number {
  let width = 4;
  for (const ch of title) {
    width += (ch.codePointAt(0) ?? 0) > 0x2e7f ? 11 : 6;
  }
  return width;
}

export type LabelPlacement = 'inside' | 'right' | 'none';

/**
 * Label rule: wide bars embed the label; narrow bars hang it on the right
 * (dim) when it fits before the next bar in the same sub-lane; extremely
 * narrow bars show nothing (hover 铭文卡 covers them).
 */
export function labelPlacement(
  barWidth: number,
  labelWidth: number,
  rightSpace: number,
): LabelPlacement {
  if (barWidth >= LABEL_INSIDE_MIN_WIDTH) {
    return 'inside';
  }
  if (rightSpace >= labelWidth + 6) {
    return 'right';
  }
  return 'none';
}

// ---------------------------------------------------------------------------
// 状态即笔法 (status → stroke)
// ---------------------------------------------------------------------------

export type BarStatus = 'queue' | 'doing' | 'done';

export function barStatus(task: { done?: boolean; column?: string }): BarStatus {
  if (task.done || task.column === 'done') {
    return 'done';
  }
  return task.column === 'queue' || task.column === 'someday' ? 'queue' : 'doing';
}

/** 逾期: planned_end already past and the task is not finished. */
export function isOverdue(
  task: { done?: boolean; column?: string; planned_end?: string | null },
  today: string,
): boolean {
  if (!today || barStatus(task) === 'done') {
    return false;
  }
  const end = task.planned_end ?? '';
  return !!end && !Number.isNaN(parseDate(end)) && end < today;
}

// ---------------------------------------------------------------------------
// 项目筛选 + 聚焦
// ---------------------------------------------------------------------------

/** localStorage key for the project multi-select (array of project ids). */
export const TIMELINE_FILTER_KEY = 'nblane.timeline.projects';

/**
 * Selected project ids from storage, intersected with the ids that exist
 * now; no stored value (or junk) means 默认全选.
 */
export function loadProjectFilter(storage: Storage, allIds: string[]): Set<string> {
  const raw = storage.getItem(TIMELINE_FILTER_KEY);
  if (raw) {
    try {
      const parsed: unknown = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        const known = new Set(allIds);
        return new Set(parsed.filter((id): id is string => typeof id === 'string' && known.has(id)));
      }
    } catch {
      // fall through to select-all
    }
  }
  return new Set(allIds);
}

export function saveProjectFilter(storage: Storage, selected: ReadonlySet<string>): void {
  try {
    storage.setItem(TIMELINE_FILTER_KEY, JSON.stringify([...selected]));
  } catch {
    // storage full / unavailable — filtering still works for the session
  }
}

/**
 * Hide unchecked project rows wholesale; a group header disappears when all
 * its sub-projects are hidden. (日课行 lives outside groups and is immune.)
 */
export function filterGroupsBySelection<T extends { projects: { id: string }[] }>(
  groups: T[],
  selected: ReadonlySet<string>,
): T[] {
  return groups
    .map((group) => ({ ...group, projects: group.projects.filter((p) => selected.has(p.id)) }))
    .filter((group) => group.projects.length > 0);
}

/**
 * Focus window for a lane: the project time_range when present, else the
 * min~max span of its task bars; padded 5% on both ends (at least 1 day).
 * Returns null when the project has nothing dated to focus on.
 */
export function focusWindowForProject(
  project: Pick<ProjectsBoardProject, 'time_range' | 'queue' | 'doing' | 'someday'>,
  today: string,
): BarRange | null {
  let range = projectRange(project.time_range ?? '');
  if (!range) {
    let min = Number.POSITIVE_INFINITY;
    let max = Number.NEGATIVE_INFINITY;
    for (const list of [project.queue, project.doing, project.someday]) {
      for (const task of list ?? []) {
        const bar = taskBarRange(task, today);
        if (!bar) {
          continue;
        }
        min = Math.min(min, parseDate(bar.start));
        max = Math.max(max, parseDate(bar.end));
      }
    }
    if (!Number.isFinite(min) || !Number.isFinite(max)) {
      return null;
    }
    range = { start: formatDate(min), end: formatDate(max) };
  }
  const pad = Math.max(1, Math.round((daysBetween(range.start, range.end) + 1) * 0.05));
  return { start: shiftDate(range.start, -pad), end: shiftDate(range.end, pad) };
}
