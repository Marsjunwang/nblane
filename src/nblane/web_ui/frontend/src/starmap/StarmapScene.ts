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
  INK, GOLD, GOLD_BRIGHT,
  type StarmapLayout,
} from './layout';
import { mulberry32 } from './rng';
import type { StarmapSnapshot } from './snapshot';
import fontUrl from './assets/NotoSerifSC-subset.ttf?url';
import imingUrl from './assets/fonts/IMing-subset.ttf?url';
import wenkaiUrl from './assets/fonts/LXGWWenKai-subset.ttf?url';
import fellUrl from './assets/fonts/IMFellEnglish-subset.ttf?url';

export interface StarmapSelection {
  kind: 'north' | 'goal' | 'planet' | 'guest' | 'skill';
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
  initialState?: 'planisphere' | 'deepspace';
}

type FadeMat = { mat: THREE.LineBasicMaterial; plan: number; deep: number; ch: number };
type LabelRec = {
  t: Text;
  fade: 'band' | 'north' | 'goal';
  planPos: number[];
  deepPos: number[] | null;
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
  private labelObjs: LabelRec[] = [];
  private morphables: Morphable[] = [];
  private dimPts!: THREE.Points;
  private litPts!: THREE.Points;
  private goalPts!: THREE.Points;
  private planetPts!: THREE.Points;
  private guestPts!: THREE.Points;
  private planetInnerPts!: THREE.Points;
  private moonPts!: THREE.Points;
  private guestTails!: THREE.LineSegments;
  private glows: { spr: THREE.Sprite; mat: THREE.SpriteMaterial; getPos: () => number[]; maxOpacity: number }[] = [];
  private guestGlows: { spr: THREE.Sprite; mat: THREE.SpriteMaterial; idx: number; breathe: boolean }[] = [];
  private nebulae: { spr: THREE.Sprite; mat: THREE.SpriteMaterial; op: number }[] = [];
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
  private clickables: { kind: StarmapSelection['kind']; idx: number; title: string; pos: () => number[] }[] = [];
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
    this.reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
    this.coarsePointer = matchMedia('(pointer: coarse)').matches;
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

    this.bakeBackgrounds();
    this.buildLinework();

    this.dimPts = this.makePoints({
      plan: this.L.dim.plan,
      deep: this.L.dim.deep,
      size: this.L.dim.size,
      opacity: this.L.dim.opacity,
      core: this.L.dim.core,
      ring: this.L.dim.ring,
      color: this.L.dim.color,
    });
    this.dimPts.userData.filler = this.L.dim.filler;
    this.dimPts.userData.baseOpacity = new Float32Array(this.L.dim.opacity);
    this.dimPts.userData.baseSize = new Float32Array(this.L.dim.size);
    this.dimPts.userData.baseRing = new Float32Array(
      this.dimPts.geometry.attributes.aRing.array,
    );
    this.dimPts.userData.deepOpScale = new Float32Array(this.L.dim.deepOpScale);
    this.dimPts.userData.deepSizeScale = new Float32Array(this.L.dim.deepSizeScale);

    this.litPts = this.makePoints({
      plan: this.L.lit.plan,
      deep: this.L.lit.deep,
      size: this.L.lit.size,
      opacity: this.L.lit.opacity,
      core: this.L.lit.core,
      ring: this.L.lit.ring,
      color: this.L.lit.color,
    });
    this.goalPts = this.makePoints({
      plan: this.L.goals.flatMap((g) => g.plan),
      deep: this.L.goals.flatMap((g) => g.deep),
      size: this.L.goals.map(() => 2.6),
      opacity: this.L.goals.map(() => 1),
      core: this.L.goals.map(() => 1),
      ring: this.L.goals.map(() => 1),
      color: this.L.goals.flatMap(() => [0.91, 0.72, 0.36]),
    });
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
    const northPts = this.makePoints({
      plan: [0, 0, 0],
      deep: [0, 0, 0],
      size: [4.4],
      opacity: [1],
      core: [1],
      ring: [0],
      color: [0.98, 0.85, 0.55],
    });
    this.planetPts = this.makePoints({
      plan: this.L.planets.flatMap((p) => p.plan),
      deep: this.L.planets.flatMap((p) => p.deep),
      size: this.L.planets.map(() => 3.0),
      opacity: this.L.planets.map((p) => (p.status === 'active' ? 0.9 : 0.35)),
      core: this.L.planets.map(() => 0.4),
      ring: this.L.planets.map(() => 1),
      color: this.L.planets.flatMap(() => [0.961, 0.918, 0.824]),
    });
    this.moonPts = this.makePoints({
      plan: this.L.moons.plan,
      deep: this.L.moons.deep,
      size: this.L.moons.size,
      opacity: this.L.moons.opacity,
      core: this.L.moons.size.map(() => 1),
      ring: this.L.moons.size.map(() => 0),
      color: this.L.moons.size.flatMap(() => [0.961, 0.918, 0.824]),
    });
    const seatedPts = this.makePoints({
      plan: this.L.seated.plan,
      deep: this.L.seated.deep,
      size: this.L.seated.size,
      opacity: this.L.seated.opacity,
      core: this.L.seated.size.map(() => 1),
      ring: this.L.seated.size.map(() => 0),
      color: this.L.seated.size.flatMap(() => [0.961, 0.918, 0.824]),
    });
    this.guestPts = this.makePoints({
      plan: this.L.guests.flatMap((g) => g.plan),
      deep: this.L.guests.flatMap((g) => g.deep),
      size: this.L.guests.map(() => 1.15),
      opacity: this.L.guests.map(() => 0.95),
      core: this.L.guests.map(() => 1),
      ring: this.L.guests.map(() => 0),
      color: this.L.guests.flatMap(() => [1.0, 0.95, 0.85]),
    });
    const dustPts = this.makePoints({
      plan: this.L.dust.plan,
      deep: this.L.dust.deep,
      size: this.L.dust.size,
      opacity: this.L.dust.opacity,
      core: this.L.dust.size.map(() => 1),
      ring: this.L.dust.size.map(() => 0),
      color: this.L.dust.size.flatMap(() => [0.961, 0.918, 0.824]),
    });
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
    });

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
            this.lineMat(GOLD, 0.55, 0, 2),
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
    addGlow(() => [0, 0, 0], 20, 0xffd98a, 0.8); // north star warm core glow
    addGlow(() => [0, 0, 0], 40, 0x96a8dc, 0.1); // north star cool halo
    this.L.goals.forEach((_g, i) =>
      addGlow(() => {
        const p = this.goalPts.geometry.attributes.position.array as Float32Array;
        return [p[i * 3], p[i * 3 + 1], p[i * 3 + 2]];
      }, 9, 0xffcd78, 0.35),
    );
    // 呼吸 halos: the breath moves ONLY the halo, never the star point itself
    this.guestGlows = this.L.guests.map((g, i) => {
      const mat = new THREE.SpriteMaterial({
        map: glowTex,
        color: 0xffe8c0,
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
      this.dimPts, this.litPts, this.goalPts, courtPts, northPts,
      this.planetPts, this.planetInnerPts, this.moonPts, seatedPts,
      this.guestPts, dustPts,
      this.guestTails as unknown as Morphable,
      dustTrails,
    ] as Morphable[];
    for (const pts of [
      this.goalPts, this.planetPts, this.planetInnerPts, this.moonPts,
      this.guestPts, this.guestTails,
    ]) {
      pts.userData.orbitManaged = true;
    }

    // ---------- motion bookkeeping ----------
    this.goalPeriods = this.L.goals.map((_, i) => 60 + i * 15);
    this.planetPeriods = this.L.planets.map((_, i) => 40 + i * 5);
    this.guestPeriods = this.L.guests.map((_, i) => 8 + i * 2.3);
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
      { title: '北极星', info: snapshot.north_star.split(/[，。]/)[0], pos: () => [0, 0, 0] },
      ...this.L.goals.map((g, i) => ({
        title: g.title,
        info: '目标恒星',
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
      { kind: 'north', idx: -1, title: '北极星', pos: () => [0, 0, 0] },
      ...this.L.goals.map((g, i) => ({
        kind: 'goal' as const, idx: i, title: g.title, pos: () => attrPos(this.goalPts, i),
      })),
      ...this.L.planets.map((p, i) => ({
        kind: 'planet' as const, idx: i, title: p.title, pos: () => attrPos(this.planetPts, i),
      })),
      ...this.L.guests.map((g, i) => ({
        kind: 'guest' as const, idx: i, title: g.title, pos: () => attrPos(this.guestPts, i),
      })),
      ...this.L.lit.skills.map((s, i) => ({
        kind: 'skill' as const, idx: i, title: s.label, pos: () => attrPos(this.litPts, i),
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

  /** Morph to 图态 (0) or 境态 (1). */
  goTo(target: number, instant = false) {
    if (this.tween) this.tween.kill();
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

  /** Morph toggle button hook. */
  toggle() {
    this.goTo(this.state.t > 0.5 ? 0 : 1);
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
    const ringMat = this.lineMat(INK, 0.42, 0.2, 2);
    const tickMat = this.lineMat(INK, 0.55, 0, 1);
    const spokeMat = this.lineMat(INK, 0.18, 0, 1);
    const subSpokeMat = this.lineMat(INK, 0.08, 0, 1);
    const bandMat = this.lineMat(INK, 0.5, 0, 2);
    const asterMat = this.lineMat(INK, 0.52, 0.15, 2);
    const courtMat = this.lineMat(INK, 0.35, 0, 2);

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
      // asterism links
      const pts: THREE.Vector3[] = [];
      const P = L.lit.plan;
      for (let i = 0; i < L.lit.links.length; i += 2) {
        const a = L.lit.links[i] * 3;
        const b = L.lit.links[i + 1] * 3;
        pts.push(new THREE.Vector3(P[a], P[a + 1], 0));
        pts.push(new THREE.Vector3(P[b], P[b + 1], 0));
      }
      const geo = new THREE.BufferGeometry().setFromPoints(pts);
      this.chart.add(new THREE.LineSegments(geo, asterMat));
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
    // engraved ring around the north star
    addLine(this.circlePoints(4.2, 64), this.lineMat(INK, 0.55, 0, 2), true);
  }

  private makePoints(opts: {
    plan: number[];
    deep: number[];
    size: number[];
    opacity: number[];
    core: number[];
    ring: number[];
    color: number[];
  }): THREE.Points {
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
    this.chart.add(points);
    return points;
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
    this.labelObjs.push({ t, fade, planPos: pos.slice(), deepPos: deepPos ? deepPos.slice() : null });
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
    },
  ) {
    const { size = 3.6, color = 0xeed696, pos, align = 'left', fade = 'goal', goalIdx = -1 } = opts;
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
      this.labelObjs.push({ t, fade, planPos: pos.slice(), deepPos: null });
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

  private buildLabels() {
    const L = this.L;
    // outer category-name band: chars rotated along the arc (一点明体, 刻感)
    for (const sec of L.sectors) {
      const mid = sec.start + sec.width / 2;
      const chars = Array.from(sec.name);
      const angStep = ((3.4 * 1.25) / BAND_TEXT) * (180 / Math.PI);
      const a0 = mid - (angStep * (chars.length - 1)) / 2;
      chars.forEach((ch, i) => {
        const a = a0 + i * angStep;
        const rad = (a * Math.PI) / 180;
        this.addLabel(ch, {
          size: 3.2,
          color: INK,
          font: imingUrl,
          fade: 'band',
          pos: [BAND_TEXT * Math.cos(rad), BAND_TEXT * Math.sin(rad), 0],
          rotZ: rad + Math.PI / 2,
        });
      });
    }
    // goal labels (一点明体 + IM Fell segmented for mixed strings)
    L.goals.forEach((g, gi) => {
      const cos = Math.cos((g.angle * Math.PI) / 180);
      const align = cos > 0.35 ? 'left' : cos < -0.35 ? 'right' : 'center';
      const rr = R_GOAL + 8;
      const a = (g.angle * Math.PI) / 180;
      this.addSegmentedLabel(g.title, {
        size: 3.6,
        color: 0xeed696,
        align,
        goalIdx: gi,
        pos: [rr * Math.cos(a) + (align === 'left' ? 1 : align === 'right' ? -1 : 0), rr * Math.sin(a), 0],
      });
    });
    // north star label (two lines, first clause)
    const clause = this.snapshot.north_star.split(/[，。]/)[0];
    const idx = clause.indexOf('成为');
    const nsLines = idx > 0 ? [clause.slice(0, idx + 2), clause.slice(idx + 2)] : [clause, ''];
    this.addLabel(nsLines[0], {
      size: 3.8,
      color: INK,
      font: wenkaiUrl,
      anchorX: 'left',
      pos: [6.5, 3.4, 0],
      deepPos: [10.5, -8.5, 0],
      fade: 'north',
    });
    this.addLabel(nsLines[1], {
      size: 3.8,
      color: 0xeed696,
      font: wenkaiUrl,
      anchorX: 'left',
      pos: [6.5, -2.6, 0],
      deepPos: [10.5, -13.6, 0],
      fade: 'north',
    });
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
    // dim field restraint (月.png) + ring taper, both late-phase
    const dimAttr = this.dimPts.geometry.attributes.aOpacity as THREE.BufferAttribute;
    const dimSizeAttr = this.dimPts.geometry.attributes.aSize as THREE.BufferAttribute;
    const dimRingAttr = this.dimPts.geometry.attributes.aRing as THREE.BufferAttribute;
    const base = this.dimPts.userData.baseOpacity as Float32Array;
    const baseSz = this.dimPts.userData.baseSize as Float32Array;
    const baseRing = this.dimPts.userData.baseRing as Float32Array;
    const dOpS = this.dimPts.userData.deepOpScale as Float32Array;
    const dSzS = this.dimPts.userData.deepSizeScale as Float32Array;
    const filler = this.dimPts.userData.filler as number[];
    for (let i = 0; i < dimAttr.array.length; i++) {
      const densityGate = filler[i] ? this.state.density : 1;
      (dimAttr.array as Float32Array)[i] = (base[i] * densityGate * (1 + (dOpS[i] - 1) * ch3));
      (dimSizeAttr.array as Float32Array)[i] = baseSz[i] * (1 + (dSzS[i] - 1) * ch3);
      (dimRingAttr.array as Float32Array)[i] = baseRing[i] * (1 - 0.55 * ch3);
    }
    dimAttr.needsUpdate = true;
    dimSizeAttr.needsUpdate = true;
    dimRingAttr.needsUpdate = true;
    this.applyBackground(ch2, this.state.duskPos);
    this.fxPass.enabled = !this.softGL && ch3 > 0.02;
    this.bloom.intensity = 0.7 * ch3 * this.state.bloom;
    this.vignette.style.opacity = String(0.55 + 0.45 * ch2);
    // React-owned DOM
    const domOpacity = String(1 - ch2);
    const refs = this.opts.domRefs;
    if (refs?.cartouche) refs.cartouche.style.opacity = domOpacity;
    if (refs?.briefing) refs.briefing.style.opacity = domOpacity;
    if (refs?.toggle) refs.toggle.textContent = t > 0.5 ? '→ 图态' : '→ 境态';
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
    if (c.kind === 'north') return [['类型', '北极星'], ['铭文', snapshot.north_star]];
    if (c.kind === 'goal') {
      const g = snapshot.goals[c.idx];
      return [
        ['状态', g.status],
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
        ['所属目标', gi >= 0 ? snapshot.goals[gi].title : '（自由轨道）'],
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
    const s = this.L.lit.skills[c.idx];
    return [['类别', s.category], ['状态', s.status], ['关联证据', `${s.evidenceCount} 条`]];
  }

  private openDetail(i: number) {
    this.selectedIdx = i;
    const c = this.clickables[i];
    this.opts.onSelect?.({ kind: c.kind, title: c.title, rows: this.detailRows(c) });
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

    const rotZ = (x: number, y: number, a: number): [number, number] => [
      x * Math.cos(a) - y * Math.sin(a),
      x * Math.sin(a) + y * Math.cos(a),
    ];

    // ---- orbit-managed clouds: single writer (morph lerp + integrated phase) ----
    {
      const gAttr = this.goalPts.geometry.attributes.position as THREE.BufferAttribute;
      const goalNow = L.goals.map((g, i) => {
        const deep = this.goalDeepBase[i];
        this.goalPhase[i] += dt * ((2 * Math.PI) / this.goalPeriods[i]) * ch3;
        const [rx, ry] = rotZ(deep[0], deep[1], this.goalPhase[i]);
        return [
          g.plan[0] + (deep[0] - g.plan[0]) * ch2 + (rx - deep[0]),
          g.plan[1] + (deep[1] - g.plan[1]) * ch2 + (ry - deep[1]),
          g.plan[2] + (deep[2] - g.plan[2]) * ch2,
        ];
      });
      goalNow.forEach((p, i) => gAttr.setXYZ(i, p[0], p[1], p[2]));
      gAttr.needsUpdate = true;
      for (const grp of this.goalLabelGroups) {
        if (!grp.base.length) continue;
        const gp = goalNow[grp.goalIdx];
        const morphBase = L.goals[grp.goalIdx].plan;
        const deep = this.goalDeepBase[grp.goalIdx];
        const bx = morphBase[0] + (deep[0] - morphBase[0]) * ch2;
        const by = morphBase[1] + (deep[1] - morphBase[1]) * ch2;
        const dx = gp[0] - bx;
        const dy = gp[1] - by;
        grp.segs.forEach((s, si) => s.position.set(grp.base[si][0] + dx, grp.base[si][1] + dy, 0));
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
        const [rx, ry] = rotZ(deep[0] - anchorDeep[0], deep[1] - anchorDeep[1], this.planetPhase[i]);
        const morphX = p.plan[0] + (deep[0] - p.plan[0]) * ch2;
        const morphY = p.plan[1] + (deep[1] - p.plan[1]) * ch2;
        return [
          morphX + (anchorNow[0] - anchorDeep[0]) + (rx - (deep[0] - anchorDeep[0])),
          morphY + (anchorNow[1] - anchorDeep[1]) + (ry - (deep[1] - anchorDeep[1])),
          p.plan[2] + (deep[2] - p.plan[2]) * ch2,
        ];
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

      const guAttr = this.guestPts.geometry.attributes.position as THREE.BufferAttribute;
      const tAttr = this.guestTails.geometry.attributes.position as THREE.BufferAttribute;
      L.guests.forEach((g, i) => {
        const deep = this.guestDeepBase[i];
        this.guestPhase[i] += dt * ((2 * Math.PI) / this.guestPeriods[i]) * ch3;
        const drift = 7 * ch3;
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
