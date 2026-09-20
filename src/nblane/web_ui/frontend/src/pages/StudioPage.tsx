import {
  Alert,
  Badge,
  Button,
  Card,
  Center,
  Group,
  Loader,
  MultiSelect,
  Radio,
  Select,
  Stack,
  Table,
  Tabs,
  Text,
  Textarea,
  TextInput,
  Title,
} from '@mantine/core';
import {
  IconBolt,
  IconChecklist,
  IconDeviceFloppy,
  IconPlus,
  IconUpload,
} from '@tabler/icons-react';
import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';

import { ApiError } from '../api/client';
import { MutationErrorAlert } from '../components/ConflictAlert';
import {
  useCheckStudioPost,
  useCreateStudioDraft,
  useCreateStudioPost,
  useInitStudio,
  useJdMatch,
  usePreviewStudioCandidate,
  usePublishStudioPost,
  useSaveStudioPost,
  useStudio,
  useStudioPost,
} from '../api/hooks';
import type {
  StudioCandidateResponse,
  StudioPost,
  StudioPostDetail,
  StudioPostSaveRequest,
  StudioResponse,
  StudioSourceOption,
  StudioValidationResponse,
} from '../api/types';

const STATUS_LABELS: Record<string, string> = {
  draft: '草稿',
  published: '已发布',
  archived: '已归档',
};
const POST_STATUSES = Object.keys(STATUS_LABELS);

const TARGET_LABELS: Record<string, string> = {
  blog: '博客草稿',
  resume: '简历要点预览',
  project: '项目更新草稿',
};

function csvToList(value: string): string[] {
  return value
    .split(/[,\n]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function listToCsv(value: string[] | undefined): string {
  return (value ?? []).join(', ');
}

interface PostDraft {
  title: string;
  date: string;
  status: string;
  summary: string;
  cover: string;
  tags: string;
  relatedEvidence: string;
  relatedClaims: string;
  body: string;
}

function draftFromPost(post: StudioPostDetail): PostDraft {
  return {
    title: post.title ?? '',
    date: post.date ?? '',
    status: post.status ?? 'draft',
    summary: post.summary ?? '',
    cover: post.cover ?? '',
    tags: listToCsv(post.tags),
    relatedEvidence: listToCsv(post.related_evidence),
    relatedClaims: listToCsv(post.related_claims),
    body: post.body ?? '',
  };
}

function draftToSaveRequest(draft: PostDraft): StudioPostSaveRequest {
  return {
    title: draft.title,
    date: draft.date,
    status: draft.status,
    summary: draft.summary,
    cover: draft.cover,
    tags: csvToList(draft.tags),
    related_evidence: csvToList(draft.relatedEvidence),
    related_claims: csvToList(draft.relatedClaims),
    body: draft.body,
  };
}

/** Refetch every studio query (overview + open post) after a 412 conflict. */
function useRefreshStudio() {
  const { name = '' } = useParams();
  const queryClient = useQueryClient();
  return () => void queryClient.invalidateQueries({ queryKey: ['profiles', name, 'studio'] });
}

function MutationError({ error, title }: { error: unknown; title: string }) {
  const refreshStudio = useRefreshStudio();
  return <MutationErrorAlert error={error} title={title} onRefetch={refreshStudio} />;
}

function CreatePostCard({
  etag,
  onCreated,
}: {
  etag: string;
  onCreated: (slug: string) => void;
}) {
  const { name = '' } = useParams();
  const [title, setTitle] = useState('');
  const create = useCreateStudioPost(name);

  const submit = () => {
    if (!title.trim()) {
      return;
    }
    create.mutate(
      { body: { title: title.trim(), summary: '', tags: [], body: '' }, etag },
      {
        onSuccess: (result) => {
          setTitle('');
          onCreated(result.post.slug);
        },
      },
    );
  };

  return (
    <Card withBorder radius="md" data-testid="create-post-form">
      <Group align="flex-end">
        <TextInput
          label="新建博客草稿"
          placeholder="标题"
          value={title}
          onChange={(event) => setTitle(event.currentTarget.value)}
          style={{ flex: 1 }}
        />
        <Button
          leftSection={<IconPlus size={14} />}
          onClick={submit}
          loading={create.isPending}
          disabled={!title.trim()}
        >
          创建
        </Button>
      </Group>
      {create.isError && <MutationError error={create.error} title="创建失败" />}
    </Card>
  );
}

function PostEditor({ slug }: { slug: string }) {
  const { name = '' } = useParams();
  const detail = useStudioPost(name, slug);

  if (detail.isPending) {
    return (
      <Center py="md">
        <Loader size="sm" />
      </Center>
    );
  }
  if (detail.isError || !detail.data) {
    return (
      <Alert color="red" title="加载失败">
        {detail.error?.message ?? '无法加载博客文章。'}
      </Alert>
    );
  }
  return (
    <PostEditorForm
      key={slug}
      slug={slug}
      post={detail.data.post}
      etag={detail.data.etag}
    />
  );
}

function PostEditorForm({
  slug,
  post,
  etag,
}: {
  slug: string;
  post: StudioPostDetail;
  etag: string;
}) {
  const { name = '' } = useParams();
  const [draft, setDraft] = useState<PostDraft>(() => draftFromPost(post));
  const [dirty, setDirty] = useState(false);
  const [checkResult, setCheckResult] = useState<StudioValidationResponse | null>(null);
  const save = useSaveStudioPost(name);
  const check = useCheckStudioPost(name);
  const publish = usePublishStudioPost(name);

  // The editor is keyed by slug only, so refetches re-render instead of
  // remounting. Follow server-side changes only while the draft is clean;
  // a dirty draft always wins.
  const lastSynced = useRef(post);
  useEffect(() => {
    if (!dirty && post !== lastSynced.current) {
      lastSynced.current = post;
      setDraft(draftFromPost(post));
    }
  }, [post, dirty]);

  const set = <K extends keyof PostDraft>(field: K, value: PostDraft[K]) => {
    setDirty(true);
    setDraft((prev) => ({ ...prev, [field]: value }));
  };

  const runCheck = () =>
    check.mutate(
      { slug, body: draftToSaveRequest(draft) },
      { onSuccess: (result) => setCheckResult(result) },
    );

  return (
    <Card withBorder radius="md" data-testid="post-editor">
      <Stack gap="sm">
        <Group gap="sm">
          <Title order={3}>{post.title || slug}</Title>
          <Badge variant="light">{STATUS_LABELS[draft.status] ?? draft.status}</Badge>
          <Text size="xs" c="dimmed">
            {slug}
          </Text>
        </Group>
        <Group grow align="flex-start">
          <TextInput
            label="标题"
            value={draft.title}
            onChange={(event) => set('title', event.currentTarget.value)}
            required
          />
          <TextInput
            label="日期"
            type="date"
            value={draft.date}
            onChange={(event) => set('date', event.currentTarget.value)}
          />
          <Select
            label="状态"
            data={POST_STATUSES.map((status) => ({
              value: status,
              label: STATUS_LABELS[status],
            }))}
            value={draft.status}
            onChange={(value) => set('status', value ?? 'draft')}
          />
        </Group>
        <Textarea
          label="摘要"
          value={draft.summary}
          onChange={(event) => set('summary', event.currentTarget.value)}
          minRows={2}
        />
        <Group grow align="flex-start">
          <TextInput
            label="封面"
            value={draft.cover}
            onChange={(event) => set('cover', event.currentTarget.value)}
          />
          <TextInput
            label="标签(逗号分隔)"
            value={draft.tags}
            onChange={(event) => set('tags', event.currentTarget.value)}
          />
        </Group>
        <Group grow align="flex-start">
          <TextInput
            label="关联证据(逗号分隔)"
            value={draft.relatedEvidence}
            onChange={(event) => set('relatedEvidence', event.currentTarget.value)}
          />
          <TextInput
            label="关联断言(逗号分隔)"
            value={draft.relatedClaims}
            onChange={(event) => set('relatedClaims', event.currentTarget.value)}
          />
        </Group>
        {post.has_math && (
          <Alert color="blue" title="公式安全模式" data-testid="math-notice">
            检测到公式,正文使用 Markdown 源码编辑器,避免结构化编辑器改写公式。
          </Alert>
        )}
        <Textarea
          label="正文 (Markdown)"
          value={draft.body}
          onChange={(event) => set('body', event.currentTarget.value)}
          minRows={12}
          autosize
          styles={{ input: { fontFamily: 'monospace' } }}
          data-testid="post-body"
        />
        <MutationError error={save.error} title="保存失败" />
        <MutationError error={publish.error} title="发布失败" />
        {checkResult && (
          <Alert
            color={checkResult.ok ? 'green' : 'red'}
            title={checkResult.ok ? '发布前检查通过' : '发布前检查未通过'}
            data-testid="check-result"
          >
            <Stack gap={4}>
              {(checkResult.errors ?? []).map((item) => (
                <Text key={item} size="sm">
                  · {item}
                </Text>
              ))}
              {(checkResult.warnings ?? []).map((item) => (
                <Text key={item} size="sm" c="dimmed">
                  · {item}
                </Text>
              ))}
            </Stack>
          </Alert>
        )}
        <Group gap="sm" wrap="wrap">
          <Button
            leftSection={<IconDeviceFloppy size={14} />}
            onClick={() =>
              save.mutate(
                { slug, body: draftToSaveRequest(draft), etag },
                { onSuccess: () => setDirty(false) },
              )
            }
            loading={save.isPending}
            disabled={!draft.title.trim()}
          >
            保存
          </Button>
          <Button
            variant="default"
            leftSection={<IconChecklist size={14} />}
            onClick={runCheck}
            loading={check.isPending}
          >
            发布检查
          </Button>
          <Button
            variant="light"
            color="green"
            leftSection={<IconUpload size={14} />}
            onClick={() =>
              publish.mutate(
                { slug, body: draftToSaveRequest(draft), etag },
                { onSuccess: () => setDirty(false) },
              )
            }
            loading={publish.isPending}
            disabled={draft.status === 'published'}
            data-testid="publish-button"
          >
            发布
          </Button>
        </Group>
      </Stack>
    </Card>
  );
}

function BlogTab({
  studio,
  etag,
  selectedSlug,
  onSelect,
}: {
  studio: StudioResponse;
  etag: string;
  selectedSlug: string;
  onSelect: (slug: string) => void;
}) {
  const [statusFilter, setStatusFilter] = useState('');
  const posts = (studio.posts ?? []).filter(
    (post) => !statusFilter || post.status === statusFilter,
  );
  const counts = studio.summary?.status_counts ?? {};

  return (
    <Stack gap="md">
      <Group gap="xs" wrap="wrap" data-testid="studio-summary">
        {POST_STATUSES.map((status) => (
          <Badge
            key={status}
            color={statusFilter === status ? 'brand' : 'gray'}
            variant={statusFilter === status ? 'filled' : 'light'}
            style={{ cursor: 'pointer' }}
            onClick={() => setStatusFilter(statusFilter === status ? '' : status)}
          >
            {STATUS_LABELS[status]} {counts[status] ?? 0}
          </Badge>
        ))}
      </Group>

      <CreatePostCard etag={etag} onCreated={onSelect} />

      {posts.length === 0 ? (
        <Text c="dimmed" size="sm">
          暂无文章。
        </Text>
      ) : (
        <Card withBorder radius="md" p={0}>
          <Table highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>文章</Table.Th>
                <Table.Th>状态</Table.Th>
                <Table.Th>日期</Table.Th>
                <Table.Th />
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {posts.map((post: StudioPost) => (
                <Table.Tr key={post.slug} data-testid={`post-row-${post.slug}`}>
                  <Table.Td>
                    <Text size="sm" fw={500}>
                      {post.title || post.slug}
                    </Text>
                    <Text size="xs" c="dimmed">
                      {post.slug}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Badge size="sm" variant="light">
                      {STATUS_LABELS[post.status ?? ''] ?? post.status}
                    </Badge>
                  </Table.Td>
                  <Table.Td>
                    <Text size="xs" c="dimmed">
                      {post.date || '—'}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Button
                      size="compact-sm"
                      variant={selectedSlug === post.slug ? 'filled' : 'default'}
                      disabled={selectedSlug === post.slug}
                      onClick={() => onSelect(post.slug)}
                    >
                      {selectedSlug === post.slug ? '编辑中' : '编辑'}
                    </Button>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        </Card>
      )}

      {selectedSlug && <PostEditor slug={selectedSlug} />}
    </Stack>
  );
}

function GenerateTab({ studio, etag }: { studio: StudioResponse; etag: string }) {
  const { name = '' } = useParams();
  const [source, setSource] = useState('claims');
  const [target, setTarget] = useState('blog');
  const [claimIds, setClaimIds] = useState<string[]>([]);
  const [evidenceId, setEvidenceId] = useState('');
  const [projectId, setProjectId] = useState('');
  const [preview, setPreview] = useState<StudioCandidateResponse | null>(null);
  const previewMutation = usePreviewStudioCandidate(name);
  const createDraft = useCreateStudioDraft(name);

  const options = studio.options ?? { claims: [], evidence: [], projects: [] };
  const optionData = (rows: StudioSourceOption[]) =>
    rows.map((row) => ({ value: row.id, label: row.label || row.id }));

  const request = {
    target,
    source,
    claim_ids: claimIds,
    evidence_id: evidenceId,
    project_id: projectId,
  };

  const canCreate = preview !== null && preview.kind !== 'resume';

  return (
    <Stack gap="md">
      <Text size="sm" c="dimmed">
        先选择已审阅证据或已确认断言,再生成可追溯的公开输出候选。未配置 LLM
        时使用规则模板生成。
      </Text>
      <Group grow align="flex-start">
        <Radio.Group
          label="来源"
          value={source}
          onChange={setSource}
        >
          <Group mt="xs">
            <Radio value="claims" label="已确认断言" />
            <Radio value="evidence" label="证据" />
          </Group>
        </Radio.Group>
        <Select
          label="输出目标"
          data={Object.entries(TARGET_LABELS).map(([value, label]) => ({
            value,
            label,
          }))}
          value={target}
          onChange={(value) => setTarget(value ?? 'blog')}
        />
        {target === 'project' && (
          <Select
            label="项目"
            data={optionData(options.projects ?? [])}
            value={projectId || null}
            onChange={(value) => setProjectId(value ?? '')}
            placeholder="选择项目"
          />
        )}
      </Group>
      {source === 'claims' ? (
        <MultiSelect
          label="断言"
          data={optionData(options.claims ?? [])}
          value={claimIds}
          onChange={setClaimIds}
          placeholder={options.claims?.length ? '选择断言' : '暂无已确认断言'}
        />
      ) : (
        <Select
          label="证据"
          data={optionData(options.evidence ?? [])}
          value={evidenceId || null}
          onChange={(value) => setEvidenceId(value ?? '')}
          placeholder={options.evidence?.length ? '选择证据' : '暂无证据'}
        />
      )}
      <MutationError error={previewMutation.error} title="生成预览失败" />
      <MutationError error={createDraft.error} title="创建草稿失败" />
      <Group>
        <Button
          leftSection={<IconBolt size={14} />}
          onClick={() =>
            previewMutation.mutate(request, {
              onSuccess: (result) => setPreview(result),
            })
          }
          loading={previewMutation.isPending}
          disabled={source === 'evidence' && !evidenceId}
        >
          生成预览
        </Button>
        <Button
          variant="default"
          onClick={() =>
            createDraft.mutate(
              { body: request, etag },
              { onSuccess: () => setPreview(null) },
            )
          }
          loading={createDraft.isPending}
          disabled={!canCreate}
          data-testid="create-draft-button"
        >
          确认创建草稿
        </Button>
      </Group>
      {preview && (
        <Card withBorder radius="md" data-testid="candidate-preview">
          <Stack gap="xs">
            <Group gap="sm">
              <Badge variant="light">{TARGET_LABELS[target] ?? target}</Badge>
              <Text fw={500}>{String(preview.candidate?.title ?? '')}</Text>
            </Group>
            {!!preview.candidate?.summary && (
              <Text size="sm" c="dimmed">
                {String(preview.candidate.summary)}
              </Text>
            )}
            <Textarea
              label="正文预览"
              value={String(preview.candidate?.body ?? '')}
              readOnly
              minRows={8}
              autosize
              styles={{ input: { fontFamily: 'monospace' } }}
            />
          </Stack>
        </Card>
      )}
      {createDraft.isSuccess && createDraft.data && (
        <Alert color="green" title="草稿已创建" data-testid="draft-created">
          {createDraft.data.path}
        </Alert>
      )}
    </Stack>
  );
}

function JdMatchTab() {
  const { name = '' } = useParams();
  const [resumeMd, setResumeMd] = useState('');
  const [jdText, setJdText] = useState('');
  const jdMatch = useJdMatch(name);

  const unavailable =
    jdMatch.isError &&
    jdMatch.error instanceof ApiError &&
    jdMatch.error.status === 422 &&
    jdMatch.error.code === 'studio_jd_match_unavailable';

  return (
    <Stack gap="md">
      <Text size="sm" c="dimmed">
        粘贴目标 JD 与现有简历,生成证据支撑的匹配分析。
      </Text>
      <Textarea
        label="简历内容"
        value={resumeMd}
        onChange={(event) => setResumeMd(event.currentTarget.value)}
        minRows={6}
        autosize
      />
      <Textarea
        label="目标 JD(职位描述)"
        value={jdText}
        onChange={(event) => setJdText(event.currentTarget.value)}
        minRows={6}
        autosize
      />
      <Group>
        <Button
          onClick={() => jdMatch.mutate({ resume_md: resumeMd, jd_text: jdText })}
          loading={jdMatch.isPending}
          disabled={!resumeMd.trim() || !jdText.trim()}
        >
          分析 JD 匹配
        </Button>
      </Group>
      {unavailable && (
        <Alert color="yellow" title="AI 分析不可用" data-testid="jd-degraded">
          {jdMatch.error.message}。配置 LLM 后重试;其余功能不受影响。
        </Alert>
      )}
      {jdMatch.isError && !unavailable && (
        <Alert color="red" title="分析失败">
          {jdMatch.error.message}
        </Alert>
      )}
      {jdMatch.isSuccess && jdMatch.data && (
        <Card withBorder radius="md" data-testid="jd-analysis">
          <Text size="sm" style={{ whiteSpace: 'pre-wrap' }}>
            {jdMatch.data.analysis}
          </Text>
        </Card>
      )}
    </Stack>
  );
}

export function StudioPage() {
  const { name = '' } = useParams();
  const studio = useStudio(name);
  const init = useInitStudio(name);
  const [selectedSlug, setSelectedSlug] = useState('');

  if (studio.isPending) {
    return (
      <Center py="xl">
        <Loader />
      </Center>
    );
  }
  if (studio.isError || !studio.data) {
    return (
      <Alert color="red" title="加载失败">
        {studio.error?.message ?? '无法加载输出工作室。'}
      </Alert>
    );
  }

  const data = studio.data.data;
  const etag = studio.data.etag;

  return (
    <Stack gap="md">
      <Title order={2}>{name} · 输出工作室</Title>
      <Text size="sm" c="dimmed">
        从证据、断言与研究来源生成可追溯公开输出。
      </Text>

      {!data.initialized && (
        <Alert color="yellow" title="公开层未初始化" data-testid="init-needed">
          <Group justify="space-between">
            <Text size="sm">此档案尚未初始化公开层。</Text>
            <Button
              size="compact-sm"
              onClick={() => init.mutate({ etag })}
              loading={init.isPending}
            >
              初始化公开层
            </Button>
          </Group>
        </Alert>
      )}
      {init.isError && <MutationError error={init.error} title="初始化失败" />}

      <Tabs defaultValue="blog">
        <Tabs.List>
          <Tabs.Tab value="blog">博客</Tabs.Tab>
          <Tabs.Tab value="generate">从证据生成</Tabs.Tab>
          <Tabs.Tab value="jd">JD 匹配</Tabs.Tab>
        </Tabs.List>
        <Tabs.Panel value="blog" pt="md">
          <BlogTab
            studio={data}
            etag={etag}
            selectedSlug={selectedSlug}
            onSelect={setSelectedSlug}
          />
        </Tabs.Panel>
        <Tabs.Panel value="generate" pt="md">
          <GenerateTab studio={data} etag={etag} />
        </Tabs.Panel>
        <Tabs.Panel value="jd" pt="md">
          <JdMatchTab />
        </Tabs.Panel>
      </Tabs>
    </Stack>
  );
}
