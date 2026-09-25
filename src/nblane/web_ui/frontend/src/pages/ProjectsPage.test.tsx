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
          evidence_ref_count: 2,
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
const BOARD_ETAG_PROJECT = 'W/"project-board-1"';

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
    if (url.includes('/profiles/alice/projects-board')) {
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
    if (url.includes('/profiles/alice/habit-plans')) {
      return jsonResponse(200, { ok: true, profile: 'alice', plans: [] });
    }
    if (url.endsWith('/profiles/alice/project-board')) {
      return new Response(JSON.stringify(PROJECT_BOARD), {
        status: 200,
        headers: { 'Content-Type': 'application/json', ETag: BOARD_ETAG_PROJECT },
      });
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
  window.localStorage.clear();
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

    // Someday renders as a dashed badge card inside the Queue column,
    // with the two exits into the daily loop on the card itself.
    const someday = screen.getByTestId('someday-card-kb_3');
    expect(someday).toHaveTextContent('someday');
    expect(within(someday).getByTestId('someday-queue-kb_3')).toHaveTextContent('列入 Queue');
    expect(within(someday).getByTestId('someday-done-kb_3')).toHaveTextContent('标记 Done');
    expect(screen.getByTestId('lane-column-p1-queue')).toContainElement(someday);

    // Done fold count includes archived tasks.
    expect(screen.getByTestId('done-count-p1')).toHaveTextContent('Done · 5（含归档 3）');
    // Unassigned lane (dashed gold) with its task.
    const unassigned = screen.getByTestId('unassigned-lane');
    expect(within(unassigned).getByText('无归属任务')).toBeInTheDocument();

    // Habit band row: 7 week dots (1 done), streak + check-in button.
    const habitRow = screen.getByTestId('habit-band-row-exercise');
    expect(habitRow).toHaveTextContent('保持锻炼');
    expect(habitRow).toHaveTextContent('连续 1 天');
    expect(habitRow).toHaveTextContent('累计 38 次');
    expect(screen.getByTestId('habit-dot-exercise-2026-09-23')).toHaveAttribute(
      'data-done',
      'true',
    );
    expect(screen.getByTestId('habit-dot-exercise-2026-09-24')).toHaveAttribute(
      'data-done',
      'false',
    );
    // Quick-add rows pinned to every lane's Queue column top (裁决4).
    expect(within(screen.getByTestId('lane-column-p1-queue')).getByTestId('quick-add-p1'));
    expect(
      within(screen.getByTestId('lane-column-unassigned-queue')).getByTestId('quick-add-unassigned'),
    );
  });

  it('未归属 stats badge matches the lane, naming the hidden done remainder', async () => {
    // Backend stats.tasks_unassigned counts Done-column cards too (they are
    // still live kanban rows); the lane only renders queue/doing/someday.
    stubFetch((url) => {
      if (url.includes('/profiles/alice/projects-board')) {
        return new Response(
          JSON.stringify({
            ...BOARD,
            unassigned_tasks: [
              makeTask({ id: 'kb_9', title: '无归属任务' }),
              makeTask({
                id: 'kb_10',
                title: '已完成旧任务',
                section: 'Done',
                column: 'done',
                done: true,
              }),
            ],
            stats: { tasks_total: 5, tasks_unassigned: 2 },
          }),
          { status: 200, headers: { 'Content-Type': 'application/json', ETag: BOARD_ETAG } },
        );
      }
      return undefined as unknown as Response;
    });
    renderPage();

    const badge = await screen.findByTestId('stats-tasks_unassigned');
    // Lane truth: 1 visible card; the done one is named, not miscounted.
    expect(badge).toHaveTextContent('未归属 1(含已完成 1)');
  });

  it('未归属 stats badge without hidden done cards shows the plain count', async () => {
    stubFetch((url) => {
      if (url.includes('/profiles/alice/projects-board')) {
        return new Response(
          JSON.stringify({ ...BOARD, stats: { tasks_total: 4, tasks_unassigned: 1 } }),
          { status: 200, headers: { 'Content-Type': 'application/json', ETag: BOARD_ETAG } },
        );
      }
      return undefined as unknown as Response;
    });
    renderPage();

    const badge = await screen.findByTestId('stats-tasks_unassigned');
    expect(badge).toHaveTextContent('未归属 1');
    expect(badge).not.toHaveTextContent('含已完成');
  });

  it('日课栏 dedupe: a habit-plan renders only as a band row, never as a lane', async () => {
    const habitPlan = {
      id: 'plan-exercise',
      title: '锻炼 30 天',
      status: 'active',
      kind: 'habit',
      visibility: 'private',
      summary: '',
      time_range: '2026-09-01/2026-09-30',
      goal_refs: [],
      milestones: [],
      queue: [],
      doing: [],
      someday: [],
      column_counts: {},
      done_count: 0,
      archived_done_count: 0,
      evidence_ref_count: 0,
      last_activity: '',
      habit_id: 'exercise',
    };
    stubFetch((url, init) => {
      if (url.endsWith('/profiles/alice/projects-board') && !init?.method) {
        const board = {
          ...BOARD,
          ungrouped_projects: [habitPlan],
          habits: [{ ...BOARD.habits[0], project_id: 'plan-exercise', recent_days: [] }],
        };
        return new Response(JSON.stringify(board), {
          status: 200,
          headers: { 'Content-Type': 'application/json', ETag: BOARD_ETAG },
        });
      }
      return undefined as unknown as Response;
    });
    renderPage();
    await screen.findByText('alice · 项目');

    // Exactly one row for the habit, in the band; no swimlane, no 未分组 ghost.
    expect(screen.getByTestId('habit-band')).toBeInTheDocument();
    expect(screen.getAllByText('保持锻炼')).toHaveLength(1);
    expect(screen.queryByTestId('project-lane-plan-exercise')).not.toBeInTheDocument();
    expect(screen.queryByTestId('lane-group-__ungrouped__')).not.toBeInTheDocument();
    // Habit-plan row: 第N/30天 progress arc, no Queue/Doing columns.
    expect(screen.getByTestId('habit-plan-arc')).toHaveTextContent('第23/30天');
    expect(screen.queryByTestId('lane-column-plan-exercise-queue')).not.toBeInTheDocument();
  });

  it('quick-add posts a project task with the project-board ETag (裁决4) and auto-opens the detail card', async () => {
    const fetchMock = stubFetch();
    renderPage();
    await screen.findByText('读 VLA 综述');

    fireEvent.click(screen.getByTestId('quick-add-p1'));
    const input = screen.getByTestId('quick-add-input-p1');
    fireEvent.change(input, { target: { value: '新任务甲' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    await waitFor(() => {
      const call = fetchMock.mock.calls.find(
        ([inputUrl, init]) =>
          init?.method === 'POST' && String(inputUrl).endsWith('/project-board/cases/p1/tasks'),
      );
      expect(call).toBeDefined();
      expect(JSON.parse(String(call?.[1]?.body))).toMatchObject({
        title: '新任务甲',
        section: 'Queue',
      });
      expect((call?.[1]?.headers as Record<string, string>)['If-Match']).toBe(BOARD_ETAG_PROJECT);
    });
    // ≤1-click kept, but the detail card opens on the created card so edits
    // land in context (MUTATION_RESULT.card.id = kb_1 in this fixture).
    await waitFor(() => expect(lastSearch).toContain('task=kb_1'));
    expect(await screen.findByTestId('task-detail-card')).toHaveTextContent('读 VLA 综述');
  });

  it('unassigned quick-add posts a kanban card and auto-opens the detail card', async () => {
    const fetchMock = stubFetch();
    renderPage();
    await screen.findByText('无归属任务');

    fireEvent.click(screen.getByTestId('quick-add-unassigned'));
    const input = screen.getByTestId('quick-add-input-unassigned');
    fireEvent.change(input, { target: { value: '野卡片' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    await waitFor(() => {
      const call = fetchMock.mock.calls.find(
        ([inputUrl, init]) =>
          init?.method === 'POST' && String(inputUrl).endsWith('/kanban/cards'),
      );
      expect(call).toBeDefined();
      expect(JSON.parse(String(call?.[1]?.body))).toMatchObject({
        title: '野卡片',
        section: 'Queue',
      });
      expect((call?.[1]?.headers as Record<string, string>)['If-Match']).toBe(KANBAN_ETAG);
    });
    await waitFor(() => expect(lastSearch).toContain('task=kb_1'));
    expect(await screen.findByTestId('task-detail-card')).toBeInTheDocument();
  });

  it('habit-plan band rows expose a 设置 affordance that opens the edit drawer (日课项目可删除)', async () => {
    const habitPlan = {
      id: 'plan-exercise',
      title: '锻炼 30 天',
      status: 'active',
      kind: 'habit',
      visibility: 'private',
      summary: '',
      time_range: '2026-09-01/2026-09-30',
      goal_refs: [],
      milestones: [],
      queue: [],
      doing: [],
      someday: [],
      column_counts: {},
      done_count: 0,
      archived_done_count: 0,
      evidence_ref_count: 0,
      last_activity: '',
      habit_id: 'exercise',
    };
    stubFetch((url, init) => {
      if (url.endsWith('/profiles/alice/projects-board') && !init?.method) {
        const board = {
          ...BOARD,
          ungrouped_projects: [habitPlan],
          habits: [{ ...BOARD.habits[0], project_id: 'plan-exercise', recent_days: [] }],
        };
        return new Response(JSON.stringify(board), {
          status: 200,
          headers: { 'Content-Type': 'application/json', ETag: BOARD_ETAG },
        });
      }
      return undefined as unknown as Response;
    });
    renderPage();
    await screen.findByTestId('habit-band');

    // The pure-habit affordance is absent when the row has no linked case…
    // (this row IS linked, so its 设置 button is present in the DOM and
    // reveals on hover/focus).
    const settings = screen.getByTestId('habit-plan-settings-plan-exercise');
    fireEvent.click(settings);

    // The drawer opens for the habit-plan case (delete zone lives inside).
    const drawer = await screen.findByTestId('project-edit-drawer');
    expect(drawer).toBeInTheDocument();
    expect(await screen.findByText('项目不存在')).toBeInTheDocument();
  });

  it('task card shows checklist progress (清单 done/total)', async () => {
    stubFetch((url, init) => {
      if (url.endsWith('/profiles/alice/projects-board') && !init?.method) {
        const board = JSON.parse(JSON.stringify(BOARD)) as typeof BOARD;
        board.goals[0].projects[0].doing[0] = {
          ...board.goals[0].projects[0].doing[0],
          todos: [
            { text: '拆 schema', done: true },
            { text: '接线页面', done: false },
          ],
        } as never;
        return new Response(JSON.stringify(board), {
          status: 200,
          headers: { 'Content-Type': 'application/json', ETag: BOARD_ETAG },
        });
      }
      return undefined as unknown as Response;
    });
    renderPage();
    expect(await screen.findByTestId('todo-progress-kb_2')).toHaveTextContent('清单 1/2');
    // Cards without a checklist render no progress line.
    expect(screen.queryByTestId('todo-progress-kb_1')).not.toBeInTheDocument();
  });

  it('heatmap expand + empty-cell backfill posts a dated check-in', async () => {
    const fetchMock = stubFetch((url, init) => {
      if (url.endsWith('/profiles/alice/projects-board') && !init?.method) {
        const board = {
          ...BOARD,
          habits: [
            {
              ...BOARD.habits[0],
              recent_days: [{ date: '2026-09-01', count: 1 }],
            },
          ],
        };
        return new Response(JSON.stringify(board), {
          status: 200,
          headers: { 'Content-Type': 'application/json', ETag: BOARD_ETAG },
        });
      }
      return undefined as unknown as Response;
    });
    renderPage();
    await screen.findByTestId('habit-band');

    fireEvent.click(screen.getByTestId('habit-expand-exercise'));
    const heatmap = await screen.findByTestId('habit-heatmap-exercise');
    // A filled cell with id-less rows renders but offers no 销印 target.
    expect(screen.getByTestId('heatmap-cell-exercise-2026-09-01')).toHaveAttribute(
      'data-filled',
      'true',
    );
    // An empty past cell backfills on click.
    const emptyCell = screen.getByTestId('heatmap-cell-exercise-2026-09-02');
    expect(emptyCell).toHaveAttribute('data-filled', 'false');
    fireEvent.click(emptyCell);

    await waitFor(() => {
      const call = fetchMock.mock.calls.find(
        ([input, init]) => init?.method === 'POST' && String(input).endsWith('/checkins'),
      );
      expect(call).toBeDefined();
      expect(JSON.parse(String(call?.[1]?.body))).toMatchObject({
        habit: 'exercise',
        date: '2026-09-02',
      });
    });
    expect(within(heatmap).getByText(/近 90 天/)).toBeInTheDocument();
  });

  it('filled heatmap cell with ids offers 销印 (confirm → DELETE → invalidate)', async () => {
    const fetchMock = stubFetch((url, init) => {
      if (url.endsWith('/profiles/alice/projects-board') && !init?.method) {
        const board = {
          ...BOARD,
          habits: [
            {
              ...BOARD.habits[0],
              recent_days: [
                { date: '2026-09-01', count: 2, checkin_ids: ['act_a', 'act_b'] },
              ],
            },
          ],
        };
        return new Response(JSON.stringify(board), {
          status: 200,
          headers: { 'Content-Type': 'application/json', ETag: BOARD_ETAG },
        });
      }
      if (init?.method === 'DELETE' && url.includes('/checkins/')) {
        return jsonResponse(200, { ok: true, checkin_id: 'act_b' });
      }
      return undefined as unknown as Response;
    });
    renderPage();
    await screen.findByTestId('habit-band');

    fireEvent.click(screen.getByTestId('habit-expand-exercise'));
    await screen.findByTestId('habit-heatmap-exercise');
    const cell = screen.getByTestId('heatmap-cell-exercise-2026-09-01');
    expect(cell).toHaveAttribute('data-filled', 'true');
    fireEvent.click(cell);

    // Inline confirm names the date; cancel dismisses without a DELETE.
    const confirmBar = await screen.findByTestId('unseal-confirm-exercise');
    expect(confirmBar).toHaveTextContent('销印 2026-09-01 最近一次打卡?');
    fireEvent.click(screen.getByTestId('unseal-confirm-no-exercise'));
    expect(screen.queryByTestId('unseal-confirm-exercise')).not.toBeInTheDocument();
    expect(
      fetchMock.mock.calls.some(([, init]) => init?.method === 'DELETE'),
    ).toBe(false);

    // Confirm deletes the day's LATEST check-in id.
    fireEvent.click(cell);
    fireEvent.click(await screen.findByTestId('unseal-confirm-yes-exercise'));
    await waitFor(() => {
      const call = fetchMock.mock.calls.find(
        ([input, init]) => init?.method === 'DELETE' && String(input).includes('/checkins/'),
      );
      expect(call).toBeDefined();
      expect(String(call?.[0])).toContain('/checkins/act_b');
    });
  });

  it('archived strip expands inline to dimmed read-only lanes', async () => {
    stubFetch((url, init) => {
      if (url.endsWith('/profiles/alice/projects-board') && !init?.method) {
        const board = {
          ...BOARD,
          ungrouped_projects: [
            {
              id: 'p-old',
              title: '旧项目',
              status: 'archived',
              kind: 'internal',
              visibility: 'private',
              summary: '',
              time_range: '',
              goal_refs: [],
              milestones: [],
              queue: [makeTask({ id: 'kb_old', title: '历史任务', project_id: 'p-old' })],
              doing: [],
              someday: [],
              column_counts: {},
              done_count: 2,
              archived_done_count: 0,
              evidence_ref_count: 0,
              last_activity: '',
              habit_id: '',
            },
          ],
        };
        return new Response(JSON.stringify(board), {
          status: 200,
          headers: { 'Content-Type': 'application/json', ETag: BOARD_ETAG },
        });
      }
      return undefined as unknown as Response;
    });
    renderPage();
    const toggle = await screen.findByTestId('archived-strip-toggle');
    expect(screen.queryByTestId('archived-lane-p-old')).not.toBeInTheDocument();

    fireEvent.click(toggle);
    const lane = await screen.findByTestId('archived-lane-p-old');
    expect(lane).toHaveTextContent('旧项目');
    expect(lane).toHaveTextContent('历史任务');
    // Read-only: no drag handles, no quick-add; drawer + restore actions stay.
    expect(within(lane).queryByRole('button', { name: /^拖拽卡片 / })).not.toBeInTheDocument();
    expect(screen.queryByTestId('quick-add-p-old')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: '恢复项目 旧项目' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '查看项目 旧项目' })).toBeInTheDocument();
  });

  it('restore posts status=active with the project-board ETag', async () => {
    const fetchMock = stubFetch((url, init) => {
      if (url.endsWith('/profiles/alice/projects-board') && !init?.method) {
        const board = {
          ...BOARD,
          ungrouped_projects: [
            {
              id: 'p-old',
              title: '旧项目',
              status: 'archived',
              kind: 'internal',
              visibility: 'private',
              summary: '',
              time_range: '',
              goal_refs: [],
              milestones: [],
              queue: [],
              doing: [],
              someday: [],
              column_counts: {},
              done_count: 0,
              archived_done_count: 0,
              evidence_ref_count: 0,
              last_activity: '',
              habit_id: '',
            },
          ],
        };
        return new Response(JSON.stringify(board), {
          status: 200,
          headers: { 'Content-Type': 'application/json', ETag: BOARD_ETAG },
        });
      }
      return undefined as unknown as Response;
    });
    renderPage();
    fireEvent.click(await screen.findByTestId('archived-strip-toggle'));
    fireEvent.click(await screen.findByRole('button', { name: '恢复项目 旧项目' }));

    await waitFor(() => {
      const call = fetchMock.mock.calls.find(
        ([input, init]) =>
          init?.method === 'POST' && String(input).endsWith('/project-board/cases/p-old/save'),
      );
      expect(call).toBeDefined();
      expect(JSON.parse(String(call?.[1]?.body))).toEqual({ status: 'active' });
      expect((call?.[1]?.headers as Record<string, string>)['If-Match']).toBe(BOARD_ETAG_PROJECT);
    });
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

describe('ProjectsPage habit lifecycle', () => {
  it('week dots are 石刻化: 泥金 fill / 月白 hollow ring / today gold ring (no green)', async () => {
    stubFetch();
    renderPage();
    await screen.findByTestId('habit-band');

    const done = screen.getByTestId('habit-dot-exercise-2026-09-23');
    expect(done).toHaveAttribute('data-done', 'true');
    // 2026-09-23 is board.today: thin gold outer ring via box-shadow.
    expect(done).toHaveAttribute('data-today', 'true');
    expect(done.style.cssText).toContain('220, 174, 85');
    expect(done.style.cssText).not.toContain('125, 191, 142');

    const undone = screen.getByTestId('habit-dot-exercise-2026-09-22');
    expect(undone).toHaveAttribute('data-done', 'false');
    expect(undone).toHaveAttribute('data-today', 'false');
    expect(undone.style.cssText).toContain('rgba(242, 237, 224, 0.35)');
  });

  it('归档 folds the row away; 显示已归档 brings it back dimmed with 恢复', async () => {
    const fetchMock = stubFetch((url, init) => {
      if (init?.method === 'POST' && url.endsWith('/habits/exercise/archive')) {
        const body = JSON.parse(String(init.body)) as { archived: boolean };
        return jsonResponse(200, { ok: true, habit_id: 'exercise', archived: body.archived });
      }
      return undefined as unknown as Response;
    });
    renderPage();
    await screen.findByTestId('habit-band-row-exercise');

    fireEvent.click(screen.getByTestId('habit-menu-exercise'));
    fireEvent.click(await screen.findByTestId('habit-archive-exercise'));

    await waitFor(() => {
      const call = fetchMock.mock.calls.find(
        ([input, init]) =>
          init?.method === 'POST' && String(input).endsWith('/habits/exercise/archive'),
      );
      expect(call).toBeDefined();
      expect(JSON.parse(String(call?.[1]?.body))).toEqual({ archived: true });
    });
    // One click and the row disappears (restore comes via the toggle).
    expect(await screen.findByText('已归档')).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.queryByTestId('habit-band-row-exercise')).not.toBeInTheDocument(),
    );

    // 显示已归档 toggle surfaces the row dimmed, with a 恢复 menu item.
    fireEvent.click(screen.getByTestId('habit-show-archived-toggle'));
    const row = await screen.findByTestId('habit-band-row-exercise');
    expect(row).toHaveTextContent('已归档');

    fireEvent.click(screen.getByTestId('habit-menu-exercise'));
    fireEvent.click(await screen.findByTestId('habit-restore-exercise'));
    await waitFor(() => {
      const call = fetchMock.mock.calls.find(
        ([input, init]) =>
          init?.method === 'POST' &&
          String(input).endsWith('/habits/exercise/archive') &&
          JSON.parse(String(init?.body)).archived === false,
      );
      expect(call).toBeDefined();
    });
    expect(await screen.findByText('已恢复')).toBeInTheDocument();
    // Back to a live row: the 已归档 badge clears.
    await waitFor(() =>
      expect(screen.getByTestId('habit-band-row-exercise')).not.toHaveTextContent('已归档'),
    );
  });

  it('显示已归档 also surfaces server-side archived habits (?include_archived=true)', async () => {
    const fetchMock = stubFetch((url, init) => {
      if (!init?.method && url.includes('include_archived=true')) {
        const board = {
          ...BOARD,
          habits: [
            ...BOARD.habits,
            { ...BOARD.habits[0], id: 'piano', title: '练琴', archived: true },
          ],
        };
        return new Response(JSON.stringify(board), {
          status: 200,
          headers: { 'Content-Type': 'application/json', ETag: BOARD_ETAG },
        });
      }
      return undefined as unknown as Response;
    });
    renderPage();
    await screen.findByTestId('habit-band-row-exercise');

    // The server-archived habit only appears after the toggle.
    expect(screen.queryByTestId('habit-band-row-piano')).not.toBeInTheDocument();
    fireEvent.click(screen.getByTestId('habit-show-archived-toggle'));
    const row = await screen.findByTestId('habit-band-row-piano');
    expect(row).toHaveTextContent('练琴');
    expect(row).toHaveTextContent('已归档');

    // 恢复 posts archived:false through the same lifecycle menu.
    fireEvent.click(screen.getByTestId('habit-menu-piano'));
    fireEvent.click(await screen.findByTestId('habit-restore-piano'));
    await waitFor(() => {
      const call = fetchMock.mock.calls.find(
        ([input, init]) =>
          init?.method === 'POST' && String(input).endsWith('/habits/piano/archive'),
      );
      expect(call).toBeDefined();
      expect(JSON.parse(String(call?.[1]?.body))).toEqual({ archived: false });
    });
  });

  it('delete habit: consequence preview + type-the-name confirm + DELETE body', async () => {
    const fetchMock = stubFetch((url, init) => {
      if (init?.method === 'DELETE' && url.endsWith('/habits/exercise')) {
        return jsonResponse(200, { ok: true, deleted_id: 'exercise', checkins_removed: 38 });
      }
      return undefined as unknown as Response;
    });
    renderPage();
    await screen.findByTestId('habit-band-row-exercise');

    fireEvent.click(screen.getByTestId('habit-menu-exercise'));
    fireEvent.click(await screen.findByTestId('habit-delete-exercise'));

    // Consequence preview counts the habit's total check-ins.
    expect(await screen.findByTestId('delete-habit-preview-exercise')).toHaveTextContent(
      '将移除 38 条打卡记录',
    );
    const confirm = screen.getByTestId('delete-habit-confirm-exercise');
    expect(confirm).toBeDisabled();
    // 记入大事记 defaults OFF.
    expect(screen.getByTestId('delete-habit-record-chronicle-exercise')).not.toBeChecked();

    fireEvent.change(screen.getByTestId('delete-habit-confirm-title-exercise'), {
      target: { value: '保持锻炼 ' },
    });
    expect(confirm).toBeDisabled();
    fireEvent.change(screen.getByTestId('delete-habit-confirm-title-exercise'), {
      target: { value: '保持锻炼' },
    });
    expect(confirm).toBeEnabled();
    fireEvent.click(confirm);

    await waitFor(() => {
      const call = fetchMock.mock.calls.find(
        ([input, init]) =>
          init?.method === 'DELETE' && String(input).endsWith('/habits/exercise'),
      );
      expect(call).toBeDefined();
      expect(JSON.parse(String(call?.[1]?.body))).toEqual({
        confirm_title: '保持锻炼',
        record_chronicle: false,
      });
    });
    expect(await screen.findByText('习惯已删除')).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.queryByTestId('habit-band-row-exercise')).not.toBeInTheDocument(),
    );
  });

  it('delete habit: 422 habit_delete_confirm_mismatch lands as an inline error', async () => {
    stubFetch((url, init) => {
      if (init?.method === 'DELETE' && url.endsWith('/habits/exercise')) {
        return jsonResponse(422, {
          code: 'habit_delete_confirm_mismatch',
          message: 'confirm_title does not match the habit title',
        });
      }
      return undefined as unknown as Response;
    });
    renderPage();
    await screen.findByTestId('habit-band-row-exercise');

    fireEvent.click(screen.getByTestId('habit-menu-exercise'));
    fireEvent.click(await screen.findByTestId('habit-delete-exercise'));
    fireEvent.change(await screen.findByTestId('delete-habit-confirm-title-exercise'), {
      target: { value: '保持锻炼' },
    });
    fireEvent.click(screen.getByTestId('delete-habit-confirm-exercise'));

    expect(await screen.findByText('习惯名不匹配,请逐字输入。')).toBeInTheDocument();
    // The row survives a rejected delete.
    expect(screen.getByTestId('habit-band-row-exercise')).toBeInTheDocument();
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
    // kb_2 started 2026-09-10 → spans 14 days to today → sinks to a 期间带
    // (P1 分层); kb_1 has no dates → 未排期 row note.
    expect(screen.getByTestId('timeline-period-kb_2')).toBeInTheDocument();
    expect(screen.getByTestId('unscheduled-p1')).toHaveTextContent('读 VLA 综述');
    // Habit strip with this week's done dot.
    expect(screen.getByTestId('timeline-habit-exercise')).toBeInTheDocument();
    expect(screen.getByTestId('timeline-habit-dot-exercise-2026-09-23')).toBeInTheDocument();
    // Clicking a period band selects the task (shared detail card).
    fireEvent.click(screen.getByTestId('timeline-period-kb_2'));
    expect(await screen.findByTestId('task-detail-card')).toHaveTextContent('完成技能树重构');
  });

  it('timeline filter hides unchecked project rows (and their empty group header)', async () => {
    stubFetch();
    renderPage('/p/alice/projects?view=timeline');
    expect(await screen.findByTestId('timeline-row-p1')).toBeInTheDocument();
    expect(screen.getByTestId('timeline-group-g1')).toBeInTheDocument();

    // Uncheck 知识补全 in the project multi-select (options stay listed so
    // they can be toggled back on).
    const filter = screen.getByTestId('timeline-project-filter');
    fireEvent.mouseDown(filter);
    fireEvent.click(filter);
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

    await waitFor(() =>
      expect(screen.queryByTestId('timeline-row-p1')).not.toBeInTheDocument(),
    );
    // g1 had only p1 — the group header goes with it.
    expect(screen.queryByTestId('timeline-group-g1')).not.toBeInTheDocument();
    // 日课 rows are immune to the project filter.
    expect(screen.getByTestId('timeline-habit-exercise')).toBeInTheDocument();
    // The selection persists (localStorage) for the next visit.
    expect(window.localStorage.getItem('nblane.timeline.projects')).toBe('[]');
  });

  it('timeline focus button zooms to the project span; 全部 restores', async () => {
    stubFetch();
    renderPage('/p/alice/projects?view=timeline');
    const toolbar = await screen.findByTestId('timeline-toolbar');
    // Default 半年 window: 2026-09-23 − 136d → +45d.
    expect(toolbar).toHaveTextContent('2026-05-10 → 2026-11-07');

    // p1 has no time_range; focus falls back to its task span (kb_2:
    // 2026-09-10 → today) padded 1 day on both ends.
    fireEvent.click(screen.getByTestId('timeline-focus-p1'));
    await waitFor(() => expect(toolbar).toHaveTextContent('2026-09-09 → 2026-09-24'));

    // 全部 preset clears the focus window and refits the full extent.
    fireEvent.click(within(screen.getByTestId('timeline-zoom-toggle')).getByText('全部'));
    await waitFor(() => expect(toolbar).toHaveTextContent('2026-09-10 → 2026-10-07'));
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
  it('delete project: preview + type-the-name confirm + DELETE with board ETag (裁决3)', async () => {
    const projectCase = {
      id: 'p1',
      title: '知识补全',
      status: 'active',
      kind: 'learning',
      visibility: 'private',
      time_range: '',
      summary: '',
      notes: '',
      goal_refs: ['g1'],
      task_refs: [],
      evidence_refs: ['ev_a', 'ev_b'],
      source_refs: [],
      experience_refs: [],
      output_refs: [],
      milestones: [],
      tasks: [],
      derived_time_range: '',
    };
    const fetchMock = stubFetch((url, init) => {
      const target = String(url);
      if (target.endsWith('/profiles/alice/project-board') && !init?.method) {
        return new Response(
          JSON.stringify({ ...PROJECT_BOARD, cases: [projectCase] }),
          {
            status: 200,
            headers: { 'Content-Type': 'application/json', ETag: BOARD_ETAG_PROJECT },
          },
        );
      }
      if (init?.method === 'DELETE' && target.endsWith('/project-board/cases/p1')) {
        return jsonResponse(200, {
          ok: true,
          deleted_id: 'p1',
          tasks_unassigned: 8,
          evidence_refs_kept: 2,
        });
      }
      return undefined as unknown as Response;
    });
    renderPage();
    await screen.findByText('读 VLA 综述');

    // Open the drawer from the lane header, enter the danger zone.
    fireEvent.click(screen.getByRole('button', { name: '编辑项目 知识补全' }));
    const drawer = await screen.findByTestId('project-edit-drawer');
    fireEvent.click(await within(drawer).findByTestId('delete-project-button'));

    const modal = await screen.findByTestId('delete-project-modal');
    expect(modal).toBeInTheDocument();
    // Consequence preview from column_counts (1+1+1+5) + evidence_ref_count.
    // (Modal content portals to document.body — query via screen; the root
    // mounts before its transitioned children, so await them.)
    expect(await screen.findByTestId('delete-project-preview')).toHaveTextContent(
      '8 个任务将回到未归属 · 2 条证据保留引用',
    );
    const confirm = await screen.findByTestId('delete-project-confirm');
    expect(confirm).toBeDisabled();
    // 记入大事记 defaults OFF (家务删除不混入叙事).
    expect(screen.getByTestId('delete-record-chronicle')).not.toBeChecked();

    // A near-miss title keeps the confirm disabled.
    fireEvent.change(screen.getByTestId('delete-confirm-title'), {
      target: { value: '知识补全 ' },
    });
    expect(confirm).toBeDisabled();
    fireEvent.change(screen.getByTestId('delete-confirm-title'), {
      target: { value: '知识补全' },
    });
    expect(confirm).toBeEnabled();
    fireEvent.click(confirm);

    await waitFor(() => {
      const call = fetchMock.mock.calls.find(
        ([input, init]) =>
          init?.method === 'DELETE' && String(input).endsWith('/project-board/cases/p1'),
      );
      expect(call).toBeDefined();
      expect(JSON.parse(String(call?.[1]?.body))).toEqual({
        confirm_title: '知识补全',
        record_chronicle: false,
      });
      expect((call?.[1]?.headers as Record<string, string>)['If-Match']).toBe(BOARD_ETAG_PROJECT);
    });
    // Drawer closes and the boards invalidate after a successful delete.
    expect(await screen.findByText('项目已删除')).toBeInTheDocument();
    // Mantine keeps the closed Drawer's root mounted; its content unmounts.
    await waitFor(() =>
      expect(screen.queryByTestId('delete-project-zone')).not.toBeInTheDocument(),
    );
  });

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
      `/kanban/cards/kb_1/move`,
    );
    expect(JSON.parse(String(moveCall?.[1]?.body))).toEqual({
      target_section: 'Doing',
      to_index: 1,
    });
    // Mutations use the kanban-file ETag, never the board ETag.
    expect((moveCall?.[1]?.headers as Record<string, string>)['If-Match']).toBe(KANBAN_ETAG);
  });

  it('promotes a someday badge into Queue or Done without opening the detail card', async () => {
    const fetchMock = stubFetch();
    renderPage();
    fireEvent.click(await screen.findByTestId('someday-queue-kb_3'));

    expect(await screen.findByText('已列入 Queue')).toBeInTheDocument();
    const moveCall = fetchMock.mock.calls.find(
      ([input, init]) => String(input).endsWith('/kanban/cards/kb_3/move') && init?.method === 'POST',
    );
    expect(moveCall).toBeDefined();
    expect(JSON.parse(String(moveCall?.[1]?.body))).toEqual({ target_section: 'Queue' });
    expect((moveCall?.[1]?.headers as Record<string, string>)['If-Match']).toBe(KANBAN_ETAG);
    expect(lastSearch).not.toContain('task=');

    fireEvent.click(screen.getByTestId('someday-done-kb_3'));
    expect(await screen.findByText('已标记完成')).toBeInTheDocument();
    const doneCall = fetchMock.mock.calls.find(
      ([input, init]) => String(input).endsWith('/kanban/cards/kb_3/done') && init?.method === 'POST',
    );
    expect(doneCall).toBeDefined();
    expect((doneCall?.[1]?.headers as Record<string, string>)['If-Match']).toBe(KANBAN_ETAG);
    expect(lastSearch).not.toContain('task=');
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
          String(input).includes('/kanban/cards/kb_9'),
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

// --- 习惯阶段计划 (habit phase plans) -----------------------------------------

/** Active plan bound to habit `exercise`; board today is 2026-09-23 → W2/4. */
const ACTIVE_PLAN = {
  id: 'hp1',
  title: '28天减脂',
  habit_id: 'exercise',
  start_date: '2026-09-14',
  end_date: '2026-10-11',
  status: 'active',
  weekly_tasks: [
    { week: 1, tasks: ['控制饮食', '每天 8k 步'] },
    { week: 2, tasks: ['晨跑 3 次', '记录体重'] },
    { week: 3, tasks: ['力量训练'] },
    { week: 4, tasks: ['复盘'] },
  ],
  current_week: 2,
  days_done: 9,
  days_total: 28,
  completion_rate: 0.32,
  weeks: [],
};

function stubPlans(plans: unknown[]) {
  return (url: string, init?: RequestInit) => {
    if (url.includes('/profiles/alice/habit-plans') && !init?.method) {
      return jsonResponse(200, { ok: true, profile: 'alice', plans });
    }
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
  };
}

function lastCheckinCall(fetchMock: ReturnType<typeof stubFetch>) {
  return fetchMock.mock.calls.find(
    ([input, init]) => String(input).endsWith('/checkins') && init?.method === 'POST',
  );
}

describe('ProjectsPage habit phase plans', () => {
  it('日课栏 shows the active-plan badge (title · W2/4), hides non-active plans', async () => {
    stubFetch(
      stubPlans([
        ACTIVE_PLAN,
        { ...ACTIVE_PLAN, id: 'hp2', title: '已完成计划', status: 'completed' },
        { ...ACTIVE_PLAN, id: 'hp3', title: '别人的计划', habit_id: 'reading' },
      ]),
    );
    renderPage();

    const badge = await screen.findByTestId('habit-plan-badge-exercise-hp1');
    expect(badge).toHaveTextContent('28天减脂 · W2/4');
    expect(screen.queryByTestId('habit-plan-badge-exercise-hp2')).toBeNull();
    expect(screen.queryByTestId('habit-plan-badge-exercise-hp3')).toBeNull();
  });

  it('打卡 with one in-window active plan asks first, then posts plan_id', async () => {
    const fetchMock = stubFetch(stubPlans([ACTIVE_PLAN]));
    renderPage();

    fireEvent.click(await screen.findByTestId('checkin-button-exercise'));
    // No request yet — the inline 计入计划 confirm opens first.
    expect(lastCheckinCall(fetchMock)).toBeUndefined();
    const panel = await screen.findByTestId('checkin-plan-panel-exercise');
    expect(panel).toHaveTextContent('计入「28天减脂」计划(W2/4)');
    // Default on: the checkbox starts checked.
    expect(within(panel).getByTestId('checkin-plan-toggle-hp1')).toBeChecked();

    fireEvent.click(within(panel).getByTestId('checkin-plan-confirm-exercise'));
    expect(await screen.findByText('已打卡')).toBeInTheDocument();
    const call = lastCheckinCall(fetchMock);
    expect(JSON.parse(String(call?.[1]?.body))).toMatchObject({
      habit: 'exercise',
      plan_id: 'hp1',
    });
    // Panel folds away after the mutation settles.
    await waitFor(() =>
      expect(screen.queryByTestId('checkin-plan-panel-exercise')).toBeNull(),
    );
  });

  it('unchecking 计入计划 posts a plain check-in without plan_id', async () => {
    const fetchMock = stubFetch(stubPlans([ACTIVE_PLAN]));
    renderPage();

    fireEvent.click(await screen.findByTestId('checkin-button-exercise'));
    const panel = await screen.findByTestId('checkin-plan-panel-exercise');
    fireEvent.click(within(panel).getByTestId('checkin-plan-toggle-hp1'));
    fireEvent.click(within(panel).getByTestId('checkin-plan-confirm-exercise'));

    expect(await screen.findByText('已打卡')).toBeInTheDocument();
    const body = JSON.parse(String(lastCheckinCall(fetchMock)?.[1]?.body));
    expect(body.habit).toBe('exercise');
    expect(body.plan_id).toBeUndefined();
  });

  it('取消 closes the confirm without posting', async () => {
    const fetchMock = stubFetch(stubPlans([ACTIVE_PLAN]));
    renderPage();

    fireEvent.click(await screen.findByTestId('checkin-button-exercise'));
    const panel = await screen.findByTestId('checkin-plan-panel-exercise');
    fireEvent.click(within(panel).getByTestId('checkin-plan-cancel-exercise'));

    expect(screen.queryByTestId('checkin-plan-panel-exercise')).toBeNull();
    expect(lastCheckinCall(fetchMock)).toBeUndefined();
  });

  it('multiple in-window active plans open a picker; the chosen plan lands in plan_id', async () => {
    const second = {
      ...ACTIVE_PLAN,
      id: 'hp2',
      title: '晨跑专项',
      start_date: '2026-09-21',
      end_date: '2026-10-04',
    };
    const fetchMock = stubFetch(stubPlans([ACTIVE_PLAN, second]));
    renderPage();

    fireEvent.click(await screen.findByTestId('checkin-button-exercise'));
    const picker = await screen.findByTestId('checkin-plan-picker-exercise');
    fireEvent.click(within(picker).getByTestId('checkin-plan-option-hp2'));
    fireEvent.click(screen.getByTestId('checkin-plan-confirm-exercise'));

    expect(await screen.findByText('已打卡')).toBeInTheDocument();
    expect(JSON.parse(String(lastCheckinCall(fetchMock)?.[1]?.body))).toMatchObject({
      plan_id: 'hp2',
    });
  });

  it('out-of-window or no active plan → 打卡 posts immediately without plan_id', async () => {
    const stale = { ...ACTIVE_PLAN, start_date: '2026-08-01', end_date: '2026-08-28' };
    const fetchMock = stubFetch(stubPlans([stale]));
    renderPage();

    fireEvent.click(await screen.findByTestId('checkin-button-exercise'));

    expect(await screen.findByText('已打卡')).toBeInTheDocument();
    expect(screen.queryByTestId('checkin-plan-panel-exercise')).toBeNull();
    const body = JSON.parse(String(lastCheckinCall(fetchMock)?.[1]?.body));
    expect(body.habit).toBe('exercise');
    expect(body.plan_id).toBeUndefined();
  });

  it('lane 阶段计划 section renders title/range/rate and the current week tasks', async () => {
    const board = {
      ...BOARD,
      goals: [
        {
          ...BOARD.goals[0],
          projects: [{ ...BOARD.goals[0].projects[0], habit_id: 'exercise' }],
        },
      ],
    };
    stubFetch((url, init) => {
      if (url.includes('/profiles/alice/projects-board') && !init?.method) {
        return new Response(JSON.stringify(board), {
          status: 200,
          headers: { 'Content-Type': 'application/json', ETag: BOARD_ETAG },
        });
      }
      return stubPlans([ACTIVE_PLAN])(url, init);
    });
    renderPage();

    const lane = await screen.findByTestId('project-lane-p1');
    const section = within(lane).getByTestId('habit-plan-section');
    const card = within(section).getByTestId('habit-plan-card-hp1');
    expect(card).toHaveTextContent('阶段计划');
    expect(card).toHaveTextContent('28天减脂');
    expect(card).toHaveTextContent('2026-09-14 ~ 2026-10-11');
    expect(card).toHaveTextContent('W2/4 · 打卡 9/28 天 · 32%');
    const weekTasks = within(card).getByTestId('habit-plan-week-tasks-hp1');
    expect(weekTasks).toHaveTextContent('本周任务(W2)');
    expect(weekTasks).toHaveTextContent('晨跑 3 次');
    expect(weekTasks).toHaveTextContent('记录体重');
    // Only the current week's tasks — week 1 stays out.
    expect(weekTasks).not.toHaveTextContent('控制饮食');
    expect(card).toHaveTextContent('每周任务已生成周卡进入看板 Queue 列');
  });

  it('lane without an active habit plan renders no 阶段计划 section', async () => {
    stubFetch(stubPlans([]));
    renderPage();

    const lane = await screen.findByTestId('project-lane-p1');
    expect(within(lane).queryByTestId('habit-plan-section')).toBeNull();
  });

  it('习惯行菜单 新建计划 opens the modal with 28-day defaults and 4 week blocks', async () => {
    stubFetch(stubPlans([ACTIVE_PLAN]));
    renderPage();
    await screen.findByTestId('habit-band-row-exercise');

    // The entry lives in the same lifecycle menu as 归档/删除 — also present
    // for a habit that already has an active plan (并存, picker on check-in).
    fireEvent.click(screen.getByTestId('habit-menu-exercise'));
    fireEvent.click(await screen.findByTestId('habit-new-plan-exercise'));

    const modal = await screen.findByTestId('new-habit-plan-modal-exercise');
    expect(screen.getByTestId('habit-plan-title-exercise')).toHaveValue('保持锻炼 · 28天计划');
    // Board today 2026-09-23 → +27 days = 2026-10-20, inclusive 28 days.
    expect(screen.getByTestId('habit-plan-start-exercise')).toHaveValue('2026-09-23');
    expect(screen.getByTestId('habit-plan-end-exercise')).toHaveValue('2026-10-20');
    for (const week of [1, 2, 3, 4]) {
      expect(within(modal).getByTestId(`habit-plan-week-exercise-${week}`)).toBeInTheDocument();
    }
    expect(within(modal).queryByTestId('habit-plan-week-exercise-5')).toBeNull();
    // Every week needs ≥1 task before submit unlocks.
    expect(screen.getByTestId('habit-plan-submit-exercise')).toBeDisabled();
  });

  it('week blocks follow the date range (ceil(days/7)), preserving typed text', async () => {
    stubFetch(stubPlans([]));
    renderPage();
    await screen.findByTestId('habit-band-row-exercise');

    fireEvent.click(screen.getByTestId('habit-menu-exercise'));
    fireEvent.click(await screen.findByTestId('habit-new-plan-exercise'));
    await screen.findByTestId('new-habit-plan-modal-exercise');

    // 7 days → exactly 1 week; typed text survives later resizes.
    fireEvent.change(screen.getByTestId('habit-plan-end-exercise'), {
      target: { value: '2026-09-29' },
    });
    expect(screen.getByTestId('habit-plan-week-exercise-1')).toBeInTheDocument();
    expect(screen.queryByTestId('habit-plan-week-exercise-2')).toBeNull();
    fireEvent.change(screen.getByTestId('habit-plan-week-exercise-1'), {
      target: { value: '每天 8k 步' },
    });

    // 8 days → 2 weeks (partial tail week).
    fireEvent.change(screen.getByTestId('habit-plan-end-exercise'), {
      target: { value: '2026-09-30' },
    });
    expect(screen.getByTestId('habit-plan-week-exercise-1')).toHaveValue('每天 8k 步');
    expect(screen.getByTestId('habit-plan-week-exercise-2')).toBeInTheDocument();
    expect(screen.queryByTestId('habit-plan-week-exercise-3')).toBeNull();

    // End before start → no week blocks, submit stays locked.
    fireEvent.change(screen.getByTestId('habit-plan-end-exercise'), {
      target: { value: '2026-09-22' },
    });
    expect(screen.queryByTestId('habit-plan-week-exercise-1')).toBeNull();
    expect(screen.getByTestId('habit-plan-submit-exercise')).toBeDisabled();
  });

  it('submit assembles weekly_tasks per week and toasts the generated Queue cards', async () => {
    const fetchMock = stubFetch((url, init) => {
      if (init?.method === 'POST' && url.endsWith('/habit-plans')) {
        return jsonResponse(201, {
          ok: true,
          plan: { ...ACTIVE_PLAN, id: 'hp-new', title: '秋季冲刺' },
          kanban_card_ids: ['kb_w1', 'kb_w2', 'kb_w3', 'kb_w4'],
        });
      }
      return stubPlans([])(url, init);
    });
    renderPage();
    await screen.findByTestId('habit-band-row-exercise');

    fireEvent.click(screen.getByTestId('habit-menu-exercise'));
    fireEvent.click(await screen.findByTestId('habit-new-plan-exercise'));
    await screen.findByTestId('new-habit-plan-modal-exercise');

    fireEvent.change(screen.getByTestId('habit-plan-title-exercise'), {
      target: { value: '秋季冲刺' },
    });
    const weeks = [
      '控制饮食\n\n每天 8k 步\n', // blank lines drop
      '晨跑 3 次',
      '力量训练',
      '复盘',
    ];
    weeks.forEach((text, index) => {
      fireEvent.change(screen.getByTestId(`habit-plan-week-exercise-${index + 1}`), {
        target: { value: text },
      });
    });
    const submit = screen.getByTestId('habit-plan-submit-exercise');
    expect(submit).toBeEnabled();
    fireEvent.click(submit);

    expect(await screen.findByText('阶段计划已创建')).toBeInTheDocument();
    expect(await screen.findByText(/周卡已生成到看板 Queue/)).toBeInTheDocument();
    const call = fetchMock.mock.calls.find(
      ([input, init]) => init?.method === 'POST' && String(input).endsWith('/habit-plans'),
    );
    expect(call).toBeDefined();
    expect(JSON.parse(String(call?.[1]?.body))).toEqual({
      title: '秋季冲刺',
      habit_id: 'exercise',
      start_date: '2026-09-23',
      end_date: '2026-10-20',
      generate_weekly_cards: true,
      weekly_tasks: [
        { week: 1, tasks: ['控制饮食', '每天 8k 步'] },
        { week: 2, tasks: ['晨跑 3 次'] },
        { week: 3, tasks: ['力量训练'] },
        { week: 4, tasks: ['复盘'] },
      ],
    });
    // Modal closes on success.
    await waitFor(() =>
      expect(screen.queryByTestId('new-habit-plan-modal-exercise')).toBeNull(),
    );
  });

  it('422 invalid_weekly_tasks surfaces the server message inline', async () => {
    stubFetch((url, init) => {
      if (init?.method === 'POST' && url.endsWith('/habit-plans')) {
        return jsonResponse(422, {
          code: 'invalid_weekly_tasks',
          message: 'weekly_tasks must cover exactly 4 weeks',
        });
      }
      return stubPlans([])(url, init);
    });
    renderPage();
    await screen.findByTestId('habit-band-row-exercise');

    fireEvent.click(screen.getByTestId('habit-menu-exercise'));
    fireEvent.click(await screen.findByTestId('habit-new-plan-exercise'));
    await screen.findByTestId('new-habit-plan-modal-exercise');

    for (const week of [1, 2, 3, 4]) {
      fireEvent.change(screen.getByTestId(`habit-plan-week-exercise-${week}`), {
        target: { value: '任务' },
      });
    }
    fireEvent.click(screen.getByTestId('habit-plan-submit-exercise'));

    const alert = await screen.findByTestId('mutation-error');
    expect(alert).toHaveTextContent('weekly_tasks must cover exactly 4 weeks');
    // The modal stays open so the user can fix and retry.
    expect(screen.getByTestId('new-habit-plan-modal-exercise')).toBeInTheDocument();
  });
});

// --- Timeline P1: 分层 / 归档泳道 / 折叠 / 虚位 / 空行 / 撞期 / URL --------

function makeP1Project(overrides: Record<string, unknown>) {
  return {
    id: '',
    title: '',
    status: 'active',
    kind: 'work',
    visibility: 'private',
    summary: '',
    time_range: '',
    goal_refs: ['g1'],
    milestones: [],
    queue: [],
    doing: [],
    someday: [],
    column_counts: {},
    done_count: 0,
    archived_done_count: 0,
    evidence_ref_count: 0,
    last_activity: '',
    habit_id: '',
    ...overrides,
  };
}

const BOARD_P1 = {
  profile: 'alice',
  today: '2026-09-25',
  north_star: '',
  goals: [
    {
      id: 'g1',
      title: '目标',
      status: 'active',
      summary: '',
      target: '',
      projects: [
        makeP1Project({
          id: 'p_long',
          title: '长项目',
          time_range: '2026-08-01/2026-11-30',
          queue: [
            // 45d span → sinks to a 期间带.
            makeTask({ id: 't_long', title: '长任务', planned_start: '2026-09-01', planned_end: '2026-10-15', project_id: 'p_long' }),
            // 5d + 7d future bars overlapping 09-30→10-02 → 撞期.
            makeTask({ id: 't_short', title: '短任务', planned_start: '2026-09-28', planned_end: '2026-10-02', project_id: 'p_long' }),
            makeTask({ id: 't_clash', title: '撞期任务', planned_start: '2026-09-30', planned_end: '2026-10-06', project_id: 'p_long' }),
          ],
          someday: [
            // 虚位 whose activation date is today → already 朱砂 expired.
            makeTask({ id: 't_seat', title: '虚位任务', section: 'Someday / Maybe', column: 'someday', planned_start: '2026-09-25', project_id: 'p_long' }),
          ],
        }),
        // Nothing inside the window → 空行瘦身.
        makeP1Project({ id: 'p_empty', title: '空项目', time_range: '2026-01-01/2026-02-01' }),
      ],
    },
  ],
  ungrouped_projects: [
    makeP1Project({
      id: 'p_arch',
      title: '旧项目',
      status: 'archived',
      goal_refs: [],
      time_range: '2026-06-01/2026-08-31',
      queue: [
        makeTask({ id: 't_arch', title: '旧任务', planned_start: '2026-09-26', planned_end: '2026-09-30', project_id: 'p_arch' }),
      ],
    }),
  ],
  unassigned_tasks: [],
  habits: [],
  stats: {},
};

function stubP1Fetch() {
  return stubFetch((url) => {
    if (url.includes('/profiles/alice/projects-board')) {
      return new Response(JSON.stringify(BOARD_P1), {
        status: 200,
        headers: { 'Content-Type': 'application/json', ETag: BOARD_ETAG },
      });
    }
    return undefined as unknown as Response;
  });
}

describe('ProjectsPage timeline P1', () => {
  it('sinks ≥14d bars to 期间带 and keeps short bars on sub-lanes', async () => {
    stubP1Fetch();
    renderPage('/p/alice/projects?view=timeline');

    expect(await screen.findByTestId('timeline-period-t_long')).toBeInTheDocument();
    expect(screen.getByTestId('timeline-bar-t_short')).toBeInTheDocument();
    // Someday seat: dashed 虚位, expired (planned_start == today → 朱砂).
    expect(screen.getByTestId('timeline-someday-t_seat')).toHaveAttribute('data-expired', 'true');
  });

  it('marks future-zone schedule clashes with the 朱砂 stroke flag', async () => {
    stubP1Fetch();
    renderPage('/p/alice/projects?view=timeline');

    expect(await screen.findByTestId('timeline-bar-t_short')).toHaveAttribute('data-clash', 'true');
    expect(screen.getByTestId('timeline-bar-t_clash')).toHaveAttribute('data-clash', 'true');
    // The period band never flashes 朱砂 even though it overlaps both.
    expect(screen.getByTestId('timeline-period-t_long')).not.toHaveAttribute('data-clash');
  });

  it('slims lanes with nothing in the window and says so on the label', async () => {
    stubP1Fetch();
    renderPage('/p/alice/projects?view=timeline');

    expect(await screen.findByTestId('timeline-note-p_empty')).toHaveTextContent('本窗口无活动');
    // The busy lane shows no such note.
    expect(screen.queryByTestId('timeline-note-p_long')).not.toBeInTheDocument();
  });

  it('renders archived projects as a read-only 归档 section behind a toggle', async () => {
    stubP1Fetch();
    renderPage('/p/alice/projects?view=timeline');

    const section = await screen.findByTestId('timeline-group-archived');
    expect(within(section).getByTestId('timeline-badge-p_arch')).toHaveTextContent('归档');
    // 整行降饱和 + 无地色带, bars muted (pointer drag disabled → no onPointerDown).
    expect(within(section).getByTestId('timeline-bar-t_arch')).toBeInTheDocument();
    expect(within(section).queryByTestId('project-range-p_arch')).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId('timeline-archived-toggle'));
    await waitFor(() =>
      expect(screen.queryByTestId('timeline-group-archived')).not.toBeInTheDocument(),
    );
    expect(window.localStorage.getItem('nblane.timeline.archived')).toBe('0');
  });

  it('collapses a row to envelope + ticks + count, persisted per case id', async () => {
    stubP1Fetch();
    renderPage('/p/alice/projects?view=timeline');

    const row = await screen.findByTestId('timeline-row-p_long');
    fireEvent.click(screen.getByTestId('timeline-collapse-p_long'));

    expect(await within(row).findByTestId('collapsed-envelope')).toBeInTheDocument();
    // 2 short bars + 1 期间带 + 1 虚位 seat = 4 ticks, 「4 任务」.
    expect(within(row).getAllByTestId('collapsed-tick')).toHaveLength(4);
    expect(within(row).getByTestId('collapsed-count')).toHaveTextContent('4 任务');
    // Bars leave the sub-lanes while collapsed.
    expect(within(row).queryByTestId('timeline-bar-t_short')).not.toBeInTheDocument();
    expect(JSON.parse(window.localStorage.getItem('nblane.timeline.collapsed') ?? '[]')).toEqual([
      'p_long',
    ]);

    fireEvent.click(screen.getByTestId('timeline-collapse-p_long'));
    expect(await within(row).findByTestId('timeline-bar-t_short')).toBeInTheDocument();
    expect(window.localStorage.getItem('nblane.timeline.collapsed')).toBe('[]');
  });

  it('round-trips zoom/window through the URL and resets to defaults', async () => {
    stubP1Fetch();
    renderPage('/p/alice/projects?view=timeline');
    const toolbar = await screen.findByTestId('timeline-toolbar');

    // Default 半年窗 (2026-09-25 − 136d → time_range right extension 11-30).
    await waitFor(() => expect(toolbar).toHaveTextContent('2026-05-12 → 2026-11-30'));
    expect(lastSearch).toContain('tz=half');

    // Focus writes a custom window into the URL.
    fireEvent.click(screen.getByTestId('timeline-focus-p_long'));
    await waitFor(() => expect(toolbar).toHaveTextContent('2026-07-26 → 2026-12-06'));
    expect(lastSearch).toContain('tws=2026-07-26');
    expect(lastSearch).toContain('twe=2026-12-06');

    // 重置视图: back to the default window; window params leave the URL.
    fireEvent.click(screen.getByTestId('timeline-reset-view'));
    await waitFor(() => expect(toolbar).toHaveTextContent('2026-05-12 → 2026-11-30'));
    expect(lastSearch).toContain('tz=half');
    expect(lastSearch).not.toContain('tws=');
  });

  it('restores the zoom preset from the URL on entry', async () => {
    stubP1Fetch();
    renderPage('/p/alice/projects?view=timeline&tz=month');
    const toolbar = await screen.findByTestId('timeline-toolbar');
    // 月窗: today − 23d = 2026-09-02; right extension to the time_range end.
    await waitFor(() => expect(toolbar).toHaveTextContent('2026-09-02 → 2026-11-30'));
  });
});
