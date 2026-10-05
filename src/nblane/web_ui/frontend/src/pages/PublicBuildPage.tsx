import {
  ActionIcon,
  Alert,
  Anchor,
  Badge,
  Box,
  Button,
  Center,
  Grid,
  Group,
  Image,
  List,
  Loader,
  Modal,
  Paper,
  Select,
  Stack,
  Switch,
  Text,
  TextInput,
  Title,
  Tooltip,
} from '@mantine/core';
import {
  IconArrowBackUp,
  IconExternalLink,
  IconPencil,
  IconRefresh,
  IconRocket,
  IconWorld,
} from '@tabler/icons-react';
import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useState, type ReactNode } from 'react';
import { Link, useParams } from 'react-router-dom';

import {
  publicSitePreviewPageUrl,
  useDeployPublicSite,
  useInitStudio,
  usePublicSite,
  usePublicSitePreview,
  useRollbackPublicSite,
  useSetPublicSitePost,
  useUpdatePublicSiteSettings,
} from '../api/hooks';
import type { PublicSitePost, PublicSiteSettingsUpdate } from '../api/types';
import { careerResumePath } from '../components/career/resumeModel';
import { MutationErrorAlert } from '../components/ConflictAlert';
import { contentEditorPath } from '../components/content/contentDraft';
import { WorksEditor } from '../components/publicSite/WorksEditor';
import {
  formatTime,
  liveChangeCount,
  liveSummary,
  pageLabel,
  siteView,
  type PublicSiteView,
} from '../components/publicSite/publicSiteModel';

function Section({ title, extra, children, testid }: { title: string; extra?: ReactNode; children: ReactNode; testid: string }) {
  return (
    <Paper withBorder radius="md" p="md" data-testid={testid}>
      <Group justify="space-between" mb="sm" wrap="nowrap">
        <Text fw={700}>{title}</Text>
        {extra}
      </Group>
      {children}
    </Paper>
  );
}

/** Site visibility, display switches and the intro read from the master resume. */
function SiteSection({ profile, data }: { profile: string; data: PublicSiteView }) {
  const update = useUpdatePublicSiteSettings(profile);
  const settings = data.settings;
  const intro = data.intro;
  const [baseUrl, setBaseUrl] = useState(settings.base_url);
  useEffect(() => setBaseUrl(settings.base_url), [settings.base_url]);

  const patch = (body: PublicSiteSettingsUpdate) => update.mutate(body);
  const toggle = (key: keyof PublicSiteSettingsUpdate, label: string, description: string, disabled = false) => (
    <Switch
      size="sm"
      label={label}
      description={description}
      checked={Boolean(settings[key as keyof typeof settings])}
      disabled={update.isPending || disabled}
      onChange={(event) => patch({ [key]: event.currentTarget.checked })}
      data-testid={`setting-${key}`}
    />
  );
  const isPublic = data.visibility === 'public';

  return (
    <Section title="网站与自我介绍" testid="site-section">
      <Stack gap="sm">
        <Switch
          size="md"
          label="网站公开"
          description={isPublic ? '发布后任何人都能访问。' : '私有时不能发布到线上。'}
          checked={isPublic}
          disabled={update.isPending}
          onChange={(event) => patch({ visibility: event.currentTarget.checked ? 'public' : 'private' })}
          data-testid="setting-visibility"
        />
        <Paper withBorder radius="sm" p="sm" bg="var(--mantine-color-default-hover)" data-testid="intro-card">
          <Group align="flex-start" wrap="nowrap" gap="sm">
            {intro.photo_url && settings.show_photo && (
              <Image src={intro.photo_url} alt="照片" w={48} h={64} radius="sm" fit="cover" />
            )}
            <Stack gap={2} style={{ minWidth: 0, flex: 1 }}>
              <Text size="sm" fw={600}>
                {intro.name}
                {intro.english_name ? ` · ${intro.english_name}` : ''}
              </Text>
              {intro.title && <Text size="xs">{intro.title}</Text>}
              <Text size="xs" c="dimmed" lineClamp={3}>
                {intro.summary.replace(/\*\*/g, '') || '还没有简介。'}
              </Text>
              <Anchor component={Link} to={careerResumePath(profile)} size="xs" data-testid="intro-edit">
                <IconPencil size={12} style={{ verticalAlign: 'middle' }} /> 在求职工作台编辑照片、头衔和简介
              </Anchor>
            </Stack>
          </Group>
        </Paper>
        {toggle('show_photo', '显示照片', intro.photo ? '首页显示简历照片。' : '主简历还没有照片。')}
        {toggle('show_email', '显示邮箱', intro.email ? '首页联系方式里显示邮箱。' : '主简历没有填邮箱。')}
        {toggle('show_phone', '显示电话', intro.phone ? '首页联系方式里显示电话。' : '主简历没有填电话。')}
        {toggle(
          'resume_pdf',
          '提供简历 PDF 下载',
          !data.pdf_available
            ? '服务器没有 Chromium，暂时无法生成 PDF。'
            : '发布时用主简历生成一页 PDF；电话、邮箱、照片跟随上面的开关。',
          !data.pdf_available && !settings.resume_pdf,
        )}
        {toggle(
          'show_projects',
          '公开项目页',
          `项目是内部工作记录，默认不上线（现有 ${data.projects_count} 个）。`,
        )}
        <TextInput
          size="xs"
          label="网站地址（可选）"
          description="部署在子路径时填写，例如 https://example.com/site；根域名留空即可。"
          placeholder="留空"
          value={baseUrl}
          onChange={(event) => setBaseUrl(event.currentTarget.value)}
          onBlur={() => {
            if (baseUrl.trim() !== settings.base_url) patch({ base_url: baseUrl.trim() });
          }}
          data-testid="setting-base-url"
        />
        <MutationErrorAlert error={update.error} title="设置保存失败" />
      </Stack>
    </Section>
  );
}

function PostRow({ profile, post }: { profile: string; post: PublicSitePost }) {
  const setPost = useSetPublicSitePost(profile);
  return (
    <Stack gap={4} py={6} style={{ borderBottom: '1px solid var(--mantine-color-default-border)' }} data-testid={`post-${post.slug}`}>
      <Group justify="space-between" wrap="nowrap" gap="xs">
        <Stack gap={0} style={{ minWidth: 0, flex: 1 }}>
          <Anchor component={Link} to={contentEditorPath(profile, post.slug)} size="sm" fw={500} truncate>
            {post.title || post.slug}
          </Anchor>
          <Group gap={6}>
            <Text size="xs" c="dimmed">
              {post.date}
            </Text>
            {post.live ? (
              <Badge size="xs" variant="light" color="teal">
                线上
              </Badge>
            ) : post.public ? (
              <Badge size="xs" variant="light" color="blue">
                待发布
              </Badge>
            ) : null}
            {post.live && !post.public && (
              <Badge size="xs" variant="light" color="orange">
                发布后下线
              </Badge>
            )}
            {post.status === 'published' && post.library_hidden && (
              <Tooltip label="已发布，但在内容库里设成了隐藏；打开开关即可公开" withinPortal>
                <Badge size="xs" variant="light" color="gray">
                  库中隐藏
                </Badge>
              </Tooltip>
            )}
            {post.status !== 'published' && (
              <Badge size="xs" variant="light" color="gray">
                草稿
              </Badge>
            )}
          </Group>
        </Stack>
        <Switch
          size="sm"
          checked={post.public}
          disabled={setPost.isPending}
          onChange={(event) => setPost.mutate({ slug: post.slug, isPublic: event.currentTarget.checked })}
          aria-label={`公开 ${post.title || post.slug}`}
          data-testid={`post-public-${post.slug}`}
        />
      </Group>
      {setPost.error && (
        <Text size="xs" c="red" data-testid={`post-error-${post.slug}`}>
          {setPost.error.message}
        </Text>
      )}
    </Stack>
  );
}

function PostsSection({ profile, posts }: { profile: string; posts: PublicSitePost[] }) {
  const publicCount = posts.filter((post) => post.public).length;
  return (
    <Section
      title="写作"
      testid="posts-section"
      extra={
        <Text size="xs" c="dimmed">
          公开 {publicCount} / {posts.length}
        </Text>
      }
    >
      {posts.length === 0 ? (
        <Text size="sm" c="dimmed">
          还没有文章，去内容工作台写第一篇。
        </Text>
      ) : (
        <Stack gap={0} mah={420} style={{ overflowY: 'auto' }}>
          {posts.map((post) => (
            <PostRow key={post.slug} profile={profile} post={post} />
          ))}
        </Stack>
      )}
      <Text size="xs" c="dimmed" mt="xs">
        打开开关会发布这篇文章（需通过发布检查），关闭会撤回为草稿。
      </Text>
    </Section>
  );
}

function PreviewPanel({ profile }: { profile: string }) {
  const [includeDrafts, setIncludeDrafts] = useState(false);
  const preview = usePublicSitePreview(profile, includeDrafts);
  const [selected, setSelected] = useState('index.html');
  const pages = preview.data?.pages ?? [];

  // Keep the selection while it still exists, otherwise fall back to the index.
  useEffect(() => {
    if (pages.length && !pages.some((page) => page.path === selected)) {
      setSelected((pages.find((page) => page.path === 'index.html') ?? pages[0]).path);
    }
  }, [pages, selected]);

  const src = publicSitePreviewPageUrl(profile, selected, includeDrafts);
  return (
    <Paper withBorder radius="md" p="sm" data-testid="preview-panel" style={{ position: 'sticky', top: 'calc(var(--app-shell-header-height, 0px) + 16px)' }}>
      <Group justify="space-between" mb="xs" wrap="wrap" gap="xs">
        <Group gap="xs" wrap="nowrap">
          <Select
            size="xs"
            w={260}
            data={pages.map((page) => ({ value: page.path, label: `${page.title || page.path}  ${pageLabel(page.path)}` }))}
            value={selected}
            onChange={(value) => value && setSelected(value)}
            allowDeselect={false}
            aria-label="预览页面"
            data-testid="preview-select"
          />
          <Tooltip label="刷新预览" withinPortal>
            <ActionIcon variant="default" onClick={() => void preview.refetch()} aria-label="刷新预览">
              <IconRefresh size={15} />
            </ActionIcon>
          </Tooltip>
          <Tooltip label="在新窗口打开" withinPortal>
            <ActionIcon variant="default" component="a" href={src} target="_blank" rel="noreferrer" aria-label="在新窗口打开">
              <IconExternalLink size={15} />
            </ActionIcon>
          </Tooltip>
        </Group>
        <Switch
          size="xs"
          label="预览包含草稿"
          checked={includeDrafts}
          onChange={(event) => setIncludeDrafts(event.currentTarget.checked)}
          data-testid="preview-include-drafts"
        />
      </Group>
      {includeDrafts && (
        <Text size="xs" c="orange" mb="xs">
          正在预览草稿；线上网站只会包含已公开的内容。
        </Text>
      )}
      {preview.isError ? (
        <Alert color="red" title="预览加载失败">
          {preview.error.message}
        </Alert>
      ) : preview.isPending ? (
        <Center h={600}>
          <Loader size="sm" />
        </Center>
      ) : (
        <iframe
          // Remount when the preview data refreshes so edits show up.
          key={`${src}-${preview.dataUpdatedAt}`}
          title="网站预览"
          data-testid="preview-frame"
          src={src}
          style={{
            width: '100%',
            height: 'calc(100vh - 220px)',
            minHeight: 560,
            border: '1px solid var(--mantine-color-default-border)',
            borderRadius: 'var(--mantine-radius-sm)',
            background: '#fff',
          }}
        />
      )}
    </Paper>
  );
}

/** Top bar: what the next deploy changes, deploy (with confirmation) and rollback. */
function LiveBar({ profile, data }: { profile: string; data: PublicSiteView }) {
  const deploy = useDeployPublicSite(profile);
  const rollback = useRollbackPublicSite(profile);
  const [confirm, setConfirm] = useState<'' | 'deploy' | 'rollback'>('');
  const live = data.live;
  if (!live) return null;
  const blocked = data.errors.length > 0;
  const pending = !live.in_sync;

  const run = () => {
    const mutation = confirm === 'deploy' ? deploy : rollback;
    mutation.mutate(undefined, { onSettled: () => setConfirm('') });
  };
  const changes = [
    ...(live.added ?? []).map((page) => ({ ...page, kind: '新增' })),
    ...(live.changed ?? []).map((page) => ({ ...page, kind: '更新' })),
    ...(live.removed ?? []).map((page) => ({ ...page, kind: '下线' })),
  ];

  return (
    <Paper withBorder radius="md" p="sm" data-testid="live-bar">
      <Group justify="space-between" wrap="wrap" gap="sm">
        <Stack gap={2}>
          <Group gap="xs">
            <IconWorld size={16} />
            <Text size="sm" fw={600} data-testid="live-summary">
              {liveSummary(live)}
            </Text>
          </Group>
          <Text size="xs" c="dimmed">
            {live.exists ? `上次发布：${formatTime(live.built_at)} · ${live.page_count} 页` : '尚未发布'}
            {live.pdf_live ? ' · 含简历 PDF' : ''}
          </Text>
        </Stack>
        <Group gap="xs">
          {live.has_previous && (
            <Tooltip label={`恢复到 ${formatTime(live.previous_built_at)} 的版本`} withinPortal>
              <Button
                size="sm"
                variant="default"
                leftSection={<IconArrowBackUp size={15} />}
                onClick={() => setConfirm('rollback')}
                data-testid="rollback-button"
              >
                回滚
              </Button>
            </Tooltip>
          )}
          <Button
            size="sm"
            leftSection={<IconRocket size={15} />}
            disabled={blocked || !pending}
            onClick={() => setConfirm('deploy')}
            data-testid="deploy-button"
          >
            发布到线上
          </Button>
        </Group>
      </Group>
      {blocked && (
        <Alert color="red" mt="sm" p="xs" title="发布前需要处理" data-testid="site-errors">
          <List size="xs">
            {data.errors.map((error) => (
              <List.Item key={error}>{error}</List.Item>
            ))}
          </List>
        </Alert>
      )}
      {data.warnings.length > 0 && (
        <Alert color="yellow" mt="sm" p="xs" data-testid="site-warnings">
          <List size="xs">
            {data.warnings.slice(0, 8).map((warning) => (
              <List.Item key={warning}>{warning}</List.Item>
            ))}
          </List>
        </Alert>
      )}
      {deploy.isSuccess && (deploy.data.warnings?.length ?? 0) > 0 && (
        <Alert color="yellow" mt="sm" p="xs" title="已发布，但有提示" data-testid="deploy-warnings">
          {deploy.data.warnings?.join('；')}
        </Alert>
      )}
      <Box mt={deploy.error || rollback.error ? 'sm' : 0}>
        <MutationErrorAlert error={deploy.error} title="发布失败" />
        <MutationErrorAlert error={rollback.error} title="回滚失败" />
      </Box>

      <Modal
        opened={confirm !== ''}
        onClose={() => setConfirm('')}
        title={confirm === 'deploy' ? '发布到线上' : '回滚线上网站'}
        centered
      >
        <Stack gap="sm" data-testid="live-confirm">
          {confirm === 'deploy' ? (
            <>
              <Text size="sm">发布后线上网站立即更新，只包含已公开的文章和作品。当前线上版本会保留，可以回滚。</Text>
              {changes.length > 0 && (
                <Stack gap={2} mah={240} style={{ overflowY: 'auto' }}>
                  {changes.map((page) => (
                    <Group key={`${page.kind}-${page.path}`} gap={6} wrap="nowrap">
                      <Badge size="xs" variant="light" color={page.kind === '下线' ? 'orange' : page.kind === '新增' ? 'teal' : 'blue'}>
                        {page.kind}
                      </Badge>
                      <Text size="xs" truncate>
                        {page.title}{' '}
                        <Text span c="dimmed" size="xs">
                          {pageLabel(page.path)}
                        </Text>
                      </Text>
                    </Group>
                  ))}
                </Stack>
              )}
              {live.pdf_pending && (
                <Text size="xs" c="dimmed">
                  {data.settings.resume_pdf ? '会重新生成简历 PDF。' : '会移除简历 PDF。'}
                </Text>
              )}
              {liveChangeCount(live) === 0 && !live.pdf_pending && (
                <Text size="xs" c="dimmed">页面没有变化。</Text>
              )}
            </>
          ) : (
            <Text size="sm">
              线上网站恢复到 {formatTime(live.previous_built_at)} 发布的版本；当前版本会被保留，可以再次回滚回来。
            </Text>
          )}
          <Group justify="flex-end">
            <Button variant="default" onClick={() => setConfirm('')}>
              取消
            </Button>
            <Button
              onClick={run}
              loading={deploy.isPending || rollback.isPending}
              color={confirm === 'rollback' ? 'orange' : undefined}
              data-testid="live-confirm-button"
            >
              {confirm === 'deploy' ? '确认发布' : '确认回滚'}
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Paper>
  );
}

/**
 * 公开站点 console: what the public site shows (intro switches, which posts,
 * works with videos/links), a live preview, and go-live with rollback.
 */
export function PublicBuildPage() {
  const { name = '' } = useParams();
  const site = usePublicSite(name);
  const init = useInitStudio(name);
  const queryClient = useQueryClient();

  if (site.isPending) {
    return (
      <Center py="xl">
        <Loader />
      </Center>
    );
  }
  if (site.isError || !site.data) {
    return (
      <Alert color="red" title="加载失败">
        {site.error?.message ?? '无法加载公开站点。'}
      </Alert>
    );
  }
  const data = siteView(site.data);

  if (!data.initialized) {
    return (
      <Stack gap="md" maw={720} mx="auto" w="100%">
        <Title order={2}>公开站点</Title>
        <Alert color="yellow" title="公开站点还没有初始化" data-testid="init-needed">
          <Group justify="space-between">
            <Text size="sm">初始化会创建公开资料文件，不会改动已有内容。</Text>
            <Button
              size="compact-sm"
              onClick={() =>
                init.mutate(
                  { etag: '' },
                  { onSuccess: () => queryClient.invalidateQueries({ queryKey: ['profiles', name, 'public-site'] }) },
                )
              }
              loading={init.isPending}
            >
              初始化
            </Button>
          </Group>
        </Alert>
        <MutationErrorAlert error={init.error} title="初始化失败" />
      </Stack>
    );
  }

  return (
    <Stack gap="md" data-testid="public-site-page" maw={1600} mx="auto" w="100%">
      <div>
        <Group gap="xs">
          <IconWorld size={24} />
          <Title order={2}>公开站点</Title>
        </Group>
        <Text size="sm" c="dimmed" mt={4}>
          自我介绍、写作和作品。左边决定网站显示什么，右边是实时预览，确认后发布到线上。
        </Text>
      </div>
      <LiveBar profile={name} data={data} />
      <Grid gutter="md" align="flex-start">
        <Grid.Col span={{ base: 12, lg: 5, xl: 4 }}>
        <Stack gap="md">
          <SiteSection profile={name} data={data} />
          <PostsSection profile={name} posts={data.posts} />
          <Section title="作品" testid="works-section">
            <WorksEditor profile={name} works={data.works} etag={data.works_etag} />
          </Section>
        </Stack>
        </Grid.Col>
        <Grid.Col span={{ base: 12, lg: 7, xl: 8 }}>
          <PreviewPanel profile={name} />
        </Grid.Col>
      </Grid>
    </Stack>
  );
}
