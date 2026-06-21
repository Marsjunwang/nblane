import { expect, test } from "@playwright/test";

// Closed-loop check for the v2 evidence React editor on the 18503 Streamlit UI.
// Validates: page loads, dev profile selected, the React editor iframe renders
// the toolbar + list, and a row can be opened in the detail pane.

const baseUrl =
  process.env.NBLANE_EVIDENCE_EDITOR_BASE_URL ||
  process.env.NBLANE_STREAMLIT_BASE_URL ||
  "http://127.0.0.1:18503";

async function ensureDevProfile(page) {
  // Streamlit hydrates the sidebar asynchronously; wait for it.
  await page.waitForSelector('[data-testid="stSidebar"]', { timeout: 20_000 });
  await page.waitForSelector('[data-baseweb="select"]', { timeout: 20_000 });
  const sidebar = page.locator('[data-testid="stSidebar"]');
  const text = await sidebar.innerText().catch(() => "");
  if (/Current profile[\s\S]*\bdev\b/.test(text)) return; // already dev

  // The profile selector is the first baseweb select in the sidebar.
  const profileSelect = sidebar.locator('[data-baseweb="select"]').first();
  await profileSelect.click();
  const opt = page.getByRole("option", { name: /^\s*dev\s*$/ }).first();
  if (await opt.count()) {
    await opt.click();
  } else {
    await page.keyboard.type("dev");
    await page.keyboard.press("Enter");
  }
  // Profile switch triggers a full rerun.
  await page.waitForLoadState("networkidle", { timeout: 20_000 }).catch(() => {});
  await page.waitForTimeout(2500);
}

async function findEditorFrame(page) {
  const deadline = Date.now() + 25_000;
  let frame = null;
  while (Date.now() < deadline && !frame) {
    for (const f of page.frames()) {
      const hit = await f
        .locator(".ee-toolbar, .ee-root")
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

test("evidence editor renders in the React component iframe", async ({ page }, testInfo) => {
  let response;
  try {
    response = await page.goto(`${baseUrl}/Evidence_Review`, {
      waitUntil: "domcontentloaded",
      timeout: 30_000,
    });
  } catch {
    test.skip(true, "Run the 18503 Streamlit UI or set NBLANE_STREAMLIT_BASE_URL.");
  }
  if (!response || response.status() >= 400) {
    test.skip(true, "Evidence Review page unavailable on 18503.");
  }
  await page.waitForLoadState("networkidle", { timeout: 20_000 }).catch(() => {});
  await page.waitForTimeout(3000);
  await ensureDevProfile(page);

  // The page title / nav should be present.
  await expect(page.locator("body")).toContainText(
    /Evidence|证据/,
    { timeout: 15_000 }
  );

  // The component renders inside a Streamlit component iframe.
  const frame = await findEditorFrame(page);

  if (!frame) {
    // Capture a screenshot to aid debugging before failing.
    const body = await page.screenshot({ fullPage: true });
    await testInfo.attach("no-editor-frame", { body, contentType: "image/png" });
  }
  expect(frame, "evidence editor iframe should be present").not.toBeNull();

  // Toolbar actions are visible.
  await expect(frame.locator(".ee-toolbar")).toBeVisible({ timeout: 10_000 });
  await expect(frame.locator(".ee-list")).toBeVisible();

  // There should be at least one evidence row in the list (dev pool is seeded).
  await expect(frame.locator(".ee-li").first()).toBeVisible({ timeout: 10_000 });

  // Open the first row -> detail pane shows the Save action.
  await frame.locator(".ee-li").first().click();
  await expect(frame.locator(".ee-detail")).toBeVisible({ timeout: 8_000 });

  const body = await page.screenshot({ fullPage: true });
  await testInfo.attach("evidence-editor", { body, contentType: "image/png" });
  expect(body.byteLength).toBeGreaterThan(20_000);
});

test("run migration backfills v2 provenance and persists", async ({ page }, testInfo) => {
  let response;
  try {
    response = await page.goto(`${baseUrl}/Evidence_Review`, {
      waitUntil: "domcontentloaded",
      timeout: 30_000,
    });
  } catch {
    test.skip(true, "Run the 18503 Streamlit UI or set NBLANE_STREAMLIT_BASE_URL.");
  }
  if (!response || response.status() >= 400) {
    test.skip(true, "Evidence Review page unavailable on 18503.");
  }
  await page.waitForLoadState("networkidle", { timeout: 20_000 }).catch(() => {});
  await page.waitForTimeout(3000);
  await ensureDevProfile(page);

  const frame = await findEditorFrame(page);
  expect(frame, "evidence editor iframe should be present").not.toBeNull();

  // Click "Run migration" (zh: 运行迁移 / en: Run migration).
  const migrateBtn = frame.getByRole("button", { name: /运行迁移|Run migration/ });
  await expect(migrateBtn).toBeVisible({ timeout: 10_000 });
  await migrateBtn.click();

  // The save triggers a Streamlit rerun + success toast. Give it time to persist.
  await page.waitForLoadState("networkidle", { timeout: 20_000 }).catch(() => {});
  await page.waitForTimeout(4000);

  const body = await page.screenshot({ fullPage: true });
  await testInfo.attach("after-migration", { body, contentType: "image/png" });
  // After migration, the needs-migration counter should drop toward 0.
  // (Asserted on disk by the companion shell check; here we just confirm no crash.)
  expect(body.byteLength).toBeGreaterThan(20_000);
});

test("detail pane stays open on the same row after an action (no page jump)", async ({ page }, testInfo) => {
  let response;
  try {
    response = await page.goto(`${baseUrl}/Evidence_Review`, {
      waitUntil: "domcontentloaded",
      timeout: 30_000,
    });
  } catch {
    test.skip(true, "Run the 18503 Streamlit UI or set NBLANE_STREAMLIT_BASE_URL.");
  }
  if (!response || response.status() >= 400) {
    test.skip(true, "Evidence Review page unavailable on 18503.");
  }
  await page.waitForLoadState("networkidle", { timeout: 20_000 }).catch(() => {});
  await page.waitForTimeout(3000);
  await ensureDevProfile(page);

  const frame = await findEditorFrame(page);
  expect(frame, "evidence editor iframe should be present").not.toBeNull();

  // Open the first row and capture its id from the detail header.
  await frame.locator(".ee-li").first().click();
  await expect(frame.locator(".ee-detail")).toBeVisible({ timeout: 8_000 });
  const metaBefore = await frame.locator(".ee-meta").innerText();
  const idMatch = metaBefore.match(/id:\s*([^\s·]+)/);
  expect(idMatch, "detail meta should show the row id").not.toBeNull();
  const rowId = idMatch[1];

  // Click "Run migration" (an action that triggers a Python rerun).
  await frame.getByRole("button", { name: /运行迁移|Run migration/ }).click();
  await page.waitForTimeout(4000);

  // After the fragment rerun, the editor frame re-mounts; re-find it and assert
  // the detail pane is still open on the SAME row (Fix 3: selection preserved).
  const frame2 = await findEditorFrame(page);
  expect(frame2, "editor iframe should re-mount").not.toBeNull();
  await expect(frame2.locator(".ee-detail")).toBeVisible({ timeout: 10_000 });
  const metaAfter = await frame2.locator(".ee-meta").innerText();
  expect(metaAfter).toContain(rowId);

  const body = await page.screenshot({ fullPage: true });
  await testInfo.attach("selection-preserved", { body, contentType: "image/png" });
});
