import { expect, test } from "@playwright/test";

/**
 * Acceptance suite for the Phase 3 SPA Home: the growth starmap replaces the
 * Phase-1 dashboard cards and the sidecar 3D iframe (the Streamlit home is
 * retired with it — see docs/zh/dev/phase-plan.md).
 *
 * 1. Starmap rendering — the planisphere mounts with real profile data from
 *    the dedicated aggregation (GET /api/v1/profiles/<name>/starmap: sectors
 *    from skill categories incl. locked schema nodes, planets from projects,
 *    guest stars from evidence), the cartouche + briefing + morph toggle
 *    chrome, and hover/click → inscription detail card.
 * 2. Sidecar URL regression (kept) — `GET /api/v1/profiles/<name>/home` and
 *    `/research` used to answer the hardcoded default `http://127.0.0.1:8502`
 *    on the isolated stack; the payloads must follow the stack's reader port.
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

test.describe("SPA Home (growth starmap)", () => {
  test("starmap mounts with real data: briefing counts match the API", async ({
    page,
    request,
  }) => {
    const starmapRes = await request.get(
      `${SPA_BASE_URL}/api/v1/profiles/${encodeURIComponent(PROFILE)}/starmap`,
    );
    expect(starmapRes.status()).toBe(200);
    const starmap = await starmapRes.json();
    const activeProjects = starmap.counts.projects_active ?? 0;
    const needsReview = starmap.counts.evidence_needs_review ?? 0;

    await page.goto(spa("home"));
    const root = page.getByTestId("starmap-root");
    await expect(root).toBeVisible({ timeout: 30_000 });
    // WebGL canvas (or the explicit no-WebGL fallback, never a blank box).
    const canvas = root.locator("canvas.starmap-canvas");
    const fallback = page.getByTestId("starmap-fallback");
    await expect(canvas.or(fallback)).toBeVisible({ timeout: 30_000 });

    const briefing = page.getByTestId("starmap-briefing");
    await expect(briefing).toBeVisible();
    await expect(briefing).toContainText(`${needsReview} 条客星待评审`);
    await expect(briefing).toContainText(`${activeProjects} 颗行星在轨`);

    // Morph toggle flips the world state label.
    const toggle = page.getByTestId("starmap-toggle");
    if ((await canvas.count()) > 0) {
      await expect(toggle).toContainText("境态");
      await toggle.click();
      await expect(toggle).toContainText("图态", { timeout: 10_000 });
      await toggle.click();
      await expect(toggle).toContainText("境态", { timeout: 10_000 });
    }
  });

  test("clicking the pole star opens the inscription detail card", async ({ page }) => {
    await page.goto(spa("home"));
    const heart = page.getByTestId("starmap-heart");
    await expect(heart).toBeVisible({ timeout: 30_000 });
    const canvas = page.locator("canvas.starmap-canvas");
    test.skip((await canvas.count()) === 0, "no WebGL in this environment");

    // The pole star sits at the chart center.
    const box = (await heart.boundingBox())!;
    await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
    const detail = page.getByTestId("starmap-detail");
    await expect(detail).toHaveClass(/open/);
    await expect(detail.locator("h3")).toHaveText("北极星");
    await expect(detail.getByRole("link")).toHaveAttribute(
      "href",
      `/p/${encodeURIComponent(PROFILE)}/goals`,
    );

    // Escape dismisses.
    await page.keyboard.press("Escape");
    await expect(detail).not.toHaveClass(/open/);
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
});
