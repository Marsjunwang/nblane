// Habit-plan UI: 创建弹窗 (项目挂载下拉映射 + 按天编辑器行数联动/组装),
// 计划小节 (今日任务/休息日文案 + 删除确认:输名不匹配禁提交、选项进 body)。

import { fireEvent, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import type { HabitPlan, ProjectsBoardHabit } from '../../api/types';
import { jsonResponse, renderWithProviders } from '../../test/render';
import { NewHabitPlanModal } from './NewHabitPlanModal';
import { HabitPlanSection } from './ProjectLane';

const HABIT = {
  id: 'exercise',
  title: '锻炼',
  streak: 0,
  total_checkins: 0,
  week: [],
  recent_days: [],
} as unknown as ProjectsBoardHabit;

const BOARD = {
  profile: 'alice',
  today: '2026-09-25',
  north_star: '',
  goals: [],
  habits: [HABIT],
  ungrouped_projects: [
    {
      id: 'case-auto',
      title: '减脂项目',
      status: 'active',
      kind: 'habit',
      habit_id: 'exercise',
    },
    { id: 'case-other', title: '其他项目', status: 'active', kind: 'learning', habit_id: '' },
    { id: 'case-archived', title: '旧项目', status: 'archived', kind: 'work', habit_id: '' },
  ],
  unassigned_tasks: [],
};

function makeDailyPlan(overrides: Record<string, unknown>): HabitPlan {
  return {
    id: 'hp1',
    habit_id: 'exercise',
    title: '28天减脂',
    start_date: '2026-09-23',
    end_date: '2026-10-20',
    status: 'active',
    current_week: 1,
    current_day: 3,
    days_done: 2,
    days_total: 28,
    completion_rate: 0.07,
    daily_tasks: [{ day: 1, tasks: ['晨跑'] }],
    today_tasks: ['晨跑 5km'],
    weeks: [
      { week: 1 },
      { week: 2 },
      { week: 3 },
      { week: 4 },
    ],
    ...overrides,
  } as unknown as HabitPlan;
}

type FetchHandler = (url: string, init?: RequestInit) => Response | undefined;

function stubFetch(handler?: FetchHandler) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const custom = handler?.(url, init);
    if (custom) {
      return custom;
    }
    if (url.includes('/profiles/alice/projects-board')) {
      return jsonResponse(200, BOARD);
    }
    return jsonResponse(404, { detail: 'not found' });
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('NewHabitPlanModal 按天编辑器', () => {
  it('默认按天,行数跟随起止日期联动(空行 = 休息日)', async () => {
    stubFetch();
    renderWithProviders(
      <NewHabitPlanModal
        profile="alice"
        habit={HABIT}
        today="2026-09-25"
        opened
        onClose={() => {}}
      />,
    );

    // 默认 2026-09-25 → +27 天 = 28 行。
    expect(await screen.findByTestId('habit-plan-day-exercise-28')).toBeInTheDocument();
    expect(screen.queryByTestId('habit-plan-day-exercise-29')).not.toBeInTheDocument();

    // 缩短到 3 天 → 行数联动收缩。
    fireEvent.change(screen.getByTestId('habit-plan-end-exercise'), {
      target: { value: '2026-09-27' },
    });
    expect(await screen.findByTestId('habit-plan-day-exercise-3')).toBeInTheDocument();
    expect(screen.queryByTestId('habit-plan-day-exercise-4')).not.toBeInTheDocument();
  });

  it('默认挂载自动 case,提交组装 daily_tasks 且不传 project_id', async () => {
    let posted: Record<string, unknown> | null = null;
    stubFetch((url, init) => {
      if (url.endsWith('/profiles/alice/habit-plans') && init?.method === 'POST') {
        posted = JSON.parse(String(init.body)) as Record<string, unknown>;
        return jsonResponse(200, { ok: true, plan: {}, kanban_card_ids: ['kb_1'] });
      }
      return undefined;
    });
    renderWithProviders(
      <NewHabitPlanModal
        profile="alice"
        habit={HABIT}
        today="2026-09-25"
        opened
        onClose={() => {}}
      />,
    );

    // 项目下拉默认选中 habit 自动挂接的 active case(看板数据异步到达后再断言),
    // 归档 case 不出现在选项里。jsdom 中下拉层 display:none,选项按 hidden 查询。
    const mount = (await screen.findByTestId('habit-plan-project-exercise')) as HTMLInputElement;
    await waitFor(() => expect(mount.value).toBe('减脂项目(自动)'));
    fireEvent.click(mount);
    expect(await screen.findByRole('option', { name: '不挂项目', hidden: true })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: '其他项目', hidden: true })).toBeInTheDocument();
    expect(screen.queryByRole('option', { name: '旧项目', hidden: true })).not.toBeInTheDocument();

    fireEvent.change(await screen.findByTestId('habit-plan-day-exercise-1'), {
      target: { value: '晨跑 5km' },
    });
    fireEvent.click(screen.getByTestId('habit-plan-submit-exercise'));

    await waitFor(() => expect(posted).not.toBeNull());
    expect(posted!.daily_tasks).toEqual([{ day: 1, tasks: ['晨跑 5km'] }]);
    expect(posted!.weekly_tasks).toBeUndefined();
    expect('project_id' in posted!).toBe(false);
  });

  it('改选「不挂项目」提交 project_id 空串,改选其他 case 传其 id', async () => {
    const bodies: Record<string, unknown>[] = [];
    stubFetch((url, init) => {
      if (url.endsWith('/profiles/alice/habit-plans') && init?.method === 'POST') {
        bodies.push(JSON.parse(String(init.body)) as Record<string, unknown>);
        return jsonResponse(200, { ok: true, plan: {}, kanban_card_ids: [] });
      }
      return undefined;
    });

    const first = renderWithProviders(
      <NewHabitPlanModal
        profile="alice"
        habit={HABIT}
        today="2026-09-25"
        opened
        onClose={() => {}}
      />,
    );
    fireEvent.change(await screen.findByTestId('habit-plan-day-exercise-2'), {
      target: { value: '跳绳' },
    });
    const mount1 = screen.getByTestId('habit-plan-project-exercise') as HTMLInputElement;
    await waitFor(() => expect(mount1.value).toBe('减脂项目(自动)'));
    fireEvent.click(mount1);
    fireEvent.click(await screen.findByRole('option', { name: '不挂项目', hidden: true }));
    fireEvent.click(screen.getByTestId('habit-plan-submit-exercise'));
    await waitFor(() => expect(bodies).toHaveLength(1));
    expect(bodies[0].daily_tasks).toEqual([{ day: 2, tasks: ['跳绳'] }]);
    expect(bodies[0].project_id).toBe('');
    first.unmount();

    renderWithProviders(
      <NewHabitPlanModal
        profile="alice"
        habit={HABIT}
        today="2026-09-25"
        opened
        onClose={() => {}}
      />,
    );
    fireEvent.change(await screen.findByTestId('habit-plan-day-exercise-1'), {
      target: { value: '晨跑' },
    });
    const mount2 = screen.getByTestId('habit-plan-project-exercise') as HTMLInputElement;
    await waitFor(() => expect(mount2.value).toBe('减脂项目(自动)'));
    fireEvent.click(mount2);
    fireEvent.click(await screen.findByRole('option', { name: '其他项目', hidden: true }));
    fireEvent.click(screen.getByTestId('habit-plan-submit-exercise'));
    await waitFor(() => expect(bodies).toHaveLength(2));
    expect(bodies[1].project_id).toBe('case-other');
  });
});

describe('HabitPlanSection 今日任务与删除', () => {
  it('daily 计划显示今日任务(第 N 天),空则显示休息日文案', () => {
    stubFetch();
    const { unmount } = renderWithProviders(
      <HabitPlanSection profile="alice" plans={[makeDailyPlan({})]} />,
    );
    expect(screen.getByTestId('habit-plan-today-tasks-hp1')).toHaveTextContent(
      '今日任务(第 3 天)',
    );
    expect(screen.getByTestId('habit-plan-today-tasks-hp1')).toHaveTextContent('晨跑 5km');
    expect(screen.getByTestId('habit-plan-card-hp1')).toHaveTextContent('第 3/28 天');
    unmount();

    renderWithProviders(
      <HabitPlanSection profile="alice" plans={[makeDailyPlan({ today_tasks: [] })]} />,
    );
    expect(screen.getByTestId('habit-plan-rest-day-hp1')).toHaveTextContent('今日休息/自由安排');
  });

  it('删除确认:输名不匹配禁提交,选项进入 DELETE body', async () => {
    let deleted: { body: Record<string, unknown>; method: string } | null = null;
    stubFetch((url, init) => {
      if (url.endsWith('/profiles/alice/habit-plans/hp1') && init?.method === 'DELETE') {
        deleted = { body: JSON.parse(String(init.body)) as Record<string, unknown>, method: 'DELETE' };
        return jsonResponse(200, { ok: true, deleted_id: 'hp1', cards_removed: 0 });
      }
      return undefined;
    });
    renderWithProviders(
      <HabitPlanSection profile="alice" plans={[makeDailyPlan({})]} />,
    );

    fireEvent.click(screen.getByTestId('habit-plan-delete-open-hp1'));
    const confirm = await screen.findByTestId('delete-habit-plan-confirm-hp1');
    expect(confirm).toBeDisabled();

    // 预告后果:打卡历史保留。
    expect(screen.getByTestId('delete-habit-plan-preview-hp1')).toHaveTextContent('打卡历史保留');

    // 默认勾选「同时删除未完成的周卡」、不勾「记入大事记」;逐项翻转。
    const cards = screen.getByTestId('delete-habit-plan-delete-cards-hp1');
    const chronicle = screen.getByTestId('delete-habit-plan-record-chronicle-hp1');
    expect(cards).toBeChecked();
    expect(chronicle).not.toBeChecked();
    fireEvent.click(cards);
    fireEvent.click(chronicle);

    // 输名不匹配 → 禁提交;逐字输入后解锁。
    fireEvent.change(screen.getByTestId('delete-habit-plan-confirm-title-hp1'), {
      target: { value: '28天减' },
    });
    expect(confirm).toBeDisabled();
    fireEvent.change(screen.getByTestId('delete-habit-plan-confirm-title-hp1'), {
      target: { value: '28天减脂' },
    });
    expect(confirm).toBeEnabled();

    fireEvent.click(confirm);
    await waitFor(() => expect(deleted).not.toBeNull());
    expect(deleted!.body).toEqual({
      confirm_title: '28天减脂',
      delete_open_cards: false,
      record_chronicle: true,
    });
  });
});
