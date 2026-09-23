import { describe, expect, it } from 'vitest';

import { buildLayout, R, R_GOAL, SECTOR_START } from './layout';
import { mulberry32 } from './rng';
import { normalizeStarmapResponse, type StarmapSnapshot } from './snapshot';

/* Snapshot fixture in the server /starmap shape (post-aggregation: locked
 * schema nodes included, zh category names, flying already computed — those
 * semantics are covered by tests/test_web_api_starmap.py on the backend). */
function snapshotFixture(overrides: Partial<StarmapSnapshot> = {}): StarmapSnapshot {
  return {
    north_star: '成为能独立交付机器人 demo 的工程师',
    goals: [
      { id: 'g1', title: 'Goal One', status: 'active', summary: 's', start: '2026-01-01', target: '2026-12-31' },
      { id: 'g2', title: 'Goal Two', status: 'active', summary: '', start: '', target: '' },
    ],
    categories: [
      { id: 'control', name: '控制', count: 2, lit_count: 1, learning_count: 1 },
      { id: 'perception', name: '感知', count: 2, lit_count: 1, learning_count: 0 },
      { id: 'misc', name: 'misc', count: 1, lit_count: 0, learning_count: 0 },
    ],
    skills: [
      { id: 's1', label: 'Skill 1', category: 'control', status: 'solid', lit: true },
      { id: 's2', label: 'Skill 2', category: 'control', status: 'learning', lit: false },
      { id: 's3', label: 'Skill 3', category: 'perception', status: 'expert', lit: true },
      { id: 's4', label: 'Skill 4', category: 'perception', status: 'locked', lit: false },
      { id: 's5', label: 'Skill 5', category: 'misc', status: 'locked', lit: false },
    ],
    projects: [
      {
        id: 'p1',
        title: 'Planet One',
        status: 'active',
        kind: 'work',
        goal_ids: ['g1'],
        progress: 0.5,
        task_count: 4,
        time_range: '2026-08 ~ 2026-12',
      },
      {
        id: 'p2',
        title: 'Free Planet',
        status: 'archived',
        kind: 'internal',
        goal_ids: [],
        progress: 0.5,
        task_count: 0,
        time_range: '',
      },
    ],
    evidence: [
      {
        id: 'ev_recent',
        type: 'project',
        title: 'Recent evidence',
        date: '2026-09-20',
        strength: 'strong',
        review_status: 'needs_review',
        summary: 'sum',
        skill_ids: ['s1'],
        project_refs: ['p1'],
        flying: true,
      },
      {
        id: 'ev_old',
        type: 'practice',
        title: 'Old evidence',
        date: '2025-01-10',
        strength: 'weak',
        review_status: 'reviewed',
        summary: '',
        skill_ids: ['s3'],
        project_refs: [],
        flying: true, // density floor (server-side)
      },
    ],
    counts: {
      evidence: 2,
      evidence_needs_review: 1,
      evidence_flying: 2,
      projects_active: 1,
      skills_lit: 2,
    },
    ...overrides,
  };
}

describe('mulberry32', () => {
  it('is deterministic and stays in [0, 1)', () => {
    const a = mulberry32(42);
    const b = mulberry32(42);
    for (let i = 0; i < 100; i++) {
      const v = a();
      expect(v).toBe(b());
      expect(v).toBeGreaterThanOrEqual(0);
      expect(v).toBeLessThan(1);
    }
  });
});

describe('normalizeStarmapResponse', () => {
  it('passes through server values and fills wire defaults', () => {
    const snap = normalizeStarmapResponse({
      profile: 'alice',
      north_star: '北极星',
      goals: [{ id: 'g1', title: 'Goal One' }],
      categories: [{ id: 'control', name: '控制' }],
      skills: [{ id: 's1' }],
      projects: [{ id: 'p1' }],
      evidence: [{ id: 'e1' }],
      counts: { evidence: 1, evidence_flying: 1 },
    } as never);
    expect(snap.north_star).toBe('北极星');
    expect(snap.goals[0]).toMatchObject({ id: 'g1', status: 'active', summary: '' });
    expect(snap.categories[0]).toMatchObject({ name: '控制', count: 0 });
    expect(snap.skills[0]).toMatchObject({ label: 's1', category: 'misc', status: 'locked', lit: false });
    expect(snap.projects[0]).toMatchObject({ goal_ids: [], progress: null, task_count: 0 });
    expect(snap.evidence[0]).toMatchObject({
      type: 'practice',
      strength: 'unrated',
      review_status: 'needs_review',
      project_refs: [],
      flying: false,
    });
    expect(snap.counts).toMatchObject({ evidence: 1, evidence_flying: 1, projects_active: 0 });
  });

  it('tolerates a minimal payload (empty profile)', () => {
    const snap = normalizeStarmapResponse({ profile: 'alice' } as never);
    expect(snap).toMatchObject({
      north_star: '',
      goals: [],
      categories: [],
      skills: [],
      projects: [],
      evidence: [],
    });
    expect(snap.counts.evidence).toBe(0);
  });
});

describe('buildLayout', () => {
  const snap = snapshotFixture();
  const L = buildLayout(snap);

  it('lays out sectors proportionally over the full circle', () => {
    expect(L.sectors).toHaveLength(3);
    const widths = L.sectors.reduce((a, s) => a + s.width, 0);
    expect(widths).toBeCloseTo(360, 6);
    expect(L.sectors[0].start).toBeCloseTo(SECTOR_START, 6);
    expect(L.sectors[0].width).toBeCloseTo((2 / 5) * 360, 6);
    expect(L.sectors[0].name).toBe('控制'); // server-provided zh display name
  });

  it('hangs grouped planets beside their goal star', () => {
    const p1 = L.planets.find((p) => p.id === 'p1')!;
    expect(p1.goalIndex).toBe(0);
    const gx = L.goals[0].plan[0];
    const gy = L.goals[0].plan[1];
    const dist = Math.hypot(p1.plan[0] - gx, p1.plan[1] - gy);
    expect(dist).toBeLessThan(R_GOAL * 0.4); // sibling offset, not across the chart
  });

  it('sends ungrouped planets to free orbit slots', () => {
    const p2 = L.planets.find((p) => p.id === 'p2')!;
    expect(p2.goalIndex).toBe(-1);
    const rr = Math.hypot(p2.plan[0], p2.plan[1]);
    expect(rr).toBeCloseTo(R_GOAL + 24, 3);
  });

  it('emits one moon per task (capped at 5)', () => {
    expect(L.moons.plan.length / 3).toBe(4); // p1 task_count = 4, p2 = 0
  });

  it('marks flying evidence as guests with strength-scaled tails', () => {
    expect(L.guests.map((g) => g.id)).toEqual(['ev_recent', 'ev_old']);
    expect(L.guests[0].tailLen).toBe(9); // strong
    expect(L.guests[1].tailLen).toBe(4); // weak
  });

  it('seats non-flying evidence near its project planet', () => {
    const seatedSnap = snapshotFixture({
      evidence: [
        {
          id: 'ev_seated',
          type: 'practice',
          title: 'Seated',
          date: '2025-01-10',
          strength: 'medium',
          review_status: 'reviewed',
          summary: '',
          skill_ids: [],
          project_refs: ['p1'],
          flying: false,
        },
      ],
    });
    const sl = buildLayout(seatedSnap);
    expect(sl.seated.plan.length / 3).toBe(1);
    const planet = sl.planets.find((p) => p.id === 'p1')!;
    const dist = Math.hypot(sl.seated.plan[0] - planet.plan[0], sl.seated.plan[1] - planet.plan[1]);
    expect(dist).toBeLessThan(10); // clustered around the planet, not in a sector
  });

  it('grows a dust mote per evidence entry', () => {
    expect(L.dust.plan.length / 3).toBe(2);
    expect(L.dust.trailPlan.length / 3).toBe(4); // 2 verts per mote
  });

  it('keeps learning stars solid and lit stars ringed (点外套圈)', () => {
    const solidIdx = L.lit.skills.findIndex((s) => s.status === 'solid');
    const learningIdx = L.lit.skills.findIndex((s) => s.status === 'learning');
    expect(solidIdx).toBeGreaterThanOrEqual(0);
    expect(learningIdx).toBeGreaterThanOrEqual(0);
    expect(L.lit.ring[solidIdx]).toBe(1);
    expect(L.lit.ring[learningIdx]).toBe(0);
    expect(L.lit.core[solidIdx]).toBe(1);
  });

  it('puts locked real nodes into the dim field as empty rings (空圈)', () => {
    // s4 + s5 are locked: 2 carved rings among the synthetic filler
    const realLocked = L.dim.filler.filter((f) => f === 0).length;
    expect(realLocked).toBe(2);
    for (let i = 0; i < L.dim.filler.length; i++) {
      if (L.dim.filler[i] === 0) {
        expect(L.dim.core[i]).toBe(0);
        expect(L.dim.ring[i]).toBe(1);
      }
    }
  });

  it('is deterministic for the same snapshot', () => {
    const again = buildLayout(snap);
    expect(again.planets.map((p) => p.plan)).toEqual(L.planets.map((p) => p.plan));
    expect(again.guests.map((g) => g.plan)).toEqual(L.guests.map((g) => g.plan));
    expect(again.dim.plan).toEqual(L.dim.plan);
  });

  it('handles an empty profile without dividing by zero', () => {
    const empty = buildLayout(
      snapshotFixture({
        north_star: '',
        goals: [],
        categories: [],
        skills: [],
        projects: [],
        evidence: [],
        counts: {
          evidence: 0,
          evidence_needs_review: 0,
          evidence_flying: 0,
          projects_active: 0,
          skills_lit: 0,
        },
      }),
    );
    expect(empty.sectors).toEqual([]);
    expect(empty.planets).toEqual([]);
    expect(empty.guests).toEqual([]);
  });
});

describe('chart constants', () => {
  it('keeps the playground proportions', () => {
    expect(R).toBe(100);
    expect(R_GOAL).toBeCloseTo(54, 6);
  });
});
