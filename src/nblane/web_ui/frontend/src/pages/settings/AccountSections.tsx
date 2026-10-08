// 账号 · 我的账号 (everyone) and 系统 · 账号管理 (admin): password changes,
// sign-out everywhere, user CRUD and agent API tokens. users.yaml is only
// written by the backend (core/auth_store.py); nothing here is cached
// beyond the account list, and token plaintext lives only in modal state.

import {
  Alert,
  Badge,
  Button,
  Card,
  Center,
  Checkbox,
  Code,
  CopyButton,
  Group,
  Loader,
  Modal,
  MultiSelect,
  PasswordInput,
  SegmentedControl,
  Select,
  Stack,
  Text,
  TextInput,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconCheck, IconCopy, IconDice5, IconKey, IconLock, IconLogout, IconUserCircle, IconUserPlus, IconUsers } from '@tabler/icons-react';
import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';

import { ApiError } from '../../api/client';
import {
  useAccounts,
  useChangePassword,
  useCreateAccount,
  useCreateAccountToken,
  useLogoutAll,
  useMe,
  useProfiles,
  useResetAccountPassword,
  useRevokeAccountToken,
  useSchemas,
  useUpdateAccount,
} from '../../api/hooks';
import type { AccountInfo, TokenCreateResult } from '../../api/types';
import { SettingsCard } from './shared';

export const MIN_PASSWORD_LENGTH = 10;
/** Template default domain (profiles/template/skill-tree.yaml). */
const DEFAULT_SCHEMA = 'robotics-engineer';

const ERROR_TEXT: Record<string, string> = {
  user_exists: '用户名已存在',
  profile_exists: '同名档案已存在',
  unknown_schema: '领域模板不存在',
  cannot_disable_self: '不能停用自己',
  cannot_demote_self: '不能取消自己的管理员',
  last_admin: '至少要保留一个可登录的管理员',
  weak_password: `密码至少 ${MIN_PASSWORD_LENGTH} 位`,
  // Mirrors core/auth_store._validate_user_id (validate_profile_name + no whitespace).
  invalid_user_id: '用户名不能为空，也不能含空格、/、\\ 或控制字符，且不能是 . 或 ..',
  invalid_current_password: '当前密码不对',
  auth_not_configured: '未开启登录（本地模式无需账号）',
  rate_limited: '尝试次数过多，请稍后再试',
  user_not_found: '账号不存在',
};

/** Chinese message for a backend error code; falls back to the server text. */
export function accountErrorText(error: unknown): string {
  if (error instanceof ApiError && ERROR_TEXT[error.code]) return ERROR_TEXT[error.code];
  return error instanceof Error ? error.message : String(error);
}

function ErrorText({ error }: { error: unknown }) {
  if (!error) return null;
  return <Alert color="red" title="操作失败">{accountErrorText(error)}</Alert>;
}

/** 16 chars from an unambiguous alphabet, via crypto.getRandomValues. */
export function randomPassword(length = 16): string {
  const alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789';
  const bytes = new Uint32Array(length);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (value) => alphabet[value % alphabet.length]).join('');
}

const ROLE_LABEL: Record<string, string> = { admin: '管理员', member: '成员' };

function PasswordField({ label, value, onChange, generate }: { label: string; value: string; onChange: (value: string) => void; generate?: boolean }) {
  return (
    <Group gap="xs" align="flex-end" wrap="nowrap">
      <PasswordInput
        style={{ flex: 1 }}
        label={label}
        description={`至少 ${MIN_PASSWORD_LENGTH} 位`}
        value={value}
        onChange={(event) => onChange(event.currentTarget.value)}
        autoComplete="new-password"
        required
      />
      {generate && (
        <Button variant="light" leftSection={<IconDice5 size={16} />} onClick={() => onChange(randomPassword())}>随机生成</Button>
      )}
    </Group>
  );
}

// ---------------------------------------------------------------- 我的账号

function ChangePasswordCard() {
  const change = useChangePassword();
  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [confirm, setConfirm] = useState('');
  const [localError, setLocalError] = useState('');

  const submit = (event: FormEvent) => {
    event.preventDefault();
    setLocalError('');
    change.reset();
    if (next.length < MIN_PASSWORD_LENGTH) { setLocalError(`新密码至少 ${MIN_PASSWORD_LENGTH} 位`); return; }
    if (next !== confirm) { setLocalError('两次输入的新密码不一致'); return; }
    change.mutate({ current_password: current, new_password: next }, {
      onSuccess: () => {
        setCurrent(''); setNext(''); setConfirm('');
        notifications.show({ title: '密码已修改', message: '密码已修改，其他设备上的登录已失效', color: 'green' });
      },
    });
  };

  return (
    <SettingsCard icon={<IconLock size={22} />} title="修改密码" description="修改后，其他设备上的登录会失效，当前设备保持登录。">
      <form onSubmit={submit} aria-label="修改密码">
        <Stack gap="sm">
          <PasswordInput label="当前密码" value={current} onChange={(event) => setCurrent(event.currentTarget.value)} autoComplete="current-password" required />
          <PasswordInput label="新密码" description={`至少 ${MIN_PASSWORD_LENGTH} 位`} value={next} onChange={(event) => setNext(event.currentTarget.value)} autoComplete="new-password" required />
          <PasswordInput label="确认新密码" value={confirm} onChange={(event) => setConfirm(event.currentTarget.value)} autoComplete="new-password" required />
          {localError && <Alert color="red" title="请检查输入">{localError}</Alert>}
          <ErrorText error={change.error} />
          <Group><Button type="submit" loading={change.isPending}>修改密码</Button></Group>
        </Stack>
      </form>
    </SettingsCard>
  );
}

function LogoutAllCard() {
  const logoutAll = useLogoutAll();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  return (
    <SettingsCard icon={<IconLogout size={22} />} title="登出所有设备" description="让这个账号在所有浏览器和设备上的登录全部失效，包括当前这个。">
      <Group><Button color="red" variant="light" onClick={() => setOpen(true)}>登出所有设备</Button></Group>
      <ErrorText error={logoutAll.error} />
      <Modal opened={open} onClose={() => setOpen(false)} title="登出所有设备？" centered>
        <Stack gap="md">
          <Text size="sm">所有设备（包括当前设备）都需要重新登录。</Text>
          <Group justify="flex-end">
            <Button variant="default" onClick={() => setOpen(false)}>取消</Button>
            <Button color="red" loading={logoutAll.isPending} onClick={() => logoutAll.mutate(undefined, { onSuccess: () => navigate('/login', { replace: true }) })}>确认登出</Button>
          </Group>
        </Stack>
      </Modal>
    </SettingsCard>
  );
}

export function MyAccountSection() {
  const me = useMe();
  if (!me.data) return null;
  const user = me.data;
  return (
    <Stack gap="lg">
      {user.auth_enabled && user.must_change_password && (
        <Alert color="yellow" title="需要修改密码">首次登录或密码被重置，请先修改密码</Alert>
      )}
      <SettingsCard icon={<IconUserCircle size={22} />} title="当前账号" description="登录用的用户名和显示名。">
        <Group gap="xs">
          <Code>{user.id}</Code>
          <Text size="sm">{user.display_name}</Text>
          <Badge variant="light" color={user.role === 'admin' ? 'yellow' : 'gray'}>{ROLE_LABEL[user.role] ?? user.role}</Badge>
          {user.agent && <Badge variant="light" color="cyan">助手</Badge>}
        </Group>
      </SettingsCard>
      {user.auth_enabled ? (
        <>
          <ChangePasswordCard />
          <LogoutAllCard />
        </>
      ) : (
        <Alert color="gray" title="本地模式">本地模式未开启登录，无需账号和密码。设置 NBLANE_AUTH_FILE 后才会启用登录。</Alert>
      )}
    </Stack>
  );
}

// ---------------------------------------------------------------- 账号管理

function useProfileOptions() {
  const profiles = useProfiles();
  return (profiles.data ?? []).map((item) => ({ value: item.name, label: item.name }));
}

function CreateAccountModal({ opened, onClose }: { opened: boolean; onClose: () => void }) {
  const create = useCreateAccount();
  const profileOptions = useProfileOptions();
  const [id, setId] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [role, setRole] = useState('member');
  const [password, setPassword] = useState('');
  const [createProfile, setCreateProfile] = useState(true);
  const [profiles, setProfiles] = useState<string[]>([]);
  const [schema, setSchema] = useState<string | null>(null);
  const [localError, setLocalError] = useState('');
  const schemas = useSchemas(opened);
  const schemaOptions = (schemas.data ?? []).map((item) => ({
    value: item.name,
    label: `${item.domain}（${item.node_count} 个技能）`,
  }));
  // Default to robotics-engineer (the template's domain) when offered.
  const fallbackSchema = schemaOptions.find((item) => item.value === DEFAULT_SCHEMA)?.value ?? schemaOptions[0]?.value ?? null;
  const chosenSchema = schema ?? fallbackSchema;

  const close = () => {
    setId(''); setDisplayName(''); setRole('member'); setPassword(''); setCreateProfile(true); setProfiles([]); setSchema(null); setLocalError('');
    create.reset();
    onClose();
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    setLocalError('');
    if (!id.trim()) { setLocalError('请填写用户名'); return; }
    if (password.length < MIN_PASSWORD_LENGTH) { setLocalError(`初始密码至少 ${MIN_PASSWORD_LENGTH} 位`); return; }
    create.mutate(
      {
        id: id.trim(),
        display_name: displayName.trim(),
        role,
        password,
        profiles,
        create_profile: createProfile,
        schema: createProfile && chosenSchema ? chosenSchema : '',
      },
      {
        onSuccess: (account) => {
          notifications.show({ title: '用户已创建', message: `${account.id} 首次登录时需要修改密码`, color: 'green' });
          close();
        },
      },
    );
  };

  return (
    <Modal opened={opened} onClose={close} title="新建用户" centered>
      <form onSubmit={submit} aria-label="新建用户">
        <Stack gap="sm">
          <TextInput label="用户名" description="登录用，创建后不能修改" value={id} onChange={(event) => setId(event.currentTarget.value)} required />
          <TextInput label="显示名" value={displayName} onChange={(event) => setDisplayName(event.currentTarget.value)} />
          <Stack gap={4}>
            <Text size="sm" fw={500} id="create-account-role">角色</Text>
            <SegmentedControl aria-labelledby="create-account-role" value={role} onChange={setRole} data={[{ value: 'member', label: '成员' }, { value: 'admin', label: '管理员' }]} />
          </Stack>
          <PasswordField label="初始密码" value={password} onChange={setPassword} generate />
          <Checkbox label="同时用模板创建同名档案" checked={createProfile} onChange={(event) => setCreateProfile(event.currentTarget.checked)} />
          {createProfile && (
            <Select
              label="领域"
              description="档案技能树用哪个领域模板；以后可在 skill-tree.yaml 的 schema 字段修改"
              data={schemaOptions}
              value={chosenSchema}
              onChange={setSchema}
              allowDeselect={false}
              disabled={schemas.isLoading}
              placeholder={schemas.isLoading ? '加载中…' : '模板默认'}
            />
          )}
          <MultiSelect label="可访问的已有档案" placeholder="可不选" data={profileOptions} value={profiles} onChange={setProfiles} searchable clearable />
          <Text size="xs" c="dimmed">新用户首次登录必须改密码。</Text>
          {localError && <Alert color="red" title="请检查输入">{localError}</Alert>}
          <ErrorText error={create.error} />
          <Group justify="flex-end">
            <Button variant="default" onClick={close}>取消</Button>
            <Button type="submit" loading={create.isPending}>创建</Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}

function ResetPasswordModal({ account, onClose }: { account: AccountInfo; onClose: () => void }) {
  const reset = useResetAccountPassword();
  const [password, setPassword] = useState('');
  const [localError, setLocalError] = useState('');
  const submit = (event: FormEvent) => {
    event.preventDefault();
    setLocalError('');
    if (password.length < MIN_PASSWORD_LENGTH) { setLocalError(`新密码至少 ${MIN_PASSWORD_LENGTH} 位`); return; }
    reset.mutate({ id: account.id, password }, {
      onSuccess: () => {
        notifications.show({ title: '密码已重置', message: `${account.id} 的旧登录已失效，下次登录需要改密码`, color: 'green' });
        onClose();
      },
    });
  };
  return (
    <Modal opened onClose={onClose} title={`重置 ${account.id} 的密码`} centered>
      <form onSubmit={submit} aria-label="重置密码">
        <Stack gap="sm">
          <PasswordField label="新密码" value={password} onChange={setPassword} generate />
          <Text size="xs" c="dimmed">重置后该账号所有设备都会掉线，下次登录必须改密码。把新密码通过安全渠道告诉对方。</Text>
          {localError && <Alert color="red" title="请检查输入">{localError}</Alert>}
          <ErrorText error={reset.error} />
          <Group justify="flex-end">
            <Button variant="default" onClick={onClose}>取消</Button>
            <Button type="submit" loading={reset.isPending}>重置密码</Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}

function EditAccountModal({ account, isSelf, onClose }: { account: AccountInfo; isSelf: boolean; onClose: () => void }) {
  const update = useUpdateAccount();
  const profileOptions = useProfileOptions();
  const [displayName, setDisplayName] = useState(account.display_name);
  const [role, setRole] = useState(account.role);
  const [profiles, setProfiles] = useState<string[]>(account.profiles ?? []);
  // Keep profiles the account already has even if the list does not show them.
  const options = [...profileOptions, ...(account.profiles ?? []).filter((name) => !profileOptions.some((item) => item.value === name)).map((name) => ({ value: name, label: name }))];
  const submit = (event: FormEvent) => {
    event.preventDefault();
    update.mutate(
      { id: account.id, patch: { display_name: displayName.trim(), profiles, ...(account.agent ? {} : { role }) } },
      { onSuccess: () => { notifications.show({ title: '已保存', message: account.id, color: 'green' }); onClose(); } },
    );
  };
  return (
    <Modal opened onClose={onClose} title={`编辑 ${account.id}`} centered>
      <form onSubmit={submit} aria-label="编辑账号">
        <Stack gap="sm">
          <TextInput label="显示名" value={displayName} onChange={(event) => setDisplayName(event.currentTarget.value)} />
          {!account.agent && (
            <Stack gap={4}>
              <Text size="sm" fw={500} id="edit-account-role">角色</Text>
              <SegmentedControl aria-labelledby="edit-account-role" disabled={isSelf} value={role} onChange={setRole} data={[{ value: 'member', label: '成员' }, { value: 'admin', label: '管理员' }]} />
              {isSelf && <Text size="xs" c="dimmed">不能修改自己的角色。</Text>}
            </Stack>
          )}
          <MultiSelect label="可访问的档案" data={options} value={profiles} onChange={setProfiles} searchable clearable />
          <ErrorText error={update.error} />
          <Group justify="flex-end">
            <Button variant="default" onClick={onClose}>取消</Button>
            <Button type="submit" loading={update.isPending}>保存</Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}

function ConfirmModal({ title, body, confirmLabel, color = 'red', loading, error, onConfirm, onClose }: { title: string; body: string; confirmLabel: string; color?: string; loading: boolean; error: unknown; onConfirm: () => void; onClose: () => void }) {
  return (
    <Modal opened onClose={onClose} title={title} centered>
      <Stack gap="md">
        <Text size="sm">{body}</Text>
        <ErrorText error={error} />
        <Group justify="flex-end">
          <Button variant="default" onClick={onClose}>取消</Button>
          <Button color={color} loading={loading} onClick={onConfirm}>{confirmLabel}</Button>
        </Group>
      </Stack>
    </Modal>
  );
}

function CreateTokenModal({ account, onClose }: { account: AccountInfo; onClose: () => void }) {
  const create = useCreateAccountToken();
  const [name, setName] = useState('');
  const [result, setResult] = useState<TokenCreateResult | null>(null);
  const submit = (event: FormEvent) => {
    event.preventDefault();
    create.mutate({ id: account.id, name: name.trim() }, { onSuccess: setResult });
  };
  return (
    <Modal opened onClose={onClose} title={result ? 'Token 已生成' : `给 ${account.id} 生成 token`} centered closeOnClickOutside={!result}>
      {result ? (
        <Stack gap="sm">
          <Alert color="yellow" title="只显示这一次">关闭后无法再次查看，请现在复制并保存到助手的配置里。</Alert>
          <Group gap="xs" wrap="nowrap" align="flex-start">
            <Code block style={{ flex: 1, wordBreak: 'break-all', whiteSpace: 'pre-wrap' }} data-testid="token-plaintext">{result.token}</Code>
            <CopyButton value={result.token}>
              {({ copied, copy }) => <Button size="xs" variant="light" leftSection={copied ? <IconCheck size={14} /> : <IconCopy size={14} />} onClick={copy}>{copied ? '已复制' : '复制'}</Button>}
            </CopyButton>
          </Group>
          <Group justify="flex-end"><Button onClick={onClose}>我已保存</Button></Group>
        </Stack>
      ) : (
        <form onSubmit={submit} aria-label="生成 token">
          <Stack gap="sm">
            <TextInput label="名称" description="用来区分用途，例如 openclaw" value={name} onChange={(event) => setName(event.currentTarget.value)} required />
            <ErrorText error={create.error} />
            <Group justify="flex-end">
              <Button variant="default" onClick={onClose}>取消</Button>
              <Button type="submit" loading={create.isPending}>生成</Button>
            </Group>
          </Stack>
        </form>
      )}
    </Modal>
  );
}

type Dialog =
  | { kind: 'reset' | 'edit' | 'toggle' | 'token'; account: AccountInfo }
  | { kind: 'revoke'; account: AccountInfo; tokenId: string; tokenName: string };

function AccountCard({ account, isSelf, onOpen }: { account: AccountInfo; isSelf: boolean; onOpen: (dialog: Dialog) => void }) {
  const tokens = account.tokens ?? [];
  return (
    <Card withBorder radius="md" padding="sm" aria-label={`账号 ${account.id}`} component="section">
      <Stack gap="xs">
        <Group justify="space-between" wrap="wrap" gap="xs">
          <Group gap="xs">
            <Code>{account.id}</Code>
            {account.display_name && account.display_name !== account.id && <Text size="sm">{account.display_name}</Text>}
            {account.agent
              ? <Badge variant="light" color="cyan">助手</Badge>
              : <Badge variant="light" color={account.role === 'admin' ? 'yellow' : 'gray'}>{ROLE_LABEL[account.role] ?? account.role}</Badge>}
            {account.disabled && <Badge variant="light" color="red">已停用</Badge>}
            {account.must_change_password && <Badge variant="light" color="orange">需改密码</Badge>}
            {isSelf && <Badge variant="outline" color="gray">你</Badge>}
          </Group>
          <Group gap={6}>
            <Button size="compact-xs" variant="light" onClick={() => onOpen({ kind: 'edit', account })}>编辑</Button>
            {!account.agent && <Button size="compact-xs" variant="light" onClick={() => onOpen({ kind: 'reset', account })}>重置密码</Button>}
            {!isSelf && (
              <Button size="compact-xs" variant="light" color={account.disabled ? 'green' : 'red'} onClick={() => onOpen({ kind: 'toggle', account })}>
                {account.disabled ? '启用' : '停用'}
              </Button>
            )}
          </Group>
        </Group>
        <Text size="xs" c="dimmed">档案：{(account.profiles ?? []).length ? (account.profiles ?? []).join('、') : '无'}</Text>
        {account.agent && (
          <Stack gap={4}>
            <Group justify="space-between">
              <Text size="xs" fw={600}>API token</Text>
              <Button size="compact-xs" variant="light" leftSection={<IconKey size={12} />} onClick={() => onOpen({ kind: 'token', account })}>生成 token</Button>
            </Group>
            {tokens.length === 0 && <Text size="xs" c="dimmed">还没有 token。</Text>}
            {tokens.map((token) => (
              <Group key={token.id} justify="space-between" gap="xs" wrap="nowrap">
                <Text size="xs">{token.name || token.id} <Text span c="dimmed" size="xs">{token.created}</Text></Text>
                <Button size="compact-xs" variant="subtle" color="red" aria-label={`撤销 token ${token.name || token.id}`} onClick={() => onOpen({ kind: 'revoke', account, tokenId: token.id, tokenName: token.name || token.id })}>撤销</Button>
              </Group>
            ))}
          </Stack>
        )}
      </Stack>
    </Card>
  );
}

function ToggleModal({ account, onClose }: { account: AccountInfo; onClose: () => void }) {
  const update = useUpdateAccount();
  const disabling = !account.disabled;
  return (
    <ConfirmModal
      title={disabling ? `停用 ${account.id}？` : `启用 ${account.id}？`}
      body={disabling ? '停用后该账号立即掉线，无法登录，token 也会失效。随时可以重新启用。' : '启用后该账号可以重新登录。'}
      confirmLabel={disabling ? '停用' : '启用'}
      color={disabling ? 'red' : 'green'}
      loading={update.isPending}
      error={update.error}
      onConfirm={() => update.mutate({ id: account.id, patch: { disabled: disabling } }, { onSuccess: onClose })}
      onClose={onClose}
    />
  );
}

function RevokeModal({ account, tokenId, tokenName, onClose }: { account: AccountInfo; tokenId: string; tokenName: string; onClose: () => void }) {
  const revoke = useRevokeAccountToken();
  return (
    <ConfirmModal
      title={`撤销 token「${tokenName}」？`}
      body="撤销后使用这个 token 的助手会立即无法访问 nblane。"
      confirmLabel="撤销"
      loading={revoke.isPending}
      error={revoke.error}
      onConfirm={() => revoke.mutate({ id: account.id, tokenId }, { onSuccess: onClose })}
      onClose={onClose}
    />
  );
}

export function AccountsSection() {
  const me = useMe();
  const accounts = useAccounts(Boolean(me.data?.auth_enabled));
  const [creating, setCreating] = useState(false);
  const [dialog, setDialog] = useState<Dialog | null>(null);
  const close = () => setDialog(null);

  if (me.data && !me.data.auth_enabled) {
    return <Alert color="gray" title="本地模式">本地模式未开启登录，无需管理账号。设置 NBLANE_AUTH_FILE 后才会启用登录。</Alert>;
  }
  if (accounts.isPending) return <Center py="xl"><Loader /></Center>;
  if (accounts.isError) return <ErrorText error={accounts.error} />;

  return (
    <SettingsCard icon={<IconUsers size={22} />} title="账号管理" description="新建用户、重置密码、停用账号，给助手账号发 API token。">
      <Group><Button leftSection={<IconUserPlus size={16} />} onClick={() => setCreating(true)}>新建用户</Button></Group>
      <Stack gap="sm">
        {accounts.data.map((account) => (
          <AccountCard key={account.id} account={account} isSelf={account.id === me.data?.id} onOpen={setDialog} />
        ))}
      </Stack>
      <CreateAccountModal opened={creating} onClose={() => setCreating(false)} />
      {dialog?.kind === 'reset' && <ResetPasswordModal account={dialog.account} onClose={close} />}
      {dialog?.kind === 'edit' && <EditAccountModal account={dialog.account} isSelf={dialog.account.id === me.data?.id} onClose={close} />}
      {dialog?.kind === 'toggle' && <ToggleModal account={dialog.account} onClose={close} />}
      {dialog?.kind === 'token' && <CreateTokenModal account={dialog.account} onClose={close} />}
      {dialog?.kind === 'revoke' && <RevokeModal account={dialog.account} tokenId={dialog.tokenId} tokenName={dialog.tokenName} onClose={close} />}
    </SettingsCard>
  );
}
