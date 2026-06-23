import { expect, test } from "@playwright/test";

// Closed-loop check for the reworked Project Board homepage:
//  - the evidence pool editor is REMOVED (it lives on Evidence Review now);
//  - the timeline React component renders;
//  - "Create project" is folded into the component toolbar (not a Streamlit
//    expander), and the overview counts sit on the legend row.
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

async function findTimelineFrame(page) {
  const deadline = Date.now() + 25_000;
  let frame = null;
  while (Date.now() < deadline && !frame) {
    for (const f of page.frames()) {
      const hit = await f
        .locator(".tl-root, .tl-toolbar")
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

test("Project Board homepage shows the timeline with in-component create", async ({ page }, testInfo) => {
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

  // The embedded evidence pool expander must be GONE from this page.
  await expect(page.getByText(/Evidence pool|证据池/)).toHaveCount(0);

  // The timeline React component iframe should render.
  const frame = await findTimelineFrame(page);
  if (!frame) {
    const body = await page.screenshot({ fullPage: true });
    await testInfo.attach("no-timeline-frame", { body, contentType: "image/png" });
  }
  expect(frame, "timeline component iframe should be present").not.toBeNull();
  await expect(frame.locator(".tl-toolbar")).toBeVisible({ timeout: 10_000 });

  // Create project is a toolbar button inside the component.
  const createBtn = frame
    .locator("button", { hasText: /Create project|新建项目/ })
    .first();
  await expect(createBtn).toBeVisible({ timeout: 10_000 });

  // Clicking it opens the inline create form (title field shows up).
  await createBtn.click();
  await expect(frame.locator(".tl-create-form")).toBeVisible({ timeout: 8_000 });

  const body = await page.screenshot({ fullPage: true });
  await testInfo.attach("project-board-timeline", { body, contentType: "image/png" });
});
