import { Badge, Group, Paper, Stack, Text } from '@mantine/core';
import { useDroppable } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';
import type { ReactNode } from 'react';

import type { ProjectsBoardTask } from '../../api/types';
import { boardPalette } from './palette';

/** Droppable id for one lane column (unique per lane + column). */
export function laneColumnDroppableId(laneId: string, column: string): string {
  return `lane::${laneId}::${column}`;
}

/** One lane column (Queue / Doing): droppable container + sortable list. */
export function LaneColumn({
  laneId,
  column,
  title,
  tasks,
  highlighted,
  quickAdd,
  children,
}: {
  laneId: string;
  /** Board column key: 'queue' | 'doing'. */
  column: string;
  title: string;
  tasks: ProjectsBoardTask[];
  highlighted: boolean;
  /** Optional persistent inline-create row pinned above the cards. */
  quickAdd?: ReactNode;
  children: ReactNode;
}) {
  const { setNodeRef } = useDroppable({ id: laneColumnDroppableId(laneId, column) });
  return (
    <Paper
      ref={setNodeRef}
      radius="md"
      p="sm"
      className="projects-lane-column"
      data-testid={`lane-column-${laneId}-${column}`}
      data-drop-target={highlighted ? 'true' : undefined}
      style={{
        background: highlighted ? 'rgba(220, 174, 85, 0.12)' : 'rgba(16, 29, 48, 0.6)',
        border: highlighted
          ? `1px dashed ${boardPalette.gold}`
          : `1px solid ${boardPalette.border}`,
        transition: 'background-color 120ms ease, border-color 120ms ease',
      }}
    >
      <Group justify="space-between" mb="sm">
        <Text fw={600} size="sm" style={{ color: boardPalette.goldText }}>
          {title}
        </Text>
        <Badge
          size="sm"
          variant="outline"
          style={{ borderColor: boardPalette.border, color: boardPalette.dim }}
        >
          {tasks.length}
        </Badge>
      </Group>
      <SortableContext items={tasks.map((task) => task.id)} strategy={verticalListSortingStrategy}>
        {quickAdd && <div style={{ marginBottom: 8 }}>{quickAdd}</div>}
        {/* Empty columns stay reachable as drop targets. Wide screens cap long
            lists in CSS; phones use the page's natural vertical scroll. */}
        <Stack
          gap="xs"
          mih={48}
          className="projects-lane-list"
          data-testid={`lane-scroll-${laneId}-${column}`}
        >
          {children}
        </Stack>
      </SortableContext>
    </Paper>
  );
}
