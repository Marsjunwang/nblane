import {
  ActionIcon,
  Alert,
  Badge,
  Box,
  Button,
  Center,
  CloseButton,
  FileButton,
  Group,
  Image,
  Loader,
  Modal,
  Paper,
  ScrollArea,
  SegmentedControl,
  Select,
  Stack,
  TagsInput,
  Text,
  TextInput,
  Textarea,
  Title,
  Tooltip,
  UnstyledButton,
} from '@mantine/core';
import { useHotkeys, useMediaQuery } from '@mantine/hooks';
import {
  IconAlertTriangle,
  IconArrowBackUp,
  IconBook2,
  IconChecklist,
  IconDeviceFloppy,
  IconExternalLink,
  IconPhoto,
  IconPhotoStar,
  IconPlus,
  IconRefresh,
  IconRocket,
  IconRowInsertBottom,
  IconUpload,
} from '@tabler/icons-react';
import { useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';

import { containsDisplayMathBlock } from '../../../../public_blog_editor_component/frontend/src/blocks/markdown.js';
import { isConflictError } from '../components/ConflictAlert';
import {
  contentMediaUrl,
  publicBuildPreviewPageUrl,
  useCheckContentPost,
  useContentPost,
  useContentPostMedia,
  useContentWorkspace,
  useCreateContentPost,
  usePublishContentPost,
  useSaveContentPost,
  useUploadContentMedia,
} from '../api/hooks';
import type {
  ContentMedia,
  StudioPost,
  StudioPostDetail,
  StudioPostSaveRequest,
  StudioValidationResponse,
} from '../api/types';
import {
  BlockNoteBlogEditor,
  type BlockNoteBlogEditorHandle,
  type EditorBlocks,
} from '../components/BlockNoteBlogEditor';

const STATUS_LABELS: Record<string, string> = { draft: '草稿', published: '已发布', archived: '已归档' };
const STATUS_COLORS: Record<string, string> = { draft: 'yellow', published: 'green', archived: 'gray' };

type EditorMode = 'visual' | 'source' | 'preview';

interface PostDraft {
  title: string;
  date: string;
  status: string;
  summary: string;
  cover: string;
  tags: string[];
  body: string;
  blocksJson: EditorBlocks;
}

function draftFromPost(post: StudioPostDetail): PostDraft {
  return {
    title: post.title ?? '',
    date: post.date ?? '',
    status: post.status ?? 'draft',
    summary: post.summary ?? '',
    cover: post.cover ?? '',
    tags: post.tags ?? [],
    body: post.body ?? '',
    blocksJson: (post.blocks_json ?? []) as EditorBlocks,
  };
}

function draftToSaveRequest(draft: PostDraft): StudioPostSaveRequest {
  return {
    title: draft.title,
    date: draft.date,
    status: draft.status,
    summary: draft.summary,
    cover: draft.cover,
    tags: draft.tags,
    body: draft.body,
    // Source-mode edits clear the blocks: the server must not keep a sidecar
    // that no longer matches the Markdown it is saving.
    blocks_json: draft.blocksJson,
  };
}

/** Markdown snippet for one media file; alt text defaults to the file name. */
function mediaSnippet(kind: string, path: string, name: string): string {
  const label = name.replace(/\.[^.]+$/, '').replace(/[\[\]]/g, '');
  return kind === 'video' ? `::video[${label}](${path})` : `![${label}](${path})`;
}

const CHECK_MESSAGE_LABELS: Array<[RegExp, string]> = [
  [/missing required field 'summary'/, '缺少摘要：在右侧「文章属性」填写摘要。'],
  [/missing required field 'title'/, '缺少标题。'],
  [/missing required field 'date'/, '缺少日期。'],
];

/** Drop the "blog/<slug>.md: " prefix and translate the common gate messages. */
function checkMessage(raw: string): string {
  const text = raw.replace(/^blog\/[^:]+\.md:\s*/, '');
  for (const [pattern, label] of CHECK_MESSAGE_LABELS) {
    if (pattern.test(text)) return label;
  }
  return text;
}

function errorText(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

// --- Post list ----------------------------------------------------------------

function PostList({
  posts,
  selectedSlug,
  onSelect,
  onCreate,
}: {
  posts: StudioPost[];
  selectedSlug: string;
  onSelect: (slug: string) => void;
  onCreate: () => void;
}) {
  const [filter, setFilter] = useState('');
  const [query, setQuery] = useState('');
  const visible = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return posts.filter(
      (post) =>
        (!filter || post.status === filter) &&
        (!needle || `${post.title} ${post.slug} ${(post.tags ?? []).join(' ')}`.toLowerCase().includes(needle)),
    );
  }, [filter, posts, query]);

  return (
    <Paper withBorder p="md" radius="md" data-testid="content-post-list">
      <Group justify="space-between" align="center">
        <Text fw={700}>博客</Text>
        <Button size="compact-sm" leftSection={<IconPlus size={14} />} onClick={onCreate} data-testid="content-create">
          新建
        </Button>
      </Group>
      <TextInput
        mt="sm"
        size="xs"
        placeholder="搜索标题、标签"
        aria-label="搜索文章"
        value={query}
        onChange={(event) => setQuery(event.currentTarget.value)}
      />
      <SegmentedControl
        mt="xs"
        size="xs"
        fullWidth
        value={filter}
        onChange={setFilter}
        data={[
          { value: '', label: `全部 ${posts.length}` },
          ...Object.entries(STATUS_LABELS).map(([value, label]) => ({
            value,
            label: `${label} ${posts.filter((post) => post.status === value).length}`,
          })),
        ]}
      />
      <ScrollArea.Autosize mah="calc(100vh - 300px)" mt="sm" offsetScrollbars>
        <Stack gap={2}>
          {visible.map((post) => {
            const active = post.slug === selectedSlug;
            return (
              <UnstyledButton
                key={post.slug}
                onClick={() => onSelect(post.slug)}
                data-testid="content-post-item"
                aria-current={active ? 'true' : undefined}
                style={{
                  padding: '8px 10px',
                  borderRadius: 6,
                  background: active ? 'var(--mantine-color-dark-5)' : undefined,
                  borderLeft: `3px solid ${active ? 'var(--mantine-color-brand-5)' : 'transparent'}`,
                }}
              >
                <Text size="sm" fw={active ? 600 : 400} lineClamp={2}>
                  {post.title || post.slug}
                </Text>
                <Group gap={6} mt={4}>
                  <Badge size="xs" variant="light" color={STATUS_COLORS[post.status] ?? 'gray'}>
                    {STATUS_LABELS[post.status] ?? post.status}
                  </Badge>
                  <Text size="xs" c="dimmed">
                    {post.date}
                  </Text>
                </Group>
              </UnstyledButton>
            );
          })}
          {!visible.length && (
            <Text size="sm" c="dimmed" ta="center" py="xl">
              {posts.length ? '没有符合条件的文章。' : '还没有文章，点「新建」开始写。'}
            </Text>
          )}
        </Stack>
      </ScrollArea.Autosize>
    </Paper>
  );
}

// --- Side panel ---------------------------------------------------------------

function MediaPanel({
  profile,
  media,
  loading,
  uploading,
  cover,
  onUpload,
  onInsert,
  onSetCover,
}: {
  profile: string;
  media: ContentMedia[];
  loading: boolean;
  uploading: boolean;
  cover: string;
  onUpload: (file: File | null) => void;
  onInsert: (item: ContentMedia) => void;
  onSetCover: (path: string) => void;
}) {
  return (
    <Stack gap="xs" data-testid="content-media">
      <Group justify="space-between">
        <Group gap={6}>
          <IconPhoto size={16} />
          <Text size="sm" fw={600}>
            媒体
          </Text>
        </Group>
        <FileButton onChange={onUpload} accept="image/png,image/jpeg,image/webp,image/gif,video/mp4,video/webm">
          {(props) => (
            <Button {...props} size="compact-xs" variant="light" loading={uploading} leftSection={<IconUpload size={13} />}>
              上传
            </Button>
          )}
        </FileButton>
      </Group>
      {loading ? (
        <Loader size="xs" />
      ) : media.length ? (
        <Stack gap={6}>
          {media.map((item) => (
            <Group key={item.path} gap="xs" wrap="nowrap" align="center">
              {item.kind === 'image' ? (
                <Image src={contentMediaUrl(profile, item.path)} w={44} h={44} radius="sm" fit="cover" alt={item.name} />
              ) : (
                <Center w={44} h={44} bg="dark.5" style={{ borderRadius: 4 }}>
                  <Text size="xs">视频</Text>
                </Center>
              )}
              <Box style={{ flex: 1, minWidth: 0 }}>
                <Text size="xs" truncate>
                  {item.name}
                </Text>
                <Text size="xs" c="dimmed">
                  {item.path === cover ? '封面' : item.referenced ? '正文已引用' : '未使用'}
                </Text>
              </Box>
              <Tooltip label="插入到光标处">
                <ActionIcon variant="subtle" size="sm" aria-label={`插入 ${item.name}`} onClick={() => onInsert(item)}>
                  <IconRowInsertBottom size={15} />
                </ActionIcon>
              </Tooltip>
              {item.kind === 'image' && item.path !== cover && (
                <Tooltip label="设为封面">
                  <ActionIcon variant="subtle" size="sm" aria-label={`设 ${item.name} 为封面`} onClick={() => onSetCover(item.path)}>
                    <IconPhotoStar size={15} />
                  </ActionIcon>
                </Tooltip>
              )}
            </Group>
          ))}
        </Stack>
      ) : (
        <Text size="xs" c="dimmed">
          上传图片或视频后可插入正文、设为封面。也可以直接把图片拖进正文。
        </Text>
      )}
    </Stack>
  );
}

function CheckResult({ result, stale }: { result: StudioValidationResponse; stale: boolean }) {
  const errors = result.errors ?? [];
  const warnings = result.warnings ?? [];
  return (
    <Alert
      color={stale ? 'gray' : result.ok ? 'green' : 'red'}
      icon={result.ok ? <IconChecklist size={16} /> : <IconAlertTriangle size={16} />}
      title={stale ? '检查结果已过期（内容有改动）' : result.ok ? '可以发布' : '发布前需要修正'}
      data-testid="content-check-result"
    >
      <Stack gap={4}>
        {errors.map((item) => (
          <Text key={item} size="xs">
            {checkMessage(item)}
          </Text>
        ))}
        {warnings.map((item) => (
          <Text key={item} size="xs" c="dimmed">
            提示：{checkMessage(item)}
          </Text>
        ))}
        {!errors.length && !warnings.length && <Text size="xs">没有发现问题。</Text>}
      </Stack>
    </Alert>
  );
}

// --- Page -----------------------------------------------------------------------

export function ContentWorkspacePage() {
  const { name = '' } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const slug = searchParams.get('post') ?? '';
  const queryClient = useQueryClient();
  const wide = useMediaQuery('(min-width: 75em)') ?? true;

  const content = useContentWorkspace(name);
  const detail = useContentPost(name, slug);
  const media = useContentPostMedia(name, slug);
  const create = useCreateContentPost(name);
  const save = useSaveContentPost(name);
  const check = useCheckContentPost(name);
  const publish = usePublishContentPost(name);
  const upload = useUploadContentMedia(name);

  const [draft, setDraft] = useState<PostDraft | null>(null);
  const [etag, setEtag] = useState('');
  const [dirty, setDirty] = useState(false);
  // Bumped on every edit; a check result is only valid for the revision it saw.
  const [revision, setRevision] = useState(0);
  const [checked, setChecked] = useState<{ result: StudioValidationResponse; revision: number } | null>(null);
  const [mode, setMode] = useState<EditorMode>('visual');
  const [editorKey, setEditorKey] = useState('');
  const [notice, setNotice] = useState<{ color: string; text: string } | null>(null);
  const [writeError, setWriteError] = useState<unknown>(null);
  const [pendingSlug, setPendingSlug] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [previewNonce, setPreviewNonce] = useState(0);
  const editorRef = useRef<BlockNoteBlogEditorHandle>(null);

  // Load a post into the editor once per selection. Later server copies of
  // the same post (our own saves, background refetches) never replace the
  // editor content; an explicit reload resets loadedSlugRef first.
  const loadedSlugRef = useRef('');
  useEffect(() => {
    const post = detail.data?.post;
    if (!post || post.slug !== slug) return;
    if (loadedSlugRef.current === slug) return;
    loadedSlugRef.current = slug;
    const next = draftFromPost(post);
    setDraft(next);
    setEtag(detail.data!.etag);
    setDirty(false);
    setChecked(null);
    setWriteError(null);
    // Display math is not reliably editable as blocks; start those in source.
    setMode(containsDisplayMathBlock(next.body) ? 'source' : 'visual');
    setEditorKey(`${slug}:${Date.now()}`);
  }, [detail.data, editorKey, slug]);

  // Warn before closing the tab with unsaved edits.
  useEffect(() => {
    if (!dirty) return undefined;
    const handler = (event: BeforeUnloadEvent) => {
      event.preventDefault();
    };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [dirty]);

  const openPost = useCallback(
    (next: string) => {
      loadedSlugRef.current = '';
      setEditorKey('');
      setDraft(null);
      setDirty(false);
      setNotice(null);
      setSearchParams(next ? { post: next } : {}, { replace: false });
    },
    [setSearchParams],
  );

  const selectPost = (next: string) => {
    if (next === slug) return;
    if (dirty) {
      setPendingSlug(next);
      return;
    }
    openPost(next);
  };

  const edit = useCallback((patch: Partial<PostDraft>) => {
    setDraft((previous) => (previous ? { ...previous, ...patch } : previous));
    setDirty(true);
    setRevision((value) => value + 1);
    setNotice(null);
  }, []);

  const applyServerPost = (post: StudioPostDetail, nextEtag: string) => {
    setEtag(nextEtag);
    setDirty(false);
    setWriteError(null);
    setDraft((previous) =>
      previous
        ? { ...previous, status: post.status ?? previous.status, date: post.date ?? previous.date }
        : previous,
    );
    queryClient.setQueryData(['profiles', name, 'content', 'post', slug], { post, etag: nextEtag });
    setPreviewNonce((value) => value + 1);
  };

  const savePost = (overrides: Partial<PostDraft> = {}, okText = '已保存。') => {
    if (!draft || !slug || save.isPending) return;
    const body = draftToSaveRequest({ ...draft, ...overrides });
    save.mutate(
      { slug, etag, body },
      {
        onSuccess: (result) => {
          applyServerPost(result.post, result.etag);
          setNotice({ color: 'green', text: okText });
        },
        onError: setWriteError,
      },
    );
  };

  const runCheck = () => {
    if (!draft || !slug) return;
    const atRevision = revision;
    check.mutate(
      { slug, body: draftToSaveRequest(draft) },
      { onSuccess: (result) => setChecked({ result, revision: atRevision }), onError: setWriteError },
    );
  };

  // One click: run the gate on the current text, publish only if it passes.
  const publishPost = () => {
    if (!draft || !slug) return;
    const atRevision = revision;
    const body = draftToSaveRequest(draft);
    check.mutate(
      { slug, body },
      {
        onSuccess: (result) => {
          setChecked({ result, revision: atRevision });
          if (!result.ok) return;
          publish.mutate(
            { slug, etag, body: { ...body, status: 'published' } },
            {
              onSuccess: (published) => {
                applyServerPost(published.post, published.etag);
                setNotice({ color: 'green', text: '已发布到公开层。构建站点后才会出现在静态网站上。' });
              },
              onError: setWriteError,
            },
          );
        },
        onError: setWriteError,
      },
    );
  };

  const reloadFromServer = async () => {
    loadedSlugRef.current = '';
    setEditorKey('');
    setDirty(false);
    setWriteError(null);
    await queryClient.invalidateQueries({ queryKey: ['profiles', name, 'content', 'post', slug] });
  };

  const uploadToPost = useCallback(
    async (file: File) => {
      const result = await upload.mutateAsync({ slug, file });
      return result.path;
    },
    [slug, upload],
  );

  const uploadFromPanel = async (file: File | null) => {
    if (!file || !slug) return;
    try {
      const result = await upload.mutateAsync({ slug, file });
      if (mode === 'preview') setMode('visual');
      // Give a just-switched editor a tick to mount before inserting.
      const snippet = mediaSnippet(result.kind, result.path, file.name);
      window.setTimeout(() => editorRef.current?.insertMarkdown(snippet), 0);
      setNotice({ color: 'blue', text: `已上传 ${file.name} 并插入正文，保存后生效。` });
    } catch (error) {
      setNotice({ color: 'red', text: `上传失败：${errorText(error)}` });
    }
  };

  const insertMedia = (item: ContentMedia) => {
    const snippet = mediaSnippet(item.kind, item.path, item.name);
    if (mode === 'preview') setMode('visual');
    window.setTimeout(() => editorRef.current?.insertMarkdown(snippet), 0);
  };

  const createPost = () => {
    const title = newTitle.trim();
    if (!title) return;
    create.mutate(
      // No If-Match: creating never overwrites (the core picks a free slug),
      // so a stale list ETag must not block it.
      { body: { title, summary: '', tags: [], body: '' }, etag: '' },
      {
        onSuccess: (result) => {
          setCreateOpen(false);
          setNewTitle('');
          queryClient.setQueryData(['profiles', name, 'content', 'post', result.post.slug], result);
          openPost(result.post.slug);
          setNotice({ color: 'green', text: '文章已创建（草稿）。' });
        },
      },
    );
  };

  useHotkeys([['mod+S', () => savePost()]], [], true);

  if (content.isPending) {
    return (
      <Center py="xl">
        <Loader />
      </Center>
    );
  }
  if (content.isError || !content.data) {
    return (
      <Alert color="red" title="内容工作台加载失败">
        {content.error?.message}
      </Alert>
    );
  }

  const posts = content.data.data.posts ?? [];
  const checkStale = checked !== null && checked.revision !== revision;
  const busy = save.isPending || publish.isPending || check.isPending;
  const isPublished = draft?.status === 'published';
  const previewUrl = slug
    ? `${publicBuildPreviewPageUrl(name, `blog/${slug}/index.html`, true)}&n=${previewNonce}`
    : '';
  const mediaItems = media.data ?? [];
  const coverOptions = mediaItems.filter((item) => item.kind === 'image').map((item) => ({ value: item.path, label: item.name }));
  if (draft?.cover && !coverOptions.some((option) => option.value === draft.cover)) {
    coverOptions.unshift({ value: draft.cover, label: draft.cover });
  }

  const header = (
    <Group justify="space-between" align="flex-end" wrap="wrap">
      <div>
        <Group gap="xs">
          <IconBook2 size={24} />
          <Title order={2}>内容工作台</Title>
        </Group>
        <Text size="sm" c="dimmed" mt={4}>
          写博客、管理媒体、检查并发布。发布后到公开站点构建静态网站。
        </Text>
      </div>
      <Button component={Link} to={`/p/${encodeURIComponent(name)}/public-build`} variant="light" leftSection={<IconRocket size={15} />}>
        公开站点
      </Button>
    </Group>
  );

  const editorPane = (
    <Paper withBorder p="md" radius="md" data-testid="content-editor" style={{ minWidth: 0 }}>
      {!slug ? (
        <Stack align="center" justify="center" mih={520} gap="sm">
          <IconBook2 size={40} opacity={0.35} />
          <Title order={4}>选择一篇文章，或新建一篇</Title>
          <Button onClick={() => setCreateOpen(true)} leftSection={<IconPlus size={15} />}>
            新建文章
          </Button>
        </Stack>
      ) : detail.isError ? (
        <Alert color="red" title="文章加载失败">
          {detail.error?.message}
        </Alert>
      ) : !draft || !editorKey ? (
        <Center mih={520}>
          <Loader />
        </Center>
      ) : (
        <Stack gap="sm">
          <Group justify="space-between" wrap="nowrap" align="flex-start">
            <TextInput
              aria-label="标题"
              placeholder="文章标题"
              variant="unstyled"
              value={draft.title}
              onChange={(event) => edit({ title: event.currentTarget.value })}
              styles={{ input: { fontSize: 26, fontWeight: 700, height: 'auto', lineHeight: 1.3 } }}
              style={{ flex: 1 }}
            />
            <Badge mt={8} variant="light" color={STATUS_COLORS[draft.status] ?? 'gray'}>
              {STATUS_LABELS[draft.status] ?? draft.status}
            </Badge>
          </Group>
          <Group justify="space-between" wrap="wrap" gap="xs">
            <SegmentedControl
              size="xs"
              value={mode}
              onChange={(value) => setMode(value as EditorMode)}
              data={[
                { value: 'visual', label: '编辑' },
                { value: 'source', label: 'Markdown' },
                { value: 'preview', label: '站点预览' },
              ]}
              data-testid="content-mode"
            />
            <Group gap="xs">
              <Text size="xs" c={dirty ? 'yellow' : 'dimmed'} data-testid="content-save-state">
                {save.isPending ? '保存中…' : dirty ? '有未保存的修改' : '已保存'}
              </Text>
              <Button
                size="xs"
                onClick={() => savePost()}
                loading={save.isPending}
                disabled={!dirty}
                leftSection={<IconDeviceFloppy size={14} />}
                data-testid="content-save"
              >
                保存
              </Button>
            </Group>
          </Group>

          {isConflictError(writeError) ? (
            <Alert color="yellow" title="文章已在别处被修改" data-testid="conflict-alert">
              <Text size="sm">你的修改还在编辑器里，没有丢失。可以先复制需要的内容，再加载最新版本。</Text>
              <Button mt="xs" size="compact-sm" variant="default" leftSection={<IconRefresh size={14} />} onClick={reloadFromServer}>
                加载最新版本（放弃本地修改）
              </Button>
            </Alert>
          ) : writeError ? (
            <Alert color="red" title="操作失败" withCloseButton onClose={() => setWriteError(null)}>
              {errorText(writeError)}
            </Alert>
          ) : null}
          {notice && (
            <Alert color={notice.color} variant="light" withCloseButton onClose={() => setNotice(null)}>
              {notice.text}
            </Alert>
          )}

          {mode === 'preview' ? (
            <Stack gap={6}>
              <Group justify="space-between">
                <Text size="xs" c="dimmed">
                  {dirty ? '预览显示的是上次保存的版本；保存后刷新。' : '使用公开站点模板渲染（含草稿）。'}
                </Text>
                <Button
                  size="compact-xs"
                  variant="subtle"
                  component="a"
                  href={previewUrl}
                  target="_blank"
                  rel="noreferrer"
                  rightSection={<IconExternalLink size={12} />}
                >
                  新窗口打开
                </Button>
              </Group>
              <iframe
                key={previewUrl}
                title="文章站点预览"
                src={previewUrl}
                data-testid="content-preview-frame"
                style={{ width: '100%', height: 'calc(100vh - 300px)', minHeight: 520, border: 0, borderRadius: 10, background: '#fff' }}
              />
            </Stack>
          ) : (
            <BlockNoteBlogEditor
              key={editorKey}
              ref={editorRef}
              markdown={draft.body}
              blocksJson={draft.blocksJson}
              sourceMode={mode === 'source'}
              resolveMediaUrl={(path) => contentMediaUrl(name, path)}
              uploadMedia={uploadToPost}
              onChange={(value) => edit({ body: value.markdown, blocksJson: value.blocksJson })}
            />
          )}
        </Stack>
      )}
    </Paper>
  );

  const sidePane = draft && slug && editorKey ? (
    <Stack gap="md">
      <Paper withBorder p="md" radius="md" data-testid="content-publish-panel">
        <Stack gap="xs">
          <Text fw={700}>发布</Text>
          {isPublished ? (
            <>
              <Text size="xs" c="dimmed">
                这篇文章已发布。修改后保存即可更新公开内容。
              </Text>
              <Button
                variant="default"
                size="xs"
                leftSection={<IconArrowBackUp size={14} />}
                loading={save.isPending}
                onClick={() => savePost({ status: 'draft' }, '已撤回为草稿。')}
              >
                撤回为草稿
              </Button>
            </>
          ) : (
            <>
              <Text size="xs" c="dimmed">
                发布会先运行检查，通过后才写入发布状态。
              </Text>
              <Group gap="xs" grow>
                <Button size="xs" variant="light" onClick={runCheck} loading={check.isPending && !publish.isPending} leftSection={<IconChecklist size={14} />}>
                  检查
                </Button>
                <Button
                  size="xs"
                  color="green"
                  onClick={publishPost}
                  loading={publish.isPending}
                  disabled={busy || draft.status === 'archived'}
                  leftSection={<IconRocket size={14} />}
                  data-testid="content-publish"
                >
                  发布
                </Button>
              </Group>
            </>
          )}
          {checked && <CheckResult result={checked.result} stale={checkStale} />}
        </Stack>
      </Paper>

      <Paper withBorder p="md" radius="md" data-testid="content-properties">
        <Stack gap="sm">
          <Text fw={700}>文章属性</Text>
          <Textarea
            label="摘要"
            description="发布必填；显示在博客列表和分享卡片上"
            withAsterisk
            autosize
            minRows={2}
            maxRows={6}
            value={draft.summary}
            onChange={(event) => edit({ summary: event.currentTarget.value })}
          />
          <TagsInput label="标签" placeholder="回车添加" value={draft.tags} onChange={(tags) => edit({ tags })} clearable />
          <TextInput label="日期" type="date" value={draft.date} onChange={(event) => edit({ date: event.currentTarget.value })} />
          <Select
            label="封面"
            placeholder="不使用封面"
            data={coverOptions}
            value={draft.cover || null}
            onChange={(value) => edit({ cover: value ?? '' })}
            clearable
            nothingFoundMessage="先在下方上传图片"
          />
          {draft.cover && (
            <Box pos="relative">
              <Image src={contentMediaUrl(name, draft.cover)} radius="sm" mah={140} fit="cover" alt="封面预览" />
              <CloseButton
                size="sm"
                pos="absolute"
                top={4}
                right={4}
                aria-label="移除封面"
                onClick={() => edit({ cover: '' })}
              />
            </Box>
          )}
          {!isPublished && (
            <Select
              label="状态"
              data={[
                { value: 'draft', label: '草稿' },
                { value: 'archived', label: '已归档（不公开）' },
              ]}
              value={draft.status === 'archived' ? 'archived' : 'draft'}
              onChange={(value) => edit({ status: value ?? 'draft' })}
              allowDeselect={false}
            />
          )}
          <Text size="xs" c="dimmed">
            公开地址：/blog/{slug}/
          </Text>
        </Stack>
      </Paper>

      <Paper withBorder p="md" radius="md">
        <MediaPanel
          profile={name}
          media={mediaItems}
          loading={media.isPending}
          uploading={upload.isPending}
          cover={draft.cover}
          onUpload={uploadFromPanel}
          onInsert={insertMedia}
          onSetCover={(path) => edit({ cover: path })}
        />
      </Paper>
    </Stack>
  ) : null;

  return (
    <Stack gap="lg" data-testid="content-workspace">
      {header}
      <Box
        style={{
          display: 'grid',
          gap: 16,
          alignItems: 'start',
          gridTemplateColumns: wide ? '260px minmax(0, 1fr) 300px' : 'minmax(0, 1fr)',
        }}
      >
        <PostList posts={posts} selectedSlug={slug} onSelect={selectPost} onCreate={() => setCreateOpen(true)} />
        {editorPane}
        {sidePane}
      </Box>

      <Modal opened={createOpen} onClose={() => setCreateOpen(false)} title="新建文章" centered>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            createPost();
          }}
        >
          <Stack>
            <TextInput
              label="标题"
              description="用于生成文章地址，之后仍可修改标题"
              value={newTitle}
              onChange={(event) => setNewTitle(event.currentTarget.value)}
              data-autofocus
              data-testid="content-new-title"
            />
            {create.isError && <Alert color="red">{create.error.message}</Alert>}
            <Group justify="flex-end">
              <Button variant="default" onClick={() => setCreateOpen(false)}>
                取消
              </Button>
              <Button type="submit" loading={create.isPending} disabled={!newTitle.trim()} data-testid="content-create-confirm">
                创建
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>

      <Modal opened={pendingSlug !== null} onClose={() => setPendingSlug(null)} title="有未保存的修改" centered>
        <Text size="sm">切换文章会丢弃当前文章未保存的修改。</Text>
        <Group justify="flex-end" mt="md">
          <Button variant="default" onClick={() => setPendingSlug(null)}>
            继续编辑
          </Button>
          <Button
            color="red"
            variant="light"
            onClick={() => {
              const next = pendingSlug ?? '';
              setPendingSlug(null);
              openPost(next);
            }}
          >
            放弃修改并切换
          </Button>
        </Group>
      </Modal>

    </Stack>
  );
}
