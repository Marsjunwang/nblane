import { Badge, Button, Group, Stack, Text, Tooltip } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconCheck } from '@tabler/icons-react';

import { useAddCheckin } from '../../api/hooks';
import type { ProjectsBoardHabit } from '../../api/types';
import { boardPalette } from './palette';

/**
 * Habit check-in lane (持续型项目). Renders from the aggregation's top-level
 * habits[] (current ISO week dots + streak + totals); the habit<->project
 * link only decides WHERE the lane shows up, never the data source.
 */
export function HabitLane({
  profile,
  habit,
}: {
  profile: string;
  habit: ProjectsBoardHabit;
}) {
  const checkin = useAddCheckin(profile);
  const todayDone = (habit.week ?? []).some((day) => day.done && !day.future && isToday(day.date));

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
      gap="xs"
      p="sm"
      data-testid={`habit-lane-${habit.id}`}
      style={{
        background: boardPalette.groundSoft,
        border: `1px solid ${boardPalette.border}`,
        borderRadius: 12,
      }}
    >
      <Group justify="space-between" wrap="nowrap">
        <Group gap="xs" wrap="wrap" style={{ minWidth: 0 }}>
          <Text fw={600} style={{ color: boardPalette.titleText }}>
            {habit.title || habit.id}
          </Text>
          <Badge
            size="sm"
            variant="outline"
            style={{ borderColor: boardPalette.habitGreen, color: boardPalette.habitGreen }}
          >
            持续型 · habit
          </Badge>
          <Text size="xs" style={{ color: boardPalette.dim }}>
            连续 {habit.streak ?? 0} 天
            {habit.last_checkin ? ` · 上次 ${habit.last_checkin.slice(5)}` : ''} · 累计{' '}
            {habit.total_checkins ?? 0} 次
          </Text>
        </Group>
        <Group gap="sm" wrap="nowrap" style={{ flexShrink: 0 }}>
          <Group gap={6} data-testid={`habit-week-${habit.id}`}>
            {(habit.week ?? []).map((day) => (
              <Tooltip key={day.date} label={day.date} withArrow>
                <span
                  data-testid={`habit-dot-${habit.id}-${day.date}`}
                  data-done={day.done ? 'true' : 'false'}
                  style={{
                    display: 'inline-block',
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    background: day.done ? boardPalette.habitGreen : 'transparent',
                    border: `1.5px solid ${
                      day.done
                        ? boardPalette.habitGreen
                        : day.future
                          ? 'rgba(176, 167, 140, 0.4)'
                          : boardPalette.dim
                    }`,
                    opacity: day.future ? 0.5 : 1,
                  }}
                />
              </Tooltip>
            ))}
          </Group>
          <Button
            size="compact-sm"
            variant={todayDone ? 'subtle' : 'light'}
            color="green"
            leftSection={<IconCheck size={14} />}
            loading={checkin.isPending}
            onClick={runCheckin}
            data-testid={`checkin-button-${habit.id}`}
          >
            {todayDone ? '再打卡' : '打卡'}
          </Button>
        </Group>
      </Group>
    </Stack>
  );
}

function isToday(date: string): boolean {
  const now = new Date();
  const pad = (value: number) => String(value).padStart(2, '0');
  return date === `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}
