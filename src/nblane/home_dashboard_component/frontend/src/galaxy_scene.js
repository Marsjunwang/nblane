// Native THREE.js "Growth Galaxy" scene for the Growth Graph.
//
// The 8 data roles are rendered as a luminous galaxy rather than a literal tree:
//   - trunk (North Star) → the bright core everything radiates from
//   - direction/branch/leaf/fruit → glowing orbs on a layered galactic plane,
//     parent→child drawn as gently-curved glowing filaments (containment reads
//     as arms spiralling out from the core)
//   - star (skills)  → a surrounding spherical halo of points, category-tinted,
//     brightness by mastery — the "群星闪耀" shell
//   - constellation (claims) → bright nodes with star-lines to their sources
//   - sand (sources) → faint ambient dust in the deep background
// Nodes glow (orb + additive halo sprite), edges glow, a slow auto-rotation and
// hover/click make it explorable. Deep indigo space + bloom let the lights sing.
//
// Framework-agnostic; the React component drives it via mount/setData/setSelected
// /fit/focus/dispose. Selection + framing mirror the old contract so the
// inspector / goal editor / Gap button keep working.

import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { EffectComposer } from "three/examples/jsm/postprocessing/EffectComposer.js";
import { RenderPass } from "three/examples/jsm/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/examples/jsm/postprocessing/UnrealBloomPass.js";
import { OutputPass } from "three/examples/jsm/postprocessing/OutputPass.js";

const DUST_COLOR = 0x9fb0e0;

function v3(p) {
  return new THREE.Vector3(p.x || 0, p.y || 0, p.z || 0);
}

// Soft radial glow sprite — the halo around every luminous node and the look of
// each skill point.
let _glowTex = null;
function glowTexture() {
  if (_glowTex) return _glowTex;
  const s = 128;
  const c = document.createElement("canvas");
  c.width = s;
  c.height = s;
  const ctx = c.getContext("2d");
  const g = ctx.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, s / 2);
  g.addColorStop(0, "rgba(255,255,255,1)");
  g.addColorStop(0.18, "rgba(255,255,255,0.85)");
  g.addColorStop(0.45, "rgba(255,255,255,0.32)");
  g.addColorStop(0.75, "rgba(255,255,255,0.08)");
  g.addColorStop(1, "rgba(255,255,255,0)");
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, s, s);
  _glowTex = new THREE.CanvasTexture(c);
  _glowTex.needsUpdate = true;
  return _glowTex;
}

// Deep-space vertical gradient backdrop.
function makeSpaceGradient() {
  const c = document.createElement("canvas");
  c.width = 2;
  c.height = 512;
  const ctx = c.getContext("2d");
  const g = ctx.createLinearGradient(0, 0, 0, 512);
  g.addColorStop(0, "#0c1638");
  g.addColorStop(0.55, "#0a1030");
  g.addColorStop(1, "#070a1c");
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 2, 512);
  const tex = new THREE.CanvasTexture(c);
  // Mark as sRGB so the tone-mapping + OutputPass pipeline round-trips it
  // correctly. Without this the dark gradient is read as LINEAR, then ACES + sRGB
  // re-encode brightens deep space into a washed-out blue that flattens the suns,
  // halos and the day/night terminator into the background.
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.needsUpdate = true;
  return tex;
}

export class GalaxyScene {
  constructor() {
    this.renderer = null;
    this.scene = null;
    this.camera = null;
    this.controls = null;
    this.composer = null;
    this.bloom = null;
    this.raf = 0;
    this.frame = 0;
    this.el = null;
    this.width = 900;
    this.height = 560;

    this.nodeGroup = new THREE.Group(); // pickable orb meshes
    this.haloGroup = new THREE.Group(); // additive glow sprites
    this.linkGroup = new THREE.Group(); // orbit rings
    this.trailGroup = new THREE.Group(); // comet trails for evidence moons
    this.selEdgeGroup = new THREE.Group(); // relationship filaments for the selection
    this.fxGroup = new THREE.Group(); // skill halo points, dust, core glow
    this.labelGroup = new THREE.Group(); // hover / selected labels
    this.focusLabelGroup = new THREE.Group(); // persistent project labels in focus

    this._edges = [];
    this._posById = new Map();
    this._orbMesh = new Map(); // nodeId -> orb mesh
    this._orbHalo = new Map(); // nodeId -> halo sprite
    this._comets = new Map(); // nodeId -> { line, positions:Float32Array, history:[Vector3] } for evidence moon trails
    this._goalArcs = new Map(); // nodeId -> { ring, ringBg, radius } progress arc around a goal sun
    this._orbGlow = new Map(); // nodeId -> glow entry (for focus dimming)
    this._nodeOrbits = {}; // nodeId -> { parentId, a, b, tilt, swivel, baseAngle, speed }
    this._orbitOrder = []; // node ids ordered parent-before-child for animation
    this._livePos = new Map(); // nodeId -> THREE.Vector3 current position
    this._orbitMotion = true; // toggle for live orbital rotation
    this._childrenByParent = new Map(); // parentId -> [childId] (from nodeOrbits)
    this._roleById = new Map(); // nodeId -> role
    this._focusRootId = null; // subsystem currently zoomed into (a goal id) or null
    this._coreOrb = null; // North Star orb mesh
    this._coreHalos = []; // North Star halo sprites
    this._focusLabels = []; // [{ sprite, nodeId }] project names shown while focused
    this.pickables = [];
    this.skillField = null;
    this._constLines = []; // constellation figure lines (dimmed in focus)
    this._constLabels = []; // category label sprites
    this.dust = null;
    this.glows = []; // { sprite, base } for subtle pulsing
    this.nodeById = new Map();
    this.selectedId = "";
    this.onSelect = null;
    this.onHover = null;
    this.makeLabel = null;
    this.makeCatLabel = null;

    this.raycaster = new THREE.Raycaster();
    this.raycaster.params.Points = { threshold: 6 };
    this.pointer = new THREE.Vector2();
    this._hoverScheduled = false;
    this._framed = false;
    this._autoRotate = true;
    this._cameraTween = null;
    this._downXY = null;
    this._resumeTimer = 0;

    this._onPointerDown = this._onPointerDown.bind(this);
    this._onPointerMove = this._onPointerMove.bind(this);
    this._onPointerLeave = this._onPointerLeave.bind(this);
    this._onClick = this._onClick.bind(this);
    this._onDoubleClick = this._onDoubleClick.bind(this);
    this._animate = this._animate.bind(this);
  }

  mount(el, { width, height, makeLabel, makeCatLabel, onSelect, onHover }) {
    this.el = el;
    this.width = Math.max(320, width || 900);
    this.height = Math.max(320, height || 560);
    this.makeLabel = makeLabel;
    this.makeCatLabel = makeCatLabel;
    this.onSelect = onSelect;
    this.onHover = onHover;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
    renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
    renderer.setSize(this.width, this.height, false);
    renderer.setClearColor(new THREE.Color("#080c20"), 1);
    // Tone mapping + sRGB output: without these, three.js renders emissive/bloom
    // in raw linear space — washed-out, flat, "plastic" materials and a dim core.
    // ACES filmic gives suns a proper bright-to-warm rolloff; exposure >1 lifts
    // the whole scene so the North Star reads as a luminous body, not a grey ball.
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.35;
    renderer.domElement.style.display = "block";
    renderer.domElement.style.width = "100%";
    renderer.domElement.style.height = "100%";
    el.appendChild(renderer.domElement);
    this.renderer = renderer;

    const scene = new THREE.Scene();
    scene.background = makeSpaceGradient();
    // Atmospheric depth: exponential fog so the distant skill shell (≈230–270
    // units out) recedes into the background instead of competing with the
    // foreground goal suns — but eased back from 0.0019 so the brighter North
    // Star light (see _coreLight) isn't swallowed and the scene isn't too black.
    scene.fog = new THREE.FogExp2(0x070a1c, 0.0005);
    scene.add(this.linkGroup, this.trailGroup, this.selEdgeGroup, this.fxGroup, this.haloGroup, this.nodeGroup, this.labelGroup, this.focusLabelGroup);
    this.scene = scene;

    const camera = new THREE.PerspectiveCamera(52, this.width / this.height, 1, 4000);
    camera.position.set(0, 120, 280);
    this.camera = camera;

    // Lighting for SELF-LUMINOUS goal stars (reverted from planet mode): goals
    // glow on their own, so lighting just needs to model the smaller
    // non-emissive children (projects/tasks) softly and not leave them black or
    // plastic. Ambient eased down so the core PointLight reclaims its
    // day/night terminator; a HemisphereLight then fills the dark side with a
    // directional cool wash instead of a flat global lift.
    scene.add(new THREE.AmbientLight(0x6c7aa6, 0.6));
    scene.add(new THREE.HemisphereLight(0x2a3a66, 0x0a0f24, 0.3));
    const key = new THREE.PointLight(0xbcd4ff, 1.0, 1600);
    key.position.set(120, 220, 200);
    scene.add(key);
    const core = new THREE.PointLight(0xffe9b8, 2.2, 1100, 0.7);
    core.position.set(0, 10, 0);
    scene.add(core);
    this._coreLight = core;

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.rotateSpeed = 0.7;
    controls.target.set(0, 12, 0);
    controls.minDistance = 80;
    controls.maxDistance = 1200;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.01;
    this.controls = controls;

    const composer = new EffectComposer(renderer);
    composer.addPass(new RenderPass(scene, camera));
    const bloom = new UnrealBloomPass(new THREE.Vector2(this.width, this.height), 0.6, 0.7, 0.65);
    composer.addPass(bloom);
    // CRITICAL: when rendering through EffectComposer, renderer.toneMapping /
    // outputColorSpace do NOT apply — the composer writes raw LINEAR colour to the
    // canvas, which is why suns looked grey/flat/"plastic" and bloom never sang.
    // OutputPass is the final pass that applies ACES tone mapping + sRGB to the
    // composited (post-bloom) image. Without it the whole scene is washed out.
    composer.addPass(new OutputPass());
    this.composer = composer;
    this.bloom = bloom;

    this._addDust();

    renderer.domElement.addEventListener("pointerdown", this._onPointerDown);
    renderer.domElement.addEventListener("pointermove", this._onPointerMove);
    renderer.domElement.addEventListener("pointerleave", this._onPointerLeave);
    renderer.domElement.addEventListener("click", this._onClick);
    renderer.domElement.addEventListener("dblclick", this._onDoubleClick);

    this.raf = window.requestAnimationFrame(this._animate);
  }

  resize(width, height) {
    if (!this.renderer) return;
    this.width = Math.max(320, width || this.width);
    this.height = Math.max(320, height || this.height);
    this.renderer.setSize(this.width, this.height, false);
    this.camera.aspect = this.width / this.height;
    this.camera.updateProjectionMatrix();
    this.composer.setSize(this.width, this.height);
    this.bloom?.setSize(this.width, this.height);
  }

  setData(graphData, sand) {
    // Capture the previous id set BEFORE clearing the scene so we can flag
    // newly-arrived nodes (e.g. fresh evidence/skills imported from a resume)
    // for a one-shot bloom-in animation. First load is intentionally NOT
    // animated — every node would shimmer, defeating the cue.
    const prevIds = new Set(this.nodeById ? this.nodeById.keys() : []);
    this._clearScene();
    const nodes = graphData.nodes || [];
    this.nodeById = new Map(nodes.map((n) => [n.id, n]));
    if (prevIds.size > 0) {
      const added = new Set();
      nodes.forEach((n) => {
        if (n && n.id && !prevIds.has(n.id)) added.add(n.id);
      });
      // Cap how many things can shimmer at once — a giant resume ingest can
      // produce 100+ new nodes, and animating them all at full brightness is
      // both visually noisy and a GPU hit at the wrong moment.
      this._newlyAdded = added.size > 80 ? new Set([...added].slice(0, 80)) : added;
      this._newlyAddedAt = typeof performance !== "undefined" ? performance.now() : Date.now();
    } else {
      this._newlyAdded = new Set();
    }
    const posById = new Map(nodes.map((n) => [n.id, v3(n)]));
    this._posById = posById;

    const byRole = (role) => nodes.filter((n) => n.role === role);
    const links = (graphData.links || []).map((l) => ({
      source: typeof l.source === "object" ? l.source.id : l.source,
      target: typeof l.target === "object" ? l.target.id : l.target,
      relation: l.relation || l.type,
    }));

    // ---- Core glow (North Star) ----
    const core = byRole("trunk")[0];
    this._coreId = core ? core.id : null;
    if (core) this._addCoreGlow(posById.get(core.id));

    // ---- Orbit rings express the hierarchy (who circles whom) instead of a web
    // of edges: each goal/project/… ring is drawn as a faint glowing ellipse.
    // Relationship filaments are reserved for selection (see applySelection).
    (graphData.orbits || []).forEach((o) => this._addOrbitRing(o));

    // Keep edge metadata for selection highlighting, but don't draw the full web
    // up-front — only the selected node's ties light up.
    this._edges = links
      .filter((l) => ["alignment", "contains", "generated_by", "produces", "supports", "derives"].includes(l.relation))
      .map((l) => ({ source: l.source, target: l.target, relation: l.relation }));

    // ---- Orb nodes (everything except skills + sand) ----
    nodes.forEach((node) => {
      if (node.role === "star") return;
      this._addOrb(node, posById.get(node.id));
    });

    // ---- Skill constellations (per-category clusters + figure lines) ----
    this._addConstellations(byRole("star"), graphData.constellations || []);

    // ---- Source spiral galaxy below: faint core glow so it reads as its own
    // galaxy (research themes = arms), distinct from the growth system above. ----
    if (sand && sand.points) {
      this.fxGroup.add(sand.points);
      this.sandPoints = sand.points;
      this.sandClusters = sand.clusters || [];
      const srcCenter = new THREE.Vector3(0, -175, 0);
      this._addHalo(srcCenter, 0x9ec8ff, 70, 0.32);
      this._addHalo(srcCenter, 0xbfe0ff, 32, 0.5);
    }

    // ---- Orbital animation model: order nodes parent-before-child so each
    // frame we can compose nested orbits (a project follows its moving goal). ----
    this._nodeOrbits = graphData.nodeOrbits || {};
    this._roleById = new Map(nodes.map((n) => [n.id, n.role]));
    this._statusById = new Map(nodes.map((n) => [n.id, String(n.status || "")]));
    this._childrenByParent = new Map();
    Object.entries(this._nodeOrbits).forEach(([id, o]) => {
      if (!o || !o.parentId) return;
      if (!this._childrenByParent.has(o.parentId)) this._childrenByParent.set(o.parentId, []);
      this._childrenByParent.get(o.parentId).push(id);
    });
    this._livePos = new Map(nodes.map((n) => [n.id, v3(n).clone()]));
    const order = [];
    const seen = new Set();
    const visit = (id) => {
      if (seen.has(id)) return;
      const o = this._nodeOrbits[id];
      if (o && o.parentId && this._nodeOrbits[o.parentId]) visit(o.parentId);
      seen.add(id);
      order.push(id);
    };
    Object.keys(this._nodeOrbits).forEach(visit);
    this._orbitOrder = order;

    // Re-apply any active subsystem focus to the freshly-built scene.
    if (this._focusRootId && !this.nodeById.has(this._focusRootId)) {
      this._focusRootId = null;
    }
    this._applyLevelOfDetail();

    this.applySelectionHighlight();
    if (!this._framed) {
      this.fit(0);
      this._framed = true;
    }
  }

  // ---------- builders ----------

  _addDust() {
    // Faint far-field star dust filling the deep space backdrop.
    const N = 1400;
    const pos = new Float32Array(N * 3);
    for (let i = 0; i < N; i += 1) {
      // Deterministic-ish spread (not layout-critical): spherical shell.
      const a = (i * 2.39996) % (Math.PI * 2);
      const b = Math.acos(1 - (2 * ((i * 0.61803) % 1)));
      const r = 700 + ((i * 53) % 900);
      pos[i * 3] = Math.sin(b) * Math.cos(a) * r;
      pos[i * 3 + 1] = Math.cos(b) * r * 0.6;
      pos[i * 3 + 2] = Math.sin(b) * Math.sin(a) * r;
    }
    const geom = new THREE.BufferGeometry();
    geom.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    const mat = new THREE.PointsMaterial({
      color: DUST_COLOR,
      size: 1.6,
      sizeAttenuation: true,
      map: glowTexture(),
      transparent: true,
      opacity: 0.5,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    });
    const dust = new THREE.Points(geom, mat);
    this.fxGroup.add(dust);
    this.dust = dust;
  }

  _addCoreGlow(pos) {
    if (!pos) return;
    // Bright core sphere + layered halo sprites. The North Star is the centre of
    // gravity, so it must read as the single largest body — sized clearly above
    // the biggest goal sun (goals cap at ~18, see _addOrb → core ≈ 1.8x). Halos
    // scale with it.
    const orb = new THREE.Mesh(
      new THREE.SphereGeometry(32, 28, 22),
      new THREE.MeshStandardMaterial({
        color: 0xffe9b8,
        emissive: 0xffd98f,
        emissiveIntensity: 1.5,
        roughness: 0.35,
      }),
    );
    orb.position.copy(pos);
    orb.userData.node = this.nodeById.get([...this.nodeById.keys()].find((k) => this.nodeById.get(k).role === "trunk"));
    this.nodeGroup.add(orb);
    if (orb.userData.node) this.pickables.push(orb);
    this._coreOrb = orb;
    this._coreHalos = [this._addHalo(pos, 0xffe6ad, 120, 0.7), this._addHalo(pos, 0xffcf80, 230, 0.3)];
  }

  _addHalo(pos, color, size, opacity) {
    const mat = new THREE.SpriteMaterial({
      map: glowTexture(),
      color,
      transparent: true,
      opacity,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    });
    const sprite = new THREE.Sprite(mat);
    sprite.position.copy(pos);
    sprite.scale.set(size, size, 1);
    this.haloGroup.add(sprite);
    // `vis` is a level-of-detail multiplier the focus system sets; the breathing
    // loop multiplies it into the live opacity so LOD dimming isn't clobbered.
    const entry = { sprite, base: size, baseOpacity: opacity, phase: (pos.x + pos.z) * 0.05, vis: 1 };
    sprite.userData.glow = entry;
    this.glows.push(entry);
    return sprite;
  }

  _addOrb(node, pos) {
    if (!pos) return;
    const weight = node.visualWeight || { radius: 1, opacity: 0.9, emissive: 1 };
    const color = new THREE.Color(node.color || "#9fb29c");
    const placeholder = Boolean(node.placeholder || node.implemented === false);
    // Evidence moons (task-generated evidence orbiting its task) read as a tiny
    // bright point — a comet nucleus, clearly subordinate to the task. Its size is
    // fixed (decoupled from the degree-based `val`) so it always stays a dot no
    // matter how many edges the evidence has.
    const moon = Boolean(node.moon);
    const val = node.val || 5;
    let r;
    if (moon) {
      r = 0.55;
    } else if (node.role === "direction") {
      // Goals are suns: `val` carries subtree mass (≈11..18), so let the radius
      // ride a moderate range (≈12..18). A goal must always out-size the projects
      // orbiting it, yet stay clearly UNDER the North Star core (32, ≈1.8x the
      // biggest goal) so the centre of gravity reads as the single largest body.
      r = Math.max(12, Math.min(18, 7 + val * 0.5)) * (weight.radius || 1);
    } else {
      // Children get PER-ROLE size bands so a node's tier is readable from size
      // alone (the strongest pre-attentive channel): projects clearly out-size
      // tasks, tasks out-size evidence, none of them rival a goal sun. `val` here
      // is the degree-based size (≈3..9). Bands: project 5..9, task 2.5..4.5,
      // other children (constellation/output) ≈3..5.
      const ride = 0.7 + Math.min(1.0, val / 9);
      if (node.role === "branch") {
        // Project.
        r = Math.max(5, Math.min(9, 5 * ride)) * (weight.radius || 1);
      } else if (node.role === "leaf") {
        // Task / output.
        r = Math.max(2.5, Math.min(4.5, 2.6 * ride)) * (weight.radius || 1);
      } else {
        // Project-tied evidence (fruit), claims (constellation), misc children.
        r = Math.max(2.2, Math.min(5, 2.8 * ride)) * (weight.radius || 1);
      }
    }

    // Planet-like material: a touch of metalness + lower roughness give a soft
    // specular sheen so spheres read as lit bodies rather than flat discs, while
    // the emissive keeps them glowing against the deep space. Placeholders stay
    // matte + dim. Moons (a task's generated-evidence satellite) are tiny but the
    // brightest body on screen — a sparkling firefly whose mere presence signals
    // "this task has already produced evidence".
    //
    // Goal suns are rendered as PLANETS lit by the North Star, NOT as self-glowing
    // stars: the only warm light in the scene comes from the core PointLight, so
    // each goal shows a lit core-facing hemisphere and a shadowed far side — a
    // real day/night terminator. Progress is carried by SIZE (see main.jsx val),
    // not brightness; a stalled goal desaturates toward grey + dims its faint
    // ember so "stopped work" still reads pre-attentively as a cooling world.
    const isGoal = node.role === "direction";
    const stalled = isGoal && Boolean(node.stalled);
    // Non-active goal lifecycle: completed = cool stable white star (achievement),
    // archived/paused = burnt-out grey ember. Reads as "history" instead of
    // disappearing — keeps the sense of accomplishment + the past trajectory.
    const goalStatus = isGoal ? String(node.status || "active") : "";
    const isCompletedGoal = goalStatus === "completed";
    const isExtinguishedGoal = goalStatus === "archived" || goalStatus === "paused";
    if (isGoal && !placeholder) {
      // Self-luminous star: warm-white only nudges the hue so an active goal
      // keeps its goal-coloured identity (the per-goal hashed colour) and a
      // stalled goal cools by a small amount instead of flattening to grey.
      // Previously a stalled goal lerped 0.5 into a steel-grey, which made
      // EVERY goal in a profile that had not been touched recently read as
      // generic dead matter — defeating the point of distinct goal colours.
      color.lerp(new THREE.Color("#fff4e0"), stalled ? 0.18 : 0.35);
      if (stalled) {
        // Slight cool desat (still keeps the underlying hue legible).
        color.lerp(new THREE.Color("#a8b1c5"), 0.18);
      }
      if (isCompletedGoal) {
        color.lerp(new THREE.Color("#dde6ff"), 0.55);
      } else if (isExtinguishedGoal) {
        color.lerp(new THREE.Color("#6b7384"), 0.65);
      }
    }
    let baseEmissive = placeholder ? 0.22 : moon ? 1.6 : 0.62;
    if (isGoal && !placeholder) {
      if (isExtinguishedGoal) {
        baseEmissive = 0.3;
      } else if (isCompletedGoal) {
        baseEmissive = 0.95;
      } else {
        // Active goals: strong but under bloom threshold so core light still
        // sculpts a day/night terminator instead of frying the whole sphere.
        baseEmissive = stalled ? 0.7 : 1.0;
      }
    }
    const baseOpacity = placeholder ? 0.5 : isExtinguishedGoal ? 0.78 : 0.98;
    const orb = new THREE.Mesh(
      new THREE.SphereGeometry(r, 32, 24),
      new THREE.MeshStandardMaterial({
        color,
        emissive: color.clone().multiplyScalar(0.9),
        emissiveIntensity: baseEmissive,
        roughness: placeholder ? 0.7 : isGoal ? 0.55 : 0.42,
        metalness: placeholder ? 0.0 : isGoal ? 0.1 : 0.22,
        transparent: true,
        opacity: baseOpacity,
      }),
    );
    orb.position.copy(pos);
    orb.userData.node = node;
    orb.userData.baseEmissive = baseEmissive;
    orb.userData.baseOpacity = baseOpacity;
    this.nodeGroup.add(orb);
    // Moons are ambient indicators, not navigation targets — leave them out of the
    // pickables so a click falls through to the task/empty space behind them.
    if (!moon) this.pickables.push(orb);

    // Glow halo, dimmer for placeholders; the moon keeps a tight vivid halo a few
    // times its (tiny) radius so the little comet nucleus twinkles bright without
    // growing into a disc. Goals (planet mode) get only a SMALL, faint halo: a
    // big additive bloom would wash out the North-Star day/night terminator that
    // is the whole point, so we keep it tight so the lit/shadow line stays crisp.
    const haloColor = color.clone().lerp(new THREE.Color("#ffffff"), moon ? 0.6 : 0.25);
    const haloScale = moon ? 3.4 : isGoal ? r * 1.5 : r * (placeholder ? 2.4 : 3.4);
    const haloOpacity = placeholder ? 0.16 : moon ? 0.8 : isGoal ? 0.18 : 0.42;
    const halo = this._addHalo(pos, haloColor.getHex(), haloScale, haloOpacity);
    // Track for orbital animation: orb + halo move together each frame.
    this._orbMesh.set(node.id, orb);
    this._orbHalo.set(node.id, halo);

    // Overview "produced evidence" cue: tasks with attached evidence get a
    // small static halo (no comet — that's a focused-mode detail). Preserves
    // the "this task has produced something" signal in zoomed-out view
    // without the high-speed comet noise.
    if (node.hasEvidence && !moon && node.role === "leaf" && !placeholder) {
      const evidenceHalo = this._addHalo(
        pos,
        new THREE.Color("#f4c97a").getHex(),
        r * 2.1,
        0.34,
      );
      this._orbHalo.set(`${node.id}::evidence`, evidenceHalo);
    }

    // Goal progress arc: a thin ring around the goal whose lit sweep = derived
    // project-completion progress (0..1). Progress is carried by this ARC, never
    // by the goal's size or brightness, so importance (size) / lit-by-North-Star
    // (brightness) / progress (arc) stay three independent channels.
    if (isGoal && !placeholder && typeof node.progress === "number") {
      this._addGoalProgressArc(node.id, r, node.progress, color, stalled);
    }

    // Evidence moons get a fading comet trail — a vertex-coloured line whose tail
    // dims to nothing. The whipping comet (head + trail) is the sole cue that this
    // task has produced evidence, so the tier-3 orbit ring is intentionally absent.
    if (moon) this._addCometTrail(node.id, color, node);
  }

  // A progress ring around a goal: a faint full background annulus + a bright
  // foreground arc swept to `progress` (0..1). Built from filled RingGeometry
  // (NOT THREE.Line — WebGL caps line width at 1px, so a line ring is nearly
  // invisible). This is the ONLY channel that encodes derived project-completion
  // progress — size stays mass, brightness stays North-Star lighting. Tracked in
  // the per-frame loop so it stays glued + camera-facing as the goal orbits.
  _addGoalProgressArc(id, orbR, progress, color, stalled) {
    const p = Math.max(0, Math.min(1, Number(progress) || 0));
    // Slim halo ring, hugging the goal: a 0.9-unit thick band ~1.4 units off
    // the surface. The earlier 3-unit thick band sitting 3.5 units out felt
    // like Saturn's rings — visually dominant + ugly. With a tighter, thinner
    // band the progress reads as a subtle bracelet on the goal, not the main
    // event.
    const inner = orbR + 1.4;
    const outer = orbR + 2.3;
    const TAU = Math.PI * 2;
    const arcColor = stalled ? new THREE.Color("#9aa0ad") : color.clone().lerp(new THREE.Color("#ffffff"), 0.35);

    const group = new THREE.Group();

    // Faint full-circle track (the "100%" reference) so a 20% arc reads as
    // "20% of a ring" rather than a stray sliver.
    const bg = new THREE.Mesh(
      new THREE.RingGeometry(inner, outer, 96),
      new THREE.MeshBasicMaterial({ color: 0x7889b4, transparent: true, opacity: 0.14, side: THREE.DoubleSide, depthWrite: false }),
    );
    group.add(bg);

    // Bright foreground arc sweeping p·TAU from the top (12 o'clock), clockwise.
    if (p > 0.001) {
      const arc = new THREE.Mesh(
        new THREE.RingGeometry(inner, outer, Math.max(3, Math.round(96 * p)), 1, Math.PI / 2 - p * TAU, p * TAU),
        new THREE.MeshBasicMaterial({ color: arcColor.getHex(), transparent: true, opacity: stalled ? 0.55 : 0.85, side: THREE.DoubleSide, depthWrite: false, blending: THREE.AdditiveBlending }),
      );
      group.add(arc);
    }

    group.userData.isGoalArc = true;
    this.haloGroup.add(group);
    this._goalArcs.set(id, { group, radius: outer });
  }

  // Map evidence quality to comet visuals. Defaults give every comet enough
  // tail + brightness to be visible (the earlier defaults bottomed out at
  // strength=0.35 / LEN=18 and made unrated evidence vanish on dark stages).
  _cometProfile(node) {
    const meta = (node && node.meta) || {};
    const strength = String(meta.strength || "").toLowerCase();
    const review = String(meta.review_status || (node && node.status) || "").toLowerCase();
    const reviewed = review === "reviewed" || review === "accepted" || review === "verified";
    let strengthScore;
    if (strength === "strong" || strength === "high" || strength === "high_trust" || strength === "very_high") {
      strengthScore = 1;
    } else if (strength === "medium" || strength === "moderate" || strength === "mid" || strength === "ok") {
      strengthScore = 0.7;
    } else if (strength === "weak" || strength === "low" || strength === "low_trust" || strength === "draft") {
      strengthScore = 0.45;
    } else if (strength) {
      // Unknown bucket — give it the default high-confidence "evidence exists"
      // baseline rather than punishing it for not matching our enum.
      strengthScore = 0.75;
    } else {
      strengthScore = 0.65;
    }
    const len = Math.round(18 + strengthScore * 20); // 18..38 samples, always visibly long
    const headGlow = 0.75 + strengthScore * 0.25;    // 0.75..1.0 — comet head always bright
    const tailWhitePeak = reviewed ? 0.55 : 0.32;    // unreviewed dims tip, still glows
    let recencyDays = null;
    const dateStr = String(meta.date || "");
    if (dateStr) {
      const t = Date.parse(dateStr);
      if (!Number.isNaN(t)) {
        recencyDays = Math.max(0, (Date.now() - t) / (1000 * 60 * 60 * 24));
      }
    }
    // Recency NEVER drops the speed below 1.0 — older items just don't get the
    // fresh-evidence boost. Previously we let recency throttle tier-3 orbits
    // down to 0.55x, which combined with the focus-graded 0.29x slowdown made
    // the comets nearly static. Now: undated = 1, fresh = 1.25, otherwise 1.
    const recencyBoost =
      recencyDays === null ? 1 : recencyDays < 7 ? 1.25 : recencyDays < 30 ? 1.05 : 1.0;
    return { len, headGlow, tailWhitePeak, reviewed, strengthScore, recencyBoost };
  }

  _addCometTrail(id, color, node = null) {
    const profile = this._cometProfile(node);
    const LEN = profile.len;
    const positions = new Float32Array(LEN * 3);
    const colors = new Float32Array(LEN * 3);
    const geom = new THREE.BufferGeometry();
    for (let i = 0; i < LEN; i += 1) {
      // Tail fades to black (additive blending → fades to invisible). Head
      // brightness rides `strength` (stronger evidence = brighter head); only
      // reviewed items get the bright-white nucleus tip, so unreviewed drafts
      // read as "in flight, not yet vouched for".
      const f = 1 - i / (LEN - 1);
      const headIntensity = Math.pow(f, 1.6) * profile.headGlow;
      const white = profile.tailWhitePeak * Math.pow(f, 6);
      colors[i * 3] = Math.min(1, color.r * headIntensity + white);
      colors[i * 3 + 1] = Math.min(1, color.g * headIntensity + white);
      colors[i * 3 + 2] = Math.min(1, color.b * headIntensity + white);
    }
    geom.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geom.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    const mat = new THREE.LineBasicMaterial({
      vertexColors: true,
      transparent: true,
      // Reviewed comets sit at full glow; unreviewed dim a touch so a batch
      // of new drafts does not strobe the user.
      opacity: profile.reviewed ? 0.95 : 0.78,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    const line = new THREE.Line(geom, mat);
    line.frustumCulled = false;
    this.trailGroup.add(line);
    this._comets.set(id, { line, positions, history: [], recencyBoost: profile.recencyBoost });
  }

  _advanceComet(comet, head) {
    const LEN = comet.positions.length / 3;
    const hist = comet.history;
    hist.unshift(head.clone()); // newest at index 0 (the head)
    if (hist.length > LEN) hist.length = LEN;
    for (let i = 0; i < LEN; i += 1) {
      // Before the trail has filled, clamp to the oldest known sample so the tail
      // collapses onto the head instead of sitting at the origin.
      const s = hist[Math.min(i, hist.length - 1)] || head;
      comet.positions[i * 3] = s.x;
      comet.positions[i * 3 + 1] = s.y;
      comet.positions[i * 3 + 2] = s.z;
    }
    comet.line.geometry.attributes.position.needsUpdate = true;
  }

  _addOrbitRing(orbit) {
    // A faint glowing ellipse on the orbit's inclined, swivelled plane — the
    // visual cue for "these nodes circle this center". Mirrors the layout's
    // ellipse math (semi-major a, semi-minor b, in-plane swivel, X-axis tilt) so
    // the ring sits exactly under the orbiting nodes. Tiny orbits are skipped.
    const { center, a, b, tilt, swivel } = orbit;
    const semiMajor = Number.isFinite(a) ? a : Number.isFinite(orbit.radius) ? orbit.radius : 0;
    const semiMinor = Number.isFinite(b) ? b : semiMajor;
    if (!(semiMajor > 6)) return;
    const SEG = 128;
    const cosT = Math.cos(tilt || 0);
    const sinT = Math.sin(tilt || 0);
    const cosS = Math.cos(swivel || 0);
    const sinS = Math.sin(swivel || 0);
    // Build the ring relative to its center and place it via line.position, so the
    // animation loop can translate the whole ring by its (orbiting) parent's live
    // displacement each frame — keeping the ellipse glued under its orbiting nodes.
    const pts = [];
    for (let i = 0; i <= SEG; i += 1) {
      const ang = (i / SEG) * Math.PI * 2;
      const ex = Math.cos(ang) * semiMajor;
      const ey = Math.sin(ang) * semiMinor;
      const px = ex * cosS - ey * sinS;
      const pz = ex * sinS + ey * cosS;
      pts.push(new THREE.Vector3(px, pz * sinT, pz * cosT));
    }
    const geom = new THREE.BufferGeometry().setFromPoints(pts);
    // Cool per-tier palette so projects / tasks / evidence rings read as distinct
    // shells (no more the murky blue-green that washed the goal ring out).
    const TIER_RING = { 1: 0xcfe0ff, 2: 0xa9b8ff, 3: 0xc9a8ff };
    const TIER_OP = { 1: 0.22, 2: 0.18, 3: 0.18 };
    const ringColor = TIER_RING[orbit.tier] || 0xcfe0ff;
    const ringOpacity = TIER_OP[orbit.tier] || 0.2;
    const mat = new THREE.LineBasicMaterial({
      color: ringColor,
      transparent: true,
      opacity: ringOpacity,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    const line = new THREE.Line(geom, mat);
    line.position.set(center.x, center.y, center.z);
    // Tag the ring with its owning parent so focus-mode can dim/hide it per tier,
    // and so the animation loop can re-translate it as that parent orbits. The
    // base center is the parent's *initial* position; each frame we shift the ring
    // by the parent's live displacement from that base (see _updateOrbits).
    line.userData.parentId = orbit.parentId || null;
    line.userData.baseCenter = new THREE.Vector3(center.x, center.y, center.z);
    line.userData.baseOpacity = ringOpacity;
    line.userData.tier = orbit.tier || null;
    this.linkGroup.add(line);
  }

  _addSelectionEdge(a, b, color, options = {}) {
    const { dashed = false, dashSize = 4, gapSize = 3, lineWidth = 1, completed = false } = options;
    const mid = a.clone().lerp(b, 0.5);
    mid.y += a.distanceTo(b) * 0.12;
    const curve = new THREE.QuadraticBezierCurve3(a, mid, b);
    const geom = new THREE.BufferGeometry().setFromPoints(curve.getPoints(20));
    // Completed paths (e.g. a task → reviewed evidence → lit skill chain) get
    // a warm gold relight so the user can scan the canvas for "where did
    // things actually pay off". Everything else keeps its semantic colour.
    const finalColor = completed ? 0xffcf6b : color;
    const mat = dashed
      ? new THREE.LineDashedMaterial({
          color: finalColor,
          transparent: true,
          opacity: completed ? 0.92 : 0.75,
          dashSize,
          gapSize,
          blending: THREE.AdditiveBlending,
          depthWrite: false,
          linewidth: lineWidth,
        })
      : new THREE.LineBasicMaterial({
          color: finalColor,
          transparent: true,
          opacity: completed ? 0.92 : 0.7,
          blending: THREE.AdditiveBlending,
          depthWrite: false,
          linewidth: lineWidth,
        });
    const line = new THREE.Line(geom, mat);
    if (dashed) line.computeLineDistances();
    this.selEdgeGroup.add(line);
    return line;
  }

  _addConstellations(stars, constellations) {
    if (!stars.length) return;
    const byId = new Map(stars.map((n) => [n.id, n]));
    const litOf = (node) => {
      const lit = Number.isFinite(node.starEmissive) ? node.starEmissive : 0.2;
      return Math.min(1, Math.max(0, (lit - 0.2) / 0.58));
    };
    // ---- Star points (same shader/size/color mapping as the old halo) ----
    const positions = [];
    const colors = [];
    const sizes = [];
    stars.forEach((node) => {
      const p = v3(node);
      positions.push(p.x, p.y, p.z);
      const c = new THREE.Color(node.color || "#9bbf86");
      const vivid = litOf(node);
      // Mastered skills blaze in full category color and large; locked ones glow
      // faint warm-white and small — a real night sky where some stars burn bright.
      const floor = new THREE.Color("#cfd8ff");
      c.lerp(floor, (1 - vivid) * 0.55);
      c.multiplyScalar(0.92 + vivid * 0.5); // locked .92 → expert 1.42 (HDR for bloom)
      colors.push(c.r, c.g, c.b);
      sizes.push(20 + vivid * 28); // locked 20 → expert 48
    });
    const geom = new THREE.BufferGeometry();
    geom.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    geom.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
    geom.setAttribute("aSize", new THREE.Float32BufferAttribute(sizes, 1));
    // Custom shader so each star carries its own size (PointsMaterial can't), with
    // a soft round glow and additive blending against the deep space.
    const mat = new THREE.ShaderMaterial({
      uniforms: {
        uTex: { value: glowTexture() },
        uPulse: { value: 1.0 },
        uDim: { value: 1.0 },
      },
      vertexShader: `
        attribute float aSize;
        varying vec3 vColor;
        uniform float uPulse;
        void main() {
          vColor = color;
          vec4 mv = modelViewMatrix * vec4(position, 1.0);
          gl_PointSize = aSize * uPulse * (300.0 / -mv.z);
          gl_Position = projectionMatrix * mv;
        }
      `,
      fragmentShader: `
        uniform sampler2D uTex;
        uniform float uDim;
        varying vec3 vColor;
        void main() {
          vec4 t = texture2D(uTex, gl_PointCoord);
          gl_FragColor = vec4(vColor * uDim, 1.0) * t;
        }
      `,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      vertexColors: true,
    });
    const points = new THREE.Points(geom, mat);
    this.fxGroup.add(points);
    this.skillField = { points };

    // ---- Constellation figure lines: within each category, chain its stars from
    // brightest to faintest so the cluster reads as a drawn constellation. One
    // LineSegments for all clusters (cheap), dimmable by the focus LOD. ----
    this._constLines = [];
    this._constLabels = [];
    const segPts = [];
    const segCols = [];
    (constellations || []).forEach((c) => {
      const members = (c.memberIds || [])
        .map((id) => byId.get(id))
        .filter(Boolean)
        .sort((a, b) => litOf(b) - litOf(a));
      if (members.length >= 2) {
        const lineColor = new THREE.Color(c.color || "#9bbf86");
        for (let i = 0; i < members.length - 1; i += 1) {
          const a = v3(members[i]);
          const b = v3(members[i + 1]);
          segPts.push(a.x, a.y, a.z, b.x, b.y, b.z);
          segCols.push(lineColor.r, lineColor.g, lineColor.b, lineColor.r, lineColor.g, lineColor.b);
        }
      }
      // Category label floating just above the cluster.
      if (this.makeCatLabel && c.center) {
        const sprite = this.makeCatLabel(c.cat, c.color || "#9bbf86");
        if (sprite) {
          sprite.position.set(c.center.x, c.center.y + 38, c.center.z);
          sprite.userData.baseOpacity = sprite.material.opacity;
          this.fxGroup.add(sprite);
          this._constLabels.push(sprite);
        }
      }
    });
    if (segPts.length) {
      const lgeom = new THREE.BufferGeometry();
      lgeom.setAttribute("position", new THREE.Float32BufferAttribute(segPts, 3));
      lgeom.setAttribute("color", new THREE.Float32BufferAttribute(segCols, 3));
      const lmat = new THREE.LineBasicMaterial({
        vertexColors: true,
        transparent: true,
        opacity: 0.16,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      });
      const segs = new THREE.LineSegments(lgeom, lmat);
      segs.userData.baseOpacity = 0.16;
      this.fxGroup.add(segs);
      this._constLines.push(segs);
    }
  }

  // ---------- selection / labels ----------

  setSelected(id) {
    const next = id || "";
    if (next === this.selectedId) {
      this.applySelectionHighlight(); // same id, data may have rebuilt
      return;
    }
    this.selectedId = next;
    this.applySelectionHighlight();
  }

  applySelectionHighlight() {
    // Rebuild label + relationship filaments for the current selection. Called on
    // selection change (and data rebuild) — NOT every frame; per-frame motion uses
    // the cheap _repositionSelection so we don't recreate the label texture 60x/s.
    [this.labelGroup, this.selEdgeGroup].forEach((g) => {
      while (g.children.length) {
        const c = g.children.pop();
        c.material?.map?.dispose?.();
        c.material?.dispose?.();
        c.geometry?.dispose?.();
        g.remove(c);
      }
    });
    this._selEdgePairs = [];
    this._selLabel = null;
    const sel = this.selectedId;
    if (!sel) return;
    const node = this.nodeById.get(sel);
    if (!node) return;

    // Relationship filaments (only on selection, so the resting view stays clean).
    const here = this._posById.get(sel);
    if (here) {
      this._edges.forEach((e) => {
        if (e.source !== sel && e.target !== sel) return;
        const otherId = e.source === sel ? e.target : e.source;
        const other = this._posById.get(otherId);
        if (!other) return;
        // Relation-typed visual encoding so the user can read structural ties
        // (contains/alignment = solid hierarchy) apart from semantic ones
        // (supports/derives = derivation, dashed). The colour palette stays
        // close to the original blue/gold split so the new dashing is the
        // only addition for the resting case.
        const relation = String(e.relation || "");
        const isContainment = relation === "contains" || relation === "alignment";
        const isProduction = relation === "generated_by" || relation === "produces";
        const isDerivation = relation === "supports" || relation === "derives";
        const color =
          isDerivation ? 0x9fc0ff :
          isProduction ? 0xc8a6ff :
          0xffd9a0;
        // Goal/project status drives the "completed = gold" relight: an
        // archived/paused goal does NOT glow gold, but a done task/evidence
        // pair does, since the chain actually paid off.
        const aStatus = this._statusById && this._statusById.get(e.source);
        const bStatus = this._statusById && this._statusById.get(e.target);
        const completed =
          aStatus === "completed" || bStatus === "completed" ||
          aStatus === "reviewed" || bStatus === "reviewed" ||
          aStatus === "done" || bStatus === "done";
        const dashed = isDerivation;
        const line = this._addSelectionEdge(here, other, color, { dashed, completed });
        this._selEdgePairs.push({ line, aId: sel, bId: otherId });
      });
    }

    if (!this.makeLabel) return;
    const pos = v3(node);
    const sprite = this.makeLabel(node, true);
    if (sprite) {
      sprite.scale.multiplyScalar(2.2);
      const r = node.role === "direction" ? 12 : node.role === "branch" ? 9 : 7;
      this._selLabelOffsetY = r + 10;
      sprite.position.set(pos.x, pos.y + this._selLabelOffsetY, pos.z);
      this.labelGroup.add(sprite);
      this._selLabel = sprite;
    }
  }

  // Cheap per-frame update: move the existing label + selection filaments to the
  // selected node's current (orbiting) position without rebuilding geometry.
  _repositionSelection() {
    const sel = this.selectedId;
    if (!sel) return;
    const here = this._posById.get(sel);
    if (here && this._selLabel) {
      this._selLabel.position.set(here.x, here.y + (this._selLabelOffsetY || 12), here.z);
    }
    if (here && this._selEdgePairs) {
      this._selEdgePairs.forEach(({ line, bId }) => {
        const other = this._posById.get(bId);
        if (!other || !line.geometry) return;
        const mid = here.clone().lerp(other, 0.5);
        mid.y += here.distanceTo(other) * 0.12;
        const curve = new THREE.QuadraticBezierCurve3(here, mid, other);
        line.geometry.setFromPoints(curve.getPoints(20));
        line.geometry.attributes.position.needsUpdate = true;
        // Dashed lines need their per-vertex distance attribute refreshed on
        // every reposition or the dash pattern walks/sticks as the line moves.
        if (line.material && line.material.isLineDashedMaterial) {
          line.computeLineDistances();
        }
      });
    }
  }

  // ---------- camera ----------

  _bounds() {
    const box = new THREE.Box3();
    let any = false;
    this.nodeById.forEach((node) => {
      box.expandByPoint(v3(node));
      any = true;
    });
    if (!any) box.set(new THREE.Vector3(-120, -40, -120), new THREE.Vector3(120, 60, 120));
    return box;
  }

  fit(duration = 700) {
    if (!this.camera || !this.controls) return;
    // Fitting the whole galaxy exits any focused subsystem.
    this._focusRootId = null;
    this._applyLevelOfDetail();
    const box = this._bounds();
    // Include the source spiral galaxy below so the whole composition frames.
    if (this.sandPoints) box.expandByPoint(new THREE.Vector3(0, -200, 0));
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z, 80);
    const fov = (this.camera.fov * Math.PI) / 180;
    let dist = (maxDim / 2 / Math.tan(fov / 2)) * 0.85;
    dist = Math.max(this.controls.minDistance + 20, Math.min(this.controls.maxDistance - 20, dist));
    // A 3/4 side view (moderate elevation) so orbits read as ellipses AND the
    // source spiral below is visible — not a flat top-down map.
    const dir = new THREE.Vector3(0.1, 0.5, 1).normalize();
    this._tweenCamera(center.clone().add(dir.multiplyScalar(dist)), center, duration);
  }

  // Ellipse radius for an orbit record ({a,b} or legacy {radius}).
  _orbitRadius(o) {
    if (!o) return 0;
    const a = Number.isFinite(o.a) ? o.a : Number.isFinite(o.radius) ? o.radius : 0;
    const b = Number.isFinite(o.b) ? o.b : a;
    return Math.max(a, b);
  }

  // Walk the parentId chain up to the owning goal (role === "direction").
  _ancestorGoal(id) {
    let cur = id;
    const guard = new Set();
    while (cur && !guard.has(cur)) {
      guard.add(cur);
      if (this._roleById.get(cur) === "direction") return cur;
      const o = this._nodeOrbits[cur];
      cur = o ? o.parentId : null;
    }
    return null;
  }

  // The goal + every node orbiting under it (projects → tasks/evidence).
  _descendantsOf(rootId) {
    const out = new Set([rootId]);
    const stack = [rootId];
    while (stack.length) {
      const id = stack.pop();
      (this._childrenByParent.get(id) || []).forEach((k) => {
        if (!out.has(k)) {
          out.add(k);
          stack.push(k);
        }
      });
    }
    return out;
  }

  // Level-of-detail: when a goal subsystem is focused, fade the North Star and
  // the sibling goals (plus their subtrees) out, keep the skill star shell as the
  // outer reference, and dim claims to context. With no focus, everything is at
  // full strength (the "north-star level" overview). Borrowed from NASA Eyes /
  // 100k Stars: structure stays legible by fading, not hard culling.
  _setMeshLOD(mesh, level) {
    if (!mesh) return;
    mesh.visible = level > 0.02;
    const mat = mesh.material;
    if (!mat) return;
    const baseO = mesh.userData.baseOpacity == null ? 1 : mesh.userData.baseOpacity;
    const baseE = mesh.userData.baseEmissive == null ? 0.6 : mesh.userData.baseEmissive;
    mat.opacity = baseO * level;
    if ("emissiveIntensity" in mat) mat.emissiveIntensity = baseE * Math.max(level, level > 0 ? 0.18 : 0);
  }

  _applyLevelOfDetail() {
    const focus = this._focusRootId;
    const inFocus = focus ? this._descendantsOf(focus) : null;

    // Orbs (direction/branch/leaf/fruit/constellation — stars live in the field).
    // At OVERVIEW (no focus) we cull aggressively so the resting view is just the
    // North Star + goal suns: tasks/evidence/claims hide, projects dim to faint
    // pips. They reveal on goal focus. This turns the "dot-cloud blob" into a
    // readable map. In a FOCUSED goal, only that subsystem stays lit.
    this._orbMesh.forEach((mesh, id) => {
      const role = this._roleById.get(id);
      let level = 1;
      if (focus) {
        if (inFocus.has(id)) level = 1;
        else if (role === "constellation") level = 0.32; // claims fade to context
        else level = 0; // North Star siblings + their subtrees hide
      } else {
        // Overview level-of-detail.
        if (role === "direction") level = 1; // goal suns: the named map
        else if (role === "branch") level = 0.35; // projects: faint pips
        else if (role === "leaf" && mesh.userData.node?.hasEvidence) level = 0.32; // tasks-with-evidence: faint produced cue
        else level = 0; // tasks, evidence, claims: hidden until you focus a goal
      }
      this._setMeshLOD(mesh, level);
      const halo = this._orbHalo.get(id);
      if (halo && halo.userData.glow) halo.userData.glow.vis = level;
      const evHalo = this._orbHalo.get(`${id}::evidence`);
      if (evHalo && evHalo.userData.glow) evHalo.userData.glow.vis = level;
      // Comet trail dims with its own node (the evidence moon).
      const comet = this._comets.get(id);
      if (comet) {
        comet.line.visible = level > 0.02;
        comet.line.material.opacity = 0.85 * level;
      }
    });

    // North Star core: hidden while a goal subsystem is focused, dominant at overview.
    const coreLevel = focus ? 0 : 1;
    this._setMeshLOD(this._coreOrb, coreLevel);
    this._coreHalos.forEach((h) => {
      if (h && h.userData.glow) h.userData.glow.vis = coreLevel;
    });

    // Orbit rings. Focused: keep only the focused subsystem's inner rings. Overview:
    // keep only the goal orbit rings (parentId === core) as faint alignment lines;
    // hide tier-2/3 (project/task/evidence) rings so 50 rings collapse to a handful.
    this.linkGroup.children.forEach((line) => {
      const pid = line.userData ? line.userData.parentId : null;
      const tier = line.userData ? line.userData.tier : null;
      const baseOp = (line.userData && line.userData.baseOpacity) || 0.26;
      let level = 1;
      if (focus) {
        level = pid && inFocus.has(pid) && pid !== this._coreId ? 1 : 0;
      } else {
        // Overview: only goal orbits (tier 1 around the core / orphan core rings).
        level = pid === this._coreId || tier === 1 ? 1 : 0;
      }
      line.visible = level > 0.02;
      if (line.material) line.material.opacity = baseOp * level;
    });

    // Skill shell + sand stay visible (the outer reference). Dim it both when
    // focused (active subsystem reads nearer) AND at overview (it's background
    // context that shouldn't compete with the goal suns).
    if (this.skillField && this.skillField.points.material.uniforms.uDim) {
      this.skillField.points.material.uniforms.uDim.value = focus ? 0.55 : 0.7;
    }
    // Constellation figure-lines dim as background context, but the category
    // LABELS stay readable (the user needs to read the constellation names) —
    // labels get their own higher level than the faint lines.
    const constLineLevel = focus ? 0.5 : 0.6;
    const constLabelLevel = focus ? 0.7 : 0.95;
    this._constLines.forEach((segs) => {
      if (segs.material) segs.material.opacity = (segs.userData.baseOpacity || 0.16) * constLineLevel;
    });
    this._constLabels.forEach((sprite) => {
      if (sprite.material) sprite.material.opacity = (sprite.userData.baseOpacity || 0.86) * constLabelLevel;
    });

    this._rebuildFocusLabels();
  }

  // Persistent name tags. In a focused goal: the goal + its direct projects. At
  // overview (no focus): the North Star + every goal sun, so the resting view is a
  // NAMED map of suns rather than a field of anonymous dots — the single biggest
  // legibility win. Unlike the selection label (one node, rebuilt on select),
  // these stay up so the user always sees what each sun is. The per-frame loop
  // keeps them glued to the orbiting orbs (_repositionFocusLabels).
  _rebuildFocusLabels() {
    while (this.focusLabelGroup.children.length) {
      const c = this.focusLabelGroup.children.pop();
      c.material?.map?.dispose?.();
      c.material?.dispose?.();
      this.focusLabelGroup.remove(c);
    }
    this._focusLabels = [];
    if (!this.makeLabel) return;
    const focus = this._focusRootId;

    // Overview: label the North Star (trunk) + each goal (direction). Goals are
    // the only nodes drawn at full size at overview (see _applyLevelOfDetail), so
    // only they get names; projects/tasks/evidence reveal their labels on focus.
    if (!focus) {
      const overviewIds = [];
      if (this._coreId) overviewIds.push(this._coreId);
      this.nodeById.forEach((n, id) => {
        if (n.role === "direction") overviewIds.push(id);
      });
      overviewIds.forEach((id) => {
        const node = this.nodeById.get(id);
        if (!node) return;
        const isCore = id === this._coreId;
        const sprite = this.makeLabel(node, isCore);
        if (!sprite) return;
        if (isCore) sprite.scale.multiplyScalar(1.5);
        sprite.userData.baseOpacity = sprite.material.opacity;
        const r = isCore ? 28 : 18;
        sprite.userData.offsetY = r + 8;
        this.focusLabelGroup.add(sprite);
        this._focusLabels.push({ sprite, nodeId: id });
      });
      this._repositionFocusLabels();
      return;
    }

    // Focused goal: the goal itself + every direct project (role "branch") under it.
    const ids = [focus, ...(this._childrenByParent.get(focus) || []).filter((id) => this._roleById.get(id) === "branch")];
    ids.forEach((id) => {
      const node = this.nodeById.get(id);
      if (!node) return;
      const sprite = this.makeLabel(node, id === focus);
      if (!sprite) return;
      if (id === focus) sprite.scale.multiplyScalar(1.4);
      sprite.userData.baseOpacity = sprite.material.opacity;
      const r = id === focus ? 14 : 9;
      sprite.userData.offsetY = r + 7;
      this.focusLabelGroup.add(sprite);
      this._focusLabels.push({ sprite, nodeId: id });
    });
    this._repositionFocusLabels();
  }

  _repositionFocusLabels() {
    if (!this._focusLabels.length) return;
    // Screen-space LOD pass: project each label to clip space, clamp its
    // on-screen height to 11–28px (so distant labels do not vanish and near
    // ones do not blow up), and greedily hide overlapping siblings — keep one
    // label per ~80×24px bucket. Without this, sprites either disappear past
    // ~150 world units or pile into an unreadable mash on top of each other.
    const camera = this.camera;
    if (!camera) {
      this._focusLabels.forEach(({ sprite, nodeId }) => {
        const p = this._livePos.get(nodeId) || this._posById.get(nodeId);
        if (p) sprite.position.set(p.x, p.y + (sprite.userData.offsetY || 12), p.z);
      });
      return;
    }
    const projection = new THREE.Vector3();
    const renderer = this.renderer;
    const sizeVec = renderer && renderer.getSize ? renderer.getSize(new THREE.Vector2()) : new THREE.Vector2(800, 500);
    const viewportH = Math.max(120, sizeVec.y || 500);
    const viewportW = Math.max(120, sizeVec.x || 800);
    const occupied = new Map(); // bucket key -> priority
    const BUCKET_W = 80;
    const BUCKET_H = 24;
    const items = [];
    this._focusLabels.forEach(({ sprite, nodeId }) => {
      const p = this._livePos.get(nodeId) || this._posById.get(nodeId);
      if (!p) return;
      sprite.position.set(p.x, p.y + (sprite.userData.offsetY || 12), p.z);
      projection.copy(sprite.position).project(camera);
      const inFront = projection.z < 1 && projection.z > -1;
      if (!inFront) {
        sprite.visible = false;
        return;
      }
      const screenX = (projection.x * 0.5 + 0.5) * viewportW;
      const screenY = (1 - (projection.y * 0.5 + 0.5)) * viewportH;
      // Priority by role: north star > goal > selected > project > task > evidence.
      const role = this._roleById.get(nodeId);
      const priority = role === "trunk" ? 0 : role === "direction" ? 1 : nodeId === this.selectedId ? 2 : role === "branch" ? 3 : role === "leaf" ? 4 : 5;
      items.push({ sprite, nodeId, screenX, screenY, priority, projZ: projection.z });
    });
    items.sort((a, b) => a.priority - b.priority || a.projZ - b.projZ);
    items.forEach((item) => {
      const bx = Math.floor(item.screenX / BUCKET_W);
      const by = Math.floor(item.screenY / BUCKET_H);
      const key = `${bx}:${by}`;
      if (occupied.has(key)) {
        item.sprite.visible = false;
        return;
      }
      occupied.set(key, item.priority);
      item.sprite.visible = true;
      // Clamp on-screen height by adjusting sprite world scale: distance from
      // camera ∝ how much world-space the sprite eats per CSS pixel.
      const dist = Math.max(1, item.sprite.position.distanceTo(camera.position));
      const fovRad = ((camera.fov || 50) * Math.PI) / 180;
      const worldPerPixel = (2 * dist * Math.tan(fovRad / 2)) / viewportH;
      const baseHeight = item.sprite.userData.baseLabelHeight || item.sprite.scale.y || 6;
      if (!item.sprite.userData.baseLabelHeight) {
        item.sprite.userData.baseLabelHeight = baseHeight;
      }
      const targetPx = item.priority <= 1 ? 22 : item.priority === 2 ? 20 : 14;
      const targetWorld = targetPx * worldPerPixel;
      const k = Math.max(0.45, Math.min(2.6, targetWorld / baseHeight));
      const aspect = item.sprite.userData.baseAspect || (item.sprite.scale.x / item.sprite.scale.y);
      if (!item.sprite.userData.baseAspect) {
        item.sprite.userData.baseAspect = aspect;
      }
      item.sprite.scale.set(baseHeight * k * aspect, baseHeight * k, 1);
    });
  }

  focus(node, duration = 700) {
    if (!node || !this.camera || !this.controls) return;
    const id = typeof node === "string" ? node : node.id;
    const role = this._roleById.get(id) || (typeof node === "object" ? node.role : null);

    // Clicking the North Star (trunk) resets to the full galaxy overview.
    if (role === "trunk") {
      this.fit(duration);
      return;
    }

    // Entering a goal reveals its subsystem; focusing a project/task/evidence
    // keeps (or switches to) the owning goal as the focused root so its little
    // galaxy stays open while we dive deeper.
    if (role === "direction") {
      this._focusRootId = id;
    } else {
      const goalId = this._ancestorGoal(id);
      if (goalId) this._focusRootId = goalId;
    }
    this._applyLevelOfDetail();

    // Drill-down: frame the node together with its children's orbits so clicking
    // a goal reveals its projects, a project reveals its tasks + evidence, etc.
    const target = (this._livePos.get(id) || v3(node)).clone();
    const box = new THREE.Box3();
    box.expandByPoint(target);
    let subtreeR = 18;
    (this._childrenByParent.get(id) || []).forEach((cid) => {
      const cp = this._livePos.get(cid);
      if (cp) box.expandByPoint(cp);
      const o = this._nodeOrbits[cid];
      if (o) subtreeR = Math.max(subtreeR, this._orbitRadius(o) + 14);
    });
    // Pad by the child orbit radius so the whole ring is in frame.
    const center = box.getCenter(new THREE.Vector3());
    const span = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(span.x, span.y, span.z, subtreeR * 2, 44);
    const fov = (this.camera.fov * Math.PI) / 180;
    // Pad generously (1.6x) so the whole focused subsystem has breathing room and
    // its tiers don't crowd the frame edges — 1.25x sat the rings right against
    // the viewport.
    let dist = (maxDim / 2 / Math.tan(fov / 2)) * 1.6;
    dist = Math.max(this.controls.minDistance + 8, Math.min(this.controls.maxDistance - 20, dist));
    const dir = new THREE.Vector3(0.15, 0.5, 1).normalize();
    this._tweenCamera(center.clone().add(dir.multiplyScalar(dist)), center, duration);
  }

  _tweenCamera(toPos, toTarget, duration) {
    if (duration <= 0) {
      this.camera.position.copy(toPos);
      this.controls.target.copy(toTarget);
      this.controls.update();
      return;
    }
    this._cameraTween = {
      fromPos: this.camera.position.clone(),
      toPos,
      fromTarget: this.controls.target.clone(),
      toTarget,
      start: this.frame,
      frames: Math.max(1, Math.round((duration / 1000) * 60)),
    };
  }

  // ---------- interaction ----------

  _pointerNDC(event) {
    const rect = this.renderer.domElement.getBoundingClientRect();
    this.pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    return rect;
  }

  _onPointerDown(event) {
    this._downXY = { x: event.clientX, y: event.clientY };
    this._downAt = (typeof performance !== "undefined" ? performance.now() : Date.now());
    this._lastInteractionAt = this._downAt;
    if (this.controls) this.controls.autoRotate = false;
    if (this._resumeTimer) window.clearTimeout(this._resumeTimer);
    this._resumeTimer = window.setTimeout(() => {
      if (this.controls && this._autoRotate) this.controls.autoRotate = true;
    }, 5000);
  }

  _resolvePick(object) {
    let o = object;
    while (o) {
      if (o.userData && o.userData.node) return o.userData.node;
      o = o.parent;
    }
    return null;
  }

  _onPointerMove(event) {
    this._lastInteractionAt = typeof performance !== "undefined" ? performance.now() : Date.now();
    if (this._hoverScheduled) return;
    this._hoverScheduled = true;
    window.requestAnimationFrame(() => {
      this._hoverScheduled = false;
      if (!this.sandPoints || !this.onHover) return;
      const rect = this._pointerNDC(event);
      this.raycaster.setFromCamera(this.pointer, this.camera);
      const hits = this.raycaster.intersectObject(this.sandPoints, false);
      if (!hits.length) {
        this.onHover(null);
        return;
      }
      const point = hits[0].point;
      let best = null;
      let bestDist = Infinity;
      this.sandClusters.forEach((cluster) => {
        const c = cluster.center;
        const d = (c.x - point.x) ** 2 + (c.y - point.y) ** 2 + (c.z - point.z) ** 2;
        if (d < bestDist) {
          bestDist = d;
          best = cluster;
        }
      });
      if (best) this.onHover({ cluster: best, x: event.clientX - rect.left, y: event.clientY - rect.top });
    });
  }

  _onPointerLeave() {
    this.onHover?.(null);
  }

  _onClick(event) {
    // Drag / long-press guards — anything that looks like a controlled gesture
    // (long press or > ~8px screen drift) should NOT register as a click. The
    // earlier ~6px threshold was too tight: a noisy trackpad would fire clicks
    // mid-orbit. 64 squared ≈ 8px tolerance, in line with browser defaults.
    if (this._downXY) {
      const dx = event.clientX - this._downXY.x;
      const dy = event.clientY - this._downXY.y;
      if (dx * dx + dy * dy > 64) return;
    }
    const now = typeof performance !== "undefined" ? performance.now() : Date.now();
    if (this._downAt && now - this._downAt > 250) return; // long press = drag intent
    this._pointerNDC(event);
    this.raycaster.setFromCamera(this.pointer, this.camera);
    const hits = this.raycaster.intersectObjects(this.pickables, true);
    if (hits.length) {
      const node = this._resolvePick(hits[0].object);
      if (node) {
        // Single click = SELECT ONLY (cheap, reversible). Focus / drill is
        // reserved for double click (an explicit "open" gesture); this stops
        // an accidental click while orbiting from yanking the camera into a
        // sub-galaxy the user did not ask for.
        this.onSelect?.(node.id);
        return;
      }
    }
    // Empty single click = clear selection, but DO NOT fit() — that camera
    // tween is a big reversible action and should require an explicit double
    // click on empty space (see _onDoubleClick below).
    this.onSelect?.("");
  }

  _onDoubleClick(event) {
    this._pointerNDC(event);
    this.raycaster.setFromCamera(this.pointer, this.camera);
    const hits = this.raycaster.intersectObjects(this.pickables, true);
    if (hits.length) {
      const node = this._resolvePick(hits[0].object);
      if (node) {
        // Double click = explicit drill / open: select then focus, the same
        // big move the legend chips and search results trigger.
        this.onSelect?.(node.id);
        this.focus(node);
        return;
      }
    }
    // Empty double click = framing reset (Fit). Pair with the single-click
    // "select nothing" so the two gestures are: light/reversible vs. heavy.
    this.onSelect?.("");
    this.fit();
  }

  // ---------- loop ----------

  _updateOrbits(t) {
    if (!this._orbitOrder.length) return;
    // Per-frame delta for phase accumulation (so a speed multiplier can change
    // without the body jumping — phase continues smoothly from where it was).
    // Clamped so a pause/resume of orbit motion can't inject a huge jump.
    const dt = this._lastOrbitT == null ? 0 : Math.min(0.1, Math.max(0, t - this._lastOrbitT));
    this._lastOrbitT = t;
    const core = this._livePos.get(this._coreId);
    for (let i = 0; i < this._orbitOrder.length; i += 1) {
      const id = this._orbitOrder[i];
      const o = this._nodeOrbits[id];
      if (!o) continue;
      const center = this._livePos.get(o.parentId) || (core || new THREE.Vector3());
      // Focus-graded speed: tier-3 evidence comets whip at full pace ONLY when the
      // user has selected their owning task; while you're just viewing the goal
      // they slow (~4/14 of full) so the resting subsystem reads as structure, not
      // a swarm. All other orbits keep their baked speed (mult = 1). The phase
      // accumulator makes the speed change seamless (no positional jump).
      let mult = 1;
      if (o.tier === 3) {
        mult = this.selectedId && o.parentId === this.selectedId ? 1 : 0.29;
        // Recency boost — a fresh evidence comet whips faster than a stale one,
        // so a quick scan of the goal reads "what's *moving* right now". The
        // boost only kicks in once we're in focused-task mode (mult > 0); we
        // never let the recency overlay add motion to an evidence subsystem
        // that the overview meant to keep quiet.
        const comet = this._comets && this._comets.get(id);
        if (comet && Number.isFinite(comet.recencyBoost)) {
          mult *= comet.recencyBoost;
        }
      }
      // Archived / paused goals freeze entirely — a dead/dormant sun does not
      // sweep its planets through space. Children inherit because their parent
      // position stops moving anyway; we mute the child speed too so a frozen
      // goal's whole subsystem reads as "history" rather than a ghost swarm.
      const ownerStatus = this._statusById && this._statusById.get(o.parentId);
      if (ownerStatus === "archived" || ownerStatus === "paused") mult = 0;
      const selfStatus = this._statusById && this._statusById.get(id);
      if (selfStatus === "archived" || selfStatus === "paused") mult = 0;
      if (o.phase == null) o.phase = o.baseAngle;
      o.phase += o.speed * mult * dt;
      const ang = o.phase;
      // Match the layout's ellipse: semi-major a, semi-minor b, in-plane swivel,
      // then incline about the X axis by tilt. (Falls back to a circle if only a
      // legacy `radius` is present.)
      const a = Number.isFinite(o.a) ? o.a : Number.isFinite(o.radius) ? o.radius : 0;
      const b = Number.isFinite(o.b) ? o.b : a;
      const cosT = Math.cos(o.tilt || 0);
      const sinT = Math.sin(o.tilt || 0);
      const cosS = Math.cos(o.swivel || 0);
      const sinS = Math.sin(o.swivel || 0);
      const ex = Math.cos(ang) * a;
      const ey = Math.sin(ang) * b;
      const px = ex * cosS - ey * sinS;
      const pz = ex * sinS + ey * cosS;
      const p = this._livePos.get(id);
      if (!p) continue;
      // Lift/lower the orbital plane off the (moving) parent so sibling tiers
      // sharing a parent stay vertically separated as the parent orbits.
      const cy = center.y + (o.centerOffsetY || 0);
      p.set(center.x + px, cy + pz * sinT, center.z + pz * cosT);
      const mesh = this._orbMesh.get(id);
      if (mesh) mesh.position.copy(p);
      const halo = this._orbHalo.get(id);
      if (halo) halo.position.copy(p);
      const evidenceHalo = this._orbHalo.get(`${id}::evidence`);
      if (evidenceHalo) evidenceHalo.position.copy(p);
      // Comet trail: push the new head position, keep the last LEN samples, and
      // write them tail→head into the line buffer so the trail streams behind.
      const comet = this._comets.get(id);
      if (comet) this._advanceComet(comet, p);
      // Keep selection lookups in sync with the moving node.
      const pb = this._posById.get(id);
      if (pb) pb.copy(p);
    }
    // Keep each orbit ring glued under its orbiting nodes: shift the ring by its
    // parent's displacement from the parent's baked (initial) position. Rings whose
    // parent is static (the focused goal, the North Star core) get a zero shift.
    this.linkGroup.children.forEach((line) => {
      const base = line.userData && line.userData.baseCenter;
      const pid = line.userData && line.userData.parentId;
      if (!base || !pid) return;
      const live = this._livePos.get(pid);
      const init = this.nodeById.get(pid);
      if (!live || !init) return;
      line.position.set(
        base.x + (live.x - (init.x || 0)),
        base.y + (live.y - (init.y || 0)),
        base.z + (live.z - (init.z || 0)),
      );
    });
    // Keep each goal progress arc glued to its goal and camera-facing (billboard)
    // so the lit sweep always reads as a flat ring regardless of orbit position.
    if (this._goalArcs.size && this.camera) {
      this._goalArcs.forEach((arc, id) => {
        const live = this._livePos.get(id) || this._posById.get(id);
        if (!live) return;
        arc.group.position.copy(live);
        arc.group.quaternion.copy(this.camera.quaternion);
      });
    }
    // Keep the selected node's label + filaments glued to its moving position.
    if (this.selectedId) this._repositionSelection();
    // Keep the persistent focus labels glued to their orbiting projects.
    if (this._focusLabels.length) this._repositionFocusLabels();
  }

  _animate() {
    this.raf = window.requestAnimationFrame(this._animate);
    // Adaptive frame skipping: when nothing is changing (no camera tween, no
    // hover/select activity, controls idle), throttle to ~6 fps so we stop
    // burning GPU on a static scene. Any interaction lifts us back to 60.
    const now = typeof performance !== "undefined" ? performance.now() : Date.now();
    const userActive = this._lastInteractionAt && (now - this._lastInteractionAt) < 1500;
    const cameraTweening = Boolean(this._cameraTween);
    const idle = !userActive && !cameraTweening && !this.controls?.autoRotate;
    if (idle) {
      if (this._lastIdleRenderAt && now - this._lastIdleRenderAt < 160) {
        return; // skip — ~6 fps idle cap
      }
      this._lastIdleRenderAt = now;
    } else {
      this._lastIdleRenderAt = 0;
    }
    this.frame += 1;
    const t = this.frame / 60;

    // Gentle halo pulse — the galaxy breathes. `vis` is the focus level-of-detail
    // multiplier so dimmed tiers stay dim while still breathing.
    this.glows.forEach(({ sprite, base, baseOpacity, phase, vis }) => {
      const v = vis == null ? 1 : vis;
      const k = 1 + Math.sin(t * 0.8 + phase) * 0.05;
      sprite.scale.set(base * k, base * k, 1);
      sprite.material.opacity = baseOpacity * v * (0.9 + Math.sin(t * 0.8 + phase) * 0.1);
    });
    // Skill halo shimmer.
    if (this.skillField) {
      this.skillField.points.material.uniforms.uPulse.value = 1 + Math.sin(t * 1.1) * 0.08;
    }
    // Slow dust drift.
    if (this.dust) this.dust.rotation.y = t * 0.01;

    // Fade-in shimmer for newly-arrived nodes (resume ingest, etc). Bloom
    // their emissiveIntensity for ~1200ms then settle back to baseline so the
    // user sees what the import added without an indefinite glow.
    if (this._newlyAdded && this._newlyAdded.size && this._newlyAddedAt) {
      const elapsed = now - this._newlyAddedAt;
      const FADE_MS = 1200;
      if (elapsed >= FADE_MS) {
        // Settle: restore baseEmissive once and clear the set.
        this._newlyAdded.forEach((id) => {
          const mesh = this._orbMesh.get(id);
          if (mesh && mesh.material && "emissiveIntensity" in mesh.material) {
            const base = mesh.userData.baseEmissive || 0.62;
            mesh.material.emissiveIntensity = base;
          }
        });
        this._newlyAdded.clear();
        this._newlyAddedAt = 0;
      } else {
        const k = 1 - elapsed / FADE_MS; // 1 → 0
        const boost = 1.6 * k;
        this._newlyAdded.forEach((id) => {
          const mesh = this._orbMesh.get(id);
          if (mesh && mesh.material && "emissiveIntensity" in mesh.material) {
            const base = mesh.userData.baseEmissive || 0.62;
            mesh.material.emissiveIntensity = base * (1 + boost);
          }
        });
        // Keep the loop awake while the animation is running.
        this._lastInteractionAt = now;
      }
    }

    // Live orbital motion: recompute nested positions and move orbs + halos.
    if (this._orbitMotion) this._updateOrbits(t);

    if (this._cameraTween) {
      const tw = this._cameraTween;
      const k = Math.min(1, (this.frame - tw.start) / tw.frames);
      const e = k < 0.5 ? 2 * k * k : 1 - (-2 * k + 2) ** 2 / 2;
      this.camera.position.lerpVectors(tw.fromPos, tw.toPos, e);
      this.controls.target.lerpVectors(tw.fromTarget, tw.toTarget, e);
      if (k >= 1) this._cameraTween = null;
    }

    this.controls?.update();
    // Frame-time sampling: average the last ~30 frames and tune bloom (or
    // skip it outright) when we slip below ~30 fps. The bloom cost is the
    // biggest swing factor on integrated GPUs, so trading bloom strength for
    // FPS is the right knob.
    const renderStart = typeof performance !== "undefined" ? performance.now() : Date.now();
    if (this._adaptiveSkipBloom && this.renderer) {
      this.renderer.render(this.scene, this.camera);
    } else if (this.composer) {
      this.composer.render();
    } else if (this.renderer) {
      this.renderer.render(this.scene, this.camera);
    }
    const renderEnd = typeof performance !== "undefined" ? performance.now() : Date.now();
    const dur = renderEnd - renderStart;
    if (!this._frameTimes) this._frameTimes = [];
    this._frameTimes.push(dur);
    if (this._frameTimes.length > 30) this._frameTimes.shift();
    if (this._frameTimes.length === 30 && this.frame % 60 === 0) {
      const avg = this._frameTimes.reduce((a, b) => a + b, 0) / this._frameTimes.length;
      if (this.bloom) {
        if (avg > 30) {
          this._adaptiveSkipBloom = true;
        } else if (avg > 22) {
          this._adaptiveSkipBloom = false;
          this.bloom.strength = 0.3;
        } else {
          this._adaptiveSkipBloom = false;
          this.bloom.strength = 0.6;
        }
      }
    }
  }

  // ---------- teardown ----------

  _disposeObject(obj) {
    obj.traverse?.((o) => {
      o.geometry?.dispose?.();
      if (Array.isArray(o.material)) o.material.forEach((m) => m.dispose?.());
      else o.material?.dispose?.();
    });
  }

  _clearGroup(group) {
    while (group.children.length) {
      const c = group.children.pop();
      this._disposeObject(c);
      group.remove(c);
    }
  }

  _clearScene() {
    this._clearGroup(this.nodeGroup);
    this._clearGroup(this.haloGroup);
    this._clearGroup(this.linkGroup);
    this._clearGroup(this.trailGroup);
    this._clearGroup(this.selEdgeGroup);
    this._clearGroup(this.labelGroup);
    this._clearGroup(this.focusLabelGroup);
    this._focusLabels = [];
    // fxGroup holds dust (keep) + skill field + sand (rebuild). Remove all but dust.
    const keep = this.dust;
    const survivors = [];
    while (this.fxGroup.children.length) {
      const c = this.fxGroup.children.pop();
      if (c === keep) {
        survivors.push(c);
      } else {
        this._disposeObject(c);
      }
    }
    survivors.forEach((s) => this.fxGroup.add(s));
    this.pickables = [];
    this.glows = [];
    this._orbMesh = new Map();
    this._orbHalo = new Map();
    this._comets = new Map();
    this._goalArcs = new Map();
    this._orbitOrder = [];
    this._childrenByParent = new Map();
    this._coreOrb = null;
    this._coreHalos = [];
    this.skillField = null;
    this._constLines = [];
    this._constLabels = [];
    this.sandPoints = null;
    this.sandClusters = [];
  }

  dispose() {
    window.cancelAnimationFrame(this.raf);
    this.raf = 0;
    if (this._resumeTimer) window.clearTimeout(this._resumeTimer);
    if (this.renderer) {
      this.renderer.domElement.removeEventListener("pointerdown", this._onPointerDown);
      this.renderer.domElement.removeEventListener("pointermove", this._onPointerMove);
      this.renderer.domElement.removeEventListener("pointerleave", this._onPointerLeave);
      this.renderer.domElement.removeEventListener("click", this._onClick);
      this.renderer.domElement.removeEventListener("dblclick", this._onDoubleClick);
    }
    this._clearScene();
    this._clearGroup(this.fxGroup);
    this.controls?.dispose?.();
    this.bloom?.dispose?.();
    this.composer?.dispose?.();
    if (this.renderer) {
      this.renderer.dispose();
      this.renderer.domElement.parentNode?.removeChild(this.renderer.domElement);
    }
    this.renderer = null;
    this.scene = null;
    this.camera = null;
    this.controls = null;
    this.composer = null;
  }
}
