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
async function tryClick(page, locator, label) {
  try { await locator.first().click({ timeout: 4000 }); return true; }
  catch { console.warn(`skip click: ${label}`); return false; }
}

async function nav(page, label) {
  await page.getByRole("link", { name: label, exact: true }).first().click(); await wait(page, 2500);
}

const SCENES = {
  // 1. Home star map: let the 3D scene breathe, sweep the cursor across it.
  async home(page) {
    await page.goto(`${base}/p/demo/home`); await wait(page, 4500);
    await glide(page, 420, 320, 40); await wait(page, 900);
    await glide(page, 760, 420, 40); await wait(page, 900);
    await page.mouse.wheel(0, -300); await wait(page, 1500);
    await glide(page, 940, 300, 40); await wait(page, 1500);
  },
  // 2. Projects -> evidence review -> skill tree.
  async loop(page) {
    await page.goto(`${base}/p/demo/projects`); await wait(page, 3000);
    await page.mouse.wheel(0, 300); await wait(page, 1500);
    await nav(page, "证据");
    await tryClick(page, page.getByText("MVP 上线"), "evidence row"); await wait(page, 2200);
    await tryClick(page, page.getByRole("button", { name: "已入座 8" }), "seated tab"); await wait(page, 1800);
    await nav(page, "技能树");
    await tryClick(page, page.getByText("ROS2 Basics"), "skill"); await wait(page, 2500);
  },
  // 3. Research desk -> reader.
  async research(page) {
    await page.goto(`${base}/p/demo/research`); await wait(page, 3000);
    await tryClick(page, page.getByRole("link", { name: /Embodied Chain-of-Thought/ }), "paper"); await wait(page, 3000);
    await page.goto(`${base}/p/demo/research/papers/${encodeURIComponent("source:research:20261003-001")}/read`); await wait(page, 3500);
    const frame = page.frameLocator("iframe[src*=\"/reader/view/\"]");
    await frame.getByText("对照", { exact: true }).first().waitFor({ timeout: 20000 }).catch(() => console.warn("reader not ready"));
    await wait(page, 2000);
    await tryClick(page, frame.getByText("对照", { exact: true }), "bilingual"); await wait(page, 4000);
    await page.mouse.move(800, 600); await page.mouse.wheel(0, 400); await wait(page, 2500);
    await page.mouse.move(640, 450); await page.mouse.wheel(0, 500); await wait(page, 2500);
  },
  // 4. Content editor -> public site preview.
  async content(page) {
    await page.goto(`${base}/p/demo/content`); await wait(page, 2500);
    await tryClick(page, page.getByRole("link", { name: "Sim2Real 域随机化实践笔记" }), "post"); await wait(page, 3500);
    await page.mouse.move(640, 450); await page.mouse.wheel(0, 400); await wait(page, 2000);
    await nav(page, "公开站点"); await wait(page, 1500);
    await page.mouse.move(1000, 450); await page.mouse.wheel(0, 500); await wait(page, 2500);
  },
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
  const ctx = await newCtx(name);
  const page = await ctx.newPage();
  const t0 = Date.now();
  await SCENES[name](page);
  const video = page.video();
  await ctx.close();
  const src = await video.path();
  fs.renameSync(src, `${outDir}/${name}.webm`);
  console.log(name, "done", ((Date.now() - t0) / 1000).toFixed(1) + "s");
}
await browser.close();
