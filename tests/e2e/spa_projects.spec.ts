import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";

/**
 * SPA /projects — the unified Phase 2 page (kanban swimlanes + timeline
 * sharing `?task=`) against the isolated sandbox
 * (`scripts/dev-web.sh --isolated`, profile=dev).
 *
 * Covers:
 *  - lane drag & drop (dnd-kit, scoped to one lane): mouse cross-column,
 *    keyboard lift/arrows/drop, in-column reorder with to_index;
 *  - shared selection: ?task= deep link opens the inscription detail card,
 *    and the 泳道看板/时间轴 switch keeps it;
 *  - detail-card mutations: 排期 save (schedule endpoint), habit 打卡
 *    (checkins endpoint);
 *  - legacy redirects: /kanban and /project-board land on /projects with
 *    the query string intact.
 *
 * Seeding goes through the API (no toast overlaying the cards); every title
 * is unique per run so reruns never collide with kanban's title-based
 * addressing. Cards seeded without a project land in the 未归属 lane.
 */

const SPA_BASE_URL = (process.env.NBLANE_E2E_SPA_BASE_URL || "http://127.0.0.1:18504").replace(
  /\/+$/,
  "",
);
const PROFILE = process.env.NBLANE_E2E_PROFILE || "dev";

function spa(path: string): string {
  return `${SPA_BASE_URL}/p/${encodeURIComponent(PROFILE)}/${path}`;
}

function api(path: string): string {
  return `${SPA_BASE_URL}/api/v1/profiles/${encodeURIComponent(PROFILE)}${path}`;
}

/** The unassigned lane's columns (seeded cards have no project). */
function queueColumn(page: Page) {
  return page.getByTestId("lane-column-unassigned-queue");
}
function doingColumn(page: Page) {
  return page.getByTestId("lane-column-unassigned-doing");
}

/** Seed one card into Queue via the API; returns its card id (kb_xxx). */
async function seedQueueCard(page: Page, title: string): Promise<string> {
  const response = await page.request.post(api("/kanban/cards"), {
    data: { title, section: "Queue", context: "" },
  });
  expect(response.status(), "kanban card seed should succeed").toBe(201);
  return ((await response.json()) as { card: { id: string } }).card.id;
}

/** Wait for the POST .../move a drop triggers and assert it succeeded. */
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

test.describe("SPA /projects lane drag & drop", () => {
  test("mouse: drag a card from Queue to Doing within its lane", async ({ page }) => {
    const title = `e2e-dnd-${Date.now()}`;
    await seedQueueCard(page, title);
    await page.goto(spa("projects"));
    await expect(queueColumn(page).getByText(title)).toBeVisible();

    // The whole card is the drag handle (dnd-kit sortable attributes).
    // Cards are appended at the END of Queue; scroll into view FIRST, then
    // take viewport-relative boxes.
    const handle = page.getByRole("button", { name: `拖拽卡片 ${title}` });
    await handle.scrollIntoViewIfNeeded();
    const handleBox = await handle.boundingBox();
    const targetBox = await doingColumn(page).boundingBox();
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
      const viewportHeight = page.viewportSize()?.height ?? 1000;
      const visibleTop = Math.max(targetBox!.y, 40);
      const visibleBottom = Math.min(targetBox!.y + targetBox!.height, viewportHeight - 40);
      const dropY = (visibleTop + visibleBottom) / 2;
      await page.mouse.move(targetBox!.x + targetBox!.width / 2, dropY, { steps: 25 });
      // Gate the release on dnd-kit resolving Doing as the drop target;
      // under CPU contention onDragOver trails the pointer event stream.
      await expect(doingColumn(page)).toHaveAttribute("data-drop-target", "true", {
        timeout: 10_000,
      });
      await page.mouse.up();
    });
    expect(move.targetSection, "drop must land in Doing, not silently fall back to Queue").toBe(
      "Doing",
    );

    await expect(doingColumn(page).getByText(title)).toBeVisible();
    await expect(queueColumn(page).getByText(title)).toHaveCount(0);
  });

  test("keyboard: Space lifts, arrows reach the Doing column, Space drops", async ({ page }) => {
    const title = `e2e-dnd-kb-${Date.now()}`;
    await seedQueueCard(page, title);
    await page.goto(spa("projects"));
    await expect(queueColumn(page).getByText(title)).toBeVisible();

    const handle = page.getByRole("button", { name: `拖拽卡片 ${title}` });
    await handle.focus();
    await expect(handle).toBeFocused();

    // Lift, then gate on dnd-kit actually picking the card up (its keydown
    // listener for arrows/drop binds in a setTimeout — don't race it).
    await page.keyboard.press("Space"); // lift
    await expect(handle, "Space should lift the card (KeyboardSensor active)").toHaveAttribute(
      "aria-pressed",
      "true",
    );

    // The lane has exactly two columns; ArrowRight reaches Doing. Poll the
    // live drop-target highlight so React has time to resolve collisions.
    const highlighted = page.locator('[data-drop-target="true"]');
    let targetTestId = "";
    for (let attempt = 0; attempt < 6 && !targetTestId; attempt++) {
      await page.keyboard.press("ArrowRight");
      try {
        await expect(highlighted).toHaveCount(1, { timeout: 1_500 });
        const testId = await highlighted.getAttribute("data-testid");
        if (testId === "lane-column-unassigned-doing") {
          targetTestId = testId;
        }
      } catch {
        // Arrow stayed inside Queue (reorder preview) or raced the sensor
        // binding — press again.
      }
    }
    expect(targetTestId, "keyboard drag should reach the Doing column").toBeTruthy();

    const move = await expectMoveResponse(page, () => page.keyboard.press("Space"));
    expect(move.targetSection).toBe("Doing");

    await expect(doingColumn(page).getByText(title)).toBeVisible();
    await expect(queueColumn(page).getByText(title)).toHaveCount(0);
  });

  test("mouse: in-column drag reorders a lane's Queue and persists after reload", async ({
    page,
    request,
  }) => {
    // A fresh project lane holds exactly our three cards — no 460-card tail
    // geometry from the shared unassigned lane.
    const run = Date.now();
    const create = await request.post(api("/project-board/cases"), {
      data: { title: `e2e-reorder-case-${run}` },
    });
    expect(create.status(), "project case seed should succeed").toBe(201);
    const caseId: string = (await create.json()).case.id;
    const titles = [`e2e-reorder-a-${run}`, `e2e-reorder-b-${run}`, `e2e-reorder-c-${run}`];
    for (const title of titles) {
      const task = await request.post(api(`/project-board/cases/${caseId}/tasks`), {
        data: { title, section: "Queue", milestone_id: "", context: "", date: "" },
      });
      expect(task.status(), "project task seed should succeed").toBe(201);
    }

    await page.goto(spa("projects"));
    const laneQueue = page.getByTestId(`lane-column-${caseId}-queue`);
    await expect(laneQueue.getByText(titles[0])).toBeVisible();
    const laneOrder = async (): Promise<string[]> =>
      laneQueue
        .getByRole("button", { name: /^拖拽卡片 / })
        .evaluateAll((els) =>
          els.map((el) => (el.getAttribute("aria-label") ?? "").replace(/^拖拽卡片 /, "")),
        );
    expect(await laneOrder()).toEqual(titles);

    // Drag the first card onto the third (drop on a card inserts after it:
    // to_index is post-removal, so C's pre-removal index lands A behind C).
    const handleA = laneQueue.getByRole("button", { name: `拖拽卡片 ${titles[0]}` });
    const cardC = laneQueue.getByRole("button", { name: `拖拽卡片 ${titles[2]}` });
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
    await page.mouse.move(startX + 12, startY + 10, { steps: 5 });

    const move = await expectMoveResponse(page, async () => {
      // Aim at the bottom edge of C instead of chasing its live center (the
      // sortable preview lifts C one slot up).
      const dropX = targetBox!.x + targetBox!.width / 2;
      const dropY = targetBox!.y + targetBox!.height - 4;
      await page.mouse.move(dropX, dropY, { steps: 20 });
      await page.mouse.up();
    });

    expect(move.targetSection).toBe("Queue");
    expect(typeof move.toIndex, "in-column drop must carry to_index").toBe("number");
    await expect.poll(laneOrder).toEqual([titles[1], titles[2], titles[0]]);
    await page.reload();
    await expect(laneQueue.getByText(titles[0])).toBeVisible();
    expect(await laneOrder()).toEqual([titles[1], titles[2], titles[0]]);

    // Tidy up: archive the throwaway lane.
    const archive = await request.post(api(`/project-board/cases/${caseId}/archive`));
    expect(archive.status()).toBeLessThan(300);
  });
});

test.describe("SPA /projects shared selection & views", () => {
  test("?task= deep link opens the detail card; the view switch keeps it", async ({ page }) => {
    const title = `e2e-link-${Date.now()}`;
    const cardId = await seedQueueCard(page, title);

    // Deep link straight into the detail card.
    await page.goto(spa(`projects?task=${cardId}`));
    const detail = page.getByTestId("task-detail-card");
    await expect(detail).toBeVisible();
    await expect(detail).toContainText(title);

    // Switch to the timeline: the selection (and the card) survives.
    await page.getByText("时间轴", { exact: true }).click();
    await expect(page).toHaveURL(new RegExp(`view=timeline`));
    await expect(page).toHaveURL(new RegExp(`task=${cardId}`));
    await expect(page.getByTestId("timeline-view")).toBeVisible();
    await expect(detail).toBeVisible();

    // Back to the board; close the card → only the task param drops.
    await page.getByText("泳道看板", { exact: true }).click();
    await expect(page.getByTestId("board-view")).toBeVisible();
    await detail.getByRole("button", { name: "关闭详情" }).click();
    await expect(detail).toHaveCount(0);
    await expect(page).not.toHaveURL(/task=/);
  });

  test("detail card 保存排期 posts planned dates; 打卡 posts a check-in", async ({ page }) => {
    const title = `e2e-sched-${Date.now()}`;
    const cardId = await seedQueueCard(page, title);
    await page.goto(spa(`projects?task=${cardId}`));
    const detail = page.getByTestId("task-detail-card");
    await expect(detail).toBeVisible();

    const scheduleResponse = page.waitForResponse(
      (res) => res.url().includes("/schedule") && res.request().method() === "POST",
    );
    await detail.getByLabel("排期开始").fill("2026-10-01");
    await detail.getByLabel("排期结束").fill("2026-10-15");
    await detail.getByTestId("schedule-save").click();
    const response = await scheduleResponse;
    expect(response.status(), "schedule should succeed").toBeLessThan(300);
    expect(
      response.request().postDataJSON() as { planned_start?: string; planned_end?: string },
    ).toMatchObject({ planned_start: "2026-10-01", planned_end: "2026-10-15" });

    // The scheduled span renders on the timeline.
    await detail.getByRole("button", { name: "关闭详情" }).click();
    await page.getByText("时间轴", { exact: true }).click();
    await expect(page.getByTestId(`timeline-bar-${cardId}`)).toBeVisible();

    // Habit check-in from the lane (when the sandbox has habits).
    await page.getByText("泳道看板", { exact: true }).click();
    const checkinButton = page.locator('[data-testid^="checkin-button-"]').first();
    if ((await checkinButton.count()) > 0) {
      const checkinResponse = page.waitForResponse(
        (res) => res.url().includes("/checkins") && res.request().method() === "POST",
      );
      await checkinButton.click();
      expect((await checkinResponse).status(), "check-in should succeed").toBeLessThan(300);
    }
  });

  test("legacy /kanban and /project-board redirect to /projects keeping the query", async ({
    page,
  }) => {
    const title = `e2e-legacy-${Date.now()}`;
    const cardId = await seedQueueCard(page, title);

    await page.goto(spa(`kanban?task=${cardId}`));
    await expect(page).toHaveURL(new RegExp(`/projects\\?task=${cardId}`));
    await expect(page.getByTestId("task-detail-card")).toBeVisible();
    await page.getByRole("button", { name: "关闭详情" }).click();

    await page.goto(spa(`project-board?view=timeline`));
    await expect(page).toHaveURL(/\/projects\?view=timeline/);
    await expect(page.getByTestId("timeline-view")).toBeVisible();
  });
});
