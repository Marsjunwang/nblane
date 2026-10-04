import { screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import { jsonResponse, renderWithProviders } from '../test/render';
import { PaperReaderPage } from './PaperReaderPage';

const BODY = {
  profile: 'alice',
  papers: [{ id: 'source:paper/1', title: 'A paper', pdf_available: true, tags: [], status: 'reading', summary: '' }],
  summary: {},
  sidecar: { base: 'http://127.0.0.1:8502', configured: false, auth_enabled: false, handoff_token: '', paper_library_url: '', dashboard_url: '' },
};

afterEach(() => vi.unstubAllGlobals());

describe('PaperReaderPage', () => {
  it('builds a reader deep link and preserves query state', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('/papers/source%3Apaper%2F1/reader')) {
        return jsonResponse(200, { profile: 'alice', source_id: 'source:paper/1', reader_url: 'http://127.0.0.1:8502/reader/view/source%3Apaper%2F1?token=reader-token', token: 'reader-token' });
      }
      return jsonResponse(200, BODY);
    });
    vi.stubGlobal('fetch', fetchMock);
    renderWithProviders(<Routes><Route path="/p/:name/research/papers/:sourceId" element={<PaperReaderPage />} /></Routes>, '/p/alice/research/papers/source%3Apaper%2F1?page=3&mode=translation&anchor=segment-42&target_lang=zh');
    expect(await screen.findByText('A paper')).toBeInTheDocument();
    expect(screen.getByTestId('sidecar-frame')).toHaveAttribute('src', expect.stringContaining('/reader/view/source%3Apaper%2F1'));
    expect(screen.getByTestId('sidecar-frame')).toHaveAttribute('src', expect.stringContaining('page=3'));
    expect(screen.getByTestId('sidecar-frame')).toHaveAttribute('src', expect.stringContaining('mode=translation'));
    expect(screen.getByTestId('sidecar-frame')).toHaveAttribute('src', expect.stringContaining('anchor=segment-42'));
  });

  it('keeps the outer shell focused on the reading session', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('/papers/source%3Apaper%2F1/reader')) {
        return jsonResponse(200, { profile: 'alice', source_id: 'source:paper/1', reader_url: 'http://127.0.0.1:8502/reader/view/source%3Apaper%2F1?token=reader-token', token: 'reader-token' });
      }
      return jsonResponse(200, BODY);
    });
    vi.stubGlobal('fetch', fetchMock);
    renderWithProviders(<Routes><Route path="/p/:name/research/papers/:sourceId" element={<PaperReaderPage />} /></Routes>, '/p/alice/research/papers/source%3Apaper%2F1');

    await screen.findByText('A paper');
    expect(screen.getByText('Reader 会自动保存阅读位置')).toBeInTheDocument();
    expect(screen.queryByRole('radio', { name: '原文对照' })).toBeNull();
  });
});
