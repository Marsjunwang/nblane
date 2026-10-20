import { notifications } from '@mantine/notifications';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { jsonResponse, renderWithProviders } from '../test/render';
import { MiniPage } from './MiniPage';

const TODAY = '2026-10-19';

function kanban(todos: Array<{ text: string; done: boolean }>) {
  return {
    profile: 'alice',
    total: 4,
    sections: [
      {
        name: 'Doing',
        tasks: [
          { id: 'kb_1', title: '写 VLA 复现', done: false, todos, planned_end: '2026-10-25' },
          { id: 'kb_2', title: '已完成但未移走', done: true },
          { id: 'kb_4', title: '逾期的任务', done: false, planned_end: '2026-10-10' },
        ],
      },
      {
        name: 'Queue',
        tasks: [
          { id: 'kb_3', title: '排队中的任务', done: false },
          { id: 'kb_5', title: 'Queue 二', done: false },
          { id: 'kb_6', title: 'Queue 三', done: false },
          { id: 'kb_7', title: 'Queue 四', done: false },
        ],
      },
    ],
  };
}

const BOARD = {
  profile: 'alice',
  north_star: '',
  today: TODAY,
  habits: [
    { id: 'study', title: 'Learning', streak: 5, week: [{ date: TODAY, done: false, future: false }] },
    { id: 'exercise', title: 'Exercise', streak: 4, week: [{ date: TODAY, done: true, future: false }] },
    { id: 'run', title: 'Running', streak: 0, week: [{ date: TODAY, done: false, future: false }] },
  ],
};

const plan = (id: string, title: string, habit: string, extra: Record<string, unknown> = {}) => ({
  id, title, habit_id: habit, status: 'active', start_date: '2026-10-01', end_date: '2026-10-31',
  current_week: 3, current_day: 19, days_done: 10, days_total: 31, completion_rate: 0.3,
  weekly_tasks: [{}, {}, {}, {}], ...extra,
});

const PLANS = {
  plans: [
    plan('p_study', '28天学习', 'study', { daily_tasks: [{ day: 19, tasks: ['读一篇论文'] }], today_tasks: ['读一篇论文'] }),
    plan('p_run_a', '5K 训练', 'run'),
    plan('p_run_b', '半马备赛', 'run'),
  ],
};

type Call = { url: string; method: string; body: unknown; ifMatch: string };

interface Server {
  todos: Array<{ text: string; done: boolean }>;
  /** Make the next PATCH fail with 412 after swapping in this list. */
  conflictWith?: Array<{ text: string; done: boolean }>;
  failAdd?: boolean;
  exceptions?: Array<Record<string, unknown>>;
}

function mockFetch(calls: Call[], server: Server) {
  let version = 1;
  return vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const method = init?.method ?? 'GET';
    const headers = new Headers(init?.headers);
    const body = init?.body ? JSON.parse(String(init.body)) : undefined;
    calls.push({ url, method, body, ifMatch: headers.get('If-Match') ?? '' });
    const etag = `"v${version}"`;
    if (url.endsWith('/kanban') && method === 'GET') {
      return new Response(JSON.stringify(kanban(server.todos)), { status: 200, headers: { 'Content-Type': 'application/json', ETag: etag } });
    }
    if (url.includes('/projects-board') && method === 'GET') return jsonResponse(200, BOARD);
    if (url.includes('/habit-plans') && method === 'GET') return jsonResponse(200, PLANS);
    if (url.includes('/ai-exceptions') && method === 'GET') {
      const items = server.exceptions ?? [];
      return jsonResponse(200, { profile: 'alice', total: items.length, items });
    }
    if (url.endsWith('/checkins') && method === 'POST') return jsonResponse(201, { ok: true });
    if (url.includes('/kanban/cards/') && url.endsWith('/done')) return jsonResponse(200, { ok: true });
    if (url.includes('/kanban/cards/') && url.endsWith('/move')) return jsonResponse(200, { ok: true });
    if (url.endsWith('/kanban/cards') && method === 'POST') {
      if (server.failAdd) return jsonResponse(500, { code: 'boom', message: '服务暂时不可用' });
      return jsonResponse(201, { ok: true });
    }
    if (url.endsWith('/kanban/cards/kb_1') && method === 'PATCH') {
      if (server.conflictWith) {
        server.todos = server.conflictWith;
        server.conflictWith = undefined;
        version += 1;
        return new Response(JSON.stringify({ code: 'etag_mismatch', message: 'changed' }), {
          status: 412,
          headers: { 'Content-Type': 'application/json', ETag: `"v${version}"` },
        });
      }
      server.todos = body.todos;
      version += 1;
      return new Response(JSON.stringify({ ok: true }), { status: 200, headers: { 'Content-Type': 'application/json', ETag: `"v${version}"` } });
    }
    return jsonResponse(404, { code: 'not_found', message: url });
  });
}

function renderMini(calls: Call[], server: Server) {
  vi.stubGlobal('fetch', mockFetch(calls, server));
  return renderWithProviders(
    <Routes>
      <Route path="/p/:name/mini" element={<MiniPage />} />
    </Routes>,
    '/p/alice/mini',
  );
}

const patches = (calls: Call[]) => calls.filter((call) => call.method === 'PATCH');

beforeEach(() => {
  window.localStorage.clear();
  // The notifications store is module-level and shows at most 5 at once;
  // earlier tests' toasts would otherwise queue this test's ones out of view.
  notifications.clean();
  notifications.cleanQueue();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('MiniPage', () => {
  it('lists open Doing tasks (overdue first) and today habits only', async () => {
    renderMini([], { todos: [] });
    expect(await screen.findByText('写 VLA 复现')).toBeInTheDocument();
    expect(screen.queryByText('已完成但未移走')).toBeNull();
    expect(screen.queryByText('排队中的任务')).toBeNull();
    const titles = screen.getAllByRole('button', { name: /^标记完成：/ }).map((el) => el.getAttribute('aria-label'));
    expect(titles).toEqual(['标记完成：逾期的任务', '标记完成：写 VLA 复现']);
    expect(screen.getByText('已逾期')).toBeInTheDocument();
    expect(screen.getByText('已打卡')).toBeInTheDocument();
    expect(screen.getByLabelText('连续 5 天')).toBeInTheDocument();
  });

  it('expands a task and ticks a todo, keeping the expansion across reloads', async () => {
    const calls: Call[] = [];
    const server: Server = { todos: [{ text: '跑基线', done: false }, { text: '写记录', done: false }] };
    renderMini(calls, server);
    expect(await screen.findByText('清单 0/2')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '展开清单：写 VLA 复现' }));
    fireEvent.click(screen.getByRole('checkbox', { name: '跑基线' }));
    await waitFor(() => expect(patches(calls)).toHaveLength(1));
    expect(patches(calls)[0].body).toEqual({ todos: [{ text: '跑基线', done: true }, { text: '写记录', done: false }] });
    expect(patches(calls)[0].ifMatch).toBe('"v1"');
    expect(await screen.findByText('清单 1/2')).toBeInTheDocument();
    expect(JSON.parse(window.localStorage.getItem('nblane-mini-open:alice') ?? '[]')).toEqual(['kb_1']);
  });

  it('on a 412 re-applies the tick to the fresh list without dropping new items', async () => {
    const calls: Call[] = [];
    const server: Server = {
      todos: [{ text: '跑基线', done: false }],
      conflictWith: [{ text: '项目页新加', done: false }, { text: '跑基线', done: false }],
    };
    renderMini(calls, server);
    fireEvent.click(await screen.findByRole('button', { name: '展开清单：写 VLA 复现' }));
    fireEvent.click(screen.getByRole('checkbox', { name: '跑基线' }));
    await waitFor(() => expect(patches(calls)).toHaveLength(2));
    expect(patches(calls)[1].body).toEqual({ todos: [{ text: '项目页新加', done: false }, { text: '跑基线', done: true }] });
    expect(patches(calls)[1].ifMatch).toBe('"v2"');
    expect(await screen.findByRole('checkbox', { name: '项目页新加' })).toBeInTheDocument();
  });

  it('on a 412 where the item is gone, refreshes instead of writing a stale list', async () => {
    const calls: Call[] = [];
    const server: Server = { todos: [{ text: '跑基线', done: false }], conflictWith: [{ text: '别的', done: false }] };
    renderMini(calls, server);
    fireEvent.click(await screen.findByRole('button', { name: '展开清单：写 VLA 复现' }));
    fireEvent.click(screen.getByRole('checkbox', { name: '跑基线' }));
    expect(await screen.findByText('清单在别处改过了，已刷新为最新内容。')).toBeInTheDocument();
    expect(patches(calls)).toHaveLength(1);
    expect(await screen.findByRole('checkbox', { name: '别的' })).toBeInTheDocument();
  });

  it('checks in against the single in-window plan and shows today tasks', async () => {
    const calls: Call[] = [];
    renderMini(calls, { todos: [] });
    expect(await screen.findByText('今日：读一篇论文')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '打卡：Learning' }));
    await waitFor(() => expect(calls.some((call) => call.method === 'POST' && call.url.endsWith('/checkins'))).toBe(true));
    const post = calls.find((call) => call.method === 'POST' && call.url.endsWith('/checkins'));
    expect(post?.body).toMatchObject({ habit: 'study', plan_id: 'p_study' });
  });

  it('asks which plan to count when several are in window', async () => {
    const calls: Call[] = [];
    renderMini(calls, { todos: [] });
    fireEvent.click(await screen.findByRole('button', { name: '打卡：Running' }));
    fireEvent.click(await screen.findByRole('menuitem', { name: '半马备赛' }));
    await waitFor(() => expect(calls.some((call) => call.method === 'POST' && call.url.endsWith('/checkins'))).toBe(true));
    const post = calls.find((call) => call.method === 'POST' && call.url.endsWith('/checkins'));
    expect(post?.body).toMatchObject({ habit: 'run', plan_id: 'p_run_b' });
  });

  it('keeps Queue collapsed, then shows the first three with 开始', async () => {
    const calls: Call[] = [];
    renderMini(calls, { todos: [] });
    const toggle = await screen.findByRole('button', { name: /接下来 · Queue 4/ });
    expect(screen.queryByText('排队中的任务')).toBeNull();
    fireEvent.click(toggle);
    expect(screen.getByText('排队中的任务')).toBeInTheDocument();
    expect(screen.queryByText('Queue 四')).toBeNull();
    expect(screen.getByText('还有 1 条，在项目页查看')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '开始：排队中的任务' }));
    await waitFor(() => expect(calls.some((call) => call.url.endsWith('/kanban/cards/kb_3/move'))).toBe(true));
    const move = calls.find((call) => call.url.endsWith('/kanban/cards/kb_3/move'));
    expect(move?.body).toEqual({ target_section: 'Doing' });
    expect(JSON.parse(window.localStorage.getItem('nblane-mini-queue:alice') ?? 'false')).toBe(true);
  });

  it('quick-adds a task to Queue on Enter and clears the input', async () => {
    const calls: Call[] = [];
    renderMini(calls, { todos: [] });
    const input = await screen.findByRole('textbox', { name: '添加任务到 Queue' });
    fireEvent.change(input, { target: { value: '  回复评审意见  ' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    await waitFor(() => expect(calls.some((call) => call.method === 'POST' && call.url.endsWith('/kanban/cards'))).toBe(true));
    const post = calls.find((call) => call.method === 'POST' && call.url.endsWith('/kanban/cards'));
    expect(post?.body).toEqual({ title: '回复评审意见', section: 'Queue', context: '' });
    await waitFor(() => expect(input).toHaveValue(''));
  });

  it('ignores Enter while an IME is composing and keeps the text on failure', async () => {
    const calls: Call[] = [];
    renderMini(calls, { todos: [], failAdd: true });
    const input = await screen.findByRole('textbox', { name: '添加任务到 Queue' });
    fireEvent.change(input, { target: { value: '拼音输入中' } });
    fireEvent.keyDown(input, { key: 'Enter', isComposing: true });
    expect(calls.some((call) => call.method === 'POST' && call.url.endsWith('/kanban/cards'))).toBe(false);
    fireEvent.keyDown(input, { key: 'Enter' });
    expect(await screen.findByText('服务暂时不可用')).toBeInTheDocument();
    expect(input).toHaveValue('拼音输入中');
  });

  it('shows no AI exception badge when nothing failed', async () => {
    renderMini([], { todos: [] });
    expect(await screen.findByText('写 VLA 复现')).toBeInTheDocument();
    await waitFor(() => expect(screen.queryByRole('button', { name: /AI 异常/ })).toBeNull());
  });

  it('shows the AI exception count and opens the list in the 小窗, linking to the main window', async () => {
    const exceptions = [
      {
        id: 'run:r1', source: 'AI 调用', title: 'content.meta', message: 'AI 响应超时，请重试。',
        action: 'content.meta', created: '2026-10-19T08:00:00Z', source_ref: 'r1', retryable: true,
        href: '/p/alice/content', severity: 'error',
      },
    ];
    renderMini([], { todos: [], exceptions });
    fireEvent.click(await screen.findByRole('button', { name: 'AI 异常 1 条' }));
    expect(await screen.findByText('AI 响应超时，请重试。')).toBeInTheDocument();
    const link = screen.getByRole('link', { name: /打开来源/ });
    expect(link).toHaveAttribute('href', '/p/alice/content');
    expect(link).toHaveAttribute('target', 'nblane-main');
  });

  it('hides a task in the mini window only, and can show it again', async () => {
    const calls: Call[] = [];
    renderMini(calls, { todos: [] });
    fireEvent.click(await screen.findByRole('button', { name: '隐藏：写 VLA 复现' }));
    expect(screen.queryByText('写 VLA 复现')).toBeNull();
    expect(JSON.parse(window.localStorage.getItem('nblane-mini-hidden:alice') ?? '[]')).toEqual(['kb_1']);
    // Hiding is local: nothing is written to the kanban.
    expect(calls.some((call) => call.method !== 'GET')).toBe(false);

    fireEvent.click(screen.getByRole('button', { name: /已隐藏 1 条/ }));
    fireEvent.click(await screen.findByRole('button', { name: '取消隐藏：写 VLA 复现' }));
    // Nothing hidden any more: the task is back and the toggle disappears.
    expect(screen.getByText('写 VLA 复现')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /已隐藏/ })).toBeNull();
    expect(JSON.parse(window.localStorage.getItem('nblane-mini-hidden:alice') ?? '[]')).toEqual([]);
  });

  it('collapses the habits section and remembers it', async () => {
    renderMini([], { todos: [] });
    expect(await screen.findByRole('button', { name: '打卡：Learning' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /日课 · 3/ }));
    expect(screen.queryByRole('button', { name: '打卡：Learning' })).toBeNull();
    expect(JSON.parse(window.localStorage.getItem('nblane-mini-habits:alice') ?? 'true')).toBe(false);
  });

  it('marks a Doing task done', async () => {
    const calls: Call[] = [];
    renderMini(calls, { todos: [] });
    fireEvent.click(await screen.findByRole('button', { name: '标记完成：写 VLA 复现' }));
    await waitFor(() => expect(calls.some((call) => call.url.endsWith('/kanban/cards/kb_1/done'))).toBe(true));
  });
});
