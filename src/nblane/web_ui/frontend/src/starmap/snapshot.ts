/* Starmap snapshot: the data shape the layout/scene consume. Since Phase 3
 * follow-up, the snapshot is aggregated server-side by
 * GET /api/v1/profiles/{name}/starmap (core.starmap_snapshot, which ports
 * playground/tools/export_snapshot.py semantics); this module only declares
 * the shape and normalizes the wire response (generated OpenAPI types mark
 * most fields optional). Pure functions — vitest-covered. */

import type { GoalsResponse, StarmapResponse } from '../api/types';

export interface SnapshotCategory {
  id: string;
  name: string;
  count: number;
  lit_count: number;
  learning_count: number;
}

export interface SnapshotSkill {
  id: string;
  label: string;
  category: string;
  status: string;
  lit: boolean;
}

export interface SnapshotGoal {
  id: string;
  title: string;
  status: string;
  summary: string;
  start: string;
  target: string;
}

/** Owner-facing North Star detail (from GET /goals' NorthStarModel). The
 * /starmap aggregation carries only the display string, so the editing UI
 * merges the goal book over the snapshot (mergeGoalBook). */
export interface SnapshotNorthStar {
  is_set: boolean;
  full: string;
  brief: string;
  /** Binary public-output flag: 'public' | 'private' (legacy values map server-side). */
  visibility: string;
}

export interface SnapshotProject {
  id: string;
  title: string;
  status: string;
  kind: string;
  goal_ids: string[];
  progress: number | null;
  task_count: number;
  time_range: string;
}

export interface SnapshotEvidence {
  id: string;
  type: string;
  title: string;
  date: string;
  strength: string;
  review_status: string;
  summary: string;
  skill_ids: string[];
  project_refs: string[];
  flying: boolean;
}

export interface StarmapSnapshot {
  north_star: string;
  north: SnapshotNorthStar;
  goals: SnapshotGoal[];
  categories: SnapshotCategory[];
  skills: SnapshotSkill[];
  projects: SnapshotProject[];
  evidence: SnapshotEvidence[];
  counts: {
    evidence: number;
    evidence_needs_review: number;
    evidence_flying: number;
    projects_active: number;
    skills_lit: number;
  };
}

/** Normalize the /starmap wire response into the scene snapshot, filling
 * defaults for fields the OpenAPI schema marks optional. The aggregation
 * semantics (locked schema nodes, guest window/floor, zh category names)
 * live server-side; this is a structural projection only. */
export function normalizeStarmapResponse(data: StarmapResponse): StarmapSnapshot {
  const northText = data.north_star ?? '';
  return {
    north_star: northText,
    // The aggregation has no is_set/brief/visibility; derive is_set from the
    // text until mergeGoalBook overlays the authoritative NorthStarModel.
    north: {
      is_set: northText.trim().length > 0,
      full: northText,
      brief: '',
      visibility: 'private',
    },
    goals: (data.goals ?? []).map((g) => ({
      id: g.id,
      title: g.title || g.id,
      status: g.status || 'active',
      summary: g.summary ?? '',
      start: g.start ?? '',
      target: g.target ?? '',
    })),
    categories: (data.categories ?? []).map((c) => ({
      id: c.id,
      name: c.name || c.id,
      count: c.count ?? 0,
      lit_count: c.lit_count ?? 0,
      learning_count: c.learning_count ?? 0,
    })),
    skills: (data.skills ?? []).map((s) => ({
      id: s.id,
      label: s.label || s.id,
      category: s.category || 'misc',
      status: s.status || 'locked',
      lit: s.lit ?? false,
    })),
    projects: (data.projects ?? []).map((p) => ({
      id: p.id,
      title: p.title || p.id,
      status: p.status || 'active',
      kind: p.kind || 'internal',
      goal_ids: p.goal_ids ?? [],
      progress: p.progress ?? null,
      task_count: p.task_count ?? 0,
      time_range: p.time_range ?? '',
    })),
    evidence: (data.evidence ?? []).map((e) => ({
      id: e.id,
      type: e.type || 'practice',
      title: e.title || e.id,
      date: e.date ?? '',
      strength: e.strength || 'unrated',
      review_status: e.review_status || 'needs_review',
      summary: e.summary ?? '',
      skill_ids: e.skill_ids ?? [],
      project_refs: e.project_refs ?? [],
      flying: e.flying ?? false,
    })),
    counts: {
      evidence: data.counts?.evidence ?? 0,
      evidence_needs_review: data.counts?.evidence_needs_review ?? 0,
      evidence_flying: data.counts?.evidence_flying ?? 0,
      projects_active: data.counts?.projects_active ?? 0,
      skills_lit: data.counts?.skills_lit ?? 0,
    },
  };
}

/**
 * Merge the goal book (GET /goals: full detail, ALL statuses) over the
 * starmap aggregation (active goals only, bare north-star string). The
 * scene needs paused/completed goals for the 星表 catalog and the 刻痕星
 * (completed goals pinned on the disc, design §4), and the inscription edit
 * form needs the authoritative NorthStarModel (is_set/brief/visibility).
 *
 * Active goals keep the aggregation's order (stable star positions); paused
 * and completed goals append in book order. A goal missing from the
 * aggregation (race with a fresh create) still appears via the book.
 */
export function mergeGoalBook(
  snapshot: StarmapSnapshot,
  book: GoalsResponse | undefined,
): StarmapSnapshot {
  if (!book) return snapshot;
  const north = book.north_star;
  const mergedNorth: SnapshotNorthStar = north
    ? {
        is_set: north.is_set ?? snapshot.north.is_set,
        full: north.full ?? '',
        brief: north.brief ?? '',
        visibility: north.visibility || 'private',
      }
    : snapshot.north;
  const seen = new Set(snapshot.goals.map((g) => g.id));
  const extra: SnapshotGoal[] = (book.goals ?? [])
    .filter((g) => !seen.has(g.id))
    .map((g) => ({
      id: g.id,
      title: g.title || g.id,
      status: g.status || 'active',
      summary: g.summary ?? '',
      start: g.start ?? '',
      target: g.target ?? '',
    }));
  return {
    ...snapshot,
    north: mergedNorth,
    north_star: mergedNorth.is_set
      ? mergedNorth.full || mergedNorth.brief || snapshot.north_star
      : '',
    goals: [...snapshot.goals, ...extra],
  };
}

export function goalStatusLabel(status: string): string {
  return status === 'completed' ? '已镌刻' : status === 'paused' ? '已暂停' : '进行中';
}

/** Inscription-card rows for a goal star (mirrors the scene's detailRows;
 * used for catalog-driven selections of goals beyond the disc's seat cap). */
export function goalRows(g: SnapshotGoal): [string, string][] {
  return [
    ['状态', goalStatusLabel(g.status)],
    ['起始', g.start || '—'],
    ['目标', g.target || '—'],
    ['铭文', g.summary || '—'],
  ];
}
