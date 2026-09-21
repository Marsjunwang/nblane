import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";

/**
 * SPA kanban drag & drop (dnd-kit) against the isolated sandbox
 * (`scripts/dev-web.sh --isolated`, profile=dev).
 *
 * The backend move endpoint takes a target section plus an optional
 * to_index, so both cross-column and in-column drags persist; the "…"
 * 移动到… menu remains as the no-drag fallback (covered by
 * spa_mutations.spec.ts). Every card title is unique per run so reruns
 * never collide with kanban's title-based addressing.
 */

const SPA_BASE_URL = (process.env.NBLANE_E2E_SPA_BASE_URL || "http://127.0.0.1:18504").replace(
  /\/+$/,
  "",
);
const PROFILE = process.env.NBLANE_E2E_PROFILE || "dev";

function spa(path: string): string {
  return `${SPA_BASE_URL}/p/${encodeURIComponent(PROFILE)}/${path}`;
}

function column(page: Page, name: string) {
  return page.getByTestId(`kanban-column-${name}`);
}

/** Seed one card into Queue through the real UI and wait for the refetch. */
async function seedQueueCard(page: Page, title: string): Promise<void> {
  await page.goto(spa("kanban"));
  await page.getByLabel("快速添加").fill(title);
  const addResponse = page.waitForResponse(
    (res) => res.url().includes("/kanban/cards") && res.request().method() === "POST",
  );
  await page.getByRole("button", { name: "添加", exact: true }).click();
  expect((await addResponse).status()).toBeLessThan(300);
  await expect(column(page, "Queue").getByText(title)).toBeVisible();
}

/** Wait for the POST .../move the drop triggers and assert it succeeded. */
async function expectMoveResponse(
  page: Page,
  action: () => Promise<void>,
): Promise<{ targetSection: string; toIndex?: number }> {
  const responsePromise = page.waitForResponse(
    (res) => res.url().includes("/move") && res.request().method() === "POST",
  );
  await action();
  const response = await responsePromise;
  expect(response.status(), "drop should POST a successful move").toBeLessThan(300);
  expect(response.status()).toBeGreaterThanOrEqual(200);
  const body = response.request().postDataJSON() as {
    target_section?: string;
    to_index?: number;
  };
  expect(body.target_section, "move body must carry target_section").toBeTruthy();
  return { targetSection: body.target_section!, toIndex: body.to_index };
}

test.describe("SPA kanban drag & drop", () => {
  test("mouse: drag a card from Queue to Doing", async ({ page }) => {
    const title = `e2e-dnd-${Date.now()}`;
    await seedQueueCard(page, title);

    // The whole card is the drag handle (dnd-kit sortable attributes).
    // Cards are appended at the END of Queue; once the column outgrows the
    // viewport the fresh card sits below the fold and page.mouse (viewport
    // coordinates) would miss it — scroll it into view FIRST, then take the
    // boxes (boundingBox is viewport-relative, so recompute after scrolling).
    const handle = page.getByRole("button", { name: `拖拽卡片 ${title}` });
    await handle.scrollIntoViewIfNeeded();
    const handleBox = await handle.boundingBox();
    const targetBox = await column(page, "Doing").boundingBox();
    expect(handleBox, "drag handle must be laid out").toBeTruthy();
    expect(targetBox, "target column must be laid out").toBeTruthy();

    const startX = handleBox!.x + handleBox!.width / 2;
    const startY = handleBox!.y + handleBox!.height / 2;
    await page.mouse.move(startX, startY);
    await page.mouse.down();
    // Pass the MouseSensor activation distance (4px) in small steps so the
    // drag actually starts before crossing columns.
    await page.mouse.move(startX + 24, startY + 8, { steps: 6 });
    const move = await expectMoveResponse(page, async () => {
      // Drop into the MIDDLE of the Doing column's *visible* slice: clamping
      // the box center into the viewport is not enough — once the Queue is
      // taller than Doing, the page scrolls past Doing's bottom edge and a
      // bottom-clamped point lands in dead space below the column (the drop
      // silently falls back to Queue; surfaced 2026-09-21 as the sandbox
      // columns' heights drifted apart).
      const viewportHeight = page.viewportSize()?.height ?? 1000;
      const visibleTop = Math.max(targetBox!.y, 40);
      const visibleBottom = Math.min(targetBox!.y + targetBox!.height, viewportHeight - 40);
      const dropY = (visibleTop + visibleBottom) / 2;
      await page.mouse.move(targetBox!.x + targetBox!.width / 2, dropY, {
        steps: 25,
      });
      // Gate the release on dnd-kit actually resolving Doing as the drop
      // target: under CPU contention onDragOver's collision resolution trails
      // the pointer event stream, and releasing early drops onto the last
      // resolved container — Queue — which the backend dutifully persists
      // (trace evidence 2026-09-21: target_section=Queue, to_index=126 with
      // the sandbox Queue at 126+ cards). The keyboard case below uses the
      // same data-drop-target gate.
      await expect(column(page, "Doing")).toHaveAttribute("data-drop-target", "true", {
        timeout: 10_000,
      });
      await page.mouse.up();
    });
    expect(move.targetSection, "drop must land in Doing, not silently fall back to Queue").toBe(
      "Doing",
    );

    await expect(column(page, "Doing").getByText(title)).toBeVisible();
    await expect(column(page, "Queue").getByText(title)).toHaveCount(0);
  });

  test("keyboard: Space lifts, arrows reach another column, Space drops", async ({ page }) => {
    const title = `e2e-dnd-kb-${Date.now()}`;
    await seedQueueCard(page, title);

    const handle = page.getByRole("button", { name: `拖拽卡片 ${title}` });
    await handle.focus();
    await expect(handle).toBeFocused();

    // Lift, then gate on dnd-kit actually picking the card up. Space triggers
    // the KeyboardSensor activator, but its keydown listener for arrows/drop
    // is attached in a setTimeout — pressing on without waiting races it.
    await page.keyboard.press("Space"); // lift
    await expect(handle, "Space should lift the card (KeyboardSensor active)").toHaveAttribute(
      "aria-pressed",
      "true",
    );

    // Geometry-agnostic: move in one direction until the live drop-target
    // highlight (driven by onDragOver) lands on any non-Queue column, then
    // read the actual target from the DOM instead of assuming a column.
    // Retrying absorbs the sensor's async keydown binding; each press is
    // followed by a poll so React has time to resolve collisions.
    const highlighted = page.locator('[data-drop-target="true"]');
    let targetColumnName = "";
    for (const key of ["ArrowRight", "ArrowLeft"] as const) {
      for (let attempt = 0; attempt < 4 && !targetColumnName; attempt++) {
        await page.keyboard.press(key);
        try {
          await expect(highlighted).toHaveCount(1, { timeout: 1_500 });
          const testId = await highlighted.getAttribute("data-testid");
          if (testId?.startsWith("kanban-column-")) {
            targetColumnName = testId.slice("kanban-column-".length);
          }
        } catch {
          // Arrow stayed inside Queue (reorder preview) or the press raced
          // the sensor binding — press again in the same direction.
        }
      }
      if (targetColumnName) break;
    }
    expect(targetColumnName, "keyboard drag should reach a non-Queue column").toBeTruthy();

    const move = await expectMoveResponse(page, () => page.keyboard.press("Space"));
    expect(move.targetSection).toBe(targetColumnName);

    await expect(column(page, targetColumnName).getByText(title)).toBeVisible();
    await expect(column(page, "Queue").getByText(title)).toHaveCount(0);
  });

  test("mouse: in-column drag reorders Queue and persists after reload", async ({ page }) => {
    const run = Date.now();
    const titles = [`e2e-reorder-a-${run}`, `e2e-reorder-b-${run}`, `e2e-reorder-c-${run}`];
    for (const title of titles) {
      await seedQueueCard(page, title);
    }
    // The seeds land consecutively at the Queue tail: [A, B, C]. Other
    // specs may interleave their own cards, so always assert the relative
    // order of OUR three titles, never absolute positions.
    const queue = column(page, "Queue");
    const seededOrder = async (): Promise<string[]> => {
      const labels = await queue
        .getByRole("button", { name: /^拖拽卡片 / })
        .evaluateAll((els) => els.map((el) => el.getAttribute("aria-label") ?? ""));
      return labels
        .map((label) => label.replace(/^拖拽卡片 /, ""))
        .filter((label) => titles.includes(label));
    };
    expect(await seededOrder()).toEqual(titles);

    // Drag the first seed onto the third (same geometry caveats as the
    // cross-column case: scroll into view first, viewport-relative boxes).
    const handleA = page.getByRole("button", { name: `拖拽卡片 ${titles[0]}` });
    const cardC = page.getByRole("button", { name: `拖拽卡片 ${titles[2]}` });
    await handleA.scrollIntoViewIfNeeded();
    await cardC.scrollIntoViewIfNeeded();
    const startBox = await handleA.boundingBox();
    const targetBox = await cardC.boundingBox();
    expect(startBox, "drag handle must be laid out").toBeTruthy();
    expect(targetBox, "drop target card must be laid out").toBeTruthy();

    const startX = startBox!.x + startBox!.width / 2;
    const startY = startBox!.y + startBox!.height / 2;
    await page.mouse.move(startX, startY);
    await page.mouse.down();
    // Pass the MouseSensor activation distance (4px) in small steps.
    await page.mouse.move(startX + 12, startY + 10, { steps: 5 });

    const move = await expectMoveResponse(page, async () => {
      // Aim at the bottom edge of C instead of chasing its live center:
      // once the sortable preview lifts C one slot up, the pointer rests in
      // the vacated tail space and the collision fallback keeps resolving
      // the drop to C — a stable `over` with no moving target. (Dropping on
      // C inserts AFTER it: the backend's to_index is post-removal, so C's
      // pre-removal index lands the dragged card right behind C.)
      const viewportHeight = page.viewportSize()?.height ?? 1000;
      const dropX = targetBox!.x + targetBox!.width / 2;
      const dropY = Math.min(targetBox!.y + targetBox!.height - 4, viewportHeight - 8);
      await page.mouse.move(dropX, dropY, { steps: 20 });
      await page.mouse.up();
    });

    // Same target section + to_index: dropping A on C lands A right after C
    // (post-removal insertion), so the seeded order becomes [B, C, A].
    expect(move.targetSection).toBe("Queue");
    expect(typeof move.toIndex, "in-column drop must carry to_index").toBe("number");
    await expect.poll(seededOrder).toEqual([titles[1], titles[2], titles[0]]);

    await page.reload();
    await expect(queue.getByText(titles[0])).toBeVisible();
    expect(await seededOrder()).toEqual([titles[1], titles[2], titles[0]]);
  });
});
