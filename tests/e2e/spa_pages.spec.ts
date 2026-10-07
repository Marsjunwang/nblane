import { expect, test } from "@playwright/test";
import type { Page, Response } from "@playwright/test";

/**
 * Real-browser journeys for the core SPA pages that had no e2e coverage
 * (2026-09-21 batch), against the isolated sandbox
 * (`scripts/dev-web.sh --isolated`, profile=dev):
 *
 * - 项目 Projects: case → milestone → task → move columns; M-FE-1
 *   regression (an unsaved basics draft survives a tab switch + the board
 *   refetch triggered by moving a task); archive; AI suggest-refs renders
 *   the degradation card on the no-LLM job-error contract (stubbed — the
 *   sandbox sources .env and its LLM is live, so the real job outcome is
 *   nondeterministic; jobs/SSE migration 2026-09-21).
 * - 研究台 Research: reading queue, progress summary, and standalone Paper
 *   Library entry match the API payload; sidecar coordinates point at this
 *   stack's reader port (18502, same convention as spa_home.spec.ts).
 *
 * Every entity the suite creates carries a unique `e2e-<page>-<ts>` prefix so
 * reruns never collide with existing sandbox data or other specs.
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

function api(path: string): string {
  return `${SPA_BASE_URL}/api/v1${path}`;
}

/** Click `action`, wait for the POST to `urlPart`, return the response. */
async function waitPost(page: Page, urlPart: string, action: () => Promise<void>): Promise<Response> {
  const responsePromise = page.waitForResponse(
    (res) => res.url().includes(urlPart) && res.request().method() === "POST",
  );
  await action();
  return responsePromise;
}

const JOBS_CREATE_RE = /\/api\/v1\/profiles\/[^/]+\/jobs$/;

function mockJob(
  kind: string,
  jobId: string,
  status: string,
  phase: string,
): Record<string, unknown> {
  return {
    job_id: jobId,
    profile: PROFILE,
    kind,
    status,
    phase,
    message: "",
    created_at: 1,
    started_at: 1,
    finished_at: 0,
    elapsed_ms: 0,
    error: null,
  };
}

/** Serialize one SSE frame (same wire shape as web_api/jobs.py sse_event). */
function sseFrame(event: string, data: unknown): string {
  return `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
}

/**
 * Stub the LLM-job journey so it fails structured: creation answers 202,
 * the SSE stream sends the initial job frame then a terminal error frame
 * carrying `code` — the same degradation contract the no-LLM stack produces
 * for real (jobs/SSE migration 2026-09-21; the sync endpoints' 422s moved
 * into the job error event).
 */
async function stubFailingJob(
  page: Page,
  kind: string,
  jobId: string,
  error: { code: string; message: string },
): Promise<void> {
  await page.route(JOBS_CREATE_RE, async (route) => {
    await route.fulfill({
      status: 202,
      contentType: "application/json",
      body: JSON.stringify({ ok: true, job_id: jobId, job: mockJob(kind, jobId, "queued", "queued") }),
    });
  });
  const streamBody =
    sseFrame("job", { ok: true, job: mockJob(kind, jobId, "running", "starting") }) +
    sseFrame("error", {
      ok: false,
      job: mockJob(kind, jobId, "failed", "failed"),
      error,
    });
  await page.route(new RegExp(`/api/v1/profiles/[^/]+/jobs/${jobId}/stream$`), async (route) => {
    // Hold the frames back briefly so the queued progress card paints first.
    await new Promise((resolve) => setTimeout(resolve, 300));
    await route.fulfill({
      status: 200,
      headers: { "content-type": "text/event-stream", "cache-control": "no-cache" },
      body: streamBody,
    });
  });
}

test.describe("SPA Projects (项目 — 一体化看板)", () => {
  test("case → milestone → task → move → draft protection (M-FE-1) → archive", async ({
    page,
  }) => {
    const ts = Date.now();
    const caseTitle = `e2e-pb-${ts}`;
    const milestoneTitle = `e2e-ms-${ts}`;
    const taskTitle = `e2e-task-${ts}`;

    await page.goto(spa("projects"));
    await expect(page.getByTestId("projects-toolbar")).toBeVisible();

    // 1. Create the case via 新建项目; the edit drawer opens on the new id.
    await page.getByTestId("new-project-button").click();
    const createForm = page.getByTestId("create-case-form");
    await createForm.getByRole("textbox", { name: "标题", exact: true }).fill(caseTitle);
    const createResponse = await waitPost(page, "/project-board/cases", () =>
      createForm.getByRole("button", { name: "创建项目" }).click(),
    );
    expect(createResponse.status()).toBe(201);
    const caseId: string = (await createResponse.json()).case.id;
    expect(caseId).toBeTruthy();

    const detail = page.getByTestId("case-detail");
    await expect(detail).toBeVisible();
    await expect(page.getByTestId("project-edit-drawer")).toContainText(caseTitle);

    // 2. Add a milestone.
    await detail.getByRole("tab", { name: "里程碑" }).click();
    const milestoneForm = detail.getByTestId("add-milestone-form");
    await milestoneForm.getByRole("textbox", { name: "标题", exact: true }).fill(milestoneTitle);
    const milestoneResponse = await waitPost(page, "/milestones", () =>
      milestoneForm.getByRole("button", { name: "添加里程碑" }).click(),
    );
    expect(milestoneResponse.status()).toBe(201);
    await expect(detail.getByRole("button", { name: new RegExp(milestoneTitle) })).toBeVisible();

    // 3. Add a project task (lands on the lane in Queue).
    await detail.getByRole("tab", { name: "任务" }).click();
    const taskForm = detail.getByTestId("add-task-form");
    await taskForm.getByRole("textbox", { name: "标题", exact: true }).fill(taskTitle);
    const taskResponse = await waitPost(page, "/tasks", () =>
      taskForm.getByRole("button", { name: "新建任务" }).click(),
    );
    expect(taskResponse.status()).toBe(201);
    const taskRow = detail.locator('[data-testid^="project-task-"]', { hasText: taskTitle });
    await expect(taskRow).toBeVisible();

    // 4. Move the task Queue → Doing; the select follows the refetched board.
    const moveSelect = detail.getByRole("combobox", { name: `移动 ${taskTitle}` });
    const moveResponse = await waitPost(page, "/move", () => moveSelect.selectOption("Doing"));
    expect(moveResponse.status()).toBe(200);
    await expect(moveSelect).toHaveValue("Doing");

    // 5. M-FE-1 regression: an unsaved basics draft survives switching to the
    // tasks tab, moving a task (which refetches the whole board), and back.
    await detail.getByRole("tab", { name: "基本信息" }).click();
    const draftTitle = `${caseTitle}（草稿）`;
    await detail.getByRole("textbox", { name: "标题", exact: true }).fill(draftTitle);
    await detail.getByRole("tab", { name: "任务" }).click();
    const moveBackResponse = await waitPost(page, "/move", () => moveSelect.selectOption("Queue"));
    expect(moveBackResponse.status()).toBe(200);
    await expect(moveSelect).toHaveValue("Queue");
    await detail.getByRole("tab", { name: "基本信息" }).click();
    await expect(
      detail.getByRole("textbox", { name: "标题", exact: true }),
      "unsaved basics draft must survive a tab switch + board refetch (M-FE-1)",
    ).toHaveValue(draftTitle);

    // 6. Archive: the lane folds into the count-only 已归档项目 footer.
    const archiveResponse = await waitPost(page, "/archive", () =>
      detail.getByRole("button", { name: "归档项目" }).click(),
    );
    expect(archiveResponse.status()).toBe(200);
    await expect(detail.getByRole("button", { name: "归档项目" })).toHaveCount(0);
    await page.keyboard.press("Escape");
    await expect(page.getByTestId(`project-lane-${caseId}`)).toHaveCount(0);
    // The footer shows the SAVED title (the 草稿 draft was never saved).
    await expect(page.getByTestId("archived-projects-footer")).toContainText(caseTitle);
  });

  test("AI 建议引用 shows the degradation card on the no-LLM job contract", async ({ page }) => {
    // The sandbox sources .env and has a LIVE LLM: the real suggest-refs
    // job outcome is nondeterministic (suggestions, or the designed yellow
    // degradation card when the provider's structured output fails
    // validation). The deterministic no-LLM degradation journey is
    // therefore exercised against the documented job-error contract
    // (project_suggest_refs_failed, the same code the sync endpoint used
    // to answer as 422), stubbed at the network edge — the same simulation
    // pattern spa_home.spec.ts uses for the unreachable-sidecar journey.
    // The page code under test (create job → SSE → error mapping → card)
    // is all real.
    await stubFailingJob(page, "project-suggest-refs", "mock-suggest-fail", {
      code: "project_suggest_refs_failed",
      message: "routing_error: no backend available",
    });

    const ts = Date.now();
    await page.goto(spa("projects"));
    await expect(page.getByTestId("projects-toolbar")).toBeVisible();

    await page.getByTestId("new-project-button").click();
    const createForm = page.getByTestId("create-case-form");
    await createForm
      .getByRole("textbox", { name: "标题", exact: true })
      .fill(`e2e-pb-ai-${ts}`);
    const createResponse = await waitPost(page, "/project-board/cases", () =>
      createForm.getByRole("button", { name: "创建项目" }).click(),
    );
    expect(createResponse.status()).toBe(201);

    const detail = page.getByTestId("case-detail");
    await expect(detail).toBeVisible();
    await detail.getByTestId("suggest-refs-button").click();

    // Progress card first, then the yellow degradation card replaces it.
    await expect(detail.getByTestId("suggest-progress")).toBeVisible();
    const degraded = detail.getByTestId("suggest-error");
    await expect(degraded).toBeVisible();
    await expect(degraded).toContainText("AI 建议不可用");
    await expect(degraded).toContainText("配置 LLM 后重试");
    await expect(detail.getByTestId("suggest-progress")).toHaveCount(0);
  });
});

test.describe("SPA Research (研究台)", () => {
  test("reading desk + paper library entry render from the API payload", async ({
    page,
    request,
  }) => {
    const response = await request.get(api(`/profiles/${encodeURIComponent(PROFILE)}/research`));
    expect(response.status()).toBe(200);
    const data = await response.json();

    await page.goto(spa("research"));

    await expect(page.getByText(`${PROFILE} · 研究台`)).toBeVisible();
    await expect(page.getByText("论文总数")).toBeVisible();
    await expect(page.getByText("阅读队列")).toBeVisible();
    await expect(page.getByText("最近读过")).toBeVisible();
    await expect(page.getByRole("link", { name: /打开论文库/ })).toHaveAttribute(
      "href",
      expect.stringContaining(`${data.sidecar.base}/paper-library?profile=${PROFILE}&auth_handoff=`),
    );
    await expect(page.getByText("断言")).toHaveCount(0);
    await expect(page.getByText("引用")).toHaveCount(0);
  });

  test("sidecar coordinates point at 18502 and Paper Library stays standalone", async ({ page, request }) => {
    const response = await request.get(api(`/profiles/${encodeURIComponent(PROFILE)}/research`));
    expect(response.status()).toBe(200);
    const sidecar = (await response.json()).sidecar;
    // Same convention as spa_home.spec.ts: the sandbox payload must follow
    // the stack's reader port, not the hardcoded 8502 default.
    expect(sidecar.base).toBe(EXPECTED_SIDECAR_BASE);
    expect(sidecar.configured).toBe(true);
    expect(sidecar.paper_library_url).toContain(`${EXPECTED_SIDECAR_BASE}/paper-library`);
    await page.goto(spa("research"));
    await expect(page.locator('iframe[data-testid="sidecar-frame"]')).toHaveCount(0);

    const libraryResponse = await request.get(sidecar.paper_library_url);
    expect(libraryResponse.status(), "paper library endpoint should load with the minted handoff").toBe(200);
  });
});
