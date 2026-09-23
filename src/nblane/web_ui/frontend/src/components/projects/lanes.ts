// Lane-group derivation for the unified /projects page.
//
// Both views (kanban swimlanes + timeline) render the SAME LaneGroup[] array
// so a view switch never reorders lanes. `goal` grouping follows the
// aggregation's goals[]/ungrouped_projects split; `activity` grouping buckets
// every project by its `kind` (KIND_LABELS).

import type {
  ProjectsBoardProject,
  ProjectsBoardResponse,
  ProjectsBoardTask,
} from '../../api/types';

export const KIND_LABELS: Record<string, string> = {
  internal: '内部',
  research: '研究',
  work: '工作',
  side_project: '副业',
  learning: '学习',
  habit: '习惯',
};

/** Stable bucket order for the 按活动 grouping. */
const KIND_ORDER = ['internal', 'research', 'work', 'side_project', 'learning', 'habit'];

export const PROJECT_STATUS_LABELS: Record<string, string> = {
  active: '进行中',
  paused: '已暂停',
  completed: '已完成',
  archived: '已归档',
};

export type ProjectsGroupBy = 'goal' | 'activity';

export interface LaneGroup {
  /** Goal id, kind key, or the '__ungrouped__' sentinel. */
  id: string;
  /** Display title (「目标 · xxx」 for goal groups). */
  title: string;
  /** Secondary line (goal target/summary or kind description). */
  meta: string;
  /** Raw goal target date (goal groups only), for the header chip. */
  target: string;
  projects: ProjectsBoardProject[];
}

/** Every project lane the aggregation returned (goal-grouped + ungrouped). */
export function collectProjects(board: ProjectsBoardResponse): ProjectsBoardProject[] {
  const all: ProjectsBoardProject[] = [];
  for (const goal of board.goals ?? []) {
    all.push(...(goal.projects ?? []));
  }
  all.push(...(board.ungrouped_projects ?? []));
  return all;
}

/** Active (non-archived) lanes; archived ones fold into the footer count. */
export function isArchivedProject(project: ProjectsBoardProject): boolean {
  return project.status === 'archived';
}

export function buildLaneGroups(
  board: ProjectsBoardResponse,
  groupBy: ProjectsGroupBy,
): LaneGroup[] {
  if (groupBy === 'activity') {
    const buckets = new Map<string, ProjectsBoardProject[]>();
    for (const project of collectProjects(board)) {
      if (isArchivedProject(project)) {
        continue;
      }
      const key = project.kind || 'internal';
      const bucket = buckets.get(key) ?? [];
      bucket.push(project);
      buckets.set(key, bucket);
    }
    const keys = [...buckets.keys()].sort((a, b) => {
      const ia = KIND_ORDER.indexOf(a);
      const ib = KIND_ORDER.indexOf(b);
      return (ia < 0 ? KIND_ORDER.length : ia) - (ib < 0 ? KIND_ORDER.length : ib);
    });
    return keys.map((key) => ({
      id: key,
      title: KIND_LABELS[key] ?? key,
      meta: '',
      target: '',
      projects: buckets.get(key) ?? [],
    }));
  }
  const groups: LaneGroup[] = (board.goals ?? [])
    .map((goal) => ({
      id: goal.id,
      title: `目标 · ${goal.title || goal.id}`,
      meta: goal.summary ?? '',
      target: goal.target ?? '',
      projects: (goal.projects ?? []).filter((project) => !isArchivedProject(project)),
    }))
    .filter((group) => group.projects.length > 0);
  const ungrouped = (board.ungrouped_projects ?? []).filter(
    (project) => !isArchivedProject(project),
  );
  if (ungrouped.length > 0) {
    groups.push({
      id: '__ungrouped__',
      title: '未分组',
      meta: '未关联任何目标的项目',
      target: '',
      projects: ungrouped,
    });
  }
  return groups;
}

/** Archived lanes fold into a count-only footer (本期仅计数折叠). */
export function collectArchivedProjects(
  board: ProjectsBoardResponse,
): ProjectsBoardProject[] {
  return collectProjects(board).filter(isArchivedProject);
}

/** Locate a task by id across lanes (queue/doing/someday) and unassigned. */
export function findBoardTask(
  board: ProjectsBoardResponse,
  taskId: string,
): { task: ProjectsBoardTask; project: ProjectsBoardProject | null } | null {
  if (!taskId) {
    return null;
  }
  for (const project of collectProjects(board)) {
    for (const list of [project.queue, project.doing, project.someday]) {
      const hit = (list ?? []).find((task) => task.id === taskId);
      if (hit) {
        return { task: hit, project };
      }
    }
  }
  const loose = (board.unassigned_tasks ?? []).find((task) => task.id === taskId);
  return loose ? { task: loose, project: null } : null;
}
