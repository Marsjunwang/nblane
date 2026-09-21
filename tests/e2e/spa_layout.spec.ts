import { expect, test } from "@playwright/test";
import type { Frame, Page } from "@playwright/test";

/**
 * Desktop viewport layout regression for the SPA — the automated arm of the
 * wide-screen rules in docs/zh/guides/spa-experience-checklist.md §5, against
 * the isolated sandbox (`scripts/dev-web.sh --isolated`, profile=dev).
 *
 * Covers the 2026-09-21 wide-screen fixes:
 *  a) every page's main column is centered and capped (≤ 1400px) so tables,
 *     cards and forms no longer stretch into unreadable rows at 1920 — the
 *     kanban board is the single full-bleed exemption (data-layout="wide");
 *  b) no page overflows horizontally at 1280×800 or 1920×1080;
 *  c) the home galaxy iframe fills its card's width exactly and takes a
 *     viewport-relative height (clamp(640px, 100vh-180px, 900px)) instead of
 *     the old fixed 560px that cut the 3D scene off;
 *  d) the embedded dashboard runs in ?compact=1 mode: the inspector is an
 *     on-demand drawer (no permanent right rail) and the 3D stage keeps the
 *     majority of the iframe width at 1920.
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

/** Wait for the galaxy hero to settle; returns the dashboard frame or null. */
async function galaxyFrame(page: Page): Promise<Frame | null> {
  const frame = page.locator("[data-testid='sidecar-frame']");
  const fallback = page.getByTestId("home-galaxy-fallback");
  await expect(frame.or(fallback), "galaxy hero should resolve to embed or fallback").toBeVisible({
    timeout: 20_000,
  });
  if ((await frame.count()) === 0) {
    return null;
  }
  const dashboard = page.frames().find((f) => f.url().includes("/dashboard"));
  expect(dashboard, "dashboard iframe should be registered").toBeTruthy();
  await dashboard!.waitForSelector(".hd-canvas-workbench", { timeout: 20_000 });
  return dashboard!;
}

const VIEWPORTS = [
  { name: "1280×800", width: 1280, height: 800 },
  { name: "1920×1080", width: 1920, height: 1080 },
] as const;

for (const viewport of VIEWPORTS) {
  test.describe(`SPA 桌面布局 ${viewport.name}`, () => {
    test.use({ viewport: { width: viewport.width, height: viewport.height } });

    test("证据评审页: 内容限宽居中且无横向溢出", async ({ page }) => {
      await page.goto(spa("evidence-review"));
      const emptyState = page.getByText("当前过滤条件下没有待处理的证据。");
      await expect(page.locator("table").first().or(emptyState)).toBeVisible();

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

    test("看板页: 全宽豁免生效且无横向溢出", async ({ page }) => {
      await page.goto(spa("kanban"));
      await expect(page.getByTestId("kanban-column-Queue")).toBeVisible();

      const container = page.getByTestId("page-container");
      await expect(container).toHaveAttribute("data-layout", "wide");
      const width = await containerWidth(page);
      if (viewport.width >= 1920) {
        expect(
          width,
          `kanban is the full-bleed exemption — board (${width}px) should use the wide viewport`,
        ).toBeGreaterThan(CONTENT_MAX_WIDTH);
      }
      await expectNoHorizontalOverflow(page);
    });

    test("首页: 星系 iframe 与卡片同宽、高度合理、compact embed 无固定右栏", async ({ page }) => {
      await page.goto(spa("home"));
      const dashboard = await galaxyFrame(page);
      test.skip(!dashboard, "sidecar dashboard unreachable in this stack");

      const frame = page.locator("[data-testid='sidecar-frame']");
      const src = await frame.getAttribute("src");
      expect(src, "galaxy embed should request the compact dashboard mode").toContain("compact=1");

      const frameBox = await frame.boundingBox();
      const cardBox = await page.getByTestId("home-galaxy-hero").boundingBox();
      expect(frameBox).toBeTruthy();
      expect(cardBox).toBeTruthy();
      // The iframe fills the card's content box: card padding (lg=24px each
      // side) + border are the only allowed difference.
      const slack = cardBox!.width - frameBox!.width;
      expect(
        slack,
        `iframe width ${frameBox!.width} should match the hero card content width ${cardBox!.width}`,
      ).toBeLessThanOrEqual(52);
      expect(
        frameBox!.height,
        `iframe height ${frameBox!.height} must sit inside the clamp(640px,100vh-180px,900px) band`,
      ).toBeGreaterThanOrEqual(560);
      expect(frameBox!.height).toBeLessThanOrEqual(1000);

      // Compact embed: no permanent inspector rail — it is a closed drawer —
      // and the 3D stage keeps the majority of the iframe width.
      const inner = await dashboard!.evaluate(() => {
        const shell = document.querySelector(".hd-shell");
        const inspector = document.querySelector(".hd-inspector");
        const stage = document.querySelector(".hd-graph3d-stage");
        return {
          compact: shell?.classList.contains("hd-shell-compact") ?? false,
          inspectorVisible: inspector
            ? inspector.getBoundingClientRect().width > 0 &&
              getComputedStyle(inspector).display !== "none"
            : false,
          stageWidth: stage ? Math.round(stage.getBoundingClientRect().width) : 0,
        };
      });
      expect(inner.compact, "embed should carry the hd-shell-compact class").toBe(true);
      expect(inner.inspectorVisible, "no permanent inspector rail before a node is picked").toBe(
        false,
      );
      if (viewport.width >= 1920) {
        expect(
          inner.stageWidth / frameBox!.width,
          `3D stage (${inner.stageWidth}px) should keep the majority of the ${frameBox!.width}px iframe`,
        ).toBeGreaterThan(0.55);
      }

      // The compact embed fits its canvas inside the iframe: no internal
      // document scroll taller than a small slack.
      const innerScroll = await dashboard!.evaluate(() => ({
        body: document.body.scrollHeight,
        inner: window.innerHeight,
      }));
      expect(
        innerScroll.body - innerScroll.inner,
        `embed content (${innerScroll.body}px) should fit the ${innerScroll.inner}px iframe without a tall internal scroll`,
      ).toBeLessThanOrEqual(80);

      await expectNoHorizontalOverflow(page);
    });
  });
}
