import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { gzipSync } from "node:zlib";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const staticRoot = path.join(repoRoot, "src/nblane/web_ui/static");
const html = fs.readFileSync(path.join(staticRoot, "index.html"), "utf8");
// Resolve only entry scripts referenced by index.html, not unrelated chunks
// whose generated names also start with index-.
const entries = [...html.matchAll(/<script\b[^>]*\bsrc=["']([^"']+\.js)["'][^>]*>/g)]
  .map((match) => match[1]);
if (!entries.length) throw new Error("SPA index.html has no JavaScript entry.");
const budget = 260 * 1024;
let total = 0;
for (const entry of new Set(entries)) {
  const asset = path.resolve(staticRoot, entry.replace(/^\//, ""));
  if (!asset.startsWith(`${staticRoot}${path.sep}`)) throw new Error(`Invalid entry: ${entry}`);
  const bytes = gzipSync(fs.readFileSync(asset)).length;
  total += bytes;
  console.log(`${entry}: ${(bytes / 1024).toFixed(1)} KiB gzip`);
}
if (total > budget) {
  throw new Error(`SPA entry is ${(total / 1024).toFixed(1)} KiB gzip; budget is ${budget / 1024} KiB.`);
}
console.log(`SPA entry budget passed (${budget / 1024} KiB gzip).`);
