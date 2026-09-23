/* Briefing-line chronicle flavor (design §8): the base briefing text stays
 * primary; this appends a small "this month" coda derived from the
 * append-only chronicle (goal.added / goal.completed / north_star.rewritten).
 * Pure function — vitest-covered. */

import type { ChronicleEntry } from '../api/types';

function monthKey(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

/**
 * Render the chronicle coda (e.g. "本月新立目标 1，新镌 2 星"), or '' when
 * nothing happened this month. `today` is injectable for tests.
 */
export function chronicleFlavor(entries: ChronicleEntry[], today: Date = new Date()): string {
  const month = monthKey(today);
  let added = 0;
  let completed = 0;
  let rewritten = 0;
  for (const e of entries) {
    if (!e.date || !String(e.date).startsWith(month)) continue;
    if (e.kind === 'goal.added') added += 1;
    else if (e.kind === 'goal.completed') completed += 1;
    else if (e.kind === 'north_star.rewritten') rewritten += 1;
  }
  const parts: string[] = [];
  if (added > 0) parts.push(`本月新立目标 ${added}`);
  if (completed > 0) parts.push(`新镌 ${completed} 星`);
  if (rewritten > 0) parts.push('北极星已重刻');
  return parts.join('，');
}

/** Append the coda inside the briefing's closing bracket, keeping the base
 * text primary. */
export function withChronicleFlavor(base: string, flavor: string): string {
  if (!flavor) return base;
  if (base.endsWith('。」')) {
    return `${base.slice(0, -2)}，${flavor}。」`;
  }
  if (base.endsWith('」')) return `${base.slice(0, -1)}，${flavor}」`;
  return `${base} ${flavor}`;
}
