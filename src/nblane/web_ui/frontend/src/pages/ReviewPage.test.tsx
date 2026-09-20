import { fireEvent, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';

import { jsonResponse, renderWithProviders } from '../test/render';
import { ReviewPage } from './ReviewPage';

const ETAG = 'W/"review-sha"';

const REVIEW = {
  profile: 'alice',
  week_start: '2026-09-14',
  week_end: '2026-09-20',
  done_task_ids: ['done-fresh', 'done-public'],
  activity_summary: {},
  learning_summary: {},
  inbox_summary: {},
  evidence_candidates: [
    {
      source: 'kanban_done',
      task_id: 'done-fresh',
      resource_id: '',
      title: 'Fresh task',
      summary: 'shipped the thing',
      notes: [],
      visibility: '',
      draft: true,
    },
  ],
  next_queue_candidates: [
    {
      source: 'learning',
      task_id: '',
      resource_id: 'res-1',
      title: 'Reproduce the benchmark',
      summary: '',
      notes: [],
      visibility: '',
      draft: true,
    },
  ],
  method_candidates: [
    {
      source: 'kanban_done',
      task_id: 'done-fresh',
      resource_id: '',
      title: 'Fresh task',
      summary: '',
      notes: ['a detail line'],
      visibility: '',
      draft: true,
    },
  ],
  public_candidates: [],
  summary: {
    done_tasks: 2,
    evidence_candidates: 1,
    next_action_candidates: 1,
    public_draft_candidates: 0,
  },
};

function reviewResponse(body: unknown = REVIEW): Response {
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
      <Route path="/p/:name/review" element={<ReviewPage />} />
    </Routes>,
    '/p/alice/review',
  );
}

function mockReviewOnly() {
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.includes('/profiles/alice/review')) {
      return reviewResponse();
    }
    return jsonResponse(404, { code: 'not_found', message: 'not found' });
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

describe('ReviewPage', () => {
  it('renders the summary counters and evidence candidates', async () => {
    mockReviewOnly();
    renderPage();

    expect(await screen.findByTestId('review-candidate-evidence-0')).toBeInTheDocument();
    expect(screen.getByText('alice · 周回顾')).toBeInTheDocument();
    const summary = screen.getByTestId('review-summary');
    expect(summary).toHaveTextContent('已完成任务 2');
    expect(summary).toHaveTextContent('证据候选 1');
    expect(summary).toHaveTextContent('下一步候选 1');
    expect(summary).toHaveTextContent('公开草稿候选 0');

    expect(screen.getByTestId('review-candidate-evidence-0')).toHaveTextContent('Fresh task');
    expect(screen.getByTestId('selection-count-evidence')).toHaveTextContent('已选 0 条');
  });

  it('sends the requested window as query params', async () => {
    const fetchMock = mockReviewOnly();
    renderPage();
    await screen.findByTestId('review-candidate-evidence-0');
    const url = String(fetchMock.mock.calls[0][0]);
    expect(url).toContain('/profiles/alice/review?');
    expect(url).toMatch(/start=\d{4}-\d{2}-\d{2}/);
    expect(url).toMatch(/end=\d{4}-\d{2}-\d{2}/);
  });

  it('saves selected candidates to activity with If-Match', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes('/review/save')) {
        expect(init?.method).toBe('POST');
        expect((init?.headers as Record<string, string>)['If-Match']).toBe(ETAG);
        const body = JSON.parse(String(init?.body));
        expect(body.candidate_type).toBe('evidence');
        expect(body.start).toBe('2026-09-14');
        expect(body.end).toBe('2026-09-20');
        expect(body.candidates).toHaveLength(1);
        expect(body.candidates[0].title).toBe('Fresh task');
        return jsonResponse(200, { ok: true, saved: 1, item_ids: ['act:review:evidence:x'] });
      }
      if (url.includes('/profiles/alice/review')) {
        return reviewResponse();
      }
      return jsonResponse(404, { code: 'not_found', message: 'not found' });
    });
    vi.stubGlobal('fetch', fetchMock);

    renderPage();
    await screen.findByTestId('review-candidate-evidence-0');
    fireEvent.click(screen.getByLabelText('选择 Fresh task'));
    expect(screen.getByTestId('selection-count-evidence')).toHaveTextContent('已选 1 条');
    fireEvent.click(screen.getByRole('button', { name: /保存到活动 \(1\)/ }));

    expect(await screen.findByTestId('save-success-evidence')).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByTestId('selection-count-evidence')).toHaveTextContent('已选 0 条'),
    );
  });

  it('applies selected evidence candidates with mark_crystallized', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes('/review/apply')) {
        expect((init?.headers as Record<string, string>)['If-Match']).toBe(ETAG);
        const body = JSON.parse(String(init?.body));
        expect(body.candidate_type).toBe('evidence');
        expect(body.mark_crystallized).toBe(true);
        expect(body.candidates[0].task_id).toBe('done-fresh');
        return jsonResponse(200, {
          ok: true,
          applied: 1,
          failed: 0,
          results: [{ ok: true, title: 'Fresh task', warnings: [], errors: [], changed_paths: [], output_path: '' }],
        });
      }
      if (url.includes('/profiles/alice/review')) {
        return reviewResponse();
      }
      return jsonResponse(404, { code: 'not_found', message: 'not found' });
    });
    vi.stubGlobal('fetch', fetchMock);

    renderPage();
    await screen.findByTestId('review-candidate-evidence-0');
    fireEvent.click(screen.getByLabelText('选择 Fresh task'));
    fireEvent.click(screen.getByRole('button', { name: /应用所选 \(1\)/ }));

    expect(await screen.findByTestId('apply-result-evidence')).toHaveTextContent(
      '成功 1 条,失败 0 条',
    );
  });

  it('switches to the next-action tab and applies from there', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes('/review/apply')) {
        const body = JSON.parse(String(init?.body));
        expect(body.candidate_type).toBe('next_action');
        expect(body.candidates[0].resource_id).toBe('res-1');
        return jsonResponse(200, {
          ok: true,
          applied: 1,
          failed: 0,
          results: [{ ok: true, title: 'Reproduce the benchmark', warnings: [], errors: [], changed_paths: [], output_path: '' }],
        });
      }
      if (url.includes('/profiles/alice/review')) {
        return reviewResponse();
      }
      return jsonResponse(404, { code: 'not_found', message: 'not found' });
    });
    vi.stubGlobal('fetch', fetchMock);

    renderPage();
    await screen.findByTestId('review-candidate-evidence-0');
    fireEvent.click(screen.getByRole('tab', { name: '下一步候选' }));
    expect(await screen.findByTestId('review-candidate-next_action-0')).toHaveTextContent(
      'Reproduce the benchmark',
    );
    fireEvent.click(screen.getByLabelText('选择 Reproduce the benchmark'));
    fireEvent.click(screen.getByRole('button', { name: /应用所选 \(1\)/ }));

    expect(await screen.findByTestId('apply-result-next_action')).toBeInTheDocument();
  });

  it('renders method notes from the method tab', async () => {
    mockReviewOnly();
    renderPage();
    await screen.findByTestId('review-candidate-evidence-0');
    fireEvent.click(screen.getByRole('tab', { name: '方法笔记' }));
    expect(await screen.findByTestId('method-note-0')).toHaveTextContent('a detail line');
  });

  it('flags a stale ETag (412) as a conflict with a refresh button that refetches', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('/review/apply')) {
        return jsonResponse(412, {
          code: 'etag_mismatch',
          message: 'Review source files changed since they were loaded',
        });
      }
      if (url.includes('/profiles/alice/review')) {
        return reviewResponse();
      }
      return jsonResponse(404, { code: 'not_found', message: 'not found' });
    });
    vi.stubGlobal('fetch', fetchMock);

    renderPage();
    await screen.findByTestId('review-candidate-evidence-0');
    fireEvent.click(screen.getByLabelText('选择 Fresh task'));
    fireEvent.click(screen.getByRole('button', { name: /应用所选 \(1\)/ }));

    // 412 is recognized as a conflict: yellow unified copy, not the raw red
    // error message.
    const conflict = await screen.findByTestId('conflict-alert');
    expect(conflict).toHaveTextContent('数据已被他人修改');
    expect(conflict).toHaveTextContent('请刷新后重试');
    expect(screen.queryByText(/Review source files changed/)).not.toBeInTheDocument();

    const reviewGets = () =>
      fetchMock.mock.calls.filter(([input]) =>
        String(input).includes('/profiles/alice/review?'),
      ).length;
    const before = reviewGets();
    fireEvent.click(screen.getByRole('button', { name: '刷新' }));
    await waitFor(() => expect(reviewGets()).toBeGreaterThan(before));
  });

  it('shows an error alert when the review fails to load', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => jsonResponse(403, { code: 'profile_forbidden', message: 'denied' })),
    );
    renderPage();
    expect(await screen.findByText('加载失败')).toBeInTheDocument();
  });

  it('clears the success banner when a new selection starts', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('/review/save')) {
        return jsonResponse(200, { ok: true, saved: 1, item_ids: ['act:review:evidence:x'] });
      }
      if (url.includes('/profiles/alice/review')) {
        return reviewResponse();
      }
      return jsonResponse(404, { code: 'not_found', message: 'not found' });
    });
    vi.stubGlobal('fetch', fetchMock);

    renderPage();
    await screen.findByTestId('review-candidate-evidence-0');
    fireEvent.click(screen.getByLabelText('选择 Fresh task'));
    fireEvent.click(screen.getByRole('button', { name: /保存到活动 \(1\)/ }));
    expect(await screen.findByTestId('save-success-evidence')).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText('选择 Fresh task'));
    expect(screen.queryByTestId('save-success-evidence')).not.toBeInTheDocument();
  });
});
