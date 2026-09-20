import {
  ActionIcon,
  Alert,
  Badge,
  Button,
  Card,
  Center,
  Group,
  Loader,
  Menu,
  Paper,
  Progress,
  ScrollArea,
  Select,
  Stack,
  Text,
  TextInput,
  Title,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconDots, IconRefresh } from '@tabler/icons-react';
import { useState } from 'react';
import type { FormEvent } from 'react';
import { useParams } from 'react-router-dom';

import { ApiError } from '../api/client';
import {
  useAddKanbanCard,
  useDoneKanbanCard,
  useKanbanBoard,
  useMoveKanbanCard,
} from '../api/hooks';
import type { KanbanTask } from '../api/types';

function splitTags(tags: string): string[] {
  return tags
    .split(/[,\s]+/)
    .map((tag) => tag.trim())
    .filter(Boolean);
}

interface CardActions {
  sectionNames: string[];
  mutating: boolean;
  onMove: (cardRef: string, targetSection: string) => void;
  onDone: (cardRef: string) => void;
}

function KanbanCardItem({
  task,
  section,
  actions,
}: {
  task: KanbanTask;
  section: string;
  actions: CardActions;
}) {
  const tags = splitTags(task.tags ?? '');
  const subtasks = task.subtasks ?? [];
  const doneCount = subtasks.filter((subtask) => subtask.done).length;
  const dueDate = task.completed_on ?? task.started_on;
  const moveTargets = actions.sectionNames.filter((name) => name !== section);

  return (
    <Card withBorder radius="sm" padding="sm" shadow="xs">
      <Stack gap="xs">
        <Group justify="space-between" wrap="nowrap" align="flex-start">
          <Text fw={500} size="sm" td={task.done ? 'line-through' : undefined}>
            {task.title}
          </Text>
          <Menu withinPortal position="bottom-end">
            <Menu.Target>
              <ActionIcon
                variant="subtle"
                color="gray"
                size="sm"
                aria-label={`卡片操作 ${task.title}`}
                disabled={actions.mutating}
              >
                <IconDots size={14} />
              </ActionIcon>
            </Menu.Target>
            <Menu.Dropdown>
              <Menu.Sub>
                <Menu.Sub.Target>
                  <Menu.Sub.Item>移动到…</Menu.Sub.Item>
                </Menu.Sub.Target>
                <Menu.Sub.Dropdown>
                  {moveTargets.map((name) => (
                    <Menu.Item key={name} onClick={() => actions.onMove(task.title, name)}>
                      {name}
                    </Menu.Item>
                  ))}
                </Menu.Sub.Dropdown>
              </Menu.Sub>
              <Menu.Item
                disabled={task.done && section === 'Done'}
                onClick={() => actions.onDone(task.title)}
              >
                标记完成
              </Menu.Item>
            </Menu.Dropdown>
          </Menu>
        </Group>
        {subtasks.length > 0 && (
          <Stack gap={4}>
            <Group justify="space-between">
              <Text size="xs" c="dimmed">
                子任务 {doneCount}/{subtasks.length}
              </Text>
            </Group>
            <Progress
              size="sm"
              value={(doneCount / subtasks.length) * 100}
              aria-label={`子任务进度 ${doneCount}/${subtasks.length}`}
            />
          </Stack>
        )}
        {tags.length > 0 && (
          <Group gap={4}>
            {tags.map((tag) => (
              <Badge key={tag} size="sm" variant="light" color="gray">
                {tag}
              </Badge>
            ))}
          </Group>
        )}
        {dueDate && (
          <Text size="xs" c="dimmed">
            {task.completed_on ? `完成于 ${task.completed_on}` : `开始于 ${task.started_on}`}
          </Text>
        )}
      </Stack>
    </Card>
  );
}

export function KanbanPage() {
  const { name = '' } = useParams();
  const board = useKanbanBoard(name);
  const addCard = useAddKanbanCard(name);
  const moveCard = useMoveKanbanCard(name);
  const doneCard = useDoneKanbanCard(name);
  const [newTitle, setNewTitle] = useState('');
  const [newSection, setNewSection] = useState<string | null>(null);

  const etag = board.data?.etag ?? '';
  const sectionNames = (board.data?.board.sections ?? []).map((section) => section.name);
  const targetSection = newSection ?? (sectionNames.includes('Queue') ? 'Queue' : sectionNames[0] ?? 'Queue');
  const mutating = addCard.isPending || moveCard.isPending || doneCard.isPending;

  function handleMutationError(error: unknown, fallbackTitle: string) {
    if (error instanceof ApiError && error.status === 412) {
      notifications.show({
        color: 'yellow',
        title: '数据已被他人修改',
        message: '看板已被他人修改,已为你刷新。请确认后再试。',
      });
      void board.refetch();
      return;
    }
    // The backend addresses cards by title; a duplicate title is ambiguous
    // and cannot be resolved client-side — point the user at the data layer.
    if (
      error instanceof ApiError &&
      error.status === 422 &&
      error.code === 'kanban_card_ambiguous'
    ) {
      notifications.show({
        color: 'orange',
        title: '存在重名卡片',
        message:
          '看板中存在多张同名卡片,无法确定操作目标。请先在数据层(kanban.md)重命名重复卡片后再试。',
      });
      return;
    }
    notifications.show({
      color: 'red',
      title: fallbackTitle,
      message: error instanceof Error ? error.message : String(error),
    });
  }

  function handleAdd(event: FormEvent) {
    event.preventDefault();
    const title = newTitle.trim();
    if (!title) {
      return;
    }
    addCard.mutate(
      { body: { title, section: targetSection, context: '' }, etag },
      {
        onSuccess: (result) => {
          notifications.show({
            color: 'green',
            title: '已添加',
            message: `已加入 ${result.section || targetSection}。`,
          });
          setNewTitle('');
        },
        onError: (error) => handleMutationError(error, '添加失败'),
      },
    );
  }

  function handleMove(cardRef: string, section: string) {
    moveCard.mutate(
      { cardRef, targetSection: section, etag },
      {
        onSuccess: (result) => {
          notifications.show({
            color: 'green',
            title: '已移动',
            message: `已移动到 ${result.section || section}。`,
          });
        },
        onError: (error) => handleMutationError(error, '移动失败'),
      },
    );
  }

  function handleDone(cardRef: string) {
    doneCard.mutate(
      { cardRef, etag },
      {
        onSuccess: () => {
          notifications.show({ color: 'green', title: '已完成', message: '卡片已标记完成。' });
        },
        onError: (error) => handleMutationError(error, '操作失败'),
      },
    );
  }

  if (board.isPending) {
    return (
      <Center py="xl">
        <Loader />
      </Center>
    );
  }
  if (board.isError) {
    return (
      <Alert color="red" title="加载失败">
        {board.error.message}
      </Alert>
    );
  }

  const data = board.data.board;
  const cardActions: CardActions = {
    sectionNames,
    mutating,
    onMove: handleMove,
    onDone: handleDone,
  };
  return (
    <Stack gap="md">
      <Group justify="space-between">
        <Group gap="sm">
          <Title order={2}>{data.profile} · 看板</Title>
          <Badge variant="light" color="brand">
            共 {data.total} 项
          </Badge>
        </Group>
        <Button
          variant="light"
          size="compact-sm"
          leftSection={<IconRefresh size={14} />}
          loading={board.isFetching}
          onClick={() => void board.refetch()}
        >
          刷新
        </Button>
      </Group>
      <Card withBorder radius="md" padding="md">
        <form onSubmit={handleAdd}>
          <Group align="flex-end" wrap="nowrap">
            <TextInput
              label="快速添加"
              placeholder="任务标题…"
              value={newTitle}
              onChange={(event) => setNewTitle(event.currentTarget.value)}
              style={{ flex: 1 }}
            />
            <Select
              label="目标列"
              data={sectionNames}
              value={targetSection}
              onChange={setNewSection}
              w={180}
              allowDeselect={false}
            />
            <Button type="submit" loading={addCard.isPending} disabled={!newTitle.trim()}>
              添加
            </Button>
          </Group>
        </form>
      </Card>
      {(data.sections ?? []).length === 0 || data.total === 0 ? (
        <Text c="dimmed">看板为空,暂无任务。</Text>
      ) : (
        <ScrollArea>
          <Group align="flex-start" wrap="nowrap" gap="md" pb="sm">
            {(data.sections ?? []).map((section) => (
              <Paper
                key={section.name}
                withBorder
                radius="md"
                p="sm"
                w={280}
                miw={280}
                bg="var(--mantine-color-gray-0)"
              >
                <Group justify="space-between" mb="sm">
                  <Text fw={600} size="sm">
                    {section.name}
                  </Text>
                  <Badge size="sm" variant="light" color="gray">
                    {(section.tasks ?? []).length}
                  </Badge>
                </Group>
                <Stack gap="xs">
                  {(section.tasks ?? []).map((task, index) => (
                    <KanbanCardItem
                      key={task.id || `${section.name}-${index}`}
                      task={task}
                      section={section.name}
                      actions={cardActions}
                    />
                  ))}
                </Stack>
              </Paper>
            ))}
          </Group>
        </ScrollArea>
      )}
    </Stack>
  );
}
