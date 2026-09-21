import {
  Alert,
  Badge,
  Button,
  Card,
  Center,
  Group,
  Loader,
  Menu,
  Modal,
  SegmentedControl,
  Stack,
  Text,
  Textarea,
  TextInput,
  Timeline,
  Title,
  UnstyledButton,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconChevronDown, IconRefresh } from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { useParams } from 'react-router-dom';

import { ApiError } from '../api/client';
import {
  useArchiveInboxItem,
  useCaptureInbox,
  useClarifyInbox,
  useDiscardInboxItem,
  useInboxList,
} from '../api/hooks';
import type { InboxClarifyAction, InboxItem } from '../api/types';

const STATUS_LABELS: Record<string, string> = {
  inbox: '待处置',
  captured: '已捕获',
  clarified: '已澄清',
  active: '进行中',
  archived: '已归档',
  discarded: '已丢弃',
};

const STATUS_COLORS: Record<string, string> = {
  inbox: 'yellow',
  captured: 'cyan',
  clarified: 'green',
  active: 'blue',
  archived: 'gray',
  discarded: 'red',
};

const OPEN_STATUSES = new Set(['inbox', 'captured', 'clarified', 'active']);

const CLARIFY_ACTIONS: { action: InboxClarifyAction; label: string }[] = [
  { action: 'to_kanban_queue', label: '转入看板' },
  { action: 'to_learning_resource', label: '转入学习资源' },
  { action: 'to_activity_habit', label: '转为习惯' },
  { action: 'to_evidence_draft', label: '转为证据草稿' },
  { action: 'discard', label: '丢弃' },
  { action: 'archive', label: '归档' },
];

function statusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status;
}

function statusColor(status: string): string {
  return STATUS_COLORS[status] ?? 'gray';
}

/** openclaw (agent/WeChat MCP capture) vs human-web (this UI) badge. */
function capturedByColor(capturedBy: string): string {
  if (capturedBy === 'openclaw') {
    return 'violet';
  }
  if (capturedBy.startsWith('human-')) {
    return 'blue';
  }
  return 'gray';
}

function parseTags(raw: string): string[] {
  return raw
    .split(/[,，\n]/)
    .map((tag) => tag.trim())
    .filter((tag) => tag.length > 0);
}

export function InboxPage() {
  const { name = '' } = useParams();
  const [status, setStatus] = useState('inbox,captured,clarified');
  const [title, setTitle] = useState('');
  const [tags, setTags] = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [note, setNote] = useState('');

  const list = useInboxList(name, status);
  const capture = useCaptureInbox(name);
  const clarify = useClarifyInbox(name);
  const archive = useArchiveInboxItem(name);
  const discard = useDiscardInboxItem(name);

  const etag = list.data?.etag ?? '';
  const item: InboxItem | null =
    (list.data?.data.items ?? []).find((entry) => entry.id === selectedId) ?? null;
  const mutating =
    capture.isPending || clarify.isPending || archive.isPending || discard.isPending;

  // Close the modal when the selected entry is no longer in the loaded list
  // (filter switch or refetch dropping it) instead of leaving an empty shell.
  // Guards on `list.data` so a filter change (data briefly undefined while the
  // new query loads) does not close the modal prematurely.
  useEffect(() => {
    if (selectedId !== null && list.data !== undefined && item === null) {
      setSelectedId(null);
    }
  }, [selectedId, list.data, item]);

  function handleMutationError(error: unknown, fallbackTitle: string) {
    if (error instanceof ApiError && error.status === 412) {
      notifications.show({
        color: 'yellow',
        title: '数据已被他人修改',
        message: '数据已被他人修改,已为你刷新。请确认后再试。',
      });
      void list.refetch();
      return;
    }
    notifications.show({
      color: 'red',
      title: fallbackTitle,
      message: error instanceof Error ? error.message : String(error),
    });
    if (error instanceof ApiError && error.status === 409) {
      void list.refetch();
    }
  }

  function handleCapture(event: FormEvent) {
    event.preventDefault();
    const cleanTitle = title.trim();
    if (!cleanTitle) {
      return;
    }
    capture.mutate(
      { body: { title: cleanTitle, raw_text: '', source: 'web', tags: parseTags(tags) }, etag },
      {
        onSuccess: () => {
          notifications.show({ color: 'green', title: '已记录', message: '已加入收件箱。' });
          setTitle('');
          setTags('');
        },
        onError: (error) => handleMutationError(error, '记录失败'),
      },
    );
  }

  function handleClarify(action: InboxClarifyAction) {
    if (!selectedId) {
      return;
    }
    clarify.mutate(
      { itemId: selectedId, action, note: note.trim(), etag },
      {
        onSuccess: () => {
          notifications.show({ color: 'green', title: '已处置', message: '条目已处置。' });
          setSelectedId(null);
          setNote('');
        },
        onError: (error) => handleMutationError(error, '处置失败'),
      },
    );
  }

  function handleClose(kind: 'archive' | 'discard') {
    if (!selectedId) {
      return;
    }
    const mutation = kind === 'archive' ? archive : discard;
    mutation.mutate(
      { itemId: selectedId, note: note.trim(), etag },
      {
        onSuccess: () => {
          notifications.show({
            color: 'green',
            title: kind === 'archive' ? '已归档' : '已丢弃',
            message: kind === 'archive' ? '条目已归档。' : '条目已丢弃。',
          });
          setSelectedId(null);
          setNote('');
        },
        onError: (error) =>
          handleMutationError(error, kind === 'archive' ? '归档失败' : '丢弃失败'),
      },
    );
  }

  return (
    <Stack gap="md">
      <Group justify="space-between" wrap="nowrap">
        <Title order={2}>{name} · 收件箱</Title>
        <Button
          variant="default"
          leftSection={<IconRefresh size={14} />}
          loading={list.isFetching}
          onClick={() => void list.refetch()}
        >
          刷新
        </Button>
      </Group>

      <Card withBorder radius="md" padding="md">
        <form onSubmit={handleCapture}>
          <Group align="flex-end">
            <TextInput
              label="随手记"
              placeholder="微信随手记: 一句话就行…"
              value={title}
              onChange={(event) => setTitle(event.currentTarget.value)}
              style={{ flex: '1 1 160px' }}
            />
            <TextInput
              label="标签(可选)"
              placeholder="逗号分隔"
              value={tags}
              onChange={(event) => setTags(event.currentTarget.value)}
              style={{ flex: '1 1 140px', maxWidth: 220 }}
            />
            <Button type="submit" loading={capture.isPending} disabled={!title.trim()}>
              记录
            </Button>
          </Group>
        </form>
      </Card>

      <SegmentedControl
        value={status}
        onChange={setStatus}
        data={[
          { value: 'inbox,captured,clarified', label: '待处置' },
          { value: 'archived', label: '已归档' },
          { value: 'discarded', label: '已丢弃' },
          { value: 'all', label: '全部' },
        ]}
      />

      {list.isPending ? (
        <Center py="xl">
          <Loader />
        </Center>
      ) : list.isError ? (
        <Alert color="red" title="加载失败">
          {list.error.message}
        </Alert>
      ) : (list.data.data.items ?? []).length === 0 ? (
        <Text c="dimmed">当前筛选下没有收件箱条目。</Text>
      ) : (
        <Stack gap="sm">
          {(list.data.data.items ?? []).map((entry) => (
            <UnstyledButton
              key={entry.id}
              onClick={() => {
                setSelectedId(entry.id);
                setNote('');
              }}
            >
              <Card withBorder radius="md" padding="md">
                <Group justify="space-between" wrap="nowrap" align="flex-start">
                  <div>
                    <Text fw={500}>{entry.title}</Text>
                    <Group gap="xs" mt="xs">
                      <Badge variant="light" color="cyan">
                        {entry.type}
                      </Badge>
                      {(entry.tags ?? []).map((tag) => (
                        <Badge key={tag} variant="light" color="brand">
                          {tag}
                        </Badge>
                      ))}
                    </Group>
                  </div>
                  <Group gap="sm" wrap="nowrap">
                    {entry.created_at && (
                      <Text size="xs" c="dimmed">
                        {entry.created_at}
                      </Text>
                    )}
                    {entry.captured_by && (
                      <Badge variant="light" color={capturedByColor(entry.captured_by)}>
                        {entry.captured_by}
                      </Badge>
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

      <Modal
        opened={selectedId !== null}
        onClose={() => setSelectedId(null)}
        size="lg"
        title={item?.title || '条目详情'}
        centered
      >
        {item ? (
          <Stack gap="md">
            <Group gap="xs">
              <Badge color={statusColor(item.status)} variant="filled">
                {statusLabel(item.status)}
              </Badge>
              <Badge variant="light" color="cyan">
                {item.type}
              </Badge>
              {item.captured_by && (
                <Badge variant="light" color={capturedByColor(item.captured_by)}>
                  {item.captured_by}
                </Badge>
              )}
              {(item.tags ?? []).map((tag) => (
                <Badge key={tag} variant="light" color="brand">
                  {tag}
                </Badge>
              ))}
            </Group>

            <Stack gap={4}>
              {item.created_at && <MetaRow label="创建时间" value={item.created_at} />}
              {item.source && <MetaRow label="来源" value={item.source} />}
            </Stack>

            {item.raw_text && (
              <div>
                <Title order={5} mb="xs">
                  原文
                </Title>
                <Text size="sm" style={{ whiteSpace: 'pre-wrap' }}>
                  {item.raw_text}
                </Text>
              </div>
            )}

            {(item.history ?? []).length > 0 && (
              <div>
                <Title order={5} mb="xs">
                  历史
                </Title>
                <Timeline active={(item.history ?? []).length - 1} bulletSize={12} lineWidth={1}>
                  {(item.history ?? []).map((event, index) => (
                    <Timeline.Item
                      key={index}
                      title={
                        event.action +
                        (event.to_status ? ` → ${statusLabel(event.to_status)}` : '')
                      }
                    >
                      <Text size="xs" c="dimmed">
                        {event.at}
                      </Text>
                      {event.note && <Text size="sm">{event.note}</Text>}
                    </Timeline.Item>
                  ))}
                </Timeline>
              </div>
            )}

            {OPEN_STATUSES.has(item.status) && (
              <>
                <Textarea
                  label="备注(可选)"
                  placeholder="处置备注…"
                  value={note}
                  onChange={(event) => setNote(event.currentTarget.value)}
                  autosize
                  minRows={2}
                />
                <Group justify="flex-end" mt="sm">
                  <Button
                    variant="default"
                    color="red"
                    onClick={() => handleClose('discard')}
                    disabled={mutating}
                  >
                    丢弃
                  </Button>
                  <Button
                    variant="default"
                    onClick={() => handleClose('archive')}
                    disabled={mutating}
                  >
                    归档
                  </Button>
                  <Menu withinPortal position="bottom-end">
                    <Menu.Target>
                      <Button rightSection={<IconChevronDown size={14} />} loading={clarify.isPending}>
                        处置
                      </Button>
                    </Menu.Target>
                    <Menu.Dropdown>
                      {CLARIFY_ACTIONS.map(({ action, label }) => (
                        <Menu.Item key={action} onClick={() => handleClarify(action)}>
                          {label}
                        </Menu.Item>
                      ))}
                    </Menu.Dropdown>
                  </Menu>
                </Group>
              </>
            )}
          </Stack>
        ) : null}
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
