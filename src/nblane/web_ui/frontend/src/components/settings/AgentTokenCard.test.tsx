import { fireEvent, screen, waitFor, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { jsonResponse, renderWithProviders } from '../../test/render';
import { AgentTokenCard } from './AgentSetupSections';

afterEach(() => vi.unstubAllGlobals());

const STATUS = {
  account: 'openclaw', account_exists: true, account_is_agent: true, env_path: '/home/u/.config/nblane/api.env',
  configured: false, token_id: '', token_valid: false, created: '', password_fallback: false, rotated: false,
};

function mockApi(status: Record<string, unknown>, post: () => Response, authEnabled = true) {
  const calls: Array<{ url: string; method: string }> = [];
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const method = init?.method ?? 'GET';
    calls.push({ url, method });
    if (url.endsWith('/auth/me')) return jsonResponse(200, { id: 'admin', display_name: 'Admin', role: 'admin', auth_enabled: authEnabled, profiles: [], teams: [] });
    if (url.endsWith('/settings/agents/token')) return method === 'POST' ? post() : jsonResponse(200, { ...STATUS, ...status });
    return jsonResponse(404, { code: 'not_found', message: url });
  }));
  return calls;
}

describe('AgentTokenCard', () => {
  it('shows unconfigured state and POSTs on confirm', async () => {
    const calls = mockApi({}, () => jsonResponse(200, { ...STATUS, configured: true, token_valid: true, token_id: 'ab12', created: '2026-10-08T01:02:03Z' }));
    renderWithProviders(<AgentTokenCard />, '/settings/agents');
    expect(await screen.findByText('未配置')).toBeInTheDocument();
    expect(screen.getByText('/home/u/.config/nblane/api.env')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '生成并配置 token' }));
    expect(calls.some((c) => c.method === 'POST')).toBe(false);
    const dialog = await screen.findByRole('dialog');
    fireEvent.click(within(dialog).getByRole('button', { name: '生成并配置' }));
    expect(await screen.findByText('已配置，助手下次调用即用新 token')).toBeInTheDocument();
    expect(calls.filter((c) => c.method === 'POST' && c.url.endsWith('/settings/agents/token'))).toHaveLength(1);
    expect(await screen.findByText(/已配置 token（创建于/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '轮换 token' })).toBeInTheDocument();
  });

  it('renders invalid / non-agent states', async () => {
    mockApi({ configured: true, token_valid: false }, () => jsonResponse(500, {}));
    const { unmount } = renderWithProviders(<AgentTokenCard />, '/settings/agents');
    expect(await screen.findByText('token 已失效')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '生成并配置 token' })).toBeEnabled();
    unmount();
    mockApi({ account_is_agent: false }, () => jsonResponse(500, {}));
    renderWithProviders(<AgentTokenCard />, '/settings/agents');
    expect(await screen.findByText('账号未标记为助手')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '生成并配置 token' })).toBeDisabled();
  });

  it('maps error codes to Chinese', async () => {
    mockApi({}, () => jsonResponse(500, { code: 'token_verify_failed', message: 'x' }));
    renderWithProviders(<AgentTokenCard />, '/settings/agents');
    fireEvent.click(await screen.findByRole('button', { name: '生成并配置 token' }));
    const dialog = await screen.findByRole('dialog');
    fireEvent.click(within(dialog).getByRole('button', { name: '生成并配置' }));
    expect(await within(dialog).findByText('写入后校验失败，已恢复原文件并作废新 token，旧 token 仍可用。')).toBeInTheDocument();
  });

  it('hides when login is off', async () => {
    const calls = mockApi({}, () => jsonResponse(500, {}), false);
    renderWithProviders(<AgentTokenCard />, '/settings/agents');
    await waitFor(() => expect(calls.some((c) => c.url.endsWith('/auth/me'))).toBe(true));
    expect(screen.queryByText('服务账号凭据')).toBeNull();
    expect(calls.some((c) => c.url.endsWith('/settings/agents/token'))).toBe(false);
  });
});
