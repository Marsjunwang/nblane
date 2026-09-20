import { expect, test } from "@playwright/test";

/**
 * Smoke suite for the React SPA served by the FastAPI backend
 * (nblane.web_api, one process for /api/v1 + web_ui/static).
 *
 * Self-contained: does NOT use helpers.ts (those target the Streamlit UI and
 * the Reader API sidecar). The SPA base URL is independent of the Streamlit
 * baseURL in playwright.config.ts:
 *
 *   default dev  (`scripts/dev-web.sh`):            http://127.0.0.1:8504
 *   isolated dev (`scripts/dev-web.sh --isolated`): http://127.0.0.1:18504
 *
 * Override with NBLANE_E2E_SPA_BASE_URL. The default matches the isolated
 * instance so a bare run never collides with a live dev server.
 *
 * Data-shape independence: the isolated data root (.dev-data) may hold any
 * number of profiles, so UI assertions branch on what GET /api/v1/profiles
 * actually returns instead of hardcoding profile names.
 */

const SPA_BASE_URL = (process.env.NBLANE_E2E_SPA_BASE_URL || "http://127.0.0.1:18504").replace(
  /\/+$/,
  "",
);

function spaURL(path: string = "/"): string {
  return new URL(path, `${SPA_BASE_URL}/`).toString();
}

/** Absolute asset paths (src=/assets/…, href=/assets/…) referenced by the html. */
function extractAssetPaths(html: string): string[] {
  const paths = new Set<string>();
  for (const match of html.matchAll(/(?:src|href)="(\/assets\/[^"]+)"/g)) {
    paths.add(match[1]);
  }
  return [...paths];
}

test.describe("SPA smoke (web_api on " + SPA_BASE_URL + ")", () => {
  test("GET / serves the SPA html and its hashed assets load", async ({ request }) => {
    const response = await request.get(spaURL("/"));
    expect(response.status()).toBe(200);
    expect(response.headers()["content-type"]).toContain("text/html");
    const html = await response.text();
    // Vite entry shell: title + React mount point.
    expect(html).toContain("<title>nblane</title>");
    expect(html).toContain('<div id="root">');

    const assetPaths = extractAssetPaths(html);
    expect(assetPaths.length).toBeGreaterThan(0);
    expect(assetPaths.some((p) => p.endsWith(".js"))).toBe(true);
    expect(assetPaths.some((p) => p.endsWith(".css"))).toBe(true);
    for (const assetPath of assetPaths) {
      const assetResponse = await request.get(spaURL(assetPath));
      expect(assetResponse.status(), `asset ${assetPath} should load`).toBe(200);
    }
  });

  test("client-route fallback: /p/anything/kanban serves the SPA html, not 404", async ({
    request,
  }) => {
    const response = await request.get(spaURL("/p/anything/kanban"));
    expect(response.status()).toBe(200);
    expect(response.headers()["content-type"]).toContain("text/html");
    const html = await response.text();
    expect(html).toContain('<div id="root">');
  });

  test("GET /api/v1/health returns ok", async ({ request }) => {
    const response = await request.get(spaURL("/api/v1/health"));
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.ok).toBe(true);
  });

  test("UI smoke: profiles view, first profile kanban, assistant page", async ({
    page,
    request,
  }) => {
    // Branch UI expectations on the real data root via the API.
    const profilesResponse = await request.get(spaURL("/api/v1/profiles"));
    expect(profilesResponse.status()).toBe(200);
    const profiles: Array<{ name: string }> = await profilesResponse.json();

    await page.goto(spaURL("/"));

    // Auth-off guard: NBLANE_AUTH_FILE is unset on the isolated stack, so
    // /auth/me answers a synthetic admin and RequireAuth must NOT bounce the
    // browser to /login.
    await expect(page.getByRole("heading", { name: "档案列表" })).toBeVisible();
    expect(page.url()).not.toContain("/login");

    if (profiles.length === 0) {
      // Empty data root: the profiles page shows its empty state instead of cards.
      await expect(page.getByText(/还没有档案/)).toBeVisible();
    } else {
      const first = profiles[0];
      // The profiles grid renders one card per profile; each card links to
      // the profile health page.
      const firstCard = page.getByRole("link", { name: new RegExp(first.name) }).first();
      await expect(firstCard).toBeVisible();
      await firstCard.click();
      await page.waitForURL(`**/p/${encodeURIComponent(first.name)}/health`);
      expect(page.url()).not.toContain("/login");

      // Kanban page: heading always renders; sections render column headers,
      // an empty board renders its empty state instead.
      await page.goto(spaURL(`/p/${encodeURIComponent(first.name)}/kanban`));
      await expect(page.getByRole("heading", { name: /看板/ })).toBeVisible();
      const kanbanResponse = await request.get(
        spaURL(`/api/v1/profiles/${encodeURIComponent(first.name)}/kanban`),
      );
      expect(kanbanResponse.status()).toBe(200);
      const kanbanBody = await kanbanResponse.json();
      // Flat shape: {profile, sections: [{name, tasks}], total} (the frontend
      // wraps it as {board, etag} itself).
      const sections: Array<{ name: string }> = kanbanBody.sections ?? [];
      const total: number = kanbanBody.total ?? 0;
      if (sections.length === 0 || total === 0) {
        await expect(page.getByText(/看板为空/)).toBeVisible();
      } else {
        for (const section of sections) {
          await expect(page.getByText(section.name, { exact: true }).first()).toBeVisible();
        }
      }
    }

    // Assistant page: renders the 助手 status card when the OpenClaw CLI is
    // installed (it is on this dev box), otherwise the 未安装 empty state.
    // Generous timeout: on a cold server the backend probes `openclaw`
    // subprocesses with a 5s budget each before caching for 60s.
    await page.goto(spaURL("/assistant"));
    const emptyState = page.getByRole("heading", { name: "本机未安装 OpenClaw" });
    const statusCard = page.getByRole("heading", { name: "助手", exact: true });
    await expect(emptyState.or(statusCard)).toBeVisible({ timeout: 30_000 });
    expect(page.url()).not.toContain("/login");
  });
});
