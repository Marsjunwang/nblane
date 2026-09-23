import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";

/**
 * Desktop viewport layout regression for the SPA — the automated arm of the
 * wide-screen rules in docs/zh/guides/spa-experience-checklist.md §5, against
 * the isolated sandbox (`scripts/dev-web.sh --isolated`, profile=dev).
 *
 * Covers the 2026-09-21 wide-screen fixes (plus the Phase 3 home swap and the
 * 2026-09-23 dark-unification/icon-rail pass):
 *  a) every page's main column is centered and capped (≤ 1400px) so tables,
 *     cards and forms no longer stretch into unreadable rows at 1920 — the
 *     home starmap (immersive full-bleed), the projects board and the
 *     workshop terminal are the full-bleed exemptions (data-layout="wide");
 *  b) no page overflows horizontally at 1280×800 or 1920×1080;
 *  c) the home growth starmap fills the whole AppShell main area (padding 0,
 *     no inner card frame) and takes the full viewport height under the 56px
 *     header;
 *  d) the desktop sidebar is a 56px icon rail that expands on demand.
 */

const SPA_BASE_URL = (process.env.NBLANE_E2E_SPA_BASE_URL || "http://127.0.0.1:18504").replace(
  /\/+$/,
  "",
);
const PROFILE = process.env.NBLANE_E2E_PROFILE || "dev";
const CONTENT_MAX_WIDTH = 1400;

function spa(path: string): string {
  return `${SPA_BASE_URL}/p/${encodeURIComponent(PROFILE)}/${path}`;
}

/** Document-level horizontal overflow check (must never happen on desktop). */
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

async function containerWidth(page: Page): Promise<number> {
  const box = await page.getByTestId("page-container").boundingBox();
  expect(box, "page-container must be laid out").toBeTruthy();
  return Math.round(box!.width);
}

const VIEWPORTS = [
  { name: "1280×800", width: 1280, height: 800 },
  { name: "1920×1080", width: 1920, height: 1080 },
] as const;

for (const viewport of VIEWPORTS) {
  test.describe(`SPA 桌面布局 ${viewport.name}`, () => {
    test.use({ viewport: { width: viewport.width, height: viewport.height } });

    test("证据页(含旧评审页重定向): 内容限宽居中且无横向溢出", async ({ page }) => {
      await page.goto(spa("evidence-review"));
      // Redirects into the single Evidence page (五阶段工序).
      await expect(page.getByTestId("stage-nav")).toBeVisible();

      const container = page.getByTestId("page-container");
      await expect(container).toHaveAttribute("data-layout", "capped");
      const width = await containerWidth(page);
      expect(
        width,
        `content column (${width}px) must stay within the ${CONTENT_MAX_WIDTH}px cap`,
      ).toBeLessThanOrEqual(CONTENT_MAX_WIDTH);
      if (viewport.width >= 1920) {
        // The cap must actually engage on wide monitors (not just "narrower
        // than the cap because the viewport is narrow").
        expect(width, "cap should engage at 1920 (column near the cap)").toBeGreaterThan(1100);
      }
      await expectNoHorizontalOverflow(page);
    });

    test("输出工作室页: 内容限宽居中且无横向溢出", async ({ page }) => {
      await page.goto(spa("studio"));
      await expect(page.getByRole("heading", { name: /输出工作室/ })).toBeVisible();

      const width = await containerWidth(page);
      expect(width).toBeLessThanOrEqual(CONTENT_MAX_WIDTH);
      if (viewport.width >= 1920) {
        expect(width).toBeGreaterThan(1100);
      }
      await expectNoHorizontalOverflow(page);
    });

    test("项目页: 全宽豁免生效且无横向溢出", async ({ page }) => {
      // /kanban redirects to /projects (legacy deep links stay alive).
      await page.goto(spa("kanban"));
      await expect(page.getByTestId("projects-toolbar")).toBeVisible();

      const container = page.getByTestId("page-container");
      await expect(container).toHaveAttribute("data-layout", "wide");
      const width = await containerWidth(page);
      if (viewport.width >= 1920) {
        expect(
          width,
          `projects is the full-bleed exemption — board (${width}px) should use the wide viewport`,
        ).toBeGreaterThan(CONTENT_MAX_WIDTH);
      }
      await expectNoHorizontalOverflow(page);
    });

    test("首页: 星图全出血填满内容区、高度随视口、无横向溢出", async ({ page }) => {
      // Phase 3 + dark unification: the home is the growth starmap rendered
      // full-bleed — AppShell padding drops to 0, so there is no inner card
      // frame or color seam around the indigo canvas.
      await page.goto(spa("home"));
      const root = page.getByTestId("starmap-root");
      await expect(root).toBeVisible({ timeout: 30_000 });
      // WebGL canvas, or the explicit no-WebGL fallback — never a blank box.
      await expect(
        root.locator("canvas.starmap-canvas").or(page.getByTestId("starmap-fallback")),
      ).toBeVisible({ timeout: 30_000 });

      const container = page.getByTestId("page-container");
      await expect(container).toHaveAttribute("data-layout", "wide");
      const rootBox = await root.boundingBox();
      const containerBox = await container.boundingBox();
      expect(rootBox).toBeTruthy();
      expect(containerBox).toBeTruthy();
      // Full bleed: the starmap matches the container exactly on both axes —
      // any slack (padding/frame) would show up as a seam here.
      expect(
        Math.abs(containerBox!.width - rootBox!.width),
        `starmap width ${rootBox!.width} should match the full-bleed container ${containerBox!.width}`,
      ).toBeLessThanOrEqual(4);
      expect(
        Math.abs(containerBox!.x - rootBox!.x),
        `starmap x ${rootBox!.x} should align with the container x ${containerBox!.x}`,
      ).toBeLessThanOrEqual(2);
      expect(
        rootBox!.height,
        `starmap height ${rootBox!.height} must be 100dvh minus the 56px header`,
      ).toBeGreaterThanOrEqual(viewport.height - 56 - 4);

      await expectNoHorizontalOverflow(page);
    });
  });
}

test.describe("SPA 桌面图标导航栏", () => {
  test.use({ viewport: { width: 1280, height: 800 } });

  test("默认 56px 图标栏收起, 可展开为标签栏并记住状态", async ({ page }) => {
    await page.goto(spa("home"));
    await expect(page.getByTestId("starmap-root")).toBeVisible({ timeout: 30_000 });
    const navbar = page.locator("[class*='AppShell-navbar']");
    await expect(navbar).toBeVisible();

    // Collapsed icon rail (~56px): links are icon-only but keep aria-labels.
    await expect
      .poll(async () => Math.round((await navbar.boundingBox())!.width))
      .toBeLessThanOrEqual(64);
    await expect(navbar.getByRole("link", { name: "首页", exact: true })).toBeAttached();
    // Labels are not rendered as visible text while collapsed.
    await expect(navbar.getByText("技能树", { exact: true })).toBeHidden();

    // Expand to the full labelled rail.
    await page.getByTestId("rail-toggle").click();
    await expect
      .poll(async () => Math.round((await navbar.boundingBox())!.width))
      .toBeGreaterThan(150);
    await expect(navbar.getByText("技能树", { exact: true })).toBeVisible();

    // Persisted across reloads.
    await page.reload();
    await expect(page.getByTestId("starmap-root")).toBeVisible({ timeout: 30_000 });
    await expect
      .poll(async () => Math.round((await navbar.boundingBox())!.width))
      .toBeGreaterThan(150);

    // Collapse again to leave a clean state.
    await page.getByTestId("rail-toggle").click();
    await expect
      .poll(async () => Math.round((await navbar.boundingBox())!.width))
      .toBeLessThanOrEqual(64);
  });
});
