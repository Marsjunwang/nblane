import { Alert, Button, Group, Loader, Modal, Stack, Text } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { usePurgeContentTrash, useContentTrash, useRestoreContentTrash } from '../../api/hooks';
import type { ContentTrashItem } from '../../api/types';
import { STATUS_LABELS, contentEditorPath } from './contentDraft';

function deletedAt(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

/** Deleted posts: restore one back into the library, or delete it for good. */
export function ContentTrashModal({ profile, onClose }: { profile: string; onClose: () => void }) {
  const navigate = useNavigate();
  const trash = useContentTrash(profile);
  const restore = useRestoreContentTrash(profile);
  const purge = usePurgeContentTrash(profile);
  const [purging, setPurging] = useState<ContentTrashItem | null>(null);
  const items = trash.data?.items ?? [];
  const busy = restore.isPending || purge.isPending;

  const onRestore = (item: ContentTrashItem) => {
    restore.mutate(item.id, {
      onSuccess: (result) => {
        notifications.show({ color: 'teal', title: '已恢复', message: `「${item.title || item.route}」回到了文章库。` });
        onClose();
        navigate(contentEditorPath(profile, result.slug));
      },
    });
  };

  return (
    <Modal opened onClose={() => { if (!busy) onClose(); }} title="回收站" centered size="lg" data-testid="content-trash">
      <Stack gap="sm">
        <Text size="sm" c="dimmed">
          删除的文章先放在这里，恢复后回到原来的位置和状态。彻底删除后只能从 Git 备份找回。
        </Text>
        {trash.isLoading && <Loader size="sm" />}
        {trash.isError && <Alert color="red">{trash.error.message}</Alert>}
        {restore.error && <Alert color="red" title="恢复失败">{restore.error.message}</Alert>}
        {purge.error && <Alert color="red" title="删除失败">{purge.error.message}</Alert>}
        {!trash.isLoading && !trash.isError && items.length === 0 && (
          <Text size="sm" c="dimmed">回收站是空的。</Text>
        )}
        {items.map((item) => (
          <Group key={item.id} justify="space-between" wrap="nowrap" data-testid="content-trash-item">
            <div style={{ minWidth: 0 }}>
              <Text size="sm" fw={500} truncate>{item.title || item.route}</Text>
              <Text size="xs" c="dimmed">
                {STATUS_LABELS[item.status] ?? item.status} · 删除于 {deletedAt(item.deleted_at)}
              </Text>
            </div>
            <Group gap="xs" wrap="nowrap">
              <Button size="compact-sm" variant="light" loading={restore.isPending && restore.variables === item.id}
                disabled={busy} onClick={() => onRestore(item)} data-testid="content-trash-restore">
                恢复
              </Button>
              <Button size="compact-sm" variant="subtle" color="red" disabled={busy}
                onClick={() => setPurging(item)} data-testid="content-trash-purge">
                彻底删除
              </Button>
            </Group>
          </Group>
        ))}
      </Stack>
      {purging && (
        <Modal opened onClose={() => { if (!purge.isPending) setPurging(null); }} title="彻底删除" centered size="sm">
          <Stack>
            <Text size="sm">「{purging.title || purging.route}」会从回收站删除，工作台里无法再恢复。</Text>
            <Group justify="flex-end">
              <Button variant="default" onClick={() => setPurging(null)} disabled={purge.isPending}>取消</Button>
              <Button color="red" loading={purge.isPending} data-testid="content-trash-purge-confirm"
                onClick={() => purge.mutate(purging.id, { onSuccess: () => setPurging(null) })}>
                彻底删除
              </Button>
            </Group>
          </Stack>
        </Modal>
      )}
    </Modal>
  );
}
