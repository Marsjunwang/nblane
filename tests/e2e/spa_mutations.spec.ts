import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";

/**
 * Acceptance suite for the two P0 SPA write defects (real-browser, no mocks):
 *
 * P0-1 — every mutation 422'd with "Input should be a valid dictionary or
 *   object to extract fields from" because requestWithHeaders spread `init`
 *   AFTER `headers`, so any mutation carrying If-Match lost
 *   `Content-Type: application/json` (fetch then sent the JSON string body as
 *   text/plain). Each test here asserts the request really goes out with
 *   `content-type: application/json` and a 2xx status.
 *
 * P0-2 — Activity offered 应用 for every pending item, but the backend only
 *   applies Review-origin candidates (Streamlit parity: button hidden +
 *   explanation for anything else). Covered by both directions below.
 *
 * Runs against the isolated sandbox (`scripts/dev-web.sh --isolated`,
 * profile=dev); every entity title is unique per run so reruns never collide
 * with kanban's title-based addressing.
 */

const SPA_BASE_URL = (process.env.NBLANE_E2E_SPA_BASE_URL || "http://127.0.0.1:18504").replace(
  /\/+$/,
  "",
);
const PROFILE = process.env.NBLANE_E2E_PROFILE || "dev";

function spa(path: string): string {
  return `${SPA_BASE_URL}/p/${encodeURIComponent(PROFILE)}/${path}`;
}

/** Wait for a mutation response and assert P0-1's regression: JSON content-type + 2xx. */
async function expectJsonMutation(
  page: Page,
  urlPart: string,
  action: () => Promise<void>,
): Promise<void> {
  const responsePromise = page.waitForResponse(
    (res) => res.url().includes(urlPart) && res.request().method() === "POST",
  );
  await action();
  const response = await responsePromise;
  const contentType = response.request().headers()["content-type"] ?? "";
  expect(
    contentType,
    `POST ${urlPart} must go out as application/json (P0-1 regression: ` +
      `mutations carrying If-Match lost Content-Type and 422'd)`,
  ).toContain("application/json");
  expect(response.status(), `POST ${urlPart} should succeed`).toBeLessThan(300);
  expect(response.status()).toBeGreaterThanOrEqual(200);
}

/**
 * Wait out the mutation success toast. The toast parks bottom-right for ~4s;
 * on a long Queue the tail card's 「…」 menu flips open into exactly that
 * corner (position="bottom-end"), so a still-visible toast swallows the menu
 * click and closes it (surfaced 2026-09-21 once sandbox data growth pushed
 * the tail card to the viewport's bottom edge — same interception class the
 * mobile spec avoids by seeding over the API).
 *
 * NB: the toast mounts a beat AFTER the mutation response resolves, so a
 * bare toHaveCount(0) can pass before it ever renders — always wait for the
 * mount first, then for the auto-close.
 */
async function waitForToastsToSettle(page: Page): Promise<void> {
  const toasts = page.locator(".mantine-Notification-root");
  await toasts
    .first()
    .waitFor({ state: "visible", timeout: 5_000 })
    .catch(() => {});
  await expect(toasts).toHaveCount(0, { timeout: 15_000 });
}

/**
 * Seed one needs_review evidence row through the real chain (kanban card →
 * 标记完成 → weekly-review save → activity apply). The bulk-accept test must
 * NOT consume whatever row the sandbox happens to hold: every suite run
 * depletes the seeded pool by one, so after a few runs the "first row" simply
 * does not exist and the test dies waiting for it.
 */
async function seedNeedsReviewEvidence(page: Page, title: string): Promise<void> {
  // 1. Done card through the UI (kanban add + 标记完成).
  await page.goto(spa("kanban"));
  await page.getByLabel("快速添加").fill(title);
  await expectJsonMutation(page, "/kanban/cards", () =>
    page.getByRole("button", { name: "添加", exact: true }).click(),
  );
  await waitForToastsToSettle(page);
  await page.getByLabel(`卡片操作 ${title}`).click();
  await expectJsonMutation(page, "/done", () =>
    page.getByRole("menuitem", { name: "标记完成" }).click(),
  );

  // 2. Weekly review: the Done card is an evidence candidate → 保存到活动.
  await page.goto(spa("review"));
  const candidateRow = page
    .locator('[data-testid^="review-candidate-evidence-"]')
    .filter({ hasText: title });
  await expect(candidateRow).toBeVisible();
  await candidateRow.getByRole("checkbox").click();
  await expectJsonMutation(page, "/review/save", () =>
    page.getByRole("button", { name: /^保存到活动/ }).click(),
  );
  await expect(page.getByTestId("save-success-evidence")).toBeVisible();

  // 3. Activity: apply the saved Review candidate — that writes the
  // needs_review evidence row into the pool.
  await page.goto(spa("activity"));
  await page.getByText(title, { exact: true }).click();
  await expectJsonMutation(page, "/apply", () =>
    page.getByRole("button", { name: "应用", exact: true }).click(),
  );
  await expect(page.getByText("应用成功")).toBeVisible();
}

test.describe("SPA mutations (P0-1/P0-2 acceptance)", () => {
  test("inbox capture: 201 as JSON and the item shows up in the list", async ({ page }) => {
    const title = `e2e-capture-${Date.now()}`;
    await page.goto(spa("inbox"));
    await page.getByLabel("随手记").fill(title);

    await expectJsonMutation(page, "/inbox", () =>
      page.getByRole("button", { name: "记录", exact: true }).click(),
    );

    await expect(page.getByText(title)).toBeVisible();
    await expect(page.getByText("已加入收件箱。")).toBeVisible();
  });

  test("kanban: add a card into Queue, then move it to Doing", async ({ page }) => {
    const title = `e2e-card-${Date.now()}`;
    await page.goto(spa("kanban"));
    const column = (name: string) =>
      page.locator("div.mantine-Paper-root").filter({ has: page.getByText(name, { exact: true }) });

    await page.getByLabel("快速添加").fill(title);
    await expectJsonMutation(page, "/kanban/cards", () =>
      page.getByRole("button", { name: "添加", exact: true }).click(),
    );
    await expect(column("Queue").getByText(title)).toBeVisible();

    // Card menu → 移动到… → Doing (sub-menu opens on hover).
    await waitForToastsToSettle(page);
    await page.getByLabel(`卡片操作 ${title}`).click();
    await page.getByRole("menuitem", { name: "移动到…" }).hover();
    await expectJsonMutation(page, "/move", () =>
      page.getByRole("menuitem", { name: "Doing", exact: true }).click(),
    );
    await expect(column("Doing").getByText(title)).toBeVisible();
    await expect(column("Queue").getByText(title)).toHaveCount(0);
  });

  test("evidence review: accept removes the row from the needs_review queue", async ({
    page,
  }) => {
    // Self-seeded (see seedNeedsReviewEvidence): the sandbox pool of
    // needs_review rows is finite and every suite run consumes one, so the
    // test accepts the exact row it created — never a foreign "first row".
    const title = `e2e-bulk-${Date.now()}`;
    await seedNeedsReviewEvidence(page, title);

    // Phase 1: /evidence-review redirects into the single Evidence page.
    await page.goto(spa("evidence-review"));
    const row = page.locator('[data-testid^="evidence-row-"]').filter({ hasText: title });
    await expect(row).toBeVisible();
    const testId = (await row.getAttribute("data-testid")) ?? "";

    await row.click();
    await expectJsonMutation(page, "/review", () =>
      page.getByTestId("evidence-accept").click(),
    );

    // Accepted rows leave the needs_review stage after the list refetch.
    await expect(page.locator(`[data-testid="${testId}"]`)).toHaveCount(0);
  });

  test("activity P0-2: pending non-Review item offers no 应用, with an explanation", async ({
    page,
    request,
  }) => {
    // The sandbox carries AI-Gateway pending items; the e2e itself never
    // consumes them. If a regenerated sandbox lacks one, skip loudly.
    const listResponse = await request.get(
      `${SPA_BASE_URL}/api/v1/profiles/${encodeURIComponent(PROFILE)}/activity?status=pending&limit=200`,
    );
    expect(listResponse.ok()).toBe(true);
    const list = (await listResponse.json()) as {
      items: { id: string; title: string; source_page: string }[];
    };
    const foreign = (list.items ?? []).find((item) => item.source_page !== "Review");
    test.skip(!foreign, "sandbox has no pending non-Review activity item to assert against");

    await page.goto(spa("activity"));
    await page.getByText(foreign!.title, { exact: true }).first().click();

    await expect(page.getByRole("button", { name: "驳回", exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "应用", exact: true })).toHaveCount(0);
    await expect(page.getByText(/只能应用 pending 的 Review 候选/)).toBeVisible();
  });

  test("activity apply: kanban done card → review save → activity apply (full chain)", async ({
    page,
  }) => {
    const title = `e2e-chain-${Date.now()}`;

    // 1. Seed a Done card through the UI (kanban add + 标记完成).
    await page.goto(spa("kanban"));
    await page.getByLabel("快速添加").fill(title);
    await expectJsonMutation(page, "/kanban/cards", () =>
      page.getByRole("button", { name: "添加", exact: true }).click(),
    );
    await waitForToastsToSettle(page);
    await page.getByLabel(`卡片操作 ${title}`).click();
    await expectJsonMutation(page, "/done", () =>
      page.getByRole("menuitem", { name: "标记完成" }).click(),
    );

    // 2. Weekly review: the Done card is an evidence candidate → 保存到活动.
    await page.goto(spa("review"));
    const candidateRow = page
      .locator('[data-testid^="review-candidate-evidence-"]')
      .filter({ hasText: title });
    await expect(candidateRow).toBeVisible();
    await candidateRow.getByRole("checkbox").click();
    await expectJsonMutation(page, "/review/save", () =>
      page.getByRole("button", { name: /^保存到活动/ }).click(),
    );
    await expect(page.getByTestId("save-success-evidence")).toBeVisible();

    // 3. Activity: the saved Review candidate offers 应用 and applies cleanly.
    await page.goto(spa("activity"));
    await page.getByText(title, { exact: true }).click();
    await expectJsonMutation(page, "/apply", () =>
      page.getByRole("button", { name: "应用", exact: true }).click(),
    );
    await expect(page.getByText("应用成功")).toBeVisible();
    // Applied items leave the default pending list after invalidation refetch
    // (list rows are Cards; the open drawer renders no Card with the title).
    await expect(
      page.locator("div.mantine-Card-root").filter({ hasText: title }),
    ).toHaveCount(0);
  });
});
