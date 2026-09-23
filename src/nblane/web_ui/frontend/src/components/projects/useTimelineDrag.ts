// Custom pointer-drag hook for timeline bars (no new dependency): pointerdown
// records the origin, pointermove converts to a whole-day offset (snapped),
// pointerup commits a schedule mutation (whole-bar translation). Failures
// (412/422) roll the preview back and surface through the caller.

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
      if (event.button !== 0 || schedule.isPending) {
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
      const finish = (upEvent: PointerEvent, cancelled: boolean) => {
        window.removeEventListener('pointermove', onMove);
        window.removeEventListener('pointerup', onUp);
        window.removeEventListener('pointercancel', onCancel);
        const current = gesture.current;
        gesture.current = null;
        setPreview(null);
        if (!current || cancelled) {
          return;
        }
        const deltaDays = Math.round((upEvent.clientX - current.startX) / scale.dayWidth);
        if (deltaDays === 0) {
          return;
        }
        // Whole-bar translation: shift both ends; absent planned dates are
        // seeded from the rendered range (planned_start ?? started_on …).
        schedule.mutate(
          {
            cardRef: current.task.title,
            body: {
              planned_start: shiftDate(current.range.start, deltaDays),
              planned_end: shiftDate(current.range.end, deltaDays),
            },
            etag: kanbanEtag,
          },
          { onError },
        );
      };
      const onUp = (upEvent: PointerEvent) => finish(upEvent, false);
      const onCancel = (upEvent: PointerEvent) => finish(upEvent, true);
      window.addEventListener('pointermove', onMove);
      window.addEventListener('pointerup', onUp);
      window.addEventListener('pointercancel', onCancel);
    },
    // `today` is part of range derivation upstream; scale/kanbanEtag/onError
    // identity changes must rebind the gesture closure.
    [schedule, scale.dayWidth, kanbanEtag, onError, today],
  );

  return { preview, active: preview !== null || schedule.isPending, startDrag };
}
