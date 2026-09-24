/**
 * Layout audit helper (not a spec — run directly with node):
 *   node tests/e2e/audit_layout.mjs [outDir]
 *
 * Visits every SPA page at 1280×800 / 1440×900 / 1920×1080, records
 * horizontal-overflow + main-column width metrics as JSON, and saves a
 * full-page screenshot per page per viewport for manual review.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "@playwright/test";

const configDir = path.dirname(fileURLToPath(import.meta.url));
const SPA_BASE_URL = (process.env.NBLANE_E2E_SPA_BASE_URL || "http://127.0.0.1:18504").replace(/\/+$/, "");
const PROFILE = process.env.NBLANE_E2E_PROFILE || "dev";
const STORAGE_STATE = path.join(configDir, ".auth", "spa-admin.json");

const PAGES = [
  ["Home", `/p/${PROFILE}/home`],
  ["Kanban", `/p/${PROFILE}/kanban`],
  ["Inbox", `/p/${PROFILE}/inbox`],
  ["Evidence", `/p/${PROFILE}/evidence`],
  ["EvidenceReview", `/p/${PROFILE}/evidence-review`],
  ["Review", `/p/${PROFILE}/review`],
  ["ProjectBoard", `/p/${PROFILE}/project-board`],
  ["Studio", `/p/${PROFILE}/studio`],
  ["Research", `/p/${PROFILE}/research`],
  ["Goals", `/p/${PROFILE}/goals`],
  ["Activity", `/p/${PROFILE}/activity`],
  ["PublicBuild", `/p/${PROFILE}/public-build`],
  ["SkillTree", `/p/${PROFILE}/skill-tree`],
  ["Assistant", `/assistant`],
  ["Profiles", `/`],
];

const VIEWPORTS = [
  { name: "1280x800", width: 1280, height: 800 },
  { name: "1440x900", width: 1440, height: 900 },
  { name: "1920x1080", width: 1920, height: 1080 },
];

const outDir = process.argv[2] || path.join(configDir, "audit-out");
fs.mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch({ args: ["--no-sandbox"] });
const results = [];

for (const viewport of VIEWPORTS) {
  const context = await browser.newContext({
    storageState: STORAGE_STATE,
    viewport: { width: viewport.width, height: viewport.height },
  });
  const page = await context.newPage();
  for (const [name, route] of PAGES) {
    const url = `${SPA_BASE_URL}${route}`;
    const record = { viewport: viewport.name, page: name, url };
    try {
      try {
        await page.goto(url, { waitUntil: "networkidle", timeout: 30_000 });
      } catch {
        // Storm-load retry: networkidle can starve on a loaded box; one more
        // attempt with a plain domcontentloaded + settle wait.
        await page.goto(url, { waitUntil: "domcontentloaded", timeout: 45_000 });
        await page.waitForTimeout(3_000);
      }
      // Give the 3D galaxy / queries a moment to settle; the hero iframe
      // needs the sidecar probe + auth handoff + payload fetch first.
      await page.waitForTimeout(4_000);
      const metrics = await page.evaluate(() => {
        const main = document.querySelector("[class*='AppShell-main']") || document.querySelector("main");
        const mainRect = main ? main.getBoundingClientRect() : null;
        // Widest direct child of the main column (what actually stretches).
        let widestChild = null;
        if (main) {
          let best = 0;
          for (const el of main.querySelectorAll(":scope > *")) {
            const r = el.getBoundingClientRect();
            if (r.width > best) {
              best = r.width;
              widestChild = { tag: el.tagName, cls: String(el.className).slice(0, 80), width: Math.round(r.width) };
            }
          }
        }
        const galaxy = document.querySelector("[data-testid='home-galaxy-hero'] iframe");
        const galaxyCard = document.querySelector("[data-testid='home-galaxy-hero']");
        return {
          innerWidth: window.innerWidth,
          docScrollWidth: document.documentElement.scrollWidth,
          bodyScrollWidth: document.body.scrollWidth,
          mainWidth: mainRect ? Math.round(mainRect.width) : null,
          widestChild,
          galaxyIframe: galaxy
            ? { width: Math.round(galaxy.getBoundingClientRect().width), height: Math.round(galaxy.getBoundingClientRect().height) }
            : null,
          galaxyCardWidth: galaxyCard ? Math.round(galaxyCard.getBoundingClientRect().width) : null,
        };
      });
      Object.assign(record, metrics);
      record.ok = true;
      await page.screenshot({
        path: path.join(outDir, `${name}-${viewport.name}.png`),
        fullPage: true,
      });
    } catch (error) {
      record.ok = false;
      record.error = String(error).slice(0, 200);
    }
    results.push(record);
  }
  await context.close();
}

await browser.close();
fs.writeFileSync(path.join(outDir, "audit.json"), JSON.stringify(results, null, 2));
console.log(JSON.stringify(results, null, 2));
