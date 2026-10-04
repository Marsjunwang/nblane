import { screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';

import { jsonResponse, renderWithProviders } from '../test/render';
import { ResearchPage } from './ResearchPage';

const RESEARCH = {
  profile: 'alice',
  summary: {
    total: 3,
    active_total: 2,
    status_counts: { reading: 1, inbox: 1, archived: 1 },
    kind_counts: { paper: 2, web: 1 },
    claims_total: 1,
    citations_total: 1,
  },
  sources: [
    {
      id: 'src:002',
      title: 'grasp tooling post',
      kind: 'web',
      status: 'inbox',
      url: '',
      captured_at: '2026-09-19',
      tags: [],
      summary: '',
    },
    {
      id: 'src:001',
      title: 'SLAM survey',
      kind: 'paper',
      status: 'reading',
      url: 'https://example.org/slam',
      captured_at: '2026-09-18',
      tags: ['robotics'],
      summary: '',
    },
  ],
  sidecar: {
    base: 'http://127.0.0.1:8502',
    configured: false,
    auth_enabled: false,
    handoff_token: '',
    paper_library_url: 'http://127.0.0.1:8502/paper-library?profile=alice',
    dashboard_url: 'http://127.0.0.1:8502/dashboard?profile=alice&embed=1',
  },
};

function renderPage(body: unknown = RESEARCH) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('/profiles/alice/research')) {
        return jsonResponse(200, body);
      }
      return jsonResponse(404, { code: 'not_found', message: 'not found' });
    }),
  );
  return renderWithProviders(
    <Routes>
      <Route path="/p/:name/research" element={<ResearchPage />} />
    </Routes>,
    '/p/alice/research',
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('ResearchPage', () => {
  it('renders a reading desk and links to the standalone library', async () => {
    renderPage();

    expect(await screen.findByText('alice · 研究台')).toBeInTheDocument();
    expect(screen.getByText('继续阅读')).toBeInTheDocument();
    expect(screen.getByText('论文总数')).toBeInTheDocument();
    expect(screen.queryByText('断言 1')).toBeNull();
    expect(screen.queryByText('引用 1')).toBeNull();
    const workspace = screen.getByRole('link', { name: /打开论文库/ });
    expect(workspace).toHaveAttribute(
      'href',
      'http://127.0.0.1:8502/paper-library?profile=alice',
    );
  });

  it('keeps the paper library outside the reading desk', async () => {
    renderPage();
    await screen.findByText('alice · 研究台');

    expect(screen.queryByTestId('sidecar-frame')).toBeNull();
    expect(screen.queryByText('嵌入显示')).toBeNull();
  });

  it('shows an empty-state hint when the inbox has no sources', async () => {
    renderPage({
      ...RESEARCH,
      summary: { ...RESEARCH.summary, total: 0, active_total: 0 },
      sources: [],
    });

    expect(await screen.findByText(/队列为空/)).toBeInTheDocument();
  });
});
