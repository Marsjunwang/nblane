import { describe, expect, it } from 'vitest';

import type {
  ProjectsBoardProject,
  ProjectsBoardResponse,
  ProjectsBoardTask,
} from '../../api/types';
import {
  buildLaneGroups,
  collectArchivedProjects,
  collectProjects,
  findBoardTask,
} from './lanes';

function makeTask(overrides: Partial<ProjectsBoardTask>): ProjectsBoardTask {
  return {
    id: '',
    title: '',
    section: 'Queue',
    column: 'queue',
    done: false,
    context: '',
    why: '',
    started_on: null,
    completed_on: null,
    planned_start: null,
    planned_end: null,
    project_id: '',
    milestone_id: '',
    tags: '',
    ...overrides,
  };
}

function makeProject(overrides: Partial<ProjectsBoardProject>): ProjectsBoardProject {
  return {
    id: 'p',
    title: '项目',
    status: 'active',
    kind: 'internal',
    visibility: 'private',
    summary: '',
    time_range: '',
    goal_refs: [],
    milestones: [],
    queue: [],
    doing: [],
    someday: [],
    column_counts: {},
    done_count: 0,
    archived_done_count: 0,
    last_activity: '',
    habit_id: '',
    ...overrides,
  };
}

const BOARD: ProjectsBoardResponse = {
  profile: 'dev',
  today: '2026-09-23',
  north_star: '',
  goals: [
    {
      id: 'g1',
      title: '2026持续学习',
      status: 'active',
      summary: '长期投入',
      target: '2026-12-31',
      projects: [
        makeProject({ id: 'p1', title: '知识补全', kind: 'learning', goal_refs: ['g1'] }),
        makeProject({ id: 'p2', title: '旧项目', status: 'archived', goal_refs: ['g1'] }),
      ],
    },
    {
      id: 'g2',
      title: '空目标',
      status: 'active',
      summary: '',
      target: '',
      projects: [],
    },
  ],
  ungrouped_projects: [makeProject({ id: 'p3', title: '游离项目', kind: 'research' })],
  unassigned_tasks: [makeTask({ id: 'kb_loose', title: '无归属任务' })],
  habits: [],
  stats: {},
};

describe('lanes buildLaneGroups (goal)', () => {
  it('groups projects under goals, drops archived lanes, appends 未分组', () => {
    const groups = buildLaneGroups(BOARD, 'goal');
    expect(groups.map((group) => group.id)).toEqual(['g1', '__ungrouped__']);
    expect(groups[0].title).toBe('目标 · 2026持续学习');
    expect(groups[0].target).toBe('2026-12-31');
    expect(groups[0].projects.map((project) => project.id)).toEqual(['p1']);
    expect(groups[1].projects.map((project) => project.id)).toEqual(['p3']);
  });
});

describe('lanes buildLaneGroups (activity)', () => {
  it('buckets active projects by kind in the stable KIND order', () => {
    const groups = buildLaneGroups(BOARD, 'activity');
    // internal (none) drops out; learning before research per KIND_ORDER…
    // learning is in KIND_ORDER after research, so research sorts first.
    expect(groups.map((group) => group.id)).toEqual(['research', 'learning']);
    expect(groups[0].title).toBe('研究');
    expect(groups[1].title).toBe('学习');
    // Archived lanes never appear in activity buckets either.
    expect(
      groups.flatMap((group) => group.projects).some((project) => project.id === 'p2'),
    ).toBe(false);
  });
});

describe('lanes collect / find', () => {
  it('collectProjects flattens goals + ungrouped (archived included)', () => {
    expect(collectProjects(BOARD).map((project) => project.id)).toEqual(['p1', 'p2', 'p3']);
  });

  it('collectArchivedProjects returns only archived lanes', () => {
    expect(collectArchivedProjects(BOARD).map((project) => project.id)).toEqual(['p2']);
  });

  it('findBoardTask searches lanes and the unassigned pool by id', () => {
    const withTask: ProjectsBoardResponse = {
      ...BOARD,
      ungrouped_projects: [
        makeProject({
          id: 'p3',
          someday: [makeTask({ id: 'kb_someday', title: '以后再说', column: 'someday' })],
        }),
      ],
    };
    expect(findBoardTask(withTask, 'kb_someday')?.project?.id).toBe('p3');
    expect(findBoardTask(withTask, 'kb_loose')?.project).toBeNull();
    expect(findBoardTask(withTask, 'kb_missing')).toBeNull();
    expect(findBoardTask(withTask, '')).toBeNull();
  });
});
