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
});
