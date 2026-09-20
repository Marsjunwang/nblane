import { fireEvent, screen } from '@testing-library/react';
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
  it('renders the research summary counters and recent sources', async () => {
    renderPage();

    expect(await screen.findByText('alice · 研究台')).toBeInTheDocument();
    // Summary badges.
    expect(screen.getByText('来源 3')).toBeInTheDocument();
    expect(screen.getByText('进行中 2')).toBeInTheDocument();
    expect(screen.getByText('断言 1')).toBeInTheDocument();
    expect(screen.getByText('引用 1')).toBeInTheDocument();
    expect(screen.getByText('paper: 2')).toBeInTheDocument();
    // Recent source rows, newest first.
    expect(screen.getByText('grasp tooling post')).toBeInTheDocument();
    const linked = screen.getByRole('link', { name: 'SLAM survey' });
    expect(linked).toHaveAttribute('href', 'https://example.org/slam');
    // Sidecar workspace link points at the paper library with the profile.
    const workspace = screen.getByRole('link', { name: /新标签打开/ });
    expect(workspace).toHaveAttribute(
      'href',
      'http://127.0.0.1:8502/paper-library?profile=alice',
    );
  });

  it('embeds the paper library workspace on toggle (fireEvent)', async () => {
    renderPage();
    await screen.findByText('alice · 研究台');

    expect(screen.queryByTestId('sidecar-frame')).toBeNull();
    fireEvent.click(screen.getByText('嵌入显示'));
    expect(screen.getByTestId('sidecar-frame')).toHaveAttribute(
      'src',
      'http://127.0.0.1:8502/paper-library?profile=alice',
    );
    fireEvent.click(screen.getByText('收起嵌入'));
    expect(screen.queryByTestId('sidecar-frame')).toBeNull();
  });

  it('shows an empty-state hint when the inbox has no sources', async () => {
    renderPage({
      ...RESEARCH,
      summary: { ...RESEARCH.summary, total: 0, active_total: 0 },
      sources: [],
    });

    expect(
      await screen.findByText(/研究收件箱还没有来源/),
    ).toBeInTheDocument();
  });
});
