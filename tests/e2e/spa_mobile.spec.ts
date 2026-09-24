import { expect, test } from "@playwright/test";
import type { APIRequestContext, Page } from "@playwright/test";

/**
 * Mobile viewport (375×812, iPhone) spot-checks for the SPA — the automated
 * arm of the experience manual §5 (docs/zh/guides/spa-experience-checklist.md),
 * against the isolated sandbox (`scripts/dev-web.sh --isolated`, profile=dev).
 * 9 tests across four groups:
 *
 * Coverage:
 *  a) navigation: hamburger open/close, every menu entry clickable, 项目
 *     navigates and collapses the drawer;
 *  b) the wide-content pages (周回顾/项目抽屉/研究台 keep wide tables; 证据 is
 *     now the Phase 1 single page with the five-stage nav): tables stay
 *     inside their Table.ScrollContainer and the document never overflows
 *     horizontally;
 *  c) projects lane touch drag: a real CDP touch gesture (press-and-hold past
 *     the dnd-kit TouchSensor 250ms delay, then drag) moves a card
 *     Queue→Doing inside its lane, plus the detail-card 移至 Doing fallback
 *     over tap;
 *  d) inbox quick capture at 375px: usable input width, submit succeeds, no
 *     horizontal overflow.
 *
 * Touch-drag geometry notes (hard-won, do not "simplify"):
 *  - The dragged card is seeded via API and moved to the Queue HEAD: the
 *    columns are only as tall as their content, so at the tail card's scroll
 *    depth the shorter columns' boxes have long ended and the pointer hovers
 *    dead space (collision resolves nowhere). At the column head all four
 *    column boxes coexist on the first screen.
 *  - Seeding via API (not the UI form) avoids the success notification
 *    overlaying the card and swallowing the touchstart.
 *  - Doing and Queue never share a 375px viewport (Doing 16..296, Queue
 *    608..888), so the drag parks near the left edge with a small jiggle and
 *    lets dnd-kit auto-scroll the column strip until Doing slides under the
 *    pointer (observed: highlight fires around scrollLeft≈250).
 *
 * Every entity the suite creates carries a unique `e2e-mob-<ts>` prefix so
 * reruns never collide with existing sandbox data or other specs.
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

test.use({
  viewport: { width: 375, height: 812 },
  hasTouch: true,
  isMobile: true,
});

/** Document-level horizontal overflow check (mobile must never break out). */
async function expectNoHorizontalOverflow(page: Page): Promise<void> {
  const metrics = await page.evaluate(() => ({
    inner: window.innerWidth,
    doc: document.documentElement.scrollWidth,
    body: document.body.scrollWidth,
  }));
  expect(
    metrics.doc,
    `documentElement.scrollWidth (${metrics.doc}) must not exceed the ${metrics.inner}px viewport`,
  ).toBeLessThanOrEqual(metrics.inner + 2);
  expect(
    metrics.body,
    `body.scrollWidth (${metrics.body}) must not exceed the ${metrics.inner}px viewport`,
  ).toBeLessThanOrEqual(metrics.inner + 2);
}

/**
 * Every table on the page must live inside a Mantine Table.ScrollContainer
 * whose viewport clips the overflow (scrollWidth > clientWidth at 375px) and
 * actually scrolls horizontally.
 */
async function expectTablesScrollable(page: Page, minContainers = 1): Promise<void> {
  const containers = page.locator(".mantine-TableScrollContainer-scrollContainer");
  const count = await containers.count();
  expect(count, "page should render its table(s) inside Table.ScrollContainer").toBeGreaterThanOrEqual(
    minContainers,
  );
  for (let i = 0; i < count; i++) {
    const result = await containers.nth(i).evaluate((el) => {
      const viewport = el.querySelector("[class*='ScrollArea-viewport']") as HTMLElement | null;
      const target = viewport ?? (el as HTMLElement);
      const wider = target.scrollWidth > target.clientWidth;
      let scrolled = true;
      if (wider) {
        target.scrollLeft = 80;
        scrolled = target.scrollLeft > 0;
        target.scrollLeft = 0;
      }
      return { wider, scrolled, scrollWidth: target.scrollWidth, clientWidth: target.clientWidth };
    });
    expect(
      result.wider,
      `table scroll container ${i} should be wider than its ${result.clientWidth}px viewport ` +
        `(scrollWidth=${result.scrollWidth}) — the wide-table scenario this test exists for`,
    ).toBe(true);
    expect(result.scrolled, `table scroll container ${i} must scroll horizontally`).toBe(true);
  }
}

/** Seed a kanban card via the API (no UI notification overlaying the board). */
async function seedKanbanCard(
  request: APIRequestContext,
  title: string,
  section = "Queue",
): Promise<void> {
  const response = await request.post(api("/kanban/cards"), {
    data: { title, section, context: "" },
  });
  expect(response.status(), "kanban card seed should succeed").toBe(201);
}

/** Navbar slide state: Mantine collapses with translateX(-width), display stays flex. */
async function navbarRightEdge(page: Page): Promise<number> {
  return page.evaluate(() => {
    const navbar = document.querySelector("[class*='AppShell-navbar']");
    return navbar ? navbar.getBoundingClientRect().right : -1;
  });
}

// The drawer slides with a transition — always assert through a poll.
async function expectNavbarCollapsed(page: Page): Promise<void> {
  await expect.poll(() => navbarRightEdge(page), { timeout: 3_000 }).toBeLessThanOrEqual(0);
}

async function expectNavbarOpen(page: Page): Promise<void> {
  await expect.poll(() => navbarRightEdge(page), { timeout: 3_000 }).toBeGreaterThan(0);
}

test.describe("SPA mobile 375px — 导航", () => {
  test("汉堡菜单可开合,全部菜单项可点,点项目正确跳转并收合", async ({ page }) => {
    await page.goto(spa("home"));
    const burger = page.getByRole("button", { name: "切换导航" });
    await expect(burger).toBeVisible();

    // Collapsed on load (off-canvas); tap opens, tap again closes.
    await expectNavbarCollapsed(page);
    await burger.tap();
    await expect(page.getByRole("link", { name: "项目", exact: true })).toBeVisible();
    await expectNavbarOpen(page);
    await burger.tap();
    await expectNavbarCollapsed(page);

    // Click through every drawer entry: 10 profile pages + 档案列表, plus the
    // header 助手 entry (12 clickable entries total on mobile). The 目标 page
    // was absorbed by the home starmap 星表 (home-editing slice, 2026-09-23);
    // the 健康 page dissolved into 证据「待补强」(2026-09-24, /health redirects);
    // the 差距分析 page was retired into 占卜 (2026-09-24, /gap APIs kept).
    const drawerItems: { label: string; url: string }[] = [
      { label: "首页", url: spa("home") },
      { label: "项目", url: spa("projects") },
      { label: "技能树", url: spa("skill-tree") },
      { label: "证据", url: spa("evidence") },
      { label: "周回顾", url: spa("review") },
      { label: "输出工作室", url: spa("studio") },
      { label: "公开构建", url: spa("public-build") },
      { label: "研究台", url: spa("research") },
      { label: "收件箱", url: spa("inbox") },
      { label: "代理活动", url: spa("activity") },
    ];
    for (const item of drawerItems) {
      if ((await navbarRightEdge(page)) <= 0) {
        await burger.tap();
        await expectNavbarOpen(page);
      }
      await page.getByRole("link", { name: item.label, exact: true }).click();
      await expect(page, `menu entry ${item.label} should navigate`).toHaveURL(item.url);
      // Wait for the slide-out to finish before the next iteration decides
      // whether the burger needs another tap.
      await expectNavbarCollapsed(page);
    }

    // The header 助手 entry stays reachable on mobile (12th entry).
    await page.getByRole("link", { name: "助手" }).click();
    await expect(page).toHaveURL(`${SPA_BASE_URL}/assistant`);

    // 档案列表 leaves the profile context to the profiles list.
    await page.goto(spa("home"));
    await burger.tap();
    await page.getByRole("link", { name: "档案列表", exact: true }).click();
    await expect(page).toHaveURL(`${SPA_BASE_URL}/`);

    // Explicit 项目 journey: open → tap 项目 → correct page, drawer collapsed.
    await page.goto(spa("home"));
    await burger.tap();
    await page.getByRole("link", { name: "项目", exact: true }).click();
    await expect(page).toHaveURL(spa("projects"));
    await expect(page.getByTestId("projects-toolbar")).toBeVisible();
    await expectNavbarCollapsed(page);
    await expectNoHorizontalOverflow(page);
  });
});

test.describe("SPA mobile 375px — 宽表格五页", () => {
  test("证据页(单页五阶段): 阶段导航可见且文档不溢出", async ({ page }) => {
    await page.goto(spa("evidence"));
    // Phase 1 single page: card list + stage nav instead of a wide table.
    await expect(page.getByTestId("stage-nav")).toBeVisible();
    await expectNoHorizontalOverflow(page);
  });

  test("证据评审旧路由: 重定向进证据单页且文档不溢出", async ({ page }) => {
    await page.goto(spa("evidence-review"));
    // /evidence-review redirects to /evidence?stage=review; the queue may be
    // empty (consumable) — the stage nav renders either way.
    await expect(page.getByTestId("stage-nav")).toBeVisible();
    await expect(page).toHaveURL(/\/evidence\?stage=review/);
    await expectNoHorizontalOverflow(page);
  });

  test("周回顾页: 近 30 天窗口候选表格横向滚动且文档不溢出", async ({ page, request }) => {
    // Seed a Done card dated today so the 近 30 天 window always has at least
    // one 证据候选 row (the default tab).
    const title = `e2e-mob-review-${Date.now()}`;
    await seedKanbanCard(request, title);
    const done = await request.post(api(`/kanban/cards/${encodeURIComponent(title)}/done`));
    expect(done.status(), "mark-done seed should succeed").toBeLessThan(300);

    await page.goto(spa("review"));
    await page.getByRole("textbox", { name: "时间窗口预设" }).click();
    await page.getByRole("option", { name: "近 30 天" }).click();
    await expect(page.locator("table").first()).toBeVisible();
    await expect(page.getByText(title).first()).toBeVisible();
    await expectTablesScrollable(page);
    await expectNoHorizontalOverflow(page);
  });

  test("项目页编辑抽屉: 案例任务表格横向滚动且文档不溢出", async ({ page, request }) => {
    // Seed a case with one task so the drawer 任务 tab renders its table.
    const run = Date.now();
    const create = await request.post(api("/project-board/cases"), {
      data: { title: `e2e-mob-case-${run}` },
    });
    expect(create.status(), "project case seed should succeed").toBe(201);
    const caseId: string = (await create.json()).case.id;
    const task = await request.post(api(`/project-board/cases/${caseId}/tasks`), {
      data: { title: `e2e-mob-task-${run}`, section: "Queue", milestone_id: "", context: "", date: "" },
    });
    expect(task.status(), "project task seed should succeed").toBe(201);

    await page.goto(spa("projects"));
    const lane = page.getByTestId(`project-lane-${caseId}`);
    await expect(lane).toBeVisible();
    await lane.getByRole("button", { name: `编辑项目 e2e-mob-case-${run}` }).tap();
    const detail = page.getByTestId("case-detail");
    await expect(detail).toBeVisible();
    await detail.getByRole("tab", { name: "任务" }).tap();
    await expect(page.locator("table").first()).toBeVisible();
    await expect(
      page.locator("[data-testid^='project-task-']").getByText(`e2e-mob-task-${run}`),
    ).toBeVisible();
    await expectTablesScrollable(page);
    await expectNoHorizontalOverflow(page);
  });

  test("研究台页: 最近来源表格横向滚动且文档不溢出", async ({ page }) => {
    await page.goto(spa("research"));
    await expect(page.locator("table").first()).toBeVisible();
    await expectTablesScrollable(page);
    await expectNoHorizontalOverflow(page);
  });
});

test.describe("SPA mobile 375px — 项目泳道触屏", () => {
  test("触屏长按拖拽把 Queue 卡移到 Doing(真 CDP touch + auto-scroll)", async ({
    page,
    context,
    request,
  }) => {
    const title = `e2e-mob-dnd-${Date.now()}`;
    await seedKanbanCard(request, title);
    // Move to the Queue head: at the tail card's scroll depth the shorter
    // column's box has ended and the pointer would hover dead space.
    const toHead = await request.post(api(`/kanban/cards/${encodeURIComponent(title)}/move`), {
      data: { target_section: "Queue", to_index: 0 },
    });
    expect(toHead.status()).toBeLessThan(300);

    // Seeded without a project → the 未归属 lane (Queue left, Doing right).
    await page.goto(spa("projects"));
    await page.getByTestId("lane-column-unassigned-queue").getByText(title).first().waitFor();
    const handle = page.getByRole("button", { name: `拖拽卡片 ${title}` }).first();
    await handle.scrollIntoViewIfNeeded();
    const handleBox = await handle.boundingBox();
    expect(handleBox, "drag handle must be laid out").toBeTruthy();
    const startX = handleBox!.x + handleBox!.width / 2;
    const startY = handleBox!.y + handleBox!.height / 2;

    const moveResponse = page.waitForResponse(
      (res) => res.url().includes("/move") && res.request().method() === "POST",
    );
    const session = await context.newCDPSession(page);
    try {
      await session.send("Input.dispatchTouchEvent", {
        type: "touchStart",
        touchPoints: [{ x: startX, y: startY, id: 1 }],
      });
      // Press-and-hold past the TouchSensor activation delay (250ms).
      await page.waitForTimeout(450);
      await expect(handle, "long-press should lift the card (TouchSensor active)").toHaveAttribute(
        "aria-pressed",
        "true",
      );

      // Drag briskly toward the right edge, then jiggle: dnd-kit auto-scrolls
      // the lane strip until Doing slides under the parked pointer.
      for (let x = startX; x < 350; x += 30) {
        await session.send("Input.dispatchTouchEvent", {
          type: "touchMove",
          touchPoints: [{ x, y: startY, id: 1 }],
        });
        await page.waitForTimeout(60);
      }
      const doingHighlight = page.locator("[data-drop-target='true']");
      let highlighted = false;
      for (let i = 0; i < 40 && !highlighted; i++) {
        await session.send("Input.dispatchTouchEvent", {
          type: "touchMove",
          touchPoints: [{ x: 345 - (i % 2 === 0 ? 0 : 6), y: startY, id: 1 }],
        });
        await page.waitForTimeout(120);
        highlighted =
          (await doingHighlight.getAttribute("data-testid")) === "lane-column-unassigned-doing";
      }
      expect(highlighted, "auto-scroll should bring the Doing column under the pointer").toBe(true);
      await session.send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
    } finally {
      await session.detach();
    }

    const response = await moveResponse;
    expect(response.status(), "touch drop should POST a successful move").toBeLessThan(300);
    expect((response.request().postDataJSON() as { target_section?: string }).target_section).toBe(
      "Doing",
    );
    await expect(page.getByTestId("lane-column-unassigned-doing").getByText(title)).toBeVisible();
    await expect(page.getByTestId("lane-column-unassigned-queue").getByText(title)).toHaveCount(0);
  });

  test("详情卡「移至 Doing」在触屏上可用(无拖拽回退路径)", async ({ page, request }) => {
    const title = `e2e-mob-menu-${Date.now()}`;
    await seedKanbanCard(request, title);
    await page.goto(spa("projects"));
    await page.getByTestId("lane-column-unassigned-queue").getByText(title).waitFor();

    // Tap the card (not a drag) → the inscription detail card opens.
    const card = page.getByTestId("lane-column-unassigned-queue").getByText(title);
    await card.scrollIntoViewIfNeeded();
    await card.tap();
    await expect(page.getByTestId("task-detail-card")).toBeVisible();

    const moveResponse = page.waitForResponse(
      (res) => res.url().includes("/move") && res.request().method() === "POST",
    );
    await page.getByRole("button", { name: "移至 Doing" }).tap();
    expect((await moveResponse).status()).toBeLessThan(300);
    await expect(page.getByTestId("lane-column-unassigned-doing").getByText(title)).toBeVisible();
  });
});

test.describe("SPA mobile 375px — 收件箱", () => {
  test("快速捕获: 输入可用、提交成功、无横向溢出", async ({ page }) => {
    await page.goto(spa("inbox"));
    const title = `e2e-mob-inbox-${Date.now()}`;
    const input = page.getByLabel("随手记");
    await expect(input).toBeVisible();

    // One-handed usability: the title field must stay wide enough to see what
    // you type (regression: it used to be squeezed to ~26px by the fixed-width
    // tags field + submit button on a nowrap row).
    const inputBox = await input.boundingBox();
    expect(inputBox, "capture input must be laid out").toBeTruthy();
    expect(
      inputBox!.width,
      `capture input width ${inputBox!.width}px is too narrow for a phone`,
    ).toBeGreaterThan(140);

    await input.fill(title);
    const captureResponse = page.waitForResponse(
      (res) =>
        res.url().includes(`/profiles/${encodeURIComponent(PROFILE)}/inbox`) &&
        res.request().method() === "POST",
    );
    await page.getByRole("button", { name: "记录" }).tap();
    expect((await captureResponse).status(), "capture should succeed").toBeLessThan(300);
    await expect(page.getByText(title)).toBeVisible();
    await expectNoHorizontalOverflow(page);
  });
});
