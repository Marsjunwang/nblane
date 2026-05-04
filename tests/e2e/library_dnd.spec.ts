import { expect, test } from "@playwright/test";

const e2eBaseUrl =
  process.env.NBLANE_E2E_BASE_URL || "http://127.0.0.1:8510/Public_Site";

async function openEditorFrame(page) {
  try {
    await page.goto(e2eBaseUrl, { waitUntil: "domcontentloaded", timeout: 20000 });
  } catch {
    test.skip(true, "Set NBLANE_E2E_BASE_URL or run the Streamlit app on port 8510.");
  }
  await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  const blogTab = page.getByText(/^Blog$/).first();
  if (await blogTab.count()) {
    await blogTab.click();
    await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
    await page.waitForTimeout(2500);
  }
  const deadline = Date.now() + 10_000;
  while (Date.now() < deadline) {
    for (const frame of page.frames()) {
      if (await frame.locator(".nb-library-tree:visible").first().count()) {
        return frame;
      }
    }
    await page.waitForTimeout(250);
  }
  if (await page.locator(".nb-library-tree:visible").first().count()) {
    return page;
  }
  test.skip(true, "Blog library tree is not visible at the configured URL.");
}

test("library search and row menu are wired", async ({ page }) => {
  const frame = await openEditorFrame(page);
  const search = frame.locator(".nb-library-search").first();
  await expect(search).toBeVisible();
  await search.fill("post");
  await expect(frame.locator(".nb-library-tree").first()).toBeVisible();

  const rowMenu = frame.locator(".nb-library-row-menu").first();
  if (!(await rowMenu.count())) {
    test.skip(true, "No library rows are available in this profile.");
  }
  await rowMenu.click();
  await expect(frame.locator(".nb-library-context-menu").first()).toBeVisible();
});

test("library drag surfaces a drop target or gracefully skips sparse profiles", async ({ page }) => {
  const frame = await openEditorFrame(page);
  const rows = frame.locator(".nb-library-row");
  const rowCount = await rows.count();
  if (rowCount < 2) {
    test.skip(true, "Need at least two library rows to exercise drag.");
  }
  let sourceIndex = -1;
  for (let index = 0; index < rowCount; index += 1) {
    const typeText = await rows.nth(index).locator(".nb-library-type").innerText().catch(() => "");
    if (typeText.trim() !== "R") {
      sourceIndex = index;
      break;
    }
  }
  if (sourceIndex < 0) {
    test.skip(true, "Need a non-root library row to exercise drag.");
  }
  const targetIndex = sourceIndex + 1 < rowCount ? sourceIndex + 1 : sourceIndex - 1;
  const source = rows.nth(sourceIndex);
  const target = rows.nth(targetIndex);
  const sourceHandleBox = await source.locator(".nb-library-drag-handle").boundingBox();
  const secondBox = await target.boundingBox();
  if (!sourceHandleBox || !secondBox) {
    test.skip(true, "Library row boxes are unavailable.");
  }
  await page.mouse.move(
    sourceHandleBox.x + sourceHandleBox.width / 2,
    sourceHandleBox.y + sourceHandleBox.height / 2,
  );
  await page.mouse.down();
  await page.mouse.move(secondBox.x + secondBox.width / 2, secondBox.y + 2, { steps: 8 });
  await expect(frame.locator(".nb-library-drop-indicator").first()).toBeVisible({ timeout: 4000 });
  await expect(frame.locator(".nb-library-drop-indicator")).toHaveCount(1);
  await page.mouse.move(
    secondBox.x + secondBox.width / 2,
    secondBox.y + secondBox.height - 2,
    { steps: 6 },
  );
  await expect(frame.locator(".nb-library-drop-indicator")).toHaveCount(1);
  await page.mouse.up();
});

test("left library panel resize handle updates and persists width", async ({ page }) => {
  const frame = await openEditorFrame(page);
  const handle = frame.locator(".nb-resize-left:visible").first();
  if (!(await handle.count())) {
    test.skip(true, "Left resize handle is not visible in this viewport.");
  }
  const workspace = frame.locator(".nb-workspace").first();
  const initialWidth = await workspace.evaluate((element) =>
    Number.parseFloat(window.getComputedStyle(element).gridTemplateColumns.split(" ")[0]),
  );
  const handleBox = await handle.boundingBox();
  if (!handleBox || !Number.isFinite(initialWidth)) {
    test.skip(true, "Resize handle or workspace metrics are unavailable.");
  }
  await page.mouse.move(handleBox.x + handleBox.width / 2, handleBox.y + 32);
  await page.mouse.down();
  await page.mouse.move(handleBox.x + handleBox.width / 2 + 140, handleBox.y + 32, {
    steps: 8,
  });
  await page.mouse.up();
  await expect
    .poll(async () =>
      workspace.evaluate((element) =>
        Number.parseFloat(window.getComputedStyle(element).gridTemplateColumns.split(" ")[0]),
      ),
    )
    .toBeGreaterThan(Math.min(initialWidth + 40, 520));
  const stored = await frame.evaluate(() => window.localStorage.getItem("nb.leftPanelWidth"));
  expect(Number(stored)).toBeGreaterThan(Math.min(initialWidth + 40, 520));
});
