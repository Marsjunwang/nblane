import { expect, test } from "@playwright/test";
import type { APIRequestContext, Page } from "@playwright/test";

/**
 * Mobile viewport (375×812, iPhone) spot-checks for the SPA — the automated
 * arm of the SPA manual (docs/zh/guides/web-ui.md),
 * against the isolated sandbox (`scripts/dev-web.sh --isolated`, profile=dev).
 * Coverage:
 *  a) navigation: hamburger open/close, every menu entry clickable, 项目
 *     navigates and collapses the drawer;
 *  b) project editor: full-width form fields and adaptive task rows fit the
 *     phone without horizontal overflow;
 *  c) project touch journeys: quick-add and edit-save, vertical Queue→Doing
 *     long-press drag, the detail-card fallback, and touch navigation in the
 *     timeline and chronicle;
 *  d) content editor: top bar stays inside 375px (lesser controls in the ⋯
 *     overflow menu), 发布 opens its dialog, autosave is observable on the
 *     compact save icon, and desktop-pinned panels never auto-open drawers.
 *
 * Touch-drag geometry notes:
 *  - A dedicated one-card project keeps the empty Doing column below Queue
 *    inside the same viewport, so the CDP gesture tests the real vertical drop.
 *  - Seeding via API avoids a success notification covering the touchstart;
 *    the press-and-hold exceeds dnd-kit's 250ms TouchSensor delay.
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

async function expectDrawerFits(page: Page): Promise<void> {
  const drawer = page.locator(".mantine-Drawer-content");
  await expect
    .poll(() =>
      drawer.evaluate((el) => {
        const rect = el.getBoundingClientRect();
        return (
          rect.left >= -1 &&
          rect.right <= window.innerWidth + 1 &&
          el.scrollWidth <= el.clientWidth + 1
        );
      }),
    )
    .toBe(true);
}

/** Seed a kanban card via the API (no UI notification overlaying the board). */
async function seedKanbanCard(
  request: APIRequestContext,
  title: string,
  section = "Queue",
): Promise<string> {
  const response = await request.post(api("/kanban/cards"), {
    data: { title, section, context: "" },
  });
  expect(response.status(), "kanban card seed should succeed").toBe(201);
  return ((await response.json()) as { card: { id: string } }).card.id;
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
    const navbar = page.locator('[class*="mantine-AppShell-navbar"]');
    await expect(navbar.getByRole("link", { name: "输出工作室", exact: true })).toHaveCount(0);
    await expectNavbarOpen(page);
    await burger.tap();
    await expectNavbarCollapsed(page);

    // Click through every drawer entry. The 目标 page
    // was absorbed by the home starmap 星表 (home-editing slice, 2026-09-23);
    // the 健康 page dissolved into 证据「待补强」(2026-09-24, /health redirects);
    // the 差距分析 page was retired into 占卜 (2026-09-24, /gap APIs kept).
    const drawerItems: { label: string; url: string }[] = [
      { label: "首页", url: spa("home") },
      { label: "项目", url: spa("projects") },
      { label: "技能树", url: spa("skill-tree") },
      { label: "证据", url: spa("evidence") },
      { label: "内容工作台", url: spa("content") },
      { label: "求职工作台", url: spa("career") },
      { label: "公开站点", url: spa("public-build") },
      { label: "研究台", url: spa("research") },
    ];
    for (const item of drawerItems) {
      if ((await navbarRightEdge(page)) <= 0) {
        await burger.tap();
        await expectNavbarOpen(page);
      }
      await navbar.getByRole("link", { name: item.label, exact: true }).click();
      await expect(page, `menu entry ${item.label} should navigate`).toHaveURL(item.url);
      // Wait for the slide-out to finish before the next iteration decides
      // whether the burger needs another tap.
      await expectNavbarCollapsed(page);
    }
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

test.describe("SPA mobile 375px — 窄屏页面与编辑布局", () => {
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

  test("项目页编辑抽屉: 全宽表单、任务行自适应且文档不溢出", async ({ page, request }) => {
    const run = Date.now();
    const caseTitle = `e2e-mob-case-${run}`;
    const taskTitle = `e2e-mob-task-${run}`;
    const create = await request.post(api("/project-board/cases"), {
      data: { title: caseTitle },
    });
    expect(create.status(), "project case seed should succeed").toBe(201);
    const caseId: string = (await create.json()).case.id;
    let taskId = "";
    try {
      const task = await request.post(api(`/project-board/cases/${caseId}/tasks`), {
        data: { title: taskTitle, section: "Queue", milestone_id: "", context: "", date: "" },
      });
      expect(task.status(), "project task seed should succeed").toBe(201);
      taskId = (await task.json()).card.id;

      await page.goto(spa("projects"));
      const lane = page.getByTestId(`project-lane-${caseId}`);
      await expect(lane).toBeVisible();
      await lane.getByRole("button", { name: `编辑项目 ${caseTitle}` }).tap();
      const detail = page.getByTestId("case-detail");
      await expect(detail).toBeVisible();
      await expectDrawerFits(page);

      const titleInput = detail.getByRole("textbox", { name: "标题", exact: true });
      await expect(titleInput).toHaveCSS("font-size", "16px");
      expect(await titleInput.evaluate((el) => el.getBoundingClientRect().width)).toBeGreaterThan(300);
      await detail.getByRole("tab", { name: "任务" }).tap();
      const row = page.locator("[data-testid^='project-task-']").filter({ hasText: taskTitle });
      await expect(row).toHaveCSS("display", "grid");
      const taskSelect = row.getByRole("combobox", { name: `移动 ${taskTitle}` });
      await expect(taskSelect).toBeVisible();
      await expect(taskSelect).toHaveCSS("font-size", "16px");
      await expectDrawerFits(page);
      await expectNoHorizontalOverflow(page);

      await detail.getByRole("tab", { name: "基本信息" }).tap();
      await page.getByTestId("delete-project-button").tap();
      const confirmInput = page.getByTestId("delete-confirm-title");
      await expect(confirmInput).toBeVisible();
      await expect(confirmInput).toHaveCSS("font-size", "16px");
      await page.getByRole("button", { name: "取消", exact: true }).tap();
    } finally {
      if (taskId) {
        await request.delete(api(`/kanban/cards/${encodeURIComponent(taskId)}`), {
          data: { record_chronicle: false },
        });
      }
      await request.delete(api(`/project-board/cases/${caseId}`), {
        data: { confirm_title: caseTitle, record_chronicle: false },
      });
    }
  });

  test("研究台页: 阅读台卡片与论文索引筛选不溢出", async ({ page }) => {
    // The research page is a card-based reading desk (no wide table since
    // 2026-10): queue / recent cards plus the paper index with search+filter.
    await page.goto(spa("research"));
    await expect(page.getByRole("heading", { name: /研究台/ })).toBeVisible();
    await expect(page.getByText("论文索引", { exact: true })).toBeVisible();
    await expect(page.getByPlaceholder("搜索标题、摘要或标签")).toBeVisible();
    await expectNoHorizontalOverflow(page);
  });
});

test.describe("SPA mobile 375px — 内容编辑器", () => {
  test("顶栏不溢出,发布可达,编辑后有保存指示,持久抽屉不自动打开", async ({ page, request }) => {
    // Desktop-pinned panels must not auto-open as full drawers on a phone.
    await page.addInitScript(() => {
      window.localStorage.setItem("nblane.content.settingsOpen", "true");
      window.localStorage.setItem("nblane.content.outlineOpen", "true");
    });

    const title = `e2e-mob-editor-${Date.now()}`;
    const create = await request.post(api("/content/blog"), {
      data: { title, body: "移动端顶栏验收正文。", tags: [], summary: "" },
    });
    expect(create.status(), "content post seed should succeed").toBe(201);
    const slug: string = (await create.json()).post.slug;

    await page.goto(spa(`content/${encodeURIComponent(slug)}`));
    await expect(page.getByTestId("content-editor-topbar")).toBeVisible();
    await expect(page.locator(".bn-editor")).toBeVisible();
    await expectNoHorizontalOverflow(page);

    // Persisted pinned state must not reopen drawers on mobile.
    await expect(page.getByRole("dialog", { name: "文章设置" })).toHaveCount(0);
    await expect(page.getByRole("dialog", { name: "目录" })).toHaveCount(0);

    // Lesser controls live behind the overflow menu; 发布 stays reachable.
    const overflow = page.getByTestId("content-overflow-menu");
    await expect(overflow).toBeVisible();
    await overflow.tap();
    await expect(page.getByRole("menuitem", { name: "跳转到文章" })).toBeVisible();
    await expect(page.getByRole("menuitem", { name: "专注模式" })).toBeVisible();
    await page.getByRole("menuitem", { name: "跳转到文章" }).tap();
    await expect(page.getByTestId("content-switcher")).toBeVisible();
    await page.keyboard.press("Escape");

    const publish = page.getByTestId("content-publish");
    await expect(publish).toBeVisible();
    await publish.tap();
    // The Mantine Modal root itself is a zero-height wrapper; assert the panel.
    const publishDialog = page.getByRole("dialog", { name: "发布文章" });
    await expect(publishDialog).toBeVisible();
    await publishDialog.getByRole("button", { name: "取消" }).tap();

    // Autosave is observable on mobile: dirty → saved on the compact icon.
    const saveIndicator = page.getByTestId("content-save-state-mobile");
    await expect(saveIndicator).toBeVisible();
    await page.getByTestId("content-title").fill(`${title}（改）`);
    await expect(saveIndicator).toHaveAttribute("aria-label", /编辑中|保存中/);
    await expect(saveIndicator).toHaveAttribute("aria-label", /已保存/, { timeout: 10_000 });
    await expectNoHorizontalOverflow(page);
  });
});

test.describe("SPA mobile 375px — 项目触屏", () => {
  test("Queue/Doing 上下排列，快速添加后可在详情中编辑保存", async ({ page, request }) => {
    const run = Date.now();
    const caseTitle = `e2e-mob-flow-${run}`;
    const taskTitle = `e2e-mob-flow-task-${run}`;
    const create = await request.post(api("/project-board/cases"), { data: { title: caseTitle } });
    expect(create.status()).toBe(201);
    const caseId: string = (await create.json()).case.id;
    let taskId = "";
    try {
      await page.goto(spa("projects"));
      const lane = page.getByTestId(`project-lane-${caseId}`);
      await expect(lane).toBeVisible();
      await lane.getByTestId(`quick-add-${caseId}`).tap();
      const input = lane.getByTestId(`quick-add-input-${caseId}`);
      await expect(input).toHaveCSS("font-size", "16px");
      await input.fill(taskTitle);
      const addResponse = page.waitForResponse(
        (res) => res.url().includes(`/project-board/cases/${encodeURIComponent(caseId)}/tasks`) && res.request().method() === "POST",
      );
      await input.press("Enter");
      const added = await addResponse;
      expect(added.status()).toBeLessThan(300);
      taskId = (await added.json()).card.id;

      const detail = page.getByTestId("task-detail-card");
      await expect(detail).toBeVisible();
      await detail.getByTestId("detail-edit").tap();
      const contextInput = detail.getByTestId("edit-context");
      await expect(contextInput).toHaveCSS("font-size", "16px");
      await contextInput.fill("手机端补充的上下文");
      const patchResponse = page.waitForResponse(
        (res) => res.url().includes(`/kanban/cards/${taskId}`) && res.request().method() === "PATCH",
      );
      await detail.getByTestId("edit-save").tap();
      expect((await patchResponse).status()).toBeLessThan(300);
      await expect(detail.getByText("手机端补充的上下文", { exact: true })).toBeVisible();
      await expectNoHorizontalOverflow(page);
      await detail.getByRole("button", { name: "关闭详情" }).tap();
      await expect(lane.getByText(taskTitle, { exact: true })).toBeVisible();
    } finally {
      if (taskId) {
        await request.delete(api(`/kanban/cards/${encodeURIComponent(taskId)}`), {
          data: { record_chronicle: false },
        });
      }
      await request.delete(api(`/project-board/cases/${caseId}`), {
        data: { confirm_title: caseTitle, record_chronicle: false },
      });
    }
  });

  test("触屏长按拖拽把 Queue 卡移到下方的 Doing(真 CDP touch)", async ({
    page,
    context,
    request,
  }) => {
    const run = Date.now();
    const caseTitle = `e2e-mob-dnd-case-${run}`;
    const title = `e2e-mob-dnd-${run}`;
    const create = await request.post(api("/project-board/cases"), { data: { title: caseTitle } });
    expect(create.status()).toBe(201);
    const caseId: string = (await create.json()).case.id;
    let taskId = "";
    try {
      const task = await request.post(api(`/project-board/cases/${caseId}/tasks`), {
        data: { title, section: "Queue", milestone_id: "", context: "", date: "" },
      });
      expect(task.status()).toBe(201);
      taskId = (await task.json()).card.id;
      await page.goto(spa("projects"));
      const queue = page.getByTestId(`lane-column-${caseId}-queue`);
      const doing = page.getByTestId(`lane-column-${caseId}-doing`);
      await expect(queue.getByText(title)).toBeVisible();
      const handle = page.getByRole("button", { name: `拖拽卡片 ${title}` });
      await handle.scrollIntoViewIfNeeded();
      const handleBox = await handle.boundingBox();
      const doingBox = await doing.boundingBox();
      expect(handleBox, "drag handle must be laid out").toBeTruthy();
      expect(doingBox, "Doing must be below Queue in the same touch viewport").toBeTruthy();
      expect(doingBox!.y).toBeGreaterThan(handleBox!.y + handleBox!.height);
      expect(doingBox!.y).toBeLessThan(812);
      const startX = handleBox!.x + handleBox!.width / 2;
      const startY = handleBox!.y + handleBox!.height / 2;
      const targetX = doingBox!.x + doingBox!.width / 2;
      const targetY = doingBox!.y + doingBox!.height / 2;

      const moveResponse = page.waitForResponse(
        (res) => res.url().includes("/move") && res.request().method() === "POST",
      );
      const session = await context.newCDPSession(page);
      try {
        await session.send("Input.dispatchTouchEvent", {
          type: "touchStart",
          touchPoints: [{ x: startX, y: startY, id: 1 }],
        });
        await page.waitForTimeout(450);
        await expect(handle).toHaveAttribute("aria-pressed", "true");
        for (let step = 1; step <= 12; step++) {
          await session.send("Input.dispatchTouchEvent", {
            type: "touchMove",
            touchPoints: [{
              x: startX + ((targetX - startX) * step) / 12,
              y: startY + ((targetY - startY) * step) / 12,
              id: 1,
            }],
          });
          await page.waitForTimeout(60);
        }
        await expect(doing).toHaveAttribute("data-drop-target", "true", { timeout: 6_000 });
        await session.send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
      } finally {
        await session.send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] }).catch(() => undefined);
        await session.detach();
      }

      const response = await moveResponse;
      expect(response.status(), "touch drop should POST a successful move").toBeLessThan(300);
      expect((response.request().postDataJSON() as { target_section?: string }).target_section).toBe("Doing");
      await expect(doing.getByText(title)).toBeVisible();
      await expect(queue.getByText(title)).toHaveCount(0);
    } finally {
      if (taskId) {
        await request.delete(api(`/kanban/cards/${encodeURIComponent(taskId)}`), {
          data: { record_chronicle: false },
        });
      }
      await request.delete(api(`/project-board/cases/${caseId}`), {
        data: { confirm_title: caseTitle, record_chronicle: false },
      });
    }
  });

  test("详情卡「移至 Doing」在触屏上可用(无拖拽回退路径)", async ({ page, request }) => {
    const title = `e2e-mob-menu-${Date.now()}`;
    const taskId = await seedKanbanCard(request, title);
    try {
      await page.goto(spa("projects"));
      await page.getByTestId("lane-column-unassigned-queue").getByText(title).waitFor();
      const card = page.getByTestId("lane-column-unassigned-queue").getByText(title);
      await card.scrollIntoViewIfNeeded();
      await card.tap();
      const detail = page.getByTestId("task-detail-card");
      await expect(detail).toBeVisible();
      const moveResponse = page.waitForResponse(
        (res) => res.url().includes("/move") && res.request().method() === "POST",
      );
      await detail.getByRole("button", { name: "移至 Doing" }).tap();
      expect((await moveResponse).status()).toBeLessThan(300);
      await expect(page.getByTestId("lane-column-unassigned-doing").getByText(title)).toBeVisible();
    } finally {
      await request.delete(api(`/kanban/cards/${encodeURIComponent(taskId)}`), {
        data: { record_chronicle: false },
      });
    }
  });

  test("时间轴与大事记提供触屏翻页、回今天和缩放", async ({ page, request }) => {
    const boardResponse = await request.get(api("/projects-board"));
    expect(boardResponse.status()).toBe(200);
    const today = ((await boardResponse.json()) as { today: string }).today;
    const title = `e2e-mob-views-${Date.now()}`;
    const create = await request.post(api("/kanban/cards"), {
      data: { title, section: "Queue", context: "", planned_start: today, planned_end: today },
    });
    expect(create.status()).toBe(201);
    const taskId: string = (await create.json()).card.id;
    try {
      await page.goto(spa("projects?view=timeline&tz=month"));
      const timelineToday = page.getByTestId("timeline-today");
      await expect(timelineToday).toBeVisible();
      const initialWindow = await timelineToday.textContent();
      await page.getByTestId("timeline-older").tap();
      await expect(timelineToday).not.toHaveText(initialWindow ?? "");
      await expect(page).toHaveURL(/tws=/);
      await page.getByTestId("timeline-newer").tap();
      await expect(timelineToday).toHaveText(initialWindow ?? "");
      const zoomControl = page.getByTestId("timeline-zoom-toggle");
      expect(await zoomControl.evaluate((el) => el.getBoundingClientRect().width)).toBeGreaterThan(150);
      await zoomControl.getByText("周", { exact: true }).tap();
      await expect(page).toHaveURL(/tz=week/);
      await expectNoHorizontalOverflow(page);

      await page.goto(spa("projects?view=story"));
      const readout = page.getByTestId("chronicle-span-readout");
      await expect(readout).toBeVisible();
      const initialChronicle = await readout.textContent();
      await page.getByTestId("chronicle-older").tap();
      await expect(readout).not.toHaveText(initialChronicle ?? "");
      await page.getByTestId("chronicle-newer").tap();
      await expect(readout).toHaveText(initialChronicle ?? "");
      await page.getByRole("textbox", { name: "每行天数" }).tap();
      await page.getByRole("option", { name: "7 天/行" }).tap();
      await expect(readout).toContainText("每行 7 天");
      await page.getByTestId(`chronicle-event-${taskId}`).tap();
      const inspector = page.getByTestId("chronicle-inspector");
      await expect(inspector).toBeVisible();
      await expect(inspector).toHaveCSS("position", "relative");
      await page.getByTestId("chronicle-inspector-close").tap();
      await expect(inspector).toHaveCount(0);
      await expectNoHorizontalOverflow(page);
    } finally {
      await request.delete(api(`/kanban/cards/${encodeURIComponent(taskId)}`), {
        data: { record_chronicle: false },
      });
    }
  });
});

test.describe("SPA mobile 375px — 项目可用性回归", () => {
  test("任务详情输入不被工具栏遮挡，大事记默认 30 天且图例可点开", async ({ page, request }) => {
    const title = `e2e-mob-usability-${Date.now()}`;
    const taskId = await seedKanbanCard(request, title);
    try {
      await page.goto(spa(`projects?task=${taskId}`));
      const dateInput = page.getByLabel("排期开始");
      await dateInput.tap();
      await dateInput.fill("2026-11-01");
      await expect(dateInput).toHaveValue("2026-11-01");
      const coveredByToolbar = await dateInput.evaluate((el) => {
        const rect = el.getBoundingClientRect();
        const hit = document.elementFromPoint(rect.x + rect.width / 2, rect.y + rect.height / 2);
        return Boolean(hit?.closest("[data-testid='projects-toolbar']"));
      });
      expect(coveredByToolbar).toBe(false);
      await page.getByRole("button", { name: "关闭详情" }).tap();

      await page.goto(spa("projects?view=story"));
      await expect(page.getByRole("textbox", { name: "每行天数" })).toHaveValue("30 天/行");
      await page.getByTestId("chronicle-legend-button").tap();
      await expect(page.getByTestId("chronicle-legend-content")).toBeVisible();
      await expect(page.getByText("月白刻点 = 已完成", { exact: true })).toBeVisible();
      await expect(page.getByText("虚线框 = 待办 / 排期", { exact: true })).toBeVisible();
      await expectNoHorizontalOverflow(page);
    } finally {
      await request.delete(api(`/kanban/cards/${encodeURIComponent(taskId)}`), {
        data: { record_chronicle: false },
      });
    }
  });

  test("空泳道连续添加两条后仍保留输入框和焦点", async ({ page, request }) => {
    const run = Date.now();
    const caseTitle = `e2e-mob-continuous-${run}`;
    const create = await request.post(api("/project-board/cases"), { data: { title: caseTitle } });
    expect(create.status()).toBe(201);
    const caseId: string = (await create.json()).case.id;
    const taskIds: string[] = [];
    try {
      await page.goto(spa("projects"));
      const lane = page.getByTestId(`project-lane-${caseId}`);
      await lane.getByTestId(`quick-add-${caseId}`).tap();
      const continuous = lane.getByRole("checkbox", { name: "连续添加" });
      await continuous.tap();
      await expect(continuous).toBeChecked();
      const input = lane.getByTestId(`quick-add-input-${caseId}`);
      const add = async (title: string) => {
        await input.fill(title);
        const responsePromise = page.waitForResponse(
          (res) => res.url().includes(`/project-board/cases/${encodeURIComponent(caseId)}/tasks`) && res.request().method() === "POST",
        );
        await input.press("Enter");
        const response = await responsePromise;
        expect(response.status()).toBeLessThan(300);
        taskIds.push((await response.json()).card.id);
      };

      await add(`连续任务一-${run}`);
      await expect(input).toHaveValue("");
      await expect(input).toBeFocused();
      await add(`连续任务二-${run}`);
      await expect(input).toHaveValue("");
      await expect(input).toBeFocused();
      await expect(page.getByTestId("task-detail-card")).toHaveCount(0);
      await expect(lane.getByText(`连续任务一-${run}`, { exact: true })).toBeVisible();
      await expect(lane.getByText(`连续任务二-${run}`, { exact: true })).toBeVisible();
    } finally {
      for (const taskId of taskIds) {
        await request.delete(api(`/kanban/cards/${encodeURIComponent(taskId)}`), {
          data: { record_chronicle: false },
        });
      }
      await request.delete(api(`/project-board/cases/${caseId}`), {
        data: { confirm_title: caseTitle, record_chronicle: false },
      });
    }
  });

  test("快添请求失败时保留草稿并在输入区显示错误", async ({ page }) => {
    const lane = page.locator("[data-testid^=project-lane-]").first();
    await page.goto(spa("projects"));
    const laneId = (await lane.getAttribute("data-testid"))!.replace("project-lane-", "");
    const title = `失败时保留-${Date.now()}`;
    await lane.locator(`[data-testid="quick-add-${laneId}"]`).tap();
    const input = lane.getByTestId(`quick-add-input-${laneId}`);
    await input.fill(title);
    await page.route("**/api/v1/profiles/dev/project-board/cases/*/tasks", (route) =>
      route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ detail: "forced offline test" }),
      }),
    );
    try {
      await input.press("Enter");
      await expect(page.getByText("forced offline test", { exact: true })).toBeVisible();
      await expect(input).toHaveValue(title);
      await expect(input).toBeFocused();
      await expect(lane.getByTestId(`quick-add-editor-${laneId}`)).toBeVisible();
      await expect(page.getByTestId("task-detail-card")).toHaveCount(0);
      await expectNoHorizontalOverflow(page);
    } finally {
      await page.unroute("**/api/v1/profiles/dev/project-board/cases/*/tasks");
    }
  });
});
