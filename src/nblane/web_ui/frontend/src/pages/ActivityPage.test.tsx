import { fireEvent, screen, waitFor } from '@testing-library/react';
import { cleanNotifications } from '@mantine/notifications';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';

import { jsonResponse, renderWithProviders } from '../test/render';
import { ActivityPage } from './ActivityPage';

const ITEM = {
  id: 'item-1',
  kind: 'candidate',
  candidate_type: 'evidence',
  source_page: 'Review',
  source_ref: 'review:2026-09-14:2026-09-20',
  target_owner: 'evidence_pool',
  status: 'pending',
  title: '新增技能: 机械臂标定',
  summary: '从评审中提炼的候选技能。',
  payload: { node: { name: '机械臂标定' } },
  preview: { diff: '+ name: 机械臂标定' },
  warnings: ['技能树缺少父节点'],
  error: '',
  changed_paths: [],
  created: '2026-09-18T10:00:00',
  updated: '2026-09-18T10:00:00',
  applied_at: '',
};

/** Pending but not Review-origin: Apply must not be offered (backend 409s). */
const NON_REVIEW_ITEM = {
  ...ITEM,
  id: 'item-2',
  kind: 'candidate',
  candidate_type: 'research_paper_deep_read_codex',
  source_page: 'AI Gateway',
  source_ref: 'airun_123',
  target_owner: 'research',
  title: 'AI 网关候选: 论文深读',
};

const LIST = {
  profile: 'alice',
  status: 'pending',
  kind: '',
  limit: 200,
  total: 1,
  items: [ITEM],
  summary: {
    status: { pending: 1, applied: 2 },
    kind: { candidate: 1 },
    target_owner: { alice: 1 },
    candidate_type: { skill: 1 },
  },
};

const ETAG = 'W/"v1"';

function detailResponse(item: unknown, etag: string): Response {
  return new Response(JSON.stringify(item), {
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
      <Route path="/p/:name/activity" element={<ActivityPage />} />
    </Routes>,
    '/p/alice/activity',
  );
}

function isDetailCall(input: unknown, init?: RequestInit): boolean {
  const url = String(input);
  const method = init?.method ?? 'GET';
  return (
    method === 'GET' && url.includes('/activity/item-1') && !url.endsWith('/apply') && !url.endsWith('/dismiss')
  );
}

async function openDrawer() {
  fireEvent.click(await screen.findByText('新增技能: 机械臂标定'));
  await screen.findByRole('button', { name: '应用' });
}

afterEach(() => {
  cleanNotifications();
  vi.unstubAllGlobals();
});

describe('ActivityPage', () => {
  it('renders the list with filter tabs and summary chips', async () => {
    stubFetch(() => jsonResponse(200, LIST));
    renderPage();

    // Wait for the query to resolve (the title renders before data).
    expect(await screen.findByText('新增技能: 机械臂标定')).toBeInTheDocument();
    expect(screen.getByText('alice · 代理活动')).toBeInTheDocument();
    // Summary chips from the summary block (queue-wide counts).
    expect(screen.getByText('待审批: 1')).toBeInTheDocument();
    expect(screen.getByText('已应用: 2')).toBeInTheDocument();
    // Status tabs: 待审批 / 已应用 / 已驳回 / 失败 / 全部.
    expect(screen.getByText('已驳回')).toBeInTheDocument();
    expect(screen.getByText('失败')).toBeInTheDocument();
    expect(screen.getByText('全部')).toBeInTheDocument();
    // Item row: kind badge, status badge.
    expect(screen.getAllByText('candidate').length).toBeGreaterThan(0);
    expect(screen.getAllByText('待审批').length).toBeGreaterThan(0);
  });

  it('opens the detail drawer with metadata, payload and warnings', async () => {
    stubFetch((url, init) => {
      if (isDetailCall(url, init)) {
        return detailResponse(ITEM, ETAG);
      }
      return jsonResponse(200, LIST);
    });
    renderPage();

    await openDrawer();

    expect(await screen.findByText('从评审中提炼的候选技能。')).toBeInTheDocument();
    expect(screen.getByText('目标')).toBeInTheDocument();
    expect(screen.getByText('技能树缺少父节点')).toBeInTheDocument();
    // Payload/preview rendered as JSON code blocks.
    expect(screen.getAllByText(/机械臂标定/).length).toBeGreaterThan(1);
    expect(screen.getByRole('button', { name: '驳回' })).toBeInTheDocument();
  });

  it('sends If-Match on apply, shows a success notification and refetches the list', async () => {
    const fetchMock = stubFetch((url, init) => {
      if (init?.method === 'POST' && url.endsWith('/apply')) {
        return jsonResponse(200, {
          ok: true,
          item: { ...ITEM, status: 'applied' },
          warnings: [],
          changed_paths: ['skill-tree.yaml'],
        });
      }
      if (isDetailCall(url, init)) {
        return detailResponse(ITEM, ETAG);
      }
      return jsonResponse(200, LIST);
    });
    renderPage();

    await openDrawer();
    fireEvent.click(screen.getByRole('button', { name: '应用' }));

    expect(await screen.findByText('应用成功')).toBeInTheDocument();
    // The mutation carried the detail ETag as If-Match.
    const applyCall = fetchMock.mock.calls.find(
      ([input, init]) => String(input).endsWith('/apply') && init?.method === 'POST',
    );
    expect(applyCall).toBeDefined();
    const headers = applyCall?.[1]?.headers as Record<string, string>;
    expect(headers['If-Match']).toBe(ETAG);
    // List invalidated → refetched after the mutation.
    await waitFor(() => {
      const listCalls = fetchMock.mock.calls.filter(
        ([input, init]) =>
          (init?.method ?? 'GET') === 'GET' && String(input).includes('status=pending'),
      );
      expect(listCalls.length).toBeGreaterThanOrEqual(2);
    });
  });

  it('on 412 warns about stale data and refetches the detail for a fresh ETag', async () => {
    const fetchMock = stubFetch((url, init) => {
      if (init?.method === 'POST' && url.endsWith('/apply')) {
        return new Response(
          JSON.stringify({
            code: 'etag_mismatch',
            message: 'agent-activity.yaml changed since this item was loaded',
            item: ITEM,
          }),
          {
            status: 412,
            headers: { 'Content-Type': 'application/json', ETag: 'W/"v2"' },
          },
        );
      }
      if (isDetailCall(url, init)) {
        return detailResponse(ITEM, ETAG);
      }
      return jsonResponse(200, LIST);
    });
    renderPage();

    await openDrawer();
    fireEvent.click(screen.getByRole('button', { name: '应用' }));

    expect(await screen.findByText('数据已被他人修改')).toBeInTheDocument();
    expect(screen.getByText(/已为你刷新/)).toBeInTheDocument();
    // The detail query refetches so the next 应用 press uses the fresh ETag.
    await waitFor(() => {
      const detailCalls = fetchMock.mock.calls.filter(([input, init]) =>
        isDetailCall(input, init as RequestInit | undefined),
      );
      expect(detailCalls.length).toBeGreaterThanOrEqual(2);
    });
    // The mutation itself is not retried automatically.
    const applyCalls = fetchMock.mock.calls.filter(
      ([input, init]) => String(input).endsWith('/apply') && init?.method === 'POST',
    );
    expect(applyCalls.length).toBe(1);
  });

  it('hides Apply for pending non-Review items and explains why (P0-2)', async () => {
    const list = {
      ...LIST,
      items: [NON_REVIEW_ITEM],
      summary: { status: { pending: 1 }, kind: { candidate: 1 } },
    };
    const fetchMock = stubFetch((url, init) => {
      const method = init?.method ?? 'GET';
      if (method === 'GET' && url.includes('/activity/item-2')) {
        return detailResponse(NON_REVIEW_ITEM, ETAG);
      }
      return jsonResponse(200, list);
    });
    renderPage();

    fireEvent.click(await screen.findByText('AI 网关候选: 论文深读'));
    // 驳回 stays available; 应用 is not offered for non-Review origins.
    expect(await screen.findByRole('button', { name: '驳回' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '应用' })).not.toBeInTheDocument();
    expect(screen.getByText(/只能应用 pending 的 Review 候选/)).toBeInTheDocument();
    // No apply request can be issued through the UI.
    expect(
      fetchMock.mock.calls.filter(
        ([input, init]) => String(input).endsWith('/apply') && init?.method === 'POST',
      ),
    ).toHaveLength(0);
  });

  it('dismisses via the modal, sending If-Match and the note', async () => {
    const fetchMock = stubFetch((url, init) => {
      if (init?.method === 'POST' && url.endsWith('/dismiss')) {
        return jsonResponse(200, { ok: true, item: { ...ITEM, status: 'dismissed' } });
      }
      if (isDetailCall(url, init)) {
        return detailResponse(ITEM, ETAG);
      }
      return jsonResponse(200, LIST);
    });
    renderPage();

    await openDrawer();
    fireEvent.click(screen.getByRole('button', { name: '驳回' }));

    const noteInput = await screen.findByPlaceholderText('记录驳回原因…');
    fireEvent.change(noteInput, { target: { value: '信息过时' } });
    fireEvent.click(screen.getByRole('button', { name: '确认驳回' }));

    // Tab label plus the success notification title both read 已驳回.
    await waitFor(() =>
      expect(screen.getAllByText('已驳回').length).toBeGreaterThanOrEqual(2),
    );
    const dismissCall = fetchMock.mock.calls.find(
      ([input, init]) => String(input).endsWith('/dismiss') && init?.method === 'POST',
    );
    expect(dismissCall).toBeDefined();
    const init = dismissCall?.[1];
    expect((init?.headers as Record<string, string>)['If-Match']).toBe(ETAG);
    expect(JSON.parse(String(init?.body))).toEqual({ note: '信息过时' });
  });
});
