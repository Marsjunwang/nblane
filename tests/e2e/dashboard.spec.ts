import { expect, test } from "@playwright/test";

// WebGL hero on the Streamlit home dashboard (software GL on this headless
// 2-CPU/3.75GB sandbox). At the tail of a full-suite run — after dozens of
// specs holding Streamlit sessions — session startup + canvas mount can outrun
// the locator budgets (it passes standalone, and after small subsets). One
// scoped retry re-runs the test on an idle machine with a fresh page; do not
// widen this into suite-wide retries.
test.describe.configure({ retries: 1 });

// Targets the Streamlit home dashboard; the URL resolves against the
// configured use.baseURL (see playwright.config.ts).
async function openStreamlitDashboard(page) {
  let response;
  try {
    response = await page.goto("/", {
      waitUntil: "domcontentloaded",
      timeout: 30_000,
    });
  } catch {
    test.skip(true, "Run the Streamlit UI (scripts/dev-web.sh --isolated) or set NBLANE_E2E_BASE_URL.");
  }
  if (!response || response.status() >= 400) {
    test.skip(true, "Dashboard is not available at the configured baseURL.");
  }
  await page.waitForLoadState("networkidle", { timeout: 20_000 }).catch(() => {});
}

async function attachScreenshot(page, name: string, testInfo) {
  const body = await page.screenshot({ fullPage: true });
  await testInfo.attach(name, { body, contentType: "image/png" });
  expect(body.byteLength).toBeGreaterThan(25_000);
}

// The isolated instance's default profile may have an empty graph (no 3D
// canvas in the hero); the seeded `dev` profile carries a full skill tree.
async function ensureDevProfile(page) {
  await page.waitForSelector('[data-testid="stSidebar"]', { timeout: 20_000 });
  await page.waitForSelector('[data-baseweb="select"]', { timeout: 20_000 });
  const sidebar = page.locator('[data-testid="stSidebar"]');
  const text = await sidebar.innerText().catch(() => "");
  if (/当前档案[\s\S]*\bdev\b|Current profile[\s\S]*\bdev\b/.test(text)) return;
  const profileSelect = sidebar.locator('[data-baseweb="select"]').first();
  await profileSelect.click();
  const opt = page.getByRole("option", { name: /^\s*dev\s*$/ }).first();
  if (await opt.count()) {
    await opt.click();
  } else {
    await page.keyboard.type("dev");
    await page.keyboard.press("Enter");
  }
  await page.waitForLoadState("networkidle", { timeout: 20_000 }).catch(() => {});
  await page.waitForTimeout(2500);
}

async function canvasPixelStats(locator) {
  return locator.evaluate((canvas: HTMLCanvasElement) => {
    const probe = document.createElement("canvas");
    probe.width = 96;
    probe.height = 96;
    const ctx = probe.getContext("2d");
    if (!ctx) {
      return { colored: 0, alpha: 0, unique: 0 };
    }
    ctx.drawImage(canvas, 0, 0, probe.width, probe.height);
    const data = ctx.getImageData(0, 0, probe.width, probe.height).data;
    const colors = new Set<string>();
    let colored = 0;
    let alpha = 0;
    for (let index = 0; index < data.length; index += 4) {
      const r = data[index];
      const g = data[index + 1];
      const b = data[index + 2];
      const a = data[index + 3];
      if (a > 24) alpha += 1;
      if (a > 24 && (r < 245 || g < 245 || b < 245)) colored += 1;
      if (a > 24) colors.add(`${Math.round(r / 16)}:${Math.round(g / 16)}:${Math.round(b / 16)}`);
    }
    return { colored, alpha, unique: colors.size };
  });
}

async function homeDashboardFrame(page) {
  for (let attempt = 0; attempt < 80; attempt += 1) {
    for (const frame of page.frames()) {
      if (!frame.url().includes("nblane_home_dashboard")) {
        continue;
      }
      if (await frame.locator(".hd-graph-hero, .hd-canvas-summary, .hd-canvas-embed, .hd-canvas-panel").count()) {
        return frame;
      }
    }
    await page.waitForTimeout(250);
  }
  throw new Error("Home Dashboard component frame did not become ready.");
}

test("Home dashboard exposes top-right guide, AI settings, optional fullscreen galaxy link, and scales", async ({ page }, testInfo) => {
  // This walkthrough (profile switch, goal editor, 3 viewport resizes, 3
  // fullPage screenshots on software GL) intrinsically takes ~2.5-3 min on
  // this box — the old 180s budget left ~15% headroom idle and none under
  // full-suite load (observed: both attempts died late-stage at 180s).
  test.setTimeout(300_000);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await openStreamlitDashboard(page);
  await ensureDevProfile(page);

  await expect(page.locator("body")).toContainText(/Dashboard|仪表盘/);

  const helpButton = page.getByText(/使用说明|Dashboard guide/).first();
  await expect(helpButton).toBeVisible({ timeout: 20_000 });
  await helpButton.click();
  await expect(page.locator("body")).toContainText(/Source|Evidence|Claim|Skill|Output|材料|证据|断言|能力|表达/);

  await page.keyboard.press("Escape").catch(() => {});
  // The unified per-action AI panel (commit f36bdb9) sits behind an "AI"
  // popover (ui key `ai_config_short`, falling back to "AI").
  const aiButton = page.getByRole("button", { name: /^(AI|本页 AI 设置|Dashboard AI)$/ }).first();
  await expect(aiButton).toBeVisible();
  await aiButton.click();
  await expect(page.locator("body")).toContainText(/dashboard\.goal_skill_match|dashboard\.daily_brief|Goal-skill|目标.*技能/);
  await expect(page.locator("body")).toContainText(/LLM model[\s\S]*Codex model|Codex model[\s\S]*LLM model/);
  await expect(page.getByText(/Effective backend[:：]|生效后端/).first()).toBeVisible();
  await expect(page.getByRole("button", { name: /^(Save|保存)$/ }).first()).toBeVisible();
  await page.keyboard.press("Escape").catch(() => {});

  const dashboard = await homeDashboardFrame(page);
  await expect(dashboard.locator('[data-action="open-fullscreen-galaxy"]')).toBeVisible();
  await expect(dashboard.locator(".hd-graph-hero")).toBeVisible();
  await expect(dashboard.locator(".hd-graph-hero .hd-graph3d-stage canvas").first()).toBeVisible({ timeout: 20_000 });
  const heroPixelStats = await canvasPixelStats(dashboard.locator(".hd-graph-hero .hd-graph3d-stage canvas").first());
  expect(heroPixelStats.alpha).toBeGreaterThan(900);
  expect(heroPixelStats.colored).toBeGreaterThan(120);
  expect(heroPixelStats.unique).toBeGreaterThan(6);
  // The in-app hero layout retired the old .hd-workbench section; the hero
  // panel (skill progress, evidence shortcut, today-focus signals) is its
  // semantic successor.
  await expect(dashboard.locator(".hd-workbench")).toHaveCount(0);
  await expect(dashboard.locator(".hd-graph-hero-panel")).toBeVisible();
  expect(await dashboard.locator(".hd-hero-signal").count()).toBeGreaterThan(0);
  // Per-node links out to the standalone canvas were retired; hero nodes are
  // now selected in place via select-node chips (legend nav, goals only).
  const heroNodeChips = dashboard.locator('.hd-graph-hero [data-action="select-node"][data-node-id]');
  if (await heroNodeChips.count()) {
    const firstChip = heroNodeChips.first();
    expect(await firstChip.getAttribute("data-node-id")).toBeTruthy();
    await firstChip.click();
    await expect(firstChip).toHaveAttribute("aria-pressed", "true");
  }
  await expect(dashboard.locator(".hd-canvas-embed")).toHaveCount(0);
  // Goal pills live in the context header now and drive an inline goal editor.
  const goalPills = dashboard.locator('button.hd-goal-pill[data-action="select-goal"]');
  expect(await goalPills.count()).toBeGreaterThan(0);
  const firstGoalPill = goalPills.first();
  await firstGoalPill.click();
  await expect(firstGoalPill).toHaveAttribute("aria-pressed", "true");
  await expect(dashboard.locator('[data-section="goal-editor"]')).toBeVisible();
  await dashboard.locator('[data-action="close-goal-form"]').first().click();
  await expect(dashboard.locator('[data-section="goal-editor"]')).toHaveCount(0);
  expect(await dashboard.locator('[data-action="navigate"]').count()).toBeGreaterThan(2);
  const firstScreenOrder = await dashboard.evaluate(() => {
    const context = document.querySelector(".hd-context-header")?.getBoundingClientRect();
    const hero = document.querySelector(".hd-graph-hero")?.getBoundingClientRect();
    return {
      contextTop: context?.top ?? 0,
      heroTop: hero?.top ?? 0,
    };
  });
  expect(firstScreenOrder.contextTop).toBeLessThan(firstScreenOrder.heroTop);

  await attachScreenshot(page, "dashboard-desktop", testInfo);
  const desktopLayout = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    viewportWidth: window.innerWidth,
  }));
  expect(desktopLayout.scrollWidth).toBeLessThanOrEqual(desktopLayout.viewportWidth + 8);

  await page.setViewportSize({ width: 1280, height: 900 });
  await page.waitForTimeout(500);
  const zoomStressFrame = await homeDashboardFrame(page);
  await expect(zoomStressFrame.locator(".hd-graph-hero .hd-graph3d-stage canvas").first()).toBeVisible({ timeout: 20_000 });
  const zoomStressLayout = await zoomStressFrame.evaluate(() => {
    const hero = document.querySelector(".hd-graph-hero")?.getBoundingClientRect();
    const graph = document.querySelector(".hd-graph-hero .hd-graph3d-stage")?.getBoundingClientRect();
    const panel = document.querySelector(".hd-graph-hero-panel")?.getBoundingClientRect();
    return {
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
      heroHeight: hero?.height || 0,
      graphLeft: graph?.left || 0,
      graphTop: graph?.top || 0,
      graphWidth: graph?.width || 0,
      graphBottom: graph?.bottom || 0,
      panelLeft: panel?.left || 0,
      panelTop: panel?.top || 0,
    };
  });
  expect(zoomStressLayout.scrollWidth).toBeLessThanOrEqual(zoomStressLayout.clientWidth + 8);
  // The hero is a two-column grid down to a 1100px breakpoint, then stacks.
  if (zoomStressLayout.clientWidth > 1104) {
    expect(zoomStressLayout.heroHeight).toBeLessThanOrEqual(820);
    expect(zoomStressLayout.panelLeft).toBeGreaterThan(zoomStressLayout.graphLeft + zoomStressLayout.graphWidth - 4);
  } else {
    // Stacked: the panel sits below the graph and the hero grows past one
    // screen by design (graph stage alone is min-height 560px).
    expect(zoomStressLayout.panelTop).toBeGreaterThanOrEqual(zoomStressLayout.graphBottom - 4);
  }

  await page.setViewportSize({ width: 1024, height: 900 });
  await page.waitForTimeout(500);
  await expect(page.locator("body")).toContainText(/Dashboard|仪表盘/);
  const narrowFrame = await homeDashboardFrame(page);
  const narrowFrameLayout = await narrowFrame.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
    canvasCount: document.querySelectorAll(".hd-graph-hero .hd-graph3d-stage canvas").length,
  }));
  expect(narrowFrameLayout.scrollWidth).toBeLessThanOrEqual(narrowFrameLayout.clientWidth + 8);
  expect(narrowFrameLayout.canvasCount).toBeGreaterThan(0);
  await attachScreenshot(page, "dashboard-scaled-1024", testInfo);
  const scaledLayout = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    viewportWidth: window.innerWidth,
  }));
  expect(scaledLayout.scrollWidth).toBeLessThanOrEqual(scaledLayout.viewportWidth + 8);

  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.waitForTimeout(500);
  // The in-app "load embedded canvas" trigger was retired (the fullscreen
  // galaxy on the sidecar replaced it); embedded/standalone canvas behavior
  // is covered by dashboard_canvas.spec.ts and galaxy_redesign.spec.ts.
  await expect(dashboard.locator('[data-action="load-embedded-canvas"]')).toHaveCount(0);
});
