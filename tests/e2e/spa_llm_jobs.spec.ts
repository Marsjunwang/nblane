import { expect, test } from "@playwright/test";
import type { Page, Response } from "@playwright/test";

/**
 * JD 匹配 (career-match) + AI 建议引用 (project-suggest-refs) 的
 * LLM jobs + SSE 迁移 e2e(2026-09-21,沿用已删除的 spa_gap_deep.spec.ts 手法):
 *
 * - Fast path (network stub): `POST /api/v1/profiles/{name}/jobs` 被拦截
 *   返回 202 mock job,SSE stream 端点按帧序列兑现(job → progress 阶段 →
 *   done + result)。页面全链路为真:按钮 → 建 job → EventSource 订阅 →
 *   进行中状态 → 结果渲染(JD 为结构化匹配报告,suggest-refs 额外验证
 *   confirm-not-fill「合并到表单」交互)。与 spa_home.spec.ts 模拟 sidecar
 *   不可达同手法,除网络外全链路真实、确定性。
 * - Slow path (real LLM, test.slow): 隔离沙箱 web-api source 仓库 .env
 *   有活 LLM,真实 job 跑到终态。JD 匹配真实分析约 55s(给 150s 超时);
 *   suggest-refs 的 provider 结构化输出校验失败是设计内降级(黄卡,见
 *   体验官手册 §2.8),慢路径只断言「进度卡 → 终态卡」管道畅通,不断言
 *   provider 输出质量。仅当确认 LLM 未配置时 skip。
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

async function createCareerTarget(page: Page, target: string): Promise<string> {
  await page.goto(spa("career"));
  await expect(page.getByTestId("career-workspace")).toBeVisible();
  await page.getByTestId("career-new-target").click();
  await page.getByTestId("career-new-target-name").fill(target);
  const created = await waitPost(page, "/career/drafts", () =>
    page.getByTestId("career-new-target-confirm").click(),
  );
  expect(created.status()).toBe(201);
  const draft = (await created.json()) as { markdown: string };
  await expect(page.getByTestId("career-target")).toBeVisible();
  await expect(page.getByTestId("career-target-name")).toHaveText(target);
  return draft.markdown;
}

async function deleteCareerTarget(page: Page, target: string): Promise<void> {
  await expect(page.getByTestId("career-save-state")).toHaveText(/已保存/, { timeout: 10_000 });
  await page.getByRole("button", { name: "删除", exact: true }).click();
  await page.getByTestId("career-delete-confirm").click();
  await expect(page.getByTestId("career-workspace")).toBeVisible();
  await expect(page.getByTestId("career-target-row").filter({ hasText: target })).toHaveCount(0);
}

test.describe("SPA Career JD 匹配 (career-match job + SSE)", () => {
  test("stubbed job: 匹配按钮(分析中)→ 结构化匹配报告", async ({ page }) => {
    let createBody: {
      kind?: string;
      input?: { resume_md?: string; jd_text?: string; notes?: string; use_evidence?: boolean };
    } | null = null;
    await stubJobStream(
      page,
      "career-match",
      JD_JOB_ID,
      [
        ["analyzing", "分析中:汇总档案证据与简历上下文。"],
        ["generating", "生成中:LLM 正在撰写匹配分析。"],
      ],
      {
        method: "llm",
        score: 88,
        summary: "e2e 匹配分析结论：符合。",
        requirements: [
          {
            requirement: "机器人算法经验",
            verdict: "match",
            basis: "e2e 匹配依据：机械臂项目。",
            evidence_refs: [],
          },
        ],
        strengthen: ["e2e 建议：补充量化指标。"],
        gaps: [],
        keywords: ["ROS2"],
        de_emphasize: [],
        interview_questions: [],
        evidence: [],
        evidence_used: 0,
      },
      (body) => {
        createBody = body as typeof createBody;
      },
    );

    const target = `e2e-jd-stub-${Date.now()}`;
    const resumeMarkdown = await createCareerTarget(page, target);
    const jdText = "e2e JD：机器人算法工程师，需要 ROS2 与机械臂开发经验。";
    await page.getByTestId("career-jd").fill(jdText);
    const matchButton = page.getByTestId("career-match");
    const createdPromise = page.waitForResponse(
      (res) => JOBS_CREATE_RE.test(res.url()) && res.request().method() === "POST",
    );
    await matchButton.click();
    const created = await createdPromise;
    expect(created.status()).toBe(202);
    expect(((await created.json()) as { job_id: string }).job_id).toBe(JD_JOB_ID);

    // The current workspace shows the pending job in the match button.
    await expect(matchButton).toBeDisabled();
    await expect(matchButton).toContainText("分析中…");
    expect(createBody?.kind).toBe("career-match");
    expect(createBody?.input?.resume_md).toBe(resumeMarkdown);
    expect(createBody?.input?.resume_md?.length).toBeGreaterThan(0);
    expect(createBody?.input?.jd_text).toBe(jdText);
    expect(createBody?.input?.notes).toBe("");
    expect(createBody?.input?.use_evidence).toBe(true);

    // The terminal SSE frame renders the structured report and ends the busy state.
    const report = page.getByTestId("career-match-report");
    await expect(report).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId("career-match-score")).toHaveText("88");
    await expect(report).toContainText("e2e 匹配分析结论");
    await expect(page.getByTestId("career-requirements")).toContainText("e2e 匹配依据：机械臂项目。");
    await expect(page.getByTestId("career-strengthen")).toContainText("补充量化指标");
    await expect(matchButton).toBeEnabled();
    await expect(matchButton).toHaveText("重新匹配");
    await deleteCareerTarget(page, target);
  });

  test("real LLM job runs to done (slow; sandbox live LLM)", async ({ page, request }) => {
    test.slow();
    test.setTimeout(150_000);

    // Do not enqueue a known-unconfigured model; all other failures remain test failures.
    const careerResponse = await request.get(
      `${SPA_BASE_URL}/api/v1/profiles/${encodeURIComponent(PROFILE)}/career`,
    );
    expect(careerResponse.status()).toBe(200);
    const career = (await careerResponse.json()) as { ai_available: boolean };
    test.skip(career.ai_available === false, "sandbox LLM not configured");

    const target = `e2e-jd-real-${Date.now()}`;
    const resumeMarkdown = await createCareerTarget(page, target);
    const jdText = "机器人算法工程师：熟悉 ROS2、运动规划与机械臂控制，有真实项目落地经验。";
    await page.getByTestId("career-jd").fill(jdText);
    const matchButton = page.getByTestId("career-match");
    const createdPromise = page.waitForResponse(
      (res) => JOBS_CREATE_RE.test(res.url()) && res.request().method() === "POST",
    );
    await matchButton.click();
    const created = await createdPromise;
    expect(created.status()).toBe(202);
    const createdBody = (await created.json()) as { job_id: string; job: { kind: string } };
    expect(createdBody.job_id).toMatch(/^job-/);
    expect(createdBody.job.kind).toBe("career-match");
    const requestBody = created.request().postDataJSON() as {
      kind: string;
      input: { resume_md: string; jd_text: string; use_evidence: boolean };
    };
    expect(requestBody.kind).toBe("career-match");
    expect(requestBody.input.resume_md).toBe(resumeMarkdown);
    expect(requestBody.input.jd_text).toBe(jdText);
    expect(requestBody.input.use_evidence).toBe(true);

    // The real job is pending while the LLM compares the master resume with the JD.
    await expect(matchButton).toBeDisabled();
    await expect(matchButton).toContainText(/分析中…|AI 正在逐条比对 JD 要求。/);

    const report = page.getByTestId("career-match-report");
    const failed = page.getByRole("alert").filter({ hasText: "匹配失败" });
    await expect(report.or(failed).first()).toBeVisible({ timeout: 120_000 });

    if (await failed.isVisible().catch(() => false)) {
      const reason = await failed.innerText();
      if (/未配置 LLM|configured LLM/i.test(reason)) {
        test.skip(true, `sandbox LLM not configured: ${reason}`);
      }
      throw new Error(`career-match job failed in the UI: ${reason}`);
    }

    // Happy path: the real structured result is rendered, including at least one JD requirement.
    await expect(report).toBeVisible();
    await expect(page.getByTestId("career-match-score")).toHaveText(/^(100|[0-9]{1,2})$/);
    await expect(page.getByTestId("career-requirements").locator("tbody tr").first()).toBeVisible();
    await expect(matchButton).toBeEnabled();
    await expect(matchButton).toHaveText("重新匹配");

    // Server-side truth: the same job completed with a non-empty career-match payload.
    const status = await request.get(
      `${SPA_BASE_URL}/api/v1/profiles/${encodeURIComponent(PROFILE)}/jobs/${createdBody.job_id}`,
    );
    expect(status.status()).toBe(200);
    const payload = (await status.json()) as {
      job: { kind: string; status: string };
      result: {
        method: string;
        score: number;
        summary: string;
        requirements: { requirement: string; verdict: string; basis: string }[];
      };
    };
    expect(payload.job.kind).toBe("career-match");
    expect(payload.job.status).toBe("done");
    expect(payload.result.method).toBe("llm");
    expect(Number.isFinite(payload.result.score)).toBe(true);
    expect(payload.result.score).toBeGreaterThanOrEqual(0);
    expect(payload.result.score).toBeLessThanOrEqual(100);
    expect(typeof payload.result.summary).toBe("string");
    expect(payload.result.requirements.length).toBeGreaterThan(0);
    expect(payload.result.requirements[0].requirement.length).toBeGreaterThan(0);
    await deleteCareerTarget(page, target);
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
    test.setTimeout(630_000);

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
    const jobUrl = `${SPA_BASE_URL}/api/v1/profiles/${encodeURIComponent(PROFILE)}/jobs/${createdBody.job_id}`;
    await expect
      .poll(
        async () => {
          const response = await request.get(jobUrl);
          if (response.status() === 404) return "missing";
          const payload = (await response.json()) as { job?: { status?: string } };
          return payload.job?.status || "unknown";
        },
        { timeout: 600_000, intervals: [1000, 2000, 5000, 10_000] },
      )
      .toMatch(/^(done|failed)$/);
    await expect(result.or(degraded).or(failed).first()).toBeVisible({ timeout: 15_000 });

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
