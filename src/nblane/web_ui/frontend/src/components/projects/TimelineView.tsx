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
//
// P1 (2026-09): 长/短任务分层 — ≥14d task bars sink to 期间带 (fainter than
// the 地色带, pinned at the baseline, no sub-lane, no label, hover 铭文卡);
// sub-lane heights compress (刻痕 10px / task 20px / gap 2px). 归档项目 render
// as desaturated read-only lanes after the active groups (toolbar toggle,
// localStorage). Rows collapse to an envelope band + per-task waveform ticks
// (localStorage per case id). Wheel pans (Shift+wheel / trackpad = horizontal),
// blank-area drag pans, 重置视图 restores defaults, and zoom/window/filter/
// archived/history state round-trips through the URL. Future-zone schedule
// clashes get a 朱砂 stroke + 铭文卡 line; someday seats render as dashed
// 虚位 marks (朱砂 dashed once their planned_start has passed). Lanes with
// nothing in the window slim to one text line.

import {
  ActionIcon,
  Badge,
  Box,
  Button,
  Group,
  MultiSelect,
  SegmentedControl,
  Stack,
  Switch,
  Text,
  Tooltip,
} from '@mantine/core';
import { IconChevronDown, IconChevronRight, IconFocus2, IconRestore } from '@tabler/icons-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

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
  clampRangeToScale,
  collapsedSummary,
  COLLAPSED_ROW_HEIGHT,
  computeScale,
  dateToX,
  daysBetween,
  decodeTimelineParams,
  detectScheduleClashes,
  EMPTY_ROW_HEIGHT,
  encodeTimelineParams,
  estimateLabelWidth,
  filterGroupsBySelection,
  focusWindowForProject,
  groundBandHeight,
  historyBarRange,
  isOverdue,
  isPeriodBand,
  labelPlacement,
  labelsVisible,
  LABEL_INSIDE_MIN_WIDTH,
  laneIsEmptyInWindow,
  layoutLane,
  loadArchivedVisible,
  loadCollapsedRows,
  loadProjectFilter,
  monthTicks,
  panWindow,
  PERIOD_BAND_HEIGHT,
  projectRange,
  rightSpaces,
  saveArchivedVisible,
  saveCollapsedRows,
  saveProjectFilter,
  scaleWidth,
  shiftDate,
  somedaySeatRange,
  taskBarRange,
  TASK_BAR_HEIGHT,
  thinTicks,
  TIMELINE_FILTER_KEY,
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
  | { kind: 'someday'; task: ProjectsBoardTask }
  | { kind: 'history'; task: TimelineHistoryTask };

export interface TimelineViewProps {
  profile: string;
  board: ProjectsBoardResponse;
  groups: LaneGroup[];
  /** Archived cases (status=archived) — rendered as read-only lanes after the
   * active groups when the 归档项目 toggle is on. */
  archivedProjects: ProjectsBoardProject[];
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
  note,
  badge,
  collapsed,
  onToggleCollapse,
  onFocus,
  focusTestId,
}: {
  title: string;
  meta?: string;
  /** Extra dim line (本窗口无活动). */
  note?: string;
  /** Grey status badge next to the title (归档). */
  badge?: string;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
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
        <Group gap={2} wrap="nowrap" style={{ minWidth: 0 }}>
          {onToggleCollapse && (
            <ActionIcon
              size="sm"
              variant="subtle"
              aria-label={collapsed ? `展开 ${title}` : `收起 ${title}`}
              data-testid={collapseTestId(focusTestId)}
              onClick={onToggleCollapse}
              style={{ color: boardPalette.dim, flexShrink: 0 }}
            >
              {collapsed ? <IconChevronRight size={14} /> : <IconChevronDown size={14} />}
            </ActionIcon>
          )}
          <Box style={{ minWidth: 0 }}>
            <Group gap={6} wrap="nowrap">
              <Text size="sm" fw={600} lineClamp={1} style={{ color: boardPalette.titleText }}>
                {title}
              </Text>
              {badge && (
                <Badge
                  size="xs"
                  variant="outline"
                  data-testid={badgeTestId(focusTestId)}
                  style={{ borderColor: boardPalette.dim, color: boardPalette.dim, flexShrink: 0 }}
                >
                  {badge}
                </Badge>
              )}
            </Group>
            {meta && (
              <Text size="xs" lineClamp={1} style={{ color: boardPalette.dim }}>
                {meta}
              </Text>
            )}
            {note && (
              <Text
                size="xs"
                lineClamp={1}
                data-testid={noteTestId(focusTestId)}
                style={{ color: boardPalette.dim, opacity: 0.75 }}
              >
                {note}
              </Text>
            )}
          </Box>
        </Group>
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

// Derived testids keep row-scoped queries working for collapse/note/badge.
function collapseTestId(focusTestId?: string): string | undefined {
  return focusTestId?.replace('timeline-focus-', 'timeline-collapse-');
}
function badgeTestId(focusTestId?: string): string | undefined {
  return focusTestId?.replace('timeline-focus-', 'timeline-badge-');
}
function noteTestId(focusTestId?: string): string | undefined {
  return focusTestId?.replace('timeline-focus-', 'timeline-note-');
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
  clashWith,
  muted,
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
  /** Titles of same-lane bars whose schedule clashes in the future zone. */
  clashWith?: string[];
  /** 归档泳道: everything 淡月白, read-only (no drag). */
  muted?: boolean;
  onSelect: (taskId: string) => void;
  onDragStart: (event: React.PointerEvent, task: ProjectsBoardTask, range: BarRange) => void;
}) {
  const width = Math.max((daysBetween(range.start, range.end) + 1) * scale.dayWidth, 6);
  const status = barStatus(task);
  const overdue = isOverdue(task, today);
  const clash = (clashWith?.length ?? 0) > 0;
  const placement = showLabels
    ? labelPlacement(width, estimateLabelWidth(task.title), rightSpace)
    : 'none';
  const dashed = status === 'queue';
  const border = selected
    ? `2px solid ${boardPalette.selectedBorder}`
    : muted
      ? '1px solid rgba(176, 167, 140, 0.4)'
      : overdue || clash
        ? `1px ${dashed ? 'dashed' : 'solid'} ${boardPalette.overdue}`
        : status === 'queue'
          ? `1px dashed ${boardPalette.dim}`
          : status === 'done'
            ? '1px solid rgba(242, 237, 224, 0.45)'
            : `1px solid ${boardPalette.gold}`;
  const statusLabel = task.column === 'someday' ? '也许' : (STATUS_LABELS[status] ?? status);
  const inscriptionLines = [
    overdue ? `${statusLabel} · 已逾期` : statusLabel,
    ...(clash ? [`与 ${clashWith!.join('、')} 撞期`] : []),
    projectTitle,
  ].filter(Boolean);
  const bar = (
    <Box
      role="button"
      tabIndex={0}
      aria-label={`时间轴任务 ${task.title}`}
      title={placement === 'none' ? undefined : `${task.title} · ${range.start} → ${range.end}`}
      data-testid={`timeline-bar-${task.id}`}
      data-clash={clash || undefined}
      onClick={() => onSelect(task.id)}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          onSelect(task.id);
        }
      }}
      onPointerDown={muted ? undefined : (event) => onDragStart(event, task, range)}
      style={{
        position: 'absolute',
        left: dateToX(range.start, scale),
        top,
        width,
        height: TASK_BAR_HEIGHT,
        borderRadius: 3,
        transform: previewDelta ? `translateX(${previewDelta * scale.dayWidth}px)` : undefined,
        cursor: muted ? 'pointer' : 'grab',
        touchAction: 'pan-y',
        background: !muted && status === 'doing' ? 'rgba(220, 174, 85, 0.12)' : 'transparent',
        border,
        opacity: muted ? 0.55 : status === 'done' ? 0.6 : 1,
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
  if (placement === 'none' || clash) {
    // Clash bars keep their on-bar label but still need the 铭文卡 to name
    // the clashing partners on hover.
    return (
      <Tooltip
        label={
          <BarInscription title={task.title} range={range} lines={inscriptionLines} />
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
 * brightens the stroke. Labels follow the same labelPlacement rule as task
 * bars (P1: 归档刻痕不再当无标签处理) — the 7px stroke is too thin to embed
 * text, so 'inside' degrades to the right-hang slot when it fits.
 */
function HistoryBar({
  task,
  range,
  scale,
  selected,
  top,
  rightSpace,
  showLabels,
  projectTitle,
  onSelect,
}: {
  task: TimelineHistoryTask;
  range: BarRange;
  scale: TimelineScale;
  selected: boolean;
  top: number;
  rightSpace: number;
  showLabels: boolean;
  projectTitle: string;
  onSelect: (taskId: string) => void;
}) {
  const width = Math.max((daysBetween(range.start, range.end) + 1) * scale.dayWidth, 6);
  const archived = task.archived === true;
  // 刻痕 embeds nothing: cap barWidth below LABEL_INSIDE_MIN_WIDTH so the
  // shared rule only ever answers right/none here.
  const placement = showLabels
    ? labelPlacement(
        Math.min(width, LABEL_INSIDE_MIN_WIDTH - 1),
        estimateLabelWidth(task.title),
        rightSpace,
      )
    : 'none';
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
      >
        {placement === 'right' && (
          <Text
            component="span"
            data-testid={`timeline-history-label-${task.id}`}
            style={{
              position: 'absolute',
              left: width + 4,
              // Center the 10px label on the 7px stroke.
              top: -3,
              fontSize: 10,
              lineHeight: '13px',
              color: 'rgba(176, 167, 140, 0.8)',
              whiteSpace: 'nowrap',
              pointerEvents: 'none',
            }}
          >
            {task.title}
          </Text>
        )}
      </Box>
    </Tooltip>
  );
}

/**
 * 期间带 (P1 分层): task bars spanning ≥14 days sink to the baseline as a
 * translucent band one notch fainter than the 地色带 — no sub-lane, no label,
 * no drag; hover keeps the 铭文卡, click still selects.
 */
function PeriodBand({
  task,
  range,
  scale,
  selected,
  rowHeight,
  groundHeight,
  muted,
  projectTitle,
  onSelect,
}: {
  task: ProjectsBoardTask;
  range: BarRange;
  scale: TimelineScale;
  selected: boolean;
  rowHeight: number;
  /** 0 when the lane has no 地色带 — the band then hugs the baseline itself. */
  groundHeight: number;
  muted?: boolean;
  projectTitle: string;
  onSelect: (taskId: string) => void;
}) {
  const width = Math.max((daysBetween(range.start, range.end) + 1) * scale.dayWidth, 6);
  const top = rowHeight - groundHeight - (groundHeight > 0 ? 4 : 3) - PERIOD_BAND_HEIGHT;
  return (
    <Tooltip
      label={
        <BarInscription
          title={task.title}
          range={range}
          lines={['期间带', projectTitle].filter(Boolean)}
        />
      }
      withinPortal
      styles={inscriptionTooltipStyles}
    >
      <Box
        role="button"
        tabIndex={0}
        aria-label={`期间带 ${task.title}`}
        data-testid={`timeline-period-${task.id}`}
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
          height: PERIOD_BAND_HEIGHT,
          borderRadius: 3,
          cursor: 'pointer',
          background: muted ? 'rgba(176, 167, 140, 0.05)' : 'rgba(220, 174, 85, 0.035)',
          border: selected
            ? `1px solid ${boardPalette.selectedBorder}`
            : muted
              ? '1px solid rgba(176, 167, 140, 0.12)'
              : '1px solid rgba(220, 174, 85, 0.07)',
        }}
      />
    </Tooltip>
  );
}

/**
 * Someday 虚位: a dashed thin seat at the task's planned activation window
 * plus an S marker. 过期 seats (planned_start already past) flip to 朱砂
 * dashed. Read-only; click selects, hover shows the 铭文卡.
 */
function SomedayBar({
  task,
  range,
  scale,
  selected,
  top,
  today,
  muted,
  projectTitle,
  onSelect,
}: {
  task: ProjectsBoardTask;
  range: BarRange;
  scale: TimelineScale;
  selected: boolean;
  top: number;
  today: string;
  muted?: boolean;
  projectTitle: string;
  onSelect: (taskId: string) => void;
}) {
  const width = Math.max((daysBetween(range.start, range.end) + 1) * scale.dayWidth, 6);
  // 过期: the activation date has arrived (or passed) and the seat is still
  // someday — planned_start <= today flips the dashes to 朱砂.
  const expired = !muted && !!today && range.start <= today;
  const stroke = muted ? 'rgba(176, 167, 140, 0.45)' : expired ? boardPalette.overdue : boardPalette.dim;
  return (
    <Tooltip
      label={
        <BarInscription
          title={task.title}
          range={range}
          lines={[`虚位 · 期望激活 ${range.start}${expired ? ' · 已过期' : ''}`, projectTitle].filter(
            Boolean,
          )}
        />
      }
      withinPortal
      styles={inscriptionTooltipStyles}
    >
      <Box
        role="button"
        tabIndex={0}
        aria-label={`虚位任务 ${task.title}`}
        data-testid={`timeline-someday-${task.id}`}
        data-expired={expired || undefined}
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
          height: 8,
          borderRadius: 2,
          cursor: 'pointer',
          background: 'transparent',
          border: `1px dashed ${selected ? boardPalette.selectedBorder : stroke}`,
          opacity: expired ? 0.85 : 0.7,
        }}
      >
        <Text
          component="span"
          style={{
            position: 'absolute',
            left: 2,
            top: -8,
            fontSize: 8,
            lineHeight: '8px',
            color: stroke,
            pointerEvents: 'none',
          }}
        >
          S
        </Text>
      </Box>
    </Tooltip>
  );
}

/** Build the stacking pool for one lane: placed task bars + visible history
 * 刻痕. ≥14d bars split out as 期间带 (baseline band, no sub-lane, no label). */
function laneInputs(
  tasks: ProjectsBoardTask[],
  history: { task: TimelineHistoryTask; range: BarRange }[],
  showHistory: boolean,
  today: string,
  scale: TimelineScale,
): {
  inputs: LaneLayoutInput<LaneItem>[];
  periods: { task: ProjectsBoardTask; range: BarRange }[];
  unscheduled: ProjectsBoardTask[];
} {
  const inputs: LaneLayoutInput<LaneItem>[] = [];
  const periods: { task: ProjectsBoardTask; range: BarRange }[] = [];
  const unscheduled: ProjectsBoardTask[] = [];
  for (const task of tasks) {
    const bar = taskBarRange(task, today);
    const clipped = bar ? clampRangeToScale(bar, scale) : null;
    if (!clipped) {
      // No anchor date (未排期) or dated fully outside the current window.
      unscheduled.push(task);
      continue;
    }
    if (bar && isPeriodBand(bar)) {
      periods.push({ task, range: clipped });
    } else {
      inputs.push({ item: { kind: 'task', task }, range: clipped, tall: true });
    }
  }
  if (showHistory) {
    for (const { task, range } of history) {
      inputs.push({ item: { kind: 'history', task }, range, tall: false });
    }
  }
  return { inputs, periods, unscheduled };
}

/** Someday seats (虚位): dashed thin markers at planned_start, short lanes. */
function somedayInputs(
  tasks: ProjectsBoardTask[],
  scale: TimelineScale,
): { inputs: LaneLayoutInput<LaneItem>[]; unscheduled: ProjectsBoardTask[] } {
  const inputs: LaneLayoutInput<LaneItem>[] = [];
  const unscheduled: ProjectsBoardTask[] = [];
  for (const task of tasks) {
    const seat = somedaySeatRange(task);
    const clipped = seat ? clampRangeToScale(seat, scale) : null;
    if (clipped) {
      inputs.push({ item: { kind: 'someday', task }, range: clipped, tall: false });
    } else {
      unscheduled.push(task);
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
  clashes,
  muted,
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
  /** Future-zone schedule clashes: taskId → clashing titles. */
  clashes?: Map<string, string[]>;
  /** 归档泳道: desaturated read-only bars. */
  muted?: boolean;
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
            clashWith={clashes?.get(entry.item.task.id)}
            muted={muted}
            projectTitle={projectTitle}
            onSelect={onSelectTask}
            onDragStart={onDragStart}
          />
        ) : entry.item.kind === 'someday' ? (
          <SomedayBar
            key={entry.item.task.id}
            task={entry.item.task}
            range={entry.range}
            scale={scale}
            today={today}
            selected={selectedTaskId === entry.item.task.id}
            top={entry.top}
            muted={muted}
            projectTitle={projectTitle}
            onSelect={onSelectTask}
          />
        ) : (
          <HistoryBar
            key={entry.item.task.id}
            task={entry.item.task}
            range={entry.range}
            scale={scale}
            selected={selectedTaskId === entry.item.task.id}
            top={entry.top}
            rightSpace={spaces[index]}
            showLabels={showLabels}
            projectTitle={projectTitle}
            onSelect={onSelectTask}
          />
        ),
      )}
    </>
  );
}

/** 折叠行内容: 包络带 + per-task 波形 tick + 「N 任务」计数; 里程碑菱形保留. */
function CollapsedLaneContent({
  entries,
  periods,
  milestones,
  scale,
  today,
}: {
  entries: LaneLayoutEntry<LaneItem>[];
  periods: { task: ProjectsBoardTask; range: BarRange }[];
  milestones: ProjectsBoardMilestone[];
  scale: TimelineScale;
  today: string;
}) {
  const eventOf = (entry: LaneLayoutEntry<LaneItem>): string =>
    entry.item.kind === 'task'
      ? entry.item.task.completed_on || entry.item.task.planned_end || entry.range.end
      : entry.item.kind === 'someday'
        ? entry.range.start
        : entry.range.end;
  const summary = collapsedSummary([
    ...entries.map((entry) => ({ range: entry.range, event: eventOf(entry) })),
    ...periods.map(({ task, range }) => ({
      range,
      event: task.completed_on || task.planned_end || range.end,
    })),
  ]);
  const taskCount =
    entries.filter((entry) => entry.item.kind !== 'history').length + periods.length;
  return (
    <>
      {summary.envelope && (
        <Box
          data-testid="collapsed-envelope"
          style={{
            position: 'absolute',
            left: dateToX(summary.envelope.start, scale),
            top: COLLAPSED_ROW_HEIGHT / 2 - 3,
            width:
              (daysBetween(summary.envelope.start, summary.envelope.end) + 1) * scale.dayWidth,
            height: 6,
            borderRadius: 3,
            background: 'rgba(242, 237, 224, 0.07)',
            pointerEvents: 'none',
          }}
        />
      )}
      {summary.ticks.map((tick, index) => (
        <Box
          key={`${tick}-${index}`}
          data-testid="collapsed-tick"
          style={{
            position: 'absolute',
            left: dateToX(tick, scale) + scale.dayWidth / 2 - 1,
            top: COLLAPSED_ROW_HEIGHT / 2 - 5,
            width: 2,
            height: 10,
            background: 'rgba(242, 237, 224, 0.65)',
            pointerEvents: 'none',
          }}
        />
      ))}
      {milestones.map((milestone) => (
        <MilestoneDiamond
          key={milestone.id}
          milestone={milestone}
          scale={scale}
          today={today}
          top={COLLAPSED_ROW_HEIGHT - 14}
        />
      ))}
      <Text
        size="xs"
        data-testid="collapsed-count"
        style={{
          position: 'absolute',
          right: 8,
          top: COLLAPSED_ROW_HEIGHT / 2 - 9,
          color: boardPalette.dim,
          pointerEvents: 'none',
        }}
      >
        {taskCount} 任务
      </Text>
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
  archivedRow,
  collapsed,
  onToggleCollapse,
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
  /** 归档泳道: 整行降饱和 + 只读 + 无地色带. */
  archivedRow?: boolean;
  collapsed: boolean;
  onToggleCollapse: () => void;
  selectedTaskId: string;
  previewTaskId: string | null;
  previewDelta: number;
  onSelectTask: (taskId: string) => void;
  onDragStart: (event: React.PointerEvent, task: ProjectsBoardTask, range: BarRange) => void;
  onFocus: (project: ProjectsBoardProject) => void;
}) {
  const range = projectRange(project.time_range ?? '');
  const clippedRange = archivedRow ? null : range ? clampRangeToScale(range, scale) : null;
  const tasks = [...(project.queue ?? []), ...(project.doing ?? [])];
  const { inputs, periods, unscheduled } = laneInputs(tasks, history, showHistory, today, scale);
  const someday = somedayInputs(project.someday ?? [], scale);
  const layout = layoutLane([...inputs, ...someday.inputs]);
  const unscheduledAll = [...unscheduled, ...someday.unscheduled];
  // 撞期预警: same-lane queue/doing short bars overlapping at/after today.
  // Period bands stay background — they never flash 朱砂.
  const clashes = detectScheduleClashes(
    layout.entries
      .filter((entry) => entry.item.kind === 'task')
      .map((entry) => ({
        id: entry.item.task.id,
        title: entry.item.task.title,
        range: entry.range,
      })),
    today,
  );
  const milestones = project.milestones ?? [];
  // 空行瘦身: nothing in the window → one text line + a dim note. Archived
  // lanes never slim (their quiet is stated by the badge, not by height).
  const empty =
    !archivedRow &&
    laneIsEmptyInWindow({
      entryCount: layout.entries.length,
      periodCount: periods.length,
      ground: clippedRange,
      milestoneDates: milestones.map((milestone) => milestone.date),
      scale,
    });
  const rowHeight = collapsed
    ? COLLAPSED_ROW_HEIGHT
    : empty
      ? EMPTY_ROW_HEIGHT
      : layout.rowHeight;
  const groundHeight = clippedRange ? groundBandHeight(rowHeight) : 0;
  return (
    <Group
      wrap="nowrap"
      gap={0}
      data-testid={`timeline-row-${project.id}`}
      data-archived={archivedRow || undefined}
    >
      <RowLabel
        title={project.title || project.id}
        meta={`${KIND_LABELS[project.kind ?? ''] ?? project.kind} · Done ${project.done_count}`}
        note={empty ? '本窗口无活动' : undefined}
        badge={archivedRow ? '归档' : undefined}
        collapsed={collapsed}
        onToggleCollapse={onToggleCollapse}
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
        {collapsed ? (
          <CollapsedLaneContent
            entries={layout.entries}
            periods={periods}
            milestones={milestones}
            scale={scale}
            today={today}
          />
        ) : (
          <>
            {clippedRange && (
              <Box
                data-testid={`project-range-${project.id}`}
                style={{
                  position: 'absolute',
                  left: dateToX(clippedRange.start, scale),
                  // 衬底细带: pinned to the row baseline, never grows with 错峰
                  // sub-lanes — the time_range stays a ground tint, not a slab.
                  top: rowHeight - groundHeight - 3,
                  width: (daysBetween(clippedRange.start, clippedRange.end) + 1) * scale.dayWidth,
                  height: groundHeight,
                  borderRadius: 3,
                  background: 'rgba(220, 174, 85, 0.05)',
                  border: '1px solid rgba(220, 174, 85, 0.1)',
                  // Milestones sit on the same baseline and must stay visible.
                  pointerEvents: 'none',
                }}
              />
            )}
            {periods.map(({ task, range: periodRange }) => (
              <PeriodBand
                key={task.id}
                task={task}
                range={periodRange}
                scale={scale}
                selected={selectedTaskId === task.id}
                rowHeight={rowHeight}
                groundHeight={groundHeight}
                muted={archivedRow}
                projectTitle={project.title || project.id}
                onSelect={onSelectTask}
              />
            ))}
            <LaneBars
              entries={layout.entries}
              scale={scale}
              today={today}
              selectedTaskId={selectedTaskId}
              previewTaskId={previewTaskId}
              previewDelta={previewDelta}
              showLabels={showLabels}
              clashes={clashes}
              muted={archivedRow}
              projectTitle={project.title || project.id}
              onSelectTask={onSelectTask}
              onDragStart={onDragStart}
            />
            {milestones.map((milestone) => (
              <MilestoneDiamond
                key={milestone.id}
                milestone={milestone}
                scale={scale}
                today={today}
                top={rowHeight - 14}
              />
            ))}
            {unscheduledAll.length > 0 && (
              <Text
                size="xs"
                lineClamp={1}
                data-testid={`unscheduled-${project.id}`}
                title={unscheduledAll.map((task) => task.title).join('、')}
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
                未排期 ×{unscheduledAll.length}:{' '}
                {unscheduledAll.map((task) => task.title).join('、')}
              </Text>
            )}
          </>
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
  archivedProjects,
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
  // URL 视图状态: present params win on entry; absent ones fall back to
  // localStorage prefs / defaults. State is decoded once — later param
  // changes come from our own sync effect below.
  const [searchParams, setSearchParams] = useSearchParams();
  const [initialUrl] = useState(() => decodeTimelineParams(searchParams));
  const [showHistory, setShowHistory] = useState(initialUrl.history ?? true);
  const [showArchived, setShowArchived] = useState(
    initialUrl.archived ?? loadArchivedVisible(window.localStorage),
  );
  const [zoom, setZoom] = useState<TimelineZoom>(initialUrl.zoom ?? 'half');
  // Custom window: set by 聚焦 and by Ctrl+wheel zoom (the window span IS the
  // zoom level — dayWidth stays fit-to-viewport, so zooming out reveals a
  // longer span instead of compressing bars into a sliver).
  const [customWindow, setCustomWindow] = useState<BarRange | null>(initialUrl.window ?? null);
  const [filterSelection, setFilterSelection] = useState<Set<string> | null>(
    initialUrl.projects ?? null,
  );
  // 折叠行: collapsed lane ids, localStorage per case id.
  const [collapsedRows, setCollapsedRows] = useState<Set<string>>(() =>
    loadCollapsedRows(window.localStorage),
  );

  const toggleCollapsed = (projectId: string) => {
    setCollapsedRows((prev) => {
      const next = new Set(prev);
      if (next.has(projectId)) {
        next.delete(projectId);
      } else {
        next.add(projectId);
      }
      saveCollapsedRows(window.localStorage, next);
      return next;
    });
  };

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

  // 窗口平移模型 (2026-09-25 hotfix): the window span always fits the
  // viewport (dayWidth = fitWidth/span), so the content is never DOM-
  // scrollable horizontally and scrollLeft-based panning was a no-op.
  // Panning moves the WINDOW itself: presets materialize their implicit
  // window on first pan (preset highlight drops), and panWindow clamps the
  // result loosely so a fling can't strand the view in empty time.
  const panRemainder = useRef(0);
  const panBy = (days: number) => {
    if (!days) {
      return;
    }
    setCustomWindow((prev) => panWindow(prev ?? { start: scale.start, end: scale.end }, days, today));
  };

  // Plain wheel = page scroll (bubbles untouched); Shift+wheel / trackpad
  // horizontal = window pan (~10% span per notch, sub-notch deltas
  // accumulate); Ctrl+wheel / pinch = stepless zoom anchored at the cursor
  // date (the anchor's relative position inside the window is preserved).
  useEffect(() => {
    const viewport = viewportRef.current;
    if (!viewport) {
      return;
    }
    const onWheel = (event: WheelEvent) => {
      if (!event.ctrlKey && !event.metaKey) {
        const horizontal = event.shiftKey
          ? event.deltaY
          : Math.abs(event.deltaX) > Math.abs(event.deltaY)
            ? event.deltaX
            : 0;
        if (!horizontal) {
          return;
        }
        event.preventDefault();
        const span = daysBetween(scale.start, scale.end) + 1;
        panRemainder.current += (horizontal / 100) * span * 0.1;
        const days = Math.trunc(panRemainder.current);
        panRemainder.current -= days;
        panBy(days);
        return;
      }
      event.preventDefault();
      const mouseX = event.clientX - viewport.getBoundingClientRect().left;
      const axisX = mouseX - LABEL_WIDTH;
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
      setCustomWindow({ start, end });
    };
    viewport.addEventListener('wheel', onWheel, { passive: false });
    return () => viewport.removeEventListener('wheel', onWheel);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scale, today]);

  // 空白处按住拖拽 = 窗口平移 (grab cursor; dx → 天数按 dayWidth 换算).
  // Bars/labels/buttons keep their own gestures — the pan only starts on
  // bare ground, and the window snapshot at gesture start keeps the
  // mapping 1:1 with the cursor.
  const [panning, setPanning] = useState(false);
  const panGesture = useRef<{ startX: number; window: BarRange; pointerId: number } | null>(null);
  const startPan = (event: React.PointerEvent) => {
    if (event.button !== 0 || drag.active) {
      return;
    }
    const target = event.target as HTMLElement;
    if (target.closest('[role="button"], button, a, input, [role="switch"]')) {
      return;
    }
    panGesture.current = {
      startX: event.clientX,
      window: customWindow ?? { start: scale.start, end: scale.end },
      pointerId: event.pointerId,
    };
    const onMove = (moveEvent: PointerEvent) => {
      const gesture = panGesture.current;
      if (!gesture || moveEvent.pointerId !== gesture.pointerId) {
        return;
      }
      const days = Math.round((gesture.startX - moveEvent.clientX) / scale.dayWidth);
      if (!days) {
        return;
      }
      setPanning(true);
      setCustomWindow(panWindow(gesture.window, days, today));
    };
    const finish = () => {
      panGesture.current = null;
      setPanning(false);
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('pointerup', finish);
      window.removeEventListener('pointercancel', finish);
    };
    window.addEventListener('pointermove', onMove);
    window.addEventListener('pointerup', finish);
    window.addEventListener('pointercancel', finish);
  };

  // Today-at-75% horizontal centering: only meaningful when the content can
  // overflow horizontally (全部 zoom over a huge extent → dayWidth floors at
  // 1px). Runs ONLY on first load / preset switch / focus / reset — panning
  // and Ctrl+wheel never retrigger it (they own the window/scroll state).
  const centerOnScale = useRef(true);
  useEffect(() => {
    const viewport = viewportRef.current;
    if (!viewport || !today || !centerOnScale.current) {
      return;
    }
    centerOnScale.current = false;
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
    centerOnScale.current = true;
  };

  const focusProject = (project: ProjectsBoardProject) => {
    const window = focusWindowForProject(project, today);
    if (!window) {
      return;
    }
    setCustomWindow(window);
    centerOnScale.current = true;
  };

  // 重置视图: back to the default 半年窗 + 全项目 + 历史开 + 归档开, and
  // drop the stored prefs so a refresh stays on the default too.
  const resetView = () => {
    setZoom('half');
    setCustomWindow(null);
    setFilterSelection(null);
    setShowHistory(true);
    setShowArchived(true);
    centerOnScale.current = true;
    try {
      window.localStorage.removeItem(TIMELINE_FILTER_KEY);
      saveArchivedVisible(window.localStorage, true);
    } catch {
      // storage unavailable — the in-memory reset still applies
    }
  };

  // URL sync: zoom/window/filter/archived/history ride the searchParams so a
  // refresh or a shared link restores the same view. Replace (not push) —
  // view tweaks must not flood the history stack.
  useEffect(() => {
    const allSelected = allProjectIds.every((id) => selectedProjects.has(id));
    const updates = encodeTimelineParams({
      zoom,
      window: customWindow,
      selectedProjects: allSelected ? null : selectedProjects,
      archived: showArchived,
      history: showHistory,
    });
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        for (const [key, value] of Object.entries(updates)) {
          if (value === null) {
            next.delete(key);
          } else {
            next.set(key, value);
          }
        }
        return next;
      },
      { replace: true },
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [zoom, customWindow, selectedProjects, allProjectIds, showArchived, showHistory]);

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
    const { inputs, periods, unscheduled } = laneInputs(
      unassigned,
      historyByProject.loose,
      showHistory,
      today,
      scale,
    );
    return { layout: layoutLane(inputs), periods, unscheduled };
  }, [unassigned, historyByProject.loose, showHistory, today, scale]);

  return (
    <Stack gap="xs" data-testid="timeline-view">
      {/* Toolbar: 历史/归档 toggles, zoom presets, 项目筛选, 重置视图. */}
      <Group gap="md" wrap="wrap" data-testid="timeline-toolbar">
        <Switch
          size="sm"
          label="历史"
          checked={showHistory}
          onChange={(event) => setShowHistory(event.currentTarget.checked)}
          data-testid="timeline-history-toggle"
          styles={{ label: { color: boardPalette.dim } }}
        />
        <Switch
          size="sm"
          label="归档项目"
          checked={showArchived}
          onChange={(event) => {
            setShowArchived(event.currentTarget.checked);
            saveArchivedVisible(window.localStorage, event.currentTarget.checked);
          }}
          data-testid="timeline-archived-toggle"
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
        <Button
          variant="subtle"
          size="compact-sm"
          leftSection={<IconRestore size={14} />}
          onClick={resetView}
          data-testid="timeline-reset-view"
          style={{ color: boardPalette.dim }}
        >
          重置视图
        </Button>
      </Group>

      {/* Plain scrollport, not ScrollArea: overflowY hidden means the
          timeline never owns the vertical wheel — it chains straight to the
          page (scrollLeft panning is gone; horizontal scroll only survives
          for the 全部-zoom dayWidth-floor overflow edge). */}
      <Box
        ref={viewportRef}
        data-testid="timeline-scrollport"
        style={{ overflowX: 'auto', overflowY: 'hidden' }}
      >
        <Box
          onPointerDown={startPan}
          style={{
            position: 'relative',
            minWidth: LABEL_WIDTH + width,
            cursor: panning ? 'grabbing' : undefined,
            userSelect: panning ? 'none' : undefined,
          }}
        >
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
                  collapsed={collapsedRows.has(project.id)}
                  onToggleCollapse={() => toggleCollapsed(project.id)}
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

          {/* 归档项目泳道: after the active groups, desaturated + read-only. */}
          {showArchived && archivedProjects.length > 0 && (
            <Stack gap={0} data-testid="timeline-group-archived">
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
                  <Text fw={700} size="sm" style={{ color: boardPalette.dim }}>
                    归档
                  </Text>
                </Box>
                <Box style={{ flex: 1, borderBottom: `1px solid ${boardPalette.border}` }} />
              </Group>
              {archivedProjects.map((project) => (
                <ProjectRow
                  key={project.id}
                  project={project}
                  scale={scale}
                  today={today}
                  history={historyByProject.byProject.get(project.id) ?? []}
                  showHistory={showHistory}
                  showLabels={showLabels}
                  archivedRow
                  collapsed={collapsedRows.has(project.id)}
                  onToggleCollapse={() => toggleCollapsed(project.id)}
                  selectedTaskId={selectedTaskId}
                  previewTaskId={null}
                  previewDelta={0}
                  onSelectTask={onSelectTask}
                  onDragStart={drag.startDrag}
                  onFocus={focusProject}
                />
              ))}
            </Stack>
          )}

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
                {unassignedLane.periods.map(({ task, range: periodRange }) => (
                  <PeriodBand
                    key={task.id}
                    task={task}
                    range={periodRange}
                    scale={scale}
                    selected={selectedTaskId === task.id}
                    rowHeight={unassignedLane.layout.rowHeight}
                    groundHeight={0}
                    projectTitle=""
                    onSelect={onSelectTask}
                  />
                ))}
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
      </Box>
    </Stack>
  );
}
