import { Alert, Button, Center, Checkbox, Group, Image, Loader, Modal, ScrollArea, Stack, Text } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { useEffect, useMemo, useState } from 'react';

import { contentMediaUrl, useDeleteUnusedContentMedia, useUnusedContentMedia } from '../../api/hooks';

export function formatBytes(size: number): string {
  if (size >= 1024 * 1024) return `${(size / 1024 / 1024).toFixed(1)} MB`;
  if (size >= 1024) return `${Math.round(size / 1024)} KB`;
  return `${size} B`;
}

/**
 * Images / videos under media/blog/ that no post uses (covers and bodies of
 * every post, including drafts and the trash) and no public-library entry
 * points at. The owner picks what to delete; the server re-checks first.
 */
export function UnusedMediaModal({ profile, onClose }: { profile: string; onClose: () => void }) {
  const unused = useUnusedContentMedia(profile);
  const remove = useDeleteUnusedContentMedia(profile);
  const items = useMemo(() => unused.data?.items ?? [], [unused.data]);
  const [picked, setPicked] = useState<Set<string>>(new Set());
  const [confirming, setConfirming] = useState(false);

  useEffect(() => setPicked(new Set(items.map((item) => item.path))), [items]);

  const pickedSize = items.filter((item) => picked.has(item.path)).reduce((sum, item) => sum + item.size, 0);
  const toggle = (path: string) =>
    setPicked((current) => {
      const next = new Set(current);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });

  const confirm = () =>
    remove.mutate([...picked], {
      onSuccess: (result) => {
        setConfirming(false);
        const removed = result.removed ?? [];
        const skipped = picked.size - removed.length;
        notifications.show({
          color: 'teal',
          title: `已删除 ${removed.length} 个文件`,
          message: skipped > 0 ? `${skipped} 个刚被文章用上，已跳过。` : '可从 Git 备份找回。',
        });
      },
    });

  return (
    <Modal opened onClose={() => { if (!remove.isPending) onClose(); }} title="清理未使用的图片" centered size="lg"
      data-testid="content-unused-media">
      <Stack gap="sm">
        <Text size="sm" c="dimmed">
          没有任何文章（包括草稿和回收站里的）用作封面或插在正文里、也不在公开目录里的图片和视频。
        </Text>
        {unused.isLoading && <Loader size="sm" />}
        {unused.isError && <Alert color="red">{unused.error.message}</Alert>}
        {remove.error && <Alert color="red" title="删除失败">{remove.error.message}</Alert>}
        {!unused.isLoading && !unused.isError && items.length === 0 && (
          <Text size="sm" c="dimmed">没有未使用的文件。</Text>
        )}
        {items.length > 0 && (
          <>
            <ScrollArea.Autosize mah={420}>
              <Stack gap="xs">
                {items.map((item) => (
                  <Group key={item.path} gap="sm" wrap="nowrap" data-testid="content-unused-media-item">
                    <Checkbox checked={picked.has(item.path)} onChange={() => toggle(item.path)} aria-label={`选择 ${item.name}`} />
                    {item.kind === 'image' ? (
                      <Image src={contentMediaUrl(profile, item.path)} w={52} h={52} radius="sm" fit="cover" alt={item.name} />
                    ) : (
                      <Center w={52} h={52} bg="dark.5" style={{ borderRadius: 4 }}>
                        <Text size="xs">视频</Text>
                      </Center>
                    )}
                    <div style={{ minWidth: 0, flex: 1 }}>
                      <Text size="xs" truncate>{item.name}</Text>
                      <Text size="xs" c="dimmed" truncate>{item.post} · {formatBytes(item.size)}</Text>
                    </div>
                  </Group>
                ))}
              </Stack>
            </ScrollArea.Autosize>
            <Group justify="space-between">
              <Text size="sm">已选 {picked.size} 个，共 {formatBytes(pickedSize)}</Text>
              <Button color="red" variant="outline" disabled={picked.size === 0} onClick={() => setConfirming(true)}
                data-testid="content-unused-media-delete">
                删除所选
              </Button>
            </Group>
          </>
        )}
      </Stack>
      {confirming && (
        <Modal opened onClose={() => { if (!remove.isPending) setConfirming(false); }} title="删除文件" centered size="sm">
          <Stack>
            <Text size="sm">
              删除 {picked.size} 个文件（{formatBytes(pickedSize)}）。工作台里无法恢复，只能从 Git 备份找回。
            </Text>
            <Group justify="flex-end">
              <Button variant="default" onClick={() => setConfirming(false)} disabled={remove.isPending}>取消</Button>
              <Button color="red" loading={remove.isPending} onClick={confirm} data-testid="content-unused-media-confirm">
                删除
              </Button>
            </Group>
          </Stack>
        </Modal>
      )}
    </Modal>
  );
}
