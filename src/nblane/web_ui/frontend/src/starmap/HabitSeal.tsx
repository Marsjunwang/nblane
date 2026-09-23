// 日课印 — the bottom-left seal on the home starmap (裁决2 双重居所:首页
// 左下). One line `日课 锻炼○ 学习●` — 空圈 = 未打卡,金点 = 已打卡 today;
// clicking a habit name posts today's check-in (L1: ≤1 次点击); hovering
// floats this week's seven dots.
//
// Composition: it balances the bottom-right →境态 toggle and sits beside the
// 星表「+」seal as part of the 裱边 layer (same seal aesthetic).
//
// Data: projects-board habits[] (useProjectsBoard). Justification — 单端点
// 原则: the backend folded habit data into the projects-board aggregation
// (docs/zh/dev/phase2-projects-hci.md 后端补件清单) and no lighter habits
// endpoint exists; react-query shares the cache with the /projects page, so
// the extra fetch happens at most once per profile visit.

import { Group, Tooltip } from '@mantine/core';
import { notifications } from '@mantine/notifications';

import { useAddCheckin, useProjectsBoard } from '../api/hooks';
import type { ProjectsBoardHabit } from '../api/types';

function SealWeekDots({ habit }: { habit: ProjectsBoardHabit }) {
  return (
    <Group gap={5} wrap="nowrap">
      {(habit.week ?? []).map((day) => (
        <span
          key={day.date}
          title={day.date}
          style={{
            display: 'inline-block',
            width: 9,
            height: 9,
            borderRadius: '50%',
            background: day.done ? '#dcae55' : 'transparent',
            border: `1px solid ${day.done ? '#dcae55' : 'rgba(232, 226, 210, 0.55)'}`,
            opacity: day.future ? 0.4 : 1,
          }}
        />
      ))}
      <span style={{ marginLeft: 6, fontSize: 11, opacity: 0.75 }}>
        连续 {habit.streak ?? 0} 天
      </span>
    </Group>
  );
}

export function HabitSeal({ profile }: { profile: string }) {
  const board = useProjectsBoard(profile);
  const checkin = useAddCheckin(profile);
  const habits = board.data?.board.habits ?? [];
  const today = board.data?.board.today ?? '';
  if (habits.length === 0) {
    return null;
  }

  const todayDone = (habit: ProjectsBoardHabit) =>
    (habit.week ?? []).some((day) => day.done && !day.future && day.date === today);

  const runCheckin = (habit: ProjectsBoardHabit) => {
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
    <div className="starmap-habit-seal" data-starmap-ui data-testid="habit-seal">
      <span className="starmap-habit-seal-label">日课</span>
      {habits.map((habit) => {
        const done = todayDone(habit);
        return (
          <Tooltip
            key={habit.id}
            label={<SealWeekDots habit={habit} />}
            withArrow
            position="top"
          >
            <button
              type="button"
              className="starmap-habit-seal-item"
              data-testid={`habit-seal-${habit.id}`}
              data-done={done ? 'true' : 'false'}
              disabled={checkin.isPending}
              onClick={() => runCheckin(habit)}
              aria-label={`日课打卡 ${habit.title || habit.id}`}
            >
              {habit.title || habit.id}
              <span className={`starmap-habit-seal-dot${done ? ' done' : ''}`}>
                {done ? '●' : '○'}
              </span>
            </button>
          </Tooltip>
        );
      })}
    </div>
  );
}
