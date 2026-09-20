import {
  Alert,
  Badge,
  Button,
  Card,
  Center,
  Code,
  Drawer,
  Group,
  Loader,
  Modal,
  SegmentedControl,
  Select,
  Stack,
  Text,
  Textarea,
  Title,
  UnstyledButton,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconRefresh } from '@tabler/icons-react';
import { useState } from 'react';
import { useParams } from 'react-router-dom';

import { ApiError } from '../api/client';
import {
  useActivityItem,
  useActivityList,
  useApplyActivity,
  useDismissActivity,
} from '../api/hooks';

const STATUS_LABELS: Record<string, string> = {
  pending: '待审批',
  applied: '已应用',
  dismissed: '已驳回',
  failed: '失败',
  superseded: '已取代',
};

const STATUS_COLORS: Record<string, string> = {
  pending: 'yellow',
  applied: 'green',
  dismissed: 'gray',
  failed: 'red',
  superseded: 'violet',
};

function statusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status;
}

function statusColor(status: string): string {
  return STATUS_COLORS[status] ?? 'gray';
}

function JsonBlock({ value }: { value: unknown }) {
  if (value === null || value === undefined || value === '') {
    return null;
  }
  const text = typeof value === 'string' ? value : JSON.stringify(value, null, 2);
  return <Code block>{text}</Code>;
}

export function ActivityPage() {
  const { name = '' } = useParams();
  const [status, setStatus] = useState('pending');
  const [kind, setKind] = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [dismissOpen, setDismissOpen] = useState(false);
  const [dismissNote, setDismissNote] = useState('');

  const list = useActivityList(name, { status, kind });
  const detail = useActivityItem(name, selectedId ?? '');
  const apply = useApplyActivity(name);
  const dismiss = useDismissActivity(name);

  const item = detail.data?.item ?? null;
  const etag = detail.data?.etag ?? '';

  function handleMutationError(error: unknown, fallbackTitle: string) {
    if (error instanceof ApiError && error.status === 412) {
      notifications.show({
        color: 'yellow',
        title: '数据已被他人修改',
        message: '数据已被他人修改,已为你刷新。请确认后再试。',
      });
      void detail.refetch();
      return;
    }
    notifications.show({
      color: 'red',
      title: fallbackTitle,
      message: error instanceof Error ? error.message : String(error),
    });
    if (error instanceof ApiError && error.status === 409) {
      void detail.refetch();
    }
  }

  function handleApply() {
    if (!selectedId) {
      return;
    }
    apply.mutate(
      { itemId: selectedId, etag },
      {
        onSuccess: (result) => {
          notifications.show({
            color: 'green',
            title: '应用成功',
            message: (result.changed_paths ?? []).length > 0
              ? `已更新 ${(result.changed_paths ?? []).length} 个文件。`
              : '条目已应用。',
          });
        },
        onError: (error) => handleMutationError(error, '应用失败'),
      },
    );
  }

  function handleDismiss() {
    if (!selectedId) {
      return;
    }
    dismiss.mutate(
      { itemId: selectedId, etag, note: dismissNote.trim() },
      {
        onSuccess: () => {
          notifications.show({ color: 'green', title: '已驳回', message: '条目已驳回。' });
          setDismissOpen(false);
          setDismissNote('');
        },
        onError: (error) => handleMutationError(error, '驳回失败'),
      },
    );
  }

  const summaryStatus = list.data?.summary?.status ?? {};

  return (
    <Stack gap="md">
      <Group justify="space-between" wrap="nowrap">
        <Title order={2}>{name} · 代理活动</Title>
        <Group gap="xs">
          {Object.entries(summaryStatus).map(([key, count]) => (
            <Badge key={key} color={statusColor(key)} variant="light">
              {statusLabel(key)}: {count}
            </Badge>
          ))}
        </Group>
      </Group>

      <Group justify="space-between">
        <Group gap="sm">
          <SegmentedControl
            value={status}
            onChange={setStatus}
            data={[
              { value: 'pending', label: '待审批' },
              { value: 'applied', label: '已应用' },
              { value: 'dismissed', label: '已驳回' },
              { value: 'failed', label: '失败' },
              { value: 'all', label: '全部' },
            ]}
          />
          <Select
            aria-label="类型筛选"
            placeholder="全部类型"
            clearable
            value={kind || null}
            onChange={(value) => setKind(value ?? '')}
            data={[
              { value: 'candidate', label: 'candidate' },
              { value: 'patch', label: 'patch' },
              { value: 'writeback', label: 'writeback' },
            ]}
          />
        </Group>
        <Button
          variant="default"
          leftSection={<IconRefresh size={14} />}
          loading={list.isFetching}
          onClick={() => {
            void list.refetch();
            if (selectedId) {
              void detail.refetch();
            }
          }}
        >
          刷新
        </Button>
      </Group>

      {list.isPending ? (
        <Center py="xl">
          <Loader />
        </Center>
      ) : list.isError ? (
        <Alert color="red" title="加载失败">
          {list.error.message}
        </Alert>
      ) : (list.data.items ?? []).length === 0 ? (
        <Text c="dimmed">当前筛选下没有活动条目。</Text>
      ) : (
        <Stack gap="sm">
          {(list.data.items ?? []).map((entry) => (
            <UnstyledButton key={entry.id} onClick={() => setSelectedId(entry.id)}>
              <Card withBorder radius="md" padding="md">
                <Group justify="space-between" wrap="nowrap" align="flex-start">
                  <div>
                    <Text fw={500}>{entry.title || entry.id}</Text>
                    <Group gap="xs" mt="xs">
                      <Badge variant="light" color="blue">
                        {entry.kind}
                      </Badge>
                      {entry.candidate_type && (
                        <Badge variant="light" color="cyan">
                          {entry.candidate_type}
                        </Badge>
                      )}
                      {entry.target_owner && (
                        <Text size="sm" c="dimmed">
                          {entry.target_owner}
                        </Text>
                      )}
                    </Group>
                  </div>
                  <Group gap="sm" wrap="nowrap">
                    {entry.created && (
                      <Text size="xs" c="dimmed">
                        {entry.created}
                      </Text>
                    )}
                    <Badge color={statusColor(entry.status)} variant="filled">
                      {statusLabel(entry.status)}
                    </Badge>
                  </Group>
                </Group>
              </Card>
            </UnstyledButton>
          ))}
        </Stack>
      )}

      <Drawer
        opened={selectedId !== null}
        onClose={() => setSelectedId(null)}
        position="right"
        size="xl"
        title={item?.title || '活动详情'}
      >
        {detail.isPending ? (
          <Center py="xl">
            <Loader />
          </Center>
        ) : detail.isError ? (
          <Alert color="red" title="加载失败">
            {detail.error.message}
          </Alert>
        ) : item ? (
          <Stack gap="md">
            <Group gap="xs">
              <Badge color={statusColor(item.status)} variant="filled">
                {statusLabel(item.status)}
              </Badge>
              <Badge variant="light" color="blue">
                {item.kind}
              </Badge>
              {item.candidate_type && (
                <Badge variant="light" color="cyan">
                  {item.candidate_type}
                </Badge>
              )}
            </Group>

            <Stack gap={4}>
              {item.target_owner && <MetaRow label="目标" value={item.target_owner} />}
              {item.source_page && <MetaRow label="来源页面" value={item.source_page} />}
              {item.source_ref && <MetaRow label="来源引用" value={item.source_ref} />}
              {item.created && <MetaRow label="创建时间" value={item.created} />}
              {item.updated && <MetaRow label="更新时间" value={item.updated} />}
              {item.applied_at && <MetaRow label="应用时间" value={item.applied_at} />}
            </Stack>

            {item.summary && (
              <div>
                <Title order={5} mb="xs">
                  摘要
                </Title>
                <Text size="sm">{item.summary}</Text>
              </div>
            )}

            {item.error && (
              <Alert color="red" title="错误信息">
                {item.error}
              </Alert>
            )}

            {(item.warnings ?? []).length > 0 && (
              <Alert color="yellow" title="警告">
                <Stack gap={4}>
                  {(item.warnings ?? []).map((warning, index) => (
                    <Text key={index} size="sm">
                      {warning}
                    </Text>
                  ))}
                </Stack>
              </Alert>
            )}

            {item.preview !== '' && (
              <div>
                <Title order={5} mb="xs">
                  预览
                </Title>
                <JsonBlock value={item.preview} />
              </div>
            )}

            {item.payload !== undefined && Object.keys(item.payload).length > 0 && (
              <div>
                <Title order={5} mb="xs">
                  载荷
                </Title>
                <JsonBlock value={item.payload} />
              </div>
            )}

            {(item.changed_paths ?? []).length > 0 && (
              <div>
                <Title order={5} mb="xs">
                  变更文件
                </Title>
                <Stack gap={4}>
                  {(item.changed_paths ?? []).map((path) => (
                    <Code key={path}>{path}</Code>
                  ))}
                </Stack>
              </div>
            )}

            {item.status === 'pending' && (
              <Group justify="flex-end" mt="sm">
                <Button
                  variant="default"
                  color="red"
                  onClick={() => setDismissOpen(true)}
                  disabled={apply.isPending || dismiss.isPending}
                >
                  驳回
                </Button>
                <Button onClick={handleApply} loading={apply.isPending}>
                  应用
                </Button>
              </Group>
            )}
          </Stack>
        ) : null}
      </Drawer>

      <Modal
        opened={dismissOpen}
        onClose={() => setDismissOpen(false)}
        title="驳回条目"
        centered
      >
        <Stack gap="md">
          <Textarea
            label="备注(可选)"
            placeholder="记录驳回原因…"
            value={dismissNote}
            onChange={(event) => setDismissNote(event.currentTarget.value)}
            autosize
            minRows={2}
          />
          <Group justify="flex-end">
            <Button variant="default" onClick={() => setDismissOpen(false)}>
              取消
            </Button>
            <Button color="red" onClick={handleDismiss} loading={dismiss.isPending}>
              确认驳回
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  );
}

function MetaRow({ label, value }: { label: string; value: string }) {
  return (
    <Group gap="xs" wrap="nowrap">
      <Text size="sm" c="dimmed" w={80}>
        {label}
      </Text>
      <Text size="sm">{value}</Text>
    </Group>
  );
}
