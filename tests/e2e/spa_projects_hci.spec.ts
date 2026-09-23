import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";

import { SPA_BASE_URL } from "./spa_auth_shared";

/**
 * Acceptance suite for the projects-page HCI frontend package
 * (docs/zh/dev/phase2-projects-hci.md — 总纲/视觉降级规范/五项裁决):
 *
 * 1. 归档带展开 — archived strip expands inline to dimmed read-only lanes
 *    (restore + drawer actions, no drag handles, no quick-add).
 * 2. 日课栏 — one band row per habit (habit-plan doppelgänger lanes gone),
 *    第N/30天 arc, month-heatmap expand + past-cell backfill check-in.
 * 3. 行内快添 — 「＋ 快速添加」round trip into a throwaway project lane.
 * 4. 时间轴 — history 刻痕 bars visible by default, default window is the
 *    trailing 6 months,「全部」 zoom extends the domain.
 * 5. 删除项目 — danger-zone confirm dialog with consequence preview.
 * 6. 首页日课印 — bottom-left seal, click-to-checkin, hover dots.
 *
 * Runs against the isolated stack (127.0.0.1:18504, admin/test1234) with the
 * REAL 王军 profile. Writes are confined to: one throwaway project (deleted
 * again via the UI flow), one backfill + one today check-in on real habits.
 * Screenshots land in /tmp/hci-shots/.
 */

const PROFILE = process.env.NBLANE_E2E_PROFILE || "王军";
const SHOTS = process.env.NBLANE_HCI_SHOTS || "/tmp/hci-shots";

function spa(path: string): string {
  return `${SPA_BASE_URL}/p/${encodeURIComponent(PROFILE)}/${path}`;
}

function api(path: string): string {
  return `${SPA_BASE_URL}/api/v1/profiles/${encodeURIComponent(PROFILE)}${path}`;
}

async function shot(page: Page, name: string): Promise<void> {
  fs.mkdirSync(SHOTS, { recursive: true });
  await page.screenshot({ path: `${SHOTS}/${name}.png`, fullPage: false });
}

async function openProjects(page: Page, query = ""): Promise<void> {
  await page.goto(spa(`projects${query}`));
  await expect(page.getByTestId("projects-page")).toBeVisible({ timeout: 30_000 });
  const viewTestId = query.includes("view=timeline") ? "timeline-view" : "board-view";
  await expect(page.getByTestId(viewTestId)).toBeVisible({ timeout: 15_000 });
}

/** Mantine Drawer/Modal roots are zero-box wrappers — assert on content. */
async function expectDrawerOpen(page: Page): Promise<void> {
  await expect(page.getByTestId("case-detail")).toBeVisible({ timeout: 10_000 });
}

test.describe("SPA /projects HCI package (phase2-projects-hci)", () => {
  test("日课栏: band on top, each habit exactly once, habit-plan arc, no ghost lanes", async ({
    page,
    request,
  }) => {
    const board = await (await request.get(api("/projects-board"))).json();
    await openProjects(page);

    const band = page.getByTestId("habit-band");
    await expect(band).toBeVisible();
    // The band sits above every goal group.
    const bandBox = await band.boundingBox();
    const firstGroup = page.locator('[data-testid^="lane-group-"]').first();
    if ((await firstGroup.count()) > 0) {
      const groupBox = await firstGroup.boundingBox();
      expect(bandBox!.y).toBeLessThan(groupBox!.y);
    }

    for (const habit of board.habits ?? []) {
      // 全站一行: exactly one band row per habit …
      await expect(page.getByTestId(`habit-band-row-${habit.id}`)).toHaveCount(1);
      if (habit.project_id) {
        // … and the linked habit-plan project NEVER renders a swimlane.
        await expect(page.getByTestId(`project-lane-${habit.project_id}`)).toHaveCount(0);
        await expect(
          page.getByTestId(`lane-column-${habit.project_id}-queue`),
        ).toHaveCount(0);
      }
    }
    // No trailing 习惯 section and no 未分组 ghost for habit-plans.
    await expect(page.getByTestId("lane-group-habits")).toHaveCount(0);

    // Habit-plan rows carry the 第N/30天 progress arc.
    const planRow = page.getByTestId("habit-band-row-康复训练");
    if ((await planRow.count()) > 0) {
      await expect(planRow.getByTestId("habit-plan-arc")).toContainText(/第\d+\/30天/);
    }
    await shot(page, "01-habit-band");
  });

  test("heatmap: expand → GitHub-style grid → past-cell backfill posts a dated check-in", async ({
    page,
  }) => {
    await openProjects(page);
    // 康复训练 (fresh habit-plan) has empty cells in the trailing 90 days.
    const row = page.getByTestId("habit-band-row-康复训练");
    test.skip((await row.count()) === 0, "profile has no 康复训练 habit");

    await row.getByTestId("habit-expand-康复训练").click();
    const heatmap = page.getByTestId("habit-heatmap-康复训练");
    await expect(heatmap).toBeVisible();
    await shot(page, "02-habit-heatmap");

    // Pick the latest empty past cell (never future, never today).
    const today = new Date();
    const pad = (v: number) => String(v).padStart(2, "0");
    const todayIso = `${today.getFullYear()}-${pad(today.getMonth() + 1)}-${pad(today.getDate())}`;
    const cells = await heatmap.locator('[data-filled="false"]').all();
    const pastCells: { date: string; locator: ReturnType<Page["locator"]> }[] = [];
    for (const cell of cells) {
      const testid = (await cell.getAttribute("data-testid")) ?? "";
      const date = testid.replace("heatmap-cell-康复训练-", "");
      if (date < todayIso) pastCells.push({ date, locator: cell });
    }
    expect(pastCells.length, "heatmap should expose empty past cells").toBeGreaterThan(0);
    const target = pastCells[pastCells.length - 1];

    const checkinResponse = page.waitForResponse(
      (res) => res.url().includes("/checkins") && res.request().method() === "POST",
    );
    await target.locator.click();
    const response = await checkinResponse;
    expect(response.status(), "backfill check-in should succeed").toBeLessThan(300);
    expect(
      (response.request().postDataJSON() as { habit?: string; date?: string }).date,
    ).toBe(target.date);
    // After the invalidation refetch the cell is filled.
    await expect(heatmap.getByTestId(`heatmap-cell-康复训练-${target.date}`)).toHaveAttribute(
      "data-filled",
      "true",
      { timeout: 10_000 },
    );
    await shot(page, "03-habit-heatmap-backfilled");
  });

  test("行内快添 + 删除项目: quick-add round trip, then delete with preview", async ({
    page,
    request,
  }) => {
    const run = Date.now();
    const title = `hci-快添验收-${run}`;
    const create = await request.post(api("/project-board/cases"), {
      data: { title: `hci-验收项目-${run}` },
    });
    expect(create.status(), "throwaway case seed should succeed").toBe(201);
    const caseId: string = (await create.json()).case.id;

    await openProjects(page);
    const lane = page.getByTestId(`project-lane-${caseId}`);
    await expect(lane).toBeVisible();

    // 行内快添: click → type → Enter, zero scrolling (pinned to Queue top).
    const queueColumn = page.getByTestId(`lane-column-${caseId}-queue`);
    const quickAdd = queueColumn.getByTestId(`quick-add-${caseId}`);
    const quickAddBox = await quickAdd.boundingBox();
    const columnBox = await queueColumn.boundingBox();
    expect(quickAddBox!.y - columnBox!.y).toBeLessThan(60);
    const addResponse = page.waitForResponse(
      (res) =>
        res.url().includes(`/cases/${encodeURIComponent(caseId)}/tasks`) &&
        res.request().method() === "POST",
    );
    await quickAdd.click();
    await queueColumn.getByTestId(`quick-add-input-${caseId}`).fill(title);
    await queueColumn.getByTestId(`quick-add-input-${caseId}`).press("Enter");
    expect((await addResponse).status()).toBeLessThan(300);
    await expect(queueColumn.getByText(title)).toBeVisible({ timeout: 10_000 });
    await shot(page, "04-quick-add");

    // 删除项目: drawer → danger zone → preview + confirm + DELETE.
    await lane.getByRole("button", { name: `编辑项目 hci-验收项目-${run}` }).click();
    await expectDrawerOpen(page);
    await page.getByTestId("delete-project-button").click();
    const preview = page.getByTestId("delete-project-preview");
    await expect(preview).toBeVisible();
    await expect(preview).toContainText("1 个任务将回到未归属");
    await expect(preview).toContainText("0 条证据保留引用");
    await shot(page, "05-delete-preview");

    const confirm = page.getByTestId("delete-project-confirm");
    await expect(confirm).toBeDisabled();
    // 记入大事记 defaults off.
    await expect(page.getByTestId("delete-record-chronicle")).not.toBeChecked();
    await page.getByTestId("delete-confirm-title").fill(`hci-验收项目-${run}`);
    await expect(confirm).toBeEnabled();
    const deleteResponse = page.waitForResponse(
      (res) =>
        res.url().includes(`/cases/${encodeURIComponent(caseId)}`) &&
        res.request().method() === "DELETE",
    );
    await confirm.click();
    const del = await deleteResponse;
    expect(del.status()).toBe(200);
    const body = (await del.json()) as { tasks_unassigned?: number; evidence_refs_kept?: number };
    expect(body.tasks_unassigned).toBe(1);
    // Drawer closes; the lane is gone after the board invalidation.
    await expect(page.getByTestId("case-detail")).toHaveCount(0, { timeout: 10_000 });
    await expect(page.getByTestId(`project-lane-${caseId}`)).toHaveCount(0, { timeout: 10_000 });
    await shot(page, "06-delete-done");
  });

  test("归档带: strip expands inline to dimmed read-only lanes with 恢复", async ({
    page,
    request,
  }) => {
    // Self-seeded archived lane: the flow drives ONLY this case, so the run
    // never toggles the real archived projects either way.
    const run = Date.now();
    const title = `hci-归档验收-${run}`;
    const create = await request.post(api("/project-board/cases"), { data: { title } });
    expect(create.status(), "throwaway case seed should succeed").toBe(201);
    const caseId: string = (await create.json()).case.id;
    const archive = await request.post(
      api(`/project-board/cases/${encodeURIComponent(caseId)}/archive`),
    );
    expect(archive.status()).toBeLessThan(300);

    await openProjects(page);
    const toggle = page.getByTestId("archived-strip-toggle");
    await expect(toggle).toBeVisible();
    await expect(page.locator('[data-testid^="archived-lane-"]')).toHaveCount(0);

    await toggle.click();
    const lanes = page.locator('[data-testid^="archived-lane-"]');
    await expect(lanes.first()).toBeVisible();
    expect(await lanes.count()).toBeGreaterThanOrEqual(1);
    const lane = page.getByTestId(`archived-lane-${caseId}`);
    await expect(lane).toBeVisible();
    // Read-only: no drag handles, no quick-add inside archived lanes.
    await expect(lane.getByRole("button", { name: /^拖拽卡片 / })).toHaveCount(0);
    await expect(lane.locator('[data-testid^="quick-add-"]')).toHaveCount(0);
    await shot(page, "07-archived-expanded");

    // 恢复 via the strip action → active lane appears; then re-archive from
    // the drawer so the board returns to the seeded state.
    await lane.getByRole("button", { name: `恢复项目 ${title}` }).click();
    await expect(page.getByTestId(`project-lane-${caseId}`)).toBeVisible({ timeout: 10_000 });
    await shot(page, "08-archived-restored");
    await page
      .getByTestId(`project-lane-${caseId}`)
      .getByRole("button", { name: `编辑项目 ${title}` })
      .click();
    await expectDrawerOpen(page);
    await page
      .getByTestId("case-detail")
      .getByRole("button", { name: "归档项目" })
      .click();
    // Archiving keeps the drawer open (only delete closes it) — dismiss and
    // confirm the lane is back in the strip.
    await page.keyboard.press("Escape");
    await expect(page.getByTestId("case-detail")).toHaveCount(0, { timeout: 10_000 });
    await expect(page.getByTestId(`archived-lane-${caseId}`)).toHaveCount(1, {
      timeout: 10_000,
    });

    // Cleanup: delete the throwaway case entirely (tasks_unassigned=0).
    const del = await request.delete(
      api(`/project-board/cases/${encodeURIComponent(caseId)}`),
      { data: { confirm_title: title, record_chronicle: false } },
    );
    expect(del.status()).toBe(200);
  });

  test("时间轴: history 刻痕 bars on by default, 6-month window, 全部 zoom extends", async ({
    page,
  }) => {
    await openProjects(page, "?view=timeline");
    await expect(page.getByTestId("timeline-view")).toBeVisible({ timeout: 15_000 });

    // 历史 toggle defaults ON; 刻痕 bars (Done history) render.
    const historyToggle = page.getByTestId("timeline-history-toggle");
    await expect(historyToggle).toBeChecked();
    const historyBars = page.locator('[data-testid^="timeline-history-bar-"]');
    await expect(historyBars.first()).toBeVisible({ timeout: 10_000 });
    const barBox = await historyBars.first().boundingBox();
    // 半高 thin bars (7px) — clearly thinner than active bars (14px).
    expect(barBox!.height).toBeLessThan(10);

    // Default window = trailing 6 months (start ≥ today − 6mo − 7d pad − 1d slack).
    const scaleText = await page.getByTestId("timeline-toolbar").innerText();
    const start = scaleText.match(/(\d{4}-\d{2}-\d{2})\s*→/)?.[1] ?? "";
    const sixMonthsAgo = new Date();
    sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);
    sixMonthsAgo.setDate(sixMonthsAgo.getDate() - 8);
    expect(start >= `${sixMonthsAgo.getFullYear()}-${String(sixMonthsAgo.getMonth() + 1).padStart(2, "0")}-${String(sixMonthsAgo.getDate()).padStart(2, "0")}`).toBe(true);
    await shot(page, "09-timeline-recent");

    // 「全部」 extends the domain left (王军 has history back to 2022, clamped ≥2015).
    await page.getByTestId("timeline-zoom-toggle").getByText("全部").click();
    const toolbarText = await page.getByTestId("timeline-toolbar").innerText();
    const allStart = toolbarText.match(/(\d{4}-\d{2}-\d{2})\s*→/)?.[1] ?? "";
    expect(allStart < start).toBe(true);
    await shot(page, "10-timeline-all");

    // Toggling 历史 off hides the 刻痕 bars.
    await historyToggle.click();
    await expect(page.locator('[data-testid^="timeline-history-bar-"]')).toHaveCount(0);
  });

  test("首页日课印: bottom-left seal, click name → today check-in", async ({ page, request }) => {
    const board = await (await request.get(api("/projects-board"))).json();
    const undone = (board.habits ?? []).find(
      (h: { id: string; week?: { date: string; done: boolean }[] }) =>
        !(h.week ?? []).some((d) => d.done && d.date === board.today),
    );
    test.skip(!undone, "every habit is already checked in today");

    await page.goto(spa("home"));
    await expect(page.getByTestId("starmap-root")).toBeVisible({ timeout: 30_000 });
    const seal = page.getByTestId("habit-seal");
    await expect(seal).toBeVisible({ timeout: 15_000 });
    await expect(seal).toContainText("日课");
    // Bottom-left: beside the 星表 seal, left half of the screen.
    const sealBox = await seal.boundingBox();
    const viewport = page.viewportSize()!;
    expect(sealBox!.x).toBeLessThan(viewport.width / 2);
    expect(sealBox!.y + sealBox!.height).toBeGreaterThan(viewport.height * 0.8);
    await shot(page, "11-habit-seal");

    const item = seal.getByTestId(`habit-seal-${undone.id}`);
    await expect(item).toHaveAttribute("data-done", "false");
    // Hover → this-week 7 dots tooltip.
    await item.hover();
    await expect(page.locator('[role="tooltip"]')).toBeVisible({ timeout: 5_000 });

    const checkinResponse = page.waitForResponse(
      (res) => res.url().includes("/checkins") && res.request().method() === "POST",
    );
    await item.click();
    expect((await checkinResponse).status()).toBeLessThan(300);
    await expect(seal.getByTestId(`habit-seal-${undone.id}`)).toHaveAttribute(
      "data-done",
      "true",
      { timeout: 10_000 },
    );
    await shot(page, "12-habit-seal-checked");
  });

  test("mobile viewport: band, quick-add and archive strip stay usable", async ({
    page,
    request,
  }) => {
    // Self-seeded archived case so the strip is guaranteed present.
    const run = Date.now();
    const title = `hci-移动验收-${run}`;
    const create = await request.post(api("/project-board/cases"), { data: { title } });
    const caseId: string = (await create.json()).case.id;
    await request.post(api(`/project-board/cases/${encodeURIComponent(caseId)}/archive`));

    await page.setViewportSize({ width: 390, height: 844 });
    await openProjects(page);
    await expect(page.getByTestId("habit-band")).toBeVisible();
    await expect(page.getByTestId("archived-strip-toggle")).toBeVisible();
    const firstQuickAdd = page.locator('[data-testid^="quick-add-"]').first();
    await expect(firstQuickAdd).toBeVisible();
    await shot(page, "13-mobile-board");

    await page.goto(spa("home"));
    await expect(page.getByTestId("starmap-root")).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId("habit-seal")).toBeVisible({ timeout: 15_000 });
    await shot(page, "14-mobile-home-seal");

    await request.delete(api(`/project-board/cases/${encodeURIComponent(caseId)}`), {
      data: { confirm_title: title, record_chronicle: false },
    });
  });
});
