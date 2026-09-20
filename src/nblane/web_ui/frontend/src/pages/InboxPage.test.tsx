import { fireEvent, screen, waitFor } from '@testing-library/react';
import { cleanNotifications } from '@mantine/notifications';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';

import { jsonResponse, renderWithProviders } from '../test/render';
import { InboxPage } from './InboxPage';

const OPENCLAW_ITEM = {
  id: 'item-1',
  title: '微信: 看看 VLA 综述',
  type: 'note',
  source: 'wechat',
  created_at: '2026-09-19',
  captured_by: 'openclaw',
  raw_text: '群里转的文章链接',
  tags: ['vla'],
  visibility: 'private',
  status: 'inbox',
  metadata: {},
  history: [
    {
      at: '2026-09-19',
      action: 'added',
      from_status: '',
      to_status: 'inbox',
      note: '',
      metadata: {},
    },
  ],
};

const WEB_ITEM = {
  ...OPENCLAW_ITEM,
  id: 'item-2',
  title: '网页随手记的一条',
  source: 'web',
  captured_by: 'human-web',
  tags: [],
  history: [],
};

const LIST = {
  profile: 'alice',
  statuses: ['inbox', 'captured', 'clarified'],
  total: 2,
  items: [OPENCLAW_ITEM, WEB_ITEM],
};

const ETAG = 'W/"v1"';

function listResponse(etag: string = ETAG): Response {
  return new Response(JSON.stringify(LIST), {
    status: 200,
    headers: { 'Content-Type': 'application/json', ETag: etag },
  });
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
      <Route path="/p/:name/inbox" element={<InboxPage />} />
    </Routes>,
    '/p/alice/inbox',
  );
}

function isListCall(input: unknown, init?: RequestInit): boolean {
  const url = String(input);
  return (init?.method ?? 'GET') === 'GET' && url.includes('/inbox?');
}

async function openModal(title: string = '微信: 看看 VLA 综述') {
  fireEvent.click(await screen.findByText(title));
  await screen.findByRole('button', { name: '处置' });
}

afterEach(() => {
  cleanNotifications();
  vi.unstubAllGlobals();
});

describe('InboxPage', () => {
  it('renders the list with distinct captured_by badges and status', async () => {
    stubFetch(() => listResponse());
    renderPage();

    expect(await screen.findByText('微信: 看看 VLA 综述')).toBeInTheDocument();
    expect(screen.getByText('网页随手记的一条')).toBeInTheDocument();
    expect(screen.getByText('alice · 收件箱')).toBeInTheDocument();
    // openclaw vs human-web badges both render, visually distinct by color.
    expect(screen.getByText('openclaw')).toBeInTheDocument();
    expect(screen.getByText('human-web')).toBeInTheDocument();
    // Tag chip and status badges.
    expect(screen.getAllByText('vla').length).toBeGreaterThan(0);
    expect(screen.getAllByText('待处置').length).toBeGreaterThan(0);
  });

  it('capture posts the title/tags with If-Match and invalidates the list', async () => {
    const fetchMock = stubFetch((url, init) => {
      if (init?.method === 'POST' && url.endsWith('/inbox')) {
        return jsonResponse(201, { ok: true, item: OPENCLAW_ITEM, result: {} });
      }
      return listResponse();
    });
    renderPage();

    const input = await screen.findByPlaceholderText('微信随手记: 一句话就行…');
    fireEvent.change(input, { target: { value: '  新的随手记  ' } });
    fireEvent.change(screen.getByPlaceholderText('逗号分隔'), {
      target: { value: 'vla, reading' },
    });
    fireEvent.click(screen.getByRole('button', { name: '记录' }));

    expect(await screen.findByText('已记录')).toBeInTheDocument();
    const postCall = fetchMock.mock.calls.find(
      ([input, init]) => String(input).endsWith('/inbox') && init?.method === 'POST',
    );
    expect(postCall).toBeDefined();
    const init = postCall?.[1];
    expect(JSON.parse(String(init?.body))).toEqual({
      title: '新的随手记',
      raw_text: '',
      source: 'web',
      tags: ['vla', 'reading'],
    });
    expect((init?.headers as Record<string, string>)['If-Match']).toBe(ETAG);
    // List invalidated → refetched after the mutation.
    await waitFor(() => {
      const listCalls = fetchMock.mock.calls.filter(([input, init]) =>
        isListCall(input, init as RequestInit | undefined),
      );
      expect(listCalls.length).toBeGreaterThanOrEqual(2);
    });
    // Inputs cleared after a successful capture.
    expect((input as HTMLInputElement).value).toBe('');
  });

  it('clarify menu sends the chosen action with If-Match', async () => {
    const fetchMock = stubFetch((url, init) => {
      if (init?.method === 'POST' && url.endsWith('/clarify')) {
        return jsonResponse(200, {
          ok: true,
          item: { ...OPENCLAW_ITEM, status: 'clarified' },
          result: { action: 'to_kanban_queue', item_id: 'item-1', target_id: 'kb_abc' },
        });
      }
      return listResponse();
    });
    renderPage();

    await openModal();
    fireEvent.click(screen.getByRole('button', { name: '处置' }));
    fireEvent.click(await screen.findByRole('menuitem', { name: '转入看板' }));

    expect(await screen.findByText('已处置')).toBeInTheDocument();
    const clarifyCall = fetchMock.mock.calls.find(
      ([input, init]) => String(input).endsWith('/clarify') && init?.method === 'POST',
    );
    expect(clarifyCall).toBeDefined();
    expect(String(clarifyCall?.[0])).toContain('/inbox/item-1/clarify');
    const init = clarifyCall?.[1];
    expect(JSON.parse(String(init?.body))).toEqual({
      action: 'to_kanban_queue',
      note: '',
    });
    expect((init?.headers as Record<string, string>)['If-Match']).toBe(ETAG);
  });

  it('quick archive button posts to /archive', async () => {
    const fetchMock = stubFetch((url, init) => {
      if (init?.method === 'POST' && url.endsWith('/archive')) {
        return jsonResponse(200, {
          ok: true,
          item: { ...OPENCLAW_ITEM, status: 'archived' },
          result: {},
        });
      }
      return listResponse();
    });
    renderPage();

    await openModal();
    fireEvent.click(screen.getByRole('button', { name: '归档' }));

    expect(await screen.findByText('已归档')).toBeInTheDocument();
    const archiveCall = fetchMock.mock.calls.find(
      ([input, init]) => String(input).endsWith('/archive') && init?.method === 'POST',
    );
    expect(archiveCall).toBeDefined();
    expect((archiveCall?.[1]?.headers as Record<string, string>)['If-Match']).toBe(ETAG);
  });

  it('on 412 warns about stale data, refetches the list, and does not retry', async () => {
    const fetchMock = stubFetch((url, init) => {
      if (init?.method === 'POST' && url.endsWith('/archive')) {
        return new Response(
          JSON.stringify({
            code: 'etag_mismatch',
            message: 'inbox.yaml changed since this item was loaded',
            item: OPENCLAW_ITEM,
          }),
          {
            status: 412,
            headers: { 'Content-Type': 'application/json', ETag: 'W/"v2"' },
          },
        );
      }
      return listResponse();
    });
    renderPage();

    await openModal();
    fireEvent.click(screen.getByRole('button', { name: '归档' }));

    expect(await screen.findByText('数据已被他人修改')).toBeInTheDocument();
    expect(screen.getByText(/已为你刷新/)).toBeInTheDocument();
    await waitFor(() => {
      const listCalls = fetchMock.mock.calls.filter(([input, init]) =>
        isListCall(input, init as RequestInit | undefined),
      );
      expect(listCalls.length).toBeGreaterThanOrEqual(2);
    });
    // The mutation itself is not retried automatically.
    const archiveCalls = fetchMock.mock.calls.filter(
      ([input, init]) => String(input).endsWith('/archive') && init?.method === 'POST',
    );
    expect(archiveCalls.length).toBe(1);
  });

  it('closes the modal when the selected item disappears after a filter switch', async () => {
    stubFetch((url) => {
      if (url.includes('status=archived')) {
        return new Response(
          JSON.stringify({ profile: 'alice', statuses: ['archived'], total: 0, items: [] }),
          { status: 200, headers: { 'Content-Type': 'application/json', ETag: ETAG } },
        );
      }
      return listResponse();
    });
    renderPage();

    // Open the detail modal for the openclaw item.
    fireEvent.click(await screen.findByText('微信: 看看 VLA 综述'));
    expect(await screen.findByRole('button', { name: '处置' })).toBeInTheDocument();

    // Switching the status filter drops the item from the loaded list; the
    // modal must close itself instead of staying open as an empty shell.
    fireEvent.click(screen.getByRole('radio', { name: '已归档' }));
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
    expect(screen.getByText('当前筛选下没有收件箱条目。')).toBeInTheDocument();
  });
});
