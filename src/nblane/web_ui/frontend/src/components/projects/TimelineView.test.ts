import { describe, expect, it } from 'vitest';

import type { KanbanSection, KanbanTask } from '../../api/types';
import { collectHistoryTasks } from './TimelineView';

function kanbanTask(partial: Partial<KanbanTask> & { title: string }): KanbanTask {
  return {
    id: '',
    done: false,
    context: '',
    why: '',
    blocked_by: '',
    outcome: '',
    crystallized: false,
    project_id: '',
    milestone_id: '',
    agent_task_id: '',
    tags: '',
    subtasks: [],
    todos: [],
    details: [],
    ...partial,
  };
}

function section(name: string, tasks: KanbanTask[]): KanbanSection {
  return { name, tasks };
}

describe('collectHistoryTasks', () => {
  it('collects Done-section tasks and done tasks from other sections', () => {
    const sections = [
      section('Done', [kanbanTask({ id: 'd1', title: 'shipped', done: true })]),
      section('Doing', [
        kanbanTask({ id: 'q1', title: 'wip', done: false }),
        kanbanTask({ id: 'q2', title: 'done in place', done: true }),
      ]),
    ];
    const items = collectHistoryTasks(sections, undefined);
    expect(items.map((task) => task.id)).toEqual(['d1', 'q2']);
  });

  it('includes kanban-archive tasks alongside section history', () => {
    const sections = [
      section('Done', [kanbanTask({ id: 'd1', title: 'shipped', done: true })]),
    ];
    const archive = [
      kanbanTask({
        id: 'a1',
        title: 'archived with date',
        done: true,
        completed_on: '2026-04-15',
        project_id: 'project:demo',
      }),
      // Archive entries without completed_on get the group date as fallback
      // server-side; a missing one still lands here and historyBarRange
      // simply skips it (no anchor).
      kanbanTask({ id: 'a2', title: 'archived no date', done: true }),
    ];
    const items = collectHistoryTasks(sections, archive);
    expect(items.map((task) => task.id)).toEqual(['d1', 'a1', 'a2']);
    expect(items[1].completed_on).toBe('2026-04-15');
    expect(items[1].project_id).toBe('project:demo');
  });

  it('returns archive tasks even with no sections', () => {
    const archive = [kanbanTask({ id: 'a1', title: 'archived', done: true })];
    expect(collectHistoryTasks(undefined, archive).map((task) => task.id)).toEqual(['a1']);
    expect(collectHistoryTasks(undefined, undefined)).toEqual([]);
  });
});
