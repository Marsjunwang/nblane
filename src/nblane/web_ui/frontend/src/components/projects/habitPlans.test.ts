// habit-plans pure helpers: badge/progress labels with day granularity,
// 今日任务 rest-day fallback, the create modal's mount-pick mapping, and the
// 按天 editor assembly (sparse daily_tasks, blank row = rest day).

import { describe, expect, it } from 'vitest';

import type { HabitPlan, ProjectsBoardProject } from '../../api/types';
import {
  NO_PROJECT_PICK,
  activeCaseOptions,
  assembleDailyTasks,
  autoMountCaseId,
  planBadgeLabel,
  planProgressLabel,
  planTodayTasks,
  resizeRowTexts,
  resolvePlanProjectId,
} from './habitPlans';

function makePlan(overrides: Record<string, unknown>): HabitPlan {
  return {
    id: 'hp1',
    habit_id: 'exercise',
    title: '28天减脂',
    start_date: '2026-09-01',
    end_date: '2026-09-28',
    status: 'active',
    current_week: 2,
    current_day: 0,
    days_done: 9,
    days_total: 28,
    completion_rate: 0.32,
    weekly_tasks: [
      { week: 1, tasks: ['晨跑 3 次'] },
      { week: 2, tasks: ['控糖'] },
      { week: 3, tasks: ['复盘'] },
      { week: 4, tasks: ['巩固'] },
    ],
    ...overrides,
  } as HabitPlan;
}

function makeCase(overrides: Record<string, unknown>): ProjectsBoardProject {
  return {
    id: 'case-1',
    title: '减脂项目',
    status: 'active',
    kind: 'habit',
    habit_id: '',
    ...overrides,
  } as ProjectsBoardProject;
}

describe('planBadgeLabel', () => {
  it('weekly-only plans keep the week-only label', () => {
    expect(planBadgeLabel(makePlan({}))).toBe('28天减脂 · W2/4');
  });

  it('daily plans add the day while inside the window', () => {
    const plan = makePlan({
      daily_tasks: [{ day: 1, tasks: ['晨跑'] }],
      current_day: 3,
      current_week: 1,
    });
    expect(planBadgeLabel(plan)).toBe('28天减脂 · 第3天 · W1/4');
  });

  it('daily plans outside the window (current_day 0) drop the day segment', () => {
    const plan = makePlan({ daily_tasks: [{ day: 1, tasks: ['晨跑'] }], current_day: 0 });
    expect(planBadgeLabel(plan)).toBe('28天减脂 · W2/4');
  });
});

describe('planProgressLabel', () => {
  it('daily plans inside the window show 第 N/M 天 between week and check-ins', () => {
    const plan = makePlan({
      daily_tasks: [{ day: 1, tasks: ['晨跑'] }],
      current_day: 12,
      current_week: 2,
    });
    expect(planProgressLabel(plan)).toBe('W2/4 · 第 12/28 天 · 打卡 9/28 天 · 32%');
  });

  it('weekly-only plans keep the week/打卡/percent form', () => {
    expect(planProgressLabel(makePlan({}))).toBe('W2/4 · 打卡 9/28 天 · 32%');
  });
});

describe('planTodayTasks', () => {
  it('carries the server today_tasks labeled with the current day', () => {
    const readout = planTodayTasks(
      makePlan({ current_day: 3, today_tasks: ['晨跑 5km', ' 拉伸 '] }),
    );
    expect(readout.label).toBe('今日任务(第 3 天):');
    expect(readout.tasks).toEqual(['晨跑 5km', '拉伸']);
    expect(readout.restDay).toBe(false);
  });

  it('empty today_tasks is a rest day', () => {
    const readout = planTodayTasks(makePlan({ current_day: 5, today_tasks: [] }));
    expect(readout.restDay).toBe(true);
    expect(readout.tasks).toEqual([]);
  });
});

describe('project mount pick', () => {
  const cases = [
    makeCase({ id: 'case-auto', title: '减脂项目', habit_id: 'exercise' }),
    makeCase({ id: 'case-other', title: '其他项目', kind: 'learning' }),
    makeCase({ id: 'case-archived', title: '旧项目', status: 'archived' }),
  ];

  it('options list active cases only, labeled by title', () => {
    expect(activeCaseOptions(cases)).toEqual([
      { value: 'case-auto', label: '减脂项目' },
      { value: 'case-other', label: '其他项目' },
    ]);
  });

  it('the auto-mount case is the habit’s first active case', () => {
    expect(autoMountCaseId(cases, 'exercise')).toBe('case-auto');
    expect(autoMountCaseId(cases, 'unknown-habit')).toBe('');
  });

  it('maps the pick to the tri-state project_id', () => {
    // 默认项(自动挂接的 case)→ 不传 project_id。
    expect(resolvePlanProjectId('case-auto', 'case-auto')).toBeUndefined();
    // 改选其他 case → 传 id。
    expect(resolvePlanProjectId('case-other', 'case-auto')).toBe('case-other');
    // 不挂项目 → 空串。
    expect(resolvePlanProjectId(NO_PROJECT_PICK, 'case-auto')).toBe('');
    // 没有自动 case 时选中的任何 case 都显式传递。
    expect(resolvePlanProjectId('case-other', '')).toBe('case-other');
  });
});

describe('按天 editor assembly', () => {
  it('resizeRowTexts grows/shrinks preserving typed rows', () => {
    expect(resizeRowTexts(['a', 'b'], 4)).toEqual(['a', 'b', '', '']);
    expect(resizeRowTexts(['a', 'b', 'c'], 2)).toEqual(['a', 'b']);
    expect(resizeRowTexts([], 0)).toEqual([]);
  });

  it('assembleDailyTasks emits sparse 1-based entries, blank rows = rest days', () => {
    expect(assembleDailyTasks(['晨跑', '', '  拉伸  ', ' '])).toEqual([
      { day: 1, tasks: ['晨跑'] },
      { day: 3, tasks: ['拉伸'] },
    ]);
    expect(assembleDailyTasks(['', ''])).toEqual([]);
  });
});
