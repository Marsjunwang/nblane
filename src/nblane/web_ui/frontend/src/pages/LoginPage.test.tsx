import { fireEvent, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';

import { jsonResponse, renderWithProviders } from '../test/render';
import { LoginPage } from './LoginPage';

afterEach(() => {
  vi.unstubAllGlobals();
});

function renderLogin(entry: string | { pathname: string; state?: unknown }) {
  return renderWithProviders(
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<div>profiles home</div>} />
      <Route path="/p/:name/studio" element={<div>studio page</div>} />
    </Routes>,
    entry,
  );
}

function mockLoginApi() {
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.endsWith('/auth/login')) {
      return jsonResponse(200, {
        id: 'u1',
        display_name: 'Admin',
        role: 'admin',
        auth_enabled: true,
      });
    }
    return jsonResponse(401, { detail: 'Authentication required' });
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

async function submitLogin() {
  fireEvent.change(await screen.findByLabelText(/用户名/), { target: { value: 'admin' } });
  fireEvent.change(screen.getByLabelText(/密码/), { target: { value: 'secret' } });
  fireEvent.click(screen.getByRole('button', { name: '登录' }));
}

describe('LoginPage', () => {
  it('renders the username/password form when no session exists', async () => {
    // /auth/me rejects with 401 → the login wall must stay up.
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => jsonResponse(401, { detail: 'Authentication required' })),
    );
    renderLogin('/login');

    expect(await screen.findByLabelText(/用户名/)).toBeInTheDocument();
    expect(screen.getByLabelText(/密码/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '登录' })).toBeInTheDocument();
  });

  it('returns to the originally requested page after a successful login', async () => {
    mockLoginApi();
    renderLogin({
      pathname: '/login',
      state: { from: { pathname: '/p/alice/studio' } },
    });

    await submitLogin();
    expect(await screen.findByText('studio page')).toBeInTheDocument();
  });

  it('falls back to / and ignores non-local redirect targets', async () => {
    mockLoginApi();
    renderLogin({
      pathname: '/login',
      state: { from: { pathname: '//evil.example/phish' } },
    });

    await submitLogin();
    expect(await screen.findByText('profiles home')).toBeInTheDocument();
  });
});
