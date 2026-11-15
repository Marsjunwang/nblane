import { fireEvent, screen, waitFor } from '@testing-library/react';
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
      <Route path="/p/:name/projects" element={<div>projects page</div>} />
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
      state: { from: { pathname: '/p/alice/projects' } },
    });

    await submitLogin();
    expect(await screen.findByText('projects page')).toBeInTheDocument();
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

  it.each(['用户名', '密码'])('clears an old rejection when %s changes and submits the current credentials', async (field) => {
    const submitted: Array<{ username: string; password: string }> = [];
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      if (!String(input).endsWith('/auth/login')) {
        return jsonResponse(401, { detail: 'Authentication required' });
      }
      submitted.push(JSON.parse(String(init?.body)));
      return submitted.length === 1
        ? jsonResponse(401, { detail: 'Invalid username or password' })
        : jsonResponse(200, { id: 'u1', display_name: 'Admin', role: 'admin', auth_enabled: true });
    }));
    renderLogin('/login');
    await submitLogin();
    expect(await screen.findByTestId('login-error')).toHaveTextContent('Invalid username or password');

    fireEvent.change(screen.getByLabelText(new RegExp(field)), {
      target: { value: field === '用户名' ? ' updated-admin ' : ' updated-secret ' },
    });
    await waitFor(() => expect(screen.queryByTestId('login-error')).not.toBeInTheDocument());
    expect(submitted).toHaveLength(1);
    fireEvent.click(screen.getByRole('button', { name: '登录' }));
    expect(await screen.findByText('profiles home')).toBeInTheDocument();
    expect(submitted[1]).toEqual(field === '用户名'
      ? { username: 'updated-admin', password: 'secret' }
      : { username: 'admin', password: ' updated-secret ' });
  });

  it('keeps a pending login active while editing and ignores duplicate form submissions', async () => {
    let finishLogin!: (response: Response) => void;
    const loginResponse = new Promise<Response>((resolve) => { finishLogin = resolve; });
    const submitted: unknown[] = [];
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      if (!String(input).endsWith('/auth/login')) {
        return jsonResponse(401, { detail: 'Authentication required' });
      }
      submitted.push(JSON.parse(String(init?.body)));
      return loginResponse;
    }));
    renderLogin('/login');
    await submitLogin();
    const button = screen.getByRole('button', { name: '登录' });
    await waitFor(() => expect(button).toBeDisabled());
    fireEvent.change(screen.getByLabelText(/密码/), { target: { value: 'edited-during-request' } });
    expect(button).toBeDisabled();
    fireEvent.submit(button.closest('form')!);

    finishLogin(jsonResponse(200, { id: 'u1', display_name: 'Admin', role: 'admin', auth_enabled: true }));
    expect(await screen.findByText('profiles home')).toBeInTheDocument();
    expect(submitted).toEqual([{ username: 'admin', password: 'secret' }]);
  });
});
