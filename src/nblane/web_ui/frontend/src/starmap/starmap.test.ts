import { describe, expect, it } from 'vitest';

import { buildLayout, CARVED_ANGLES, GOAL_ANGLES, R, R_GOAL, SECTOR_START, TEMP, SECTOR_ASTERISM_TABLE, asterismById, asterismLinearity } from './layout';
import { mulberry32 } from './rng';
import { mergeGoalBook, normalizeStarmapResponse, type StarmapSnapshot } from './snapshot';
import type { GoalsResponse } from '../api/types';

/* Snapshot fixture in the server /starmap shape (post-aggregation: locked
 * schema nodes included, zh category names, flying already computed — those
 * semantics are covered by tests/test_web_api_starmap.py on the backend). */
function snapshotFixture(overrides: Partial<StarmapSnapshot> = {}): StarmapSnapshot {
  return {
    north_star: '成为能独立交付机器人 demo 的工程师',
    north: {
      is_set: true,
      full: '成为能独立交付机器人 demo 的工程师',
      brief: '',
      visibility: 'private',
    },
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
    expect(snap.north).toMatchObject({ is_set: false, full: '', visibility: 'private' });
  });
});

describe('mergeGoalBook', () => {
  const book: GoalsResponse = {
    profile: 'alice',
    north_star: {
      is_set: true,
      full: '全文北极星',
      brief: '简称',
      visibility: 'public',
    },
    goals: [
      { id: 'g1', title: 'Goal One', status: 'active' },
      { id: 'g3', title: 'Paused Goal', status: 'paused' },
      { id: 'g4', title: 'Done Goal', status: 'completed', target: '2026-06-01' },
    ],
  } as GoalsResponse;

  it('overlays the authoritative NorthStarModel and appends non-active goals', () => {
    const merged = mergeGoalBook(snapshotFixture(), book);
    expect(merged.north).toMatchObject({
      is_set: true,
      full: '全文北极星',
      brief: '简称',
      visibility: 'public',
    });
    expect(merged.north_star).toBe('全文北极星');
    // active goals keep aggregation order; paused/completed append in book order
    expect(merged.goals.map((g) => g.id)).toEqual(['g1', 'g2', 'g3', 'g4']);
    expect(merged.goals[3]).toMatchObject({ status: 'completed', target: '2026-06-01' });
  });

  it('marks the pole vacant when the book says is_set=false', () => {
    const merged = mergeGoalBook(snapshotFixture(), {
      ...book,
      north_star: { is_set: false, full: '', brief: '', visibility: 'private' },
    } as GoalsResponse);
    expect(merged.north.is_set).toBe(false);
    expect(merged.north_star).toBe('');
  });

  it('returns the snapshot untouched when the book is unavailable', () => {
    const snap = snapshotFixture();
    expect(mergeGoalBook(snap, undefined)).toBe(snap);
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
        north: { is_set: false, full: '', brief: '', visibility: 'private' },
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

  it('pins completed goals on the carved seats (刻痕星, design §4)', () => {
    const withDone = buildLayout(
      snapshotFixture({
        goals: [
          { id: 'g1', title: 'Goal One', status: 'active', summary: '', start: '', target: '' },
          { id: 'g2', title: 'Goal Two', status: 'paused', summary: '', start: '', target: '' },
          { id: 'g3', title: 'Done Goal', status: 'completed', summary: '', start: '', target: '' },
        ],
      }),
    );
    expect(withDone.goals.map((g) => [g.id, g.status])).toEqual([
      ['g1', 'active'],
      ['g2', 'paused'],
      ['g3', 'completed'],
    ]);
    // living goals sit on GOAL_ANGLES; the carved one on CARVED_ANGLES
    expect(withDone.goals[0].angle).toBe(GOAL_ANGLES[0]);
    expect(withDone.goals[1].angle).toBe(GOAL_ANGLES[1]);
    expect(withDone.goals[2].angle).toBe(CARVED_ANGLES[0]);
    // carved seats share the R_GOAL ring (rotate with the disc, no collision)
    const r = Math.hypot(withDone.goals[2].plan[0], withDone.goals[2].plan[1]);
    expect(r).toBeCloseTo(R_GOAL, 6);
  });
});

describe('chart constants', () => {
  it('keeps the playground proportions', () => {
    expect(R).toBe(100);
    expect(R_GOAL).toBeCloseTo(54, 6);
  });
});

describe('北斗环卫 naming layer (design 四轮)', () => {
  const snap = snapshotFixture();
  const L = buildLayout(snap);

  it('names living goals by dipper seat order and keeps 虚位 seats hollow', () => {
    expect(L.seats).toHaveLength(7);
    expect(L.seats.map((s) => s.name)).toEqual([
      '天枢', '天璇', '天玑', '天权', '玉衡', '开阳', '摇光',
    ]);
    // two living goals hold 天枢/天璇; the rest are 虚位 (incl. the 开阳/摇光
    // reserve seats beyond the 5-goal cap)
    expect(L.seats.map((s) => s.goalIndex)).toEqual([0, 1, null, null, null, null, null]);
    expect(L.goals[0].seatName).toBe('天枢');
    expect(L.goals[1].seatName).toBe('天璇');
    // seat positions stay on the existing goal ring (no repositioning)
    expect(L.seats[0].angle).toBe(GOAL_ANGLES[0]);
  });

  it('revokes the dipper name on completion (刻痕星 has no seatName)', () => {
    const withDone = buildLayout(
      snapshotFixture({
        goals: [
          { id: 'g1', title: 'Goal One', status: 'active', summary: '', start: '', target: '' },
          { id: 'g3', title: 'Done Goal', status: 'completed', summary: '', start: '', target: '' },
        ],
      }),
    );
    expect(withDone.goals[0].seatName).toBe('天枢');
    expect(withDone.goals[1].status).toBe('completed');
    expect(withDone.goals[1].seatName).toBeUndefined();
    expect(withDone.seats[1].goalIndex).toBeNull();
  });
});

describe('sector asterism figures (星官真形)', () => {
  const L = buildLayout(snapshotFixture());

  it('maps categories to the user-confirmed 星官 names (rim band labels)', () => {
    // 控制→轸宿 (name only, shape falls back to templates), 感知→毕宿 (real
    // shape in asterisms.json), unmapped categories keep their own name
    expect(L.sectors[0].asterism).toBe('轸宿');
    expect(L.sectors[1].asterism).toBe('毕宿');
    expect(L.sectors[2].asterism).toBe('misc');
  });

  it('carves the full figure: members on shape slots, rest etched 空圈', () => {
    // 控制: template (7 slots) with 2 members → 5 etched; 感知: 毕宿 (9
    // stars) with 1 member → 8 etched; misc unmapped+empty → skipped
    expect(L.etched.plan.length / 3).toBe(5 + 8);
    // etched lines cover the whole figure (6 template links + 8 毕宿 links)
    expect(L.shapeLinesPlan.length / 6).toBe(6 + 8);
  });

  it('etches the full figure for a mapped sector with no lit members (空圈蚀刻)', () => {
    const locked = buildLayout(
      snapshotFixture({
        categories: [
          { id: 'research', name: '研究', count: 1, lit_count: 0, learning_count: 0 },
        ],
        skills: [{ id: 's9', label: 'Skill 9', category: 'research', status: 'locked', lit: false }],
      }),
    );
    expect(locked.sectors[0].asterism).toBe('文昌'); // 心宿 culled (near-collinear)
    expect(locked.etched.plan.length / 3).toBe(5); // 文昌五星, all vacant seats
    expect(locked.shapeLinesPlan.length / 6).toBe(4); // its four line segments
    expect(locked.lit.plan).toHaveLength(0);
    // figure radius recorded so the muted in-sector name can sit beyond it
    expect(locked.sectors[0].figRadius).toBeGreaterThan(0);
  });

  it('culls near-collinear shapes: every mapped real figure passes the linearity guard', () => {
    // 王军 round-2: figures that read as a straight line at sector scale must
    // not be mapped (角宿 2星一线 and 心宿 三星近共线 were culled this way).
    for (const [cat, m] of Object.entries(SECTOR_ASTERISM_TABLE)) {
      const aster = asterismById(m.id);
      if (!aster) continue; // template-fallback names (翼/房/箕/轸/轩辕/虚)
      expect(
        asterismLinearity(aster.stars),
        `${cat}→${m.name} reads as a line — substitute or drop it`,
      ).toBeGreaterThanOrEqual(0.18);
    }
    // the two culled figures really are gone from the table
    expect(Object.values(SECTOR_ASTERISM_TABLE).map((m) => m.id)).not.toContain('jiao');
    expect(Object.values(SECTOR_ASTERISM_TABLE).map((m) => m.id)).not.toContain('xin');
  });
});

describe('境态 deepspace tuning', () => {
  const L = buildLayout(snapshotFixture());

  it('gives background filler a power-law pseudo-magnitude (~5% bright)', () => {
    const scales = L.dim.deepOpScale.filter((_, i) => L.dim.filler[i] === 1);
    const bright = scales.filter((s) => s > 0.9).length;
    const frac = bright / scales.length;
    expect(frac).toBeGreaterThan(0.01);
    expect(frac).toBeLessThan(0.12);
  });

  it('assigns only the discrete 4-step deep color temperatures', () => {
    const palette = new Set(
      [TEMP.blueWhite, TEMP.moonWhite, TEMP.warmGold, TEMP.softOrange].map((c) => c.join(',')),
    );
    for (let i = 0; i < L.dim.deepColor.length; i += 3) {
      const key = [L.dim.deepColor[i], L.dim.deepColor[i + 1], L.dim.deepColor[i + 2]].join(',');
      expect(palette.has(key)).toBe(true);
    }
  });
});
