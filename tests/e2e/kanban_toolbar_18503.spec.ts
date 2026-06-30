import { expect, test } from "@playwright/test";

// Smoke check for the compacted Kanban toolbar: the view toggles, Reload/Save,
// and the Total chip now live INSIDE the React board's sticky toolbar, and the
// old tall Streamlit-side checkbox/button/metric stack is gone.
// Drives the live 18503 UI on the `dev` profile.

const baseUrl =
  process.env.NBLANE_STREAMLIT_BASE_URL || "http://127.0.0.1:18503";

async function ensureDevProfile(page) {
  await page.waitForSelector('[data-testid="stSidebar"]', { timeout: 20_000 });
  await page.waitForSelector('[data-baseweb="select"]', { timeout: 20_000 });
  const sidebar = page.locator('[data-testid="stSidebar"]');
  const text = await sidebar.innerText().catch(() => "");
  if (/Current profile[\s\S]*\bdev\b/.test(text)) return;
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

async function findBoardFrame(page) {
  const deadline = Date.now() + 25_000;
  let frame = null;
  while (Date.now() < deadline && !frame) {
    for (const f of page.frames()) {
      const hit = await f
        .locator(".kb-topbar, .kb-toolbar-controls")
        .count()
        .catch(() => 0);
      if (hit > 0) {
        frame = f;
        break;
      }
    }
    if (!frame) await page.waitForTimeout(1000);
  }
  return frame;
}

test("Kanban toolbar folds toggles, Reload/Save, and Total into the board", async ({ page }, testInfo) => {
  let response;
  try {
    response = await page.goto(`${baseUrl}/Kanban`, {
      waitUntil: "domcontentloaded",
      timeout: 30_000,
    });
  } catch {
    test.skip(true, "Run the 18503 Streamlit UI or set NBLANE_STREAMLIT_BASE_URL.");
  }
  if (!response || response.status() >= 400) {
    test.skip(true, "Kanban page unavailable on 18503.");
  }
  await page.waitForLoadState("networkidle", { timeout: 20_000 }).catch(() => {});
  await page.waitForTimeout(3000);
  await ensureDevProfile(page);

  // The board iframe should render with the new in-toolbar controls.
  const frame = await findBoardFrame(page);
  if (!frame) {
    const body = await page.screenshot({ fullPage: true });
    await testInfo.attach("no-board-frame", { body, contentType: "image/png" });
  }
  expect(frame, "kanban board component iframe should be present").not.toBeNull();

  await expect(frame.locator(".kb-toolbar-controls")).toBeVisible({ timeout: 10_000 });
  // Both view toggles live in the toolbar now.
  await expect(frame.locator('[data-view-pref="auto_dates"]')).toHaveCount(1);
  await expect(frame.locator('[data-view-pref="focus_mode"]')).toHaveCount(1);
  // Reload + Save buttons live in the toolbar.
  await expect(frame.locator("[data-board-reload]")).toBeVisible({ timeout: 8_000 });
  await expect(frame.locator("[data-board-save]")).toBeVisible({ timeout: 8_000 });
  // The compact Total chip is present.
  await expect(frame.locator(".kb-toolbar-meta .kb-count")).toBeVisible({ timeout: 8_000 });

  // Toggling focus mode flips the layout client-side (focus layout appears).
  await frame.locator('[data-view-pref="focus_mode"]').check();
  await expect(frame.locator(".kb-focus-layout")).toBeVisible({ timeout: 8_000 });

  const body = await page.screenshot({ fullPage: true });
  await testInfo.attach("kanban-compact-toolbar", { body, contentType: "image/png" });
});
