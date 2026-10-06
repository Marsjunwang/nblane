// Custom pointer-drag hook for timeline bars (no new dependency): pointerdown
// records the origin, pointermove converts to a whole-day offset (snapped),
// pointerup commits a schedule mutation (whole-bar translation). The preview
// is held until the refetched board lands (no snap-back flash); failures
// (412/422) roll it back and surface through the caller. A real drag
// swallows its trailing click (no accidental detail-card open) and Esc
// cancels mid-drag.

import { useQueryClient } from '@tanstack/react-query';
import { useCallback, useRef, useState } from 'react';

import { useScheduleKanbanCard } from '../../api/hooks';
import type { ProjectsBoardTask } from '../../api/types';
import type { BarRange, TimelineScale } from './timelineMath';
import { shiftDate } from './timelineMath';

export interface TimelineDragPreview {
  taskId: string;
  deltaDays: number;
}

export interface TimelineDrag {
  /** Live preview offset; null when idle. */
  preview: TimelineDragPreview | null;
  /** True while a drag gesture or its commit is in flight. */
  active: boolean;
  /** Attach to a task bar's onPointerDown. */
  startDrag: (event: React.PointerEvent, task: ProjectsBoardTask, range: BarRange) => void;
}

/** Pointer travel (px) past which a press counts as a drag, not a click. */
const DRAG_CLICK_SLOP_PX = 3;

export function useTimelineDrag({
  profile,
  scale,
  kanbanEtag,
  today,
  onError,
}: {
  profile: string;
  scale: TimelineScale;
  kanbanEtag: string;
  today: string;
  /** Called with the mutation error after a failed commit (preview rolled back). */
  onError: (error: unknown) => void;
}): TimelineDrag {
  const schedule = useScheduleKanbanCard(profile);
  const queryClient = useQueryClient();
  // Latest mutation object for the gesture closure (its identity changes on
  // every render, which would otherwise rebind startDrag constantly).
  const scheduleRef = useRef(schedule);
  scheduleRef.current = schedule;
  const [preview, setPreview] = useState<TimelineDragPreview | null>(null);
  const gesture = useRef<{
    task: ProjectsBoardTask;
    range: BarRange;
    startX: number;
    pointerId: number;
  } | null>(null);

  const startDrag = useCallback(
    (event: React.PointerEvent, task: ProjectsBoardTask, range: BarRange) => {
      // Primary button only; right-click context menus stay intact.
      if (event.button !== 0 || scheduleRef.current.isPending) {
        return;
      }
      event.preventDefault();
      gesture.current = {
        task,
        range,
        startX: event.clientX,
        pointerId: event.pointerId,
      };
      setPreview({ taskId: task.id, deltaDays: 0 });

      const onMove = (moveEvent: PointerEvent) => {
        if (!gesture.current || moveEvent.pointerId !== gesture.current.pointerId) {
          return;
        }
        const deltaDays = Math.round(
          (moveEvent.clientX - gesture.current.startX) / scale.dayWidth,
        );
        setPreview({ taskId: gesture.current.task.id, deltaDays });
      };
      const swallowClick = (clickEvent: MouseEvent) => {
        clickEvent.stopPropagation();
        clickEvent.preventDefault();
      };
      const finish = (clientX: number, cancelled: boolean) => {
        window.removeEventListener('pointermove', onMove);
        window.removeEventListener('pointerup', onUp);
        window.removeEventListener('pointercancel', onCancel);
        window.removeEventListener('keydown', onKey, true);
        const current = gesture.current;
        gesture.current = null;
        if (current && Math.abs(clientX - current.startX) > DRAG_CLICK_SLOP_PX) {
          // The pointerup lands on the bar, so a click follows — eat it once.
          window.addEventListener('click', swallowClick, { capture: true, once: true });
          setTimeout(() => window.removeEventListener('click', swallowClick, true), 0);
        }
        const deltaDays = current ? Math.round((clientX - current.startX) / scale.dayWidth) : 0;
        if (!current || cancelled || deltaDays === 0) {
          setPreview(null);
          return;
        }
        // Hold the dropped offset: clear only once the refetched board (with
        // the new dates) is in the cache, or on failure.
        setPreview({ taskId: current.task.id, deltaDays });
        // Whole-bar translation: shift both ends; absent planned dates are
        // seeded from the rendered range (planned_start ?? started_on …).
        scheduleRef.current.mutate(
          {
            // Id-first addressing: the task id is URL-safe, unlike titles with '/'.
            cardRef: current.task.id || current.task.title,
            body: {
              planned_start: shiftDate(current.range.start, deltaDays),
              planned_end: shiftDate(current.range.end, deltaDays),
            },
            etag: kanbanEtag,
          },
          {
            onSuccess: async () => {
              await queryClient.refetchQueries({
                queryKey: ['profiles', profile, 'projects-board'],
              });
              setPreview(null);
            },
            onError: (error) => {
              setPreview(null);
              onError(error);
            },
          },
        );
      };
      const onUp = (upEvent: PointerEvent) => finish(upEvent.clientX, false);
      const onCancel = (upEvent: PointerEvent) => finish(upEvent.clientX, true);
      const onKey = (keyEvent: KeyboardEvent) => {
        if (keyEvent.key === 'Escape' && gesture.current) {
          keyEvent.preventDefault();
          keyEvent.stopPropagation();
          // Cancel = no commit and no click swallow (pointer never moved "for real").
          finish(gesture.current.startX, true);
        }
      };
      window.addEventListener('pointermove', onMove);
      window.addEventListener('pointerup', onUp);
      window.addEventListener('pointercancel', onCancel);
      window.addEventListener('keydown', onKey, true);
    },
    // `today` is part of range derivation upstream; scale/kanbanEtag/onError
    // identity changes must rebind the gesture closure.
    [scale.dayWidth, kanbanEtag, onError, today, queryClient, profile],
  );

  return { preview, active: preview !== null || schedule.isPending, startDrag };
}
