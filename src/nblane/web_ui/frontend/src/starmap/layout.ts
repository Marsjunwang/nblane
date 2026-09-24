/* Layout math for the growth starmap — TypeScript port of the approved
 * playground layout.js (src/nblane/home_dashboard_component/frontend/
 * playground/layout.js). Every point carries two poses: planisphere (flat
 * carved chart) and deepspace (spread; tilt handled by group/camera). */
import { mulberry32 } from './rng';
import type { StarmapSnapshot } from './snapshot';
import asterismsData from './data/asterisms.json';

export const R = 100;
const S = R / 400;
export const R_IN = 0.3 * R;
export const R_GOAL = 0.54 * R;
export const R_OUT = 0.95 * R;
export const BAND_IN = R + 22 * S;
export const BAND_OUT = R + 52 * S;
export const BAND_TEXT = R + 37 * S;
export const SECTOR_START = -160;

export const INK = 0xe8e2d2;
export const GOLD = 0xdcae55;
export const GOLD_BRIGHT = 0xf0cd7f;

export const GOAL_ANGLES = [-145, -72, -2, 52, 160];
// 刻痕星 (completed goals, design §4): pinned on the disc between the living
// goal bearings — same R_GOAL ring, carved seats of their own, so a completed
// star can never collide with a living one (fixed relative positions, both
// rotate with the disc).
export const CARVED_ANGLES = [-108, -37, 25, 106, -170];

// 北斗环卫 (design 四轮): living goals keep their current ring seats and gain
// dipper names by seat order — names only, no formation lines and no
// repositioning (王军 ruling 2026-09-23 evening). Seats 6/7 (开阳/摇光) are
// reserve seats beyond the current 5-goal cap and always show 虚位 hollow.
export const DIPPER_NAMES = ['天枢', '天璇', '天玑', '天权', '玉衡', '开阳', '摇光'];
export const SEAT_ANGLES = [...GOAL_ANGLES, 200, 262];

// Discrete 4-step color temperature (境态 only — 图态 palette untouched):
// 蓝白 / 月白 / 暖金 / 淡橙, assigned by entity semantics, never continuous.
export const TEMP = {
  blueWhite: [0.78, 0.86, 1.0],
  moonWhite: [0.949, 0.929, 0.878],
  warmGold: [0.98, 0.8, 0.45],
  softOrange: [0.93, 0.66, 0.44],
} as const;

interface AsterismStar {
  x: number;
  y: number;
  mag?: number;
  name?: string;
}
interface Asterism {
  id: string;
  name_zh: string;
  lore: string;
  stars: AsterismStar[];
  lines: [number, number][];
}
const ASTERISMS = new Map(
  (asterismsData.asterisms as Asterism[]).map((a) => [a.id, a]),
);

// 技能域 → 星官 mapping. User-confirmed default table (王军, 2026-09-23,
// phase3.5 mockups README): edit here only. Keys are the server-provided zh
// category names; values are asterisms.json ids + a display name for the
// six 星官 whose real line shapes are not in the data asset yet (翼/房/箕/
// 轸/轩辕/虚 fall back to the generic morphology templates for their shape).
// Shape culling (王军 round-2 review, 2026-09-23): figures that read as a
// near-straight line at sector scale are substituted — 基础 角宿(2星一线)→
// 华盖(覆于帝座,庇荫之基), 研究 心宿(三星近共线)→文昌(司禄主文,掌文运).
// Guard: the vitest linearity check keeps every real-shape entry honest.
const SECTOR_ASTERISM: Record<string, { id: string; name: string }> = {
  系统: { id: 'dou', name: '斗宿' },
  学习力: { id: 'kui', name: '奎宿' },
  基础: { id: 'huagai', name: '华盖' },
  操作: { id: 'shen', name: '参宿' },
  感知: { id: 'bi', name: '毕宿' },
  研究: { id: 'wenchang', name: '文昌' },
  中间件: { id: 'kang', name: '亢宿' },
  影响力: { id: 'liu', name: '柳宿' },
  导航: { id: 'yi', name: '翼宿' },
  战略: { id: 'fang', name: '房宿' },
  运动: { id: 'ji', name: '箕宿' },
  控制: { id: 'zhen', name: '轸宿' },
  领导力: { id: 'xuanyuan', name: '轩辕' },
  仿真: { id: 'xu', name: '虚宿' },
};

/** Exported for the shape-quality guard test (and future mapping UI). */
export const SECTOR_ASTERISM_TABLE = SECTOR_ASTERISM;

/** PCA minor/major axis ratio of an asterism's star spread: ~0 means the
 * figure reads as a straight line at sector scale (culled from mapping). */
export function asterismLinearity(stars: { x: number; y: number }[]): number {
  const n = stars.length;
  if (n < 3) return 0;
  const mx = stars.reduce((a, s) => a + s.x, 0) / n;
  const my = stars.reduce((a, s) => a + s.y, 0) / n;
  let sxx = 0, syy = 0, sxy = 0;
  for (const s of stars) {
    sxx += (s.x - mx) ** 2;
    syy += (s.y - my) ** 2;
    sxy += (s.x - mx) * (s.y - my);
  }
  sxx /= n; syy /= n; sxy /= n;
  const tr = sxx + syy;
  const det = sxx * syy - sxy * sxy;
  const disc = Math.sqrt(Math.max(0, (tr * tr) / 4 - det));
  const l1 = tr / 2 + disc;
  const l2 = tr / 2 - disc;
  return l1 > 0 ? Math.sqrt(l2) / Math.sqrt(l1) : 0;
}

/** Real asterism figure by id (asterisms.json), for shape consumers. */
export function asterismById(id: string): Asterism | undefined {
  return ASTERISMS.get(id);
}

/** Ancient asterism name for a skill-domain sector (rim band label). */
export function sectorAsterismName(categoryName: string): string {
  return SECTOR_ASTERISM[categoryName]?.name ?? categoryName;
}

/** Orbit-managed star position (round-6 fix): morph lerp plan→deep by ch2,
 * plus the slow orbit-rotation residual — gated by ch3 so 图态 always lands
 * EXACTLY on plan, no matter what phase the orbit reached during 境态.
 * (The round-6 drift bug: the residual used to apply at all ch values, so
 * the phase frozen on leaving 境态 displaced stars off R_GOAL — invisible
 * before the fan-out, massive after it.) */
export function orbitPos(
  plan: number[],
  deep: number[],
  phase: number,
  ch2: number,
  ch3: number,
): [number, number, number] {
  const rx = deep[0] * Math.cos(phase) - deep[1] * Math.sin(phase);
  const ry = deep[0] * Math.sin(phase) + deep[1] * Math.cos(phase);
  return [
    plan[0] + (deep[0] - plan[0]) * ch2 + (rx - deep[0]) * ch3,
    plan[1] + (deep[1] - plan[1]) * ch2 + (ry - deep[1]) * ch3,
    plan[2] + (deep[2] - plan[2]) * ch2,
  ];
}

/** Anchored variant (planets riding a goal star): the follow term compares
 * the anchor's CURRENT position against its ch2-MORPHED base (never its deep
 * base), and the planet's own orbit residual is likewise ch3-gated. */
export function orbitPosAnchored(
  plan: number[],
  deep: number[],
  anchorDeep: number[],
  anchorMorph: number[],
  anchorNow: number[],
  phase: number,
  ch2: number,
  ch3: number,
): [number, number, number] {
  const ox = deep[0] - anchorDeep[0];
  const oy = deep[1] - anchorDeep[1];
  const rx = ox * Math.cos(phase) - oy * Math.sin(phase);
  const ry = ox * Math.sin(phase) + oy * Math.cos(phase);
  return [
    plan[0] + (deep[0] - plan[0]) * ch2 + (anchorNow[0] - anchorMorph[0]) + (rx - ox) * ch3,
    plan[1] + (deep[1] - plan[1]) * ch2 + (anchorNow[1] - anchorMorph[1]) + (ry - oy) * ch3,
    plan[2] + (deep[2] - plan[2]) * ch2,
  ];
}

// Asterism morphology templates (ported from the v2 mockup).
type Slot = [number, number, number];
const TEMPLATES: { slots: Slot[]; links: [number, number][] }[] = [
  {
    // branch tree
    slots: [
      [0, 4, 1.15], [-0.5, -1.5, 0.68], [-4, -6, 0.62], [-8, -8.5, 0.78],
      [-11.2, -7.2, 0.58], [3, -5.5, 0.62], [6.8, -7.8, 0.72],
    ],
    links: [[0, 1], [1, 2], [2, 3], [3, 4], [1, 5], [5, 6]],
  },
  {
    // gentle chain
    slots: [
      [-11.8, 2.8, 0.62], [-6, 0.5, 0.72], [-0.5, -1, 0.92], [5, -0.5, 0.68],
      [10.8, 1.8, 0.6],
    ],
    links: [[0, 1], [1, 2], [2, 3], [3, 4]],
  },
  {
    // bow arc
    slots: [
      [-8.8, -1.8, 0.62], [-4.5, 2, 0.7], [0, 3.5, 0.9], [4.5, 2, 0.7],
      [8.8, -1.8, 0.62],
    ],
    links: [[0, 1], [1, 2], [2, 3], [3, 4]],
  },
  {
    // tight cluster
    slots: [[-2, -1.2, 0.85], [2.2, -0.8, 0.65], [0, 2, 0.6]],
    links: [[0, 1], [1, 2], [2, 0]],
  },
  {
    // zigzag
    slots: [
      [-9.2, -2.5, 0.62], [-4, 2.2, 0.72], [1, -2.2, 0.82], [6, 2.5, 0.65],
      [10.2, -0.8, 0.6],
    ],
    links: [[0, 1], [1, 2], [2, 3], [3, 4]],
  },
];

// 紫微垣 court cluster (decorative, from the v2 mockup).
const COURT: [number, number, number, number][] = [
  [-40, 18, 0.72, 1], [-78, 11.5, 0.6, 0], [-112, 15.5, 0.68, 0], [-148, 12.5, 0.58, 0],
  [168, 19, 0.78, 1], [142, 11.5, 0.58, 0], [116, 17, 0.65, 0], [88, 11, 0.58, 0],
  [58, 15, 0.72, 1], [34, 21, 0.6, 0], [-32, 24, 0.62, 0], [-95, 22.5, 0.65, 1],
];
const COURT_LINKS: [number, number][] = [[0, 1], [1, 2], [2, 3], [5, 6], [6, 7], [8, 9]];

function polar(r: number, deg: number): [number, number] {
  const a = (deg * Math.PI) / 180;
  return [r * Math.cos(a), r * Math.sin(a)];
}

function normAngle(a: number): number {
  a = a % 360;
  if (a > 180) a -= 360;
  if (a < -180) a += 360;
  return a;
}

export interface Sector {
  id: string;
  name: string;
  /** Ancient asterism name for the rim band (mapped via SECTOR_ASTERISM). */
  asterism: string;
  start: number;
  width: number;
  count: number;
}

export interface DimField {
  plan: number[];
  deep: number[];
  size: number[];
  opacity: number[];
  core: number[];
  ring: number[];
  legacyRing: number[];
  color: number[];
  /** 境态 4-step color temperature targets (图态 keeps `color`). */
  deepColor: number[];
  filler: number[];
  deepOpScale: number[];
  deepSizeScale: number[];
}

export interface LitField {
  plan: number[];
  deep: number[];
  size: number[];
  opacity: number[];
  core: number[];
  ring: number[];
  color: number[];
  /** 境态 4-step color temperature per star (蓝白 bright / 月白 dim). */
  deepColor: number[];
  links: number[];
  skills: {
    id: string;
    label: string;
    category: string;
    status: string;
    evidenceCount: number;
  }[];
}

export interface GoalPoint {
  id: string;
  title: string;
  /** 'active' | 'paused' | 'completed' (completed = 刻痕星). */
  status: string;
  angle: number;
  /** Dipper seat name (天枢…玉衡) for living goals; undefined for 刻痕星 —
   * completion revokes the name (design §1: 星名是活资源). */
  seatName?: string;
  plan: number[];
  deep: number[];
}

/** One dipper seat on the R_GOAL ring: name + bearing; goalIndex points into
 * StarmapLayout.goals when a living goal holds the seat, null when 虚位. */
export interface DipperSeat {
  name: string;
  angle: number;
  goalIndex: number | null;
}

export interface CourtField {
  plan: number[];
  size: number[];
  gold: number[];
  links: [number, number][];
}

export interface Planet {
  id: string;
  title: string;
  status: string;
  progress: number | null;
  taskCount: number;
  goalIndex: number;
  plan: number[];
  deep: number[];
}

export interface PointCloud {
  plan: number[];
  deep: number[];
  size: number[];
  opacity: number[];
}

export interface Guest {
  id: string;
  title: string;
  date: string;
  strength: string;
  review: string;
  plan: number[];
  deep: number[];
  tailDir: number;
  tailLen: number;
}

export interface DustField extends PointCloud {
  trailPlan: number[];
  trailDeep: number[];
}

/** Etched sector-asterism figure: the full 星官 shape carved faintly (空圈
 * seats for shape stars with no lit/learning member). All core=0, ring=1. */
export interface EtchedField extends PointCloud {
  color: number[];
  /** 境态 ignite tints (per-slot temperature, same anchor as the figure). */
  deepColor: number[];
}

export interface StarmapLayout {
  sectors: Sector[];
  dim: DimField;
  lit: LitField;
  goals: GoalPoint[];
  seats: DipperSeat[];
  court: CourtField;
  planets: Planet[];
  moons: PointCloud;
  guests: Guest[];
  seated: PointCloud;
  dust: DustField;
  etched: EtchedField;
  /** Full sector-asterism line figures (flat xyz segment endpoints, plan
   * coords) — the etched carve under the brighter formed-member links. */
  shapeLinesPlan: number[];
  /** Same segments in 境态 constellation coords (per-slot z jitter, so the
   * persisting faint lines are not coplanar). */
  shapeLinesDeep: number[];
}

export function buildLayout(snapshot: StarmapSnapshot): StarmapLayout {
  const rnd = mulberry32(20260921);

  // ---- sectors: width proportional to real per-category skill counts ----
  const total = snapshot.categories.reduce((a, c) => a + c.count, 0) || 1;
  const sectors: Sector[] = [];
  let acc = SECTOR_START;
  for (const cat of snapshot.categories) {
    const width = (cat.count / total) * 360;
    sectors.push({
      id: cat.id,
      name: cat.name,
      asterism: sectorAsterismName(cat.name),
      start: acc,
      width,
      count: cat.count,
    });
    acc += width;
  }
  const sectorOf = (id: string) => sectors.find((s) => s.id === id);

  // ---- dim star field: real locked nodes + synthetic filler ----
  // shape language (石刻三家星记): locked=空圈(core0,ring1) learning=实点(core1,ring0)
  // lit=点外套圈(core1,ring1); filler stars are plain dots and carry no semantics
  const WARM = [0.961, 0.918, 0.824]; // #f5ead2, unified star color for both states
  const dim: DimField = {
    plan: [], deep: [], size: [], opacity: [], core: [], ring: [], legacyRing: [],
    color: [], deepColor: [], filler: [], deepOpScale: [], deepSizeScale: [],
  };
  const pushDim = (
    px: number, py: number, dx: number, dy: number, dz: number,
    size: number, opacity: number, isFiller: boolean, tint: number[],
    deepOpScale: number, deepSizeScale: number, core: number, ring: number,
    legacyRing: number, deepTint: readonly number[] = TEMP.moonWhite,
  ) => {
    dim.plan.push(px, py, 0);
    dim.deep.push(dx, dy, dz);
    dim.size.push(size);
    dim.opacity.push(opacity);
    dim.core.push(core);
    dim.ring.push(ring);
    dim.legacyRing.push(legacyRing);
    dim.color.push(tint[0], tint[1], tint[2]);
    dim.deepColor.push(deepTint[0], deepTint[1], deepTint[2]);
    dim.filler.push(isFiller ? 1 : 0);
    dim.deepOpScale.push(deepOpScale);
    dim.deepSizeScale.push(deepSizeScale);
  };
  const deepSpread = (): [number, number, number] => [
    (rnd() * 2 - 1) * 250,
    (rnd() * 2 - 1) * 140,
    40 - rnd() * 180,
  ];

  const byCat = new Map<string, StarmapSnapshot['skills']>();
  for (const sk of snapshot.skills) {
    if (!byCat.has(sk.category)) byCat.set(sk.category, []);
    byCat.get(sk.category)!.push(sk);
  }

  // locked real nodes: empty carved rings (空圈)
  for (const sk of snapshot.skills) {
    if (sk.lit || sk.status === 'learning') continue;
    const sec = sectorOf(sk.category);
    if (!sec) continue;
    const ang = sec.start + 1.5 + rnd() * (sec.width - 3);
    const rr = R * (0.34 + 0.58 * Math.sqrt(rnd()));
    const [px, py] = polar(rr, ang);
    const [dx, dy, dz] = deepSpread();
    pushDim(
      px, py, dx, dy, dz, 0.62 + rnd() * 0.2, 0.34 + rnd() * 0.08, false,
      WARM, 0.6, 0.55, 0, 1, rnd() < 0.3 ? 1 : 0,
    );
  }

  // synthetic filler, distributed across sectors by weight
  const FILLER = 1800;
  for (const sec of sectors) {
    const n = Math.round((sec.count / total) * FILLER);
    for (let i = 0; i < n; i++) {
      let ang: number, rr: number;
      if (rnd() < 0.15) {
        // 紫微垣: dense central disc
        ang = rnd() * 360;
        rr = R_IN * (0.52 + 0.46 * rnd());
        if (Math.abs(normAngle(ang)) < 25) continue;
      } else {
        ang = sec.start + 1.3 + rnd() * (sec.width - 2.6);
        rr = R * (0.33 + 0.61 * Math.sqrt(rnd()));
      }
      const [px, py] = polar(rr, ang);
      const [dx, dy, dz] = deepSpread();
      // 图态 tint lottery unchanged (subtle warm/blue variation on the stone).
      const goldTint = [1.0, 0.88, 0.69];
      const blueTint = [0.74, 0.81, 1.0];
      const tintRoll = rnd();
      const tint = tintRoll > 0.975 ? goldTint : tintRoll > 0.95 ? blueTint : WARM;
      // 境态 pseudo-magnitude: power-law brightness (~5% bright end) +
      // discrete 4-step color temperature (bright winners run 蓝白-hot).
      const mag = Math.pow(rnd(), 8); // 0..1, heavily skewed to faint
      const bright = mag > 0.42; // ≈5% of the field
      const deepOpScale = Math.min(1.15, 0.15 + Math.pow(rnd(), 1.8) * 0.55 + mag * 0.75);
      const deepSizeScale = 0.35 + Math.pow(rnd(), 2) * 0.35 + mag * 0.6;
      const deepTint = bright
        ? TEMP.blueWhite
        : tintRoll > 0.92
          ? TEMP.softOrange
          : tintRoll > 0.88
            ? TEMP.warmGold
            : TEMP.moonWhite;
      pushDim(
        px, py, dx, dy, dz,
        bright ? 0.62 : 0.34 + rnd() * 0.22,
        bright ? 0.38 : 0.10 + rnd() * 0.12,
        true, tint, deepOpScale, deepSizeScale, 1, 0, rnd() < 0.18 ? 1 : 0,
        deepTint,
      );
    }
  }

  // ---- lit / learning skill asterisms + etched sector figures ----
  // 星官真形 (design 二轮§2 + scope-B ruling): each mapped sector carries its
  // real asterism shape (asterisms.json) — lit/learning members occupy shape
  // slots in order, remaining slots stay as faint etched 空圈; the full line
  // figure is carved faintly under the brighter formed-member links. Sectors
  // mapped to 星官 missing from the data asset (翼/房/箕/轸/轩辕/虚) fall back
  // to the generic morphology templates; unmapped empty sectors stay blank.
  //
  // 星官点燃 (round-5, 2026-09-24): in 境态 the figure stays put as a living
  // constellation — deep coords anchor to the figure (×1.08 breath, per-slot
  // z jitter so nothing is coplanar) instead of scattering into the field.
  const lit: LitField = {
    plan: [], deep: [], size: [], opacity: [], core: [], ring: [], color: [],
    deepColor: [], links: [], skills: [],
  };
  const etched: EtchedField = { plan: [], deep: [], size: [], opacity: [], color: [], deepColor: [] };
  const shapeLinesPlan: number[] = [];
  const shapeLinesDeep: number[] = [];
  const evCountBySkill = new Map<string, number>();
  snapshot.evidence.forEach((e) =>
    e.skill_ids.forEach((id) => evCountBySkill.set(id, (evCountBySkill.get(id) || 0) + 1)),
  );
  let vertexCount = 0;
  snapshot.categories.forEach((cat, ci) => {
    const sec = sectorOf(cat.id);
    if (!sec) return;
    const mapping = SECTOR_ASTERISM[cat.name];
    const aster = mapping ? ASTERISMS.get(mapping.id) : undefined;
    const members = (byCat.get(cat.id) || []).filter((s) => s.lit || s.status === 'learning');
    if (!members.length && !mapping) return; // unmapped empty sector: blank
    const mid = sec.start + sec.width / 2;
    const [ccx, ccy] = polar(R * 0.72, mid);
    const jrnd = mulberry32(500 + ci);

    let slots: Slot[];
    let links: [number, number][];
    let slotTints: (readonly number[])[];
    if (aster) {
      // real figure: rotate so local +y points radially outward, scale tight
      // into the sector arc (texture tier, not a centerpiece); no jitter —
      // the true geometry is the point (形自证).
      const arcLen = (sec.width * Math.PI) / 180 * (R * 0.72);
      const scale = Math.min(11, Math.max(6, arcLen * 0.24));
      const th = ((mid - 90) * Math.PI) / 180;
      const cs = Math.cos(th);
      const sn = Math.sin(th);
      slots = aster.stars.map((s) => {
        const mag = s.mag ?? 5;
        const os = 0.55 + Math.min(3, Math.max(0, 5.6 - mag)) * 0.11;
        return [(s.x * cs - s.y * sn) * scale, (s.x * sn + s.y * cs) * scale, os] as Slot;
      });
      // 境态色温: bright stars run 蓝白, the rest 月白 (discrete steps)
      slotTints = aster.stars.map((s) => ((s.mag ?? 5) < 3 ? TEMP.blueWhite : TEMP.moonWhite));
      links = aster.lines;
    } else {
      const tpl = TEMPLATES[ci % TEMPLATES.length];
      slots = tpl.slots.map((s) => [s[0], s[1], s[2]] as Slot);
      slotTints = tpl.slots.map(() => TEMP.moonWhite);
      links = tpl.links;
    }
    while (slots.length < members.length) {
      // extend as a chain if needed
      const last = slots[slots.length - 1];
      slots.push([last[0] + 4.5, last[1] + (jrnd() - 0.5) * 3, 0.58]);
      slotTints.push(TEMP.moonWhite);
    }
    // per-slot constellation anchors for 境态 (shared by member stars, etched
    // seats and line endpoints so the figure stays connected, not coplanar)
    const slotDeep: [number, number, number][] = slots.map(([ox, oy]) => [
      ccx + ox * 1.08,
      ccy + oy * 1.08,
      (jrnd() - 0.5) * 36,
    ]);
    // full figure carve (faint etched lines under the formed-member links);
    // the carve dissolves early in the morph (境不留图线)
    for (const [a, b] of links) {
      if (a >= slots.length || b >= slots.length) continue;
      shapeLinesPlan.push(
        ccx + slots[a][0], ccy + slots[a][1], 0,
        ccx + slots[b][0], ccy + slots[b][1], 0,
      );
      shapeLinesDeep.push(
        slotDeep[a][0], slotDeep[a][1], slotDeep[a][2],
        slotDeep[b][0], slotDeep[b][1], slotDeep[b][2],
      );
    }
    const base = vertexCount;
    members.forEach((sk, i) => {
      const [ox, oy, os] = slots[i];
      // template figures keep the organic jitter; real figures stay true
      const jx = aster ? 0 : (jrnd() - 0.5) * 1.6;
      const jy = aster ? 0 : (jrnd() - 0.5) * 1.6;
      const px = ccx + ox + jx;
      const py = ccy + oy + jy;
      const [dx, dy, dz] = slotDeep[i];
      lit.plan.push(px, py, 0);
      lit.deep.push(dx, dy, dz);
      lit.size.push(os * (sk.lit ? 1.15 : 0.9));
      lit.opacity.push(sk.lit ? 0.95 : 0.55);
      lit.core.push(1); // 实点
      lit.ring.push(sk.lit ? 1 : 0); // 点亮 = 点外套圈
      lit.color.push(0.961, 0.918, 0.824); // unified warm white
      const tint = slotTints[i];
      lit.deepColor.push(tint[0], tint[1], tint[2]);
      lit.skills.push({
        id: sk.id,
        label: sk.label,
        category: sk.category,
        status: sk.status,
        evidenceCount: evCountBySkill.get(sk.id) || 0,
      });
      vertexCount += 1;
    });
    // shape slots with no member: small open rings (小空圈, Suzhou 石刻 style)
    // in 图态; in 境态 they ignite as the constellation's fainter stars
    // (color-temperature per slot, same anchor as the figure).
    for (let i = members.length; i < slots.length; i++) {
      const [ox, oy, os] = slots[i];
      const [dx, dy, dz] = slotDeep[i];
      etched.plan.push(ccx + ox, ccy + oy, 0);
      etched.deep.push(dx, dy, dz);
      etched.size.push(Math.max(0.7, os * 0.85));
      etched.opacity.push(0.16);
      etched.color.push(TEMP.moonWhite[0], TEMP.moonWhite[1], TEMP.moonWhite[2]);
      const tint = slotTints[i];
      etched.deepColor.push(tint[0], tint[1], tint[2]);
    }
    // only formed asterisms (>= 3 stars) get links; segments join actual star points
    if (members.length >= 3) {
      for (const [a, b] of links) {
        if (a < members.length && b < members.length) lit.links.push(base + a, base + b);
      }
    }
  });

  // ---- goals: living stars (active/paused) on GOAL_ANGLES, completed ones
  // (刻痕星) on CARVED_ANGLES. L.goals order = placement order; planets index
  // into THIS array (goalIndex), not into snapshot.goals. Living goals hold
  // dipper seats in order (天枢…); remaining seats stay 虚位 (hollow).
  const living = snapshot.goals.filter((g) => g.status !== 'completed');
  const carved = snapshot.goals.filter((g) => g.status === 'completed');
  const placed = [
    ...living.slice(0, GOAL_ANGLES.length).map((g, i) => ({ g, angle: GOAL_ANGLES[i], seat: i })),
    ...carved.slice(0, CARVED_ANGLES.length).map((g, i) => ({ g, angle: CARVED_ANGLES[i], seat: -1 })),
  ];
  const goals: GoalPoint[] = placed.map(({ g, angle, seat }, i) => {
    const [px, py] = polar(R_GOAL, angle);
    const jr = mulberry32(900 + i);
    // 境态 = 展开 (round-4): each living goal's system gets its own radial
    // lane (bearing kept from the disc seat), so planet systems never share
    // sweep tracks. Lane step 26 > 2× the widest planet orbit lane (≤12.6),
    // so no two systems' orbits intersect at any rotation phase. 刻痕星 host
    // no systems and stay on a shared quiet lane near the ring.
    const lane = seat >= 0 ? 58 + seat * 26 : 60;
    const [dx, dy] = polar(lane, angle);
    return {
      id: g.id,
      title: g.title,
      status: g.status || 'active',
      angle,
      seatName: seat >= 0 ? DIPPER_NAMES[seat] : undefined,
      plan: [px, py, 0],
      deep: [dx, dy, (jr() - 0.5) * 20],
    };
  });
  const seats: DipperSeat[] = SEAT_ANGLES.map((angle, si) => ({
    name: DIPPER_NAMES[si],
    angle,
    // goals[0..4] are the living slice in seat order (carved goals append after)
    goalIndex: si < GOAL_ANGLES.length && goals[si]?.seatName ? si : null,
  }));

  // ---- 紫微垣 court stars ----
  const court: CourtField = { plan: [], size: [], gold: [], links: COURT_LINKS };
  for (const [ang, rr, size, gold] of COURT) {
    const [px, py] = polar(rr, ang);
    court.plan.push(px, py, 0);
    court.size.push(size);
    court.gold.push(gold);
  }

  // ---- projects=planets, tasks=moons, evidence=guests/seated/dust ----
  const catBySkill = new Map(snapshot.skills.map((s) => [s.id, s.category]));
  const goalIndexOf = new Map(goals.map((g, i) => [g.id, i]));
  const goalAngleOf = new Map(goals.map((g) => [g.id, g.angle]));
  const goalDeepOf = new Map(goals.map((g) => [g.id, g.deep]));
  const SIB_OFF = [-13, 9, -6, 15];
  const sibCount = new Map<string, number>();
  let freeIdx = 0;
  const planets: Planet[] = [];
  // 行星轨道分级 (round-4): siblings of one goal get stepped orbit lanes in
  // 境态 (each its own track). Free planets take a circumpolar lane beyond
  // the outermost goal system so they never cross a system's orbit.
  const livingLaneCount = living.slice(0, GOAL_ANGLES.length).length;
  const FREE_LANE = 58 + livingLaneCount * 26 + 18;
  snapshot.projects.forEach((p) => {
    const gid = (p.goal_ids || []).find((id) => goalAngleOf.has(id));
    let angle: number, rr: number, goalIndex = -1;
    let deep: number[];
    const jr = mulberry32(3000 + planets.length);
    if (gid !== undefined) {
      goalIndex = goalIndexOf.get(gid) ?? -1;
      const n = sibCount.get(gid) || 0;
      sibCount.set(gid, n + 1);
      angle = goalAngleOf.get(gid)! + SIB_OFF[n % SIB_OFF.length];
      // 图态归环 (round-6): planets sit exactly on R_GOAL — angular sibling
      // offsets only, no radial jitter; deep lanes (fan-out) unchanged.
      rr = R_GOAL;
      const gd = goalDeepOf.get(gid)!;
      const orbitLane = 5 + Math.min(n, 4) * 2.2; // stepped lanes, ≤ 12.6
      const [ox, oy] = polar(orbitLane, jr() * 360);
      deep = [gd[0] + ox, gd[1] + oy, gd[2] + (jr() - 0.5) * 8];
    } else {
      angle = -170 + freeIdx * 42;
      freeIdx += 1;
      rr = R_GOAL; // free planets ring in on R_GOAL too (was +24)
      const [fx, fy] = polar(FREE_LANE, angle);
      deep = [fx, fy, (jr() - 0.5) * 12];
    }
    const [px, py] = polar(rr, angle);
    planets.push({
      id: p.id,
      title: p.title,
      status: p.status,
      progress: p.progress,
      taskCount: p.task_count,
      goalIndex,
      plan: [px, py, 0],
      deep,
    });
  });

  // moons (tasks) clustered around their planet
  const moons: PointCloud = { plan: [], deep: [], size: [], opacity: [] };
  planets.forEach((pl, pi) => {
    const jr = mulberry32(3100 + pi);
    for (let i = 0; i < Math.min(pl.taskCount, 5); i++) {
      const a = jr() * 360;
      const d = 3.8 + jr() * 2.4;
      const [ox, oy] = polar(d, a);
      moons.plan.push(pl.plan[0] + ox, pl.plan[1] + oy, 0);
      moons.deep.push(
        pl.deep[0] + ox * 1.3,
        pl.deep[1] + oy * 1.3,
        pl.deep[2] + (jr() - 0.5) * 4,
      );
      moons.size.push(0.42);
      moons.opacity.push(pl.status === 'active' ? 0.55 : 0.3);
    }
  });

  // guest stars (客星): recent evidence in flight, tail length from strength
  const STRENGTH_LEN: Record<string, number> = {
    weak: 4, unrated: 4, medium: 6.5, strong: 9, high_trust: 12,
  };
  const guests: Guest[] = [];
  snapshot.evidence
    .filter((e) => e.flying)
    .forEach((e, i) => {
      const jr = mulberry32(3200 + i);
      const ang = jr() * 360;
      const rr = R * (0.42 + 0.42 * jr());
      const [px, py] = polar(rr, ang);
      guests.push({
        id: e.id,
        title: e.title,
        date: e.date,
        strength: e.strength,
        review: e.review_status,
        plan: [px, py, 0],
        deep: [(jr() * 2 - 1) * 230, (jr() * 2 - 1) * 120, 30 - jr() * 150],
        tailDir: ang + 90 + (jr() - 0.5) * 30,
        tailLen: STRENGTH_LEN[e.strength] || 5,
      });
    });

  // seated evidence: quiet stars near their project planet or skill sector
  const seated: PointCloud = { plan: [], deep: [], size: [], opacity: [] };
  snapshot.evidence
    .filter((e) => !e.flying)
    .forEach((e, i) => {
      const jr = mulberry32(3300 + i);
      let px: number, py: number;
      const pl = e.project_refs.length && planets.find((pp) => pp.id === e.project_refs[0]);
      if (pl) {
        const [ox, oy] = polar(5.5 + jr() * 4, jr() * 360);
        px = pl.plan[0] + ox;
        py = pl.plan[1] + oy;
      } else {
        const cat = e.skill_ids.length ? catBySkill.get(e.skill_ids[0]) : undefined;
        const sec = (cat && sectorOf(cat)) || sectors[Math.floor(jr() * sectors.length)];
        if (!sec) return;
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
  const dust: DustField = { plan: [], deep: [], size: [], opacity: [], trailPlan: [], trailDeep: [] };
  {
    const P0 = [-1.15 * R, -0.35 * R],
      P1 = [-0.42 * R, 0.28 * R],
      P2 = [0.42 * R, -0.58 * R],
      P3 = [1.15 * R, 0.04 * R];
    const n = snapshot.evidence.length;
    snapshot.evidence.forEach((e, i) => {
      const jr = mulberry32(3400 + i);
      const t = n <= 1 ? 0 : i / (n - 1);
      const u = 1 - t;
      const bx = u * u * u * P0[0] + 3 * u * u * t * P1[0] + 3 * u * t * t * P2[0] + t * t * t * P3[0];
      const by = u * u * u * P0[1] + 3 * u * u * t * P1[1] + 3 * u * t * t * P2[1] + t * t * t * P3[1];
      let tx = 3 * u * u * (P1[0] - P0[0]) + 6 * u * t * (P2[0] - P1[0]) + 3 * t * t * (P3[0] - P2[0]);
      let ty = 3 * u * u * (P1[1] - P0[1]) + 6 * u * t * (P2[1] - P1[1]) + 3 * t * t * (P3[1] - P2[1]);
      const tl = Math.hypot(tx, ty) || 1;
      tx /= tl;
      ty /= tl;
      const hx = bx + (jr() - 0.5) * 10;
      const hy = by + (jr() - 0.5) * 10;
      const dx = bx * 1.9 + (jr() - 0.5) * 20,
        dy = by * 1.9 + (jr() - 0.5) * 16,
        dz = 30 - t * 130 + (jr() - 0.5) * 20;
      dust.plan.push(hx, hy, 0);
      dust.deep.push(dx, dy, dz);
      dust.trailPlan.push(hx, hy, 0, hx - tx * 2.6, hy - ty * 2.6, 0);
      dust.trailDeep.push(dx, dy, dz, dx - tx * 4.9, dy - ty * 4.9, dz - 2.2);
      dust.size.push(0.75);
      dust.opacity.push(e.review_status === 'needs_review' ? 0.38 : 0.2);
    });
  }

  return { sectors, dim, lit, goals, seats, court, planets, moons, guests, seated, dust, etched, shapeLinesPlan, shapeLinesDeep };
}
