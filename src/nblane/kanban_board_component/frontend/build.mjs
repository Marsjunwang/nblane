import { mkdir, readFile, copyFile } from "node:fs/promises";
import { dirname } from "node:path";
import { fileURLToPath } from "node:url";

const root = new URL("./", import.meta.url);
const sourceUrl = new URL("./src/index.html", root);
const outputUrl = new URL("./static/index.html", root);
const sourcePath = fileURLToPath(sourceUrl);
const outputPath = fileURLToPath(outputUrl);
const verifyOnly = process.argv.includes("--verify");

function fail(message) {
  console.error(`kanban static build failed: ${message}`);
  process.exit(1);
}

function verifyHtml(html, label) {
  const required = [
    "<div id=\"root\"></div>",
    "streamlit:componentReady",
    "streamlit:setComponentValue",
    "streamlit:render",
    "function render()",
    "event_id",
    "Doing",
    "Queue",
    "Done",
    "Someday / Maybe",
    "request_done_ingest",
    "confirm_subtask_alignment",
  ];
  for (const needle of required) {
    if (!html.includes(needle)) {
      fail(`${label} is missing ${needle}`);
    }
  }

  const forbidden = [
    "/src/main.jsx",
    "@vite/client",
    "react-refresh",
    "vite.svg",
  ];
  for (const needle of forbidden) {
    if (html.includes(needle)) {
      fail(`${label} still references the old Vite path ${needle}`);
    }
  }
}

const sourceHtml = await readFile(sourcePath, "utf8").catch((error) => {
  fail(`cannot read ${sourcePath}: ${error.message}`);
});
verifyHtml(sourceHtml, "source");

if (!verifyOnly) {
  await mkdir(dirname(outputPath), { recursive: true });
  await copyFile(sourcePath, outputPath);
}

const outputHtml = await readFile(outputPath, "utf8").catch((error) => {
  fail(`cannot read ${outputPath}: ${error.message}`);
});
verifyHtml(outputHtml, "static output");

if (outputHtml !== sourceHtml) {
  fail("static/index.html does not match src/index.html; run npm run build");
}

console.log(
  verifyOnly
    ? "Verified static/index.html matches src/index.html."
    : "Copied src/index.html to static/index.html and verified it.",
);
