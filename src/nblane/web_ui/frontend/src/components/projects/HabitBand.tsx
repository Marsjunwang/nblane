// 日课栏 — the habit band at the top of the /projects board (above the goal
// groups, separated by a 裱边 gold hairline). One row per habit,全站一行:
// habit-plan projects (kind 'habit') live here too as a progress-arc row and
// never render Queue/Doing swimlanes.
//
// Row: [name · streak · this-week 7 dots · 打卡 button]; habit-plan rows add
// a 第N/总天 progress arc (N from the plan's time_range vs board.today) and a
// hover-revealed 设置 affordance that opens the ProjectEditDrawer for the
// linked case (basics/milestones/delete live there — 日课项目可删除).
// Pure-habit rows get the same hover-reveal gear, opening a lifecycle menu:
// 归档 (one click, the row folds away; 显示已归档 toggle brings it back
// dimmed with a 恢复 item) and 删除 (type-the-name confirm modal with the
// 打卡记录 consequence preview + optional 记入大事记). The week dots are
// 石刻化: unchecked = thin 月白-35% hollow ring, checked = 泥金 filled dot,
// today carries a thin gold outer ring (no Mantine green).
// A row expands into the month heatmap
// (recent_days, 月白→泥金). Clicking an
// EMPTY past/today cell backfills a check-in for that date (POST /checkins);
// clicking a FILLED cell with known check-in ids offers 销印 (inline confirm
// → DELETE /checkins/{id} of the day's latest row). Filled cells whose rows
// predate check-in ids are read-only (tooltip explains). The starmap
// HabitSeal stays disabled until it is wired to the same endpoint.

import {
  ActionIcon,
  Alert,
  Button,
  Checkbox,
  Group,
  Menu,
  Modal,
  Stack,
  Text,
  TextInput,
  Tooltip,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconArchive,
  IconCheck,
  IconChevronDown,
  IconChevronRight,
  IconSettings,
  IconTrash,
} from '@tabler/icons-react';
import { useMemo, useState } from 'react';

import { ApiError } from '../../api/client';
import {
  useAddCheckin,
  useArchivedBoardHabits,
  useArchiveHabit,
  useDeleteCheckin,
  useDeleteHabit,
} from '../../api/hooks';
import type { ProjectsBoardHabit } from '../../api/types';
import { buildHeatmapWeeks, heatmapCellColor } from './habitHeatmap';
import type { HabitRow } from './lanes';
import { HABIT_PLAN_KINDS } from './lanes';
import { boardPalette } from './palette';
import { daysBetween, projectRange } from './timelineMath';

function isTodayDate(date: string, today: string): boolean {
  return date === today;
}

/** Habit-plan progress: day N of the plan's time_range (1-based, clamped). */
export function planDayProgress(
  timeRange: string,
  today: string,
): { current: number; total: number } | null {
  const range = projectRange(timeRange);
  if (!range) {
    return null;
  }
  const total = daysBetween(range.start, range.end) + 1;
  if (total <= 0) {
    return null;
  }
  const current = Math.min(Math.max(daysBetween(range.start, today) + 1, 0), total);
  return { current, total };
}

/** Small ring arc: 第N/总天 for habit-plan rows. */
function PlanArc({ current, total }: { current: number; total: number }) {
  const radius = 11;
  const circumference = 2 * Math.PI * radius;
  const fraction = total > 0 ? Math.min(current / total, 1) : 0;
  return (
    <Group gap={6} wrap="nowrap" data-testid="habit-plan-arc">
      <svg width={28} height={28} viewBox="0 0 28 28" aria-hidden="true">
        <circle
          cx={14}
          cy={14}
          r={radius}
          fill="none"
          stroke="rgba(242, 237, 224, 0.18)"
          strokeWidth={2.5}
        />
        <circle
          cx={14}
          cy={14}
          r={radius}
          fill="none"
          stroke={boardPalette.gold}
          strokeWidth={2.5}
          strokeLinecap="round"
          strokeDasharray={`${(fraction * circumference).toFixed(1)} ${circumference.toFixed(1)}`}
          transform="rotate(-90 14 14)"
        />
      </svg>
      <Text size="xs" style={{ color: boardPalette.goldText, whiteSpace: 'nowrap' }}>
        第{current}/{total}天
      </Text>
    </Group>
  );
}

/** 石刻化 week dots: unchecked = thin 月白-35% hollow ring, checked = 泥金
 * filled dot, today's cell carries a thin gold outer ring (box-shadow so the
 * fill/border vocabulary stays intact). No Mantine green. */
function WeekDots({ habit, today }: { habit: ProjectsBoardHabit; today: string }) {
  return (
    <Group gap={6} wrap="nowrap" data-testid={`habit-week-${habit.id}`}>
      {(habit.week ?? []).map((day) => {
        const isToday = isTodayDate(day.date, today) && !day.future;
        return (
          <Tooltip key={day.date} label={day.date} withArrow>
            <span
              data-testid={`habit-dot-${habit.id}-${day.date}`}
              data-done={day.done ? 'true' : 'false'}
              data-today={isToday ? 'true' : 'false'}
              style={{
                display: 'inline-block',
                width: 12,
                height: 12,
                borderRadius: '50%',
                boxSizing: 'border-box',
                background: day.done ? boardPalette.gold : 'transparent',
                border: `1px solid ${
                  day.done ? boardPalette.gold : 'rgba(242, 237, 224, 0.35)'
                }`,
                boxShadow: isToday ? `0 0 0 1.5px ${boardPalette.gold}` : undefined,
                opacity: day.future ? 0.5 : 1,
              }}
            />
          </Tooltip>
        );
      })}
    </Group>
  );
}

/** GitHub-style trailing-90-day grid; empty past/today cells backfill,
 * filled cells (with known check-in ids) offer 销印 via an inline confirm. */
function HabitHeatmap({
  profile,
  habit,
  today,
}: {
  profile: string;
  habit: ProjectsBoardHabit;
  today: string;
}) {
  const checkin = useAddCheckin(profile);
  const deleteCheckin = useDeleteCheckin(profile);
  const weeks = useMemo(() => buildHeatmapWeeks(habit, today), [habit, today]);
  const maxCount = useMemo(
    () =>
      weeks.reduce(
        (max, week) => week.reduce((inner, cell) => Math.max(inner, cell.count), max),
        0,
      ),
    [weeks],
  );
  const [pendingDate, setPendingDate] = useState<string | null>(null);
  /** Date whose filled cell is awaiting 销印 confirmation. */
  const [confirmDate, setConfirmDate] = useState<string | null>(null);

  const backfill = (date: string) => {
    setPendingDate(date);
    checkin.mutate(
      { habit: habit.id, date, summary: '', note: '' },
      {
        onSuccess: () => {
          notifications.show({
            color: 'green',
            title: '已补卡',
            message: `${habit.title || habit.id} · ${date} 打卡成功。`,
          });
        },
        onError: (error) => {
          notifications.show({
            color: 'red',
            title: '补卡失败',
            message: error instanceof Error ? error.message : String(error),
          });
        },
        onSettled: () => setPendingDate(null),
      },
    );
  };

  const confirmCell = confirmDate
    ? weeks.flat().find((cell) => cell.date === confirmDate)
    : undefined;
  /** 销印 removes the day's LATEST check-in row first (most likely a mis-tap). */
  const confirmTargetId =
    confirmCell && confirmCell.checkinIds.length > 0
      ? confirmCell.checkinIds[confirmCell.checkinIds.length - 1]
      : null;

  const unseal = () => {
    if (!confirmDate || !confirmTargetId) {
      return;
    }
    const date = confirmDate;
    setPendingDate(date);
    deleteCheckin.mutate(
      { checkinId: confirmTargetId },
      {
        onSuccess: () => {
          notifications.show({
            color: 'green',
            title: '已销印',
            message: `${habit.title || habit.id} · ${date} 最近一次打卡已删除。`,
          });
        },
        onError: (error) => {
          notifications.show({
            color: 'red',
            title: '销印失败',
            message: error instanceof Error ? error.message : String(error),
          });
        },
        onSettled: () => {
          setPendingDate(null);
          setConfirmDate(null);
        },
      },
    );
  };

  if (weeks.length === 0) {
    return null;
  }
  return (
    <Stack gap={4} data-testid={`habit-heatmap-${habit.id}`} pl="sm" pb={4}>
      <Group gap={3} wrap="nowrap" align="flex-start">
        {weeks.map((week, weekIndex) => (
          <Stack key={weekIndex} gap={3}>
            {week.map((cell) => {
              const filled = cell.count > 0;
              const deletable = filled && cell.checkinIds.length > 0;
              const backfillable = !filled && !cell.future;
              const busy = pendingDate !== null;
              const label = filled
                ? deletable
                  ? `${cell.date} · 已打卡 ${cell.count} 次 · 点击销印最近一次`
                  : `${cell.date} · 已打卡 ${cell.count} 次（记录缺少 id,暂不可销印)`
                : cell.future
                  ? `${cell.date} · 未来`
                  : `${cell.date} · 点击补卡`;
              const onClick = busy
                ? undefined
                : backfillable
                  ? () => backfill(cell.date)
                  : deletable
                    ? () => setConfirmDate(cell.date)
                    : undefined;
              return (
                <Tooltip key={cell.date} label={label} withArrow>
                  <span
                    role={onClick ? 'button' : undefined}
                    aria-label={
                      backfillable
                        ? `补卡 ${habit.title || habit.id} ${cell.date}`
                        : deletable
                          ? `销印 ${habit.title || habit.id} ${cell.date}`
                          : undefined
                    }
                    aria-pressed={deletable ? confirmDate === cell.date : undefined}
                    data-testid={`heatmap-cell-${habit.id}-${cell.date}`}
                    data-filled={filled ? 'true' : 'false'}
                    onClick={onClick}
                    style={{
                      display: 'inline-block',
                      width: 11,
                      height: 11,
                      borderRadius: 2,
                      background: heatmapCellColor(cell.count, maxCount),
                      border: `1px solid ${
                        confirmDate === cell.date
                          ? boardPalette.goldText
                          : isTodayDate(cell.date, today)
                            ? boardPalette.gold
                            : 'rgba(242, 237, 224, 0.12)'
                      }`,
                      opacity: cell.future ? 0.35 : pendingDate === cell.date ? 0.5 : 1,
                      cursor: onClick ? 'pointer' : 'default',
                    }}
                  />
                </Tooltip>
              );
            })}
          </Stack>
        ))}
      </Group>
      {confirmDate && (
        <Group gap="xs" data-testid={`unseal-confirm-${habit.id}`} wrap="nowrap">
          <Text size="xs" style={{ color: boardPalette.titleText }}>
            销印 {confirmDate} 最近一次打卡?
          </Text>
          <Button
            size="compact-xs"
            variant="light"
            color="red"
            disabled={!confirmTargetId || deleteCheckin.isPending}
            onClick={unseal}
            data-testid={`unseal-confirm-yes-${habit.id}`}
          >
            确认销印
          </Button>
          <Button
            size="compact-xs"
            variant="subtle"
            onClick={() => setConfirmDate(null)}
            data-testid={`unseal-confirm-no-${habit.id}`}
          >
            取消
          </Button>
        </Group>
      )}
      <Text size="xs" style={{ color: boardPalette.dim }}>
        近 90 天 · 空格点击补卡,实格点击销印(删最近一次)
      </Text>
    </Stack>
  );
}

/**
 * 删除习惯 confirm modal: consequence preview (将移除 N 条打卡记录) +
 * type-the-name confirm + optional 记入大事记 (default off). 422
 * `habit_delete_confirm_mismatch` lands as an inline field error.
 */
function DeleteHabitModal({
  profile,
  habit,
  opened,
  onClose,
  onDeleted,
}: {
  profile: string;
  habit: ProjectsBoardHabit;
  opened: boolean;
  onClose: () => void;
  onDeleted: (habitId: string) => void;
}) {
  const remove = useDeleteHabit(profile);
  const [confirmTitle, setConfirmTitle] = useState('');
  const [recordChronicle, setRecordChronicle] = useState(false);
  const title = habit.title || habit.id;
  const checkins = habit.total_checkins ?? 0;
  const confirmed = confirmTitle === title;

  const close = () => {
    setConfirmTitle('');
    setRecordChronicle(false);
    remove.reset();
    onClose();
  };

  const runDelete = () => {
    remove.mutate(
      {
        habitId: habit.id,
        body: { confirm_title: confirmTitle, record_chronicle: recordChronicle },
      },
      {
        onSuccess: (result) => {
          notifications.show({
            color: 'green',
            title: '习惯已删除',
            message: `「${title}」已删除,移除 ${result.checkins_removed ?? 0} 条打卡记录。`,
          });
          onDeleted(habit.id);
          close();
        },
      },
    );
  };

  const mismatch =
    remove.error instanceof ApiError &&
    remove.error.status === 422 &&
    remove.error.code === 'habit_delete_confirm_mismatch';

  return (
    <Modal
      opened={opened}
      onClose={close}
      title={`删除习惯 · ${title}`}
      data-testid={`delete-habit-modal-${habit.id}`}
    >
      <Stack gap="sm">
        <Alert color="red" title="后果预告" data-testid={`delete-habit-preview-${habit.id}`}>
          将移除 {checkins} 条打卡记录,习惯「{title}」不再出现在日课栏;此操作不可撤销。
        </Alert>
        <TextInput
          label={`输入习惯名「${title}」以确认`}
          placeholder={title}
          value={confirmTitle}
          onChange={(event) => setConfirmTitle(event.currentTarget.value)}
          error={mismatch ? '习惯名不匹配,请逐字输入。' : undefined}
          data-testid={`delete-habit-confirm-title-${habit.id}`}
        />
        <Checkbox
          label="记入大事记(chronicle 追加 habit.deleted 条目)"
          checked={recordChronicle}
          onChange={(event) => setRecordChronicle(event.currentTarget.checked)}
          data-testid={`delete-habit-record-chronicle-${habit.id}`}
        />
        {remove.error && !mismatch && (
          <Alert color="red" title="删除失败">
            {remove.error.message}
          </Alert>
        )}
        <Group justify="flex-end">
          <Button variant="subtle" onClick={close}>
            取消
          </Button>
          <Button
            color="red"
            disabled={!confirmed}
            loading={remove.isPending}
            onClick={runDelete}
            data-testid={`delete-habit-confirm-${habit.id}`}
          >
            永久删除
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}

/** Pure-habit lifecycle gear: hover-revealed, opens the 归档/删除 menu. */
function HabitLifecycleMenu({
  profile,
  habit,
  archived,
  visible,
  onVisibility,
  onArchived,
  onDeleted,
}: {
  profile: string;
  habit: ProjectsBoardHabit;
  archived: boolean;
  visible: boolean;
  onVisibility: (visible: boolean) => void;
  onArchived: (habitId: string, archived: boolean) => void;
  onDeleted: (habitId: string) => void;
}) {
  const archiveHabit = useArchiveHabit(profile);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const title = habit.title || habit.id;

  const runArchive = (next: boolean) => {
    archiveHabit.mutate(
      { habitId: habit.id, archived: next },
      {
        onSuccess: () => {
          notifications.show({
            color: 'green',
            title: next ? '已归档' : '已恢复',
            message: next
              ? `「${title}」已归档,不再出现在日课栏;打卡历史保留。`
              : `「${title}」已恢复到日课栏。`,
          });
          onArchived(habit.id, next);
        },
        onError: (error) => {
          notifications.show({
            color: 'red',
            title: next ? '归档失败' : '恢复失败',
            message: error instanceof Error ? error.message : String(error),
          });
        },
      },
    );
  };

  return (
    <>
      <Menu withinPortal position="bottom-end" shadow="md">
        <Menu.Target>
          <ActionIcon
            variant="subtle"
            size="sm"
            aria-label={`习惯设置 ${title}`}
            data-testid={`habit-menu-${habit.id}`}
            onFocus={() => onVisibility(true)}
            onBlur={() => onVisibility(false)}
            style={{
              color: boardPalette.dim,
              opacity: visible ? 1 : 0,
              transition: 'opacity 120ms ease',
            }}
          >
            <IconSettings size={14} />
          </ActionIcon>
        </Menu.Target>
        <Menu.Dropdown>
          {archived ? (
            <Menu.Item
              leftSection={<IconArchive size={14} />}
              onClick={() => runArchive(false)}
              data-testid={`habit-restore-${habit.id}`}
            >
              恢复
            </Menu.Item>
          ) : (
            <Menu.Item
              leftSection={<IconArchive size={14} />}
              onClick={() => runArchive(true)}
              data-testid={`habit-archive-${habit.id}`}
            >
              归档
            </Menu.Item>
          )}
          <Menu.Item
            color="red"
            leftSection={<IconTrash size={14} />}
            onClick={() => setDeleteOpen(true)}
            data-testid={`habit-delete-${habit.id}`}
          >
            删除…
          </Menu.Item>
        </Menu.Dropdown>
      </Menu>
      <DeleteHabitModal
        profile={profile}
        habit={habit}
        opened={deleteOpen}
        onClose={() => setDeleteOpen(false)}
        onDeleted={onDeleted}
      />
    </>
  );
}

function HabitBandRow({
  profile,
  row,
  today,
  archived,
  onEditProject,
  onArchived,
  onDeleted,
}: {
  profile: string;
  row: HabitRow;
  today: string;
  /** Locally archived (folded away unless 显示已归档 is on). */
  archived: boolean;
  /** Opens the ProjectEditDrawer for a habit-plan case (日课项目可删除). */
  onEditProject?: (projectId: string) => void;
  onArchived: (habitId: string, archived: boolean) => void;
  onDeleted: (habitId: string) => void;
}) {
  const { habit, project } = row;
  const [expanded, setExpanded] = useState(false);
  // Hover (or keyboard focus on the button) reveals the 设置 affordance.
  const [settingsVisible, setSettingsVisible] = useState(false);
  const checkin = useAddCheckin(profile);
  const todayDone = (habit.week ?? []).some(
    (day) => day.done && !day.future && isTodayDate(day.date, today),
  );
  const isPlan = project ? HABIT_PLAN_KINDS.has(project.kind ?? '') : false;
  const progress = isPlan ? planDayProgress(project?.time_range ?? '', today) : null;
  const planArchived = project?.status === 'archived';

  const runCheckin = () => {
    checkin.mutate(
      { habit: habit.id, date: '', summary: '', note: '' },
      {
        onSuccess: () => {
          notifications.show({
            color: 'green',
            title: '已打卡',
            message: `${habit.title || habit.id} 今日打卡成功。`,
          });
        },
        onError: (error) => {
          notifications.show({
            color: 'red',
            title: '打卡失败',
            message: error instanceof Error ? error.message : String(error),
          });
        },
      },
    );
  };

  return (
    <Stack
      gap={6}
      py={6}
      data-testid={`habit-band-row-${habit.id}`}
      style={{ opacity: archived ? 0.5 : planArchived ? 0.55 : 1 }}
      onMouseEnter={() => setSettingsVisible(true)}
      onMouseLeave={() => setSettingsVisible(false)}
    >
      <Group justify="space-between" wrap="wrap">
        <Group gap="xs" wrap="wrap" style={{ minWidth: 0, flex: '1 1 220px' }}>
          <ActionIcon
            variant="subtle"
            size="sm"
            aria-label={`展开 ${habit.title || habit.id} 热力图`}
            aria-expanded={expanded}
            data-testid={`habit-expand-${habit.id}`}
            onClick={() => setExpanded((value) => !value)}
            style={{ color: boardPalette.dim }}
          >
            {expanded ? <IconChevronDown size={14} /> : <IconChevronRight size={14} />}
          </ActionIcon>
          <Text fw={600} style={{ color: boardPalette.titleText }}>
            {habit.title || habit.id}
          </Text>
          {isPlan && (
            <Text size="xs" style={{ color: boardPalette.goldText }}>
              {planArchived
                ? '习惯计划 · 已归档'
                : project?.title
                  ? `习惯计划 · ${project.title}`
                  : '习惯计划'}
            </Text>
          )}
          {isPlan && project && onEditProject && (
            <ActionIcon
              variant="subtle"
              size="sm"
              aria-label={`编辑项目 ${project.title || project.id}`}
              data-testid={`habit-plan-settings-${project.id}`}
              onClick={() => onEditProject(project.id)}
              onFocus={() => setSettingsVisible(true)}
              onBlur={() => setSettingsVisible(false)}
              style={{
                color: boardPalette.dim,
                opacity: settingsVisible ? 1 : 0,
                transition: 'opacity 120ms ease',
              }}
            >
              <IconSettings size={14} />
            </ActionIcon>
          )}
          {!isPlan && (
            <HabitLifecycleMenu
              profile={profile}
              habit={habit}
              archived={archived}
              visible={settingsVisible}
              onVisibility={setSettingsVisible}
              onArchived={onArchived}
              onDeleted={onDeleted}
            />
          )}
          {archived && (
            <Text size="xs" style={{ color: boardPalette.dim }}>
              已归档
            </Text>
          )}
          <Text size="xs" style={{ color: boardPalette.dim }}>
            连续 {habit.streak ?? 0} 天
            {habit.last_checkin ? ` · 上次 ${habit.last_checkin.slice(5)}` : ''} · 累计{' '}
            {habit.total_checkins ?? 0} 次
          </Text>
        </Group>
        <Group gap="sm" wrap="nowrap" style={{ flexShrink: 0 }}>
          {progress && <PlanArc current={progress.current} total={progress.total} />}
          <WeekDots habit={habit} today={today} />
          <Button
            size="compact-sm"
            variant={todayDone ? 'subtle' : 'light'}
            color="brand"
            leftSection={<IconCheck size={14} />}
            loading={checkin.isPending}
            onClick={runCheckin}
            data-testid={`checkin-button-${habit.id}`}
          >
            {todayDone ? '再打卡' : '打卡'}
          </Button>
        </Group>
      </Group>
      {expanded && <HabitHeatmap profile={profile} habit={habit} today={today} />}
    </Stack>
  );
}

/**
 * The 日课栏 band: one row per habit (linked or not), separated from the goal
 * groups by a 裱边 gold hairline. Renders nothing when the board has no habits.
 * Locally archived rows fold away instantly; the 显示已归档 toggle then
 * fetches server-side archived habits (?include_archived=true) and renders
 * them dimmed with a 恢复 item. A board whose habits are ALL archived renders
 * no band (nothing to toggle from).
 */
export function HabitBand({
  profile,
  rows,
  today,
  onEditProject,
}: {
  profile: string;
  rows: HabitRow[];
  today: string;
  /** Passed to habit-plan rows for the hover 设置 affordance. */
  onEditProject?: (projectId: string) => void;
}) {
  const [archivedIds, setArchivedIds] = useState<ReadonlySet<string>>(new Set());
  const [deletedIds, setDeletedIds] = useState<ReadonlySet<string>>(new Set());
  const [showArchived, setShowArchived] = useState(false);
  // Server-side archived habits, fetched lazily once the toggle is on
  // (archived habits exit the default board payload per the contract).
  const archivedQuery = useArchivedBoardHabits(profile, showArchived);

  const setHabitArchived = (habitId: string, archived: boolean) => {
    setArchivedIds((prev) => {
      const next = new Set(prev);
      if (archived) {
        next.add(habitId);
      } else {
        next.delete(habitId);
      }
      return next;
    });
  };
  const removeHabit = (habitId: string) => {
    setArchivedIds((prev) => {
      if (!prev.has(habitId)) {
        return prev;
      }
      const next = new Set(prev);
      next.delete(habitId);
      return next;
    });
    setDeletedIds((prev) => new Set(prev).add(habitId));
  };

  const liveRows = rows.filter(
    (row) => !deletedIds.has(row.habit.id) && !archivedIds.has(row.habit.id),
  );
  // 已归档 rows (toggle on): locally archived rows still inside `rows` (the
  // refetch window) plus server-side archived habits not already rendered.
  const archivedRows: HabitRow[] = showArchived
    ? [
        ...rows.filter((row) => archivedIds.has(row.habit.id) && !deletedIds.has(row.habit.id)),
        ...(archivedQuery.data ?? [])
          .filter(
            (habit) =>
              !deletedIds.has(habit.id) && !rows.some((row) => row.habit.id === habit.id),
          )
          .map((habit) => ({ habit, project: null })),
      ]
    : [];
  const visibleRows = [...liveRows, ...archivedRows];
  const archivedCount = archivedIds.size + (archivedQuery.data?.length ?? 0);
  if (rows.length === 0) {
    return null;
  }
  return (
    <Stack
      gap={2}
      px="sm"
      py="xs"
      data-testid="habit-band"
      style={{
        background: boardPalette.groundSoft,
        // 裱边: gold hairline separating the band from the goal groups.
        borderTop: '1px solid rgba(220, 174, 85, 0.4)',
        borderBottom: '1px solid rgba(220, 174, 85, 0.4)',
        borderRadius: 4,
      }}
    >
      <Group justify="space-between" wrap="nowrap">
        <Text size="xs" fw={700} style={{ color: boardPalette.goldText, letterSpacing: 2 }}>
          日课
        </Text>
        <Button
          size="compact-xs"
          variant="subtle"
          color="gray"
          onClick={() => setShowArchived((value) => !value)}
          data-testid="habit-show-archived-toggle"
        >
          {showArchived
            ? '隐藏已归档'
            : `显示已归档${archivedCount > 0 ? ` (${archivedCount})` : ''}`}
        </Button>
      </Group>
      {visibleRows.map((row) => (
        <HabitBandRow
          key={row.habit.id}
          profile={profile}
          row={row}
          today={today}
          archived={archivedIds.has(row.habit.id) || row.habit.archived === true}
          onEditProject={onEditProject}
          onArchived={setHabitArchived}
          onDeleted={removeHabit}
        />
      ))}
    </Stack>
  );
}
