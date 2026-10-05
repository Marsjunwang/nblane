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
