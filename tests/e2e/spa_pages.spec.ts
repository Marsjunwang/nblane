import { expect, test } from "@playwright/test";
import type { Page, Response } from "@playwright/test";

/**
 * Real-browser journeys for the four core SPA pages that had no e2e coverage
 * (2026-09-21 batch), against the isolated sandbox
 * (`scripts/dev-web.sh --isolated`, profile=dev):
 *
 * - 差距分析 Gap: analyze → coverage/strong/gap sections → 加入看板 lands a
 *   learning card in the kanban Queue; empty/whitespace task descriptions are
 *   intercepted client-side (no /gap/analyze request ever fires).
 * - 项目 Projects: case → milestone → task → move columns; M-FE-1
 *   regression (an unsaved basics draft survives a tab switch + the board
 *   refetch triggered by moving a task); archive; AI suggest-refs renders
 *   the degradation card on the no-LLM job-error contract (stubbed — the
 *   sandbox sources .env and its LLM is live, so the real job outcome is
 *   nondeterministic; jobs/SSE migration 2026-09-21).
 * - 输出工作室 Studio: blog create → edit markdown → save → publish check
 *   gates the missing summary → publish blocked 422 → fix → publish;
 *   从证据生成 preview → create draft → draft listed under 博客; JD 匹配
 *   renders the degradation card on the no-LLM job-error contract (stubbed
 *   — same reason as above; a live jd-match job takes ~55s here).
 * - 研究台 Research: summary card + recent sources match the API payload;
 *   Paper Library sidecar entry; sidecar coordinates point at this stack's
 *   reader port (18502, same convention as spa_home.spec.ts); the embedded
 *   workspace bootstraps auth and really loads.
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

test.describe("SPA Gap (差距分析)", () => {
  test("analyze → coverage/strong/gap sections → 加入看板 creates a Queue learning card", async ({
    page,
  }) => {
    await page.goto(spa("gap"));
    await page.getByLabel("任务描述").fill("用机械臂完成抓取并放置的任务");
    const analyze = await waitPost(page, "/gap/analyze", () =>
      page.getByRole("button", { name: "分析", exact: true }).click(),
    );
    expect(analyze.status()).toBe(200);

    // Coverage bar + the two partitions render.
    await expect(page.getByText(/技能覆盖率/)).toBeVisible();
    await expect(page.getByRole("progressbar", { name: "技能覆盖率" })).toBeVisible();
    const strong = page.getByTestId("gap-strong-section");
    const missing = page.getByTestId("gap-missing-section");
    await expect(strong).toBeVisible();
    await expect(missing).toBeVisible();
    await expect(strong.getByText(/已具备的技能 \(\d+\)/)).toBeVisible();
    await expect(missing.getByText(/能力差距 \(\d+\)/)).toBeVisible();

    // The rule-based analysis of this task always finds gaps on the dev
    // sandbox. The learning card title is 学习 <node label> — read the label
    // off the first gap row so the kanban assertion tracks the real payload.
    // (NB: a `has:` locator chain must resolve within the candidate subtree —
    // rooting it at `missing` matches nothing, and `.first()` inside `has:`
    // never matches either.)
    const firstIntake = missing.getByRole("button", { name: "加入看板" }).first();
    await expect(firstIntake).toBeVisible();
    const firstRow = missing
      .locator("div.mantine-Group-root", {
        has: page.getByRole("button", { name: "加入看板" }),
      })
      .first();
    const label = (await firstRow.locator("p").first().innerText()).trim();
    const cardTitle = `学习 ${label}`;

    const intake = await waitPost(page, "/gap/intake", () => firstIntake.click());
    expect(intake.status()).toBe(201);
    await expect(page.getByText("学习任务已加入看板 Queue。")).toBeVisible();

    // Rule results point at the deep-analysis entry: the blue info alert
    // explains the 深度分析(LLM) button (wired to the async jobs slice).
    await expect(page.getByText(/以上为规则匹配结果/)).toBeVisible();
    await expect(page.getByRole("button", { name: "深度分析(LLM)" })).toBeVisible();

    // Projects: the learning card (no project) lands in the 未归属 lane's
    // Queue column (duplicate titles from earlier runs are fine — assert the
    // first match).
    await page.goto(spa("projects"));
    const queueColumn = page.getByTestId("lane-column-unassigned-queue");
    await expect(queueColumn).toBeVisible();
    await expect(queueColumn.getByText(cardTitle).first()).toBeVisible();
  });

  test("empty and whitespace task descriptions are blocked client-side (no analyze request)", async ({
    page,
  }) => {
    let analyzeCalls = 0;
    page.on("request", (req) => {
      if (req.url().includes("/gap/analyze")) {
        analyzeCalls += 1;
      }
    });

    await page.goto(spa("gap"));
    const analyzeButton = page.getByRole("button", { name: "分析", exact: true });
    const validationError = page.getByText("请先描述要分析的任务。");

    await analyzeButton.click();
    await expect(validationError).toBeVisible();

    // Whitespace-only input is also intercepted (the page trims).
    await page.getByLabel("任务描述").fill("   ");
    await analyzeButton.click();
    await expect(validationError).toBeVisible();

    // Give any stray request a chance to fire, then prove none did.
    await page.waitForTimeout(500);
    expect(analyzeCalls, "client-side validation must not POST /gap/analyze").toBe(0);
  });
});

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

test.describe("SPA Studio (输出工作室)", () => {
  test("blog: create → edit → save → check gates summary → publish blocked → publish", async ({
    page,
  }) => {
    const ts = Date.now();
    const title = `e2e-studio-${ts}`;

    await page.goto(spa("studio"));
    await expect(page.getByTestId("studio-summary")).toBeVisible();

    // 1. Create a draft; the editor opens on the new slug.
    const createForm = page.getByTestId("create-post-form");
    await createForm.getByRole("textbox", { name: "新建博客草稿" }).fill(title);
    const createResponse = await waitPost(page, "/studio/blog", () =>
      createForm.getByRole("button", { name: "创建", exact: true }).click(),
    );
    expect(createResponse.status()).toBe(201);
    const slug: string = (await createResponse.json()).post.slug;
    expect(slug).toBeTruthy();

    const editor = page.getByTestId("post-editor");
    await expect(editor).toBeVisible();

    // 2. Edit the markdown body and save.
    await page.getByTestId("post-body").fill(`# ${title}\n\n正文内容 e2e。`);
    const saveResponse = await waitPost(page, "/save", () =>
      editor.getByRole("button", { name: "保存", exact: true }).click(),
    );
    expect(saveResponse.status()).toBe(200);

    // 3. Publish check gates the missing summary (read-only, nothing saved).
    const checkResponse = await waitPost(page, "/check", () =>
      editor.getByRole("button", { name: "发布检查" }).click(),
    );
    expect(checkResponse.status()).toBe(200);
    const checkResult = page.getByTestId("check-result");
    await expect(checkResult).toBeVisible();
    await expect(checkResult).toContainText("发布前检查未通过");
    await expect(checkResult).toContainText("summary");

    // 4. Publish is blocked with the 422 gate (blog_publish_blocked).
    const blockedResponse = await waitPost(page, "/publish", () =>
      page.getByTestId("publish-button").click(),
    );
    expect(blockedResponse.status()).toBe(422);
    expect((await blockedResponse.json()).code).toBe("blog_publish_blocked");
    const publishError = editor.getByTestId("mutation-error");
    await expect(publishError).toBeVisible();
    await expect(publishError).toContainText("发布失败");
    await expect(publishError).toContainText("summary");

    // 5. Fill the summary; the same editor publishes in one call.
    await editor.getByRole("textbox", { name: "摘要" }).fill(`e2e 摘要 ${ts}`);
    const publishedResponse = await waitPost(page, "/publish", () =>
      page.getByTestId("publish-button").click(),
    );
    expect(publishedResponse.status()).toBe(200);
    await expect(editor.getByText("已发布", { exact: true }).first()).toBeVisible();
    await expect(page.getByTestId("publish-button")).toBeDisabled();
  });

  test("从证据生成: evidence preview → create draft → draft listed under 博客", async ({
    page,
  }) => {
    await page.goto(spa("studio"));
    await expect(page.getByTestId("studio-summary")).toBeVisible();

    await page.getByRole("tab", { name: "从证据生成" }).click();
    await page.getByRole("radio", { name: "证据" }).click();
    await page.getByRole("textbox", { name: "证据", exact: true }).click();
    await page.getByRole("option").first().click();

    const previewResponse = await waitPost(page, "/candidates/preview", () =>
      page.getByRole("button", { name: "生成预览" }).click(),
    );
    expect(previewResponse.status()).toBe(200);
    await expect(page.getByTestId("candidate-preview")).toBeVisible();

    const draftResponse = await waitPost(page, "/candidates/create", () =>
      page.getByTestId("create-draft-button").click(),
    );
    expect(draftResponse.status()).toBe(201);
    const created = await draftResponse.json();
    expect(created.slug).toBeTruthy();
    await expect(page.getByTestId("draft-created")).toBeVisible();

    // The new draft is listed under the blog tab after the refetch.
    await page.getByRole("tab", { name: "博客" }).click();
    await expect(page.getByTestId(`post-row-${created.slug}`)).toBeVisible();
  });

  test("JD 匹配 shows the degradation card on the no-LLM job contract", async ({ page }) => {
    // Same sandbox reality as the project-board AI journey: the LLM is LIVE
    // here (a real jd-match job takes ~55s), so the deterministic no-LLM
    // degradation journey stubs the documented job-error contract
    // (studio_jd_match_unavailable, the same code the sync endpoint used to
    // answer as 422) at the network edge; the page's create-job → SSE →
    // error → degradation-card mapping is exercised for real.
    await stubFailingJob(page, "studio-jd-match", "mock-jd-fail", {
      code: "studio_jd_match_unavailable",
      message:
        "JD match analysis requires a configured LLM backend " +
        "(set LLM_API_KEY / LLM_BASE_URL); the rest of the studio works without it.",
    });

    await page.goto(spa("studio"));
    await expect(page.getByTestId("studio-summary")).toBeVisible();

    await page.getByRole("tab", { name: "JD 匹配" }).click();
    await page.getByRole("textbox", { name: "简历内容" }).fill("e2e 简历：机械臂开发经验。");
    await page.getByRole("textbox", { name: /目标 JD/ }).fill("e2e JD：机器人算法工程师。");
    await page.getByRole("button", { name: "分析 JD 匹配" }).click();

    // Progress card first, then the yellow degradation card replaces it.
    await expect(page.getByTestId("jd-progress")).toBeVisible();
    const degraded = page.getByTestId("jd-degraded");
    await expect(degraded).toBeVisible();
    await expect(degraded).toContainText("AI 分析不可用");
    await expect(degraded).toContainText("配置 LLM 后重试");
    await expect(page.getByTestId("jd-progress")).toHaveCount(0);
  });
});

test.describe("SPA Research (研究台)", () => {
  test("summary card + recent sources render from the API payload; sidecar entry exists", async ({
    page,
    request,
  }) => {
    const response = await request.get(api(`/profiles/${encodeURIComponent(PROFILE)}/research`));
    expect(response.status()).toBe(200);
    const data = await response.json();

    await page.goto(spa("research"));

    const summaryCard = page.getByTestId("research-summary");
    await expect(summaryCard).toBeVisible();
    await expect(summaryCard).toContainText(`来源 ${data.summary.total}`);
    await expect(summaryCard).toContainText(`进行中 ${data.summary.active_total}`);

    const sourcesCard = page.getByTestId("research-sources");
    await expect(sourcesCard).toBeVisible();
    const rows = sourcesCard.locator("tbody tr");
    await expect(rows).toHaveCount(data.sources.length);
    if (data.sources.length > 0) {
      await expect(rows.first()).toContainText(
        data.sources[0].title || data.sources[0].id,
      );
    }

    // Paper Library sidecar entry: card + external link with the sidecar URL.
    await expect(page.getByTestId("research-paper-library")).toBeVisible();
    await expect(page.getByRole("link", { name: "新标签打开" })).toHaveAttribute(
      "href",
      data.sidecar.paper_library_url,
    );
  });

  test("sidecar coordinates point at 18502 and the embedded Paper Library really loads", async ({
    page,
    request,
  }) => {
    const response = await request.get(api(`/profiles/${encodeURIComponent(PROFILE)}/research`));
    expect(response.status()).toBe(200);
    const sidecar = (await response.json()).sidecar;
    // Same convention as spa_home.spec.ts: the sandbox payload must follow
    // the stack's reader port, not the hardcoded 8502 default.
    expect(sidecar.base).toBe(EXPECTED_SIDECAR_BASE);
    expect(sidecar.configured).toBe(true);
    expect(sidecar.paper_library_url).toContain(`${EXPECTED_SIDECAR_BASE}/paper-library`);

    await page.goto(spa("research"));
    await expect(page.getByTestId("research-paper-library")).toBeVisible();

    // Auth-on sandbox: the SPA bootstraps the sidecar session cookie via a
    // hidden form POST before the content iframe gets its src (auth-off
    // stacks skip the bootstrap entirely).
    const authBootstrap = sidecar.handoff_token
      ? page.waitForRequest(
          (req) => req.url() === `${sidecar.base}/auth/session` && req.method() === "POST",
        )
      : Promise.resolve(null);
    const libraryLoaded = page.waitForResponse(
      (res) =>
        res.url().startsWith(`${sidecar.base}/paper-library`) &&
        res.request().resourceType() === "document",
      { timeout: 20_000 },
    );

    await page.getByRole("button", { name: "嵌入显示" }).click();
    await authBootstrap;

    const frame = page.locator('iframe[data-testid="sidecar-frame"]');
    await expect(frame).toBeVisible();
    await expect(frame).toHaveAttribute("src", sidecar.paper_library_url);
    const libraryResponse = await libraryLoaded;
    expect(libraryResponse.status(), "paper library document should load, not refuse").toBe(200);
  });
});
