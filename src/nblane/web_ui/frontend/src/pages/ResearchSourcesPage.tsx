import {
  Alert,
  Anchor,
  Badge,
  Button,
  Card,
  Center,
  Checkbox,
  Group,
  Loader,
  Menu,
  Modal,
  NativeSelect,
  Paper,
  SegmentedControl,
  Select,
  SimpleGrid,
  Stack,
  Switch,
  Tabs,
  Text,
  Textarea,
  TextInput,
  ThemeIcon,
  Title,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconArrowLeft,
  IconChevronDown,
  IconDeviceFloppy,
  IconDownload,
  IconExternalLink,
  IconInbox,
  IconListCheck,
  IconPencil,
  IconPlugConnected,
  IconPlus,
  IconRefresh,
  IconRobot,
  IconSearch,
} from '@tabler/icons-react';
import { useEffect, useRef, useState } from 'react';
import type { FormEvent, ReactNode } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';

import { ApiError } from '../api/client';
import { streamJob } from '../api/jobs';
import {
  useCreateResearchSource,
  useCreateResearchSourceTask,
  useImportManualItems,
  useImportResearchConnector,
  usePatchResearchSource,
  usePreviewManualItems,
  usePreviewResearchConnector,
  useRefreshAfterConnectorJob,
  useResearchConnectors,
  useResearchSources,
  useUpsertResearchConnector,
} from '../api/researchHooks';
import type {
  ResearchConnector,
  ResearchConnectorImportResult,
  ResearchConnectorPreview,
  ResearchImportTarget,
  ResearchSourceDetail,
  ResearchSourcePatchRequest,
} from '../api/researchHooks';
import type { JobCreateResponse } from '../api/types';
import { chrome } from '../theme';

// --- labels ---------------------------------------------------------------------

const STATUS_LABELS: Record<string, string> = {
  inbox: '收件箱',
  reading: '阅读中',
  summarized: '已总结',
  candidate_ready: '待整理',
  archived: '已归档',
  discarded: '已丢弃',
};
const STATUS_COLORS: Record<string, string> = {
  inbox: 'brand',
  reading: 'yellow',
  summarized: 'green',
  candidate_ready: 'cyan',
  archived: 'gray',
  discarded: 'red',
};
const KIND_LABELS: Record<string, string> = {
  web: '网页',
  paper: '论文',
  repo: '代码库',
  dataset: '数据集',
  pdf: 'PDF',
  book: '书籍',
  note: '笔记',
  other: '其他',
};
const PROVIDER_LABELS: Record<string, string> = {
  arxiv: 'arXiv',
  semantic_scholar: 'Semantic Scholar',
  github: 'GitHub',
  x_twitter: 'X / Twitter',
  xiaohongshu: '小红书',
};
const VISIBILITY_LABELS: Record<string, string> = { private: '私有', public: '公开' };
const ORIGIN_LABELS: Record<string, string> = {
  manual: '手动',
  home_capture: '首页捕获',
  connector: '连接器',
  resume_import: '简历导入',
};
const label = (map: Record<string, string>, value: string) => map[value] ?? value.replaceAll('_', ' ');
const options = (values: string[] | undefined, map: Record<string, string>) =>
  (values ?? []).map((value) => ({ value, label: label(map, value) }));

const FALLBACK_KINDS = Object.keys(KIND_LABELS);
const FALLBACK_STATUSES = Object.keys(STATUS_LABELS);
const VISIBILITIES = ['private', 'public'];

function parseList(raw: string): string[] {
  return raw
    .split(/[,，\n]/)
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}

const panelStyle = { background: chrome.panelBg, borderColor: 'rgba(220, 174, 85, 0.18)' } as const;
const rowStyle = { background: chrome.cardBg, borderColor: 'rgba(220, 174, 85, 0.14)' } as const;

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function LoadError({ title, error, onRetry }: { title: string; error: Error; onRetry: () => void }) {
  return (
    <Alert color="red" title={title}>
      <Stack gap="xs" align="flex-start">
        <Text size="sm">{error.message}</Text>
        <Button size="xs" variant="light" color="red" leftSection={<IconRefresh size={14} />} onClick={onRetry}>
          重试
        </Button>
      </Stack>
    </Alert>
  );
}

function SectionHeader({ icon, title, description, right }: { icon: ReactNode; title: string; description: string; right?: ReactNode }) {
  return (
    <Group justify="space-between" align="flex-start" wrap="nowrap" mb="md">
      <Group gap="sm" align="flex-start" wrap="nowrap">
        <ThemeIcon variant="light" color="brand" size={34} radius="sm">{icon}</ThemeIcon>
        <div>
          <Text fw={700}>{title}</Text>
          <Text size="xs" c={chrome.dim} mt={3}>{description}</Text>
        </div>
      </Group>
      {right}
    </Group>
  );
}

// --- 来源收件箱 -------------------------------------------------------------------

function SourceCard({
  source,
  statuses,
  busy,
  onStatus,
  onEdit,
  onTask,
}: {
  source: ResearchSourceDetail;
  statuses: string[];
  busy: boolean;
  onStatus: (status: string) => void;
  onEdit: () => void;
  onTask: () => void;
}) {
  return (
    <Paper withBorder radius="md" p="md" style={rowStyle} data-testid="research-source-row">
      <Group justify="space-between" align="flex-start" wrap="nowrap">
        <div style={{ minWidth: 0 }}>
          <Text fw={650} lineClamp={2}>{source.title || source.id}</Text>
          <Group gap={6} mt={6}>
            <Badge size="sm" variant="light" color="gray">{label(KIND_LABELS, source.kind)}</Badge>
            <Badge size="sm" variant="outline" color="gray">{label(VISIBILITY_LABELS, source.visibility)}</Badge>
            <Badge size="sm" variant="dot" color="gray">{source.provider ? label(PROVIDER_LABELS, source.provider) : label(ORIGIN_LABELS, source.origin)}</Badge>
            {(source.tags ?? []).map((tag) => <Badge key={tag} size="sm" variant="light" color="brand">{tag}</Badge>)}
          </Group>
        </div>
        <Group gap="xs" wrap="nowrap">
          <Menu withinPortal position="bottom-end">
            <Menu.Target>
              <Button
                size="xs"
                variant="light"
                color={STATUS_COLORS[source.status] ?? 'gray'}
                rightSection={<IconChevronDown size={12} />}
                loading={busy}
                aria-label={`修改状态：${source.title}`}
              >
                {label(STATUS_LABELS, source.status)}
              </Button>
            </Menu.Target>
            <Menu.Dropdown>
              {statuses.map((status) => (
                <Menu.Item key={status} disabled={status === source.status} onClick={() => onStatus(status)}>
                  {label(STATUS_LABELS, status)}
                </Menu.Item>
              ))}
            </Menu.Dropdown>
          </Menu>
          <Button size="xs" variant="default" leftSection={<IconPencil size={13} />} onClick={onEdit} aria-label={`编辑：${source.title}`}>
            编辑
          </Button>
        </Group>
      </Group>
      {source.url && (
        <Anchor href={source.url} target="_blank" rel="noreferrer" size="xs" c={chrome.goldText} mt="xs" style={{ display: 'inline-flex', alignItems: 'center', gap: 4, maxWidth: '100%' }}>
          <IconExternalLink size={12} />
          <Text span size="xs" truncate="end">{source.url}</Text>
        </Anchor>
      )}
      {source.summary && <Text size="sm" c={chrome.dim} mt="xs" lineClamp={2}>{source.summary}</Text>}
      <Group justify="space-between" mt="xs">
        <Text size="xs" c={chrome.dim}>{source.captured_at ? `收录于 ${source.captured_at}` : source.id}</Text>
        <Anchor component="button" type="button" size="xs" c={chrome.goldText} onClick={onTask}>
          <Group gap={4}><IconListCheck size={13} />建看板任务</Group>
        </Anchor>
      </Group>
    </Paper>
  );
}

function EditSourceModal({
  source,
  kinds,
  statuses,
  saving,
  onClose,
  onSave,
}: {
  source: ResearchSourceDetail | null;
  kinds: string[];
  statuses: string[];
  saving: boolean;
  onClose: () => void;
  onSave: (body: ResearchSourcePatchRequest) => void;
}) {
  const [title, setTitle] = useState('');
  const [url, setUrl] = useState('');
  const [kind, setKind] = useState('web');
  const [status, setStatus] = useState('inbox');
  const [visibility, setVisibility] = useState('private');
  const [tags, setTags] = useState('');
  const [summary, setSummary] = useState('');
  const [notes, setNotes] = useState('');

  useEffect(() => {
    if (!source) return;
    setTitle(source.title);
    setUrl(source.url);
    setKind(source.kind);
    setStatus(source.status);
    setVisibility(source.visibility);
    setTags((source.tags ?? []).join(', '));
    setSummary(source.summary);
    setNotes(source.notes);
  }, [source]);

  return (
    <Modal opened={source !== null} onClose={onClose} title="编辑来源" size="lg" centered>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          if (!title.trim()) return;
          onSave({ title: title.trim(), url: url.trim(), kind, status, visibility, tags: parseList(tags), summary, notes });
        }}
      >
        <Stack gap="sm">
          <TextInput label="标题" required value={title} onChange={(event) => setTitle(event.currentTarget.value)} />
          <TextInput label="链接" value={url} onChange={(event) => setUrl(event.currentTarget.value)} />
          <SimpleGrid cols={{ base: 1, sm: 3 }}>
            <Select label="类型" value={kind} onChange={(value) => setKind(value ?? 'web')} data={options(kinds, KIND_LABELS)} allowDeselect={false} />
            <Select label="状态" value={status} onChange={(value) => setStatus(value ?? 'inbox')} data={options(statuses, STATUS_LABELS)} allowDeselect={false} />
            <Select label="可见性" value={visibility} onChange={(value) => setVisibility(value ?? 'private')} data={options(VISIBILITIES, VISIBILITY_LABELS)} allowDeselect={false} />
          </SimpleGrid>
          <TextInput label="标签" description="逗号分隔" value={tags} onChange={(event) => setTags(event.currentTarget.value)} />
          <Textarea label="摘要" autosize minRows={2} maxRows={6} value={summary} onChange={(event) => setSummary(event.currentTarget.value)} />
          <Textarea label="笔记" autosize minRows={2} maxRows={6} value={notes} onChange={(event) => setNotes(event.currentTarget.value)} />
          <Group justify="flex-end">
            <Button variant="default" onClick={onClose}>取消</Button>
            <Button type="submit" loading={saving} disabled={!title.trim()} leftSection={<IconDeviceFloppy size={15} />}>保存</Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}

function InboxTab({ profile }: { profile: string }) {
  const [status, setStatus] = useState('active');
  const [kind, setKind] = useState('');
  const [query, setQuery] = useState('');
  const [editing, setEditing] = useState<ResearchSourceDetail | null>(null);
  const [pendingId, setPendingId] = useState<string | null>(null);
  const statusFilter = status === 'active' ? 'inbox,reading,summarized,candidate_ready' : status === 'all' ? '' : status;
  const list = useResearchSources(profile, { status: statusFilter, kind, q: query.trim() });
  const patch = usePatchResearchSource(profile);
  const createTask = useCreateResearchSourceTask(profile);

  const data = list.data?.data;
  const statuses = data?.options?.statuses?.length ? data.options.statuses : FALLBACK_STATUSES;
  const kinds = data?.options?.kinds?.length ? data.options.kinds : FALLBACK_KINDS;
  const sources = data?.sources ?? [];
  const counts = data?.status_counts ?? {};
  const activeCount = ['inbox', 'reading', 'summarized', 'candidate_ready'].reduce((sum, key) => sum + (counts[key] ?? 0), 0);

  function handlePatchError(error: unknown) {
    if (error instanceof ApiError && error.status === 412) {
      notifications.show({ color: 'yellow', title: '来源已被修改', message: '这条来源在别处被修改，已为你刷新，请确认后再试。' });
      void list.refetch();
      return;
    }
    notifications.show({ color: 'red', title: '保存失败', message: errorMessage(error) });
  }

  function save(source: ResearchSourceDetail, body: ResearchSourcePatchRequest, done?: () => void) {
    setPendingId(source.id);
    patch.mutate(
      { sourceId: source.id, body, etag: source.etag },
      {
        onSuccess: () => {
          notifications.show({ color: 'green', title: '已保存', message: source.title || source.id });
          done?.();
        },
        onError: handlePatchError,
        onSettled: () => setPendingId(null),
      },
    );
  }

  return (
    <Card withBorder radius="md" p="lg" style={panelStyle}>
      <SectionHeader
        icon={<IconInbox size={17} />}
        title="来源收件箱"
        description="所有类型的研究来源：网页、论文、代码库、数据集……只管理阅读状态与标签，不会自动变成证据。"
        right={<Button variant="default" size="xs" leftSection={<IconRefresh size={14} />} loading={list.isFetching} onClick={() => void list.refetch()}>刷新</Button>}
      />
      <Group gap="sm" mb="md" align="flex-end">
        <SegmentedControl
          value={status}
          onChange={setStatus}
          data={[
            { value: 'active', label: `进行中 ${activeCount}` },
            { value: 'archived', label: `已归档 ${counts.archived ?? 0}` },
            { value: 'discarded', label: `已丢弃 ${counts.discarded ?? 0}` },
            { value: 'all', label: `全部 ${data?.total ?? 0}` },
          ]}
        />
        <NativeSelect aria-label="按类型筛选" value={kind} onChange={(event) => setKind(event.currentTarget.value)} data={[{ value: '', label: '全部类型' }, ...options(kinds, KIND_LABELS)]} />
        <TextInput aria-label="搜索来源" placeholder="搜索标题、链接、摘要或标签" leftSection={<IconSearch size={14} />} value={query} onChange={(event) => setQuery(event.currentTarget.value)} style={{ flex: '1 1 220px' }} />
      </Group>
      {list.isPending ? (
        <Center py="xl"><Loader /></Center>
      ) : list.isError ? (
        <LoadError title="来源加载失败" error={list.error} onRetry={() => void list.refetch()} />
      ) : data && sources.length === 0 ? (
        <Text size="sm" c={chrome.dim} py="md">{data.total === 0 ? '收件箱还是空的。在「添加来源」里手动收录，或用「连接器」批量导入。' : '当前筛选下没有来源。'}</Text>
      ) : (
        <Stack gap="sm">
          {sources.map((source) => (
            <SourceCard
              key={source.id}
              source={source}
              statuses={statuses}
              busy={pendingId === source.id}
              onStatus={(next) => save(source, { status: next })}
              onEdit={() => setEditing(source)}
              onTask={() =>
                createTask.mutate(source.id, {
                  onSuccess: (task) => notifications.show({ color: 'green', title: '已建看板任务', message: task.title }),
                  onError: (error) => notifications.show({ color: 'red', title: '建任务失败', message: errorMessage(error) }),
                })
              }
            />
          ))}
        </Stack>
      )}
      <EditSourceModal
        source={editing}
        kinds={kinds}
        statuses={statuses}
        saving={patch.isPending}
        onClose={() => setEditing(null)}
        onSave={(body) => editing && save(editing, body, () => setEditing(null))}
      />
    </Card>
  );
}

// --- 添加来源 ---------------------------------------------------------------------

function AddSourceTab({ profile, onCreated }: { profile: string; onCreated: () => void }) {
  const create = useCreateResearchSource(profile);
  const [title, setTitle] = useState('');
  const [url, setUrl] = useState('');
  const [kind, setKind] = useState('web');
  const [status, setStatus] = useState('inbox');
  const [visibility, setVisibility] = useState('private');
  const [tags, setTags] = useState('');
  const [authors, setAuthors] = useState('');
  const [published, setPublished] = useState('');
  const [summary, setSummary] = useState('');
  const [notes, setNotes] = useState('');

  function submit(event: FormEvent) {
    event.preventDefault();
    if (!title.trim()) return;
    create.mutate(
      { title: title.trim(), url: url.trim(), kind, status, visibility, tags: parseList(tags), authors: parseList(authors), published: published.trim(), summary, notes },
      {
        onSuccess: (result) => {
          notifications.show({ color: 'green', title: '已收录', message: `${result.source.title} 已加入来源收件箱。` });
          setTitle(''); setUrl(''); setTags(''); setAuthors(''); setPublished(''); setSummary(''); setNotes('');
          onCreated();
        },
        onError: (error) => {
          const duplicate = error instanceof ApiError && error.status === 409;
          notifications.show({
            color: duplicate ? 'yellow' : 'red',
            title: duplicate ? '来源已存在' : '收录失败',
            message: duplicate ? '这个链接已经在收件箱里了，不会重复收录。' : errorMessage(error),
          });
        },
      },
    );
  }

  return (
    <Card withBorder radius="md" p="lg" style={panelStyle}>
      <SectionHeader icon={<IconPlus size={17} />} title="添加来源" description="手动收录一条来源。相同链接会自动去重；论文的 PDF 仍在论文库中导入。" />
      <form onSubmit={submit}>
        <Stack gap="sm">
          <SimpleGrid cols={{ base: 1, md: 2 }}>
            <TextInput label="标题" required placeholder="例如：Diffusion Policy" value={title} onChange={(event) => setTitle(event.currentTarget.value)} />
            <TextInput label="链接" placeholder="https://…" value={url} onChange={(event) => setUrl(event.currentTarget.value)} />
          </SimpleGrid>
          <SimpleGrid cols={{ base: 1, sm: 3 }}>
            <Select label="类型" value={kind} onChange={(value) => setKind(value ?? 'web')} data={options(FALLBACK_KINDS, KIND_LABELS)} allowDeselect={false} />
            <Select label="状态" value={status} onChange={(value) => setStatus(value ?? 'inbox')} data={options(FALLBACK_STATUSES, STATUS_LABELS)} allowDeselect={false} />
            <Select label="可见性" value={visibility} onChange={(value) => setVisibility(value ?? 'private')} data={options(VISIBILITIES, VISIBILITY_LABELS)} allowDeselect={false} />
          </SimpleGrid>
          <SimpleGrid cols={{ base: 1, sm: 3 }}>
            <TextInput label="标签" description="逗号分隔" value={tags} onChange={(event) => setTags(event.currentTarget.value)} />
            <TextInput label="作者" description="逗号分隔" value={authors} onChange={(event) => setAuthors(event.currentTarget.value)} />
            <TextInput label="发表时间" description="可选，如 2026-03" value={published} onChange={(event) => setPublished(event.currentTarget.value)} />
          </SimpleGrid>
          <Textarea label="摘要" autosize minRows={2} maxRows={6} value={summary} onChange={(event) => setSummary(event.currentTarget.value)} />
          <Textarea label="笔记" autosize minRows={2} maxRows={6} value={notes} onChange={(event) => setNotes(event.currentTarget.value)} />
          <Group justify="flex-end">
            <Button type="submit" loading={create.isPending} disabled={!title.trim()} leftSection={<IconPlus size={15} />}>收录来源</Button>
          </Group>
        </Stack>
      </form>
    </Card>
  );
}

// --- 连接器 -----------------------------------------------------------------------

type JobState = { label: string; phase: string; message: string } | null;

/** One SSE-backed job at a time; the stream closes on unmount/profile switch. */
function useConnectorJob(profile: string) {
  const [job, setJob] = useState<JobState>(null);
  const stopRef = useRef<(() => void) | null>(null);
  const stop = () => {
    stopRef.current?.();
    stopRef.current = null;
  };
  useEffect(() => {
    setJob(null);
    return stop;
  }, [profile]);

  function follow(
    created: JobCreateResponse,
    jobLabel: string,
    handlers: { onDone: (result: Record<string, unknown> | null | undefined) => void; onError: (message: string) => void },
  ) {
    stop();
    const jobId = created.job_id;
    setJob({ label: jobLabel, phase: created.job.phase || 'queued', message: created.job.message || '' });
    stopRef.current = streamJob(profile, jobId, {
      onProgress: (frame) =>
        setJob((prev) => (prev ? { ...prev, phase: frame.event?.phase || prev.phase, message: frame.event?.message || prev.message } : prev)),
      onDone: (frame) => {
        stop();
        setJob(null);
        handlers.onDone(frame.result);
      },
      onError: (frame) => {
        stop();
        setJob(null);
        handlers.onError(frame?.error?.message || '进度流中断，请稍后重试。');
      },
    });
  }

  return { job, follow };
}

const METADATA_ONLY = '__metadata_only__';

function CandidatePicker({
  preview,
  libraryNodes,
  importing,
  onImport,
  onDismiss,
}: {
  preview: ResearchConnectorPreview;
  libraryNodes: Array<{ id: string; path: string }>;
  importing: boolean;
  onImport: (fingerprints: string[], target: ResearchImportTarget) => void;
  onDismiss: () => void;
}) {
  const [picked, setPicked] = useState<Set<string>>(new Set());
  const [target, setTarget] = useState('');
  const candidates = preview.candidates ?? [];
  useEffect(() => {
    setPicked(new Set((preview.candidates ?? []).filter((row) => row.selected && !row.duplicate?.is_duplicate).map((row) => row.fingerprint)));
  }, [preview]);

  const targetValue: ResearchImportTarget =
    target === METADATA_ONLY ? { kind: 'metadata_only', node_id: '' } : target ? { kind: 'collection', node_id: target } : { kind: 'source_inbox', node_id: '' };

  return (
    <Paper withBorder radius="md" p="md" style={{ ...rowStyle, borderColor: 'rgba(220, 174, 85, 0.24)' }} data-testid="connector-candidates">
      <Group justify="space-between" mb="sm">
        <div>
          <Text fw={700}>候选来源 · {label(PROVIDER_LABELS, preview.provider)}</Text>
          <Text size="xs" c={chrome.dim} mt={2}>发现 {preview.discovered} · 可导入 {preview.importable} · 重复 {preview.skipped}</Text>
        </div>
        <Button size="xs" variant="subtle" color="gray" onClick={onDismiss}>收起</Button>
      </Group>
      {(preview.warnings ?? []).map((warning) => <Alert key={warning} color="yellow" variant="light" mb="xs">{warning}</Alert>)}
      {candidates.length === 0 ? (
        <Text size="sm" c={chrome.dim}>没有发现候选。试试换一个查询词。</Text>
      ) : (
        <Stack gap="xs">
          {candidates.map((candidate) => {
            const item = candidate.item as { title?: string; url?: string; kind?: string; published?: string; summary?: string };
            const duplicate = Boolean(candidate.duplicate?.is_duplicate);
            return (
              <Group key={candidate.fingerprint} align="flex-start" wrap="nowrap" gap="sm" style={{ opacity: duplicate ? 0.6 : 1 }}>
                <Checkbox
                  mt={3}
                  aria-label={`选择 ${item.title ?? candidate.fingerprint}`}
                  checked={picked.has(candidate.fingerprint)}
                  disabled={duplicate}
                  onChange={(event) => {
                    const checked = event.currentTarget.checked;
                    setPicked((current) => {
                      const next = new Set(current);
                      if (checked) next.add(candidate.fingerprint);
                      else next.delete(candidate.fingerprint);
                      return next;
                    });
                  }}
                />
                <div style={{ minWidth: 0, flex: 1 }}>
                  <Text size="sm" fw={600} lineClamp={1}>{item.title || candidate.fingerprint}</Text>
                  <Text size="xs" c={chrome.dim} lineClamp={1}>{[item.kind && label(KIND_LABELS, item.kind), item.published, item.url].filter(Boolean).join(' · ')}</Text>
                  {item.summary && <Text size="xs" c={chrome.dim} lineClamp={2} mt={2}>{item.summary}</Text>}
                  {duplicate && <Badge size="xs" color="gray" variant="light" mt={4}>已在收件箱：{String(candidate.duplicate?.existing_source_id ?? '')}</Badge>}
                </div>
              </Group>
            );
          })}
        </Stack>
      )}
      <Group mt="md" align="flex-end" justify="space-between">
        <Select
          label="导入到"
          w={280}
          value={target}
          onChange={(value) => setTarget(value ?? '')}
          allowDeselect={false}
          data={[
            { value: '', label: '来源收件箱' },
            { value: METADATA_ONLY, label: '仅元数据' },
            ...libraryNodes.map((node) => ({ value: node.id, label: `论文库 · ${node.path}` })),
          ]}
        />
        <Button leftSection={<IconDownload size={15} />} disabled={picked.size === 0} loading={importing} onClick={() => onImport([...picked], targetValue)}>
          导入选中 {picked.size}
        </Button>
      </Group>
    </Paper>
  );
}

function connectorSummary(row: ResearchConnector): string {
  const result = row.last_result as { discovered?: number; imported?: number; skipped?: number };
  if (!row.last_run) return '尚未运行';
  return `上次 ${row.last_run.replace('T', ' ').slice(0, 16)} · 发现 ${result.discovered ?? 0} · 导入 ${result.imported ?? 0} · 跳过 ${result.skipped ?? 0}`;
}

function ConnectorsTab({ profile }: { profile: string }) {
  const connectors = useResearchConnectors(profile);
  const upsert = useUpsertResearchConnector(profile);
  const previewJob = usePreviewResearchConnector(profile);
  const importJob = useImportResearchConnector(profile);
  const previewManual = usePreviewManualItems(profile);
  const importManual = useImportManualItems(profile);
  const refresh = useRefreshAfterConnectorJob(profile);
  const { job, follow } = useConnectorJob(profile);

  const [provider, setProvider] = useState('arxiv');
  const [connectorId, setConnectorId] = useState('');
  const [query, setQuery] = useState('');
  const [enabled, setEnabled] = useState(true);
  const [privacy, setPrivacy] = useState('private');
  const [optionsRaw, setOptionsRaw] = useState('');
  const [optionsError, setOptionsError] = useState('');

  const [manualProvider, setManualProvider] = useState('x_twitter');
  const [manualPrivacy, setManualPrivacy] = useState('private');
  const [manualRaw, setManualRaw] = useState('');

  // The candidate list being reviewed: a saved connector or a pasted list.
  const [preview, setPreview] = useState<{ source: 'connector' | 'manual'; connectorId: string; raw: string; privacy: string; data: ResearchConnectorPreview } | null>(null);
  const [jobError, setJobError] = useState<{ message: string; retry: () => void } | null>(null);

  if (connectors.isPending) return <Center py="xl"><Loader /></Center>;
  if (connectors.isError) return <LoadError title="连接器加载失败" error={connectors.error} onRetry={() => void connectors.refetch()} />;

  const data = connectors.data;
  const providers = data.providers?.length ? data.providers : Object.keys(PROVIDER_LABELS);
  const savedConnectors = data.connectors ?? [];
  const autoProviders = data.auto_providers ?? [];
  const busy = Boolean(job) || previewJob.isPending || importJob.isPending;

  const imported = (result: ResearchConnectorImportResult) => {
    refresh();
    notifications.show({ color: 'green', title: '导入完成', message: `导入 ${result.imported} 条，跳过 ${result.skipped} 条。` });
    (result.warnings ?? []).forEach((warning) => notifications.show({ color: 'yellow', title: '提示', message: warning }));
  };

  function runPreview(id: string) {
    setJobError(null);
    previewJob.mutate(id, {
      onSuccess: (created) =>
        follow(created, '正在预览候选', {
          onDone: (result) => {
            void connectors.refetch();
            setPreview({ source: 'connector', connectorId: id, raw: '', privacy: '', data: result as unknown as ResearchConnectorPreview });
          },
          onError: (message) => setJobError({ message, retry: () => runPreview(id) }),
        }),
      onError: (error) => setJobError({ message: errorMessage(error), retry: () => runPreview(id) }),
    });
  }

  function runImport(id: string, fingerprints: string[], target: ResearchImportTarget) {
    setJobError(null);
    importJob.mutate(
      { connectorId: id, fingerprints, target },
      {
        onSuccess: (created) =>
          follow(created, fingerprints.length ? '正在导入选中候选' : '正在运行连接器', {
            onDone: (result) => {
              setPreview(null);
              void connectors.refetch();
              imported(result as unknown as ResearchConnectorImportResult);
            },
            onError: (message) => setJobError({ message, retry: () => runImport(id, fingerprints, target) }),
          }),
        onError: (error) => setJobError({ message: errorMessage(error), retry: () => runImport(id, fingerprints, target) }),
      },
    );
  }

  function saveConnector(event: FormEvent) {
    event.preventDefault();
    let parsed: Record<string, unknown> = {};
    if (optionsRaw.trim()) {
      try {
        const value: unknown = JSON.parse(optionsRaw);
        if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('需要一个 JSON 对象');
        parsed = value as Record<string, unknown>;
      } catch (error) {
        setOptionsError(`高级选项不是合法 JSON 对象：${errorMessage(error)}`);
        return;
      }
    }
    setOptionsError('');
    upsert.mutate(
      { provider, connector_id: connectorId.trim(), query: query.trim(), enabled, privacy_default: privacy, options: parsed },
      {
        onSuccess: () => {
          notifications.show({ color: 'green', title: '连接器已保存', message: `${label(PROVIDER_LABELS, provider)} · ${query.trim() || '默认查询'}` });
          setConnectorId(''); setQuery(''); setOptionsRaw('');
        },
        onError: (error) => notifications.show({ color: 'red', title: '保存失败', message: errorMessage(error) }),
      },
    );
  }

  function editConnector(row: ResearchConnector) {
    setProvider(row.provider);
    setConnectorId(row.id);
    setQuery(row.query);
    setEnabled(row.enabled);
    setPrivacy(row.privacy_default);
    setOptionsRaw(Object.keys(row.options ?? {}).length ? JSON.stringify(row.options, null, 2) : '');
  }

  return (
    <Stack gap="lg">
      {job && (
        <Alert color="brand" variant="light" icon={<Loader size={16} />} title={job.label}>
          {job.message || '任务已排队…'}
        </Alert>
      )}
      {jobError && (
        <Alert color="red" title="连接器任务失败" withCloseButton onClose={() => setJobError(null)}>
          <Stack gap="xs" align="flex-start">
            <Text size="sm">{jobError.message}</Text>
            <Button size="xs" variant="light" color="red" leftSection={<IconRefresh size={14} />} onClick={jobError.retry}>重试</Button>
          </Stack>
        </Alert>
      )}
      {preview && (
        <CandidatePicker
          preview={preview.data}
          libraryNodes={data.library_nodes ?? []}
          importing={busy || importManual.isPending}
          onDismiss={() => setPreview(null)}
          onImport={(fingerprints, target) => {
            if (preview.source === 'connector') {
              runImport(preview.connectorId, fingerprints, target);
              return;
            }
            importManual.mutate(
              { provider: preview.data.provider, raw_items: preview.raw, fingerprints, privacy_default: preview.privacy, target },
              {
                onSuccess: (result) => {
                  setPreview(null);
                  setManualRaw('');
                  imported(result);
                },
                onError: (error) => notifications.show({ color: 'red', title: '导入失败', message: errorMessage(error) }),
              },
            );
          }}
        />
      )}

      <Card withBorder radius="md" p="lg" style={panelStyle}>
        <SectionHeader icon={<IconPlugConnected size={17} />} title="已保存的连接器" description="arXiv、Semantic Scholar、GitHub 支持自动发现；先预览候选再挑选导入，重复项自动跳过。" />
        {savedConnectors.length === 0 ? (
          <Text size="sm" c={chrome.dim}>还没有连接器。在下方配置第一个，或直接粘贴链接手动导入。</Text>
        ) : (
          <Stack gap="sm">
            {savedConnectors.map((row) => {
              const error = (row.last_result as { error?: string }).error;
              return (
                <Paper key={row.id} withBorder radius="md" p="md" style={rowStyle} data-testid="connector-row">
                  <Group justify="space-between" align="flex-start" wrap="nowrap">
                    <div style={{ minWidth: 0 }}>
                      <Group gap={6}>
                        <Text fw={650}>{label(PROVIDER_LABELS, row.provider)}</Text>
                        <Badge size="sm" variant="light" color={row.enabled ? 'brand' : 'gray'}>{row.enabled ? '已启用' : '已停用'}</Badge>
                        <Badge size="sm" variant="outline" color={row.status === 'failed' ? 'red' : row.status === 'ok' ? 'green' : 'gray'}>{row.status === 'failed' ? '失败' : row.status === 'ok' ? '正常' : '空闲'}</Badge>
                      </Group>
                      <Text size="sm" mt={4}>{row.query || '（无查询词）'}</Text>
                      <Text size="xs" c={chrome.dim} mt={2}>{row.id} · {connectorSummary(row)}</Text>
                      {error && <Text size="xs" c="red.4" mt={2}>{error}</Text>}
                    </div>
                    <Group gap="xs" wrap="nowrap">
                      <Button size="xs" variant="default" onClick={() => editConnector(row)}>编辑</Button>
                      <Button size="xs" variant="light" leftSection={<IconSearch size={13} />} disabled={busy || !row.enabled} onClick={() => runPreview(row.id)}>预览候选</Button>
                      <Button size="xs" variant="subtle" disabled={busy || !row.enabled} onClick={() => runImport(row.id, [], { kind: 'source_inbox', node_id: '' })}>全部导入</Button>
                    </Group>
                  </Group>
                </Paper>
              );
            })}
          </Stack>
        )}
      </Card>

      <SimpleGrid cols={{ base: 1, lg: 2 }} spacing="lg">
        <Card withBorder radius="md" p="lg" style={panelStyle}>
          <SectionHeader icon={<IconDeviceFloppy size={17} />} title="配置连接器" description="连接器配置不保存 token、cookie 或 API key；凭据只放在服务端环境变量。" />
          <form onSubmit={saveConnector}>
            <Stack gap="sm">
              <SimpleGrid cols={{ base: 1, sm: 2 }}>
                <Select label="来源平台" value={provider} onChange={(value) => setProvider(value ?? 'arxiv')} data={options(providers, PROVIDER_LABELS)} allowDeselect={false} />
                <TextInput label="连接器 ID" description="留空自动生成；填已有 ID 即覆盖" value={connectorId} onChange={(event) => setConnectorId(event.currentTarget.value)} />
              </SimpleGrid>
              <TextInput label="查询词" placeholder="例如：vision language action" value={query} onChange={(event) => setQuery(event.currentTarget.value)} />
              <Group grow align="flex-end">
                <Select label="默认可见性" value={privacy} onChange={(value) => setPrivacy(value ?? 'private')} data={options(VISIBILITIES, VISIBILITY_LABELS)} allowDeselect={false} />
                <Switch label="启用" checked={enabled} onChange={(event) => setEnabled(event.currentTarget.checked)} mb={8} />
              </Group>
              <Textarea label="高级选项（JSON，可选）" placeholder='{"limit": 10}' autosize minRows={2} maxRows={6} value={optionsRaw} error={optionsError || undefined} onChange={(event) => setOptionsRaw(event.currentTarget.value)} styles={{ input: { fontFamily: 'monospace' } }} />
              {!autoProviders.includes(provider) && (
                <Text size="xs" c={chrome.dim}>{label(PROVIDER_LABELS, provider)} 不支持自动发现，建议用右侧的手动导入。</Text>
              )}
              <Group justify="flex-end"><Button type="submit" loading={upsert.isPending} leftSection={<IconDeviceFloppy size={15} />}>保存连接器</Button></Group>
            </Stack>
          </form>
        </Card>

        <Card withBorder radius="md" p="lg" style={panelStyle}>
          <SectionHeader icon={<IconDownload size={17} />} title="手动导入" description="粘贴链接（每行一个）、带表头的 CSV 或 JSON 列表；自动化不可用时也能导入。" />
          <form
            onSubmit={(event) => {
              event.preventDefault();
              if (!manualRaw.trim()) return;
              previewManual.mutate(
                { provider: manualProvider, raw_items: manualRaw },
                {
                  onSuccess: (result) => setPreview({ source: 'manual', connectorId: '', raw: manualRaw, privacy: manualPrivacy, data: result }),
                  onError: (error) => notifications.show({ color: 'red', title: '解析失败', message: errorMessage(error) }),
                },
              );
            }}
          >
            <Stack gap="sm">
              <SimpleGrid cols={{ base: 1, sm: 2 }}>
                <Select label="来源平台" value={manualProvider} onChange={(value) => setManualProvider(value ?? 'x_twitter')} data={options(providers, PROVIDER_LABELS)} allowDeselect={false} />
                <Select label="默认可见性" value={manualPrivacy} onChange={(value) => setManualPrivacy(value ?? 'private')} data={options(VISIBILITIES, VISIBILITY_LABELS)} allowDeselect={false} />
              </SimpleGrid>
              <Textarea label="内容" placeholder={'https://example.com/post-1\nhttps://example.com/post-2'} autosize minRows={4} maxRows={10} value={manualRaw} onChange={(event) => setManualRaw(event.currentTarget.value)} />
              <Group justify="flex-end"><Button type="submit" variant="light" loading={previewManual.isPending} disabled={!manualRaw.trim()} leftSection={<IconSearch size={15} />}>预览</Button></Group>
            </Stack>
          </form>
        </Card>
      </SimpleGrid>
    </Stack>
  );
}

// --- 研究 AI ----------------------------------------------------------------------

// Research AI routing lives in Settings → 档案 → 研究与阅读 (one place for
// all per-profile AI choices); this tab only points there for old links.
function AITab({ profile }: { profile: string }) {
  return (
    <Card withBorder radius="md" p="lg" style={panelStyle}>
      <SectionHeader
        icon={<IconRobot size={17} />}
        title="研究 AI 已移到设置"
        description="论文翻译、快速分析、问答、深度研读等动作的执行方式和模型，现在统一在「设置 → 档案 → 研究与阅读」里配置。"
      />
      <Group mt="md">
        <Button component={Link} to={`/settings/research?profile=${encodeURIComponent(profile)}`} leftSection={<IconRobot size={15} />}>
          打开研究与阅读设置
        </Button>
      </Group>
    </Card>
  );
}

// --- page -------------------------------------------------------------------------

const TABS = ['inbox', 'add', 'connectors', 'ai'] as const;
type TabValue = (typeof TABS)[number];

export function ResearchSourcesPage() {
  const { name = '' } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const requested = searchParams.get('tab') as TabValue | null;
  const tab: TabValue = requested && TABS.includes(requested) ? requested : 'inbox';
  const setTab = (value: string | null) => {
    const next = new URLSearchParams(searchParams);
    if (!value || value === 'inbox') next.delete('tab');
    else next.set('tab', value);
    setSearchParams(next, { replace: true });
  };

  return (
    <Stack gap="lg" pb="xl">
      <Group justify="space-between" align="flex-end">
        <div>
          <Text size="xs" fw={700} c={chrome.goldText}>研究台 · 来源收件箱</Text>
          <Title order={2} mt={4}>{name} · 研究来源</Title>
          <Text size="sm" c={chrome.dim} mt={5}>收录、整理和批量导入研究来源；阅读与论文整理仍在研究台和论文库。</Text>
        </div>
        <Button component={Link} to={`/p/${encodeURIComponent(name)}/research`} variant="default" leftSection={<IconArrowLeft size={15} />}>
          返回研究台
        </Button>
      </Group>
      <Tabs value={tab} onChange={setTab} keepMounted={false}>
        <Tabs.List mb="md">
          <Tabs.Tab value="inbox" leftSection={<IconInbox size={15} />}>来源收件箱</Tabs.Tab>
          <Tabs.Tab value="add" leftSection={<IconPlus size={15} />}>添加来源</Tabs.Tab>
          <Tabs.Tab value="connectors" leftSection={<IconPlugConnected size={15} />}>连接器</Tabs.Tab>
          <Tabs.Tab value="ai" leftSection={<IconRobot size={15} />}>研究 AI</Tabs.Tab>
        </Tabs.List>
        <Tabs.Panel value="inbox"><InboxTab profile={name} /></Tabs.Panel>
        <Tabs.Panel value="add"><AddSourceTab profile={name} onCreated={() => setTab('inbox')} /></Tabs.Panel>
        <Tabs.Panel value="connectors"><ConnectorsTab profile={name} /></Tabs.Panel>
        <Tabs.Panel value="ai"><AITab profile={name} /></Tabs.Panel>
      </Tabs>
    </Stack>
  );
}
