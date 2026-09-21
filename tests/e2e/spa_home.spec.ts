import { expect, test } from "@playwright/test";

/**
 * Acceptance suite for the SPA Home redesign (2026-09-20 UX batch):
 *
 * 1. iOS-style reduction — the old quick-entry button bar and the 8-card flat
 *    grid are gone; the page is 焦点卡 + 成长星系 hero + 今日待办聚合带.
 * 2. Sidecar URL regression — `GET /api/v1/profiles/<name>/home` used to
 *    answer the hardcoded default `http://127.0.0.1:8502` on the isolated
 *    stack (dev-web.sh never injected NBLANE_READER_API_BASE into the
 *    web-api tmux session), so the embedded dashboard iframe landed on a
 *    "refused to connect" page. The script now passes the resolved reader
 *    base through, so the sandbox home/research payloads point at 18502.
 * 3. Reachability gating — the SPA probes the sidecar before embedding:
 *    reachable → full-width galaxy iframe (asserted here as a real 200
 *    document response, i.e. NOT a browser error page); unreachable → a
 *    static metrics band instead of a refused-connection gray box.
 *
 * Self-contained like spa_smoke.spec.ts: targets the SPA backend
 * (web_api), default http://127.0.0.1:18504 (isolated sandbox, profile=dev).
 */

const SPA_BASE_URL = (process.env.NBLANE_E2E_SPA_BASE_URL || "http://127.0.0.1:18504").replace(
  /\/+$/,
  "",
);
const PROFILE = process.env.NBLANE_E2E_PROFILE || "dev";

// Port convention: reader sidecar = SPA backend port − 2
// (8504→8502 default dev, 18504→18502 isolated dev).
const spaUrl = new URL(SPA_BASE_URL);
const EXPECTED_SIDECAR_BASE = `${spaUrl.protocol}//${spaUrl.hostname}:${Number(spaUrl.port) - 2}`;

function spa(path: string): string {
  return `${SPA_BASE_URL}/p/${encodeURIComponent(PROFILE)}/${path}`;
}

test.describe("SPA Home (UX redesign + sidecar cohesion)", () => {
  test("focus card + today band render; quick-entry bar and flat grid are gone", async ({
    page,
    request,
  }) => {
    const homeResponse = await request.get(
      `${SPA_BASE_URL}/api/v1/profiles/${encodeURIComponent(PROFILE)}/home`,
    );
    expect(homeResponse.status()).toBe(200);
    const home = await homeResponse.json();

    await page.goto(spa("home"));

    // Focus card: north star + primary goal (dev profile has both set).
    const focus = page.getByTestId("home-focus-card");
    await expect(focus).toBeVisible();
    if (home.north_star?.is_set) {
      await expect(
        page.getByText(home.north_star.brief || home.north_star.full),
      ).toBeVisible();
    }
    if (home.primary_goal) {
      await expect(focus.getByText(home.primary_goal.title)).toBeVisible();
      await expect(focus.getByRole("progressbar")).toBeVisible();
    }

    // Removed in the redesign: the 7 quick-entry buttons and the flat cards.
    for (const label of ["看板", "技能树", "目标", "证据评审", "周回顾", "研究台", "输出工作室"]) {
      await expect(page.getByRole("button", { name: label, exact: true })).toHaveCount(0);
    }
    for (const testId of [
      "home-skills-card",
      "home-kanban-card",
      "home-evidence-card",
      "home-research-card",
      "home-activity-card",
      "home-projects-card",
      "home-health-card",
      "home-dashboard-card",
    ]) {
      await expect(page.getByTestId(testId)).toHaveCount(0);
    }

    // Today band aggregates approvals / reviews / doing and links out.
    const band = page.getByTestId("home-today-band");
    await expect(band).toBeVisible();
    if ((home.agent_activity?.pending_total ?? 0) > 0) {
      const approvals = band.getByTestId("home-todo-approvals");
      await expect(approvals).toBeVisible();
      await approvals.click();
      await page.waitForURL(`**/p/${encodeURIComponent(PROFILE)}/activity`);
      await page.goto(spa("home"));
    }
    if ((home.evidence?.needs_review_count ?? 0) > 0) {
      await expect(band.getByTestId("home-todo-review")).toBeVisible();
    }
    if ((home.kanban?.doing ?? []).length > 0) {
      await expect(band.getByTestId("home-todo-doing").first()).toBeVisible();
    }
  });

  test("sidecar coordinates point at this stack's reader port (18502 in the sandbox)", async ({
    request,
  }) => {
    for (const endpoint of ["home", "research"]) {
      const response = await request.get(
        `${SPA_BASE_URL}/api/v1/profiles/${encodeURIComponent(PROFILE)}/${endpoint}`,
      );
      expect(response.status()).toBe(200);
      const sidecar = (await response.json()).sidecar;
      // The 2026-09-20 regression: base stayed on the hardcoded default 8502
      // because the web-api tmux session never got NBLANE_READER_API_BASE.
      expect(
        sidecar.base,
        `${endpoint}.sidecar.base must follow the stack's reader port, not the 8502 default`,
      ).toBe(EXPECTED_SIDECAR_BASE);
      expect(sidecar.configured).toBe(true);
      expect(sidecar.dashboard_url).toContain(`${EXPECTED_SIDECAR_BASE}/dashboard`);
    }
  });

  test("reachable sidecar embeds the galaxy iframe and it really loads (no refused page)", async ({
    page,
    request,
  }) => {
    const homeResponse = await request.get(
      `${SPA_BASE_URL}/api/v1/profiles/${encodeURIComponent(PROFILE)}/home`,
    );
    const sidecar = (await homeResponse.json()).sidecar;

    // The probe must hit the sidecar origin, and the dashboard document must
    // answer 200 — a refused connection would produce no response at all.
    const probeSeen = page.waitForRequest(`${sidecar.base}/auth/session-ok`);
    const dashboardLoaded = page.waitForResponse(
      (res) => res.url().startsWith(`${sidecar.base}/dashboard`),
      { timeout: 20_000 },
    );
    await page.goto(spa("home"));
    await probeSeen;

    const frame = page.locator('iframe[data-testid="sidecar-frame"]');
    await expect(frame).toBeVisible();
    await expect(frame).toHaveAttribute("src", sidecar.dashboard_url);
    const response = await dashboardLoaded;
    expect(response.status(), "dashboard document should load, not refuse").toBe(200);

    // Metric chips overlay the galaxy and dive into their pages.
    const chips = page.getByTestId("home-galaxy-metrics");
    await expect(chips).toBeVisible();
    await expect(page.getByTestId("home-galaxy-fallback")).toHaveCount(0);
  });

  test("unreachable sidecar degrades to a static metrics band instead of an error frame", async ({
    page,
  }) => {
    // Simulate the refused connection by aborting the reachability probe.
    await page.route("**/auth/session-ok", (route) => route.abort());
    await page.goto(spa("home"));

    const fallback = page.getByTestId("home-galaxy-fallback");
    await expect(fallback).toBeVisible({ timeout: 15_000 });
    // No iframe is mounted at all — the browser can never render its
    // "refused to connect" error page inside the page.
    await expect(page.locator('iframe[data-testid="sidecar-frame"]')).toHaveCount(0);
    await expect(fallback.getByText(/3D 仪表盘服务暂时不可达/)).toBeVisible();
    await expect(fallback.getByRole("button", { name: "重试" })).toBeVisible();
  });
});
