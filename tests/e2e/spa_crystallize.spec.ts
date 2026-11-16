import { expect, test } from "@playwright/test";
import { SPA_BASE_URL, SPA_E2E_PROFILE } from "./spa_auth_shared";

// Run through run.mjs: ordinary API calls use its isolated synthetic stack.
// Only the crystallize model job is stubbed; EventSource and the UI are real.
test("batch AI crystallization survives 130 seconds and renders the completed draft", async ({ page }) => {
  const profile = SPA_E2E_PROFILE;
  const base = `/api/v1/profiles/${encodeURIComponent(profile)}`;
  const jobId = "crystallize-batch-timeout-regression";
  const tasks = [
    { id: "crystal-alpha", title: "完成规划器优化" },
    { id: "crystal-beta", title: "完成控制器验证" },
  ].map((task) => ({
    ...task,
    completed_on: "2026-11-16",
    project_id: "project:browser-fixture",
    snapshot: `# ${task.title}\nid: ${task.id}`,
    blockers: [],
  }));
  const job = {
    job_id: jobId,
    profile,
    kind: "evidence-crystallize",
    status: "running",
    phase: "drafting",
    message: "AI 正在生成第 2/2 个任务",
    timeout_seconds: 210,
    elapsed_ms: 0,
    error: null,
  };
  const result = {
    ok: true,
    profile,
    backend: "llm",
    patch: {
      evidence_entries: tasks.map((task) => ({
        type: "practice",
        title: task.title,
        summary: `${task.title}的证据草稿`,
        source_task_id: task.id,
        origin: "kanban_task",
        kanban_refs: [`kanban:${task.id}`],
        original_content: task.snapshot,
      })),
      node_updates: [],
    },
    tasks: tasks.map((task) => ({ ...task, kanban_ref: `kanban:${task.id}` })),
    missing: [],
  };
  const frame = (event: string, data: unknown) =>
    `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
  let deleteCount = 0;
  let releaseStream = () => {};
  let markSubscribed = () => {};
  const streamReady = new Promise<void>((resolve) => { markSubscribed = resolve; });
  const streamRelease = new Promise<void>((resolve) => { releaseStream = resolve; });
  let cleaningUp = false;

  await page.route(`**${base}/crystallize/candidates`, (route) =>
    route.fulfill({ json: { profile, items: tasks } }));
  await page.route(`**${base}/crystallize/draft`, async (route) => {
    expect(route.request().postDataJSON()).toMatchObject({
      task_ids: tasks.map((task) => task.id),
      use_llm: true,
    });
    await route.fulfill({ status: 202, json: { ok: true, job_id: jobId, job } });
  });
  await page.route(`**${base}/jobs/${jobId}`, async (route) => {
    if (route.request().method() === "DELETE") deleteCount += 1;
    await route.fulfill({ json: { ok: true, job, result: null } });
  });
  await page.route(`**${base}/jobs/${jobId}/stream`, async (route) => {
    markSubscribed();
    await streamRelease;
    try {
      await route.fulfill({
        status: 200,
        headers: { "content-type": "text/event-stream", "cache-control": "no-cache" },
        body: frame("job", { ok: true, job })
          + frame("progress", {
            ok: true,
            job,
            event: { phase: "drafting", message: job.message, seq: 1 },
          })
          + frame("done", {
            ok: true,
            job: { ...job, status: "done", phase: "done", elapsed_ms: 142_000 },
            result,
          }),
      });
    } catch (error) {
      if (!cleaningUp) throw error;
    }
  });

  try {
    await page.clock.install();
    await page.goto(`${SPA_BASE_URL}/p/${encodeURIComponent(profile)}/evidence?stage=crystallize`);
    await page.getByTestId("open-crystallize-wizard").click();
    for (const task of tasks) await page.getByTestId(`wizard-pick-${task.id}`).check();
    await page.getByRole("button", { name: /下一步/ }).click();
    await page.getByTestId("wizard-ai-draft").click();
    await expect(page.getByTestId("wizard-progress")).toBeVisible();
    await streamReady;

    // Reproduce the old fixed client watchdog without waiting two wall minutes.
    await page.clock.fastForward(131_000);
    await expect(page.getByTestId("wizard-progress")).toBeVisible();
    await expect(page.getByTestId("wizard-ai-error")).toHaveCount(0);
    expect(deleteCount).toBe(0);

    releaseStream();
    await expect(page.getByTestId("wizard-row-0")).toContainText(tasks[0].title);
    await expect(page.getByTestId("wizard-row-1")).toContainText(tasks[1].title);
    await expect(page.getByTestId("wizard-progress")).toHaveCount(0);
    await expect(page.getByTestId("wizard-ai-error")).toHaveCount(0);
    await expect(page.getByTestId("wizard-apply")).toBeEnabled();
    expect(deleteCount).toBe(0);
  } finally {
    cleaningUp = true;
    releaseStream();
    await page.unrouteAll({ behavior: "wait" });
  }
});
