/* Layout math for the growth-galaxy playground.
 * Ports the design language of .dev-assets/design-mockups/starchart.js (v2)
 * into data both scene states can share: every point has a planisphere pose
 * (flat chart) and a deepspace pose (spread + tilt handled by group/camera). */
import { mulberry32 } from './rng.js';

export const R = 100;
const S = R / 400;
export const R_IN = 0.30 * R;
export const R_GOAL = 0.54 * R;
export const R_OUT = 0.95 * R;
export const BAND_IN = R + 22 * S;
export const BAND_OUT = R + 52 * S;
export const BAND_TEXT = R + 37 * S;
export const SECTOR_START = -160;

export const INK = 0xe8e2d2;
export const GOLD = 0xdcae55;
export const GOLD_BRIGHT = 0xf0cd7f;

const GOAL_ANGLES = [-145, -72, -2, 52, 160];

// Asterism morphology templates (ported from v2, scaled to chart units).
const TEMPLATES = [
  { // branch tree
    slots: [[0, 4, 1.15], [-0.5, -1.5, 0.68], [-4, -6, 0.62], [-8, -8.5, 0.78], [-11.2, -7.2, 0.58], [3, -5.5, 0.62], [6.8, -7.8, 0.72]],
    links: [[0, 1], [1, 2], [2, 3], [3, 4], [1, 5], [5, 6]],
  },
  { // gentle chain
    slots: [[-11.8, 2.8, 0.62], [-6, 0.5, 0.72], [-0.5, -1, 0.92], [5, -0.5, 0.68], [10.8, 1.8, 0.6]],
    links: [[0, 1], [1, 2], [2, 3], [3, 4]],
  },
  { // bow arc
    slots: [[-8.8, -1.8, 0.62], [-4.5, 2, 0.7], [0, 3.5, 0.9], [4.5, 2, 0.7], [8.8, -1.8, 0.62]],
    links: [[0, 1], [1, 2], [2, 3], [3, 4]],
  },
  { // tight cluster
    slots: [[-2, -1.2, 0.85], [2.2, -0.8, 0.65], [0, 2, 0.6]],
    links: [[0, 1], [1, 2], [2, 0]],
  },
  { // zigzag
    slots: [[-9.2, -2.5, 0.62], [-4, 2.2, 0.72], [1, -2.2, 0.82], [6, 2.5, 0.65], [10.2, -0.8, 0.6]],
    links: [[0, 1], [1, 2], [2, 3], [3, 4]],
  },
];

// 紫微垣 court cluster (decorative, from the v2 mockup).
const COURT = [
  [-40, 18, 0.72, 1], [-78, 11.5, 0.6, 0], [-112, 15.5, 0.68, 0], [-148, 12.5, 0.58, 0],
  [168, 19, 0.78, 1], [142, 11.5, 0.58, 0], [116, 17, 0.65, 0], [88, 11, 0.58, 0],
  [58, 15, 0.72, 1], [34, 21, 0.6, 0], [-32, 24, 0.62, 0], [-95, 22.5, 0.65, 1],
];
const COURT_LINKS = [[0, 1], [1, 2], [2, 3], [5, 6], [6, 7], [8, 9]];

function polar(r, deg) {
  const a = (deg * Math.PI) / 180;
  return [r * Math.cos(a), r * Math.sin(a)];
}

function normAngle(a) {
  a = a % 360;
  if (a > 180) a -= 360;
  if (a < -180) a += 360;
  return a;
}

export function buildLayout(snapshot) {
  const rnd = mulberry32(20260921);

  // ---- sectors: width proportional to real per-category skill counts ----
  const total = snapshot.categories.reduce((a, c) => a + c.count, 0);
  const sectors = [];
  let acc = SECTOR_START;
  for (const cat of snapshot.categories) {
    const width = (cat.count / total) * 360;
    sectors.push({ id: cat.id, name: cat.name, start: acc, width, count: cat.count });
    acc += width;
  }
  const sectorOf = (id) => sectors.find((s) => s.id === id);

  // ---- dim star field: real locked nodes + synthetic filler ----
  // shape language (石刻三家星记): locked=空圈(core0,ring1) learning=实点(core1,ring0)
  // lit=点外套圈(core1,ring1); filler stars are plain dots and carry no semantics
  const WARM = [0.961, 0.918, 0.824]; // #f5ead2, unified star color for both states
  const dim = { plan: [], deep: [], size: [], opacity: [], core: [], ring: [], legacyRing: [], color: [], filler: [], deepOpScale: [], deepSizeScale: [] };
  const pushDim = (px, py, dx, dy, dz, size, opacity, isFiller, tint, deepOpScale, deepSizeScale, core, ring, legacyRing) => {
    dim.plan.push(px, py, 0);
    dim.deep.push(dx, dy, dz);
    dim.size.push(size);
    dim.opacity.push(opacity);
    dim.core.push(core);
    dim.ring.push(ring);
    dim.legacyRing.push(legacyRing);
    dim.color.push(tint[0], tint[1], tint[2]);
    dim.filler.push(isFiller ? 1 : 0);
    dim.deepOpScale.push(deepOpScale);
    dim.deepSizeScale.push(deepSizeScale);
  };
  const deepSpread = () => [(rnd() * 2 - 1) * 250, (rnd() * 2 - 1) * 140, 40 - rnd() * 180];

  const byCat = new Map();
  for (const sk of snapshot.skills) {
    if (!byCat.has(sk.category)) byCat.set(sk.category, []);
    byCat.get(sk.category).push(sk);
  }

  // locked real nodes: empty carved rings (空圈)
  for (const sk of snapshot.skills) {
    if (sk.lit || sk.status === 'learning') continue;
    const sec = sectorOf(sk.category);
    const ang = sec.start + 1.5 + rnd() * (sec.width - 3);
    const rr = R * (0.34 + 0.58 * Math.sqrt(rnd()));
    const [px, py] = polar(rr, ang);
    const [dx, dy, dz] = deepSpread();
    pushDim(px, py, dx, dy, dz, 0.62 + rnd() * 0.2, 0.34 + rnd() * 0.08, false, WARM, 0.6, 0.55, 0, 1, rnd() < 0.3 ? 1 : 0);
  }

  // synthetic filler, distributed across sectors by weight
  const FILLER = 1800;
  for (const sec of sectors) {
    const n = Math.round((sec.count / total) * FILLER);
    for (let i = 0; i < n; i++) {
      let ang, rr;
      if (rnd() < 0.15) { // 紫微垣: dense central disc
        ang = rnd() * 360;
        rr = R_IN * (0.52 + 0.46 * rnd());
        if (Math.abs(normAngle(ang)) < 25) continue;
      } else {
        ang = sec.start + 1.3 + rnd() * (sec.width - 2.6);
        rr = R * (0.33 + 0.61 * Math.sqrt(rnd()));
      }
      const [px, py] = polar(rr, ang);
      const [dx, dy, dz] = deepSpread();
      const goldTint = [1.0, 0.88, 0.69];
      const blueTint = [0.74, 0.81, 1.0];
      const m = rnd();
      // ~5% carry a constant color-temperature tint, identical in both states
      const tint = m > 0.975 ? goldTint : m > 0.95 ? blueTint : WARM;
      const bright = m > 0.992; // <1% bright stars (月.png restraint)
      // deepspace restraint (月.png): mostly very faint pins, a few bright stars
      const deepOpScale = bright ? 1.1 : 0.15 + Math.pow(rnd(), 1.8) * 0.85;
      const deepSizeScale = bright ? 0.9 : 0.35 + Math.pow(rnd(), 2) * 0.5;
      pushDim(px, py, dx, dy, dz,
        bright ? 0.62 : 0.34 + rnd() * 0.22,
        bright ? 0.38 : 0.10 + rnd() * 0.12,
        true, tint, deepOpScale, deepSizeScale, 1, 0, rnd() < 0.18 ? 1 : 0);
    }
  }

  // ---- lit / learning skill asterisms ----
  const lit = { plan: [], deep: [], size: [], opacity: [], core: [], ring: [], color: [], links: [], skills: [] };
  const evCountBySkill = new Map();
  snapshot.evidence.forEach((e) => e.skill_ids.forEach((id) => evCountBySkill.set(id, (evCountBySkill.get(id) || 0) + 1)));
  let vertexCount = 0;
  snapshot.categories.forEach((cat, ci) => {
    const members = (byCat.get(cat.id) || []).filter((s) => s.lit || s.status === 'learning');
    if (!members.length) return;
    const sec = sectorOf(cat.id);
    const mid = sec.start + sec.width / 2;
    const [ccx, ccy] = polar(R * 0.72, mid);
    const tpl = TEMPLATES[ci % TEMPLATES.length];
    const jrnd = mulberry32(500 + ci);
    const slots = tpl.slots.slice(0, members.length);
    while (slots.length < members.length) { // extend as a chain if needed
      const last = slots[slots.length - 1];
      slots.push([last[0] + 4.5, last[1] + (jrnd() - 0.5) * 3, 0.58]);
    }
    const base = vertexCount;
    members.forEach((sk, i) => {
      const [ox, oy, os] = slots[i];
      const px = ccx + (ox + (jrnd() - 0.5) * 1.6);
      const py = ccy + (oy + (jrnd() - 0.5) * 1.6);
      const [dx, dy, dz] = deepSpread();
      lit.plan.push(px, py, 0);
      lit.deep.push(dx, dy, dz);
      lit.size.push(os * (sk.lit ? 1.15 : 0.9));
      lit.opacity.push(sk.lit ? 0.95 : 0.55);
      lit.core.push(1); // 实点
      lit.ring.push(sk.lit ? 1 : 0); // 点亮 = 点外套圈
      lit.color.push(0.961, 0.918, 0.824); // unified warm white
      lit.skills.push({
        id: sk.id, label: sk.label, category: sk.category, status: sk.status,
        evidenceCount: evCountBySkill.get(sk.id) || 0,
      });
      vertexCount += 1;
    });
    // only formed asterisms (>= 3 stars) get links; segments join actual star points
    if (members.length >= 3) {
      for (const [a, b] of tpl.links) {
        if (a < members.length && b < members.length) lit.links.push(base + a, base + b);
      }
    }
  });

  // ---- goals ----
  const goals = snapshot.goals.slice(0, 5).map((g, i) => {
    const [px, py] = polar(R_GOAL, GOAL_ANGLES[i % GOAL_ANGLES.length]);
    const jr = mulberry32(900 + i);
    return {
      title: g.title,
      angle: GOAL_ANGLES[i % GOAL_ANGLES.length],
      plan: [px, py, 0],
      deep: [px + (jr() - 0.5) * 10, py + (jr() - 0.5) * 6, (jr() - 0.5) * 24],
    };
  });

  // ---- 紫微垣 court stars ----
  const court = { plan: [], size: [], gold: [], links: COURT_LINKS };
  for (const [ang, rr, size, gold] of COURT) {
    const [px, py] = polar(rr, ang);
    court.plan.push(px, py, 0);
    court.size.push(size);
    court.gold.push(gold);
  }

  // ---- snapshot v2: projects=planets, tasks=moons, evidence=guests/seated/dust ----
  const catBySkill = new Map(snapshot.skills.map((s) => [s.id, s.category]));
  const goalAngleOf = new Map(snapshot.goals.slice(0, 5).map((g, i) => [g.id, GOAL_ANGLES[i % GOAL_ANGLES.length]]));
  const SIB_OFF = [-13, 9, -6, 15];
  const sibCount = new Map();
  let freeIdx = 0;
  const planets = [];
  snapshot.projects.forEach((p) => {
    const gid = (p.goal_ids || []).find((id) => goalAngleOf.has(id));
    let angle, rr, goalIndex = -1;
    if (gid !== undefined) {
      goalIndex = snapshot.goals.findIndex((g) => g.id === gid);
      const n = sibCount.get(gid) || 0;
      sibCount.set(gid, n + 1);
      angle = goalAngleOf.get(gid) + SIB_OFF[n % SIB_OFF.length];
      rr = R_GOAL + (n % 2 === 0 ? -10 : 10);
    } else {
      angle = -170 + freeIdx * 42;
      freeIdx += 1;
      rr = R_GOAL + 24;
    }
    const [px, py] = polar(rr, angle);
    const jr = mulberry32(3000 + planets.length);
    planets.push({
      id: p.id, title: p.title, status: p.status, progress: p.progress,
      taskCount: p.task_count, goalIndex,
      plan: [px, py, 0],
      deep: [px + (jr() - 0.5) * 8, py + (jr() - 0.5) * 8, (jr() - 0.5) * 10],
    });
  });

  // moons (tasks) clustered around their planet
  const moons = { plan: [], deep: [], size: [], opacity: [] };
  planets.forEach((pl, pi) => {
    const jr = mulberry32(3100 + pi);
    for (let i = 0; i < Math.min(pl.taskCount, 5); i++) {
      const a = jr() * 360, d = 3.8 + jr() * 2.4;
      const [ox, oy] = polar(d, a);
      moons.plan.push(pl.plan[0] + ox, pl.plan[1] + oy, 0);
      moons.deep.push(pl.deep[0] + ox * 1.3, pl.deep[1] + oy * 1.3, pl.deep[2] + (jr() - 0.5) * 4);
      moons.size.push(0.42);
      moons.opacity.push(pl.status === 'active' ? 0.55 : 0.3);
    }
  });

  // guest stars (客星): recent evidence in flight, tail length from strength
  const STRENGTH_LEN = { weak: 4, unrated: 4, medium: 6.5, strong: 9, high_trust: 12 };
  const guests = [];
  snapshot.evidence.filter((e) => e.flying).forEach((e, i) => {
    const jr = mulberry32(3200 + i);
    const ang = jr() * 360;
    const rr = R * (0.42 + 0.42 * jr());
    const [px, py] = polar(rr, ang);
    guests.push({
      id: e.id, title: e.title, date: e.date, strength: e.strength,
      review: e.review_status, plan: [px, py, 0],
      deep: [(jr() * 2 - 1) * 230, (jr() * 2 - 1) * 120, 30 - jr() * 150],
      tailDir: ang + 90 + (jr() - 0.5) * 30,
      tailLen: STRENGTH_LEN[e.strength] || 5,
    });
  });

  // seated evidence: quiet stars near their project planet or skill sector
  const seated = { plan: [], deep: [], size: [], opacity: [] };
  snapshot.evidence.filter((e) => !e.flying).forEach((e, i) => {
    const jr = mulberry32(3300 + i);
    let px, py;
    const pl = e.project_refs.length && planets.find((pp) => pp.id === e.project_refs[0]);
    if (pl) {
      const [ox, oy] = polar(5.5 + jr() * 4, jr() * 360);
      px = pl.plan[0] + ox; py = pl.plan[1] + oy;
    } else {
      const cat = e.skill_ids.length ? catBySkill.get(e.skill_ids[0]) : null;
      const sec = (cat && sectorOf(cat)) || sectors[Math.floor(jr() * sectors.length)];
      const ang = sec.start + 2 + jr() * (sec.width - 4);
      const rr = R * (0.45 + 0.43 * Math.sqrt(jr()));
      [px, py] = polar(rr, ang);
    }
    seated.plan.push(px, py, 0);
    seated.deep.push((jr() * 2 - 1) * 240, (jr() * 2 - 1) * 130, 40 - jr() * 170);
    seated.size.push(0.5);
    seated.opacity.push(0.4);
  });

  // the whole evidence pool as a faint dust ribbon (one mote per entry),
  // each mote trailed by a short directional streak along the band tangent
  const dust = { plan: [], deep: [], size: [], opacity: [], trailPlan: [], trailDeep: [] };
  {
    const P0 = [-1.15 * R, -0.35 * R], P1 = [-0.42 * R, 0.28 * R],
          P2 = [0.42 * R, -0.58 * R], P3 = [1.15 * R, 0.04 * R];
    const n = snapshot.evidence.length;
    snapshot.evidence.forEach((e, i) => {
      const jr = mulberry32(3400 + i);
      const t = n <= 1 ? 0 : i / (n - 1), u = 1 - t;
      const bx = u * u * u * P0[0] + 3 * u * u * t * P1[0] + 3 * u * t * t * P2[0] + t * t * t * P3[0];
      const by = u * u * u * P0[1] + 3 * u * u * t * P1[1] + 3 * u * t * t * P2[1] + t * t * t * P3[1];
      let tx = 3 * u * u * (P1[0] - P0[0]) + 6 * u * t * (P2[0] - P1[0]) + 3 * t * t * (P3[0] - P2[0]);
      let ty = 3 * u * u * (P1[1] - P0[1]) + 6 * u * t * (P2[1] - P1[1]) + 3 * t * t * (P3[1] - P2[1]);
      const tl = Math.hypot(tx, ty) || 1;
      tx /= tl; ty /= tl;
      const hx = bx + (jr() - 0.5) * 10, hy = by + (jr() - 0.5) * 10;
      const dx = bx * 1.9 + (jr() - 0.5) * 20, dy = by * 1.9 + (jr() - 0.5) * 16,
            dz = 30 - t * 130 + (jr() - 0.5) * 20;
      dust.plan.push(hx, hy, 0);
      dust.deep.push(dx, dy, dz);
      dust.trailPlan.push(hx, hy, 0, hx - tx * 2.6, hy - ty * 2.6, 0);
      dust.trailDeep.push(dx, dy, dz, dx - tx * 4.9, dy - ty * 4.9, dz - 2.2);
      dust.size.push(0.75);
      dust.opacity.push(e.review_status === 'needs_review' ? 0.38 : 0.20);
    });
  }

  return { sectors, dim, lit, goals, court, planets, moons, guests, seated, dust };
}

// tiny local color helper (avoid importing three here)
function rgb(hex) {
  return [((hex >> 16) & 255) / 255, ((hex >> 8) & 255) / 255, (hex & 255) / 255];
}
void rgb;
