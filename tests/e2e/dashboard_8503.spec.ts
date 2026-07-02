import { expect, test } from "@playwright/test";

const baseUrl =
  process.env.NBLANE_DASHBOARD_8503_BASE_URL ||
  process.env.NBLANE_STREAMLIT_BASE_URL ||
  "http://127.0.0.1:8503";

async function openStreamlitDashboard(page) {
  let response;
  try {
    response = await page.goto(baseUrl, {
      waitUntil: "domcontentloaded",
      timeout: 30_000,
    });
  } catch {
    test.skip(true, "Run the 8503 Streamlit dashboard or set NBLANE_DASHBOARD_8503_BASE_URL.");
  }
  if (!response || response.status() >= 400) {
    test.skip(true, "Dashboard is not available at the configured 8503 URL.");
  }
  await page.waitForLoadState("networkidle", { timeout: 20_000 }).catch(() => {});
}

async function attachScreenshot(page, name: string, testInfo) {
  const body = await page.screenshot({ fullPage: true });
  await testInfo.attach(name, { body, contentType: "image/png" });
  expect(body.byteLength).toBeGreaterThan(25_000);
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

async function canvasBitmapSnapshot(locator) {
  const dataUrl = await locator.evaluate((canvas: HTMLCanvasElement) => canvas.toDataURL("image/png"));
  const encoded = dataUrl.split(",", 2)[1] || "";
  const body = Buffer.from(encoded, "base64");
  expect(body.byteLength).toBeGreaterThan(1000);
  return body;
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

async function embeddedDashboardCanvasFrame(page) {
  for (let attempt = 0; attempt < 100; attempt += 1) {
    for (const frame of page.frames()) {
      const url = frame.url();
      if (!url.includes("/dashboard") || !url.includes("embed=1")) {
        continue;
      }
      if (await frame.locator(".hd-canvas-panel").count()) {
        return frame;
      }
    }
    await page.waitForTimeout(250);
  }
  throw new Error("Embedded 8502 Dashboard Canvas frame did not become ready.");
}

test("8503 Dashboard exposes top-right guide, AI settings, optional fullscreen galaxy link, and scales", async ({ page }, testInfo) => {
  test.setTimeout(180_000);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await openStreamlitDashboard(page);

  await expect(page.locator("body")).toContainText(/Dashboard|仪表盘/);

  const helpButton = page.getByText(/使用说明|Dashboard guide/).first();
  await expect(helpButton).toBeVisible({ timeout: 20_000 });
  await helpButton.click();
  await expect(page.locator("body")).toContainText(/Source|Evidence|Claim|Skill|Output|材料|证据|断言|能力|表达/);

  await page.keyboard.press("Escape").catch(() => {});
  const aiButton = page.getByRole("button", { name: /本页 AI 设置|Dashboard AI|AI 设置|AI settings/ }).first();
  await expect(aiButton).toBeVisible();
  await aiButton.click();
  await expect(page.locator("body")).toContainText(/Goal-skill|目标.*能力|Backend|后端|模型|Model/);
  await expect(page.locator("body")).toContainText(/LLM[:：][\s\S]*Codex[:：]|Codex[:：][\s\S]*LLM[:：]/);
  await expect(page.getByRole("button", { name: /测试模型|Test model/ }).first()).toBeVisible();

  await expect(page.getByText(/打开全屏星系|Open Fullscreen Galaxy/).first()).toBeVisible();

  const dashboard = await homeDashboardFrame(page);
  await expect(dashboard.locator(".hd-graph-hero")).toBeVisible();
  await expect(dashboard.locator(".hd-graph-hero .hd-graph3d-stage canvas").first()).toBeVisible({ timeout: 20_000 });
  const heroPixelStats = await canvasPixelStats(dashboard.locator(".hd-graph-hero .hd-graph3d-stage canvas").first());
  expect(heroPixelStats.alpha).toBeGreaterThan(900);
  expect(heroPixelStats.colored).toBeGreaterThan(120);
  expect(heroPixelStats.unique).toBeGreaterThan(6);
  await expect(dashboard.locator(".hd-workbench")).toBeVisible();
  const workbenchOverlap = await dashboard.evaluate(() => {
    const quick = document.querySelector(".hd-workbench-quick")?.getBoundingClientRect();
    const health = document.querySelector(".hd-workbench-health")?.getBoundingClientRect();
    const overlaps = Boolean(
      quick &&
      health &&
      quick.left < health.right &&
      quick.right > health.left &&
      quick.top < health.bottom &&
      quick.bottom > health.top
    );
    return {
      overlaps,
      quickTop: quick?.top || 0,
      healthTop: health?.top || 0,
    };
  });
  expect(workbenchOverlap.overlaps).toBeFalsy();
  const summaryNodeLinks = dashboard.locator('.hd-graph-hero [data-action="open-8502-node"]');
  if (await summaryNodeLinks.count()) {
    const firstSummaryHref = await summaryNodeLinks.first().getAttribute("href");
    expect(firstSummaryHref || "").toContain("view=3d");
    expect(firstSummaryHref || "").toContain("node=");
  }
  await expect(dashboard.locator(".hd-canvas-embed")).toHaveCount(0);
  await expect(dashboard.locator('[data-action="open-goal-form"]')).toHaveCount(0);
  await expect(dashboard.locator("button.hd-goal-pill")).toHaveCount(0);
  expect(await dashboard.locator('[data-action="navigate"]').count()).toBeGreaterThan(6);
  const firstScreenOrder = await dashboard.evaluate(() => {
    const context = document.querySelector(".hd-context-header")?.getBoundingClientRect();
    const hero = document.querySelector(".hd-graph-hero")?.getBoundingClientRect();
    const workbench = document.querySelector(".hd-workbench")?.getBoundingClientRect();
    return {
      contextTop: context?.top ?? 0,
      heroTop: hero?.top ?? 0,
      workbenchTop: workbench?.top ?? 0,
    };
  });
  expect(firstScreenOrder.contextTop).toBeLessThan(firstScreenOrder.heroTop);
  expect(firstScreenOrder.heroTop).toBeLessThan(firstScreenOrder.workbenchTop);

  await attachScreenshot(page, "dashboard-8503-desktop", testInfo);
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
      panelLeft: panel?.left || 0,
      graphWidth: graph?.width || 0,
    };
  });
  expect(zoomStressLayout.scrollWidth).toBeLessThanOrEqual(zoomStressLayout.clientWidth + 8);
  expect(zoomStressLayout.heroHeight).toBeLessThanOrEqual(760);
  expect(zoomStressLayout.panelLeft).toBeGreaterThan(zoomStressLayout.graphLeft + zoomStressLayout.graphWidth - 4);

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
  await attachScreenshot(page, "dashboard-8503-scaled-1024", testInfo);
  const scaledLayout = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    viewportWidth: window.innerWidth,
  }));
  expect(scaledLayout.scrollWidth).toBeLessThanOrEqual(scaledLayout.viewportWidth + 8);

  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.waitForTimeout(500);
  if (await dashboard.locator('[data-action="load-embedded-canvas"]').count()) {
    await dashboard.locator('[data-action="load-embedded-canvas"]').click();
    await expect(dashboard.locator(".hd-canvas-embed iframe")).toBeVisible();

    const canvasFrame = await embeddedDashboardCanvasFrame(page);
    await expect(canvasFrame.locator('[data-action="view-toggle"][data-view="focus"]')).toHaveClass(/active/);
    await expect(canvasFrame.locator(".hd-focus-path")).toBeVisible();
    expect(await canvasFrame.locator(".hd-focus-node").count()).toBeGreaterThan(3);
    expect(await canvasFrame.locator('[data-action="select-node"][data-source="focus-path"]').count()).toBeGreaterThan(3);
    await canvasFrame.getByRole("button", { name: /3D Graph|3D 全局图/ }).click();
    await expect(canvasFrame.locator('[data-action="view-toggle"][data-view="3d"]')).toHaveClass(/active/);
    await expect(canvasFrame.locator(".hd-explore-canvas")).toBeVisible();
    await expect(canvasFrame.locator(".hd-graph3d-stage")).toBeVisible();
    await expect(canvasFrame.locator(".hd-graph3d-stage canvas").first()).toBeVisible({ timeout: 20_000 });
    await expect(canvasFrame.locator(".hd-explore-panel")).toBeVisible();
    await expect(canvasFrame.locator(".hd-explore-list button").first()).toBeVisible();
    const graphLayout = await canvasFrame.locator(".hd-explore-canvas").evaluate((element) => {
      return {
        scrollWidth: element.scrollWidth,
        clientWidth: element.clientWidth,
        scrollHeight: element.scrollHeight,
        clientHeight: element.clientHeight,
        graphCanvases: element.querySelectorAll(".hd-graph3d-stage canvas").length,
        exploreButtons: element.querySelectorAll(".hd-explore-list button").length,
        legendItems: element.querySelectorAll(".hd-graph3d-legend span").length,
      };
    });
    expect(graphLayout.graphCanvases).toBeGreaterThan(0);
    expect(graphLayout.exploreButtons).toBeGreaterThan(8);
    expect(graphLayout.legendItems).toBeGreaterThan(6);
    expect(graphLayout.scrollWidth).toBeLessThanOrEqual(graphLayout.clientWidth + 4);
    expect(graphLayout.scrollHeight).toBeLessThanOrEqual(graphLayout.clientHeight + 280);
    const pixelStats = await canvasPixelStats(canvasFrame.locator(".hd-graph3d-stage canvas").first());
    expect(pixelStats.alpha).toBeGreaterThan(900);
    expect(pixelStats.colored).toBeGreaterThan(140);
    expect(pixelStats.unique).toBeGreaterThan(7);
    const canvas = canvasFrame.locator(".hd-graph3d-stage canvas").first();
    const canvasBox = await canvas.boundingBox();
    expect(canvasBox?.width || 0).toBeGreaterThan(280);
    expect(canvasBox?.height || 0).toBeGreaterThan(460);
    const beforeDrag = await canvasBitmapSnapshot(canvas);
    await page.mouse.move((canvasBox?.x || 0) + (canvasBox?.width || 0) / 2, (canvasBox?.y || 0) + (canvasBox?.height || 0) / 2);
    await page.mouse.down();
    await page.mouse.move((canvasBox?.x || 0) + (canvasBox?.width || 0) / 2 + 130, (canvasBox?.y || 0) + (canvasBox?.height || 0) / 2 - 70, { steps: 12 });
    await page.mouse.up();
    await page.waitForTimeout(600);
    const afterDrag = await canvasBitmapSnapshot(canvas);
    await page.mouse.wheel(0, -650);
    await page.waitForTimeout(500);
    const afterZoom = await canvasBitmapSnapshot(canvas);
    expect(Buffer.compare(beforeDrag, afterDrag)).not.toBe(0);
    expect(Buffer.compare(afterDrag, afterZoom)).not.toBe(0);

    const graphShot = await canvasFrame.locator(".hd-explore-canvas").screenshot();
    await testInfo.attach("dashboard-8503-3d-graph", { body: graphShot, contentType: "image/png" });
    expect(graphShot.byteLength).toBeGreaterThan(18_000);
  }
});
