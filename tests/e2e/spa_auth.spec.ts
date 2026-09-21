import { expect, test } from "@playwright/test";
import type { APIRequestContext, Page } from "@playwright/test";

import {
  SPA_BASE_URL,
  SPA_ADMIN_USER,
  SPA_ADMIN_PASSWORD,
  SPA_MEMBER_USER,
  SPA_MEMBER_PASSWORD,
  SPA_E2E_PROFILE,
} from "./spa_auth_shared";

/**
 * Real-browser acceptance of the full SPA login journey against the
 * auth-enabled isolated stack (`scripts/dev-web.sh --isolated` with
 * .dev-data/auth/users.yaml → NBLANE_AUTH_FILE on the web-api session):
 *
 *   a) unauthenticated deep link bounces to /login (API itself answers 401)
 *   b) wrong password → generic error, identical for unknown users (no
 *      account-existence leak)
 *   c) valid login returns to the original target page (M-FE-3 regression)
 *   d) logout → back to /login, inner pages blocked again
 *   e) member account sees only granted profiles (M-API-1)
 *   f) 5 consecutive failures rate-limit that username (429), and the UI
 *      surfaces the throttle message
 *
 * This spec runs WITHOUT the baked admin storageState (own Playwright
 * project) — every test drives its own session. Rate-limit buckets are
 * keyed ip+username, so the wrong-password/lockout cases below never touch
 * the admin/member budgets the other specs rely on.
 */

const GENERIC_LOGIN_ERROR = "Invalid username or password";
const RATE_LIMIT_MESSAGE = /Too many failed login attempts/;

function spaURL(path: string = "/"): string {
  return new URL(path, `${SPA_BASE_URL}/`).toString();
}

function profileURL(page: string): string {
  return spaURL(`/p/${encodeURIComponent(SPA_E2E_PROFILE)}/${page}`);
}

async function spaAuthEnabled(request: APIRequestContext): Promise<boolean> {
  try {
    const me = await request.get(spaURL("/api/v1/auth/me"));
    if (me.status() === 401) {
      return true; // auth on, no session cookie on this fresh context
    }
    if (me.ok()) {
      return ((await me.json()) as { auth_enabled?: boolean }).auth_enabled === true;
    }
    return false;
  } catch {
    return false;
  }
}

async function submitLoginForm(page: Page, username: string, password: string): Promise<void> {
  await page.getByLabel("用户名").fill(username);
  await page.getByLabel("密码").fill(password);
  await page.getByRole("button", { name: "登录", exact: true }).click();
}

/** Log in through the API; the context cookie jar is shared with the page. */
async function loginViaApi(page: Page, username: string, password: string): Promise<void> {
  const res = await page.request.post(spaURL("/api/v1/auth/login"), {
    data: { username, password },
  });
  expect(res.status(), `API login as ${username} should succeed`).toBe(200);
}

test.describe("SPA login journey (auth-enabled web_api on " + SPA_BASE_URL + ")", () => {
  test.beforeEach(async ({ request }) => {
    test.skip(
      !(await spaAuthEnabled(request)),
      "SPA backend auth is off — restart the isolated stack with .dev-data/auth/users.yaml present",
    );
  });

  test("a) unauthenticated /p/<profile>/kanban bounces to /login; API answers 401", async ({
    page,
  }) => {
    await page.goto(profileURL("kanban"));
    await page.waitForURL("**/login");
    await expect(page.getByRole("heading", { name: "nblane 登录" })).toBeVisible();

    const res = await page.request.get(
      spaURL(`/api/v1/profiles/${encodeURIComponent(SPA_E2E_PROFILE)}/kanban`),
    );
    expect(res.status()).toBe(401);
  });

  test("b) wrong password shows the generic error; unknown users get the identical answer", async ({
    page,
  }) => {
    await page.goto(spaURL("/login"));
    await submitLoginForm(page, SPA_ADMIN_USER, "definitely-wrong-password");
    const alert = page.getByTestId("login-error");
    await expect(alert).toBeVisible();
    await expect(alert).toContainText(GENERIC_LOGIN_ERROR);
    expect(page.url()).toContain("/login");

    // No account-existence leak: unknown username → same status, same detail.
    const res = await page.request.post(spaURL("/api/v1/auth/login"), {
      data: { username: "e2e-no-such-user", password: "whatever" },
    });
    expect(res.status()).toBe(401);
    expect(((await res.json()) as { detail?: string }).detail).toBe(GENERIC_LOGIN_ERROR);
  });

  // The redirect-back chain (deep link → bounce to /login → login POST with
  // password-hash verify → SPA reload → heading render) is this spec's most
  // load-sensitive case: at the tail of a full-suite run on this
  // 2-CPU/3.75GB sandbox it can outrun the 45s default budget (it passes
  // standalone, and after small subsets). The retry is scoped to this case
  // only — re-running it is state-free (a fresh context + one successful
  // login, which also clears the ip+username failure bucket); do not widen
  // this into suite-wide retries.
  test.describe("c) redirect-back after login", () => {
    test.describe.configure({ retries: 1 });

    test("c) valid login returns to the original target page (M-FE-3)", async ({ page }) => {
      test.setTimeout(60_000);
      await page.goto(profileURL("kanban"));
      await page.waitForURL("**/login");
      await submitLoginForm(page, SPA_ADMIN_USER, SPA_ADMIN_PASSWORD);
      await page.waitForURL(`**/p/${encodeURIComponent(SPA_E2E_PROFILE)}/kanban`);
      await expect(page.getByRole("heading", { name: /看板/ })).toBeVisible();
    });
  });

  test("d) logout returns to /login and inner pages are blocked again", async ({ page }) => {
    await loginViaApi(page, SPA_ADMIN_USER, SPA_ADMIN_PASSWORD);
    await page.goto(spaURL("/"));
    await expect(page.getByRole("heading", { name: "档案列表" })).toBeVisible();

    await page.getByRole("button", { name: "退出登录" }).click();
    await page.waitForURL("**/login");
    await expect(page.getByRole("heading", { name: "nblane 登录" })).toBeVisible();

    await page.goto(profileURL("kanban"));
    await page.waitForURL("**/login");
  });

  test("e) member sees only granted profiles, UI and API alike (M-API-1)", async ({ page }) => {
    await loginViaApi(page, SPA_MEMBER_USER, SPA_MEMBER_PASSWORD);

    const res = await page.request.get(spaURL("/api/v1/profiles"));
    expect(res.ok()).toBeTruthy();
    const profiles = (await res.json()) as Array<{ name: string }>;
    expect(
      profiles.map((p) => p.name),
      "member grant is exactly the sandbox dev profile",
    ).toEqual([SPA_E2E_PROFILE]);

    await page.goto(spaURL("/"));
    await expect(page.getByRole("heading", { name: "档案列表" })).toBeVisible();
    await expect(
      page.getByRole("link", { name: new RegExp(SPA_E2E_PROFILE) }).first(),
    ).toBeVisible();
    // 王军 exists in this sandbox (admin sees it) but must not leak to member.
    await expect(page.getByRole("link", { name: /王军/ })).toHaveCount(0);

    // Direct API access to a non-granted profile: scope check precedes the
    // 404 lookup, so even existence is not probeable.
    const denied = await page.request.get(
      spaURL(`/api/v1/profiles/${encodeURIComponent("王军")}/kanban`),
    );
    expect(denied.status()).toBe(403);
  });

  test("f) five consecutive failures rate-limit that username (429), UI shows the throttle", async ({
    page,
  }) => {
    // Fresh username per run → its ip+username bucket starts empty, so the
    // case neither waits out the 60s window nor disturbs other accounts.
    const username = `e2e-ratelimit-${Date.now()}`;
    for (let attempt = 1; attempt <= 5; attempt++) {
      const res = await page.request.post(spaURL("/api/v1/auth/login"), {
        data: { username, password: "wrong-password" },
      });
      expect(res.status(), `failure ${attempt}/5 should still be a plain 401`).toBe(401);
    }
    const blocked = await page.request.post(spaURL("/api/v1/auth/login"), {
      data: { username, password: "wrong-password" },
    });
    expect(blocked.status()).toBe(429);
    expect(((await blocked.json()) as { detail?: string }).detail).toMatch(RATE_LIMIT_MESSAGE);

    // The login page surfaces the same server-side throttle message.
    await page.goto(spaURL("/login"));
    await submitLoginForm(page, username, "wrong-password");
    await expect(page.getByTestId("login-error")).toContainText(RATE_LIMIT_MESSAGE);
  });
});
