import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";

import { SPA_BASE_URL, SPA_E2E_PROFILE } from "./spa_auth_shared";

/**
 * Acceptance suite for the star-catalog interaction + goal start-date slice
 * (docs/zh/dev/home-starmap-enhancements-design.md §2/§3):
 *
 * A1. Esc = one-key return to the pure chart from every state (catalog,
 *     card, edit mode, catalog+card) — no layering.
 * A2. The catalog stays open when a goal row is selected; the detail card
 *     updates live.
 * A3. ↑/↓ (j/k) moves the catalog highlight with wrap; Enter opens the card.
 * A4. Chart click → catalog row highlight + scroll (two-way sync).
 * A5. One-time fading hint bar on first catalog open (per session).
 * B.  Goal start date: POST auto-stamps today; 重刻 edit form edits 起始.
 *
 * Targets the isolated SPA backend (default http://127.0.0.1:18504).
 * Screenshots land in /tmp/catalog-ux-shots/.
 */

const PROFILE = process.env.NBLANE_E2E_PROFILE || SPA_E2E_PROFILE;
const SHOTS = process.env.NBLANE_E2E_SHOTS || "/tmp/catalog-ux-shots";

function spa(path: string): string {
  return `${SPA_BASE_URL}/p/${encodeURIComponent(PROFILE)}/${path}`;
}

function api(path: string): string {
  return `${SPA_BASE_URL}/api/v1/profiles/${encodeURIComponent(PROFILE)}/${path}`;
}

async function shot(page: Page, name: string): Promise<void> {
  fs.mkdirSync(SHOTS, { recursive: true });
  await page.screenshot({ path: `${SHOTS}/${name}.png` });
}

async function openHome(page: Page): Promise<void> {
  await page.goto(spa("home"));
  await expect(page.getByTestId("starmap-root")).toBeVisible({ timeout: 30_000 });
  const canvas = page.locator("canvas.starmap-canvas");
  test.skip((await canvas.count()) === 0, "no WebGL in this environment");
}

async function clickPoleStar(page: Page): Promise<void> {
  const heart = page.getByTestId("starmap-heart");
  const box = (await heart.boundingBox())!;
  await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
  await expect(page.getByTestId("starmap-detail")).toHaveClass(/open/);
}

function expectPureChart(page: Page): Promise<void> {
  return (async () => {
    await expect(page.getByTestId("starmap-catalog")).not.toHaveClass(/open/);
    await expect(page.getByTestId("starmap-detail")).not.toHaveClass(/open/);
  })();
}

test.describe("SPA Home 星表交互 + 起始日期 (home-starmap-enhancements §2/§3)", () => {
  test("Esc from every state returns to the pure chart", async ({ page, request }) => {
    const goals = (await (await request.get(api("goals"))).json()).goals ?? [];
    const active = goals.find((g: { status?: string }) => (g.status ?? "active") === "active");
    test.skip(!active, "profile has no active goal");
    await openHome(page);
    const catalog = page.getByTestId("starmap-catalog");
    const detail = page.getByTestId("starmap-detail");

    // 1. Catalog only → Esc closes it.
    await page.getByTestId("starmap-catalog-btn").click();
    await expect(catalog).toHaveClass(/open/);
    await page.keyboard.press("Escape");
    await expectPureChart(page);

    // 2. Card only (pole star) → Esc closes it.
    await clickPoleStar(page);
    await page.keyboard.press("Escape");
    await expectPureChart(page);

    // 3. Edit mode (重刻) → Esc closes everything, not just the form.
    await clickPoleStar(page);
    await detail.getByTestId("starmap-recarve").click();
    await expect(detail.getByTestId("starmap-edit-north")).toBeVisible();
    await shot(page, "01-edit-mode-before-esc");
    await page.keyboard.press("Escape");
    await expectPureChart(page);

    // 4. Catalog + card together → one Esc clears both.
    await page.getByTestId("starmap-catalog-btn").click();
    await catalog.getByTestId(`catalog-row-${active.id}`).click();
    await expect(detail).toHaveClass(/open/, { timeout: 10_000 });
    await page.keyboard.press("Escape");
    await expectPureChart(page);
    await shot(page, "02-pure-chart-after-esc");
  });

  test("catalog persists on row select; ↑↓ wraps and Enter opens the card", async ({
    page,
    request,
  }) => {
    const goals = (await (await request.get(api("goals"))).json()).goals ?? [];
    const active = goals.find((g: { status?: string }) => (g.status ?? "active") === "active");
    test.skip(!active, "profile has no active goal");
    await openHome(page);
    const catalog = page.getByTestId("starmap-catalog");
    const detail = page.getByTestId("starmap-detail");

    await page.getByTestId("starmap-catalog-btn").click();
    await expect(catalog).toHaveClass(/open/);
    // One-time hint bar shows on first open of the session.
    await expect(catalog.getByTestId("catalog-hintbar")).toBeVisible();
    await shot(page, "03-catalog-hintbar");

    // Keyboard nav from the default 帝星 highlight: ↓/j move down, ↑/k move
    // up, both wrap around the ends.
    const rows = catalog.locator(".starmap-catalog-row");
    await expect(catalog.getByTestId("catalog-row-north")).toHaveClass(/active/);
    await page.keyboard.press("ArrowDown");
    await expect(rows.nth(1)).toHaveClass(/active/);
    await page.keyboard.press("k");
    await expect(catalog.getByTestId("catalog-row-north")).toHaveClass(/active/);
    await page.keyboard.press("ArrowUp"); // wrap → last row
    await expect(rows.last()).toHaveClass(/active/);
    await page.keyboard.press("j"); // wrap → 帝星
    await expect(catalog.getByTestId("catalog-row-north")).toHaveClass(/active/);

    // Enter opens the highlighted row's card; the catalog stays open.
    await page.keyboard.press("Enter");
    await expect(detail).toHaveClass(/open/, { timeout: 10_000 });
    await expect(catalog).toHaveClass(/open/);
    await shot(page, "04-enter-opens-north-card");

    // Row click keeps the catalog open; the detail card updates live.
    await catalog.getByTestId(`catalog-row-${active.id}`).click();
    await expect(detail.locator("h3")).toHaveText(active.title || active.id, { timeout: 10_000 });
    await expect(catalog).toHaveClass(/open/);
    await expect(catalog.getByTestId(`catalog-row-${active.id}`)).toHaveClass(/active/);
    await shot(page, "05-catalog-stays-open-with-card");
  });

  test("chart → catalog: clicking the pole star highlights its row", async ({ page }) => {
    await openHome(page);
    await page.getByTestId("starmap-catalog-btn").click();
    const catalog = page.getByTestId("starmap-catalog");
    // Move the highlight away from 帝星 first.
    await page.keyboard.press("ArrowDown");
    await clickPoleStar(page);
    await expect(catalog.getByTestId("catalog-row-north")).toHaveClass(/active/);
    await expect(catalog).toHaveClass(/open/);
    await shot(page, "06-chart-to-catalog-sync");
  });

  test("goal start: create auto-stamps today; 重刻 edits 起始", async ({ page, request }) => {
    const TITLE = "验收·起始日期";
    const fetchGoals = async () =>
      ((await (await request.get(api("goals"))).json()).goals ?? []) as {
        id: string;
        title: string;
        start?: string;
        status?: string;
      }[];
    const today = new Date().toLocaleDateString("sv-SE"); // YYYY-MM-DD, local
    let goal = (await fetchGoals()).find((g) => g.title === TITLE);

    await openHome(page);
    await page.getByTestId("starmap-catalog-btn").click();
    const catalog = page.getByTestId("starmap-catalog");

    if (!goal) {
      await catalog.getByTestId("catalog-add-goal").click();
      const form = catalog.getByTestId("catalog-goal-form");
      await form.getByTestId("create-goal-title").fill(TITLE);
      await form.getByTestId("create-goal-save").click();
      await expect(catalog).toContainText("已入星表", { timeout: 10_000 });
      goal = (await fetchGoals()).find((g) => g.title === TITLE);
    }
    expect(goal, "acceptance goal should exist (created or reused)").toBeTruthy();

    // Auto-stamped 立项日 on create (reused leftovers may carry an older date,
    // which is fine — only fresh creates are asserted).
    const fresh = (await fetchGoals()).find((g) => g.title === TITLE);
    expect(fresh!.start).toBeTruthy();
    await shot(page, "07-goal-with-start");

    // Detail card shows 起始.
    const row = catalog.getByTestId(`catalog-row-${goal!.id}`);
    await expect(row).toBeVisible({ timeout: 15_000 });
    await row.click();
    const detail = page.getByTestId("starmap-detail");
    await expect(detail).toHaveClass(/open/, { timeout: 10_000 });
    await expect(detail).toContainText("起始");
    await expect(detail).toContainText(fresh!.start!);

    // 重刻: edit 起始 and persist.
    await detail.getByTestId("starmap-recarve").click();
    const edit = detail.getByTestId("starmap-edit-goal");
    const startInput = edit.getByTestId("edit-goal-start");
    await expect(startInput).toBeVisible();
    await expect(startInput).toHaveValue(fresh!.start!);
    const newStart = fresh!.start === "2026-01-15" ? "2026-02-15" : "2026-01-15";
    await startInput.fill(newStart);
    await shot(page, "08-goal-edit-start");
    await edit.getByTestId("starmap-save").click();
    await expect(edit).toBeHidden({ timeout: 10_000 });
    const after = (await fetchGoals()).find((g) => g.id === goal!.id);
    expect(after!.start).toBe(newStart);
    await expect(detail).toContainText(newStart, { timeout: 10_000 });
    await shot(page, "09-goal-start-saved");

    // A brand-new create stamps today server-side.
    const stamp = await (
      await request.post(api("goals"), { data: { title: "验收·起始日期·自动" } })
    ).json();
    expect(stamp.goal.start).toBe(today);
  });
});
