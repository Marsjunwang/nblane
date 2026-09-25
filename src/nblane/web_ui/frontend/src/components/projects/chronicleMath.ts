// Pure math for the 大事记 (chronicle) view — the S-shaped boustrophedon
// (牛耕式) read of the SAME projects data the swimlane timeline renders.
//
// Layout model: rows tile a contiguous time axis, newest on top. Row 0
// contains the anchor date (默认锚定今天, ~25% future room); row i covers
// exactly `span` days and is `span*i` days older than row 0. Even rows are
// mirrored (newest at the LEFT edge, read 右→左), odd rows read 左→右, so the
// elbow between row i and row i+1 always drops on the side where row i's
// oldest end and row i+1's newest end already meet.
//
// Empty stretches (>21 days without any event) compress into ~34px `///`
// break blocks; each row clips the breaks to its own range, so a break may
// span row boundaries. Clicking a break expands it for the session (the
// expansion set is component state — never persisted).
//
// Labels collide like map annotations: try above, then below, then one font
// notch smaller on each side, else hide (hover 铭文卡 covers hidden ones).
// The today marker is a pinned above-side participant so labels avoid it.

import type {
  KanbanSection,
  KanbanTask,
  ProjectsBoardProject,
  ProjectsBoardTask,
} from '../../api/types';
import type { BarRange } from './timelineMath';
import { daysBetween, estimateLabelWidth, formatDate, parseDate, shiftDate } from './timelineMath';

// ---------------------------------------------------------------------------
// 行划分 (row tiling)
// ---------------------------------------------------------------------------

export const CHRONICLE_DEFAULT_SPAN = 90;
export const CHRONICLE_SPAN_MIN = 7;
export const CHRONICLE_SPAN_MAX = 365;

export function clampChronicleSpan(span: number): number {
  if (!Number.isFinite(span)) {
    return CHRONICLE_DEFAULT_SPAN;
  }
  return Math.min(Math.max(Math.round(span), CHRONICLE_SPAN_MIN), CHRONICLE_SPAN_MAX);
}

export interface ChronicleRow {
  /** 0 = top row (newest). */
  index: number;
  /** Oldest day on the row (ISO, inclusive). */
  start: string;
  /** Newest day on the row (ISO, inclusive). */
  end: string;
  /** true = reads left→right (oldest at left); false = mirrored (newest at left). */
  ltr: boolean;
}

/**
 * Tile `rowCount` rows downward from the anchor (row 0's newest date). Rows
 * are contiguous: row i's end is `anchor - i*span`, its start `span-1` days
 * earlier. Even rows mirror; odd rows read left→right.
 */
export function buildChronicleRows(anchor: string, span: number, rowCount: number): ChronicleRow[] {
  const rows: ChronicleRow[] = [];
  const safeSpan = Math.max(1, Math.round(span));
  for (let i = 0; i < Math.max(0, rowCount); i += 1) {
    const end = shiftDate(anchor, -i * safeSpan);
    rows.push({ index: i, start: shiftDate(end, -(safeSpan - 1)), end, ltr: i % 2 === 1 });
  }
  return rows;
}

/** Default anchor: today with ~25% of the span kept as future room. */
export function defaultChronicleAnchor(today: string, span: number): string {
  return shiftDate(today, Math.round(clampChronicleSpan(span) * 0.25));
}

/** Loose pan bounds (same sane domain as the timeline window). */
const PAN_MIN = '2015-01-01';

/** Shift the anchor by whole days (negative = toward the past), loosely clamped. */
export function panChronicle(anchor: string, days: number, today: string): string {
  if (!days) {
    return anchor;
  }
  const shifted = shiftDate(anchor, days);
  const max = formatDate(parseDate(today) + 366 * 2 * 86_400_000);
  if (shifted < PAN_MIN) {
    return PAN_MIN;
  }
  return shifted > max ? max : shifted;
}

/**
 * Ctrl+wheel zoom: re-anchor so `focusDate` keeps its row and its time
 * fraction (0 = at the row's newest end, 1 = at its oldest end) under the
 * new span.
 */
export function zoomChronicle(options: {
  newSpan: number;
  focusDate: string;
  focusRow: number;
  focusFrac: number;
}): string {
  const span = clampChronicleSpan(options.newSpan);
  const frac = Math.min(Math.max(options.focusFrac, 0), 1);
  return shiftDate(
    options.focusDate,
    Math.max(0, options.focusRow) * span + Math.round(frac * (span - 1)),
  );
}

// ---------------------------------------------------------------------------
// 事件收集 (event collection — five strokes, archive included)
// ---------------------------------------------------------------------------

export type ChronicleKind = 'done' | 'doing' | 'queue' | 'someday';

export interface ChronicleEvent {
  /** Task id (drives 铭文卡 / 去编辑). */
  id: string;
  kind: ChronicleKind;
  title: string;
  /** Owning project id ('' = unassigned — always visible, no badge). */
  projectId: string;
  /** Project badge (≤4 chars; '' for unassigned). */
  badge: string;
  /** Archive task or archived-project task → faded badge + mark. */
  archived: boolean;
  start: string;
  end: string;
  /** someday only: planned_start already arrived → 朱砂 dashed dot. */
  overdue: boolean;
  /** Short date label, e.g. `09-12` or `09-08 → 09-25`. */
  dateLabel: string;
}

/** 徽章: first 4 chars of the project title. */
export function projectBadge(title: string): string {
  return title.trim().slice(0, 4);
}

function mmdd(date: string): string {
  return date.slice(5);
}

function rangeLabel(start: string, end: string): string {
  return start === end ? mmdd(start) : `${mmdd(start)} → ${mmdd(end)}`;
}

function valid(date: string | null | undefined): date is string {
  return !!date && !Number.isNaN(parseDate(date));
}

export interface CollectChronicleOptions {
  /** Lane projects plus archived projects (the timeline's full lane set). */
  projects: ProjectsBoardProject[];
  unassigned: ProjectsBoardTask[];
  kanbanSections?: KanbanSection[];
  kanbanArchive?: KanbanTask[];
  today: string;
}

/**
 * Collect every event the chronicle draws, from the same sources as the
 * swimlane timeline: board queue/doing/someday lanes (+ unassigned), the
 * kanban Done section and kanban-archive.md. Point events (done/someday)
 * have start === end. Tasks with no anchor date are skipped (the chronicle
 * is a read of time — the 未排期 list stays a kanban/timeline concern).
 */
export function collectChronicleEvents(options: CollectChronicleOptions): ChronicleEvent[] {
  const { projects, unassigned, kanbanSections, kanbanArchive, today } = options;
  const events: ChronicleEvent[] = [];
  const archivedProjectIds = new Set(
    projects.filter((project) => project.status === 'archived').map((project) => project.id),
  );
  const projectMeta = new Map<string, { badge: string; archived: boolean }>();
  for (const project of projects) {
    projectMeta.set(project.id, {
      badge: projectBadge(project.title || project.id),
      archived: project.status === 'archived',
    });
  }
  const metaFor = (projectId: string) =>
    projectMeta.get(projectId) ?? { badge: '', archived: archivedProjectIds.has(projectId) };

  const pushBoardTask = (task: ProjectsBoardTask, column: string, projectId: string) => {
    const { badge, archived } = metaFor(projectId);
    if (column === 'doing') {
      const start = valid(task.started_on) ? task.started_on : task.planned_start;
      if (!valid(start)) {
        return;
      }
      const end = start <= today ? today : start;
      events.push({
        id: task.id,
        kind: 'doing',
        title: task.title,
        projectId,
        badge,
        archived,
        start,
        end,
        overdue: false,
        dateLabel: rangeLabel(start, end),
      });
      return;
    }
    if (column === 'queue') {
      if (!valid(task.planned_start)) {
        return;
      }
      const start = task.planned_start;
      const end = valid(task.planned_end) && task.planned_end >= start ? task.planned_end : start;
      events.push({
        id: task.id,
        kind: 'queue',
        title: task.title,
        projectId,
        badge,
        archived,
        start,
        end,
        overdue: false,
        dateLabel: rangeLabel(start, end),
      });
      return;
    }
    if (column === 'someday') {
      if (!valid(task.planned_start)) {
        return;
      }
      events.push({
        id: task.id,
        kind: 'someday',
        title: task.title,
        projectId,
        badge,
        archived,
        start: task.planned_start,
        end: task.planned_start,
        overdue: task.planned_start <= today,
        dateLabel: mmdd(task.planned_start),
      });
    }
  };

  for (const project of projects) {
    for (const task of project.queue ?? []) {
      pushBoardTask(task, 'queue', project.id);
    }
    for (const task of project.doing ?? []) {
      pushBoardTask(task, 'doing', project.id);
    }
    for (const task of project.someday ?? []) {
      pushBoardTask(task, 'someday', project.id);
    }
  }
  for (const task of unassigned) {
    pushBoardTask(task, task.column, '');
  }

  const pushDone = (task: KanbanTask, archivedTask: boolean) => {
    const date = valid(task.completed_on)
      ? task.completed_on
      : valid(task.planned_end)
        ? task.planned_end
        : '';
    if (!date) {
      return;
    }
    const projectId = task.project_id ?? '';
    const { badge, archived } = metaFor(projectId);
    events.push({
      id: task.id,
      kind: 'done',
      title: task.title,
      projectId,
      badge,
      archived: archived || archivedTask,
      start: date,
      end: date,
      overdue: false,
      dateLabel: mmdd(date),
    });
  };
  for (const section of kanbanSections ?? []) {
    if (section.name !== 'Done') {
      continue;
    }
    for (const task of section.tasks ?? []) {
      pushDone(task, false);
    }
  }
  for (const task of kanbanArchive ?? []) {
    pushDone(task, true);
  }
  return events;
}

/**
 * Project filter: null = 全选; otherwise events whose project is unselected
 * drop out. Unassigned events (projectId '') are immune — same as the
 * timeline's 未归属 lane.
 */
export function filterChronicleEvents(
  events: ChronicleEvent[],
  selected: ReadonlySet<string> | null,
): ChronicleEvent[] {
  if (!selected) {
    return events;
  }
  return events.filter((event) => event.projectId === '' || selected.has(event.projectId));
}

// ---------------------------------------------------------------------------
// 断轴 (break compression)
// ---------------------------------------------------------------------------

/** Gaps strictly longer than this (days without any event) compress. */
export const BREAK_MIN_GAP_DAYS = 21;
/** Compressed break width on the axis. */
export const BREAK_WIDTH_PX = 34;

export interface ChronicleBreak {
  /** First empty day (ISO). */
  start: string;
  /** Last empty day (ISO). */
  end: string;
  days: number;
  /** Stable key (`start_end`) for the expand set. */
  key: string;
}

/**
 * Interior gaps between event intervals: merge all event spans, then any
 * stretch strictly between two spans longer than BREAK_MIN_GAP_DAYS becomes
 * a break. Leading/trailing emptiness (window edge → first/last event) never
 * breaks — there is nothing on one side to compress between.
 */
export function detectBreaks(
  events: Pick<ChronicleEvent, 'start' | 'end'>[],
  minGapDays: number = BREAK_MIN_GAP_DAYS,
): ChronicleBreak[] {
  const spans = events
    .filter((event) => valid(event.start) && valid(event.end))
    .map((event) => ({
      start: event.start <= event.end ? event.start : event.end,
      end: event.start <= event.end ? event.end : event.start,
    }))
    .sort((a, b) => (a.start < b.start ? -1 : a.start > b.start ? 1 : 0));
  const merged: BarRange[] = [];
  for (const span of spans) {
    const last = merged[merged.length - 1];
    // Overlapping or ADJACENT spans merge — a break needs real empty days.
    if (last && span.start <= shiftDate(last.end, 1)) {
      last.end = span.end > last.end ? span.end : last.end;
    } else {
      merged.push({ ...span });
    }
  }
  const breaks: ChronicleBreak[] = [];
  for (let i = 0; i < merged.length - 1; i += 1) {
    const start = shiftDate(merged[i].end, 1);
    const end = shiftDate(merged[i + 1].start, -1);
    const days = daysBetween(start, end) + 1;
    if (days > minGapDays) {
      breaks.push({ start, end, days, key: `${start}_${end}` });
    }
  }
  return breaks;
}

// ---------------------------------------------------------------------------
// 行坐标 (row scale: date ↔ x, with breaks and mirroring)
// ---------------------------------------------------------------------------

export interface RowSegment {
  /** Segment range in TIME order (oldest → newest, ISO, inclusive). */
  start: string;
  end: string;
  /** X span in unmirrored plot coords (time runs left→right). */
  x0: number;
  x1: number;
  gap: boolean;
  /** Break key when gap (for the expand toggle / hover card). */
  breakKey?: string;
  breakDays?: number;
}

export interface RowScale {
  row: ChronicleRow;
  segments: RowSegment[];
  /** px per uncompressed day inside this row (0 when the row is all break). */
  dayWidth: number;
  plotX: number;
  plotW: number;
}

export interface BuildRowScaleOptions {
  plotX: number;
  plotW: number;
  /** Break keys currently expanded (rendered uncompressed). */
  expandedKeys?: ReadonlySet<string>;
  /** Breaks wider than this share of the plot are left uncompressed. */
  maxBreakCover?: number;
}

/**
 * Compress the breaks clipping this row and lay out day columns. Segments
 * are emitted in TIME order; `dateToX`/`xToDate` apply the row mirroring.
 * A break spanning a row boundary contributes its clipped portion to each
 * row it touches.
 */
export function buildRowScale(
  row: ChronicleRow,
  breaks: ChronicleBreak[],
  options: BuildRowScaleOptions,
): RowScale {
  const { plotX, plotW } = options;
  const expanded = options.expandedKeys ?? new Set<string>();
  const totalDays = daysBetween(row.start, row.end) + 1;
  const inside = breaks
    .filter((brk) => !expanded.has(brk.key))
    .map((brk) => ({
      start: brk.start > row.start ? brk.start : row.start,
      end: brk.end < row.end ? brk.end : row.end,
      key: brk.key,
    }))
    .filter((brk) => brk.start <= brk.end)
    .sort((a, b) => (a.start < b.start ? -1 : 1));
  // Cap the compressed share so a dense row of breaks can never eat the plot.
  const maxBreaks = Math.max(1, Math.floor((plotW * (options.maxBreakCover ?? 0.6)) / BREAK_WIDTH_PX));
  const used = inside.slice(0, maxBreaks);
  const gapDays = used.reduce((sum, brk) => sum + daysBetween(brk.start, brk.end) + 1, 0);
  const normalDays = totalDays - gapDays;
  const dayWidth = normalDays > 0 ? Math.max(0, (plotW - used.length * BREAK_WIDTH_PX) / normalDays) : 0;

  const segments: RowSegment[] = [];
  let cursor = row.start;
  let px = plotX;
  for (const brk of used) {
    if (brk.start > cursor) {
      const segEnd = shiftDate(brk.start, -1);
      const width = (daysBetween(cursor, segEnd) + 1) * dayWidth;
      segments.push({ start: cursor, end: segEnd, x0: px, x1: px + width, gap: false });
      px += width;
    }
    segments.push({
      start: brk.start,
      end: brk.end,
      x0: px,
      x1: px + BREAK_WIDTH_PX,
      gap: true,
      breakKey: brk.key,
      breakDays: daysBetween(brk.start, brk.end) + 1,
    });
    px += BREAK_WIDTH_PX;
    cursor = shiftDate(brk.end, 1);
  }
  if (cursor <= row.end) {
    segments.push({ start: cursor, end: row.end, x0: px, x1: plotX + plotW, gap: false });
  }
  return { row, segments, dayWidth, plotX, plotW };
}

/** Mirror an unmirrored (time-order) x into the row's visual direction. */
function mirrorX(scale: RowScale, x: number): number {
  return scale.row.ltr ? x : scale.plotX + scale.plotW - (x - scale.plotX);
}

/** X of a date inside the row; null when the date is outside the row range. */
export function chronicleDateToX(scale: RowScale, date: string): number | null {
  if (date < scale.row.start || date > scale.row.end) {
    return null;
  }
  for (const seg of scale.segments) {
    if (date >= seg.start && date <= seg.end) {
      if (seg.gap) {
        // Days inside a break spread across the compressed block so the
        // inverse mapping stays sane.
        const span = daysBetween(seg.start, seg.end) + 1;
        const frac = span > 1 ? daysBetween(seg.start, date) / span : 0.5;
        return mirrorX(scale, seg.x0 + frac * (seg.x1 - seg.x0));
      }
      return mirrorX(scale, seg.x0 + daysBetween(seg.start, date) * scale.dayWidth);
    }
  }
  return null;
}

/** Date at an x inside the row (inverse of chronicleDateToX, clamped). */
export function chronicleXToDate(scale: RowScale, x: number): string {
  const unmirrored = scale.row.ltr ? x : scale.plotX + scale.plotW - (x - scale.plotX);
  const clamped = Math.min(Math.max(unmirrored, scale.plotX), scale.plotX + scale.plotW);
  for (let i = 0; i < scale.segments.length; i += 1) {
    const seg = scale.segments[i];
    // Half-open [x0, x1) so a boundary pixel belongs to the FOLLOWING
    // segment (a day column, not the break's right edge); the last segment
    // stays closed at the plot edge.
    const last = i === scale.segments.length - 1;
    if (clamped >= seg.x0 && (clamped < seg.x1 || (last && clamped <= seg.x1))) {
      if (seg.gap) {
        const span = daysBetween(seg.start, seg.end) + 1;
        const frac = seg.x1 > seg.x0 ? (clamped - seg.x0) / (seg.x1 - seg.x0) : 0.5;
        return shiftDate(seg.start, Math.min(Math.floor(frac * span), span - 1));
      }
      if (scale.dayWidth <= 0) {
        return seg.start;
      }
      const days = Math.min(
        Math.floor((clamped - seg.x0) / scale.dayWidth + 1e-6),
        daysBetween(seg.start, seg.end),
      );
      return shiftDate(seg.start, Math.max(0, days));
    }
  }
  return clamped >= scale.plotX + scale.plotW ? scale.row.end : scale.row.start;
}

/** Clip an event range to a row; null when the event misses the row. */
export function clipRangeToRow(range: BarRange, row: ChronicleRow): BarRange | null {
  if (range.end < row.start || range.start > row.end) {
    return null;
  }
  return {
    start: range.start < row.start ? row.start : range.start,
    end: range.end > row.end ? row.end : range.end,
  };
}

// ---------------------------------------------------------------------------
// 自适应行数
// ---------------------------------------------------------------------------

export const CHRONICLE_ROW_HEIGHT = 120;
export const CHRONICLE_ELBOW_HEIGHT = 36;

/** Rows that fit the available height (min 1). */
export function chronicleRowsForHeight(height: number): number {
  if (!Number.isFinite(height) || height <= 0) {
    return 1;
  }
  return Math.max(
    1,
    Math.floor((height + CHRONICLE_ELBOW_HEIGHT) / (CHRONICLE_ROW_HEIGHT + CHRONICLE_ELBOW_HEIGHT)),
  );
}

// ---------------------------------------------------------------------------
// 标签碰撞 (map-annotation label layout)
// ---------------------------------------------------------------------------

export type LabelSide = 'above' | 'below';
export type LabelSize = 'normal' | 'small' | 'hidden';

export interface ChronicleLabelItem {
  id: string;
  /** Anchor x on the axis. */
  x: number;
  /** Full-size label width (px). */
  width: number;
  /** Pinned side (today marker) — placed first, never displaced. */
  pinnedSide?: LabelSide;
}

export interface ChronicleLabelPlacement {
  id: string;
  /** Clamped label center x (kept inside the plot). */
  cx: number;
  side: LabelSide;
  size: LabelSize;
}

/** Rough label width: badge + title line vs the date line, whichever wins. */
export function chronicleLabelWidth(title: string, badge: string, dateLabel: string): number {
  const head = badge ? `[${badge}] ${title}` : title;
  return Math.max(estimateLabelWidth(head), estimateLabelWidth(dateLabel));
}

/**
 * Collision layout: pinned items first (they reserve their slot), then each
 * label tries above → below at full size, then above → below one font notch
 * smaller (smallScale), else it hides (the hover 铭文卡 covers it). Centers
 * clamp inside the plot so edge labels never clip.
 */
export function layoutChronicleLabels(
  items: ChronicleLabelItem[],
  options: { plotX: number; plotW: number; pad?: number; smallScale?: number; edge?: number },
): ChronicleLabelPlacement[] {
  const pad = options.pad ?? 6;
  const smallScale = options.smallScale ?? 0.85;
  const edge = options.edge ?? 4;
  const occupied: Record<LabelSide, [number, number][]> = { above: [], below: [] };
  const placements = new Map<string, ChronicleLabelPlacement>();

  const fits = (side: LabelSide, cx: number, width: number): boolean => {
    const lo = cx - width / 2 - pad;
    const hi = cx + width / 2 + pad;
    return !occupied[side].some(([a, b]) => lo < b && hi > a);
  };
  const clampCenter = (x: number, width: number): number =>
    Math.min(
      Math.max(x, options.plotX + width / 2 + edge),
      options.plotX + options.plotW - width / 2 - edge,
    );
  const place = (item: ChronicleLabelItem, side: LabelSide, size: LabelSize, width: number) => {
    const cx = clampCenter(item.x, width);
    occupied[side].push([cx - width / 2 - pad, cx + width / 2 + pad]);
    placements.set(item.id, { id: item.id, cx, side, size });
  };

  const sorted = [...items].sort((a, b) => a.x - b.x || (a.id < b.id ? -1 : 1));
  for (const item of sorted.filter((entry) => entry.pinnedSide)) {
    place(item, item.pinnedSide!, 'normal', item.width);
  }
  for (const item of sorted.filter((entry) => !entry.pinnedSide)) {
    let placed = false;
    for (const size of ['normal', 'small'] as const) {
      const width = size === 'normal' ? item.width : item.width * smallScale;
      for (const side of ['above', 'below'] as const) {
        const cx = clampCenter(item.x, width);
        if (fits(side, cx, width)) {
          place(item, side, size, width);
          placed = true;
          break;
        }
      }
      if (placed) {
        break;
      }
    }
    if (!placed) {
      const cx = clampCenter(item.x, item.width);
      placements.set(item.id, { id: item.id, cx, side: 'above', size: 'hidden' });
    }
  }
  return items.map((item) => placements.get(item.id)!);
}

// ---------------------------------------------------------------------------
// URL 视图状态 (view=story 还原)
// ---------------------------------------------------------------------------

export interface ChronicleUrlState {
  span?: number;
  /** Top row's newest date (the pan state). */
  top?: string;
  /** Present (even empty) when the param exists; absent = use stored filter. */
  projects?: Set<string>;
}

export function decodeChronicleParams(params: URLSearchParams): ChronicleUrlState {
  const state: ChronicleUrlState = {};
  const span = Number(params.get('cspan'));
  if (Number.isFinite(span) && span > 0) {
    state.span = clampChronicleSpan(span);
  }
  const top = params.get('ctop');
  if (top && !Number.isNaN(parseDate(top))) {
    state.top = top;
  }
  if (params.has('cproj')) {
    const raw = params.get('cproj') ?? '';
    state.projects = new Set(raw ? raw.split(',').filter(Boolean) : []);
  }
  return state;
}

/**
 * Serialize the story view state (null = delete the key). The span and top
 * date always ride the URL so a refresh or shared link restores the exact
 * S-fold; the filter only writes when it narrows below 全选.
 */
export function encodeChronicleParams(state: {
  span: number;
  top: string;
  selectedProjects: ReadonlySet<string> | null;
}): Record<string, string | null> {
  return {
    cspan: String(clampChronicleSpan(state.span)),
    ctop: state.top,
    cproj: state.selectedProjects ? [...state.selectedProjects].sort().join(',') : null,
  };
}
