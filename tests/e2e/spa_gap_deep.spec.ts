import { expect, test } from "@playwright/test";

/**
 * Gap 深度分析 (LLM) e2e — the async-jobs + SSE slice (2026-09-21):
 *
 * - Fast path (network stub): `POST /gap/analyze` with use_llm=true is
 *   intercepted to answer 202 with a mock job, and the SSE stream endpoint
 *   is fulfilled with a canned frame sequence (job → progress routing →
 *   progress merging → done + result). The page under test is real: button →
 *   job creation → EventSource subscription → progress card → result
 *   rendering with the LLM origin annotations. Same stub technique as the
 *   sidecar-unreachable case in spa_home.spec.ts — the whole chain except
 *   the network is exercised, deterministically.
 * - Slow path (real LLM, test.slow): the isolated sandbox web-api sources
 *   the repo .env and has a live LLM, so the real job runs to done. Real
 *   learned-keyword writes under .dev-data/schemas/.learned are accepted
 *   (sandbox data root). Skips only when the backend reports the LLM as not
 *   configured; a real router failure fails the test.
 */

const SPA_BASE_URL = (process.env.NBLANE_E2E_SPA_BASE_URL || "http://127.0.0.1:18504").replace(
  /\/+$/,
  "",
);
const PROFILE = process.env.NBLANE_E2E_PROFILE || "dev";

function spa(path: string): string {
  return `${SPA_BASE_URL}/p/${encodeURIComponent(PROFILE)}/${path}`;
}

const MOCK_JOB_ID = "mock-deep-job";

function mockJob(status: string, phase: string): Record<string, unknown> {
  return {
    job_id: MOCK_JOB_ID,
    profile: PROFILE,
    kind: "gap-analysis",
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

const MOCK_LLM_RESULT = {
  profile: PROFILE,
  task: "e2e 深度分析:用机械臂完成抓取任务",
  top_matches: [
    { id: "manipulation", label: "Manipulation", score: 3, source: "rule" },
    { id: "navigation", label: "Navigation", score: 0, source: "llm" },
  ],
  closure: [
    { id: "robotics", label: "Robotics", status: "solid", is_gap: false, evidence_count: 0 },
    { id: "manipulation", label: "Manipulation", status: "learning", is_gap: true, evidence_count: 0 },
    { id: "navigation", label: "Navigation", status: "locked", is_gap: true, evidence_count: 0 },
  ],
  gaps: ["manipulation", "navigation"],
  strong: ["robotics"],
  can_solve: false,
  coverage: 1 / 3,
  next_steps: ["Advance 'manipulation' (Manipulation) from learning -> learning/solid"],
  roots_from_rule: ["manipulation"],
  roots_from_llm: ["navigation"],
  learned_merged: true,
  analysis_mode: "rule+llm",
  llm_router_error: null,
};

/** Serialize one SSE frame (same wire shape as web_api/jobs.py sse_event). */
function sseFrame(event: string, data: unknown): string {
  return `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
}

test.describe("SPA Gap 深度分析 (LLM jobs + SSE)", () => {
  test("stubbed job: progress card → LLM result with root-origin annotations", async ({
    page,
  }) => {
    let analyzeBody: { task?: string; use_llm?: boolean } | null = null;
    await page.route("**/api/v1/profiles/*/gap/analyze", async (route) => {
      analyzeBody = route.request().postDataJSON() as typeof analyzeBody;
      await route.fulfill({
        status: 202,
        contentType: "application/json",
        body: JSON.stringify({ ok: true, job_id: MOCK_JOB_ID, job: mockJob("queued", "queued") }),
      });
    });
    const streamBody =
      sseFrame("job", { ok: true, job: mockJob("running", "starting") }) +
      sseFrame("progress", {
        ok: true,
        job: mockJob("running", "routing"),
        event: { event: "progress", phase: "routing", message: "LLM routing.", seq: 1 },
      }) +
      sseFrame("progress", {
        ok: true,
        job: mockJob("running", "merging"),
        event: { event: "progress", phase: "merging", message: "Merging.", seq: 2 },
      }) +
      sseFrame("done", { ok: true, job: mockJob("done", "done"), result: MOCK_LLM_RESULT });
    await page.route(`**/api/v1/profiles/*/jobs/${MOCK_JOB_ID}/stream`, async (route) => {
      // Hold the frames back briefly so the queued progress card paints first.
      await new Promise((resolve) => setTimeout(resolve, 300));
      await route.fulfill({
        status: 200,
        headers: { "content-type": "text/event-stream", "cache-control": "no-cache" },
        body: streamBody,
      });
    });

    await page.goto(spa("gap"));
    await page.getByLabel("任务描述").fill("e2e 深度分析:用机械臂完成抓取任务");
    await page.getByRole("button", { name: "深度分析(LLM)" }).click();

    // Job created with use_llm=true; the queued progress card shows.
    const progress = page.getByTestId("gap-deep-progress");
    await expect(progress).toBeVisible();
    await expect(progress.getByText("排队中")).toBeVisible();
    expect(analyzeBody?.use_llm).toBe(true);
    expect(analyzeBody?.task).toBe("e2e 深度分析:用机械臂完成抓取任务");

    // Terminal frame: the result renders on the rule layout, annotated as LLM.
    await expect(page.getByText("LLM 深度分析", { exact: true })).toBeVisible({ timeout: 10_000 });
    await expect(progress).toHaveCount(0);
    const origins = page.getByTestId("gap-root-origins");
    await expect(origins).toContainText("规则 1 项(manipulation)");
    await expect(origins).toContainText("LLM 1 项(navigation)");
    const missing = page.getByTestId("gap-missing-section");
    await expect(missing.getByText("能力差距 (2)")).toBeVisible();
    await expect(missing.getByText("Navigation", { exact: true })).toBeVisible();
  });

  test("real LLM job runs to done (slow; sandbox live LLM)", async ({ page, request }) => {
    test.slow();
    test.setTimeout(120_000);

    await page.goto(spa("gap"));
    await page.getByLabel("任务描述").fill("用机械臂完成抓取并放置的任务");
    const createdPromise = page.waitForResponse(
      (res) => res.url().includes("/gap/analyze") && res.request().method() === "POST",
    );
    await page.getByRole("button", { name: "深度分析(LLM)" }).click();
    const created = await createdPromise;
    expect(created.status()).toBe(202);
    const createdBody = (await created.json()) as { job_id: string };
    expect(createdBody.job_id).toMatch(/^job-/);

    // Progress card first; the run itself takes seconds-to-a-minute.
    await expect(page.getByTestId("gap-deep-progress")).toBeVisible();

    const badge = page.getByText("LLM 深度分析", { exact: true });
    const degraded = page.getByTestId("gap-llm-degraded");
    const failed = page.getByTestId("gap-deep-error");
    await expect(badge.or(degraded).or(failed).first()).toBeVisible({ timeout: 100_000 });

    if (await failed.isVisible().catch(() => false)) {
      throw new Error(`deep-analysis job failed in the UI: ${await failed.innerText()}`);
    }
    if (await degraded.isVisible().catch(() => false)) {
      const reason = await degraded.innerText();
      if (/not configured/i.test(reason)) {
        test.skip(true, `sandbox LLM not configured: ${reason}`);
      }
      throw new Error(`LLM router degraded instead of routing: ${reason}`);
    }

    // Happy path: LLM-annotated result rendered from the real job.
    await expect(badge).toBeVisible();
    await expect(page.getByTestId("gap-root-origins")).toContainText("LLM");
    await expect(page.getByTestId("gap-missing-section")).toBeVisible();

    // Server-side truth: the job really completed in rule+llm mode.
    const status = await request.get(
      `${SPA_BASE_URL}/api/v1/profiles/${encodeURIComponent(PROFILE)}/jobs/${createdBody.job_id}`,
    );
    expect(status.status()).toBe(200);
    const payload = (await status.json()) as {
      job: { status: string };
      result: { analysis_mode: string; llm_router_error: string | null };
    };
    expect(payload.job.status).toBe("done");
    expect(payload.result.analysis_mode).toBe("rule+llm");
    expect(payload.result.llm_router_error).toBeNull();
  });
});
