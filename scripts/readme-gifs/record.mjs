// Record the README demo videos (webm) against the isolated stack.
// Usage: node scripts/readme-gifs/record.mjs <outDir> [scene...]
// Scenes: home loop research content (default: all). See README.md here.
import { chromium } from "@playwright/test";
import fs from "node:fs";

const base = (process.env.NBLANE_DEMO_BASE_URL || "http://127.0.0.1:18504").replace(/\/+$/, "");
const user = process.env.NBLANE_DEMO_USER || "admin";
const password = process.env.NBLANE_DEMO_PASSWORD || "test1234";
const chromiumPath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || (fs.existsSync("/snap/bin/chromium") ? "/snap/bin/chromium" : undefined);
const [outDir = "dist/readme-gifs", ...picked] = process.argv.slice(2);
const W = 1280, H = 800;
const browser = await chromium.launch({ executablePath: chromiumPath, args: ["--no-sandbox"] });

async function newCtx(name) {
  const dir = `${outDir}/raw-${name}`;
  fs.mkdirSync(dir, { recursive: true });
  const ctx = await browser.newContext({ viewport: { width: W, height: H }, recordVideo: { dir, size: { width: W, height: H } } });
  await ctx.request.post(base + "/api/v1/auth/login", { data: { username: user, password } });
  return ctx;
}
const wait = (p, ms) => p.waitForTimeout(ms);
async function glide(page, x, y, steps = 25) { await page.mouse.move(x, y, { steps }); }
// Scroll in small wheel steps so the recording shows motion, not a jump.
async function scroll(page, dy, ms = 900) {
  const steps = Math.max(1, Math.round(ms / 16));
  for (let i = 0; i < steps; i++) { await page.mouse.wheel(0, dy / steps); await page.waitForTimeout(16); }
}
async function tryClick(page, locator, label) {
  try { await locator.first().click({ timeout: 4000 }); return true; }
  catch { console.warn(`skip click: ${label}`); return false; }
}

// Loading gaps [start, end] in seconds since the page opened; to-webp.sh cuts
// them so the clip jumps straight from a click to the rendered page.
let marks = [];
let T0 = 0;
async function until(ready) {
  const start = Date.now();
  await ready();
  const end = Date.now();
  if (end - start > 250) marks.push([(start - T0) / 1000 + 0.15, (end - T0) / 1000]);
}
const visible = (locator) => () => locator.first().waitFor({ state: "visible", timeout: 30000 });
async function nav(page, label, readyText) {
  await page.getByRole("link", { name: label, exact: true }).first().click();
  await until(visible(page.getByText(readyText)));
}

const SCENES = {
  // 1. Home star map. Software WebGL on a GPU-less host renders ~9 fps while
  // a video is recording, so freeze time and screenshot frame by frame:
  // every frame is fully rendered and the motion is evenly spaced.
  home: {
    frames: { fps: 15, seconds: 10 },
    async run(page, shoot) {
      await page.clock.install();
      await page.goto(`${base}/p/demo/home`);
      for (let i = 0; i < 100 && !(await page.locator("canvas").count()); i++) {
        await page.clock.runFor(100); await wait(page, 100);
      }
      await page.clock.runFor(300); await wait(page, 300);
      const path = [[640, 400], [420, 320], [760, 420], [940, 300]];
      await shoot(async (i, n) => {
        const t = (i / (n - 1)) * (path.length - 1);
        const k = Math.min(path.length - 2, Math.floor(t)); const f = t - k;
        await page.mouse.move(path[k][0] + (path[k + 1][0] - path[k][0]) * f, path[k][1] + (path[k + 1][1] - path[k][1]) * f);
        if (i >= Math.round(n * 0.55) && i < Math.round(n * 0.55) + 15) await page.mouse.wheel(0, -20);
      });
    },
  },
  // 2. Projects -> evidence review -> skill tree.
  loop: { async run(page) {
    await page.goto(`${base}/p/demo/projects`);
    await until(visible(page.getByText("真机导航栈")));
    await wait(page, 1000);
    await page.mouse.move(700, 500); await scroll(page, 300); await wait(page, 1200);
    await nav(page, "证据", "MVP 上线"); await wait(page, 800);
    await tryClick(page, page.getByText("MVP 上线"), "evidence row");
    await until(visible(page.getByTestId("evidence-detail"))); await wait(page, 2200);
    await tryClick(page, page.getByRole("button", { name: /已入座/ }), "seated tab");
    await until(visible(page.getByText("感知节点推理延迟优化"))); await wait(page, 1800);
    await nav(page, "技能树", "ROS2 Basics"); await wait(page, 800);
    await tryClick(page, page.getByText("ROS2 Basics"), "skill"); await wait(page, 2800);
  } },
  // 3. Research desk -> paper overview -> reader in side-by-side mode.
  research: { async run(page) {
    await page.goto(`${base}/p/demo/research`);
    await until(visible(page.getByText("阅读队列"))); await wait(page, 1500);
    await tryClick(page, page.getByRole("link", { name: /Embodied Chain-of-Thought/ }), "paper");
    await until(visible(page.getByText("对照阅读"))); await wait(page, 2200);
    await tryClick(page, page.getByRole("link", { name: "对照阅读" }), "compare");
    const frame = page.frameLocator('iframe[src*="/reader/view/"]');
    await until(async () => {
      await page.locator("[data-testid=sidecar-loading]").first().waitFor({ state: "detached", timeout: 30000 }).catch(() => {});
      await frame.locator("canvas").first().waitFor({ state: "visible", timeout: 30000 }).catch(() => console.warn("reader canvas not seen"));
    });
    await wait(page, 2500);
    await page.mouse.move(800, 600); await scroll(page, 400); await wait(page, 1800);
    await page.mouse.move(640, 450); await scroll(page, 500); await wait(page, 2200);
  } },
  // 4. Content editor -> public site preview.
  content: { async run(page) {
    await page.goto(`${base}/p/demo/content`);
    await until(visible(page.getByText("Sim2Real 域随机化实践笔记"))); await wait(page, 1200);
    await tryClick(page, page.getByRole("link", { name: "Sim2Real 域随机化实践笔记" }), "post");
    await until(visible(page.getByText("为什么要做域随机化"))); await wait(page, 1800);
    await page.mouse.move(640, 450); await scroll(page, 400); await wait(page, 1500);
    await nav(page, "公开站点", "网站与自我介绍"); await wait(page, 2000);
    await page.mouse.move(1000, 450); await scroll(page, 500); await wait(page, 2200);
  } },
};

const scenes = picked.length ? picked : Object.keys(SCENES);
const unknown = scenes.filter((n) => !SCENES[n]);
if (unknown.length) throw new Error(`unknown scene(s): ${unknown.join(", ")}`);
if (scenes.includes("research")) {
  // Warm the reader (page previews, translations) outside the recording.
  const warm = await browser.newContext({ viewport: { width: W, height: H } });
  await warm.request.post(base + "/api/v1/auth/login", { data: { username: user, password } });
  const wp = await warm.newPage();
  await wp.goto(`${base}/p/demo/research/papers/${encodeURIComponent("source:research:20261003-001")}/read`);
  await wp.waitForTimeout(12000); await warm.close();
}
for (const name of scenes) {
  const scene = SCENES[name];
  const t0 = Date.now();
  if (scene.frames) {
    const dir = `${outDir}/frames-${name}`;
    fs.rmSync(dir, { recursive: true, force: true });
    fs.mkdirSync(dir, { recursive: true });
    const ctx = await browser.newContext({ viewport: { width: W, height: H } });
    await ctx.request.post(base + "/api/v1/auth/login", { data: { username: user, password } });
    const page = await ctx.newPage();
    const { fps, seconds } = scene.frames;
    const n = Math.round(fps * seconds);
    await scene.run(page, async (onFrame) => {
      for (let i = 0; i < n; i++) {
        await onFrame(i, n);
        await page.clock.runFor(1000 / fps);
        await page.screenshot({ path: `${dir}/f${String(i).padStart(4, "0")}.png` });
      }
    });
    await ctx.close();
    console.log(name, `${n} frames @${fps}fps`, ((Date.now() - t0) / 1000).toFixed(1) + "s");
    continue;
  }
  const ctx = await newCtx(name);
  const page = await ctx.newPage();
  marks = []; T0 = Date.now();
  await scene.run(page);
  fs.writeFileSync(`${outDir}/${name}.cuts.json`, JSON.stringify(marks.map(([a, b]) => [+a.toFixed(2), +b.toFixed(2)])));
  const video = page.video();
  await ctx.close();
  fs.renameSync(await video.path(), `${outDir}/${name}.webm`);
  console.log(name, "done", ((Date.now() - t0) / 1000).toFixed(1) + "s", "cuts", JSON.stringify(marks.map(([a, b]) => `${a.toFixed(1)}-${b.toFixed(1)}`)));
}
await browser.close();
