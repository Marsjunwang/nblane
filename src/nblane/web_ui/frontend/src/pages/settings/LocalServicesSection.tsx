// 系统 · 本地服务: local translation models (llama.cpp) and GROBID (admin).
// Both compete for the same RAM, so one resource bar sits on top.

import { Alert, Badge, Button, Card, Divider, Group, Progress, SegmentedControl, Select, SimpleGrid, Stack, Text, Textarea, Tooltip } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconCheck, IconCpu, IconDownload, IconFileText, IconLanguage, IconPlayerPlay, IconPlayerStop, IconRefresh, IconTrash, IconX } from '@tabler/icons-react';
import { useState } from 'react';

import {
  useCancelLocalModelInstall,
  useDeleteLocalModel,
  useGrobidAction,
  useGrobidLogs,
  useGrobidStatus,
  useInstallLocalModel,
  useLocalModels,
  useSetActiveLocalModel,
  useSetGrobidBackend,
  useTestLocalModel,
  useUninstallGrobid,
} from '../../api/hooks';
import type { GrobidStatus, LocalModel, LocalModels } from '../../api/types';
import { chrome } from '../../theme';
import { ErrorAlert, SettingsCard, formatGb, formatMb } from './shared';

const onError = (title: string) => ({ onError: (error: Error) => notifications.show({ title, message: error.message, color: 'red' }) });

// --- resource bar -----------------------------------------------------------------

function ResourceBar({ models, grobid }: { models?: LocalModels; grobid?: GrobidStatus }) {
  const resources = models?.resources;
  const total = resources?.total_ram_mb || grobid?.total_ram_mb || 0;
  const available = resources?.available_ram_mb || grobid?.available_ram_mb || 0;
  if (!total) return null;
  const modelMb = models?.server.running && !models.server.sleeping ? models.server.rss_mb : 0;
  const grobidMb = grobid?.unit_state.memory_mb ?? 0;
  const otherMb = Math.max(0, total - available - modelMb - grobidMb);
  const pct = (mb: number) => (mb / total) * 100;
  return (
    <Card withBorder radius="md" padding="md">
      <Stack gap={8}>
        <Group justify="space-between" gap="xs">
          <Text fw={600} size="sm">服务器资源</Text>
          <Text size="xs" c="dimmed">
            {resources ? `${resources.cores} 核${resources.avx2 ? ' · AVX2' : ''} · ` : ''}内存 {formatMb(total)}，可用 {formatMb(available)}{resources ? ` · 磁盘可用 ${formatMb(resources.free_disk_mb)}` : ''}
          </Text>
        </Group>
        <Progress.Root size="lg" aria-label="内存占用">
          <Tooltip label={`其他进程 ${formatMb(otherMb)}`}><Progress.Section value={pct(otherMb)} color="gray" /></Tooltip>
          {grobidMb > 0 && <Tooltip label={`GROBID ${formatMb(grobidMb)}`}><Progress.Section value={pct(grobidMb)} color="blue" /></Tooltip>}
          {modelMb > 0 && <Tooltip label={`本地翻译模型 ${formatMb(modelMb)}`}><Progress.Section value={pct(modelMb)} color="brand" /></Tooltip>}
        </Progress.Root>
        <Group gap="md">
          <Text size="xs" c="dimmed">本地翻译模型：{models?.server.running ? (models.server.sleeping ? '休眠（已释放内存）' : formatMb(modelMb)) : '未运行'}</Text>
          <Text size="xs" c="dimmed">GROBID：{grobidMb ? formatMb(grobidMb) : grobid?.state === 'external' ? '外部服务' : '未运行'}</Text>
        </Group>
      </Stack>
    </Card>
  );
}

// --- local translation models -----------------------------------------------------

const TIER_LABEL: Record<string, string> = { fit: '适配当前服务器', quality: '高质量 · 需更大内存' };
const SAMPLE_TEXT = 'We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.';

function LocalModelCard({ model, busy }: { model: LocalModel; busy: boolean }) {
  const install = useInstallLocalModel();
  const cancel = useCancelLocalModelInstall();
  const remove = useDeleteLocalModel();
  const activate = useSetActiveLocalModel();
  const running = model.install.status === 'running';
  const percent = model.install.total ? Math.min(100, (model.install.downloaded / model.install.total) * 100) : 0;
  const phase = model.install.phase === 'runtime' ? '下载 llama.cpp 运行时' : '下载模型';
  return (
    <Card withBorder radius="sm" padding="md" style={model.active ? { borderColor: chrome.gold } : undefined}>
      <Stack gap="xs">
        <Group justify="space-between" align="flex-start" wrap="nowrap">
          <div>
            <Group gap="xs"><Text fw={600}>{model.name}</Text>{model.active && <Badge color="green" variant="light">使用中</Badge>}{model.installed && !model.active && <Badge variant="light">已安装</Badge>}</Group>
            <Text size="xs" c="dimmed">{TIER_LABEL[model.tier] ?? model.tier}</Text>
          </div>
          <Badge variant="outline" color="gray">{model.license}</Badge>
        </Group>
        <Text size="sm">{model.description}</Text>
        <Text size="xs" c="dimmed">文件 {formatGb(model.size)} · 运行约 {formatMb(model.runtime_ram_mb)} · 建议总内存 ≥ {formatMb(model.min_ram_mb)} · <a href={model.homepage} target="_blank" rel="noreferrer">模型主页</a></Text>
        {running && <Stack gap={4}><Progress value={percent} animated aria-label={`${model.name}安装进度`} /><Text size="xs" c="dimmed">{phase} {percent.toFixed(0)}%（{formatGb(model.install.downloaded)} / {formatGb(model.install.total)}）</Text></Stack>}
        {model.install.status === 'failed' && <Alert color="red" variant="light">{model.install.error}</Alert>}
        {!model.installed && !running && model.install_blocker && <Text size="xs" c="dimmed">暂不能安装：{model.install_blocker}</Text>}
        <Group gap="xs">
          {!model.installed && !running && <Button size="xs" leftSection={<IconDownload size={14} />} disabled={busy || Boolean(model.install_blocker)} loading={install.isPending} onClick={() => install.mutate(model.id, onError('安装失败'))}>{model.install.status === 'cancelled' || model.install.status === 'failed' ? '继续安装' : '安装'}</Button>}
          {running && <Button size="xs" variant="default" leftSection={<IconX size={14} />} loading={cancel.isPending} onClick={() => cancel.mutate(model.id)}>取消</Button>}
          {model.installed && !model.active && <Button size="xs" leftSection={<IconCheck size={14} />} disabled={!model.fits_ram} loading={activate.isPending} onClick={() => activate.mutate(model.id, { onSuccess: () => notifications.show({ title: '已启用本地模型', message: model.name, color: 'green' }), ...onError('启用失败') })}>启用</Button>}
          {model.active && <Button size="xs" variant="default" loading={activate.isPending} onClick={() => activate.mutate('', onError('停用失败'))}>停用</Button>}
          {model.installed && <Button size="xs" variant="subtle" color="red" leftSection={<IconTrash size={14} />} loading={remove.isPending} onClick={() => { if (window.confirm(`删除 ${model.name} 的模型文件（${formatGb(model.size)}）？之后需要重新下载。`)) remove.mutate(model.id, onError('删除失败')); }}>删除</Button>}
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
      <Divider />
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

function LocalModelsCard({ status }: { status: LocalModels }) {
  const busy = status.models.some((model) => model.install.status === 'running');
  return (
    <SettingsCard icon={<IconCpu size={22} />} title="本地翻译模型" description="用 llama.cpp 在服务器上运行开源翻译模型，选区和当前页翻译不再消耗 LLM 额度；首次翻译时自动启动，空闲 5 分钟后释放内存。哪些翻译用它，在「档案 → 研究与阅读」里选。">
      <SimpleGrid cols={{ base: 1, md: 2 }}>
        {status.models.map((model) => <LocalModelCard key={model.id} model={model} busy={busy} />)}
      </SimpleGrid>
      <LocalModelTest models={status.models} activeId={status.active_model_id} />
    </SettingsCard>
  );
}

// --- GROBID -----------------------------------------------------------------------

const GROBID_STATE: Record<string, { label: string; color: string }> = {
  running: { label: '运行中', color: 'green' },
  starting: { label: '启动中', color: 'yellow' },
  external: { label: '运行中（外部服务）', color: 'green' },
  stopped: { label: '已停止', color: 'gray' },
  failed: { label: '启动失败', color: 'red' },
  not_installed: { label: '未安装', color: 'gray' },
};
const GROBID_PHASE: Record<string, string> = { image: '拉取镜像（约 1.7 GB）', unit: '写入服务', start: '启动服务' };
const PDF_BACKENDS = [
  { value: 'auto', label: '自动', description: 'GROBID 可用就用，不可用时退回 PyMuPDF 文本' },
  { value: 'grobid', label: 'GROBID', description: '总是先用 GROBID 抽取章节、段落和参考文献' },
  { value: 'pymupdf', label: '仅 PyMuPDF', description: '不调用 GROBID，只做页面文本抽取' },
];

function GrobidCard({ data, refetch, fetching }: { data: GrobidStatus; refetch: () => void; fetching: boolean }) {
  const action = useGrobidAction();
  const uninstall = useUninstallGrobid();
  const setBackend = useSetGrobidBackend();
  const [showLogs, setShowLogs] = useState(false);
  const logs = useGrobidLogs(showLogs);
  const state = GROBID_STATE[data.state] ?? { label: data.state, color: 'gray' };
  const installing = data.install.status === 'running';
  const managed = data.unit_state.installed;
  // Without an override each service follows its own startup env, which can
  // differ (Reader vs SPA backend), so show "unset" instead of guessing.
  const backend = data.backend_override;
  const pending = (name: string) => action.isPending && action.variables === name;
  return (
    <SettingsCard icon={<IconFileText size={22} />} title="GROBID 结构化抽取" description="把论文 PDF 解析成章节、段落和参考文献；Reader 的段落定位、结构化翻译和参考文献卡片都依赖它。">
      <Group gap="xs">
        <Badge color={state.color} variant="light">{state.label}</Badge>
        {data.version && <Badge variant="outline" color="gray">v{data.version}</Badge>}
        <Text size="xs" c="dimmed">{data.url}</Text>
      </Group>
      {data.state === 'external' && <Alert color="blue" variant="light">GROBID 正在运行，但不是由 nblane 管理（例如 root 下的 Docker 容器），这里只能查看状态。要在界面里启停，先停掉原容器，再点「安装并启动」。</Alert>}
      {data.state === 'starting' && <Text size="xs" c="dimmed">GROBID 启动需要约 1 分钟加载模型。</Text>}
      {installing && <Stack gap={4}><Progress value={100} animated aria-label="GROBID 安装进度" /><Text size="xs" c="dimmed">{GROBID_PHASE[data.install.phase] ?? '处理中'}…</Text></Stack>}
      {data.install.status === 'failed' && <Alert color="red" variant="light">{data.install.error}</Alert>}
      {data.blocker && !managed && <Text size="xs" c="dimmed">暂不能安装：{data.blocker}</Text>}
      {!managed && data.total_ram_mb > 0 && data.total_ram_mb < data.min_ram_mb && <Text size="xs" c="orange">本机内存低于 {formatMb(data.min_ram_mb)}，GROBID 可能会很慢或被系统杀掉。</Text>}
      <Group gap="xs">
        {!managed && <Button size="xs" leftSection={<IconDownload size={14} />} disabled={Boolean(data.blocker) || installing} loading={pending('install')} onClick={() => action.mutate('install', onError('安装失败'))}>{data.image_present ? '安装并启动' : '安装（下载镜像）'}</Button>}
        {managed && data.state !== 'running' && data.state !== 'starting' && <Button size="xs" leftSection={<IconPlayerPlay size={14} />} loading={pending('start')} onClick={() => action.mutate('start', onError('启动失败'))}>启动</Button>}
        {managed && (data.state === 'running' || data.state === 'starting') && <Button size="xs" variant="default" leftSection={<IconPlayerStop size={14} />} loading={pending('stop')} onClick={() => action.mutate('stop', onError('停止失败'))}>停止</Button>}
        {managed && data.state === 'running' && <Button size="xs" variant="default" leftSection={<IconRefresh size={14} />} loading={pending('restart')} onClick={() => action.mutate('restart', onError('重启失败'))}>重启</Button>}
        {managed && <Button size="xs" variant="subtle" onClick={() => setShowLogs((value) => !value)}>{showLogs ? '收起日志' : '查看日志'}</Button>}
        {managed && <Button size="xs" variant="subtle" color="red" leftSection={<IconTrash size={14} />} loading={uninstall.isPending} onClick={() => { if (window.confirm('停止并移除 GROBID 服务？镜像会保留，之后可以重新安装。')) uninstall.mutate(undefined, onError('移除失败')); }}>移除服务</Button>}
        <Button size="xs" variant="subtle" leftSection={<IconRefresh size={14} />} loading={fetching} onClick={refetch}>刷新</Button>
      </Group>
      {showLogs && <Card withBorder radius="sm" padding="xs"><Text component="pre" size="xs" style={{ whiteSpace: 'pre-wrap', maxHeight: 260, overflow: 'auto', margin: 0 }}>{logs.data?.text || (logs.isPending ? '加载中…' : '暂无日志')}</Text></Card>}
      <Divider />
      <Stack gap={6}>
        <div><Text fw={600} size="sm">PDF 结构后端</Text><Text size="xs" c="dimmed">Reader 和 SPA 后端共用这个选择，点选立即生效；已抽取的论文不受影响，重新抽取时才会用新后端。</Text></div>
        <SegmentedControl aria-label="PDF 结构后端" w="fit-content" value={backend} onChange={(value) => setBackend.mutate(value, onError('保存失败'))} data={PDF_BACKENDS.map(({ value, label }) => ({ value, label }))} />
        {backend
          ? <Text size="xs" c="dimmed">{PDF_BACKENDS.find((item) => item.value === backend)?.description}</Text>
          : <Text size="xs" c="orange">未设置：Reader 和 SPA 后端各按自己的启动配置（可能不一致，例如 Reader 设成了只用 PyMuPDF）。选一个即可统一。</Text>}
      </Stack>
    </SettingsCard>
  );
}

export function LocalServicesSection() {
  const models = useLocalModels();
  const grobid = useGrobidStatus();
  return (
    <Stack gap="lg">
      <ResourceBar models={models.data} grobid={grobid.data} />
      {models.isError ? <ErrorAlert error={models.error} /> : models.data && <LocalModelsCard status={models.data} />}
      {grobid.isError ? <ErrorAlert error={grobid.error} /> : grobid.data && <GrobidCard data={grobid.data} refetch={() => void grobid.refetch()} fetching={grobid.isFetching} />}
      <Text size="xs" c="dimmed">两项服务都只监听 127.0.0.1，不对外开放；停用或删除不会影响已保存的译文和已抽取的论文结构。</Text>
    </Stack>
  );
}
