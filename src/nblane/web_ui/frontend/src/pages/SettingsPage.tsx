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
  Progress,
  SegmentedControl,
  Select,
  SimpleGrid,
  Stack,
  Tabs,
  Text,
  Textarea,
  TextInput,
  Title,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconCheck,
  IconBook2,
  IconCpu,
  IconDeviceFloppy,
  IconDownload,
  IconLanguage,
  IconTrash,
  IconX,
  IconKey,
  IconPlugConnected,
  IconRefresh,
  IconSettings,
} from '@tabler/icons-react';
import { useEffect, useMemo, useState } from 'react';

import {
  useCancelLocalModelInstall,
  useCodexStatus,
  useDeleteLocalModel,
  useInstallLocalModel,
  useLocalModels,
  useSetActiveLocalModel,
  useTestLocalModel,
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
import type { CodexSettingsPatch, LlmConnectionUpdate, LocalModel, ProfileSettingsPatch } from '../api/types';

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

type ActionConfig = { backend: string; model: string };

const LOCAL_ROUTE_SCOPES = [
  { key: 'selection', label: '选区翻译', description: '划词、选中句子或单段。' },
  { key: 'visible', label: '当前页翻译', description: 'Reader 中可见页面的段落。' },
  { key: 'full', label: '全文翻译', description: '整篇论文；本地 1.8B 较慢，建议用 AI。' },
];
const LOCAL_ROUTE_DEFAULTS: Record<string, string> = { selection: 'local', visible: 'local', full: 'ai' };

const TIER_LABEL: Record<string, string> = { fit: '适配当前服务器', quality: '高质量 · 需更大内存' };
const SAMPLE_TEXT = 'We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.';

function formatGb(bytes: number): string {
  return `${(bytes / 1e9).toFixed(2)} GB`;
}

function formatMb(mb: number): string {
  return mb >= 1024 ? `${(mb / 1024).toFixed(1)} GB` : `${mb} MB`;
}

function LocalModelCard({ model, busy }: { model: LocalModel; busy: boolean }) {
  const install = useInstallLocalModel();
  const cancel = useCancelLocalModelInstall();
  const remove = useDeleteLocalModel();
  const activate = useSetActiveLocalModel();
  const running = model.install.status === 'running';
  const percent = model.install.total ? Math.min(100, (model.install.downloaded / model.install.total) * 100) : 0;
  const phase = model.install.phase === 'runtime' ? '下载 llama.cpp 运行时' : '下载模型';
  const notify = (title: string) => ({ onError: (error: Error) => notifications.show({ title, message: error.message, color: 'red' }) });
  return (
    <Card withBorder radius="sm" padding="md">
      <Stack gap="xs">
        <Group justify="space-between" align="flex-start" wrap="nowrap">
          <div>
            <Group gap="xs"><Text fw={600}>{model.name}</Text>{model.active && <Badge color="green" variant="light">使用中</Badge>}{model.installed && !model.active && <Badge variant="light">已安装</Badge>}</Group>
            <Text size="xs" c="dimmed">{TIER_LABEL[model.tier] ?? model.tier}</Text>
          </div>
          <Badge variant="outline" color="gray">{model.license}</Badge>
        </Group>
        <Text size="sm">{model.description}</Text>
        <Text size="xs" c="dimmed">文件 {formatGb(model.size)} · 运行约 {formatMb(model.runtime_ram_mb)} 内存 · 建议总内存 ≥ {formatMb(model.min_ram_mb)} · <a href={model.homepage} target="_blank" rel="noreferrer">模型主页</a></Text>
        {running && <Stack gap={4}><Progress value={percent} animated aria-label={`${model.name}安装进度`} /><Text size="xs" c="dimmed">{phase} {percent.toFixed(0)}%（{formatGb(model.install.downloaded)} / {formatGb(model.install.total)}）</Text></Stack>}
        {model.install.status === 'failed' && <Alert color="red" variant="light">{model.install.error}</Alert>}
        {!model.installed && !running && model.install_blocker && <Text size="xs" c="dimmed">暂不能安装：{model.install_blocker}</Text>}
        <Group gap="xs">
          {!model.installed && !running && <Button size="xs" leftSection={<IconDownload size={14} />} disabled={busy || Boolean(model.install_blocker)} loading={install.isPending} onClick={() => install.mutate(model.id, notify('安装失败'))}>{model.install.status === 'cancelled' || model.install.status === 'failed' ? '继续安装' : '安装'}</Button>}
          {running && <Button size="xs" variant="default" leftSection={<IconX size={14} />} loading={cancel.isPending} onClick={() => cancel.mutate(model.id)}>取消</Button>}
          {model.installed && !model.active && <Button size="xs" leftSection={<IconCheck size={14} />} disabled={!model.fits_ram} loading={activate.isPending} onClick={() => activate.mutate(model.id, { onSuccess: () => notifications.show({ title: '已启用本地模型', message: model.name, color: 'green' }), ...notify('启用失败') })}>启用</Button>}
          {model.active && <Button size="xs" variant="default" loading={activate.isPending} onClick={() => activate.mutate('', notify('停用失败'))}>停用</Button>}
          {model.installed && <Button size="xs" variant="subtle" color="red" leftSection={<IconTrash size={14} />} loading={remove.isPending} onClick={() => { if (window.confirm(`删除 ${model.name} 的模型文件（${formatGb(model.size)}）？之后需要重新下载。`)) remove.mutate(model.id, notify('删除失败')); }}>删除</Button>}
        </Group>
      </Stack>
    </Card>
  );
}

function LocalModelTest({ models, activeId }: { models: LocalModel[]; activeId: string }) {
  const installed = models.filter((model) => model.installed);
  const [modelId, setModelId] = useState('');
  const [text, setText] = useState(SAMPLE_TEXT);
  const test = useTestLocalModel();
  const selected = modelId && installed.some((model) => model.id === modelId) ? modelId : activeId || installed[0]?.id || '';
  if (installed.length === 0) return null;
  return (
    <Stack gap="xs">
      <Text fw={600} size="sm">试译</Text>
      <Group align="flex-end" gap="xs">
        <Select w={260} label="模型" value={selected} onChange={(value) => setModelId(value ?? '')} data={installed.map((model) => ({ value: model.id, label: model.name }))} />
        <Button leftSection={<IconLanguage size={16} />} loading={test.isPending} disabled={!text.trim()} onClick={() => test.mutate({ model_id: selected, text })}>翻译</Button>
      </Group>
      <Textarea aria-label="试译原文" autosize minRows={2} maxRows={6} maxLength={2000} value={text} onChange={(event) => setText(event.currentTarget.value)} />
      {test.isPending && <Text size="xs" c="dimmed">首次调用需要加载模型，可能要十几秒。</Text>}
      {test.data && <Card withBorder radius="sm" padding="sm"><Text size="sm">{test.data.translated_text}</Text><Text size="xs" c="dimmed" mt={4}>{test.data.seconds}s · {test.data.model_id}</Text></Card>}
      <ErrorAlert error={test.error} />
    </Stack>
  );
}

function LocalModelsSection() {
  const status = useLocalModels();
  if (status.isPending) return null;
  if (status.isError) return <ErrorAlert error={status.error} />;
  const { resources, server, models } = status.data;
  const busy = models.some((model) => model.install.status === 'running');
  return (
    <Card withBorder radius="md" padding="lg">
      <Stack gap="md">
        <SectionTitle icon={<IconCpu size={22} />} title="本地翻译模型" description="在服务器上用 llama.cpp 运行开源翻译模型，选区和段落翻译不再消耗 LLM 额度；失败时自动回到 AI 连接。" />
        <Text size="xs" c="dimmed">
          本机 {resources.cores} 核{resources.avx2 ? ' · AVX2' : ''} · 内存 {formatMb(resources.total_ram_mb)}（可用 {formatMb(resources.available_ram_mb)}） · 磁盘可用 {formatMb(resources.free_disk_mb)}
          {server.running ? ` · 模型服务${server.sleeping ? '休眠中（已释放内存）' : `运行中，占用 ${formatMb(server.rss_mb)}`}` : ' · 模型服务未启动（首次翻译时自动启动，空闲 5 分钟后释放内存）'}
        </Text>
        <SimpleGrid cols={{ base: 1, md: 2 }}>
          {models.map((model) => <LocalModelCard key={model.id} model={model} busy={busy} />)}
        </SimpleGrid>
        <LocalModelTest models={models} activeId={status.data.active_model_id} />
      </Stack>
    </Card>
  );
}

const ACTION_GROUPS: Array<{ title: string; description: string; actions: Array<{ key: string; label: string; description: string }> }> = [
  { title: '看板与项目', description: '决定工作流辅助动作使用哪一种 AI 执行路径。', actions: [
    { key: 'kanban.task_alignment', label: '任务对齐', description: '把任务与技能/目标做关联建议。' },
    { key: 'kanban.subtasks', label: '子任务拆分', description: '将看板任务拆成可执行步骤。' },
    { key: 'dashboard.goal_skill_match', label: '目标与技能匹配', description: '分析目标与技能树的相关性。' },
    { key: 'dashboard.daily_brief', label: '每日简报', description: '生成当天的工作摘要。' },
    { key: 'project.suggest_refs', label: '项目引用建议', description: '为项目补充相关引用和关联。' },
  ] },
  { title: '研究与阅读', description: '配置论文库和 Reader 中的 AI 操作；阅读本身不会自动变成证据。', actions: [
    { key: 'research.paper_search_codex', label: '论文搜索', description: '扩展论文库的搜索与检索。' },
    { key: 'research.paper_translate', label: '论文翻译', description: '翻译论文段落或页面内容。' },
    { key: 'research.paper_explain_selection', label: '选区解释', description: '解释 Reader 中选中的内容。' },
    { key: 'research.paper_source_guide', label: '来源导览', description: '给出论文来源和阅读路径提示。' },
    { key: 'research.paper_review_card', label: '阅读回顾卡', description: '整理阅读回顾，不写入证据池。' },
    { key: 'research.paper_qa', label: '论文问答', description: '针对当前论文进行问答。' },
    { key: 'research.paper_claim_extract', label: '观点提取', description: '按需提取论文观点，仅作为 AI 输出。' },
    { key: 'research.paper_deep_read_codex', label: '论文深读', description: '使用 Codex 做长文档深读。' },
    { key: 'research.paper_compare_codex', label: '论文比较', description: '比较多篇论文的内容与差异。' },
  ] },
  { title: '输出与证据', description: '保留现有输出工作流的 AI 路由，和 Reader 阅读默认值相互独立。', actions: [
    { key: 'evidence.crystallize', label: '证据结晶', description: '仅在证据工作流中使用，不改变 Reader。' },
  ] },
];

function ActionRow({ label, description, value, onChange }: { label: string; description: string; value: ActionConfig; onChange: (next: ActionConfig) => void }) {
  return (
    <Card withBorder radius="sm" padding="sm">
      <Stack gap="xs">
        <div><Text fw={600} size="sm">{label}</Text><Text size="xs" c="dimmed">{description}</Text></div>
        <SimpleGrid cols={{ base: 1, sm: 2 }}>
          <Select aria-label={`${label}后端`} label="后端" placeholder="跟随默认" value={value.backend || null} onChange={(next) => onChange({ ...value, backend: next ?? '' })} data={[{ value: 'llm', label: '兼容 API' }, { value: 'codex', label: 'Codex' }]} clearable />
          <TextInput aria-label={`${label}模型`} label="模型" placeholder="留空使用默认模型" value={value.model} onChange={(event) => onChange({ ...value, model: event.currentTarget.value })} />
        </SimpleGrid>
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
  const [actions, setActions] = useState<Record<string, ActionConfig>>({});
  const [localRoutes, setLocalRoutes] = useState<Record<string, string>>(LOCAL_ROUTE_DEFAULTS);

  useEffect(() => {
    const value = preferences.data?.preferences;
    setLocalRoutes(Object.fromEntries(LOCAL_ROUTE_SCOPES.map(({ key }) => [key, preferenceString(value, 'ai', 'local_translation', key) || LOCAL_ROUTE_DEFAULTS[key]])));
    setUiLang(preferenceString(value, 'ai', 'llm', 'ui_lang'));
    setReplyLang(preferenceString(value, 'ai', 'llm', 'reply_lang'));
    setKanbanBackend(preferenceString(value, 'ai', 'kanban_backend'));
    const next: Record<string, ActionConfig> = {};
    ACTION_GROUPS.flatMap((group) => group.actions).forEach(({ key }) => {
      const backend = preferenceString(value, 'ai', 'actions', key, 'backend');
      next[key] = { backend, model: preferenceString(value, 'ai', 'actions', key, backend === 'codex' ? 'codex_model' : 'llm_model') };
    });
    setActions(next);
  }, [preferences.data]);

  if (preferences.isPending) return <Center py="xl"><Loader /></Center>;
  if (preferences.isError) return <ErrorAlert error={preferences.error} />;

  const patch: ProfileSettingsPatch = {
    ai: {
      llm: { ui_lang: uiLang, reply_lang: replyLang },
      kanban_backend: kanbanBackend,
      local_translation: localRoutes,
      actions: Object.fromEntries(Object.entries(actions).map(([key, config]) => [key, config])),
    },
  };
  return (
    <Card withBorder radius="md" padding="lg">
      <Stack gap="md">
        <SectionTitle icon={<IconSettings size={22} />} title="当前档案的 AI 路由" description="每个动作都可以单独选择兼容 API 或 Codex；留空表示沿用系统默认。" />
        <SimpleGrid cols={{ base: 1, sm: 2 }}>
          <Select label="界面语言" placeholder="跟随默认值" value={uiLang || null} onChange={(value) => setUiLang(value ?? '')} data={[{ value: 'zh', label: '中文' }, { value: 'en', label: 'English' }]} clearable />
          <Select label="AI 回复语言" placeholder="自动" value={replyLang || null} onChange={(value) => setReplyLang(value ?? '')} data={[{ value: 'auto', label: '自动' }, { value: 'zh', label: '中文' }, { value: 'en', label: 'English' }]} clearable />
        </SimpleGrid>
        <Stack gap={6}>
          <div><Text fw={700}>论文翻译分工</Text><Text size="xs" c="dimmed">管理员启用本地翻译模型后生效；本地模型失败或未启用时一律走 AI。单词始终先查本地词典。</Text></div>
          <SimpleGrid cols={{ base: 1, sm: 3 }}>
            {LOCAL_ROUTE_SCOPES.map((scope) => (
              <Stack key={scope.key} gap={4}>
                <Text size="sm" fw={600}>{scope.label}</Text>
                <SegmentedControl aria-label={`${scope.label}翻译方式`} size="xs" value={localRoutes[scope.key] ?? LOCAL_ROUTE_DEFAULTS[scope.key]} onChange={(next) => setLocalRoutes((current) => ({ ...current, [scope.key]: next }))} data={[{ value: 'local', label: '本地模型' }, { value: 'ai', label: 'AI' }]} />
                <Text size="xs" c="dimmed">{scope.description}</Text>
              </Stack>
            ))}
          </SimpleGrid>
        </Stack>
        <Stack gap="md">
          {ACTION_GROUPS.map((group) => <Stack key={group.title} gap="xs"><div><Text fw={700}>{group.title}</Text><Text size="xs" c="dimmed">{group.description}</Text></div><SimpleGrid cols={{ base: 1, lg: 2 }}>{group.actions.map((action) => <ActionRow key={action.key} label={action.label} description={action.description} value={actions[action.key] ?? { backend: '', model: '' }} onChange={(next) => setActions((current) => ({ ...current, [action.key]: next }))} />)}</SimpleGrid></Stack>)}
        </Stack>
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

const READER_DEFAULTS = {
  default_mode: 'pdf', default_scale: 'fit-width', default_side_panel: 'collapsed',
  default_active_tab: 'notes', default_left_rail: 'open', default_left_tab: 'outline',
  default_translation_source: true, default_target_lang: 'zh', default_translation_layout: 'flow',
  compare_split_ratio: 50, panel_width: 340,
};

function ReaderDefaultsSection({ profile }: { profile: string }) {
  const preferences = useProfileSettings(profile);
  const save = usePatchProfileSettings(profile);
  const [reader, setReader] = useState(READER_DEFAULTS);

  useEffect(() => {
    const value = preferences.data?.preferences;
    const stored = value && typeof value === 'object' ? (value as Record<string, unknown>).research : undefined;
    const storedReader = stored && typeof stored === 'object' ? (stored as Record<string, unknown>).reader : undefined;
    if (storedReader && typeof storedReader === 'object') setReader({ ...READER_DEFAULTS, ...(storedReader as Partial<typeof READER_DEFAULTS>) });
  }, [preferences.data]);

  if (preferences.isPending) return <Center py="xl"><Loader /></Center>;
  if (preferences.isError) return <ErrorAlert error={preferences.error} />;
  const update = (key: keyof typeof READER_DEFAULTS, value: string | number | boolean | null) => setReader((current) => ({ ...current, [key]: value }));
  const patch: ProfileSettingsPatch = { research: { reader } };
  return (
    <Card withBorder radius="md" padding="lg">
      <Stack gap="md">
        <SectionTitle icon={<IconBook2 size={22} />} title="研究与阅读默认值" description="这是新论文的档案默认值；论文已保存的阅读位置和状态永远优先。" />
        <Alert color="blue" variant="light">这些设置只决定 Reader 的初始工作面，不会把阅读内容自动写入 claims、citation 或 evidence。</Alert>
        <SimpleGrid cols={{ base: 1, sm: 2 }}>
          <Select label="默认模式" value={reader.default_mode} onChange={(value) => update('default_mode', value ?? 'pdf')} data={[{ value: 'pdf', label: 'PDF' }, { value: 'translation', label: '翻译' }, { value: 'compare', label: '对照' }]} />
          <Select label="默认缩放" value={reader.default_scale} onChange={(value) => update('default_scale', value ?? 'fit-width')} data={[{ value: 'fit-width', label: '适合宽度' }, { value: 'fit-page', label: '适合页面' }, { value: 'actual', label: '实际大小' }]} />
          <Select label="右侧面板" value={reader.default_side_panel} onChange={(value) => update('default_side_panel', value ?? 'collapsed')} data={[{ value: 'collapsed', label: '默认收起' }, { value: 'open', label: '默认展开' }]} />
          <Select label="右侧默认页签" value={reader.default_active_tab} onChange={(value) => update('default_active_tab', value ?? 'notes')} data={[{ value: 'notes', label: '笔记' }, { value: 'translation', label: '翻译' }, { value: 'review', label: '回顾' }]} />
          <Select label="左侧导航栏" value={reader.default_left_rail} onChange={(value) => update('default_left_rail', value ?? 'open')} data={[{ value: 'open', label: '默认展开' }, { value: 'collapsed', label: '默认收起' }]} />
          <Select label="左侧默认页签" value={reader.default_left_tab} onChange={(value) => update('default_left_tab', value ?? 'outline')} data={[{ value: 'outline', label: '大纲' }, { value: 'thumbnails', label: '缩略图' }]} />
          <TextInput label="默认目标语言" value={reader.default_target_lang} onChange={(event) => update('default_target_lang', event.currentTarget.value)} placeholder="zh" />
          <Select label="翻译布局" value={reader.default_translation_layout} onChange={(value) => update('default_translation_layout', value ?? 'flow')} data={[{ value: 'flow', label: '流式' }, { value: 'overlay', label: '叠加' }]} />
          <TextInput label="对照分栏比例" type="number" min={20} max={80} value={String(reader.compare_split_ratio)} onChange={(event) => update('compare_split_ratio', Number(event.currentTarget.value) || 50)} description="20-80" />
          <TextInput label="右侧面板宽度" type="number" min={260} max={520} value={String(reader.panel_width)} onChange={(event) => update('panel_width', Number(event.currentTarget.value) || 340)} description="260-520 px" />
        </SimpleGrid>
        <Checkbox label="默认显示翻译原文" checked={reader.default_translation_source} onChange={(event) => update('default_translation_source', event.currentTarget.checked)} />
        <Button w="fit-content" leftSection={<IconDeviceFloppy size={16} />} loading={save.isPending} onClick={() => save.mutate(patch, { onSuccess: () => notifications.show({ title: '研究与阅读设置已保存', message: profile, color: 'green' }) })}>保存研究设置</Button>
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
        <div><Title order={2}>设置</Title><Text c="dimmed" size="sm">集中管理 AI 连接、本地模型、档案偏好与 Codex 运行状态。</Text></div>
        {availableProfiles.length > 0 && <Select w={{ base: 220, sm: 280 }} label="编辑档案" value={profile} onChange={(value) => setProfile(value ?? '')} data={profileOptions(availableProfiles)} />}
      </Group>
      {isAdmin && <ConnectionSection isAdmin />}
      {isAdmin && <LocalModelsSection />}
      {!isAdmin && <Alert color="blue" title="部署连接由管理员管理">你可以编辑自己有权限档案的 AI 偏好；部署级 Base URL、模型和 API Key 需要管理员处理。</Alert>}
      <Tabs defaultValue="ai">
        <Tabs.List mb="md">
          <Tabs.Tab value="ai" leftSection={<IconSettings size={15} />}>AI 路由</Tabs.Tab>
          <Tabs.Tab value="research" leftSection={<IconBook2 size={15} />}>研究与阅读</Tabs.Tab>
          <Tabs.Tab value="codex" leftSection={<IconRefresh size={15} />}>Codex</Tabs.Tab>
        </Tabs.List>
        {profile ? <>
          <Tabs.Panel value="ai"><ProfileSection profile={profile} /></Tabs.Panel>
          <Tabs.Panel value="research"><ReaderDefaultsSection profile={profile} /></Tabs.Panel>
          <Tabs.Panel value="codex"><CodexSection profile={profile} /></Tabs.Panel>
        </> : <Alert color="gray" title="暂无可编辑档案">当前账号没有可访问的 profile。</Alert>}
      </Tabs>
      <Divider />
      <Text size="xs" c="dimmed">API Key、Codex auth.json 和 token 不会在此页面读取或显示。</Text>
    </Stack>
  );
}
