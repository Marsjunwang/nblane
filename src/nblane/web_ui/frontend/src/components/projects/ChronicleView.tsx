// 大事记 (chronicle) view — the S-shaped boustrophedon (牛耕式) read of the
// SAME data as the swimlane timeline (queue/doing/done/someday/归档), newest
// on top, read direction alternating per row. Five strokes on one axis per
// row: 月白刻点=done (刻点顶部带项目图形 glyph) · 描金短条=doing · 虚框短条
// =queue · 金虚点=someday (过期转朱砂) · `///` 断轴 for ANY >21d empty
// stretch — between events AND leading/trailing against the domain, so a
// legally empty window renders as a chain of break rows (a fully covered row
// collapses to a thin 断行 strip). Click a break to expand it (session-only,
// never persisted). Elbow connectors drop between rows with a dim-gold ▼;
// date anchors sit at both row ends. Labels live on FOUR tiers (above×2 +
// below×2) and degrade 截断 → 缩字号 before clustering into 「+N」 chips
// (hover lists every name — nothing hides silently). Same-day done marks fan
// out ordered by started_on (earliest at the point, mirrored rows flip).
// Vertical wheel pans time, Ctrl+wheel zooms the per-row span anchored at
// the cursor date. Read-only: hover/click any mark opens the 铭文卡 with a
// 去编辑 jump to the kanban view. No milestones, no zebra, no ground blocks.

import { Box, Button, Group, MultiSelect, Popover, Stack, Text, Tooltip } from '@mantine/core';
import { IconRestore } from '@tabler/icons-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import type {
  KanbanSection,
  KanbanTask,
  ProjectsBoardProject,
  ProjectsBoardResponse,
  ProjectsBoardTask,
} from '../../api/types';
import { inscription } from '../../theme';
import type { LaneGroup } from './lanes';
import { boardPalette } from './palette';
import type {
  ChronicleEvent,
  ChronicleLabelPlacement,
  LabelSide,
  LabelTier,
  RowScale,
} from './chronicleMath';
import {
  buildChronicleRows,
  buildReadingOrder,
  buildRowScale,
  chronicleDateToX,
  chronicleLabelWidth,
  chronicleRowsForHeight,
  chronicleXToDate,
  clampChronicleSpan,
  clipRangeToRow,
  collectChronicleEvents,
  CHRONICLE_COLLAPSED_ROW_HEIGHT,
  CHRONICLE_DEFAULT_SPAN,
  CHRONICLE_ELBOW_HEIGHT,
  CHRONICLE_ROW_HEIGHT,
  decodeChronicleParams,
  defaultChronicleAnchor,
  detectBreaks,
  encodeChronicleParams,
  filterChronicleEvents,
  LABEL_TRUNCATE_KEEP,
  layoutChronicleLabels,
  moveReadingSelection,
  neighborWindow,
  panChronicle,
  sameDayFanOffsets,
  zoomChronicle,
} from './chronicleMath';
import { daysBetween, loadProjectFilter, saveProjectFilter, TIMELINE_FILTER_KEY } from './timelineMath';

// Row geometry (px). Two label tiers per side at ~24px pitch around the axis.
const AXIS_Y = 70;
const AXIS_COLOR = '#3a4d6e';
const DIM_DEEP = '#8d8570';
const MOON = boardPalette.text;
const GOLD = boardPalette.gold;
const GOLD_TEXT = boardPalette.goldText;
const CINNABAR = boardPalette.overdue;
const PLOT_X = 34;
const RIGHT_RESERVE = 64;

/** Label block top for a side/tier; each block is ~24px (title + date lines). */
function labelTop(side: LabelSide, tier: LabelTier): number {
  return side === 'above' ? (tier === 0 ? 28 : 2) : tier === 0 ? 84 : 110;
}

/** Connector line from the label block to the axis. */
function connectorStyle(side: LabelSide, tier: LabelTier): { top: number; height: number } {
  if (side === 'above') {
    const top = labelTop(side, tier) + 24;
    return { top, height: AXIS_Y - 5 - top };
  }
  return { top: AXIS_Y + 8, height: labelTop(side, tier) - (AXIS_Y + 8) };
}

const STATUS_LABELS: Record<ChronicleEvent['kind'], string> = {
  queue: '排队',
  doing: '进行',
  done: '完成',
  someday: '虚位',
};

export interface ChronicleViewProps {
  board: ProjectsBoardResponse;
  groups: LaneGroup[];
  archivedProjects: ProjectsBoardProject[];
  unassigned: ProjectsBoardTask[];
  kanbanSections: KanbanSection[] | undefined;
  kanbanArchive: KanbanTask[] | undefined;
  /** 去编辑: jump to the kanban view with the task selected. */
  onEditTask: (taskId: string) => void;
}

interface PlacedEvent {
  event: ChronicleEvent;
  /** Visual x of the clipped range start/end (start may be right of end on mirrored rows). */
  x0: number;
  x1: number;
  /** Label anchor x (range midpoint, or the point x). */
  cx: number;
}

/** Events clipping this row, with their visual coordinates. */
function placeEvents(events: ChronicleEvent[], scale: RowScale): PlacedEvent[] {
  const placed: PlacedEvent[] = [];
  for (const event of events) {
    const clipped = clipRangeToRow({ start: event.start, end: event.end }, scale.row);
    if (!clipped) {
      continue;
    }
    const x0 = chronicleDateToX(scale, clipped.start);
    const x1 = chronicleDateToX(scale, clipped.end);
    if (x0 == null || x1 == null) {
      continue;
    }
    placed.push({ event, x0, x1, cx: (x0 + x1) / 2 });
  }
  // Point marks (done 刻点 / someday 虚位) render AFTER range bars so they
  // stay clickable/hoverable on days a bar also covers.
  placed
    .sort((a, b) => a.cx - b.cx)
    .sort((a, b) => {
      const pa = a.event.kind === 'done' || a.event.kind === 'someday' ? 1 : 0;
      const pb = b.event.kind === 'done' || b.event.kind === 'someday' ? 1 : 0;
      return pa - pb;
    });
  // 同日完成扇排: done events sharing one completion date fan out around the
  // point ordered by started_on (earliest at the point; mirrored rows flip).
  // The label anchor (cx) stays on the true date.
  const fan = sameDayFanOffsets(
    placed
      .filter((entry) => entry.event.kind === 'done')
      .map((entry) => ({
        id: entry.event.id,
        date: entry.event.start,
        startedOn: entry.event.startedOn,
      })),
    { mirror: !scale.row.ltr, step: 10 },
  );
  for (const entry of placed) {
    const dx = fan.get(entry.event.id) ?? 0;
    entry.x0 += dx;
    entry.x1 += dx;
  }
  return placed;
}

/** 铭文卡 (read-only): 任务名 / 项目 / 起止 / 状态 / 去编辑. */
function ChronicleInscription({
  event,
  projectTitle,
  onEdit,
}: {
  event: ChronicleEvent;
  projectTitle: string;
  onEdit: () => void;
}) {
  const statusLine = [
    STATUS_LABELS[event.kind],
    event.overdue ? '已过期' : '',
    event.archived ? '归档' : '',
  ]
    .filter(Boolean)
    .join(' · ');
  return (
    <Stack gap={4} data-testid={`chronicle-card-${event.id}`}>
      <Text
        size="sm"
        fw={600}
        style={{ color: inscription.titleColor, fontFamily: inscription.titleFontFamily }}
      >
        {event.title}
      </Text>
      {projectTitle && (
        <Text size="xs" style={{ color: inscription.accentColor }}>
          {projectTitle}
          {event.archived ? '（归档）' : ''}
        </Text>
      )}
      <Text size="xs" style={{ color: inscription.bodyColor, fontFamily: inscription.bodyFontFamily }}>
        {event.start === event.end ? event.start : `${event.start} → ${event.end}`}
      </Text>
      <Text size="xs" style={{ color: inscription.dimColor }}>
        {statusLine}
      </Text>
      <Button
        size="compact-xs"
        variant="light"
        data-testid={`chronicle-edit-${event.id}`}
        onClick={onEdit}
      >
        去编辑
      </Button>
    </Stack>
  );
}

const LABEL_FONT = '"Songti SC", "SimSun", "Noto Serif SC", serif';

/** One event mark on the axis (刻点+glyph / 描金条 / 虚框条 / 虚位点) + its label. */
function EventMark({
  placed,
  placement,
  projectTitle,
  cardOpen,
  selected,
  onOpenCard,
  onSelect,
  onScheduleClose,
  onToggleProject,
  projectFiltered,
  onEditTask,
}: {
  placed: PlacedEvent;
  placement: ChronicleLabelPlacement | undefined;
  projectTitle: string;
  cardOpen: boolean;
  /** 键盘/画布选中态: 描金高亮. */
  selected: boolean;
  onOpenCard: () => void;
  onSelect: () => void;
  onScheduleClose: () => void;
  onToggleProject: (projectId: string) => void;
  projectFiltered: boolean;
  onEditTask: (taskId: string) => void;
}) {
  const { event } = placed;
  const faded = event.archived;
  const opacity = faded ? 0.55 : 1;
  const x = Math.min(placed.x0, placed.x1);
  const width = Math.abs(placed.x1 - placed.x0);
  const isPoint = event.kind === 'done' || event.kind === 'someday';
  // Inner mark coordinates are WRAPPER-relative. Point marks get a 10px hit
  // wrapper; the done wrapper reaches up to carry the project glyph above
  // the 刻点. Range bars get a wrapper padded 2px around the bar.
  let mark: React.ReactNode = null;
  if (event.kind === 'done') {
    mark = (
      <>
        {event.glyph && (
          <Text
            component="span"
            data-testid={`chronicle-glyph-${event.id}`}
            style={{
              position: 'absolute',
              left: 0,
              right: 0,
              top: 0,
              textAlign: 'center',
              fontSize: 9,
              lineHeight: '11px',
              color: MOON,
              opacity: faded ? 0.45 : 0.8,
              pointerEvents: 'none',
            }}
          >
            {event.glyph}
          </Text>
        )}
        <Box
          style={{
            position: 'absolute',
            left: 4,
            top: 10,
            width: 2,
            height: 14,
            background: MOON,
            opacity: faded ? 0.55 : 0.85,
          }}
        />
      </>
    );
  } else if (event.kind === 'doing') {
    mark = (
      <Box
        style={{
          position: 'absolute',
          left: 2,
          top: 5,
          width: Math.max(width, 4),
          height: 10,
          borderRadius: 4,
          background: 'rgba(220, 174, 85, 0.14)',
          border: `1.2px solid ${GOLD}`,
          opacity,
        }}
      />
    );
  } else if (event.kind === 'queue') {
    mark = (
      <Box
        style={{
          position: 'absolute',
          left: 2,
          top: 5,
          width: Math.max(width, 4),
          height: 10,
          borderRadius: 3,
          border: `1.1px dashed ${DIM_DEEP}`,
          opacity,
        }}
      />
    );
  } else {
    const stroke = event.overdue ? CINNABAR : GOLD;
    mark = (
      <Box
        style={{
          position: 'absolute',
          left: 0.5,
          top: 5.5,
          width: 9,
          height: 9,
          borderRadius: '50%',
          border: `1.4px dashed ${stroke}`,
          opacity: faded ? 0.55 : event.overdue ? 0.9 : 1,
        }}
      />
    );
  }

  const side = placement?.side ?? 'above';
  const tier = placement?.tier ?? 0;
  const titleFont = placement?.size === 'small' ? 8.5 : 11.5;
  const dateFont = placement?.size === 'small' ? 8 : 9.5;
  const labelCx = placement?.cx ?? placed.cx;
  const displayTitle =
    placement?.truncated && event.title.length > LABEL_TRUNCATE_KEEP
      ? `${event.title.slice(0, LABEL_TRUNCATE_KEEP)}…`
      : event.title;
  const label = placement && (
    <>
      <Box
        style={{
          position: 'absolute',
          left: labelCx,
          width: 1,
          background: AXIS_COLOR,
          pointerEvents: 'none',
          ...connectorStyle(side, tier),
        }}
      />
      <Box
        data-testid={`chronicle-label-${event.id}`}
        data-tier={tier}
        data-size={placement.size}
        style={{
          position: 'absolute',
          left: labelCx,
          top: labelTop(side, tier),
          transform: 'translateX(-50%)',
          textAlign: 'center',
          whiteSpace: 'nowrap',
          fontFamily: LABEL_FONT,
          opacity: faded ? 0.6 : 1,
        }}
      >
        <Text component="div" style={{ fontSize: titleFont, lineHeight: 1.25, color: faded ? boardPalette.dim : GOLD_TEXT }}>
          {event.badge && (
            <Text
              component="span"
              role="button"
              tabIndex={0}
              title={projectFiltered ? '取消只看该项目' : `只看 ${projectTitle}`}
              data-testid={`chronicle-badge-${event.projectId}`}
              data-filtered={projectFiltered || undefined}
              onClick={(clickEvent) => {
                clickEvent.stopPropagation();
                onToggleProject(event.projectId);
              }}
              onKeyDown={(keyEvent) => {
                if (keyEvent.key === 'Enter' || keyEvent.key === ' ') {
                  keyEvent.preventDefault();
                  keyEvent.stopPropagation();
                  onToggleProject(event.projectId);
                }
              }}
              style={{
                fontSize: Math.max(titleFont - 2, 8),
                color: faded ? DIM_DEEP : GOLD,
                cursor: 'pointer',
                marginRight: 3,
                textDecoration: projectFiltered ? 'underline' : 'none',
              }}
            >
              [{event.badge}]
            </Text>
          )}
          {displayTitle}
        </Text>
        <Text component="div" style={{ fontSize: dateFont, lineHeight: 1.3, color: boardPalette.dim }}>
          {event.dateLabel}
        </Text>
      </Box>
    </>
  );

  return (
    <>
      <Popover
        opened={cardOpen}
        onClose={onScheduleClose}
        position={side === 'above' ? 'top' : 'bottom'}
        withArrow
        withinPortal
        shadow="md"
        width={240}
        styles={{
          dropdown: {
            background: inscription.background,
            border: `1px solid ${inscription.borderColor}`,
          },
          arrow: { borderColor: inscription.borderColor },
        }}
      >
        <Popover.Target>
          <Box
            role="button"
            tabIndex={0}
            aria-label={`大事记事件 ${event.title}`}
            data-testid={`chronicle-event-${event.id}`}
            data-kind={event.kind}
            data-archived={faded || undefined}
            data-selected={selected || undefined}
            onMouseEnter={onOpenCard}
            onMouseLeave={onScheduleClose}
            onClick={(clickEvent) => {
              clickEvent.stopPropagation();
              onSelect();
              onOpenCard();
            }}
            onKeyDown={(keyEvent) => {
              if (keyEvent.key === 'Enter' || keyEvent.key === ' ') {
                keyEvent.preventDefault();
                keyEvent.stopPropagation();
                onSelect();
                onOpenCard();
              }
            }}
            style={{
              position: 'absolute',
              left: isPoint ? x - 5 : x - 2,
              top: event.kind === 'done' ? AXIS_Y - 17 : AXIS_Y - 10,
              width: isPoint ? 10 : Math.max(width, 4) + 4,
              height: event.kind === 'done' ? 27 : 20,
              cursor: 'pointer',
              borderRadius: 6,
              boxShadow: selected ? `0 0 0 1.5px ${GOLD}, 0 0 6px rgba(220, 174, 85, 0.45)` : undefined,
            }}
          >
            {mark}
          </Box>
        </Popover.Target>
        <Popover.Dropdown
          onMouseEnter={onOpenCard}
          onMouseLeave={onScheduleClose}
          style={{ cursor: 'auto' }}
        >
          <ChronicleInscription
            event={event}
            projectTitle={projectTitle}
            onEdit={() => onEditTask(event.id)}
          />
        </Popover.Dropdown>
      </Popover>
      {label}
    </>
  );
}

/** 「+N」 chip: the last-resort label bucket; hover lists every member name. */
function LabelChip({
  cx,
  side,
  tier,
  members,
  projectTitles,
  onOpenMember,
  onScheduleClose,
  chipOpen,
  onOpenChip,
}: {
  cx: number;
  side: LabelSide;
  tier: LabelTier;
  members: { event: ChronicleEvent }[];
  projectTitles: Map<string, string>;
  onOpenMember: (id: string) => void;
  onScheduleClose: () => void;
  chipOpen: boolean;
  onOpenChip: () => void;
}) {
  return (
    <Popover
      opened={chipOpen}
      onClose={onScheduleClose}
      position={side === 'above' ? 'top' : 'bottom'}
      withArrow
      withinPortal
      shadow="md"
      width={260}
      styles={{
        dropdown: {
          background: inscription.background,
          border: `1px solid ${inscription.borderColor}`,
        },
        arrow: { borderColor: inscription.borderColor },
      }}
    >
      <Popover.Target>
        <Box
          role="button"
          tabIndex={0}
          aria-label={`还有 ${members.length} 个事件`}
          data-testid={`chronicle-chip-${members[0]?.event.id ?? 'empty'}`}
          onMouseEnter={onOpenChip}
          onMouseLeave={onScheduleClose}
          onClick={(clickEvent) => {
            clickEvent.stopPropagation();
            onOpenChip();
          }}
          style={{
            position: 'absolute',
            left: cx - 15,
            top: labelTop(side, tier) + 4,
            width: 30,
            height: 16,
            borderRadius: 8,
            border: `1px dashed ${GOLD}`,
            color: GOLD_TEXT,
            fontSize: 9.5,
            lineHeight: '15px',
            textAlign: 'center',
            cursor: 'pointer',
            userSelect: 'none',
            background: 'rgba(220, 174, 85, 0.08)',
          }}
        >
          +{members.length}
        </Box>
      </Popover.Target>
      <Popover.Dropdown
        onMouseEnter={onOpenChip}
        onMouseLeave={onScheduleClose}
        style={{ cursor: 'auto' }}
      >
        <Stack gap={2} data-testid="chronicle-chip-list">
          {members.map(({ event }) => (
            <Text
              key={event.id}
              size="xs"
              role="button"
              tabIndex={0}
              data-testid={`chronicle-chip-member-${event.id}`}
              onClick={() => onOpenMember(event.id)}
              onKeyDown={(keyEvent) => {
                if (keyEvent.key === 'Enter' || keyEvent.key === ' ') {
                  keyEvent.preventDefault();
                  onOpenMember(event.id);
                }
              }}
              style={{
                color: inscription.bodyColor,
                fontFamily: inscription.bodyFontFamily,
                cursor: 'pointer',
              }}
            >
              {event.badge ? `[${event.badge}] ` : ''}
              {event.title} · {event.dateLabel}
              {projectTitles.get(event.projectId) ? `(${projectTitles.get(event.projectId)})` : ''}
            </Text>
          ))}
        </Stack>
      </Popover.Dropdown>
    </Popover>
  );
}

/** One inspector neighbor row (or the highlighted current row). */
function InspectorRow({
  event,
  projectTitle,
  current,
  onJump,
}: {
  event: ChronicleEvent;
  projectTitle: string;
  current: boolean;
  onJump: (id: string) => void;
}) {
  return (
    <Group
      gap={6}
      wrap="nowrap"
      role="button"
      tabIndex={0}
      data-testid={`chronicle-inspector-row-${event.id}`}
      data-current={current || undefined}
      title={projectTitle ? `${event.title} · ${projectTitle}` : event.title}
      onClick={() => onJump(event.id)}
      onKeyDown={(keyEvent) => {
        if (keyEvent.key === 'Enter' || keyEvent.key === ' ') {
          keyEvent.preventDefault();
          onJump(event.id);
        }
      }}
      style={{
        padding: '2px 6px',
        borderRadius: 4,
        cursor: 'pointer',
        background: current ? 'rgba(220, 174, 85, 0.12)' : undefined,
        boxShadow: current ? `inset 2px 0 0 ${GOLD}` : undefined,
      }}
    >
      <Text
        component="span"
        style={{ width: 12, fontSize: 9, color: MOON, opacity: event.archived ? 0.45 : 0.8 }}
      >
        {event.glyph}
      </Text>
      <Text
        component="span"
        lineClamp={1}
        style={{
          flex: 1,
          fontSize: 11,
          fontFamily: LABEL_FONT,
          color: current ? GOLD_TEXT : event.archived ? boardPalette.dim : inscription.bodyColor,
        }}
      >
        {event.badge ? `[${event.badge}] ` : ''}
        {event.title}
      </Text>
      <Text
        component="span"
        style={{ fontSize: 9.5, color: boardPalette.dim, fontFamily: LABEL_FONT, flexShrink: 0 }}
      >
        {event.dateLabel}
      </Text>
    </Group>
  );
}

/**
 * 上下文小窗 (inspector): fixed bottom-right floating panel, 石刻风 (ground
 * 底 + 细金边,半透不挡轴). Shows the selected event's mini 铭文卡 plus the
 * reading-order neighbors (前 3 / 后 3, current row highlighted); clicking a
 * neighbor jumps the selection. Auto-hides with no selection.
 */
function ChronicleInspector({
  event,
  projectTitle,
  before,
  after,
  eventById,
  projectTitles,
  onJump,
}: {
  event: ChronicleEvent;
  projectTitle: string;
  before: string[];
  after: string[];
  eventById: Map<string, ChronicleEvent>;
  projectTitles: Map<string, string>;
  onJump: (id: string) => void;
}) {
  const statusLine = [
    STATUS_LABELS[event.kind],
    event.overdue ? '已过期' : '',
    event.archived ? '归档' : '',
  ]
    .filter(Boolean)
    .join(' · ');
  const neighbors = [...before, event.id, ...after];
  return (
    <Box
      data-testid="chronicle-inspector"
      style={{
        position: 'fixed',
        right: 20,
        bottom: 20,
        width: 320,
        zIndex: 300,
        background: boardPalette.ground,
        border: `1px solid ${inscription.borderColor}`,
        borderRadius: 10,
        padding: '10px 12px',
        boxShadow: '0 6px 24px rgba(0, 0, 0, 0.45)',
        opacity: 0.96,
      }}
    >
      <Text size="xs" mb={6} style={{ color: DIM_DEEP, fontSize: 10 }} data-testid="chronicle-inspector-hint">
        ←/→ 或 j/k 移动 · Enter 详情 · Esc 关闭
      </Text>
      <Stack gap={2} mb={6}>
        <Text
          size="sm"
          fw={600}
          lineClamp={1}
          style={{ color: inscription.titleColor, fontFamily: inscription.titleFontFamily }}
        >
          {event.glyph ? `${event.glyph} ` : ''}
          {event.badge ? `[${event.badge}] ` : ''}
          {event.title}
        </Text>
        {projectTitle && (
          <Text size="xs" style={{ color: inscription.accentColor }}>
            {projectTitle}
            {event.archived ? '（归档）' : ''}
          </Text>
        )}
        <Text size="xs" style={{ color: inscription.bodyColor, fontFamily: inscription.bodyFontFamily }}>
          {event.start === event.end ? event.start : `${event.start} → ${event.end}`} · {statusLine}
        </Text>
      </Stack>
      <Stack gap={1} data-testid="chronicle-inspector-neighbors">
        {neighbors.map((id) => {
          const neighbor = eventById.get(id);
          if (!neighbor) {
            return null;
          }
          return (
            <InspectorRow
              key={id}
              event={neighbor}
              projectTitle={projectTitles.get(neighbor.projectId) ?? ''}
              current={id === event.id}
              onJump={onJump}
            />
          );
        })}
      </Stack>
    </Box>
  );
}

export function ChronicleView({
  board,
  groups,
  archivedProjects,
  unassigned,
  kanbanSections,
  kanbanArchive,
  onEditTask,
}: ChronicleViewProps) {
  const today = board.today || '';
  const [searchParams, setSearchParams] = useSearchParams();
  const [initialUrl] = useState(() => decodeChronicleParams(searchParams));
  const [span, setSpan] = useState(initialUrl.span ?? CHRONICLE_DEFAULT_SPAN);
  const [anchor, setAnchor] = useState(() => initialUrl.top ?? defaultChronicleAnchor(today, span));
  const [filterSelection, setFilterSelection] = useState<Set<string> | null>(
    initialUrl.projects ?? null,
  );
  // 断轴展开: session-only by design (展开不记忆).
  const [expandedBreaks, setExpandedBreaks] = useState<Set<string>>(new Set());
  const [openCardId, setOpenCardId] = useState<string | null>(null);
  const closeTimer = useRef<number | null>(null);
  const openCard = (id: string) => {
    if (closeTimer.current != null) {
      window.clearTimeout(closeTimer.current);
      closeTimer.current = null;
    }
    setOpenCardId(id);
  };
  const scheduleClose = () => {
    if (closeTimer.current != null) {
      window.clearTimeout(closeTimer.current);
    }
    closeTimer.current = window.setTimeout(() => setOpenCardId(null), 300);
  };

  const allProjects = useMemo(() => groups.flatMap((group) => group.projects), [groups]);
  const allProjectIds = useMemo(() => allProjects.map((project) => project.id), [allProjects]);
  const selectedProjects = useMemo(
    () => filterSelection ?? loadProjectFilter(window.localStorage, allProjectIds),
    [filterSelection, allProjectIds],
  );

  // Archived lanes are immune to the MultiSelect in the timeline (their own
  // toggle governs them) — mirror that here: they stay selected regardless.
  const selectedForEvents = useMemo(
    () => new Set([...selectedProjects, ...archivedProjects.map((project) => project.id)]),
    [selectedProjects, archivedProjects],
  );

  const laneProjects = useMemo(
    () => [...allProjects, ...archivedProjects],
    [allProjects, archivedProjects],
  );
  const projectTitles = useMemo(() => {
    const map = new Map<string, string>();
    for (const project of laneProjects) {
      map.set(project.id, project.title || project.id);
    }
    return map;
  }, [laneProjects]);

  const events = useMemo(
    () =>
      filterChronicleEvents(
        collectChronicleEvents({
          projects: laneProjects,
          unassigned,
          kanbanSections,
          kanbanArchive,
          today,
        }),
        selectedForEvents,
      ),
    [laneProjects, unassigned, kanbanSections, kanbanArchive, today, selectedForEvents],
  );

  // Canvas size drives both the plot width and the adaptive row count.
  const viewportRef = useRef<HTMLDivElement>(null);
  const [viewportSize, setViewportSize] = useState({ width: 0, height: 0 });
  useEffect(() => {
    const viewport = viewportRef.current;
    if (!viewport) {
      return;
    }
    const update = () =>
      setViewportSize({ width: viewport.clientWidth, height: viewport.clientHeight });
    update();
    if (typeof ResizeObserver === 'undefined') {
      window.addEventListener('resize', update);
      return () => window.removeEventListener('resize', update);
    }
    const observer = new ResizeObserver(update);
    observer.observe(viewport);
    return () => observer.disconnect();
  }, []);

  const plotW = Math.max(240, viewportSize.width - PLOT_X - RIGHT_RESERVE);
  const rowCount = chronicleRowsForHeight(viewportSize.height);
  const rows = useMemo(
    () => buildChronicleRows(anchor, span, rowCount),
    [anchor, span, rowCount],
  );
  // 断轴无处不在: breaks are measured against the whole visible domain —
  // interior gaps AND leading/trailing emptiness (empty window → break rows).
  const domain = useMemo(
    () =>
      rows.length > 0
        ? { start: rows[rows.length - 1].start, end: rows[0].end }
        : { start: anchor, end: anchor },
    [rows, anchor],
  );
  const breaks = useMemo(() => detectBreaks(events, domain), [events, domain]);
  const rowScales = useMemo(
    () =>
      rows.map((row) =>
        buildRowScale(row, breaks, { plotX: PLOT_X, plotW, expandedKeys: expandedBreaks }),
      ),
    [rows, breaks, plotW, expandedBreaks],
  );

  // Per-row placed events, hoisted so the keyboard reading order and the row
  // render share one computation.
  const placedByRow = useMemo(
    () => rowScales.map((scale) => placeEvents(events, scale)),
    [rowScales, events],
  );
  const eventById = useMemo(
    () => new Map(events.map((event) => [event.id, event])),
    [events],
  );

  // 键盘导航: 蛇形阅读顺序 (最新→最久, chip 成员是独立节点), selection is
  // an event id; the ring/Enter row comes from its newest-row occurrence.
  const readingOrder = useMemo(
    () =>
      buildReadingOrder(
        placedByRow.flatMap((placed, rowIndex) =>
          placed.map((entry) => ({
            id: entry.event.id,
            rowIndex,
            date: entry.event.end,
            startedOn: entry.event.startedOn,
          })),
        ),
      ),
    [placedByRow],
  );
  const selectionRowById = useMemo(() => {
    const map = new Map<string, number>();
    placedByRow.forEach((placed, rowIndex) => {
      for (const entry of placed) {
        if (!map.has(entry.event.id)) {
          map.set(entry.event.id, rowIndex);
        }
      }
    });
    return map;
  }, [placedByRow]);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  // Prune a selection that fell out of the visible data (pan/zoom/filter).
  useEffect(() => {
    if (selectedEventId && !readingOrder.includes(selectedEventId)) {
      setSelectedEventId(null);
    }
  }, [readingOrder, selectedEventId]);
  // 自动滚动到可见 (the chronicle rarely overflows, but the contract stands).
  useEffect(() => {
    if (!selectedEventId) {
      return;
    }
    const element = viewportRef.current?.querySelector<HTMLElement>(
      `[data-testid="chronicle-event-${selectedEventId}"]`,
    );
    element?.scrollIntoView?.({ block: 'nearest', inline: 'nearest' });
  }, [selectedEventId]);

  const moveSelection = (delta: number) => {
    setSelectedEventId(moveReadingSelection(readingOrder, selectedEventId, delta));
  };

  // Keyboard: ←/↑/k = 向现在, →/↓/j = 向过去 (方向沿阅读路径,不是屏幕左右);
  // Enter opens the 铭文卡, Esc cancels. No selection + any direction key
  // selects the first (newest) event.
  const onViewportKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Escape') {
      setOpenCardId(null);
      setSelectedEventId(null);
      return;
    }
    if (event.key === 'Enter') {
      if (selectedEventId) {
        event.preventDefault();
        openCard(`${selectionRowById.get(selectedEventId) ?? 0}:${selectedEventId}`);
      }
      return;
    }
    const delta =
      event.key === 'ArrowRight' || event.key === 'ArrowDown' || event.key === 'j'
        ? 1
        : event.key === 'ArrowLeft' || event.key === 'ArrowUp' || event.key === 'k'
          ? -1
          : 0;
    if (!delta) {
      return;
    }
    event.preventDefault();
    moveSelection(delta);
  };

  // 画布任意处点击 = 选中最近事件并接管键盘 (marks stopPropagation, so this
  // only fires on bare ground / labels).
  const onViewportClick = (event: React.MouseEvent<HTMLDivElement>) => {
    const viewport = viewportRef.current;
    if (!viewport) {
      return;
    }
    viewport.focus();
    const rect = viewport.getBoundingClientRect();
    const unit = CHRONICLE_ROW_HEIGHT + CHRONICLE_ELBOW_HEIGHT;
    const rowIndex = Math.min(
      Math.max(Math.floor((event.clientY - rect.top) / unit), 0),
      placedByRow.length - 1,
    );
    const placed = placedByRow[rowIndex] ?? [];
    if (placed.length === 0) {
      return;
    }
    const x = event.clientX - rect.left;
    let best = placed[0];
    let bestDistance = Number.POSITIVE_INFINITY;
    for (const entry of placed) {
      const distance = Math.abs(entry.cx - x);
      if (distance < bestDistance) {
        bestDistance = distance;
        best = entry;
      }
    }
    setSelectedEventId(best.event.id);
  };

  // Latest-layout ref for the wheel handler (bound once, reads live state).
  const liveRef = useRef({ span, anchor, rowScales, today });
  liveRef.current = { span, anchor, rowScales, today };
  const panRemainder = useRef(0);
  useEffect(() => {
    const viewport = viewportRef.current;
    if (!viewport) {
      return;
    }
    const onWheel = (event: WheelEvent) => {
      event.preventDefault();
      const live = liveRef.current;
      if (event.ctrlKey || event.metaKey) {
        // Ctrl+wheel / pinch: stepless per-row span zoom, anchored at the
        // date under the cursor (row + time fraction preserved).
        const rect = viewport.getBoundingClientRect();
        const unit = CHRONICLE_ROW_HEIGHT + CHRONICLE_ELBOW_HEIGHT;
        const rowIndex = Math.min(
          Math.max(Math.floor((event.clientY - rect.top) / unit), 0),
          live.rowScales.length - 1,
        );
        const scale = live.rowScales[rowIndex];
        if (!scale) {
          return;
        }
        const focusDate = chronicleXToDate(scale, event.clientX - rect.left);
        const focusFrac = daysBetween(focusDate, scale.row.end) / Math.max(1, live.span - 1);
        const newSpan = clampChronicleSpan(Math.round(live.span * Math.exp(event.deltaY * 0.0025)));
        if (newSpan === live.span) {
          return;
        }
        setSpan(newSpan);
        setAnchor(zoomChronicle({ newSpan, focusDate, focusRow: rowIndex, focusFrac }));
        return;
      }
      // 垂直滚轮 = 时间平移: down = toward the past (rows climb, older rows
      // grow from the bottom). One row of wheel ≈ one row of time.
      panRemainder.current += (event.deltaY / (CHRONICLE_ROW_HEIGHT + CHRONICLE_ELBOW_HEIGHT)) * live.span;
      const days = Math.trunc(panRemainder.current);
      panRemainder.current -= days;
      if (days) {
        setAnchor(panChronicle(live.anchor, -days, live.today));
      }
    };
    viewport.addEventListener('wheel', onWheel, { passive: false });
    return () => viewport.removeEventListener('wheel', onWheel);
  }, []);

  const toggleProject = (projectId: string) => {
    const only = filterSelection != null && filterSelection.size === 1 && filterSelection.has(projectId);
    const next = only ? null : new Set([projectId]);
    setFilterSelection(next);
    saveProjectFilter(window.localStorage, next ?? new Set(allProjectIds));
  };

  // 重置视图: default 90 天/行 anchored on today, 全项目, breaks folded,
  // and the stored filter pref dropped so a refresh stays on the default.
  const resetView = () => {
    setSpan(CHRONICLE_DEFAULT_SPAN);
    setAnchor(defaultChronicleAnchor(today, CHRONICLE_DEFAULT_SPAN));
    setFilterSelection(null);
    setExpandedBreaks(new Set());
    try {
      window.localStorage.removeItem(TIMELINE_FILTER_KEY);
    } catch {
      // storage unavailable — the in-memory reset still applies
    }
  };

  // URL sync: span + 顶部日期 + filter ride the searchParams so a refresh or
  // shared link restores the same S-fold. Replace — never flood history.
  useEffect(() => {
    const allSelected = allProjectIds.every((id) => selectedProjects.has(id));
    const updates = encodeChronicleParams({
      span,
      top: anchor,
      selectedProjects: allSelected ? null : selectedProjects,
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
  }, [span, anchor, selectedProjects, allProjectIds]);

  const canvasW = PLOT_X + plotW + 40;
  const mmdd = (date: string) => date.slice(5);
  const expandBreak = (key: string) =>
    setExpandedBreaks((prev) => new Set(prev).add(key));

  const breakTooltipStyles = {
    tooltip: {
      background: inscription.background,
      border: `1px solid ${inscription.borderColor}`,
    },
  } as const;

  return (
    <Stack gap="xs" data-testid="chronicle-view">
      {/* Toolbar: 项目筛选 (shared with the timeline), span readout, 重置视图. */}
      <Group gap="md" wrap="wrap" data-testid="chronicle-toolbar">
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
          data-testid="chronicle-project-filter"
          styles={{
            input: { background: boardPalette.groundSoft, borderColor: boardPalette.border },
            pill: { display: 'none' },
          }}
        />
        <Text size="xs" style={{ color: boardPalette.dim }} data-testid="chronicle-span-readout">
          每行 {span} 天 · {rows.length > 0 ? `${rows[rows.length - 1].start} → ${rows[0].end}` : ''}
        </Text>
        <Text size="xs" style={{ color: DIM_DEEP }}>
          刻点=完成(顶部图形=项目 ●◆■▲★✦◈✚) · 金条=进行 · 虚框=排期 · 虚点=虚位 · ///=断轴 · ▲=今天
        </Text>
        <Button
          variant="subtle"
          size="compact-sm"
          leftSection={<IconRestore size={14} />}
          onClick={resetView}
          data-testid="chronicle-reset-view"
          style={{ color: boardPalette.dim }}
        >
          重置视图
        </Button>
      </Group>

      {/* The chronicle owns the vertical wheel (pan) — no page scroll chaining.
          Keyboard: ←/↑/k 向现在, →/↓/j 向过去, Enter 铭文卡, Esc 取消. */}
      <Box
        ref={viewportRef}
        data-testid="chronicle-scrollport"
        tabIndex={0}
        h="calc(100vh - 236px)"
        mih={320}
        onKeyDown={onViewportKeyDown}
        onClick={onViewportClick}
        style={{ overflow: 'hidden', position: 'relative', outline: 'none' }}
      >
        {rows.map((row, rowIndex) => {
          const scale = rowScales[rowIndex];
          // 断行: a break covering the whole row collapses it to a thin strip.
          const onlySeg = scale.segments.length === 1 ? scale.segments[0] : null;
          const collapsed =
            !!onlySeg && onlySeg.gap && onlySeg.start === row.start && onlySeg.end === row.end;
          const elbow =
            rowIndex < rows.length - 1 &&
            (() => {
              const rightSide = row.index % 2 === 0;
              const xd = rightSide ? PLOT_X + plotW + 24 : 12;
              const edge = rightSide ? PLOT_X + plotW : PLOT_X;
              const d = rightSide
                ? `M${edge} 4 H${xd - 10} Q${xd} 4 ${xd} 14 V22 Q${xd} 32 ${xd - 10} 32 H${edge}`
                : `M${edge} 4 H${xd + 10} Q${xd} 4 ${xd} 14 V22 Q${xd} 32 ${xd + 10} 32 H${edge}`;
              return (
                <svg
                  data-testid={`chronicle-elbow-${row.index}`}
                  width={canvasW}
                  height={CHRONICLE_ELBOW_HEIGHT}
                  style={{ display: 'block', margin: '-2px 0' }}
                >
                  <path d={d} fill="none" stroke={AXIS_COLOR} strokeWidth={1.4} />
                  <path d={`M${xd - 6} 14 h12 l-6 10 z`} fill={GOLD} fillOpacity={0.55} />
                </svg>
              );
            })();

          if (collapsed) {
            return (
              <Box key={row.index}>
                <Tooltip
                  label={`${onlySeg.start} → ${onlySeg.end} · ${onlySeg.breakDays} 天无事件,点击展开`}
                  withinPortal
                  styles={breakTooltipStyles}
                >
                  <Box
                    role="button"
                    tabIndex={0}
                    aria-label={`断行 ${onlySeg.start} → ${onlySeg.end}`}
                    data-testid={`chronicle-row-${row.index}`}
                    data-collapsed
                    onClick={() => expandBreak(onlySeg.breakKey!)}
                    onKeyDown={(keyEvent) => {
                      if (keyEvent.key === 'Enter' || keyEvent.key === ' ') {
                        keyEvent.preventDefault();
                        expandBreak(onlySeg.breakKey!);
                      }
                    }}
                    style={{
                      position: 'relative',
                      height: CHRONICLE_COLLAPSED_ROW_HEIGHT,
                      margin: `0 ${PLOT_X}px 0 ${PLOT_X}px`,
                      width: plotW,
                      borderTop: `1px dashed ${AXIS_COLOR}`,
                      color: DIM_DEEP,
                      fontSize: 10,
                      lineHeight: `${CHRONICLE_COLLAPSED_ROW_HEIGHT - 2}px`,
                      textAlign: 'center',
                      fontFamily: LABEL_FONT,
                      cursor: 'pointer',
                      userSelect: 'none',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                    }}
                  >
                    /// {onlySeg.breakDays} 天 · {onlySeg.start} → {onlySeg.end}
                  </Box>
                </Tooltip>
                {elbow}
              </Box>
            );
          }

          const placed = placedByRow[rowIndex];
          const placedById = new Map(placed.map((entry) => [entry.event.id, entry]));
          const todayX = today ? chronicleDateToX(scale, today) : null;
          const layout = layoutChronicleLabels(
            [
              ...(todayX != null
                ? [
                    {
                      id: '__today__',
                      x: todayX,
                      width: 64,
                      title: '今天',
                      badge: '',
                      dateLabel: mmdd(today),
                      pinnedSide: 'above' as const,
                    },
                  ]
                : []),
              ...placed.map((entry) => ({
                id: entry.event.id,
                x: entry.cx,
                width: chronicleLabelWidth(entry.event.title, entry.event.badge, entry.event.dateLabel),
                title: entry.event.title,
                badge: entry.event.badge,
                dateLabel: entry.event.dateLabel,
              })),
            ],
            { plotX: PLOT_X, plotW },
          );
          const placementById = new Map(layout.placements.map((entry) => [entry.id, entry]));
          const todayPlacement = placementById.get('__today__');
          const gaps = scale.segments.filter((seg) => seg.gap);
          const anchorLeft = row.ltr ? row.start : row.end;
          const anchorRight = row.ltr ? row.end : row.start;
          return (
            <Box key={row.index}>
              <Box
                data-testid={`chronicle-row-${row.index}`}
                data-ltr={row.ltr || undefined}
                style={{ position: 'relative', height: CHRONICLE_ROW_HEIGHT }}
              >
                {/* Axis */}
                <Box
                  style={{
                    position: 'absolute',
                    left: PLOT_X,
                    top: AXIS_Y,
                    width: plotW,
                    borderTop: `1.2px solid ${AXIS_COLOR}`,
                  }}
                />
                {/* 断轴 /// blocks */}
                {gaps.map((seg) => {
                  const gx0 = row.ltr ? seg.x0 : PLOT_X + plotW - (seg.x1 - PLOT_X);
                  return (
                    <Tooltip
                      key={seg.breakKey}
                      label={`${seg.start} → ${seg.end} · ${seg.breakDays} 天无事件,点击展开`}
                      withinPortal
                      styles={breakTooltipStyles}
                    >
                      <Box
                        role="button"
                        tabIndex={0}
                        aria-label={`断轴 ${seg.start} → ${seg.end}`}
                        data-testid={`chronicle-break-${seg.breakKey}`}
                        onClick={() => expandBreak(seg.breakKey!)}
                        onKeyDown={(keyEvent) => {
                          if (keyEvent.key === 'Enter' || keyEvent.key === ' ') {
                            keyEvent.preventDefault();
                            expandBreak(seg.breakKey!);
                          }
                        }}
                        style={{
                          position: 'absolute',
                          left: gx0,
                          top: AXIS_Y - 9,
                          width: seg.x1 - seg.x0,
                          height: 18,
                          borderRadius: 3,
                          background: 'rgba(141, 133, 112, 0.10)',
                          color: boardPalette.dim,
                          fontSize: 11,
                          lineHeight: '18px',
                          textAlign: 'center',
                          cursor: 'pointer',
                          userSelect: 'none',
                        }}
                      >
                        ///
                        <Text
                          component="span"
                          style={{
                            position: 'absolute',
                            left: 0,
                            right: 0,
                            top: 20,
                            fontSize: 9,
                            color: DIM_DEEP,
                            textAlign: 'center',
                          }}
                        >
                          {seg.breakDays}天
                        </Text>
                      </Box>
                    </Tooltip>
                  );
                })}
                {/* Date anchors at both ends, nudged inward against clipping */}
                <Text
                  data-testid={`chronicle-anchor-${row.index}-left`}
                  style={{
                    position: 'absolute',
                    left: PLOT_X + 24,
                    top: CHRONICLE_ROW_HEIGHT - 14,
                    transform: 'translateX(-50%)',
                    fontSize: 10,
                    color: DIM_DEEP,
                    fontFamily: LABEL_FONT,
                    whiteSpace: 'nowrap',
                  }}
                >
                  {anchorLeft.slice(2)}
                </Text>
                <Text
                  data-testid={`chronicle-anchor-${row.index}-right`}
                  style={{
                    position: 'absolute',
                    left: PLOT_X + plotW - 24,
                    top: CHRONICLE_ROW_HEIGHT - 14,
                    transform: 'translateX(-50%)',
                    fontSize: 10,
                    color: DIM_DEEP,
                    fontFamily: LABEL_FONT,
                    whiteSpace: 'nowrap',
                  }}
                >
                  {anchorRight.slice(2)}
                </Text>
                {/* Events (card id is row-scoped: a long bar shows in several
                    rows and must not open several 铭文卡 at once) */}
                {placed.map((entry) => (
                  <EventMark
                    key={entry.event.id}
                    placed={entry}
                    placement={placementById.get(entry.event.id)}
                    projectTitle={projectTitles.get(entry.event.projectId) ?? ''}
                    cardOpen={openCardId === `${rowIndex}:${entry.event.id}`}
                    selected={selectedEventId === entry.event.id}
                    onOpenCard={() => openCard(`${rowIndex}:${entry.event.id}`)}
                    onSelect={() => setSelectedEventId(entry.event.id)}
                    onScheduleClose={scheduleClose}
                    onToggleProject={toggleProject}
                    onEditTask={onEditTask}
                    projectFiltered={
                      filterSelection != null &&
                      filterSelection.size === 1 &&
                      filterSelection.has(entry.event.projectId)
                    }
                  />
                ))}
                {/* 「+N」 chips: the overflow bucket, hover lists every name. */}
                {layout.chips.map((chip) => (
                  <LabelChip
                    key={chip.id}
                    cx={chip.cx}
                    side={chip.side}
                    tier={chip.tier}
                    members={chip.memberIds
                      .map((id) => placedById.get(id))
                      .filter((entry): entry is PlacedEvent => !!entry)}
                    projectTitles={projectTitles}
                    chipOpen={openCardId === `${rowIndex}:${chip.id}`}
                    onOpenChip={() => openCard(`${rowIndex}:${chip.id}`)}
                    onOpenMember={(id) => openCard(`${rowIndex}:${id}`)}
                    onScheduleClose={scheduleClose}
                  />
                ))}
                {/* 今天: 朱砂三角 + label (collision-pinned above) */}
                {todayX != null && (
                  <>
                    <Box
                      data-testid="chronicle-today"
                      style={{
                        position: 'absolute',
                        left: todayX - 6,
                        top: AXIS_Y - 16,
                        width: 0,
                        height: 0,
                        borderLeft: '6px solid transparent',
                        borderRight: '6px solid transparent',
                        borderBottom: `10px solid ${CINNABAR}`,
                        pointerEvents: 'none',
                      }}
                    />
                    {todayPlacement && (
                      <Text
                        data-testid="chronicle-today-label"
                        style={{
                          position: 'absolute',
                          left: todayPlacement.cx,
                          top: labelTop('above', 0) + 2,
                          transform: 'translateX(-50%)',
                          fontSize: 10,
                          color: CINNABAR,
                          fontFamily: LABEL_FONT,
                          whiteSpace: 'nowrap',
                          pointerEvents: 'none',
                        }}
                      >
                        今天 {mmdd(today)}
                      </Text>
                    )}
                  </>
                )}
              </Box>
              {/* 行间弯头: row i's oldest end drops to row i+1's newest end
                  (same side by construction); dim-gold ▼ mid-drop. */}
              {elbow}
            </Box>
          );
        })}
      </Box>

      {/* 上下文小窗: 选中事件时出现,无选中自动收起。 */}
      {selectedEventId &&
        (() => {
          const selected = eventById.get(selectedEventId);
          if (!selected) {
            return null;
          }
          const { before, after } = neighborWindow(readingOrder, selectedEventId, 3);
          return (
            <ChronicleInspector
              event={selected}
              projectTitle={projectTitles.get(selected.projectId) ?? ''}
              before={before}
              after={after}
              eventById={eventById}
              projectTitles={projectTitles}
              onJump={(id) => {
                setSelectedEventId(id);
                viewportRef.current?.focus();
              }}
            />
          );
        })()}
    </Stack>
  );
}
