import { fireEvent, screen, waitFor } from '@testing-library/react';
import { cleanNotifications } from '@mantine/notifications';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';

import { jsonResponse, renderWithProviders } from '../test/render';
import { KanbanPage } from './KanbanPage';

const BOARD = {
  profile: 'alice',
  total: 2,
  sections: [
    {
      name: 'Queue',
      tasks: [
        {
          id: 't0',
          title: '读 VLA 综述',
          done: false,
          tags: '',
          started_on: null,
          completed_on: null,
          subtasks: [],
        },
      ],
    },
    {
      name: '进行中',
      tasks: [
        {
          id: 't1',
          title: '完成技能树重构',
          done: false,
          tags: 'frontend,urgent',
          started_on: '2026-09-10',
          completed_on: null,
          subtasks: [
            { title: '拆分节点', done: true },
            { title: '更新校验', done: true },
            { title: '编写文档', done: false },
          ],
        },
      ],
    },
    {
      name: '已完成',
      tasks: [
        {
          id: 't2',
          title: '搭建 CI 流水线',
          done: true,
          tags: '',
          started_on: '2026-09-01',
          completed_on: '2026-09-05',
          subtasks: [],
        },
      ],
    },
  ],
};

const EMPTY_BOARD = { profile: 'alice', total: 0, sections: [] };

const ETAG = 'W/"board-v1"';

function boardResponse(etag: string = ETAG): Response {
  return new Response(JSON.stringify(BOARD), {
    status: 200,
    headers: { 'Content-Type': 'application/json', ETag: etag },
  });
}

function mockKanbanFetch(body: unknown) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('/profiles/alice/kanban')) {
        return jsonResponse(200, body);
      }
      return jsonResponse(404, { code: 'not_found', message: 'not found' });
    }),
  );
}

type FetchHandler = (url: string, init?: RequestInit) => Response | Promise<Response>;

function stubFetch(handler: FetchHandler) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) =>
    handler(String(input), init),
  );
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

function renderPage() {
  return renderWithProviders(
    <Routes>
      <Route path="/p/:name/kanban" element={<KanbanPage />} />
    </Routes>,
    '/p/alice/kanban',
  );
}

function isBoardGet(input: unknown, init?: RequestInit): boolean {
  const url = String(input);
  return (init?.method ?? 'GET') === 'GET' && url.endsWith('/profiles/alice/kanban');
}

const MUTATION_RESULT = {
  ok: true,
  card: BOARD.sections[0].tasks[0],
  section: 'Queue',
  warnings: [],
  merged_external: false,
  merge_notices: [],
};

afterEach(() => {
  cleanNotifications();
  vi.unstubAllGlobals();
});

describe('KanbanPage', () => {
  it('renders columns with headers, counts and cards from the board payload', async () => {
    mockKanbanFetch(BOARD);

    renderPage();

    expect(await screen.findByText('alice · 看板')).toBeInTheDocument();
    // Section columns with per-column count badges (section names also
    // appear in the quick-add select, hence getAllByText).
    expect(screen.getAllByText('进行中').length).toBeGreaterThan(0);
    expect(screen.getAllByText('已完成').length).toBeGreaterThan(0);
    expect(screen.getAllByText('1').length).toBeGreaterThanOrEqual(3);
    // Card titles and tags.
    expect(screen.getByText('完成技能树重构')).toBeInTheDocument();
    expect(screen.getByText('frontend')).toBeInTheDocument();
    expect(screen.getByText('urgent')).toBeInTheDocument();
    expect(screen.getByText('搭建 CI 流水线')).toBeInTheDocument();
    // Dates surfaced for completed cards.
    expect(screen.getByText('完成于 2026-09-05')).toBeInTheDocument();
  });

  it('shows an empty state when the board has no sections', async () => {
    mockKanbanFetch(EMPTY_BOARD);

    renderPage();

    expect(await screen.findByText('看板为空,暂无任务。')).toBeInTheDocument();
  });

  it('renders subtask progress for cards that have subtasks', async () => {
    mockKanbanFetch(BOARD);

    renderPage();

    expect(await screen.findByText('子任务 2/3')).toBeInTheDocument();
    const progress = screen.getByRole('progressbar', { name: '子任务进度 2/3' });
    expect(progress).toHaveAttribute('aria-valuenow', String((2 / 3) * 100));
    // The card without subtasks shows no progress text.
    expect(screen.queryByText('子任务 0/0')).not.toBeInTheDocument();
  });

  it('quick-add posts the title/section with If-Match and refetches the board', async () => {
    const fetchMock = stubFetch((url, init) => {
      if (init?.method === 'POST' && url.endsWith('/kanban/cards')) {
        return jsonResponse(201, MUTATION_RESULT);
      }
      return boardResponse();
    });
    renderPage();

    const input = await screen.findByPlaceholderText('任务标题…');
    fireEvent.change(input, { target: { value: '  新的看板任务  ' } });
    fireEvent.click(screen.getByRole('button', { name: '添加' }));

    expect(await screen.findByText('已添加')).toBeInTheDocument();
    const postCall = fetchMock.mock.calls.find(
      ([input, init]) => String(input).endsWith('/kanban/cards') && init?.method === 'POST',
    );
    expect(postCall).toBeDefined();
    const init = postCall?.[1];
    // The section select defaults to Queue.
    expect(JSON.parse(String(init?.body))).toEqual({
      title: '新的看板任务',
      section: 'Queue',
      context: '',
    });
    expect((init?.headers as Record<string, string>)['If-Match']).toBe(ETAG);
    // Board invalidated → refetched after the mutation.
    await waitFor(() => {
      const gets = fetchMock.mock.calls.filter(([input, init]) =>
        isBoardGet(input, init as RequestInit | undefined),
      );
      expect(gets.length).toBeGreaterThanOrEqual(2);
    });
    expect((input as HTMLInputElement).value).toBe('');
  });

  it('move menu posts target_section with If-Match', async () => {
    const fetchMock = stubFetch((url, init) => {
      if (init?.method === 'POST' && url.endsWith('/move')) {
        return jsonResponse(200, { ...MUTATION_RESULT, section: '进行中' });
      }
      return boardResponse();
    });
    renderPage();

    fireEvent.click(await screen.findByRole('button', { name: '卡片操作 读 VLA 综述' }));
    const subTarget = await screen.findByRole('menuitem', { name: '移动到…' });
    fireEvent.mouseOver(subTarget);
    // The submenu dropdown stays display:none in jsdom (floating-ui
    // positioning), so locate the item by text rather than role.
    await waitFor(() => {
      const items = screen
        .getAllByText('进行中')
        .filter((el) => el.closest('[data-sub-menu-item], [data-menu-item]'));
      expect(items.length).toBeGreaterThan(0);
    });
    const subItemText = screen
      .getAllByText('进行中')
      .find((el) => el.closest('[data-menu-item]'));
    const subItem = subItemText?.closest('[role="menuitem"]');
    expect(subItem).not.toBeNull();
    fireEvent.click(subItem as HTMLElement);

    expect(await screen.findByText('已移动')).toBeInTheDocument();
    const moveCall = fetchMock.mock.calls.find(
      ([input, init]) => String(input).endsWith('/move') && init?.method === 'POST',
    );
    expect(moveCall).toBeDefined();
    expect(String(moveCall?.[0])).toContain(
      `/kanban/cards/${encodeURIComponent('读 VLA 综述')}/move`,
    );
    const init = moveCall?.[1];
    expect(JSON.parse(String(init?.body))).toEqual({ target_section: '进行中' });
    expect((init?.headers as Record<string, string>)['If-Match']).toBe(ETAG);
  });

  it('on 412 warns about stale data, refetches the board, and does not retry', async () => {
    const fetchMock = stubFetch((url, init) => {
      if (init?.method === 'POST' && url.endsWith('/done')) {
        return new Response(
          JSON.stringify({
            code: 'etag_mismatch',
            message: 'kanban.md changed since it was loaded',
          }),
          {
            status: 412,
            headers: { 'Content-Type': 'application/json', ETag: 'W/"board-v2"' },
          },
        );
      }
      return boardResponse();
    });
    renderPage();

    fireEvent.click(await screen.findByRole('button', { name: '卡片操作 读 VLA 综述' }));
    fireEvent.click(await screen.findByRole('menuitem', { name: '标记完成' }));

    expect(await screen.findByText('数据已被他人修改')).toBeInTheDocument();
    expect(screen.getByText(/已为你刷新/)).toBeInTheDocument();
    await waitFor(() => {
      const gets = fetchMock.mock.calls.filter(([input, init]) =>
        isBoardGet(input, init as RequestInit | undefined),
      );
      expect(gets.length).toBeGreaterThanOrEqual(2);
    });
    // The mutation itself is not retried automatically.
    const doneCalls = fetchMock.mock.calls.filter(
      ([input, init]) => String(input).endsWith('/done') && init?.method === 'POST',
    );
    expect(doneCalls.length).toBe(1);
  });

  it('on 422 kanban_card_ambiguous explains the duplicate-title conflict and does not retry', async () => {
    const fetchMock = stubFetch((url, init) => {
      if (init?.method === 'POST' && url.endsWith('/done')) {
        return jsonResponse(422, {
          code: 'kanban_card_ambiguous',
          message: 'multiple kanban cards match title 读 VLA 综述',
        });
      }
      return boardResponse();
    });
    renderPage();

    fireEvent.click(await screen.findByRole('button', { name: '卡片操作 读 VLA 综述' }));
    fireEvent.click(await screen.findByRole('menuitem', { name: '标记完成' }));

    expect(await screen.findByText('存在重名卡片')).toBeInTheDocument();
    expect(screen.getByText(/重命名重复卡片后再试/)).toBeInTheDocument();
    // No generic red error and no automatic refetch/retry: resolving the
    // ambiguity requires a data-layer rename first.
    expect(screen.queryByText('操作失败')).not.toBeInTheDocument();
    const doneCalls = fetchMock.mock.calls.filter(
      ([input, init]) => String(input).endsWith('/done') && init?.method === 'POST',
    );
    expect(doneCalls.length).toBe(1);
  });
});
