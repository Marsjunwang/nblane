import { expect, request as apiRequest, test } from "@playwright/test";
import type { APIRequestContext, Page } from "@playwright/test";
import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import { execFileSync } from "node:child_process";
import { pbkdf2Sync, randomBytes } from "node:crypto";
import fs from "node:fs";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const e2eDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(e2eDir, "../..");
const python = path.join(repoRoot, ".venv", "bin", "python");
const profile = "dev";
const otherProfile = "other";
const sourceId = "source:paper:agent-policy";
const otherSourceId = "source:paper:other-source";
const password = "test1234";
const collectionTitle = "人工集合 · Reader Policy";
const confirmHeader = "X-Nblane-Confirm";

interface SeedInfo {
  pdf: string;
  sources: string;
  pages: string;
  segments: string;
  annotations: string;
}

interface JournalEntry {
  id: string;
  actor: string;
  action: string;
  tier: string;
  summary: string;
  status: "undoable" | "conflict" | "undone";
}

interface PaperState {
  id: string;
  title: string;
  last_page: number;
  page_count: number;
}

let tempRoot = "";
let spaBase = "";
let readerBase = "";
let seed: SeedInfo;
let readerServer: ChildProcessWithoutNullStreams | null = null;
let spaServer: ChildProcessWithoutNullStreams | null = null;
const serverOutput = { reader: "", spa: "" };
const serverLogs = { reader: "", spa: "" };

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function freePort(): Promise<number> {
  return new Promise((resolve, reject) => {
    const socket = net.createServer();
    socket.once("error", reject);
    socket.listen(0, "127.0.0.1", () => {
      const address = socket.address();
      socket.close(() => {
        if (address && typeof address === "object") resolve(address.port);
        else reject(new Error("Could not allocate an isolated TCP port."));
      });
    });
  });
}

async function assertPortFree(port: number, envName: string): Promise<void> {
  await new Promise<void>((resolve, reject) => {
    const socket = net.createServer();
    socket.once("error", (error) => {
      reject(new Error(`${envName}=${port} is not available; refusing to use an existing service: ${error.message}`));
    });
    socket.listen(port, "127.0.0.1", () => socket.close(() => resolve()));
  });
}

async function requestedPort(envName: string, excluded: number[]): Promise<number> {
  const raw = (process.env[envName] || "").trim();
  if (raw) {
    const value = Number(raw);
    if (!Number.isInteger(value) || value < 1 || value > 65535) {
      throw new Error(`${envName} must be a TCP port between 1 and 65535; got ${raw}`);
    }
    await assertPortFree(value, envName);
    return value;
  }
  for (;;) {
    const value = await freePort();
    if (!excluded.includes(value)) return value;
  }
}

function baseEnvironment(): NodeJS.ProcessEnv {
  return {
    ...process.env,
    PATH: `${path.join(tempRoot, "bin")}:${process.env.PATH || ""}`,
    PYTHONPATH: path.join(repoRoot, "src"),
    PYTHONDONTWRITEBYTECODE: "1",
    NBLANE_ROOT: tempRoot,
    NBLANE_AUTH_FILE: path.join(tempRoot, "auth", "users.yaml"),
    NBLANE_AUTH_SESSION_SECRET: "agent-reader-e2e-auth-secret",
    NBLANE_READER_TOKEN_SECRET: "agent-reader-e2e-reader-secret",
    NBLANE_AUTH_COOKIE_SECURE: "0",
    NBLANE_RESEARCH_ASSET_ROOT: path.join(tempRoot, "assets"),
    NBLANE_AGENT_STATE_DIR: path.join(tempRoot, "agent-state"),
    NBLANE_AGENT_DATA_ROOT: path.join(tempRoot, "agent-data"),
    NBLANE_ENV_FILE: path.join(tempRoot, "empty.env"),
    NBLANE_DISABLE_NETWORK_LOOKUPS: "1",
    NBLANE_DATA_GIT_AUTOCOMMIT: "0",
    NBLANE_DATA_GIT_AUTOPUSH: "0",
    NBLANE_READER_FULL_DOCUMENT_PAYLOAD: "0",
    NBLANE_OPENCLAW_PROFILE: "e2e-agent-reader-policy",
    NBLANE_OPENCLAW_GATEWAY_PORT: "1",
    LLM_API_KEY: "",
    LLM_BASE_URL: "",
    UI_LANG: "zh",
  };
}

function writeAuthAndLocalProbeFixture(): void {
  const iterations = 600_000;
  const salt = randomBytes(16);
  const digest = pbkdf2Sync(password, salt, iterations, 32, "sha256");
  const hash = [
    "pbkdf2_sha256",
    String(iterations),
    salt.toString("base64"),
    digest.toString("base64"),
  ].join("$");
  const authDir = path.join(tempRoot, "auth");
  fs.mkdirSync(authDir, { recursive: true });
  fs.writeFileSync(
    path.join(authDir, "users.yaml"),
    `schema_version: "1.0"\nusers:\n  admin:\n    display_name: Admin\n    password_hash: "${hash}"\n    role: admin\n  agent:\n    display_name: Agent\n    password_hash: "${hash}"\n    role: member\n    agent: true\n    profiles: [dev]\n`,
    { encoding: "utf8", mode: 0o600 },
  );

  // Only the unrelated OpenClaw status probe is isolated. The SPA, Reader,
  // journal, browser handoff and undo endpoints are the real applications.
  const binDir = path.join(tempRoot, "bin");
  fs.mkdirSync(binDir, { recursive: true });
  fs.writeFileSync(
    path.join(binDir, "openclaw"),
    `#!/bin/sh\ncase " $* " in\n  *" --version "*) echo "e2e-local"; exit 0 ;;\n  *" automations "*) echo '{"automations":[]}'; exit 0 ;;\nesac\nexit 0\n`,
    { encoding: "utf8", mode: 0o755 },
  );
  fs.writeFileSync(path.join(tempRoot, "empty.env"), "", "utf8");
}

const seedScript = `
import json
from pathlib import Path
import fitz

from nblane.core.profile_io import profile_dir
from nblane.core.research_papers import (
    PaperPage,
    PaperSegment,
    import_paper_pdf,
    paper_pdf_asset_path,
    save_paper_pages,
    save_paper_segments,
    text_hash,
)
from nblane.core.research_sources import ResearchSourceInbox, add_research_source, save_research_sources
from nblane.core.research_workspace import source_slug

profile = "dev"
source_id = "source:paper:agent-policy"
other_source_id = "source:paper:other-source"
pdir = profile_dir(profile)
pdir.mkdir(parents=True, exist_ok=False)
profile_dir("other").mkdir(parents=True, exist_ok=False)
texts = ["Deterministic passage for agent annotation.", "Second page for reading progress."]
doc = fitz.open()
for text in texts:
    page = doc.new_page(width=360, height=240)
    page.insert_text((36, 72), text, fontsize=10)
pdf_bytes = doc.tobytes()
doc.close()

inbox = ResearchSourceInbox(profile=profile)
add_research_source(
    inbox,
    "Agent Reader Policy Paper",
    source_id=source_id,
    kind="paper",
    status="reading",
    visibility="private",
    metadata={"last_read_page": 1},
)
add_research_source(
    inbox,
    "Other Source",
    source_id=other_source_id,
    kind="paper",
    status="reading",
    visibility="private",
    metadata={"last_read_page": 1},
)
save_research_sources(pdir, inbox)
import_paper_pdf(pdir, source_id, pdf_bytes, "agent-policy.pdf")
save_paper_pages(
    pdir,
    source_id,
    [PaperPage(source_id=source_id, page=index, text=text, text_hash=text_hash(text))
     for index, text in enumerate(texts, 1)],
)
save_paper_segments(
    pdir,
    source_id,
    [PaperSegment(segment_id=f"seg:{index}", source_id=source_id, page=index,
                  order=index, text=text, text_hash=text_hash(text))
     for index, text in enumerate(texts, 1)],
)
slug = source_slug(source_id)
result = {
    "pdf": str(paper_pdf_asset_path(pdir, source_id)),
    "sources": str(pdir / "research" / "sources.yaml"),
    "pages": str(pdir / "research" / "paper-pages" / f"{slug}.jsonl"),
    "segments": str(pdir / "research" / "paper-segments" / f"{slug}.jsonl"),
    "annotations": str(pdir / "research" / "annotations" / f"{slug}.jsonl"),
}
print("NBLANE_E2E_SEED=" + json.dumps(result))
`;

function seedProfile(): SeedInfo {
  const stdout = execFileSync(python, ["-c", seedScript], {
    cwd: repoRoot,
    env: baseEnvironment(),
    encoding: "utf8",
    timeout: 30_000,
  });
  const marker = "NBLANE_E2E_SEED=";
  const line = stdout.trim().split(/\r?\n/).find((row) => row.startsWith(marker));
  if (!line) throw new Error(`Core seed returned no fixture metadata: ${stdout}`);
  return JSON.parse(line.slice(marker.length)) as SeedInfo;
}

function startServer(kind: "reader" | "spa", port: number): ChildProcessWithoutNullStreams {
  const module = kind === "reader" ? "nblane.web_reader_api:app" : "nblane.web_api:app";
  fs.writeFileSync(serverLogs[kind], "", "utf8");
  const child = spawn(
    python,
    ["-m", "uvicorn", module, "--host", "127.0.0.1", "--port", String(port)],
    {
      cwd: repoRoot,
      env: {
        ...baseEnvironment(),
        NBLANE_READER_API_BASE: readerBase,
        NBLANE_SPA_BASE_URL: spaBase,
      },
    },
  );
  const capture = (chunk: Buffer) => {
    const text = chunk.toString();
    serverOutput[kind] = `${serverOutput[kind]}${text}`.slice(-200_000);
    fs.appendFileSync(serverLogs[kind], text, "utf8");
  };
  child.stdout.on("data", capture);
  child.stderr.on("data", capture);
  return child;
}

function diagnostics(): string {
  return `\n--- Reader server ---\n${serverOutput.reader}\n--- SPA server ---\n${serverOutput.spa}`;
}

async function waitForHttp(url: string, child: ChildProcessWithoutNullStreams): Promise<void> {
  const deadline = Date.now() + 30_000;
  let lastError = "not attempted";
  while (Date.now() < deadline) {
    if (child.exitCode !== null || child.signalCode !== null) {
      throw new Error(`Server exited while waiting for ${url}.${diagnostics()}`);
    }
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(1500) });
      if (response.ok) return;
      lastError = `${response.status} ${response.statusText}`;
    } catch (error) {
      lastError = error instanceof Error ? error.message : String(error);
    }
    await delay(200);
  }
  throw new Error(`Timed out waiting for ${url}: ${lastError}.${diagnostics()}`);
}

async function stopServer(child: ChildProcessWithoutNullStreams | null): Promise<void> {
  if (!child || child.exitCode !== null || child.signalCode !== null) return;
  const exited = new Promise<void>((resolve) => child.once("exit", () => resolve()));
  child.kill("SIGTERM");
  const deadline = Date.now() + 5000;
  while (child.exitCode === null && child.signalCode === null && Date.now() < deadline) {
    await delay(50);
  }
  if (child.exitCode === null && child.signalCode === null) child.kill("SIGKILL");
  await exited;
}

async function stopServers(): Promise<void> {
  await Promise.all([stopServer(readerServer), stopServer(spaServer)]);
  readerServer = null;
  spaServer = null;
}

test.beforeAll(async ({}, testInfo) => {
  if (!fs.existsSync(python)) throw new Error(`Repo virtualenv Python is required: ${python}`);
  tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), "nblane-agent-reader-e2e-"));
  const logsDir = testInfo.outputPath("server-logs");
  fs.mkdirSync(logsDir, { recursive: true });
  serverLogs.reader = path.join(logsDir, "reader.log");
  serverLogs.spa = path.join(logsDir, "spa.log");
  try {
    writeAuthAndLocalProbeFixture();
    seed = seedProfile();
    const readerPort = await requestedPort("NBLANE_E2E_AGENT_READER_PORT", []);
    const spaPort = await requestedPort("NBLANE_E2E_AGENT_SPA_PORT", [readerPort]);
    if (readerPort === spaPort) throw new Error("Reader and SPA ports must be different.");
    readerBase = `http://127.0.0.1:${readerPort}`;
    spaBase = `http://127.0.0.1:${spaPort}`;
    readerServer = startServer("reader", readerPort);
    spaServer = startServer("spa", spaPort);
    await Promise.all([
      waitForHttp(`${readerBase}/auth/session-ok`, readerServer),
      waitForHttp(`${spaBase}/api/v1/health`, spaServer),
    ]);
  } catch (error) {
    await stopServers();
    fs.rmSync(tempRoot, { recursive: true, force: true });
    throw new Error(`${error instanceof Error ? error.message : String(error)}${diagnostics()}`);
  }
});

test.afterEach(async ({}, testInfo) => {
  if (testInfo.status === testInfo.expectedStatus) return;
  for (const kind of ["reader", "spa"] as const) {
    if (serverLogs[kind] && fs.existsSync(serverLogs[kind])) {
      await testInfo.attach(`${kind}-server.log`, {
        path: serverLogs[kind],
        contentType: "text/plain",
      });
    }
  }
});

test.afterAll(async () => {
  await stopServers();
  if (tempRoot) fs.rmSync(tempRoot, { recursive: true, force: true });
});

function spaUrl(suffix: string): string {
  return `${spaBase}${suffix}`;
}

function readerUrl(source: string, suffix: string): string {
  return `${readerBase}/reader/api/${encodeURIComponent(source)}/${suffix}`;
}

function readerHeaders(token: string): Record<string, string> {
  return { "X-Reader-Token": token };
}

async function loginAdmin(page: Page): Promise<void> {
  const response = await page.request.post(spaUrl("/api/v1/auth/login"), {
    data: { username: "admin", password },
  });
  expect(response.status(), await response.text()).toBe(200);
  await page.goto(spaUrl("/"), { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: "档案列表" })).toBeVisible();
}

async function agentLoginAndReaderToken(agent: APIRequestContext): Promise<string> {
  const login = await agent.post(spaUrl("/api/v1/auth/login"), {
    data: { username: "agent", password },
  });
  expect(login.status(), await login.text()).toBe(200);
  const identity = await login.json();
  expect(identity.agent).toBe(true);
  expect(identity.profiles).toEqual([profile]);

  const sidecarResponse = await agent.get(
    spaUrl(`/api/v1/profiles/${profile}/research/sidecar`),
  );
  expect(sidecarResponse.status(), await sidecarResponse.text()).toBe(200);
  const sidecarBody = await sidecarResponse.json();
  expect(sidecarBody.sidecar.base).toBe(readerBase);
  expect(sidecarBody.sidecar.handoff_token).toBeTruthy();

  const handoff = await agent.post(`${readerBase}/auth/session`, {
    form: { token: sidecarBody.sidecar.handoff_token },
  });
  expect(handoff.status(), await handoff.text()).toBe(200);
  expect(handoff.headers()["set-cookie"]).toContain("nblane_auth_session=");

  const tokenResponse = await agent.post(
    `${readerBase}/api/research/${profile}/papers/${encodeURIComponent(sourceId)}/reader-token`,
  );
  expect(tokenResponse.status(), await tokenResponse.text()).toBe(200);
  const tokenBody = await tokenResponse.json();
  expect(tokenBody.ok).toBe(true);
  expect(tokenBody.token).toBeTruthy();
  const token = tokenBody.token as string;
  const claims = JSON.parse(Buffer.from(token.split(".")[0], "base64url").toString("utf8"));
  expect(claims).toMatchObject({ user_id: "agent", profile, source_id: sourceId });
  return token;
}

async function journalEntries(request: APIRequestContext): Promise<JournalEntry[]> {
  const response = await request.get(
    spaUrl(`/api/v1/profiles/${profile}/agent/journal?limit=50`),
  );
  expect(response.status(), await response.text()).toBe(200);
  return (await response.json()).entries as JournalEntry[];
}

function entryByAction(
  entries: JournalEntry[],
  action: string,
  status?: JournalEntry["status"],
): JournalEntry {
  const entry = entries.find((item) => item.action === action && (!status || item.status === status));
  expect(
    entry,
    `Expected a ${status || "recorded"} ${action} journal entry; actual entries: ${JSON.stringify(entries)}`,
  ).toBeTruthy();
  return entry!;
}

async function clickRealUndo(page: Page, entry: JournalEntry): Promise<void> {
  const label = `撤销：${entry.summary || entry.action}`;
  const button = page.getByRole("button", { name: label, exact: true });
  await expect(button).toBeVisible();
  const responsePromise = page.waitForResponse(
    (response) =>
      response.request().method() === "POST" &&
      response.url().includes(`/agent/journal/${encodeURIComponent(entry.id)}/undo`),
    { timeout: 10_000 },
  );
  await button.click();
  const response = await responsePromise;
  expect(response.status(), await response.text()).toBe(200);
  await expect
    .poll(
      async () => {
        const entries = await journalEntries(page.request);
        return entries.find((item) => item.id === entry.id)?.status;
      },
      { timeout: 10_000, intervals: [100, 250, 500] },
    )
    .toBe("undone");
  await expect(button).toHaveCount(0);
}

async function paperState(
  request: APIRequestContext,
  source: string = sourceId,
): Promise<{ status: number; paper?: PaperState }> {
  const response = await request.get(
    spaUrl(`/api/v1/profiles/${profile}/research/sidecar?source_id=${encodeURIComponent(source)}`),
  );
  const body = await response.json();
  return { status: response.status(), paper: body.paper as PaperState | undefined };
}

async function annotationState(
  agent: APIRequestContext,
  token: string,
  annotationId: string,
): Promise<Record<string, unknown> | null> {
  const response = await agent.get(readerUrl(sourceId, "payload?page=1&full_document=0"), {
    headers: readerHeaders(token),
  });
  expect(response.status(), await response.text()).toBe(200);
  const body = await response.json();
  const annotations = Array.isArray(body.annotations) ? body.annotations : [];
  return (
    (annotations.find((item: Record<string, unknown>) => item.id === annotationId) as
      | Record<string, unknown>
      | undefined) || null
  );
}

function fileSnapshot(paths: string[]): Record<string, Buffer | null> {
  return Object.fromEntries(
    paths.map((item) => [item, fs.existsSync(item) ? fs.readFileSync(item) : null]),
  );
}

function expectSameFiles(actual: Record<string, Buffer | null>, expected: Record<string, Buffer | null>): void {
  for (const [item, bytes] of Object.entries(expected)) {
    const current = actual[item];
    if (bytes === null) expect(current, `${item} should still be absent`).toBeNull();
    else expect(current?.equals(bytes), `${item} should be byte-identical`).toBe(true);
  }
}

test("agent Reader policy, browser handoff and real undo are isolated end to end", async ({ page }) => {
  test.setTimeout(120_000);
  const agent = await apiRequest.newContext();
  try {
    await loginAdmin(page);
    await page.goto(spaUrl(`/p/${profile}/research/library`), {
      waitUntil: "domcontentloaded",
    });
    await expect(page).toHaveURL(`${spaBase}/p/${profile}/research/library`);
    await expect(page.getByTestId("paper-library-page")).toBeVisible();
    const library = page.frameLocator('iframe[data-testid="sidecar-frame"]');
    await expect(library.locator(".paper-tree-shell")).toBeVisible({ timeout: 20_000 });
    await expect(library.locator(`[data-paper-id="${sourceId}"]`)).toBeVisible();
    await expect(library.locator(".paper-tree-shell")).toHaveAttribute("class", /is-embed/);

    await library.locator(".paper-tree-head-action").click();
    const createDialog = library.locator(".paper-tree-dialog");
    await expect(createDialog).toBeVisible();
    await createDialog.locator("input").fill(collectionTitle);
    await createDialog.locator(".paper-tree-dialog-actions .is-primary").click();
    await expect(createDialog).toHaveCount(0);
    await expect(
      library.locator(".paper-tree-row").filter({ hasText: collectionTitle }),
    ).toBeVisible();
    expect(await journalEntries(page.request), "human collection edits are not journaled").toEqual([]);

    const token = await agentLoginAndReaderToken(agent);
    const created = await agent.post(readerUrl(sourceId, "annotation"), {
      headers: readerHeaders(token),
      data: {
        selected_text: "Deterministic passage for agent annotation.",
        segment_refs: ["seg:1"],
        page: 1,
        note: "agent-created annotation",
      },
    });
    expect(created.status(), await created.text()).toBe(200);
    const annotationId = (await created.json()).changed_ids.annotation_id as string;
    expect(annotationId).toBeTruthy();
    expect((await annotationState(agent, token, annotationId))?.status).toBe("active");

    const progress = await agent.post(readerUrl(sourceId, "progress"), {
      headers: readerHeaders(token),
      data: { page: 2 },
    });
    expect(progress.status(), await progress.text()).toBe(200);
    expect((await paperState(page.request)).paper?.last_page).toBe(2);

    const initialEntries = await journalEntries(page.request);
    const annotationEntry = entryByAction(initialEntries, "reader.annotation.create");
    const progressEntry = entryByAction(initialEntries, "reader.progress", "undoable");
    expect(annotationEntry.status).toBe("conflict");
    expect(annotationEntry.actor).toBe("agent");
    expect(progressEntry.actor).toBe("agent");
    expect(annotationEntry.tier).toBe("T1");
    expect(progressEntry.tier).toBe("T1");

    await page.setViewportSize({ width: 375, height: 812 });
    // AssistantPage is a global route; RecentAgentOps scopes its records to dev.
    await page.goto(spaUrl("/assistant"), { waitUntil: "domcontentloaded" });
    await expect(page.getByText("最近操作", { exact: true })).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(annotationEntry.summary, { exact: true })).toBeVisible();
    await expect(page.getByText(progressEntry.summary, { exact: true })).toBeVisible();

    // Progress was written after the annotation, so undo it first to avoid a
    // legitimate optimistic-concurrency conflict on research_source.
    await clickRealUndo(page, progressEntry);
    await expect
      .poll(async () => (await paperState(page.request)).paper?.last_page, {
        timeout: 10_000,
        intervals: [100, 250, 500],
      })
      .toBe(1);
    await clickRealUndo(page, annotationEntry);
    await expect
      .poll(async () => annotationState(agent, token, annotationId), {
        timeout: 10_000,
        intervals: [100, 250, 500],
      })
      .toBeNull();

    const secondCreate = await agent.post(readerUrl(sourceId, "annotation"), {
      headers: readerHeaders(token),
      data: {
        selected_text: "Deterministic passage for agent annotation.",
        segment_refs: ["seg:1"],
        page: 1,
        note: "annotation restored with the deleted paper",
      },
    });
    expect(secondCreate.status(), await secondCreate.text()).toBe(200);
    const restoredAnnotationId = (await secondCreate.json()).changed_ids.annotation_id as string;
    expect((await annotationState(agent, token, restoredAnnotationId))?.status).toBe("active");

    const annotationDeleteBody = {
      action: "annotation_delete",
      annotation_id: restoredAnnotationId,
    };
    const beforeAnnotationDelete = fileSnapshot([seed.annotations]);
    const annotationDelete = await agent.post(readerUrl(sourceId, "annotation"), {
      headers: readerHeaders(token),
      data: annotationDeleteBody,
    });
    expect(annotationDelete.status(), await annotationDelete.text()).toBe(428);
    const annotationDeleteRequired = await annotationDelete.json();
    expect(annotationDeleteRequired.code).toBe("confirmation_required");
    expect(annotationDeleteRequired.confirmation.confirm_id).toBeTruthy();
    expectSameFiles(fileSnapshot([seed.annotations]), beforeAnnotationDelete);
    expect((await annotationState(agent, token, restoredAnnotationId))?.status).toBe("active");

    const unknownAction = await agent.post(readerUrl(sourceId, "annotation"), {
      headers: readerHeaders(token),
      data: { action: "not_registered" },
    });
    expect(unknownAction.status(), await unknownAction.text()).toBe(403);
    expect((await unknownAction.json()).code).toBe("agent_forbidden");
    expectSameFiles(fileSnapshot([seed.annotations]), beforeAnnotationDelete);

    const wrongProfile = await agent.post(
      `${readerBase}/api/research/${otherProfile}/papers/${encodeURIComponent(sourceId)}/reader-token`,
    );
    expect(wrongProfile.status(), await wrongProfile.text()).toBe(403);

    const wrongSource = await agent.post(readerUrl(otherSourceId, "progress"), {
      headers: readerHeaders(token),
      data: { page: 2 },
    });
    expect(wrongSource.status(), await wrongSource.text()).toBe(401);
    expect((await paperState(page.request, otherSourceId)).paper?.last_page).toBe(1);

    const wrongUser = await agent.post(readerUrl(sourceId, "tasks"), {
      headers: readerHeaders(token),
      data: {
        action: "ask_paper",
        payload: { question: "must be rejected before execution", user_id: "admin" },
      },
    });
    expect(wrongUser.status(), await wrongUser.text()).toBe(403);
    expect((await journalEntries(page.request)).filter((item) => item.action === "reader.annotation.delete")).toEqual([]);

    // Active annotations are intentional paper-delete blockers. Complete the
    // body-classified T2 annotation deletion first, then verify its JSONL row
    // survives the later whole-paper delete/undo round trip.
    const annotationDeleted = await agent.post(readerUrl(sourceId, "annotation"), {
      headers: {
        ...readerHeaders(token),
        [confirmHeader]: annotationDeleteRequired.confirmation.confirm_id,
      },
      data: annotationDeleteBody,
    });
    expect(annotationDeleted.status(), await annotationDeleted.text()).toBe(200);
    expect((await annotationState(agent, token, restoredAnnotationId))?.status).toBe("deleted");

    const deleteBody = {
      action: "paper_library_delete_paper_record",
      payload: {
        paper_ids: [sourceId],
        confirm: sourceId,
        delete_pdf_asset: true,
        delete_reader_artifacts: true,
      },
    };
    const trackedPaths = [seed.sources, seed.pdf, seed.pages, seed.segments, seed.annotations];
    const beforeDelete = fileSnapshot(trackedPaths);
    const expectedPdf = beforeDelete[seed.pdf]!;
    const required = await agent.post(`${readerBase}/api/research/${profile}/paper-library/events`, {
      data: deleteBody,
    });
    expect(required.status(), await required.text()).toBe(428);
    const requiredBody = await required.json();
    expect(requiredBody.code).toBe("confirmation_required");
    expect(requiredBody.confirmation.action).toBe("reader.paper.delete");
    expect(requiredBody.confirmation.confirm_id).toBeTruthy();
    expectSameFiles(fileSnapshot(trackedPaths), beforeDelete);

    const deleted = await agent.post(`${readerBase}/api/research/${profile}/paper-library/events`, {
      headers: { [confirmHeader]: requiredBody.confirmation.confirm_id },
      data: deleteBody,
    });
    expect(deleted.status(), await deleted.text()).toBe(200);
    for (const item of [seed.pdf, seed.pages, seed.segments, seed.annotations]) {
      expect(fs.existsSync(item), `${item} should be physically deleted`).toBe(false);
    }
    expect((await paperState(page.request)).status).toBe(404);

    const deleteEntry = entryByAction(
      await journalEntries(page.request),
      "reader.paper.delete",
    );
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.reload({ waitUntil: "domcontentloaded" });
    await expect(page.getByText("最近操作", { exact: true })).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(deleteEntry.summary, { exact: true })).toBeVisible();
    await clickRealUndo(page, deleteEntry);

    await expect
      .poll(async () => (await paperState(page.request)).status, {
        timeout: 10_000,
        intervals: [100, 250, 500],
      })
      .toBe(200);
    const restoredPaper = (await paperState(page.request)).paper;
    expect(restoredPaper?.id).toBe(sourceId);
    expect(restoredPaper?.title).toBe("Agent Reader Policy Paper");
    expect(restoredPaper?.last_page).toBe(1);
    expect(restoredPaper?.page_count).toBe(2);

    for (const item of [seed.pages, seed.segments, seed.annotations]) {
      expectSameFiles(fileSnapshot([item]), { [item]: beforeDelete[item] });
    }
    expect(fs.readFileSync(seed.pdf).equals(expectedPdf)).toBe(true);
    expect((await annotationState(agent, token, restoredAnnotationId))?.status).toBe("deleted");
    expect((await annotationState(agent, token, restoredAnnotationId))?.note).toBe(
      "annotation restored with the deleted paper",
    );
    const servedPdf = await agent.get(readerUrl(sourceId, "pdf"), {
      headers: readerHeaders(token),
    });
    expect(servedPdf.status(), await servedPdf.text()).toBe(200);
    expect((await servedPdf.body()).equals(expectedPdf)).toBe(true);
  } finally {
    await agent.dispose();
  }
});
