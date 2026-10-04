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
 * Wait out the mutation success toast. The toast parks bottom-right for ~4s
 * and can swallow a follow-up click in that corner (surfaced 2026-09-21 once
 * sandbox data growth pushed the tail card to the viewport's bottom edge —
 * same interception class the mobile spec avoids by seeding over the API).
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
 * Seed one kanban card over the API (the unified /projects page has no
 * quick-add form; card creation lives in the project edit drawer or the
 * API). Returns the new card's id (used for the `task-card-<id>` testid).
 */
async function seedKanbanCard(page: Page, title: string): Promise<string> {
  const response = await page.request.post(
    `${SPA_BASE_URL}/api/v1/profiles/${encodeURIComponent(PROFILE)}/kanban/cards`,
    { data: { title, section: "Queue", context: "" } },
  );
  expect(response.status(), "kanban card seed should succeed").toBe(201);
  const body = (await response.json()) as { card: { id: string } };
  return body.card.id;
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

  test("projects: seed a card into Queue, then move it to Doing via the detail card", async ({
    page,
  }) => {
    const title = `e2e-card-${Date.now()}`;
    const cardId = await seedKanbanCard(page, title);
    await page.goto(spa("projects"));

    // Seeded without a project → lands in the dashed-gold 未归属 lane.
    const unassigned = page.getByTestId("unassigned-lane");
    await expect(unassigned.getByTestId("lane-column-unassigned-queue").getByText(title)).toBeVisible();

    // Card click opens the inscription detail card; 移至 Doing moves it.
    await waitForToastsToSettle(page);
    await unassigned.getByTestId(`task-card-${cardId}`).click();
    await expect(page.getByTestId("task-detail-card")).toBeVisible();
    await expectJsonMutation(page, "/move", () =>
      page.getByRole("button", { name: "移至 Doing" }).click(),
    );
    await expect(
      unassigned.getByTestId("lane-column-unassigned-doing").getByText(title),
    ).toBeVisible();
    await expect(
      unassigned.getByTestId("lane-column-unassigned-queue").getByText(title),
    ).toHaveCount(0);
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

});
