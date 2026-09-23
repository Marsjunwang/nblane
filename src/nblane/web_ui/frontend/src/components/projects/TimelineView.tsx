// 时间轴视图 — same LaneGroup[] as the board view (view switch keeps order
// and selection). Month axis + gold dashed today line; per lane a sticky
// label column, the project time_range as a faded ground block, task bars
// (queue/doing dotted thin blocks, done faded, selected gold-framed),
// milestone diamonds (planned & overdue = hollow), habit rows as green
// dashed week strips with dots, and a row-tail 未排期 list for tasks with
// no anchor date.

import { Box, Group, ScrollArea, Stack, Text } from '@mantine/core';
import { useMemo } from 'react';

import type {
  ProjectsBoardHabit,
  ProjectsBoardMilestone,
  ProjectsBoardProject,
  ProjectsBoardResponse,
  ProjectsBoardTask,
} from '../../api/types';
import type { LaneGroup } from './lanes';
import { KIND_LABELS } from './lanes';
import { boardPalette } from './palette';
import type { BarRange, TimelineScale } from './timelineMath';
import {
  computeScale,
  dateToX,
  daysBetween,
  monthTicks,
  projectRange,
  scaleWidth,
  taskBarRange,
} from './timelineMath';
import { useTimelineDrag } from './useTimelineDrag';

const LABEL_WIDTH = 200;
const ROW_HEIGHT = 44;

export interface TimelineViewProps {
  profile: string;
  board: ProjectsBoardResponse;
  groups: LaneGroup[];
  habits: ProjectsBoardHabit[];
  unassigned: ProjectsBoardTask[];
  kanbanEtag: string;
  selectedTaskId: string;
  onSelectTask: (taskId: string) => void;
  onDragError: (error: unknown) => void;
}

function RowLabel({ title, meta }: { title: string; meta?: string }) {
  return (
    <Box
      w={LABEL_WIDTH}
      miw={LABEL_WIDTH}
      pl="sm"
      style={{
        position: 'sticky',
        left: 0,
        zIndex: 2,
        background: boardPalette.ground,
        borderRight: `1px solid ${boardPalette.border}`,
        overflow: 'hidden',
      }}
    >
      <Text size="sm" fw={600} lineClamp={1} style={{ color: boardPalette.titleText }}>
        {title}
      </Text>
      {meta && (
        <Text size="xs" lineClamp={1} style={{ color: boardPalette.dim }}>
          {meta}
        </Text>
      )}
    </Box>
  );
}

function MilestoneDiamond({
  milestone,
  scale,
  today,
  top,
}: {
  milestone: ProjectsBoardMilestone;
  scale: TimelineScale;
  today: string;
  top: number;
}) {
  if (!milestone.date) {
    return null;
  }
  // The data model has no completed-milestone workflow; planned + past date
  // renders as a hollow diamond (过期 planned = 空心).
  const hollow = milestone.status === 'planned' && milestone.date < today;
  return (
    <Box
      title={`${milestone.title || milestone.id} · ${milestone.date}`}
      data-testid={`milestone-diamond-${milestone.id}`}
      style={{
        position: 'absolute',
        left: dateToX(milestone.date, scale) - 5,
        top,
        width: 10,
        height: 10,
        transform: 'rotate(45deg)',
        background: hollow ? 'transparent' : boardPalette.gold,
        border: `1.5px solid ${boardPalette.gold}`,
      }}
    />
  );
}

function TaskBar({
  task,
  range,
  scale,
  selected,
  previewDelta,
  onSelect,
  onDragStart,
}: {
  task: ProjectsBoardTask;
  range: BarRange;
  scale: TimelineScale;
  selected: boolean;
  previewDelta: number | null;
  onSelect: (taskId: string) => void;
  onDragStart: (event: React.PointerEvent, task: ProjectsBoardTask, range: BarRange) => void;
}) {
  const width = Math.max((daysBetween(range.start, range.end) + 1) * scale.dayWidth, 6);
  const queued = task.column === 'queue' || task.column === 'someday';
  const done = task.done || task.column === 'done';
  return (
    <Box
      role="button"
      tabIndex={0}
      aria-label={`时间轴任务 ${task.title}`}
      title={`${task.title} · ${range.start} → ${range.end}`}
      data-testid={`timeline-bar-${task.id}`}
      onClick={() => onSelect(task.id)}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          onSelect(task.id);
        }
      }}
      onPointerDown={(event) => onDragStart(event, task, range)}
      style={{
        position: 'absolute',
        left: dateToX(range.start, scale),
        top: ROW_HEIGHT / 2 - 7,
        width,
        height: 14,
        borderRadius: 3,
        transform: previewDelta ? `translateX(${previewDelta * scale.dayWidth}px)` : undefined,
        cursor: 'grab',
        touchAction: 'pan-y',
        background: done
          ? 'rgba(176, 167, 140, 0.25)'
          : queued
            ? 'transparent'
            : 'rgba(220, 174, 85, 0.35)',
        border: selected
          ? `2px solid ${boardPalette.selectedBorder}`
          : done
            ? '1px solid rgba(176, 167, 140, 0.4)'
            : queued
              ? `1px dotted ${boardPalette.gold}`
              : `1px solid ${boardPalette.gold}`,
        opacity: done ? 0.55 : 1,
      }}
    />
  );
}

function ProjectRow({
  project,
  scale,
  today,
  selectedTaskId,
  previewTaskId,
  previewDelta,
  onSelectTask,
  onDragStart,
}: {
  project: ProjectsBoardProject;
  scale: TimelineScale;
  today: string;
  selectedTaskId: string;
  previewTaskId: string | null;
  previewDelta: number;
  onSelectTask: (taskId: string) => void;
  onDragStart: (event: React.PointerEvent, task: ProjectsBoardTask, range: BarRange) => void;
}) {
  const range = projectRange(project.time_range ?? '');
  const tasks = [...(project.queue ?? []), ...(project.doing ?? []), ...(project.someday ?? [])];
  const placed: { task: ProjectsBoardTask; range: BarRange }[] = [];
  const unscheduled: ProjectsBoardTask[] = [];
  for (const task of tasks) {
    const bar = taskBarRange(task, today);
    if (bar) {
      placed.push({ task, range: bar });
    } else {
      unscheduled.push(task);
    }
  }
  return (
    <Group wrap="nowrap" gap={0} data-testid={`timeline-row-${project.id}`}>
      <RowLabel
        title={project.title || project.id}
        meta={`${KIND_LABELS[project.kind ?? ''] ?? project.kind} · Done ${project.done_count}`}
      />
      <Box
        style={{
          position: 'relative',
          height: ROW_HEIGHT,
          flex: 1,
          borderBottom: `1px solid ${boardPalette.border}`,
        }}
      >
        {range && (
          <Box
            data-testid={`project-range-${project.id}`}
            style={{
              position: 'absolute',
              left: dateToX(range.start, scale),
              top: 4,
              width: (daysBetween(range.start, range.end) + 1) * scale.dayWidth,
              height: ROW_HEIGHT - 8,
              borderRadius: 6,
              background: 'rgba(220, 174, 85, 0.07)',
              border: '1px solid rgba(220, 174, 85, 0.15)',
            }}
          />
        )}
        {placed.map(({ task, range: bar }) => (
          <TaskBar
            key={task.id}
            task={task}
            range={bar}
            scale={scale}
            selected={selectedTaskId === task.id}
            previewDelta={previewTaskId === task.id ? previewDelta : null}
            onSelect={onSelectTask}
            onDragStart={onDragStart}
          />
        ))}
        {(project.milestones ?? []).map((milestone) => (
          <MilestoneDiamond
            key={milestone.id}
            milestone={milestone}
            scale={scale}
            today={today}
            top={ROW_HEIGHT - 14}
          />
        ))}
        {unscheduled.length > 0 && (
          <Text
            size="xs"
            lineClamp={1}
            data-testid={`unscheduled-${project.id}`}
            title={unscheduled.map((task) => task.title).join('、')}
            style={{
              position: 'absolute',
              right: 8,
              top: ROW_HEIGHT / 2 - 9,
              maxWidth: '40%',
              color: boardPalette.dim,
              // Never intercept bar drags/clicks underneath.
              pointerEvents: 'none',
            }}
          >
            未排期 ×{unscheduled.length}: {unscheduled.map((task) => task.title).join('、')}
          </Text>
        )}
      </Box>
    </Group>
  );
}

function HabitRow({
  habit,
  scale,
}: {
  habit: ProjectsBoardHabit;
  scale: TimelineScale;
}) {
  const week = habit.week ?? [];
  const span =
    week.length > 0 ? { start: week[0].date, end: week[week.length - 1].date } : null;
  return (
    <Group wrap="nowrap" gap={0} data-testid={`timeline-habit-${habit.id}`}>
      <RowLabel
        title={habit.title || habit.id}
        meta={`连续 ${habit.streak ?? 0} 天 · 累计 ${habit.total_checkins ?? 0} 次`}
      />
      <Box
        style={{
          position: 'relative',
          height: ROW_HEIGHT,
          flex: 1,
          borderBottom: `1px solid ${boardPalette.border}`,
        }}
      >
        {span && (
          <Box
            style={{
              position: 'absolute',
              left: dateToX(span.start, scale),
              top: ROW_HEIGHT / 2 - 6,
              width: (daysBetween(span.start, span.end) + 1) * scale.dayWidth,
              height: 12,
              borderRadius: 6,
              border: `1px dashed ${boardPalette.habitGreen}`,
              background: 'rgba(125, 191, 142, 0.08)',
            }}
          />
        )}
        {week
          .filter((day) => day.done)
          .map((day) => (
            <Box
              key={day.date}
              title={day.date}
              data-testid={`timeline-habit-dot-${habit.id}-${day.date}`}
              style={{
                position: 'absolute',
                left: dateToX(day.date, scale) + scale.dayWidth / 2 - 4,
                top: ROW_HEIGHT / 2 - 4,
                width: 8,
                height: 8,
                borderRadius: '50%',
                background: boardPalette.habitGreen,
              }}
            />
          ))}
      </Box>
    </Group>
  );
}

export function TimelineView({
  profile,
  board,
  groups,
  habits,
  unassigned,
  kanbanEtag,
  selectedTaskId,
  onSelectTask,
  onDragError,
}: TimelineViewProps) {
  const today = board.today || '';
  const scale = useMemo(() => computeScale(board), [board]);
  const width = scaleWidth(scale);
  const drag = useTimelineDrag({
    profile,
    scale,
    kanbanEtag,
    today,
    onError: onDragError,
  });

  const habitsByProject = new Map<string, ProjectsBoardHabit[]>();
  const unlinkedHabits: ProjectsBoardHabit[] = [];
  for (const habit of habits) {
    if (habit.project_id) {
      const rows = habitsByProject.get(habit.project_id) ?? [];
      rows.push(habit);
      habitsByProject.set(habit.project_id, rows);
    } else {
      unlinkedHabits.push(habit);
    }
  }

  const unassignedPlaced: { task: ProjectsBoardTask; range: BarRange }[] = [];
  const unassignedLoose: ProjectsBoardTask[] = [];
  for (const task of unassigned) {
    const bar = taskBarRange(task, today);
    if (bar) {
      unassignedPlaced.push({ task, range: bar });
    } else {
      unassignedLoose.push(task);
    }
  }

  return (
    <ScrollArea data-testid="timeline-view">
      <Box style={{ position: 'relative', minWidth: LABEL_WIDTH + width }}>
        {/* Month axis */}
        <Group wrap="nowrap" gap={0}>
          <Box w={LABEL_WIDTH} miw={LABEL_WIDTH} />
          <Box
            style={{
              position: 'relative',
              height: 28,
              flex: 1,
              borderBottom: `1px solid ${boardPalette.border}`,
            }}
            data-testid="timeline-month-axis"
          >
            {monthTicks(scale).map((tick) => (
              <Box key={tick.date}>
                <Box
                  style={{
                    position: 'absolute',
                    left: tick.x,
                    top: 0,
                    bottom: 0,
                    borderLeft: `1px solid ${boardPalette.border}`,
                  }}
                />
                <Text
                  size="xs"
                  style={{
                    position: 'absolute',
                    left: tick.x + 4,
                    top: 6,
                    color: boardPalette.goldText,
                  }}
                >
                  {tick.label}
                </Text>
              </Box>
            ))}
          </Box>
        </Group>

        {groups.map((group) => (
          <Stack key={group.id} gap={0} data-testid={`timeline-group-${group.id}`}>
            <Group wrap="nowrap" gap={0}>
              <Box
                w={LABEL_WIDTH}
                miw={LABEL_WIDTH}
                pl="sm"
                py={4}
                style={{
                  position: 'sticky',
                  left: 0,
                  zIndex: 2,
                  background: boardPalette.ground,
                }}
              >
                <Text fw={700} size="sm" style={{ color: boardPalette.goldText }}>
                  {group.title}
                </Text>
              </Box>
              <Box style={{ flex: 1, borderBottom: `1px solid ${boardPalette.border}` }} />
            </Group>
            {group.projects.map((project) => (
              <Box key={project.id}>
                <ProjectRow
                  project={project}
                  scale={scale}
                  today={today}
                  selectedTaskId={selectedTaskId}
                  previewTaskId={drag.preview?.taskId ?? null}
                  previewDelta={drag.preview?.deltaDays ?? 0}
                  onSelectTask={onSelectTask}
                  onDragStart={drag.startDrag}
                />
                {(habitsByProject.get(project.id) ?? []).map((habit) => (
                  <HabitRow key={habit.id} habit={habit} scale={scale} />
                ))}
              </Box>
            ))}
          </Stack>
        ))}

        {unlinkedHabits.length > 0 && (
          <Stack gap={0} data-testid="timeline-group-habits">
            <Group wrap="nowrap" gap={0}>
              <Box
                w={LABEL_WIDTH}
                miw={LABEL_WIDTH}
                pl="sm"
                py={4}
                style={{ position: 'sticky', left: 0, zIndex: 2, background: boardPalette.ground }}
              >
                <Text fw={700} size="sm" style={{ color: boardPalette.goldText }}>
                  习惯
                </Text>
              </Box>
              <Box style={{ flex: 1, borderBottom: `1px solid ${boardPalette.border}` }} />
            </Group>
            {unlinkedHabits.map((habit) => (
              <HabitRow key={habit.id} habit={habit} scale={scale} />
            ))}
          </Stack>
        )}

        {unassigned.length > 0 && (
          <Group wrap="nowrap" gap={0} data-testid="timeline-unassigned">
            <RowLabel title="未归属任务" meta={`${unassigned.length} 项`} />
            <Box
              style={{
                position: 'relative',
                height: ROW_HEIGHT,
                flex: 1,
                borderBottom: `1px dashed ${boardPalette.gold}`,
              }}
            >
              {unassignedPlaced.map(({ task, range }) => (
                <TaskBar
                  key={task.id}
                  task={task}
                  range={range}
                  scale={scale}
                  selected={selectedTaskId === task.id}
                  previewDelta={drag.preview?.taskId === task.id ? drag.preview.deltaDays : null}
                  onSelect={onSelectTask}
                  onDragStart={drag.startDrag}
                />
              ))}
              {unassignedLoose.length > 0 && (
                <Text
                  size="xs"
                  lineClamp={1}
                  title={unassignedLoose.map((task) => task.title).join('、')}
                  style={{
                    position: 'absolute',
                    right: 8,
                    top: ROW_HEIGHT / 2 - 9,
                    maxWidth: '40%',
                    color: boardPalette.dim,
                    pointerEvents: 'none',
                  }}
                >
                  未排期 ×{unassignedLoose.length}: {unassignedLoose.map((task) => task.title).join('、')}
                </Text>
              )}
            </Box>
          </Group>
        )}

        {/* Today line (gold dashed, board.today). */}
        {today && (
          <Box
            data-testid="timeline-today-line"
            style={{
              position: 'absolute',
              left: LABEL_WIDTH + dateToX(today, scale) + scale.dayWidth / 2,
              top: 28,
              bottom: 0,
              borderLeft: `1.5px dashed ${boardPalette.todayLine}`,
              pointerEvents: 'none',
            }}
          />
        )}
      </Box>
    </ScrollArea>
  );
}
