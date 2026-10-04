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
});
