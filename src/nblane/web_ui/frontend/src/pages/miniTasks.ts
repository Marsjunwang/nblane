// Pure helpers for the 小窗 (MiniPage): todo toggling that survives a
// concurrent edit, and due-date labels. Kept separate so they are testable
// without rendering.

export interface MiniTodo {
  text: string;
  done: boolean;
}

/** Flip one todo, matched by index on the list we rendered. */
export function toggleAt(todos: MiniTodo[], index: number): MiniTodo[] {
  return todos.map((todo, i) => (i === index ? { ...todo, done: !todo.done } : todo));
}

/**
 * Re-apply a toggle on a list that changed elsewhere (after a 412).
 *
 * PATCH todos replaces the whole list, so writing our stale copy would drop
 * items added in the projects page. Find the same item by text (and its old
 * state) in the fresh list and flip only that one; null when it is gone or
 * already in the wanted state, so the caller refreshes instead of writing.
 */
export function reapplyToggle(fresh: MiniTodo[], target: MiniTodo): MiniTodo[] | null {
  const index = fresh.findIndex((todo) => todo.text === target.text && todo.done === target.done);
  return index === -1 ? null : toggleAt(fresh, index);
}

export type DueState = 'overdue' | 'today' | '';

/** 'overdue' / 'today' for a planned end on or before today (ISO dates). */
export function dueState(plannedEnd: string | null | undefined, today: string): DueState {
  if (!plannedEnd || !today) return '';
  if (plannedEnd < today) return 'overdue';
  if (plannedEnd === today) return 'today';
  return '';
}

/** Overdue first, then due today, then the rest; stable within each group. */
export function byDue<T>(items: T[], state: (item: T) => DueState): T[] {
  const rank = (item: T) => ({ overdue: 0, today: 1, '': 2 })[state(item)];
  return items
    .map((item, index) => ({ item, index }))
    .sort((a, b) => rank(a.item) - rank(b.item) || a.index - b.index)
    .map(({ item }) => item);
}
