import { fireEvent, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';

import { jsonResponse, renderWithProviders } from '../test/render';
import { EvidenceReviewPage } from './EvidenceReviewPage';

const ETAG = 'W/"pool-sha"';

const LIST = {
  profile: 'alice',
  status: 'needs_review',
  q: '',
  limit: 500,
  total: 2,
  summary: {
    needs_review_count: 2,
    unlinked_count: 1,
    total_entries: 3,
    deprecated_count: 1,
  },
  items: [
    {
      id: 'ev_alpha',
      title: 'Alpha 项目',
      evidence_type: 'project',
      date: '2026-09-01',
      url: '',
      review_status: 'needs_review',
      strength: 'strong',
      confidence: 'medium',
      public_readiness: 'private',
      deprecated: false,
      usage_count: 1,
      skill_refs: ['robotics'],
      review_reason: 'needs_review',
    },
    {
      id: 'ev_delta',
      title: 'Delta 课程',
      evidence_type: 'course',
      date: '',
      url: '',
      review_status: 'needs_review',
      strength: 'unrated',
      confidence: '',
      public_readiness: 'private',
      deprecated: false,
      usage_count: 0,
      skill_refs: [],
      review_reason: 'missing_strength, needs_review',
    },
  ],
};

function listResponse(body: unknown = LIST): Response {
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
      <Route path="/p/:name/evidence-review" element={<EvidenceReviewPage />} />
    </Routes>,
    '/p/alice/evidence-review',
  );
}

function mockListOnly() {
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.includes('/profiles/alice/evidence-review')) {
      return listResponse();
    }
    return jsonResponse(404, { code: 'not_found', message: 'not found' });
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

describe('EvidenceReviewPage', () => {
  it('renders the queue with summary counters and review reasons', async () => {
    mockListOnly();
    renderPage();

    expect(await screen.findByTestId('review-row-ev_alpha')).toBeInTheDocument();
    expect(screen.getByText('alice · 证据评审')).toBeInTheDocument();
    const summary = screen.getByTestId('review-summary');
    expect(summary).toHaveTextContent('待审核 2');
    expect(summary).toHaveTextContent('未关联 1');
    expect(summary).toHaveTextContent('活跃条目 3');

    expect(screen.getByTestId('review-row-ev_alpha')).toHaveTextContent('Alpha 项目');
    expect(screen.getByTestId('review-row-ev_delta')).toHaveTextContent(
      'missing_strength, needs_review',
    );
    expect(screen.getByTestId('selection-count')).toHaveTextContent('已选 0 条');
  });

  it('accepts the selected rows via the bulk endpoint with If-Match', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes('/evidence-review/bulk')) {
        expect(init?.method).toBe('POST');
        expect((init?.headers as Record<string, string>)['If-Match']).toBe(ETAG);
        expect(JSON.parse(String(init?.body))).toEqual({
          ids: ['ev_alpha', 'ev_delta'],
          field: 'review_status',
          value: 'reviewed',
        });
        return listResponse({ ok: true, changed: 2, missing: [], warnings: [] });
      }
      if (url.includes('/profiles/alice/evidence-review')) {
        return listResponse();
      }
      return jsonResponse(404, { code: 'not_found', message: 'not found' });
    });
    vi.stubGlobal('fetch', fetchMock);

    renderPage();
    await screen.findByTestId('review-row-ev_alpha');
    fireEvent.click(screen.getByRole('button', { name: '全选' }));
    expect(screen.getByTestId('selection-count')).toHaveTextContent('已选 2 条');
    fireEvent.click(screen.getByRole('button', { name: /接受 \(2\)/ }));

    expect(await screen.findByTestId('mutation-success')).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByTestId('selection-count')).toHaveTextContent('已选 0 条'),
    );
  });

  it('tags strength through the bulk menu', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes('/evidence-review/bulk')) {
        expect(JSON.parse(String(init?.body))).toEqual({
          ids: ['ev_delta'],
          field: 'strength',
          value: 'weak',
        });
        return listResponse({ ok: true, changed: 1, missing: [], warnings: [] });
      }
      if (url.includes('/profiles/alice/evidence-review')) {
        return listResponse();
      }
      return jsonResponse(404, { code: 'not_found', message: 'not found' });
    });
    vi.stubGlobal('fetch', fetchMock);

    renderPage();
    await screen.findByTestId('review-row-ev_delta');
    fireEvent.click(screen.getByLabelText('选择 Delta 课程'));
    expect(screen.getByTestId('selection-count')).toHaveTextContent('已选 1 条');

    fireEvent.click(screen.getByRole('button', { name: /打标/ }));
    // Menu.Sub opens on hover; its dropdown renders display:none in jsdom,
    // so locate the nested item by menuitem role with hidden: true.
    fireEvent.mouseEnter(await screen.findByRole('menuitem', { name: '强度' }));
    fireEvent.click(await screen.findByRole('menuitem', { name: '弱', hidden: true }));

    expect(await screen.findByTestId('mutation-success')).toBeInTheDocument();
  });

  it('rejects the selected rows via the deprecate endpoint', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes('/evidence-review/deprecate')) {
        expect((init?.headers as Record<string, string>)['If-Match']).toBe(ETAG);
        expect(JSON.parse(String(init?.body))).toEqual({
          ids: ['ev_alpha'],
          deprecated: true,
        });
        return listResponse({ ok: true, changed: 1, missing: [], warnings: [] });
      }
      if (url.includes('/profiles/alice/evidence-review')) {
        return listResponse();
      }
      return jsonResponse(404, { code: 'not_found', message: 'not found' });
    });
    vi.stubGlobal('fetch', fetchMock);

    renderPage();
    await screen.findByTestId('review-row-ev_alpha');
    fireEvent.click(screen.getByLabelText('选择 Alpha 项目'));
    fireEvent.click(screen.getByRole('button', { name: /拒绝 \(1\)/ }));

    expect(await screen.findByTestId('mutation-success')).toBeInTheDocument();
  });

  it('flags a stale ETag (412) as a conflict with a refresh button that refetches', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('/evidence-review/bulk')) {
        return jsonResponse(412, {
          code: 'etag_mismatch',
          message: 'evidence-pool.yaml changed since it was loaded',
        });
      }
      if (url.includes('/profiles/alice/evidence-review')) {
        return listResponse();
      }
      return jsonResponse(404, { code: 'not_found', message: 'not found' });
    });
    vi.stubGlobal('fetch', fetchMock);

    renderPage();
    await screen.findByTestId('review-row-ev_alpha');
    fireEvent.click(screen.getByRole('button', { name: '全选' }));
    fireEvent.click(screen.getByRole('button', { name: /接受 \(2\)/ }));

    // 412 is recognized as a conflict: yellow unified copy, not the raw red
    // error message.
    const conflict = await screen.findByTestId('conflict-alert');
    expect(conflict).toHaveTextContent('数据已被他人修改');
    expect(conflict).toHaveTextContent('请刷新后重试');
    expect(screen.queryByText(/evidence-pool.yaml changed/)).not.toBeInTheDocument();

    const listGets = () =>
      fetchMock.mock.calls.filter(([input]) =>
        String(input).includes('/profiles/alice/evidence-review?'),
      ).length;
    const before = listGets();
    fireEvent.click(screen.getByRole('button', { name: '刷新' }));
    await waitFor(() => expect(listGets()).toBeGreaterThan(before));
  });

  it('shows an error alert when the queue fails to load', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => jsonResponse(403, { code: 'profile_forbidden', message: 'denied' })),
    );
    renderPage();
    expect(await screen.findByText('加载失败')).toBeInTheDocument();
  });

  it('omits the If-Match header when the list response carries no ETag', async () => {
    let bulkInit: RequestInit | undefined;
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes('/evidence-review/bulk')) {
        bulkInit = init;
        return jsonResponse(200, { ok: true, changed: 2, missing: [], warnings: [] });
      }
      if (url.includes('/profiles/alice/evidence-review')) {
        // No ETag header: an empty If-Match would 412 unconditionally, so the
        // mutation must send no precondition header at all.
        return jsonResponse(200, LIST);
      }
      return jsonResponse(404, { code: 'not_found', message: 'not found' });
    });
    vi.stubGlobal('fetch', fetchMock);

    renderPage();
    await screen.findByTestId('review-row-ev_alpha');
    fireEvent.click(screen.getByRole('button', { name: '全选' }));
    fireEvent.click(screen.getByRole('button', { name: /接受 \(2\)/ }));

    await waitFor(() => expect(bulkInit).toBeDefined());
    expect(bulkInit?.headers as Record<string, string>).not.toHaveProperty('If-Match');
  });

  it('clears the success banner when the filters change', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('/evidence-review/bulk')) {
        return jsonResponse(200, { ok: true, changed: 2, missing: [], warnings: [] });
      }
      if (url.includes('/profiles/alice/evidence-review')) {
        return listResponse();
      }
      return jsonResponse(404, { code: 'not_found', message: 'not found' });
    });
    vi.stubGlobal('fetch', fetchMock);

    renderPage();
    await screen.findByTestId('review-row-ev_alpha');
    fireEvent.click(screen.getByRole('button', { name: '全选' }));
    fireEvent.click(screen.getByRole('button', { name: /接受 \(2\)/ }));
    expect(await screen.findByTestId('mutation-success')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('搜索证据'), { target: { value: 'alpha' } });
    expect(screen.queryByTestId('mutation-success')).not.toBeInTheDocument();
  });
});
