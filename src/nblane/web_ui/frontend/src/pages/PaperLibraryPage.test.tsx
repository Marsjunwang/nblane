import { act, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes, useParams } from 'react-router-dom';

import { jsonResponse, renderWithProviders } from '../test/render';
import { PaperLibraryPage } from './PaperLibraryPage';

const RESEARCH = {
  profile: 'alice',
  papers: [],
  summary: {},
  sources: [],
  sidecar: {
    base: 'http://127.0.0.1:8502',
    configured: false,
    auth_enabled: false,
    handoff_token: '',
    paper_library_url: 'http://127.0.0.1:8502/paper-library?profile=alice',
    dashboard_url: '',
  },
};

function OverviewProbe() {
  const { sourceId = '' } = useParams();
  return <div data-testid="overview-probe">{sourceId}</div>;
}

function renderLibrary(body: unknown = RESEARCH) {
  vi.stubGlobal('fetch', vi.fn(async () => jsonResponse(200, body)));
  return renderWithProviders(
    <Routes>
      <Route path="/p/:name/research/library" element={<PaperLibraryPage />} />
      <Route path="/p/:name/research/papers/:sourceId" element={<OverviewProbe />} />
    </Routes>,
    '/p/alice/research/library',
  );
}

function post(origin: string, data: unknown) {
  act(() => {
    window.dispatchEvent(new MessageEvent('message', { origin, data }));
  });
}

afterEach(() => vi.unstubAllGlobals());

describe('PaperLibraryPage', () => {
  it('embeds the sidecar library in Chinese embed mode', async () => {
    renderLibrary();
    const frame = await screen.findByTestId('sidecar-frame');
    const src = frame.getAttribute('src') ?? '';
    expect(src).toContain('/paper-library?');
    expect(src).toContain('profile=alice');
    expect(src).toContain('ui_lang=zh');
    expect(src).toContain('embed=1');
    expect(screen.getByRole('link', { name: '研究台' })).toHaveAttribute('href', '/p/alice/research');
  });

  it('navigates to the paper overview on nblane.library.open_reader', async () => {
    renderLibrary();
    await screen.findByTestId('sidecar-frame');

    post('http://127.0.0.1:8502', { type: 'nblane.library.open_reader', source_id: 'source:paper:x', profile: 'alice' });

    expect(await screen.findByTestId('overview-probe')).toHaveTextContent('source:paper:x');
  });

  it('ignores foreign origins, other profiles and unrelated messages', async () => {
    renderLibrary();
    await screen.findByTestId('sidecar-frame');

    post('http://evil.example', { type: 'nblane.library.open_reader', source_id: 'source:paper:x', profile: 'alice' });
    post('http://127.0.0.1:8502', { type: 'nblane.library.open_reader', source_id: 'source:paper:x', profile: 'bob' });
    post('http://127.0.0.1:8502', { type: 'nblane.library.ready', profile: 'alice' });
    post('http://127.0.0.1:8502', { type: 'nblane.library.open_reader', source_id: '' });

    expect(screen.queryByTestId('overview-probe')).toBeNull();
    expect(screen.getByTestId('sidecar-frame')).toBeInTheDocument();
  });

  it('explains when no sidecar library is configured', async () => {
    renderLibrary({ ...RESEARCH, sidecar: { ...RESEARCH.sidecar, paper_library_url: '' } });
    expect(await screen.findByText('论文库不可用')).toBeInTheDocument();
    expect(screen.queryByTestId('sidecar-frame')).toBeNull();
  });
});
