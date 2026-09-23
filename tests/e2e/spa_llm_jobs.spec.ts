import { expect, test } from "@playwright/test";
import type { Page, Response } from "@playwright/test";

/**
 * JD 匹配 (studio-jd-match) + AI 建议引用 (project-suggest-refs) 的
 * LLM jobs + SSE 迁移 e2e(2026-09-21,参照 spa_gap_deep.spec.ts 手法):
 *
 * - Fast path (network stub): `POST /api/v1/profiles/{name}/jobs` 被拦截
 *   返回 202 mock job,SSE stream 端点按帧序列兑现(job → progress 阶段 →
 *   done + result)。页面全链路为真:按钮 → 建 job → EventSource 订阅 →
 *   进度卡(排队中)→ 结果渲染(suggest-refs 额外验证 confirm-not-fill
 *   「合并到表单」交互)。与 spa_home.spec.ts 模拟 sidecar 不可达同手法,
 *   除网络外全链路真实、确定性。
 * - Slow path (real LLM, test.slow): 隔离沙箱 web-api source 仓库 .env
 *   有活 LLM,真实 job 跑到终态。JD 匹配真实分析约 55s(给 150s 超时);
 *   suggest-refs 的 provider 结构化输出校验失败是设计内降级(黄卡,见
 *   体验官手册 §2.8),慢路径只断言「进度卡 → 终态卡」管道畅通,不断言
 *   provider 输出质量。仅当后端报 LLM 未配置时 skip。
 */

const SPA_BASE_URL = (process.env.NBLANE_E2E_SPA_BASE_URL || "http://127.0.0.1:18504").replace(
  /\/+$/,
  "",
);
const PROFILE = process.env.NBLANE_E2E_PROFILE || "dev";

function spa(path: string): string {
  return `${SPA_BASE_URL}/p/${encodeURIComponent(PROFILE)}/${path}`;
}

/** Click `action`, wait for the POST to `urlPart`, return the response. */
async function waitPost(page: Page, urlPart: string, action: () => Promise<void>): Promise<Response> {
  const responsePromise = page.waitForResponse(
    (res) => res.url().includes(urlPart) && res.request().method() === "POST",
  );
  await action();
  return responsePromise;
}

const JD_JOB_ID = "mock-jd-job";
const SUGGEST_JOB_ID = "mock-suggest-job";
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

/** Stub job creation (202) + the job's SSE stream (canned frame sequence). */
async function stubJobStream(
  page: Page,
  kind: string,
  jobId: string,
  phases: [string, string][],
  result: Record<string, unknown>,
  onCreate?: (body: unknown) => void,
): Promise<void> {
  await page.route(JOBS_CREATE_RE, async (route) => {
    onCreate?.(route.request().postDataJSON());
    await route.fulfill({
      status: 202,
      contentType: "application/json",
      body: JSON.stringify({ ok: true, job_id: jobId, job: mockJob(kind, jobId, "queued", "queued") }),
    });
  });
  let streamBody = sseFrame("job", { ok: true, job: mockJob(kind, jobId, "running", "starting") });
  phases.forEach(([phase, message], index) => {
    streamBody += sseFrame("progress", {
      ok: true,
      job: mockJob(kind, jobId, "running", phase),
      event: { event: "progress", phase, message, seq: index + 1 },
    });
  });
  streamBody += sseFrame("done", { ok: true, job: mockJob(kind, jobId, "done", "done"), result });
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

test.describe("SPA Studio JD 匹配 (studio-jd-match job + SSE)", () => {
  test("stubbed job: 进度卡(排队中)→ 匹配分析卡", async ({ page }) => {
    let createBody: { kind?: string; input?: { resume_md?: string; jd_text?: string } } | null =
      null;
    await stubJobStream(
      page,
      "studio-jd-match",
      JD_JOB_ID,
      [
        ["analyzing", "分析中:汇总档案证据与简历上下文。"],
        ["generating", "生成中:LLM 正在撰写匹配分析。"],
      ],
      { ok: true, analysis: "## 匹配分析\n\ne2e 匹配分析结论:✅ 符合。" },
      (body) => {
        createBody = body as typeof createBody;
      },
    );

    await page.goto(spa("studio"));
    await expect(page.getByTestId("studio-summary")).toBeVisible();
    await page.getByRole("tab", { name: "JD 匹配" }).click();
    await page.getByRole("textbox", { name: "简历内容" }).fill("e2e 简历:机械臂开发经验。");
    await page.getByRole("textbox", { name: /目标 JD/ }).fill("e2e JD:机器人算法工程师。");
    await page.getByRole("button", { name: "分析 JD 匹配" }).click();

    // Job created with the jd-match kind; the queued progress card shows.
    const progress = page.getByTestId("jd-progress");
    await expect(progress).toBeVisible();
    await expect(progress.getByText("排队中")).toBeVisible();
    expect(createBody?.kind).toBe("studio-jd-match");
    expect(createBody?.input?.resume_md).toContain("机械臂");
    expect(createBody?.input?.jd_text).toContain("机器人算法工程师");

    // Terminal frame: the analysis card replaces the progress card.
    const analysis = page.getByTestId("jd-analysis");
    await expect(analysis).toBeVisible({ timeout: 10_000 });
    await expect(analysis).toContainText("e2e 匹配分析结论");
    await expect(progress).toHaveCount(0);
  });

  test("real LLM job runs to done (slow; sandbox live LLM)", async ({ page, request }) => {
    test.slow();
    test.setTimeout(150_000);

    await page.goto(spa("studio"));
    await expect(page.getByTestId("studio-summary")).toBeVisible();
    await page.getByRole("tab", { name: "JD 匹配" }).click();
    await page
      .getByRole("textbox", { name: "简历内容" })
      .fill("熟悉 ROS2 与机械臂运动规划,主导过 piper 臂抓取 demo 与 VLA 模型复现。");
    await page
      .getByRole("textbox", { name: /目标 JD/ })
      .fill("机器人算法工程师:熟悉 ROS2、运动规划与机械臂控制,有真实项目落地经验。");
    const createdPromise = page.waitForResponse(
      (res) => JOBS_CREATE_RE.test(res.url()) && res.request().method() === "POST",
    );
    await page.getByRole("button", { name: "分析 JD 匹配" }).click();
    const created = await createdPromise;
    expect(created.status()).toBe(202);
    const createdBody = (await created.json()) as { job_id: string };
    expect(createdBody.job_id).toMatch(/^job-/);

    // Progress card first; the real analysis takes ~55s here.
    await expect(page.getByTestId("jd-progress")).toBeVisible();

    const analysis = page.getByTestId("jd-analysis");
    const degraded = page.getByTestId("jd-degraded");
    const failed = page.getByTestId("jd-error");
    await expect(analysis.or(degraded).or(failed).first()).toBeVisible({ timeout: 120_000 });

    if (await failed.isVisible().catch(() => false)) {
      throw new Error(`jd-match job failed in the UI: ${await failed.innerText()}`);
    }
    if (await degraded.isVisible().catch(() => false)) {
      const reason = await degraded.innerText();
      if (/configured LLM/i.test(reason)) {
        test.skip(true, `sandbox LLM not configured: ${reason}`);
      }
      throw new Error(`jd-match degraded unexpectedly: ${reason}`);
    }

    // Happy path: real analysis markdown rendered from the job result.
    await expect(analysis).toBeVisible();
    await expect(analysis).not.toBeEmpty();

    // Server-side truth: the job really completed with an analysis payload.
    const status = await request.get(
      `${SPA_BASE_URL}/api/v1/profiles/${encodeURIComponent(PROFILE)}/jobs/${createdBody.job_id}`,
    );
    expect(status.status()).toBe(200);
    const payload = (await status.json()) as {
      job: { status: string };
      result: { analysis: string };
    };
    expect(payload.job.status).toBe("done");
    expect(payload.result.analysis.length).toBeGreaterThan(0);
  });
});

test.describe("SPA Project Board AI 建议引用 (project-suggest-refs job + SSE)", () => {
  test("stubbed job: 进度卡(排队中)→ AI 引用建议卡 → 合并到表单", async ({ page }) => {
    let createBody: { kind?: string; input?: { case_id?: string } } | null = null;
    await stubJobStream(
      page,
      "project-suggest-refs",
      SUGGEST_JOB_ID,
      [
        ["collecting", "收集目标/任务/证据/资料/输出候选。"],
        ["suggesting", "AI 正在生成引用建议。"],
      ],
      {
        ok: true,
        backend: "fake",
        suggestions: {
          goal_refs: [],
          task_refs: ["task-e2e-mock"],
          evidence_refs: [],
          source_refs: [],
          output_refs: [],
        },
        rationale: "e2e mock rationale",
        warnings: [],
      },
      (body) => {
        createBody = body as typeof createBody;
      },
    );

    const ts = Date.now();
    await page.goto(spa("projects"));
    await expect(page.getByTestId("projects-toolbar")).toBeVisible();
    await page.getByTestId("new-project-button").click();
    const createForm = page.getByTestId("create-case-form");
    await createForm.getByRole("textbox", { name: "标题", exact: true }).fill(`e2e-suggest-${ts}`);
    const createResponse = await waitPost(page, "/project-board/cases", () =>
      createForm.getByRole("button", { name: "创建项目" }).click(),
    );
    expect(createResponse.status()).toBe(201);
    const caseId: string = (await createResponse.json()).case.id;

    const detail = page.getByTestId("case-detail");
    await expect(detail).toBeVisible();
    await detail.getByTestId("suggest-refs-button").click();

    // Job created for this case; the queued progress card shows.
    const progress = detail.getByTestId("suggest-progress");
    await expect(progress).toBeVisible();
    await expect(progress.getByText("排队中")).toBeVisible();
    expect(createBody?.kind).toBe("project-suggest-refs");
    expect(createBody?.input?.case_id).toBe(caseId);

    // Terminal frame: suggestions land in the existing confirm-not-fill card.
    const result = detail.getByTestId("suggest-result");
    await expect(result).toBeVisible({ timeout: 10_000 });
    await expect(result).toContainText("共 1 条建议");
    await expect(result).toContainText("任务: task-e2e-mock");
    await expect(progress).toHaveCount(0);

    // The merge interaction is unchanged by the jobs migration.
    await result.getByRole("button", { name: "合并到表单" }).click();
    await expect(detail.getByTestId("suggest-result")).toHaveCount(0);
  });

  test("real LLM job reaches a terminal card (slow; sandbox live LLM)", async ({
    page,
    request,
  }) => {
    test.slow();
    test.setTimeout(120_000);

    const ts = Date.now();
    await page.goto(spa("projects"));
    await expect(page.getByTestId("projects-toolbar")).toBeVisible();
    await page.getByTestId("new-project-button").click();
    const createForm = page.getByTestId("create-case-form");
    await createForm
      .getByRole("textbox", { name: "标题", exact: true })
      .fill(`e2e-suggest-real-${ts}`);
    const createResponse = await waitPost(page, "/project-board/cases", () =>
      createForm.getByRole("button", { name: "创建项目" }).click(),
    );
    expect(createResponse.status()).toBe(201);

    const detail = page.getByTestId("case-detail");
    await expect(detail).toBeVisible();
    const createdPromise = page.waitForResponse(
      (res) => JOBS_CREATE_RE.test(res.url()) && res.request().method() === "POST",
    );
    await detail.getByTestId("suggest-refs-button").click();
    const created = await createdPromise;
    expect(created.status()).toBe(202);
    const createdBody = (await created.json()) as { job_id: string };
    expect(createdBody.job_id).toMatch(/^job-/);

    await expect(detail.getByTestId("suggest-progress")).toBeVisible();

    const result = detail.getByTestId("suggest-result");
    const degraded = detail.getByTestId("suggest-error");
    const failed = detail.getByTestId("suggest-failed");
    await expect(result.or(degraded).or(failed).first()).toBeVisible({ timeout: 90_000 });

    if (await failed.isVisible().catch(() => false)) {
      throw new Error(`suggest-refs job failed hard: ${await failed.innerText()}`);
    }
    if (await degraded.isVisible().catch(() => false)) {
      const reason = await degraded.innerText();
      if (/no backend available|not configured/i.test(reason)) {
        test.skip(true, `sandbox LLM not configured: ${reason}`);
      }
      // Provider structured-output hiccups are a designed degradation
      // outcome (checklist §2.8): reaching the terminal yellow card still
      // proves the jobs/SSE plumbing — pass with an annotation.
      test
        .info()
        .annotations.push({ type: "note", description: `degraded terminal card: ${reason}` });
    } else {
      await expect(result.getByRole("button", { name: "合并到表单" })).toBeVisible();
    }

    // Server-side truth: the job really reached a final status.
    const status = await request.get(
      `${SPA_BASE_URL}/api/v1/profiles/${encodeURIComponent(PROFILE)}/jobs/${createdBody.job_id}`,
    );
    expect(status.status()).toBe(200);
    const payload = (await status.json()) as { job: { status: string } };
    expect(["done", "failed"]).toContain(payload.job.status);
  });
});
