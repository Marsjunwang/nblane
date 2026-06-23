import { expect, test } from "@playwright/test";

const baseUrl =
  process.env.NBLANE_STREAMLIT_BASE_URL || "http://127.0.0.1:18503";

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
      if (a > 24 && (r > 20 || g > 20 || b > 20)) colored += 1;
      if (a > 24) colors.add(`${Math.round(r / 16)}:${Math.round(g / 16)}:${Math.round(b / 16)}`);
    }
    return { colored, alpha, unique: colors.size };
  });
}

test("star-tree 3D view renders with bloom stars and no console errors", async ({ page }, testInfo) => {
  test.setTimeout(120_000);
  const consoleErrors: string[] = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") {
      consoleErrors.push(msg.text());
    }
  });
  page.on("pageerror", (err) => consoleErrors.push(`pageerror: ${err.message}`));

  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(baseUrl, { waitUntil: "domcontentloaded", timeout: 30_000 });
  await page.waitForLoadState("networkidle", { timeout: 20_000 }).catch(() => {});

  const dashboard = await homeDashboardFrame(page);
  await expect(dashboard.locator(".hd-graph-hero")).toBeVisible({ timeout: 30_000 });
  const heroCanvas = dashboard.locator(".hd-graph-hero .hd-graph3d-stage canvas").first();
  await expect(heroCanvas).toBeVisible({ timeout: 25_000 });
  // Let the breathing loop + bloom settle.
  await page.waitForTimeout(2500);

  const stats = await canvasPixelStats(heroCanvas);
  testInfo.annotations.push({ type: "pixelStats", description: JSON.stringify(stats) });
  // Night sky with a colored star tree: many lit pixels, several distinct hues.
  expect(stats.colored).toBeGreaterThan(120);
  expect(stats.unique).toBeGreaterThan(5);

  const shot = await dashboard.locator(".hd-graph-hero .hd-graph3d-stage").screenshot();
  await testInfo.attach("startree-hero", { body: shot, contentType: "image/png" });
  expect(shot.byteLength).toBeGreaterThan(10_000);

  // No JS errors from the rewritten bundle (bloom import, layout, rAF loop).
  const relevant = consoleErrors.filter(
    (text) => !/Streamlit|favicon|net::ERR|websocket|Failed to load resource/i.test(text),
  );
  testInfo.annotations.push({ type: "consoleErrors", description: JSON.stringify(relevant) });
  expect(relevant, relevant.join("\n")).toHaveLength(0);
});
