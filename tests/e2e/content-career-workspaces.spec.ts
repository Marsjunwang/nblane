import { expect, test } from "@playwright/test";
import { SPA_BASE_URL, SPA_E2E_PROFILE } from "./spa_auth_shared";

test.describe("SPA content and career workspaces", () => {
  test("creates a post, autosaves, restores and publishes without Evidence", async ({ page }) => {
    const title = `内容工作台验收 ${Date.now()}`;
    await page.goto(`${SPA_BASE_URL}/p/${encodeURIComponent(SPA_E2E_PROFILE)}/content`);
    await expect(page.getByTestId("content-post-table").or(page.getByText("还没有文章。"))).toBeVisible();

    await page.getByTestId("content-create").click();
    await page.getByTestId("content-new-title").fill(title);
    await page.getByTestId("content-create-confirm").click();
    await expect(page).toHaveURL(/\/content\/.+/);

    // The caret lands in the body: type, then autosave settles after idle.
    await expect(page.locator(".bn-editor")).toBeVisible();
    await page.keyboard.type("无需 Evidence 的正文。");
    await expect(page.getByTestId("content-save-state")).toHaveText(/编辑中|保存中/);
    await expect(page.getByTestId("content-save-state")).toHaveText(/已保存/, { timeout: 10_000 });

    await page.reload();
    await expect(page.locator(".bn-editor")).toContainText("无需 Evidence 的正文。");
    await expect(page.getByTestId("content-title")).toHaveValue(title);

    // Publish dialog runs the gate; the missing summary is fixed inline.
    await page.getByTestId("content-publish").click();
    const dialog = page.getByTestId("content-publish-dialog");
    await expect(page.getByTestId("content-check-result")).toContainText("缺少摘要");
    await dialog.getByLabel("摘要").fill("浏览器验收摘要");
    await dialog.getByRole("button", { name: "重新检查" }).click();
    await expect(page.getByTestId("content-check-result")).toContainText("检查通过");
    await page.getByTestId("content-publish-confirm").click();
    await expect(page.getByTestId("content-published-menu")).toBeVisible();
  });

  test("leaving the editor saves pending edits first", async ({ page }) => {
    await page.goto(`${SPA_BASE_URL}/p/${encodeURIComponent(SPA_E2E_PROFILE)}/content`);
    const title = `返回保存验收 ${Date.now()}`;
    await page.getByTestId("content-create").click();
    await page.getByTestId("content-new-title").fill(title);
    await page.getByTestId("content-create-confirm").click();
    await expect(page.locator(".bn-editor")).toBeVisible();
    await page.keyboard.type("立刻返回");
    // Back before the autosave debounce fires.
    await page.getByTestId("content-back").click();
    await expect(page.getByTestId("content-post-table")).toBeVisible();
    await page.getByTestId("content-post-item").filter({ hasText: title }).click();
    await expect(page.locator(".bn-editor")).toContainText("立刻返回");
  });

  test("wide toggle widens the writing column", async ({ page }) => {
    await page.setViewportSize({ width: 1600, height: 900 });
    await page.goto(`${SPA_BASE_URL}/p/${encodeURIComponent(SPA_E2E_PROFILE)}/content`);
    await page.getByTestId("content-post-item").first().click();
    const column = page.getByTestId("content-editor");
    await expect(column).toBeVisible();
    const before = (await column.boundingBox())!.width;
    await page.getByTestId("content-wide-toggle").click();
    await expect.poll(async () => (await column.boundingBox())!.width).toBeGreaterThan(before + 200);
    await page.getByTestId("content-wide-toggle").click();
  });

  test("outline jumps to headings, ⌘K switches posts, focus mode dims the rest", async ({ page }) => {
    await page.setViewportSize({ width: 1600, height: 900 });
    const title = `目录验收 ${Date.now()}`;
    await page.goto(`${SPA_BASE_URL}/p/${encodeURIComponent(SPA_E2E_PROFILE)}/content`);
    await page.getByTestId("content-create").click();
    await page.getByTestId("content-new-title").fill(title);
    await page.getByTestId("content-create-confirm").click();
    await expect(page.locator(".bn-editor")).toBeVisible();

    await page.getByTestId("content-mode").getByText("Markdown").click();
    const body = Array.from({ length: 5 }, (_, i) => `## 第${i + 1}节\n\n${"正文。".repeat(80)}`).join("\n\n");
    await page.getByLabel("Markdown 源码").fill(body);
    await page.getByTestId("content-mode").getByText("编辑").click();

    await page.getByTestId("content-outline-toggle").click();
    const items = page.getByTestId("content-outline-item");
    await expect(items).toHaveCount(5);
    await items.nth(3).click();
    await expect(page.locator("[data-testid=content-outline-item][data-active]")).toHaveText("第4节");

    await page.getByTestId("content-focus-toggle").click();
    const outers = page.locator(".bn-editor > .bn-block-group > .bn-block-outer");
    await expect
      .poll(async () => (await outers.evaluateAll((n) => n.map((e) => getComputedStyle(e).opacity))).filter((o) => o === "1").length)
      .toBe(1);
    await page.getByTestId("content-focus-toggle").click();

    await page.keyboard.press("Control+k");
    await expect(page.getByTestId("content-switcher")).toBeVisible();
    await page.keyboard.type("内容工作台验收");
    await expect(page.getByTestId("content-switcher-item").first()).toBeVisible();
    await page.keyboard.press("Enter");
    await expect(page).not.toHaveURL(new RegExp(encodeURIComponent(title.split(" ")[1])));
  });

  test("AI cover, meta suggestions and rewrite are candidates until accepted (stubbed jobs)", async ({ page }) => {
    // Stub the job endpoints so the test never calls the LLM or the paid
    // image provider: POST /jobs returns a job id per kind, and the SSE
    // stream answers with a canned done frame.
    const results: Record<string, unknown> = {
      "content-rewrite": { operation: "polish", original: "", text: "AI 润色后的第一段。" },
      "content-meta": { titles: ["AI 标题一"], summaries: ["AI 摘要一。"], tags: ["机器人"] },
    };
    let coverCandidate = "";
    await page.route("**/api/v1/profiles/*/content/ai/status", (route) =>
      route.fulfill({ json: { text: true, cover: true } }),
    );
    await page.route("**/api/v1/profiles/*/jobs", async (route) => {
      const body = route.request().postDataJSON() as { kind: string; input: Record<string, unknown> };
      if (body.kind === "content-cover") {
        // Stage a real candidate file through the upload route is not possible;
        // reuse a 1x1 PNG served by the fulfill below instead.
        coverCandidate = "blog/.candidates/cover-e2e/generated-cover-e2e.png";
        results["content-cover"] = {
          slug: body.input.slug,
          candidates: [{ candidate_path: coverCandidate, filename: "generated-cover-e2e.png", provider: "stub", model: "stub" }],
        };
      }
      await route.fulfill({ status: 202, json: { ok: true, job_id: `job-${body.kind}`, job: { job_id: `job-${body.kind}` } } });
    });
    await page.route("**/api/v1/profiles/*/jobs/*/stream", (route) => {
      const kind = route.request().url().split("/jobs/job-")[1].split("/")[0];
      const frame = JSON.stringify({ ok: true, job: { status: "done" }, result: results[kind] });
      return route.fulfill({
        status: 200,
        headers: { "Content-Type": "text/event-stream" },
        body: `event: done\ndata: ${frame}\n\n`,
      });
    });
    await page.route("**/content/cover-candidates/file*", (route) =>
      route.fulfill({
        status: 200,
        contentType: "image/png",
        body: Buffer.from(
          "89504e470d0a1a0a0000000d4948445200000001000000010806000000" +
            "1f15c4890000000d49444154789c63000100000500010d0a2db40000000049454e44ae426082",
          "hex",
        ),
      }),
    );
    await page.route("**/cover-candidates/promote", (route) =>
      route.fulfill({ json: { ok: true, path: "media/blog/e2e/generated-cover-e2e.png" } }),
    );

    await page.goto(`${SPA_BASE_URL}/p/${encodeURIComponent(SPA_E2E_PROFILE)}/content`);
    await page.getByTestId("content-create").click();
    await page.getByTestId("content-new-title").fill(`AI 验收 ${Date.now()}`);
    await page.getByTestId("content-create-confirm").click();
    await expect(page.locator(".bn-editor")).toBeVisible();
    await page.keyboard.type("第一段原文，需要润色。");
    await page.keyboard.press("Enter");
    await page.keyboard.type("第二段保持不变。");

    // Rewrite: select paragraph 1 → toolbar AI → 润色 → diff → accept.
    await page.locator('.bn-editor [data-content-type="paragraph"]').first().click({ clickCount: 3 });
    await page.locator(".nb-ai-toolbar-button").click();
    await page.getByRole("menuitem", { name: "润色" }).click();
    await expect(page.getByTestId("content-ai-diff")).toContainText("AI 润色后的第一段。");
    await page.getByTestId("content-ai-accept").click();
    await expect(page.locator(".bn-editor")).toContainText("AI 润色后的第一段。");
    await expect(page.locator(".bn-editor")).toContainText("第二段保持不变。");
    await expect(page.locator(".bn-editor")).not.toContainText("需要润色");

    // Meta: suggestions apply only when clicked.
    await page.getByTestId("content-settings-toggle").click();
    const settings = page.getByTestId("content-properties");
    await settings.getByTestId("content-ai-meta-run").click();
    await expect(settings.getByLabel("摘要")).toHaveValue("");
    await settings.getByTestId("content-ai-summary").first().click();
    await expect(settings.getByLabel("摘要")).toHaveValue("AI 摘要一。");
    await settings.getByTestId("content-ai-tag").first().click();

    // Cover: candidate shown; 用作封面 sets the draft cover.
    await page.getByTestId("content-ai-cover-run").click();
    await expect(page.getByTestId("content-ai-cover-candidate")).toHaveCount(1);
    await page.getByTestId("content-ai-cover-use").click();
    await expect(page.getByTestId("content-ai-cover-candidate")).toHaveCount(0);
    await expect(page.getByAltText("封面预览")).toBeVisible();
  });

  test("matches a JD and saves an explicitly named tailored draft", async ({ page }) => {
    await page.goto(`${SPA_BASE_URL}/p/${encodeURIComponent(SPA_E2E_PROFILE)}/career`);
    await expect(page.getByTestId("career-workspace")).toBeVisible();
    await page.getByTestId("career-jd").fill("Python FastAPI Docker");
    await page.getByTestId("career-match").click();
    await expect(page.getByText(/匹配度/)).toBeVisible();
    await page.getByRole("tab", { name: "定制草稿" }).click();
    await page.getByLabel("目标岗位标识").fill("browser-career-acceptance");
    await page.getByLabel("定制简历草稿（人工确认后保存）").fill("# Browser career acceptance\n\n- Python");
    await page.getByRole("button", { name: "保存定制草稿" }).click();
    await expect(page.getByText("browser-career-acceptance · 已保存")).toBeVisible();
  });
});
