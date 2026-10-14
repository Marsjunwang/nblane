import { Alert, Button, Checkbox, Group, Loader, Modal, Stack, Text, TextInput } from '@mantine/core';
import { useEffect, useState } from 'react';

import { ApiError } from '../../api/client';
import { fetchContentPost, useDeleteContentPost } from '../../api/hooks';
import type { StudioPostResult } from '../../api/types';
import { clearLocalDraft } from './contentDraft';

/** Shared destructive-action confirmation for the library and editor. */
export function DeleteContentPostDialog({ profile, slug, onClose, onDeleted }: {
  profile: string;
  slug: string;
  onClose: () => void;
  onDeleted: () => void;
}) {
  const remove = useDeleteContentPost(profile);
  const [source, setSource] = useState<StudioPostResult | null>(null);
  const [loadError, setLoadError] = useState('');
  const [confirmTitle, setConfirmTitle] = useState('');
  const [recordChronicle, setRecordChronicle] = useState(false);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let active = true;
    setSource(null);
    setLoadError('');
    setConfirmTitle('');
    fetchContentPost(profile, slug).then(
      (result) => { if (active) setSource(result); },
      (error: unknown) => { if (active) setLoadError(error instanceof Error ? error.message : '文章加载失败'); },
    );
    return () => { active = false; };
  }, [profile, slug, reload]);

  const conflict = remove.error instanceof ApiError && remove.error.status === 412;
  const refresh = () => { remove.reset(); setReload((value) => value + 1); };
  const confirm = () => {
    if (!source || confirmTitle !== source.post.title || remove.isPending || conflict) return;
    remove.mutate({ slug, etag: source.etag, body: { confirm_title: confirmTitle, record_chronicle: recordChronicle } }, {
      onSuccess: () => {
        clearLocalDraft(window.localStorage, profile, slug);
        onDeleted();
      },
    });
  };

  return (
    <Modal opened onClose={() => { if (!remove.isPending) onClose(); }} title="删除文章" centered
      closeOnClickOutside={!remove.isPending} closeOnEscape={!remove.isPending} withCloseButton={!remove.isPending}
      data-testid="content-delete-dialog">
      <Stack>
        <Alert color="red" title="删除后会发生什么">
          正文、编辑模型和公开目录中的文章条目会被删除，未保存的修改会丢弃。图片和视频保留。
          删除后无法在工作台撤销；已有 Git 备份时可从备份找回。
          已上线的文章需要重新发布公开站点，才会从网站移除。
        </Alert>
        {!source && !loadError && <Loader size="sm" />}
        {loadError && <Alert color="red">{loadError}</Alert>}
        {source && <>
          <Text size="sm">请输入文章标题「{source.post.title}」确认删除。</Text>
          <TextInput label="文章标题" value={confirmTitle} onChange={(event) => setConfirmTitle(event.currentTarget.value)}
            disabled={remove.isPending} autoFocus data-testid="content-delete-title" />
          <Checkbox label="记入大事记" checked={recordChronicle} disabled={remove.isPending}
            onChange={(event) => setRecordChronicle(event.currentTarget.checked)} data-testid="content-delete-chronicle" />
        </>}
        {remove.error && <Alert color="red" title="删除失败">
          {conflict ? '文章已在别处被修改，请加载最新文章后重新确认。' : remove.error.message}
        </Alert>}
        <Group justify="flex-end">
          {(loadError || conflict) && <Button variant="default" onClick={refresh}>加载最新文章</Button>}
          <Button variant="default" onClick={onClose} disabled={remove.isPending}>取消</Button>
          <Button color="red" variant="outline" loading={remove.isPending}
            disabled={!source || !source.post.title || confirmTitle !== source.post.title || conflict}
            onClick={confirm} data-testid="content-delete-confirm">确认删除</Button>
        </Group>
      </Stack>
    </Modal>
  );
}
