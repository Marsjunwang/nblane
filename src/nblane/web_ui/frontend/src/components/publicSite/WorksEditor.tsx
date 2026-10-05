import {
  ActionIcon,
  Alert,
  Badge,
  Box,
  Button,
  Collapse,
  FileButton,
  Group,
  Image,
  Paper,
  SegmentedControl,
  Select,
  Stack,
  Switch,
  Text,
  Textarea,
  TextInput,
  Tooltip,
} from '@mantine/core';
import {
  IconArrowDown,
  IconArrowUp,
  IconChevronDown,
  IconChevronRight,
  IconLink,
  IconPhoto,
  IconPlus,
  IconStar,
  IconTrash,
  IconVideo,
} from '@tabler/icons-react';
import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';

import { profileMediaUrl, uploadPublicSiteWorkMedia, useSavePublicSiteWorks } from '../../api/hooks';
import type { PublicSiteWork, PublicSiteWorkLink } from '../../api/types';
import { MutationErrorAlert } from '../ConflictAlert';
import {
  WORK_TYPE_OPTIONS,
  cleanWorks,
  emptyWork,
  moveItem,
  videoHint,
  videoKind,
  workTypeLabel,
  worksIssues,
} from './publicSiteModel';

function mediaSrc(profile: string, value: string): string {
  const clean = value.trim();
  if (!clean) return '';
  return /^https?:\/\//i.test(clean) ? clean : profileMediaUrl(profile, clean);
}

function LinkRows({
  links,
  onChange,
  testid,
}: {
  links: PublicSiteWorkLink[];
  onChange: (links: PublicSiteWorkLink[]) => void;
  testid: string;
}) {
  const set = (index: number, patch: Partial<PublicSiteWorkLink>) =>
    onChange(links.map((link, i) => (i === index ? { ...link, ...patch } : link)));
  return (
    <Stack gap={6}>
      <Text size="xs" fw={500}>
        链接（论文、代码、公开文章、演示……）
      </Text>
      {links.map((link, index) => (
        <Group key={index} gap={6} wrap="nowrap">
          <TextInput
            size="xs"
            placeholder="名称，如 论文"
            value={link.label}
            onChange={(event) => set(index, { label: event.currentTarget.value })}
            w={130}
            aria-label="链接名称"
          />
          <TextInput
            size="xs"
            placeholder="https://"
            value={link.url}
            onChange={(event) => set(index, { url: event.currentTarget.value })}
            style={{ flex: 1 }}
            aria-label="链接地址"
            data-testid={`${testid}-link-url-${index}`}
          />
          <ActionIcon
            variant="subtle"
            color="gray"
            onClick={() => onChange(links.filter((_, i) => i !== index))}
            aria-label="删除链接"
          >
            <IconTrash size={14} />
          </ActionIcon>
        </Group>
      ))}
      <Button
        size="compact-xs"
        variant="subtle"
        leftSection={<IconLink size={13} />}
        onClick={() => onChange([...links, { label: '', url: '' }])}
        style={{ alignSelf: 'flex-start' }}
        data-testid={`${testid}-add-link`}
      >
        添加链接
      </Button>
    </Stack>
  );
}

function WorkCard({
  profile,
  work,
  index,
  total,
  open,
  onToggle,
  onChange,
  onMove,
  onRemove,
}: {
  profile: string;
  work: PublicSiteWork;
  index: number;
  total: number;
  open: boolean;
  onToggle: () => void;
  onChange: (patch: Partial<PublicSiteWork>) => void;
  onMove: (delta: number) => void;
  onRemove: () => void;
}) {
  const [busy, setBusy] = useState<'' | 'video' | 'cover'>('');
  const [uploadError, setUploadError] = useState('');
  const testid = `work-${index}`;
  const kind = videoKind(work.video);
  const coverSrc = mediaSrc(profile, work.cover);

  const upload = (field: 'video' | 'cover') => (file: File | null) => {
    if (!file) return;
    setBusy(field);
    setUploadError('');
    uploadPublicSiteWorkMedia(profile, file)
      .then((res) => onChange(field === 'video' ? { video: res.path, video_mode: 'embed' } : { cover: res.path }))
      .catch((err: unknown) => setUploadError(err instanceof Error ? err.message : String(err)))
      .finally(() => setBusy(''));
  };

  return (
    <Paper withBorder radius="md" p="sm" data-testid={testid}>
      <Group justify="space-between" wrap="nowrap" gap="xs">
        <Group
          gap="xs"
          wrap="nowrap"
          style={{ cursor: 'pointer', minWidth: 0, flex: 1 }}
          onClick={onToggle}
          data-testid={`${testid}-toggle`}
        >
          {open ? <IconChevronDown size={15} /> : <IconChevronRight size={15} />}
          <Text size="sm" fw={600} truncate>
            {work.title || '未命名作品'}
          </Text>
          <Badge size="xs" variant="light" color="gray">
            {workTypeLabel(work.type)}
          </Badge>
          {work.featured && <IconStar size={13} color="var(--mantine-color-yellow-6)" />}
          {kind && <IconVideo size={13} />}
        </Group>
        <Group gap={4} wrap="nowrap">
          <Switch
            size="xs"
            label="公开"
            checked={work.status === 'published'}
            onChange={(event) => onChange({ status: event.currentTarget.checked ? 'published' : 'draft' })}
            data-testid={`${testid}-published`}
          />
          <ActionIcon variant="subtle" color="gray" disabled={index === 0} onClick={() => onMove(-1)} aria-label="上移">
            <IconArrowUp size={14} />
          </ActionIcon>
          <ActionIcon variant="subtle" color="gray" disabled={index === total - 1} onClick={() => onMove(1)} aria-label="下移">
            <IconArrowDown size={14} />
          </ActionIcon>
          <ActionIcon variant="subtle" color="red" onClick={onRemove} aria-label="删除作品" data-testid={`${testid}-remove`}>
            <IconTrash size={14} />
          </ActionIcon>
        </Group>
      </Group>
      <Collapse in={open}>
        <Stack gap="xs" mt="sm">
          <Group gap="xs" grow align="flex-start">
            <TextInput
              size="xs"
              label="标题"
              required
              value={work.title}
              onChange={(event) => onChange({ title: event.currentTarget.value })}
              data-testid={`${testid}-title`}
            />
            <Select
              size="xs"
              label="类型"
              data={WORK_TYPE_OPTIONS}
              value={work.type}
              onChange={(value) => onChange({ type: value ?? 'other' })}
              allowDeselect={false}
              maw={120}
            />
            <TextInput
              size="xs"
              label="年份"
              value={work.year}
              onChange={(event) => onChange({ year: event.currentTarget.value })}
              maw={90}
            />
          </Group>
          <Textarea
            size="xs"
            label="简介"
            autosize
            minRows={2}
            maxRows={6}
            value={work.summary}
            onChange={(event) => onChange({ summary: event.currentTarget.value })}
          />
          <Stack gap={4}>
            <Group gap="xs" align="flex-end" wrap="nowrap">
              <TextInput
                size="xs"
                label="视频"
                placeholder="B 站 / YouTube / Vimeo 网址，或上传 mp4"
                value={work.video}
                onChange={(event) => onChange({ video: event.currentTarget.value })}
                style={{ flex: 1 }}
                data-testid={`${testid}-video`}
              />
              <FileButton accept="video/mp4,video/webm,video/quicktime" onChange={upload('video')}>
                {(props) => (
                  <Button {...props} size="xs" variant="default" loading={busy === 'video'} leftSection={<IconVideo size={14} />}>
                    上传
                  </Button>
                )}
              </FileButton>
            </Group>
            {kind && (
              <Group gap="xs" wrap="wrap">
                <SegmentedControl
                  size="xs"
                  value={work.video_mode}
                  onChange={(value) => onChange({ video_mode: value })}
                  data={[
                    { value: 'embed', label: '直接播放' },
                    { value: 'link', label: '只放链接' },
                  ]}
                  data-testid={`${testid}-video-mode`}
                />
                <Text size="xs" c={kind === 'link' && work.video_mode === 'embed' ? 'orange' : 'dimmed'} data-testid={`${testid}-video-hint`}>
                  {videoHint(work)}
                </Text>
              </Group>
            )}
          </Stack>
          <Group gap="xs" align="flex-end" wrap="nowrap">
            {coverSrc && <Image src={coverSrc} alt="封面" w={64} h={40} radius="sm" fit="cover" />}
            <TextInput
              size="xs"
              label={kind && work.video_mode === 'embed' ? '封面（有内嵌视频时不显示）' : '封面图'}
              placeholder="可选"
              value={work.cover}
              onChange={(event) => onChange({ cover: event.currentTarget.value })}
              style={{ flex: 1 }}
            />
            <FileButton accept="image/png,image/jpeg,image/webp,image/gif" onChange={upload('cover')}>
              {(props) => (
                <Button {...props} size="xs" variant="default" loading={busy === 'cover'} leftSection={<IconPhoto size={14} />}>
                  上传
                </Button>
              )}
            </FileButton>
          </Group>
          {uploadError && (
            <Text size="xs" c="red">
              上传失败：{uploadError}
            </Text>
          )}
          <LinkRows links={work.links ?? []} onChange={(links) => onChange({ links })} testid={testid} />
          <Switch
            size="xs"
            label="首页精选（没有精选时首页显示前 4 条）"
            checked={work.featured}
            onChange={(event) => onChange({ featured: event.currentTarget.checked })}
          />
        </Stack>
      </Collapse>
    </Paper>
  );
}

/**
 * Works list editor (`outputs.yaml`). Edits stay local until 保存作品; the
 * save carries `works_etag` so a concurrent edit elsewhere is not clobbered.
 */
export function WorksEditor({ profile, works, etag }: { profile: string; works: PublicSiteWork[]; etag: string }) {
  const save = useSavePublicSiteWorks(profile);
  const queryClient = useQueryClient();
  const [draft, setDraft] = useState<PublicSiteWork[]>(works);
  const [dirty, setDirty] = useState(false);
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  // Follow server data while there are no local edits (e.g. after save/refresh).
  useEffect(() => {
    if (!dirty) setDraft(works);
  }, [works, dirty]);

  const update = (next: PublicSiteWork[]) => {
    setDraft(next);
    setDirty(true);
  };
  const issues = worksIssues(draft);

  const submit = () =>
    save.mutate(
      { works: cleanWorks(draft), etag },
      {
        onSuccess: () => setDirty(false),
      },
    );
  const reset = () => {
    setDraft(works);
    setDirty(false);
    save.reset();
  };

  return (
    <Stack gap="xs" data-testid="works-editor">
      {draft.length === 0 && (
        <Text size="sm" c="dimmed" data-testid="works-empty">
          还没有作品。可以放重点项目视频、论文、代码仓库、发表在别处的文章链接。
        </Text>
      )}
      {draft.map((work, index) => (
        <WorkCard
          key={work.id || `new-${index}`}
          profile={profile}
          work={work}
          index={index}
          total={draft.length}
          open={openIndex === index}
          onToggle={() => setOpenIndex(openIndex === index ? null : index)}
          onChange={(patch) => update(draft.map((row, i) => (i === index ? { ...row, ...patch } : row)))}
          onMove={(delta) => {
            update(moveItem(draft, index, delta));
            if (openIndex === index) setOpenIndex(index + delta);
          }}
          onRemove={() => {
            update(draft.filter((_, i) => i !== index));
            setOpenIndex(null);
          }}
        />
      ))}
      {issues.length > 0 && dirty && (
        <Alert color="yellow" p="xs" data-testid="works-issues">
          <Text size="xs">{issues.join('；')}</Text>
        </Alert>
      )}
      <MutationErrorAlert
        error={save.error}
        title="作品保存失败"
        onRefetch={() => {
          reset();
          void queryClient.invalidateQueries({ queryKey: ['profiles', profile, 'public-site'] });
        }}
      />
      <Group justify="space-between">
        <Button
          size="xs"
          variant="light"
          leftSection={<IconPlus size={14} />}
          onClick={() => {
            update([...draft, emptyWork()]);
            setOpenIndex(draft.length);
          }}
          disabled={draft.length >= 60}
          data-testid="works-add"
        >
          添加作品
        </Button>
        <Group gap="xs">
          {dirty && (
            <Button size="xs" variant="subtle" color="gray" onClick={reset}>
              放弃修改
            </Button>
          )}
          <Tooltip label="作品改动保存后会出现在右侧预览里" withinPortal>
            <Box>
              <Button
                size="xs"
                onClick={submit}
                disabled={!dirty || issues.length > 0}
                loading={save.isPending}
                data-testid="works-save"
              >
                {dirty ? '保存作品' : '已保存'}
              </Button>
            </Box>
          </Tooltip>
        </Group>
      </Group>
    </Stack>
  );
}
