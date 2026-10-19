import { ActionIcon, Anchor, Badge, Box, Button, Center, Group, Loader, ScrollArea, Stack, Text, Tooltip } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconCheck, IconExternalLink, IconRefresh } from '@tabler/icons-react';
import { useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';

import {
  useAddCheckin,
  useDoneKanbanCard,
  useKanbanBoard,
  useProjectsBoard,
} from '../api/hooks';

/** How often the always-on-top window refreshes on its own. */
export const MINI_REFRESH_MS = 60_000;

function errorText(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

/**
 * Compact view for the always-on-top 小窗 (MiniWindowButton): what is in
 * Doing, and today's habit check-ins. No app shell, no 3D starmap, so it
 * stays light when left open all day.
 */
export function MiniPage() {
  const { name = '' } = useParams();
  const kanban = useKanbanBoard(name);
  const board = useProjectsBoard(name);
  const done = useDoneKanbanCard(name);
  const checkin = useAddCheckin(name);

  // Global queries do not refetch on focus; a window left open all day must.
  const refresh = () => {
    void kanban.refetch();
    void board.refetch();
  };
  useAutoRefresh(refresh);

  if (kanban.isPending || board.isPending) {
    return (
      <Center h="100vh">
        <Loader size="sm" />
      </Center>
    );
  }

  const doing =
    kanban.data?.board.sections?.find((section) => section.name === 'Doing')?.tasks?.filter((task) => !task.done) ?? [];
  const today = board.data?.board.today ?? '';
  const habits = (board.data?.board.habits ?? []).filter((habit) => !('archived' in habit && habit.archived));
  const fullHref = `/p/${encodeURIComponent(name)}/projects`;

  const markDone = (cardRef: string, title: string) =>
    done.mutate(
      { cardRef, etag: kanban.data?.etag ?? '' },
      {
        onSuccess: () => notifications.show({ color: 'green', message: `「${title}」已完成。` }),
        onError: (error) => notifications.show({ color: 'red', title: '标记失败', message: errorText(error) }),
      },
    );

  const checkIn = (habitId: string, title: string) =>
    checkin.mutate(
      { habit: habitId, date: '', summary: '', note: '' },
      {
        onSuccess: () => notifications.show({ color: 'green', message: `${title} 今日已打卡。` }),
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
          <Tooltip label="刷新" withArrow>
            <ActionIcon variant="subtle" size="sm" aria-label="刷新" onClick={refresh}>
              <IconRefresh size={14} />
            </ActionIcon>
          </Tooltip>
          <Tooltip label="在完整页面打开" withArrow>
            <ActionIcon
              component="a"
              href={fullHref}
              target="nblane-main"
              variant="subtle"
              size="sm"
              aria-label="在完整页面打开"
            >
              <IconExternalLink size={14} />
            </ActionIcon>
          </Tooltip>
        </Group>
      </Group>

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
              <Stack gap={6}>
                {doing.map((task) => (
                  <Group key={task.id || task.title} gap="xs" wrap="nowrap" justify="space-between">
                    <Text size="sm" lineClamp={2} style={{ flex: 1 }}>
                      {task.title}
                    </Text>
                    <Tooltip label="标记完成" withArrow>
                      <ActionIcon
                        variant="light"
                        color="green"
                        size="sm"
                        aria-label={`标记完成：${task.title}`}
                        loading={done.isPending && done.variables?.cardRef === (task.id || task.title)}
                        onClick={() => markDone(task.id || task.title, task.title)}
                      >
                        <IconCheck size={14} />
                      </ActionIcon>
                    </Tooltip>
                  </Group>
                ))}
              </Stack>
            )}
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
              <Stack gap={6}>
                {habits.map((habit) => {
                  const title = habit.title || habit.id;
                  const doneToday = (habit.week ?? []).some((day) => day.done && day.date === today);
                  return (
                    <Group key={habit.id} gap="xs" wrap="nowrap" justify="space-between">
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
                      ) : (
                        <Button
                          size="compact-xs"
                          variant="light"
                          aria-label={`打卡：${title}`}
                          loading={checkin.isPending && checkin.variables?.habit === habit.id}
                          onClick={() => checkIn(habit.id, title)}
                        >
                          打卡
                        </Button>
                      )}
                    </Group>
                  );
                })}
              </Stack>
            )}
          </Box>
        </Stack>
      </ScrollArea>

      <Anchor href={fullHref} target="nblane-main" size="xs" c="dimmed">
        计划内打卡、拖动任务等操作请在项目页进行
      </Anchor>
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
