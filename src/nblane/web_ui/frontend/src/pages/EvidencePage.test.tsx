import { fireEvent, screen, waitFor, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';

import { jsonResponse, renderWithProviders } from '../test/render';
import { EvidencePage } from './EvidencePage';

const LIST = {
  profile: 'alice',
  status: '',
  q: '',
  limit: 50,
  total: 3,
  items: [
    {
      id: 'ev_1',
      title: 'Built ROS2 pick demo',
      evidence_type: 'project',
      review_status: 'reviewed',
      date: '2026-08-20',
      url: 'https://example.org/demo',
      summary: 'End-to-end pick-and-place demo',
      source_refs: ['kb_doing1', 'out_blog1'],
    },
    {
      id: 'ev_2',
      title: 'MoveIt2 workshop notes',
      evidence_type: 'learning',
      review_status: 'needs_review',
      date: '2026-07-15',
      url: '',
      summary: '',
      source_refs: [],
    },
    {
      id: 'ev_3',
      title: 'Published grasp paper review',
      evidence_type: 'output',
      review_status: 'reviewed',
      date: '2026-06-01',
      url: 'https://example.org/blog/grasp',
      summary: '',
      source_refs: ['out_blog1'],
    },
  ],
};

const DETAIL = {
  ...LIST.items[0],
  strength: 'strong',
  confidence: 'high',
  public_readiness: '',
  project_refs: ['proj_demo'],
  experience_refs: [],
  kanban_refs: [],
  source_excerpt: 'demo ran 20 pick cycles',
  origin: 'manual',
  origin_ref: 'kanban:kb_doing1',
  origin_detail: '',
  original_content: '',
  formatted_content: '',
  language: 'en',
  original_language: '',
  original_content_hash: '',
  source_content_hash: '',
  deprecated: false,
  replaced_by: '',
};

function stubFetch(listBody: unknown = LIST) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.includes('/profiles/alice/evidence/ev_1')) {
      return jsonResponse(200, DETAIL);
    }
    if (url.includes('/profiles/alice/evidence')) {
      return jsonResponse(200, listBody);
    }
    return jsonResponse(404, { code: 'not_found', message: 'not found' });
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

function renderPage() {
  renderWithProviders(
    <Routes>
      <Route path="/p/:name/evidence" element={<EvidencePage />} />
    </Routes>,
    '/p/alice/evidence',
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('EvidencePage', () => {
  it('renders the evidence table with badges, ref counts and link icons', async () => {
    stubFetch();
    renderPage();

    expect(await screen.findByText('alice · 证据池')).toBeInTheDocument();
    const row = await screen.findByTestId('evidence-row-ev_1');
    expect(within(row).getByText('Built ROS2 pick demo')).toBeInTheDocument();
    expect(within(row).getByText('project')).toBeInTheDocument();
    expect(within(row).getByText('2026-08-20')).toBeInTheDocument();
    expect(within(row).getByText('已审核')).toBeInTheDocument();
    // source_refs count.
    expect(within(row).getByText('2')).toBeInTheDocument();
    // External link icon only when url is present.
    expect(within(row).getByLabelText('外部链接')).toBeInTheDocument();
    const row2 = screen.getByTestId('evidence-row-ev_2');
    expect(within(row2).getByText('待审核')).toBeInTheDocument();
    expect(within(row2).queryByLabelText('外部链接')).not.toBeInTheDocument();
    expect(screen.getByTestId('evidence-count')).toHaveTextContent('显示 3 / 共 3 条');
  });

  it('sends the debounced search as the q query param', async () => {
    const fetchMock = stubFetch();
    renderPage();

    expect(await screen.findByText('alice · 证据池')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('搜索证据'), {
      target: { value: 'moveit2' },
    });
    await waitFor(
      () => {
        const urls = fetchMock.mock.calls.map((call) => String(call[0]));
        expect(
          urls.some(
            (url) =>
              url.includes('/profiles/alice/evidence') && url.includes('q=moveit2'),
          ),
        ).toBe(true);
      },
      { timeout: 2000 },
    );
  });

  it('opens the detail modal with full fields on row click', async () => {
    stubFetch();
    renderPage();

    expect(await screen.findByText('alice · 证据池')).toBeInTheDocument();
    fireEvent.click(await screen.findByTestId('evidence-row-ev_1'));
    const detail = await screen.findByTestId('evidence-detail');
    expect(within(detail).getByText('strong')).toBeInTheDocument();
    expect(within(detail).getByText('demo ran 20 pick cycles')).toBeInTheDocument();
    expect(within(detail).getByText('kanban:kb_doing1')).toBeInTheDocument();
    const link = within(detail).getByRole('link', {
      name: 'https://example.org/demo',
    });
    expect(link).toHaveAttribute('href', 'https://example.org/demo');
    expect(link).toHaveAttribute('target', '_blank');
  });

  it('shows 加载更多 when more entries exist and grows the limit', async () => {
    const fetchMock = stubFetch({ ...LIST, total: 80 });
    renderPage();

    expect(await screen.findByText('alice · 证据池')).toBeInTheDocument();
    const more = await screen.findByRole('button', { name: '加载更多' });
    fireEvent.click(more);
    await waitFor(() => {
      const urls = fetchMock.mock.calls.map((call) => String(call[0]));
      expect(urls.some((url) => url.includes('limit=100'))).toBe(true);
    });
  });
});
