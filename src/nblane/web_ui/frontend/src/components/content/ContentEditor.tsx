import {
  ActionIcon,
  Alert,
  Badge,
  Box,
  Button,
  Center,
  CloseButton,
  Drawer,
  Group,
  Loader,
  Menu,
  Modal,
  ScrollArea,
  SegmentedControl,
  Stack,
  Text,
  Textarea,
  Tooltip,
} from '@mantine/core';
import { useHotkeys, useLocalStorage, useMediaQuery } from '@mantine/hooks';
import { notifications } from '@mantine/notifications';
import {
  IconAlertTriangle,
  IconArrowBackUp,
  IconArrowLeft,
  IconArrowsHorizontal,
  IconCheck,
  IconChevronDown,
  IconCircleCheck,
  IconDots,
  IconExternalLink,
  IconFocusCentered,
  IconLayoutSidebarRight,
  IconListSearch,
  IconPencil,
  IconRefresh,
  IconRocket,
  IconSearch,
  IconShare,
  IconTrash,
} from '@tabler/icons-react';
import { useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

import { containsDisplayMathBlock } from '../../blogBlocks/markdown.js';
import {
  contentMediaUrl,
  publicSitePreviewPageUrl,
  useCheckContentPost,
  useContentPost,
  useContentPostMedia,
  usePublishContentPost,
  useUploadContentMedia,
} from '../../api/hooks';
import type { ContentRewriteResult, StudioValidationResponse } from '../../api/types';
import {
  BlockNoteBlogEditor,
  type AIRewriteRequest,
  type BlockNoteBlogEditorHandle,
  type ReplaceOutcome,
} from '../BlockNoteBlogEditor';
import { isConflictError } from '../ConflictAlert';
import {
  STATUS_COLORS,
  STATUS_LABELS,
  clearLocalDraft,
  contentEditorPath,
  contentLibraryPath,
  draftToSaveRequest,
  errorText,
  mediaSnippet,
  outlineFromBlocks,
  wordCount,
  writeLocalDraft,
  type EditorBlocks,
  type OutlineItem,
  type PostDraft,
} from './contentDraft';
import { ImageWorkspace } from './ImageWorkspace';
import { ImagePreview } from './ImagePreview';
import { useImageRuns } from './imageApi';
import type { ImageEditRequest, SelectedImage } from './imageTypes';
import { changedFields, previousOf, undoPatch, type AIPatch } from './aiUndo';
import { showAIUndo } from './aiUndoNotice';
import { AIRewriteDialog, type RewriteState } from './AIRewriteDialog';
import { runContentJob } from './contentJobs';
import { combineJobs, useContentJob } from './useContentJob';
import { OutlinePanel } from './OutlinePanel';
import { PostSwitcher } from './PostSwitcher';
import { PublishDialog } from './PublishDialog';
import { PostSettings } from './PostSettings';
import { SocialShareDrawer } from './SocialShareDrawer';
import { DeleteContentPostDialog } from './DeleteContentPostDialog';
import { AUTOSAVE_DELAY_MS, usePostSaveController, type SaveState } from './usePostSaveController';
import { useContentAIStatus, useContentWorkspace } from '../../api/hooks';

type EditorMode = 'visual' | 'source' | 'preview';

const COLUMN_WIDTH = { normal: 760, wide: 1080 } as const;
const TOP_BAR_HEIGHT = 52;
const SETTINGS_WIDTH = 340;
const OUTLINE_WIDTH = 240;

const REPLACE_FAILURE_TEXT: Record<Exclude<ReplaceOutcome, 'ok'>, string> = {
  'no-selection': '找不到当时选中的位置。可以复制候选，或重新选中原文后再点「接受并替换」。',
  'source-mode': '源码模式下无法按选区替换。切回可视模式后再点「接受并替换」，或复制候选手动粘贴。',
  changed: '原文在 AI 处理期间被修改了，为免覆盖你的改动没有替换。可以复制候选，或重新选中后重新生成。',
  empty: '候选里有空白区域，补上内容后再替换。',
  media: '候选里出现了图片或视频，只能替换文字。请在「编辑候选」里删掉媒体后再替换，或复制候选手动粘贴。',
};

function formatTime(date: Date): string {
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
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
  const imageRuns = useImageRuns(profile, slug);
  const [imageOpen, setImageOpen] = useState(false);
  const [imageRequest, setImageRequest] = useState<ImageEditRequest | null>(null);
  const [imageChoices, setImageChoices] = useState<SelectedImage[]>([]);
  const openImages = (request: ImageEditRequest | null) => { setImageRequest(request); setImageOpen(true); };
  const editSelectedImages = (images: SelectedImage[]) => {
    if (images.length > 1) { setImageChoices(images); return; }
    const image = images[0];
    if (image) openImages({ mode: 'edit', reference: image.source, target: { kind: 'block', source: image.source, block_id: image.id, fingerprint: image.fingerprint } });
  };
  const check = useCheckContentPost(profile);
  const publish = usePublishContentPost(profile);
  const upload = useUploadContentMedia(profile);

  const [mode, setMode] = useState<EditorMode>('visual');
  const [editorKey, setEditorKey] = useState('');
  const [checked, setChecked] = useState<{ result: StudioValidationResponse; revision: number } | null>(null);
  const [publishOpen, setPublishOpen] = useState(false);
  const [wideColumn, setWideColumn] = useLocalStorage({ key: 'nblane.content.wideColumn', defaultValue: false });
  const [settingsPinned, setSettingsPinned] = useLocalStorage({ key: 'nblane.content.settingsOpen', defaultValue: false });
  const [outlinePinned, setOutlinePinned] = useLocalStorage({ key: 'nblane.content.outlineOpen', defaultValue: false });
  const [focusMode, setFocusMode] = useLocalStorage({ key: 'nblane.content.focusMode', defaultValue: false });
  // Mobile drawers are explicit, never restored from the pinned desktop state.
  const [settingsOpenMobile, setSettingsOpenMobile] = useState(false);
  const [outlineOpenMobile, setOutlineOpenMobile] = useState(false);
  const [outline, setOutline] = useState<OutlineItem[]>([]);
  const [activeHeading, setActiveHeading] = useState('');
  const [switcherOpen, setSwitcherOpen] = useState(false);
  const [shareOpen, setShareOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [rewrite, setRewrite] = useState<(RewriteState & { request: AIRewriteRequest }) | null>(null);
  const [rewriteView, setRewriteView] = useState<'diff' | 'edit'>('diff');
  const rewriteJob = useContentJob<ContentRewriteResult[]>();

  const editorRef = useRef<BlockNoteBlogEditorHandle>(null);

  // UI reset after the save controller (re)loads a draft: switch mode for
  // display math, remount the editor, and (on server loads) reset the outline.
  const handleApplyPost = useCallback(
    (next: PostDraft, options: { resetOutline: boolean }) => {
      setMode(containsDisplayMathBlock(next.body) ? 'source' : 'visual');
      if (options.resetOutline) {
        setOutline([]);
        setActiveHeading('');
      }
      setEditorKey(`${slug}:${Date.now()}`);
    },
    [slug],
  );

  const {
    draft,
    setDraft,
    saveState,
    setSaveState,
    savedAt,
    setSavedAt,
    saveError,
    localCandidate,
    revision,
    previewNonce,
    setPreviewNonce,
    draftRef,
    etagRef,
    revisionRef,
    savedRevisionRef,
    uncommittedRef,
    inFlightRef,
    timerRef,
    localTimerRef,
    loadedSlugRef,
    deletingRef,
    conflictRef,
    isDirty,
    applyServerPost,
    runSave,
    edit,
    reloadFromServer,
    keepMine,
    restoreLocalDraft,
    discardLocalDraft,
  } = usePostSaveController({ profile, slug, onApplyPost: handleApplyPost });

  // Load the post once per mount (the page remounts this component per slug).
  useEffect(() => {
    const result = detail.data;
    if (!result || result.post.slug !== slug || loadedSlugRef.current === slug) return;
    applyServerPost(result);
    if ((location.state as { focusBody?: boolean } | null)?.focusBody) {
      window.setTimeout(() => editorRef.current?.focusStart(), 120);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [detail.data, location.state, slug]);

  // AI suggestions and AI covers overwrite fields the writer may have typed;
  // apply at once, but offer 撤销 (restores only fields still holding the AI
  // value, so later hand edits survive).
  const applyAI = useCallback(
    (patch: AIPatch) => {
      const current = draftRef.current;
      if (!current) return;
      const fields = changedFields(patch, current);
      if (fields.length === 0) return;
      const previous = previousOf(patch, current);
      edit(patch);
      showAIUndo(fields, () => {
        const now = draftRef.current;
        if (!now) return;
        const restore = undoPatch(previous, patch, now);
        if (Object.keys(restore).length > 0) edit(restore);
      });
    },
    [edit],
  );

  const backToLibrary = async () => {
    if (isDirty() || uncommittedRef.current) {
      const ok = await runSave(false);
      if (!ok) return;
    }
    navigate(contentLibraryPath(profile));
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
            message: '文章已进入公开层。到「公开站点」发布到线上后会出现在网站上。',
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

  const openDelete = async () => {
    if (deletingRef.current || publish.isPending || upload.isPending) return;
    deletingRef.current = true;
    window.clearTimeout(timerRef.current);
    window.clearTimeout(localTimerRef.current);
    // Wait for an already-sent save before the dialog reads its ETag. Any
    // follow-up autosave or unmount keepalive is blocked until cancellation.
    if (inFlightRef.current) await inFlightRef.current;
    if (draftRef.current && isDirty()) {
      writeLocalDraft(window.localStorage, profile, slug, draftRef.current, etagRef.current);
    }
    setDeleteOpen(true);
  };

  const closeDelete = () => {
    setDeleteOpen(false);
    deletingRef.current = false;
    if (isDirty() || uncommittedRef.current) {
      timerRef.current = window.setTimeout(() => void runSave(true), AUTOSAVE_DELAY_MS);
    }
  };

  const onDeleted = () => {
    window.clearTimeout(timerRef.current);
    window.clearTimeout(localTimerRef.current);
    rewriteJob.cancel();
    clearLocalDraft(window.localStorage, profile, slug);
    // Keep deletingRef set through unmount so exit flushing cannot recreate
    // the deleted document or its browser draft.
    navigate(contentLibraryPath(profile), { replace: true });
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
    async (request: AIRewriteRequest) => {
      setRewriteView('diff');
      setRewrite({ request, operation: request.operation, original: request.selection, status: 'running' });
      const selections = request.parts ?? [request.selection];
      const total = selections.length;
      const outcome = await rewriteJob.start((onProgress) =>
        combineJobs(
          selections.map((selection, index) =>
            runContentJob<ContentRewriteResult>(
              profile,
              'content-rewrite',
              { operation: request.operation, selection, context: request.context, title: draftRef.current?.title ?? '' },
              (message) => onProgress(total > 1 ? `文字区域 ${index + 1}/${total}：${message}` : message),
            ),
          ),
        ),
      );
      if (outcome.status === 'stale') return;
      setRewrite((current) => {
        if (current?.request !== request) return current;
        if (outcome.status === 'error') return { ...current, status: 'error', error: outcome.error };
        const texts = outcome.value.map((item) => item.text);
        return { ...current, status: 'done', text: texts.join('\n\n'), parts: request.parts ? texts : undefined, originals: request.parts };
      });
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [profile, rewriteJob.start],
  );

  const closeRewrite = () => {
    rewriteJob.cancel();
    setRewrite(null);
  };

  const acceptRewrite = () => {
    if (!rewrite?.text) return;
    const outcome = editorRef.current?.replaceCapturedSelection(rewrite.text, rewrite.parts) ?? 'no-selection';
    if (outcome === 'ok') {
      closeRewrite();
      notifications.show({ color: 'green', message: '已替换。可按 Ctrl+Z（⌘Z）撤销。' });
      return;
    }
    // Keep the dialog (and any hand edits to the candidate) so a 60s result
    // is never thrown away; say why and how to recover.
    setRewrite((current) => (current ? { ...current, acceptError: REPLACE_FAILURE_TEXT[outcome] } : current));
  };

  const copyRewrite = () => {
    if (!rewrite?.text) return;
    void navigator.clipboard
      ?.writeText(rewrite.text)
      .then(() => notifications.show({ color: 'green', message: '候选已复制，可粘贴到正文。' }))
      .catch(() => notifications.show({ color: 'red', message: '复制失败，请在「编辑候选」里手动选中复制。' }));
  };

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

  // On mobile the panels are ephemeral drawers; elsewhere they follow the
  // pinned state (inline rail on wide screens, drawer in between).
  const openSettings = () => (mobile ? setSettingsOpenMobile(true) : setSettingsPinned(true));
  const openOutline = () => (mobile ? setOutlineOpenMobile(true) : setOutlinePinned(true));
  const closeSettings = () => (mobile ? setSettingsOpenMobile(false) : setSettingsPinned(false));
  const closeOutline = () => (mobile ? setOutlineOpenMobile(false) : setOutlinePinned(false));

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
  const previewUrl = `${publicSitePreviewPageUrl(profile, `blog/${slug}/index.html`, true)}&n=${previewNonce}`;
  const words = wordCount(draft.body);

  const saveLabel: Record<SaveState, string> = {
    saved: savedAt ? `已保存 ${formatTime(savedAt)}` : '已保存',
    dirty: '编辑中…',
    saving: '保存中…',
    error: '保存失败，将在下次修改时重试',
    conflict: '文章已在别处被修改',
    empty: '正文已清空，等待确认',
  };

  const settings = (
    <Stack>
    <Button variant="light" onClick={() => openImages(null)}>
      图片任务与候选{imageRuns.data?.runs.some((run) => run.status === 'running') ? ' · 生成中' : imageRuns.data?.runs.some((run) => run.candidates.some((candidate) => !candidate.applied_path)) ? ' · 待确认' : ''}
    </Button>
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
      onApplyAI={applyAI}
      onImageOpen={openImages}
      onUpload={uploadFromPanel}
      onInsert={(item) => insertSnippet(mediaSnippet(item.kind, item.path, item.name))}
    />
    <Button color="red" variant="outline" leftSection={<IconTrash size={16} />}
      onClick={() => void openDelete()} disabled={publish.isPending || upload.isPending}
      data-testid="content-editor-delete">删除文章</Button>
    </Stack>
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
          c={saveState === 'error' || saveState === 'conflict' || saveState === 'empty' ? 'red' : 'dimmed'}
          truncate
          data-testid="content-save-state"
        >
          {saveLabel[saveState]}
        </Text>
        <Box
          hiddenFrom="sm"
          component="span"
          role="status"
          aria-label={saveLabel[saveState]}
          data-testid="content-save-state-mobile"
          style={{ display: 'inline-flex', alignItems: 'center', flexShrink: 0 }}
        >
          {saveState === 'saving' ? (
            <Loader size={14} />
          ) : saveState === 'error' || saveState === 'conflict' || saveState === 'empty' ? (
            <IconAlertTriangle size={16} color="var(--mantine-color-red-5)" />
          ) : saveState === 'dirty' ? (
            <IconPencil size={14} color="var(--mantine-color-dimmed)" />
          ) : (
            <IconCircleCheck size={16} color="var(--mantine-color-dimmed)" />
          )}
        </Box>
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
        {!mobile && (
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
        )}
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
        {!mobile && (
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
        )}
        {mobile && (
          <Menu position="bottom-end" withinPortal>
            <Menu.Target>
              <ActionIcon variant="subtle" color="gray" size="lg" aria-label="更多操作" data-testid="content-overflow-menu">
                <IconDots size={18} />
              </ActionIcon>
            </Menu.Target>
            <Menu.Dropdown>
              <Menu.Item
                leftSection={<IconSearch size={14} />}
                onClick={() => setSwitcherOpen(true)}
                data-testid="content-switcher-menu-item"
              >
                跳转到文章
              </Menu.Item>
              <Menu.Item leftSection={<IconListSearch size={14} />} onClick={openOutline} data-testid="content-outline-menu-item">
                文档目录
              </Menu.Item>
              <Menu.Item
                leftSection={<IconFocusCentered size={14} />}
                rightSection={focusMode ? <IconCheck size={14} /> : null}
                onClick={() => setFocusMode((value) => !value)}
                data-testid="content-focus-menu-item"
              >
                专注模式
              </Menu.Item>
              <Menu.Item
                leftSection={<IconArrowsHorizontal size={14} />}
                rightSection={wideColumn ? <IconCheck size={14} /> : null}
                onClick={() => setWideColumn((value) => !value)}
              >
                加宽版面
              </Menu.Item>
              <Menu.Item
                leftSection={<IconLayoutSidebarRight size={14} />}
                onClick={openSettings}
                data-testid="content-settings-menu-item"
              >
                文章设置
              </Menu.Item>
              {!published && (
                <Menu.Item leftSection={<IconShare size={14} />} onClick={() => setShareOpen(true)} data-testid="content-share-menu-item">
                  发到小红书 / X
                </Menu.Item>
              )}
            </Menu.Dropdown>
          </Menu>
        )}
        {!published && !mobile && (
          <Tooltip label="发到小红书 / X">
            <ActionIcon variant="subtle" color="gray" size="lg" aria-label="发到小红书 / X" onClick={() => setShareOpen(true)} data-testid="content-share-draft">
              <IconShare size={18} />
            </ActionIcon>
          </Tooltip>
        )}
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
                去公开站点发布
              </Menu.Item>
              <Menu.Item leftSection={<IconShare size={14} />} onClick={() => setShareOpen(true)} data-testid="content-share">
                发到小红书 / X
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
    <Box style={{ flex: 1, minWidth: 100 }}>
      {saveState === 'conflict' && (
        <Box maw={columnWidth} mx="auto" px="md" pt="md">
          <Alert color="yellow" title="文章已在别处被修改" data-testid="conflict-alert">
            <Text size="sm">自动保存已暂停，你的修改还在编辑器里。可以保留你的版本覆盖服务器上的，或加载最新版本。</Text>
            <Group gap="xs" mt="xs">
              <Button size="compact-sm" variant="light" color="yellow" onClick={() => void keepMine()} data-testid="conflict-keep-mine">
                保留我的版本
              </Button>
              <Button size="compact-sm" variant="default" leftSection={<IconRefresh size={14} />} onClick={() => void reloadFromServer()}>
                加载最新版本（放弃本地修改）
              </Button>
            </Group>
          </Alert>
        </Box>
      )}
      {saveState === 'empty' && (
        <Box maw={columnWidth} mx="auto" px="md" pt="md">
          <Alert color="red" title="正文已被清空" data-testid="empty-body-alert">
            <Text size="sm">服务器上的正文还在，自动保存已暂停。是误操作的话点「恢复正文」。</Text>
            <Group gap="xs" mt="xs">
              <Button size="compact-sm" variant="light" leftSection={<IconRefresh size={14} />} onClick={() => void reloadFromServer()}>
                恢复正文
              </Button>
              <Button size="compact-sm" variant="subtle" color="red" onClick={() => void runSave(false, { allowEmpty: true })}>
                确认保存为空白
              </Button>
            </Group>
          </Alert>
        </Box>
      )}
      {localCandidate && (
        <Box maw={columnWidth} mx="auto" px="md" pt="md">
          <Alert color="blue" title="发现未保存的本地草稿" data-testid="local-draft-alert">
            <Text size="sm">
              这台设备上有 {formatTime(new Date(localCandidate.savedAt))} 的修改没存到服务器（例如登录过期或页面被关掉）。
            </Text>
            <Group gap="xs" mt="xs">
              <Button size="compact-sm" variant="light" onClick={restoreLocalDraft} data-testid="local-draft-restore">
                恢复本地草稿
              </Button>
              <Button size="compact-sm" variant="subtle" color="gray" onClick={discardLocalDraft}>
                丢弃
              </Button>
            </Group>
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
              height: `calc(100dvh - 56px - ${TOP_BAR_HEIGHT}px - 32px)`,
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
                  onClick={openSettings}
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
            onAIImage={aiCover ? editSelectedImages : undefined}
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
        opened={mobile ? settingsOpenMobile : !wideScreen && settingsPinned}
        onClose={closeSettings}
        position="right"
        size={mobile ? '100%' : SETTINGS_WIDTH + 40}
        title="文章设置"
      >
        {settings}
      </Drawer>

      <Drawer
        opened={mobile ? outlineOpenMobile : !wideScreen && outlinePinned}
        onClose={closeOutline}
        position="left"
        size={mobile ? '80%' : OUTLINE_WIDTH + 40}
        title="目录"
      >
        <OutlinePanel items={outline} activeId={activeHeading} onJump={(id) => { closeOutline(); jumpToHeading(id); }} />
      </Drawer>

      {deleteOpen && <DeleteContentPostDialog profile={profile} slug={slug}
        onClose={closeDelete} onDeleted={onDeleted} />}

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
        onApplySummary={(value) => applyAI({ summary: value })}
        onConfirm={() => void confirmPublish()}
      />

      <AIRewriteDialog
        state={rewrite && rewrite.status === 'running' ? { ...rewrite, progress: rewriteJob.progress } : rewrite}
        view={rewriteView}
        onViewChange={setRewriteView}
        onEditPart={(index, text) => setRewrite((current) => {
          if (!current?.parts) return current;
          const parts = [...current.parts]; parts[index] = text;
          return { ...current, parts, text: parts.join('\n\n'), acceptError: undefined };
        })}
        onEditCandidate={(text) => setRewrite((current) => (current ? { ...current, text, acceptError: undefined } : current))}
        onAccept={acceptRewrite}
        onCopy={copyRewrite}
        onRetry={() => rewrite && startRewrite(rewrite.request)}
        onClose={closeRewrite}
      />

      <ImageWorkspace profile={profile} slug={slug} opened={imageOpen} request={imageRequest} enabled={aiCover}
        draft={draft} media={media.data ?? []} onClose={() => setImageOpen(false)}
        retarget={(target, appliedPath) => {
          if (target.kind === 'block') return editorRef.current?.retargetImage(target, appliedPath) ?? null;
          if (target.kind === 'cover' && (draftRef.current?.cover ?? '') === appliedPath) return { ...target, source: appliedPath };
          return target.kind === 'media' ? target : null;
        }}
        canApply={(target) => target.kind === 'block' ? !!editorRef.current?.canReplaceImage(target) : target.kind !== 'cover' || (draftRef.current?.cover ?? '') === (target.source ?? '')}
        onApply={(target, path) => {
          if (target.kind === 'block') return editorRef.current?.replaceImage(target, path) ?? false;
          if (target.kind === 'cover') {
            if ((draftRef.current?.cover ?? '') !== (target.source ?? '')) return false;
            applyAI({ cover: path });
          }
          return true;
        }} />
      <Modal opened={imageChoices.length > 0} onClose={() => setImageChoices([])} title="选择一张图片修改">
        <Stack>{imageChoices.map((image, index) => <Box key={image.id}>
          <ImagePreview src={contentMediaUrl(profile, image.source)} alt={`选中图片 ${index + 1}`} />
          <Button fullWidth onClick={() => { setImageChoices([]); editSelectedImages([image]); }}>修改这张图</Button>
        </Box>)}</Stack>
      </Modal>

      <SocialShareDrawer
        profile={profile}
        slug={slug}
        title={draft.title}
        body={draft.body}
        opened={shareOpen}
        onClose={() => setShareOpen(false)}
        aiText={aiText}
        mobile={mobile}
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
