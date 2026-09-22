/* 成长星图 playground: interactive planisphere <-> deepspace morph.
 * Visual baseline: .dev-assets/design-mockups/starchart.js (v2) + 月.png. */
import * as THREE from 'three';
import { Text } from 'troika-three-text';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import gsap from 'gsap';
import { EffectComposer, RenderPass, EffectPass, BloomEffect } from 'postprocessing';
import { interpolate, converter } from 'culori';
import snapshot from './data/snapshot.json';
import fontUrl from './assets/NotoSerifSC-subset.ttf?url';
import imingUrl from './assets/fonts/IMing-subset.ttf?url';
import wenkaiUrl from './assets/fonts/LXGWWenKai-subset.ttf?url';
import fellUrl from './assets/fonts/IMFellEnglish-subset.ttf?url';
import titleV2Url from './assets/title-v2-b.svg?url';
import './style.css';
import {
  buildLayout, R, R_IN, R_GOAL, R_OUT, BAND_IN, BAND_OUT, BAND_TEXT,
  INK, GOLD, GOLD_BRIGHT,
} from './layout.js';
import { mulberry32 } from './rng.js';

const params = new URLSearchParams(location.search);
const START_STATE = params.get('state') || 'planisphere';
const SHOW_PANEL = params.get('panel') !== '0';
const NO_FX = params.get('fx') === '0'; // perf fallback: skip post-processing
const FORCE_FX = params.get('fx') === '1'; // force composer path even on software GL
const REDUCED_MOTION = matchMedia('(prefers-reduced-motion: reduce)').matches;
const COARSE_POINTER = matchMedia('(pointer: coarse)').matches;

const L = buildLayout(snapshot);
window.__layout = L; // debug aid for tooling/screenshots
// ---------- renderer / scene ----------
const heart = document.getElementById('heart');
const canvas = document.getElementById('scene');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
renderer.setClearColor(0x000000, 0); // DOM layer carries the background
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

const scene = new THREE.Scene();
window.__scene = scene; // debug/perf tooling
const camera = new THREE.PerspectiveCamera(45, 1, 1, 2000);
const CAM_PLAN = { pos: new THREE.Vector3(0, 4, 346), look: new THREE.Vector3(0, 0, 0) };
const CAM_DEEP = { pos: new THREE.Vector3(0, 72, 232), look: new THREE.Vector3(0, -4, 0) };
// planisphere camera distance is computed so the outer band circle inscribes
// the heart's short side (画心内切)
function fitPlanCamera() {
  const w = heart.clientWidth || 1600, h = heart.clientHeight || 900;
  const fovTan = Math.tan((camera.fov * Math.PI) / 360);
  CAM_PLAN.pos.z = (BAND_OUT + 16) / (fovTan * Math.min(1, w / h));
}

const chart = new THREE.Group();
scene.add(chart);

// ---------- background: baked textures (stone / dusk / slate) + DOM vignette ----------
// Full-screen procedural shaders are prohibitively slow on software GL; the
// whole background is baked once into 1024x640 canvases and cross-faded.
// Blue-hour script: stone -> dusk (绀青 + warm pole glow) -> deep slate,
// keyframe colors interpolated in OKLCH so the path never turns muddy grey.
const oklchToRgb = converter('rgb');
const oklchMix = (a, b, t) => {
  const c = oklchToRgb(interpolate([a, b], 'oklch')(t));
  return [Math.round(c.r * 255), Math.round(c.g * 255), Math.round(c.b * 255)];
};
const DUSK_TOP = oklchMix('#1c2c4e', '#10172c', 0.4); // 绀青, slightly violet
const DUSK_BOT = oklchMix('#182642', '#0d1322', 0.4);
function makeBgCanvas(mode) {
  const W = 1024, H = 640;
  const c = document.createElement('canvas');
  c.width = W; c.height = H;
  const x = c.getContext('2d');
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
  // large uneven ink blotches
  for (let i = 0; i < 9; i++) {
    const bx = rnd() * W, by = rnd() * H, br = 120 + rnd() * 260;
    const light = rnd() > 0.5;
    const a = (stone ? 0.05 : dusk ? 0.04 : 0.035) * (0.7 + rnd() * 0.6);
    const bg = x.createRadialGradient(bx, by, 0, bx, by, br);
    bg.addColorStop(0, light ? `rgba(70,98,132,${a})` : `rgba(10,20,36,${a})`);
    bg.addColorStop(1, 'rgba(0,0,0,0)');
    x.fillStyle = bg;
    x.fillRect(bx - br, by - br, br * 2, br * 2);
  }
  // dusk frame: the last warm light pooled low-center, near the pole star
  if (dusk) {
    const wg = x.createRadialGradient(W / 2, H * 0.62, 0, W / 2, H * 0.62, W * 0.34);
    wg.addColorStop(0, 'rgba(196,138,64,0.13)');
    wg.addColorStop(0.55, 'rgba(150,100,52,0.05)');
    wg.addColorStop(1, 'rgba(150,100,52,0)');
    x.fillStyle = wg;
    x.fillRect(0, 0, W, H);
  }
  // faint milky band (same diagonal as the dust ribbon)
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
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}
// the baked backgrounds live in the DOM compositor: full-screen texture
// rasterization inside WebGL is the single biggest cost on software GL
document.getElementById('bg-stone').style.backgroundImage =
  `url(${makeBgCanvas('stone').image.toDataURL('image/png')})`;
const bgDeepEl = document.getElementById('bg-deep');
bgDeepEl.style.backgroundImage =
  `url(${makeBgCanvas('deep').image.toDataURL('image/png')})`;
const bgDuskEl = document.getElementById('bg-dusk');
bgDuskEl.style.backgroundImage =
  `url(${makeBgCanvas('dusk').image.toDataURL('image/png')})`;
// three-layer cross-fade driven by the morph's ch2 channel:
// 0 → duskPos: stone dissolves into dusk; duskPos → 1: dusk sinks into deep
function applyBackground(ch2, duskPos) {
  if (ch2 <= duskPos) {
    bgDuskEl.style.opacity = String(ch2 / duskPos);
    bgDeepEl.style.opacity = '0';
  } else {
    bgDuskEl.style.opacity = '1'; // dusk stays beneath, deep sinks over it
    bgDeepEl.style.opacity = String((ch2 - duskPos) / (1 - duskPos));
  }
}

// ---------- chart linework (rings, ticks, wobbled spokes, band) ----------
const fadeMats = []; // {mat, plan, deep, ch} — ch: morph channel (1=survey lines, 2=structure)
function lineMat(color, plan, deep, ch = 1) {
  const mat = new THREE.LineBasicMaterial({ color, transparent: true, opacity: plan, depthWrite: false });
  fadeMats.push({ mat, plan, deep, ch });
  return mat;
}
function circlePoints(r, seg = 160) {
  const pts = [];
  for (let i = 0; i <= seg; i++) {
    const a = (i / seg) * Math.PI * 2;
    pts.push(new THREE.Vector3(r * Math.cos(a), r * Math.sin(a), 0));
  }
  return pts;
}
function addLine(pts, mat, loop = false) {
  const geo = new THREE.BufferGeometry().setFromPoints(pts);
  const line = loop ? new THREE.LineLoop(geo, mat) : new THREE.Line(geo, mat);
  chart.add(line);
  return line;
}

const srnd = mulberry32(53);
function wobblySpoke(r1, r2, deg, mat) {
  const pts = [];
  for (let i = 0; i <= 4; i++) {
    const rr = r1 + ((r2 - r1) * i) / 4;
    const aa = deg + (i > 0 && i < 4 ? (srnd() - 0.5) * 1.4 : 0);
    const a = (aa * Math.PI) / 180;
    pts.push(new THREE.Vector3(rr * Math.cos(a), rr * Math.sin(a), 0));
  }
  addLine(pts, mat);
}

const ringMat = lineMat(INK, 0.42, 0.20, 2); // goal ring survives as a faint orbit
const tickMat = lineMat(INK, 0.55, 0, 1);
const spokeMat = lineMat(INK, 0.18, 0, 1);
const subSpokeMat = lineMat(INK, 0.08, 0, 1);
const bandMat = lineMat(INK, 0.5, 0, 2);
const asterMat = lineMat(INK, 0.52, 0.15, 2);
const courtMat = lineMat(INK, 0.35, 0, 2);

for (const [r, m] of [[R_GOAL, ringMat], [R_OUT, ringMat], [R, tickMat], [BAND_IN, bandMat], [BAND_OUT, bandMat]]) {
  addLine(circlePoints(r), m, true);
}
{ // 恒显圈, with an arc gap behind the north-star label (clearPatch, geometrically)
  const pts = [];
  for (let d = 18; d <= 342; d += 2) {
    const a = (d * Math.PI) / 180;
    pts.push(new THREE.Vector3(R_IN * Math.cos(a), R_IN * Math.sin(a), 0));
  }
  addLine(pts, ringMat);
}
// tick marks
{
  const pts = [];
  for (let d = 0; d < 360; d += 6) {
    const a = (d * Math.PI) / 180;
    const r2 = R + (d % 30 === 0 ? 3.25 : 1.5);
    pts.push(new THREE.Vector3(R * Math.cos(a), R * Math.sin(a), 0));
    pts.push(new THREE.Vector3(r2 * Math.cos(a), r2 * Math.sin(a), 0));
  }
  const geo = new THREE.BufferGeometry().setFromPoints(pts);
  chart.add(new THREE.LineSegments(geo, tickMat));
}
// sector spokes (unequal) + jittered sub-spokes, from 恒显圈 outward
const normDeg = (a) => { a = a % 360; if (a > 180) a -= 360; if (a < -180) a += 360; return a; };
for (const sec of L.sectors) {
  if (Math.abs(normDeg(sec.start)) >= 12) wobblySpoke(R_IN, R, sec.start, spokeMat);
  const parts = Math.max(1, Math.round(sec.count / 6));
  const fracs = [];
  for (let f = 1; f < parts; f++) fracs.push(f / parts + ((srnd() - 0.5) * 0.5) / parts);
  fracs.sort();
  for (const fr of fracs) {
    const a = sec.start + sec.width * fr;
    if (Math.abs(normDeg(a)) >= 12) wobblySpoke(R_IN, R, a, subSpokeMat);
  }
  // band divider
  const a = (sec.start * Math.PI) / 180;
  addLine(
    [new THREE.Vector3(BAND_IN * Math.cos(a), BAND_IN * Math.sin(a), 0),
     new THREE.Vector3(BAND_OUT * Math.cos(a), BAND_OUT * Math.sin(a), 0)],
    bandMat
  );
}
// asterism links
{
  const pts = [];
  const P = L.lit.plan;
  for (let i = 0; i < L.lit.links.length; i += 2) {
    const a = L.lit.links[i] * 3, b = L.lit.links[i + 1] * 3;
    pts.push(new THREE.Vector3(P[a], P[a + 1], 0));
    pts.push(new THREE.Vector3(P[b], P[b + 1], 0));
  }
  const geo = new THREE.BufferGeometry().setFromPoints(pts);
  chart.add(new THREE.LineSegments(geo, asterMat));
}
// court links
{
  const pts = [];
  const P = L.court.plan;
  for (const [a, b] of L.court.links) {
    pts.push(new THREE.Vector3(P[a * 3], P[a * 3 + 1], 0));
    pts.push(new THREE.Vector3(P[b * 3], P[b * 3 + 1], 0));
  }
  const geo = new THREE.BufferGeometry().setFromPoints(pts);
  chart.add(new THREE.LineSegments(geo, courtMat));
}
// engraved ring around the north star
addLine(circlePoints(4.2, 64), lineMat(INK, 0.55, 0, 2), true);

// ---------- points shader (shape channels: core + ring, both interpolatable) ----------
function makePoints({ plan, deep, size, opacity, core, ring, color }) {
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
  chart.add(points);
  return points;
}

const LEGACY_STARS = params.get('stars') === 'legacy';

const dimPts = makePoints({
  plan: L.dim.plan, deep: L.dim.deep,
  size: L.dim.size, opacity: L.dim.opacity,
  core: LEGACY_STARS ? L.dim.core.map(() => 1) : L.dim.core,
  ring: LEGACY_STARS ? L.dim.legacyRing : L.dim.ring,
  color: L.dim.color,
});
dimPts.userData.filler = L.dim.filler;
dimPts.userData.baseOpacity = new Float32Array(L.dim.opacity);
dimPts.userData.baseSize = new Float32Array(L.dim.size);
dimPts.userData.baseRing = new Float32Array(dimPts.geometry.attributes.aRing.array);
dimPts.userData.deepOpScale = new Float32Array(L.dim.deepOpScale);
dimPts.userData.deepSizeScale = new Float32Array(L.dim.deepSizeScale);

const litPts = makePoints({
  plan: L.lit.plan, deep: L.lit.deep,
  size: L.lit.size, opacity: L.lit.opacity,
  core: L.lit.core, ring: L.lit.ring, color: L.lit.color,
});

// goals (gold, 点外套圈) + court stars
const goalPts = makePoints({
  plan: L.goals.flatMap((g) => g.plan),
  deep: L.goals.flatMap((g) => g.deep),
  size: L.goals.map(() => 2.6),
  opacity: L.goals.map(() => 1),
  core: L.goals.map(() => 1),
  ring: L.goals.map(() => 1),
  color: L.goals.flatMap(() => [0.91, 0.72, 0.36]),
});
const courtPts = makePoints({
  plan: L.court.plan, deep: L.court.plan.map((v, i) => (i % 3 === 2 ? (v ? v : 0) : v * 1.6)),
  size: L.court.size,
  opacity: L.court.gold.map((g) => (g ? 1 : 0.85)),
  core: L.court.gold.map(() => 1),
  ring: L.court.gold.map(() => 0),
  color: L.court.gold.flatMap((g) => (g ? [0.91, 0.72, 0.36] : [0.961, 0.918, 0.824])),
});
const northPts = makePoints({
  plan: [0, 0, 0], deep: [0, 0, 0],
  size: [4.4], opacity: [1], core: [1], ring: [0], color: [[0.98, 0.85, 0.55]].flat(),
});

// ---------- snapshot v2: planets / moons / guests / seated / dust ----------
// planets: hollow carved rings (空圈), gold progress arc when derivable
const planetPts = makePoints({
  plan: L.planets.flatMap((p) => p.plan), deep: L.planets.flatMap((p) => p.deep),
  size: L.planets.map(() => 3.0),
  opacity: L.planets.map((p) => (p.status === 'active' ? 0.9 : 0.35)),
  core: L.planets.map(() => 0.4), ring: L.planets.map(() => 1),
  color: L.planets.flatMap(() => [0.961, 0.918, 0.824]),
});
const moonPts = makePoints({
  plan: L.moons.plan, deep: L.moons.deep, size: L.moons.size, opacity: L.moons.opacity,
  core: L.moons.size.map(() => 1), ring: L.moons.size.map(() => 0),
  color: L.moons.size.flatMap(() => [0.961, 0.918, 0.824]),
});
const seatedPts = makePoints({
  plan: L.seated.plan, deep: L.seated.deep, size: L.seated.size, opacity: L.seated.opacity,
  core: L.seated.size.map(() => 1), ring: L.seated.size.map(() => 0),
  color: L.seated.size.flatMap(() => [0.961, 0.918, 0.824]),
});
const guestPts = makePoints({
  plan: L.guests.flatMap((g) => g.plan), deep: L.guests.flatMap((g) => g.deep),
  size: L.guests.map(() => 1.15),
  opacity: L.guests.map(() => 0.95),
  core: L.guests.map(() => 1), ring: L.guests.map(() => 0),
  color: L.guests.flatMap(() => [1.0, 0.95, 0.85]),
});
const dustPts = makePoints({
  plan: L.dust.plan, deep: L.dust.deep, size: L.dust.size, opacity: L.dust.opacity,
  core: L.dust.size.map(() => 1), ring: L.dust.size.map(() => 0),
  color: L.dust.size.flatMap(() => [0.961, 0.918, 0.824]),
});
// dust directional streaks along the band tangent (makes the ribbon readable)
const dustTrails = (() => {
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(L.dust.trailPlan), 3));
  const line = new THREE.LineSegments(geo, lineMat(INK, 0.26, 0.22, 3));
  chart.add(line);
  return { geometry: geo, userData: { plan: new Float32Array(L.dust.trailPlan), deep: new Float32Array(L.dust.trailDeep) } };
})();
// planets: a second inner carved ring so they read as planets at a glance
const planetInnerPts = makePoints({
  plan: L.planets.flatMap((p) => p.plan), deep: L.planets.flatMap((p) => p.deep),
  size: L.planets.map(() => 2.0),
  opacity: L.planets.map((p) => (p.status === 'active' ? 0.9 : 0.35)),
  core: L.planets.map(() => 0), ring: L.planets.map(() => 1),
  color: L.planets.flatMap(() => [0.961, 0.918, 0.824]),
});

// planet -> goal hairlines (survey-order language: dissolve with ch1)
{
  const pts = [];
  for (const p of L.planets) {
    if (p.goalIndex < 0) continue;
    const g = L.goals[p.goalIndex];
    pts.push(new THREE.Vector3(p.plan[0], p.plan[1], 0));
    pts.push(new THREE.Vector3(g.plan[0], g.plan[1], 0));
  }
  chart.add(new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(pts), lineMat(INK, 0.22, 0, 1)));
}
// progress arcs around planets (only when honestly derivable; arc length = progress)
{
  const pts = [];
  for (const p of L.planets) {
    if (p.progress === null || p.progress === undefined || p.progress <= 0) continue;
    const segs = 32, r = 4.6;
    for (let i = 0; i < segs; i++) {
      const a0 = Math.PI / 2 - (i / segs) * p.progress * Math.PI * 2;
      const a1 = Math.PI / 2 - ((i + 1) / segs) * p.progress * Math.PI * 2;
      pts.push(new THREE.Vector3(p.plan[0] + r * Math.cos(a0), p.plan[1] + r * Math.sin(a0), 0));
      pts.push(new THREE.Vector3(p.plan[0] + r * Math.cos(a1), p.plan[1] + r * Math.sin(a1), 0));
    }
  }
  if (pts.length) {
    chart.add(new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(pts), lineMat(GOLD, 0.55, 0, 2)));
  }
}
// guest-star tails (客星拖尾): trailing polyline per guest, morphed via plan/deep verts
const guestTails = (() => {
  const plan = [], deep = [];
  for (const g of L.guests) {
    const dir = (g.tailDir * Math.PI) / 180;
    const dx = Math.cos(dir), dy = Math.sin(dir);
    const px = -dy, py = dx; // perpendicular wobble
    const n = 5;
    for (let i = 0; i < n; i++) {
      for (const t of [i / n, (i + 1) / n]) {
        const wob = Math.sin(t * 2.5) * 1.1;
        plan.push(g.plan[0] - dx * g.tailLen * t + px * wob, g.plan[1] - dy * g.tailLen * t + py * wob, 0);
        deep.push(
          g.deep[0] - dx * g.tailLen * 1.3 * t + px * wob,
          g.deep[1] - dy * g.tailLen * 1.3 * t + py * wob,
          g.deep[2]
        );
      }
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(plan), 3));
  const mat = lineMat(INK, 0.55, 0.4, 3);
  const line = new THREE.LineSegments(geo, mat);
  chart.add(line);
  return { geometry: geo, userData: { plan: new Float32Array(plan), deep: new Float32Array(deep) } };
})();

// ---------- glow sprites (deepspace) ----------
function glowTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 128;
  const x = c.getContext('2d');
  const g = x.createRadialGradient(64, 64, 0, 64, 64, 64);
  g.addColorStop(0, 'rgba(255,255,255,1)');
  g.addColorStop(0.25, 'rgba(255,255,255,0.35)');
  g.addColorStop(1, 'rgba(255,255,255,0)');
  x.fillStyle = g;
  x.fillRect(0, 0, 128, 128);
  return new THREE.CanvasTexture(c);
}
const glowTex = glowTexture();
const glows = [];
function addGlow(getPos, scale, color, maxOpacity) {
  const mat = new THREE.SpriteMaterial({
    map: glowTex, color, transparent: true, opacity: 0,
    blending: THREE.AdditiveBlending, depthWrite: false,
  });
  const spr = new THREE.Sprite(mat);
  spr.scale.set(scale, scale, 1);
  chart.add(spr);
  glows.push({ spr, mat, getPos, maxOpacity });
  return spr;
}
addGlow(() => [0, 0, 0], 20, 0xffd98a, 0.8); // north star warm core glow
addGlow(() => [0, 0, 0], 40, 0x96a8dc, 0.10); // north star cool halo
const goalGlowSprites = L.goals.map((g, i) =>
  addGlow(() => {
    const p = goalPts.geometry.attributes.position.array;
    return [p[i * 3], p[i * 3 + 1], p[i * 3 + 2]];
  }, 9, 0xffcd78, 0.35)
);
// guest-star breathing halos: the breath moves ONLY the halo, never the star
// point itself (动=未竟之事). Managed by the animation loop, not by applyMorph.
const guestGlows = L.guests.map((g, i) => {
  const mat = new THREE.SpriteMaterial({
    map: glowTex, color: 0xffe8c0, transparent: true, opacity: 0,
    blending: THREE.AdditiveBlending, depthWrite: false,
  });
  const spr = new THREE.Sprite(mat);
  spr.scale.set(5.5, 5.5, 1);
  chart.add(spr);
  return { spr, mat, idx: i, breathe: g.review === 'needs_review' };
});
// nebula sprites
const nebulae = [];
  for (const [x, y, z, sc, color, op] of [
  [150, 70, -120, 260, 0x7a5638, 0.13],
  [-170, -60, -100, 300, 0x5d6070, 0.10],
  [0, 120, -140, 200, 0x46527a, 0.085],
]) {
  const mat = new THREE.SpriteMaterial({ map: glowTex, color, transparent: true, opacity: 0, depthWrite: false });
  const spr = new THREE.Sprite(mat);
  spr.position.set(x, y, z);
  spr.scale.set(sc, sc, 1);
  spr.visible = false;
  scene.add(spr); // not in chart group: nebulae stay put when the chart tilts
  nebulae.push({ mat, op, spr });
}

// ---------- title asset (v2 三字匾 default, ?title=v1 keeps the 5-char plaque) ----------
const cartEl = document.getElementById('cartouche');
const cartV1 = document.getElementById('cartouche-v1');
if (params.get('title') === 'v1') {
  cartEl.style.display = 'none';
} else {
  cartEl.src = titleV2Url;
  cartV1.style.display = 'none';
}

// ---------- labels (troika SDF; 一点明体=类别/目标, 文楷=铭文, IM Fell=西文) ----------
const labelObjs = [];
function addLabel(text, { size = 3.4, color = INK, font = fontUrl, pos = [0, 0, 0], deepPos = null, rotZ = 0, anchorX = 'center', fade = 'band' }) {
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
  chart.add(t);
  labelObjs.push({ t, fade, planPos: pos.slice(), deepPos: deepPos ? deepPos.slice() : null });
  return t;
}

let segPending = 0;
const goalLabelGroups = []; // {goalIdx, segs:[Text], base:[[x,y]...], anchor:[x,y]}
// mixed CJK/latin strings: latin segments get IM Fell, CJK segments I.Ming,
// measured after SDF sync and laid out sequentially
function addSegmentedLabel(text, { size = 3.6, color = 0xeed696, pos, align = 'left', fade = 'goal', goalIdx = -1 }) {
  const segs = text.split(/([A-Za-z0-9.]+)/).filter(Boolean);
  const group = { goalIdx, segs: [], base: [], anchor: pos.slice() };
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
    chart.add(t);
    labelObjs.push({ t, fade, planPos: pos.slice(), deepPos: null });
    group.segs.push(t);
    return t;
  });
  if (goalIdx >= 0) goalLabelGroups.push(group);
  segPending += objs.length;
  let left = objs.length;
  objs.forEach((o) => o.sync(() => {
    segPending -= 1;
    left -= 1;
    if (left === 0) {
      const widths = objs.map((o) => {
        const b = o.textRenderInfo && o.textRenderInfo.blockBounds;
        return b ? Math.max(0.1, b[2] - b[0]) : o.text.length * size * 0.6;
      });
      const total = widths.reduce((a, b) => a + b, 0) + 0.4 * (objs.length - 1);
      let x = pos[0] - (align === 'right' ? total : align === 'center' ? total / 2 : 0);
      objs.forEach((o, i) => { o.position.set(x, pos[1], 0); x += widths[i] + 0.4; });
      group.base = objs.map((o) => [o.position.x, o.position.y]);
    }
  }));
}
// outer category-name band: chars rotated along the arc (一点明体, 刻感)
for (const sec of L.sectors) {
  const mid = sec.start + sec.width / 2;
  const chars = Array.from(sec.name);
  const angStep = ((3.4 * 1.25) / BAND_TEXT) * (180 / Math.PI);
  const a0 = mid - (angStep * (chars.length - 1)) / 2;
  chars.forEach((ch, i) => {
    const a = a0 + i * angStep;
    const rad = (a * Math.PI) / 180;
    addLabel(ch, {
      size: 3.2, color: INK, font: imingUrl, fade: 'band',
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
  addSegmentedLabel(g.title, {
    size: 3.6, color: 0xeed696, align, goalIdx: gi,
    pos: [rr * Math.cos(a) + (align === 'left' ? 1 : align === 'right' ? -1 : 0), rr * Math.sin(a), 0],
  });
});
// north star label (two lines)
const nsLines = (() => {
  const clause = snapshot.north_star.split(/[，。]/)[0]; // first clause only
  const idx = clause.indexOf('成为');
  return idx > 0 ? [clause.slice(0, idx + 2), clause.slice(idx + 2)] : [clause, ''];
})();
// north star labels: in deepspace they drift to the lower-right of the
// nucleus, clear of the glow radius, and dim slightly (文楷, 书写感)
addLabel(nsLines[0], { size: 3.8, color: INK, font: wenkaiUrl, anchorX: 'left', pos: [6.5, 3.4, 0], deepPos: [10.5, -8.5, 0], fade: 'north' });
addLabel(nsLines[1], { size: 3.8, color: 0xeed696, font: wenkaiUrl, anchorX: 'left', pos: [6.5, -2.6, 0], deepPos: [10.5, -13.6, 0], fade: 'north' });

let labelsPending = labelObjs.length;
for (const { t } of labelObjs) t.sync(() => { labelsPending -= 1; });

// ---------- postprocessing ----------
// Bloom at full res is catastrophic on software GL (SwiftShader/llvmpipe);
// detect it and leave the glow-sprite look to carry the deepspace there.
const glCtx = renderer.getContext();
const dbgInfo = glCtx.getExtension('WEBGL_debug_renderer_info');
const glRendererName = dbgInfo ? String(glCtx.getParameter(dbgInfo.UNMASKED_RENDERER_WEBGL)) : '';
const SOFT_GL = /swiftshader|llvmpipe|software/i.test(glRendererName);
const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
const bloom = new BloomEffect({ luminanceThreshold: 0.65, intensity: 0, mipmapBlur: true });
const fxPass = new EffectPass(camera, bloom);
composer.addPass(fxPass);
window.__composer = composer; // debug aid (playground page only)
composer.setSize(heart.clientWidth || 1600, heart.clientHeight || 900); // buffers were born at 300x150 otherwise

// ---------- morph ----------
const state = {
  t: START_STATE === 'deepspace' ? 1 : 0,
  density: 1,
  bloom: 1,
  w1: 0,   // channel-1 window start: survey lines dissolve
  w2: 0.3, // channel-2 window start: camera / labels / background
  w3: 0.6, // channel-3 window start: pins / glows / nebulae
  duskPos: 0.45, // blue-hour keyframe position within ch2
  duskAmt: 1,    // pole-star warm flare strength at dusk
  ch1: 0, ch2: 0, ch3: 0, // latest channel values, read by the animation loop
};
// ?t=0.5 pins the morph progress for mid-state screenshots
const FIXED_T = parseFloat(params.get('t'));
if (!Number.isNaN(FIXED_T)) state.t = Math.min(1, Math.max(0, FIXED_T));
const morphables = [dimPts, litPts, goalPts, courtPts, northPts, planetPts, planetInnerPts, moonPts, seatedPts, guestPts, dustPts, guestTails, dustTrails];
// orbit-managed clouds have exactly one writer: the animation loop
// (morph lerp + integrated orbit phase, computed there every frame)
for (const pts of [goalPts, planetPts, planetInnerPts, moonPts, guestPts, guestTails]) {
  pts.userData.orbitManaged = true;
}

// staggered morph timeline: survey lines dissolve first, then the world tilts,
// then the deep sky ignites. state.t drives three channel windows.
//   ch1 [w1 .. w1+0.4]: spokes / ticks / sector survey lines dissolve
//   ch2 [w2 .. w2+0.4]: camera sinks & tilts, band labels fade, stone opens to sky
//   ch3 [w3 .. w3+0.4]: dim stars shrink to pins, glows & nebulae ignite
const chan = (t, start) => Math.min(1, Math.max(0, (t - start) / 0.4));

function applyMorph() {
  const t = state.t;
  const ch1 = chan(t, state.w1);
  const ch2 = chan(t, state.w2);
  const ch3 = chan(t, state.w3);
  state.ch1 = ch1; state.ch2 = ch2; state.ch3 = ch3;
  // node positions (fly out with the camera phase; orbit-managed clouds are
  // written by the animation loop instead — single writer per attribute)
  for (const pts of morphables) {
    if (pts.userData.orbitManaged) continue;
    const attr = pts.geometry.attributes.position;
    const { plan, deep } = pts.userData;
    for (let i = 0; i < attr.array.length; i++) {
      attr.array[i] = plan[i] + (deep[i] - plan[i]) * ch2;
    }
    attr.needsUpdate = true;
  }
  // chart tilt + camera
  chart.rotation.x = -1.05 * ch2;
  camera.position.lerpVectors(CAM_PLAN.pos, CAM_DEEP.pos, ch2);
  camera.lookAt(new THREE.Vector3().lerpVectors(CAM_PLAN.look, CAM_DEEP.look, ch2));
  // materials on their channels
  for (const { mat, plan, deep, ch } of fadeMats) {
    const c = ch === 1 ? ch1 : ch === 3 ? ch3 : ch2;
    mat.opacity = plan + (deep - plan) * c;
  }
  for (const { t: txt, fade, planPos, deepPos } of labelObjs) {
    if (fade === 'band') {
      txt.material.opacity = 1 - ch2;
      txt.visible = ch2 < 0.98; // troika re-syncs can restore shared-material opacity
    } else if (fade === 'north' && deepPos) {
      txt.material.opacity = 1 - 0.25 * ch2;
      txt.position.set(
        planPos[0] + (deepPos[0] - planPos[0]) * ch2,
        planPos[1] + (deepPos[1] - planPos[1]) * ch2,
        0
      );
    }
  }
  // glows + nebulae (ignite last); invisible sprites are skipped entirely —
  // on software GL their giant quads cost real fill-rate even at opacity 0
  for (const g of glows) {
    g.mat.opacity = g.maxOpacity * ch3;
    g.spr.visible = g.mat.opacity > 0.004;
    const p = g.getPos();
    g.spr.position.set(p[0], p[1], p[2]);
  }
  for (const n of nebulae) {
    n.mat.opacity = n.op * ch3;
    n.spr.visible = n.mat.opacity > 0.004;
  }
  // blue hour: the pole star flares warm for a moment as the world tilts
  const duskBoost = Math.exp(-Math.pow((ch2 - state.duskPos) / 0.13, 2)) * state.duskAmt;
  const ng = glows[0]; // north-star warm glow
  if (duskBoost > 0.01) {
    ng.mat.opacity = Math.min(1, Math.max(ng.mat.opacity, ng.maxOpacity * duskBoost * 0.6));
    ng.spr.visible = true;
    const sc = 20 * (1 + 0.55 * duskBoost);
    ng.spr.scale.set(sc, sc, 1);
  } else {
    ng.spr.scale.set(20, 20, 1);
  }
  // dim field restraint (月.png) + ring taper, both late-phase
  const dimAttr = dimPts.geometry.attributes.aOpacity;
  const dimSizeAttr = dimPts.geometry.attributes.aSize;
  const dimRingAttr = dimPts.geometry.attributes.aRing;
  const base = dimPts.userData.baseOpacity;
  const baseSz = dimPts.userData.baseSize;
  const baseRing = dimPts.userData.baseRing;
  const dOpS = dimPts.userData.deepOpScale;
  const dSzS = dimPts.userData.deepSizeScale;
  const filler = dimPts.userData.filler;
  for (let i = 0; i < dimAttr.array.length; i++) {
    const densityGate = filler[i] ? state.density : 1;
    dimAttr.array[i] = base[i] * densityGate * (1 + (dOpS[i] - 1) * ch3);
    dimSizeAttr.array[i] = baseSz[i] * (1 + (dSzS[i] - 1) * ch3);
    dimRingAttr.array[i] = baseRing[i] * (1 - 0.55 * ch3);
  }
  dimAttr.needsUpdate = true;
  dimSizeAttr.needsUpdate = true;
  dimRingAttr.needsUpdate = true;
  // background cross-fade (DOM, three keyframes) + DOM vignette + post
  applyBackground(ch2, state.duskPos);
  fxPass.enabled = FORCE_FX || (!NO_FX && !SOFT_GL && ch3 > 0.02); // bloom costs full-res mips; skip while dormant
  bloom.intensity = 0.7 * ch3 * state.bloom;
  document.getElementById('vignette').style.opacity = String(0.55 + 0.45 * ch2);
  // DOM overlay
  const domOpacity = String(1 - ch2);
  cartEl.style.opacity = domOpacity;
  cartV1.style.opacity = domOpacity;
  document.getElementById('briefing').style.opacity = domOpacity;
  document.getElementById('toggle').textContent = t > 0.5 ? '→ 图态' : '→ 境态';
}

let tween = null;
function goTo(target, instant = false) {
  if (tween) tween.kill();
  closeDetail(); // morphing with an open inscription card breaks the immersion
  if (instant || REDUCED_MOTION) {
    state.t = target;
    applyMorph();
    return;
  }
  tween = gsap.to(state, { t: target, duration: 2.4, ease: 'power2.inOut', onUpdate: applyMorph });
}

// wheel / zoom threshold auto-switch
let wheelAcc = 0;
window.addEventListener('wheel', (e) => {
  wheelAcc += e.deltaY;
  if (Math.abs(wheelAcc) > 260) {
    goTo(wheelAcc < 0 ? 1 : 0);
    wheelAcc = 0;
  }
}, { passive: true });
document.getElementById('toggle').addEventListener('click', () => goTo(state.t > 0.5 ? 0 : 1));

// ---------- debug panel ----------
const uiMorph = document.getElementById('ui-morph');
const uiDensity = document.getElementById('ui-density');
const uiBloom = document.getElementById('ui-bloom');
if (!SHOW_PANEL) {
  document.getElementById('panel').style.display = 'none';
  document.getElementById('toggle').style.display = 'none';
}
uiMorph.addEventListener('input', () => {
  if (tween) tween.kill();
  state.t = uiMorph.value / 100;
  applyMorph();
});
uiDensity.addEventListener('input', () => { state.density = uiDensity.value / 100; applyMorph(); });
uiBloom.addEventListener('input', () => { state.bloom = uiBloom.value / 100; applyMorph(); });
for (const [id, key] of [['ui-w1', 'w1'], ['ui-w2', 'w2'], ['ui-w3', 'w3'], ['ui-duskpos', 'duskPos'], ['ui-duskamt', 'duskAmt']]) {
  document.getElementById(id).addEventListener('input', (e) => {
    state[key] = e.target.value / 100;
    applyMorph();
  });
}
setInterval(() => { if (document.activeElement !== uiMorph) uiMorph.value = String(Math.round(state.t * 100)); }, 300);
if (window.innerWidth < 700 && params.get('panel') !== '1') {
  document.getElementById('panel').style.display = 'none'; // narrow screens: chrome stays off the painting
}

// ---------- hover tooltip (minimal, 文楷) ----------
const tip = document.getElementById('tooltip');
const PIN_HOVER = params.get('hover');
const attrPos = (pts, i) => {
  const a = pts.geometry.attributes.position.array;
  return [a[i * 3], a[i * 3 + 1], a[i * 3 + 2]];
};
const hoverables = [
  { title: '北极星', info: snapshot.north_star.split(/[，。]/)[0], pos: () => [0, 0, 0] },
  ...L.goals.map((g, i) => ({ title: g.title, info: '目标恒星', pos: () => attrPos(goalPts, i) })),
  ...L.planets.map((p, i) => ({
    title: p.title,
    info: `${p.status === 'active' ? '行星 · 在轨' : '行星 · 归档'} · 任务 ${p.taskCount}` +
      (p.progress !== null && p.progress !== undefined ? ` · 进度 ${Math.round(p.progress * 100)}%` : ''),
    pos: () => attrPos(planetPts, i),
  })),
  ...L.guests.map((g, i) => ({
    title: g.title,
    info: `客星 · ${g.date} · ${g.strength}${g.review === 'needs_review' ? ' · 待评审' : ''}`,
    pos: () => attrPos(guestPts, i),
  })),
];
function screenOf(local) {
  const v = new THREE.Vector3(local[0], local[1], local[2] ?? 0);
  chart.localToWorld(v);
  v.project(camera);
  const r = heart.getBoundingClientRect();
  return [r.left + (v.x * 0.5 + 0.5) * r.width, r.top + (-v.y * 0.5 + 0.5) * r.height];
}
let hoverIdx = PIN_HOVER !== null ? Math.min(hoverables.length - 1, Math.max(0, parseInt(PIN_HOVER, 10) || 0)) : -1;
window.addEventListener('pointermove', (e) => {
  if (PIN_HOVER !== null) return;
  hoverIdx = -1;
  let bestD = 26;
  hoverables.forEach((h, i) => {
    const [x, y] = screenOf(h.pos());
    const d = Math.hypot(x - e.clientX, y - e.clientY);
    if (d < bestD) { bestD = d; hoverIdx = i; }
  });
});
function updateTooltip() {
  if (hoverIdx < 0 || !hoverables[hoverIdx]) { tip.style.display = 'none'; return; }
  const h = hoverables[hoverIdx];
  const [x, y] = screenOf(h.pos());
  tip.innerHTML = `<div class="tt-title"></div><div class="tt-info"></div>`;
  tip.querySelector('.tt-title').textContent = h.title;
  tip.querySelector('.tt-info').textContent = h.info;
  tip.style.display = 'block';
  const tw = tip.offsetWidth;
  tip.style.left = Math.min(window.innerWidth - tw - 12, x + 16) + 'px';
  tip.style.top = Math.max(10, y - 44) + 'px';
}

// real counts in the briefing line
document.getElementById('briefing').textContent =
  `「${snapshot.counts.evidence_needs_review} 条客星待评审，${snapshot.counts.projects_active} 颗行星在轨。」`;

// ---------- click detail card (铭文卡, slides in from the right) ----------
const detail = document.getElementById('detail');
const detailTitle = detail.querySelector('h3');
const detailList = detail.querySelector('dl');
const clickables = [
  { kind: 'goal', idx: -1, title: '北极星', pos: () => [0, 0, 0] },
  ...L.goals.map((g, i) => ({ kind: 'goal', idx: i, title: g.title, pos: () => attrPos(goalPts, i) })),
  ...L.planets.map((p, i) => ({ kind: 'planet', idx: i, title: p.title, pos: () => attrPos(planetPts, i) })),
  ...L.guests.map((g, i) => ({ kind: 'guest', idx: i, title: g.title, pos: () => attrPos(guestPts, i) })),
  ...L.lit.skills.map((s, i) => ({ kind: 'skill', idx: i, title: s.label, pos: () => attrPos(litPts, i) })),
];
const selRing = new THREE.LineLoop(
  new THREE.BufferGeometry().setFromPoints(circlePoints(3.2, 48)),
  new THREE.LineBasicMaterial({ color: GOLD_BRIGHT, transparent: true, opacity: 0.8, depthWrite: false })
);
selRing.visible = false;
chart.add(selRing);
let selectedIdx = -1;

function detailRows(c) {
  if (c.kind === 'goal' && c.idx === -1) return [['类型', '北极星'], ['铭文', snapshot.north_star]];
  if (c.kind === 'goal') {
    const g = snapshot.goals[c.idx];
    return [['状态', g.status], ['起始', g.start || '—'], ['目标', g.target || '—'], ['铭文', g.summary || '—']];
  }
  if (c.kind === 'planet') {
    const p = snapshot.projects[c.idx];
    const gi = L.planets[c.idx].goalIndex;
    return [
      ['状态', p.status === 'active' ? '在轨' : '归档'],
      ['所属目标', gi >= 0 ? snapshot.goals[gi].title : '（自由轨道）'],
      ['任务', `${p.task_count} 项`],
      ['进度', p.progress === null || p.progress === undefined ? '—' : `${Math.round(p.progress * 100)}%`],
      ['时间范围', p.time_range || '—'],
    ];
  }
  if (c.kind === 'guest') {
    const e = snapshot.evidence.find((x) => x.id === L.guests[c.idx].id) || L.guests[c.idx];
    return [
      ['类型', e.type || '—'], ['强度', e.strength || '—'], ['日期', e.date || '—'],
      ['评审', e.review_status === 'needs_review' || e.review === 'needs_review' ? '待评审' : '已入座'],
      ['摘要', e.summary || '—'],
    ];
  }
  const s = L.lit.skills[c.idx];
  return [['类别', s.category], ['状态', s.status], ['关联证据', `${s.evidenceCount} 条`]];
}

function openDetail(i) {
  selectedIdx = i;
  const c = clickables[i];
  detailTitle.textContent = c.title;
  detailList.innerHTML = '';
  for (const [k, v] of detailRows(c)) {
    const dt = document.createElement('dt');
    dt.textContent = k;
    const dd = document.createElement('dd');
    dd.textContent = v;
    detailList.append(dt, dd);
  }
  detail.classList.add('open');
}
function closeDetail() {
  selectedIdx = -1;
  detail.classList.remove('open');
  selRing.visible = false;
}
window.addEventListener('click', (e) => {
  if (PIN_HOVER !== null) return;
  if (dragDist > 6) { dragDist = 0; return; } // a dial-drag is not a click
  if (e.target.closest('#detail') || e.target.closest('#panel') || e.target.closest('#toggle')) return;
  let best = -1, bestD = 26;
  clickables.forEach((c, i) => {
    const [x, y] = screenOf(c.pos());
    const d = Math.hypot(x - e.clientX, y - e.clientY);
    if (d < bestD) { bestD = d; best = i; }
  });
  if (best >= 0) openDetail(best);
  else closeDetail();
});
window.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeDetail(); });
// bottom sheet: swipe down to close (mobile)
let detailTouchY = null;
detail.addEventListener('touchstart', (e) => { detailTouchY = e.touches[0].clientY; }, { passive: true });
detail.addEventListener('touchmove', (e) => {
  if (detailTouchY !== null && e.touches[0].clientY - detailTouchY > 70) {
    closeDetail();
    detailTouchY = null;
  }
}, { passive: true });
detail.addEventListener('touchend', () => { detailTouchY = null; }, { passive: true });
const PIN_SELECT = params.get('select');
if (PIN_SELECT !== null) {
  openDetail(Math.min(clickables.length - 1, Math.max(0, parseInt(PIN_SELECT, 10) || 0)));
}

// ---------- resize / touch controls / animation loop ----------
function updatePointScale() {
  const h = renderer.domElement.height; // device px
  const scale = h / (2 * Math.tan((camera.fov * Math.PI) / 360));
  for (const pts of morphables) {
    if (pts.isPoints) pts.material.uniforms.uScale.value = scale;
  }
}
function onResize() {
  const w = heart.clientWidth || 1, h = heart.clientHeight || 1;
  renderer.setSize(w, h);
  composer.setSize(w, h); // keeps bloom buffers at canvas resolution
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  fitPlanCamera();
  if (controls) {
    controls.minDistance = CAM_PLAN.pos.z * 0.65;
    controls.maxDistance = CAM_PLAN.pos.z * 1.6;
  }
  updatePointScale();
  applyMorph();
}
window.addEventListener('resize', onResize);

// touch: pan + pinch on the planisphere, clamped near the chart
const controls = COARSE_POINTER
  ? new OrbitControls(camera, canvas)
  : null;
if (controls) {
  controls.enableRotate = false;
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.enableZoom = true;
  controls.zoomSpeed = 0.9;
  controls.enablePan = true;
  controls.panSpeed = 0.8;
}

// motion semantics: 动=未竟之事, 静=已定之史
const goalPeriods = L.goals.map((_, i) => 60 + i * 15);     // 60–120s
const planetPeriods = L.planets.map((_, i) => 40 + i * 5);   // 40–80s
const guestPeriods = L.guests.map((_, i) => 8 + i * 2.3);    // 8–15s
const guestDeepBase = L.guests.map((g) => g.deep.slice());
const planetDeepBase = L.planets.map((p) => p.deep.slice());
const goalDeepBase = L.goals.map((g) => g.deep.slice());
// moon -> planet index map (layout pushes moons grouped per planet)
const moonPlanet = [];
L.planets.forEach((p, pi) => {
  for (let i = 0; i < Math.min(p.taskCount, 5); i++) moonPlanet.push(pi);
});
const moonDeepBase = [];
for (let i = 0; i < L.moons.deep.length; i += 3) moonDeepBase.push(L.moons.deep.slice(i, i + 3));
// guest tail vertex offsets relative to the guest's deep-space position
const tailOffsets = [];
L.guests.forEach((g, i) => {
  const arr = [];
  for (let v = 0; v < 10; v++) {
    const k = (i * 10 + v) * 3;
    arr.push([
      guestTails.userData.deep[k] - g.deep[0],
      guestTails.userData.deep[k + 1] - g.deep[1],
      guestTails.userData.deep[k + 2] - g.deep[2],
    ]);
  }
  tailOffsets.push(arr);
});
const rotZ = (x, y, a) => [x * Math.cos(a) - y * Math.sin(a), x * Math.sin(a) + y * Math.cos(a)];

// ---------- desktop drag-to-spin (拨盘) + approach-to-stop (伸手即停) ----------
let dragging = false, dragLastX = 0, dragLastT = 0, dragDist = 0, spinVel = 0;
let spinFactor = 1;                     // eased 0..1, drives the armillary spin
let lastPointerActive = -1e9;
window.addEventListener('pointermove', () => { lastPointerActive = performance.now(); }, { passive: true });
canvas.addEventListener('pointerdown', (e) => {
  if (COARSE_POINTER || state.t >= 0.5) return; // touch pan/pinch belongs to OrbitControls
  dragging = true;
  dragLastX = e.clientX;
  dragLastT = performance.now();
  dragDist = 0;
  spinVel = 0;
  canvas.setPointerCapture(e.pointerId);
});
canvas.addEventListener('pointermove', (e) => {
  if (!dragging) return;
  const now = performance.now();
  const dx = e.clientX - dragLastX;
  const dtm = Math.max((now - dragLastT) / 1000, 0.008);
  dragLastX = e.clientX;
  dragLastT = now;
  dragDist += Math.abs(dx);
  const d = dx * 0.004;
  chart.rotation.z += d;
  spinVel = spinVel * 0.75 + (d / dtm) * 0.25; // smoothed drag velocity for inertia
});
const endDrag = () => { dragging = false; };
canvas.addEventListener('pointerup', endDrag);
canvas.addEventListener('pointercancel', endDrag);
window.__motion = { // debug aid (playground page only)
  get spinFactor() { return spinFactor; },
  get rotationZ() { return chart.rotation.z; },
};

onResize();
applyMorph();
if (START_STATE === 'deepspace') goTo(1, true);

let frames = 0;
const clock = new THREE.Clock();
const guestBaseOpacity = new Float32Array(guestPts.geometry.attributes.aOpacity.array);
const guestPulse = L.guests.map((g) => (g.review === 'needs_review' ? 1 : 0));
// orbit phases accumulate (integrated): ch3 scales angular SPEED, never position
const goalPhase = L.goals.map(() => 0);
const planetPhase = L.planets.map(() => 0);
const guestPhase = L.guests.map(() => 0);
const BASE_SPIN = (Math.PI * 2) / 3600; // one revolution per hour — furnishing, not motion

// breathing: 11s period, inhale-fast / plateau / long-exhale, amplitude 0.85→1.0
function breathWave(p) {
  if (p < 0.25) return 0.5 - 0.5 * Math.cos((p / 0.25) * Math.PI);
  if (p < 0.45) return 1;
  return 0.5 + 0.5 * Math.cos(((p - 0.45) / 0.55) * Math.PI);
}

function loop() {
  requestAnimationFrame(loop);
  const dt = Math.min(clock.getDelta(), 0.1);
  const tt = clock.elapsedTime;
  const { ch2, ch3 } = state;

  // ---- 伸手即停: pointer activity / hover / open card / drag pause the spin ----
  const now = performance.now();
  const busy = dragging || hoverIdx >= 0 || selectedIdx >= 0 || now - lastPointerActive < 3000;
  const spinTarget = busy || REDUCED_MOTION ? 0 : 1;
  spinFactor += (spinTarget - spinFactor) * Math.min(1, dt / 0.8);

  // armillary spin: 1h/rev, quickens briefly while the world tilts (ch2 window)
  chart.rotation.z += dt * BASE_SPIN * spinFactor * (1 + 2.5 * Math.sin(ch2 * Math.PI));
  // drag inertia: release glides to a stop
  if (!dragging && Math.abs(spinVel) > 1e-4) {
    chart.rotation.z += spinVel * dt;
    spinVel *= Math.exp(-dt / 1.2);
  }

  // ---- orbit-managed clouds: single writer (morph lerp + integrated phase) ----
  {
    const gAttr = goalPts.geometry.attributes.position;
    const goalNow = L.goals.map((g, i) => {
      const deep = goalDeepBase[i];
      goalPhase[i] += dt * (2 * Math.PI / goalPeriods[i]) * ch3;
      const [rx, ry] = rotZ(deep[0], deep[1], goalPhase[i]);
      return [
        g.plan[0] + (deep[0] - g.plan[0]) * ch2 + (rx - deep[0]),
        g.plan[1] + (deep[1] - g.plan[1]) * ch2 + (ry - deep[1]),
        g.plan[2] + (deep[2] - g.plan[2]) * ch2,
      ];
    });
    goalNow.forEach((p, i) => gAttr.setXYZ(i, p[0], p[1], p[2]));
    gAttr.needsUpdate = true;
    for (const grp of goalLabelGroups) {
      if (!grp.base.length) continue;
      const gp = goalNow[grp.goalIdx];
      const morphBase = L.goals[grp.goalIdx].plan;
      const deep = goalDeepBase[grp.goalIdx];
      const bx = morphBase[0] + (deep[0] - morphBase[0]) * ch2;
      const by = morphBase[1] + (deep[1] - morphBase[1]) * ch2;
      const dx = gp[0] - bx, dy = gp[1] - by;
      grp.segs.forEach((s, si) => s.position.set(grp.base[si][0] + dx, grp.base[si][1] + dy, 0));
    }

    const pAttr = planetPts.geometry.attributes.position;
    const pInAttr = planetInnerPts.geometry.attributes.position;
    const mAttr = moonPts.geometry.attributes.position;
    const planetNow = L.planets.map((p, i) => {
      const deep = planetDeepBase[i];
      planetPhase[i] += dt * (2 * Math.PI / planetPeriods[i]) * ch3;
      const gi = p.goalIndex;
      const anchorDeep = gi >= 0 ? goalDeepBase[gi] : [0, 0, 0];
      const anchorNow = gi >= 0 ? goalNow[gi] : [0, 0, 0];
      const [rx, ry] = rotZ(deep[0] - anchorDeep[0], deep[1] - anchorDeep[1], planetPhase[i]);
      const morphX = p.plan[0] + (deep[0] - p.plan[0]) * ch2;
      const morphY = p.plan[1] + (deep[1] - p.plan[1]) * ch2;
      return [
        morphX + (anchorNow[0] - anchorDeep[0]) + (rx - (deep[0] - anchorDeep[0])),
        morphY + (anchorNow[1] - anchorDeep[1]) + (ry - (deep[1] - anchorDeep[1])),
        p.plan[2] + (deep[2] - p.plan[2]) * ch2,
      ];
    });
    planetNow.forEach((p, i) => { pAttr.setXYZ(i, p[0], p[1], p[2]); pInAttr.setXYZ(i, p[0], p[1], p[2]); });
    pAttr.needsUpdate = true;
    pInAttr.needsUpdate = true;
    moonDeepBase.forEach((md, mi) => {
      const pi = moonPlanet[mi];
      if (pi === undefined) return;
      mAttr.setXYZ(mi,
        md[0] + (planetNow[pi][0] - planetDeepBase[pi][0]),
        md[1] + (planetNow[pi][1] - planetDeepBase[pi][1]),
        md[2]);
    });
    mAttr.needsUpdate = true;

    const guAttr = guestPts.geometry.attributes.position;
    const tAttr = guestTails.geometry.attributes.position;
    L.guests.forEach((g, i) => {
      const deep = guestDeepBase[i];
      guestPhase[i] += dt * (2 * Math.PI / guestPeriods[i]) * ch3;
      const drift = 7 * ch3;
      const gx = g.plan[0] + (deep[0] - g.plan[0]) * ch2 + drift * Math.cos(guestPhase[i] + i * 1.3);
      const gy = g.plan[1] + (deep[1] - g.plan[1]) * ch2 + drift * Math.sin(guestPhase[i] + i * 1.3);
      const gz = g.plan[2] + (deep[2] - g.plan[2]) * ch2;
      guAttr.setXYZ(i, gx, gy, gz);
      const glow = guestGlows[i];
      glow.spr.position.set(gx, gy, gz);
      tailOffsets[i].forEach((off, v) => tAttr.setXYZ(i * 10 + v, gx + off[0] * ch2, gy + off[1] * ch2, gz + off[2] * ch2));
    });
    guAttr.needsUpdate = true;
    tAttr.needsUpdate = true;
  }

  // ---- breathing: halos only, star points never move ----
  if (!REDUCED_MOTION) {
    for (const glow of guestGlows) {
      const base = 0.34 + 0.3 * ch3;
      const wave = glow.breathe ? breathWave((tt / 11 + glow.idx * 0.31) % 1) : 0.4;
      glow.mat.opacity = base * (0.85 + 0.15 * wave);
      glow.spr.visible = glow.mat.opacity > 0.004;
      const sc = 5.5 * (1 + 0.4 * ch3);
      glow.spr.scale.set(sc, sc, 1);
    }
  } else {
    for (const glow of guestGlows) {
      glow.mat.opacity = (0.34 + 0.3 * ch3) * 0.925;
      glow.spr.visible = glow.mat.opacity > 0.004;
    }
  }
  // star point opacity stays put (no pulse on the carved dot itself)
  {
    const attr = guestPts.geometry.attributes.aOpacity;
    let dirty = false;
    for (let i = 0; i < attr.array.length; i++) {
      if (attr.array[i] !== guestBaseOpacity[i]) { attr.array[i] = guestBaseOpacity[i]; dirty = true; }
    }
    if (dirty) attr.needsUpdate = true;
  }

  updateTooltip();
  if (selectedIdx >= 0) {
    const p = clickables[selectedIdx].pos();
    selRing.visible = true;
    selRing.position.set(p[0], p[1], p[2] ?? 0);
    const pulse = REDUCED_MOTION ? 1 : 1 + 0.04 * Math.sin(tt * 3);
    selRing.scale.set(pulse, pulse, 1);
  }
  if (controls) {
    controls.enabled = state.t < 0.5;
    controls.update();
    // clamp pan near the chart so the painting can't be dragged off-screen
    const tg = controls.target;
    const cx = Math.max(-70, Math.min(70, tg.x));
    const cy = Math.max(-70, Math.min(70, tg.y));
    if (cx !== tg.x || cy !== tg.y) {
      camera.position.x += cx - tg.x;
      camera.position.y += cy - tg.y;
      tg.x = cx; tg.y = cy; tg.z = 0;
    }
  }
  if (NO_FX || !fxPass.enabled) renderer.render(scene, camera);
  else composer.render();
  frames += 1;
  if (!window.__ready && frames > 10 && labelsPending <= 0 && segPending <= 0) window.__ready = true;
}
loop();
