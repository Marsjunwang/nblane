// Tests for TaskDetailCard edit mode (编辑): the PATCH /kanban/cards/{ref}
// form for title/context/why/project_id/tags under the kanban.md ETag.

import { fireEvent, screen, waitFor } from '@testing-library/react';
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

function renderCard(task: ProjectsBoardTask = TASK) {
  const fetchMock = vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
    if (init?.method === 'PATCH') {
      return patchResponse('读 VLA 综述 · 第二版');
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
      onClose={() => {}}
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
        `/profiles/alice/kanban/cards/${encodeURIComponent('读 VLA 综述')}`,
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
