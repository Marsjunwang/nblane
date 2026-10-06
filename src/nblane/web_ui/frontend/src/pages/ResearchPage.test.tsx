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
  it('renders a reading desk and links to the standalone library', async () => {
    renderPage();

    expect(await screen.findByText('alice · 研究台')).toBeInTheDocument();
    expect(screen.getByText('继续阅读')).toBeInTheDocument();
    expect(screen.getByText('论文总数')).toBeInTheDocument();
    expect(screen.queryByText('断言 1')).toBeNull();
    expect(screen.queryByText('引用 1')).toBeNull();
    // The library opens inside the SPA, not in a new sidecar tab.
    const workspace = screen.getByRole('link', { name: /打开论文库/ });
    expect(workspace).toHaveAttribute('href', '/p/alice/research/library');
    expect(workspace).not.toHaveAttribute('target');
    expect(screen.queryByText(/Research \/ reading desk/)).toBeNull();
    expect(screen.getByRole('link', { name: /查看研究收件箱/ })).toHaveAttribute(
      'href',
      '/p/alice/research/sources',
    );
  });

  it('keeps the paper library outside the reading desk', async () => {
    renderPage();
    await screen.findByText('alice · 研究台');

    expect(screen.queryByTestId('sidecar-frame')).toBeNull();
    expect(screen.queryByText('嵌入显示')).toBeNull();
  });

  it('links paper cards to the overview and 继续阅读 straight to the reader', async () => {
    renderPage({
      ...RESEARCH,
      papers: [
        {
          id: 'source:paper:a',
          title: 'Paper A',
          status: 'reading',
          pdf_available: true,
          page_count: 10,
          last_page: 4,
          segment_count: 20,
          translated_count: 5,
          missing_count: 12,
          stale_count: 3,
          failed_count: 0,
          translation_status: 'stale',
          analysis: { tldr: 'A short verdict.' },
          tags: [],
          summary: '',
        },
        {
          id: 'source:paper:b',
          title: 'Paper B',
          status: 'inbox',
          pdf_available: false,
          page_count: 0,
          last_page: 0,
          segment_count: 0,
          translated_count: 0,
          missing_count: 0,
          stale_count: 0,
          failed_count: 0,
          translation_status: 'missing',
          analysis: {},
          tags: [],
          summary: '',
        },
      ],
    });
    await screen.findByText('alice · 研究台');

    const cards = screen.getAllByRole('link', { name: 'Paper A · 论文概览' });
    expect(cards[0]).toHaveAttribute('href', '/p/alice/research/papers/source%3Apaper%3Aa');
    // Papers without a PDF still land on their overview.
    expect(screen.getAllByRole('link', { name: 'Paper B · 论文概览' })[0]).toHaveAttribute(
      'href',
      '/p/alice/research/papers/source%3Apaper%3Ab',
    );
    expect(screen.getByRole('link', { name: /^继续阅读$/ })).toHaveAttribute(
      'href',
      '/p/alice/research/papers/source%3Apaper%3Aa/read',
    );
    expect(screen.getAllByText('译 5 / 20 · 过期 3').length).toBeGreaterThan(0);
    expect(screen.getAllByText('已快速分析').length).toBeGreaterThan(0);
    expect(screen.getAllByText('未分析').length).toBeGreaterThan(0);
  });

  it('shows a retryable alert when the desk fails to load', async () => {
    let calls = 0;
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => {
        calls += 1;
        return calls === 1
          ? jsonResponse(500, { code: 'boom', message: '服务暂时不可用' })
          : jsonResponse(200, RESEARCH);
      }),
    );
    renderWithProviders(
      <Routes>
        <Route path="/p/:name/research" element={<ResearchPage />} />
      </Routes>,
      '/p/alice/research',
    );
    expect(await screen.findByText('服务暂时不可用')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '重试' }));
    expect(await screen.findByText('alice · 研究台')).toBeInTheDocument();
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
