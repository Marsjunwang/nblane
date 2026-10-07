import { act, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import { jsonResponse, renderWithProviders } from '../test/render';
import { PaperReaderPage } from './PaperReaderPage';

const BODY = {
  profile: 'alice',
  papers: [{ id: 'source:paper/1', title: 'A paper', pdf_available: true, tags: [], status: 'reading', summary: '', page_count: 12, last_page: 4 }],
  summary: {},
  sidecar: { base: 'http://127.0.0.1:8502', configured: false, auth_enabled: false, handoff_token: '', paper_library_url: '' },
};
const READER = {
  profile: 'alice',
  source_id: 'source:paper/1',
  reader_url: 'http://127.0.0.1:8502/reader/view/source%3Apaper%2F1?token=reader-token',
  token: 'reader-token',
};
const READ_PATH = '/p/:name/research/papers/:sourceId/read';

function renderReader(route: string) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL) =>
      String(input).includes('/papers/source%3Apaper%2F1/reader') ? jsonResponse(200, READER) : jsonResponse(200, BODY),
    ),
  );
  return renderWithProviders(
    <Routes>
      <Route path={READ_PATH} element={<PaperReaderPage />} />
      <Route path="/p/:name/research/papers/:sourceId" element={<div>overview-page</div>} />
    </Routes>,
    route,
  );
}

afterEach(() => vi.unstubAllGlobals());

describe('PaperReaderPage', () => {
  it('builds a reader deep link and preserves query state', async () => {
    renderReader('/p/alice/research/papers/source%3Apaper%2F1/read?page=3&mode=translation&anchor=segment-42&target_lang=zh');
    const frame = await screen.findByTestId('sidecar-frame');
    expect(frame).toHaveAttribute('src', expect.stringContaining('/reader/view/source%3Apaper%2F1'));
    expect(frame).toHaveAttribute('src', expect.stringContaining('page=3'));
    expect(frame).toHaveAttribute('src', expect.stringContaining('mode=translation'));
    expect(frame).toHaveAttribute('src', expect.stringContaining('anchor=segment-42'));
    expect(frame).toHaveAttribute('src', expect.stringContaining('ui_lang=zh'));
  });

  it('renders one slim bar: back to overview, title, progress, SPA new-tab link', async () => {
    renderReader('/p/alice/research/papers/source%3Apaper%2F1/read');

    const back = await screen.findByRole('link', { name: '论文概览' });
    expect(back).toHaveAttribute('href', '/p/alice/research/papers/source%3Apaper%2F1');
    expect(screen.getByText('A paper')).toBeInTheDocument();
    expect(screen.getByTestId('paper-reader-progress')).toHaveTextContent('第 4 / 12 页');
    const external = screen.getByRole('link', { name: /新标签打开/ });
    // The new tab opens the SPA reader route, never the bare sidecar URL.
    expect(external.getAttribute('href')).toMatch(/^\/p\/alice\/research\/papers\/source%3Apaper%2F1\/read\?/);
    expect(external.getAttribute('href')).not.toContain('8502');
    // The old title block / big progress bar / built-in reload row are gone.
    expect(screen.queryByText('Reading session')).toBeNull();
    expect(screen.queryByRole('heading', { name: 'A paper' })).toBeNull();
    expect(screen.queryByRole('button', { name: '重新加载' })).toBeNull();
    expect(screen.getByRole('button', { name: '重新加载阅读器' })).toBeInTheDocument();
  });

  it('syncs reader state messages into the bar and the URL (replaceState)', async () => {
    renderReader('/p/alice/research/papers/source%3Apaper%2F1/read?mode=pdf');
    await screen.findByTestId('sidecar-frame');
    const replace = vi.spyOn(window.history, 'replaceState');

    act(() => {
      window.dispatchEvent(
        new MessageEvent('message', {
          origin: 'http://127.0.0.1:8502',
          data: { type: 'nblane.reader.state', source_id: 'source:paper/1', mode: 'compare', page: 7, total_pages: 12 },
        }),
      );
    });
    expect(screen.getByTestId('paper-reader-progress')).toHaveTextContent('对照 · 第 7 / 12 页');
    expect(replace).toHaveBeenCalled();
    const url = String(replace.mock.calls.at(-1)?.[2] ?? '');
    expect(url).toContain('mode=compare');
    expect(url).toContain('page=7');
    expect(screen.getByRole('link', { name: /新标签打开/ }).getAttribute('href')).toContain('mode=compare');

    // Messages from another origin are ignored.
    act(() => {
      window.dispatchEvent(
        new MessageEvent('message', {
          origin: 'http://evil.example',
          data: { type: 'nblane.reader.state', source_id: 'source:paper/1', mode: 'pdf', page: 1, total_pages: 12 },
        }),
      );
    });
    expect(screen.getByTestId('paper-reader-progress')).toHaveTextContent('第 7 / 12 页');
    replace.mockRestore();
  });

  it('shows a retryable error when the reader session cannot be minted', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) =>
        String(input).includes('/reader')
          ? jsonResponse(409, { code: 'paper_pdf_missing', message: 'Paper PDF is not ready' })
          : jsonResponse(200, BODY),
      ),
    );
    renderWithProviders(
      <Routes><Route path={READ_PATH} element={<PaperReaderPage />} /></Routes>,
      '/p/alice/research/papers/source%3Apaper%2F1/read',
    );
    expect(await screen.findByText('Paper PDF is not ready')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '重试' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: '论文概览' })).toBeInTheDocument();
  });
});
