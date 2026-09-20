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

    const link = await screen.findByRole('link', { name: '看板' });
    expect(link).toHaveAttribute('href', '/p/we%20ird/kanban');
  });
});
