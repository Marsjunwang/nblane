import { fireEvent, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { jsonResponse, renderWithProviders } from '../../test/render';
import { AgentsAndBackupSection, githubLinks } from './AgentSetupSections';

afterEach(() => vi.unstubAllGlobals());

describe('AgentsAndBackupSection', () => {
  it('derives GitHub links only from SSH URLs', () => {
    expect(githubLinks('git@github.com:alice/ws.git')?.deployKeys).toBe('https://github.com/alice/ws/settings/keys/new');
    expect(githubLinks('https://github.com/alice/ws.git')).toBeNull();
  });

  it('walks the backup remote wizard and installs OpenClaw reusing the AI connection', async () => {
    const target = (extra: Record<string, unknown> = {}) => ({
      id: 'openclaw-workspace', label: 'OpenClaw 工作区', description: 'memory', path: '/srv/agent-data/openclaw/workspace', commit_mode: 'all',
      exists: true, is_git: true, remote_url: '', branch: 'main', upstream: '', ahead: 3, dirty: 0, has_commits: true,
      last_commit_at: '', last_commit_subject: '', key_path: '/k', key_ready: false, public_key: '', last_run: {}, ...extra,
    });
    const backup = (t: unknown) => ({ targets: [t], timer: { unit: 'nblane-backup', installed: false, enabled: false, next_run: '', schedule: '每天 03:30' }, backups_dir: '/b', data_git: { autocommit: true, autopush: true } });
    const agent = (extra: Record<string, unknown> = {}) => ({
      installed: false, version: '', pinned_version: '2026.9.4', npm_available: true, node_version: '24.21.0', node_supported: true, profile: '',
      state_dir: '/h/.openclaw', configured: false, workspace: '', workspace_exists: false, workspace_in_agent_root: false, agent_data_root: '/srv/agent-data',
      target_workspace: '/srv/agent-data/openclaw/workspace', gateway_port: 18789, gateway_unit: 'openclaw-gateway.service', gateway_service: '', gateway_reachable: false,
      mcp_registered: false, mcp_profile: '', connected_profile: '', corpus_present: false, weixin_installed: false, weixin_login_command: 'openclaw channels login --channel openclaw-weixin',
      llm_reusable: true, llm_model: 'qwen3.8-flash', llm_base_url: 'https://x', mcp_entry: { command: 'nblane-mcp' },
      job: { kind: '', status: '', phase: '', error: '', log: [], started_at: 0, finished_at: 0 }, ...extra,
    });
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      calls.push({ url, init });
      if (url.endsWith('/auth/me')) return jsonResponse(200, { id: 'admin', display_name: 'Admin', role: 'admin', auth_enabled: true, profiles: [], teams: [] });
      if (url.endsWith('/profiles')) return jsonResponse(200, [{ name: 'alice' }]);
            if (url.endsWith('/targets/openclaw-workspace/key')) return jsonResponse(200, { public_key: 'ssh-ed25519 AAAA nblane', key_path: '/k' });
      if (url.endsWith('/remote/test')) return jsonResponse(200, { ok: true, visibility: 'hidden', reachable: true, writable: true, remote_empty: true, message: '连接正常，仓库为私有，可以保存。' });
      if (url.endsWith('/targets/openclaw-workspace/remote')) return jsonResponse(200, backup(target({ remote_url: 'git@github.com:alice/ws.git', ahead: 0, public_key: 'ssh-ed25519 AAAA nblane' })));
      if (url.endsWith('/settings/backup')) return jsonResponse(200, backup(target()));
      if (url.endsWith('/settings/agents/openclaw/install')) return jsonResponse(200, agent({ job: { kind: 'install', status: 'running', phase: 'npm', error: '', log: ['▶ 安装 OpenClaw 2026.9.4'], started_at: 1, finished_at: 0 } }));
      if (url.endsWith('/settings/agents/openclaw')) return jsonResponse(200, agent());
      return jsonResponse(200, {});
    });

    vi.stubGlobal('fetch', fetchMock);
    renderWithProviders(<AgentsAndBackupSection />, '/settings/agents');
    expect(await screen.findByText('数据备份')).toBeInTheDocument();
    expect(screen.getByText('只在本机')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '添加私有远端' }));
    fireEvent.click(screen.getByRole('button', { name: '生成部署密钥' }));
    expect(await screen.findByText('ssh-ed25519 AAAA nblane')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('仓库 SSH 地址'), { target: { value: 'git@github.com:alice/ws.git' } });
    expect(screen.getByRole('link', { name: '打开这个仓库的 Deploy keys 页面' })).toHaveAttribute('href', 'https://github.com/alice/ws/settings/keys/new');
    fireEvent.click(screen.getByRole('button', { name: '测试连接' }));
    expect(await screen.findByText('连接正常，仓库为私有，可以保存。')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '保存并推送' }));
    expect(await screen.findByText('已同步')).toBeInTheDocument();
    const saveCall = calls.find((call) => call.url.endsWith('/targets/openclaw-workspace/remote'));
    expect(saveCall?.init?.method).toBe('PUT');
    expect(JSON.parse(String(saveCall?.init?.body))).toEqual({ url: 'git@github.com:alice/ws.git' });

    expect(screen.getByText('模型复用 nblane 的 AI 连接（qwen3.8-flash）')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '一键安装 OpenClaw' }));
    expect(await screen.findByText('▶ 安装 OpenClaw 2026.9.4')).toBeInTheDocument();
    const installCall = calls.find((call) => call.url.endsWith('/settings/agents/openclaw/install'));
    expect(JSON.parse(String(installCall?.init?.body))).toEqual({ profile: 'alice', reuse_llm: true });
    expect(installCall?.init?.body).not.toContain('api_key');
  });
});
