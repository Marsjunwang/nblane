import { fireEvent, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';

import { jsonResponse, renderWithProviders } from '../test/render';
import { SettingsPage } from './SettingsPage';

const CONNECTION = {
  base_url: 'https://api.example.test/v1',
  model: 'gpt-test',
  api_key_set: true,
  configured: true,
};

const PROFILE_SETTINGS = {
  profile: 'alice',
  preferences: {
    ai: {
      llm: { ui_lang: 'zh', reply_lang: 'auto' },
      paper: { translation_backend: 'llm', translation_model: 'paper-model' },
      kanban_backend: 'codex',
    },
  },
};

const CODEX_SETTINGS = {
  profile: 'alice',
  settings: { bin_path: 'codex', cloud_env_id: 'env-1', model: 'codex-model', branch: 'main', timeout_seconds: 60 },
};

const CODEX_STATUS = {
  installed: true,
  bin_path: '/usr/bin/codex',
  resolved_path: '/usr/bin/codex',
  version: 'codex 1.0',
  logged_in: true,
  login_status: 'logged_in',
  cloud_env_id: 'env-1',
  cloud_env_configured: true,
  install_command: '',
  upgrade_command: '',
  error: '',
};

function renderPage(fetchImpl: typeof fetch) {
  vi.stubGlobal('fetch', fetchImpl);
  return renderWithProviders(
    <Routes>
      <Route path="/settings" element={<SettingsPage />} />
    </Routes>,
    '/settings',
  );
}

afterEach(() => vi.unstubAllGlobals());

describe('SettingsPage', () => {
  it('loads admin settings without putting the API key into the input', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith('/auth/me')) return jsonResponse(200, { id: 'admin', display_name: 'Admin', role: 'admin', auth_enabled: true, profiles: [], teams: [] });
      if (url.endsWith('/profiles')) return jsonResponse(200, [{ name: 'alice' }]);
      if (url.endsWith('/settings/connection')) return jsonResponse(200, CONNECTION);
      if (url.endsWith('/profiles/alice/settings')) return jsonResponse(200, PROFILE_SETTINGS);
      if (url.endsWith('/profiles/alice/settings/codex')) return jsonResponse(200, CODEX_SETTINGS);
      if (url.endsWith('/settings/codex/status')) return jsonResponse(200, CODEX_STATUS);
      return jsonResponse(404, { code: 'not_found', message: url });
    });

    renderPage(fetchMock);

    expect(await screen.findByDisplayValue('https://api.example.test/v1')).toBeInTheDocument();
    expect(screen.getByDisplayValue('gpt-test')).toBeInTheDocument();
    expect(screen.getByLabelText('API Key')).toHaveValue('');
    expect(screen.getByText('服务端已保存 Key；留空表示保留现有值。')).toBeInTheDocument();
    expect(screen.getByText('已安装并登录')).toBeInTheDocument();
  });

  it('sends only the entered API key and profile preference patch', async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      calls.push({ url, init });
      if (url.endsWith('/auth/me')) return jsonResponse(200, { id: 'admin', display_name: 'Admin', role: 'admin', auth_enabled: true, profiles: [], teams: [] });
      if (url.endsWith('/profiles')) return jsonResponse(200, [{ name: 'alice' }]);
      if (url.endsWith('/settings/connection')) return jsonResponse(200, CONNECTION);
      if (url.endsWith('/profiles/alice/settings')) return jsonResponse(200, PROFILE_SETTINGS);
      if (url.endsWith('/profiles/alice/settings/codex')) return jsonResponse(200, CODEX_SETTINGS);
      if (url.endsWith('/settings/codex/status')) return jsonResponse(200, CODEX_STATUS);
      if (url.endsWith('/settings/connection') && init?.method === 'PUT') return jsonResponse(200, CONNECTION);
      return jsonResponse(404, { code: 'not_found', message: url });
    });

    renderPage(fetchMock);
    await screen.findByDisplayValue('gpt-test');
    fireEvent.change(screen.getByLabelText('API Key'), { target: { value: 'new-secret' } });
    fireEvent.click(screen.getByRole('button', { name: '保存连接' }));

    await waitFor(() => expect(calls.some((call) => call.init?.method === 'PUT')).toBe(true));
    const put = calls.find((call) => call.init?.method === 'PUT');
    expect(JSON.parse(String(put?.init?.body))).toEqual({
      base_url: CONNECTION.base_url,
      model: CONNECTION.model,
      api_key: 'new-secret',
      clear_api_key: false,
    });
  });

  it('does not request or expose deployment connection controls to a member', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith('/auth/me')) return jsonResponse(200, { id: 'member', display_name: 'Member', role: 'member', auth_enabled: true, profiles: ['alice'], teams: [] });
      if (url.endsWith('/profiles')) return jsonResponse(200, [{ name: 'alice' }]);
      if (url.endsWith('/profiles/alice/settings')) return jsonResponse(200, PROFILE_SETTINGS);
      if (url.endsWith('/profiles/alice/settings/codex')) return jsonResponse(200, CODEX_SETTINGS);
      if (url.endsWith('/settings/codex/status')) return jsonResponse(200, CODEX_STATUS);
      return jsonResponse(500, { code: 'unexpected', message: `unexpected request: ${url}` });
    });

    renderPage(fetchMock);
    expect(await screen.findByText('部署连接由管理员管理')).toBeInTheDocument();
    expect(screen.queryByLabelText('API Key')).not.toBeInTheDocument();
    expect(fetchMock.mock.calls.some(([input]) => String(input).endsWith('/settings/connection'))).toBe(false);
  });

  it('loads and saves the evidence crystallize action with the selected backend model', async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    const profileSettings = {
      ...PROFILE_SETTINGS,
      preferences: {
        ...PROFILE_SETTINGS.preferences,
        ai: {
          ...PROFILE_SETTINGS.preferences.ai,
      actions: {
            'research.paper_translate': { backend: 'llm', llm_model: 'paper-model' },
            'research.paper_explain_selection': { backend: 'codex', codex_model: 'paper-explain' },
            'research.paper_qa': { backend: 'llm', llm_model: 'paper-qa' },
            'research.paper_deep_read_codex': { backend: 'codex', codex_model: 'paper-deep' },
            'evidence.crystallize': { backend: 'codex', codex_model: 'codex-crystal' },
          },
        },
      },
    };
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      calls.push({ url, init });
      if (url.endsWith('/auth/me')) return jsonResponse(200, { id: 'admin', display_name: 'Admin', role: 'admin', auth_enabled: true, profiles: [], teams: [] });
      if (url.endsWith('/profiles')) return jsonResponse(200, [{ name: 'alice' }]);
      if (url.endsWith('/settings/connection')) return jsonResponse(200, CONNECTION);
      if (url.endsWith('/profiles/alice/settings') && init?.method === 'PATCH') return jsonResponse(200, profileSettings);
      if (url.endsWith('/profiles/alice/settings')) return jsonResponse(200, profileSettings);
      if (url.endsWith('/profiles/alice/settings/codex')) return jsonResponse(200, CODEX_SETTINGS);
      if (url.endsWith('/settings/codex/status')) return jsonResponse(200, CODEX_STATUS);
      return jsonResponse(404, { code: 'not_found', message: url });
    });

    renderPage(fetchMock);

    expect(await screen.findByDisplayValue('codex-crystal')).toBeInTheDocument();
    expect(screen.getByDisplayValue('paper-model')).toBeInTheDocument();
    expect(screen.getByDisplayValue('paper-explain')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('证据结晶模型'), { target: { value: 'codex-crystal-v2' } });
    fireEvent.click(screen.getByRole('button', { name: '保存档案偏好' }));

    await waitFor(() => expect(calls.some((call) => call.url.endsWith('/profiles/alice/settings') && call.init?.method === 'PATCH')).toBe(true));
    const patchCall = calls.find((call) => call.url.endsWith('/profiles/alice/settings') && call.init?.method === 'PATCH');
    const body = JSON.parse(String(patchCall?.init?.body));
    expect(body.ai.actions['evidence.crystallize']).toEqual({ backend: 'codex', model: 'codex-crystal-v2' });
  });

  it('installs, enables and trial-translates a local model', async () => {
    const model = (id: string, tier: string, extra: Record<string, unknown> = {}) => ({
      id, name: id, tier, description: 'desc', repo: 'tencent/x', revision: 'r', filename: `${id}.gguf`, size: 1_130_000_000,
      min_ram_mb: 3072, runtime_ram_mb: 2100, license: 'Apache-2.0', homepage: 'https://example.test', installed: false, active: false,
      install_blocker: '', fits_ram: true, install: { status: '', phase: '', downloaded: 0, total: 0, error: '', started_at: 0 }, ...extra,
    });
    const status = (models: unknown[]) => ({
      resources: { total_ram_mb: 3724, available_ram_mb: 1900, free_disk_mb: 17000, models_dir: '/m', cores: 2, avx2: true, avx512: false },
      runtime: { tag: 'b1', installed: true, supported: true },
      server: { running: false, port: 8505, model_id: '', rss_mb: 0, sleeping: false },
      active_model_id: '', active_ready: false, models,
    });
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      calls.push({ url, init });
      if (url.endsWith('/auth/me')) return jsonResponse(200, { id: 'admin', display_name: 'Admin', role: 'admin', auth_enabled: true, profiles: [], teams: [] });
      if (url.endsWith('/profiles')) return jsonResponse(200, [{ name: 'alice' }]);
      if (url.endsWith('/settings/connection')) return jsonResponse(200, CONNECTION);
      if (url.endsWith('/settings/local-models/fit/install')) return jsonResponse(200, status([model('fit', 'fit', { install: { status: 'running', phase: 'model', downloaded: 565_000_000, total: 1_130_000_000, error: '', started_at: 1 } }), model('big', 'quality')]));
      if (url.endsWith('/settings/local-models/test')) return jsonResponse(200, { model_id: 'fit', translated_text: '我们提出了 Transformer。', seconds: 6.2 });
      if (url.endsWith('/settings/local-models')) return jsonResponse(200, status([
        model('fit', 'fit', { installed: true }),
        model('big', 'quality', { install_blocker: '需要约 7GB 以上内存，当前 3.6GB。', fits_ram: false }),
      ]));
      if (url.endsWith('/profiles/alice/settings')) return jsonResponse(200, PROFILE_SETTINGS);
      if (url.endsWith('/profiles/alice/settings/codex')) return jsonResponse(200, CODEX_SETTINGS);
      if (url.endsWith('/settings/codex/status')) return jsonResponse(200, CODEX_STATUS);
      return jsonResponse(404, { code: 'not_found', message: url });
    });

    renderPage(fetchMock);
    expect(await screen.findByText('本地翻译模型')).toBeInTheDocument();
    expect(screen.getByText('暂不能安装：需要约 7GB 以上内存，当前 3.6GB。')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '安装' })).toBeDisabled();
    fireEvent.click(screen.getByRole('button', { name: '翻译' }));
    expect(await screen.findByText('我们提出了 Transformer。')).toBeInTheDocument();
    const testCall = calls.find((call) => call.url.endsWith('/settings/local-models/test'));
    expect(JSON.parse(String(testCall?.init?.body)).model_id).toBe('fit');
    expect(screen.getByRole('radiogroup', { name: '全文翻译翻译方式' })).toBeInTheDocument();
  });
});
