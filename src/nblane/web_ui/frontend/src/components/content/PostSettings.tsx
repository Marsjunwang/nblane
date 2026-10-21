import {
  ActionIcon,
  Box,
  Button,
  Center,
  CloseButton,
  FileButton,
  Group,
  Loader,
  Select,
  Stack,
  Tabs,
  TagsInput,
  Text,
  TextInput,
  Textarea,
  Tooltip,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconPhoto,
  IconPhotoStar,
  IconRowInsertBottom,
  IconTrash,
  IconUpload,
} from '@tabler/icons-react';

import { contentMediaUrl, useDeleteContentPostMedia } from '../../api/hooks';
import type { ContentMedia } from '../../api/types';
import type { AIPatch } from './aiUndo';
import { AICoverGenerator } from './AICoverGenerator';
import { AIMetaSuggestions } from './AIMetaSuggestions';
import type { PostDraft } from './contentDraft';
import { ImagePreview } from './ImagePreview';
import type { ImageEditRequest } from './imageTypes';

function MediaList({
  profile,
  media,
  loading,
  uploading,
  cover,
  onUpload,
  onInsert,
  onSetCover,
  onDelete,
  deleting,
  bodyUses,
  onImageEdit,
}: {
  profile: string;
  media: ContentMedia[];
  loading: boolean;
  uploading: boolean;
  cover: string;
  onUpload: (file: File | null) => void;
  onInsert: (item: ContentMedia) => void;
  onSetCover: (path: string) => void;
  onDelete?: (item: ContentMedia) => void;
  deleting?: string;
  /** True when the unsaved editor text already uses this file. */
  bodyUses?: (path: string) => boolean;
  onImageEdit: (item: ContentMedia) => void;
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
        上传后插入到光标处。
        <Text span inherit visibleFrom="sm">
          也可以把图片直接拖进正文。
        </Text>
      </Text>
      {loading ? (
        <Loader size="xs" />
      ) : (
        media.map((item) => (
          <Group key={item.path} gap="xs" wrap="wrap">
            {item.kind === 'image' ? (
              <ImagePreview src={contentMediaUrl(profile, item.path)} width={88} height={66} alt={item.name} />
            ) : (
              <Center w={52} h={52} bg="dark.5" style={{ borderRadius: 4 }}>
                <Text size="xs">视频</Text>
              </Center>
            )}
            <Box style={{ flex: 1, minWidth: 100 }}>
              <Text size="xs" truncate>
                {item.name}
              </Text>
              <Text size="xs" c="dimmed">
                {item.path === cover ? '封面' : item.referenced ? '正文已引用' : '未使用'}
              </Text>
            </Box>
            {item.kind === 'image' && <Tooltip label="AI 修改图片"><ActionIcon size={44} variant="subtle" aria-label={`AI 修改 ${item.name}`} onClick={() => onImageEdit(item)}>AI</ActionIcon></Tooltip>}
            <Tooltip label="插入到光标处">
              <ActionIcon size={44} variant="subtle" aria-label={`插入 ${item.name}`} onClick={() => onInsert(item)}>
                <IconRowInsertBottom size={16} />
              </ActionIcon>
            </Tooltip>
            {item.kind === 'image' && item.path !== cover && (
              <Tooltip label="设为封面">
                <ActionIcon size={44} variant="subtle" aria-label={`设 ${item.name} 为封面`} onClick={() => onSetCover(item.path)}>
                  <IconPhotoStar size={16} />
                </ActionIcon>
              </Tooltip>
            )}
            {onDelete && !item.referenced && item.path !== cover && !bodyUses?.(item.path) && (
              <Tooltip label="删除这个文件（其他文章在用时会拒绝）">
                <ActionIcon size={44} variant="subtle" color="red" aria-label={`删除 ${item.name}`}
                  loading={deleting === item.path} disabled={Boolean(deleting)} onClick={() => onDelete(item)}
                  data-testid="content-media-delete">
                  <IconTrash size={16} />
                </ActionIcon>
              </Tooltip>
            )}
          </Group>
        ))
      )}
    </Stack>
  );
}

export function PostSettings({
  profile,
  slug,
  draft,
  media,
  mediaLoading,
  uploading,
  aiText,
  aiCover,
  onEdit,
  onApplyAI,
  onUpload,
  onInsert,
  onImageOpen,
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
  /** AI-suggested field values: applied with an undo notification. */
  onApplyAI: (patch: AIPatch) => void;
  onUpload: (file: File | null) => void;
  onInsert: (item: ContentMedia) => void;
  onImageOpen: (request: ImageEditRequest | null) => void;
}) {
  const removeMedia = useDeleteContentPostMedia(profile, slug);
  const deleteMedia = (item: ContentMedia) =>
    removeMedia.mutate(item.path, {
      onSuccess: () => notifications.show({ color: 'gray', title: '已删除', message: item.name }),
      onError: (error) =>
        notifications.show({ color: 'red', title: '没有删除', message: error instanceof Error ? error.message : String(error) }),
    });
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
          <AIMetaSuggestions profile={profile} enabled={aiText} draft={draft} onApply={onApplyAI} />
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
              <ImagePreview src={contentMediaUrl(profile, draft.cover)} height={180} alt="封面预览" />
              <CloseButton size="sm" pos="absolute" top={6} right={6} aria-label="移除封面" onClick={() => onEdit({ cover: '' })} />
            </Box>
          )}
          <AICoverGenerator enabled={aiCover} cover={draft.cover} onOpen={onImageOpen} />
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
          onDelete={deleteMedia}
          deleting={removeMedia.isPending ? removeMedia.variables : undefined}
          bodyUses={(path) => draft.body.includes(path)}
          onImageEdit={(item) => onImageOpen({ mode: 'edit', reference: item.path, target: { kind: 'media', source: item.path } })}
        />
      </Tabs.Panel>
    </Tabs>
  );
}
