import { test, expect } from "@playwright/test";

test.setTimeout(90000);

test("dashboard fix plan: scroll to 3D galaxy + verify", async ({ page }) => {
  page.on("console", (msg) => {
    if (msg.type() === "error") {
      console.log("[browser-error]", msg.text());
    }
  });
  await page.goto("http://127.0.0.1:18503", { waitUntil: "networkidle" });
  await page.waitForTimeout(2500);

  const sel = page.locator('[data-testid="stSidebar"] [data-baseweb="select"]').first();
  if (await sel.count()) {
    await sel.click().catch(() => {});
    await page.waitForTimeout(400);
    const opt = page.getByRole("option", { name: /^dev$/ });
    if (await opt.count()) await opt.first().click().catch(() => {});
    await page.waitForLoadState("networkidle", { timeout: 10000 }).catch(() => {});
  }
  await page.waitForTimeout(6000);

  // Find the 3D galaxy iframe and scroll it into view.
  const iframe = page.locator('iframe[title*="home_dashboard"], iframe[src*="home_dashboard_component"]').first();
  if (await iframe.count()) {
    await iframe.scrollIntoViewIfNeeded();
    await page.waitForTimeout(2000);

    // Inside the iframe, find the 3D stage canvas.
    const frame = page.frameLocator('iframe[src*="home_dashboard_component"]').first();
    const stage = frame.locator('.hd-graph3d-stage, canvas').first();
    if (await stage.count()) {
      await stage.scrollIntoViewIfNeeded();
      await page.waitForTimeout(2500);
      await stage.screenshot({ path: "/tmp/dashfix_canvas.png" }).catch(() => {});
    }
  }

  // Full-page screenshot regardless.
  await page.screenshot({ path: "/tmp/dashfix_scrolled.png", fullPage: true });

  // Pull the encoding legend text to confirm it's rendered + collapsed by default.
  const f = page.frameLocator('iframe[src*="home_dashboard_component"]').first();
  const legend = f.locator(".hd-graph3d-encoding-toggle").first();
  const legendCount = await legend.count();
  console.log("legend toggle count:", legendCount);
  if (legendCount) {
    const toggleText = await legend.innerText().catch(() => "");
    console.log("legend toggle text:", toggleText);
    // Expand it.
    await legend.click().catch(() => {});
    await page.waitForTimeout(800);
    const list = f.locator(".hd-graph3d-encoding-list").first();
    if (await list.count()) {
      const items = await list.locator("li").allInnerTexts();
      console.log("legend items:", items);
    }
  }

  // Confirm extinguished chip / archived toggle on rail.
  const archivedToggle = f.locator(".hd-context-archived-toggle").first();
  if (await archivedToggle.count()) {
    const txt = await archivedToggle.innerText().catch(() => "");
    console.log("archived toggle:", txt);
  }
  const extinguishedChip = f.locator(".hd-goal-pill.extinguished").first();
  console.log("extinguished chips on page:", await f.locator(".hd-goal-pill.extinguished").count());
});
