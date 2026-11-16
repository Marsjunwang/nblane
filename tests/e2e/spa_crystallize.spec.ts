import { expect, test } from "@playwright/test";
import { SPA_BASE_URL, SPA_E2E_PROFILE } from "./spa_auth_shared";

// Run through run.mjs: ordinary API calls use its isolated synthetic stack.
// Only the crystallize model job is stubbed; EventSource and the UI are real.
for (const scenario of [
  { partial: false, title: "batch AI crystallization survives 130 seconds and renders the completed draft" },
  { partial: true, title: "partial AI crystallization keeps successful evidence reviewable and failed tasks pending" },
]) {
  test(scenario.title, async ({ page }) => {
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
      timeout_seconds: 390,
      elapsed_ms: 0,
      error: null,
    };
    const result = {
      ok: true,
      profile,
      backend: "llm",
      patch: {
        evidence_entries: (scenario.partial ? tasks.slice(0, 1) : tasks).map((task) => ({
          type: "practice",
          title: task.title,
          summary: `${task.title}的证据草稿`,
          source_task_id: task.id,
          origin: "kanban_task",
          kanban_refs: [`kanban:${task.id}`],
          original_content: task.snapshot,
        })),
        node_updates: (scenario.partial ? tasks.slice(0, 1) : tasks).map((_, index) => ({
          id: `fixture-skill-${index + 1}`,
          evidence_refs: [`first_${index + 1}`],
        })),
      },
      tasks: tasks.map((task) => ({ ...task, kanban_ref: `kanban:${task.id}` })),
      missing: [],
      failed_tasks: scenario.partial ? [{
        task_id: tasks[1].id,
        title: tasks[1].title,
        message: "AI 生成超时（180 秒）",
      }] : [],
    };
    const frame = (event: string, data: unknown) =>
      `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
    let deleteCount = 0;
    let releaseStream = () => {};
    let markSubscribed = () => {};
    const streamReady = new Promise<void>((resolve) => { markSubscribed = resolve; });
    const streamRelease = new Promise<void>((resolve) => { releaseStream = resolve; });
    let cleaningUp = false;
    let appliedBody: Record<string, unknown> | undefined;

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
    await page.route(`**${base}/crystallize/apply`, async (route) => {
      appliedBody = route.request().postDataJSON();
      await route.fulfill({ json: {
        ok: true,
        items: [{ task_id: tasks[0].id, evidence_ids: ["fixture-evidence"] }],
        errors: [],
        warnings: [],
        new_evidence_ids: ["fixture-evidence"],
        crystallized_count: 1,
      } });
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
              job: { ...job, status: "done", phase: "done", elapsed_ms: scenario.partial ? 251_000 : 142_000 },
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

      if (scenario.partial) {
        // A task that times out at 180 seconds can still follow a successful task.
        await page.clock.fastForward(120_000);
        await expect(page.getByTestId("wizard-progress")).toBeVisible();
        await expect(page.getByTestId("wizard-ai-error")).toHaveCount(0);
        expect(deleteCount).toBe(0);
      }

      releaseStream();
      await expect(page.getByTestId("wizard-row-0")).toContainText(tasks[0].title);
      await expect(page.getByTestId("wizard-row-skills-0")).toContainText("fixture-skill-1");
      await expect(page.getByTestId("wizard-progress")).toHaveCount(0);
      await expect(page.getByTestId("wizard-ai-error")).toHaveCount(0);
      await expect(page.getByTestId("wizard-apply")).toBeEnabled();
      expect(deleteCount).toBe(0);

      if (scenario.partial) {
        const warning = page.getByTestId("wizard-partial-draft");
        await expect(warning).toContainText("部分任务未生成");
        await expect(warning).toContainText(`${tasks[1].title}：AI 生成超时（180 秒）`);
        await expect(warning).toContainText("未生成的任务会继续留在「待结晶」");
        await expect(page.getByTestId("wizard-row-1")).toHaveCount(0);
        await expect(page.getByRole("textbox", { name: "分量", exact: true })).toHaveCount(1);

        const row = page.getByTestId("wizard-row-0");
        await row.getByRole("checkbox").uncheck();
        await expect(page.getByTestId("wizard-apply")).toBeDisabled();
        await row.getByRole("checkbox").check();
        await row.getByRole("textbox", { name: "分量", exact: true }).click();
        await page.getByRole("option", { name: "强", exact: true }).click();
        await page.getByTestId("wizard-apply").click();

        await expect.poll(() => appliedBody).toMatchObject({
          task_ids: tasks.map((task) => task.id),
          include_evidence: [true],
          patch: {
            evidence_entries: [{
              title: tasks[0].title,
              strength: "strong",
              kanban_refs: [`kanban:${tasks[0].id}`],
            }],
            node_updates: [{ id: "fixture-skill-1", evidence_refs: ["first_1"] }],
          },
        });
        await expect(page.getByText("1 个任务没有入库", { exact: true })).toBeVisible();
        await expect(page.getByText(`${tasks[1].title} 没有对应的证据，仍留在「待结晶」。`, { exact: true })).toBeVisible();
      } else {
        await expect(page.getByTestId("wizard-row-1")).toContainText(tasks[1].title);
        await expect(page.getByTestId("wizard-row-skills-1")).toContainText("fixture-skill-2");
        await expect(page.getByTestId("wizard-partial-draft")).toHaveCount(0);
      }
    } finally {
      cleaningUp = true;
      releaseStream();
      await page.unrouteAll({ behavior: "wait" });
    }
  });
}
