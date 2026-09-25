// 新建阶段计划 — per-habit phase-plan creation (POST .../habit-plans), opened
// from the habit row's lifecycle menu (新建计划…). Fields: 计划名 (default
// 「<习惯> · 28天计划」), 起止日期 (default board today → +27 days), and one
// multiline block per week (N = ceil(days/7), one task per line, blank lines
// dropped). Every week needs ≥1 task before submit unlocks. The create hook
// owns invalidation (habit-plans / projects-board / kanban); on success the
// toast names the generated weekly Queue cards, on 422 the server message
// (e.g. invalid_weekly_tasks) lands in the inline error alert.

import { Button, Group, Modal, Stack, Text, TextInput, Textarea } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { useEffect, useState } from 'react';

import { useCreateHabitPlan } from '../../api/hooks';
import type { ProjectsBoardHabit } from '../../api/types';
import { MutationErrorAlert } from '../ConflictAlert';
import { daysBetween, shiftDate } from './timelineMath';

const DEFAULT_DAYS = 28;

/** One task per line: trim, drop blank lines. */
function splitTasks(raw: string): string[] {
  return raw
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean);
}

/** Inclusive week count for [start, end]; 0 when the range is invalid. */
export function planWeekCount(start: string, end: string): number {
  const days = daysBetween(start, end) + 1;
  return days > 0 ? Math.ceil(days / 7) : 0;
}

export function NewHabitPlanModal({
  profile,
  habit,
  today,
  opened,
  onClose,
}: {
  profile: string;
  habit: ProjectsBoardHabit;
  /** Board today — anchors the default start/end dates. */
  today: string;
  opened: boolean;
  onClose: () => void;
}) {
  const create = useCreateHabitPlan(profile);
  const [title, setTitle] = useState('');
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  /** Raw textarea content per week (resized as the date range moves). */
  const [weekTexts, setWeekTexts] = useState<string[]>([]);
  const habitTitle = habit.title || habit.id;

  // Reset the form each time the modal opens.
  useEffect(() => {
    if (!opened) {
      return;
    }
    setTitle(`${habitTitle} · ${DEFAULT_DAYS}天计划`);
    setStart(today);
    setEnd(shiftDate(today, DEFAULT_DAYS - 1));
    setWeekTexts([]);
    create.reset();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opened, today, habit.id]);

  const weekCount = planWeekCount(start, end);
  // Resize the week blocks as the date range moves, preserving typed text.
  useEffect(() => {
    setWeekTexts((prev) => Array.from({ length: weekCount }, (_, index) => prev[index] ?? ''));
  }, [weekCount]);

  const weeklyTasks = weekTexts.map(splitTasks);
  const invalidRange = weekCount === 0;
  const weeksReady = weeklyTasks.length > 0 && weeklyTasks.every((tasks) => tasks.length > 0);
  const valid = !invalidRange && title.trim().length > 0 && weeksReady;

  const submit = () => {
    if (!valid) {
      return;
    }
    create.mutate(
      {
        title: title.trim(),
        habit_id: habit.id,
        start_date: start,
        end_date: end,
        generate_weekly_cards: true,
        weekly_tasks: weeklyTasks.map((tasks, index) => ({ week: index + 1, tasks })),
      },
      {
        onSuccess: (result) => {
          const cards = result.kanban_card_ids?.length ?? 0;
          notifications.show({
            color: 'green',
            title: '阶段计划已创建',
            message:
              `「${title.trim()}」已创建` +
              (cards > 0 ? `,周卡已生成到看板 Queue(${cards} 张)。` : '。'),
          });
          onClose();
        },
      },
    );
  };

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      centered
      title={`新建阶段计划 · ${habitTitle}`}
      size="lg"
    >
      <Stack gap="sm" data-testid={`new-habit-plan-modal-${habit.id}`}>
        <Text size="sm" c="dimmed">
          按周拆解任务;创建后每周生成一张周卡进入看板 Queue 列,打卡可计入该计划。
        </Text>
        <TextInput
          label="计划名"
          value={title}
          onChange={(event) => setTitle(event.currentTarget.value)}
          data-testid={`habit-plan-title-${habit.id}`}
        />
        <Group grow align="flex-start">
          <TextInput
            label="开始日期"
            type="date"
            value={start}
            onChange={(event) => setStart(event.currentTarget.value)}
            data-testid={`habit-plan-start-${habit.id}`}
          />
          <TextInput
            label="结束日期"
            type="date"
            value={end}
            onChange={(event) => setEnd(event.currentTarget.value)}
            error={invalidRange ? '结束日期需不早于开始日期。' : undefined}
            data-testid={`habit-plan-end-${habit.id}`}
          />
        </Group>
        {!invalidRange && (
          <Stack gap="xs">
            <Text size="xs" c="dimmed">
              每周任务(共 {weekCount} 周,一行一个任务,每周至少一条)
            </Text>
            {weekTexts.map((text, index) => (
              <Textarea
                key={index}
                label={`第 ${index + 1} 周`}
                autosize
                minRows={2}
                placeholder={'一行一个任务\n例如:晨跑 3 次'}
                value={text}
                onChange={(event) => {
                  const next = event.currentTarget.value;
                  setWeekTexts((prev) =>
                    prev.map((value, at) => (at === index ? next : value)),
                  );
                }}
                data-testid={`habit-plan-week-${habit.id}-${index + 1}`}
              />
            ))}
          </Stack>
        )}
        <MutationErrorAlert error={create.error} title="创建计划失败" />
        <Group justify="flex-end">
          <Button variant="subtle" onClick={onClose}>
            取消
          </Button>
          <Button
            onClick={submit}
            loading={create.isPending}
            disabled={!valid}
            data-testid={`habit-plan-submit-${habit.id}`}
          >
            创建计划
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}
