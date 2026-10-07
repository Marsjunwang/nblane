import { fireEvent, screen, waitFor } from '@testing-library/react';
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

const JOURNAL_PAYLOAD = {
  profile: 'alice',
  retention_days: 30,
  entries: [
    {
      id: 'aj_1',
      at: '2026-10-07T01:00:00+00:00',
      actor: 'openclaw',
      action: 'kanban.card.add',
      tier: 'T1',
      summary: '新建任务「买牛奶」→ Queue',
      status: 'undoable',
      undone_at: '',
      undone_by: '',
      entities: ['kanban_card:kb_1'],
    },
    {
      id: 'aj_0',
      at: '2026-10-07T00:50:00+00:00',
      actor: 'openclaw',
      action: 'checkin.delete',
      tier: 'T2',
      summary: '删除打卡记录 act_1',
      status: 'undone',
      undone_at: '2026-10-07T00:55:00+00:00',
      undone_by: 'wang',
      entities: ['checkin:act_1'],
    },
  ],
};

/** Route the status payload to /system/assistant; profiles + journal get fixtures. */
function stubFetch(payload: unknown, status = 200) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.includes('/agent/journal/') && init?.method === 'POST') {
      return jsonResponse(200, { ok: true, entry: { ...JOURNAL_PAYLOAD.entries[0], status: 'undone' } });
    }
    if (url.includes('/agent/journal')) {
      return jsonResponse(200, JOURNAL_PAYLOAD);
    }
    if (url.endsWith('/profiles')) {
      return jsonResponse(200, [{ name: 'alice' }]);
    }
    return jsonResponse(status, payload);
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
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

describe('RecentAgentOps', () => {
  it('lists journal entries and undoes one', async () => {
    const fetchMock = stubFetch(READY_PAYLOAD);
    renderWithProviders(<AssistantPage />, '/assistant');

    expect(await screen.findByText('新建任务「买牛奶」→ Queue')).toBeInTheDocument();
    expect(screen.getByText('已撤销')).toBeInTheDocument();
    expect(screen.getByText(/聊天确认/)).toBeInTheDocument();
    const buttons = screen.getAllByRole('button', { name: /^撤销：/ });
    expect(buttons).toHaveLength(1);
    fireEvent.click(buttons[0]);
    await waitFor(() =>
      expect(
        fetchMock.mock.calls.some(
          ([url, init]) => String(url).includes('/agent/journal/aj_1/undo') && init?.method === 'POST',
        ),
      ).toBe(true),
    );
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
