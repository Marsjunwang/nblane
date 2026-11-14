import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import fs from "node:fs";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { assertOwnedStack, IDENTITY_PATH } from "./runtime.mjs";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const runId = randomUUID();
const root = fs.mkdtempSync(path.join(os.tmpdir(), "nblane-browser-e2e-"));
const children = [];
const logs = new Map();
let interrupted = false;
let exitCode = 1;

function freePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const port = server.address().port;
      server.close(() => resolve(port));
    });
  });
}

function start(command, args, env, label, inherit = false) {
  const child = spawn(command, args, { cwd: repoRoot, env, stdio: inherit ? "inherit" : ["ignore", "pipe", "pipe"] });
  children.push(child);
  child.completion = new Promise((resolve, reject) => {
    child.once("error", reject);
    child.once("exit", (code, signal) => resolve(code ?? (signal ? 130 : 1)));
  });
  // Keep startup errors observable even while waiting for another child.
  child.completion.catch(() => {});
  if (!inherit) {
    logs.set(label, "");
    for (const stream of [child.stdout, child.stderr]) {
      stream.on("data", (data) => logs.set(label, (logs.get(label) + data).slice(-80_000)));
    }
  }
  return child;
}

async function ready(child, base, label) {
  const deadline = Date.now() + 45_000;
  while (Date.now() < deadline && !interrupted) {
    if (child.exitCode !== null || child.signalCode !== null) break;
    try {
      const response = await fetch(new URL(IDENTITY_PATH, base), { signal: AbortSignal.timeout(1000) });
      if (response.ok && (await response.json()).run_id === runId) return;
    } catch {}
    await new Promise((resolve) => setTimeout(resolve, 150));
  }
  throw new Error(`${label} failed to start.\n${logs.get(label) || ""}`);
}

function interrupt() {
  interrupted = true;
  for (const child of children) if (child.exitCode === null) child.kill("SIGTERM");
}
process.once("SIGINT", interrupt);
process.once("SIGTERM", interrupt);

try {
  fs.writeFileSync(path.join(root, ".nblane-e2e.json"), JSON.stringify({ root, run_id: runId }));
  fs.writeFileSync(path.join(root, "empty.env"), "");
  fs.mkdirSync(path.join(root, "bin"));
  // Service probes stay local to the fixture instead of querying the user's assistant.
  fs.writeFileSync(path.join(root, "bin", "openclaw"), "#!/bin/sh\nexit 0\n", { mode: 0o755 });
  const spaPort = await freePort();
  let readerPort = await freePort();
  while (readerPort === spaPort) readerPort = await freePort();
  const spaBase = `http://127.0.0.1:${spaPort}`;
  const readerBase = `http://127.0.0.1:${readerPort}`;
  const env = {
    ...process.env,
    PATH: `${path.join(root, "bin")}${path.delimiter}${process.env.PATH || ""}`,
    PYTHONPATH: path.join(repoRoot, "src"),
    PYTHONDONTWRITEBYTECODE: "1",
    NBLANE_ROOT: root,
    NBLANE_ENV_FILE: path.join(root, "empty.env"),
    NBLANE_AUTH_FILE: path.join(root, "auth", "users.yaml"),
    NBLANE_AUTH_SESSION_SECRET: runId,
    NBLANE_READER_TOKEN_SECRET: runId,
    NBLANE_AUTH_COOKIE_SECURE: "0",
    NBLANE_DISABLE_NETWORK_LOOKUPS: "1",
    NBLANE_DATA_GIT_AUTOCOMMIT: "0",
    NBLANE_DATA_GIT_AUTOPUSH: "0",
    NBLANE_RESEARCH_ASSET_ROOT: path.join(root, "assets"),
    NBLANE_E2E_RESEARCH_ASSET_ROOT: path.join(root, "assets"),
    NBLANE_LOCAL_MODELS_DIR: path.join(root, "local-models"),
    NBLANE_GROBID_SERVICE_DIR: path.join(root, "grobid"),
    NBLANE_GROBID_UNIT: `nblane-e2e-${runId}`,
    NBLANE_GROBID_URL: "off",
    NBLANE_RESEARCH_PDF_BACKEND: "pymupdf",
    NBLANE_WORKSHOP_SERVICE_DIR: path.join(root, "workshop"),
    NBLANE_WORKSHOP_TMUX_SOCKET: `nblane-e2e-${runId}`,
    NBLANE_AGENT_STATE_DIR: path.join(root, "agent-state"),
    NBLANE_AGENT_DATA_ROOT: path.join(root, "agent-data"),
    NBLANE_CODEX_HOME: path.join(root, "codex"),
    NBLANE_CODEX_BIN: path.join(root, "no-codex"),
    NBLANE_CODEX_HOME_ROOT: path.join(root, "codex-profiles"),
    NBLANE_CODEX_LOCAL_WORKTREE_ROOT: path.join(root, "codex-worktrees"),
    NBLANE_BACKUP_KEY_DIR: path.join(root, "backup-keys"),
    NBLANE_BACKUP_STATE_DIR: path.join(root, "backup-state"),
    NBLANE_BACKUP_DIR: path.join(root, "backups"),
    NBLANE_OPENCLAW_PROFILE: `e2e-${runId}`,
    NBLANE_OPENCLAW_GATEWAY_PORT: "1",
    XDG_CONFIG_HOME: path.join(root, "config"),
    LLM_API_KEY: "",
    LLM_BASE_URL: "",
    OPENAI_API_KEY: "",
    VISUAL_API_KEY: "",
    DASHSCOPE_API_KEY: "",
    NBLANE_READER_API_BASE: readerBase,
    NBLANE_SPA_BASE_URL: spaBase,
    NBLANE_E2E_RUN_ID: runId,
    NBLANE_E2E_DATA_ROOT: root,
    NBLANE_E2E_BASE_URL: spaBase,
    NBLANE_E2E_SPA_BASE_URL: spaBase,
    NBLANE_E2E_READER_BASE: readerBase,
    NBLANE_E2E_PROFILE: "dev",
    NBLANE_E2E_ADMIN_USER: "admin",
    NBLANE_E2E_MEMBER_USER: "member",
    NBLANE_E2E_ADMIN_PASSWORD: "e2e-test-password",
    NBLANE_E2E_MEMBER_PASSWORD: "e2e-test-password",
    NBLANE_E2E_AUTH_STATE: path.join(root, "spa-admin.json"),
    NBLANE_HCI_SHOTS: path.join(root, "screenshots"),
    UI_LANG: "zh",
  };
  const venvPython = path.join(repoRoot, ".venv", "bin", "python");
  const python = process.env.NBLANE_E2E_PYTHON || (fs.existsSync(venvPython) ? venvPython : "python3");
  const seed = start(python, ["tests/e2e/seed.py"], env, "seed");
  if (await seed.completion !== 0) throw new Error(`Fixture seed failed.\n${logs.get("seed")}`);
  const serve = (kind, port) => start(python, ["-m", "uvicorn", `fixture_server:${kind}`, "--factory", "--app-dir", "tests/e2e", "--host", "127.0.0.1", "--port", String(port)], env, kind);
  const reader = serve("reader", readerPort);
  const spa = serve("spa", spaPort);
  await Promise.all([ready(reader, readerBase, "reader"), ready(spa, spaBase, "spa")]);
  await assertOwnedStack(env);
  console.log(`e2e: synthetic fixtures ${root}; SPA ${spaBase}; Reader ${readerBase}`);
  const cli = path.join(repoRoot, "node_modules", "@playwright", "test", "cli.js");
  const tests = start(process.execPath, [cli, "test", "-c", "tests/e2e/playwright.config.ts", ...process.argv.slice(2)], env, "playwright", true);
  exitCode = await tests.completion;
} catch (error) {
  console.error(error);
} finally {
  interrupt();
  for (const child of children) {
    if (child.exitCode !== null || child.signalCode !== null) continue;
    await Promise.race([child.completion.catch(() => {}), new Promise((resolve) => setTimeout(resolve, 3000))]);
    if (child.exitCode === null && child.signalCode === null) child.kill("SIGKILL");
  }
  if (exitCode !== 0) {
    const out = path.join(repoRoot, "test-results", `servers-${runId}`);
    fs.mkdirSync(out, { recursive: true });
    for (const [label, text] of logs) fs.writeFileSync(path.join(out, `${label}.log`), text);
  }
  if (process.env.NBLANE_E2E_KEEP_DATA === "1") console.log(`e2e: kept synthetic data at ${root}`);
  else fs.rmSync(root, { recursive: true, force: true });
}
process.exitCode = exitCode;
