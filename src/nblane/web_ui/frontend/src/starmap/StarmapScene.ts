/* Growth starmap scene — Three.js port of the approved playground main.js
 * (src/nblane/home_dashboard_component/frontend/playground/main.js), wrapped
 * as a disposable class for the SPA home page. The playground's full-viewport
 * DOM (bg layers / vignette / tooltip / canvas) is created inside the given
 * container; cartouche, briefing, toggle and the inscription detail card are
 * React-owned and driven through callbacks + element refs. */
import * as THREE from 'three';
import { Text } from 'troika-three-text';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import gsap from 'gsap';
import { EffectComposer, RenderPass, EffectPass, BloomEffect } from 'postprocessing';
import { interpolate, converter } from 'culori';
import {
  buildLayout, R, R_IN, R_GOAL, R_OUT, BAND_IN, BAND_OUT, BAND_TEXT,
  INK, GOLD, GOLD_BRIGHT, TEMP, orbitPos, orbitPosAnchored,
  type StarmapLayout,
} from './layout';
import { mulberry32 } from './rng';
import type { StarmapSnapshot } from './snapshot';
import fontUrl from './assets/NotoSerifSC-subset.ttf?url';
import imingUrl from './assets/fonts/IMing-subset.ttf?url';
import fellUrl from './assets/fonts/IMFellEnglish-subset.ttf?url';

export interface StarmapSelection {
  kind: 'north' | 'goal' | 'planet' | 'guest' | 'skill';
  /** Stable domain id: 'north' for the pole star, goal/project/evidence/skill id. */
  id: string;
  title: string;
  rows: [string, string][];
}

export interface StarmapSceneOptions {
  /** Morph-state callback: t in [0,1] (0=图态 planisphere, 1=境态 deepspace). */
  onMorph?: (t: number) => void;
  /** Click selection; null when dismissed. */
  onSelect?: (sel: StarmapSelection | null) => void;
  /** DOM nodes owned by React that the morph drives directly (opacity/text). */
  domRefs?: {
    cartouche?: HTMLElement | null;
    briefing?: HTMLElement | null;
    toggle?: HTMLButtonElement | null;
  };
  /** 显真 (design 四轮): true names primary + ancient-name notes when on.
   * Persisted by the caller (localStorage nblane.starmap.reveal). */
  reveal?: boolean;
  initialState?: 'planisphere' | 'deepspace';
}

type FadeMat = { mat: THREE.LineBasicMaterial; plan: number; deep: number; ch: number };
type LabelRec = {
  t: Text;
  fade: 'band' | 'north' | 'goal';
  planPos: number[];
  deepPos: number[] | null;
  /** Creation-time rotation.z — 图态 carving angle. In 境态 labels
   * counter-rotate by -chart.rotation.z·ch2 so names stay upright. */
  rotZ: number;
  /** Collision-fade priority (境态): 0 北极星 > 1 斗星名 > 2 虚位注. */
  prio: number;
  /** Segments of one label share a group id (a group never fights itself). */
  grpId: number;
  ca: number;
  caTarget: number;
};
type Morphable = (THREE.Points | THREE.LineSegments) & {
  userData: {
    plan?: Float32Array;
    deep?: Float32Array;
    orbitManaged?: boolean;
    [k: string]: unknown;
  };
};

const chan = (t: number, start: number) => Math.min(1, Math.max(0, (t - start) / 0.4));

/** 行星时间弧 (round-5): ultra-faint self-erasing planet trails. OFF by
 * default — the user wants the orbit rings evaluated first; flip to true to
 * compare (star-trails rationale: rotation draws the circles). */
const PLANET_TRAILS = false;

/** Partition the dim field into carved-on-disc stars vs decorative filler
 * (the parallax background layer). Triples/quads stay index-aligned. */
function subsetDim(dim: StarmapLayout['dim'], wantFiller: boolean) {
  const out = {
    plan: [] as number[], deep: [] as number[], size: [] as number[],
    opacity: [] as number[], core: [] as number[], ring: [] as number[],
    color: [] as number[], deepColor: [] as number[], filler: [] as number[],
    deepOpScale: [] as number[], deepSizeScale: [] as number[],
  };
  for (let i = 0; i < dim.filler.length; i++) {
    if ((dim.filler[i] === 1) !== wantFiller) continue;
    out.plan.push(dim.plan[i * 3], dim.plan[i * 3 + 1], dim.plan[i * 3 + 2]);
    out.deep.push(dim.deep[i * 3], dim.deep[i * 3 + 1], dim.deep[i * 3 + 2]);
    out.size.push(dim.size[i]);
    out.opacity.push(dim.opacity[i]);
    out.core.push(dim.core[i]);
    out.ring.push(dim.ring[i]);
    out.color.push(dim.color[i * 3], dim.color[i * 3 + 1], dim.color[i * 3 + 2]);
    out.deepColor.push(dim.deepColor[i * 3], dim.deepColor[i * 3 + 1], dim.deepColor[i * 3 + 2]);
    out.filler.push(dim.filler[i]);
    out.deepOpScale.push(dim.deepOpScale[i]);
    out.deepSizeScale.push(dim.deepSizeScale[i]);
  }
  return out;
}

export class StarmapScene {
  private root: HTMLElement;
  private heart: HTMLElement;
  private snapshot: StarmapSnapshot;
  private opts: StarmapSceneOptions;
  private L: StarmapLayout;
  private renderer: THREE.WebGLRenderer;
  private composer: EffectComposer;
  private bloom: BloomEffect;
  private fxPass: EffectPass;
  private scene = new THREE.Scene();
  private camera: THREE.PerspectiveCamera;
  private chart = new THREE.Group();
  private canvas: HTMLCanvasElement;
  private bgStone: HTMLDivElement;
  private bgDeep: HTMLDivElement;
  private bgDusk: HTMLDivElement;
  private vignette: HTMLDivElement;
  private tooltip: HTMLDivElement;
  private fadeMats: FadeMat[] = [];
  /** Custom opacity curves across the morph channels (dip-and-return etc.). */
  private fadeFns: {
    mat: THREE.LineBasicMaterial;
    fn: (ch1: number, ch2: number, ch3: number) => number;
  }[] = [];
  private shapeLines: THREE.LineSegments | null = null;
  private asterLinks: THREE.LineSegments | null = null;
  /** 境态 orbit ellipses (round-5, 100k Stars ruling): one thin warm-gold
   * ring per planet lane, riding its goal star at the fanned-out position;
   * `flow` is the slow light-trickle arc along the ring. */
  private orbitRings: {
    ring: THREE.LineLoop;
    ringMat: THREE.LineBasicMaterial;
    flow: THREE.Line;
    flowMat: THREE.LineBasicMaterial;
    goalIdx: number;
    phase: number;
    shimmer: number;
  }[] = [];
  /** 行星时间弧 (round-5): self-erasing motion trails — OFF by default
   * (PLANET_TRAILS flag; evaluate with rings on before enabling). */
  private planetTrails: {
    line: THREE.Line;
    mat: THREE.LineBasicMaterial;
    hist: Float32Array;
  }[] = [];
  private trailTimer = 0;
  /** 星官点燃: aCore plan→deep lerp (etched 空圈 ignite into solid stars). */
  private coreLerp: { pts: THREE.Points; plan: Float32Array; deep: Float32Array }[] = [];
  private labelObjs: LabelRec[] = [];
  private morphables: Morphable[] = [];
  private reveal: boolean;
  private dimPts!: THREE.Points;
  /** Decorative background field (parallax-lite layer, 0.3× in 境态). */
  private dimBgPts!: THREE.Points;
  private bgLayer = new THREE.Group();
  private litPts!: THREE.Points;
  private goalPts!: THREE.Points;
  private northPts!: THREE.Points;
  private northVacant: boolean;
  private planetPts!: THREE.Points;
  private guestPts!: THREE.Points;
  private planetInnerPts!: THREE.Points;
  private moonPts!: THREE.Points;
  private guestTails!: THREE.LineSegments;
  private glows: { spr: THREE.Sprite; mat: THREE.SpriteMaterial; getPos: () => number[]; maxOpacity: number }[] = [];
  private guestGlows: { spr: THREE.Sprite; mat: THREE.SpriteMaterial; idx: number; breathe: boolean }[] = [];
  private nebulae: { spr: THREE.Sprite; mat: THREE.SpriteMaterial; op: number }[] = [];
  /** 尘埃带泼墨长河: diffuse wash sprites under the dust motes (境态). */
  private dustRiver: { spr: THREE.Sprite; mat: THREE.SpriteMaterial; base: number }[] = [];
  /** 境态 prominence tiers: per-cloud deep size/opacity multipliers. */
  private tiered: {
    pts: THREE.Points;
    baseSize: Float32Array;
    baseOp: Float32Array | null;
    ds: number;
    dop: number;
  }[] = [];
  /** 境态 4-step color temperature morph targets (aColor lerp by ch2). */
  private colored: { pts: THREE.Points; plan: Float32Array; deep: Float32Array }[] = [];
  private goalLabelGroups: {
    goalIdx: number;
    segs: Text[];
    base: [number, number][];
    anchor: number[];
  }[] = [];
  private selRing: THREE.LineLoop;
  private controls: OrbitControls | null = null;

  private state = {
    t: 0,
    density: 1,
    bloom: 1,
    w1: 0,
    w2: 0.3,
    w3: 0.6,
    duskPos: 0.45,
    duskAmt: 1,
    ch1: 0,
    ch2: 0,
    ch3: 0,
  };
  private tween: gsap.core.Tween | null = null;
  private hoverIdx = -1;
  private selectedIdx = -1;
  private hoverables: { title: string; info: string; pos: () => number[] }[] = [];
  private clickables: {
    kind: StarmapSelection['kind'];
    id: string;
    idx: number;
    title: string;
    pos: () => number[];
  }[] = [];
  private focusTween: gsap.core.Tween | null = null;
  private focusToken = 0;
  private dragging = false;
  private dragLastX = 0;
  private dragLastT = 0;
  private dragDist = 0;
  private spinVel = 0;
  private spinFactor = 1;
  private lastPointerActive = -1e9;
  private clock = new THREE.Clock();
  private rafId = 0;
  private disposed = false;
  private resizeObserver: ResizeObserver | null = null;
  private labelsPending = 0;
  private segPending = 0;
  private labelGrpSeq = 0;
  private collisionTick = 0;
  private reducedMotion: boolean;
  private coarsePointer: boolean;
  private softGL: boolean;
  private camPlan = { pos: new THREE.Vector3(0, 4, 346), look: new THREE.Vector3(0, 0, 0) };
  private camDeep = { pos: new THREE.Vector3(0, 72, 232), look: new THREE.Vector3(0, -4, 0) };

  private goalPeriods: number[];
  private planetPeriods: number[];
  private guestPeriods: number[];
  private goalPhase: number[];
  private planetPhase: number[];
  private guestPhase: number[];
  private goalDeepBase: number[][];
  private planetDeepBase: number[][];
  private guestDeepBase: number[][];
  private moonDeepBase: number[][];
  private moonPlanet: number[] = [];
  private tailOffsets: number[][][] = [];
  private guestBaseOpacity!: Float32Array;

  private onPointerMoveWindow = (e: PointerEvent) => this.onPointerMove(e);
  private onPointerActive = () => {
    this.lastPointerActive = performance.now();
  };
  private onClickWindow = (e: MouseEvent) => this.onClick(e);
  private onKeydown = (e: KeyboardEvent) => {
    if (e.key === 'Escape') this.closeDetail();
  };
  private onWheel = (() => {
    let acc = 0;
    return (e: WheelEvent) => {
      acc += e.deltaY;
      if (Math.abs(acc) > 260) {
        this.goTo(acc < 0 ? 1 : 0);
        acc = 0;
      }
    };
  })();

  /** `root` carries the background/vignette layers; `heart` (the 画心) sizes
   * the canvas and camera fit. */
  constructor(root: HTMLElement, heart: HTMLElement, snapshot: StarmapSnapshot, opts: StarmapSceneOptions = {}) {
    this.root = root;
    this.heart = heart;
    this.snapshot = snapshot;
    this.opts = opts;
    this.L = buildLayout(snapshot);
    // 虚位空星 (design §2): when the North Star is unset the pole is an
    // empty carved ring with a slow faint pulse instead of the gold core.
    this.northVacant = !(snapshot.north?.is_set ?? snapshot.north_star.trim().length > 0);
    this.reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
    this.coarsePointer = matchMedia('(pointer: coarse)').matches;
    this.reveal = opts.reveal ?? false;
    this.state.t = opts.initialState === 'deepspace' ? 1 : 0;

    // ---------- DOM layers (bg cross-fade lives in the compositor) ----------
    const layer = (cls: string): HTMLDivElement => {
      const el = document.createElement('div');
      el.className = cls;
      this.root.appendChild(el);
      return el;
    };
    this.bgStone = layer('starmap-bg');
    this.bgDusk = layer('starmap-bg');
    this.bgDeep = layer('starmap-bg');
    this.vignette = layer('starmap-vignette');
    this.canvas = document.createElement('canvas');
    this.canvas.className = 'starmap-canvas';
    this.heart.appendChild(this.canvas);
    this.tooltip = layer('starmap-tooltip');
    this.tooltip.style.display = 'none';

    // ---------- renderer / scene ----------
    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      alpha: true,
    });
    this.renderer.setClearColor(0x000000, 0); // DOM layer carries the background
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    this.camera = new THREE.PerspectiveCamera(45, 1, 1, 2000);
    this.fitPlanCamera();
    this.scene.add(this.chart);
    // parallax-lite (境态): the decorative background field lives in a child
    // group counter-rotated each frame so it trails the disc at 0.3×; at
    // ch2=0 the counter-rotation is zero and the stone carving is untouched.
    this.chart.add(this.bgLayer);

    this.bakeBackgrounds();
    this.buildLinework();

    // dim field split: locked real nodes + etched semantics stay carved on
    // the disc (dimPts); the synthetic filler becomes the parallax background
    // (dimBgPts). Both share the per-star deep magnitude scales.
    const dimLocked = subsetDim(this.L.dim, false);
    const dimFiller = subsetDim(this.L.dim, true);
    this.dimPts = this.makePoints(dimLocked);
    this.dimBgPts = this.makePoints(dimFiller, this.bgLayer);
    for (const pts of [this.dimPts, this.dimBgPts]) {
      pts.userData.filler = pts === this.dimBgPts ? dimFiller.filler : dimLocked.filler;
      pts.userData.baseOpacity = new Float32Array(pts.geometry.attributes.aOpacity.array);
      pts.userData.baseSize = new Float32Array(pts.geometry.attributes.aSize.array);
      pts.userData.baseRing = new Float32Array(pts.geometry.attributes.aRing.array);
    }
    this.dimPts.userData.deepOpScale = new Float32Array(dimLocked.deepOpScale);
    this.dimPts.userData.deepSizeScale = new Float32Array(dimLocked.deepSizeScale);
    this.dimBgPts.userData.deepOpScale = new Float32Array(dimFiller.deepOpScale);
    this.dimBgPts.userData.deepSizeScale = new Float32Array(dimFiller.deepSizeScale);

    this.litPts = this.makePoints({
      plan: this.L.lit.plan,
      deep: this.L.lit.deep,
      size: this.L.lit.size,
      opacity: this.L.lit.opacity,
      core: this.L.lit.core,
      ring: this.L.lit.ring,
      color: this.L.lit.color,
      // 星官点燃 (round-5): 境态 stays on the figure as a living constellation
      deepColor: this.L.lit.deepColor,
    });
    this.addTier(this.litPts, 1.15, 1);
    // goal stars by status (design §4): active = lit gold; paused = dimmed;
    // completed = 刻痕星 — gold killed, 月白 at ~30%, an empty carved ring
    // (no core, no glow, no breathing), pinned on the rotating disc.
    const MOON_WHITE = [0.949, 0.929, 0.878];
    this.goalPts = this.makePoints({
      plan: this.L.goals.flatMap((g) => g.plan),
      deep: this.L.goals.flatMap((g) => g.deep),
      size: this.L.goals.map((g) => (g.status === 'completed' ? 2.2 : 2.6)),
      opacity: this.L.goals.map((g) =>
        g.status === 'completed' ? 0.3 : g.status === 'paused' ? 0.55 : 1,
      ),
      core: this.L.goals.map((g) => (g.status === 'completed' ? 0 : 1)),
      ring: this.L.goals.map(() => 1),
      color: this.L.goals.flatMap((g) =>
        g.status === 'completed' ? MOON_WHITE : [0.91, 0.72, 0.36],
      ),
      // 境态: 目标 = 金 (discrete temperature step); 刻痕星 stays 月白.
      deepColor: this.L.goals.flatMap((g) =>
        g.status === 'completed' ? [...TEMP.moonWhite] : [0.95, 0.76, 0.34],
      ),
    });
    this.addTier(this.goalPts, 1.18, 1);
    const courtPts = this.makePoints({
      plan: this.L.court.plan,
      deep: this.L.court.plan.map((v, i) => (i % 3 === 2 ? (v ? v : 0) : v * 1.6)),
      size: this.L.court.size,
      opacity: this.L.court.gold.map((g) => (g ? 1 : 0.85)),
      core: this.L.court.gold.map(() => 1),
      ring: this.L.court.gold.map(() => 0),
      color: this.L.court.gold.flatMap((g) =>
        g ? [0.91, 0.72, 0.36] : [0.961, 0.918, 0.824],
      ),
    });
    this.northPts = this.makePoints(
      this.northVacant
        ? {
            // 虚位: empty ring, moon-white, faint (pulse animates opacity)
            plan: [0, 0, 0],
            deep: [0, 0, 0],
            size: [4.4],
            opacity: [0.3],
            core: [0],
            ring: [1],
            color: MOON_WHITE,
          }
        : {
            plan: [0, 0, 0],
            deep: [0, 0, 0],
            size: [4.4],
            opacity: [1],
            core: [1],
            ring: [0],
            color: [0.98, 0.85, 0.55],
            // 境态: 北极星 = 暖金, brightest tier
            deepColor: [...TEMP.warmGold],
          },
    );
    if (!this.northVacant) this.addTier(this.northPts, 1.35, 1);
    this.planetPts = this.makePoints({
      plan: this.L.planets.flatMap((p) => p.plan),
      deep: this.L.planets.flatMap((p) => p.deep),
      size: this.L.planets.map(() => 3.0),
      opacity: this.L.planets.map((p) => (p.status === 'active' ? 0.9 : 0.35)),
      core: this.L.planets.map(() => 0.4),
      ring: this.L.planets.map(() => 1),
      color: this.L.planets.flatMap(() => [0.961, 0.918, 0.824]),
      // 境态: 行星 = 淡橙
      deepColor: this.L.planets.flatMap(() => [...TEMP.softOrange]),
    });
    // 光晕收敛 (round-4): planets have no dedicated glow sprites — the blobs
    // were the ring/core points under bloom; deep tier roughly halves them.
    this.addTier(this.planetPts, 0.6, 0.85);
    this.moonPts = this.makePoints({
      plan: this.L.moons.plan,
      deep: this.L.moons.deep,
      size: this.L.moons.size,
      opacity: this.L.moons.opacity,
      core: this.L.moons.size.map(() => 1),
      ring: this.L.moons.size.map(() => 0),
      color: this.L.moons.size.flatMap(() => [0.961, 0.918, 0.824]),
      deepColor: this.L.moons.size.flatMap(() => [...TEMP.moonWhite]),
    });
    this.addTier(this.moonPts, 0.9, 1);
    const seatedPts = this.makePoints({
      plan: this.L.seated.plan,
      deep: this.L.seated.deep,
      size: this.L.seated.size,
      opacity: this.L.seated.opacity,
      core: this.L.seated.size.map(() => 1),
      ring: this.L.seated.size.map(() => 0),
      color: this.L.seated.size.flatMap(() => [0.961, 0.918, 0.824]),
      deepColor: this.L.seated.size.flatMap(() => [...TEMP.moonWhite]),
    });
    this.addTier(seatedPts, 0.9, 1);
    this.guestPts = this.makePoints({
      plan: this.L.guests.flatMap((g) => g.plan),
      deep: this.L.guests.flatMap((g) => g.deep),
      size: this.L.guests.map(() => 1.15),
      opacity: this.L.guests.map(() => 0.95),
      core: this.L.guests.map(() => 1),
      ring: this.L.guests.map(() => 0),
      color: this.L.guests.flatMap(() => [1.0, 0.95, 0.85]),
      // 境态: 客星 = 蓝白
      deepColor: this.L.guests.flatMap(() => [...TEMP.blueWhite]),
    });
    // size-only tier: guest opacity is re-asserted per frame (no pulse on the
    // carved dot), so applyMorph must not write aOpacity here.
    this.addTier(this.guestPts, 0.95, null);
    const dustPts = this.makePoints({
      plan: this.L.dust.plan,
      deep: this.L.dust.deep,
      size: this.L.dust.size,
      opacity: this.L.dust.opacity,
      core: this.L.dust.size.map(() => 1),
      ring: this.L.dust.size.map(() => 0),
      color: this.L.dust.size.flatMap(() => [0.961, 0.918, 0.824]),
      // 境态: 尘埃 = 月白 (coolest, faintest tier)
      deepColor: this.L.dust.size.flatMap(() => [0.88, 0.9, 0.94]),
    });
    this.addTier(dustPts, 0.8, 1);
    // etched sector-asterism figures: 空圈 seats of the 星官 shapes. 图态 =
    // carvings; 境态 = 星官点燃 — the seats ignite into the constellation's
    // fainter solid stars (core 0→0.85, opacity up, per-slot temperature).
    const etchedPts = this.makePoints({
      plan: this.L.etched.plan,
      deep: this.L.etched.deep,
      size: this.L.etched.size,
      opacity: this.L.etched.opacity,
      core: this.L.etched.size.map(() => 0),
      ring: this.L.etched.size.map(() => 1),
      color: this.L.etched.color,
      deepColor: this.L.etched.deepColor.slice(),
      deepCore: this.L.etched.size.map(() => 0.85),
    });
    this.addTier(etchedPts, 1.05, 1.8);
    // dust directional streaks along the band tangent
    const dustTrails = (() => {
      const geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(this.L.dust.trailPlan), 3));
      const line = new THREE.LineSegments(geo, this.lineMat(INK, 0.26, 0.22, 3));
      this.chart.add(line);
      const m = line as unknown as Morphable;
      m.userData.plan = new Float32Array(this.L.dust.trailPlan);
      m.userData.deep = new Float32Array(this.L.dust.trailDeep);
      return m;
    })();
    // planets: a second inner carved ring so they read as planets at a glance
    this.planetInnerPts = this.makePoints({
      plan: this.L.planets.flatMap((p) => p.plan),
      deep: this.L.planets.flatMap((p) => p.deep),
      size: this.L.planets.map(() => 2.0),
      opacity: this.L.planets.map((p) => (p.status === 'active' ? 0.9 : 0.35)),
      core: this.L.planets.map(() => 0),
      ring: this.L.planets.map(() => 1),
      color: this.L.planets.flatMap(() => [0.961, 0.918, 0.824]),
      deepColor: this.L.planets.flatMap(() => [...TEMP.softOrange]),
    });
    this.addTier(this.planetInnerPts, 0.6, 0.85);
    // 星官真形连线 (round-5 星官点燃): the etched diagram dissolves early in
    // the morph, then the constellation's lines re-emerge faint and
    // depth-attenuated (per-slot z jitter — not coplanar) in 境态.
    if (this.L.shapeLinesPlan.length) {
      const geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(this.L.shapeLinesPlan), 3));
      const mat = new THREE.LineBasicMaterial({
        color: INK,
        transparent: true,
        opacity: 0.14,
        depthWrite: false,
      });
      const line = new THREE.LineSegments(geo, mat);
      this.chart.add(line);
      this.shapeLines = line;
      this.shapeLines.userData.plan = new Float32Array(this.L.shapeLinesPlan);
      this.shapeLines.userData.deep = new Float32Array(this.L.shapeLinesDeep);
      // dip-and-return: carve fades out with ch1, constellation lines fade in with ch3
      this.fadeFns.push({ mat, fn: (c1, _c2, c3) => 0.14 * (1 - c1) + 0.05 * c3 });
    }

    // 境态轨道环 (round-5, 100k Stars ruling): one thin warm-gold ellipse per
    // planet lane, riding its goal star at the fanned-out lane position — the
    // big survey circles stay 图态-only (they dissolve early, above). A slow
    // light-flow arc trickles along each ring (微光沿圈流转; reduced-motion
    // freezes it). Rings exist only in 境态 (opacity scales with ch3).
    {
      const jr = mulberry32(6600);
      for (const p of this.L.planets) {
        if (p.goalIndex < 0) continue; // 游离行星: no ring (circumpolar lane)
        const g = this.L.goals[p.goalIndex];
        const radius = Math.hypot(p.deep[0] - g.deep[0], p.deep[1] - g.deep[1]);
        const ringMat = new THREE.LineBasicMaterial({
          color: GOLD,
          transparent: true,
          opacity: 0,
          depthWrite: false,
        });
        const ring = new THREE.LineLoop(
          new THREE.BufferGeometry().setFromPoints(this.circlePoints(radius, 72)),
          ringMat,
        );
        this.chart.add(ring);
        // light-flow arc: ~16° of the ring, slightly brighter gold
        const flowMat = new THREE.LineBasicMaterial({
          color: GOLD_BRIGHT,
          transparent: true,
          opacity: 0,
          depthWrite: false,
        });
        const flowPts: THREE.Vector3[] = [];
        for (let i = 0; i <= 10; i++) {
          const a = (i / 10) * (Math.PI * 2) * 0.045;
          flowPts.push(new THREE.Vector3(radius * Math.cos(a), radius * Math.sin(a), 0));
        }
        const flow = new THREE.Line(new THREE.BufferGeometry().setFromPoints(flowPts), flowMat);
        ring.add(flow);
        this.orbitRings.push({
          ring,
          ringMat,
          flow,
          flowMat,
          goalIdx: p.goalIndex,
          phase: jr() * Math.PI * 2,
          shimmer: jr() * Math.PI * 2,
        });
      }
    }

    // 行星时间弧 (round-5): OFF by default — evaluate the orbit rings first
    // (flag at module top). Self-erasing motion trails, shorter and dimmer
    // than guest tails; the orbit is drawn by the planet's own motion.
    if (PLANET_TRAILS) {
      const N = 22;
      for (const p of this.L.planets) {
        const hist = new Float32Array(N * 3);
        for (let i = 0; i < N; i++) {
          hist[i * 3] = p.deep[0];
          hist[i * 3 + 1] = p.deep[1];
          hist[i * 3 + 2] = p.deep[2];
        }
        const geo = new THREE.BufferGeometry();
        geo.setAttribute('position', new THREE.BufferAttribute(hist.slice(), 3));
        const colors = new Float32Array(N * 3);
        for (let i = 0; i < N; i++) {
          const f = i / (N - 1); // 0 = tail, 1 = head
          colors[i * 3] = 0.86 * f * f;
          colors[i * 3 + 1] = 0.68 * f * f;
          colors[i * 3 + 2] = 0.33 * f * f;
        }
        geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
        const mat = new THREE.LineBasicMaterial({
          vertexColors: true,
          transparent: true,
          opacity: 0,
          blending: THREE.AdditiveBlending,
          depthWrite: false,
        });
        const line = new THREE.Line(geo, mat);
        line.frustumCulled = false;
        this.chart.add(line);
        this.planetTrails.push({ line, mat, hist });
      }
    }

    // planet -> goal hairlines (dissolve with ch1)
    {
      const pts: THREE.Vector3[] = [];
      for (const p of this.L.planets) {
        if (p.goalIndex < 0) continue;
        const g = this.L.goals[p.goalIndex];
        pts.push(new THREE.Vector3(p.plan[0], p.plan[1], 0));
        pts.push(new THREE.Vector3(g.plan[0], g.plan[1], 0));
      }
      this.chart.add(
        new THREE.LineSegments(
          new THREE.BufferGeometry().setFromPoints(pts),
          this.lineMat(INK, 0.22, 0, 1),
        ),
      );
    }
    // progress arcs around planets (only when honestly derivable)
    {
      const pts: THREE.Vector3[] = [];
      for (const p of this.L.planets) {
        if (p.progress === null || p.progress === undefined || p.progress <= 0) continue;
        const segs = 32;
        const r = 4.6;
        for (let i = 0; i < segs; i++) {
          const a0 = Math.PI / 2 - (i / segs) * p.progress * Math.PI * 2;
          const a1 = Math.PI / 2 - ((i + 1) / segs) * p.progress * Math.PI * 2;
          pts.push(
            new THREE.Vector3(p.plan[0] + r * Math.cos(a0), p.plan[1] + r * Math.sin(a0), 0),
          );
          pts.push(
            new THREE.Vector3(p.plan[0] + r * Math.cos(a1), p.plan[1] + r * Math.sin(a1), 0),
          );
        }
      }
      if (pts.length) {
        this.chart.add(
          new THREE.LineSegments(
            new THREE.BufferGeometry().setFromPoints(pts),
            this.lineMat(GOLD, 0.55, 0, 1),
          ),
        );
      }
    }
    // guest-star tails (客星拖尾)
    this.guestTails = (() => {
      const plan: number[] = [];
      const deep: number[] = [];
      for (const g of this.L.guests) {
        const dir = (g.tailDir * Math.PI) / 180;
        const dx = Math.cos(dir);
        const dy = Math.sin(dir);
        const px = -dy;
        const py = dx;
        const n = 5;
        for (let i = 0; i < n; i++) {
          for (const t of [i / n, (i + 1) / n]) {
            const wob = Math.sin(t * 2.5) * 1.1;
            plan.push(
              g.plan[0] - dx * g.tailLen * t + px * wob,
              g.plan[1] - dy * g.tailLen * t + py * wob,
              0,
            );
            deep.push(
              g.deep[0] - dx * g.tailLen * 1.3 * t + px * wob,
              g.deep[1] - dy * g.tailLen * 1.3 * t + py * wob,
              g.deep[2],
            );
          }
        }
      }
      const geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(plan), 3));
      const line = new THREE.LineSegments(geo, this.lineMat(INK, 0.55, 0.4, 3));
      this.chart.add(line);
      return line;
    })();
    {
      const m = this.guestTails as unknown as Morphable;
      m.userData.plan = new Float32Array(m.geometry.attributes.position.array);
      m.userData.deep = new Float32Array(
        this.L.guests.flatMap((g) => {
          const dir = (g.tailDir * Math.PI) / 180;
          const dx = Math.cos(dir);
          const dy = Math.sin(dir);
          const px = -dy;
          const py = dx;
          const out: number[] = [];
          const n = 5;
          for (let i = 0; i < n; i++) {
            for (const t of [i / n, (i + 1) / n]) {
              const wob = Math.sin(t * 2.5) * 1.1;
              out.push(
                g.deep[0] - dx * g.tailLen * 1.3 * t + px * wob,
                g.deep[1] - dy * g.tailLen * 1.3 * t + py * wob,
                g.deep[2],
              );
            }
          }
          return out;
        }),
      );
    }

    // ---------- glow sprites (deepspace) ----------
    const glowTex = this.makeGlowTexture();
    const addGlow = (getPos: () => number[], scale: number, color: number, maxOpacity: number) => {
      const mat = new THREE.SpriteMaterial({
        map: glowTex,
        color,
        transparent: true,
        opacity: 0,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      });
      const spr = new THREE.Sprite(mat);
      spr.scale.set(scale, scale, 1);
      this.chart.add(spr);
      this.glows.push({ spr, mat, getPos, maxOpacity });
      return spr;
    };
    addGlow(() => [0, 0, 0], 20, 0xffd98a, this.northVacant ? 0 : 0.8); // north star warm core glow
    addGlow(() => [0, 0, 0], 40, 0x96a8dc, this.northVacant ? 0 : 0.1); // north star cool halo
    this.L.goals.forEach((g, i) =>
      addGlow(() => {
        const p = this.goalPts.geometry.attributes.position.array as Float32Array;
        return [p[i * 3], p[i * 3 + 1], p[i * 3 + 2]];
      }, 9, 0xffcd78, g.status === 'completed' ? 0 : g.status === 'paused' ? 0.12 : 0.35),
    );
    // 呼吸 halos: the breath moves ONLY the halo, never the star point itself
    this.guestGlows = this.L.guests.map((g, i) => {
      const mat = new THREE.SpriteMaterial({
        map: glowTex,
        color: 0xdde8ff, // cool halo to match the 蓝白 guest temperature step
        transparent: true,
        opacity: 0,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      });
      const spr = new THREE.Sprite(mat);
      spr.scale.set(5.5, 5.5, 1);
      this.chart.add(spr);
      return { spr, mat, idx: i, breathe: g.review === 'needs_review' };
    });
    // 尘埃带泼墨长河 (境态): a diffuse radial-gradient wash UNDER the dust
    // motes; sprite count and opacity track the real evidence count, so the
    // river densifies as the pool grows. Guests still fly out of it.
    {
      const n = this.L.dust.deep.length / 3;
      if (n > 0) {
        const jr = mulberry32(7700);
        const count = Math.max(6, Math.min(26, Math.round(n * 0.6)));
        const density = Math.min(1, n / 24);
        for (let k = 0; k < count; k++) {
          const t = count <= 1 ? 0 : k / (count - 1);
          const i = Math.min(n - 1, Math.floor(t * n));
          const mat = new THREE.SpriteMaterial({
            map: glowTex,
            color: 0x8f99ad, // indigo moon-white wash
            transparent: true,
            opacity: 0,
            depthWrite: false,
          });
          const spr = new THREE.Sprite(mat);
          const sc = 30 + jr() * 26;
          spr.scale.set(sc, sc, 1);
          spr.position.set(
            this.L.dust.deep[i * 3],
            this.L.dust.deep[i * 3 + 1],
            this.L.dust.deep[i * 3 + 2] - 4,
          );
          spr.visible = false;
          spr.renderOrder = -1; // under the dust motes
          this.chart.add(spr);
          // accretion-disk luminosity (round-5): inner-bright, outer-dim —
          // not a uniform wash
          const rr = Math.hypot(this.L.dust.deep[i * 3], this.L.dust.deep[i * 3 + 1]);
          const falloff = Math.min(1.15, Math.max(0.3, 1.25 - rr / 240));
          this.dustRiver.push({ spr, mat, base: 0.06 * density * falloff * (0.7 + jr() * 0.6) });
        }
      }
    }
    // nebulae stay put when the chart tilts (not in the chart group)
    for (const [x, y, z, sc, color, op] of [
      [150, 70, -120, 260, 0x7a5638, 0.13],
      [-170, -60, -100, 300, 0x5d6070, 0.1],
      [0, 120, -140, 200, 0x46527a, 0.085],
    ] as const) {
      const mat = new THREE.SpriteMaterial({
        map: glowTex,
        color,
        transparent: true,
        opacity: 0,
        depthWrite: false,
      });
      const spr = new THREE.Sprite(mat);
      spr.position.set(x, y, z);
      spr.scale.set(sc, sc, 1);
      spr.visible = false;
      this.scene.add(spr);
      this.nebulae.push({ mat, op, spr });
    }

    // ---------- labels (troika SDF) ----------
    this.buildLabels();

    // ---------- postprocessing ----------
    const glCtx = this.renderer.getContext();
    const dbgInfo = glCtx.getExtension('WEBGL_debug_renderer_info');
    const glRendererName = dbgInfo
      ? String(glCtx.getParameter(dbgInfo.UNMASKED_RENDERER_WEBGL))
      : '';
    this.softGL = /swiftshader|llvmpipe|software/i.test(glRendererName);
    this.composer = new EffectComposer(this.renderer);
    this.composer.addPass(new RenderPass(this.scene, this.camera));
    this.bloom = new BloomEffect({ luminanceThreshold: 0.65, intensity: 0, mipmapBlur: true });
    this.fxPass = new EffectPass(this.camera, this.bloom);
    this.composer.addPass(this.fxPass);
    this.composer.setSize(
      this.heart.clientWidth || 1600,
      this.heart.clientHeight || 900,
    );

    // ---------- morphables ----------
    this.morphables = [
      this.dimPts, this.dimBgPts, this.litPts, this.goalPts, courtPts, this.northPts,
      this.planetPts, this.planetInnerPts, this.moonPts, seatedPts,
      this.guestPts, dustPts, etchedPts,
      this.guestTails as unknown as Morphable,
      dustTrails,
    ] as Morphable[];
    // constellation line sets morph with their stars (figure-anchored deep)
    if (this.shapeLines) this.morphables.push(this.shapeLines as unknown as Morphable);
    if (this.asterLinks) this.morphables.push(this.asterLinks as unknown as Morphable);
    for (const pts of [
      this.goalPts, this.planetPts, this.planetInnerPts, this.moonPts,
      this.guestPts, this.guestTails,
    ]) {
      pts.userData.orbitManaged = true;
    }

    // 北斗虚位 (design 四轮): every dipper seat without a living goal keeps a
    // faint hollow carved ring (开阳/摇光 are reserve seats beyond the current
    // 5-goal cap); the 星表「+」panel is the entry point for the next goal.
    const vacantSeats = this.L.seats.filter((s) => s.goalIndex === null);
    if (vacantSeats.length) {
      const seatPlan = vacantSeats.flatMap((s) => {
        const a = (s.angle * Math.PI) / 180;
        return [R_GOAL * Math.cos(a), R_GOAL * Math.sin(a), 0];
      });
      const seatsPts = this.makePoints({
        plan: seatPlan,
        deep: seatPlan.slice(),
        size: vacantSeats.map(() => 2.0),
        opacity: vacantSeats.map(() => 0.16),
        core: vacantSeats.map(() => 0),
        ring: vacantSeats.map(() => 1),
        color: vacantSeats.flatMap(() => [0.961, 0.918, 0.824]),
      });
      this.morphables.push(seatsPts as Morphable);
    }

    // ---------- motion bookkeeping ----------
    // 境态调参 (2026-09-23): everything slowed — goals/planets/guests drift
    // on long periods; the 1h/rev disc spin stays; twinkle/scintillation
    // (breathing halos, 虚位 pulse) is deliberately untouched (王军 veto).
    this.goalPeriods = this.L.goals.map((_, i) => 150 + i * 36);
    this.planetPeriods = this.L.planets.map((_, i) => 100 + i * 14);
    this.guestPeriods = this.L.guests.map((_, i) => 26 + i * 6.5);
    this.goalPhase = this.L.goals.map(() => 0);
    this.planetPhase = this.L.planets.map(() => 0);
    this.guestPhase = this.L.guests.map(() => 0);
    this.guestDeepBase = this.L.guests.map((g) => g.deep.slice());
    this.planetDeepBase = this.L.planets.map((p) => p.deep.slice());
    this.goalDeepBase = this.L.goals.map((g) => g.deep.slice());
    this.L.planets.forEach((p, pi) => {
      for (let i = 0; i < Math.min(p.taskCount, 5); i++) this.moonPlanet.push(pi);
    });
    this.moonDeepBase = [];
    for (let i = 0; i < this.L.moons.deep.length; i += 3) {
      this.moonDeepBase.push(this.L.moons.deep.slice(i, i + 3));
    }
    const tails = this.guestTails as unknown as Morphable;
    this.L.guests.forEach((g, i) => {
      const arr: number[][] = [];
      for (let v = 0; v < 10; v++) {
        const k = (i * 10 + v) * 3;
        arr.push([
          tails.userData.deep![k] - g.deep[0],
          tails.userData.deep![k + 1] - g.deep[1],
          tails.userData.deep![k + 2] - g.deep[2],
        ]);
      }
      this.tailOffsets.push(arr);
    });

    // ---------- hover / click ----------
    const attrPos = (pts: THREE.Points, i: number): number[] => {
      const a = pts.geometry.attributes.position.array as Float32Array;
      return [a[i * 3], a[i * 3 + 1], a[i * 3 + 2]];
    };
    this.hoverables = [
      {
        title: '北极星',
        info: this.northVacant
          ? '虚位 · 点击立星'
          : snapshot.north_star.split(/[，。]/)[0],
        pos: () => [0, 0, 0],
      },
      ...this.L.goals.map((g, i) => ({
        title: g.title,
        info:
          g.status === 'completed'
            ? '刻痕星 · 已镌刻'
            : g.status === 'paused'
              ? '目标恒星 · 暂停'
              : '目标恒星',
        pos: () => attrPos(this.goalPts, i),
      })),
      ...this.L.planets.map((p, i) => ({
        title: p.title,
        info:
          `${p.status === 'active' ? '行星 · 在轨' : '行星 · 归档'} · 任务 ${p.taskCount}` +
          (p.progress !== null && p.progress !== undefined
            ? ` · 进度 ${Math.round(p.progress * 100)}%`
            : ''),
        pos: () => attrPos(this.planetPts, i),
      })),
      ...this.L.guests.map((g, i) => ({
        title: g.title,
        info: `客星 · ${g.date} · ${g.strength}${g.review === 'needs_review' ? ' · 待评审' : ''}`,
        pos: () => attrPos(this.guestPts, i),
      })),
    ];
    this.clickables = [
      { kind: 'north', id: 'north', idx: -1, title: '北极星', pos: () => [0, 0, 0] },
      ...this.L.goals.map((g, i) => ({
        kind: 'goal' as const, id: g.id, idx: i, title: g.title, pos: () => attrPos(this.goalPts, i),
      })),
      ...this.L.planets.map((p, i) => ({
        kind: 'planet' as const, id: p.id, idx: i, title: p.title, pos: () => attrPos(this.planetPts, i),
      })),
      ...this.L.guests.map((g, i) => ({
        kind: 'guest' as const, id: g.id, idx: i, title: g.title, pos: () => attrPos(this.guestPts, i),
      })),
      ...this.L.lit.skills.map((s, i) => ({
        kind: 'skill' as const, id: s.id, idx: i, title: s.label, pos: () => attrPos(this.litPts, i),
      })),
    ];
    this.selRing = new THREE.LineLoop(
      new THREE.BufferGeometry().setFromPoints(this.circlePoints(3.2, 48)),
      new THREE.LineBasicMaterial({
        color: GOLD_BRIGHT,
        transparent: true,
        opacity: 0.8,
        depthWrite: false,
      }),
    );
    this.selRing.visible = false;
    this.chart.add(this.selRing);

    // ---------- listeners ----------
    // ResizeObserver on the heart (not window): AppShell layout settles a
    // frame after the window event, and sizing the renderer off stale box
    // metrics leaves the chart shrunken/offset.
    const ro = new ResizeObserver(() => this.onResize());
    ro.observe(this.heart);
    this.resizeObserver = ro;
    window.addEventListener('pointermove', this.onPointerMoveWindow, { passive: true });
    window.addEventListener('pointermove', this.onPointerActive, { passive: true });
    window.addEventListener('click', this.onClickWindow);
    window.addEventListener('keydown', this.onKeydown);
    window.addEventListener('wheel', this.onWheel, { passive: true });
    this.canvas.addEventListener('pointerdown', (e) => {
      // 用户手势永远赢: grabbing the disc cancels any in-flight focus.
      this.focusToken += 1;
      this.focusTween?.kill();
      this.focusTween = null;
      if (this.coarsePointer || this.state.t >= 0.5) return;
      this.dragging = true;
      this.dragLastX = e.clientX;
      this.dragLastT = performance.now();
      this.dragDist = 0;
      this.spinVel = 0;
      this.canvas.setPointerCapture(e.pointerId);
    });
    this.canvas.addEventListener('pointermove', (e) => {
      if (!this.dragging) return;
      const now = performance.now();
      const dx = e.clientX - this.dragLastX;
      const dtm = Math.max((now - this.dragLastT) / 1000, 0.008);
      this.dragLastX = e.clientX;
      this.dragLastT = now;
      this.dragDist += Math.abs(dx);
      const d = dx * 0.004;
      this.chart.rotation.z += d;
      this.spinVel = this.spinVel * 0.75 + (d / dtm) * 0.25;
    });
    const endDrag = () => {
      this.dragging = false;
    };
    this.canvas.addEventListener('pointerup', endDrag);
    this.canvas.addEventListener('pointercancel', endDrag);

    // touch: pan + pinch on the planisphere, clamped near the chart
    if (this.coarsePointer) {
      this.controls = new OrbitControls(this.camera, this.canvas);
      this.controls.enableRotate = false;
      this.controls.enableDamping = true;
      this.controls.dampingFactor = 0.08;
      this.controls.enableZoom = true;
      this.controls.zoomSpeed = 0.9;
      this.controls.enablePan = true;
      this.controls.panSpeed = 0.8;
    }

    this.guestBaseOpacity = new Float32Array(
      this.guestPts.geometry.attributes.aOpacity.array,
    );

    this.onResize();
    this.applyMorph();
    if (opts.initialState === 'deepspace') this.goTo(1, true);
    this.loop();
  }

  /** Read-only debug probe: current chart-space radial distance of each goal
   * star from the pole. In 图态 this must equal R_GOAL for every goal, at
   * every morph cycle count (round-6 drift bug hunt). */
  goalRadials(): { id: string; seatName?: string; r: number }[] {
    const attr = this.goalPts.geometry.attributes.position.array as Float32Array;
    return this.L.goals.map((g, i) => ({
      id: g.id,
      seatName: g.seatName,
      r: Math.hypot(attr[i * 3], attr[i * 3 + 1]),
    }));
  }

  /** Same probe for planets (round-6: anchored-formula residual check). */
  planetRadials(): { id: string; r: number }[] {
    const attr = this.planetPts.geometry.attributes.position.array as Float32Array;
    return this.L.planets.map((p, i) => ({
      id: p.id,
      r: Math.hypot(attr[i * 3], attr[i * 3 + 1]),
    }));
  }

  /** Morph to 图态 (0) or 境态 (1). */
  goTo(target: number, instant = false) {
    if (this.tween) this.tween.kill();
    // A world-state change cancels any in-flight focus (user gesture wins).
    this.focusToken += 1;
    this.focusTween?.kill();
    this.focusTween = null;
    this.closeDetail();
    if (instant || this.reducedMotion) {
      this.state.t = target;
      this.applyMorph();
      return;
    }
    this.tween = gsap.to(this.state, {
      t: target,
      duration: 2.4,
      ease: 'power2.inOut',
      onUpdate: () => this.applyMorph(),
    });
  }

  /**
   * 定位契约 (design §3): locate one star by id and open its inscription
   * card. Freezes the disc (伸手即停 — pointer-activity timestamp), morphs
   * back to 图态 first when in 境态, then eases the chart so the star sits
   * at the top bearing (正北). Any user drag/wheel during the animation
   * cancels it — the user gesture always wins.
   *
   * Returns false when the id is not on the disc (e.g. a goal beyond the
   * 5-seat layout cap): the caller then opens the card without the locate.
   */
  focusStar(id: string): boolean {
    const idx = this.clickables.findIndex((c) => c.id === id);
    if (idx < 0 || this.disposed) return false;
    this.lastPointerActive = performance.now(); // freeze the spin
    const token = ++this.focusToken;
    this.focusTween?.kill();
    this.focusTween = null;
    const begin = () => {
      if (token !== this.focusToken || this.disposed) return;
      this.runFocus(idx, token);
    };
    if (this.state.t > 0.5) {
      // 境态 → 图态 first; the morph tween chains into the focus.
      if (this.tween) this.tween.kill();
      this.closeDetail();
      if (this.reducedMotion) {
        this.state.t = 0;
        this.applyMorph();
        begin();
        return true;
      }
      this.tween = gsap.to(this.state, {
        t: 0,
        duration: 2.4,
        ease: 'power2.inOut',
        onUpdate: () => this.applyMorph(),
        onComplete: begin,
      });
      return true;
    }
    begin();
    return true;
  }

  private runFocus(idx: number, token: number) {
    const c = this.clickables[idx];
    const open = () => {
      if (token === this.focusToken && !this.disposed) this.openDetail(idx);
    };
    const p = c.pos();
    const r = Math.hypot(p[0], p[1]);
    if (r < 1) {
      // the pole star is already at the chart center — no rotation needed
      open();
      return;
    }
    const bearing = (Math.atan2(p[1], p[0]) * 180) / Math.PI + (this.chart.rotation.z * 180) / Math.PI;
    let delta = 90 - bearing; // 正北上位
    delta = ((delta + 540) % 360) - 180;
    const finalRot = this.chart.rotation.z + (delta * Math.PI) / 180;
    if (this.reducedMotion) {
      this.chart.rotation.z = finalRot;
      open();
      return;
    }
    this.focusTween = gsap.to(this.chart.rotation, {
      z: finalRot,
      duration: 1.1,
      ease: 'power2.inOut',
      onComplete: open,
    });
  }

  /** Morph toggle button hook. */
  toggle() {
    this.goTo(this.state.t > 0.5 ? 0 : 1);
  }

  /** 显真 switch (design 四轮 + round-2 替换制, remembered global
   * preference): rebuilds the naming layer in place — true names (泥金)
   * replace ancient names when on; ancient names only when off. No dual-name
   * notes on the chart. Positions, rotation and morph state are preserved;
   * only Text objects churn. */
  setReveal(v: boolean) {
    if (v === this.reveal || this.disposed) return;
    this.reveal = v;
    for (const { t } of this.labelObjs) {
      this.chart.remove(t);
      t.dispose();
    }
    this.labelObjs = [];
    this.goalLabelGroups = [];
    this.buildLabels();
    this.applyMorph(); // re-apply fades/positions for the current morph state
  }

  /** Clear the current selection (React detail-card close). */
  deselect() {
    this.closeDetail();
  }

  dispose() {
    this.disposed = true;
    this.resizeObserver?.disconnect();
    cancelAnimationFrame(this.rafId);
    if (this.tween) this.tween.kill();
    this.focusTween?.kill();
    window.removeEventListener('pointermove', this.onPointerMoveWindow);
    window.removeEventListener('pointermove', this.onPointerActive);
    window.removeEventListener('click', this.onClickWindow);
    window.removeEventListener('keydown', this.onKeydown);
    window.removeEventListener('wheel', this.onWheel);
    this.controls?.dispose();
    this.scene.traverse((obj) => {
      const mesh = obj as THREE.Mesh;
      if (mesh.geometry) mesh.geometry.dispose();
      const mat = mesh.material as THREE.Material | THREE.Material[] | undefined;
      if (Array.isArray(mat)) mat.forEach((m) => m.dispose());
      else mat?.dispose();
    });
    this.composer.dispose();
    this.renderer.dispose();
    for (const el of [this.bgStone, this.bgDeep, this.bgDusk, this.vignette, this.tooltip]) {
      el.remove();
    }
    this.canvas.remove();
  }

  // ---------- internals ----------

  private fitPlanCamera() {
    const w = this.heart.clientWidth || 1600;
    const h = this.heart.clientHeight || 900;
    const fovTan = Math.tan((this.camera.fov * Math.PI) / 360);
    this.camPlan.pos.z = (BAND_OUT + 16) / (fovTan * Math.min(1, w / h));
  }

  private bakeBackgrounds() {
    // Blue-hour script: stone -> dusk (绀青 + warm pole glow) -> deep slate,
    // keyframe colors interpolated in OKLCH so the path never turns muddy grey.
    const oklchToRgb = converter('rgb');
    const oklchMix = (a: string, b: string, t: number): [number, number, number] => {
      const c = oklchToRgb(interpolate([a, b], 'oklch')(t)) as { r: number; g: number; b: number };
      return [Math.round(c.r * 255), Math.round(c.g * 255), Math.round(c.b * 255)];
    };
    const DUSK_TOP = oklchMix('#1c2c4e', '#10172c', 0.4);
    const DUSK_BOT = oklchMix('#182642', '#0d1322', 0.4);
    const makeBgCanvas = (mode: 'stone' | 'dusk' | 'deep'): HTMLCanvasElement => {
      const W = 1024;
      const H = 640;
      const c = document.createElement('canvas');
      c.width = W;
      c.height = H;
      const x = c.getContext('2d')!;
      const stone = mode === 'stone';
      const dusk = mode === 'dusk';
      const top = stone ? [37, 64, 94] : dusk ? DUSK_TOP : [36, 44, 62];
      const bot = stone ? [29, 52, 80] : dusk ? DUSK_BOT : [26, 31, 46];
      const g = x.createLinearGradient(0, 0, 0, H);
      g.addColorStop(0, `rgb(${top.join(',')})`);
      g.addColorStop(1, `rgb(${bot.join(',')})`);
      x.fillStyle = g;
      x.fillRect(0, 0, W, H);
      const rnd = mulberry32(stone ? 41 : dusk ? 43 : 42);
      for (let i = 0; i < 9; i++) {
        const bx = rnd() * W;
        const by = rnd() * H;
        const br = 120 + rnd() * 260;
        const light = rnd() > 0.5;
        const a = (stone ? 0.05 : dusk ? 0.04 : 0.035) * (0.7 + rnd() * 0.6);
        const bg = x.createRadialGradient(bx, by, 0, bx, by, br);
        bg.addColorStop(0, light ? `rgba(70,98,132,${a})` : `rgba(10,20,36,${a})`);
        bg.addColorStop(1, 'rgba(0,0,0,0)');
        x.fillStyle = bg;
        x.fillRect(bx - br, by - br, br * 2, br * 2);
      }
      if (dusk) {
        const wg = x.createRadialGradient(W / 2, H * 0.62, 0, W / 2, H * 0.62, W * 0.34);
        wg.addColorStop(0, 'rgba(196,138,64,0.13)');
        wg.addColorStop(0.55, 'rgba(150,100,52,0.05)');
        wg.addColorStop(1, 'rgba(150,100,52,0)');
        x.fillStyle = wg;
        x.fillRect(0, 0, W, H);
      }
      const img = x.getImageData(0, 0, W, H);
      const bandA = stone ? 0.028 : dusk ? 0.04 : 0.05;
      const grainAmp = stone ? 0.045 : dusk ? 0.032 : 0.02;
      for (let py = 0; py < H; py++) {
        const v = py / H;
        for (let px = 0; px < W; px++) {
          const u = px / W;
          const band = Math.exp(-Math.pow((u * 0.82 + v * 0.57 - 0.78) * 5.0, 2)) * bandA;
          const grain = (rnd() - 0.5) * grainAmp;
          const k = (py * W + px) * 4;
          const lift = (band + grain) * 255;
          img.data[k] = Math.max(0, Math.min(255, img.data[k] + lift * 0.9));
          img.data[k + 1] = Math.max(0, Math.min(255, img.data[k + 1] + lift * 0.88));
          img.data[k + 2] = Math.max(0, Math.min(255, img.data[k + 2] + lift * 0.82));
        }
      }
      x.putImageData(img, 0, 0);
      return c;
    };
    this.bgStone.style.backgroundImage = `url(${makeBgCanvas('stone').toDataURL('image/png')})`;
    this.bgDusk.style.backgroundImage = `url(${makeBgCanvas('dusk').toDataURL('image/png')})`;
    this.bgDusk.style.opacity = '0';
    this.bgDeep.style.backgroundImage = `url(${makeBgCanvas('deep').toDataURL('image/png')})`;
    this.bgDeep.style.opacity = '0';
  }

  private applyBackground(ch2: number, duskPos: number) {
    if (ch2 <= duskPos) {
      this.bgDusk.style.opacity = String(ch2 / duskPos);
      this.bgDeep.style.opacity = '0';
    } else {
      this.bgDusk.style.opacity = '1';
      this.bgDeep.style.opacity = String((ch2 - duskPos) / (1 - duskPos));
    }
  }

  private lineMat(color: number, plan: number, deep: number, ch = 1): THREE.LineBasicMaterial {
    const mat = new THREE.LineBasicMaterial({
      color,
      transparent: true,
      opacity: plan,
      depthWrite: false,
    });
    this.fadeMats.push({ mat, plan, deep, ch });
    return mat;
  }

  private circlePoints(r: number, seg = 160): THREE.Vector3[] {
    const pts: THREE.Vector3[] = [];
    for (let i = 0; i <= seg; i++) {
      const a = (i / seg) * Math.PI * 2;
      pts.push(new THREE.Vector3(r * Math.cos(a), r * Math.sin(a), 0));
    }
    return pts;
  }

  private buildLinework() {
    const L = this.L;
    const ringMat = this.lineMat(INK, 0.42, 0, 1); // 测绘线先消融 (round-5): survey circles dissolve early
    const tickMat = this.lineMat(INK, 0.55, 0, 1);
    const spokeMat = this.lineMat(INK, 0.18, 0, 1);
    const subSpokeMat = this.lineMat(INK, 0.08, 0, 1);
    const bandMat = this.lineMat(INK, 0.5, 0, 1);
    const asterMat = this.lineMat(INK, 0.52, 0.12, 2);
    const courtMat = this.lineMat(INK, 0.35, 0, 1);

    const addLine = (pts: THREE.Vector3[], mat: THREE.LineBasicMaterial, loop = false) => {
      const geo = new THREE.BufferGeometry().setFromPoints(pts);
      const line = loop ? new THREE.LineLoop(geo, mat) : new THREE.Line(geo, mat);
      this.chart.add(line);
      return line;
    };
    const srnd = mulberry32(53);
    const wobblySpoke = (r1: number, r2: number, deg: number, mat: THREE.LineBasicMaterial) => {
      const pts: THREE.Vector3[] = [];
      for (let i = 0; i <= 4; i++) {
        const rr = r1 + ((r2 - r1) * i) / 4;
        const aa = deg + (i > 0 && i < 4 ? (srnd() - 0.5) * 1.4 : 0);
        const a = (aa * Math.PI) / 180;
        pts.push(new THREE.Vector3(rr * Math.cos(a), rr * Math.sin(a), 0));
      }
      addLine(pts, mat);
    };

    for (const [r, m] of [
      [R_GOAL, ringMat],
      [R_OUT, ringMat],
      [R, tickMat],
      [BAND_IN, bandMat],
      [BAND_OUT, bandMat],
    ] as const) {
      addLine(this.circlePoints(r), m, true);
    }
    {
      // 恒显圈, with an arc gap behind the north-star label
      const pts: THREE.Vector3[] = [];
      for (let d = 18; d <= 342; d += 2) {
        const a = (d * Math.PI) / 180;
        pts.push(new THREE.Vector3(R_IN * Math.cos(a), R_IN * Math.sin(a), 0));
      }
      addLine(pts, ringMat);
    }
    {
      // tick marks
      const pts: THREE.Vector3[] = [];
      for (let d = 0; d < 360; d += 6) {
        const a = (d * Math.PI) / 180;
        const r2 = R + (d % 30 === 0 ? 3.25 : 1.5);
        pts.push(new THREE.Vector3(R * Math.cos(a), R * Math.sin(a), 0));
        pts.push(new THREE.Vector3(r2 * Math.cos(a), r2 * Math.sin(a), 0));
      }
      const geo = new THREE.BufferGeometry().setFromPoints(pts);
      this.chart.add(new THREE.LineSegments(geo, tickMat));
    }
    const normDeg = (a: number) => {
      a = a % 360;
      if (a > 180) a -= 360;
      if (a < -180) a += 360;
      return a;
    };
    for (const sec of L.sectors) {
      if (Math.abs(normDeg(sec.start)) >= 12) wobblySpoke(R_IN, R, sec.start, spokeMat);
      const parts = Math.max(1, Math.round(sec.count / 6));
      const fracs: number[] = [];
      for (let f = 1; f < parts; f++) fracs.push(f / parts + ((srnd() - 0.5) * 0.5) / parts);
      fracs.sort();
      for (const fr of fracs) {
        const a = sec.start + sec.width * fr;
        if (Math.abs(normDeg(a)) >= 12) wobblySpoke(R_IN, R, a, subSpokeMat);
      }
      const a = (sec.start * Math.PI) / 180;
      addLine(
        [
          new THREE.Vector3(BAND_IN * Math.cos(a), BAND_IN * Math.sin(a), 0),
          new THREE.Vector3(BAND_OUT * Math.cos(a), BAND_OUT * Math.sin(a), 0),
        ],
        bandMat,
      );
    }
    {
      // asterism links (formed members): in 图态 the bright carve; in 境态 the
      // constellation's faint connective lines, anchored to the same per-slot
      // deep coords as the stars (深度衰减,不共面).
      const pts: THREE.Vector3[] = [];
      const deep: number[] = [];
      const P = L.lit.plan;
      const D = L.lit.deep;
      for (let i = 0; i < L.lit.links.length; i += 2) {
        const a = L.lit.links[i] * 3;
        const b = L.lit.links[i + 1] * 3;
        pts.push(new THREE.Vector3(P[a], P[a + 1], 0));
        pts.push(new THREE.Vector3(P[b], P[b + 1], 0));
        deep.push(D[a], D[a + 1], D[a + 2], D[b], D[b + 1], D[b + 2]);
      }
      const geo = new THREE.BufferGeometry().setFromPoints(pts);
      const line = new THREE.LineSegments(geo, asterMat);
      this.chart.add(line);
      this.asterLinks = line;
      this.asterLinks.userData.plan = new Float32Array(pts.flatMap((v) => [v.x, v.y, v.z]));
      this.asterLinks.userData.deep = new Float32Array(deep);
    }
    {
      // court links
      const pts: THREE.Vector3[] = [];
      const P = L.court.plan;
      for (const [a, b] of L.court.links) {
        pts.push(new THREE.Vector3(P[a * 3], P[a * 3 + 1], 0));
        pts.push(new THREE.Vector3(P[b * 3], P[b * 3 + 1], 0));
      }
      const geo = new THREE.BufferGeometry().setFromPoints(pts);
      this.chart.add(new THREE.LineSegments(geo, courtMat));
    }
    // engraved ring around the north star — 图态 carving, dissolves early
    addLine(this.circlePoints(4.2, 64), this.lineMat(INK, 0.55, 0, 1), true);
  }

  private makePoints(
    opts: {
      plan: number[];
      deep: number[];
      size: number[];
      opacity: number[];
      core: number[];
      ring: number[];
      color: number[];
      deepColor?: number[];
      /** 星官点燃: aCore lerp target in 境态 (空圈 ignite into solid stars). */
      deepCore?: number[];
    },
    parent?: THREE.Group,
  ): THREE.Points {
    const { plan, deep, size, opacity, core, ring, color } = opts;
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(plan), 3));
    geo.setAttribute('aSize', new THREE.BufferAttribute(new Float32Array(size), 1));
    geo.setAttribute('aOpacity', new THREE.BufferAttribute(new Float32Array(opacity), 1));
    geo.setAttribute('aCore', new THREE.BufferAttribute(new Float32Array(core), 1));
    geo.setAttribute('aRing', new THREE.BufferAttribute(new Float32Array(ring), 1));
    geo.setAttribute('aColor', new THREE.BufferAttribute(new Float32Array(color), 3));
    const mat = new THREE.ShaderMaterial({
      transparent: true,
      depthWrite: false,
      blending: THREE.NormalBlending,
      uniforms: { uScale: { value: 1 }, uGlobal: { value: 1 } },
      vertexShader: /* glsl */ `
        attribute float aSize;
        attribute float aOpacity;
        attribute float aCore;
        attribute float aRing;
        attribute vec3 aColor;
        varying float vOpacity;
        varying float vCore;
        varying float vRing;
        varying vec3 vColor;
        uniform float uScale;
        uniform float uGlobal;
        void main() {
          vOpacity = aOpacity;
          vCore = aCore;
          vRing = aRing;
          vColor = aColor;
          vec4 mv = modelViewMatrix * vec4(position, 1.0);
          gl_PointSize = aSize * uGlobal * uScale / -mv.z;
          gl_Position = projectionMatrix * mv;
        }
      `,
      fragmentShader: /* glsl */ `
        varying float vOpacity;
        varying float vCore;
        varying float vRing;
        varying vec3 vColor;
        void main() {
          vec2 uv = gl_PointCoord - 0.5;
          float d = length(uv) * 2.0;
          float core = (1.0 - smoothstep(0.40, 0.62, d)) * vCore;
          float ring = smoothstep(0.58, 0.70, d) * (1.0 - smoothstep(0.80, 0.92, d)) * vRing;
          float a = max(core, ring) * vOpacity;
          if (a < 0.004) discard;
          gl_FragColor = vec4(pow(vColor, vec3(2.2)), a); // linear pipeline
        }
      `,
    });
    const points = new THREE.Points(geo, mat);
    points.userData.plan = new Float32Array(plan);
    points.userData.deep = new Float32Array(deep);
    if (opts.deepColor) {
      this.colored.push({
        pts: points,
        plan: new Float32Array(color),
        deep: new Float32Array(opts.deepColor),
      });
    }
    if (opts.deepCore) {
      this.coreLerp.push({
        pts: points,
        plan: new Float32Array(core),
        deep: new Float32Array(opts.deepCore),
      });
    }
    (parent ?? this.chart).add(points);
    return points;
  }

  /** Register a 境态 prominence tier: deep size/opacity multipliers applied
   * in applyMorph (identity at ch3=0, so 图态 is untouched). */
  private addTier(pts: THREE.Points, ds: number, dop: number | null) {
    this.tiered.push({
      pts,
      baseSize: new Float32Array(pts.geometry.attributes.aSize.array),
      baseOp: dop === null ? null : new Float32Array(pts.geometry.attributes.aOpacity.array),
      ds,
      dop: dop ?? 1,
    });
  }

  private makeGlowTexture(): THREE.CanvasTexture {
    const c = document.createElement('canvas');
    c.width = c.height = 128;
    const x = c.getContext('2d')!;
    const g = x.createRadialGradient(64, 64, 0, 64, 64, 64);
    g.addColorStop(0, 'rgba(255,255,255,1)');
    g.addColorStop(0.25, 'rgba(255,255,255,0.35)');
    g.addColorStop(1, 'rgba(255,255,255,0)');
    x.fillStyle = g;
    x.fillRect(0, 0, 128, 128);
    return new THREE.CanvasTexture(c);
  }

  private addLabel(
    text: string,
    opts: {
      size?: number;
      color?: number;
      font?: string;
      pos?: number[];
      deepPos?: number[] | null;
      rotZ?: number;
      anchorX?: 'left' | 'center' | 'right';
      fade?: LabelRec['fade'];
      prio?: number;
    } = {},
  ): Text {
    const {
      size = 3.4,
      color = INK,
      font = fontUrl,
      pos = [0, 0, 0],
      deepPos = null,
      rotZ = 0,
      anchorX = 'center',
      fade = 'band',
      prio = 2,
    } = opts;
    const t = new Text();
    t.text = text;
    t.font = font;
    t.fontSize = size;
    t.color = color;
    t.anchorX = anchorX;
    t.anchorY = 'middle';
    t.position.set(pos[0], pos[1], pos[2] ?? 0);
    t.rotation.z = rotZ;
    t.material.transparent = true;
    // dark SDF rim keeps serif text readable on glows and grain alike
    t.outlineWidth = '5%';
    t.outlineColor = 0x0b1626;
    t.outlineOpacity = 0.85;
    this.chart.add(t);
    this.labelObjs.push({
      t,
      fade,
      planPos: pos.slice(),
      deepPos: deepPos ? deepPos.slice() : null,
      rotZ,
      prio,
      grpId: this.labelGrpSeq++,
      ca: 1,
      caTarget: 1,
    });
    return t;
  }

  private addSegmentedLabel(
    text: string,
    opts: {
      size?: number;
      color?: number;
      pos: number[];
      align?: 'left' | 'right' | 'center';
      fade?: LabelRec['fade'];
      goalIdx?: number;
      prio?: number;
    },
  ) {
    const { size = 3.6, color = 0xeed696, pos, align = 'left', fade = 'goal', goalIdx = -1, prio = 1 } = opts;
    const grpId = this.labelGrpSeq++;
    const segs = text.split(/([A-Za-z0-9.]+)/).filter(Boolean);
    const group: (typeof this.goalLabelGroups)[number] = {
      goalIdx,
      segs: [],
      base: [],
      anchor: pos.slice(),
    };
    const objs = segs.map((s) => {
      const latin = /^[A-Za-z0-9.]+$/.test(s);
      const t = new Text();
      t.text = s;
      t.font = latin ? fellUrl : imingUrl;
      t.fontSize = size;
      t.color = color;
      t.anchorX = 'left';
      t.anchorY = 'middle';
      t.material.transparent = true;
      t.outlineWidth = '5%';
      t.outlineColor = 0x0b1626;
      t.outlineOpacity = 0.85;
      this.chart.add(t);
      this.labelObjs.push({
        t, fade, planPos: pos.slice(), deepPos: null, rotZ: 0, prio, grpId, ca: 1, caTarget: 1,
      });
      group.segs.push(t);
      return t;
    });
    if (goalIdx >= 0) this.goalLabelGroups.push(group);
    this.segPending += objs.length;
    let left = objs.length;
    objs.forEach((o) =>
      o.sync(() => {
        this.segPending -= 1;
        left -= 1;
        if (left === 0) {
          const widths = objs.map((o2) => {
            const b = o2.textRenderInfo && o2.textRenderInfo.blockBounds;
            return b ? Math.max(0.1, b[2] - b[0]) : o2.text.length * size * 0.6;
          });
          const total = widths.reduce((a, b) => a + b, 0) + 0.4 * (objs.length - 1);
          let x = pos[0] - (align === 'right' ? total : align === 'center' ? total / 2 : 0);
          objs.forEach((o2, i) => {
            o2.position.set(x, pos[1], 0);
            x += widths[i] + 0.4;
          });
          group.base = objs.map((o2) => [o2.position.x, o2.position.y]);
        }
      }),
    );
  }

  /** Register plain (non-segmented) labels so they follow their goal star's
   * 境态 drift, same contract as addSegmentedLabel's groups. */
  private followGoal(goalIdx: number, texts: Text[]) {
    this.goalLabelGroups.push({
      goalIdx,
      segs: texts,
      base: texts.map((t) => [t.position.x, t.position.y]),
      anchor: [],
    });
  }

  private buildLabels() {
    const L = this.L;
    // outer rim band (BAND_TEXT): 星官古名 etched per char along the arc.
    // 显真替换制 (王军 round-2, supersedes 主从反转): default = ancient name
    // only; reveal = real domain name only — no dual-name notes on the chart
    // (dual naming lives in the StarCatalog and inscription cards).
    for (const sec of L.sectors) {
      const mid = sec.start + sec.width / 2;
      const chars = Array.from(this.reveal ? sec.name : sec.asterism);
      const color = this.reveal ? GOLD : 0xb5b0a0; // rim 官名 = 月白 muted
      const angStep = ((3.2 * 1.25) / BAND_TEXT) * (180 / Math.PI);
      const a0 = mid - (angStep * (chars.length - 1)) / 2;
      chars.forEach((ch, i) => {
        const rad = ((a0 + i * angStep) * Math.PI) / 180;
        this.addLabel(ch, {
          size: 3.2,
          color,
          font: imingUrl,
          fade: 'band',
          pos: [BAND_TEXT * Math.cos(rad), BAND_TEXT * Math.sin(rad), 0],
          rotZ: rad + Math.PI / 2,
        });
      });
      // round-3 ruling: the rim band is the ONLY name place for skill
      // domains — no in-sector text beside the figures (R3 reverted).
    }
    // 北斗环卫 goal labels (names only — no dipper formation lines, goals
    // keep their ring seats). 显真替换制: OFF = dipper name alone; ON = true
    // title alone (泥金) — no 古名小注. 虚位 seats show 「名·虚位」 hollow.
    // 刻痕星 keep their carved true title in both modes — etched history,
    // name revoked from the dipper pool but the carving stays.
    L.goals.forEach((g, gi) => {
      const cos = Math.cos((g.angle * Math.PI) / 180);
      const align = cos > 0.35 ? 'left' : cos < -0.35 ? 'right' : 'center';
      const rr = R_GOAL + 8;
      const a = (g.angle * Math.PI) / 180;
      const px = rr * Math.cos(a) + (align === 'left' ? 1 : align === 'right' ? -1 : 0);
      const py = rr * Math.sin(a);
      if (g.status === 'completed') {
        this.addSegmentedLabel(g.title, {
          size: 3.6,
          color: 0x9a9276,
          align,
          goalIdx: gi,
          pos: [px, py, 0],
        });
        return;
      }
      if (!this.reveal) {
        const t = this.addLabel(g.seatName ?? g.title, {
          size: 3.8,
          color: 0xeed696,
          font: imingUrl,
          fade: 'goal',
          pos: [px, py, 0],
        });
        this.followGoal(gi, [t]);
        return;
      }
      this.addSegmentedLabel(g.title, {
        size: 3.6,
        color: 0xeed696,
        align,
        goalIdx: gi,
        pos: [px, py, 0],
      });
    });
    for (const seat of L.seats) {
      if (seat.goalIndex !== null) continue;
      const a = (seat.angle * Math.PI) / 180;
      const rr = R_GOAL + 8;
      this.addLabel(`${seat.name}·虚位`, {
        size: 2.8,
        color: 0x8d8672,
        font: imingUrl,
        fade: 'goal',
        pos: [rr * Math.cos(a), rr * Math.sin(a), 0],
      });
    }
    // north star label (round-3 字级统一: one 明体 ladder — 北极星/北斗星名
    // = 泥金; 虚位注 = 再暗一档). 替换制: default shows just「北极星」, reveal
    // shows the true text alone. 虚位 keeps the seat marked.
    if (this.northVacant) {
      this.addLabel('虚位', {
        size: 3.8,
        color: 0x8d8672,
        font: imingUrl,
        anchorX: 'left',
        pos: [6.5, 0.4, 0],
        deepPos: [10.5, -10.6, 0],
        fade: 'north',
        prio: 0,
      });
    } else if (!this.reveal) {
      this.addLabel('北极星', {
        size: 3.8,
        color: 0xeed696, // 泥金
        font: imingUrl,
        anchorX: 'left',
        pos: [6.5, 0.4, 0],
        deepPos: [10.5, -10.6, 0],
        fade: 'north',
        prio: 0,
      });
    } else {
      const clause = this.snapshot.north_star.split(/[，。]/)[0];
      const idx = clause.indexOf('成为');
      const nsLines = idx > 0 ? [clause.slice(0, idx + 2), clause.slice(idx + 2)] : [clause, ''];
      this.addLabel(nsLines[0], {
        size: 3.8,
        color: 0xeed696, // 泥金真名
        font: imingUrl,
        anchorX: 'left',
        pos: [6.5, 3.4, 0],
        deepPos: [10.5, -8.5, 0],
        fade: 'north',
        prio: 0,
      });
      if (nsLines[1]) {
        this.addLabel(nsLines[1], {
          size: 3.8,
          color: 0xeed696,
          font: imingUrl,
          anchorX: 'left',
          pos: [6.5, -2.6, 0],
          deepPos: [10.5, -13.6, 0],
          fade: 'north',
          prio: 0,
        });
      }
    }
    this.labelsPending = this.labelObjs.length;
    for (const { t } of this.labelObjs) {
      t.sync(() => {
        this.labelsPending -= 1;
      });
    }
  }

  private applyMorph() {
    const t = this.state.t;
    const ch1 = chan(t, this.state.w1);
    const ch2 = chan(t, this.state.w2);
    const ch3 = chan(t, this.state.w3);
    this.state.ch1 = ch1;
    this.state.ch2 = ch2;
    this.state.ch3 = ch3;
    for (const pts of this.morphables) {
      if (pts.userData.orbitManaged) continue;
      const attr = pts.geometry.attributes.position as THREE.BufferAttribute;
      const plan = pts.userData.plan!;
      const deep = pts.userData.deep!;
      const arr = attr.array as Float32Array;
      for (let i = 0; i < arr.length; i++) {
        arr[i] = plan[i] + (deep[i] - plan[i]) * ch2;
      }
      attr.needsUpdate = true;
    }
    this.chart.rotation.x = -1.05 * ch2;
    this.camera.position.lerpVectors(this.camPlan.pos, this.camDeep.pos, ch2);
    this.camera.lookAt(new THREE.Vector3().lerpVectors(this.camPlan.look, this.camDeep.look, ch2));
    for (const { mat, plan, deep, ch } of this.fadeMats) {
      const c = ch === 1 ? ch1 : ch === 3 ? ch3 : ch2;
      mat.opacity = plan + (deep - plan) * c;
    }
    for (const { mat, fn } of this.fadeFns) {
      mat.opacity = fn(ch1, ch2, ch3);
    }
    for (const { t: txt, fade, planPos, deepPos } of this.labelObjs) {
      if (fade === 'band') {
        txt.material.opacity = 1 - ch2;
        txt.visible = ch2 < 0.98;
      } else if (fade === 'north' && deepPos) {
        txt.material.opacity = 1 - 0.25 * ch2;
        txt.position.set(
          planPos[0] + (deepPos[0] - planPos[0]) * ch2,
          planPos[1] + (deepPos[1] - planPos[1]) * ch2,
          0,
        );
      }
    }
    for (const g of this.glows) {
      g.mat.opacity = g.maxOpacity * ch3;
      g.spr.visible = g.mat.opacity > 0.004;
      const p = g.getPos();
      g.spr.position.set(p[0], p[1], p[2]);
    }
    for (const n of this.nebulae) {
      n.mat.opacity = n.op * ch3;
      n.spr.visible = n.mat.opacity > 0.004;
    }
    // blue hour: the pole star flares warm for a moment as the world tilts
    const duskBoost = Math.exp(-Math.pow((ch2 - this.state.duskPos) / 0.13, 2)) * this.state.duskAmt;
    const ng = this.glows[0];
    if (duskBoost > 0.01) {
      ng.mat.opacity = Math.min(1, Math.max(ng.mat.opacity, ng.maxOpacity * duskBoost * 0.6));
      ng.spr.visible = true;
      const sc = 20 * (1 + 0.55 * duskBoost);
      ng.spr.scale.set(sc, sc, 1);
    } else {
      ng.spr.scale.set(20, 20, 1);
    }
    // dim field restraint (月.png) + ring taper, both late-phase — applied to
    // the carved dim stars and the parallax background field alike
    for (const dimPts of [this.dimPts, this.dimBgPts]) {
      const dimAttr = dimPts.geometry.attributes.aOpacity as THREE.BufferAttribute;
      const dimSizeAttr = dimPts.geometry.attributes.aSize as THREE.BufferAttribute;
      const dimRingAttr = dimPts.geometry.attributes.aRing as THREE.BufferAttribute;
      const base = dimPts.userData.baseOpacity as Float32Array;
      const baseSz = dimPts.userData.baseSize as Float32Array;
      const baseRing = dimPts.userData.baseRing as Float32Array;
      const dOpS = dimPts.userData.deepOpScale as Float32Array;
      const dSzS = dimPts.userData.deepSizeScale as Float32Array;
      const filler = dimPts.userData.filler as number[];
      for (let i = 0; i < dimAttr.array.length; i++) {
        const densityGate = filler[i] ? this.state.density : 1;
        (dimAttr.array as Float32Array)[i] = (base[i] * densityGate * (1 + (dOpS[i] - 1) * ch3));
        (dimSizeAttr.array as Float32Array)[i] = baseSz[i] * (1 + (dSzS[i] - 1) * ch3);
        (dimRingAttr.array as Float32Array)[i] = baseRing[i] * (1 - 0.55 * ch3);
      }
      dimAttr.needsUpdate = true;
      dimSizeAttr.needsUpdate = true;
      dimRingAttr.needsUpdate = true;
    }
    // 境态 prominence tiers (北极星 > 目标金 > 行星 > 客星 > 尘埃)
    for (const e of this.tiered) {
      const szAttr = e.pts.geometry.attributes.aSize as THREE.BufferAttribute;
      const szArr = szAttr.array as Float32Array;
      const sf = 1 + (e.ds - 1) * ch3;
      for (let i = 0; i < szArr.length; i++) szArr[i] = e.baseSize[i] * sf;
      szAttr.needsUpdate = true;
      if (e.baseOp) {
        const opAttr = e.pts.geometry.attributes.aOpacity as THREE.BufferAttribute;
        const opArr = opAttr.array as Float32Array;
        const of = 1 + (e.dop - 1) * ch3;
        for (let i = 0; i < opArr.length; i++) opArr[i] = e.baseOp[i] * of;
        opAttr.needsUpdate = true;
      }
    }
    // discrete 4-step color temperature (境态): lerp aColor plan → deep
    for (const c of this.colored) {
      const attr = c.pts.geometry.attributes.aColor as THREE.BufferAttribute;
      const arr = attr.array as Float32Array;
      for (let i = 0; i < arr.length; i++) arr[i] = c.plan[i] + (c.deep[i] - c.plan[i]) * ch2;
      attr.needsUpdate = true;
    }
    // 星官点燃: lerp aCore plan → deep (etched 空圈 become solid stars)
    for (const c of this.coreLerp) {
      const attr = c.pts.geometry.attributes.aCore as THREE.BufferAttribute;
      const arr = attr.array as Float32Array;
      for (let i = 0; i < arr.length; i++) arr[i] = c.plan[i] + (c.deep[i] - c.plan[i]) * ch2;
      attr.needsUpdate = true;
    }
    // 尘埃带泼墨长河 wash (density tracks the evidence count, fades with ch3)
    for (const r of this.dustRiver) {
      r.mat.opacity = r.base * ch3;
      r.spr.visible = r.mat.opacity > 0.004;
    }
    this.applyBackground(ch2, this.state.duskPos);
    this.fxPass.enabled = !this.softGL && ch3 > 0.02;
    this.bloom.intensity = 0.7 * ch3 * this.state.bloom;
    this.vignette.style.opacity = String(0.55 + 0.45 * ch2);
    // React-owned DOM
    const domOpacity = String(1 - ch2);
    const refs = this.opts.domRefs;
    if (refs?.cartouche) refs.cartouche.style.opacity = domOpacity;
    if (refs?.briefing) refs.briefing.style.opacity = domOpacity;
    if (refs?.toggle) refs.toggle.textContent = t > 0.5 ? '图' : '境'; // 印章 glyph = target state
    this.opts.onMorph?.(t);
  }

  private screenOf(local: number[]): [number, number] {
    const v = new THREE.Vector3(local[0], local[1], local[2] ?? 0);
    this.chart.localToWorld(v);
    v.project(this.camera);
    const r = this.heart.getBoundingClientRect();
    return [r.left + (v.x * 0.5 + 0.5) * r.width, r.top + (-v.y * 0.5 + 0.5) * r.height];
  }

  private onPointerMove(e: PointerEvent) {
    this.hoverIdx = -1;
    let bestD = 26;
    this.hoverables.forEach((h, i) => {
      const [x, y] = this.screenOf(h.pos());
      const d = Math.hypot(x - e.clientX, y - e.clientY);
      if (d < bestD) {
        bestD = d;
        this.hoverIdx = i;
      }
    });
  }

  private updateTooltip() {
    const tip = this.tooltip;
    if (this.hoverIdx < 0 || !this.hoverables[this.hoverIdx]) {
      tip.style.display = 'none';
      return;
    }
    const h = this.hoverables[this.hoverIdx];
    const [x, y] = this.screenOf(h.pos());
    tip.innerHTML = `<div class="tt-title"></div><div class="tt-info"></div>`;
    (tip.querySelector('.tt-title') as HTMLElement).textContent = h.title;
    (tip.querySelector('.tt-info') as HTMLElement).textContent = h.info;
    tip.style.display = 'block';
    const tw = tip.offsetWidth;
    tip.style.left = Math.min(window.innerWidth - tw - 12, x + 16) + 'px';
    tip.style.top = Math.max(10, y - 44) + 'px';
  }

  private detailRows(c: (typeof this.clickables)[number]): [string, string][] {
    const snapshot = this.snapshot;
    if (c.kind === 'north') {
      const north = snapshot.north;
      if (this.northVacant) {
        return [
          ['类型', '北极星 · 虚位'],
          ['铭文', '（尚未立星 — 点「重刻」写下北极星）'],
        ];
      }
      return [
        ['类型', '北极星'],
        ['铭文', north.full || snapshot.north_star],
        ['简称', north.brief || '—'],
        ['可见性', north.visibility === 'public' ? '可公开' : '仅本地'],
      ];
    }
    if (c.kind === 'goal') {
      const g =
        snapshot.goals.find((x) => x.id === c.id) ??
        ({ status: this.L.goals[c.idx]?.status ?? 'active', start: '', target: '', summary: '' } as const);
      const statusLabel =
        g.status === 'completed' ? '已镌刻' : g.status === 'paused' ? '已暂停' : '进行中';
      const seatName = this.L.goals[c.idx]?.seatName;
      return [
        ['状态', statusLabel],
        ...(seatName ? ([['星位', seatName]] as [string, string][]) : []),
        ['起始', g.start || '—'],
        ['目标', g.target || '—'],
        ['铭文', g.summary || '—'],
      ];
    }
    if (c.kind === 'planet') {
      const p = snapshot.projects[c.idx];
      const gi = this.L.planets[c.idx].goalIndex;
      return [
        ['状态', p.status === 'active' ? '在轨' : '归档'],
        ['所属目标', gi >= 0 ? this.L.goals[gi].title : '（自由轨道）'],
        ['任务', `${p.task_count} 项`],
        ['进度', p.progress === null || p.progress === undefined ? '—' : `${Math.round(p.progress * 100)}%`],
        ['时间范围', p.time_range || '—'],
      ];
    }
    if (c.kind === 'guest') {
      const e =
        snapshot.evidence.find((x) => x.id === this.L.guests[c.idx].id) ?? this.L.guests[c.idx];
      return [
        ['类型', 'type' in e ? e.type : '—'],
        ['强度', e.strength || '—'],
        ['日期', e.date || '—'],
        ['评审', 'review_status' in e && e.review_status === 'needs_review' ? '待评审' : '已入座'],
        ['摘要', 'summary' in e && e.summary ? e.summary : '—'],
      ];
    }
    // 星官 (skill): 三态 + 关联证据计数 + 入座证据名录 (design §5, read-only —
    // editing stays on the skill-tree page).
    const s = this.L.lit.skills[c.idx];
    const seated = snapshot.evidence
      .filter((e) => e.skill_ids.includes(s.id))
      .slice(0, 3)
      .map((e) => e.title);
    const rows: [string, string][] = [
      ['类别', s.category],
      ['状态', s.status],
      ['关联证据', `${s.evidenceCount} 条`],
    ];
    seated.forEach((title, i) => rows.push([i === 0 ? '入座证据' : '', `· ${title}`]));
    return rows;
  }

  private openDetail(i: number) {
    this.selectedIdx = i;
    const c = this.clickables[i];
    this.opts.onSelect?.({ kind: c.kind, id: c.id, title: c.title, rows: this.detailRows(c) });
  }

  private closeDetail() {
    if (this.selectedIdx < 0) return;
    this.selectedIdx = -1;
    this.selRing.visible = false;
    this.opts.onSelect?.(null);
  }

  private onClick(e: MouseEvent) {
    if (this.dragDist > 6) {
      this.dragDist = 0;
      return;
    }
    const target = e.target as HTMLElement;
    // React flushes click handlers synchronously, so a UI control that
    // re-renders itself (重刻 → edit form, catalog row → close panel) is
    // already detached by the time this window listener runs — its
    // [data-starmap-ui] ancestry is gone. Treat detached targets as UI.
    if (!target.isConnected) return;
    if (target.closest('[data-starmap-ui]')) return;
    let best = -1;
    let bestD = 26;
    this.clickables.forEach((c, i) => {
      const [x, y] = this.screenOf(c.pos());
      const d = Math.hypot(x - e.clientX, y - e.clientY);
      if (d < bestD) {
        bestD = d;
        best = i;
      }
    });
    if (best >= 0) this.openDetail(best);
    else this.closeDetail();
  }

  private updatePointScale() {
    const h = this.renderer.domElement.height; // device px
    const scale = h / (2 * Math.tan((this.camera.fov * Math.PI) / 360));
    for (const pts of this.morphables) {
      const p = pts as unknown as THREE.Points;
      if (p.isPoints) (p.material as THREE.ShaderMaterial).uniforms.uScale.value = scale;
    }
  }

  private onResize() {
    const w = this.heart.clientWidth || 1;
    const h = this.heart.clientHeight || 1;
    this.renderer.setSize(w, h);
    this.composer.setSize(w, h);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.fitPlanCamera();
    if (this.controls) {
      this.controls.minDistance = this.camPlan.pos.z * 0.65;
      this.controls.maxDistance = this.camPlan.pos.z * 1.6;
    }
    this.updatePointScale();
    this.applyMorph();
  }

  private loop() {
    if (this.disposed) return;
    this.rafId = requestAnimationFrame(() => this.loop());
    const dt = Math.min(this.clock.getDelta(), 0.1);
    const tt = this.clock.elapsedTime;
    const { ch2, ch3 } = this.state;
    const L = this.L;

    // 伸手即停: pointer activity / hover / open card / drag pause the spin
    const now = performance.now();
    const busy =
      this.dragging || this.hoverIdx >= 0 || this.selectedIdx >= 0 || now - this.lastPointerActive < 3000;
    const spinTarget = busy || this.reducedMotion ? 0 : 1;
    this.spinFactor += (spinTarget - this.spinFactor) * Math.min(1, dt / 0.8);

    // armillary spin: 1h/rev, quickens briefly while the world tilts (ch2 window)
    const BASE_SPIN = (Math.PI * 2) / 3600;
    this.chart.rotation.z += dt * BASE_SPIN * this.spinFactor * (1 + 2.5 * Math.sin(ch2 * Math.PI));
    if (!this.dragging && Math.abs(this.spinVel) > 1e-4) {
      this.chart.rotation.z += this.spinVel * dt;
      this.spinVel *= Math.exp(-dt / 1.2);
    }

    // parallax-lite: the background field trails the disc at 0.3× in 境态
    // (counter-rotation ramps with ch2; zero in 图态 — carving stays honest)
    this.bgLayer.rotation.z = -0.7 * ch2 * this.chart.rotation.z;

    // ---- orbit-managed clouds: single writer (morph lerp + integrated phase) ----
    {
      const gAttr = this.goalPts.geometry.attributes.position as THREE.BufferAttribute;
      const goalNow = L.goals.map((g, i) => {
        const deep = this.goalDeepBase[i];
        this.goalPhase[i] += dt * ((2 * Math.PI) / this.goalPeriods[i]) * ch3;
        return orbitPos(g.plan, deep, this.goalPhase[i], ch2, ch3);
      });
      goalNow.forEach((p, i) => gAttr.setXYZ(i, p[0], p[1], p[2]));
      gAttr.needsUpdate = true;
      // goal-name labels follow the fan-out: label = goalNow + plan-offset,
      // with the offset itself spreading outward in 境态 (×1.9) so a system's
      // own planet lanes (≤12.6) never sweep across its name.
      const labelSpread = 1 + 0.9 * ch2;
      for (const grp of this.goalLabelGroups) {
        if (!grp.base.length) continue;
        const gp = goalNow[grp.goalIdx];
        const morphBase = L.goals[grp.goalIdx].plan;
        grp.segs.forEach((s, si) =>
          s.position.set(
            gp[0] + (grp.base[si][0] - morphBase[0]) * labelSpread,
            gp[1] + (grp.base[si][1] - morphBase[1]) * labelSpread,
            0,
          ),
        );
      }

      const pAttr = this.planetPts.geometry.attributes.position as THREE.BufferAttribute;
      const pInAttr = this.planetInnerPts.geometry.attributes.position as THREE.BufferAttribute;
      const mAttr = this.moonPts.geometry.attributes.position as THREE.BufferAttribute;
      const planetNow = L.planets.map((p, i) => {
        const deep = this.planetDeepBase[i];
        this.planetPhase[i] += dt * ((2 * Math.PI) / this.planetPeriods[i]) * ch3;
        const gi = p.goalIndex;
        const anchorDeep = gi >= 0 ? this.goalDeepBase[gi] : [0, 0, 0];
        const anchorNow = gi >= 0 ? goalNow[gi] : [0, 0, 0];
        // the follow term compares against the goal's ch2-MORPHED base — never
        // its deep base (round-6 fix: deep-base comparison displaced grouped
        // planets even on first load)
        const gPlan = gi >= 0 ? L.goals[gi].plan : [0, 0, 0];
        const anchorMorph = gi >= 0
          ? [gPlan[0] + (anchorDeep[0] - gPlan[0]) * ch2, gPlan[1] + (anchorDeep[1] - gPlan[1]) * ch2]
          : [0, 0];
        return orbitPosAnchored(
          p.plan, deep, anchorDeep, anchorMorph, anchorNow, this.planetPhase[i], ch2, ch3,
        );
      });
      planetNow.forEach((p, i) => {
        pAttr.setXYZ(i, p[0], p[1], p[2]);
        pInAttr.setXYZ(i, p[0], p[1], p[2]);
      });
      pAttr.needsUpdate = true;
      pInAttr.needsUpdate = true;
      this.moonDeepBase.forEach((md, mi) => {
        const pi = this.moonPlanet[mi];
        if (pi === undefined) return;
        mAttr.setXYZ(
          mi,
          md[0] + (planetNow[pi][0] - this.planetDeepBase[pi][0]),
          md[1] + (planetNow[pi][1] - this.planetDeepBase[pi][1]),
          md[2],
        );
      });
      mAttr.needsUpdate = true;

      // 境态轨道环: ride the goal stars (fanned-out lanes), shimmer faintly,
      // and trickle the light-flow arc — all gated by ch3 (图态 untouched)
      for (const orb of this.orbitRings) {
        const gp = goalNow[orb.goalIdx];
        orb.ring.position.set(gp[0], gp[1], gp[2]);
        const shimmer = this.reducedMotion ? 1 : 0.92 + 0.08 * Math.sin(tt * 0.5 + orb.shimmer);
        orb.ringMat.opacity = 0.22 * ch3 * shimmer;
        orb.ring.visible = orb.ringMat.opacity > 0.004;
        if (this.reducedMotion) {
          orb.flowMat.opacity = 0;
          orb.flow.visible = false;
        } else {
          orb.phase += dt * ((2 * Math.PI) / 46); // 微光沿圈流转, very slow
          orb.flow.rotation.z = orb.phase;
          orb.flowMat.opacity = 0.5 * ch3 * shimmer;
          orb.flow.visible = orb.flowMat.opacity > 0.004;
        }
      }

      // 行星时间弧 (flag-gated, default OFF): self-erasing motion trails
      if (PLANET_TRAILS && this.planetTrails.length) {
        this.trailTimer += dt;
        const record = ch3 > 0.5 && this.trailTimer > 0.22 && !this.reducedMotion;
        if (record) this.trailTimer = 0;
        this.planetTrails.forEach((tr, i) => {
          tr.mat.opacity = 0.3 * ch3;
          tr.line.visible = tr.mat.opacity > 0.01;
          if (!record) return;
          const h = tr.hist;
          h.copyWithin(0, 3); // shift left: oldest drops off (self-erasing)
          const N = h.length / 3;
          h[(N - 1) * 3] = planetNow[i][0];
          h[(N - 1) * 3 + 1] = planetNow[i][1];
          h[(N - 1) * 3 + 2] = planetNow[i][2];
          const attr = tr.line.geometry.attributes.position as THREE.BufferAttribute;
          (attr.array as Float32Array).set(h);
          attr.needsUpdate = true;
        });
      }

      const guAttr = this.guestPts.geometry.attributes.position as THREE.BufferAttribute;
      const tAttr = this.guestTails.geometry.attributes.position as THREE.BufferAttribute;
      L.guests.forEach((g, i) => {
        const deep = this.guestDeepBase[i];
        this.guestPhase[i] += dt * ((2 * Math.PI) / this.guestPeriods[i]) * ch3;
        const drift = 4 * ch3;
        const gx = g.plan[0] + (deep[0] - g.plan[0]) * ch2 + drift * Math.cos(this.guestPhase[i] + i * 1.3);
        const gy = g.plan[1] + (deep[1] - g.plan[1]) * ch2 + drift * Math.sin(this.guestPhase[i] + i * 1.3);
        const gz = g.plan[2] + (deep[2] - g.plan[2]) * ch2;
        guAttr.setXYZ(i, gx, gy, gz);
        const glow = this.guestGlows[i];
        glow.spr.position.set(gx, gy, gz);
        this.tailOffsets[i].forEach((off, v) =>
          tAttr.setXYZ(i * 10 + v, gx + off[0] * ch2, gy + off[1] * ch2, gz + off[2] * ch2),
        );
      });
      guAttr.needsUpdate = true;
      tAttr.needsUpdate = true;
    }

    // ---- 境态 label declutter (round-4): names stay upright while the disc
    // spins (counter-rotate by -chart·ch2 — zero effect in 图态, where the
    // carving must rotate with the stone); colliding labels FADE by priority
    // (北极星 > 斗星名 > 虚位注), never jump or reposition. Planets carry no
    // text labels at all (mark glyph only; details via click).
    for (const rec of this.labelObjs) {
      if (rec.fade === 'band') continue; // rim chars fade out with ch2 anyway
      rec.t.rotation.z = rec.rotZ - this.chart.rotation.z * ch2;
    }
    this.collisionTick += 1;
    const collisionActive = ch2 > 0.6;
    if (collisionActive && this.collisionTick % 12 === 0) {
      const cand = this.labelObjs.filter(
        (r) => r.fade !== 'band' && r.t.visible && r.t.textRenderInfo,
      );
      const rects = cand.map((r) => {
        const [cx, cy] = this.screenOf([r.t.position.x, r.t.position.y, 0]);
        const b = r.t.textRenderInfo!.blockBounds;
        const wWorld = Math.max(0.5, b[2] - b[0]);
        const hWorld = Math.max(0.5, b[3] - b[1]);
        const [ex] = this.screenOf([r.t.position.x + 1, r.t.position.y, 0]);
        const pxPerUnit = Math.abs(ex - cx) || 1;
        const w = wWorld * pxPerUnit;
        const h = hWorld * pxPerUnit;
        // anchorX left/right shift the box off the position point
        const ax = r.t.anchorX === 'left' ? 0 : r.t.anchorX === 'right' ? -w : -w / 2;
        return { r, x0: cx + ax, y0: cy - h / 2, x1: cx + ax + w, y1: cy + h / 2 };
      });
      const losers = new Set<number>();
      for (let i = 0; i < rects.length; i++) {
        for (let j = i + 1; j < rects.length; j++) {
          const A = rects[i];
          const B = rects[j];
          if (A.r.grpId === B.r.grpId) continue;
          const overlap =
            Math.min(A.x1, B.x1) - Math.max(A.x0, B.x0) > 1 &&
            Math.min(A.y1, B.y1) - Math.max(A.y0, B.y0) > 1;
          if (!overlap) continue;
          // lower priority fades (larger prio number loses; ties: later group)
          losers.add(A.r.prio === B.r.prio ? Math.max(A.r.grpId, B.r.grpId) : A.r.prio > B.r.prio ? A.r.grpId : B.r.grpId);
        }
      }
      for (const r of this.labelObjs) r.caTarget = losers.has(r.grpId) ? 0 : 1;
    } else if (!collisionActive) {
      for (const r of this.labelObjs) r.caTarget = 1;
    }
    for (const rec of this.labelObjs) {
      if (rec.fade === 'band') continue;
      rec.ca += (rec.caTarget - rec.ca) * Math.min(1, dt / 0.35);
      const baseFade = rec.fade === 'north' ? 1 - 0.25 * ch2 : 1;
      rec.t.material.opacity = baseFade * rec.ca;
    }

    // ---- breathing: halos only, star points never move (11s period) ----
    const breathWave = (p: number): number => {
      if (p < 0.25) return 0.5 - 0.5 * Math.cos((p / 0.25) * Math.PI);
      if (p < 0.45) return 1;
      return 0.5 + 0.5 * Math.cos(((p - 0.45) / 0.55) * Math.PI);
    };
    if (!this.reducedMotion) {
      for (const glow of this.guestGlows) {
        const base = 0.34 + 0.3 * ch3;
        const wave = glow.breathe ? breathWave((tt / 11 + glow.idx * 0.31) % 1) : 0.4;
        glow.mat.opacity = base * (0.85 + 0.15 * wave);
        glow.spr.visible = glow.mat.opacity > 0.004;
        const sc = 5.5 * (1 + 0.4 * ch3);
        glow.spr.scale.set(sc, sc, 1);
      }
    } else {
      for (const glow of this.guestGlows) {
        glow.mat.opacity = (0.34 + 0.3 * ch3) * 0.925;
        glow.spr.visible = glow.mat.opacity > 0.004;
      }
    }
    // star point opacity stays put (no pulse on the carved dot itself)
    {
      const attr = this.guestPts.geometry.attributes.aOpacity as THREE.BufferAttribute;
      let dirty = false;
      for (let i = 0; i < attr.array.length; i++) {
        if ((attr.array as Float32Array)[i] !== this.guestBaseOpacity[i]) {
          (attr.array as Float32Array)[i] = this.guestBaseOpacity[i];
          dirty = true;
        }
      }
      if (dirty) attr.needsUpdate = true;
    }

    this.updateTooltip();
    // 虚位空星: slow faint pulse on the empty pole ring (never on a set star)
    if (this.northVacant) {
      const a = this.northPts.geometry.attributes.aOpacity as THREE.BufferAttribute;
      (a.array as Float32Array)[0] = this.reducedMotion
        ? 0.3
        : 0.28 + 0.14 * Math.sin(tt * 0.9);
      a.needsUpdate = true;
    }
    if (this.selectedIdx >= 0) {
      const p = this.clickables[this.selectedIdx].pos();
      this.selRing.visible = true;
      this.selRing.position.set(p[0], p[1], p[2] ?? 0);
      const pulse = this.reducedMotion ? 1 : 1 + 0.04 * Math.sin(tt * 3);
      this.selRing.scale.set(pulse, pulse, 1);
    }
    if (this.controls) {
      this.controls.enabled = this.state.t < 0.5;
      this.controls.update();
      const tg = this.controls.target;
      const cx = Math.max(-70, Math.min(70, tg.x));
      const cy = Math.max(-70, Math.min(70, tg.y));
      if (cx !== tg.x || cy !== tg.y) {
        this.camera.position.x += cx - tg.x;
        this.camera.position.y += cy - tg.y;
        tg.x = cx;
        tg.y = cy;
        tg.z = 0;
      }
    }
    if (!this.fxPass.enabled) this.renderer.render(this.scene, this.camera);
    else this.composer.render();
  }
}
