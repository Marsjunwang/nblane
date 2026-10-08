import { fireEvent, screen, waitFor, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes, useLocation } from 'react-router-dom';

import { RequireAuth } from '../../auth/RequireAuth';
import { jsonResponse, renderWithProviders } from '../../test/render';
import { SettingsPage } from '../SettingsPage';

type Call = { url: string; method: string; body: unknown };

const ACCOUNTS = [
  { id: 'admin', display_name: 'Admin', role: 'admin', profiles: ['alice'], agent: false, disabled: false, must_change_password: false, tokens: [] },
  { id: 'openclaw', display_name: 'OpenClaw', role: 'member', profiles: ['alice'], agent: true, disabled: false, must_change_password: false, tokens: [] },
];

const SCHEMAS = [
  { name: 'autonomous-driving', domain: 'Autonomous Driving Engineer / 自动驾驶工程师', description: '', node_count: 82, source: 'builtin' },
  { name: 'robotics-engineer', domain: 'Robotics Engineer / 机器人与具身智能工程师', description: '', node_count: 82, source: 'builtin' },
];

function mockApi(
  me: Record<string, unknown> = {},
  overrides: Record<string, (init?: RequestInit) => Response> = {},
) {
  const calls: Call[] = [];
  const user = { id: 'admin', display_name: 'Admin', role: 'admin', auth_enabled: true, agent: false, must_change_password: false, profiles: ['alice'], ...me };
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input).replace(/^.*\/api\/v1/, '');
    const method = init?.method ?? 'GET';
    calls.push({ url, method, body: init?.body ? JSON.parse(String(init.body)) : undefined });
    const key = `${method} ${url}`;
    if (overrides[key]) return overrides[key](init);
    if (url === '/auth/me') return jsonResponse(200, user);
    if (url === '/profiles') return jsonResponse(200, [{ name: 'alice' }, { name: 'bob' }]);
    if (key === 'GET /accounts') return jsonResponse(200, ACCOUNTS);
    if (key === 'GET /schemas') return jsonResponse(200, SCHEMAS);
    return jsonResponse(404, { code: 'not_found', message: url });
  }));
  return calls;
}

function Where() {
  const location = useLocation();
  return <div data-testid="where">{location.pathname}</div>;
}

function renderAt(route: string) {
  return renderWithProviders(
    <>
      <Routes>
        <Route path="/elsewhere" element={<RequireAuth><div>elsewhere</div></RequireAuth>} />
        <Route path="/settings/:section" element={<RequireAuth><SettingsPage /></RequireAuth>} />
      </Routes>
      <Where />
    </>,
    route,
  );
}

function fillPasswordForm(current: string, next: string, confirm: string) {
  const form = screen.getByRole('form', { name: '修改密码' });
  fireEvent.change(within(form).getByLabelText(/当前密码/), { target: { value: current } });
  fireEvent.change(within(form).getByLabelText(/^新密码/), { target: { value: next } });
  fireEvent.change(within(form).getByLabelText(/确认新密码/), { target: { value: confirm } });
  fireEvent.click(within(form).getByRole('button', { name: '修改密码' }));
}

afterEach(() => vi.unstubAllGlobals());

describe('我的账号', () => {
  it('changes the password and confirms other sessions are signed out', async () => {
    const calls = mockApi({}, {
      'POST /auth/password': () => jsonResponse(200, { id: 'admin', display_name: 'Admin', role: 'admin', auth_enabled: true, agent: false, must_change_password: false, profiles: [] }),
    });
    renderAt('/settings/account');
    await screen.findByRole('form', { name: '修改密码' });
    fillPasswordForm('old-password', 'new-password-1', 'new-password-1');
    expect(await screen.findByText('密码已修改，其他设备上的登录已失效')).toBeInTheDocument();
    expect(calls.find((call) => call.url === '/auth/password')?.body).toEqual({ current_password: 'old-password', new_password: 'new-password-1' });
  });

  it('checks length and confirmation before calling the API', async () => {
    const calls = mockApi();
    renderAt('/settings/account');
    await screen.findByRole('form', { name: '修改密码' });
    fillPasswordForm('old-password', 'new-password-1', 'new-password-2');
    expect(await screen.findByText('两次输入的新密码不一致')).toBeInTheDocument();
    fillPasswordForm('old-password', 'short', 'short');
    expect(await screen.findByText('新密码至少 10 位')).toBeInTheDocument();
    expect(calls.some((call) => call.url === '/auth/password')).toBe(false);
  });

  it('maps backend error codes to Chinese', async () => {
    mockApi({}, { 'POST /auth/password': () => jsonResponse(422, { code: 'weak_password', message: 'Password must be at least 10 characters.' }) });
    renderAt('/settings/account');
    await screen.findByRole('form', { name: '修改密码' });
    fillPasswordForm('old-password', 'new-password-1', 'new-password-1');
    expect(await screen.findByText('密码至少 10 位')).toBeInTheDocument();
  });

  it('hides the forms in local mode', async () => {
    mockApi({ auth_enabled: false });
    renderAt('/settings/account');
    expect(await screen.findByText(/本地模式未开启登录/)).toBeInTheDocument();
    expect(screen.queryByRole('form', { name: '修改密码' })).not.toBeInTheDocument();
  });
});

describe('账号管理', () => {
  it('is hidden from members', async () => {
    const calls = mockApi({ id: 'bob', role: 'member' });
    renderAt('/settings/accounts');
    const nav = await screen.findByRole('navigation', { name: '设置目录' });
    expect(nav).toHaveTextContent('我的账号');
    expect(nav).not.toHaveTextContent('账号管理');
    expect(calls.some((call) => call.url === '/accounts')).toBe(false);
  });

  it('creates a user with the expected body', async () => {
    const calls = mockApi({}, {
      'POST /accounts': () => jsonResponse(200, { ...ACCOUNTS[0], id: 'carol', role: 'member', must_change_password: true }),
    });
    renderAt('/settings/accounts');
    fireEvent.click(await screen.findByRole('button', { name: '新建用户' }));
    const form = await screen.findByRole('form', { name: '新建用户' });
    fireEvent.change(within(form).getByLabelText(/^用户名/), { target: { value: 'carol' } });
    fireEvent.change(within(form).getByLabelText('显示名'), { target: { value: 'Carol' } });
    fireEvent.change(within(form).getByLabelText(/初始密码/), { target: { value: 'carol-password-1' } });
    expect(within(form).getByText('新用户首次登录必须改密码。')).toBeInTheDocument();
    fireEvent.click(within(form).getByRole('button', { name: '创建' }));
    await waitFor(() => expect(calls.some((call) => call.method === 'POST' && call.url === '/accounts')).toBe(true));
    expect(calls.find((call) => call.method === 'POST' && call.url === '/accounts')?.body).toEqual({
      id: 'carol', display_name: 'Carol', role: 'member', password: 'carol-password-1', profiles: [], create_profile: true,
      schema: 'robotics-engineer',
    });
  });

  it('sends the chosen 领域 and hides it without a new profile', async () => {
    const calls = mockApi({}, {
      'POST /accounts': () => jsonResponse(200, { ...ACCOUNTS[0], id: 'dave', role: 'member', must_change_password: true }),
    });
    renderAt('/settings/accounts');
    fireEvent.click(await screen.findByRole('button', { name: '新建用户' }));
    const form = await screen.findByRole('form', { name: '新建用户' });
    const select = within(form).getByRole('textbox', { name: /领域/ });
    await waitFor(() => expect(select).toHaveValue('Robotics Engineer / 机器人与具身智能工程师（82 个技能）'));
    fireEvent.click(select);
    fireEvent.click(await screen.findByRole('option', { name: /自动驾驶工程师/, hidden: true }));
    fireEvent.change(within(form).getByLabelText(/^用户名/), { target: { value: 'dave' } });
    fireEvent.change(within(form).getByLabelText(/初始密码/), { target: { value: 'dave-password-1' } });
    fireEvent.click(within(form).getByRole('button', { name: '创建' }));
    await waitFor(() => expect(calls.some((call) => call.method === 'POST' && call.url === '/accounts')).toBe(true));
    expect(calls.find((call) => call.method === 'POST' && call.url === '/accounts')?.body).toMatchObject({ create_profile: true, schema: 'autonomous-driving' });
  });

  it('omits the 领域 when no profile is created and maps unknown_schema', async () => {
    const calls = mockApi({}, { 'POST /accounts': () => jsonResponse(422, { code: 'unknown_schema', message: 'Unknown domain schema: x' }) });
    renderAt('/settings/accounts');
    fireEvent.click(await screen.findByRole('button', { name: '新建用户' }));
    const form = await screen.findByRole('form', { name: '新建用户' });
    fireEvent.click(within(form).getByLabelText('同时用模板创建同名档案'));
    expect(within(form).queryByRole('textbox', { name: /领域/ })).not.toBeInTheDocument();
    fireEvent.change(within(form).getByLabelText(/^用户名/), { target: { value: 'erin' } });
    fireEvent.change(within(form).getByLabelText(/初始密码/), { target: { value: 'erin-password-1' } });
    fireEvent.click(within(form).getByRole('button', { name: '创建' }));
    expect(await screen.findByText('领域模板不存在')).toBeInTheDocument();
    expect(calls.find((call) => call.method === 'POST' && call.url === '/accounts')?.body).toMatchObject({ create_profile: false, schema: '' });
  });

  it('maps user_exists on create', async () => {
    mockApi({}, { 'POST /accounts': () => jsonResponse(409, { code: 'user_exists', message: 'User already exists: admin' }) });
    renderAt('/settings/accounts');
    fireEvent.click(await screen.findByRole('button', { name: '新建用户' }));
    const form = await screen.findByRole('form', { name: '新建用户' });
    fireEvent.change(within(form).getByLabelText(/^用户名/), { target: { value: 'admin' } });
    fireEvent.change(within(form).getByLabelText(/初始密码/), { target: { value: 'whatever-pass' } });
    fireEvent.click(within(form).getByRole('button', { name: '创建' }));
    expect(await screen.findByText('用户名已存在')).toBeInTheDocument();
  });

  it('shows the token plaintext once; no disable on self, no password reset on agents', async () => {
    const calls = mockApi({}, {
      'POST /accounts/openclaw/tokens': () => jsonResponse(200, { token: 'nbl_secret_plain', id: 't1', name: 'openclaw', created: '2026-10-08' }),
    });
    renderAt('/settings/accounts');
    const selfCard = await screen.findByRole('region', { name: '账号 admin' });
    expect(within(selfCard).queryByRole('button', { name: '停用' })).not.toBeInTheDocument();
    const agentCard = screen.getByRole('region', { name: '账号 openclaw' });
    expect(within(agentCard).queryByRole('button', { name: '重置密码' })).not.toBeInTheDocument();
    fireEvent.click(within(agentCard).getByRole('button', { name: '生成 token' }));
    const form = await screen.findByRole('form', { name: '生成 token' });
    fireEvent.change(within(form).getByLabelText(/名称/), { target: { value: 'openclaw' } });
    fireEvent.click(within(form).getByRole('button', { name: '生成' }));
    expect(await screen.findByTestId('token-plaintext')).toHaveTextContent('nbl_secret_plain');
    expect(screen.getByText('只显示这一次')).toBeInTheDocument();
    expect(calls.find((call) => call.url === '/accounts/openclaw/tokens')?.body).toEqual({ name: 'openclaw' });
    fireEvent.click(screen.getByRole('button', { name: '我已保存' }));
    await waitFor(() => expect(screen.queryByText('nbl_secret_plain')).not.toBeInTheDocument());
  });
});

describe('forced password change', () => {
  it('redirects to /settings/account and shows the banner', async () => {
    mockApi({ must_change_password: true });
    renderAt('/settings/ai-service');
    expect(await screen.findByText('首次登录或密码被重置，请先修改密码')).toBeInTheDocument();
    expect(screen.getAllByTestId('where').at(-1)).toHaveTextContent('/settings/account');
  });

  it('redirects other routes too', async () => {
    mockApi({ must_change_password: true });
    renderAt('/elsewhere');
    await waitFor(() => expect(screen.getAllByTestId('where').at(-1)).toHaveTextContent('/settings/account'));
  });
});
