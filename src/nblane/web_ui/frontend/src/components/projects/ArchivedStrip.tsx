// 归档带 — L3 索引层:一行灰条就地展开为月白 40% 的只读泳道。
// No drag, no mutations except 恢复 (case save with status='active' — the
// archive endpoint is one-way; there is no dedicated unarchive route).
// Cards stay clickable: selection opens the shared 铭文卡 detail drawer.

import { ActionIcon, Badge, Box, Group, Stack, Text } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconArchive, IconChevronDown, IconChevronRight, IconEdit, IconRestore } from '@tabler/icons-react';
import { useState } from 'react';

import { useProjectBoard, useSaveProjectCase } from '../../api/hooks';
import type { ProjectsBoardProject } from '../../api/types';
import { handleLaneMutationError } from './ProjectLane';
import { TaskCardBody } from './TaskCard';
import { KIND_LABELS } from './lanes';
import { boardPalette } from './palette';

function ReadOnlyColumn({
  title,
  tasks,
  laneId,
  column,
  selectedTaskId,
  onSelectTask,
}: {
  title: string;
  tasks: ProjectsBoardProject['queue'];
  laneId: string;
  column: string;
  selectedTaskId: string;
  onSelectTask: (taskId: string) => void;
}) {
  return (
    <Box
      p="sm"
      w={280}
      miw={280}
      data-testid={`lane-column-${laneId}-${column}`}
      style={{
        background: 'rgba(16, 29, 48, 0.6)',
        border: `1px solid ${boardPalette.border}`,
        borderRadius: 8,
      }}
    >
      <Group justify="space-between" mb="sm">
        <Text fw={600} size="sm" style={{ color: boardPalette.dim }}>
          {title}
        </Text>
        <Badge
          size="sm"
          variant="outline"
          style={{ borderColor: boardPalette.border, color: boardPalette.dim }}
        >
          {(tasks ?? []).length}
        </Badge>
      </Group>
      <Stack gap="xs">
        {(tasks ?? []).map((task) => (
          <Box key={task.id} onClick={() => onSelectTask(task.id)} style={{ cursor: 'pointer' }}>
            <TaskCardBody task={task} selected={selectedTaskId === task.id} />
          </Box>
        ))}
        {(tasks ?? []).length === 0 && (
          <Text size="xs" style={{ color: boardPalette.dim }}>
            (空)
          </Text>
        )}
      </Stack>
    </Box>
  );
}

function ArchivedLane({
  profile,
  project,
  selectedTaskId,
  onSelectTask,
  onEditProject,
  onRefresh,
}: {
  profile: string;
  project: ProjectsBoardProject;
  selectedTaskId: string;
  onSelectTask: (taskId: string) => void;
  onEditProject: (projectId: string) => void;
  onRefresh: () => void;
}) {
  const board = useProjectBoard(profile);
  const restore = useSaveProjectCase(profile);
  const etag = board.data?.etag ?? '';

  const runRestore = () => {
    restore.mutate(
      { caseId: project.id, body: { status: 'active' }, etag },
      {
        onSuccess: () => {
          notifications.show({
            color: 'green',
            title: '已恢复',
            message: `「${project.title || project.id}」已恢复为进行中。`,
          });
        },
        onError: (error) => handleLaneMutationError(error, '恢复失败', onRefresh),
      },
    );
  };

  return (
    <Stack
      gap="sm"
      p="sm"
      data-testid={`archived-lane-${project.id}`}
      style={{
        background: boardPalette.ground,
        border: `1px solid ${boardPalette.border}`,
        borderRadius: 12,
      }}
    >
      <Group justify="space-between" wrap="nowrap" align="flex-start">
        <Group gap="xs" wrap="wrap" style={{ minWidth: 0 }}>
          <Text fw={600} style={{ color: boardPalette.titleText }}>
            {project.title || project.id}
          </Text>
          <Badge
            size="sm"
            variant="outline"
            style={{ borderColor: boardPalette.border, color: boardPalette.dim }}
          >
            {KIND_LABELS[project.kind ?? ''] ?? project.kind} · 已归档
          </Badge>
          <Text size="xs" style={{ color: boardPalette.dim }}>
            Done · {project.done_count}
            {(project.archived_done_count ?? 0) > 0 ? `（含归档 ${project.archived_done_count}）` : ''}
          </Text>
        </Group>
        <Group
          gap="xs"
          wrap="nowrap"
          style={{ flexShrink: 0, opacity: 1 }}
          data-testid={`archived-actions-${project.id}`}
        >
          <ActionIcon
            variant="subtle"
            size="sm"
            aria-label={`恢复项目 ${project.title || project.id}`}
            loading={restore.isPending}
            onClick={runRestore}
            style={{ color: boardPalette.goldText }}
          >
            <IconRestore size={14} />
          </ActionIcon>
          <ActionIcon
            variant="subtle"
            size="sm"
            aria-label={`查看项目 ${project.title || project.id}`}
            onClick={() => onEditProject(project.id)}
            style={{ color: boardPalette.dim }}
          >
            <IconEdit size={14} />
          </ActionIcon>
        </Group>
      </Group>
      {/* 视觉降级:月白 40% on the card columns; the header/actions stay
          readable so 恢复 and the drawer remain L1-reachable. */}
      <Group
        align="flex-start"
        wrap="nowrap"
        gap="sm"
        style={{ overflowX: 'auto', opacity: 0.4 }}
      >
        <ReadOnlyColumn
          title="Queue"
          tasks={project.queue}
          laneId={`archived-${project.id}`}
          column="queue"
          selectedTaskId={selectedTaskId}
          onSelectTask={onSelectTask}
        />
        <ReadOnlyColumn
          title="Doing"
          tasks={project.doing}
          laneId={`archived-${project.id}`}
          column="doing"
          selectedTaskId={selectedTaskId}
          onSelectTask={onSelectTask}
        />
      </Group>
    </Stack>
  );
}

/**
 * 已归档 strip: collapsed = one quiet count row; expanded = dimmed read-only
 * lanes with 恢复 (case save) and drawer view actions.
 */
export function ArchivedStrip({
  profile,
  archived,
  selectedTaskId,
  onSelectTask,
  onEditProject,
  onRefresh,
}: {
  profile: string;
  archived: ProjectsBoardProject[];
  selectedTaskId: string;
  onSelectTask: (taskId: string) => void;
  onEditProject: (projectId: string) => void;
  onRefresh: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  if (archived.length === 0) {
    return null;
  }
  return (
    <Stack
      gap="sm"
      data-testid="archived-projects-footer"
      style={{
        border: `1px dashed ${boardPalette.border}`,
        borderRadius: 12,
      }}
    >
      <Group
        gap="xs"
        p="sm"
        role="button"
        tabIndex={0}
        aria-expanded={expanded}
        data-testid="archived-strip-toggle"
        onClick={() => setExpanded((value) => !value)}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            setExpanded((value) => !value);
          }
        }}
        style={{ cursor: 'pointer', color: boardPalette.dim }}
      >
        <IconArchive size={14} />
        <Text size="sm" style={{ color: boardPalette.dim }}>
          已归档项目 · {archived.length} {expanded ? '▾' : '▸'}
        </Text>
        {!expanded && (
          <Text size="xs" style={{ color: boardPalette.dim }} lineClamp={1}>
            {archived.map((project) => project.title || project.id).join(' / ')}
          </Text>
        )}
        {expanded ? <IconChevronDown size={14} /> : <IconChevronRight size={14} />}
      </Group>
      {expanded && (
        <Stack gap="sm" px="sm" pb="sm">
          {archived.map((project) => (
            <ArchivedLane
              key={project.id}
              profile={profile}
              project={project}
              selectedTaskId={selectedTaskId}
              onSelectTask={onSelectTask}
              onEditProject={onEditProject}
              onRefresh={onRefresh}
            />
          ))}
        </Stack>
      )}
    </Stack>
  );
}
