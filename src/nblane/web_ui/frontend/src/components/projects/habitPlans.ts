// 习惯阶段计划 helpers — pure derivations over GET .../habit-plans items,
// shared by the 日课栏 badge, the check-in plan binding, and the lane
// 阶段计划 section.

import type { HabitPlan } from '../../api/types';

/** Total week count of a plan (weekly_tasks is the authored source). */
export function planTotalWeeks(plan: HabitPlan): number {
  return plan.weekly_tasks?.length ?? plan.weeks?.length ?? 0;
}

/** Today inside the inclusive [start_date, end_date] window (ISO strings
 * compare lexicographically). */
export function planInWindow(plan: HabitPlan, today: string): boolean {
  if (!today || !plan.start_date || !plan.end_date) {
    return false;
  }
  return plan.start_date <= today && today <= plan.end_date;
}

/** Active plans bound to one habit (the list endpoint may be pre-filtered
 * by status; the status check stays as a belt-and-braces guard). */
export function activePlansForHabit(plans: HabitPlan[], habitId: string): HabitPlan[] {
  return plans.filter((plan) => plan.habit_id === habitId && plan.status === 'active');
}

/** Plans a check-in may bind to: active, same habit, today in window. */
export function checkinPlansForHabit(
  plans: HabitPlan[],
  habitId: string,
  today: string,
): HabitPlan[] {
  return activePlansForHabit(plans, habitId).filter((plan) => planInWindow(plan, today));
}

/** 日课栏 badge label: 「28天减脂 · W2/4」(current week clamped to ≥1). */
export function planBadgeLabel(plan: HabitPlan): string {
  const total = planTotalWeeks(plan);
  const current = Math.max(plan.current_week ?? 0, 1);
  return total > 0 ? `${plan.title} · W${current}/${total}` : plan.title;
}
