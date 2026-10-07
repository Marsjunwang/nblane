import { MantineProvider } from '@mantine/core';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { LegacyStreamlitRedirect, legacyPageKey } from './LegacyStreamlitRedirect';

function Where() {
  const location = useLocation();
  return <div data-testid="where">{`${location.pathname}${location.search}`}</div>;
}

function renderAt(url: string, profiles: { name: string }[]) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => new Response(JSON.stringify(profiles), { status: 200, headers: { 'content-type': 'application/json' } })),
  );
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MantineProvider>
        <MemoryRouter initialEntries={[url]}>
          <Routes>
            {/* Mirrors App.tsx: static routes outrank /:legacyPage. */}
            <Route path="/settings" element={<Where />} />
            <Route path="/pages/:legacyFile" element={<LegacyStreamlitRedirect />} />
            <Route path="/:legacyPage" element={<LegacyStreamlitRedirect />} />
            <Route path="*" element={<Where />} />
          </Routes>
        </MemoryRouter>
      </MantineProvider>
    </QueryClientProvider>,
  );
}

afterEach(() => vi.unstubAllGlobals());

describe('LegacyStreamlitRedirect', () => {
  it('normalizes Streamlit page names', () => {
    expect(legacyPageKey('Skill_Tree')).toBe('skill_tree');
    expect(legacyPageKey('3_Kanban.py')).toBe('kanban');
    expect(legacyPageKey('pages/7_Research.py')).toBe('research');
  });

  it('maps a page file with an explicit profile', async () => {
    renderAt('/pages/3_Kanban.py?profile=%E7%8E%8B%E5%86%9B', []);
    expect(await screen.findByTestId('where')).toHaveTextContent('/p/%E7%8E%8B%E5%86%9B/projects');
  });

  it('sends retired orphan pages to their replacements', async () => {
    renderAt('/pages/6_Output_Studio.py?profile=dev', []);
    expect(await screen.findByTestId('where')).toHaveTextContent('/p/dev/content');
  });

  it('sends the retired Agent Activity page home', async () => {
    renderAt('/Agent_Activity?profile=dev', []);
    expect(await screen.findByTestId('where')).toHaveTextContent('/p/dev/home');
  });

  it('uses the only profile when none is given', async () => {
    renderAt('/Research', [{ name: 'dev' }]);
    expect(await screen.findByTestId('where')).toHaveTextContent('/p/dev/research');
  });

  it('falls back to the profile list when the profile is ambiguous', async () => {
    renderAt('/Skill_Tree', [{ name: 'a' }, { name: 'b' }]);
    expect(await screen.findByTestId('where')).toHaveTextContent(/^\/$/);
  });

  it('lets /Settings reach the settings route (paths match case-insensitively)', async () => {
    renderAt('/Settings', []);
    expect(await screen.findByTestId('where')).toHaveTextContent(/^\/settings$/i);
  });

  it('shows 404 for unknown single-segment paths', async () => {
    renderAt('/not-a-page', []);
    expect(await screen.findByText('页面不存在')).toBeInTheDocument();
  });
});
