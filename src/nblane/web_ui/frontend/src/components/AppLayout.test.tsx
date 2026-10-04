import { screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';

import { jsonResponse, renderWithProviders } from '../test/render';
import { AppLayout } from './AppLayout';

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('AppLayout', () => {
  it('percent-encodes the profile name in navbar links', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        jsonResponse(200, {
          id: 'u1',
          display_name: 'Admin',
          role: 'admin',
          auth_enabled: false,
        }),
      ),
    );
    renderWithProviders(
      <Routes>
        <Route path="/p/:name" element={<AppLayout />}>
          <Route path="home" element={<div>home</div>} />
        </Route>
      </Routes>,
      '/p/we ird/home',
    );

    const link = await screen.findByRole('link', { name: '项目' });
    expect(link).toHaveAttribute('href', '/p/we%20ird/projects');
    // The old 看板/项目看板 entries are gone (merged into /projects).
    expect(screen.queryByRole('link', { name: '看板' })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: '项目看板' })).not.toBeInTheDocument();
  });

  it('shows the AI exception bell only when the profile has failures', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes('/ai-exceptions')) {
          return jsonResponse(200, {
            profile: 'alice',
            total: 1,
            items: [
              {
                id: 'run:failed',
                source: 'AI 调用',
                title: '研究分析失败',
                message: '模型不可用',
                action: 'research.paper_qa',
                created: '2026-10-04T10:00:00+00:00',
                href: '/p/alice/research',
              },
            ],
          });
        }
        return jsonResponse(200, {
          id: 'u1',
          display_name: 'Admin',
          role: 'admin',
          auth_enabled: false,
        });
      }),
    );
    renderWithProviders(
      <Routes>
        <Route path="/p/:name" element={<AppLayout />}>
          <Route path="home" element={<div>home</div>} />
          <Route path="research" element={<div>research</div>} />
        </Route>
      </Routes>,
      '/p/alice/home',
    );

    const bell = await screen.findByRole('button', { name: 'AI 异常 1 条' });
    expect(bell).toBeInTheDocument();
    expect(screen.queryByText('研究分析失败')).not.toBeInTheDocument();
    bell.click();
    expect(await screen.findByText('研究分析失败')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: '打开来源' })).toHaveAttribute(
      'href',
      '/p/alice/research',
    );
  });
});
