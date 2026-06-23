import { expect, test } from "@playwright/test";

// Closed-loop check that the Project Board homepage embeds the shared evidence
// editor host (Problem 2.3). The section must be reachable even on the normal
// timeline-component path, so this drives the live 18503 UI, expands the
// "Evidence pool" section, and asserts the React editor iframe renders.

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

test("Project Board homepage embeds the evidence editor host", async ({ page }, testInfo) => {
  let response;
  try {
    response = await page.goto(`${baseUrl}/Project_Board`, {
      waitUntil: "domcontentloaded",
      timeout: 30_000,
    });
  } catch {
    test.skip(true, "Run the 18503 Streamlit UI or set NBLANE_STREAMLIT_BASE_URL.");
  }
  if (!response || response.status() >= 400) {
    test.skip(true, "Project Board page unavailable on 18503.");
  }
  await page.waitForLoadState("networkidle", { timeout: 20_000 }).catch(() => {});
  await page.waitForTimeout(3000);
  await ensureDevProfile(page);

  // The "Evidence pool" expander should be present (zh: 证据池).
  const expander = page.getByText(/Evidence pool|证据池/).first();
  await expect(expander).toBeVisible({ timeout: 15_000 });
  await expander.click();
  await page.waitForTimeout(2000);

  // The shared editor renders inside a Streamlit component iframe.
  const frame = await findEditorFrame(page);
  if (!frame) {
    const body = await page.screenshot({ fullPage: true });
    await testInfo.attach("no-editor-frame", { body, contentType: "image/png" });
  }
  expect(frame, "embedded evidence editor iframe should be present").not.toBeNull();
  await expect(frame.locator(".ee-toolbar")).toBeVisible({ timeout: 10_000 });

  const body = await page.screenshot({ fullPage: true });
  await testInfo.attach("project-board-evidence", { body, contentType: "image/png" });
});
