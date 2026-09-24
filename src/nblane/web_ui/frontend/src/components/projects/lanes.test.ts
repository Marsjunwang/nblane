import { describe, expect, it } from 'vitest';

import type {
  ProjectsBoardProject,
  ProjectsBoardResponse,
  ProjectsBoardTask,
} from '../../api/types';
import {
  buildLaneGroups,
  collectArchivedProjects,
  collectHabitPlanIds,
  collectHabitRows,
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
    evidence_ref_count: 0,
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

describe('lanes habit dedupe (裁决2:一个习惯全站一行)', () => {
  const habitPlanBoard: ProjectsBoardResponse = {
    ...BOARD,
    ungrouped_projects: [
      makeProject({ id: 'p3', title: '游离项目', kind: 'research' }),
      // habit-plan: kind 'habit' + habit-side link → lives only in the band.
      makeProject({ id: 'plan-exercise', title: '锻炼 30 天', kind: 'habit', habit_id: 'exercise' }),
      // A normal project with a habit link keeps its swimlane.
      makeProject({ id: 'p-health', title: '健康', kind: 'internal' }),
    ],
    habits: [
      {
        id: 'exercise',
        title: '保持锻炼',
        kind: 'health',
        cadence: 'daily',
        project_id: 'plan-exercise',
        week: [],
        recent_days: [],
        streak: 0,
        total_checkins: 0,
        last_checkin: '',
        archived: false,
      },
      {
        id: 'reading',
        title: '阅读',
        kind: 'learning',
        cadence: 'daily',
        project_id: 'p-health',
        week: [],
        recent_days: [],
        streak: 0,
        total_checkins: 0,
        last_checkin: '',
        archived: false,
      },
    ],
  };

  it('collectHabitRows resolves the link from either side, once per habit', () => {
    const rows = collectHabitRows(habitPlanBoard);
    expect(rows.map((row) => row.habit.id)).toEqual(['exercise', 'reading']);
    expect(rows[0].project?.id).toBe('plan-exercise');
    expect(rows[1].project?.id).toBe('p-health');
  });

  it('habit-plan projects are filtered out of every lane grouping', () => {
    expect([...collectHabitPlanIds(habitPlanBoard)]).toEqual(['plan-exercise']);
    for (const groupBy of ['goal', 'activity'] as const) {
      const ids = buildLaneGroups(habitPlanBoard, groupBy).flatMap((group) =>
        group.projects.map((project) => project.id),
      );
      expect(ids).not.toContain('plan-exercise');
      // Non-habit-plan lanes survive (including habit-linked normal projects).
      expect(ids).toContain('p-health');
      expect(ids).toContain('p3');
    }
  });

  it('a kind-habit project with NO resolved habit stays a lane (never vanishes)', () => {
    const orphan: ProjectsBoardResponse = {
      ...BOARD,
      habits: [],
      ungrouped_projects: [makeProject({ id: 'plan-orphan', kind: 'habit' })],
    };
    const ids = buildLaneGroups(orphan, 'goal').flatMap((group) =>
      group.projects.map((project) => project.id),
    );
    expect(ids).toContain('plan-orphan');
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
