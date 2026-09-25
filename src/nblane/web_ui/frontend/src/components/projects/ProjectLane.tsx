// One project swimlane: header (kind/status badges, milestone progress,
// folded Done count) + Queue/Doing columns with in-lane drag & drop.
//
// DnD scope is deliberately收敛到单条泳道内 (one DndContext per lane):
// cross-column Queue↔Doing and in-column reorder persist via the move
// endpoint's to_index; cross-lane assignment goes through the detail card's
// PATCH (归属变更). Someday cards are a dashed badge list inside the Queue
// column and never join the drag sort; their own buttons move them into
// Queue or Done through the same card endpoints.

import {
  closestCenter,
  DndContext,
  DragOverlay,
  KeyboardSensor,
  MouseSensor,
  pointerWithin,
  rectIntersection,
  TouchSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import type {
  CollisionDetection,
  DragEndEvent,
  DragOverEvent,
  DragStartEvent,
  UniqueIdentifier,
} from '@dnd-kit/core';
import { sortableKeyboardCoordinates } from '@dnd-kit/sortable';
import {
  ActionIcon,
  Alert,
  Badge,
  Box,
  Button,
  Checkbox,
  Group,
  Modal,
  Progress,
  ScrollArea,
  Stack,
  Text,
  TextInput,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconEdit, IconTrash } from '@tabler/icons-react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { ApiError } from '../../api/client';
import {
  useActiveHabitPlans,
  useAddKanbanCard,
  useAddProjectTask,
  useDeleteHabitPlan,
  useDoneKanbanCard,
  useMoveKanbanCard,
} from '../../api/hooks';
import type {
  HabitPlan,
  KanbanSection,
  ProjectsBoardProject,
  ProjectsBoardTask,
} from '../../api/types';
import {
  activePlansForHabit,
  planHasDaily,
  planProgressLabel,
  planTodayTasks,
} from './habitPlans';
import { LaneColumn, laneColumnDroppableId } from './LaneColumn';
import { QuickAddInput } from './QuickAddInput';
import { SortableTaskCard, TaskCardBody } from './TaskCard';
import { KIND_LABELS, PROJECT_STATUS_LABELS } from './lanes';
import { boardPalette } from './palette';

/** Board column keys this lane drags between (backend section names). */
const LANE_SECTIONS: Record<'queue' | 'doing', string> = { queue: 'Queue', doing: 'Doing' };

/**
 * Translate a lane-local drop into the backend's section-global to_index.
 *
 * The move endpoint reads to_index as the 0-based POST-REMOVAL index within
 * the WHOLE target section (Queue holds every project + unassigned card),
 * while the lane only sees its own filtered cards. We send the PRE-removal
 * index of the reference card (same convention as the retired full-board
 * KanbanPage): dropping on a card takes its visual slot — after it for
 * downward drags, before it for upward ones. `overTaskId` = the lane card
 * the drop landed on; null = lane tail (after the lane's last card in that
 * section; undefined = section tail).
 */
export function laneDropToGlobalIndex(
  sectionTasks: { id: string }[] | undefined,
  laneTasks: ProjectsBoardTask[],
  draggedId: string,
  overTaskId: string | null,
): number | undefined {
  if (!sectionTasks) {
    return undefined; // board not loaded — append at the tail
  }
  // NB: pre-removal indices — the backend removes the dragged card first,
  // which is exactly what makes "over X" land on X's slot.
  const globalIds = sectionTasks.map((task) => task.id);
  if (overTaskId !== null) {
    const overIndex = globalIds.indexOf(overTaskId);
    return overIndex >= 0 ? overIndex : undefined;
  }
  const laneIds = new Set(laneTasks.map((task) => task.id).filter((id) => id !== draggedId));
  let lastLaneIndex = -1;
  globalIds.forEach((id, index) => {
    if (laneIds.has(id)) {
      lastLaneIndex = index;
    }
  });
  return lastLaneIndex >= 0 ? lastLaneIndex + 1 : undefined;
}

interface LaneColumns {
  queue: ProjectsBoardTask[];
  doing: ProjectsBoardTask[];
}

function findColumn(columns: LaneColumns, id: UniqueIdentifier): 'queue' | 'doing' | null {
  const key = String(id);
  for (const column of ['queue', 'doing'] as const) {
    if (columns[column].some((task) => task.id === key)) {
      return column;
    }
  }
  return null;
}

/** Resolve a droppable id (card id or lane-column droppable id) to a column. */
function resolveColumn(
  laneId: string,
  columns: LaneColumns,
  id: UniqueIdentifier,
): 'queue' | 'doing' | null {
  const key = String(id);
  for (const column of ['queue', 'doing'] as const) {
    if (laneColumnDroppableId(laneId, column) === key) {
      return column;
    }
  }
  return findColumn(columns, key);
}

/** Return columns with the active card inserted into the over column. */
function moveBetweenColumns(
  columns: LaneColumns,
  activeId: UniqueIdentifier,
  overId: UniqueIdentifier,
): LaneColumns {
  const fromName = findColumn(columns, activeId);
  const toName = findColumn(columns, overId);
  if (!fromName || !toName || fromName === toName) {
    return columns;
  }
  const activeTask = columns[fromName].find((task) => task.id === String(activeId));
  if (!activeTask) {
    return columns;
  }
  const next: LaneColumns = {
    queue: columns.queue.filter((task) => task.id !== String(activeId)),
    doing: columns.doing.filter((task) => task.id !== String(activeId)),
  };
  const overIndex = next[toName].findIndex((task) => task.id === String(overId));
  next[toName].splice(overIndex >= 0 ? overIndex : next[toName].length, 0, activeTask);
  return next;
}

export function handleLaneMutationError(error: unknown, fallbackTitle: string, onRefresh: () => void) {
  if (error instanceof ApiError && error.status === 412) {
    notifications.show({
      color: 'yellow',
      title: '数据已被他人修改',
      message: '看板已被他人修改,已为你刷新。请确认后再试。',
    });
    onRefresh();
    return;
  }
  // The backend addresses cards by title; a duplicate title is ambiguous
  // and cannot be resolved client-side — point the user at the data layer.
  if (error instanceof ApiError && error.status === 422 && error.code === 'kanban_card_ambiguous') {
    notifications.show({
      color: 'orange',
      title: '存在重名卡片',
      message:
        '看板中存在多张同名卡片,无法确定操作目标。请先在数据层(kanban.md)重命名重复卡片后再试。',
    });
    return;
  }
  notifications.show({
    color: 'red',
    title: fallbackTitle,
    message: error instanceof Error ? error.message : String(error),
  });
}

/**
 * Queue/Doing columns with per-lane DnD. Shared by ProjectLane and the
 * unassigned lane. `laneId` scopes droppable ids; mutations address cards
 * by TITLE (backend card_ref semantics), selection by task id.
 */
export function TaskLaneDnd({
  profile,
  laneId,
  queue,
  doing,
  someday = [],
  kanbanEtag,
  kanbanSections,
  today = '',
  selectedTaskId,
  onSelectTask,
  onRefresh,
  quickAdd,
}: {
  profile: string;
  laneId: string;
  queue: ProjectsBoardTask[];
  doing: ProjectsBoardTask[];
  someday?: ProjectsBoardTask[];
  kanbanEtag: string;
  /** Full kanban.md sections (for lane-local → section-global index translation). */
  kanbanSections: KanbanSection[] | undefined;
  /** Board's today (yyyy-mm-dd); drives the 到期 someday badge. */
  today?: string;
  selectedTaskId: string;
  onSelectTask: (taskId: string) => void;
  onRefresh: () => void;
  /** Inline「＋ 快速添加」for the Queue column top (裁决4). */
  quickAdd?: { pending: boolean; onSubmit: (title: string) => void };
}) {
  const moveCard = useMoveKanbanCard(profile);
  const doneCard = useDoneKanbanCard(profile);
  const serverColumns = useMemo<LaneColumns>(() => ({ queue, doing }), [queue, doing]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [preview, setPreview] = useState<LaneColumns | null>(null);
  const [overColumn, setOverColumn] = useState<'queue' | 'doing' | null>(null);
  const lastOverIdRef = useRef<UniqueIdentifier | null>(null);
  const suppressClickRef = useRef(false);

  const activeColumns = preview ?? serverColumns;
  const activeTask = activeId
    ? (activeColumns.queue.find((task) => task.id === activeId) ??
      activeColumns.doing.find((task) => task.id === activeId) ??
      null)
    : null;
  // A stale etag 412s; block new drags and someday exits while a mutation is in flight.
  const dragDisabled = moveCard.isPending || doneCard.isPending;

  const promoteSomeday = (task: ProjectsBoardTask, target: 'queue' | 'done') => {
    const cardRef = task.id || task.title;
    if (target === 'queue') {
      moveCard.mutate(
        { cardRef, targetSection: 'Queue', etag: kanbanEtag },
        {
          onSuccess: () =>
            notifications.show({
              color: 'green',
              title: '已列入 Queue',
              message: `「${task.title}」已进入日常队列,可拖到 Doing 或在详情卡标记完成。`,
            }),
          onError: (error) => handleLaneMutationError(error, '列入失败', onRefresh),
        },
      );
      return;
    }
    doneCard.mutate(
      { cardRef, etag: kanbanEtag },
      {
        onSuccess: () =>
          notifications.show({
            color: 'green',
            title: '已标记完成',
            message: `「${task.title}」已入 Done。`,
          }),
        onError: (error) => handleLaneMutationError(error, '操作失败', onRefresh),
      },
    );
  };

  useEffect(() => {
    setPreview(null);
    setOverColumn(null);
  }, [serverColumns]);

  const sensors = useSensors(
    useSensor(MouseSensor, { activationConstraint: { distance: 4 } }),
    // Press-and-hold so touch scrolling the page/columns is not hijacked.
    useSensor(TouchSensor, { activationConstraint: { delay: 250, tolerance: 8 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  const collisionDetection: CollisionDetection = useCallback(
    (args) => {
      const columnIds = new Set(
        (['queue', 'doing'] as const).map((column) => laneColumnDroppableId(laneId, column)),
      );
      const pointerIntersections = pointerWithin(args);
      const intersections =
        pointerIntersections.length > 0 ? pointerIntersections : rectIntersection(args);
      let overId: UniqueIdentifier | null =
        intersections.length > 0 ? intersections[0].id : null;
      if (overId != null) {
        const overKey = String(overId);
        if (columnIds.has(overKey)) {
          // Over a column body: pick the closest card inside so the sortable
          // preview lands precisely (excluding the active card itself).
          const columnKey = overKey.endsWith('::queue') ? 'queue' : 'doing';
          const itemIds = activeColumns[columnKey]
            .map((task) => task.id)
            .filter((id) => id !== String(args.active.id));
          if (itemIds.length > 0) {
            const closest = closestCenter({
              ...args,
              droppableContainers: args.droppableContainers.filter((container) =>
                itemIds.includes(String(container.id)),
              ),
            });
            if (closest.length > 0) {
              overId = closest[0].id;
            }
          }
        }
        lastOverIdRef.current = overId;
        return [{ id: overId }];
      }
      return lastOverIdRef.current != null ? [{ id: lastOverIdRef.current }] : [];
    },
    [activeColumns, laneId],
  );

  function handleDragStart({ active }: DragStartEvent) {
    suppressClickRef.current = true;
    setActiveId(String(active.id));
    setPreview(serverColumns);
    setOverColumn(findColumn(serverColumns, active.id));
    lastOverIdRef.current = null;
  }

  function handleDragOver({ active, over }: DragOverEvent) {
    if (!over) {
      setOverColumn(null);
      return;
    }
    const toName = resolveColumn(laneId, activeColumns, over.id);
    setOverColumn(toName);
    const fromName = findColumn(activeColumns, active.id);
    if (!fromName || !toName || fromName === toName) {
      return;
    }
    setPreview((current) => moveBetweenColumns(current ?? serverColumns, active.id, over.id));
  }

  function handleDragEnd({ active, over }: DragEndEvent) {
    const draggedId = String(active.id);
    const fromName = findColumn(serverColumns, draggedId);
    const toName = over ? resolveColumn(laneId, activeColumns, over.id) : null;
    setActiveId(null);
    setOverColumn(null);
    lastOverIdRef.current = null;
    if (!over || !fromName || !toName) {
      setPreview(null);
      return;
    }
    const task = serverColumns[fromName].find((entry) => entry.id === draggedId);
    if (!task) {
      setPreview(null);
      return;
    }
    // Resolve the insertion index against the server board, not the live
    // preview: over a card inserts before it, over the column body lands at
    // the tail. The backend reads to_index as the post-removal index.
    const overKey = String(over.id);
    const toColumnItems = serverColumns[toName];
    let toIndex: number;
    if (overKey === laneColumnDroppableId(laneId, toName)) {
      toIndex = toColumnItems.length;
    } else if (overKey === draggedId) {
      if (toName === fromName) {
        setPreview(null);
        return;
      }
      toIndex = toColumnItems.length;
    } else {
      const overIndex = toColumnItems.findIndex((entry) => entry.id === overKey);
      if (overIndex < 0) {
        setPreview(null);
        return;
      }
      toIndex = overIndex;
    }
    const fromIndex = serverColumns[fromName].findIndex((entry) => entry.id === draggedId);
    // The backend's to_index spans the WHOLE target section, not the lane's
    // filtered subset — translate through the full kanban board order.
    const overTaskId =
      overKey === laneColumnDroppableId(laneId, toName) || overKey === draggedId
        ? null
        : overKey;
    const globalSection = (kanbanSections ?? []).find(
      (entry) => entry.name === LANE_SECTIONS[toName],
    );
    const globalToIndex = laneDropToGlobalIndex(
      globalSection?.tasks,
      serverColumns[toName],
      draggedId,
      overTaskId,
    );
    if (toName === fromName) {
      const finalIndex = Math.min(toIndex, toColumnItems.length - 1);
      if (finalIndex === fromIndex) {
        setPreview(null);
        return;
      }
      // Hold the new order in the preview until the refetch lands (no
      // snap-back flash); the insertion index mirrors post-removal semantics.
      const reordered = serverColumns[fromName].filter((entry) => entry.id !== draggedId);
      reordered.splice(Math.min(toIndex, reordered.length), 0, task);
      setPreview({ ...serverColumns, [fromName]: reordered });
    }
    moveCard.mutate(
      {
        // Id-first addressing: the task id is URL-safe, unlike titles with '/'.
        cardRef: task.id || task.title,
        targetSection: LANE_SECTIONS[toName],
        toIndex: globalToIndex,
        etag: kanbanEtag,
      },
      {
        onSuccess: (result) => {
          notifications.show({
            color: 'green',
            title: '已移动',
            message: `已移动到 ${result.data.section || LANE_SECTIONS[toName]}。`,
          });
        },
        onError: (error) => {
          setPreview(null);
          handleLaneMutationError(error, '移动失败', onRefresh);
        },
      },
    );
  }

  function handleDragCancel() {
    setActiveId(null);
    setPreview(null);
    setOverColumn(null);
    lastOverIdRef.current = null;
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={collisionDetection}
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragEnd={handleDragEnd}
      onDragCancel={handleDragCancel}
    >
      <ScrollArea>
        <Group align="flex-start" wrap="nowrap" gap="sm" pb="xs">
          {(['queue', 'doing'] as const).map((column) => (
            <LaneColumn
              key={column}
              laneId={laneId}
              column={column}
              title={column === 'queue' ? 'Queue' : 'Doing'}
              tasks={activeColumns[column]}
              highlighted={overColumn === column && findColumn(serverColumns, activeId ?? '') !== column}
              quickAdd={
                column === 'queue' && quickAdd ? (
                  <QuickAddInput
                    laneId={laneId}
                    pending={quickAdd.pending}
                    onSubmit={quickAdd.onSubmit}
                  />
                ) : undefined
              }
            >
              {activeColumns[column].map((task) => (
                <SortableTaskCard
                  key={task.id}
                  task={task}
                  disabled={dragDisabled}
                  selected={selectedTaskId === task.id}
                  onSelect={onSelectTask}
                  suppressClickRef={suppressClickRef}
                />
              ))}
              {column === 'queue' &&
                someday.map((task) => (
                  <Box key={task.id} onClick={() => onSelectTask(task.id)} style={{ cursor: 'pointer' }}>
                    <TaskCardBody
                      task={task}
                      someday
                      selected={selectedTaskId === task.id}
                      actionPending={dragDisabled}
                      today={today}
                      onPromoteQueue={() => promoteSomeday(task, 'queue')}
                      onMarkDone={() => promoteSomeday(task, 'done')}
                    />
                  </Box>
                ))}
            </LaneColumn>
          ))}
        </Group>
      </ScrollArea>
      <DragOverlay>
        {activeTask ? (
          <div style={{ width: 252, cursor: 'grabbing' }}>
            <TaskCardBody task={activeTask} selected={selectedTaskId === activeTask.id} />
          </div>
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}

/**
 * 删除计划 confirm modal: type-the-name guard (逐字) + 「同时删除未完成的周卡」
 * (default on) + 「记入大事记」 (default off), with a consequence preview
 * (打卡历史保留,plan_id 仍可追溯;Done 周卡留作历史). 422
 * `habit_plan_delete_confirm_mismatch` lands as an inline field error.
 */
export function DeleteHabitPlanModal({
  profile,
  plan,
  opened,
  onClose,
}: {
  profile: string;
  plan: HabitPlan;
  opened: boolean;
  onClose: () => void;
}) {
  const remove = useDeleteHabitPlan(profile);
  const [confirmTitle, setConfirmTitle] = useState('');
  const [deleteOpenCards, setDeleteOpenCards] = useState(true);
  const [recordChronicle, setRecordChronicle] = useState(false);
  const confirmed = confirmTitle === plan.title;

  const close = () => {
    setConfirmTitle('');
    setDeleteOpenCards(true);
    setRecordChronicle(false);
    remove.reset();
    onClose();
  };

  const runDelete = () => {
    remove.mutate(
      {
        planId: plan.id,
        body: {
          confirm_title: confirmTitle,
          delete_open_cards: deleteOpenCards,
          record_chronicle: recordChronicle,
        },
      },
      {
        onSuccess: (result) => {
          notifications.show({
            color: 'green',
            title: '计划已删除',
            message:
              `「${plan.title}」已删除` +
              (result.cards_removed
                ? `,同时移除 ${result.cards_removed} 张未完成的周卡;打卡历史保留。`
                : ';打卡历史保留。'),
          });
          close();
        },
      },
    );
  };

  const mismatch =
    remove.error instanceof ApiError &&
    remove.error.status === 422 &&
    remove.error.code === 'habit_plan_delete_confirm_mismatch';

  return (
    <Modal
      opened={opened}
      onClose={close}
      title={`删除计划 · ${plan.title}`}
      data-testid={`delete-habit-plan-modal-${plan.id}`}
    >
      <Stack gap="sm">
        <Alert color="red" title="后果预告" data-testid={`delete-habit-plan-preview-${plan.id}`}>
          打卡历史保留(plan_id 仍可追溯);已完成的周卡保留为历史。
          {deleteOpenCards ? '仍在 Queue/Doing 的周卡将一并移除。' : '未完成的周卡将保留在看板中。'}
          此操作不可撤销。
        </Alert>
        <TextInput
          label={`输入计划名「${plan.title}」以确认`}
          placeholder={plan.title}
          value={confirmTitle}
          onChange={(event) => setConfirmTitle(event.currentTarget.value)}
          error={mismatch ? '计划名不匹配,请逐字输入。' : undefined}
          data-testid={`delete-habit-plan-confirm-title-${plan.id}`}
        />
        <Checkbox
          label="同时删除未完成的周卡(Queue/Doing 中的计划周卡一并移除)"
          checked={deleteOpenCards}
          onChange={(event) => setDeleteOpenCards(event.currentTarget.checked)}
          data-testid={`delete-habit-plan-delete-cards-${plan.id}`}
        />
        <Checkbox
          label="记入大事记(chronicle 追加 habit_plan.deleted 条目)"
          checked={recordChronicle}
          onChange={(event) => setRecordChronicle(event.currentTarget.checked)}
          data-testid={`delete-habit-plan-record-chronicle-${plan.id}`}
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
            data-testid={`delete-habit-plan-confirm-${plan.id}`}
          >
            永久删除
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}

/**
 * 阶段计划 readout for lanes whose case links a habit with an active phase
 * plan: plan title + 起止 + progress line (W 周进度 + 第 N/M 天 for daily
 * plans + 打卡天数 + 完成率) + completion bar + the task list — daily plans
 * show 今日任务(第 N 天)(空 = 「今日休息/自由安排」), weekly-only plans the
 * current week's tasks (read-only — the actionable checkboxes live on the
 * generated weekly kanban cards). Each card carries a 删除计划 affordance
 * opening the type-the-name confirm modal. Shares the cached active-plans
 * query with the 日课栏.
 */
export function HabitPlanSection({ profile, plans }: { profile: string; plans: HabitPlan[] }) {
  const [deletePlan, setDeletePlan] = useState<HabitPlan | null>(null);
  if (plans.length === 0) {
    return null;
  }
  return (
    <Stack
      gap="sm"
      data-testid="habit-plan-section"
      style={{
        border: `1px solid ${boardPalette.border}`,
        borderRadius: 8,
        padding: '8px 10px',
        background: boardPalette.groundSoft,
      }}
    >
      {plans.map((plan) => {
        const daily = planHasDaily(plan);
        const todayReadout = daily ? planTodayTasks(plan) : null;
        const currentWeek = Math.max(plan.current_week ?? 0, 1);
        const weekTasks = daily
          ? []
          : ((plan.weekly_tasks ?? []).find((week) => week.week === plan.current_week)?.tasks ??
            []);
        const rate = Math.round((plan.completion_rate ?? 0) * 100);
        return (
          <Stack key={plan.id} gap={4} data-testid={`habit-plan-card-${plan.id}`}>
            <Group gap="xs" wrap="nowrap" justify="space-between">
              <Group gap="xs" wrap="wrap" style={{ minWidth: 0 }}>
                <Text size="xs" fw={700} style={{ color: boardPalette.goldText, letterSpacing: 2 }}>
                  阶段计划
                </Text>
                <Text size="sm" fw={600} style={{ color: boardPalette.titleText }}>
                  {plan.title}
                </Text>
                <Text size="xs" style={{ color: boardPalette.dim }}>
                  {plan.start_date} ~ {plan.end_date}
                </Text>
                <Text size="xs" style={{ color: boardPalette.goldText }}>
                  {planProgressLabel(plan)}
                </Text>
              </Group>
              <ActionIcon
                variant="subtle"
                size="sm"
                color="red"
                aria-label={`删除计划 ${plan.title}`}
                onClick={() => setDeletePlan(plan)}
                data-testid={`habit-plan-delete-open-${plan.id}`}
              >
                <IconTrash size={13} />
              </ActionIcon>
            </Group>
            <Progress
              value={rate}
              size="sm"
              color="brand"
              data-testid={`habit-plan-progress-${plan.id}`}
            />
            {todayReadout && (
              <Stack gap={2} data-testid={`habit-plan-today-tasks-${plan.id}`}>
                <Text size="xs" style={{ color: boardPalette.dim }}>
                  {todayReadout.label}
                </Text>
                {todayReadout.restDay ? (
                  <Text
                    size="xs"
                    style={{ color: boardPalette.dim }}
                    pl="sm"
                    data-testid={`habit-plan-rest-day-${plan.id}`}
                  >
                    今日休息/自由安排
                  </Text>
                ) : (
                  todayReadout.tasks.map((task, index) => (
                    <Text key={index} size="xs" style={{ color: boardPalette.text }} pl="sm">
                      · {task}
                    </Text>
                  ))
                )}
              </Stack>
            )}
            {weekTasks.length > 0 && (
              <Stack gap={2} data-testid={`habit-plan-week-tasks-${plan.id}`}>
                <Text size="xs" style={{ color: boardPalette.dim }}>
                  本周任务(W{currentWeek}):
                </Text>
                {weekTasks.map((task, index) => (
                  <Text key={index} size="xs" style={{ color: boardPalette.text }} pl="sm">
                    · {task}
                  </Text>
                ))}
              </Stack>
            )}
            <Text size="xs" style={{ color: boardPalette.dim }}>
              每周任务已生成周卡进入看板 Queue 列,勾选态以周卡为准。
            </Text>
          </Stack>
        );
      })}
      {deletePlan && (
        <DeleteHabitPlanModal
          profile={profile}
          plan={deletePlan}
          opened={deletePlan !== null}
          onClose={() => setDeletePlan(null)}
        />
      )}
    </Stack>
  );
}

/** One project swimlane: header + Queue/Doing DnD + someday badge cards. */
export function ProjectLane({
  profile,
  project,
  kanbanEtag,
  kanbanSections,
  projectBoardEtag,
  today = '',
  selectedTaskId,
  onSelectTask,
  onEditProject,
  onRefresh,
}: {
  profile: string;
  project: ProjectsBoardProject;
  kanbanEtag: string;
  kanbanSections: KanbanSection[] | undefined;
  /** project-board.yaml ETag for the quick-add case-task endpoint. */
  projectBoardEtag: string;
  /** Board's today (yyyy-mm-dd); drives the 到期 someday badge. */
  today?: string;
  selectedTaskId: string;
  onSelectTask: (taskId: string) => void;
  onEditProject: (projectId: string) => void;
  onRefresh: () => void;
}) {
  const milestones = project.milestones ?? [];
  const milestoneDone = milestones.reduce((sum, m) => sum + (m.done_count ?? 0), 0);
  const milestoneTotal = milestones.reduce((sum, m) => sum + (m.total_count ?? 0), 0);
  const addTask = useAddProjectTask(profile);
  // 阶段计划: active habit plans bound to this case's habit (shared cache
  // with the 日课栏 — one fetch serves both).
  const plansQuery = useActiveHabitPlans(profile);
  const lanePlans = useMemo(
    () =>
      project.habit_id ? activePlansForHabit(plansQuery.data ?? [], project.habit_id) : [],
    [plansQuery.data, project.habit_id],
  );
  const quickAdd = {
    pending: addTask.isPending,
    onSubmit: (title: string) =>
      addTask.mutate(
        {
          caseId: project.id,
          body: { title, section: 'Queue', milestone_id: '', context: '', date: '' },
          etag: projectBoardEtag,
        },
        {
          onSuccess: (result) => {
            notifications.show({ color: 'green', title: '已添加', message: `「${title}」已进入 Queue。` });
            // ≤1-click rule kept: the card exists with just a title, but the
            // detail card opens right away so edits land in context (Esc /
            // click-away costs nothing when the title was enough).
            const createdId = result?.card?.id;
            if (createdId) {
              onSelectTask(createdId);
            }
          },
          onError: (error) => handleLaneMutationError(error, '添加失败', onRefresh),
        },
      ),
  };
  return (
    <Stack
      gap="sm"
      p="sm"
      data-testid={`project-lane-${project.id}`}
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
            style={{ borderColor: boardPalette.border, color: boardPalette.goldText }}
          >
            {KIND_LABELS[project.kind ?? ''] ?? project.kind}
          </Badge>
          <Badge
            size="sm"
            variant="outline"
            style={{ borderColor: boardPalette.border, color: boardPalette.dim }}
          >
            {PROJECT_STATUS_LABELS[project.status ?? ''] ?? project.status}
          </Badge>
          {milestoneTotal > 0 && (
            <Text size="xs" style={{ color: boardPalette.dim }}>
              里程碑 {milestoneDone}/{milestoneTotal}
            </Text>
          )}
          {project.last_activity && (
            <Text size="xs" style={{ color: boardPalette.dim }}>
              最近 {project.last_activity}
            </Text>
          )}
        </Group>
        <Group gap="xs" wrap="nowrap" style={{ flexShrink: 0 }}>
          <Text size="xs" style={{ color: boardPalette.goldText }} data-testid={`done-count-${project.id}`}>
            Done · {project.done_count}
            {(project.archived_done_count ?? 0) > 0 ? `（含归档 ${project.archived_done_count}）` : ''} ▸
          </Text>
          <ActionIcon
            variant="subtle"
            size="sm"
            aria-label={`编辑项目 ${project.title || project.id}`}
            onClick={() => onEditProject(project.id)}
            style={{ color: boardPalette.dim }}
          >
            <IconEdit size={14} />
          </ActionIcon>
        </Group>
      </Group>
      <HabitPlanSection profile={profile} plans={lanePlans} />
      <TaskLaneDnd
        profile={profile}
        laneId={project.id}
        queue={project.queue ?? []}
        doing={project.doing ?? []}
        someday={project.someday ?? []}
        kanbanEtag={kanbanEtag}
        kanbanSections={kanbanSections}
        today={today}
        selectedTaskId={selectedTaskId}
        onSelectTask={onSelectTask}
        onRefresh={onRefresh}
        quickAdd={quickAdd}
      />
    </Stack>
  );
}

/** The dashed-gold 未归属任务 lane for tasks owned by no project. */
export function UnassignedLane({
  profile,
  tasks,
  kanbanEtag,
  kanbanSections,
  today = '',
  selectedTaskId,
  onSelectTask,
  onRefresh,
}: {
  profile: string;
  tasks: ProjectsBoardTask[];
  kanbanEtag: string;
  kanbanSections: KanbanSection[] | undefined;
  /** Board's today (yyyy-mm-dd); drives the 到期 someday badge. */
  today?: string;
  selectedTaskId: string;
  onSelectTask: (taskId: string) => void;
  onRefresh: () => void;
}) {
  const addCard = useAddKanbanCard(profile);
  const quickAdd = {
    pending: addCard.isPending,
    onSubmit: (title: string) =>
      addCard.mutate(
        { body: { title, section: 'Queue', context: '' }, etag: kanbanEtag },
        {
          onSuccess: (result) => {
            notifications.show({ color: 'green', title: '已添加', message: `「${title}」已进入 Queue。` });
            // Same auto-open as the project lanes: land in the detail card.
            const createdId = result?.data?.card?.id;
            if (createdId) {
              onSelectTask(createdId);
            }
          },
          onError: (error) => handleLaneMutationError(error, '添加失败', onRefresh),
        },
      ),
  };
  return (
    <Stack
      gap="sm"
      p="sm"
      data-testid="unassigned-lane"
      style={{
        background: boardPalette.groundSoft,
        border: `1px dashed ${boardPalette.gold}`,
        borderRadius: 12,
      }}
    >
      <Group gap="xs">
        <Text fw={600} style={{ color: boardPalette.goldText }}>
          未归属任务
        </Text>
        <Text size="xs" style={{ color: boardPalette.dim }}>
          没有归属项目的任务,可在详情卡中变更归属
        </Text>
      </Group>
      <TaskLaneDnd
        profile={profile}
        laneId="unassigned"
        queue={tasks.filter((task) => task.column === 'queue')}
        doing={tasks.filter((task) => task.column === 'doing')}
        someday={tasks.filter((task) => task.column === 'someday')}
        kanbanEtag={kanbanEtag}
        kanbanSections={kanbanSections}
        today={today}
        selectedTaskId={selectedTaskId}
        onSelectTask={onSelectTask}
        onRefresh={onRefresh}
        quickAdd={quickAdd}
      />
    </Stack>
  );
}
