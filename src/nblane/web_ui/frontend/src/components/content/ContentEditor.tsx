import {
  ActionIcon,
  Alert,
  Badge,
  Box,
  Button,
  Center,
  CloseButton,
  Drawer,
  FileButton,
  Group,
  Image,
  Loader,
  Menu,
  Modal,
  ScrollArea,
  SegmentedControl,
  Select,
  Stack,
  Tabs,
  TagsInput,
  Text,
  TextInput,
  Textarea,
  Tooltip,
} from '@mantine/core';
import { useHotkeys, useLocalStorage, useMediaQuery } from '@mantine/hooks';
import { notifications } from '@mantine/notifications';
import {
  IconArrowBackUp,
  IconArrowLeft,
  IconArrowsHorizontal,
  IconChecklist,
  IconChevronDown,
  IconCircleCheck,
  IconCircleX,
  IconExternalLink,
  IconFocusCentered,
  IconLayoutSidebarRight,
  IconListSearch,
  IconPhoto,
  IconPhotoStar,
  IconRefresh,
  IconRocket,
  IconRowInsertBottom,
  IconSearch,
  IconUpload,
} from '@tabler/icons-react';
import { useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

import { containsDisplayMathBlock } from '../../../../../public_blog_editor_component/frontend/src/blocks/markdown.js';
import { ifMatch } from '../../api/client';
import {
  contentBlogApiUrl,
  contentMediaUrl,
  publicBuildPreviewPageUrl,
  useCheckContentPost,
  useContentPost,
  useContentPostMedia,
  usePublishContentPost,
  useSaveContentPost,
  useUploadContentMedia,
} from '../../api/hooks';
import type { ContentMedia, ContentRewriteResult, StudioValidationResponse } from '../../api/types';
import {
  BlockNoteBlogEditor,
  type AIRewriteRequest,
  type BlockNoteBlogEditorHandle,
  type EditorBlocks,
} from '../BlockNoteBlogEditor';
import { isConflictError } from '../ConflictAlert';
import {
  STATUS_COLORS,
  STATUS_LABELS,
  checkMessage,
  contentEditorPath,
  contentLibraryPath,
  draftFromPost,
  draftToSaveRequest,
  isMissingSummary,
  mediaSnippet,
  outlineFromBlocks,
  type OutlineItem,
  type PostDraft,
  wordCount,
} from './contentDraft';
import { AICoverGenerator } from './AICoverGenerator';
import { AIMetaSuggestions } from './AIMetaSuggestions';
import { AIRewriteDialog, type RewriteState } from './AIRewriteDialog';
import { runContentJob, type ContentJobHandle } from './contentJobs';
import { OutlinePanel } from './OutlinePanel';
import { PostSwitcher } from './PostSwitcher';
import { useContentAIStatus, useContentWorkspace } from '../../api/hooks';

type EditorMode = 'visual' | 'source' | 'preview';
type SaveState = 'saved' | 'dirty' | 'saving' | 'error' | 'conflict';

/** Idle time after the last keystroke before the draft is written. */
const AUTOSAVE_DELAY_MS = 1500;
/** keepalive fetch bodies are capped at 64 KiB by browsers. */
const KEEPALIVE_MAX_BYTES = 60_000;

const COLUMN_WIDTH = { normal: 760, wide: 1080 } as const;
const TOP_BAR_HEIGHT = 52;
const SETTINGS_WIDTH = 340;
const OUTLINE_WIDTH = 240;

function errorText(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
}

// --- Settings panel -------------------------------------------------------------

function MediaList({
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
    <Stack gap="sm" data-testid="content-media">
      <FileButton onChange={onUpload} accept="image/png,image/jpeg,image/webp,image/gif,video/mp4,video/webm">
        {(props) => (
          <Button {...props} variant="light" loading={uploading} leftSection={<IconUpload size={15} />} fullWidth>
            上传图片或视频
          </Button>
        )}
      </FileButton>
      <Text size="xs" c="dimmed">
        上传后插入到光标处。也可以把图片直接拖进正文。
      </Text>
      {loading ? (
        <Loader size="xs" />
      ) : (
        media.map((item) => (
          <Group key={item.path} gap="sm" wrap="nowrap">
            {item.kind === 'image' ? (
              <Image src={contentMediaUrl(profile, item.path)} w={52} h={52} radius="sm" fit="cover" alt={item.name} />
            ) : (
              <Center w={52} h={52} bg="dark.5" style={{ borderRadius: 4 }}>
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
              <ActionIcon variant="subtle" aria-label={`插入 ${item.name}`} onClick={() => onInsert(item)}>
                <IconRowInsertBottom size={16} />
              </ActionIcon>
            </Tooltip>
            {item.kind === 'image' && item.path !== cover && (
              <Tooltip label="设为封面">
                <ActionIcon variant="subtle" aria-label={`设 ${item.name} 为封面`} onClick={() => onSetCover(item.path)}>
                  <IconPhotoStar size={16} />
                </ActionIcon>
              </Tooltip>
            )}
          </Group>
        ))
      )}
    </Stack>
  );
}

function PostSettings({
  profile,
  slug,
  draft,
  media,
  mediaLoading,
  uploading,
  aiText,
  aiCover,
  onEdit,
  onUpload,
  onInsert,
}: {
  profile: string;
  slug: string;
  draft: PostDraft;
  media: ContentMedia[];
  mediaLoading: boolean;
  uploading: boolean;
  aiText: boolean;
  aiCover: boolean;
  onEdit: (patch: Partial<PostDraft>) => void;
  onUpload: (file: File | null) => void;
  onInsert: (item: ContentMedia) => void;
}) {
  const coverOptions = media.filter((item) => item.kind === 'image').map((item) => ({ value: item.path, label: item.name }));
  if (draft.cover && !coverOptions.some((option) => option.value === draft.cover)) {
    coverOptions.unshift({ value: draft.cover, label: draft.cover });
  }
  const published = draft.status === 'published';
  return (
    <Tabs defaultValue="post" keepMounted={false} data-testid="content-properties">
      <Tabs.List grow>
        <Tabs.Tab value="post">文章</Tabs.Tab>
        <Tabs.Tab value="media" leftSection={<IconPhoto size={14} />}>
          媒体 {media.length ? media.length : ''}
        </Tabs.Tab>
      </Tabs.List>
      <Tabs.Panel value="post" pt="md">
        <Stack gap="md">
          <AIMetaSuggestions profile={profile} enabled={aiText} draft={draft} onApply={onEdit} />
          <Textarea
            label="摘要"
            description="发布必填；显示在博客列表和分享卡片上"
            withAsterisk
            autosize
            minRows={3}
            maxRows={8}
            value={draft.summary}
            onChange={(event) => onEdit({ summary: event.currentTarget.value })}
          />
          <TagsInput label="标签" placeholder="回车添加" value={draft.tags} onChange={(tags) => onEdit({ tags })} clearable />
          <TextInput label="日期" type="date" value={draft.date} onChange={(event) => onEdit({ date: event.currentTarget.value })} />
          <Select
            label="封面"
            placeholder="不使用封面"
            data={coverOptions}
            value={draft.cover || null}
            onChange={(value) => onEdit({ cover: value ?? '' })}
            clearable
            nothingFoundMessage="先在「媒体」上传图片"
          />
          {draft.cover && (
            <Box pos="relative">
              <Image src={contentMediaUrl(profile, draft.cover)} radius="sm" mah={160} fit="cover" alt="封面预览" />
              <CloseButton size="sm" pos="absolute" top={6} right={6} aria-label="移除封面" onClick={() => onEdit({ cover: '' })} />
            </Box>
          )}
          <AICoverGenerator
            profile={profile}
            slug={slug}
            enabled={aiCover}
            draft={draft}
            onUseCover={(path) => onEdit({ cover: path })}
          />
          {!published && (
            <Select
              label="可见性"
              data={[
                { value: 'draft', label: '草稿（未发布）' },
                { value: 'archived', label: '已归档（不公开，不发布）' },
              ]}
              value={draft.status === 'archived' ? 'archived' : 'draft'}
              onChange={(value) => onEdit({ status: value ?? 'draft' })}
              allowDeselect={false}
            />
          )}
          <Box>
            <Text size="sm" fw={500}>
              公开地址
            </Text>
            <Text size="xs" c="dimmed" mt={2} style={{ wordBreak: 'break-all' }}>
              /blog/{slug}/
            </Text>
          </Box>
          {published && (
            <Text size="xs" c="dimmed">
              已发布：修改会自动保存，并在下次构建站点时更新到网站。
            </Text>
          )}
        </Stack>
      </Tabs.Panel>
      <Tabs.Panel value="media" pt="md">
        <MediaList
          profile={profile}
          media={media}
          loading={mediaLoading}
          uploading={uploading}
          cover={draft.cover}
          onUpload={onUpload}
          onInsert={onInsert}
          onSetCover={(path) => onEdit({ cover: path })}
        />
      </Tabs.Panel>
    </Tabs>
  );
}

// --- Publish dialog ------------------------------------------------------------

function PublishDialog({
  opened,
  profile,
  aiText,
  draft,
  result,
  checking,
  stale,
  publishing,
  blocked,
  onClose,
  onRecheck,
  onEditSummary,
  onConfirm,
}: {
  opened: boolean;
  profile: string;
  aiText: boolean;
  draft: PostDraft;
  result: StudioValidationResponse | null;
  checking: boolean;
  stale: boolean;
  publishing: boolean;
  blocked: boolean;
  onClose: () => void;
  onRecheck: () => void;
  onEditSummary: (value: string) => void;
  onConfirm: () => void;
}) {
  const errors = result?.errors ?? [];
  const warnings = result?.warnings ?? [];
  const needsSummary = errors.some(isMissingSummary);
  const ready = !!result?.ok && !stale && !checking;
  return (
    <Modal opened={opened} onClose={onClose} title="发布文章" centered size="lg" data-testid="content-publish-dialog">
      <Stack gap="md">
        <Text size="sm" c="dimmed">
          发布后文章进入公开层；在「公开站点」构建后才会出现在静态网站上。
        </Text>
        {checking || !result ? (
          <Group gap="xs">
            <Loader size="xs" />
            <Text size="sm">正在检查…</Text>
          </Group>
        ) : (
          <Stack gap={6} data-testid="content-check-result">
            {errors.map((item) => (
              <Group key={item} gap="xs" wrap="nowrap" align="flex-start">
                <IconCircleX size={18} color="var(--mantine-color-red-5)" style={{ flexShrink: 0 }} />
                <Text size="sm">{checkMessage(item)}</Text>
              </Group>
            ))}
            {warnings.map((item) => (
              <Group key={item} gap="xs" wrap="nowrap" align="flex-start">
                <IconChecklist size={18} color="var(--mantine-color-yellow-5)" style={{ flexShrink: 0 }} />
                <Text size="sm" c="dimmed">
                  {checkMessage(item)}
                </Text>
              </Group>
            ))}
            {result.ok && (
              <Group gap="xs">
                <IconCircleCheck size={18} color="var(--mantine-color-green-5)" />
                <Text size="sm">{stale ? '内容有改动，请重新检查。' : '检查通过，可以发布。'}</Text>
              </Group>
            )}
          </Stack>
        )}
        {needsSummary && (
          <Textarea
            label="摘要"
            description="一两句话说明这篇文章讲什么"
            autosize
            minRows={2}
            value={draft.summary}
            onChange={(event) => onEditSummary(event.currentTarget.value)}
            data-autofocus
          />
        )}
        {needsSummary && (
          <AIMetaSuggestions
            profile={profile}
            enabled={aiText}
            draft={draft}
            compact
            onApply={(patch) => patch.summary && onEditSummary(patch.summary)}
          />
        )}
        <Group justify="space-between">
          <Button variant="subtle" leftSection={<IconRefresh size={14} />} onClick={onRecheck} loading={checking}>
            重新检查
          </Button>
          <Group gap="xs">
            <Button variant="default" onClick={onClose}>
              取消
            </Button>
            <Button
              color="green"
              leftSection={<IconRocket size={15} />}
              disabled={!ready || blocked}
              loading={publishing}
              onClick={onConfirm}
              data-testid="content-publish-confirm"
            >
              确认发布
            </Button>
          </Group>
        </Group>
      </Stack>
    </Modal>
  );
}

// --- Editor ---------------------------------------------------------------------

export function ContentEditor({ profile, slug }: { profile: string; slug: string }) {
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const wideScreen = useMediaQuery('(min-width: 75em)') ?? true;
  const mobile = useMediaQuery('(max-width: 48em)') ?? false;

  const detail = useContentPost(profile, slug);
  const media = useContentPostMedia(profile, slug);
  const workspace = useContentWorkspace(profile);
  const aiStatus = useContentAIStatus(profile);
  const aiText = aiStatus.data?.text ?? false;
  const aiCover = aiStatus.data?.cover ?? false;
  const save = useSaveContentPost(profile);
  const check = useCheckContentPost(profile);
  const publish = usePublishContentPost(profile);
  const upload = useUploadContentMedia(profile);

  const [draft, setDraft] = useState<PostDraft | null>(null);
  const [mode, setMode] = useState<EditorMode>('visual');
  const [editorKey, setEditorKey] = useState('');
  const [saveState, setSaveState] = useState<SaveState>('saved');
  const [savedAt, setSavedAt] = useState<Date | null>(null);
  const [saveError, setSaveError] = useState('');
  const [revision, setRevision] = useState(0);
  const [checked, setChecked] = useState<{ result: StudioValidationResponse; revision: number } | null>(null);
  const [publishOpen, setPublishOpen] = useState(false);
  const [previewNonce, setPreviewNonce] = useState(0);
  const [wideColumn, setWideColumn] = useLocalStorage({ key: 'nblane.content.wideColumn', defaultValue: false });
  const [settingsPinned, setSettingsPinned] = useLocalStorage({ key: 'nblane.content.settingsOpen', defaultValue: false });
  const [outlinePinned, setOutlinePinned] = useLocalStorage({ key: 'nblane.content.outlineOpen', defaultValue: false });
  const [focusMode, setFocusMode] = useLocalStorage({ key: 'nblane.content.focusMode', defaultValue: false });
  const [outline, setOutline] = useState<OutlineItem[]>([]);
  const [activeHeading, setActiveHeading] = useState('');
  const [switcherOpen, setSwitcherOpen] = useState(false);
  const [rewrite, setRewrite] = useState<(RewriteState & { request: AIRewriteRequest }) | null>(null);
  const [rewriteView, setRewriteView] = useState<'diff' | 'edit'>('diff');
  const rewriteJobRef = useRef<ContentJobHandle<ContentRewriteResult> | null>(null);

  // Refs mirror the latest state for timers, unload handlers and async saves.
  const draftRef = useRef<PostDraft | null>(null);
  const etagRef = useRef('');
  const revisionRef = useRef(0);
  const savedRevisionRef = useRef(0);
  const uncommittedRef = useRef(false);
  const conflictRef = useRef(false);
  const inFlightRef = useRef<Promise<boolean> | null>(null);
  const timerRef = useRef<number | undefined>(undefined);
  const loadedSlugRef = useRef('');
  const editorRef = useRef<BlockNoteBlogEditorHandle>(null);

  const isDirty = () => revisionRef.current !== savedRevisionRef.current;

  // Load the post once per mount (the page remounts this component per slug).
  useEffect(() => {
    const result = detail.data;
    if (!result || result.post.slug !== slug || loadedSlugRef.current === slug) return;
    loadedSlugRef.current = slug;
    const next = draftFromPost(result.post);
    draftRef.current = next;
    etagRef.current = result.etag;
    setDraft(next);
    setMode(containsDisplayMathBlock(next.body) ? 'source' : 'visual');
    setOutline([]);
    setActiveHeading('');
    setEditorKey(`${slug}:${Date.now()}`);
    if ((location.state as { focusBody?: boolean } | null)?.focusBody) {
      window.setTimeout(() => editorRef.current?.focusStart(), 120);
    }
  }, [detail.data, location.state, slug]);

  const runSave = useCallback(
    async (autosave: boolean): Promise<boolean> => {
      window.clearTimeout(timerRef.current);
      if (conflictRef.current || !draftRef.current) return false;
      if (inFlightRef.current) {
        // Autosaves coalesce: the in-flight save reschedules itself when it
        // finishes and edits are still pending. Explicit saves wait their turn.
        if (autosave) return inFlightRef.current;
        await inFlightRef.current;
        if (conflictRef.current) return false;
      }
      if (!isDirty() && !(uncommittedRef.current && !autosave)) return true;
      const atRevision = revisionRef.current;
      setSaveState('saving');
      const promise = save
        .mutateAsync({ slug, body: draftToSaveRequest(draftRef.current!), etag: etagRef.current, autosave })
        .then((result) => {
          etagRef.current = result.etag;
          savedRevisionRef.current = atRevision;
          uncommittedRef.current = autosave;
          queryClient.setQueryData(['profiles', profile, 'content', 'post', slug], { post: result.post, etag: result.etag });
          setSavedAt(new Date());
          setSaveError('');
          setPreviewNonce((value) => value + 1);
          if (isDirty()) {
            setSaveState('dirty');
            timerRef.current = window.setTimeout(() => void runSave(true), AUTOSAVE_DELAY_MS);
          } else {
            setSaveState('saved');
          }
          return true;
        })
        .catch((error: unknown) => {
          if (isConflictError(error)) {
            conflictRef.current = true;
            setSaveState('conflict');
          } else {
            setSaveState('error');
            setSaveError(errorText(error));
          }
          return false;
        })
        .finally(() => {
          inFlightRef.current = null;
        });
      inFlightRef.current = promise;
      return promise;
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [profile, queryClient, slug],
  );

  const edit = useCallback(
    (patch: Partial<PostDraft>) => {
      if (!draftRef.current) return;
      draftRef.current = { ...draftRef.current, ...patch };
      setDraft(draftRef.current);
      revisionRef.current += 1;
      setRevision(revisionRef.current);
      if (conflictRef.current) return;
      setSaveState('dirty');
      window.clearTimeout(timerRef.current);
      timerRef.current = window.setTimeout(() => void runSave(true), AUTOSAVE_DELAY_MS);
    },
    [runSave],
  );

  // Last-chance save when the tab closes or the user navigates elsewhere in
  // the app (rail links). keepalive lets the request outlive the page.
  const flushOnExit = useCallback(() => {
    window.clearTimeout(timerRef.current);
    const current = draftRef.current;
    if (!current || conflictRef.current || (!isDirty() && !uncommittedRef.current)) return;
    let body = draftToSaveRequest(current);
    let payload = JSON.stringify(body);
    if (payload.length > KEEPALIVE_MAX_BYTES) {
      // Drop the blocks sidecar; it is rebuilt from the Markdown on next open.
      body = { ...body, blocks_json: [] };
      payload = JSON.stringify(body);
    }
    if (payload.length > KEEPALIVE_MAX_BYTES) return;
    void fetch(contentBlogApiUrl(profile, slug), {
      method: 'PUT',
      keepalive: true,
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', ...ifMatch(etagRef.current) },
      body: payload,
    }).catch(() => undefined);
    savedRevisionRef.current = revisionRef.current;
    uncommittedRef.current = false;
  }, [profile, slug]);

  useEffect(() => {
    const onBeforeUnload = (event: BeforeUnloadEvent) => {
      if (conflictRef.current || (saveState === 'error' && isDirty())) {
        event.preventDefault();
        return;
      }
      flushOnExit();
    };
    window.addEventListener('beforeunload', onBeforeUnload);
    return () => window.removeEventListener('beforeunload', onBeforeUnload);
  }, [flushOnExit, saveState]);

  useEffect(() => () => flushOnExit(), [flushOnExit]);

  const backToLibrary = async () => {
    if (isDirty() || uncommittedRef.current) {
      const ok = await runSave(false);
      if (!ok) return;
    }
    navigate(contentLibraryPath(profile));
  };

  const reloadFromServer = async () => {
    conflictRef.current = false;
    loadedSlugRef.current = '';
    revisionRef.current = 0;
    savedRevisionRef.current = 0;
    uncommittedRef.current = false;
    setEditorKey('');
    setSaveState('saved');
    await queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'content', 'post', slug] });
  };

  const runCheck = useCallback(() => {
    if (!draftRef.current) return;
    const atRevision = revisionRef.current;
    check.mutate(
      { slug, body: draftToSaveRequest(draftRef.current) },
      { onSuccess: (result) => setChecked({ result, revision: atRevision }) },
    );
  }, [check, slug]);

  const openPublish = () => {
    setPublishOpen(true);
    runCheck();
  };

  const confirmPublish = async () => {
    if (!draftRef.current) return;
    // Let a running autosave land first so the If-Match ETag is current.
    if (inFlightRef.current) await inFlightRef.current;
    window.clearTimeout(timerRef.current);
    const atRevision = revisionRef.current;
    publish.mutate(
      { slug, etag: etagRef.current, body: { ...draftToSaveRequest(draftRef.current), status: 'published' } },
      {
        onSuccess: (result) => {
          etagRef.current = result.etag;
          savedRevisionRef.current = atRevision;
          uncommittedRef.current = false;
          draftRef.current = { ...draftRef.current!, status: result.post.status ?? 'published' };
          setDraft(draftRef.current);
          queryClient.setQueryData(['profiles', profile, 'content', 'post', slug], { post: result.post, etag: result.etag });
          setSaveState(isDirty() ? 'dirty' : 'saved');
          setSavedAt(new Date());
          setPublishOpen(false);
          setPreviewNonce((value) => value + 1);
          notifications.show({
            color: 'green',
            title: '已发布',
            message: '文章已进入公开层。到「公开站点」构建后会出现在网站上。',
          });
        },
        onError: (error) => {
          if (isConflictError(error)) {
            conflictRef.current = true;
            setSaveState('conflict');
            setPublishOpen(false);
          }
        },
      },
    );
  };

  const unpublish = async () => {
    edit({ status: 'draft' });
    const ok = await runSave(false);
    if (ok) notifications.show({ color: 'gray', title: '已撤回为草稿', message: '下次构建站点时会从网站移除。' });
  };

  const uploadToPost = useCallback(
    async (file: File) => (await upload.mutateAsync({ slug, file })).path,
    [slug, upload],
  );

  const insertSnippet = (snippet: string) => {
    if (mode === 'preview') setMode('visual');
    // A just-switched editor needs a tick to mount before inserting.
    window.setTimeout(() => editorRef.current?.insertMarkdown(snippet), 0);
  };

  const uploadFromPanel = async (file: File | null) => {
    if (!file) return;
    try {
      const result = await upload.mutateAsync({ slug, file });
      insertSnippet(mediaSnippet(result.kind, result.path, file.name));
    } catch (error) {
      notifications.show({ color: 'red', title: '上传失败', message: errorText(error) });
    }
  };

  const changeMode = (next: EditorMode) => {
    if (next === 'preview' && isDirty()) void runSave(true);
    setMode(next);
  };

  const onOutlineChange = useCallback((blocks: EditorBlocks) => setOutline(outlineFromBlocks(blocks)), []);

  const startRewrite = useCallback(
    (request: AIRewriteRequest) => {
      rewriteJobRef.current?.cancel();
      setRewriteView('diff');
      setRewrite({ request, operation: request.operation, original: request.selection, status: 'running' });
      const job = runContentJob<ContentRewriteResult>(
        profile,
        'content-rewrite',
        {
          operation: request.operation,
          selection: request.selection,
          context: request.context,
          title: draftRef.current?.title ?? '',
        },
        (message) => setRewrite((current) => (current ? { ...current, progress: message } : current)),
      );
      rewriteJobRef.current = job;
      job.result
        .then((result) =>
          setRewrite((current) => (current?.request === request ? { ...current, status: 'done', text: result.text } : current)),
        )
        .catch((error: unknown) =>
          setRewrite((current) =>
            current?.request === request ? { ...current, status: 'error', error: errorText(error) } : current,
          ),
        );
    },
    [profile],
  );

  const closeRewrite = () => {
    rewriteJobRef.current?.cancel();
    rewriteJobRef.current = null;
    setRewrite(null);
  };

  const acceptRewrite = () => {
    if (!rewrite?.text) return;
    const ok = editorRef.current?.replaceCapturedSelection(rewrite.text) ?? false;
    if (!ok) {
      notifications.show({
        color: 'yellow',
        title: '未替换',
        message: '选中的原文在 AI 处理期间被修改了。请重新选中后再试。',
      });
    }
    closeRewrite();
  };

  useEffect(() => () => rewriteJobRef.current?.cancel(), []);

  const jumpToHeading = (id: string) => {
    if (mode !== 'visual') setMode('visual');
    window.setTimeout(() => editorRef.current?.scrollToBlock(id), mode === 'visual' ? 0 : 80);
  };

  const switchPost = async (next: string) => {
    if (next === slug) return;
    if (isDirty() || uncommittedRef.current) {
      const ok = await runSave(false);
      if (!ok) return;
    }
    navigate(contentEditorPath(profile, next));
  };

  useHotkeys(
    [
      ['mod+S', () => void runSave(false)],
      ['mod+shift+.', () => setSettingsPinned((value) => !value)],
      ['mod+K', () => setSwitcherOpen(true)],
      ['mod+shift+O', () => setOutlinePinned((value) => !value)],
      ['mod+shift+F', () => setFocusMode((value) => !value)],
    ],
    [],
    true,
  );

  // --- Render -------------------------------------------------------------------

  if (detail.isError) {
    return (
      <Box p="xl">
        <Alert color="red" title="文章加载失败">
          {detail.error.message}
        </Alert>
        <Button mt="md" component={Link} to={contentLibraryPath(profile)} variant="default" leftSection={<IconArrowLeft size={15} />}>
          返回文章库
        </Button>
      </Box>
    );
  }
  if (!draft || !editorKey) {
    return (
      <Center h="calc(100vh - 56px)">
        <Loader />
      </Center>
    );
  }

  const published = draft.status === 'published';
  const checkStale = checked !== null && checked.revision !== revision;
  const columnWidth = wideColumn ? COLUMN_WIDTH.wide : COLUMN_WIDTH.normal;
  const settingsInline = wideScreen && settingsPinned;
  const outlineInline = wideScreen && outlinePinned && mode !== 'preview';
  const previewUrl = `${publicBuildPreviewPageUrl(profile, `blog/${slug}/index.html`, true)}&n=${previewNonce}`;
  const words = wordCount(draft.body);

  const saveLabel: Record<SaveState, string> = {
    saved: savedAt ? `已保存 ${formatTime(savedAt)}` : '已保存',
    dirty: '编辑中…',
    saving: '保存中…',
    error: '保存失败，将在下次修改时重试',
    conflict: '文章已在别处被修改',
  };

  const settings = (
    <PostSettings
      profile={profile}
      slug={slug}
      draft={draft}
      media={media.data ?? []}
      mediaLoading={media.isPending}
      uploading={upload.isPending}
      aiText={aiText}
      aiCover={aiCover}
      onEdit={edit}
      onUpload={uploadFromPanel}
      onInsert={(item) => insertSnippet(mediaSnippet(item.kind, item.path, item.name))}
    />
  );

  const topBar = (
    <Group
      justify="space-between"
      wrap="nowrap"
      gap="sm"
      px={mobile ? 'xs' : 'md'}
      h={TOP_BAR_HEIGHT}
      style={{
        position: 'sticky',
        top: 'var(--app-shell-header-height, 56px)',
        zIndex: 20,
        background: 'var(--mantine-color-body)',
        borderBottom: '1px solid var(--mantine-color-dark-5)',
      }}
      data-testid="content-editor-topbar"
    >
      <Group gap="xs" wrap="nowrap" style={{ minWidth: 0 }}>
        {mobile ? (
          <ActionIcon variant="subtle" color="gray" aria-label="返回文章库" onClick={() => void backToLibrary()} data-testid="content-back">
            <IconArrowLeft size={18} />
          </ActionIcon>
        ) : (
          <Button
            variant="subtle"
            color="gray"
            size="compact-sm"
            leftSection={<IconArrowLeft size={15} />}
            onClick={() => void backToLibrary()}
            data-testid="content-back"
          >
            文章库
          </Button>
        )}
        {!mobile && (
          <Badge variant="dot" color={STATUS_COLORS[draft.status] ?? 'gray'} style={{ flexShrink: 0 }}>
            {STATUS_LABELS[draft.status] ?? draft.status}
          </Badge>
        )}
        <Text
          visibleFrom="sm"
          size="xs"
          c={saveState === 'error' || saveState === 'conflict' ? 'red' : 'dimmed'}
          truncate
          data-testid="content-save-state"
        >
          {saveLabel[saveState]}
        </Text>
      </Group>
      <Group gap={6} wrap="nowrap">
        {!mobile && (
          <Tooltip label="跳转到文章（⌘K）">
            <ActionIcon
              variant="subtle"
              color="gray"
              size="lg"
              aria-label="跳转到文章"
              onClick={() => setSwitcherOpen(true)}
              data-testid="content-switcher-toggle"
            >
              <IconSearch size={18} />
            </ActionIcon>
          </Tooltip>
        )}
        <SegmentedControl
          size="xs"
          value={mode}
          onChange={(value) => changeMode(value as EditorMode)}
          data={[
            { value: 'visual', label: '编辑' },
            { value: 'source', label: mobile ? 'MD' : 'Markdown' },
            { value: 'preview', label: '预览' },
          ]}
          data-testid="content-mode"
        />
        <Tooltip label="目录（⌘⇧O）">
          <ActionIcon
            variant={outlinePinned ? 'light' : 'subtle'}
            color="gray"
            size="lg"
            aria-label="文档目录"
            aria-pressed={outlinePinned}
            onClick={() => setOutlinePinned((value) => !value)}
            data-testid="content-outline-toggle"
          >
            <IconListSearch size={18} />
          </ActionIcon>
        </Tooltip>
        {!mobile && (
          <Tooltip label="专注模式（⌘⇧F）">
            <ActionIcon
              variant={focusMode ? 'light' : 'subtle'}
              color="gray"
              size="lg"
              aria-label="专注模式"
              aria-pressed={focusMode}
              onClick={() => setFocusMode((value) => !value)}
              data-testid="content-focus-toggle"
            >
              <IconFocusCentered size={18} />
            </ActionIcon>
          </Tooltip>
        )}
        {!mobile && (
          <Tooltip label={wideColumn ? '标准宽度' : '加宽版面'}>
            <ActionIcon
              variant={wideColumn ? 'light' : 'subtle'}
              color="gray"
              size="lg"
              aria-label="切换加宽版面"
              aria-pressed={wideColumn}
              onClick={() => setWideColumn((value) => !value)}
              data-testid="content-wide-toggle"
            >
              <IconArrowsHorizontal size={18} />
            </ActionIcon>
          </Tooltip>
        )}
        <Tooltip label="文章设置与媒体（⌘⇧.）">
          <ActionIcon
            variant={settingsPinned ? 'light' : 'subtle'}
            color="gray"
            size="lg"
            aria-label="文章设置"
            aria-pressed={settingsPinned}
            onClick={() => setSettingsPinned((value) => !value)}
            data-testid="content-settings-toggle"
          >
            <IconLayoutSidebarRight size={18} />
          </ActionIcon>
        </Tooltip>
        {published ? (
          <Menu position="bottom-end" withinPortal>
            <Menu.Target>
              <Button size="xs" color="green" variant="light" rightSection={<IconChevronDown size={14} />} data-testid="content-published-menu">
                已发布
              </Button>
            </Menu.Target>
            <Menu.Dropdown>
              <Menu.Item leftSection={<IconExternalLink size={14} />} component="a" href={previewUrl} target="_blank" rel="noreferrer">
                在新窗口预览
              </Menu.Item>
              <Menu.Item
                leftSection={<IconRocket size={14} />}
                component={Link}
                to={`/p/${encodeURIComponent(profile)}/public-build`}
              >
                去公开站点构建
              </Menu.Item>
              <Menu.Divider />
              <Menu.Item leftSection={<IconArrowBackUp size={14} />} onClick={() => void unpublish()}>
                撤回为草稿
              </Menu.Item>
            </Menu.Dropdown>
          </Menu>
        ) : (
          <Button
            size="xs"
            leftSection={<IconRocket size={14} />}
            onClick={openPublish}
            disabled={draft.status === 'archived'}
            data-testid="content-publish"
          >
            发布
          </Button>
        )}
      </Group>
    </Group>
  );

  const canvas = (
    <Box style={{ flex: 1, minWidth: 0 }}>
      {saveState === 'conflict' && (
        <Box maw={columnWidth} mx="auto" px="md" pt="md">
          <Alert color="yellow" title="文章已在别处被修改" data-testid="conflict-alert">
            <Text size="sm">自动保存已暂停，你的修改还在编辑器里。需要的话先复制内容，再加载最新版本。</Text>
            <Button mt="xs" size="compact-sm" variant="default" leftSection={<IconRefresh size={14} />} onClick={() => void reloadFromServer()}>
              加载最新版本（放弃本地修改）
            </Button>
          </Alert>
        </Box>
      )}
      {saveState === 'error' && saveError && (
        <Box maw={columnWidth} mx="auto" px="md" pt="md">
          <Alert color="red" variant="light" title="保存失败">
            {saveError}
          </Alert>
        </Box>
      )}
      {mode === 'preview' ? (
        <Box px={mobile ? 0 : 'md'} py="md" style={{ maxWidth: Math.max(columnWidth, 960), margin: '0 auto' }}>
          <iframe
            key={previewUrl}
            title="文章站点预览"
            src={previewUrl}
            data-testid="content-preview-frame"
            style={{
              width: '100%',
              height: `calc(100vh - 56px - ${TOP_BAR_HEIGHT}px - 32px)`,
              border: 0,
              borderRadius: 10,
              background: '#fff',
            }}
          />
        </Box>
      ) : (
        <Box mx="auto" pt={mobile ? 20 : 48} style={{ maxWidth: columnWidth, transition: 'max-width 0.2s ease' }} data-testid="content-editor">
          <Box className="nb-spa-title" px={mobile ? 16 : 54}>
            <Textarea
              aria-label="标题"
              placeholder="无标题"
              variant="unstyled"
              autosize
              minRows={1}
              value={draft.title}
              onChange={(event) => edit({ title: event.currentTarget.value.replace(/\n/g, ' ') })}
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  event.preventDefault();
                  editorRef.current?.focusStart();
                }
              }}
              styles={{
                input: {
                  fontSize: mobile ? 26 : 34,
                  fontWeight: 700,
                  lineHeight: 1.3,
                  padding: 0,
                  color: 'var(--mantine-color-dark-0)',
                },
              }}
              data-testid="content-title"
            />
            <Group gap="xs" mt={8} mb={20}>
              <Text size="xs" c="dimmed">
                {draft.date || '未设置日期'}
              </Text>
              <Text size="xs" c="dimmed">
                ·
              </Text>
              <Text size="xs" c="dimmed" data-testid="content-word-count">
                {words} 字
              </Text>
              {draft.tags.slice(0, 4).map((tag) => (
                <Badge key={tag} size="xs" variant="outline" color="gray">
                  {tag}
                </Badge>
              ))}
              {!draft.summary.trim() && !published && (
                <Text
                  size="xs"
                  c="yellow"
                  style={{ cursor: 'pointer' }}
                  onClick={() => setSettingsPinned(true)}
                >
                  · 还没有摘要
                </Text>
              )}
            </Group>
          </Box>
          <BlockNoteBlogEditor
            key={editorKey}
            ref={editorRef}
            markdown={draft.body}
            blocksJson={draft.blocksJson}
            sourceMode={mode === 'source'}
            focusMode={focusMode}
            resolveMediaUrl={(path) => contentMediaUrl(profile, path)}
            uploadMedia={uploadToPost}
            onChange={(value) => edit({ body: value.markdown, blocksJson: value.blocksJson })}
            onOutlineChange={onOutlineChange}
            onActiveHeadingChange={setActiveHeading}
            onAIRewrite={aiText ? startRewrite : undefined}
          />
        </Box>
      )}
    </Box>
  );

  return (
    <Box data-testid="content-workspace" style={{ minHeight: 'calc(100vh - 56px)' }}>
      {topBar}
      <Box style={{ display: 'flex', alignItems: 'flex-start' }}>
        {outlineInline && (
          <Box
            component="aside"
            w={OUTLINE_WIDTH}
            style={{
              flexShrink: 0,
              position: 'sticky',
              top: `calc(var(--app-shell-header-height, 56px) + ${TOP_BAR_HEIGHT}px)`,
              height: `calc(100vh - 56px - ${TOP_BAR_HEIGHT}px)`,
              borderRight: '1px solid var(--mantine-color-dark-5)',
            }}
            data-testid="content-outline-rail"
          >
            <Group justify="space-between" px="md" pt="md" pb={4}>
              <Text size="xs" fw={600} c="dimmed" tt="uppercase">
                目录
              </Text>
              <CloseButton size="sm" aria-label="关闭目录" onClick={() => setOutlinePinned(false)} />
            </Group>
            <OutlinePanel items={outline} activeId={activeHeading} onJump={jumpToHeading} />
          </Box>
        )}
        {canvas}
        {settingsInline && (
          <Box
            component="aside"
            w={SETTINGS_WIDTH}
            style={{
              flexShrink: 0,
              position: 'sticky',
              top: `calc(var(--app-shell-header-height, 56px) + ${TOP_BAR_HEIGHT}px)`,
              height: `calc(100vh - 56px - ${TOP_BAR_HEIGHT}px)`,
              borderLeft: '1px solid var(--mantine-color-dark-5)',
            }}
            data-testid="content-settings"
          >
            <ScrollArea h="100%" p="md" offsetScrollbars>
              <Group justify="space-between" mb="xs">
                <Text fw={600}>文章设置</Text>
                <CloseButton aria-label="关闭设置" onClick={() => setSettingsPinned(false)} />
              </Group>
              {settings}
            </ScrollArea>
          </Box>
        )}
      </Box>

      <Drawer
        opened={!wideScreen && settingsPinned}
        onClose={() => setSettingsPinned(false)}
        position="right"
        size={mobile ? '100%' : SETTINGS_WIDTH + 40}
        title="文章设置"
      >
        {settings}
      </Drawer>

      <Drawer
        opened={!wideScreen && outlinePinned}
        onClose={() => setOutlinePinned(false)}
        position="left"
        size={mobile ? '80%' : OUTLINE_WIDTH + 40}
        title="目录"
      >
        <OutlinePanel items={outline} activeId={activeHeading} onJump={(id) => { setOutlinePinned(false); jumpToHeading(id); }} />
      </Drawer>

      <PublishDialog
        opened={publishOpen}
        profile={profile}
        aiText={aiText}
        draft={draft}
        result={checked?.result ?? null}
        checking={check.isPending}
        stale={checkStale}
        publishing={publish.isPending}
        blocked={saveState === 'conflict'}
        onClose={() => setPublishOpen(false)}
        onRecheck={runCheck}
        onEditSummary={(value) => edit({ summary: value })}
        onConfirm={() => void confirmPublish()}
      />

      <AIRewriteDialog
        state={rewrite}
        view={rewriteView}
        onViewChange={setRewriteView}
        onEditCandidate={(text) => setRewrite((current) => (current ? { ...current, text } : current))}
        onAccept={acceptRewrite}
        onRetry={() => rewrite && startRewrite(rewrite.request)}
        onClose={closeRewrite}
      />

      <PostSwitcher
        opened={switcherOpen}
        posts={workspace.data?.data.posts ?? []}
        currentSlug={slug}
        onClose={() => setSwitcherOpen(false)}
        onPick={(next) => void switchPost(next)}
      />
    </Box>
  );
}
