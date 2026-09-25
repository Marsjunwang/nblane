// Someday 到期判定 — a Someday / Maybe card's planned_start is its
// 「期望激活日」: once it reaches today the board badge swaps from the dashed
// gold 「someday」 frame to a 朱砂 (boardPalette.overdue) 「该激活了」 outline.
// Deliberately separate from timelineMath.isOverdue, which reads planned_end
// (missed deadline) — someday due reads planned_start (time to activate) and
// is inclusive of today.

/**
 * True when a someday card's planned_start has arrived (≤ today). Either
 * side missing/invalid → false (no badge change for unscheduled cards).
 * ISO yyyy-mm-dd strings compare lexicographically.
 */
export function isSomedayDue(plannedStart: string | null | undefined, today: string): boolean {
  if (!plannedStart || !today) {
    return false;
  }
  if (
    Number.isNaN(Date.parse(`${plannedStart}T00:00:00`)) ||
    Number.isNaN(Date.parse(`${today}T00:00:00`))
  ) {
    return false;
  }
  return plannedStart <= today;
}
