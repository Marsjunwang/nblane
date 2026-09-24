// Tests for TaskDetailCard edit mode (编辑): the PATCH /kanban/cards/{ref}
// form for title/context/why/project_id/tags under the kanban.md ETag.

import { fireEvent, screen, waitFor } from '@testing-library/react';
import { cleanNotifications } from '@mantine/notifications';
import { afterEach, describe, expect, it, vi } from 'vitest';

import type { ProjectsBoardProject, ProjectsBoardTask } from '../../api/types';
import { jsonResponse, renderWithProviders } from '../../test/render';
import { TaskDetailCard } from './TaskDetailCard';

const KANBAN_ETAG = 'W/"kanban-test"';

const PROJECT: ProjectsBoardProject = {
  id: 'p1',
  title: '知识补全',
  status: 'active',
  kind: 'learning',
  visibility: 'private',
  summary: '',
  time_range: '',
  goal_refs: [],
  milestones: [],
  queue: [],
  doing: [],
  someday: [],
  column_counts: { queue: 0, doing: 0, someday: 0, done: 0 },
  done_count: 0,
  archived_done_count: 0,
  evidence_ref_count: 0,
  last_activity: '',
  habit_id: '',
} as unknown as ProjectsBoardProject;

const TASK: ProjectsBoardTask = {
  id: 'kb_1',
  title: '读 VLA 综述',
  section: 'Queue',
  column: 'queue',
  done: false,
  context: '先扫一遍引用',
  why: '建立全景',
  started_on: null,
  completed_on: null,
  planned_start: null,
  planned_end: null,
  project_id: 'p1',
  milestone_id: '',
  tags: 'reading, survey',
  todos: [
    { text: '扫引用列表', done: true },
    { text: '整理笔记', done: false },
  ],
} as unknown as ProjectsBoardTask;

function patchResponse(title: string) {
  return jsonResponse(200, {
    ok: true,
    card: { title, done: false },
    section: 'Queue',
    warnings: [],
    merged_external: false,
    merge_notices: [],
  });
}

function deleteResponse() {
  return jsonResponse(200, { ok: true, deleted_ref: 'kb_1', deleted_title: '读 VLA 综述' });
}

function renderCard(task: ProjectsBoardTask = TASK, { onClose }: { onClose?: () => void } = {}) {
  const fetchMock = vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
    if (init?.method === 'PATCH') {
      return patchResponse('读 VLA 综述 · 第二版');
    }
    if (init?.method === 'DELETE') {
      return deleteResponse();
    }
    return jsonResponse(404, { code: 'not_found', message: 'not found' });
  });
  vi.stubGlobal('fetch', fetchMock);
  renderWithProviders(
    <TaskDetailCard
      profile="alice"
      task={task}
      project={PROJECT}
      projects={[PROJECT]}
      habits={[]}
      today="2026-09-23"
      kanbanEtag={KANBAN_ETAG}
      onClose={onClose ?? (() => {})}
      onRefresh={() => {}}
    />,
  );
  return fetchMock;
}

describe('TaskDetailCard edit mode', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('编辑 seeds the form from the task and cancel leaves without a PATCH', async () => {
    const fetchMock = renderCard();
    fireEvent.click(screen.getByTestId('detail-edit'));

    expect(screen.getByTestId('edit-title')).toHaveValue('读 VLA 综述');
    expect(screen.getByTestId('edit-context')).toHaveValue('先扫一遍引用');
    expect(screen.getByTestId('edit-why')).toHaveValue('建立全景');
    expect(screen.getByTestId('edit-tags')).toHaveValue('reading, survey');
    // Nothing changed yet -> save stays disabled.
    expect(screen.getByTestId('edit-save')).toBeDisabled();
    // The action row is replaced while editing.
    expect(screen.queryByTestId('detail-done')).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId('edit-cancel'));
    expect(screen.queryByTestId('edit-title')).not.toBeInTheDocument();
    expect(screen.getByTestId('detail-edit')).toBeInTheDocument();
    expect(fetchMock.mock.calls.some(([, init]) => init?.method === 'PATCH')).toBe(false);
  });

  it('save PATCHes only changed fields with If-Match and exits edit mode', async () => {
    const fetchMock = renderCard();
    fireEvent.click(screen.getByTestId('detail-edit'));

    fireEvent.change(screen.getByTestId('edit-title'), {
      target: { value: '读 VLA 综述 · 第二版' },
    });
    fireEvent.change(screen.getByTestId('edit-tags'), {
      target: { value: 'reading survey v2' },
    });
    const save = screen.getByTestId('edit-save');
    expect(save).toBeEnabled();
    fireEvent.click(save);

    await waitFor(() => {
      const call = fetchMock.mock.calls.find(([, init]) => init?.method === 'PATCH');
      expect(call).toBeDefined();
      const [input, init] = call!;
      expect(String(input)).toContain(
        `/profiles/alice/kanban/cards/${TASK.id}`,
      );
      expect((init?.headers as Record<string, string>)['If-Match']).toBe(KANBAN_ETAG);
      // Only the two changed fields go out; context/why/project_id keep.
      expect(JSON.parse(String(init?.body))).toEqual({
        title: '读 VLA 综述 · 第二版',
        tags: ['reading', 'survey', 'v2'],
      });
    });
    // Success closes the edit form back to the reading view.
    await waitFor(() => {
      expect(screen.queryByTestId('edit-title')).not.toBeInTheDocument();
    });
  });

  it('blank title keeps save disabled', () => {
    renderCard();
    fireEvent.click(screen.getByTestId('detail-edit'));
    fireEvent.change(screen.getByTestId('edit-title'), { target: { value: '   ' } });
    // Title change to blank is not a valid edit; with nothing else changed
    // the form is neither dirty nor valid.
    expect(screen.getByTestId('edit-save')).toBeDisabled();
  });

  it('schedule row stays the only planned-date editor in edit mode', () => {
    renderCard();
    fireEvent.click(screen.getByTestId('detail-edit'));
    // 排期 row is still rendered (not duplicated inside the edit form).
    expect(screen.getByLabelText('排期开始')).toBeInTheDocument();
    expect(screen.getByTestId('schedule-save')).toBeInTheDocument();
  });
});

describe('TaskDetailCard TODO checklist', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  async function lastPatchBody(fetchMock: ReturnType<typeof renderCard>) {
    await waitFor(
      () => {
        expect(fetchMock.mock.calls.some(([, init]) => init?.method === 'PATCH')).toBe(true);
      },
      { timeout: 2000 },
    );
    const call = fetchMock.mock.calls.find(([, init]) => init?.method === 'PATCH')!;
    expect((call[1]?.headers as Record<string, string>)['If-Match']).toBe(KANBAN_ETAG);
    return JSON.parse(String(call[1]?.body)) as { todos: { text: string; done: boolean }[] };
  }

  it('renders the checklist with done state and an add input', () => {
    renderCard();
    expect(screen.getByTestId('todo-section')).toBeInTheDocument();
    expect(screen.getByTestId('todo-item-0')).toHaveTextContent('扫引用列表');
    expect(screen.getByTestId('todo-item-1')).toHaveTextContent('整理笔记');
    expect(screen.getByTestId('todo-toggle-0')).toBeChecked();
    expect(screen.getByTestId('todo-toggle-1')).not.toBeChecked();
    expect(screen.getByTestId('todo-add-input')).toBeInTheDocument();
  });

  it('toggle flips optimistically and PATCHes the full list (debounced)', async () => {
    const fetchMock = renderCard();
    fireEvent.click(screen.getByTestId('todo-toggle-1'));
    // Optimistic: the checkbox flips before the debounced PATCH lands.
    expect(screen.getByTestId('todo-toggle-1')).toBeChecked();
    const body = await lastPatchBody(fetchMock);
    expect(body).toEqual({
      todos: [
        { text: '扫引用列表', done: true },
        { text: '整理笔记', done: true },
      ],
    });
  });

  it('add appends an item on Enter and PATCHes the grown list', async () => {
    const fetchMock = renderCard();
    const input = screen.getByTestId('todo-add-input');
    fireEvent.change(input, { target: { value: '写摘要' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    expect(screen.getByTestId('todo-item-2')).toHaveTextContent('写摘要');
    expect(input).toHaveValue('');
    const body = await lastPatchBody(fetchMock);
    expect(body.todos).toHaveLength(3);
    expect(body.todos[2]).toEqual({ text: '写摘要', done: false });
  });

  it('delete removes an item and PATCHes the shrunk list', async () => {
    const fetchMock = renderCard();
    fireEvent.click(screen.getByTestId('todo-delete-0'));
    expect(screen.queryByTestId('todo-item-1')).not.toBeInTheDocument();
    const body = await lastPatchBody(fetchMock);
    expect(body).toEqual({ todos: [{ text: '整理笔记', done: false }] });
  });
});

describe('TaskDetailCard 排期与标记完成', () => {
  afterEach(() => {
    cleanNotifications();
    vi.unstubAllGlobals();
  });

  it('排期 DateInput displays yyyy-mm-dd regardless of browser locale', () => {
    renderCard({ ...TASK, planned_start: '2026-09-10', planned_end: '2026-10-01' });
    // Mantine DateInput (valueFormat) — native type=date would render the
    // browser locale's mm/dd/yyyy in en-locale browsers.
    expect(screen.getByLabelText('排期开始')).toHaveValue('2026-09-10');
    expect(screen.getByLabelText('排期结束')).toHaveValue('2026-10-01');
  });

  it('标记 Done POSTs and raises a 已标记完成 notification', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (init?.method === 'POST' && url.includes('/kanban/cards/') && url.endsWith('/done')) {
        return jsonResponse(200, {
          ok: true,
          card: { ...TASK, done: true },
          section: 'Done',
          warnings: [],
          merged_external: false,
          merge_notices: [],
        });
      }
      return jsonResponse(404, { code: 'not_found', message: url });
    });
    vi.stubGlobal('fetch', fetchMock);
    renderWithProviders(
      <TaskDetailCard
        profile="alice"
        task={TASK}
        project={PROJECT}
        projects={[PROJECT]}
        habits={[]}
        today="2026-09-23"
        kanbanEtag={KANBAN_ETAG}
        onClose={() => {}}
        onRefresh={() => {}}
      />,
    );

    fireEvent.click(screen.getByTestId('detail-done'));
    // The confirmation survives the card closing on refetch.
    expect(await screen.findByText('已标记完成')).toBeInTheDocument();
    const call = fetchMock.mock.calls.find(
      ([input, init]) => init?.method === 'POST' && String(input).endsWith('/done'),
    )!;
    expect((call[1]?.headers as Record<string, string>)['If-Match']).toBe(KANBAN_ETAG);
  });
});

describe('TaskDetailCard delete action', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('删除任务 reveals the inline confirm (记入大事记 off); 取消 hides it without a DELETE', () => {
    const fetchMock = renderCard();
    fireEvent.click(screen.getByTestId('detail-delete'));

    const confirm = screen.getByTestId('delete-confirm');
    expect(confirm).toHaveTextContent('将删除任务「读 VLA 综述」,不可恢复');
    expect(screen.getByTestId('delete-record-chronicle')).not.toBeChecked();
    // The danger button collapses while the confirm is showing.
    expect(screen.queryByTestId('detail-delete')).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId('delete-cancel'));
    expect(screen.queryByTestId('delete-confirm')).not.toBeInTheDocument();
    expect(screen.getByTestId('detail-delete')).toBeInTheDocument();
    expect(fetchMock.mock.calls.some(([, init]) => init?.method === 'DELETE')).toBe(false);
  });

  it('confirm DELETEs with If-Match and record_chronicle off, then closes the card', async () => {
    const onClose = vi.fn();
    const fetchMock = renderCard(TASK, { onClose });
    fireEvent.click(screen.getByTestId('detail-delete'));
    fireEvent.click(screen.getByTestId('delete-confirm-button'));

    await waitFor(() => expect(onClose).toHaveBeenCalled());
    const call = fetchMock.mock.calls.find(([, init]) => init?.method === 'DELETE')!;
    expect(String(call[0])).toContain(
      `/profiles/alice/kanban/cards/${TASK.id}`,
    );
    expect((call[1]?.headers as Record<string, string>)['If-Match']).toBe(KANBAN_ETAG);
    expect(JSON.parse(String(call[1]?.body))).toEqual({ record_chronicle: false });
  });

  it('记入大事记 checkbox sends record_chronicle: true', async () => {
    const onClose = vi.fn();
    const fetchMock = renderCard(TASK, { onClose });
    fireEvent.click(screen.getByTestId('detail-delete'));
    fireEvent.click(screen.getByTestId('delete-record-chronicle'));
    fireEvent.click(screen.getByTestId('delete-confirm-button'));

    await waitFor(() => expect(onClose).toHaveBeenCalled());
    const call = fetchMock.mock.calls.find(([, init]) => init?.method === 'DELETE')!;
    expect(JSON.parse(String(call[1]?.body))).toEqual({ record_chronicle: true });
  });

  it('a 412 retries once with a freshly fetched ETag, then closes', async () => {
    const onClose = vi.fn();
    let deleteCalls = 0;
    const fetchMock = vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
      if (init?.method === 'DELETE') {
        deleteCalls += 1;
        if (deleteCalls === 1) {
          return new Response(JSON.stringify({ code: 'etag_mismatch', message: 'stale' }), {
            status: 412,
            headers: { 'Content-Type': 'application/json', ETag: 'W/"kanban-fresh"' },
          });
        }
        return deleteResponse();
      }
      // refreshKanbanEtag: GET the board for a fresh ETag.
      return new Response(
        JSON.stringify({ profile: 'alice', sections: [], total: 0 }),
        { status: 200, headers: { 'Content-Type': 'application/json', ETag: 'W/"kanban-fresh"' } },
      );
    });
    vi.stubGlobal('fetch', fetchMock);
    renderWithProviders(
      <TaskDetailCard
        profile="alice"
        task={TASK}
        project={PROJECT}
        projects={[PROJECT]}
        habits={[]}
        today="2026-09-23"
        kanbanEtag={KANBAN_ETAG}
        onClose={onClose}
        onRefresh={() => {}}
      />,
    );

    fireEvent.click(screen.getByTestId('detail-delete'));
    fireEvent.click(screen.getByTestId('delete-confirm-button'));

    await waitFor(() => expect(onClose).toHaveBeenCalled());
    const deletes = fetchMock.mock.calls.filter(([, init]) => init?.method === 'DELETE');
    expect(deletes).toHaveLength(2);
    expect((deletes[0][1]?.headers as Record<string, string>)['If-Match']).toBe(KANBAN_ETAG);
    expect((deletes[1][1]?.headers as Record<string, string>)['If-Match']).toBe('W/"kanban-fresh"');
  });
});
