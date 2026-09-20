import { fireEvent, screen, waitFor, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';

import { jsonResponse, renderWithProviders } from '../test/render';
import { ProjectBoardPage } from './ProjectBoardPage';

const ETAG = 'W/"board-sha"';

const BOARD = {
  profile: 'alice',
  updated: '2026-09-19',
  summary: {
    status_counts: { active: 1, paused: 0, completed: 1, archived: 0 },
    unassigned_tasks: 1,
    unassigned_evidence: 1,
    current_goal_projects: 1,
  },
  cases: [
    {
      id: 'project:robot-arm',
      title: 'Robot Arm',
      status: 'active',
      kind: 'internal',
      visibility: 'private',
      time_range: '',
      summary: 'Build the arm',
      notes: '',
      goal_refs: ['goal-1'],
      task_refs: ['task-owned'],
      evidence_refs: ['ev-1'],
      source_refs: [],
      experience_refs: [],
      output_refs: [],
      milestones: [
        {
          id: 'milestone:mvp',
          title: 'MVP',
          status: 'active',
          target: 'demo',
          date: '2026-10-01',
          summary: '',
          task_refs: ['task-owned'],
          evidence_refs: [],
          source_refs: [],
          output_refs: [],
          done_count: 0,
          total_count: 1,
        },
      ],
      tasks: [
        {
          id: 'task-owned',
          title: 'Owned task',
          section: 'Doing',
          done: false,
          milestone_id: '',
          started_on: '2026-09-15',
          completed_on: null,
          archived: false,
        },
      ],
      derived_time_range: '2026-09-15/2026-09-16',
    },
    {
      id: 'project:old',
      title: 'Old Project',
      status: 'completed',
      kind: 'internal',
      visibility: 'private',
      time_range: '',
      summary: '',
      notes: '',
      goal_refs: [],
      task_refs: [],
      evidence_refs: [],
      source_refs: [],
      experience_refs: [],
      output_refs: [],
      milestones: [],
      tasks: [],
      derived_time_range: '',
    },
  ],
  options: {
    goals: [{ id: 'goal-1', label: 'Ship VLA demo · active', owner: '' }],
    tasks: [
      { id: 'task-owned', label: '[Doing] Owned task · task-owned', owner: 'project:robot-arm' },
      { id: 'task-free', label: '[Queue] Free task · task-free', owner: '' },
    ],
    evidence: [{ id: 'ev-1', label: 'Arm demo video · reviewed', owner: '' }],
    sources: [],
    experiences: [],
    outputs: [],
  },
};

const CASE_RESULT = { ok: true, case: BOARD.cases[0], warnings: [] };

function boardResponse(body: unknown = BOARD): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json', ETag: ETAG },
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

function renderPage() {
  return renderWithProviders(
    <Routes>
      <Route path="/p/:name/project-board" element={<ProjectBoardPage />} />
    </Routes>,
    '/p/alice/project-board',
  );
}

function mockBoardOnly() {
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.includes('/profiles/alice/project-board')) {
      return boardResponse();
    }
    return jsonResponse(404, { code: 'not_found', message: 'not found' });
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

async function selectRobotArm() {
  const card = await screen.findByTestId('case-card-project:robot-arm');
  fireEvent.click(within(card).getByRole('button', { name: '选择' }));
  return screen.findByTestId('case-detail');
}

describe('ProjectBoardPage', () => {
  it('renders the summary chips and case cards', async () => {
    mockBoardOnly();
    renderPage();

    const card = await screen.findByTestId('case-card-project:robot-arm');
    expect(card).toHaveTextContent('Robot Arm');
    expect(card).toHaveTextContent('里程碑 1');
    const summary = screen.getByTestId('board-summary');
    expect(summary).toHaveTextContent('进行中 1');
    expect(summary).toHaveTextContent('已完成 1');
    expect(summary).toHaveTextContent('未归属任务 1');
    expect(summary).toHaveTextContent('未归属证据 1');
    expect(summary).toHaveTextContent('当前目标项目 1');
    // Completed cases live under their own (hidden) status tab.
    expect(screen.getByTestId('case-card-project:old')).not.toBeVisible();
  });

  it('selects a case and saves the basics form with If-Match', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes('/save')) {
        expect(init?.method).toBe('POST');
        expect((init?.headers as Record<string, string>)['If-Match']).toBe(ETAG);
        const body = JSON.parse(String(init?.body));
        expect(body.title).toBe('Robot Arm v2');
        expect(body.summary).toBe('Build the arm');
        expect(body.task_refs).toEqual(['task-owned']);
        return jsonResponse(200, CASE_RESULT);
      }
      if (url.includes('/profiles/alice/project-board')) {
        return boardResponse();
      }
      return jsonResponse(404, { code: 'not_found', message: 'not found' });
    });
    vi.stubGlobal('fetch', fetchMock);

    renderPage();
    const detail = await selectRobotArm();
    const titleInput = within(detail).getByDisplayValue('Robot Arm');
    fireEvent.change(titleInput, { target: { value: 'Robot Arm v2' } });
    fireEvent.click(within(detail).getByRole('button', { name: '保存项目' }));
    await waitFor(() =>
      expect(fetchMock.mock.calls.some(([url]) => String(url).includes('/save'))).toBe(true),
    );
  });

  it('flags a stale ETag (412) on save as a conflict with a refresh button', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('/save')) {
        return jsonResponse(412, {
          code: 'etag_mismatch',
          message: 'Project board source files changed since they were loaded',
        });
      }
      if (url.includes('/profiles/alice/project-board')) {
        return boardResponse();
      }
      return jsonResponse(404, { code: 'not_found', message: 'not found' });
    });
    vi.stubGlobal('fetch', fetchMock);

    renderPage();
    const detail = await selectRobotArm();
    fireEvent.click(within(detail).getByRole('button', { name: '保存项目' }));

    // 412 is recognized as a conflict: yellow unified copy, not the raw red
    // error message.
    const conflict = await within(detail).findByTestId('conflict-alert');
    expect(conflict).toHaveTextContent('数据已被他人修改');
    expect(conflict).toHaveTextContent('请刷新后重试');
    expect(within(detail).queryByText(/source files changed/)).not.toBeInTheDocument();

    const boardGets = () =>
      fetchMock.mock.calls.filter(([input]) =>
        String(input).endsWith('/profiles/alice/project-board'),
      ).length;
    const before = boardGets();
    fireEvent.click(within(detail).getByRole('button', { name: '刷新' }));
    await waitFor(() => expect(boardGets()).toBeGreaterThan(before));
  });

  it('creates a project from the create form', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith('/project-board/cases')) {
        expect(init?.method).toBe('POST');
        expect((init?.headers as Record<string, string>)['If-Match']).toBe(ETAG);
        const body = JSON.parse(String(init?.body));
        expect(body.title).toBe('New Proj');
        expect(body.kind).toBe('internal');
        return jsonResponse(201, {
          ok: true,
          case: { ...BOARD.cases[0], id: 'project:new-proj', title: 'New Proj' },
          warnings: [],
        });
      }
      if (url.includes('/profiles/alice/project-board')) {
        return boardResponse();
      }
      return jsonResponse(404, { code: 'not_found', message: 'not found' });
    });
    vi.stubGlobal('fetch', fetchMock);

    renderPage();
    const form = await screen.findByTestId('create-case-form');
    fireEvent.click(within(form).getByRole('button', { name: '展开' }));
    fireEvent.change(within(form).getByLabelText(/标题/), {
      target: { value: 'New Proj' },
    });
    fireEvent.click(within(form).getByRole('button', { name: '创建项目' }));
    await waitFor(() =>
      expect(
        fetchMock.mock.calls.some(([url]) => String(url).endsWith('/project-board/cases')),
      ).toBe(true),
    );
  });

  it('adds a milestone from the milestones tab', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith('/milestones')) {
        const body = JSON.parse(String(init?.body));
        expect(body.title).toBe('Launch');
        expect(body.target).toBe('public demo');
        expect((init?.headers as Record<string, string>)['If-Match']).toBe(ETAG);
        return jsonResponse(201, CASE_RESULT);
      }
      if (url.includes('/profiles/alice/project-board')) {
        return boardResponse();
      }
      return jsonResponse(404, { code: 'not_found', message: 'not found' });
    });
    vi.stubGlobal('fetch', fetchMock);

    renderPage();
    const detail = await selectRobotArm();
    fireEvent.click(within(detail).getByRole('tab', { name: '里程碑' }));
    const form = await within(detail).findByTestId('add-milestone-form');
    fireEvent.change(within(form).getByLabelText('标题'), { target: { value: 'Launch' } });
    fireEvent.change(within(form).getByLabelText('目标'), {
      target: { value: 'public demo' },
    });
    fireEvent.click(within(form).getByRole('button', { name: '添加里程碑' }));
    await waitFor(() =>
      expect(
        fetchMock.mock.calls.some(([url]) => String(url).endsWith('/milestones')),
      ).toBe(true),
    );
  });

  it('adds a project task from the tasks tab', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith('/tasks')) {
        const body = JSON.parse(String(init?.body));
        expect(body.title).toBe('Wire the gripper');
        expect(body.section).toBe('Queue');
        expect((init?.headers as Record<string, string>)['If-Match']).toBe(ETAG);
        return jsonResponse(201, {
          ok: true,
          card: { title: 'Wire the gripper', id: 'task-new' },
          section: 'Queue',
          warnings: [],
          merged_external: false,
          merge_notices: [],
        });
      }
      if (url.includes('/profiles/alice/project-board')) {
        return boardResponse();
      }
      return jsonResponse(404, { code: 'not_found', message: 'not found' });
    });
    vi.stubGlobal('fetch', fetchMock);

    renderPage();
    const detail = await selectRobotArm();
    fireEvent.click(within(detail).getByRole('tab', { name: '任务' }));
    expect(await within(detail).findByTestId('project-task-task-owned')).toHaveTextContent(
      'Owned task',
    );
    const form = within(detail).getByTestId('add-task-form');
    fireEvent.change(within(form).getByLabelText('标题'), {
      target: { value: 'Wire the gripper' },
    });
    fireEvent.click(within(form).getByRole('button', { name: '新建任务' }));
    await waitFor(() =>
      expect(fetchMock.mock.calls.some(([url]) => String(url).endsWith('/tasks'))).toBe(true),
    );
  });

  it('moves a task to another kanban section', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes('/tasks/task-owned/move')) {
        const body = JSON.parse(String(init?.body));
        expect(body.target_section).toBe('Done');
        expect((init?.headers as Record<string, string>)['If-Match']).toBe(ETAG);
        return jsonResponse(200, {
          ok: true,
          card: { title: 'Owned task', id: 'task-owned', done: true },
          section: 'Done',
          warnings: [],
          merged_external: false,
          merge_notices: [],
        });
      }
      if (url.includes('/profiles/alice/project-board')) {
        return boardResponse();
      }
      return jsonResponse(404, { code: 'not_found', message: 'not found' });
    });
    vi.stubGlobal('fetch', fetchMock);

    renderPage();
    const detail = await selectRobotArm();
    fireEvent.click(within(detail).getByRole('tab', { name: '任务' }));
    await within(detail).findByTestId('project-task-task-owned');
    const moveSelect = screen.getByLabelText('移动 Owned task');
    fireEvent.change(moveSelect, { target: { value: 'Done' } });
    await waitFor(() =>
      expect(
        fetchMock.mock.calls.some(([url]) => String(url).includes('/tasks/task-owned/move')),
      ).toBe(true),
    );
  });

  it('shows AI suggestions and merges them into the form on confirm', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes('/suggest-refs')) {
        return jsonResponse(200, {
          ok: true,
          backend: 'fake',
          suggestions: {
            goal_refs: [],
            task_refs: ['task-free'],
            evidence_refs: [],
            source_refs: [],
            output_refs: [],
          },
          rationale: 'closest matches',
          warnings: [],
        });
      }
      if (url.includes('/save')) {
        const body = JSON.parse(String(init?.body));
        expect(body.task_refs).toEqual(['task-owned', 'task-free']);
        return jsonResponse(200, CASE_RESULT);
      }
      if (url.includes('/profiles/alice/project-board')) {
        return boardResponse();
      }
      return jsonResponse(404, { code: 'not_found', message: 'not found' });
    });
    vi.stubGlobal('fetch', fetchMock);

    renderPage();
    const detail = await selectRobotArm();
    fireEvent.click(within(detail).getByTestId('suggest-refs-button'));
    const result = await within(detail).findByTestId('suggest-result');
    expect(result).toHaveTextContent('共 1 条建议');
    expect(result).toHaveTextContent('任务: task-free');
    fireEvent.click(within(result).getByRole('button', { name: '合并到表单' }));
    expect(within(detail).queryByTestId('suggest-result')).not.toBeInTheDocument();
    fireEvent.click(within(detail).getByRole('button', { name: '保存项目' }));
    await waitFor(() =>
      expect(fetchMock.mock.calls.some(([url]) => String(url).includes('/save'))).toBe(true),
    );
  });

  it('shows a degradation card when AI suggest-refs answers 422', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('/suggest-refs')) {
        return jsonResponse(422, {
          code: 'project_suggest_refs_failed',
          message: 'routing_error: no backend available',
        });
      }
      if (url.includes('/profiles/alice/project-board')) {
        return boardResponse();
      }
      return jsonResponse(404, { code: 'not_found', message: 'not found' });
    });
    vi.stubGlobal('fetch', fetchMock);

    renderPage();
    const detail = await selectRobotArm();
    fireEvent.click(within(detail).getByTestId('suggest-refs-button'));
    const error = await within(detail).findByTestId('suggest-error');
    expect(error).toHaveTextContent('AI 建议不可用');
    expect(error).toHaveTextContent('no backend available');
  });

  it('shows an error alert when the board fails to load', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => jsonResponse(403, { code: 'profile_forbidden', message: 'denied' })),
    );
    renderPage();
    expect(await screen.findByText('加载失败')).toBeInTheDocument();
  });

  it('keeps an unsaved basics draft when a board mutation refetches the board', async () => {
    let boardReads = 0;
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('/tasks/task-owned/move')) {
        return jsonResponse(200, {
          ok: true,
          card: { title: 'Owned task', id: 'task-owned', done: true },
          section: 'Done',
          warnings: [],
          merged_external: false,
          merge_notices: [],
        });
      }
      if (url.includes('/profiles/alice/project-board')) {
        boardReads += 1;
        // The refetch after the move carries a fresh `updated` stamp — the
        // old key scheme would remount CaseDetail here and wipe the draft.
        return boardResponse(boardReads === 1 ? BOARD : { ...BOARD, updated: '2026-09-20' });
      }
      return jsonResponse(404, { code: 'not_found', message: 'not found' });
    });
    vi.stubGlobal('fetch', fetchMock);

    renderPage();
    const detail = await selectRobotArm();
    fireEvent.change(within(detail).getByDisplayValue('Robot Arm'), {
      target: { value: 'Robot Arm v2' },
    });

    fireEvent.click(within(detail).getByRole('tab', { name: '任务' }));
    await within(detail).findByTestId('project-task-task-owned');
    fireEvent.change(screen.getByLabelText('移动 Owned task'), { target: { value: 'Done' } });
    await waitFor(() => expect(boardReads).toBeGreaterThanOrEqual(2));

    fireEvent.click(within(screen.getByTestId('case-detail')).getByRole('tab', { name: '基本信息' }));
    expect(
      within(screen.getByTestId('case-detail')).getByDisplayValue('Robot Arm v2'),
    ).toBeInTheDocument();
  });

  it('follows server-side case changes while the draft is untouched', async () => {
    let boardReads = 0;
    const serverCase = { ...BOARD.cases[0], title: 'Robot Arm (server edit)' };
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('/tasks/task-owned/move')) {
        return jsonResponse(200, {
          ok: true,
          card: { title: 'Owned task', id: 'task-owned', done: true },
          section: 'Done',
          warnings: [],
          merged_external: false,
          merge_notices: [],
        });
      }
      if (url.includes('/profiles/alice/project-board')) {
        boardReads += 1;
        return boardResponse(
          boardReads === 1
            ? BOARD
            : { ...BOARD, updated: '2026-09-20', cases: [serverCase, BOARD.cases[1]] },
        );
      }
      return jsonResponse(404, { code: 'not_found', message: 'not found' });
    });
    vi.stubGlobal('fetch', fetchMock);

    renderPage();
    const detail = await selectRobotArm();

    fireEvent.click(within(detail).getByRole('tab', { name: '任务' }));
    await within(detail).findByTestId('project-task-task-owned');
    fireEvent.change(screen.getByLabelText('移动 Owned task'), { target: { value: 'Done' } });

    // Pristine form: syncs to the server value once the refetch lands.
    await waitFor(() =>
      expect(
        within(screen.getByTestId('case-detail')).getByDisplayValue(
          'Robot Arm (server edit)',
        ),
      ).toBeInTheDocument(),
    );
  });
});
