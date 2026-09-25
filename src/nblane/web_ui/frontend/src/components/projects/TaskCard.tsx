import { Badge, Box, Button, Card, Group, Text } from '@mantine/core';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

import type { ProjectsBoardTask } from '../../api/types';
import { boardPalette } from './palette';

export function splitTags(tags: string): string[] {
  return tags
    .split(/[,\s]+/)
    .map((tag) => tag.trim())
    .filter(Boolean);
}

/**
 * One task card on a project lane. Someday tasks render as a dashed,
 * half-transparent card with a gold badge (badge, not a column — locked
 * Phase 2 design decision) and never join the drag sort. The badge carries
 * the two exits into the daily loop: list into Queue, or mark Done.
 */
export function TaskCardBody({
  task,
  someday = false,
  selected = false,
  onPromoteQueue,
  onMarkDone,
  actionPending = false,
}: {
  task: ProjectsBoardTask;
  someday?: boolean;
  selected?: boolean;
  /** L1: move this someday card into the Queue section. */
  onPromoteQueue?: () => void;
  /** L1: mark this someday card Done without passing through Queue. */
  onMarkDone?: () => void;
  actionPending?: boolean;
}) {
  const tags = splitTags(task.tags ?? '');
  const todos = task.todos ?? [];
  const todoTotal = todos.length;
  const todoDone = todos.filter((todo) => todo.done).length;
  return (
    <Card
      radius="sm"
      padding="sm"
      data-testid={someday ? `someday-card-${task.id}` : `task-card-${task.id}`}
      style={{
        background: boardPalette.groundSoft,
        border: selected
          ? `2px solid ${boardPalette.selectedBorder}`
          : someday
            ? `1px dashed ${boardPalette.gold}`
            : `1px solid ${boardPalette.border}`,
        opacity: someday ? 0.75 : 1,
        color: boardPalette.text,
      }}
    >
      <Group justify="space-between" wrap="nowrap" align="flex-start" gap="xs">
        <Text
          fw={600}
          size="15px"
          style={{ color: boardPalette.titleText, wordBreak: 'break-word', minWidth: 0 }}
        >
          {task.title}
        </Text>
        {someday && (
          <Badge
            size="sm"
            variant="outline"
            style={{ borderColor: boardPalette.gold, color: boardPalette.goldText, flexShrink: 0 }}
          >
            someday
          </Badge>
        )}
      </Group>
      {tags.length > 0 && (
        <Group gap={4} mt={6}>
          {tags.map((tag) => (
            <Badge
              key={tag}
              size="sm"
              variant="outline"
              style={{ borderColor: boardPalette.border, color: boardPalette.dim }}
            >
              {tag}
            </Badge>
          ))}
        </Group>
      )}
      {(task.planned_start || task.started_on || task.completed_on) && (
        <Text size="xs" mt={6} style={{ color: boardPalette.dim }}>
          {task.planned_start
            ? `排期 ${task.planned_start}${task.planned_end ? ` → ${task.planned_end}` : ''}`
            : task.completed_on
              ? `完成于 ${task.completed_on}`
              : `开始于 ${task.started_on}`}
        </Text>
      )}
      {todoTotal > 0 && (
        <Text size="xs" mt={6} style={{ color: boardPalette.dim }} data-testid={`todo-progress-${task.id}`}>
          清单 {todoDone}/{todoTotal}
        </Text>
      )}
      {someday && (onPromoteQueue || onMarkDone) && (
        <Group gap={6} mt={8} wrap="wrap">
          {onPromoteQueue && (
            <Button
              size="compact-xs"
              variant="light"
              disabled={actionPending}
              data-testid={`someday-queue-${task.id}`}
              styles={{
                root: {
                  color: boardPalette.goldText,
                  background: 'rgba(220, 174, 85, 0.12)',
                },
              }}
              onClick={(event) => {
                event.stopPropagation();
                onPromoteQueue();
              }}
            >
              列入 Queue
            </Button>
          )}
          {onMarkDone && (
            <Button
              size="compact-xs"
              variant="subtle"
              disabled={actionPending}
              data-testid={`someday-done-${task.id}`}
              styles={{ root: { color: boardPalette.dim } }}
              onClick={(event) => {
                event.stopPropagation();
                onMarkDone();
              }}
            >
              标记 Done
            </Button>
          )}
        </Group>
      )}
    </Card>
  );
}

/** Sortable wrapper: the whole card is the drag handle; a click selects. */
export function SortableTaskCard({
  task,
  disabled,
  selected,
  onSelect,
  suppressClickRef,
}: {
  task: ProjectsBoardTask;
  disabled: boolean;
  selected: boolean;
  onSelect: (taskId: string) => void;
  /** Shared per-lane flag: a drag end suppresses the trailing click. */
  suppressClickRef: { current: boolean };
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: task.id,
    disabled,
  });
  return (
    <Box
      ref={setNodeRef}
      {...attributes}
      {...listeners}
      aria-label={`拖拽卡片 ${task.title}`}
      onClick={() => {
        if (suppressClickRef.current) {
          suppressClickRef.current = false;
          return;
        }
        onSelect(task.id);
      }}
      style={{
        transform: CSS.Transform.toString(transform),
        transition,
        opacity: isDragging ? 0.4 : 1,
        cursor: disabled ? undefined : isDragging ? 'grabbing' : 'grab',
        touchAction: 'manipulation',
      }}
    >
      <TaskCardBody task={task} selected={selected} />
    </Box>
  );
}
