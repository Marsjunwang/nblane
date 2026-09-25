// 习惯阶段计划 helpers — pure derivations over GET .../habit-plans items,
// shared by the 日课栏 badge, the check-in plan binding, the lane 阶段计划
// section, and the create modal (project-mount pick + 按天 assembly).

import type { HabitPlan, HabitPlanDailyTasks, ProjectsBoardProject } from '../../api/types';

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

/** True when the plan carries per-day tasks (daily granularity; sparse —
 * days without an entry are rest days). */
export function planHasDaily(plan: HabitPlan): boolean {
  return (plan.daily_tasks ?? []).length > 0;
}

/** 日课栏 badge label: 「28天减脂 · W2/4」, daily plans add the day
 * (「28天减脂 · 第3天 · W1/4」) while today is inside the window
 * (current_day 0 = outside → week-only label). */
export function planBadgeLabel(plan: HabitPlan): string {
  const total = planTotalWeeks(plan);
  const parts: string[] = [plan.title];
  const day = planHasDaily(plan) ? (plan.current_day ?? 0) : 0;
  if (day > 0) {
    parts.push(`第${day}天`);
  }
  if (total > 0) {
    parts.push(`W${Math.max(plan.current_week ?? 0, 1)}/${total}`);
  }
  return parts.join(' · ');
}

/** 计划小节 progress line: 「W2/4 · 第 12/28 天 · 打卡 9/28 天 · 32%」.
 * The 第 N/M 天 segment appears only for daily plans inside the window;
 * weekly-only plans keep the W/打卡/percent form. */
export function planProgressLabel(plan: HabitPlan): string {
  const totalWeeks = planTotalWeeks(plan);
  const parts: string[] = [];
  if (totalWeeks > 0) {
    parts.push(`W${Math.max(plan.current_week ?? 0, 1)}/${totalWeeks}`);
  }
  const day = planHasDaily(plan) ? (plan.current_day ?? 0) : 0;
  if (day > 0) {
    parts.push(`第 ${day}/${plan.days_total ?? 0} 天`);
  }
  parts.push(`打卡 ${plan.days_done ?? 0}/${plan.days_total ?? 0} 天`);
  parts.push(`${Math.round((plan.completion_rate ?? 0) * 100)}%`);
  return parts.join(' · ');
}

export interface PlanTodayTasks {
  /** Header label, e.g. 今日任务(第 3 天). */
  label: string;
  tasks: string[];
  /** True → render the 「今日休息/自由安排」 fallback line instead of tasks. */
  restDay: boolean;
}

/** 今日任务 readout for daily plans: the server's today_tasks (empty = a
 * rest day), labeled with the current day number. */
export function planTodayTasks(plan: HabitPlan): PlanTodayTasks {
  const tasks = (plan.today_tasks ?? []).map((task) => task.trim()).filter(Boolean);
  return {
    label: `今日任务(第 ${plan.current_day ?? 0} 天):`,
    tasks,
    restDay: tasks.length === 0,
  };
}

// --- Create modal: project mount pick + 按天 assembly ------------------------

/** Sentinel option value for 「不挂项目」 in the mount dropdown. */
export const NO_PROJECT_PICK = '__none__';

/** Active (non-archived/completed) case options for the 项目挂载 dropdown,
 * label = case title. */
export function activeCaseOptions(
  projects: ProjectsBoardProject[],
): { value: string; label: string }[] {
  return projects
    .filter((project) => project.status === 'active')
    .map((project) => ({ value: project.id, label: project.title || project.id }));
}

/** The case a plan would auto-mount to: the habit's first active case
 * (case.habit_id matches), '' when none exists. */
export function autoMountCaseId(projects: ProjectsBoardProject[], habitId: string): string {
  const hit = projects.find(
    (project) => project.status === 'active' && project.habit_id && project.habit_id === habitId,
  );
  return hit?.id ?? '';
}

/** Map the mount dropdown pick to the POST body's tri-state project_id:
 * 不挂项目 → '' (explicitly project-less), the auto-mount case → undefined
 * (omit the field; the backend links the same case), any other case → its id. */
export function resolvePlanProjectId(pick: string, autoCaseId: string): string | undefined {
  if (pick === NO_PROJECT_PICK) {
    return '';
  }
  if (autoCaseId && pick === autoCaseId) {
    return undefined;
  }
  return pick;
}

/** Resize a per-row text array as the plan length moves, preserving input. */
export function resizeRowTexts(prev: string[], count: number): string[] {
  return Array.from({ length: Math.max(count, 0) }, (_, index) => prev[index] ?? '');
}

/** Assemble sparse daily_tasks from one input row per day: a blank row is a
 * rest day (omitted), a non-blank row is that day's single task (1-based). */
export function assembleDailyTasks(dayTexts: string[]): HabitPlanDailyTasks[] {
  const out: HabitPlanDailyTasks[] = [];
  dayTexts.forEach((raw, index) => {
    const task = raw.trim();
    if (task) {
      out.push({ day: index + 1, tasks: [task] });
    }
  });
  return out;
}
