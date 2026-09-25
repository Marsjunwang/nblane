// TaskCardBody someday badge: 期望激活日 (planned_start) ≤ today swaps the
// dashed-gold 「someday」 badge for a 朱砂 「该激活了」 outline (stroke only).

import { screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import type { ProjectsBoardTask } from '../../api/types';
import { renderWithProviders } from '../../test/render';
import { boardPalette } from './palette';
import { TaskCardBody } from './TaskCard';

const TASK: ProjectsBoardTask = {
  id: 'kb_1',
  title: '读 VLA 综述',
  section: 'Someday / Maybe',
  column: 'someday',
  done: false,
  planned_start: null,
  planned_end: null,
  tags: '',
  todos: [],
} as unknown as ProjectsBoardTask;

describe('TaskCardBody someday 到期徽章', () => {
  it('keeps the gold someday badge while planned_start is in the future', () => {
    renderWithProviders(
      <TaskCardBody task={{ ...TASK, planned_start: '2026-10-01' }} someday today="2026-09-25" />,
    );
    const badge = screen.getByTestId('someday-badge-kb_1');
    expect(badge).toHaveTextContent('someday');
    expect(badge.style.borderColor).not.toBe(boardPalette.overdue);
  });

  it('switches to a 朱砂 「该激活了」 outline once planned_start has arrived', () => {
    renderWithProviders(
      <TaskCardBody task={{ ...TASK, planned_start: '2026-09-25' }} someday today="2026-09-25" />,
    );
    const badge = screen.getByTestId('someday-badge-kb_1');
    expect(badge).toHaveTextContent('该激活了');
    expect(badge.style.borderColor).toBe('rgb(176, 84, 74)');
  });

  it('keeps the gold badge when no planned_start is set', () => {
    renderWithProviders(<TaskCardBody task={TASK} someday today="2026-09-25" />);
    expect(screen.getByTestId('someday-badge-kb_1')).toHaveTextContent('someday');
  });
});
