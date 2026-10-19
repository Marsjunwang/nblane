import { fireEvent, screen, waitFor } from '@testing-library/react';
import { Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { jsonResponse, renderWithProviders } from '../test/render';
import { MiniPage } from './MiniPage';

const KANBAN = {
  profile: 'alice',
  total: 3,
  sections: [
    { name: 'Doing', tasks: [{ id: 'kb_1', title: '写 VLA 复现', done: false }, { id: 'kb_2', title: '已完成但未移走', done: true }] },
    { name: 'Queue', tasks: [{ id: 'kb_3', title: '排队中的任务', done: false }] },
  ],
};

const BOARD = {
  profile: 'alice',
  north_star: '',
  today: '2026-10-19',
  habits: [
    { id: 'study', title: 'Learning', streak: 5, week: [{ date: '2026-10-19', done: false, future: false }] },
    { id: 'exercise', title: 'Exercise', streak: 4, week: [{ date: '2026-10-19', done: true, future: false }] },
  ],
};

type Call = { url: string; method: string; body: unknown };

function mockFetch(calls: Call[]) {
  return vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const method = init?.method ?? 'GET';
    calls.push({ url, method, body: init?.body ? JSON.parse(String(init.body)) : undefined });
    if (url.endsWith('/kanban') && method === 'GET') return jsonResponse(200, KANBAN);
    if (url.includes('/projects-board') && method === 'GET') return jsonResponse(200, BOARD);
    if (url.endsWith('/checkins') && method === 'POST') return jsonResponse(201, { ok: true });
    if (url.includes('/kanban/cards/') && url.endsWith('/done')) return jsonResponse(200, { ok: true, etag: 'e2' });
    return jsonResponse(404, { code: 'not_found', message: url });
  });
}

function renderMini(calls: Call[]) {
  vi.stubGlobal('fetch', mockFetch(calls));
  return renderWithProviders(
    <Routes>
      <Route path="/p/:name/mini" element={<MiniPage />} />
    </Routes>,
    '/p/alice/mini',
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('MiniPage', () => {
  it('lists open Doing tasks and today habits only', async () => {
    renderMini([]);
    expect(await screen.findByText('写 VLA 复现')).toBeInTheDocument();
    expect(screen.queryByText('已完成但未移走')).toBeNull();
    expect(screen.queryByText('排队中的任务')).toBeNull();
    expect(screen.getByRole('button', { name: '打卡：Learning' })).toBeInTheDocument();
    expect(screen.getByText('已打卡')).toBeInTheDocument();
    expect(screen.getByLabelText('连续 5 天')).toBeInTheDocument();
  });

  it('checks in a habit for today', async () => {
    const calls: Call[] = [];
    renderMini(calls);
    fireEvent.click(await screen.findByRole('button', { name: '打卡：Learning' }));
    await waitFor(() => expect(calls.some((call) => call.method === 'POST' && call.url.endsWith('/checkins'))).toBe(true));
    const post = calls.find((call) => call.method === 'POST' && call.url.endsWith('/checkins'));
    expect(post?.body).toMatchObject({ habit: 'study', date: '' });
  });

  it('marks a Doing task done', async () => {
    const calls: Call[] = [];
    renderMini(calls);
    fireEvent.click(await screen.findByRole('button', { name: '标记完成：写 VLA 复现' }));
    await waitFor(() => expect(calls.some((call) => call.url.endsWith('/kanban/cards/kb_1/done'))).toBe(true));
  });
});
