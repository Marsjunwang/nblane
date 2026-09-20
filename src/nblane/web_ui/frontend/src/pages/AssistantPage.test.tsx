import { screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { jsonResponse, renderWithProviders } from '../test/render';
import { AssistantPage, formatUptime } from './AssistantPage';

const READY_PAYLOAD = {
  available: true,
  version: 'openclaw 2026.9.4',
  gateway: { ready: true, uptime_ms: 7_260_000 },
  mcp_nblane_registered: true,
  automations: { total: 3, enabled: 2 },
  console_url: 'http://127.0.0.1:18789/',
  checked_at: '2026-09-19T02:30:00+00:00',
};

const UNAVAILABLE_PAYLOAD = {
  available: false,
  version: null,
  gateway: null,
  mcp_nblane_registered: null,
  automations: null,
  console_url: 'http://127.0.0.1:18789/',
  checked_at: '2026-09-19T02:30:00+00:00',
};

function stubFetch(payload: unknown, status = 200) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => jsonResponse(status, payload)),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('AssistantPage', () => {
  it('renders gateway/version/automations from the status payload', async () => {
    stubFetch(READY_PAYLOAD);
    renderWithProviders(<AssistantPage />, '/assistant');

    expect(await screen.findByText('Gateway 状态')).toBeInTheDocument();
    expect(screen.getByText('就绪')).toBeInTheDocument();
    expect(screen.getByText('运行时长:2 小时 1 分')).toBeInTheDocument();
    expect(screen.getByText('版本:openclaw 2026.9.4')).toBeInTheDocument();
    expect(screen.getByText('已注册')).toBeInTheDocument();
    expect(screen.getByText('共 3 条,启用 2 条')).toBeInTheDocument();
  });

  it('links the console button to console_url in a new tab', async () => {
    stubFetch(READY_PAYLOAD);
    renderWithProviders(<AssistantPage />, '/assistant');

    const button = await screen.findByRole('link', { name: '打开控制台' });
    expect(button).toHaveAttribute('href', 'http://127.0.0.1:18789/');
    expect(button).toHaveAttribute('target', '_blank');
    expect(button).toHaveAttribute('rel', expect.stringContaining('noopener'));
  });

  it('shows the not-installed empty state when unavailable', async () => {
    stubFetch(UNAVAILABLE_PAYLOAD);
    renderWithProviders(<AssistantPage />, '/assistant');

    expect(await screen.findByText('本机未安装 OpenClaw')).toBeInTheDocument();
    expect(screen.getByText(/openclaw-integration\.md/)).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: '打开控制台' })).not.toBeInTheDocument();
  });

  it('shows an error alert when the request fails', async () => {
    stubFetch({ detail: 'boom' }, 500);
    renderWithProviders(<AssistantPage />, '/assistant');

    expect(await screen.findByText('加载失败')).toBeInTheDocument();
  });
});

describe('formatUptime', () => {
  it('formats null, minutes, hours and days', () => {
    expect(formatUptime(null)).toBe('未知');
    expect(formatUptime(30_000)).toBe('刚刚启动');
    expect(formatUptime(5 * 60_000)).toBe('5 分');
    expect(formatUptime(7_260_000)).toBe('2 小时 1 分');
    expect(formatUptime(93_600_000)).toBe('1 天 2 小时');
  });
});
