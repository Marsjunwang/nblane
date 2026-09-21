import {
  closestCenter,
  DndContext,
  DragOverlay,
  KeyboardSensor,
  MouseSensor,
  pointerWithin,
  rectIntersection,
  TouchSensor,
  useDroppable,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import type {
  CollisionDetection,
  DragEndEvent,
  DragOverEvent,
  DragStartEvent,
  UniqueIdentifier,
} from '@dnd-kit/core';
import {
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
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
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { FormEvent, ReactNode } from 'react';
import { useParams } from 'react-router-dom';

import { ApiError } from '../api/client';
import {
  useAddKanbanCard,
  useDoneKanbanCard,
  useKanbanBoard,
  useMoveKanbanCard,
} from '../api/hooks';
import type { KanbanBoard, KanbanTask } from '../api/types';

function splitTags(tags: string): string[] {
  return tags
    .split(/[,\s]+/)
    .map((tag) => tag.trim())
    .filter(Boolean);
}

// --- Drag & drop model ------------------------------------------------------
// The backend move endpoint accepts a target section plus an optional
// to_index (0-based post-removal insertion index; omitted = column tail),
// so both cross-column and in-column drops persist. The drop index is read
// off the server-board columns (not the live preview): over a card → that
// card's index (insert before it, matching the sortable preview); over a
// column body → tail. Columns render in the server's kanban.md order with
// no client-side filtering/sorting, so preview and persisted order agree.

interface BoardItem {
  /** Stable per-board dnd id: task id, or a section/title fallback. */
  dndId: string;
  task: KanbanTask;
}

interface BoardColumn {
  name: string;
  items: BoardItem[];
}

function columnDroppableId(name: string): string {
  return `column::${name}`;
}

function buildBoardColumns(sections: KanbanBoard['sections'] | undefined): BoardColumn[] {
  return (sections ?? []).map((section) => ({
    name: section.name,
    items: (section.tasks ?? []).map((task, index) => ({
      task,
      dndId: task.id?.trim() ? task.id : `${section.name}#${index}#${task.title}`,
    })),
  }));
}

/** Resolve a droppable id (card dndId or column droppable id) to its column. */
function findColumnName(columns: BoardColumn[], id: UniqueIdentifier): string | null {
  const key = String(id);
  for (const column of columns) {
    if (columnDroppableId(column.name) === key) {
      return column.name;
    }
    if (column.items.some((item) => item.dndId === key)) {
      return column.name;
    }
  }
  return null;
}

function findItem(columns: BoardColumn[], dndId: string): BoardItem | null {
  for (const column of columns) {
    const hit = column.items.find((item) => item.dndId === dndId);
    if (hit) {
      return hit;
    }
  }
  return null;
}

/** Return columns with the active card inserted into the over column. */
function moveBetweenColumns(
  columns: BoardColumn[],
  activeId: UniqueIdentifier,
  overId: UniqueIdentifier,
): BoardColumn[] {
  const fromName = findColumnName(columns, activeId);
  const toName = findColumnName(columns, overId);
  if (!fromName || !toName || fromName === toName) {
    return columns;
  }
  const activeItem = findItem(columns, String(activeId));
  if (!activeItem) {
    return columns;
  }
  return columns.map((column) => {
    if (column.name === fromName) {
      return { ...column, items: column.items.filter((item) => item.dndId !== activeId) };
    }
    if (column.name === toName) {
      const items = [...column.items];
      const overIndex = items.findIndex((item) => item.dndId === overId);
      items.splice(overIndex >= 0 ? overIndex : items.length, 0, activeItem);
      return { ...column, items };
    }
    return column;
  });
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
  shadow = 'xs',
}: {
  task: KanbanTask;
  section: string;
  actions: CardActions;
  shadow?: string;
}) {
  const tags = splitTags(task.tags ?? '');
  const subtasks = task.subtasks ?? [];
  const doneCount = subtasks.filter((subtask) => subtask.done).length;
  const dueDate = task.completed_on ?? task.started_on;
  const moveTargets = actions.sectionNames.filter((name) => name !== section);

  return (
    <Card withBorder radius="sm" padding="sm" shadow={shadow}>
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

/** Sortable wrapper: the whole card is the drag handle (keyboard included). */
function SortableKanbanCard({
  item,
  section,
  actions,
  dragDisabled,
}: {
  item: BoardItem;
  section: string;
  actions: CardActions;
  dragDisabled: boolean;
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: item.dndId,
    disabled: dragDisabled,
  });
  return (
    <div
      ref={setNodeRef}
      {...attributes}
      {...listeners}
      aria-label={`拖拽卡片 ${item.task.title}`}
      style={{
        transform: CSS.Transform.toString(transform),
        transition,
        opacity: isDragging ? 0.4 : undefined,
        cursor: dragDisabled ? undefined : isDragging ? 'grabbing' : 'grab',
        // manipulation keeps tap + page scroll working; the TouchSensor's
        // press-and-hold delay decides when a touch becomes a drag.
        touchAction: 'manipulation',
      }}
    >
      <KanbanCardItem task={item.task} section={section} actions={actions} />
    </div>
  );
}

/** One board column: droppable container wrapping a sortable card list. */
function KanbanColumn({
  column,
  highlighted,
  children,
}: {
  column: BoardColumn;
  highlighted: boolean;
  children: ReactNode;
}) {
  const { setNodeRef } = useDroppable({ id: columnDroppableId(column.name) });
  return (
    <Paper
      ref={setNodeRef}
      withBorder
      radius="md"
      p="sm"
      w={280}
      miw={280}
      bg={highlighted ? 'var(--mantine-color-brand-0)' : 'var(--mantine-color-gray-0)'}
      style={
        highlighted
          ? {
              borderColor: 'var(--mantine-color-brand-4)',
              borderStyle: 'dashed',
              transition: 'background-color 120ms ease, border-color 120ms ease',
            }
          : undefined
      }
      data-testid={`kanban-column-${column.name}`}
      data-drop-target={highlighted ? 'true' : undefined}
    >
      <Group justify="space-between" mb="sm">
        <Text fw={600} size="sm">
          {column.name}
        </Text>
        <Badge size="sm" variant="light" color="gray">
          {column.items.length}
        </Badge>
      </Group>
      <SortableContext
        items={column.items.map((item) => item.dndId)}
        strategy={verticalListSortingStrategy}
      >
        {/* mih keeps empty columns reachable as drop targets. */}
        <Stack gap="xs" mih={48}>
          {children}
        </Stack>
      </SortableContext>
    </Paper>
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

  // --- Drag & drop state ------------------------------------------------------
  // `boardColumns` mirrors the server board; `previewColumns` holds the live
  // cross-column preview while dragging and the post-drop order (both
  // cross-column and in-column) until the invalidation refetch lands, so the
  // DOM never flashes the stale order in between. An error rolls back
  // immediately.
  const boardColumns = useMemo(() => buildBoardColumns(board.data?.board.sections), [board.data]);
  const [activeDndId, setActiveDndId] = useState<string | null>(null);
  const [previewColumns, setPreviewColumns] = useState<BoardColumn[] | null>(null);
  const [overColumnName, setOverColumnName] = useState<string | null>(null);
  const lastOverIdRef = useRef<UniqueIdentifier | null>(null);

  const activeColumns = previewColumns ?? boardColumns;
  const activeSourceSection = activeDndId ? findColumnName(boardColumns, activeDndId) : null;
  const activeItem = activeDndId ? findItem(activeColumns, activeDndId) : null;
  // A stale etag 412s; block new drags while any mutation/refetch is in flight.
  const dragDisabled = mutating || board.isFetching;

  const boardData = board.data;
  useEffect(() => {
    setPreviewColumns(null);
    setOverColumnName(null);
  }, [boardData]);

  const sensors = useSensors(
    useSensor(MouseSensor, { activationConstraint: { distance: 4 } }),
    // Press-and-hold so touch scrolling the page/columns is not hijacked.
    useSensor(TouchSensor, { activationConstraint: { delay: 250, tolerance: 8 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  // Multi-container collision detection (dnd-kit idiom): pointer position
  // first, rect intersection as fallback (keyboard); when over a column, pick
  // the closest card inside it so the sortable preview lands precisely.
  const collisionDetection: CollisionDetection = useCallback(
    (args) => {
      const columnIds = new Set(activeColumns.map((column) => columnDroppableId(column.name)));
      const pointerIntersections = pointerWithin(args);
      const intersections =
        pointerIntersections.length > 0 ? pointerIntersections : rectIntersection(args);
      let overId: UniqueIdentifier | null =
        intersections.length > 0 ? intersections[0].id : null;
      if (overId != null) {
        const overKey = String(overId);
        if (columnIds.has(overKey)) {
          const column = activeColumns.find((entry) => columnDroppableId(entry.name) === overKey);
          // The active card follows the pointer, so it would always win the
          // closest-center pick; exclude it to resolve the real drop slot.
          const activeKey = String(args.active.id);
          const itemIds = (column?.items ?? [])
            .map((item) => item.dndId)
            .filter((dndId) => dndId !== activeKey);
          if (itemIds.length > 0) {
            const closest = closestCenter({
              ...args,
              droppableContainers: args.droppableContainers.filter((container) =>
                itemIds.includes(String(container.id)),
              ),
            });
            if (closest.length > 0) {
              overId = closest[0].id;
            }
          }
        }
        lastOverIdRef.current = overId;
        return [{ id: overId }];
      }
      // Between droppables (e.g. gaps): keep the last hit so the preview and
      // the drop target stay stable instead of flickering to null.
      return lastOverIdRef.current != null ? [{ id: lastOverIdRef.current }] : [];
    },
    [activeColumns],
  );

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

  function handleMove(
    cardRef: string,
    section: string,
    options?: { toIndex?: number; onError?: () => void },
  ) {
    moveCard.mutate(
      { cardRef, targetSection: section, toIndex: options?.toIndex, etag },
      {
        onSuccess: (result) => {
          notifications.show({
            color: 'green',
            title: '已移动',
            message: `已移动到 ${result.section || section}。`,
          });
        },
        onError: (error) => {
          options?.onError?.();
          handleMutationError(error, '移动失败');
        },
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

  function handleDragStart({ active }: DragStartEvent) {
    setActiveDndId(String(active.id));
    setPreviewColumns(boardColumns);
    setOverColumnName(findColumnName(boardColumns, active.id));
    lastOverIdRef.current = null;
  }

  function handleDragOver({ active, over }: DragOverEvent) {
    if (!over) {
      setOverColumnName(null);
      return;
    }
    const toName = findColumnName(activeColumns, over.id);
    setOverColumnName(toName);
    const fromName = findColumnName(activeColumns, active.id);
    if (!fromName || !toName || fromName === toName) {
      return;
    }
    setPreviewColumns((current) => moveBetweenColumns(current ?? boardColumns, active.id, over.id));
  }

  function handleDragEnd({ active, over }: DragEndEvent) {
    const activeId = String(active.id);
    const fromName = findColumnName(boardColumns, activeId);
    const toName = over ? findColumnName(activeColumns, over.id) : null;
    setActiveDndId(null);
    setOverColumnName(null);
    lastOverIdRef.current = null;
    if (!over || !fromName || !toName) {
      setPreviewColumns(null);
      return;
    }
    const item = findItem(boardColumns, activeId);
    const fromColumn = boardColumns.find((column) => column.name === fromName);
    const toColumn = boardColumns.find((column) => column.name === toName);
    if (!item || !fromColumn || !toColumn) {
      setPreviewColumns(null);
      return;
    }
    // Resolve the insertion index against the server board, not the live
    // preview: over a card inserts before it (matching both the sortable
    // preview and moveBetweenColumns), over the column body lands at the
    // tail. The backend reads to_index as the post-removal index.
    const overKey = String(over.id);
    let toIndex: number;
    if (overKey === columnDroppableId(toName)) {
      toIndex = toColumn.items.length;
    } else if (overKey === activeId) {
      // Pointer still on the dragged card itself: in-column that means "back
      // where it started" (no-op); cross-column fall back to the tail.
      if (toName === fromName) {
        setPreviewColumns(null);
        return;
      }
      toIndex = toColumn.items.length;
    } else {
      const overIndex = toColumn.items.findIndex((entry) => entry.dndId === overKey);
      if (overIndex < 0) {
        setPreviewColumns(null);
        return;
      }
      toIndex = overIndex;
    }
    const fromIndex = fromColumn.items.findIndex((entry) => entry.dndId === activeId);
    if (toName === fromName) {
      // In-column drop: after the pop the card lands at
      // min(toIndex, length - 1); dropping back onto its own slot is a
      // no-op and fires no mutation.
      const finalIndex = Math.min(toIndex, toColumn.items.length - 1);
      if (finalIndex === fromIndex) {
        setPreviewColumns(null);
        return;
      }
      // In-column reorder: the sortable transforms disappear the moment the
      // drag ends, but the refetch lands ~100ms later — rendering the server
      // order in between flashes "old order, then new order". Seed the
      // preview with the new order (the same mechanism the cross-column path
      // keeps alive through handleDragOver) so the DOM holds it until
      // boardData changes and the effect above clears the preview. The
      // insertion index mirrors the backend's post-removal semantics.
      const reordered = fromColumn.items.filter((entry) => entry.dndId !== activeId);
      reordered.splice(Math.min(toIndex, reordered.length), 0, item);
      setPreviewColumns(
        boardColumns.map((column) =>
          column.name === fromName ? { ...column, items: reordered } : column,
        ),
      );
    }
    handleMove(item.task.title, toName, {
      toIndex,
      onError: () => setPreviewColumns(null),
    });
  }

  function handleDragCancel() {
    setActiveDndId(null);
    setPreviewColumns(null);
    setOverColumnName(null);
    lastOverIdRef.current = null;
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
    onMove: (cardRef, section) => handleMove(cardRef, section),
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
          <Group align="flex-end">
            <TextInput
              label="快速添加"
              placeholder="任务标题…"
              value={newTitle}
              onChange={(event) => setNewTitle(event.currentTarget.value)}
              style={{ flex: '1 1 160px' }}
            />
            <Select
              label="目标列"
              data={sectionNames}
              value={targetSection}
              onChange={setNewSection}
              style={{ flex: '1 1 140px', maxWidth: 180 }}
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
        <DndContext
          sensors={sensors}
          collisionDetection={collisionDetection}
          onDragStart={handleDragStart}
          onDragOver={handleDragOver}
          onDragEnd={handleDragEnd}
          onDragCancel={handleDragCancel}
        >
          <ScrollArea>
            <Group align="flex-start" wrap="nowrap" gap="md" pb="sm">
              {activeColumns.map((column) => (
                <KanbanColumn
                  key={column.name}
                  column={column}
                  highlighted={
                    overColumnName === column.name && activeSourceSection !== column.name
                  }
                >
                  {column.items.map((item) => (
                    <SortableKanbanCard
                      key={item.dndId}
                      item={item}
                      section={column.name}
                      actions={cardActions}
                      dragDisabled={dragDisabled}
                    />
                  ))}
                </KanbanColumn>
              ))}
            </Group>
          </ScrollArea>
          <DragOverlay>
            {activeItem ? (
              <div style={{ width: 252, cursor: 'grabbing' }}>
                <KanbanCardItem
                  task={activeItem.task}
                  section={activeSourceSection ?? ''}
                  actions={cardActions}
                  shadow="lg"
                />
              </div>
            ) : null}
          </DragOverlay>
        </DndContext>
      )}
    </Stack>
  );
}
