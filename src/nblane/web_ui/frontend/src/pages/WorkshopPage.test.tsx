import { fireEvent, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { jsonResponse, renderWithProviders } from '../test/render';
import { WorkshopPage, terminalUrl } from './WorkshopPage';

const REACHABLE_PAYLOAD = {
  url: '/terminal/',
  reachable: true,
  checked_at: '2026-09-22T10:00:00+00:00',
  admin: true,
  font_size_mobile: 24,
  font_size_desktop: 15,
};

type Call = { url: string; body: unknown };

function stubFetch(payload: unknown, status = 200) {
  const calls: Call[] = [];
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      calls.push({ url, body: init?.body ? JSON.parse(String(init.body)) : undefined });
      if (url.includes('/system/workshop/')) return jsonResponse(200, { ok: true });
      return jsonResponse(status, payload);
    }),
  );
  return calls;
}

afterEach(() => {
  vi.unstubAllGlobals();
  window.localStorage.clear();
});

describe('WorkshopPage', () => {
  it('embeds the terminal with the desktop font size when reachable', async () => {
    stubFetch(REACHABLE_PAYLOAD);
    renderWithProviders(<WorkshopPage />, '/workshop');

    expect(await screen.findByText('车间')).toBeInTheDocument();
    const frame = await screen.findByTestId('sidecar-frame');
    expect(frame).toHaveAttribute('src', '/terminal/?fontSize=15');
    // The page itself is the new tab now; no second "open in new tab" link.
    expect(screen.queryByRole('link', { name: '新标签页打开' })).not.toBeInTheDocument();
  });

  it('sends keys and typed text through the key bar', async () => {
    const calls = stubFetch(REACHABLE_PAYLOAD);
    renderWithProviders(<WorkshopPage />, '/workshop');

    fireEvent.click(await screen.findByRole('button', { name: '快捷输入' }));
    fireEvent.click(screen.getByRole('button', { name: '中断 / 关闭菜单' }));
    await waitFor(() => expect(calls.some((call) => call.url.endsWith('/system/workshop/keys'))).toBe(true));
    expect(calls.find((call) => call.url.endsWith('/system/workshop/keys'))?.body).toEqual({ keys: ['esc'] });

    fireEvent.change(screen.getByRole('textbox', { name: '发送到终端的文字' }), { target: { value: '你好' } });
    fireEvent.click(screen.getByRole('button', { name: '发送' }));
    await waitFor(() => expect(calls.some((call) => call.url.endsWith('/system/workshop/input'))).toBe(true));
    expect(calls.find((call) => call.url.endsWith('/system/workshop/input'))?.body).toEqual({ text: '你好', submit: true });
  });

  it('tells non-admins the terminal is admin only', async () => {
    stubFetch({ ...REACHABLE_PAYLOAD, admin: false });
    renderWithProviders(<WorkshopPage />, '/workshop');

    expect(await screen.findByText('车间终端仅管理员可用')).toBeInTheDocument();
    expect(screen.queryByTestId('sidecar-frame')).not.toBeInTheDocument();
  });

  it('points to settings instead of the iframe when ttyd is down', async () => {
    stubFetch({ ...REACHABLE_PAYLOAD, reachable: false });
    renderWithProviders(<WorkshopPage />, '/workshop');

    expect(await screen.findByText('车间终端未运行')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: '打开车间设置' })).toHaveAttribute('href', '/settings/workshop');
    expect(screen.queryByTestId('sidecar-frame')).not.toBeInTheDocument();
  });

  it('shows an error alert when the request fails', async () => {
    stubFetch({ detail: 'boom' }, 500);
    renderWithProviders(<WorkshopPage />, '/workshop');

    expect(await screen.findByText('加载失败')).toBeInTheDocument();
  });
});

describe('terminalUrl', () => {
  it('adds the font size to relative and absolute urls', () => {
    expect(terminalUrl('/terminal/', 24)).toBe('/terminal/?fontSize=24');
    expect(terminalUrl('http://127.0.0.1:7668/', 15)).toBe('http://127.0.0.1:7668/?fontSize=15');
  });
});
