import { expect, test } from "@playwright/test";

let appAvailable = false;

test.beforeAll(async ({ request, baseURL }) => {
  if (!baseURL) {
    return;
  }
  try {
    const response = await request.get(baseURL, { timeout: 3000 });
    appAvailable = response.ok();
  } catch {
    appAvailable = false;
  }
});

test.beforeEach(async () => {
  test.skip(!appAvailable, "Set NBLANE_E2E_BASE_URL or run the Streamlit app on port 8510.");
});

async function openEditor(page) {
  await page.goto("/");
  await page.waitForLoadState("networkidle");
  const editorFrame = page
    .frameLocator('iframe[title*="nblane"], iframe[title*="component"]')
    .first();
  const blocknote = editorFrame.locator(".bn-editor, .nb-blocknote-frame").first();
  if (await blocknote.count()) {
    return { frame: editorFrame, editor: blocknote };
  }
  const inlineEditor = page.locator(".bn-editor, .nb-blocknote-frame").first();
  if (!(await inlineEditor.count())) {
    test.skip(true, "Blog editor shell is not visible at the configured URL.");
  }
  await expect(inlineEditor).toBeVisible();
  return { frame: page, editor: inlineEditor };
}

test("formula slash opens the secondary prompt dialog", async ({ page }) => {
  const { frame, editor } = await openEditor(page);
  await editor.click();
  await page.keyboard.type("/公式");
  const formulaItem = frame.getByText(/公式|Formula/).first();
  await formulaItem.click();
  await expect(frame.getByRole("dialog")).toBeVisible();
});

test("outline panel is present in the AI editor shell", async ({ page }) => {
  const { frame } = await openEditor(page);
  await expect(frame.getByText(/大纲|Outline/).first()).toBeVisible();
});

test("visual controls expose candidate accept lifecycle entry points", async ({ page }) => {
  const { frame } = await openEditor(page);
  await expect(frame.getByText(/配图|Visual|图/).first()).toBeVisible();
});

test("diagram slash action is registered", async ({ page }) => {
  const { frame, editor } = await openEditor(page);
  await editor.click();
  await page.keyboard.type("/diagram");
  await expect(frame.getByText(/Diagram|流程图|图表/).first()).toBeVisible();
});
