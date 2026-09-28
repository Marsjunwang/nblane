import {
  Alert,
  Badge,
  Button,
  Card,
  Center,
  Checkbox,
  Divider,
  Group,
  Loader,
  PasswordInput,
  Select,
  SimpleGrid,
  Stack,
  Text,
  TextInput,
  Title,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconCheck,
  IconDeviceFloppy,
  IconKey,
  IconPlugConnected,
  IconRefresh,
  IconSettings,
} from '@tabler/icons-react';
import { useEffect, useMemo, useState } from 'react';

import {
  useCodexStatus,
  usePatchProfileCodexSettings,
  usePatchProfileSettings,
  useProfileCodexSettings,
  useProfileSettings,
  useProfiles,
  useSettingsConnection,
  useUpdateSettingsConnection,
  useVerifySettingsConnection,
  useMe,
} from '../api/hooks';
import type { CodexSettingsPatch, LlmConnectionUpdate, ProfileSettingsPatch } from '../api/types';

const profileOptions = (profiles: Array<{ name: string }>) =>
  profiles.map((profile) => ({ value: profile.name, label: profile.name }));

function settingString(settings: Record<string, unknown> | undefined, key: string): string {
  const value = settings?.[key];
  return value === undefined || value === null ? '' : String(value);
}

function preferenceString(preferences: Record<string, unknown> | undefined, ...path: string[]): string {
  let value: unknown = preferences;
  for (const segment of path) {
    if (!value || typeof value !== 'object') return '';
    value = (value as Record<string, unknown>)[segment];
  }
  return value === undefined || value === null ? '' : String(value);
}

function ErrorAlert({ error }: { error: Error | null | undefined }) {
  if (!error) return null;
  return <Alert color="red" title="操作失败">{error.message}</Alert>;
}

function SectionTitle({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <Group gap="sm" align="flex-start">
      {icon}
      <div>
        <Title order={3}>{title}</Title>
        <Text size="sm" c="dimmed">{description}</Text>
      </div>
    </Group>
  );
}

function ConnectionSection({ isAdmin }: { isAdmin: boolean }) {
  const connection = useSettingsConnection(isAdmin);
  const save = useUpdateSettingsConnection();
  const verify = useVerifySettingsConnection();
  const [baseUrl, setBaseUrl] = useState('');
  const [model, setModel] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [clearApiKey, setClearApiKey] = useState(false);

  useEffect(() => {
    if (connection.data) {
      setBaseUrl(connection.data.base_url);
      setModel(connection.data.model);
      // The API key is deliberately never populated from the response.
      setApiKey('');
      setClearApiKey(false);
    }
  }, [connection.data]);

  if (!isAdmin) return null;
  if (connection.isPending) return <Center py="xl"><Loader /></Center>;
  if (connection.isError) return <ErrorAlert error={connection.error} />;

  const submit = () => {
    const body: LlmConnectionUpdate = { base_url: baseUrl, model, api_key: apiKey, clear_api_key: clearApiKey };
    save.mutate(body, {
      onSuccess: () => {
        setApiKey('');
        setClearApiKey(false);
        notifications.show({ title: '连接设置已保存', message: '运行中的 AI 服务已同步更新', color: 'green' });
      },
    });
  };

  return (
    <Card withBorder radius="md" padding="lg">
      <Stack gap="md">
        <SectionTitle icon={<IconPlugConnected size={22} />} title="AI 连接" description="部署级 OpenAI 兼容服务配置。API Key 只写入服务端，不会回显。" />
        <SimpleGrid cols={{ base: 1, sm: 2 }}>
          <TextInput label="Base URL" placeholder="https://api.openai.com/v1" value={baseUrl} onChange={(event) => setBaseUrl(event.currentTarget.value)} />
          <TextInput label="默认模型" placeholder="gpt-4o-mini" value={model} onChange={(event) => setModel(event.currentTarget.value)} />
        </SimpleGrid>
        <PasswordInput label="API Key" description={connection.data?.api_key_set ? '服务端已保存 Key；留空表示保留现有值。' : '尚未配置 API Key。'} placeholder="只在新增或更换时填写" value={apiKey} onChange={(event) => setApiKey(event.currentTarget.value)} leftSection={<IconKey size={16} />} />
        <Checkbox label="清除服务端 API Key" checked={clearApiKey} onChange={(event) => { setClearApiKey(event.currentTarget.checked); if (event.currentTarget.checked) setApiKey(''); }} />
        <Group>
          <Button leftSection={<IconDeviceFloppy size={16} />} loading={save.isPending} onClick={submit}>保存连接</Button>
          <Button variant="light" leftSection={<IconCheck size={16} />} loading={verify.isPending} onClick={() => verify.mutate(undefined, { onSuccess: (result) => notifications.show({ title: result.ok ? '连接成功' : '连接失败', message: result.detail || (result.ok ? '服务响应正常。' : '服务未通过检查。'), color: result.ok ? 'green' : 'red' }) })}>测试连接</Button>
        </Group>
        <ErrorAlert error={save.error} />
        <ErrorAlert error={verify.error} />
      </Stack>
    </Card>
  );
}

function ProfileSection({ profile }: { profile: string }) {
  const preferences = useProfileSettings(profile);
  const save = usePatchProfileSettings(profile);
  const [uiLang, setUiLang] = useState('');
  const [replyLang, setReplyLang] = useState('');
  const [kanbanBackend, setKanbanBackend] = useState('');
  const [alignmentBackend, setAlignmentBackend] = useState('');
  const [alignmentModel, setAlignmentModel] = useState('');
  const [subtasksBackend, setSubtasksBackend] = useState('');
  const [subtasksModel, setSubtasksModel] = useState('');
  const [crystallizeBackend, setCrystallizeBackend] = useState('');
  const [crystallizeModel, setCrystallizeModel] = useState('');

  useEffect(() => {
    const value = preferences.data?.preferences;
    setUiLang(preferenceString(value, 'ai', 'llm', 'ui_lang'));
    setReplyLang(preferenceString(value, 'ai', 'llm', 'reply_lang'));
    setKanbanBackend(preferenceString(value, 'ai', 'kanban_backend'));
    const alignmentBackendValue = preferenceString(value, 'ai', 'actions', 'kanban.task_alignment', 'backend');
    const subtasksBackendValue = preferenceString(value, 'ai', 'actions', 'kanban.subtasks', 'backend');
    const crystallizeBackendValue = preferenceString(value, 'ai', 'actions', 'evidence.crystallize', 'backend');
    setAlignmentBackend(alignmentBackendValue);
    setAlignmentModel(preferenceString(value, 'ai', 'actions', 'kanban.task_alignment', alignmentBackendValue === 'codex' ? 'codex_model' : 'llm_model'));
    setSubtasksBackend(subtasksBackendValue);
    setSubtasksModel(preferenceString(value, 'ai', 'actions', 'kanban.subtasks', subtasksBackendValue === 'codex' ? 'codex_model' : 'llm_model'));
    setCrystallizeBackend(crystallizeBackendValue);
    setCrystallizeModel(preferenceString(value, 'ai', 'actions', 'evidence.crystallize', crystallizeBackendValue === 'codex' ? 'codex_model' : 'llm_model'));
  }, [preferences.data]);

  if (preferences.isPending) return <Center py="xl"><Loader /></Center>;
  if (preferences.isError) return <ErrorAlert error={preferences.error} />;

  const patch: ProfileSettingsPatch = {
    ai: {
      llm: { ui_lang: uiLang, reply_lang: replyLang },
      kanban_backend: kanbanBackend,
      actions: {
        'kanban.task_alignment': { backend: alignmentBackend, model: alignmentModel },
        'kanban.subtasks': { backend: subtasksBackend, model: subtasksModel },
        'evidence.crystallize': { backend: crystallizeBackend, model: crystallizeModel },
      },
    },
  };
  return (
    <Card withBorder radius="md" padding="lg">
      <Stack gap="md">
        <SectionTitle icon={<IconSettings size={22} />} title="当前档案的 AI 偏好" description="先配置看板闭环使用的 AI；论文阅读和写作设置将在后续页面迁移。" />
        <SimpleGrid cols={{ base: 1, sm: 2 }}>
          <Select label="界面语言" placeholder="跟随默认值" value={uiLang || null} onChange={(value) => setUiLang(value ?? '')} data={[{ value: 'zh', label: '中文' }, { value: 'en', label: 'English' }]} clearable />
          <Select label="AI 回复语言" placeholder="自动" value={replyLang || null} onChange={(value) => setReplyLang(value ?? '')} data={[{ value: 'auto', label: '自动' }, { value: 'zh', label: '中文' }, { value: 'en', label: 'English' }]} clearable />
          <Select label="看板 AI 后端" placeholder="默认" value={kanbanBackend || null} onChange={(value) => setKanbanBackend(value ?? '')} data={[{ value: 'llm', label: '兼容 API' }, { value: 'codex', label: 'Codex' }]} clearable />
          <Select label="任务对齐后端" placeholder="跟随看板后端" value={alignmentBackend || null} onChange={(value) => setAlignmentBackend(value ?? '')} data={[{ value: 'llm', label: '兼容 API' }, { value: 'codex', label: 'Codex' }]} clearable />
          <TextInput label="任务对齐模型" placeholder="留空使用默认模型" value={alignmentModel} onChange={(event) => setAlignmentModel(event.currentTarget.value)} />
          <Select label="子任务拆分后端" placeholder="跟随看板后端" value={subtasksBackend || null} onChange={(value) => setSubtasksBackend(value ?? '')} data={[{ value: 'llm', label: '兼容 API' }, { value: 'codex', label: 'Codex' }]} clearable />
          <TextInput label="子任务拆分模型" placeholder="留空使用默认模型" value={subtasksModel} onChange={(event) => setSubtasksModel(event.currentTarget.value)} />
          <Select label="证据结晶后端" placeholder="默认使用兼容 API" value={crystallizeBackend || null} onChange={(value) => setCrystallizeBackend(value ?? '')} data={[{ value: 'llm', label: '兼容 API' }, { value: 'codex', label: 'Codex' }]} clearable />
          <TextInput label="证据结晶模型" placeholder="留空使用默认模型" value={crystallizeModel} onChange={(event) => setCrystallizeModel(event.currentTarget.value)} />
        </SimpleGrid>
        <Group>
          <Button leftSection={<IconDeviceFloppy size={16} />} loading={save.isPending} onClick={() => save.mutate(patch, { onSuccess: () => notifications.show({ title: '档案偏好已保存', message: profile, color: 'green' }) })}>保存档案偏好</Button>
        </Group>
        <ErrorAlert error={save.error} />
      </Stack>
    </Card>
  );
}

function CodexSection({ profile }: { profile: string }) {
  const status = useCodexStatus();
  const settings = useProfileCodexSettings(profile);
  const save = usePatchProfileCodexSettings(profile);
  const [binPath, setBinPath] = useState('');
  const [cloudEnvId, setCloudEnvId] = useState('');
  const [model, setModel] = useState('');
  const [branch, setBranch] = useState('');
  const [timeout, setTimeoutValue] = useState('');

  useEffect(() => {
    const value = settings.data?.settings;
    setBinPath(settingString(value, 'bin_path'));
    setCloudEnvId(settingString(value, 'cloud_env_id'));
    setModel(settingString(value, 'model'));
    setBranch(settingString(value, 'branch'));
    setTimeoutValue(settingString(value, 'timeout_seconds'));
  }, [settings.data]);

  if (settings.isPending || status.isPending) return <Center py="xl"><Loader /></Center>;
  if (settings.isError) return <ErrorAlert error={settings.error} />;
  if (status.isError) return <ErrorAlert error={status.error} />;

  const statusLabel = status.data.installed ? (status.data.logged_in ? '已安装并登录' : '已安装,未登录') : '未安装';
  const patch: CodexSettingsPatch = {
    bin_path: binPath || null,
    cloud_env_id: cloudEnvId || null,
    model: model || null,
    branch: branch || null,
    timeout_seconds: timeout ? Number(timeout) : null,
  };
  return (
    <Card withBorder radius="md" padding="lg">
      <Stack gap="md">
        <SectionTitle icon={<IconRefresh size={22} />} title="Codex" description="查看本机 Codex 就绪状态，并保存档案级非敏感运行参数。认证仍由 Codex CLI 管理。" />
        <Group gap="xs"><Badge color={status.data.installed && status.data.logged_in ? 'green' : 'yellow'}>{statusLabel}</Badge><Text size="sm" c="dimmed">{status.data.version || status.data.error || '状态未知'}</Text></Group>
        <SimpleGrid cols={{ base: 1, sm: 2 }}>
          <TextInput label="Codex 路径" value={binPath} onChange={(event) => setBinPath(event.currentTarget.value)} placeholder="codex" />
          <TextInput label="Cloud 环境 ID" value={cloudEnvId} onChange={(event) => setCloudEnvId(event.currentTarget.value)} />
          <TextInput label="默认模型" value={model} onChange={(event) => setModel(event.currentTarget.value)} placeholder="codex" />
          <TextInput label="分支名" value={branch} onChange={(event) => setBranch(event.currentTarget.value)} placeholder="main" />
          <TextInput label="超时(秒)" type="number" min={5} value={timeout} onChange={(event) => setTimeoutValue(event.currentTarget.value)} />
        </SimpleGrid>
        <Button w="fit-content" leftSection={<IconDeviceFloppy size={16} />} loading={save.isPending} onClick={() => save.mutate(patch, { onSuccess: () => notifications.show({ title: 'Codex 设置已保存', message: profile, color: 'green' }) })}>保存 Codex 设置</Button>
        <ErrorAlert error={save.error} />
      </Stack>
    </Card>
  );
}

export function SettingsPage() {
  const me = useMe();
  const profiles = useProfiles();
  const [profile, setProfile] = useState('');
  const availableProfiles = useMemo(() => profiles.data ?? [], [profiles.data]);

  useEffect(() => {
    if (!profile && availableProfiles.length > 0) setProfile(availableProfiles[0].name);
    if (profile && !availableProfiles.some((item) => item.name === profile)) setProfile(availableProfiles[0]?.name ?? '');
  }, [availableProfiles, profile]);

  if (me.isPending || profiles.isPending) return <Center py="xl"><Loader /></Center>;
  if (me.isError) return <ErrorAlert error={me.error} />;
  if (profiles.isError) return <ErrorAlert error={profiles.error} />;

  const isAdmin = me.data.role === 'admin';
  return (
    <Stack gap="lg">
      <Group justify="space-between" align="flex-start">
        <div><Title order={2}>设置</Title><Text c="dimmed" size="sm">集中管理 AI 连接、档案偏好与 Codex 运行状态。</Text></div>
        {availableProfiles.length > 0 && <Select w={{ base: 220, sm: 280 }} label="编辑档案" value={profile} onChange={(value) => setProfile(value ?? '')} data={profileOptions(availableProfiles)} />}
      </Group>
      <ConnectionSection isAdmin={isAdmin} />
      {!isAdmin && <Alert color="blue" title="部署连接由管理员管理">你可以编辑自己有权限档案的 AI 偏好；部署级 Base URL、模型和 API Key 需要管理员处理。</Alert>}
      {profile ? <><ProfileSection profile={profile} /><CodexSection profile={profile} /></> : <Alert color="gray" title="暂无可编辑档案">当前账号没有可访问的 profile。</Alert>}
      <Divider />
      <Text size="xs" c="dimmed">API Key、Codex auth.json 和 token 不会在此页面读取或显示。</Text>
    </Stack>
  );
}
