// 时间轴视图 — same LaneGroup[] as the board view (view switch keeps order
// and selection). Month axis + gold dashed today line; per lane a sticky
// label column, the project time_range as a faded ground block, task bars
// (queue/doing dotted thin blocks, done faded, selected gold-framed),
// milestone diamonds (planned & overdue = hollow).
//
// 裁决5 contract: the history layer (Done/archived kanban tasks from the
// kanban.md sections) renders as 月白 thin 刻痕 bars — half height, no fill,
// brighten on select, never draggable; the「历史」toggle defaults ON. The
// default window is the trailing 6 months (「最近半年/全部」 zoom toggle);
// older history is reachable via the horizontal scroll / 全部 zoom, and
// computeScale clamps dirty dates with a console warning.
//
// 日课 dedupe: habit rows render once, in the top 日课 section — habit-plan
// projects are filtered out of the lane groups, so there is nothing inline
// to duplicate.

import { Box, Group, ScrollArea, SegmentedControl, Stack, Switch, Text } from '@mantine/core';
import { useEffect, useMemo, useRef, useState } from 'react';

import type {
  KanbanSection,
  ProjectsBoardMilestone,
  ProjectsBoardProject,
  ProjectsBoardResponse,
  ProjectsBoardTask,
} from '../../api/types';
import type { HabitRow, LaneGroup } from './lanes';
import { KIND_LABELS } from './lanes';
import { boardPalette } from './palette';
import type { BarRange, TimelineHistoryTask, TimelineScale, TimelineZoom } from './timelineMath';
import {
  clampRangeToScale,
  computeScale,
  dateToX,
  daysBetween,
  historyBarRange,
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
  habitRows: HabitRow[];
  unassigned: ProjectsBoardTask[];
  kanbanEtag: string;
  /** kanban.md sections — the Done section feeds the history layer. */
  kanbanSections: KanbanSection[] | undefined;
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

/**
 * 刻痕 history bar (Done/archived task): 月白, half height, no fill,
 * read-only (no drag); selection brightens the stroke.
 */
function HistoryBar({
  task,
  range,
  scale,
  selected,
  onSelect,
}: {
  task: TimelineHistoryTask;
  range: BarRange;
  scale: TimelineScale;
  selected: boolean;
  onSelect: (taskId: string) => void;
}) {
  const width = Math.max((daysBetween(range.start, range.end) + 1) * scale.dayWidth, 6);
  return (
    <Box
      role="button"
      tabIndex={0}
      aria-label={`历史任务 ${task.title}`}
      title={`${task.title} · ${range.start} → ${range.end}(已完成)`}
      data-testid={`timeline-history-bar-${task.id}`}
      onClick={() => onSelect(task.id)}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          onSelect(task.id);
        }
      }}
      style={{
        position: 'absolute',
        left: dateToX(range.start, scale),
        top: ROW_HEIGHT / 2 + 4,
        width,
        height: 7,
        borderRadius: 2,
        cursor: 'pointer',
        background: 'transparent',
        border: selected
          ? `1.5px solid ${boardPalette.titleText}`
          : '1px solid rgba(242, 237, 224, 0.45)',
        opacity: selected ? 1 : 0.6,
      }}
    />
  );
}

function ProjectRow({
  project,
  scale,
  today,
  history,
  showHistory,
  selectedTaskId,
  previewTaskId,
  previewDelta,
  onSelectTask,
  onDragStart,
}: {
  project: ProjectsBoardProject;
  scale: TimelineScale;
  today: string;
  history: { task: TimelineHistoryTask; range: BarRange }[];
  showHistory: boolean;
  selectedTaskId: string;
  previewTaskId: string | null;
  previewDelta: number;
  onSelectTask: (taskId: string) => void;
  onDragStart: (event: React.PointerEvent, task: ProjectsBoardTask, range: BarRange) => void;
}) {
  const range = projectRange(project.time_range ?? '');
  const clippedRange = range ? clampRangeToScale(range, scale) : null;
  const tasks = [...(project.queue ?? []), ...(project.doing ?? []), ...(project.someday ?? [])];
  const placed: { task: ProjectsBoardTask; range: BarRange }[] = [];
  const unscheduled: ProjectsBoardTask[] = [];
  for (const task of tasks) {
    const bar = taskBarRange(task, today);
    const clipped = bar ? clampRangeToScale(bar, scale) : null;
    if (clipped) {
      placed.push({ task, range: clipped });
    } else {
      // No anchor date (未排期) or dated fully outside the current window.
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
        {clippedRange && (
          <Box
            data-testid={`project-range-${project.id}`}
            style={{
              position: 'absolute',
              left: dateToX(clippedRange.start, scale),
              top: 4,
              width: (daysBetween(clippedRange.start, clippedRange.end) + 1) * scale.dayWidth,
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
        {showHistory &&
          history.map(({ task, range: bar }) => (
            <HistoryBar
              key={task.id}
              task={task}
              range={bar}
              scale={scale}
              selected={selectedTaskId === task.id}
              onSelect={onSelectTask}
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
  habit: HabitRow['habit'];
  scale: TimelineScale;
}) {
  const week = habit.week ?? [];
  const span =
    week.length > 0 ? { start: week[0].date, end: week[week.length - 1].date } : null;
  const clipped = span ? clampRangeToScale(span, scale) : null;
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
        {clipped && (
          <Box
            style={{
              position: 'absolute',
              left: dateToX(clipped.start, scale),
              top: ROW_HEIGHT / 2 - 6,
              width: (daysBetween(clipped.start, clipped.end) + 1) * scale.dayWidth,
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

/** Done/archived kanban tasks as timeline history items. */
export function collectHistoryTasks(kanbanSections: KanbanSection[] | undefined): TimelineHistoryTask[] {
  const items: TimelineHistoryTask[] = [];
  for (const section of kanbanSections ?? []) {
    for (const task of section.tasks ?? []) {
      if (section.name === 'Done' || task.done) {
        items.push(task);
      }
    }
  }
  return items;
}

export function TimelineView({
  profile,
  board,
  groups,
  habitRows,
  unassigned,
  kanbanEtag,
  kanbanSections,
  selectedTaskId,
  onSelectTask,
  onDragError,
}: TimelineViewProps) {
  const today = board.today || '';
  const [showHistory, setShowHistory] = useState(true);
  const [zoom, setZoom] = useState<TimelineZoom>('recent');

  const historyTasks = useMemo(() => collectHistoryTasks(kanbanSections), [kanbanSections]);
  const scale = useMemo(
    () => computeScale(board, { history: showHistory ? historyTasks : [], zoom }),
    [board, historyTasks, showHistory, zoom],
  );
  const width = scaleWidth(scale);
  const drag = useTimelineDrag({
    profile,
    scale,
    kanbanEtag,
    today,
    onError: onDragError,
  });

  // The window ends just past today; on (re)scale, scroll so the today line
  // sits ~75% across the viewport instead of leaving the user at the left
  // edge staring at six-month-old空白.
  const viewportRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const viewport = viewportRef.current;
    if (!viewport || !today) {
      return;
    }
    const target = dateToX(today, scale) + LABEL_WIDTH - viewport.clientWidth * 0.75;
    viewport.scrollLeft = Math.max(0, target);
  }, [scale, today]);

  // History bars grouped by owning lane (project_id); unassigned ones land
  // on the 未归属 row.
  const historyByProject = useMemo(() => {
    const map = new Map<string, { task: TimelineHistoryTask; range: BarRange }[]>();
    const loose: { task: TimelineHistoryTask; range: BarRange }[] = [];
    for (const task of historyTasks) {
      const bar = historyBarRange(task);
      const clipped = bar ? clampRangeToScale(bar, scale) : null;
      if (!clipped) {
        continue;
      }
      const entry = { task, range: clipped };
      const owner = task.project_id ?? '';
      if (owner) {
        const rows = map.get(owner) ?? [];
        rows.push(entry);
        map.set(owner, rows);
      } else {
        loose.push(entry);
      }
    }
    return { byProject: map, loose };
  }, [historyTasks, scale]);

  const unassignedPlaced: { task: ProjectsBoardTask; range: BarRange }[] = [];
  const unassignedLoose: ProjectsBoardTask[] = [];
  for (const task of unassigned) {
    const bar = taskBarRange(task, today);
    const clipped = bar ? clampRangeToScale(bar, scale) : null;
    if (clipped) {
      unassignedPlaced.push({ task, range: clipped });
    } else {
      unassignedLoose.push(task);
    }
  }

  return (
    <Stack gap="xs" data-testid="timeline-view">
      {/* Toolbar: 历史 layer toggle (default ON) + window zoom. */}
      <Group gap="md" wrap="wrap" data-testid="timeline-toolbar">
        <Switch
          size="sm"
          label="历史"
          checked={showHistory}
          onChange={(event) => setShowHistory(event.currentTarget.checked)}
          data-testid="timeline-history-toggle"
          styles={{ label: { color: boardPalette.dim } }}
        />
        <SegmentedControl
          size="xs"
          value={zoom}
          onChange={(value) => setZoom(value === 'all' ? 'all' : 'recent')}
          data={[
            { label: '最近半年', value: 'recent' },
            { label: '全部', value: 'all' },
          ]}
          data-testid="timeline-zoom-toggle"
        />
        <Text size="xs" style={{ color: boardPalette.dim }}>
          {scale.start} → {scale.end}
        </Text>
      </Group>

      <ScrollArea viewportRef={viewportRef}>
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

          {habitRows.length > 0 && (
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
                    日课
                  </Text>
                </Box>
                <Box style={{ flex: 1, borderBottom: `1px solid ${boardPalette.border}` }} />
              </Group>
              {habitRows.map((row) => (
                <HabitRow key={row.habit.id} habit={row.habit} scale={scale} />
              ))}
            </Stack>
          )}

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
                <ProjectRow
                  key={project.id}
                  project={project}
                  scale={scale}
                  today={today}
                  history={historyByProject.byProject.get(project.id) ?? []}
                  showHistory={showHistory}
                  selectedTaskId={selectedTaskId}
                  previewTaskId={drag.preview?.taskId ?? null}
                  previewDelta={drag.preview?.deltaDays ?? 0}
                  onSelectTask={onSelectTask}
                  onDragStart={drag.startDrag}
                />
              ))}
            </Stack>
          ))}

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
                {showHistory &&
                  historyByProject.loose.map(({ task, range }) => (
                    <HistoryBar
                      key={task.id}
                      task={task}
                      range={range}
                      scale={scale}
                      selected={selectedTaskId === task.id}
                      onSelect={onSelectTask}
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
    </Stack>
  );
}
