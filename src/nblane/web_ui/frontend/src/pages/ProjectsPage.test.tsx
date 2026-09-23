import { act, fireEvent, screen, waitFor, within } from '@testing-library/react';
import { cleanNotifications } from '@mantine/notifications';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes, useLocation } from 'react-router-dom';

import { jsonResponse, renderWithProviders } from '../test/render';
import { KanbanRedirect, ProjectBoardRedirect, ProjectsPage } from './ProjectsPage';

// jsdom has no layout; capture every DndContext (one per lane) and drive
// onDragEnd programmatically, same approach as the old KanbanPage tests.
interface FakeDragEvent {
  active: { id: string };
  over: { id: string } | null;
}
const { dndContexts } = vi.hoisted(() => ({
  dndContexts: [] as { onDragEnd?: (event: FakeDragEvent) => void }[],
}));
vi.mock('@dnd-kit/core', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@dnd-kit/core')>();
  return {
    ...actual,
    DndContext: (props: React.ComponentProps<typeof actual.DndContext>) => {
      dndContexts.push(props as unknown as { onDragEnd?: (event: FakeDragEvent) => void });
      return <actual.DndContext {...props} />;
    },
  };
});

function makeTask(overrides: Record<string, unknown>) {
  return {
    id: '',
    title: '',
    section: 'Queue',
    column: 'queue',
    done: false,
    context: '',
    why: '',
    started_on: null,
    completed_on: null,
    planned_start: null,
    planned_end: null,
    project_id: '',
    milestone_id: '',
    tags: '',
    ...overrides,
  };
}

const BOARD = {
  profile: 'alice',
  today: '2026-09-23',
  north_star: '成为机器人学习工程师',
  goals: [
    {
      id: 'g1',
      title: '2026持续学习',
      status: 'active',
      summary: '长期投入',
      target: '2026-12-31',
      projects: [
        {
          id: 'p1',
          title: '知识补全',
          status: 'active',
          kind: 'learning',
          visibility: 'private',
          summary: '',
          time_range: '',
          goal_refs: ['g1'],
          milestones: [],
          queue: [makeTask({ id: 'kb_1', title: '读 VLA 综述', project_id: 'p1' })],
          doing: [
            makeTask({
              id: 'kb_2',
              title: '完成技能树重构',
              section: 'Doing',
              column: 'doing',
              started_on: '2026-09-10',
              project_id: 'p1',
              tags: 'frontend',
            }),
          ],
          someday: [
            makeTask({
              id: 'kb_3',
              title: '研究 GAC',
              section: 'Someday / Maybe',
              column: 'someday',
              project_id: 'p1',
            }),
          ],
          column_counts: { queue: 1, doing: 1, someday: 1, done: 5 },
          done_count: 5,
          archived_done_count: 3,
          last_activity: '2026-09-20',
          habit_id: '',
        },
      ],
    },
  ],
  ungrouped_projects: [],
  unassigned_tasks: [makeTask({ id: 'kb_9', title: '无归属任务' })],
  habits: [
    {
      id: 'exercise',
      title: '保持锻炼',
      kind: 'health',
      cadence: 'daily',
      week: [
        { date: '2026-09-21', done: false, future: false },
        { date: '2026-09-22', done: false, future: false },
        { date: '2026-09-23', done: true, future: false },
        { date: '2026-09-24', done: false, future: true },
        { date: '2026-09-25', done: false, future: true },
        { date: '2026-09-26', done: false, future: true },
        { date: '2026-09-27', done: false, future: true },
      ],
      streak: 1,
      total_checkins: 38,
      last_checkin: '2026-09-23',
      project_id: '',
    },
  ],
  stats: { tasks_total: 4 },
};

const BOARD_ETAG = 'W/"board-1"';
const KANBAN_ETAG = 'W/"kanban-1"';
const PLAN_ETAG = 'W/"plan-1"';

// The full kanban.md section order: lane-local drop indices are translated
// to section-global ones through this board.
const KANBAN_BOARD = {
  profile: 'alice',
  total: 4,
  sections: [
    { name: 'Queue', tasks: [BOARD.goals[0].projects[0].queue[0], { id: 'kb_9', title: '无归属任务' }] },
    { name: 'Doing', tasks: [BOARD.goals[0].projects[0].doing[0]] },
    { name: 'Someday / Maybe', tasks: [BOARD.goals[0].projects[0].someday[0]] },
    { name: 'Done', tasks: [] },
  ],
};
const PLAN_TEMPLATES = { profile: 'alice', builtin: [], history: [] };
const PROJECT_BOARD = { profile: 'alice', cases: [], summary: {}, options: {} };

const MUTATION_RESULT = {
  ok: true,
  card: BOARD.goals[0].projects[0].queue[0],
  section: 'Doing',
  warnings: [],
  merged_external: false,
  merge_notices: [],
};

type FetchHandler = (url: string, init?: RequestInit) => Response | Promise<Response>;

function stubFetch(handler?: FetchHandler) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const method = init?.method ?? 'GET';
    const custom = handler?.(url, init);
    if (custom) {
      return custom;
    }
    if (url.endsWith('/profiles/alice/projects-board')) {
      return new Response(JSON.stringify(BOARD), {
        status: 200,
        headers: { 'Content-Type': 'application/json', ETag: BOARD_ETAG },
      });
    }
    if (url.endsWith('/profiles/alice/kanban')) {
      return new Response(JSON.stringify(KANBAN_BOARD), {
        status: 200,
        headers: { 'Content-Type': 'application/json', ETag: KANBAN_ETAG },
      });
    }
    if (url.endsWith('/profiles/alice/plan-templates')) {
      return new Response(JSON.stringify(PLAN_TEMPLATES), {
        status: 200,
        headers: { 'Content-Type': 'application/json', ETag: PLAN_ETAG },
      });
    }
    if (url.endsWith('/profiles/alice/project-board')) {
      return jsonResponse(200, PROJECT_BOARD);
    }
    if (method === 'POST') {
      return jsonResponse(200, MUTATION_RESULT);
    }
    return jsonResponse(404, { code: 'not_found', message: 'not found' });
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

let lastSearch = '';
function LocationProbe() {
  const location = useLocation();
  lastSearch = location.search;
  return null;
}

function renderPage(route = '/p/alice/projects') {
  dndContexts.length = 0;
  lastSearch = '';
  return renderWithProviders(
    <Routes>
      <Route
        path="/p/:name/projects"
        element={
          <>
            <ProjectsPage />
            <LocationProbe />
          </>
        }
      />
      <Route path="/p/:name/kanban" element={<KanbanRedirect />} />
      <Route path="/p/:name/project-board" element={<ProjectBoardRedirect />} />
    </Routes>,
    route,
  );
}

afterEach(() => {
  cleanNotifications();
  vi.unstubAllGlobals();
});

describe('ProjectsPage board view', () => {
  it('renders goal groups, lanes, someday badge cards, unassigned lane, habit dots and Done folds', async () => {
    stubFetch();
    renderPage();

    // Toolbar + group header.
    expect(await screen.findByText('alice · 项目')).toBeInTheDocument();
    expect(screen.getByTestId('north-star')).toHaveTextContent('成为机器人学习工程师');
    expect(screen.getByTestId('lane-group-g1')).toBeInTheDocument();
    expect(screen.getByTestId('lane-group-header-g1')).toHaveTextContent('目标 · 2026持续学习');
    expect(screen.getByTestId('lane-group-header-g1')).toHaveTextContent('2026-12-31');

    // Lane with Queue/Doing columns.
    const lane = screen.getByTestId('project-lane-p1');
    expect(within(lane).getByText('知识补全')).toBeInTheDocument();
    expect(within(lane).getByText('读 VLA 综述')).toBeInTheDocument();
    expect(within(lane).getByText('完成技能树重构')).toBeInTheDocument();
    expect(screen.getByTestId('lane-column-p1-queue')).toBeInTheDocument();
    expect(screen.getByTestId('lane-column-p1-doing')).toBeInTheDocument();

    // Someday renders as a dashed badge card inside the Queue column.
    const someday = screen.getByTestId('someday-card-kb_3');
    expect(someday).toHaveTextContent('someday');
    expect(screen.getByTestId('lane-column-p1-queue')).toContainElement(someday);

    // Done fold count includes archived tasks.
    expect(screen.getByTestId('done-count-p1')).toHaveTextContent('Done · 5（含归档 3）');

    // Unassigned lane (dashed gold) with its task.
    const unassigned = screen.getByTestId('unassigned-lane');
    expect(within(unassigned).getByText('无归属任务')).toBeInTheDocument();

    // Habit lane: 7 week dots (1 done), streak + check-in button.
    const habitLane = screen.getByTestId('habit-lane-exercise');
    expect(habitLane).toHaveTextContent('保持锻炼');
    expect(habitLane).toHaveTextContent('连续 1 天');
    expect(habitLane).toHaveTextContent('累计 38 次');
    expect(screen.getByTestId('habit-dot-exercise-2026-09-23')).toHaveAttribute(
      'data-done',
      'true',
    );
    expect(screen.getByTestId('habit-dot-exercise-2026-09-24')).toHaveAttribute(
      'data-done',
      'false',
    );
  });

  it('switches grouping to 按活动 (kind buckets)', async () => {
    stubFetch();
    renderPage();
    await screen.findByText('alice · 项目');

    fireEvent.click(screen.getByText('按活动'));

    expect(await screen.findByTestId('lane-group-learning')).toBeInTheDocument();
    expect(screen.queryByTestId('lane-group-g1')).not.toBeInTheDocument();
    expect(lastSearch).toContain('group=activity');
  });
});

describe('ProjectsPage selection & views', () => {
  it('opens the detail card from ?task= and closes it by dropping the param', async () => {
    stubFetch();
    renderPage('/p/alice/projects?task=kb_2');

    const card = await screen.findByTestId('task-detail-card');
    expect(card).toHaveTextContent('完成技能树重构');
    expect(card).toHaveTextContent('已进行 13 天');
    // eslint-disable-next-line no-console
    // The owning lane shows up as the 归属 select value (Mantine Select
    // syncs the displayed label one commit after the value lands).
    await waitFor(() =>
      expect(within(card).getByLabelText('归属变更')).toHaveValue('知识补全'),
    );

    fireEvent.click(within(card).getByRole('button', { name: '关闭详情' }));
    await waitFor(() => expect(screen.queryByTestId('task-detail-card')).not.toBeInTheDocument());
    expect(lastSearch).not.toContain('task=');
  });

  it('keeps the selection when switching to the timeline view', async () => {
    stubFetch();
    renderPage('/p/alice/projects?task=kb_2');
    await screen.findByTestId('task-detail-card');

    fireEvent.click(screen.getByText('时间轴'));

    expect(await screen.findByTestId('timeline-view')).toBeInTheDocument();
    // Selection survives the view switch (shared ?task= state).
    expect(screen.getByTestId('task-detail-card')).toHaveTextContent('完成技能树重构');
    expect(lastSearch).toContain('view=timeline');
    expect(lastSearch).toContain('task=kb_2');
  });

  it('renders the timeline view with month axis, today line and task bars', async () => {
    stubFetch();
    renderPage('/p/alice/projects?view=timeline');

    expect(await screen.findByTestId('timeline-view')).toBeInTheDocument();
    expect(screen.getByTestId('timeline-month-axis')).toBeInTheDocument();
    expect(screen.getByTestId('timeline-today-line')).toBeInTheDocument();
    // kb_2 has started_on → a bar; kb_1 has no dates → 未排期 row note.
    expect(screen.getByTestId('timeline-bar-kb_2')).toBeInTheDocument();
    expect(screen.getByTestId('unscheduled-p1')).toHaveTextContent('读 VLA 综述');
    // Habit strip with this week's done dot.
    expect(screen.getByTestId('timeline-habit-exercise')).toBeInTheDocument();
    expect(screen.getByTestId('timeline-habit-dot-exercise-2026-09-23')).toBeInTheDocument();
    // Clicking a bar selects the task (shared detail card).
    fireEvent.click(screen.getByTestId('timeline-bar-kb_2'));
    expect(await screen.findByTestId('task-detail-card')).toHaveTextContent('完成技能树重构');
  });

  it('redirects /kanban and /project-board to /projects preserving the query', async () => {
    stubFetch();
    renderPage('/p/alice/kanban?view=timeline&task=kb_2');
    // Lands on the projects page with the deep-link intact.
    expect(await screen.findByTestId('timeline-view')).toBeInTheDocument();
    expect(lastSearch).toContain('view=timeline');
    expect(lastSearch).toContain('task=kb_2');
  });
});

describe('ProjectsPage mutations', () => {
  it('in-lane drop posts move with target_section + to_index and the kanban ETag', async () => {
    const fetchMock = stubFetch();
    renderPage();
    await screen.findByText('读 VLA 综述');

    // The first mounted DndContext is lane p1's (Queue → Doing); the mock
    // re-pushes on every render, so index from the latest render batch.
    const context = dndContexts.at(-2);
    act(() => {
      context?.onDragEnd?.({ active: { id: 'kb_1' }, over: { id: 'lane::p1::doing' } });
    });

    expect(await screen.findByText('已移动')).toBeInTheDocument();
    const moveCall = fetchMock.mock.calls.find(
      ([input, init]) => String(input).endsWith('/move') && init?.method === 'POST',
    );
    expect(moveCall).toBeDefined();
    expect(String(moveCall?.[0])).toContain(
      `/kanban/cards/${encodeURIComponent('读 VLA 综述')}/move`,
    );
    expect(JSON.parse(String(moveCall?.[1]?.body))).toEqual({
      target_section: 'Doing',
      to_index: 1,
    });
    // Mutations use the kanban-file ETag, never the board ETag.
    expect((moveCall?.[1]?.headers as Record<string, string>)['If-Match']).toBe(KANBAN_ETAG);
  });

  it('check-in posts without If-Match on first use, then caches the ETag', async () => {
    const fetchMock = stubFetch((url, init) => {
      if (init?.method === 'POST' && url.endsWith('/checkins')) {
        return new Response(
          JSON.stringify({
            ok: true,
            checkin: { id: 'c1', date: '2026-09-23', habit_id: 'exercise' },
          }),
          { status: 201, headers: { 'Content-Type': 'application/json', ETag: 'W/"log-1"' } },
        );
      }
      return undefined as unknown as Response;
    });
    renderPage();
    const button = await screen.findByTestId('checkin-button-exercise');
    fireEvent.click(button);

    expect(await screen.findByText('已打卡')).toBeInTheDocument();
    const checkinCall = fetchMock.mock.calls.find(
      ([input, init]) => String(input).endsWith('/checkins') && init?.method === 'POST',
    );
    expect(checkinCall).toBeDefined();
    expect(JSON.parse(String(checkinCall?.[1]?.body))).toMatchObject({ habit: 'exercise' });
    expect((checkinCall?.[1]?.headers as Record<string, string>)['If-Match']).toBeUndefined();
  });

  it('detail card 归属变更 PATCHes project_id with the kanban ETag', async () => {
    const fetchMock = stubFetch();
    renderPage('/p/alice/projects?task=kb_9');
    const card = await screen.findByTestId('task-detail-card');

    // Unassigned task → assign to lane p1 via the 归属 select.
    const select = within(card).getByLabelText('归属变更');
    fireEvent.mouseDown(select);
    // Mantine renders option content in nested spans; match on textContent.
    await waitFor(() => {
      expect(
        Array.from(document.querySelectorAll('[role="option"]')).some(
          (el) => el.textContent === '知识补全',
        ),
      ).toBe(true);
    });
    const option = Array.from(document.querySelectorAll('[role="option"]')).find(
      (el) => el.textContent === '知识补全',
    ) as HTMLElement;
    fireEvent.click(option);

    await waitFor(() => {
      const patchCall = fetchMock.mock.calls.find(
        ([input, init]) =>
          init?.method === 'PATCH' &&
          String(input).includes(`/kanban/cards/${encodeURIComponent('无归属任务')}`),
      );
      expect(patchCall).toBeDefined();
      expect(JSON.parse(String(patchCall?.[1]?.body))).toEqual({ project_id: 'p1' });
      expect((patchCall?.[1]?.headers as Record<string, string>)['If-Match']).toBe(KANBAN_ETAG);
    });
  });

  it('detail card 保存排期 posts planned dates', async () => {
    const fetchMock = stubFetch();
    renderPage('/p/alice/projects?task=kb_2');
    const card = await screen.findByTestId('task-detail-card');

    fireEvent.change(within(card).getByLabelText('排期开始'), {
      target: { value: '2026-09-24' },
    });
    fireEvent.change(within(card).getByLabelText('排期结束'), {
      target: { value: '2026-09-30' },
    });
    fireEvent.click(within(card).getByTestId('schedule-save'));

    await waitFor(() => {
      const call = fetchMock.mock.calls.find(
        ([input, init]) => init?.method === 'POST' && String(input).endsWith('/schedule'),
      );
      expect(call).toBeDefined();
      expect(JSON.parse(String(call?.[1]?.body))).toEqual({
        planned_start: '2026-09-24',
        planned_end: '2026-09-30',
      });
      expect((call?.[1]?.headers as Record<string, string>)['If-Match']).toBe(KANBAN_ETAG);
    });
  });

  it('新建计划 modal instantiates a template with the plan-templates ETag', async () => {
    const fetchMock = stubFetch((url, init) => {
      const target = String(url);
      if (init?.method === 'POST' && target.endsWith('/plan-templates/instantiate')) {
        return new Response(
          JSON.stringify({
            ok: true,
            case: { id: 'plan-fat-loss', title: '减脂 30 天' },
            template_id: 'plan:fat-loss-30',
            habit_id: 'fat-loss',
            created_habit: true,
            warnings: [],
          }),
          { status: 201, headers: { 'Content-Type': 'application/json', ETag: 'W/"plan-2"' } },
        );
      }
      if (target.endsWith('/profiles/alice/plan-templates') && !init?.method) {
        return new Response(
          JSON.stringify({
            profile: 'alice',
            builtin: [
              {
                id: 'plan:fat-loss-30',
                title: '减脂 30 天',
                summary: '每天记录饮食与运动',
                duration_days: 30,
                habit: { title: '减脂打卡', kind: 'health', cadence: 'daily', target_count: 1, target_unit: '' },
                milestones: [{ title: '第 7 天复盘', offset_days: 7 }],
                builtin: true,
              },
            ],
            history: [
              { template_id: 'plan:learning-21', title: '学习 21 天', used_at: '2026-09-01T00:00:00', project_id: '', habit_id: '' },
            ],
          }),
          { status: 200, headers: { 'Content-Type': 'application/json', ETag: PLAN_ETAG } },
        );
      }
      return undefined as unknown as Response;
    });
    renderPage();

    fireEvent.click(await screen.findByTestId('new-plan-button'));
    const modal = await screen.findByTestId('new-plan-modal');
    expect(within(modal).getByTestId('plan-template-plan:fat-loss-30')).toBeInTheDocument();
    // History picker (most recent first) is present.
    expect(within(modal).getByTestId('plan-history-plan:learning-21')).toBeInTheDocument();

    fireEvent.click(within(modal).getByTestId('plan-template-plan:fat-loss-30'));
    fireEvent.change(within(modal).getByTestId('plan-title-input'), {
      target: { value: '秋季减脂' },
    });
    fireEvent.click(within(modal).getByTestId('plan-instantiate-submit'));

    expect(await screen.findByText('计划已创建')).toBeInTheDocument();
    const call = fetchMock.mock.calls.find(
      ([input, init]) =>
        init?.method === 'POST' && String(input).endsWith('/plan-templates/instantiate'),
    );
    expect(call).toBeDefined();
    expect(JSON.parse(String(call?.[1]?.body))).toMatchObject({
      template_id: 'plan:fat-loss-30',
      title: '秋季减脂',
    });
    expect((call?.[1]?.headers as Record<string, string>)['If-Match']).toBe(PLAN_ETAG);
  });
});
