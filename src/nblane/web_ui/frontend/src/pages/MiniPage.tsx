import { ActionIcon, Anchor, Badge, Box, Button, Center, Checkbox, Group, Indicator, Loader, Menu, ScrollArea, Stack, Text, TextInput, Tooltip, UnstyledButton } from '@mantine/core';
import { useDisclosure, useLocalStorage } from '@mantine/hooks';
import { notifications } from '@mantine/notifications';
import { IconAlertTriangle, IconCheck, IconChevronDown, IconChevronRight, IconExternalLink, IconPlayerPlay, IconPlus, IconRefresh } from '@tabler/icons-react';
import { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';

import { ApiError } from '../api/client';
import {
  useActiveHabitPlans,
  useAIExceptions,
  useAddCheckin,
  useAddKanbanCard,
  useDoneKanbanCard,
  useKanbanBoard,
  useMoveKanbanCard,
  usePatchKanbanCard,
  useProjectsBoard,
} from '../api/hooks';
import type { HabitPlan } from '../api/types';
import { AIExceptionDrawer } from '../components/AIExceptionDrawer';
import { checkinPlansForHabit, planBadgeLabel, planHasDaily, planTodayTasks } from '../components/projects/habitPlans';
import { byDue, dueState, reapplyToggle, toggleAt, type MiniTodo } from './miniTasks';

/** How often the always-on-top window refreshes on its own. */
export const MINI_REFRESH_MS = 60_000;
/** AI exception badge poll in the 小窗: it stays open all day, so check less often. */
export const MINI_EXCEPTIONS_POLL_MS = 120_000;
/** Queue items shown in the 小窗; the rest stay on the projects page. */
export const QUEUE_PREVIEW = 3;

function errorText(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

const DUE_LABEL = { overdue: '已逾期', today: '今天到期' } as const;

/**
 * Compact view for the always-on-top 小窗 (MiniWindowButton): Doing tasks
 * with their todo checklist, and today's habits with plan-aware check-in.
 * No app shell, no 3D starmap, so it stays light when left open all day.
 */
export function MiniPage() {
  const { name = '' } = useParams();
  const kanban = useKanbanBoard(name);
  const board = useProjectsBoard(name);
  const plans = useActiveHabitPlans(name);
  const done = useDoneKanbanCard(name);
  const patchCard = usePatchKanbanCard(name);
  const checkin = useAddCheckin(name);
  const [expanded, setExpanded] = useLocalStorage<string[]>({ key: `nblane-mini-open:${name}`, defaultValue: [] });
  // Optimistic todo lists per card while a save is in flight.
  const [pendingTodos, setPendingTodos] = useState<Record<string, MiniTodo[]>>({});
  const addCard = useAddKanbanCard(name);
  const moveCard = useMoveKanbanCard(name);
  const [queueOpen, setQueueOpen] = useLocalStorage<boolean>({ key: `nblane-mini-queue:${name}`, defaultValue: false });
  const [draft, setDraft] = useState('');
  // Same query as the main window's top-bar badge, polled every 2 minutes.
  const exceptions = useAIExceptions(name, MINI_EXCEPTIONS_POLL_MS);
  const exceptionCount = exceptions.data?.total ?? 0;
  const [exceptionsOpened, exceptionsDrawer] = useDisclosure(false);

  // Global queries do not refetch on focus; a window left open all day must.
  const refresh = () => {
    void kanban.refetch();
    void board.refetch();
    void plans.refetch();
  };
  useAutoRefresh(refresh);

  if (kanban.isPending || board.isPending) {
    return (
      <Center h="100vh">
        <Loader size="sm" />
      </Center>
    );
  }

  const today = board.data?.board.today ?? '';
  const doing = byDue(
    kanban.data?.board.sections?.find((section) => section.name === 'Doing')?.tasks?.filter((task) => !task.done) ?? [],
    (task) => dueState(task.planned_end, today),
  );
  const queue = kanban.data?.board.sections?.find((section) => section.name === 'Queue')?.tasks?.filter((task) => !task.done) ?? [];
  const habits = (board.data?.board.habits ?? []).filter((habit) => !('archived' in habit && habit.archived));
  const activePlans = plans.data ?? [];
  const fullHref = `/p/${encodeURIComponent(name)}/projects`;
  const cardRefOf = (task: { id: string; title: string }) => task.id || task.title;
  const serverTodos = (cardRef: string): MiniTodo[] => {
    const task = doing.find((item) => cardRefOf(item) === cardRef);
    return (task?.todos ?? []).map((todo) => ({ text: todo.text, done: todo.done ?? false }));
  };
  const todosOf = (cardRef: string) => pendingTodos[cardRef] ?? serverTodos(cardRef);
  const clearPending = (cardRef: string) =>
    setPendingTodos((current) => {
      const { [cardRef]: _dropped, ...rest } = current;
      return rest;
    });

  const toggleExpanded = (cardRef: string) =>
    setExpanded((current) => (current.includes(cardRef) ? current.filter((ref) => ref !== cardRef) : [...current, cardRef]));

  const toggleTodo = async (cardRef: string, index: number) => {
    const before = todosOf(cardRef);
    const target = before[index];
    if (!target) return;
    const next = toggleAt(before, index);
    setPendingTodos((current) => ({ ...current, [cardRef]: next }));
    const save = (todos: MiniTodo[], etag: string) => patchCard.mutateAsync({ cardRef, body: { todos }, etag });
    try {
      await save(next, kanban.data?.etag ?? '');
    } catch (error) {
      if (!(error instanceof ApiError) || error.status !== 412) {
        clearPending(cardRef);
        notifications.show({ color: 'red', title: '清单保存失败', message: errorText(error) });
        return;
      }
      // The list changed elsewhere: PATCH replaces it whole, so never write
      // our stale copy. Flip the same item (by text) in the fresh list.
      const fresh = await kanban.refetch();
      const freshTask = fresh.data?.board.sections
        ?.flatMap((section) => section.tasks ?? [])
        .find((task) => cardRefOf(task) === cardRef);
      const retried = reapplyToggle(
        (freshTask?.todos ?? []).map((todo) => ({ text: todo.text, done: todo.done ?? false })),
        target,
      );
      if (!retried || !fresh.data) {
        clearPending(cardRef);
        notifications.show({ color: 'yellow', message: '清单在别处改过了，已刷新为最新内容。' });
        return;
      }
      try {
        setPendingTodos((current) => ({ ...current, [cardRef]: retried }));
        await save(retried, fresh.data.etag);
      } catch (retryError) {
        notifications.show({ color: 'red', title: '清单保存失败', message: errorText(retryError) });
      }
    }
    // Hold the optimistic list until the refetch lands, so it never flashes back.
    await kanban.refetch();
    clearPending(cardRef);
  };

  const markDone = (cardRef: string, title: string) =>
    done.mutate(
      { cardRef, etag: kanban.data?.etag ?? '' },
      {
        onSuccess: () => notifications.show({ color: 'green', message: `「${title}」已完成。` }),
        onError: (error) => notifications.show({ color: 'red', title: '标记失败', message: errorText(error) }),
      },
    );

  const startTask = (cardRef: string, title: string) =>
    moveCard.mutate(
      { cardRef, targetSection: 'Doing', etag: kanban.data?.etag ?? '' },
      {
        onSuccess: () => notifications.show({ color: 'green', message: `「${title}」已开始。` }),
        onError: (error) => notifications.show({ color: 'red', title: '开始失败', message: errorText(error) }),
      },
    );

  const quickAdd = () => {
    const title = draft.trim();
    if (!title || addCard.isPending) return;
    addCard.mutate(
      { body: { title, section: 'Queue', context: '' }, etag: kanban.data?.etag ?? '' },
      {
        onSuccess: () => {
          setDraft('');
          notifications.show({ color: 'green', message: `「${title}」已加入 Queue。` });
        },
        // Keep the typed title so a retry needs no retyping.
        onError: (error) => notifications.show({ color: 'red', title: '添加失败', message: errorText(error) }),
      },
    );
  };

  const checkIn = (habitId: string, title: string, plan?: HabitPlan) =>
    checkin.mutate(
      { habit: habitId, date: '', summary: '', note: '', ...(plan ? { plan_id: plan.id } : {}) },
      {
        onSuccess: () =>
          notifications.show({
            color: 'green',
            message: plan ? `${title} 今日已打卡，已计入「${plan.title}」。` : `${title} 今日已打卡。`,
          }),
        onError: (error) => notifications.show({ color: 'red', title: '打卡失败', message: errorText(error) }),
      },
    );

  return (
    <Stack gap="sm" p="sm" h="100vh" data-testid="mini-page">
      <Group justify="space-between" wrap="nowrap">
        <Text size="sm" fw={600} truncate>
          {name} · 今日
        </Text>
        <Group gap={4} wrap="nowrap">
          {(exceptionCount > 0 || exceptions.isError) && (
            <Tooltip label="AI 异常" withArrow>
              <Indicator
                inline
                size={14}
                color="red"
                offset={3}
                label={exceptions.isError ? '!' : exceptionCount > 99 ? '99+' : exceptionCount}
              >
                <ActionIcon
                  variant="subtle"
                  color="red"
                  size="sm"
                  aria-label={exceptions.isError ? 'AI 异常列表加载失败' : `AI 异常 ${exceptionCount} 条`}
                  onClick={exceptionsDrawer.open}
                >
                  <IconAlertTriangle size={14} />
                </ActionIcon>
              </Indicator>
            </Tooltip>
          )}
          <Tooltip label="刷新" withArrow>
            <ActionIcon variant="subtle" size="sm" aria-label="刷新" onClick={refresh}>
              <IconRefresh size={14} />
            </ActionIcon>
          </Tooltip>
          <Tooltip label="在完整页面打开" withArrow>
            <ActionIcon component="a" href={fullHref} target="nblane-main" variant="subtle" size="sm" aria-label="在完整页面打开">
              <IconExternalLink size={14} />
            </ActionIcon>
          </Tooltip>
        </Group>
      </Group>

      <TextInput
        size="xs"
        placeholder="添加任务到 Queue，回车保存"
        aria-label="添加任务到 Queue"
        value={draft}
        onChange={(event) => setDraft(event.currentTarget.value)}
        onKeyDown={(event) => {
          // Enter while an IME is composing (pinyin) only confirms the word.
          if (event.key === 'Enter' && !event.nativeEvent.isComposing) {
            event.preventDefault();
            quickAdd();
          }
        }}
        rightSection={addCard.isPending ? <Loader size={12} /> : <IconPlus size={14} />}
      />

      <ScrollArea style={{ flex: 1 }} offsetScrollbars>
        <Stack gap="md">
          <Box component="section" aria-labelledby="mini-doing">
            <Text id="mini-doing" size="xs" c="dimmed" mb={6}>
              进行中 {doing.length > 0 && `· ${doing.length}`}
            </Text>
            {kanban.isError ? (
              <Text size="xs" c="red">看板加载失败：{errorText(kanban.error)}</Text>
            ) : doing.length === 0 ? (
              <Text size="xs" c="dimmed">Doing 里没有任务。</Text>
            ) : (
              <Stack gap={8}>
                {doing.map((task) => {
                  const cardRef = cardRefOf(task);
                  const todos = todosOf(cardRef);
                  const doneCount = todos.filter((todo) => todo.done).length;
                  const allDone = todos.length > 0 && doneCount === todos.length;
                  const open = expanded.includes(cardRef);
                  const due = dueState(task.planned_end, today);
                  const subtasks = task.subtasks ?? [];
                  return (
                    <Box key={cardRef}>
                      <Group gap="xs" wrap="nowrap" justify="space-between" align="flex-start">
                        <UnstyledButton
                          onClick={() => toggleExpanded(cardRef)}
                          aria-expanded={todos.length > 0 || subtasks.length > 0 ? open : undefined}
                          aria-label={`${open ? '收起' : '展开'}清单：${task.title}`}
                          style={{ flex: 1, minWidth: 0 }}
                        >
                          <Group gap={4} wrap="nowrap" align="flex-start">
                            {todos.length > 0 || subtasks.length > 0 ? (
                              open ? <IconChevronDown size={14} style={{ marginTop: 3, flexShrink: 0 }} /> : <IconChevronRight size={14} style={{ marginTop: 3, flexShrink: 0 }} />
                            ) : (
                              <Box w={14} style={{ flexShrink: 0 }} />
                            )}
                            <Text size="sm" lineClamp={2}>
                              {task.title}
                            </Text>
                          </Group>
                          <Group gap={4} pl={18} mt={2}>
                            {due && (
                              <Badge size="xs" color={due === 'overdue' ? 'red' : 'orange'} variant="light">
                                {DUE_LABEL[due]}
                              </Badge>
                            )}
                            {todos.length > 0 && (
                              <Text size="xs" c={allDone ? 'green' : 'dimmed'}>
                                清单 {doneCount}/{todos.length}
                              </Text>
                            )}
                          </Group>
                        </UnstyledButton>
                        <Tooltip label={allDone ? '清单已完成，标记任务完成' : '标记完成'} withArrow>
                          <ActionIcon
                            variant={allDone ? 'filled' : 'light'}
                            color="green"
                            size="sm"
                            aria-label={`标记完成：${task.title}`}
                            loading={done.isPending && done.variables?.cardRef === cardRef}
                            onClick={() => markDone(cardRef, task.title)}
                          >
                            <IconCheck size={14} />
                          </ActionIcon>
                        </Tooltip>
                      </Group>
                      {open && (
                        <Stack gap={4} pl={18} mt={6}>
                          {todos.map((todo, index) => (
                            <Checkbox
                              key={`${index}-${todo.text}`}
                              size="xs"
                              label={todo.text}
                              checked={todo.done}
                              onChange={() => void toggleTodo(cardRef, index)}
                              styles={{ label: { textDecoration: todo.done ? 'line-through' : undefined, opacity: todo.done ? 0.6 : 1 } }}
                            />
                          ))}
                          {subtasks.map((subtask, index) => (
                            <Text key={`sub-${index}`} size="xs" c="dimmed" td={subtask.done ? 'line-through' : undefined}>
                              子任务：{subtask.title}
                            </Text>
                          ))}
                        </Stack>
                      )}
                    </Box>
                  );
                })}
              </Stack>
            )}
          </Box>

          <Box component="section" aria-labelledby="mini-queue">
            <UnstyledButton id="mini-queue" onClick={() => setQueueOpen(!queueOpen)} aria-expanded={queueOpen}>
              <Group gap={4} wrap="nowrap">
                {queueOpen ? <IconChevronDown size={12} /> : <IconChevronRight size={12} />}
                <Text size="xs" c="dimmed">
                  接下来 · Queue {queue.length}
                </Text>
              </Group>
            </UnstyledButton>
            {queueOpen &&
              (queue.length === 0 ? (
                <Text size="xs" c="dimmed" mt={6}>
                  Queue 里没有任务。
                </Text>
              ) : (
                <Stack gap={6} mt={6}>
                  {queue.slice(0, QUEUE_PREVIEW).map((task) => {
                    const cardRef = cardRefOf(task);
                    const due = dueState(task.planned_end, today);
                    return (
                      <Group key={cardRef} gap="xs" wrap="nowrap" justify="space-between">
                        <Group gap={6} wrap="nowrap" miw={0} style={{ flex: 1 }}>
                          <Text size="sm" truncate>
                            {task.title}
                          </Text>
                          {due && (
                            <Badge size="xs" color={due === 'overdue' ? 'red' : 'orange'} variant="light">
                              {DUE_LABEL[due]}
                            </Badge>
                          )}
                        </Group>
                        <Button
                          size="compact-xs"
                          variant="light"
                          leftSection={<IconPlayerPlay size={12} />}
                          aria-label={`开始：${task.title}`}
                          loading={moveCard.isPending && moveCard.variables?.cardRef === cardRef}
                          onClick={() => startTask(cardRef, task.title)}
                        >
                          开始
                        </Button>
                      </Group>
                    );
                  })}
                  {queue.length > QUEUE_PREVIEW && (
                    <Anchor href={fullHref} target="nblane-main" size="xs" c="dimmed">
                      还有 {queue.length - QUEUE_PREVIEW} 条，在项目页查看
                    </Anchor>
                  )}
                </Stack>
              ))}
          </Box>

          <Box component="section" aria-labelledby="mini-habits">
            <Text id="mini-habits" size="xs" c="dimmed" mb={6}>
              日课
            </Text>
            {board.isError ? (
              <Text size="xs" c="red">日课加载失败：{errorText(board.error)}</Text>
            ) : habits.length === 0 ? (
              <Text size="xs" c="dimmed">还没有日课。</Text>
            ) : (
              <Stack gap={8}>
                {habits.map((habit) => {
                  const title = habit.title || habit.id;
                  const doneToday = (habit.week ?? []).some((day) => day.done && day.date === today);
                  const eligible = checkinPlansForHabit(activePlans, habit.id, today);
                  const dailyPlan = eligible.find(planHasDaily);
                  const todayTasks = dailyPlan ? planTodayTasks(dailyPlan) : null;
                  const pending = checkin.isPending && checkin.variables?.habit === habit.id;
                  return (
                    <Box key={habit.id}>
                      <Group gap="xs" wrap="nowrap" justify="space-between">
                        <Group gap={6} wrap="nowrap" miw={0}>
                          <Text size="sm" truncate>
                            {title}
                          </Text>
                          {habit.streak > 0 && (
                            <Badge size="xs" variant="light" aria-label={`连续 ${habit.streak} 天`}>
                              {habit.streak} 天
                            </Badge>
                          )}
                        </Group>
                        {doneToday ? (
                          <Text size="xs" c="green">已打卡</Text>
                        ) : eligible.length > 1 ? (
                          <Menu position="bottom-end" withinPortal={false}>
                            <Menu.Target>
                              <Button size="compact-xs" variant="light" loading={pending} aria-label={`打卡：${title}`} rightSection={<IconChevronDown size={12} />}>
                                打卡
                              </Button>
                            </Menu.Target>
                            <Menu.Dropdown>
                              <Menu.Label>计入哪个计划</Menu.Label>
                              {eligible.map((plan) => (
                                <Menu.Item key={plan.id} onClick={() => checkIn(habit.id, title, plan)}>
                                  {plan.title}
                                </Menu.Item>
                              ))}
                              <Menu.Item onClick={() => checkIn(habit.id, title)}>不计入计划</Menu.Item>
                            </Menu.Dropdown>
                          </Menu>
                        ) : (
                          <Button
                            size="compact-xs"
                            variant="light"
                            aria-label={`打卡：${title}`}
                            loading={pending}
                            onClick={() => checkIn(habit.id, title, eligible[0])}
                          >
                            打卡
                          </Button>
                        )}
                      </Group>
                      {eligible.length === 1 && (
                        <Text size="xs" c="dimmed" mt={2}>
                          {planBadgeLabel(eligible[0])}
                        </Text>
                      )}
                      {todayTasks && (
                        <Text size="xs" c="dimmed" mt={2}>
                          {todayTasks.restDay ? '今日休息 / 自由安排' : `今日：${todayTasks.tasks.join('、')}`}
                        </Text>
                      )}
                    </Box>
                  );
                })}
              </Stack>
            )}
          </Box>
        </Stack>
      </ScrollArea>

      <Anchor href={fullHref} target="nblane-main" size="xs" c="dimmed">
        编辑任务、增删清单、拖动排序请在项目页进行
      </Anchor>
      <AIExceptionDrawer
        profile={name}
        opened={exceptionsOpened}
        onClose={exceptionsDrawer.close}
        linkTarget="nblane-main"
        size="100%"
        pollMs={MINI_EXCEPTIONS_POLL_MS}
      />
    </Stack>
  );
}

/** Refetch on a timer and whenever the window regains focus or visibility. */
function useAutoRefresh(refresh: () => void) {
  const latest = useRef(refresh);
  latest.current = refresh;
  useEffect(() => {
    const run = () => latest.current();
    const onVisible = () => {
      if (document.visibilityState === 'visible') run();
    };
    const id = window.setInterval(run, MINI_REFRESH_MS);
    window.addEventListener('focus', run);
    document.addEventListener('visibilitychange', onVisible);
    return () => {
      window.clearInterval(id);
      window.removeEventListener('focus', run);
      document.removeEventListener('visibilitychange', onVisible);
    };
  }, []);
}
