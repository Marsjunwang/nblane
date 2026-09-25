// 大事记 (chronicle) view — the S-shaped boustrophedon (牛耕式) read of the
// SAME data as the swimlane timeline (queue/doing/done/someday/归档), newest
// on top, read direction alternating per row. Five strokes on one axis per
// row: 月白刻点=done · 描金短条=doing · 虚框短条=queue · 金虚点=someday
// (过期转朱砂) · `///` 断轴 for >21d empty stretches (click expands, never
// persisted). Elbow connectors drop between rows with a dim-gold ▼; date
// anchors sit at both row ends; labels alternate above/below with full
// collision layout (对侧 → 缩字号 → 隐藏). Vertical wheel pans time,
// Ctrl+wheel zooms the per-row span anchored at the cursor date. Read-only:
// hover/click any mark opens the 铭文卡 with a 去编辑 jump to the kanban
// view. No milestones, no zebra striping, no per-row ground blocks.

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
import type { ChronicleEvent, RowScale } from './chronicleMath';
import {
  buildChronicleRows,
  buildRowScale,
  chronicleDateToX,
  chronicleLabelWidth,
  chronicleRowsForHeight,
  chronicleXToDate,
  clampChronicleSpan,
  clipRangeToRow,
  collectChronicleEvents,
  CHRONICLE_DEFAULT_SPAN,
  CHRONICLE_ELBOW_HEIGHT,
  CHRONICLE_ROW_HEIGHT,
  decodeChronicleParams,
  defaultChronicleAnchor,
  detectBreaks,
  encodeChronicleParams,
  filterChronicleEvents,
  layoutChronicleLabels,
  panChronicle,
  zoomChronicle,
  type ChronicleLabelPlacement,
} from './chronicleMath';
import { daysBetween, loadProjectFilter, saveProjectFilter, TIMELINE_FILTER_KEY } from './timelineMath';

// Row geometry (px). Row band 120 = inside the 110–130 设计定稿 window.
const AXIS_Y = 58;
const AXIS_COLOR = '#3a4d6e';
const DIM_DEEP = '#8d8570';
const MOON = boardPalette.text;
const GOLD = boardPalette.gold;
const GOLD_TEXT = boardPalette.goldText;
const CINNABAR = boardPalette.overdue;
const PLOT_X = 34;
const RIGHT_RESERVE = 64;

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
  // Fan out same-day point marks (several finishes on one date stack exactly):
  // nudge each later mark a few px right so every one keeps its own hit area.
  // The label anchor (cx) stays on the true date.
  const seen = new Map<number, number>();
  for (const entry of placed) {
    if (entry.event.kind !== 'done' && entry.event.kind !== 'someday') {
      continue;
    }
    const key = Math.round(entry.cx);
    const count = seen.get(key) ?? 0;
    seen.set(key, count + 1);
    if (count > 0) {
      // 10px matches the 10px hit wrapper so fanned marks never overlap.
      entry.x0 += count * 10;
      entry.x1 += count * 10;
    }
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

/** One event mark on the axis (刻点 / 描金条 / 虚框条 / 虚位点) + its label. */
function EventMark({
  placed,
  placement,
  projectTitle,
  cardOpen,
  onOpenCard,
  onScheduleClose,
  onToggleProject,
  projectFiltered,
  onEditTask,
}: {
  placed: PlacedEvent;
  placement: ChronicleLabelPlacement | undefined;
  projectTitle: string;
  cardOpen: boolean;
  onOpenCard: () => void;
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
  // Inner mark coordinates are WRAPPER-relative: point marks get a 10px hit
  // wrapper centered on the date (axis crosses it at local y=10); range bars
  // get a wrapper padded 2px around the bar.
  let mark: React.ReactNode = null;
  if (event.kind === 'done') {
    mark = (
      <Box
        style={{
          position: 'absolute',
          left: 4,
          top: 2,
          width: 2,
          height: 16,
          background: MOON,
          opacity: faded ? 0.55 : 0.85,
        }}
      />
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
  const size = placement?.size ?? 'normal';
  const titleFont = size === 'small' ? 10 : 11.5;
  const dateFont = size === 'small' ? 8.5 : 9.5;
  const labelCx = placement?.cx ?? placed.cx;
  const label = placement && placement.size !== 'hidden' && (
    <>
      <Box
        style={{
          position: 'absolute',
          left: labelCx,
          top: side === 'above' ? AXIS_Y - 18 : AXIS_Y + 9,
          width: 1,
          height: 9,
          background: AXIS_COLOR,
          pointerEvents: 'none',
        }}
      />
      <Box
        data-testid={`chronicle-label-${event.id}`}
        style={{
          position: 'absolute',
          left: labelCx,
          top: side === 'above' ? 10 : AXIS_Y + 20,
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
                fontSize: titleFont - 2,
                color: faded ? DIM_DEEP : GOLD,
                cursor: 'pointer',
                marginRight: 3,
                textDecoration: projectFiltered ? 'underline' : 'none',
              }}
            >
              [{event.badge}]
            </Text>
          )}
          {event.title}
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
            onMouseEnter={onOpenCard}
            onMouseLeave={onScheduleClose}
            onClick={(clickEvent) => {
              clickEvent.stopPropagation();
              onOpenCard();
            }}
            onKeyDown={(keyEvent) => {
              if (keyEvent.key === 'Enter' || keyEvent.key === ' ') {
                keyEvent.preventDefault();
                onOpenCard();
              }
            }}
            style={{
              position: 'absolute',
              left: event.kind === 'done' || event.kind === 'someday' ? x - 5 : x - 2,
              top: AXIS_Y - 10,
              width:
                event.kind === 'done' || event.kind === 'someday' ? 10 : Math.max(width, 4) + 4,
              height: 20,
              cursor: 'pointer',
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
  const breaks = useMemo(() => detectBreaks(events), [events]);

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
  const rowScales = useMemo(
    () =>
      rows.map((row) =>
        buildRowScale(row, breaks, { plotX: PLOT_X, plotW, expandedKeys: expandedBreaks }),
      ),
    [rows, breaks, plotW, expandedBreaks],
  );

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
          刻点=完成 · 金条=进行 · 虚框=排期 · 虚点=虚位 · ///=断轴 · ▲=今天
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

      {/* The chronicle owns the vertical wheel (pan) — no page scroll chaining. */}
      <Box
        ref={viewportRef}
        data-testid="chronicle-scrollport"
        h="calc(100vh - 236px)"
        mih={320}
        style={{ overflow: 'hidden', position: 'relative' }}
      >
        {rows.map((row, rowIndex) => {
          const scale = rowScales[rowIndex];
          const placed = placeEvents(events, scale);
          const todayX = today ? chronicleDateToX(scale, today) : null;
          const labelItems = [
            ...(todayX != null
              ? [
                  {
                    id: '__today__',
                    x: todayX,
                    width: 64,
                    pinnedSide: 'above' as const,
                  },
                ]
              : []),
            ...placed.map((entry) => ({
              id: entry.event.id,
              x: entry.cx,
              width: chronicleLabelWidth(entry.event.title, entry.event.badge, entry.event.dateLabel),
            })),
          ];
          const placements = layoutChronicleLabels(labelItems, { plotX: PLOT_X, plotW });
          const placementById = new Map(placements.map((entry) => [entry.id, entry]));
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
                      styles={{
                        tooltip: {
                          background: inscription.background,
                          border: `1px solid ${inscription.borderColor}`,
                        },
                      }}
                    >
                      <Box
                        role="button"
                        tabIndex={0}
                        aria-label={`断轴 ${seg.start} → ${seg.end}`}
                        data-testid={`chronicle-break-${seg.breakKey}`}
                        onClick={() =>
                          setExpandedBreaks((prev) => new Set(prev).add(seg.breakKey!))
                        }
                        onKeyDown={(keyEvent) => {
                          if (keyEvent.key === 'Enter' || keyEvent.key === ' ') {
                            keyEvent.preventDefault();
                            setExpandedBreaks((prev) => new Set(prev).add(seg.breakKey!));
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
                    top: CHRONICLE_ROW_HEIGHT - 16,
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
                    top: CHRONICLE_ROW_HEIGHT - 16,
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
                    onOpenCard={() => openCard(`${rowIndex}:${entry.event.id}`)}
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
                          top: 12,
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
              {rowIndex < rows.length - 1 &&
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
                      <path
                        d={`M${xd - 6} 14 h12 l-6 10 z`}
                        fill={GOLD}
                        fillOpacity={0.55}
                      />
                    </svg>
                  );
                })()}
            </Box>
          );
        })}
      </Box>
    </Stack>
  );
}
