// 铭文详情卡 — task detail overlay for the unified /projects page. Opens on
// `?task=<id>`, reuses the InscriptionCard shell, and carries the action row:
// section moves, planned-date scheduling (timeline-drag fallback), habit
// check-in, crystallize hand-off, 归属变更 (PATCH project_id — the only
// cross-lane assignment path; board DnD stays in-lane), an edit mode
// (编辑) for title/context/why/project_id/tags via PATCH /kanban/cards/{ref}
// under the kanban.md ETag, and the「删除任务」danger action (inline confirm
// + optional 记入大事记) via DELETE /kanban/cards/{ref}. {ref} is the task id
// (URL-safe, survives titles containing '/'), with title as the fallback.
// Planned dates stay
// in the 排期 row — edit mode deliberately does not duplicate scheduling.

import {
  ActionIcon,
  Alert,
  Badge,
  Button,
  Checkbox,
  Group,
  Modal,
  Select,
  Stack,
  Text,
  Textarea,
  TextInput,
} from '@mantine/core';
import { DateInput } from '@mantine/dates';
import { notifications } from '@mantine/notifications';
import { IconArrowRight, IconPencil, IconSparkles, IconTrash, IconX } from '@tabler/icons-react';
import 'dayjs/locale/zh-cn';
import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';

import { ApiError } from '../../api/client';
import {
  useAddCheckin,
  useDeleteKanbanCard,
  useDoneKanbanCard,
  useMoveKanbanCard,
  usePatchKanbanCard,
  useScheduleKanbanCard,
} from '../../api/hooks';
import type {
  KanbanCardPatchRequest,
  ProjectsBoardHabit,
  ProjectsBoardProject,
  ProjectsBoardTask,
} from '../../api/types';
import { MutationErrorAlert } from '../ConflictAlert';
import { InscriptionCard, InscriptionRow } from '../InscriptionCard';
import { handleLaneMutationError } from './ProjectLane';
import { boardPalette } from './palette';

const COLUMN_LABELS: Record<string, string> = {
  queue: '队列',
  doing: '进行中',
  someday: '以后再说',
  done: '已完成',
};

function daysSince(start: string, today: string): number {
  const from = new Date(`${start}T00:00:00`);
  const to = new Date(`${today}T00:00:00`);
  return Math.max(0, Math.round((to.getTime() - from.getTime()) / 86_400_000));
}

// Debounce window for checklist PATCHes: toggles/add/removes batch into one
// full-replace write against kanban.md.
const TODO_SAVE_DELAY_MS = 400;

/** Card-ref for the /kanban/cards/{ref} endpoints: the stable task id
 * (URL-safe even when the title contains '/'), falling back to the title
 * for cards that never got an id persisted. */
function cardRefOf(task: ProjectsBoardTask): string {
  return task.id || task.title;
}

interface TodoDraft {
  text: string;
  done: boolean;
}

/** Checklist section of the detail card: toggle / add / delete with an
 * optimistic local list and a debounced full-replace PATCH. */
function TodoChecklist({
  task,
  kanbanEtag,
  patchCard,
  onError,
}: {
  task: ProjectsBoardTask;
  kanbanEtag: string;
  patchCard: ReturnType<typeof usePatchKanbanCard>;
  onError: (title: string) => (error: unknown) => void;
}) {
  const [todos, setTodos] = useState<TodoDraft[]>(() =>
    (task.todos ?? []).map((todo) => ({ text: todo.text, done: todo.done ?? false })),
  );
  const [newTodo, setNewTodo] = useState('');
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Re-seed only when a different task opens; same-task refetches must not
  // clobber an in-flight optimistic edit (the local list is what we sent).
  useEffect(() => {
    setTodos((task.todos ?? []).map((todo) => ({ text: todo.text, done: todo.done ?? false })));
    setNewTodo('');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [task.id]);

  useEffect(
    () => () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    },
    [],
  );

  const commit = (next: TodoDraft[]) => {
    setTodos(next);
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }
    timerRef.current = setTimeout(() => {
      timerRef.current = null;
      patchCard.mutate(
        {
          cardRef: cardRefOf(task),
          body: { todos: next.map((todo) => ({ text: todo.text, done: todo.done })) },
          etag: kanbanEtag,
        },
        { onError: onError('清单保存失败') },
      );
    }, TODO_SAVE_DELAY_MS);
  };

  const toggle = (index: number) =>
    commit(todos.map((todo, i) => (i === index ? { ...todo, done: !todo.done } : todo)));
  const remove = (index: number) => commit(todos.filter((_, i) => i !== index));
  const add = () => {
    const text = newTodo.trim();
    if (!text) {
      return;
    }
    setNewTodo('');
    commit([...todos, { text, done: false }]);
  };

  return (
    <Stack gap={4} data-testid="todo-section">
      {todos.map((todo, index) => (
        <Group key={`${index}-${todo.text}`} gap="xs" wrap="nowrap" data-testid={`todo-item-${index}`}>
          <Checkbox
            size="xs"
            checked={todo.done}
            onChange={() => toggle(index)}
            aria-label={`勾选 ${todo.text}`}
            data-testid={`todo-toggle-${index}`}
          />
          <Text
            size="sm"
            style={{
              flex: 1,
              textDecoration: todo.done ? 'line-through' : undefined,
              color: todo.done ? boardPalette.dim : undefined,
            }}
          >
            {todo.text}
          </Text>
          <ActionIcon
            size="xs"
            variant="subtle"
            aria-label={`删除 ${todo.text}`}
            data-testid={`todo-delete-${index}`}
            onClick={() => remove(index)}
            style={{ color: boardPalette.dim }}
          >
            <IconX size={12} />
          </ActionIcon>
        </Group>
      ))}
      <TextInput
        size="xs"
        placeholder="添加清单项,回车确认"
        aria-label="添加清单项"
        value={newTodo}
        onChange={(event) => setNewTodo(event.currentTarget.value)}
        onKeyDown={(event) => {
          if (event.key === 'Enter') {
            event.preventDefault();
            add();
          }
        }}
        data-testid="todo-add-input"
      />
    </Stack>
  );
}

export function TaskDetailCard({
  profile,
  task,
  project,
  projects,
  habits,
  today,
  kanbanEtag,
  onClose,
  onRefresh,
}: {
  profile: string;
  /** null = closed. */
  task: ProjectsBoardTask | null;
  /** Owning lane (null for unassigned tasks). */
  project: ProjectsBoardProject | null;
  /** All active lanes, for the 归属变更 picker. */
  projects: ProjectsBoardProject[];
  habits: ProjectsBoardHabit[];
  today: string;
  kanbanEtag: string;
  onClose: () => void;
  onRefresh: () => void;
}) {
  const moveCard = useMoveKanbanCard(profile);
  const doneCard = useDoneKanbanCard(profile);
  const scheduleCard = useScheduleKanbanCard(profile);
  const patchCard = usePatchKanbanCard(profile);
  const deleteCard = useDeleteKanbanCard(profile);
  const checkin = useAddCheckin(profile);

  const [plannedStart, setPlannedStart] = useState('');
  const [plannedEnd, setPlannedEnd] = useState('');
  const [assignTo, setAssignTo] = useState<string>('');
  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editContext, setEditContext] = useState('');
  const [editWhy, setEditWhy] = useState('');
  const [editProjectId, setEditProjectId] = useState('');
  const [editTags, setEditTags] = useState('');
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [recordChronicle, setRecordChronicle] = useState(false);

  // Re-seed the local editors whenever a different task opens (or the same
  // task's server state lands after a mutation).
  useEffect(() => {
    setPlannedStart(task?.planned_start ?? '');
    setPlannedEnd(task?.planned_end ?? '');
    setAssignTo(task?.project_id ?? project?.id ?? '');
    setEditing(false);
    setConfirmingDelete(false);
    setRecordChronicle(false);
  }, [task?.id, task?.planned_start, task?.planned_end, task?.project_id, project?.id]);

  if (!task) {
    return null;
  }

  const mutating =
    moveCard.isPending ||
    doneCard.isPending ||
    scheduleCard.isPending ||
    patchCard.isPending ||
    deleteCard.isPending ||
    checkin.isPending;
  const firstError =
    moveCard.error ??
    doneCard.error ??
    scheduleCard.error ??
    patchCard.error ??
    deleteCard.error ??
    checkin.error;
  const ambiguous =
    firstError instanceof ApiError &&
    firstError.status === 422 &&
    firstError.code === 'kanban_card_ambiguous';

  // Habit check-in entry point: the owning lane's explicit habit link.
  const habitId = project?.habit_id || habits.find((h) => h.project_id === project?.id)?.id || '';
  const habit = habits.find((h) => h.id === habitId);

  const onError = (title: string) => (error: unknown) =>
    handleLaneMutationError(error, title, onRefresh);

  const runMove = (targetSection: string) =>
    moveCard.mutate(
      { cardRef: cardRefOf(task), targetSection, etag: kanbanEtag },
      { onError: onError('移动失败') },
    );

  const runDone = () =>
    doneCard.mutate(
      { cardRef: cardRefOf(task), etag: kanbanEtag },
      {
        // The card closes itself on refetch (the task leaves the live lanes),
        // so the confirmation must fire from the mutation callback.
        onSuccess: () =>
          notifications.show({
            color: 'green',
            title: '已标记完成',
            message: `「${task.title}」已入 Done。`,
          }),
        onError: onError('操作失败'),
      },
    );

  const runSchedule = (start: string, end: string) =>
    scheduleCard.mutate(
      { cardRef: cardRefOf(task), body: { planned_start: start, planned_end: end }, etag: kanbanEtag },
      { onError: onError('排期失败') },
    );

  const runAssign = (projectId: string) => {
    setAssignTo(projectId);
    patchCard.mutate(
      { cardRef: cardRefOf(task), body: { project_id: projectId }, etag: kanbanEtag },
      { onError: onError('归属变更失败') },
    );
  };

  const runCheckin = () =>
    checkin.mutate(
      { habit: habitId, related_kanban: [task.title], date: '', summary: task.title, note: '' },
      { onError: onError('打卡失败') },
    );

  // 删除任务: irreversible — the hook invalidates board/kanban on success,
  // then the card closes itself (the task no longer exists).
  const runDelete = () =>
    deleteCard.mutate(
      {
        cardRef: cardRefOf(task),
        body: { record_chronicle: recordChronicle },
        etag: kanbanEtag,
      },
      { onSuccess: onClose, onError: onError('删除失败') },
    );

  const startedDays = task.started_on && today ? daysSince(task.started_on, today) : null;
  const tags = (task.tags ?? '')
    .split(/[,\s]+/)
    .map((tag) => tag.trim())
    .filter(Boolean);

  const startEdit = () => {
    setEditTitle(task.title);
    setEditContext(task.context ?? '');
    setEditWhy(task.why ?? '');
    setEditProjectId(task.project_id ?? '');
    setEditTags(tags.join(', '));
    setEditing(true);
  };

  // PATCH carries only the fields that actually changed (None keeps server
  // side; "" clears context/why/project_id).
  const trimmedEditTitle = editTitle.trim();
  const nextTags = editTags
    .split(/[,，\s]+/)
    .map((tag) => tag.trim())
    .filter(Boolean);
  const editBody: KanbanCardPatchRequest = {};
  if (trimmedEditTitle && trimmedEditTitle !== task.title) {
    editBody.title = trimmedEditTitle;
  }
  if (editContext !== (task.context ?? '')) {
    editBody.context = editContext.trim();
  }
  if (editWhy !== (task.why ?? '')) {
    editBody.why = editWhy.trim();
  }
  if (editProjectId !== (task.project_id ?? '')) {
    editBody.project_id = editProjectId;
  }
  if (nextTags.join(', ') !== tags.join(', ')) {
    editBody.tags = nextTags;
  }
  const editDirty = Object.keys(editBody).length > 0;

  const runSaveEdit = () =>
    patchCard.mutate(
      { cardRef: cardRefOf(task), body: editBody, etag: kanbanEtag },
      {
        onSuccess: () => setEditing(false),
        onError: onError('保存失败'),
      },
    );

  return (
    <Modal
      opened
      onClose={onClose}
      centered
      size="lg"
      withCloseButton={false}
      styles={{
        content: { background: 'transparent' },
        body: { padding: 0 },
      }}
    >
      <InscriptionCard
        testId="task-detail-card"
        title={editing ? `编辑 · ${task.title}` : task.title}
        aside={
          <Group gap={4} wrap="nowrap">
            {!editing && (
              <Button
                size="compact-sm"
                variant="subtle"
                leftSection={<IconPencil size={13} />}
                onClick={startEdit}
                data-testid="detail-edit"
              >
                编辑
              </Button>
            )}
            <Button size="compact-sm" variant="subtle" onClick={onClose} aria-label="关闭详情">
              关闭
            </Button>
          </Group>
        }
      >
        <Stack gap="xs">
          <InscriptionRow label="状态">
            <Group gap="xs">
              <Badge
                size="sm"
                variant="outline"
                style={{ borderColor: boardPalette.gold, color: boardPalette.goldText }}
              >
                {COLUMN_LABELS[task.column] ?? task.column}
              </Badge>
              {startedDays !== null && task.column === 'doing' && (
                <Text size="sm">已进行 {startedDays} 天</Text>
              )}
            </Group>
          </InscriptionRow>
          {(task.started_on || task.completed_on) && (
            <InscriptionRow label="日期">
              {task.started_on ? `开始于 ${task.started_on}` : ''}
              {task.started_on && task.completed_on ? ' · ' : ''}
              {task.completed_on ? `完成于 ${task.completed_on}` : ''}
            </InscriptionRow>
          )}
          <InscriptionRow label="排期">
            <Group gap="xs" wrap="nowrap">
              {/* Mantine DateInput: native type=date renders the browser
                  locale's mm/dd/yyyy for en-locale browsers; DateInput pins
                  the display to valueFormat regardless of browser locale. */}
              <DateInput
                size="xs"
                aria-label="排期开始"
                valueFormat="YYYY-MM-DD"
                placeholder="YYYY-MM-DD"
                locale="zh-cn"
                clearable
                value={plannedStart || null}
                onChange={(value) => setPlannedStart(value ?? '')}
              />
              <Text size="sm">→</Text>
              <DateInput
                size="xs"
                aria-label="排期结束"
                valueFormat="YYYY-MM-DD"
                placeholder="YYYY-MM-DD"
                locale="zh-cn"
                clearable
                value={plannedEnd || null}
                onChange={(value) => setPlannedEnd(value ?? '')}
              />
              <Button
                size="compact-sm"
                variant="light"
                disabled={mutating || (!plannedStart && !plannedEnd)}
                onClick={() => runSchedule(plannedStart, plannedEnd)}
                data-testid="schedule-save"
              >
                保存排期
              </Button>
              {(task.planned_start || task.planned_end) && (
                <Button
                  size="compact-sm"
                  variant="subtle"
                  disabled={mutating}
                  onClick={() => runSchedule('', '')}
                  data-testid="schedule-clear"
                >
                  清除
                </Button>
              )}
            </Group>
          </InscriptionRow>
          <InscriptionRow label="TODO">
            <TodoChecklist
              key={task.id}
              task={task}
              kanbanEtag={kanbanEtag}
              patchCard={patchCard}
              onError={onError}
            />
          </InscriptionRow>
          {editing ? (
            <>
              <InscriptionRow label="标题">
                <TextInput
                  size="xs"
                  aria-label="编辑标题"
                  value={editTitle}
                  onChange={(event) => setEditTitle(event.currentTarget.value)}
                  error={trimmedEditTitle ? undefined : '标题不能为空'}
                  data-testid="edit-title"
                />
              </InscriptionRow>
              <InscriptionRow label="上下文">
                <Textarea
                  size="xs"
                  autosize
                  minRows={2}
                  aria-label="编辑上下文"
                  value={editContext}
                  onChange={(event) => setEditContext(event.currentTarget.value)}
                  data-testid="edit-context"
                />
              </InscriptionRow>
              <InscriptionRow label="为什么">
                <Textarea
                  size="xs"
                  autosize
                  minRows={2}
                  aria-label="编辑为什么"
                  value={editWhy}
                  onChange={(event) => setEditWhy(event.currentTarget.value)}
                  data-testid="edit-why"
                />
              </InscriptionRow>
              <InscriptionRow label="归属">
                <Select
                  size="xs"
                  aria-label="编辑归属"
                  data={[
                    { value: '', label: '未归属' },
                    ...projects.map((lane) => ({
                      value: lane.id,
                      label: lane.title || lane.id,
                    })),
                  ]}
                  value={editProjectId}
                  onChange={(value) => setEditProjectId(value ?? '')}
                  data-testid="edit-project"
                />
              </InscriptionRow>
              <InscriptionRow label="标签">
                <TextInput
                  size="xs"
                  aria-label="编辑标签"
                  placeholder="逗号或空格分隔"
                  value={editTags}
                  onChange={(event) => setEditTags(event.currentTarget.value)}
                  data-testid="edit-tags"
                />
              </InscriptionRow>
            </>
          ) : (
            <>
              {task.context && <InscriptionRow label="上下文">{task.context}</InscriptionRow>}
              {task.why && <InscriptionRow label="为什么">{task.why}</InscriptionRow>}
              <InscriptionRow label="归属">
                <Group gap="xs" wrap="nowrap">
                  <Select
                    size="xs"
                    aria-label="归属变更"
                    data={[
                      { value: '', label: '未归属' },
                      ...projects.map((lane) => ({
                        value: lane.id,
                        label: lane.title || lane.id,
                      })),
                    ]}
                    value={assignTo}
                    onChange={(value) => runAssign(value ?? '')}
                    disabled={mutating}
                    data-testid="assign-select"
                  />
                </Group>
              </InscriptionRow>
              {tags.length > 0 && (
                <InscriptionRow label="标签">
                  <Group gap={4}>
                    {tags.map((tag) => (
                      <Badge
                        key={tag}
                        size="sm"
                        variant="outline"
                        style={{ borderColor: boardPalette.border, color: boardPalette.dim }}
                      >
                        {tag}
                      </Badge>
                    ))}
                  </Group>
                </InscriptionRow>
              )}
            </>
          )}

          {ambiguous && (
            <Alert color="orange" title="存在重名卡片" data-testid="ambiguous-alert">
              看板中存在多张同名卡片,无法确定操作目标。请先在数据层(kanban.md)重命名重复卡片后再试。
            </Alert>
          )}
          {!ambiguous && (
            <MutationErrorAlert error={firstError} title="操作失败" onRefetch={onRefresh} />
          )}

          <Group gap="xs" mt="sm" wrap="wrap">
            {editing ? (
              <>
                <Button
                  size="compact-sm"
                  variant="light"
                  color="green"
                  disabled={mutating || !editDirty || !trimmedEditTitle}
                  loading={patchCard.isPending}
                  onClick={runSaveEdit}
                  data-testid="edit-save"
                >
                  保存修改
                </Button>
                <Button
                  size="compact-sm"
                  variant="subtle"
                  disabled={patchCard.isPending}
                  onClick={() => setEditing(false)}
                  data-testid="edit-cancel"
                >
                  取消
                </Button>
              </>
            ) : (
              <>
            {task.column !== 'doing' && (
              <Button
                size="compact-sm"
                variant="light"
                rightSection={<IconArrowRight size={14} />}
                disabled={mutating}
                onClick={() => runMove('Doing')}
              >
                移至 Doing
              </Button>
            )}
            {task.column !== 'queue' && (
              <Button
                size="compact-sm"
                variant="light"
                disabled={mutating}
                onClick={() => runMove('Queue')}
              >
                移至 Queue
              </Button>
            )}
            {!task.done && (
              <Button
                size="compact-sm"
                color="green"
                variant="light"
                disabled={mutating}
                onClick={runDone}
                data-testid="detail-done"
              >
                标记 Done
              </Button>
            )}
            {habit && (
              <Button
                size="compact-sm"
                color="green"
                variant="subtle"
                disabled={mutating}
                onClick={runCheckin}
                data-testid="detail-checkin"
              >
                打卡 · {habit.title || habit.id}
              </Button>
            )}
            <Button
              size="compact-sm"
              variant="outline"
              component={Link}
              to={`/p/${encodeURIComponent(profile)}/evidence?stage=crystallize`}
              leftSection={<IconSparkles size={14} />}
              data-testid="detail-crystallize"
            >
              结晶为证据
            </Button>
            {!confirmingDelete && (
              <Button
                size="compact-sm"
                variant="subtle"
                color="red"
                ml="auto"
                leftSection={<IconTrash size={14} />}
                disabled={mutating}
                onClick={() => {
                  setRecordChronicle(false);
                  setConfirmingDelete(true);
                }}
                data-testid="detail-delete"
              >
                删除任务
              </Button>
            )}
              </>
            )}
          </Group>

          {confirmingDelete && (
            <Alert
              color="red"
              variant="light"
              data-testid="delete-confirm"
              styles={{ message: { width: '100%' } }}
            >
              <Stack gap="xs">
                <Text size="sm">将删除任务「{task.title}」,不可恢复</Text>
                <Checkbox
                  size="xs"
                  label="记入大事记(chronicle 追加 task.deleted 条目)"
                  checked={recordChronicle}
                  onChange={(event) => setRecordChronicle(event.currentTarget.checked)}
                  data-testid="delete-record-chronicle"
                />
                <Group gap="xs">
                  <Button
                    size="compact-sm"
                    color="red"
                    variant="light"
                    loading={deleteCard.isPending}
                    onClick={runDelete}
                    data-testid="delete-confirm-button"
                  >
                    确认删除
                  </Button>
                  <Button
                    size="compact-sm"
                    variant="subtle"
                    disabled={deleteCard.isPending}
                    onClick={() => setConfirmingDelete(false)}
                    data-testid="delete-cancel"
                  >
                    取消
                  </Button>
                </Group>
              </Stack>
            </Alert>
          )}
        </Stack>
      </InscriptionCard>
    </Modal>
  );
}
