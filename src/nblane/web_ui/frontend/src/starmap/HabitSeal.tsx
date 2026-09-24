// 日课印 (round-3 印章化, 王军规格): the bottom-left 裱边 cluster on the home
// starmap — a small vertical etched caption「日课」+ one 44×44 seal per habit.
// Glyph auto-picked from the habit name (文楷), with a curated map for common
// habits (炼/学/复/读/跑/坐/息). 白文 (etched moon-white) = not checked in
// today; 朱文 (cinnabar face, gold glyph, subtle gold glow) = checked.
// Click = today's check-in with a stamp-press micro-animation
// (reduced-motion aware); hover floats the slip (full name + streak + week
// dots); long-press/right-click a checked seal = 销印 — an inline confirm
// strip deletes today's LATEST check-in row (DELETE /checkins/{id}), and the
// seal falls back to 白文 once the board refetch lands.
//
// Data: projects-board habits[] (useProjectsBoard). 单端点原则: the backend
// folded habit data into the projects-board aggregation and no lighter habits
// endpoint exists; react-query shares the cache with the /projects page.
// 销印 addressing: habits[].recent_days[].checkin_ids (today's entry, last id).

import { useEffect, useRef, useState } from 'react';
import { Tooltip } from '@mantine/core';
import { notifications } from '@mantine/notifications';

import { useAddCheckin, useDeleteCheckin, useProjectsBoard } from '../api/hooks';
import type { ProjectsBoardHabit } from '../api/types';

/** 印面字: curated glyphs for common habits, else the title's first char. */
export function sealGlyph(habit: Pick<ProjectsBoardHabit, 'id' | 'title'>): string {
  const key = `${habit.id} ${habit.title}`.toLowerCase();
  if (/exercise|锻炼|健身/.test(key)) return '炼';
  if (/learning|学习/.test(key)) return '学';
  if (/康复|复健|recovery/.test(key)) return '复';
  if (/read|读书|阅读/.test(key)) return '读';
  if (/run|跑步/.test(key)) return '跑';
  if (/meditat|冥想|静坐/.test(key)) return '坐';
  if (/sleep|睡眠|作息/.test(key)) return '息';
  return Array.from(habit.title || habit.id)[0] ?? '课';
}

/**
 * 销印 target: today's LATEST check-in row id (most likely a mis-tap), from
 * recent_days[].checkin_ids. '' = the day is checked but carries no ids
 * (legacy rows) — the seal then refuses 销印 with a notice, same contract as
 * the /projects heatmap.
 */
export function todayCheckinId(
  habit: Pick<ProjectsBoardHabit, 'recent_days'>,
  today: string,
): string {
  const day = (habit.recent_days ?? []).find((entry) => entry.date === today);
  const ids = (day?.checkin_ids ?? []).filter((id) => id.length > 0);
  return ids.length > 0 ? ids[ids.length - 1] : '';
}

function SealSlip({
  habit,
  streak,
  done,
  today,
}: {
  habit: ProjectsBoardHabit;
  streak: number;
  done: boolean;
  today: string;
}) {
  return (
    <div style={{ maxWidth: 240 }}>
      <div style={{ fontSize: 14, marginBottom: 6 }}>{habit.title || habit.id}</div>
      <div style={{ display: 'flex', gap: 5, alignItems: 'center', marginBottom: 6 }}>
        {(habit.week ?? []).map((day) => {
          // 石刻化 dots (same vocabulary as the /projects week strip):
          // hollow 月白-35% ring / 泥金 fill, today ringed in thin gold.
          const isToday = day.date === today && !day.future;
          return (
            <span
              key={day.date}
              title={day.date}
              data-testid={`seal-slip-dot-${habit.id}-${day.date}`}
              data-done={day.done ? 'true' : 'false'}
              data-today={isToday ? 'true' : 'false'}
              style={{
                display: 'inline-block',
                width: 9,
                height: 9,
                borderRadius: '50%',
                boxSizing: 'border-box',
                background: day.done ? '#dcae55' : 'transparent',
                border: `1px solid ${day.done ? '#dcae55' : 'rgba(242, 237, 224, 0.35)'}`,
                boxShadow: isToday ? '0 0 0 1.5px #dcae55' : undefined,
                opacity: day.future ? 0.4 : 1,
              }}
            />
          );
        })}
      </div>
      <div style={{ fontSize: 12, opacity: 0.8 }}>连续 {streak} 天</div>
      <div style={{ fontSize: 11, opacity: 0.6, marginTop: 6 }}>
        {done ? '右键/长按 = 销印(撤销今日最近一次打卡)' : '点击印面 = 今日打卡'}
      </div>
    </div>
  );
}

export function HabitSeal({ profile }: { profile: string }) {
  const board = useProjectsBoard(profile);
  const checkin = useAddCheckin(profile);
  const deleteCheckin = useDeleteCheckin(profile);
  const habits = board.data?.board.habits ?? [];
  const today = board.data?.board.today ?? '';
  const [pressing, setPressing] = useState<string | null>(null);
  const [slipOpen, setSlipOpen] = useState<string | null>(null);
  /** Habit id whose seal is awaiting 销印 confirmation (inline strip). */
  const [unsealId, setUnsealId] = useState<string | null>(null);
  const pressTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  /** Set when a long-press fired so the trailing click does not check in. */
  const suppressClick = useRef(false);
  const coarse = useRef(
    typeof matchMedia !== 'undefined' && matchMedia('(pointer: coarse)').matches,
  );

  const unsealHabit = habits.find((habit) => habit.id === unsealId) ?? null;

  // Esc closes the 销印 confirm (the starmap's global Esc stays unaffected).
  useEffect(() => {
    if (!unsealId) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setUnsealId(null);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [unsealId]);

  if (habits.length === 0) {
    return null;
  }

  const todayDone = (habit: ProjectsBoardHabit) =>
    (habit.week ?? []).some((day) => day.done && !day.future && day.date === today);

  /** 销印 gesture (right-click / long-press) on a checked seal → inline confirm. */
  const requestUnseal = (habit: ProjectsBoardHabit) => {
    if (!todayDone(habit)) return;
    if (!todayCheckinId(habit, today)) {
      notifications.show({
        color: 'yellow',
        title: '销印',
        message: `${habit.title || habit.id} 今日打卡记录缺少 id,暂不可销印(可在项目页日课栏热力图核实)。`,
      });
      return;
    }
    setSlipOpen(null);
    setUnsealId(habit.id);
  };

  const runUnseal = () => {
    if (!unsealHabit) return;
    const habit = unsealHabit;
    const checkinId = todayCheckinId(habit, today);
    if (!checkinId) {
      setUnsealId(null);
      return;
    }
    deleteCheckin.mutate(
      { checkinId },
      {
        onSuccess: () => {
          notifications.show({
            color: 'green',
            title: '已销印',
            message: `${habit.title || habit.id} 今日最近一次打卡已删除。`,
          });
        },
        onError: (error) => {
          notifications.show({
            color: 'red',
            title: '销印失败',
            message: error instanceof Error ? error.message : String(error),
          });
        },
        onSettled: () => setUnsealId(null),
      },
    );
  };

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
      {unsealHabit && (
        <div
          className="starmap-habit-unseal"
          role="alertdialog"
          aria-label="销印确认"
          data-testid={`seal-unseal-${unsealHabit.id}`}
        >
          <span className="starmap-habit-unseal-text">
            销印「{unsealHabit.title || unsealHabit.id}」今日最近一次打卡?
          </span>
          <button
            type="button"
            className="starmap-habit-unseal-btn danger"
            disabled={deleteCheckin.isPending}
            onClick={runUnseal}
            data-testid={`seal-unseal-yes-${unsealHabit.id}`}
          >
            销印
          </button>
          <button
            type="button"
            className="starmap-habit-unseal-btn"
            onClick={() => setUnsealId(null)}
            data-testid={`seal-unseal-no-${unsealHabit.id}`}
          >
            取消
          </button>
        </div>
      )}
      <span className="starmap-habit-seal-caption" aria-hidden="true">
        <span>日</span>
        <span>课</span>
      </span>
      {habits.map((habit) => {
        const done = todayDone(habit);
        const id = habit.id;
        return (
          <Tooltip
            key={id}
            label={<SealSlip habit={habit} streak={habit.streak ?? 0} done={done} today={today} />}
            withArrow
            position="top"
            // While the 销印 confirm is up, hover slips would overlap it.
            disabled={unsealHabit !== null}
            opened={coarse.current ? slipOpen === id : undefined}
            events={{ hover: !coarse.current, focus: true, touch: false }}
          >
            <button
              type="button"
              className={`starmap-habit-stamp${pressing === id ? ' stamping' : ''}`}
              data-testid={`habit-seal-${id}`}
              data-done={done ? 'true' : 'false'}
              disabled={checkin.isPending || deleteCheckin.isPending}
              aria-label={`日课打卡 ${habit.title || habit.id}`}
              aria-pressed={done}
              onClick={() => {
                if (suppressClick.current) {
                  suppressClick.current = false;
                  return;
                }
                setPressing(id);
                window.setTimeout(() => setPressing(null), 380);
                runCheckin(habit);
              }}
              onContextMenu={(e) => {
                e.preventDefault();
                requestUnseal(habit);
              }}
              onPointerDown={() => {
                if (!coarse.current) return;
                pressTimer.current = setTimeout(() => {
                  suppressClick.current = true;
                  // Long-press: checked seal = 销印 confirm; unchecked = slip.
                  if (todayDone(habit)) {
                    requestUnseal(habit);
                  } else {
                    setSlipOpen(id);
                  }
                }, 550);
              }}
              onPointerUp={() => {
                if (pressTimer.current) clearTimeout(pressTimer.current);
              }}
              onPointerLeave={() => {
                if (pressTimer.current) clearTimeout(pressTimer.current);
                if (slipOpen === id) setSlipOpen(null);
              }}
            >
              {sealGlyph(habit)}
            </button>
          </Tooltip>
        );
      })}
    </div>
  );
}
