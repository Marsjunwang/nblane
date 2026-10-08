import { fireEvent, screen, waitFor, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes, useLocation } from 'react-router-dom';

import { jsonResponse, renderWithProviders } from '../test/render';
import { SettingsPage } from './SettingsPage';

const CONNECTION = { base_url: 'https://api.example.test/v1', model: 'gpt-test', api_key_set: true, configured: true, max_tokens: 8192, analysis_max_tokens: 16384 };

const PROFILE_SETTINGS = {
  profile: 'alice',
  preferences: {
    ai: {
      llm: { ui_lang: 'zh', reply_lang: 'auto' },
      actions: {
        'research.paper_translate': { backend: 'llm', llm_model: 'paper-model', codex_model: '' },
        'evidence.crystallize': { backend: 'codex', llm_model: '', codex_model: 'codex-crystal' },
      },
      local_translation: { selection: 'local', visible: 'local', full: 'ai' },
    },
    research: { reader: { default_mode: 'compare' } },
  },
};

const CODEX_SETTINGS = { profile: 'alice', settings: { bin_path: 'codex', cloud_env_id: '', model: '', branch: '', timeout_seconds: null } };
const CODEX_STATUS = {
  installed: true, bin_path: '/usr/bin/codex', resolved_path: '/usr/bin/codex', version: 'codex 1.0', logged_in: true,
  login_status: 'logged_in', cloud_env_id: '', cloud_env_configured: false, install_command: '', upgrade_command: '', error: '',
};
const AI_CONFIG = { profile: 'alice', actions: [], llm_default_model: 'qwen-plus', codex_default_model: '', codex_model_suggestions: [] };

const localModel = (id: string, tier: string, extra: Record<string, unknown> = {}) => ({
  id, name: id, tier, description: 'desc', repo: 'tencent/x', revision: 'r', filename: `${id}.gguf`, size: 1_130_000_000,
  min_ram_mb: 3072, runtime_ram_mb: 2100, license: 'Apache-2.0', homepage: 'https://example.test', installed: false, active: false,
  install_blocker: '', fits_ram: true, install: { status: '', phase: '', downloaded: 0, total: 0, error: '', started_at: 0 }, ...extra,
});
const LOCAL_MODELS = {
  resources: { total_ram_mb: 3724, available_ram_mb: 1900, free_disk_mb: 17000, models_dir: '/m', cores: 2, avx2: true, avx512: false },
  runtime: { tag: 'b1', installed: true, supported: true },
  server: { running: false, port: 8505, model_id: '', rss_mb: 0, sleeping: false },
  active_model_id: '', active_ready: false,
  models: [localModel('fit', 'fit', { installed: true }), localModel('big', 'quality', { install_blocker: '需要约 7GB 以上内存，当前 3.6GB。', fits_ram: false })],
};
const grobid = (extra: Record<string, unknown> = {}) => ({
  state: 'external', alive: true, version: '0.9.0', url: 'http://127.0.0.1:8070', manageable: true, port: 8070,
  unit: 'nblane-grobid', unit_state: { installed: false, active_state: '', sub_state: '', result: '', memory_mb: 0, since: '', restarts: 0 },
  image: 'docker.io/grobid/grobid:0.9.0-crf', image_present: true, podman_available: true, user_manager: true,
  backend: 'pymupdf', backend_override: '', env_backend: 'pymupdf', total_ram_mb: 3724, available_ram_mb: 900, min_ram_mb: 3072,
  install: { status: '', phase: '', error: '', started_at: 0 }, blocker: '', ...extra,
});

type Call = { url: string; method: string; body: unknown };

function mockApi(role: 'admin' | 'member' = 'admin', overrides: Record<string, (init?: RequestInit) => Response> = {}) {
  const calls: Call[] = [];
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input).replace(/^.*\/api\/v1/, '');
    const method = init?.method ?? 'GET';
    calls.push({ url, method, body: init?.body ? JSON.parse(String(init.body)) : undefined });
    const key = `${method} ${url}`;
    if (overrides[key]) return overrides[key](init);
    if (url === '/auth/me') return jsonResponse(200, { id: role, display_name: role, role, auth_enabled: true, profiles: ['alice'], teams: [] });
    if (url === '/profiles') return jsonResponse(200, [{ name: 'alice' }, { name: 'bob' }]);
    if (role === 'member' && url.startsWith('/settings/') && url !== '/settings/codex/status') return jsonResponse(403, { code: 'admin_required', message: 'no' });
    if (url === '/settings/connection') return jsonResponse(200, CONNECTION);
    if (url === '/settings/codex/status') return jsonResponse(200, CODEX_STATUS);
    if (url === '/settings/local-models') return jsonResponse(200, LOCAL_MODELS);
    if (url === '/settings/local-models/test') return jsonResponse(200, { model_id: 'fit', translated_text: '我们提出了 Transformer。', seconds: 6.2 });
    if (url === '/settings/grobid/backend') return jsonResponse(200, grobid({ backend: 'auto', backend_override: 'auto' }));
    if (url === '/settings/grobid') return jsonResponse(200, grobid());
    if (url.endsWith('/settings/codex')) return jsonResponse(200, CODEX_SETTINGS);
    if (/\/profiles\/\w+\/settings$/.test(url)) return jsonResponse(200, PROFILE_SETTINGS);
    if (url.endsWith('/research/ai-config')) return jsonResponse(200, AI_CONFIG);
    return jsonResponse(404, { code: 'not_found', message: url });
  });
  vi.stubGlobal('fetch', fetchMock);
  return calls;
}

function Where() {
  const location = useLocation();
  return <div data-testid="where">{`${location.pathname}${location.search}`}</div>;
}

function renderAt(route: string) {
  return renderWithProviders(
    <>
      <Routes>
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/settings/:section" element={<SettingsPage />} />
      </Routes>
      <Where />
    </>,
    route,
  );
}

afterEach(() => vi.unstubAllGlobals());

describe('SettingsPage', () => {
  it('sends admins to 系统 · AI 服务 and never fills the API key', async () => {
    mockApi();
    renderAt('/settings');
    expect(await screen.findByDisplayValue('https://api.example.test/v1')).toBeInTheDocument();
    expect(screen.getByTestId('where')).toHaveTextContent('/settings/ai-service?profile=alice');
    expect(screen.getByLabelText('API Key')).toHaveValue('');
    expect(screen.getByText('已安装并登录')).toBeInTheDocument();
    const nav = screen.getByRole('navigation', { name: '设置目录' });
    for (const label of ['AI 服务', '本地服务', '通用', '研究与阅读', 'AI 路由']) expect(nav).toHaveTextContent(label);
  });

  it('saves only the entered API key', async () => {
    const calls = mockApi();
    renderAt('/settings/ai-service');
    await screen.findByDisplayValue('gpt-test');
    fireEvent.change(screen.getByLabelText('API Key'), { target: { value: 'new-secret' } });
    fireEvent.click(screen.getByRole('button', { name: '保存连接' }));
    await waitFor(() => expect(calls.some((call) => call.method === 'PUT' && call.url === '/settings/connection')).toBe(true));
    expect(calls.find((call) => call.method === 'PUT')?.body).toEqual({ base_url: CONNECTION.base_url, model: CONNECTION.model, api_key: 'new-secret', clear_api_key: false, max_tokens: 8192, analysis_max_tokens: 16384 });
  });

  it('hides 系统 from members and never requests deployment settings', async () => {
    const calls = mockApi('member');
    renderAt('/settings/ai-service');
    expect(await screen.findByText('界面语言')).toBeInTheDocument();
    expect(screen.getByTestId('where')).toHaveTextContent('/settings/general');
    expect(screen.getByRole('navigation', { name: '设置目录' })).not.toHaveTextContent('本地服务');
    expect(screen.queryByLabelText('API Key')).not.toBeInTheDocument();
    expect(calls.some((call) => call.url === '/settings/connection' || call.url === '/settings/local-models' || call.url === '/settings/grobid')).toBe(false);
  });

  it('shows one resource bar plus local models and GROBID under 本地服务', async () => {
    const calls = mockApi();
    renderAt('/settings/local-services');
    expect(await screen.findByRole('heading', { name: '本地翻译模型' })).toBeInTheDocument();
    expect(screen.getByText('服务器资源')).toBeInTheDocument();
    expect(screen.getByText('暂不能安装：需要约 7GB 以上内存，当前 3.6GB。')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '翻译' }));
    expect(await screen.findByText('我们提出了 Transformer。')).toBeInTheDocument();
    expect(calls.find((call) => call.url === '/settings/local-models/test')?.body).toMatchObject({ model_id: 'fit' });

    expect(await screen.findByText('运行中（外部服务）')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '停止' })).not.toBeInTheDocument();
    expect(screen.getByText(/未设置：Reader 和 SPA 后端各按自己的启动配置/)).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: '自动' })).not.toBeChecked();
    fireEvent.click(screen.getByRole('radio', { name: '自动' }));
    await waitFor(() => expect(calls.some((call) => call.url === '/settings/grobid/backend')).toBe(true));
    expect(calls.find((call) => call.url === '/settings/grobid/backend')?.body).toEqual({ backend: 'auto' });
  });

  it('edits research settings as a draft and saves one patch from the save bar', async () => {
    const calls = mockApi();
    renderAt('/settings/research?profile=alice');
    expect(await screen.findByDisplayValue('paper-model')).toBeInTheDocument();
    expect(screen.queryByRole('region', { name: '未保存的修改' })).not.toBeInTheDocument();
    // Only customized actions are listed until 「显示全部」.
    expect(screen.queryByRole('textbox', { name: '深度研读模型' })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /显示全部 9 项/ }));
    expect(screen.getByRole('textbox', { name: '深度研读模型' })).toBeInTheDocument();

    fireEvent.click(within(screen.getByRole('radiogroup', { name: '选区翻译翻译方式' })).getByRole('radio', { name: 'AI' }));
    fireEvent.change(screen.getByLabelText('论文翻译模型'), { target: { value: 'qwen-max' } });
    const bar = await screen.findByRole('region', { name: '未保存的修改' });
    fireEvent.click(bar.querySelector('button:last-of-type') as HTMLButtonElement);
    await waitFor(() => expect(calls.some((call) => call.method === 'PATCH')).toBe(true));
    const body = calls.find((call) => call.method === 'PATCH')?.body as { ai: Record<string, unknown>; research: { reader: Record<string, unknown> } };
    expect(body.ai.actions).toMatchObject({ 'research.paper_translate': { backend: 'llm', llm_model: 'qwen-max' } });
    expect(body.ai.local_translation).toEqual({ selection: 'ai', visible: 'local', full: 'ai' });
    expect(body.research.reader.default_mode).toBe('compare');
  });

  it('sets Codex reasoning effort per action and saves it with the model', async () => {
    const calls = mockApi();
    renderAt('/settings/research?profile=alice');
    await screen.findByDisplayValue('paper-model');
    fireEvent.click(screen.getByRole('button', { name: /显示全部 9 项/ }));
    // Effort only applies to Codex actions; API-backed rows say so.
    expect(screen.queryByLabelText('论文翻译推理强度')).not.toBeInTheDocument();
    const effort = screen.getByRole('textbox', { name: '深度研读推理强度' });
    expect(effort).toHaveValue('默认（高）');
    fireEvent.change(screen.getByRole('textbox', { name: '深度研读模型' }), { target: { value: 'gpt-6.1-sol' } });
    fireEvent.click(effort);
    const listbox = await screen.findByRole('listbox', { name: '深度研读推理强度', hidden: true });
    fireEvent.click(within(listbox).getByRole('option', { name: '中', hidden: true }));
    const bar = await screen.findByRole('region', { name: '未保存的修改' });
    fireEvent.click(bar.querySelector('button:last-of-type') as HTMLButtonElement);
    await waitFor(() => expect(calls.some((call) => call.method === 'PATCH')).toBe(true));
    const body = calls.find((call) => call.method === 'PATCH')?.body as { ai: { actions: Record<string, unknown> } };
    expect(body.ai.actions['research.paper_deep_read_codex']).toMatchObject({ codex_model: 'gpt-6.1-sol', codex_effort: 'medium' });
  });

  it('discards edits from the save bar', async () => {
    mockApi();
    renderAt('/settings/research?profile=alice');
    const input = await screen.findByDisplayValue('paper-model');
    fireEvent.change(input, { target: { value: 'other' } });
    fireEvent.click(await screen.findByRole('button', { name: '放弃' }));
    expect(screen.getByLabelText('论文翻译模型')).toHaveValue('paper-model');
    expect(screen.queryByRole('region', { name: '未保存的修改' })).not.toBeInTheDocument();
  });

  it('saves workflow AI and Codex parameters together under AI 路由', async () => {
    const calls = mockApi();
    renderAt('/settings/ai-routing?profile=alice');
    expect(await screen.findByDisplayValue('codex-crystal')).toBeInTheDocument();
    fireEvent.change(screen.getByRole('textbox', { name: '证据结晶模型' }), { target: { value: 'codex-crystal-v2' } });
    fireEvent.change(screen.getByLabelText('超时（秒）'), { target: { value: '90' } });
    fireEvent.click(within(await screen.findByRole('region', { name: '未保存的修改' })).getByRole('button', { name: '保存' }));
    await waitFor(() => expect(calls.filter((call) => call.method === 'PATCH')).toHaveLength(2));
    const prefs = calls.find((call) => call.method === 'PATCH' && call.url === '/profiles/alice/settings')?.body as { ai: { actions: Record<string, unknown> } };
    expect(prefs.ai.actions['evidence.crystallize']).toMatchObject({ backend: 'codex', codex_model: 'codex-crystal-v2' });
    expect(calls.find((call) => call.method === 'PATCH' && call.url === '/profiles/alice/settings/codex')?.body).toMatchObject({ timeout_seconds: 90, bin_path: 'codex' });
  });

  it('asks before leaving a section with unsaved edits', async () => {
    mockApi();
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false);
    renderAt('/settings/research?profile=alice');
    fireEvent.change(await screen.findByDisplayValue('paper-model'), { target: { value: 'other' } });
    await screen.findByRole('region', { name: '未保存的修改' });
    fireEvent.click(within(screen.getByRole('navigation', { name: '设置目录' })).getByText('通用'));
    expect(confirm).toHaveBeenCalled();
    expect(screen.getByTestId('where')).toHaveTextContent('/settings/research');
    confirm.mockRestore();
  });
});
