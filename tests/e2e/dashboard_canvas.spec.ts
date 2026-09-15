import { expect, test } from "@playwright/test";
import { readerBaseURL } from "./helpers";

// Standalone Dashboard Canvas is served by the Reader API sidecar.
const baseUrl = readerBaseURL();
const profileName = process.env.NBLANE_DASHBOARD_E2E_PROFILE || "template";

function dashboardUrl(pathname = "/dashboard", params: Record<string, string> = {}): string {
  const url = new URL(pathname, baseUrl);
  url.searchParams.set("profile", profileName);
  Object.entries(params).forEach(([key, value]) => url.searchParams.set(key, value));
  return url.toString();
}

async function openDashboardCanvas(page) {
  let response;
  try {
    response = await page.goto(dashboardUrl(), {
      waitUntil: "domcontentloaded",
      timeout: 20_000,
    });
  } catch {
    test.skip(true, "Run the Reader API sidecar (scripts/dev-web.sh --isolated) or set NBLANE_E2E_READER_BASE.");
  }
  if (!response || response.status() >= 400) {
    test.skip(true, "Dashboard Canvas is not available at the configured sidecar URL.");
  }
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

test("Standalone Dashboard Canvas renders the 3D graph, attention, and inspector", async ({ page }, testInfo) => {
  test.setTimeout(240_000);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await openDashboardCanvas(page);

  await expect(page.getByRole("heading", { name: "Dashboard Canvas" })).toBeVisible();
  await expect(page.getByRole("button", { name: /Add goal|添加目标|\+ Active Goal/ })).toHaveCount(0);
  await expect(page.getByRole("button", { name: /Save goal|保存目标/ })).toHaveCount(0);
  await expect(page.locator('[data-action="capture-source"]')).toHaveCount(0);
  await expect(page.locator('[data-action="archive-goal"]')).toHaveCount(0);
  await expect(page.locator(".hd-graph3d-stage")).toBeVisible();
  await expect(page.locator(".hd-graph3d-stage canvas").first()).toBeVisible({ timeout: 20_000 });
  // The standalone page keeps the inspector as an on-demand drawer: it is
  // closed by default and opens when a node is selected.
  await expect(page.locator(".hd-inspector")).toHaveCount(0);
  await expect(page.locator('[data-action="view-toggle"][data-view="3d"]')).toHaveClass(/active/);
  // On the fullbleed standalone page only the legend chips carry select-node;
  // the explore list lives in the embed variant (exercised below).
  const legendChips = page.locator('[data-action="select-node"][data-source="graph-legend"]');
  expect(await legendChips.count()).toBeGreaterThan(1);

  const apiResponse = await page.request.get(dashboardUrl("/api/dashboard/payload"));
  expect(apiResponse.ok()).toBeTruthy();
  const apiPayload = await apiResponse.json();
  expect(apiPayload.ok).toBeTruthy();
  expect(apiPayload.payload.graph.schema_version).toBe("1.1");
  expect(apiPayload.payload.graph.contract.layers.length).toBeGreaterThan(5);
  expect(apiPayload.payload.graph.contract.node_types.length).toBeGreaterThan(10);
  expect(apiPayload.payload.graph.focus_path.length).toBeGreaterThan(3);
  expect(apiPayload.payload.graph.nodes.length).toBeGreaterThan(15);
  expect(apiPayload.payload.graph.edges.length).toBeGreaterThan(20);

  // Selecting a legend node opens the on-demand inspector drawer.
  const trunkChip = page.locator(".hd-graph3d-nav-chip.trunk").first();
  await expect(trunkChip).toBeVisible();
  const trunkLabel = (await trunkChip.locator("span").innerText()).trim();
  await trunkChip.click();
  await expect(trunkChip).toHaveClass(/selected/);
  await expect(page.locator(".hd-drawer-root")).toBeVisible();
  await expect(page.locator(".hd-inspector")).toContainText(trunkLabel);
  await page.keyboard.press("Escape");
  await expect(page.locator(".hd-drawer-root")).toHaveCount(0);

  // The embed variant keeps the explore panel: search, placeholder toggle and
  // an inline (always rendered) inspector.
  await page.goto(dashboardUrl("/dashboard", { embed: "1", view: "3d" }), {
    waitUntil: "domcontentloaded",
    timeout: 20_000,
  });
  await expect(page.locator('[data-action="view-toggle"][data-view="3d"]')).toHaveClass(/active/);
  const listNodes = page.locator(".hd-explore-list button");
  await expect(listNodes.first()).toBeVisible({ timeout: 15_000 });
  expect(await listNodes.count()).toBeGreaterThan(8);
  await expect(page.locator('[data-action="explore-search"]')).toBeVisible();
  await expect(page.locator('[data-action="hide-placeholders"]')).toBeVisible();
  expect(await page.locator(".hd-explore-group").count()).toBeGreaterThan(2);
  const secondNodeLabel = (await listNodes.nth(1).locator("strong").innerText()).trim();
  await listNodes.nth(1).click();
  await expect(page.locator(".hd-inspector")).toContainText(secondNodeLabel);
  await page.locator('[data-action="explore-search"]').fill("source:");
  expect(await page.locator(".hd-explore-list button").count()).toBeGreaterThan(0);
  await page.locator('[data-action="hide-placeholders"]').check();
  await expect(page.locator(".hd-explore-list button.placeholder")).toHaveCount(0);
  await page.locator('[data-action="explore-search"]').fill("");
  await page.locator('[data-action="hide-placeholders"]').uncheck();
  expect(await page.locator(".hd-explore-list button").count()).toBeGreaterThan(8);
  const embedInspectorText = (await page.locator(".hd-inspector").textContent()) || "";
  expect(embedInspectorText.length).toBeGreaterThan(20);

  // Back to the standalone fullbleed page for the canvas/layout assertions.
  await page.goto(dashboardUrl("/dashboard", { view: "3d" }), {
    waitUntil: "domcontentloaded",
    timeout: 20_000,
  });
  await expect(page.locator(".hd-graph3d-stage canvas").first()).toBeVisible({ timeout: 20_000 });
  await page.waitForTimeout(2500); // let the orbit + breathing loop settle
  const stats = await canvasPixelStats(page.locator(".hd-graph3d-stage canvas").first());
  expect(stats.alpha).toBeGreaterThan(900);
  expect(stats.colored).toBeGreaterThan(160);
  expect(stats.unique).toBeGreaterThan(8);

  const layout = await page.evaluate(() => ({
    graphCanvasCount: document.querySelectorAll(".hd-graph3d-stage canvas").length,
    scrollWidth: document.documentElement.scrollWidth,
    viewportWidth: window.innerWidth,
  }));
  expect(layout.graphCanvasCount).toBeGreaterThan(0);
  expect(layout.scrollWidth).toBeLessThanOrEqual(layout.viewportWidth + 4);

  const body = await page.screenshot({ fullPage: true });
  await testInfo.attach("dashboard-canvas-desktop", { body, contentType: "image/png" });
  expect(body.byteLength).toBeGreaterThan(20_000);

  await page.goto(dashboardUrl("/dashboard", { view: "3d", node: "source:inbox" }), {
    waitUntil: "domcontentloaded",
    timeout: 20_000,
  });
  // The deep-linked node is selected on load and opens the inspector drawer.
  await expect(page.locator(".hd-drawer-root")).toBeVisible({ timeout: 15_000 });
  await expect(page.locator(".hd-inspector")).toContainText(/Source inbox|来源收件箱|Inbox sources/);

  await page.setViewportSize({ width: 390, height: 820 });
  await page.goto(dashboardUrl(), {
    waitUntil: "domcontentloaded",
    timeout: 20_000,
  });
  await expect(page.getByRole("heading", { name: "Dashboard Canvas" })).toBeVisible();
  await expect(page.locator(".hd-graph3d-stage canvas").first()).toBeVisible({ timeout: 20_000 });
  await page.waitForTimeout(2500); // let the render loop settle before readback
  const mobileLayout = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    viewportWidth: window.innerWidth,
    chipCount: document.querySelectorAll('[data-action="select-node"][data-source="graph-legend"]').length,
  }));
  expect(mobileLayout.chipCount).toBeGreaterThan(1);
  expect(mobileLayout.scrollWidth).toBeLessThanOrEqual(mobileLayout.viewportWidth + 4);
  const mobileStats = await canvasPixelStats(page.locator(".hd-graph3d-stage canvas").first());
  expect(mobileStats.colored).toBeGreaterThan(120);
  expect(mobileStats.unique).toBeGreaterThan(6);
  const mobileBody = await page.screenshot({ fullPage: true });
  await testInfo.attach("dashboard-canvas-mobile", { body: mobileBody, contentType: "image/png" });
  expect(mobileBody.byteLength).toBeGreaterThan(18_000);
});
