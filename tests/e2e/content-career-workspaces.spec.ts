import { expect, test } from "@playwright/test";
import { SPA_BASE_URL, SPA_E2E_PROFILE } from "./spa_auth_shared";

test.describe("SPA content and career workspaces", () => {
  test("creates, edits, restores and publishes a blog without Evidence", async ({ page }) => {
    const title = `内容工作台验收 ${Date.now()}`;
    await page.goto(`${SPA_BASE_URL}/p/${encodeURIComponent(SPA_E2E_PROFILE)}/content`);
    await expect(page.getByTestId("content-workspace")).toBeVisible();

    await page.getByTestId("content-create").click();
    await page.getByTestId("content-new-title").fill(title);
    await page.getByTestId("content-create-confirm").click();
    await expect(page).toHaveURL(/\?post=/);

    const editor = page.locator(".bn-editor");
    await expect(editor).toBeVisible();
    await editor.click();
    await page.keyboard.type("无需 Evidence 的正文。");
    await expect(page.getByTestId("content-save-state")).toHaveText("有未保存的修改");
    await page.getByLabel("摘要").fill("浏览器验收摘要");
    await page.getByTestId("content-save").click();
    await expect(page.getByTestId("content-save-state")).toHaveText("已保存");

    // Reload restores the saved body from disk.
    await page.reload();
    await expect(page.locator(".bn-editor")).toContainText("无需 Evidence 的正文。");

    // Publishing runs the gate first, then flips the status.
    await page.getByTestId("content-publish").click();
    await expect(page.getByTestId("content-check-result")).toContainText("可以发布");
    await expect(page.getByTestId("content-properties")).not.toContainText("状态");
    await expect(page.getByRole("button", { name: "撤回为草稿" })).toBeVisible();
  });

  test("switching posts with unsaved edits asks before discarding", async ({ page }) => {
    await page.goto(`${SPA_BASE_URL}/p/${encodeURIComponent(SPA_E2E_PROFILE)}/content`);
    const items = page.getByTestId("content-post-item");
    await expect(items.nth(1)).toBeVisible();
    await items.nth(0).click();
    await page.locator(".bn-editor").click();
    await page.keyboard.type("未保存");
    await items.nth(1).click();
    await expect(page.getByText("切换文章会丢弃当前文章未保存的修改。")).toBeVisible();
    await page.getByRole("button", { name: "继续编辑" }).click();
    await expect(page.locator(".bn-editor")).toContainText("未保存");
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
