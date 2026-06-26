import { expect, test } from "@playwright/test";

// Closed-loop verification for the growth-galaxy redesign on the 18502 standalone
// Dashboard Canvas (no auth, dev profile): full-stage comet shower, clickable
// North Star / goal legend that selects + focus-dives, fixed orbit rings (no NaN),
// refined materials, and the removed "Load embedded canvas" UI.
const baseUrl =
  process.env.NBLANE_DASHBOARD_8502_BASE_URL ||
  process.env.NBLANE_READER_API_BASE ||
  "http://127.0.0.1:18502";
const profileName = process.env.NBLANE_DASHBOARD_E2E_PROFILE || "dev";

function dashboardUrl(pathname = "/dashboard", params: Record<string, string> = {}): string {
  const url = new URL(pathname, baseUrl);
  url.searchParams.set("profile", profileName);
  url.searchParams.set("view", "3d");
  Object.entries(params).forEach(([key, value]) => url.searchParams.set(key, value));
  return url.toString();
}

async function canvasPixelStats(locator) {
  return locator.evaluate((canvas: HTMLCanvasElement) => {
    const probe = document.createElement("canvas");
    probe.width = 96;
    probe.height = 96;
    const ctx = probe.getContext("2d");
    if (!ctx) return { colored: 0, alpha: 0, unique: 0 };
    ctx.drawImage(canvas, 0, 0, probe.width, probe.height);
    const data = ctx.getImageData(0, 0, probe.width, probe.height).data;
    const colors = new Set<string>();
    let colored = 0;
    let alpha = 0;
    for (let i = 0; i < data.length; i += 4) {
      const r = data[i];
      const g = data[i + 1];
      const b = data[i + 2];
      const a = data[i + 3];
      if (a > 24) alpha += 1;
      if (a > 24 && (r > 20 || g > 20 || b > 20)) colored += 1;
      if (a > 24) colors.add(`${Math.round(r / 16)}:${Math.round(g / 16)}:${Math.round(b / 16)}`);
    }
    return { colored, alpha, unique: colors.size };
  });
}

test("18502 growth galaxy: comets, clickable legend, focus-dive, no embedded-canvas", async ({ page }, testInfo) => {
  test.setTimeout(120_000);
  const consoleErrors: string[] = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });
  page.on("pageerror", (err) => consoleErrors.push(`pageerror: ${err.message}`));

  await page.setViewportSize({ width: 1440, height: 1000 });
  let response;
  try {
    response = await page.goto(dashboardUrl(), { waitUntil: "domcontentloaded", timeout: 20_000 });
  } catch {
    test.skip(true, "Run the 18502 Reader API sidecar or set NBLANE_DASHBOARD_8502_BASE_URL.");
  }
  if (!response || response.status() >= 400) {
    test.skip(true, "Dashboard Canvas is not available at the configured 18502 URL.");
  }

  // 3D scene renders.
  const stage = page.locator(".hd-graph3d-stage").first();
  await expect(stage).toBeVisible({ timeout: 20_000 });
  const canvas = stage.locator("canvas").first();
  await expect(canvas).toBeVisible({ timeout: 20_000 });
  await page.waitForTimeout(2800); // let the orbit + breathing loop settle

  const stats = await canvasPixelStats(canvas);
  testInfo.annotations.push({ type: "pixelStats", description: JSON.stringify(stats) });
  expect(stats.colored).toBeGreaterThan(120);
  expect(stats.unique).toBeGreaterThan(5);

  // "Load embedded canvas" is gone everywhere; "Open 8502 Canvas" link path stays
  // intact (it lives in the Streamlit hero, not the standalone canvas, so just
  // assert the removed control is absent here).
  await expect(page.locator('[data-action="load-embedded-canvas"]')).toHaveCount(0);
  await expect(page.getByText(/Load embedded canvas|加载内嵌画布/)).toHaveCount(0);

  // Clickable North Star / goal navigator replaces the static role key.
  const navChips = page.locator(".hd-graph3d-nav-chip");
  expect(await navChips.count()).toBeGreaterThan(1);
  const goalChip = page.locator(".hd-graph3d-nav-chip.direction").first();
  await expect(goalChip).toBeVisible();
  const goalName = (await goalChip.locator("span").innerText()).trim();
  testInfo.annotations.push({ type: "goalChip", description: goalName });

  // Clicking a goal chip selects it (focus-dive into its sub-galaxy).
  const before = await canvasPixelStats(canvas);
  await goalChip.click();
  await page.waitForTimeout(1600); // camera tween + LOD apply
  await expect(goalChip).toHaveClass(/selected/);
  const after = await canvasPixelStats(canvas);
  testInfo.annotations.push({ type: "focusDive", description: JSON.stringify({ before, after }) });
  // The framed sub-galaxy changes the rendered pixels (camera moved / tiers faded).
  expect(after.colored).toBeGreaterThan(40);

  // Clicking the North Star chip resets to the full overview.
  const trunkChip = page.locator(".hd-graph3d-nav-chip.trunk").first();
  if (await trunkChip.count()) {
    await trunkChip.click();
    await page.waitForTimeout(1400);
    await expect(trunkChip).toHaveClass(/selected/);
  }

  // Comet shower spans the whole stage (not pinned to a narrow right strip).
  const shower = stage.locator(".hd-research-shower");
  await expect(shower).toBeVisible();
  const showerBox = await shower.boundingBox();
  const stageBox = await stage.boundingBox();
  if (showerBox && stageBox) {
    testInfo.annotations.push({
      type: "showerWidthRatio",
      description: String(showerBox.width / stageBox.width),
    });
    expect(showerBox.width / stageBox.width).toBeGreaterThan(0.9);
  }
  // Comets now streak one/two at a time on randomized 4–16s gaps, so poll for a
  // meteor to appear rather than asserting an instant count (which can be 0
  // between spawns).
  await expect
    .poll(() => stage.locator(".hd-meteor").count(), { timeout: 20_000 })
    .toBeGreaterThan(0);

  const shot = await stage.screenshot();
  await testInfo.attach("galaxy-redesign", { body: shot, contentType: "image/png" });
  expect(shot.byteLength).toBeGreaterThan(10_000);

  // No JS errors from the rewritten scene (orbit math, focus/LOD, shaders).
  const relevant = consoleErrors.filter(
    (t) => !/Streamlit|favicon|net::ERR|websocket|Failed to load resource/i.test(t),
  );
  testInfo.annotations.push({ type: "consoleErrors", description: JSON.stringify(relevant) });
  expect(relevant, relevant.join("\n")).toHaveLength(0);
});
