// Pure helpers for the 日课栏 month heatmap (GitHub-style trailing-90-day
// grid). Data source: projects-board habits[].recent_days ({date, count,
// checkin_ids} ascending), merged with the authoritative week dots for
// today. Filled cells with known check-in ids support 销印 (DELETE one row).

import type { ProjectsBoardHabit } from '../../api/types';
import { formatDate, parseDate } from './timelineMath';

const DAY_MS = 86_400_000;

export interface HeatmapCell {
  date: string;
  count: number;
  /** Check-in row ids backing this day (empty for id-less legacy rows). */
  checkinIds: string[];
  /** After board.today — rendered dimmed, never clickable. */
  future: boolean;
}

export type HeatmapWeek = HeatmapCell[];

/** date -> total check-in count for the day (recent_days ∪ done week dots). */
export function habitCountMap(habit: ProjectsBoardHabit): Map<string, number> {
  const map = new Map<string, number>();
  for (const day of habit.recent_days ?? []) {
    if (day.date) {
      map.set(day.date, (map.get(day.date) ?? 0) + (day.count ?? 0));
    }
  }
  // The week strip is authoritative for the current ISO week; a just-posted
  // check-in may not have landed in recent_days yet.
  for (const day of habit.week ?? []) {
    if (day.done && (map.get(day.date) ?? 0) === 0) {
      map.set(day.date, 1);
    }
  }
  return map;
}

/** date -> check-in row ids for the day (recent_days only, oldest first). */
export function habitCheckinIdMap(habit: ProjectsBoardHabit): Map<string, string[]> {
  const map = new Map<string, string[]>();
  for (const day of habit.recent_days ?? []) {
    if (!day.date) {
      continue;
    }
    const ids = (day.checkin_ids ?? []).filter((id) => id.length > 0);
    if (ids.length > 0) {
      map.set(day.date, [...(map.get(day.date) ?? []), ...ids]);
    }
  }
  return map;
}

/**
 * Trailing-90-day grid aligned to whole weeks (Monday-first columns), ending
 * at the week containing `today`. Cells past today are marked future.
 */
export function buildHeatmapWeeks(habit: ProjectsBoardHabit, today: string): HeatmapWeek[] {
  const todayMs = parseDate(today);
  if (Number.isNaN(todayMs)) {
    return [];
  }
  const counts = habitCountMap(habit);
  const checkinIds = habitCheckinIdMap(habit);
  const firstMs = todayMs - 89 * DAY_MS;
  const first = new Date(firstMs);
  // Align the grid start back to Monday (local time, like parseDate).
  const mondayOffset = (first.getDay() + 6) % 7;
  const startMs = firstMs - mondayOffset * DAY_MS;
  const weeks: HeatmapWeek[] = [];
  for (let cursor = startMs; cursor <= todayMs; cursor += 7 * DAY_MS) {
    const week: HeatmapWeek = [];
    for (let day = 0; day < 7; day += 1) {
      const ms = cursor + day * DAY_MS;
      const date = formatDate(ms);
      week.push({
        date,
        count: counts.get(date) ?? 0,
        checkinIds: checkinIds.get(date) ?? [],
        future: ms > todayMs,
      });
    }
    weeks.push(week);
  }
  return weeks;
}

/** 月白 → 泥金 intensity ramp for one cell. */
export function heatmapCellColor(count: number, maxCount: number): string {
  if (count <= 0) {
    return 'rgba(242, 237, 224, 0.07)';
  }
  const t = maxCount > 0 ? Math.min(count / maxCount, 1) : 1;
  const alpha = 0.3 + 0.7 * t;
  return `rgba(220, 174, 85, ${alpha.toFixed(2)})`;
}
