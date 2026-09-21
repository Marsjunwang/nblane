import { expect, test } from "@playwright/test";

/**
 * Real-browser journey for the Public Build SPA page (公开构建), against the
 * isolated sandbox (`scripts/dev-web.sh --isolated`, profile=dev):
 *
 * 打开页 → 状态总览渲染（校验/产物/草稿）→ 触发一次构建（dev 档案为 private，
 * 需开「包含草稿」预览模式）→ 成功反馈 → 产物清单可见且 index.html 真实可下载
 * → 整站预览 iframe 指向 preview/page 端点且真实返回 HTML。
 *
 * The build is idempotent and lands in the sandbox `.dev-data/dist/public/dev`
 * only — no entity seeding, so reruns never collide; the first run sees
 * 「尚未构建」, later runs 「已有产物」, both are accepted.
 */

const SPA_BASE_URL = (process.env.NBLANE_E2E_SPA_BASE_URL || "http://127.0.0.1:18504").replace(
  /\/+$/,
  "",
);
const PROFILE = process.env.NBLANE_E2E_PROFILE || "dev";

function spa(path: string): string {
  return `${SPA_BASE_URL}/p/${encodeURIComponent(PROFILE)}/${path}`;
}

test.describe("SPA Public Build (公开构建)", () => {
  test("overview → build → success feedback → artifacts + preview", async ({ page }) => {
    await page.goto(spa("public-build"));

    // 状态渲染: navbar entry + status card (validation ok after the sandbox
    // outputs.yaml type fix; both build-state badges accepted for reruns).
    await expect(page.getByRole("link", { name: "公开构建", exact: true })).toBeVisible();
    const status = page.getByTestId("build-status");
    await expect(status).toBeVisible();
    await expect(status.getByTestId("validation-ok")).toBeVisible();
    await expect(status).toContainText(".dev-data/dist/public/dev");
    await expect(
      status.getByTestId("build-exists").or(status.getByTestId("build-empty")),
    ).toBeVisible();

    // Drafts section and the by-design notes card render.
    await expect(page.getByTestId("draft-list")).toBeVisible();
    await expect(page.getByTestId("build-notes")).toContainText("同步");
    await expect(page.getByTestId("build-notes")).toContainText("输出工作室");

    // 触发构建: dev 档案 visibility=private → 必须开「包含草稿」预览模式。
    await page.getByRole("switch", { name: /包含草稿/ }).click();
    const buildResponsePromise = page.waitForResponse(
      (res) => res.url().includes("/public-build/build") && res.request().method() === "POST",
    );
    await page.getByTestId("build-button").click();
    const buildResponse = await buildResponsePromise;
    expect(buildResponse.status()).toBe(200);
    const built = await buildResponse.json();
    expect(built.output_dir).toContain(".dev-data/dist/public/dev");
    expect(built.page_count).toBeGreaterThan(0);

    // 成功反馈。
    const success = page.getByTestId("build-success");
    await expect(success).toBeVisible();
    await expect(success).toContainText("已构建");

    // 产物可见: the artifacts table lists index.html and the link really
    // downloads (200 text/html through the same authenticated session).
    const artifactRow = page.getByTestId("artifact-index.html");
    await expect(artifactRow).toBeVisible();
    const href = await artifactRow.locator("a").getAttribute("href");
    expect(href).toContain(`/api/v1/profiles/${encodeURIComponent(PROFILE)}/public-build/artifacts/index.html`);
    const artifact = await page.request.get(new URL(href!, SPA_BASE_URL).toString());
    expect(artifact.status()).toBe(200);
    expect(artifact.headers()["content-type"]).toContain("text/html");
    expect(await artifact.text()).toContain("<html");

    // The status card flips to 已有产物 after the invalidation refetch.
    await expect(status.getByTestId("build-exists")).toBeVisible();

    // 整站预览: the iframe points at the preview/page endpoint and the same
    // endpoint really serves self-contained HTML (inline CSS).
    const frame = page.getByTestId("preview-frame");
    await expect(frame).toBeVisible();
    const src = await frame.getAttribute("src");
    expect(src).toContain("/public-build/preview/page");
    expect(src).toContain("path=index.html");
    const preview = await page.request.get(new URL(src!, SPA_BASE_URL).toString());
    expect(preview.status()).toBe(200);
    expect(preview.headers()["content-type"]).toContain("text/html");
    expect(await preview.text()).toContain("<html");
  });

  test("private profile without 包含草稿 hits the visibility gate (422)", async ({ page }) => {
    await page.goto(spa("public-build"));
    await expect(page.getByTestId("build-status")).toBeVisible();

    // Sandbox dev is visibility=private: a production build (switch off) is
    // blocked by the core visibility gate — the page shows the core message.
    const buildResponsePromise = page.waitForResponse(
      (res) => res.url().includes("/public-build/build") && res.request().method() === "POST",
    );
    await page.getByTestId("build-button").click();
    const buildResponse = await buildResponsePromise;
    expect(buildResponse.status()).toBe(422);
    expect((await buildResponse.json()).code).toBe("public_build_blocked");
    const error = page.getByTestId("mutation-error");
    await expect(error).toBeVisible();
    await expect(error).toContainText("visibility");
  });
});
