// 时间轴视图 — same LaneGroup[] as the board view (view switch keeps order
// and selection). Month axis + gold dashed today line; per lane a sticky
// label column, the project time_range as a faded ground block, task bars
// with sub-lane stacking (行内错峰), width-aware labels, milestone diamonds
// (planned & overdue = hollow).
//
// 裁决5 contract: the history layer (Done kanban tasks from the kanban.md
// sections + archived tasks from kanban-archive.md) renders as 月白 thin
// 刻痕 bars — half height, no fill, brighten on select, never draggable;
// archive entries are 淡月白 (dimmer than Done). The「历史」toggle defaults
// ON. computeScale clamps dirty dates with a console warning.
//
// P0 (2026-09): 连续缩放 — Ctrl+wheel (trackpad pinch included) scales the
// window span around the cursor-anchored date; dayWidth re-derives from the
// viewport fit, clamped 1–40px. Presets 周/月/季/半年 pin a fixed span with
// today at ~75%, 全部 covers the whole extent; below 3px/day labels hide
// (语义密度).
// 状态即笔法: Queue=虚线空框, Doing=gold 描边+淡金填充, Done=月白刻痕,
// 归档=淡月白, 逾期=淡朱砂描边. 工具栏项目多选筛选(存 localStorage),
// RowLabel 上的「聚焦」把窗口设为该项目的时间范围.
//
// 日课 dedupe: habit rows render once, in the top 日课 section — habit-plan
// projects are filtered out of the lane groups, so there is nothing inline
// to duplicate.

import {
  ActionIcon,
  Box,
  Group,
  MultiSelect,
  ScrollArea,
  SegmentedControl,
  Stack,
  Switch,
  Text,
  Tooltip,
} from '@mantine/core';
import { IconFocus2 } from '@tabler/icons-react';
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';

import type {
  KanbanSection,
  KanbanTask,
  ProjectsBoardMilestone,
  ProjectsBoardProject,
  ProjectsBoardResponse,
  ProjectsBoardTask,
} from '../../api/types';
import { inscription } from '../../theme';
import type { HabitRow, LaneGroup } from './lanes';
import { KIND_LABELS } from './lanes';
import { boardPalette } from './palette';
import type {
  BarRange,
  LaneLayoutEntry,
  LaneLayoutInput,
  TimelineHistoryTask,
  TimelineScale,
  TimelineZoom,
} from './timelineMath';
import {
  barStatus,
  clampDayWidth,
  clampRangeToScale,
  computeScale,
  dateToX,
  daysBetween,
  estimateLabelWidth,
  filterGroupsBySelection,
  focusWindowForProject,
  groundBandHeight,
  historyBarRange,
  isOverdue,
  labelPlacement,
  labelsVisible,
  layoutLane,
  loadProjectFilter,
  monthTicks,
  projectRange,
  rightSpaces,
  saveProjectFilter,
  scaleWidth,
  shiftDate,
  taskBarRange,
  TASK_BAR_HEIGHT,
  thinTicks,
} from './timelineMath';
import { useTimelineDrag } from './useTimelineDrag';
import './TimelineView.css';

const LABEL_WIDTH = 200;
const HABIT_ROW_HEIGHT = 44;

const STATUS_LABELS: Record<string, string> = {
  queue: '排队',
  doing: '进行',
  done: '完成',
};

type LaneItem =
  | { kind: 'task'; task: ProjectsBoardTask }
  | { kind: 'history'; task: TimelineHistoryTask };

export interface TimelineViewProps {
  profile: string;
  board: ProjectsBoardResponse;
  groups: LaneGroup[];
  habitRows: HabitRow[];
  unassigned: ProjectsBoardTask[];
  kanbanEtag: string;
  /** kanban.md sections — the Done section feeds the history layer. */
  kanbanSections: KanbanSection[] | undefined;
  /** kanban-archive.md tasks — the bulk of the history layer (淡月白 刻痕 style). */
  kanbanArchive: KanbanTask[] | undefined;
  selectedTaskId: string;
  onSelectTask: (taskId: string) => void;
  onDragError: (error: unknown) => void;
}

function RowLabel({
  title,
  meta,
  onFocus,
  focusTestId,
}: {
  title: string;
  meta?: string;
  onFocus?: () => void;
  focusTestId?: string;
}) {
  return (
    <Box
      w={LABEL_WIDTH}
      miw={LABEL_WIDTH}
      pl="sm"
      pr={4}
      className="timeline-row-label"
      style={{
        position: 'sticky',
        left: 0,
        zIndex: 2,
        background: boardPalette.ground,
        borderRight: `1px solid ${boardPalette.border}`,
        overflow: 'hidden',
      }}
    >
      <Group gap={4} wrap="nowrap" justify="space-between">
        <Box style={{ minWidth: 0 }}>
          <Text size="sm" fw={600} lineClamp={1} style={{ color: boardPalette.titleText }}>
            {title}
          </Text>
          {meta && (
            <Text size="xs" lineClamp={1} style={{ color: boardPalette.dim }}>
              {meta}
            </Text>
          )}
        </Box>
        {onFocus && (
          <Tooltip label="聚焦该项目时间范围" withinPortal>
            <ActionIcon
              size="sm"
              variant="subtle"
              aria-label={`聚焦 ${title}`}
              data-testid={focusTestId}
              className="timeline-focus-btn"
              onClick={onFocus}
            >
              <IconFocus2 size={14} />
            </ActionIcon>
          </Tooltip>
        )}
      </Group>
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
  // renders as a hollow diamond (过期 planned = 空心). Diamonds stay on the
  // row baseline regardless of sub-lane stacking.
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

/** Hover 铭文卡 for bars too narrow to carry a label. */
function BarInscription({
  title,
  range,
  lines,
}: {
  title: string;
  range: BarRange;
  lines: string[];
}) {
  return (
    <Stack gap={2}>
      <Text
        size="xs"
        fw={600}
        style={{ color: inscription.titleColor, fontFamily: inscription.titleFontFamily }}
      >
        {title}
      </Text>
      <Text size="xs" style={{ color: inscription.bodyColor, fontFamily: inscription.bodyFontFamily }}>
        {range.start} → {range.end}
      </Text>
      {lines.length > 0 && (
        <Text size="xs" style={{ color: inscription.dimColor }}>
          {lines.join(' · ')}
        </Text>
      )}
    </Stack>
  );
}

const inscriptionTooltipStyles = {
  tooltip: {
    background: inscription.background,
    border: `1px solid ${inscription.borderColor}`,
  },
} as const;

/**
 * Task bar — 状态即笔法: Queue=虚线空框(dim dashed, no fill), Doing=gold
 * 描边+淡金填充, Done=月白刻痕, 逾期=淡朱砂描边. Labels follow the width
 * rule (inside ≥60px / right hang / none → hover 铭文卡) and hide entirely
 * below LABEL_DAY_WIDTH_MIN (语义缩放).
 */
function TaskBar({
  task,
  range,
  scale,
  selected,
  previewDelta,
  top,
  rightSpace,
  showLabels,
  projectTitle,
  today,
  onSelect,
  onDragStart,
}: {
  task: ProjectsBoardTask;
  range: BarRange;
  scale: TimelineScale;
  selected: boolean;
  previewDelta: number | null;
  top: number;
  rightSpace: number;
  showLabels: boolean;
  projectTitle: string;
  today: string;
  onSelect: (taskId: string) => void;
  onDragStart: (event: React.PointerEvent, task: ProjectsBoardTask, range: BarRange) => void;
}) {
  const width = Math.max((daysBetween(range.start, range.end) + 1) * scale.dayWidth, 6);
  const status = barStatus(task);
  const overdue = isOverdue(task, today);
  const placement = showLabels
    ? labelPlacement(width, estimateLabelWidth(task.title), rightSpace)
    : 'none';
  const dashed = status === 'queue';
  const border = selected
    ? `2px solid ${boardPalette.selectedBorder}`
    : overdue
      ? `1px ${dashed ? 'dashed' : 'solid'} ${boardPalette.overdue}`
      : status === 'queue'
        ? `1px dashed ${boardPalette.dim}`
        : status === 'done'
          ? '1px solid rgba(242, 237, 224, 0.45)'
          : `1px solid ${boardPalette.gold}`;
  const statusLabel = task.column === 'someday' ? '也许' : (STATUS_LABELS[status] ?? status);
  const bar = (
    <Box
      role="button"
      tabIndex={0}
      aria-label={`时间轴任务 ${task.title}`}
      title={placement === 'none' ? undefined : `${task.title} · ${range.start} → ${range.end}`}
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
        top,
        width,
        height: TASK_BAR_HEIGHT,
        borderRadius: 3,
        transform: previewDelta ? `translateX(${previewDelta * scale.dayWidth}px)` : undefined,
        cursor: 'grab',
        touchAction: 'pan-y',
        background: status === 'doing' ? 'rgba(220, 174, 85, 0.12)' : 'transparent',
        border,
        opacity: status === 'done' ? 0.6 : 1,
      }}
    >
      {placement === 'inside' && (
        <Text
          component="span"
          data-testid={`timeline-bar-label-${task.id}`}
          style={{
            display: 'block',
            fontSize: 10,
            lineHeight: `${TASK_BAR_HEIGHT}px`,
            paddingLeft: 4,
            paddingRight: 2,
            color: status === 'doing' ? boardPalette.text : boardPalette.dim,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            pointerEvents: 'none',
          }}
        >
          {task.title}
        </Text>
      )}
      {placement === 'right' && (
        <Text
          component="span"
          data-testid={`timeline-bar-label-${task.id}`}
          style={{
            position: 'absolute',
            left: width + 4,
            top: 0,
            fontSize: 10,
            lineHeight: `${TASK_BAR_HEIGHT}px`,
            color: boardPalette.dim,
            whiteSpace: 'nowrap',
            pointerEvents: 'none',
          }}
        >
          {task.title}
        </Text>
      )}
    </Box>
  );
  if (placement === 'none') {
    return (
      <Tooltip
        label={
          <BarInscription
            title={task.title}
            range={range}
            lines={[overdue ? `${statusLabel} · 已逾期` : statusLabel, projectTitle].filter(Boolean)}
          />
        }
        withinPortal
        styles={inscriptionTooltipStyles}
      >
        {bar}
      </Tooltip>
    );
  }
  return bar;
}

/**
 * 刻痕 history bar (Done/archived task): 月白, half height, no fill,
 * read-only (no drag); archive entries are 淡月白 (dimmer). Selection
 * brightens the stroke.
 */
function HistoryBar({
  task,
  range,
  scale,
  selected,
  top,
  projectTitle,
  onSelect,
}: {
  task: TimelineHistoryTask;
  range: BarRange;
  scale: TimelineScale;
  selected: boolean;
  top: number;
  projectTitle: string;
  onSelect: (taskId: string) => void;
}) {
  const width = Math.max((daysBetween(range.start, range.end) + 1) * scale.dayWidth, 6);
  const archived = task.archived === true;
  return (
    <Tooltip
      label={
        <BarInscription
          title={task.title}
          range={range}
          lines={[archived ? '归档' : '已完成', projectTitle].filter(Boolean)}
        />
      }
      withinPortal
      styles={inscriptionTooltipStyles}
    >
      <Box
        role="button"
        tabIndex={0}
        aria-label={`历史任务 ${task.title}`}
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
          top,
          width,
          height: 7,
          borderRadius: 2,
          cursor: 'pointer',
          background: 'transparent',
          border: selected
            ? `1.5px solid ${boardPalette.titleText}`
            : archived
              ? '1px solid rgba(176, 167, 140, 0.35)'
              : '1px solid rgba(242, 237, 224, 0.45)',
          opacity: selected ? 1 : archived ? 0.45 : 0.6,
        }}
      />
    </Tooltip>
  );
}

/** Build the stacking pool for one lane: placed task bars + visible history 刻痕. */
function laneInputs(
  tasks: ProjectsBoardTask[],
  history: { task: TimelineHistoryTask; range: BarRange }[],
  showHistory: boolean,
  today: string,
  scale: TimelineScale,
): { inputs: LaneLayoutInput<LaneItem>[]; unscheduled: ProjectsBoardTask[] } {
  const inputs: LaneLayoutInput<LaneItem>[] = [];
  const unscheduled: ProjectsBoardTask[] = [];
  for (const task of tasks) {
    const bar = taskBarRange(task, today);
    const clipped = bar ? clampRangeToScale(bar, scale) : null;
    if (clipped) {
      inputs.push({ item: { kind: 'task', task }, range: clipped, tall: true });
    } else {
      // No anchor date (未排期) or dated fully outside the current window.
      unscheduled.push(task);
    }
  }
  if (showHistory) {
    for (const { task, range } of history) {
      inputs.push({ item: { kind: 'history', task }, range, tall: false });
    }
  }
  return { inputs, unscheduled };
}

function LaneBars({
  entries,
  scale,
  today,
  selectedTaskId,
  previewTaskId,
  previewDelta,
  showLabels,
  projectTitle,
  onSelectTask,
  onDragStart,
}: {
  entries: LaneLayoutEntry<LaneItem>[];
  scale: TimelineScale;
  today: string;
  selectedTaskId: string;
  previewTaskId: string | null;
  previewDelta: number;
  showLabels: boolean;
  projectTitle: string;
  onSelectTask: (taskId: string) => void;
  onDragStart: (event: React.PointerEvent, task: ProjectsBoardTask, range: BarRange) => void;
}) {
  const spaces = rightSpaces(entries, scale);
  return (
    <>
      {entries.map((entry, index) =>
        entry.item.kind === 'task' ? (
          <TaskBar
            key={entry.item.task.id}
            task={entry.item.task}
            range={entry.range}
            scale={scale}
            today={today}
            selected={selectedTaskId === entry.item.task.id}
            previewDelta={previewTaskId === entry.item.task.id ? previewDelta : null}
            top={entry.top}
            rightSpace={spaces[index]}
            showLabels={showLabels}
            projectTitle={projectTitle}
            onSelect={onSelectTask}
            onDragStart={onDragStart}
          />
        ) : (
          <HistoryBar
            key={entry.item.task.id}
            task={entry.item.task}
            range={entry.range}
            scale={scale}
            selected={selectedTaskId === entry.item.task.id}
            top={entry.top}
            projectTitle={projectTitle}
            onSelect={onSelectTask}
          />
        ),
      )}
    </>
  );
}

function ProjectRow({
  project,
  scale,
  today,
  history,
  showHistory,
  showLabels,
  selectedTaskId,
  previewTaskId,
  previewDelta,
  onSelectTask,
  onDragStart,
  onFocus,
}: {
  project: ProjectsBoardProject;
  scale: TimelineScale;
  today: string;
  history: { task: TimelineHistoryTask; range: BarRange }[];
  showHistory: boolean;
  showLabels: boolean;
  selectedTaskId: string;
  previewTaskId: string | null;
  previewDelta: number;
  onSelectTask: (taskId: string) => void;
  onDragStart: (event: React.PointerEvent, task: ProjectsBoardTask, range: BarRange) => void;
  onFocus: (project: ProjectsBoardProject) => void;
}) {
  const range = projectRange(project.time_range ?? '');
  const clippedRange = range ? clampRangeToScale(range, scale) : null;
  const tasks = [...(project.queue ?? []), ...(project.doing ?? []), ...(project.someday ?? [])];
  const { inputs, unscheduled } = laneInputs(tasks, history, showHistory, today, scale);
  const layout = layoutLane(inputs);
  const rowHeight = layout.rowHeight;
  return (
    <Group wrap="nowrap" gap={0} data-testid={`timeline-row-${project.id}`}>
      <RowLabel
        title={project.title || project.id}
        meta={`${KIND_LABELS[project.kind ?? ''] ?? project.kind} · Done ${project.done_count}`}
        onFocus={() => onFocus(project)}
        focusTestId={`timeline-focus-${project.id}`}
      />
      <Box
        style={{
          position: 'relative',
          height: rowHeight,
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
              // 衬底细带: pinned to the row baseline, never grows with 错峰
              // sub-lanes — the time_range stays a ground tint, not a slab.
              top: rowHeight - groundBandHeight(rowHeight) - 3,
              width: (daysBetween(clippedRange.start, clippedRange.end) + 1) * scale.dayWidth,
              height: groundBandHeight(rowHeight),
              borderRadius: 3,
              background: 'rgba(220, 174, 85, 0.05)',
              border: '1px solid rgba(220, 174, 85, 0.1)',
              // Milestones sit on the same baseline and must stay visible.
              pointerEvents: 'none',
            }}
          />
        )}
        <LaneBars
          entries={layout.entries}
          scale={scale}
          today={today}
          selectedTaskId={selectedTaskId}
          previewTaskId={previewTaskId}
          previewDelta={previewDelta}
          showLabels={showLabels}
          projectTitle={project.title || project.id}
          onSelectTask={onSelectTask}
          onDragStart={onDragStart}
        />
        {(project.milestones ?? []).map((milestone) => (
          <MilestoneDiamond
            key={milestone.id}
            milestone={milestone}
            scale={scale}
            today={today}
            top={rowHeight - 14}
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
              top: rowHeight / 2 - 9,
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
          height: HABIT_ROW_HEIGHT,
          flex: 1,
          borderBottom: `1px solid ${boardPalette.border}`,
        }}
      >
        {clipped && (
          <Box
            style={{
              position: 'absolute',
              left: dateToX(clipped.start, scale),
              top: HABIT_ROW_HEIGHT / 2 - 6,
              width: (daysBetween(clipped.start, clipped.end) + 1) * scale.dayWidth,
              height: 12,
              borderRadius: 6,
              border: `1px dashed ${boardPalette.gold}`,
              background: 'rgba(220, 174, 85, 0.08)',
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
                top: HABIT_ROW_HEIGHT / 2 - 4,
                width: 8,
                height: 8,
                borderRadius: '50%',
                background: boardPalette.gold,
              }}
            />
          ))}
      </Box>
    </Group>
  );
}

/** Done/archived kanban tasks as timeline history items. */
export function collectHistoryTasks(
  kanbanSections: KanbanSection[] | undefined,
  kanbanArchive: KanbanTask[] | undefined,
): TimelineHistoryTask[] {
  const items: TimelineHistoryTask[] = [];
  for (const section of kanbanSections ?? []) {
    for (const task of section.tasks ?? []) {
      if (section.name === 'Done' || task.done) {
        items.push(task);
      }
    }
  }
  // Archived tasks render with the same 刻痕 style but dimmer (淡月白).
  for (const task of kanbanArchive ?? []) {
    items.push({ ...task, archived: true });
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
  kanbanArchive,
  selectedTaskId,
  onSelectTask,
  onDragError,
}: TimelineViewProps) {
  const today = board.today || '';
  const [showHistory, setShowHistory] = useState(true);
  const [zoom, setZoom] = useState<TimelineZoom>('half');
  // Custom window: set by 聚焦 and by Ctrl+wheel zoom (the window span IS the
  // zoom level — dayWidth stays fit-to-viewport, so zooming out reveals a
  // longer span instead of compressing bars into a sliver).
  const [customWindow, setCustomWindow] = useState<BarRange | null>(null);
  const [filterSelection, setFilterSelection] = useState<Set<string> | null>(null);

  const historyTasks = useMemo(
    () => collectHistoryTasks(kanbanSections, kanbanArchive),
    [kanbanSections, kanbanArchive],
  );

  // 项目筛选: default 全选; stored selection (localStorage) intersects with
  // the ids that still exist. 日课 rows are immune (they live outside groups).
  const allProjects = useMemo(() => groups.flatMap((group) => group.projects), [groups]);
  const allProjectIds = useMemo(() => allProjects.map((project) => project.id), [allProjects]);
  const selectedProjects = useMemo(
    () => filterSelection ?? loadProjectFilter(window.localStorage, allProjectIds),
    [filterSelection, allProjectIds],
  );
  const visibleGroups = useMemo(
    () => filterGroupsBySelection(groups, selectedProjects),
    [groups, selectedProjects],
  );

  // Axis fit width = viewport minus the sticky label column.
  const viewportRef = useRef<HTMLDivElement>(null);
  const [viewportWidth, setViewportWidth] = useState(0);
  useEffect(() => {
    const viewport = viewportRef.current;
    if (!viewport) {
      return;
    }
    const update = () => setViewportWidth(viewport.clientWidth);
    update();
    if (typeof ResizeObserver === 'undefined') {
      window.addEventListener('resize', update);
      return () => window.removeEventListener('resize', update);
    }
    const observer = new ResizeObserver(update);
    observer.observe(viewport);
    return () => observer.disconnect();
  }, []);

  const scale = useMemo(
    () =>
      computeScale(board, {
        history: showHistory ? historyTasks : [],
        zoom,
        window: customWindow ?? undefined,
        fitWidth: viewportWidth > 0 ? viewportWidth - LABEL_WIDTH : undefined,
      }),
    [board, historyTasks, showHistory, zoom, customWindow, viewportWidth],
  );
  const width = scaleWidth(scale);
  const showLabels = labelsVisible(scale);
  const drag = useTimelineDrag({
    profile,
    scale,
    kanbanEtag,
    today,
    onError: onDragError,
  });

  // Ctrl+wheel / pinch: stepless zoom anchored at the cursor date. The window
  // span scales around the anchor (its relative position inside the window is
  // preserved); dayWidth re-derives from the viewport fit (clamped 1–40px).
  const pendingScrollRef = useRef<number | null>(null);
  useEffect(() => {
    const viewport = viewportRef.current;
    if (!viewport) {
      return;
    }
    const onWheel = (event: WheelEvent) => {
      if (!event.ctrlKey && !event.metaKey) {
        return;
      }
      event.preventDefault();
      const mouseX = event.clientX - viewport.getBoundingClientRect().left;
      const axisX = viewport.scrollLeft + mouseX - LABEL_WIDTH;
      const oldSpan = daysBetween(scale.start, scale.end) + 1;
      const newSpan = Math.round(
        Math.min(Math.max(oldSpan * Math.exp(event.deltaY * 0.0022), 2), 5000),
      );
      if (newSpan === oldSpan) {
        return;
      }
      const anchorDays = axisX / scale.dayWidth;
      const ratio = Math.min(Math.max(anchorDays / oldSpan, 0), 1);
      const startOffset = Math.round(anchorDays - ratio * (newSpan - 1));
      const start = shiftDate(scale.start, startOffset);
      const end = shiftDate(start, newSpan - 1);
      const fitWidth = viewport.clientWidth - LABEL_WIDTH;
      const newDayWidth = clampDayWidth(fitWidth > 0 ? fitWidth / newSpan : scale.dayWidth);
      pendingScrollRef.current = ratio * newSpan * newDayWidth + LABEL_WIDTH - mouseX;
      setCustomWindow({ start, end });
    };
    viewport.addEventListener('wheel', onWheel, { passive: false });
    return () => viewport.removeEventListener('wheel', onWheel);
  }, [scale]);

  useLayoutEffect(() => {
    const viewport = viewportRef.current;
    if (viewport && pendingScrollRef.current != null) {
      viewport.scrollLeft = Math.max(0, pendingScrollRef.current);
      pendingScrollRef.current = null;
    }
  }, [scale]);

  // On window (re)scale — preset switch, focus, data change — scroll so the
  // today line sits ~75% across the viewport; outside the window (聚焦到
  // 过去/未来) pin the left edge instead. Wheel zoom only changes dayWidth
  // and never retriggers this (anchor math above owns the scroll there).
  useEffect(() => {
    const viewport = viewportRef.current;
    if (!viewport || !today) {
      return;
    }
    const inWindow = today >= scale.start && today <= scale.end;
    const target = inWindow
      ? dateToX(today, scale) + LABEL_WIDTH - viewport.clientWidth * 0.75
      : 0;
    viewport.scrollLeft = Math.max(0, target);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scale.start, scale.end, today]);

  const applyPreset = (value: string) => {
    setZoom(value as TimelineZoom);
    setCustomWindow(null);
  };

  const focusProject = (project: ProjectsBoardProject) => {
    const window = focusWindowForProject(project, today);
    if (!window) {
      return;
    }
    setCustomWindow(window);
  };

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

  const unassignedLane = useMemo(() => {
    const { inputs, unscheduled } = laneInputs(unassigned, historyByProject.loose, showHistory, today, scale);
    return { layout: layoutLane(inputs), unscheduled };
  }, [unassigned, historyByProject.loose, showHistory, today, scale]);

  return (
    <Stack gap="xs" data-testid="timeline-view">
      {/* Toolbar: 历史 layer toggle, zoom presets, 项目筛选. */}
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
          value={customWindow ? '' : zoom}
          onChange={applyPreset}
          data={[
            { label: '周', value: 'week' },
            { label: '月', value: 'month' },
            { label: '季', value: 'quarter' },
            { label: '半年', value: 'half' },
            { label: '全部', value: 'all' },
          ]}
          data-testid="timeline-zoom-toggle"
        />
        <MultiSelect
          size="xs"
          w={220}
          data={allProjects.map((project) => ({
            value: project.id,
            label: project.title || project.id,
          }))}
          value={allProjectIds.filter((id) => selectedProjects.has(id))}
          onChange={(values) => {
            const next = new Set(values);
            setFilterSelection(next);
            saveProjectFilter(window.localStorage, next);
          }}
          placeholder="筛选项目"
          searchable
          rightSection={
            <Text size="xs" style={{ color: boardPalette.dim, whiteSpace: 'nowrap' }} component="span">
              {selectedProjects.size}/{allProjectIds.length}
            </Text>
          }
          rightSectionWidth={52}
          data-testid="timeline-project-filter"
          styles={{
            input: { background: boardPalette.groundSoft, borderColor: boardPalette.border },
            // 紧凑: no pill wrap — selection count lives in the right section,
            // toggling happens in the dropdown (options stay listed).
            pill: { display: 'none' },
          }}
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
              {thinTicks(monthTicks(scale), 56).map((tick) => (
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

          {visibleGroups.map((group) => (
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
                  showLabels={showLabels}
                  selectedTaskId={selectedTaskId}
                  previewTaskId={drag.preview?.taskId ?? null}
                  previewDelta={drag.preview?.deltaDays ?? 0}
                  onSelectTask={onSelectTask}
                  onDragStart={drag.startDrag}
                  onFocus={focusProject}
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
                  height: unassignedLane.layout.rowHeight,
                  flex: 1,
                  borderBottom: `1px dashed ${boardPalette.gold}`,
                }}
              >
                <LaneBars
                  entries={unassignedLane.layout.entries}
                  scale={scale}
                  today={today}
                  selectedTaskId={selectedTaskId}
                  previewTaskId={drag.preview?.taskId ?? null}
                  previewDelta={drag.preview?.deltaDays ?? 0}
                  showLabels={showLabels}
                  projectTitle=""
                  onSelectTask={onSelectTask}
                  onDragStart={drag.startDrag}
                />
                {unassignedLane.unscheduled.length > 0 && (
                  <Text
                    size="xs"
                    lineClamp={1}
                    title={unassignedLane.unscheduled.map((task) => task.title).join('、')}
                    style={{
                      position: 'absolute',
                      right: 8,
                      top: unassignedLane.layout.rowHeight / 2 - 9,
                      maxWidth: '40%',
                      color: boardPalette.dim,
                      pointerEvents: 'none',
                    }}
                  >
                    未排期 ×{unassignedLane.unscheduled.length}:{' '}
                    {unassignedLane.unscheduled.map((task) => task.title).join('、')}
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
