import { act, fireEvent, screen, waitFor } from '@testing-library/react';
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

/** jsdom has no visualViewport; stand one in with a controllable height. */
function stubVisualViewport(height: number) {
  let current = height;
  const fake = new EventTarget();
  Object.defineProperty(fake, 'height', { get: () => current });
  Object.defineProperty(window, 'visualViewport', { value: fake, configurable: true });
  return {
    setHeight(next: number) {
      current = next;
      fake.dispatchEvent(new Event('resize'));
    },
  };
}

afterEach(() => {
  vi.unstubAllGlobals();
  window.localStorage.clear();
  delete (window as unknown as Record<string, unknown>).visualViewport;
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

  it('sends typed text on Enter and keeps Shift+Enter as a newline', async () => {
    const calls = stubFetch(REACHABLE_PAYLOAD);
    renderWithProviders(<WorkshopPage />, '/workshop');

    fireEvent.click(await screen.findByRole('button', { name: '快捷输入' }));
    const box = screen.getByRole('textbox', { name: '发送到终端的文字' });
    fireEvent.change(box, { target: { value: 'ls -la' } });
    fireEvent.keyDown(box, { key: 'Enter' });
    await waitFor(() => expect(calls.some((call) => call.url.endsWith('/system/workshop/input'))).toBe(true));
    expect(calls.find((call) => call.url.endsWith('/system/workshop/input'))?.body).toEqual({ text: 'ls -la', submit: true });

    const sent = calls.filter((call) => call.url.endsWith('/system/workshop/input')).length;
    fireEvent.change(box, { target: { value: 'draft' } });
    fireEvent.keyDown(box, { key: 'Enter', shiftKey: true });
    expect(calls.filter((call) => call.url.endsWith('/system/workshop/input')).length).toBe(sent);
  });

  it('keeps the rare keys behind the 更多 toggle', async () => {
    stubFetch(REACHABLE_PAYLOAD);
    renderWithProviders(<WorkshopPage />, '/workshop');

    fireEvent.click(await screen.findByRole('button', { name: '快捷输入' }));
    // Enter and the arrows are always visible; Ctrl-R and PgUp are not.
    expect(screen.getByRole('button', { name: '回车' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '上' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Ctrl-R：搜索历史' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '程序内上翻页（less / man）' })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: '显示更多按键' }));
    expect(screen.getByRole('button', { name: 'Ctrl-R：搜索历史' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '程序内上翻页（less / man）' })).toBeInTheDocument();
  });

  it('offers view scroll buttons that send no key', async () => {
    const calls = stubFetch(REACHABLE_PAYLOAD);
    renderWithProviders(<WorkshopPage />, '/workshop');

    fireEvent.click(await screen.findByRole('button', { name: '快捷输入' }));
    // View paging scrolls the terminal viewport client-side; nothing goes to tmux.
    fireEvent.click(screen.getByRole('button', { name: '向上翻一屏（终端画面）' }));
    fireEvent.click(screen.getByRole('button', { name: '向下翻一屏（终端画面）' }));
    fireEvent.click(screen.getByRole('button', { name: '滚动到最新输出' }));
    expect(calls.some((call) => call.url.endsWith('/system/workshop/keys'))).toBe(false);
  });

  it('flashes a pressed state when a key is tapped', async () => {
    stubFetch(REACHABLE_PAYLOAD);
    renderWithProviders(<WorkshopPage />, '/workshop');

    fireEvent.click(await screen.findByRole('button', { name: '快捷输入' }));
    const esc = screen.getByRole('button', { name: '中断 / 关闭菜单' });
    fireEvent.click(esc);
    expect(esc).toHaveAttribute('data-pressed', 'true');
  });

  it('collapses chrome while the soft keyboard is open and restores it after', async () => {
    const viewport = stubVisualViewport(844);
    stubFetch(REACHABLE_PAYLOAD);
    renderWithProviders(<WorkshopPage />, '/workshop');

    fireEvent.click(await screen.findByRole('button', { name: '快捷输入' }));
    expect(screen.getByText('车间')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '上' })).toBeInTheDocument();

    // Keyboard opens: the page header and the arrow row drop out; the main
    // keys and the input box stay.
    act(() => viewport.setHeight(500));
    await waitFor(() => expect(screen.queryByText('车间')).not.toBeInTheDocument());
    expect(screen.queryByRole('button', { name: '上' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '显示更多按键' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: '回车' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '中断 / 关闭菜单' })).toBeInTheDocument();
    expect(screen.getByRole('textbox', { name: '发送到终端的文字' })).toBeInTheDocument();

    // Keyboard closes: everything returns.
    act(() => viewport.setHeight(844));
    await waitFor(() => expect(screen.getByText('车间')).toBeInTheDocument());
    expect(screen.getByRole('button', { name: '上' })).toBeInTheDocument();
  });

  it('blurs xterm helper focus on touch devices so terminal taps never pop the keyboard', async () => {
    vi.stubGlobal(
      'matchMedia',
      vi.fn().mockImplementation((query: string) => ({
        matches: query === '(pointer: coarse)',
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    );
    stubFetch(REACHABLE_PAYLOAD);
    renderWithProviders(<WorkshopPage />, '/workshop');
    const frame = (await screen.findByTestId('sidecar-frame')) as HTMLIFrameElement;

    // Plant xterm's helper textarea, wait for the page to mark it, then focus
    // it the way a terminal tap would. jsdom does not load iframe content, so
    // give the placeholder document a body first.
    const doc = frame.contentDocument!;
    doc.open();
    doc.write('<html><head></head><body></body></html>');
    doc.close();
    const helper = doc.createElement('textarea');
    helper.className = 'xterm-helper-textarea';
    doc.body.appendChild(helper);
    // xterm/ttyd focus the helper on load, before the page's poll notices it.
    helper.focus();
    expect(doc.activeElement).toBe(helper);
    await waitFor(() => expect(doc.activeElement).not.toBe(helper), { timeout: 2000 });
    // A later re-focus (terminal tap) is handed back immediately too.
    helper.focus();
    expect(doc.activeElement).not.toBe(helper);
  });

  it('leaves xterm helper focus alone on non-touch devices', async () => {
    stubFetch(REACHABLE_PAYLOAD);
    renderWithProviders(<WorkshopPage />, '/workshop');
    const frame = (await screen.findByTestId('sidecar-frame')) as HTMLIFrameElement;

    const doc = frame.contentDocument!;
    doc.open();
    doc.write('<html><head></head><body></body></html>');
    doc.close();
    const helper = doc.createElement('textarea');
    helper.className = 'xterm-helper-textarea';
    doc.body.appendChild(helper);
    helper.focus();
    await new Promise((resolve) => setTimeout(resolve, 700)); // past one poll cycle
    expect(helper.dataset.noblur).toBeUndefined();
    expect(doc.activeElement).toBe(helper);
  });

  it('reconnects the terminal after a long background spell, not after a short one', async () => {
    stubFetch(REACHABLE_PAYLOAD);
    renderWithProviders(<WorkshopPage />, '/workshop');
    const frame = await screen.findByTestId('sidecar-frame');

    const setVisibility = (value: string) => {
      Object.defineProperty(document, 'visibilityState', { value, configurable: true });
      document.dispatchEvent(new Event('visibilitychange'));
    };

    // A quick hide/show (app switch) keeps the same iframe.
    act(() => setVisibility('hidden'));
    act(() => setVisibility('visible'));
    expect(screen.getByTestId('sidecar-frame')).toBe(frame);

    // Two minutes in the background: the iframe is remounted (fresh socket).
    vi.useFakeTimers();
    try {
      act(() => setVisibility('hidden'));
      act(() => {
        vi.setSystemTime(Date.now() + 130_000);
      });
      act(() => setVisibility('visible'));
      expect(screen.getByTestId('sidecar-frame')).not.toBe(frame);
    } finally {
      vi.useRealTimers();
    }
    delete (document as unknown as Record<string, unknown>).visibilityState;
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
